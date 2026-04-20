"""
GitHub GraphQL client for repository ingestion.

Fetches PR metadata, linked issues, labels, and branch info using
efficient batched GraphQL queries with cursor-based pagination.
Supports date-range filtering for time-bounded feature analysis.
"""

import os
import re
import json
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://api.github.com/graphql"
REPO_SLUG_RE = re.compile(r"^(?:https?://github\.com/)?([^/]+)/([^/]+?)(?:\.git)?$")

# ── HTTP session (connection pooling + retry on 429/5xx) ──

_session_lock = threading.Lock()
_session: Optional[requests.Session] = None


def _get_session(timeout: int = 30) -> requests.Session:
    global _session
    with _session_lock:
        if _session is None:
            _session = requests.Session()
            retry = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST"],
                respect_retry_after_header=True,
            )
            adapter = HTTPAdapter(
                pool_connections=5, pool_maxsize=15, max_retries=retry
            )
            _session.mount("https://", adapter)
            _session.mount("http://", adapter)
        return _session


# ── Data models ──

@dataclass
class LinkedIssue:
    number: int
    title: str
    url: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PRMetadata:
    number: int
    title: str
    body: str
    state: str
    merged_at: str
    head_ref: str
    base_ref: str
    user: str
    url: str
    labels: List[str] = field(default_factory=list)
    linked_issues: List[LinkedIssue] = field(default_factory=list)
    files_changed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["linked_issues"] = [li.to_dict() for li in self.linked_issues]
        return d


@dataclass
class RepoMetadata:
    name: str
    full_name: str
    description: str
    default_branch: str = "main"
    primary_language: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── Client ──

