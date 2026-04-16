"""Targeted git history lookup and optional PR/Jira/enhancement enrichment."""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from models import DecisionArea
from enhancement_fetcher import EnhancementFetcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HistoryLookup:
    """Enriches DecisionAreas with historical context via targeted git queries."""

    def __init__(
        self,
        repo_path: str,
        jira_client=None,
        enhancement_fetcher: Optional[EnhancementFetcher] = None,
        repo_owner: str = "",
        repo_name: str = "",
    ):
        self.repo_path = Path(repo_path).resolve()
        self.jira_client = jira_client
        self.enhancement_fetcher = enhancement_fetcher
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self._gh_available = self._check_gh_cli()

    def enrich(self, area: DecisionArea):
        """Enrich a single DecisionArea with history, PR, Jira, and enhancement data."""
        history = self._find_introducing_commit(area)
        if not history:
            logger.debug(f"No git history found for {area.name}")
            return

        area.history = history

        pr_number = history.get("pr_number")
        if pr_number and self._gh_available:
            pr_data = self._fetch_pr(pr_number)
            if pr_data:
                history["pr_title"] = pr_data.get("title", "")
                history["pr_description"] = pr_data.get("body", "")
                history["pr_labels"] = pr_data.get("labels", [])

                enh_ref = self._extract_enhancement_ref(pr_data.get("body", ""))
                if enh_ref and self.enhancement_fetcher:
                    enh_data = self.enhancement_fetcher.fetch(enh_ref)
                    if enh_data:
                        area.enhancement = enh_data

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
                            enh_data = self.enhancement_fetcher.fetch(enh_ref)
                            if enh_data:
                                area.enhancement = enh_data
            except Exception as e:
                logger.warning(f"Failed to fetch Jira ticket {jira_key}: {e}")

        if not area.enhancement and self.enhancement_fetcher:
            for ref in area.evidence.values():
                enh_ref = self._extract_enhancement_ref(str(ref))
                if enh_ref:
                    enh_data = self.enhancement_fetcher.fetch(enh_ref)
                    if enh_data:
                        area.enhancement = enh_data
                        break

    def enrich_all(self, areas: List[DecisionArea]):
        for area in areas:
            try:
                self.enrich(area)
            except Exception as e:
                logger.warning(f"Error enriching {area.name}: {e}")

    # ------------------------------------------------------------------
    # Git history
    # ------------------------------------------------------------------

    def _find_introducing_commit(self, area: DecisionArea) -> Optional[Dict]:
        """Find the oldest commit that introduced the primary key file."""
        if not area.key_files:
            return None

        for key_file in area.key_files[:3]:
            full_path = self.repo_path / key_file
            if not full_path.exists():
                continue

            try:
                result = subprocess.run(
                    ["git", "log", "--follow", "--diff-filter=A",
                     "--format=%H|%s|%ai", "--", key_file],
                    cwd=self.repo_path,
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode != 0 or not result.stdout.strip():
                    continue

                lines = result.stdout.strip().splitlines()
                oldest = lines[-1]
                parts = oldest.split("|", 2)
                if len(parts) < 3:
                    continue

                commit_hash = parts[0]
                subject = parts[1]
                date_str = parts[2][:10]

                pr_number = self._extract_pr_number(subject)
                jira_key = self._extract_jira_key(subject)

                return {
                    "commit": commit_hash,
                    "subject": subject,
                    "date": date_str,
                    "key_file": key_file,
                    "pr_number": pr_number,
                    "jira_key": jira_key,
                }

            except (subprocess.TimeoutExpired, Exception) as e:
                logger.debug(f"Git log failed for {key_file}: {e}")
                continue

        return None

    # ------------------------------------------------------------------
    # PR fetch via gh CLI
    # ------------------------------------------------------------------

    def _fetch_pr(self, pr_number: int) -> Optional[Dict]:
        if not self.repo_owner or not self.repo_name:
            return None
        try:
            result = subprocess.run(
                ["gh", "pr", "view", str(pr_number),
                 "--repo", f"{self.repo_owner}/{self.repo_name}",
                 "--json", "title,body,labels"],
                capture_output=True, text=True, timeout=15,
                env=self._gh_env(),
            )
            if result.returncode != 0:
                return None

            import json
            data = json.loads(result.stdout)
            labels = [l.get("name", "") for l in data.get("labels", [])]
            return {
                "title": data.get("title", ""),
                "body": (data.get("body") or "")[:2000],
                "labels": labels,
            }
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_pr_number(commit_subject: str) -> Optional[int]:
        patterns = [
            r"Merge pull request #(\d+)",
            r"\(#(\d+)\)",
            r"#(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, commit_subject)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _extract_jira_key(text: str) -> Optional[str]:
        match = re.search(r"\b([A-Z]{2,}[A-Z0-9]*-\d+)\b", text)
        return match.group(1) if match else None

    @staticmethod
    def _extract_enhancement_ref(text: str) -> Optional[str]:
        if not text:
            return None
        patterns = [
            r"(openshift/enhancements#\d+)",
            r"(https?://github\.com/openshift/enhancements/pull/\d+)",
            r"(https?://github\.com/openshift/enhancements/blob/\w+/\S+\.md)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

    def _gh_env(self) -> dict:
        env = os.environ.copy()
        token = os.getenv("GITHUB_TOKEN")
        if token:
            env["GITHUB_TOKEN"] = token
        return env

    @staticmethod
    def _check_gh_cli() -> bool:
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
