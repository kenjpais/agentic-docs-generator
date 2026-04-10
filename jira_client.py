"""Jira API client for fetching ticket data."""

import os
from typing import Optional
from jira import JIRA
from models import JiraTicket
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JiraClient:
    """Client for interacting with Jira API."""

    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None,
                 email: Optional[str] = None):
        """
        Initialize Jira client with optional authentication.

        Args:
            base_url: Jira instance URL (e.g., https://yourcompany.atlassian.net)
            token: API token for authentication (optional for public Jira)
            email: Email address for authentication (optional for public Jira)
        """
        self.base_url = base_url or os.getenv('JIRA_BASE_URL')
        token = token or os.getenv('JIRA_API_TOKEN')
        email = email or os.getenv('JIRA_EMAIL')

        if not self.base_url:
            raise ValueError("JIRA_BASE_URL is required")

        # Initialize Jira client with or without authentication
        if token and email:
            logger.info("Initializing Jira client with authentication")
            self.client = JIRA(
                server=self.base_url,
                basic_auth=(email, token)
            )
        else:
            logger.info("Initializing Jira client for public access (no authentication)")
            self.client = JIRA(server=self.base_url)

    def fetch_jira_ticket(self, jira_id: str) -> Optional[JiraTicket]:
        """
        Fetch a Jira ticket by ID.

        Args:
            jira_id: Jira ticket ID (e.g., ABC-123)

        Returns:
            JiraTicket object or None if not found
        """
        try:
            logger.info(f"Fetching Jira ticket: {jira_id}")
            issue = self.client.issue(jira_id)

            # Extract description
            description = issue.fields.description or ""

            # Extract acceptance criteria (often in description or custom field)
            acceptance_criteria = self._extract_acceptance_criteria(issue)

            # Extract comments
            comments = []
            for comment in issue.fields.comment.comments:
                comments.append(comment.body)

            ticket = JiraTicket(
                id=issue.id,
                key=issue.key,
                title=issue.fields.summary,
                description=description,
                acceptance_criteria=acceptance_criteria,
                comments=comments
            )

            logger.info(f"Successfully fetched Jira ticket: {jira_id}")
            return ticket

        except Exception as e:
            logger.error(f"Error fetching Jira ticket {jira_id}: {str(e)}")
            return None

    def _extract_acceptance_criteria(self, issue) -> str:
        """
        Extract acceptance criteria from Jira ticket.

        This may be in a custom field or part of the description.
        Adjust based on your Jira configuration.
        """
        # Try to get from custom field (adjust field name as needed)
        try:
            # Common custom field names for acceptance criteria
            if hasattr(issue.fields, 'customfield_10000'):
                return issue.fields.customfield_10000 or ""
        except AttributeError:
            pass

        # Parse from description if it contains "Acceptance Criteria" section
        description = issue.fields.description or ""
        if "acceptance criteria" in description.lower():
            lines = description.split('\n')
            criteria_lines = []
            in_criteria_section = False

            for line in lines:
                if "acceptance criteria" in line.lower():
                    in_criteria_section = True
                    continue
                if in_criteria_section:
                    if line.strip() and not line.strip().startswith('#'):
                        criteria_lines.append(line)
                    elif line.strip().startswith('#'):
                        break

            if criteria_lines:
                return '\n'.join(criteria_lines)

        return ""
