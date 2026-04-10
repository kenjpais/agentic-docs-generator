"""Context builder for creating structured feature contexts."""

from typing import List
from models import Feature, PullRequest, JiraTicket
from github_client import GitHubClient
from jira_client import JiraClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds structured contexts for features."""

    def __init__(self, github_client: GitHubClient, jira_client: JiraClient):
        """Initialize context builder with API clients."""
        self.github_client = github_client
        self.jira_client = jira_client

    def link_prs_to_jira(self, prs: List[PullRequest]) -> List[Feature]:
        """
        Link pull requests to Jira tickets and create features.

        Args:
            prs: List of PullRequest objects

        Returns:
            List of Feature objects (only includes PRs with valid Jira links)
        """
        features = []

        for pr in prs:
            if not pr.jira_id:
                logger.warning(f"PR #{pr.number} has no Jira ID, skipping")
                continue

            # Fetch Jira ticket
            jira_ticket = self.jira_client.fetch_jira_ticket(pr.jira_id)

            if not jira_ticket:
                logger.warning(f"Could not fetch Jira ticket {pr.jira_id} for PR #{pr.number}, skipping")
                continue

            # Build feature context
            context = self.build_feature_context(pr, jira_ticket)

            feature = Feature(
                pr=pr,
                jira=jira_ticket,
                summary_context=context
            )
            features.append(feature)
            logger.info(f"Created feature from PR #{pr.number} and Jira {pr.jira_id}")

        return features

    def build_feature_context(self, pr: PullRequest, jira: JiraTicket) -> dict:
        """
        Build a structured context for a feature.

        Args:
            pr: PullRequest object
            jira: JiraTicket object

        Returns:
            Dictionary with structured context
        """
        # Summarize code changes
        code_changes_summary = self._summarize_code_changes(pr.files_changed)

        context = {
            "feature_title": pr.title,
            "pr_number": pr.number,
            "jira_key": jira.key,
            "problem": jira.description,
            "solution_summary": pr.description,
            "code_changes": code_changes_summary,
            "jira_context": {
                "title": jira.title,
                "description": jira.description,
                "acceptance_criteria": jira.acceptance_criteria,
                "comments_count": len(jira.comments),
                "key_discussions": self._extract_key_discussions(jira.comments)
            },
            "files_modified": [f['filename'] for f in pr.files_changed],
            "total_additions": sum(f['additions'] for f in pr.files_changed),
            "total_deletions": sum(f['deletions'] for f in pr.files_changed)
        }

        return context

    def _summarize_code_changes(self, files_changed: List[dict]) -> str:
        """
        Summarize code changes from file diffs.

        Args:
            files_changed: List of file change dictionaries

        Returns:
            Summary string of code changes
        """
        if not files_changed:
            return "No code changes"

        summary_parts = []

        # Group by file type
        file_types = {}
        for file in files_changed:
            filename = file['filename']
            ext = filename.split('.')[-1] if '.' in filename else 'other'
            if ext not in file_types:
                file_types[ext] = []
            file_types[ext].append(file)

        # Summarize by type
        for ext, files in file_types.items():
            count = len(files)
            total_additions = sum(f['additions'] for f in files)
            total_deletions = sum(f['deletions'] for f in files)
            summary_parts.append(
                f"{count} {ext} file(s): +{total_additions} -{total_deletions} lines"
            )

        # Add specific file details
        file_details = []
        for file in files_changed[:10]:  # Limit to first 10 files
            file_details.append(
                f"  - {file['filename']}: +{file['additions']} -{file['deletions']}"
            )

        summary = "Code Changes Summary:\n" + "\n".join(summary_parts)
        if file_details:
            summary += "\n\nModified Files:\n" + "\n".join(file_details)

        if len(files_changed) > 10:
            summary += f"\n  ... and {len(files_changed) - 10} more files"

        return summary

    def _extract_key_discussions(self, comments: List[str], max_comments: int = 5) -> str:
        """
        Extract key discussions from Jira comments.

        Args:
            comments: List of comment strings
            max_comments: Maximum number of comments to include

        Returns:
            Summary of key discussions
        """
        if not comments:
            return "No discussions"

        # Take the most recent comments (assumed to be most relevant)
        key_comments = comments[-max_comments:]

        discussions = []
        for i, comment in enumerate(key_comments, 1):
            # Truncate long comments
            truncated = comment[:200] + "..." if len(comment) > 200 else comment
            discussions.append(f"{i}. {truncated}")

        return "\n".join(discussions)
