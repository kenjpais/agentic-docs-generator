"""Data models for agentic documentation generator."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Repository:
    """Represents a GitHub repository."""
    name: str
    owner: str


@dataclass
class PullRequest:
    """Represents a GitHub Pull Request."""
    id: int
    number: int
    title: str
    description: str
    merged_at: Optional[datetime]
    files_changed: List[dict]  # List of {filename, additions, deletions, patch}
    jira_id: Optional[str] = None


@dataclass
class JiraTicket:
    """Represents a Jira ticket."""
    id: str
    key: str
    title: str
    description: str
    acceptance_criteria: str
    comments: List[str]


@dataclass
class Feature:
    """Represents a feature combining PR and Jira data."""
    pr: PullRequest
    jira: Optional[JiraTicket]
    summary_context: dict
