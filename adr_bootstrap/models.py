"""Data models for ADR bootstrap plugin."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    name: str
    decision_type: str
    description: str
    key_files: List[str]
    owners: List[str] = field(default_factory=list)
    evidence: Dict[str, str] = field(default_factory=dict)
    history: Optional[Dict] = None
    enhancement: Optional[Dict] = None
    significance: float = 0.0
