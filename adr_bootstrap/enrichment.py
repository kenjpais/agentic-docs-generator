"""Enrichment: git history, Jira tickets, enhancement proposals, and PR descriptions."""

import base64
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from .models import DecisionArea
import logging

logger = logging.getLogger(__name__)

MAX_ENH_BODY_CHARS = 3000


# ---------------------------------------------------------------------------
# Enhancement fetcher
# ---------------------------------------------------------------------------

class EnhancementFetcher:
    """Fetches OpenShift enhancement proposals via gh CLI."""

    def __init__(self):
        self._available = self._check_gh_cli()

    def is_available(self) -> bool:
        return self._available

    def fetch(self, ref: str) -> Optional[Dict]:
        if not self.is_available():
            return None
        pr_number = self._parse_pr_number(ref)
        if pr_number:
            return self._fetch_pr(pr_number)
        file_path = self._parse_file_path(ref)
        if file_path:
            return self._fetch_file(file_path)
        return None

    def _fetch_pr(self, pr_number: int) -> Optional[Dict]:
        try:
            r = subprocess.run(
                ["gh", "api", f"repos/openshift/enhancements/pulls/{pr_number}",
                 "--jq", ".title, .body"],
                capture_output=True, text=True, timeout=15, env=self._gh_env())
            if r.returncode != 0:
                return None
            lines = r.stdout.strip().split("\n", 1)
            return {
                "type": "pr", "number": pr_number,
                "title": lines[0] if lines else "",
                "body": (lines[1] if len(lines) > 1 else "")[:MAX_ENH_BODY_CHARS],
                "url": f"https://github.com/openshift/enhancements/pull/{pr_number}",
            }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def _fetch_file(self, file_path: str) -> Optional[Dict]:
        try:
            r = subprocess.run(
                ["gh", "api", f"repos/openshift/enhancements/contents/{file_path}",
                 "--jq", ".content"],
                capture_output=True, text=True, timeout=15, env=self._gh_env())
            if r.returncode != 0:
                return None
            content = base64.b64decode(r.stdout.strip()).decode("utf-8", errors="replace")
            return {
                "type": "file", "path": file_path,
                "title": file_path.split("/")[-1].replace("-", " ").replace(".md", ""),
                "body": content[:MAX_ENH_BODY_CHARS],
                "url": f"https://github.com/openshift/enhancements/blob/master/{file_path}",
            }
        except Exception:
            return None

    @staticmethod
    def _parse_pr_number(ref: str) -> Optional[int]:
        for p in [r"openshift/enhancements#(\d+)",
                   r"github\.com/openshift/enhancements/pull/(\d+)"]:
            m = re.search(p, ref)
            if m:
                return int(m.group(1))
        return None

    @staticmethod
    def _parse_file_path(ref: str) -> Optional[str]:
        m = re.search(r"github\.com/openshift/enhancements/blob/\w+/(.+\.md)", ref)
        return m.group(1) if m else None

    @staticmethod
    def _gh_env() -> dict:
        env = os.environ.copy()
        token = os.getenv("GITHUB_TOKEN")
        if token:
            env["GITHUB_TOKEN"] = token
        return env

    @staticmethod
    def _check_gh_cli() -> bool:
        try:
            return subprocess.run(
                ["gh", "--version"], capture_output=True, text=True, timeout=5
            ).returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


# ---------------------------------------------------------------------------
# History lookup + enrichment orchestrator
# ---------------------------------------------------------------------------

