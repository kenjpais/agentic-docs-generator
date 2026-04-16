"""Fetch enhancement proposals from openshift/enhancements via GitHub API."""

import json
import os
import re
import subprocess
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_BODY_CHARS = 3000


class EnhancementFetcher:
    """Fetches OpenShift enhancement proposals when links are found."""

    def __init__(self, github_token: Optional[str] = None):
        self.token = github_token or os.getenv("GITHUB_TOKEN")
        self._available = self._check_gh_cli()

    def is_available(self) -> bool:
        return self._available

    def fetch(self, ref: str) -> Optional[Dict]:
        """Fetch an enhancement proposal.

        Args:
            ref: One of:
              - "openshift/enhancements#1234"  (PR number)
              - "https://github.com/openshift/enhancements/pull/1234"
              - "https://github.com/openshift/enhancements/blob/master/..."
        """
        if not self.is_available():
            logger.debug("Enhancement fetching unavailable (no gh CLI or token)")
            return None

        pr_number = self._parse_pr_number(ref)
        if pr_number:
            return self._fetch_pr(pr_number)

        file_path = self._parse_file_path(ref)
        if file_path:
            return self._fetch_file(file_path)

        logger.debug(f"Could not parse enhancement reference: {ref}")
        return None

    # ------------------------------------------------------------------
    # PR-based fetch
    # ------------------------------------------------------------------

    def _fetch_pr(self, pr_number: int) -> Optional[Dict]:
        try:
            result = subprocess.run(
                ["gh", "api",
                 f"repos/openshift/enhancements/pulls/{pr_number}",
                 "--jq", ".title, .body"],
                capture_output=True, text=True, timeout=15,
                env=self._gh_env(),
            )
            if result.returncode != 0:
                logger.warning(f"Failed to fetch enhancement PR #{pr_number}: {result.stderr.strip()}")
                return None

            lines = result.stdout.strip().split("\n", 1)
            title = lines[0] if lines else ""
            body = lines[1] if len(lines) > 1 else ""

            return {
                "type": "pr",
                "number": pr_number,
                "title": title,
                "body": body[:MAX_BODY_CHARS],
                "url": f"https://github.com/openshift/enhancements/pull/{pr_number}",
            }
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Error fetching enhancement PR #{pr_number}: {e}")
            return None

    # ------------------------------------------------------------------
    # File-based fetch (raw content from a specific path in the repo)
    # ------------------------------------------------------------------

    def _fetch_file(self, file_path: str) -> Optional[Dict]:
        try:
            result = subprocess.run(
                ["gh", "api",
                 f"repos/openshift/enhancements/contents/{file_path}",
                 "--jq", ".content"],
                capture_output=True, text=True, timeout=15,
                env=self._gh_env(),
            )
            if result.returncode != 0:
                logger.warning(f"Failed to fetch enhancement file {file_path}: {result.stderr.strip()}")
                return None

            import base64
            content = base64.b64decode(result.stdout.strip()).decode("utf-8", errors="replace")
            return {
                "type": "file",
                "path": file_path,
                "title": file_path.split("/")[-1].replace("-", " ").replace(".md", ""),
                "body": content[:MAX_BODY_CHARS],
                "url": f"https://github.com/openshift/enhancements/blob/master/{file_path}",
            }
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.warning(f"Error fetching enhancement file {file_path}: {e}")
            return None

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_pr_number(ref: str) -> Optional[int]:
        patterns = [
            r"openshift/enhancements#(\d+)",
            r"github\.com/openshift/enhancements/pull/(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, ref)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _parse_file_path(ref: str) -> Optional[str]:
        match = re.search(
            r"github\.com/openshift/enhancements/blob/\w+/(.+\.md)", ref
        )
        if match:
            return match.group(1)
        return None

    def _gh_env(self) -> dict:
        env = os.environ.copy()
        if self.token:
            env["GITHUB_TOKEN"] = self.token
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
