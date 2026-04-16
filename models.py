"""Data models for agentic documentation generator."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, runtime_checkable
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Existing models (used by simple/full modes)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Bootstrap mode models
# ---------------------------------------------------------------------------

@dataclass
class RepoProfile:
    """Auto-detected profile of a repository."""
    path: str
    name: str
    owner: str
    primary_language: str           # go | python | typescript | mixed
    repo_type: str                  # operator | library | installer | cli | console | unknown
    openshift_category: str         # core_operator | ecosystem_operator | library | api | unknown
    languages_detected: Dict[str, int] = field(default_factory=dict)
    has_owners: bool = False
    has_crd: bool = False
    has_go_mod: bool = False
    has_package_json: bool = False
    has_requirements_txt: bool = False
    has_pyproject_toml: bool = False


@dataclass
class DecisionArea:
    """An architectural decision area identified from code analysis."""
    name: str                       # e.g. "Asset Graph Pipeline"
    decision_type: str              # technology_choice | design_pattern | api_design
                                    # | operator_pattern | constraint | operational
    description: str                # Brief description of the observed pattern/choice
    key_files: List[str]            # File paths that embody this decision
    owners: List[str] = field(default_factory=list)
    evidence: Dict[str, str] = field(default_factory=dict)
    history: Optional[Dict] = None           # Filled by history_lookup
    enhancement: Optional[Dict] = None       # Filled by enhancement_fetcher
    significance: float = 0.0                # Ranking score for clustering


@runtime_checkable
class LanguageScanner(Protocol):
    """Protocol that language-specific scanners must implement."""

    def scan_abstractions(self, repo_path: Path) -> List[DecisionArea]:
        """Find interfaces, base classes, protocols — design patterns."""
        ...

    def scan_dependencies(self, repo_path: Path) -> List[DecisionArea]:
        """Find significant technology choices from dependency files."""
        ...

    def scan_comments(self, repo_path: Path) -> List[Dict]:
        """Find significant code comments containing rationale."""
        ...
