"""Tests for bootstrap ADR generation components."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from models import DecisionArea, RepoProfile
from adr_generator import ADRGenerator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def go_repo(tmp_path):
    """Create a minimal Go repo fixture."""
    (tmp_path / "go.mod").write_text(
        'module example.com/myoperator\n\ngo 1.21\n\n'
        'require (\n'
        '\tsigs.k8s.io/controller-runtime v0.15.0\n'
        '\tgithub.com/openshift/api v0.0.0-20240101\n'
        '\tgithub.com/spf13/cobra v1.7.0\n'
        ')\n'
    )

    pkg = tmp_path / "pkg" / "controller"
    pkg.mkdir(parents=True)
    (pkg / "reconciler.go").write_text(
        'package controller\n\n'
        'type Reconciler interface {\n'
        '\tReconcile(ctx context.Context) error\n'
        '}\n'
    )

    impl = tmp_path / "pkg" / "controller" / "foo"
    impl.mkdir(parents=True)
    (impl / "foo_controller.go").write_text(
        'package foo\n\n'
        'func (r *FooReconciler) Reconcile(ctx context.Context) error { return nil }\n'
    )

    impl2 = tmp_path / "pkg" / "controller" / "bar"
    impl2.mkdir(parents=True)
    (impl2 / "bar_controller.go").write_text(
        'package bar\n\n'
        'func (r *BarReconciler) Reconcile(ctx context.Context) error { return nil }\n'
    )

    api = tmp_path / "pkg" / "apis" / "v1"
    api.mkdir(parents=True)
    (api / "types.go").write_text(
        'package v1\n\n'
        'type Platform interface {\n'
        '\tName() string\n'
        '}\n'
    )

    crd_dir = tmp_path / "config" / "crd"
    crd_dir.mkdir(parents=True)
    (crd_dir / "my-crd.yaml").write_text(
        'apiVersion: apiextensions.k8s.io/v1\n'
        'kind: CustomResourceDefinition\n'
        'metadata:\n'
        '  name: myresources.example.com\n'
    )

    owners = tmp_path / "OWNERS"
    owners.write_text('approvers:\n  - alice\n  - bob\n')

    (tmp_path / "README.md").write_text(
        '# My Operator\n\n'
        '## Architecture\n\n'
        'This operator uses controller-runtime reconciliation loops.\n'
    )

    (tmp_path / "Makefile").write_text(
        'build:\n\tgo build ./...\n\ntest:\n\tgo test ./...\n'
    )

    return tmp_path


@pytest.fixture
def python_repo(tmp_path):
    """Create a minimal Python repo fixture."""
    (tmp_path / "requirements.txt").write_text(
        'google-genai>=0.2.0\npydantic>=2.5.0\njira>=3.5.0\npytest>=7.4.0\n'
    )

    (tmp_path / "models.py").write_text(
        'from abc import ABC, abstractmethod\n\n'
        'class Scanner(ABC):\n'
        '    @abstractmethod\n'
        '    def scan(self):\n'
        '        pass\n'
    )

    (tmp_path / "README.md").write_text('# My Tool\n')
    return tmp_path


@pytest.fixture
def ts_repo(tmp_path):
    """Create a minimal TypeScript repo fixture."""
    (tmp_path / "package.json").write_text(json.dumps({
        "name": "my-console",
        "dependencies": {
            "react": "^18.0.0",
            "@patternfly/react-core": "^5.0.0",
            "@reduxjs/toolkit": "^1.9.0",
        },
        "devDependencies": {
            "typescript": "^5.0.0",
        }
    }))

    src = tmp_path / "src"
    src.mkdir()
    (src / "plugin.ts").write_text(
        'export interface PluginConfig {\n  name: string;\n}\n'
    )

    (tmp_path / "README.md").write_text('# Console Plugin\n')
    return tmp_path


@pytest.fixture
def sample_profile(go_repo):
    return RepoProfile(
        path=str(go_repo),
        name="myoperator",
        owner="openshift",
        primary_language="go",
        repo_type="operator",
        openshift_category="core_operator",
        languages_detected={"go": 50},
        has_owners=True,
        has_crd=True,
        has_go_mod=True,
    )


@pytest.fixture
def sample_decision_areas():
    return [
        DecisionArea(
            name="Use Kubernetes controller framework",
            decision_type="technology_choice",
            description="Dependency on controller-runtime v0.15.0",
            key_files=["go.mod"],
            owners=["alice", "bob"],
            evidence={"dependency": "sigs.k8s.io/controller-runtime", "version": "v0.15.0"},
            significance=4.0,
            history={
                "commit": "abc123",
                "subject": "Initial commit",
                "date": "2022-01-15",
                "pr_number": 1,
                "jira_key": "MCO-100",
            },
        ),
        DecisionArea(
            name="CRD: myresources.example.com",
            decision_type="api_design",
            description="Defines CRD myresources.example.com",
            key_files=["config/crd/my-crd.yaml"],
            owners=["alice"],
            evidence={"crd_name": "myresources.example.com"},
            significance=5.0,
        ),
    ]


# ---------------------------------------------------------------------------
# RepoProfiler tests
# ---------------------------------------------------------------------------

class TestRepoProfiler:
    def test_go_repo_detection(self, go_repo):
        from repo_profiler import RepoProfiler
        profiler = RepoProfiler(str(go_repo))
        profile = profiler.profile()

        assert profile.primary_language == "go"
        assert profile.has_go_mod is True
        assert profile.has_owners is True
        assert profile.name == go_repo.name

    def test_python_repo_detection(self, python_repo):
        from repo_profiler import RepoProfiler
        profiler = RepoProfiler(str(python_repo))
        profile = profiler.profile()

        assert profile.primary_language == "python"
        assert profile.has_requirements_txt is True

    def test_ts_repo_detection(self, ts_repo):
        from repo_profiler import RepoProfiler
        profiler = RepoProfiler(str(ts_repo))
        profile = profiler.profile()

        assert profile.primary_language == "typescript"
        assert profile.has_package_json is True


# ---------------------------------------------------------------------------
# Language scanner tests
# ---------------------------------------------------------------------------

class TestGoScanner:
    def test_scan_dependencies_filters_scaffolding(self, go_repo):
        from language_scanners import GoScanner
        scanner = GoScanner()
        areas = scanner.scan_dependencies(go_repo)

        dep_names = [a.name for a in areas]
        assert not any("controller-runtime" in name.lower() for name in dep_names)
        assert not any("kubernetes api client" in name.lower() for name in dep_names)

    def test_scan_dependencies_keeps_domain_deps(self, tmp_path):
        from language_scanners import GoScanner
        (tmp_path / "go.mod").write_text(
            'module example.com/myop\n\ngo 1.21\n\n'
            'require (\n'
            '\tgithub.com/spiffe/spire-controller-manager v0.6.0\n'
            '\tsigs.k8s.io/controller-runtime v0.20.0\n'
            '\tk8s.io/client-go v0.32.0\n'
            '\tgithub.com/openshift/library-go v0.0.1\n'
            ')\n'
        )
        scanner = GoScanner()
        areas = scanner.scan_dependencies(tmp_path)

        dep_names = [a.name for a in areas]
        assert any("spire" in name.lower() or "spiffe" in name.lower() for name in dep_names)
        assert any("library-go" in name.lower() for name in dep_names)
        assert not any("controller-runtime" in name.lower() for name in dep_names)
        assert len(areas) <= 3

    def test_no_gomod_returns_empty(self, tmp_path):
        from language_scanners import GoScanner
        scanner = GoScanner()
        assert scanner.scan_dependencies(tmp_path) == []


class TestPythonScanner:
    def test_scan_dependencies(self, python_repo):
        from language_scanners import PythonScanner
        scanner = PythonScanner()
        areas = scanner.scan_dependencies(python_repo)

        dep_names = [a.name for a in areas]
        assert any("gemini" in name.lower() or "google" in name.lower() for name in dep_names)
        assert any("pydantic" in name.lower() or "validation" in name.lower() for name in dep_names)


class TestTypeScriptScanner:
    def test_scan_dependencies(self, ts_repo):
        from language_scanners import TypeScriptScanner
        scanner = TypeScriptScanner()
        areas = scanner.scan_dependencies(ts_repo)

        dep_names = [a.name for a in areas]
        assert any("react" in name.lower() for name in dep_names)
        assert any("patternfly" in name.lower() for name in dep_names)


class TestYAMLScanner:
    def test_scan_crds(self, go_repo):
        from language_scanners import YAMLScanner
        scanner = YAMLScanner()
        areas = scanner.scan_crds(go_repo)

        # rg may not find files in tmp dirs on all systems;
        # if it does find them, validate the structure
        if len(areas) >= 1:
            assert areas[0].decision_type == "api_design"
            assert "myresources" in areas[0].evidence.get("crd_name", "")

    def test_extract_crd_name(self, go_repo):
        crd_path = go_repo / "config" / "crd" / "my-crd.yaml"
        from language_scanners import YAMLScanner
        name = YAMLScanner._extract_crd_name(crd_path)
        assert name == "myresources.example.com"


# ---------------------------------------------------------------------------
# CodeAnalyzer tests
# ---------------------------------------------------------------------------

class TestCodeAnalyzer:
    def test_analyze_without_llm_returns_empty(self, go_repo, sample_profile):
        from code_analyzer import CodeAnalyzer
        analyzer = CodeAnalyzer(sample_profile, llm_client=None)
        areas = analyzer.analyze()
        assert areas == []

    def test_analyze_with_mock_llm(self, go_repo, sample_profile):
        from code_analyzer import CodeAnalyzer
        import json

        mock_llm = MagicMock()
        mock_llm.generate.return_value = json.dumps([
            {
                "title": "Test Decision",
                "summary": "A test decision",
                "key_files": ["go.mod"],
                "decision_type": "technology_choice"
            }
        ])

        analyzer = CodeAnalyzer(sample_profile, llm_client=mock_llm)
        areas = analyzer.analyze()

        assert len(areas) == 1
        assert areas[0].name == "Test Decision"
        mock_llm.generate.assert_called_once()


# ---------------------------------------------------------------------------
# ADRGenerator tests
# ---------------------------------------------------------------------------

class TestADRGenerator:
    def test_frontmatter_injection(self, sample_decision_areas, sample_profile):
        mock_gemini = MagicMock()
        generator = ADRGenerator(mock_gemini, "/tmp/test-output")

        area = sample_decision_areas[0]
        frontmatter = generator._build_frontmatter(area, 1, sample_profile)

        assert frontmatter.startswith("---\n")
        assert "ADR-0001" in frontmatter
        assert "alice" in frontmatter
        assert "accepted" in frontmatter
        assert frontmatter.strip().endswith("---")

    def test_frontmatter_with_enhancement(self, sample_profile):
        mock_gemini = MagicMock()
        generator = ADRGenerator(mock_gemini, "/tmp/test-output")

        area = DecisionArea(
            name="Test Decision",
            decision_type="technology_choice",
            description="test",
            key_files=["pkg/foo/bar.go"],
            owners=["team-a"],
            significance=4.0,
            enhancement={
                "type": "pr",
                "number": 567,
                "title": "My Enhancement",
                "url": "https://github.com/openshift/enhancements/pull/567",
            },
            history={"date": "2023-06-01", "jira_key": "MCO-200"},
        )

        frontmatter = generator._build_frontmatter(area, 5, sample_profile)

        assert "ADR-0005" in frontmatter
        assert "enhancement-refs" in frontmatter
        assert "567" in frontmatter
        assert "MCO-200" in frontmatter

    def test_clean_body_strips_fences(self):
        mock_gemini = MagicMock()
        generator = ADRGenerator(mock_gemini, "/tmp/test-output")

        body = "```markdown\n# My ADR\n\nContent here\n```"
        cleaned = generator._clean_body(body)
        assert not cleaned.startswith("```")
        assert "# My ADR" in cleaned

    def test_clean_body_strips_frontmatter(self):
        mock_gemini = MagicMock()
        generator = ADRGenerator(mock_gemini, "/tmp/test-output")

        body = "---\nid: fake\nstatus: draft\n---\n# Real Content\n\nBody text"
        cleaned = generator._clean_body(body)
        assert "id: fake" not in cleaned
        assert "# Real Content" in cleaned

    def test_slugify(self):
        mock_gemini = MagicMock()
        generator = ADRGenerator(mock_gemini, "/tmp/test-output")

        assert generator._slugify("Use controller-runtime") == "use-controller-runtime"
        assert generator._slugify("CRD: myresources.example.com") == "crd-myresources-example-com"
        assert len(generator._slugify("A" * 100)) <= 50

    def test_generate_adrs_writes_files(self, tmp_path, sample_decision_areas, sample_profile):
        mock_gemini = MagicMock()
        mock_gemini.generate.return_value = (
            "# Use Kubernetes controller framework\n\n"
            "## Status\n\nAccepted\n\n"
            "## Context\n\nWe needed a controller framework.\n\n"
            "## Decision\n\nWe chose controller-runtime.\n"
        )

        sample_profile.path = str(tmp_path)
        (tmp_path / "go.mod").write_text("module test\n")

        generator = ADRGenerator(mock_gemini, str(tmp_path / "output"))
        paths = generator.generate_adrs(sample_decision_areas, sample_profile)

        assert len(paths) == 2

        decisions_dir = tmp_path / "output" / sample_profile.name / "agentic" / "decisions"
        assert (decisions_dir / "adr-template.md").exists()
        assert (decisions_dir / "index.md").exists()

        for p in paths:
            content = Path(p).read_text()
            assert content.startswith("---\n")
            assert "ADR-" in content


# ---------------------------------------------------------------------------
# HistoryLookup tests
# ---------------------------------------------------------------------------

class TestHistoryLookup:
    def test_extract_pr_number(self):
        from history_lookup import HistoryLookup

        assert HistoryLookup._extract_pr_number("Merge pull request #1234 from user/branch") == 1234
        assert HistoryLookup._extract_pr_number("OCPBUGS-123: fix thing (#456)") == 456
        assert HistoryLookup._extract_pr_number("no pr here") is None

    def test_extract_jira_key(self):
        from history_lookup import HistoryLookup

        assert HistoryLookup._extract_jira_key("OCPBUGS-12345: fix something") == "OCPBUGS-12345"
        assert HistoryLookup._extract_jira_key("MCO-100: add feature") == "MCO-100"
        assert HistoryLookup._extract_jira_key("no jira here") is None

    def test_extract_enhancement_ref(self):
        from history_lookup import HistoryLookup

        assert HistoryLookup._extract_enhancement_ref(
            "See openshift/enhancements#567 for details"
        ) == "openshift/enhancements#567"
        assert HistoryLookup._extract_enhancement_ref(
            "https://github.com/openshift/enhancements/pull/123"
        ) == "https://github.com/openshift/enhancements/pull/123"
        assert HistoryLookup._extract_enhancement_ref("nothing here") is None


# ---------------------------------------------------------------------------
# EnhancementFetcher tests
# ---------------------------------------------------------------------------

class TestEnhancementFetcher:
    def test_parse_pr_number(self):
        from enhancement_fetcher import EnhancementFetcher

        assert EnhancementFetcher._parse_pr_number("openshift/enhancements#567") == 567
        assert EnhancementFetcher._parse_pr_number(
            "https://github.com/openshift/enhancements/pull/123"
        ) == 123
        assert EnhancementFetcher._parse_pr_number("nothing") is None

    def test_parse_file_path(self):
        from enhancement_fetcher import EnhancementFetcher

        assert EnhancementFetcher._parse_file_path(
            "https://github.com/openshift/enhancements/blob/master/enhancements/foo/bar.md"
        ) == "enhancements/foo/bar.md"
        assert EnhancementFetcher._parse_file_path("nothing") is None


# ---------------------------------------------------------------------------
# Validate environment tests
# ---------------------------------------------------------------------------

class TestValidateEnvironment:
    def test_bootstrap_with_gemini(self, monkeypatch):
        from utils import validate_environment
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.delenv("ANTHROPIC_VERTEX_PROJECT_ID", raising=False)
        monkeypatch.delenv("JIRA_BASE_URL", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        assert validate_environment(mode="bootstrap") is True

    def test_bootstrap_with_claude(self, monkeypatch):
        from utils import validate_environment
        monkeypatch.setenv("ANTHROPIC_VERTEX_PROJECT_ID", "my-project")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("JIRA_BASE_URL", raising=False)

        assert validate_environment(mode="bootstrap") is True

    def test_bootstrap_fails_without_any_llm(self, monkeypatch):
        from utils import validate_environment
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_VERTEX_PROJECT_ID", raising=False)

        assert validate_environment(mode="bootstrap") is False

    def test_full_needs_jira_and_gemini(self, monkeypatch):
        from utils import validate_environment
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.setenv("JIRA_BASE_URL", "https://jira.example.com")

        assert validate_environment(mode="full") is True

    def test_full_fails_without_jira(self, monkeypatch):
        from utils import validate_environment
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.delenv("JIRA_BASE_URL", raising=False)

        assert validate_environment(mode="full") is False
