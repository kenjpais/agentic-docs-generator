"""GitHub API client for fetching pull request data."""

import re
import os
from typing import List, Optional
from github import Github, Auth
from models import PullRequest
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client with authentication token."""
        token = token or os.getenv('GITHUB_TOKEN')
        if not token:
            raise ValueError("GITHUB_TOKEN is required")

        auth = Auth.Token(token)
        self.client = Github(auth=auth)

    def fetch_merged_prs(self, repo_owner: str, repo_name: str, limit: int = 10) -> List[PullRequest]:
        """
        Fetch recently merged pull requests.

        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            limit: Maximum number of PRs to fetch

        Returns:
            List of PullRequest objects
        """
        logger.info(f"Fetching merged PRs from {repo_owner}/{repo_name}")

        repo = self.client.get_repo(f"{repo_owner}/{repo_name}")
        pulls = repo.get_pulls(state='closed', sort='updated', direction='desc')

        merged_prs = []
        count = 0

        for pr in pulls:
            if count >= limit:
                break

            if pr.merged:
                pr_data = self._extract_pr_details(pr)
                merged_prs.append(pr_data)
                count += 1
                logger.info(f"Fetched PR #{pr.number}: {pr.title}")

        return merged_prs

    def _extract_pr_details(self, pr) -> PullRequest:
        """Extract relevant details from a GitHub PR object."""
        # Parse Jira ID from PR title, description, or branch
        jira_id = self._extract_jira_id(pr)

        # Get changed files
        files_changed = []
        for file in pr.get_files():
            files_changed.append({
                'filename': file.filename,
                'additions': file.additions,
                'deletions': file.deletions,
                'changes': file.changes,
                'patch': file.patch if file.patch else ""
            })

        return PullRequest(
            id=pr.id,
            number=pr.number,
            title=pr.title,
            description=pr.body or "",
            merged_at=pr.merged_at,
            files_changed=files_changed,
            jira_id=jira_id
        )

    def _extract_jira_id(self, pr) -> Optional[str]:
        """
        Extract Jira ticket ID from PR title, description, or branch name.

        Looks for patterns like: ABC-123, JIRA-456, etc.
        """
        # Common Jira ID pattern
        jira_pattern = r'\b([A-Z]{2,}-\d+)\b'

        # Check PR title
        match = re.search(jira_pattern, pr.title)
        if match:
            return match.group(1)

        # Check PR description
        if pr.body:
            match = re.search(jira_pattern, pr.body)
            if match:
                return match.group(1)

        # Check branch name
        if pr.head and pr.head.ref:
            match = re.search(jira_pattern, pr.head.ref)
            if match:
                return match.group(1)

        return None

    def fetch_pr_details(self, repo_owner: str, repo_name: str, pr_number: int) -> PullRequest:
        """Fetch details for a specific pull request."""
        repo = self.client.get_repo(f"{repo_owner}/{repo_name}")
        pr = repo.get_pull(pr_number)
        return self._extract_pr_details(pr)
