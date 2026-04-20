"""ADR Bootstrap Plugin — self-contained ADR generation from code analysis.

Usage:
    from adr_bootstrap import generate_adrs
    paths = generate_adrs(repo_path, output_dir, llm_client)
"""

import os
import logging
from typing import List, Optional

from .profiler import RepoProfiler
from .discovery import DiscoveryAgent
from .enrichment import EnhancementFetcher, Enricher
from .generator import ADRGenerator

logger = logging.getLogger(__name__)


def generate_adrs(
    repo_path: str,
    output_dir: str,
    llm_client,
    jira_base_url: str = "https://redhat.atlassian.net",
    max_decisions: int = 8,
) -> List[str]:
    """Bootstrap ADR generation for a repository.

    Args:
        repo_path: Path to a local git repository clone.
        output_dir: Directory where output will be written.
        llm_client: Any object with a .generate(prompt: str) -> str method.
        jira_base_url: Jira instance URL for ticket enrichment.
        max_decisions: Maximum number of decisions to discover.

    Returns:
        List of generated ADR file paths.
    """
    profiler = RepoProfiler(repo_path)
    profile = profiler.profile()
    logger.info(f"Repo profile: {profile.repo_type} ({profile.openshift_category}), "
                f"lang={profile.primary_language}")

    logger.info("Pass 1: LLM-driven decision discovery...")
    discovery = DiscoveryAgent(llm_client)
    decision_areas = discovery.discover(repo_path, profile, max_decisions=max_decisions)
    logger.info(f"Found {len(decision_areas)} decision areas")

    if not decision_areas:
        logger.warning("No architectural decision areas found")
        return []

    enh_fetcher = EnhancementFetcher()
    if not enh_fetcher.is_available():
        enh_fetcher = None

    jira_client = _try_jira(jira_base_url)

    enricher = Enricher(
        repo_path=repo_path,
        jira_client=jira_client,
        enhancement_fetcher=enh_fetcher,
        repo_owner=profile.owner,
        repo_name=profile.name,
    )
    logger.info("Enriching decision areas with history...")
    enricher.enrich_all(decision_areas)

    logger.info("Pass 2: Generating ADRs with full code context...")
    generator = ADRGenerator(llm_client, output_dir)
    return generator.generate_adrs(decision_areas, profile)


def _try_jira(base_url: str):
    """Try to create a Jira client; return None on failure."""
    try:
        from jira import JIRA

        class _SimpleJiraClient:
            def __init__(self, url):
                self.client = JIRA(server=url)

            def fetch_jira_ticket(self, jira_id):
                try:
                    issue = self.client.issue(jira_id)
                    from .models import DecisionArea  # just for typing reference
                    return type("Ticket", (), {
                        "key": issue.key,
                        "title": issue.fields.summary,
                        "description": issue.fields.description or "",
                    })()
                except Exception:
                    return None

        return _SimpleJiraClient(base_url)
    except Exception as e:
        logger.info(f"Jira client not available: {e}")
        return None
