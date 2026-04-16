"""Orchestrates code analysis: LLM-driven decision discovery, OWNERS attribution,
and optional YAML/doc scanning for supplementary context."""

import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from models import DecisionArea, RepoProfile
from decision_discovery import DiscoveryAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analyzes a repository to identify architectural decision areas.

    Uses a two-pass approach:
      Pass 1 (DiscoveryAgent): LLM reads key source files and identifies decisions
      OWNERS/enrichment: attaches team attribution from OWNERS files
    """

    def __init__(self, profile: RepoProfile, llm_client=None):
        self.profile = profile
        self.repo_path = Path(profile.path)
        self.llm_client = llm_client
        self._discovery_agent = DiscoveryAgent(llm_client) if llm_client else None

    def analyze(self) -> List[DecisionArea]:
        logger.info(f"Analyzing {self.profile.owner}/{self.profile.name} "
                     f"(type={self.profile.repo_type}, lang={self.profile.primary_language})")

        if self._discovery_agent:
            areas = self._discovery_agent.discover(str(self.repo_path), self.profile)
        else:
            logger.warning("No LLM client provided — returning empty decision list")
            areas = []

        self._attach_owners(areas)

        logger.info(f"Identified {len(areas)} decision areas")
        return areas

    # ------------------------------------------------------------------
    # OWNERS attachment
    # ------------------------------------------------------------------

    def _attach_owners(self, areas: List[DecisionArea]):
        owners_cache: Dict[str, List[str]] = {}

        for area in areas:
            if area.owners:
                continue
            for filepath in area.key_files:
                dir_path = Path(filepath).parent
                approvers = self._find_owners_for(dir_path, owners_cache)
                if approvers:
                    area.owners = approvers
                    break

    def _find_owners_for(self, rel_dir: Path, cache: Dict[str, List[str]]) -> List[str]:
        key = str(rel_dir)
        if key in cache:
            return cache[key]

        search_path = self.repo_path / rel_dir
        while True:
            owners_file = search_path / "OWNERS"
            if owners_file.exists():
                approvers = self._parse_owners(owners_file)
                cache[key] = approvers
                return approvers
            if search_path == self.repo_path or search_path == search_path.parent:
                break
            search_path = search_path.parent

        cache[key] = []
        return []

    @staticmethod
    def _parse_owners(owners_file: Path) -> List[str]:
        try:
            content = owners_file.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                return data.get("approvers", []) or []
        except Exception:
            pass
        return []