class GitHubGraphQLClient:
    """
    GitHub GraphQL client optimized for bulk PR ingestion with:
    - Date-range filtering via GitHub search API
    - Linked issues via closingIssuesReferences
    - Cursor-based pagination with adaptive page sizing
    - Rate limit tracking
    """

    def __init__(self, token: str = None, api_url: str = GRAPHQL_URL):
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token required. Set GITHUB_TOKEN env var or pass token=."
            )
        self.api_url = api_url
        self.remaining = 5000
        self.reset_at: Optional[str] = None

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "agentic-docs-generator/1.0",
            "Accept": "application/vnd.github.v4+json",
        }

    def _execute(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        if self.remaining < 50:
            logger.warning(f"Rate limit low ({self.remaining}), waiting...")
            self._wait_for_reset()

        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        session = _get_session()
        resp = session.post(self.api_url, json=payload, headers=self._headers())
        resp.raise_for_status()
        data = resp.json()

        if "errors" in data:
            msgs = [e.get("message", str(e)) for e in data["errors"]]
            if any("rate limit" in m.lower() for m in msgs):
                self._wait_for_reset()
                return self._execute(query, variables)
            raise ValueError(f"GraphQL errors: {msgs}")

        rl = data.get("data", {}).get("rateLimit")
        if rl:
            self.remaining = rl.get("remaining", self.remaining)
            self.reset_at = rl.get("resetAt", self.reset_at)

        return data

    def _wait_for_reset(self):
        if self.reset_at:
            try:
                reset = datetime.fromisoformat(self.reset_at.replace("Z", "+00:00"))
                wait = max(1, min((reset - datetime.now(timezone.utc)).total_seconds() + 5, 900))
            except (ValueError, TypeError):
                wait = 60
        else:
            wait = 60
        logger.info(f"Waiting {wait:.0f}s for rate limit reset...")
        time.sleep(wait)

    def test_token(self) -> Dict[str, Any]:
        result = self._execute("query { viewer { login } rateLimit { remaining resetAt } }")
        viewer = result.get("data", {}).get("viewer", {})
        return {"valid": bool(viewer.get("login")), "login": viewer.get("login", "")}

    # ── Repo metadata ──

    def fetch_repo_metadata(self, owner: str, name: str) -> RepoMetadata:
        query = f"""
        query {{
            repository(owner: "{owner}", name: "{name}") {{
                name
                nameWithOwner
                description
                defaultBranchRef {{ name }}
                primaryLanguage {{ name }}
            }}
            rateLimit {{ remaining resetAt }}
        }}
        """
        data = self._execute(query).get("data", {}).get("repository", {})
        return RepoMetadata(
            name=data.get("name", name),
            full_name=data.get("nameWithOwner", f"{owner}/{name}"),
            description=data.get("description") or "",
            default_branch=(data.get("defaultBranchRef") or {}).get("name", "main"),
            primary_language=(data.get("primaryLanguage") or {}).get("name", ""),
        )

    # ── PR ingestion with date range + linked issues ──

    def fetch_pull_requests(
        self,
        owner: str,
        name: str,
        limit: int = 100,
        since: Optional[str] = None,
        until: Optional[str] = None,
        states: Optional[List[str]] = None,
        page_size: int = 25,
    ) -> List[PRMetadata]:
        """
        Fetch PRs for a repo with date range filtering and linked issues.

        Args:
            owner: Repo owner
            name: Repo name
            limit: Max PRs to fetch
            since: Start date (ISO 8601, e.g. "2025-10-15"). Default: 6 months ago.
            until: End date (ISO 8601). Default: today.
            states: PR states (MERGED, CLOSED, OPEN). Default: [MERGED, CLOSED].
            page_size: PRs per page (default 25, auto-reduces on errors)

        Returns:
            List of PRMetadata with linked issues populated
        """
        states = states or ["MERGED", "CLOSED"]
        states_str = ", ".join(states)

        if not since:
            since = (datetime.now(timezone.utc) - timedelta(days=180)).strftime("%Y-%m-%d")
        if not until:
            until = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        logger.info(f"Fetching PRs from {owner}/{name} | {since} to {until} | states: {states}")

        all_prs: List[PRMetadata] = []
        cursor: Optional[str] = None
        current_page = min(page_size, 100)

        while len(all_prs) < limit:
            remaining = min(current_page, limit - len(all_prs))
            after = f', after: "{cursor}"' if cursor else ""

            query = f"""
            query {{
                repository(owner: "{owner}", name: "{name}") {{
                    pullRequests(
                        first: {remaining},
                        states: [{states_str}],
                        orderBy: {{field: UPDATED_AT, direction: DESC}}
                        {after}
                    ) {{
                        pageInfo {{ hasNextPage endCursor }}
                        nodes {{
                            number
                            title
                            body
                            state
                            mergedAt
                            updatedAt
                            headRefName
                            baseRefName
                            url
                            author {{ login }}
                            labels(first: 10) {{ nodes {{ name }} }}
                            files(first: 50) {{ nodes {{ path }} }}
                            closingIssuesReferences(first: 10) {{
                                nodes {{
                                    number
                                    title
                                    url
                                }}
                            }}
                        }}
                    }}
                }}
                rateLimit {{ remaining resetAt cost }}
            }}
            """

            try:
                result = self._execute(query)
            except (requests.RequestException, requests.exceptions.RetryError, ValueError) as e:
                if current_page > 5:
                    current_page = max(5, current_page // 2)
                    logger.warning(f"Query failed, reducing page to {current_page}: {e}")
                    time.sleep(2)
                    continue
                raise

            pr_conn = result.get("data", {}).get("repository", {}).get("pullRequests", {})
            nodes = pr_conn.get("nodes") or []

            if not nodes:
                break

            since_dt = datetime.fromisoformat(since).replace(tzinfo=timezone.utc)
            until_dt = (datetime.fromisoformat(until) + timedelta(days=1)).replace(tzinfo=timezone.utc)
            hit_boundary = False

            for node in nodes:
                updated = node.get("updatedAt") or node.get("mergedAt") or ""
                if updated:
                    try:
                        updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                        if updated_dt < since_dt:
                            hit_boundary = True
                            break
                        if updated_dt > until_dt:
                            continue
                    except (ValueError, TypeError):
                        pass

                all_prs.append(self._to_pr_metadata(node))
                if len(all_prs) >= limit:
                    break

            if hit_boundary:
                break

            page_info = pr_conn.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")

        logger.info(
            f"Fetched {len(all_prs)} PRs from {owner}/{name} "
            f"(rate limit remaining: {self.remaining})"
        )
        return all_prs

    def _to_pr_metadata(self, node: Dict[str, Any]) -> PRMetadata:
        labels_data = node.get("labels") or {}
        files_data = node.get("files") or {}
        closing_refs = node.get("closingIssuesReferences") or {}

        linked = [
            LinkedIssue(
                number=issue.get("number", 0),
                title=issue.get("title", ""),
                url=issue.get("url", ""),
            )
            for issue in (closing_refs.get("nodes") or [])
        ]

        return PRMetadata(
            number=node.get("number", 0),
            title=node.get("title", ""),
            body=node.get("body") or "",
            state=(node.get("state") or "").lower(),
            merged_at=node.get("mergedAt") or "",
            head_ref=node.get("headRefName", ""),
            base_ref=node.get("baseRefName", ""),
            user=(node.get("author") or {}).get("login", ""),
            url=node.get("url", ""),
            labels=[l["name"] for l in (labels_data.get("nodes") or [])],
            files_changed=[f["path"] for f in (files_data.get("nodes") or [])],
            linked_issues=linked,
        )


# ── Ingestion orchestrator ──

def parse_repo_spec(spec: str) -> Tuple[str, str]:
    match = REPO_SLUG_RE.match(spec.strip())
    if not match:
        raise ValueError(f"Invalid repo: '{spec}'. Use 'owner/name' or GitHub URL.")
    return match.group(1), match.group(2)


def ingest_repos(
    repo_specs: List[str],
    token: str = None,
    limit: int = 100,
    since: Optional[str] = None,
    until: Optional[str] = None,
    states: Optional[List[str]] = None,
    output_dir: str = "./output/github-ingestion",
) -> List[Path]:
    """
    Ingest GitHub data for one or more repos and write JSON files.

    Args:
        repo_specs: List of "owner/name" or full GitHub URLs
        token: GitHub token (or set GITHUB_TOKEN env var)
        limit: Max PRs per repo
        since: Start date (ISO 8601). Default: 6 months ago.
        until: End date (ISO 8601). Default: today.
        states: PR state filter. Default: [MERGED, CLOSED].
        output_dir: Where to write JSON files.

    Returns:
        List of file paths created
    """
    client = GitHubGraphQLClient(token=token)

    auth = client.test_token()
    if not auth["valid"]:
        raise RuntimeError("GitHub token is invalid.")
    logger.info(f"Authenticated as: {auth['login']}")

    repos = [parse_repo_spec(s) for s in repo_specs]
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    all_results = []
    files_created = []

    for owner, name in repos:
        meta = client.fetch_repo_metadata(owner, name)
        prs = client.fetch_pull_requests(
            owner, name, limit=limit, since=since, until=until, states=states
        )

        result = {
            "github": {
                "repository": meta.to_dict(),
                "pull_requests": [pr.to_dict() for pr in prs],
            }
        }
        all_results.append(result)

        fpath = out / f"{name}.json"
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved: {fpath} ({fpath.stat().st_size / 1024:.1f} KB)")
        files_created.append(fpath)

    if len(all_results) > 1:
        combined = out / "all_repositories.json"
        with open(combined, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved combined: {combined}")
        files_created.append(combined)

    return files_created
