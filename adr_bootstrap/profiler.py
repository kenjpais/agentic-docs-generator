"""Auto-detect repository type, primary language, and OpenShift category."""

import os
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Tuple

from .models import RepoProfile
import logging

logger = logging.getLogger(__name__)

SKIP_DIRS = {
    ".git", "vendor", "node_modules", "dist", "build", "_output",
    "__pycache__", ".tox", ".mypy_cache", ".pytest_cache", "venv",
    ".venv", "env", "coverage", ".next", "zz_generated",
}

LANG_EXTENSIONS = {
    ".go": "go", ".py": "python", ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".java": "java",
    ".rb": "ruby", ".rs": "rust", ".c": "c", ".cpp": "cpp", ".sh": "shell",
}


class RepoProfiler:
    """Detects repo type, language, and OpenShift category from the file system."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        if not self.repo_path.is_dir():
            raise ValueError(f"Not a directory: {repo_path}")

    def profile(self) -> RepoProfile:
        logger.info(f"Profiling repository at {self.repo_path}")

        owner, name = self._detect_owner_name()
        lang_counts = self._count_languages()
        primary_lang = self._primary_language(lang_counts)

        has_owners = self._has_file_anywhere("OWNERS")
        has_crd = self._has_crd_files()
        has_go_mod = (self.repo_path / "go.mod").exists()
        has_package_json = (self.repo_path / "package.json").exists()
        has_requirements = (self.repo_path / "requirements.txt").exists()
        has_pyproject = (self.repo_path / "pyproject.toml").exists()

        repo_type = self._detect_repo_type(primary_lang, has_crd)
        os_category = self._detect_openshift_category(repo_type)

        p = RepoProfile(
            path=str(self.repo_path), name=name, owner=owner,
            primary_language=primary_lang, repo_type=repo_type,
            openshift_category=os_category, languages_detected=dict(lang_counts),
            has_owners=has_owners, has_crd=has_crd, has_go_mod=has_go_mod,
            has_package_json=has_package_json, has_requirements_txt=has_requirements,
            has_pyproject_toml=has_pyproject,
        )
        logger.info(f"Profile: lang={primary_lang}, type={repo_type}, category={os_category}")
        return p

    def _count_languages(self) -> Counter:
        counts: Counter = Counter()
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext in LANG_EXTENSIONS:
                    counts[LANG_EXTENSIONS[ext]] += 1
        return counts

    @staticmethod
    def _primary_language(counts: Counter) -> str:
        if not counts:
            return "unknown"
        top = counts.most_common(3)
        if len(top) >= 2 and top[1][1] > top[0][1] * 0.3:
            return "mixed"
        return top[0][0]

    def _detect_repo_type(self, primary_lang: str, has_crd: bool) -> str:
        name_lower = self.repo_path.name.lower()
        if self._has_operator_framework_dep():
            return "operator"
        if self._has_api_types_dir():
            return "operator"
        if has_crd:
            return "operator"
        if self._grep_go("ClusterOperator|config\\.openshift\\.io/v1"):
            return "operator"
        if self._grep_go("OperatorCondition|olm\\.operatorframework\\.io"):
            return "operator"
        if "operator" in name_lower:
            return "operator"
        if "installer" in name_lower or "install" in name_lower:
            return "installer"
        if "console" in name_lower:
            return "console"
        if "library" in name_lower or "client" in name_lower:
            return "library"
        if primary_lang == "typescript" and self._has_react():
            return "console"
        if self._has_cobra_commands():
            return "cli"
        if primary_lang == "go":
            if (self.repo_path / "cmd").is_dir():
                if list((self.repo_path / "cmd").rglob("main.go")):
                    return "cli"
            if (self.repo_path / "pkg").is_dir() and not (self.repo_path / "cmd").is_dir():
                return "library"
        return "unknown"

    def _detect_openshift_category(self, repo_type: str) -> str:
        if repo_type == "operator":
            if self._grep_go("ClusterOperator"):
                return "core_operator"
            if self._grep_go("OperatorCondition"):
                return "ecosystem_operator"
            return "core_operator"
        if repo_type == "library":
            return "library"
        return "unknown"

    def _detect_owner_name(self) -> Tuple[str, str]:
        try:
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=5)
            match = re.search(r"github\.com[:/]([^/]+)/([^/.\s]+)", result.stdout.strip())
            if match:
                return match.group(1), match.group(2)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return "unknown", self.repo_path.name

    def _has_file_anywhere(self, filename: str) -> bool:
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            if filename in files:
                return True
        return False

    def _has_crd_files(self) -> bool:
        try:
            r = subprocess.run(
                ["rg", "kind:\\s*CustomResourceDefinition", str(self.repo_path),
                 "--glob", "*.{yaml,yml}", "--files-with-matches", "--max-count", "1"],
                capture_output=True, text=True, timeout=15)
            return bool(r.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _grep_go(self, pattern: str) -> bool:
        try:
            r = subprocess.run(
                ["rg", pattern, str(self.repo_path),
                 "--glob", "*.go", "--max-count", "1", "--quiet"],
                capture_output=True, timeout=15)
            return r.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _has_react(self) -> bool:
        p = self.repo_path / "package.json"
        if not p.exists():
            return False
        try:
            return '"react"' in p.read_text(encoding="utf-8")
        except OSError:
            return False

    def _has_operator_framework_dep(self) -> bool:
        p = self.repo_path / "go.mod"
        if not p.exists():
            return False
        try:
            c = p.read_text(encoding="utf-8")
            return "operator-framework/api" in c or "operator-framework/operator-sdk" in c
        except OSError:
            return False

    def _has_api_types_dir(self) -> bool:
        for d in ["api", "pkg/apis", "apis"]:
            if (self.repo_path / d).is_dir() and list((self.repo_path / d).rglob("*_types.go")):
                return True
        return False

    def _has_cobra_commands(self) -> bool:
        return self._grep_go("cobra\\.Command")