class Enricher:
    """Enriches DecisionAreas with git history, Jira, PR, and enhancement data."""

    def __init__(self, repo_path: str, jira_client=None,
                 enhancement_fetcher: Optional[EnhancementFetcher] = None,
                 repo_owner: str = "", repo_name: str = ""):
        self.repo_path = Path(repo_path).resolve()
        self.jira_client = jira_client
        self.enhancement_fetcher = enhancement_fetcher
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self._gh_available = self._check_gh_cli()

    def enrich_all(self, areas: List[DecisionArea]):
        for area in areas:
            try:
                self._enrich_one(area)
            except Exception as e:
                logger.warning(f"Error enriching {area.name}: {e}")

    def _enrich_one(self, area: DecisionArea):
        history = self._find_introducing_commit(area)
        if not history:
            return
        area.history = history

        pr_number = history.get("pr_number")
        if pr_number and self._gh_available:
            pr_data = self._fetch_pr(pr_number)
            if pr_data:
                history["pr_title"] = pr_data.get("title", "")
                history["pr_description"] = pr_data.get("body", "")
                enh_ref = self._extract_enhancement_ref(pr_data.get("body", ""))
                if enh_ref and self.enhancement_fetcher:
                    enh = self.enhancement_fetcher.fetch(enh_ref)
                    if enh:
                        area.enhancement = enh

        jira_key = history.get("jira_key")
        if jira_key and self.jira_client:
            try:
                ticket = self.jira_client.fetch_jira_ticket(jira_key)
                if ticket:
                    history["jira_title"] = ticket.title
                    history["jira_description"] = ticket.description[:1000]
                    if not area.enhancement and self.enhancement_fetcher:
                        enh_ref = self._extract_enhancement_ref(ticket.description)
                        if enh_ref:
                            enh = self.enhancement_fetcher.fetch(enh_ref)
                            if enh:
                                area.enhancement = enh
            except Exception as e:
                logger.warning(f"Jira fetch failed for {jira_key}: {e}")

        if not area.enhancement and self.enhancement_fetcher:
            for ref in area.evidence.values():
                enh_ref = self._extract_enhancement_ref(str(ref))
                if enh_ref:
                    enh = self.enhancement_fetcher.fetch(enh_ref)
                    if enh:
                        area.enhancement = enh
                        break

    def _find_introducing_commit(self, area: DecisionArea) -> Optional[Dict]:
        if not area.key_files:
            return None
        for key_file in area.key_files[:3]:
            if not (self.repo_path / key_file).exists():
                continue
            try:
                r = subprocess.run(
                    ["git", "log", "--follow", "--diff-filter=A",
                     "--format=%H|%s|%ai", "--", key_file],
                    cwd=self.repo_path, capture_output=True, text=True, timeout=15)
                if r.returncode != 0 or not r.stdout.strip():
                    continue
                oldest = r.stdout.strip().splitlines()[-1]
                parts = oldest.split("|", 2)
                if len(parts) < 3:
                    continue
                return {
                    "commit": parts[0], "subject": parts[1],
                    "date": parts[2][:10], "key_file": key_file,
                    "pr_number": self._extract_pr_number(parts[1]),
                    "jira_key": self._extract_jira_key(parts[1]),
                }
            except (subprocess.TimeoutExpired, Exception):
                continue
        return None

    def _fetch_pr(self, pr_number: int) -> Optional[Dict]:
        if not self.repo_owner or not self.repo_name:
            return None
        try:
            r = subprocess.run(
                ["gh", "pr", "view", str(pr_number),
                 "--repo", f"{self.repo_owner}/{self.repo_name}",
                 "--json", "title,body,labels"],
                capture_output=True, text=True, timeout=15, env=self._gh_env())
            if r.returncode != 0:
                return None
            data = json.loads(r.stdout)
            return {"title": data.get("title", ""),
                    "body": (data.get("body") or "")[:2000],
                    "labels": [l.get("name", "") for l in data.get("labels", [])]}
        except Exception:
            return None

    @staticmethod
    def _extract_pr_number(text: str) -> Optional[int]:
        for p in [r"Merge pull request #(\d+)", r"\(#(\d+)\)", r"#(\d+)"]:
            m = re.search(p, text)
            if m:
                return int(m.group(1))
        return None

    @staticmethod
    def _extract_jira_key(text: str) -> Optional[str]:
        m = re.search(r"\b([A-Z]{2,}[A-Z0-9]*-\d+)\b", text)
        return m.group(1) if m else None

    @staticmethod
    def _extract_enhancement_ref(text: str) -> Optional[str]:
        if not text:
            return None
        for p in [r"(openshift/enhancements#\d+)",
                   r"(https?://github\.com/openshift/enhancements/pull/\d+)",
                   r"(https?://github\.com/openshift/enhancements/blob/\w+/\S+\.md)"]:
            m = re.search(p, text)
            if m:
                return m.group(1)
        return None

    @staticmethod
    def _gh_env() -> dict:
        env = os.environ.copy()
        token = os.getenv("GITHUB_TOKEN")
        if token:
            env["GITHUB_TOKEN"] = token
        return env

    @staticmethod
    def _check_gh_cli() -> bool:
        try:
            return subprocess.run(
                ["gh", "--version"], capture_output=True, text=True, timeout=5
            ).returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
