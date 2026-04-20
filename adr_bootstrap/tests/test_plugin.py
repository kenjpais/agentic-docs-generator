"""Tests for the adr_bootstrap plugin."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from adr_bootstrap.models import DecisionArea, RepoProfile
from adr_bootstrap.generator import ADRGenerator
from adr_bootstrap.enrichment import EnhancementFetcher, Enricher
from adr_bootstrap.discovery import DiscoveryAgent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_profile(tmp_path):
    return RepoProfile(
        path=str(tmp_path), name="myoperator", owner="openshift",
        primary_language="go", repo_type="operator",
        openshift_category="core_operator",
        languages_detected={"go": 50}, has_owners=True, has_go_mod=True,
    )


@pytest.fixture
def sample_areas():
    return [
        DecisionArea(
            name="Test Decision One",
            decision_type="api_design",
            description="A test decision",
            key_files=["api/v1alpha1/types.go"],
            owners=["alice", "bob"],
            significance=8.0,
            history={"date": "2025-01-01", "jira_key": "TEST-1", "subject": "init"},
        ),
        DecisionArea(
            name="Test Decision Two",
            decision_type="deployment_topology",
            description="Another decision",
            key_files=["pkg/controller/foo/controller.go"],
            significance=8.0,
        ),
    ]


# ---------------------------------------------------------------------------
# ADRGenerator tests
# ---------------------------------------------------------------------------

class TestADRGenerator:
    def test_frontmatter_injection(self, sample_areas, sample_profile):
        gen = ADRGenerator(MagicMock(), "/tmp/out")
        fm = gen._build_frontmatter(sample_areas[0], 1, sample_profile)

        assert fm.startswith("---\n")
        assert "ADR-0001" in fm
        assert "alice" in fm
        assert "accepted" in fm
        assert fm.strip().endswith("---")

    def test_frontmatter_with_enhancement(self, sample_profile):
        area = DecisionArea(
            name="Enhanced Decision", decision_type="technology_choice",
            description="test", key_files=["pkg/foo/bar.go"],
            owners=["team-a"], significance=8.0,
            enhancement={"type": "pr", "number": 567,
                         "title": "My Enhancement",
                         "url": "https://github.com/openshift/enhancements/pull/567"},
            history={"date": "2023-06-01", "jira_key": "MCO-200"},
        )
        gen = ADRGenerator(MagicMock(), "/tmp/out")
        fm = gen._build_frontmatter(area, 5, sample_profile)

        assert "ADR-0005" in fm
        assert "enhancement-refs" in fm
        assert "567" in fm

    def test_clean_body_strips_fences(self):
        gen = ADRGenerator(MagicMock(), "/tmp/out")
        assert "# My ADR" in gen._clean_body("```markdown\n# My ADR\nContent\n```")

    def test_clean_body_strips_frontmatter(self):
        gen = ADRGenerator(MagicMock(), "/tmp/out")
        cleaned = gen._clean_body("---\nid: fake\n---\n# Real Content\nBody")
        assert "id: fake" not in cleaned
        assert "# Real Content" in cleaned

    def test_slugify(self):
        gen = ADRGenerator(MagicMock(), "/tmp/out")
        assert gen._slugify("Use controller-runtime") == "use-controller-runtime"
        assert len(gen._slugify("A" * 100)) <= 50

    def test_generate_adrs_writes_files(self, tmp_path, sample_areas, sample_profile):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = (
            "# Test Decision\n\n## Executive Summary\nA test.\n\n"
            "## What\nSomething.\n\n## Why\nBecause.\n"
        )
        sample_profile.path = str(tmp_path)
        (tmp_path / "api" / "v1alpha1").mkdir(parents=True)
        (tmp_path / "api" / "v1alpha1" / "types.go").write_text("package v1alpha1\n")

        gen = ADRGenerator(mock_llm, str(tmp_path / "output"))
        paths = gen.generate_adrs(sample_areas, sample_profile)

        assert len(paths) == 2
        decisions_dir = tmp_path / "output" / sample_profile.name / "agentic" / "decisions"
        assert (decisions_dir / "adr-template.md").exists()
        assert (decisions_dir / "index.md").exists()
        for p in paths:
            content = Path(p).read_text()
            assert content.startswith("---\n")
            assert "ADR-" in content


# ---------------------------------------------------------------------------
# Discovery tests
# ---------------------------------------------------------------------------

class TestDiscovery:
    def test_discover_with_mock_llm(self, tmp_path, sample_profile):
        sample_profile.path = str(tmp_path)
        (tmp_path / "go.mod").write_text("module test\n")
        (tmp_path / "README.md").write_text("# Test\n")

        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps([
            {"title": "Test Decision", "summary": "A decision",
             "key_files": ["go.mod"], "decision_type": "technology_choice"}
        ])

        agent = DiscoveryAgent(mock_llm)
        areas = agent.discover(str(tmp_path), sample_profile)

        assert len(areas) == 1
        assert areas[0].name == "Test Decision"
        mock_llm.generate.assert_called_once()

    def test_discover_handles_bad_json(self, tmp_path, sample_profile):
        sample_profile.path = str(tmp_path)
        (tmp_path / "README.md").write_text("# Test\n")

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "This is not JSON at all"

        agent = DiscoveryAgent(mock_llm)
        areas = agent.discover(str(tmp_path), sample_profile)
        assert areas == []


# ---------------------------------------------------------------------------
# Enrichment tests
# ---------------------------------------------------------------------------

class TestEnrichment:
    def test_extract_pr_number(self):
        assert Enricher._extract_pr_number("Merge pull request #1234 from user/branch") == 1234
        assert Enricher._extract_pr_number("OCPBUGS-123: fix (#456)") == 456
        assert Enricher._extract_pr_number("no pr here") is None

    def test_extract_jira_key(self):
        assert Enricher._extract_jira_key("OCPBUGS-12345: fix") == "OCPBUGS-12345"
        assert Enricher._extract_jira_key("no jira") is None

    def test_extract_enhancement_ref(self):
        assert Enricher._extract_enhancement_ref(
            "See openshift/enhancements#567"
        ) == "openshift/enhancements#567"
        assert Enricher._extract_enhancement_ref("nothing") is None


class TestEnhancementFetcher:
    def test_parse_pr_number(self):
        assert EnhancementFetcher._parse_pr_number("openshift/enhancements#567") == 567
        assert EnhancementFetcher._parse_pr_number("nothing") is None

    def test_parse_file_path(self):
        assert EnhancementFetcher._parse_file_path(
            "https://github.com/openshift/enhancements/blob/master/enhancements/foo/bar.md"
        ) == "enhancements/foo/bar.md"


# ---------------------------------------------------------------------------
# Plugin interface test
# ---------------------------------------------------------------------------

class TestPluginInterface:
    def test_generate_adrs_function_exists(self):
        from adr_bootstrap import generate_adrs
        assert callable(generate_adrs)


# ---------------------------------------------------------------------------
# Environment validation tests
# ---------------------------------------------------------------------------

class TestValidateEnvironment:
    def test_bootstrap_with_gemini(self, monkeypatch):
        from utils import validate_environment
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.delenv("ANTHROPIC_VERTEX_PROJECT_ID", raising=False)
        assert validate_environment(mode="bootstrap") is True

    def test_bootstrap_with_claude(self, monkeypatch):
        from utils import validate_environment
        monkeypatch.setenv("ANTHROPIC_VERTEX_PROJECT_ID", "my-project")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        assert validate_environment(mode="bootstrap") is True

    def test_bootstrap_fails_without_any_llm(self, monkeypatch):
        from utils import validate_environment
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_VERTEX_PROJECT_ID", raising=False)
        assert validate_environment(mode="bootstrap") is False
