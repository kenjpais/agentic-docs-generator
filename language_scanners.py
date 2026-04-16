"""Language-specific code scanners for identifying architectural decisions."""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from models import DecisionArea
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Architecturally significant dependencies per ecosystem
# ---------------------------------------------------------------------------

GO_SIGNIFICANT_DEPS = {
    "github.com/openshift/library-go": "OpenShift shared operator patterns (library-go)",
    "github.com/hashicorp/terraform": "Infrastructure provisioning (Terraform)",
    "github.com/coreos/ignition": "Machine configuration (Ignition)",
    "github.com/containers/podman": "Container runtime (Podman)",
    "sigs.k8s.io/cluster-api": "Cluster API framework",
    "github.com/spiffe/spire": "SPIFFE/SPIRE workload identity",
    "github.com/containernetworking/cni": "Container Network Interface (CNI)",
    "github.com/openshift/machine-config-operator": "Machine Config Operator",
    "github.com/openshift/cluster-version-operator": "Cluster Version Operator",
}

GO_SCAFFOLDING_DEPS = {
    "sigs.k8s.io/controller-runtime",
    "k8s.io/client-go",
    "k8s.io/api",
    "k8s.io/apimachinery",
    "k8s.io/apiextensions-apiserver",
    "k8s.io/kubernetes",
    "k8s.io/kms",
    "github.com/openshift/api",
    "github.com/openshift/client-go",
    "github.com/operator-framework/api",
    "github.com/operator-framework/operator-sdk",
    "github.com/spf13/cobra",
    "github.com/spf13/viper",
    "github.com/prometheus/client_golang",
    "google.golang.org/grpc",
    "google.golang.org/protobuf",
    "go.etcd.io/etcd",
    "github.com/onsi/ginkgo",
    "github.com/onsi/gomega",
    "sigs.k8s.io/controller-tools",
}

MAX_DEPENDENCY_ADRS = 3

PYTHON_SIGNIFICANT_DEPS = {
    "flask": "Web framework (Flask)",
    "fastapi": "Web framework (FastAPI)",
    "django": "Web framework (Django)",
    "sqlalchemy": "ORM / database abstraction",
    "pydantic": "Data validation and settings",
    "google-genai": "Google Gemini AI client",
    "openai": "OpenAI API client",
    "kubernetes": "Kubernetes Python client",
    "jira": "Jira API client",
    "celery": "Distributed task queue",
    "pytest": "Testing framework",
    "click": "CLI framework",
    "typer": "CLI framework",
    "grpcio": "gRPC framework",
    "boto3": "AWS SDK",
    "ansible": "Automation framework",
}

TS_SIGNIFICANT_DEPS = {
    "react": "React UI framework",
    "react-dom": "React DOM rendering",
    "@reduxjs/toolkit": "Redux state management",
    "redux": "State management",
    "@patternfly/react-core": "PatternFly UI components (Red Hat)",
    "@patternfly/react-table": "PatternFly table components",
    "webpack": "Module bundler (Webpack)",
    "vite": "Build tool (Vite)",
    "typescript": "TypeScript language",
    "next": "Next.js framework",
    "express": "Express.js server",
    "axios": "HTTP client",
    "@openshift-console/dynamic-plugin-sdk": "OpenShift Console plugin SDK",
}


def _run_rg(pattern: str, repo_path: Path, *,
            include_glob: str = "", files_only: bool = False,
            context: int = 0, max_count: int = 500) -> str:
    """Run ripgrep and return stdout. Returns empty string on failure."""
    cmd = ["rg", pattern, str(repo_path), "--max-count", str(max_count)]
    if include_glob:
        cmd += ["--glob", include_glob]
    if files_only:
        cmd.append("--files-with-matches")
    if context > 0:
        cmd += ["-C", str(context)]
    cmd += ["--no-heading", "--color", "never"]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


# ---------------------------------------------------------------------------
# Go Scanner
# ---------------------------------------------------------------------------

class GoScanner:
    """Scans Go repositories for architectural patterns."""

    SKIP_DIRS = {"vendor", "hack", "test", "tests", "testdata", "_output", "zz_generated"}

    def scan_abstractions(self, repo_path: Path) -> List[DecisionArea]:
        areas: List[DecisionArea] = []

        interfaces = self._find_interfaces(repo_path)
        for iface_name, iface_file, impl_count in interfaces:
            if impl_count >= 2:
                areas.append(DecisionArea(
                    name=f"{iface_name} abstraction pattern",
                    decision_type="design_pattern",
                    description=f"Interface `{iface_name}` with {impl_count} implementations — strategy/plugin pattern",
                    key_files=[iface_file],
                    evidence={"interface": iface_name, "implementations": str(impl_count)},
                    significance=impl_count * 2.0,
                ))
            elif self._looks_like_api_boundary(iface_file):
                areas.append(DecisionArea(
                    name=f"{iface_name} API boundary",
                    decision_type="api_design",
                    description=f"Interface `{iface_name}` defines an API contract",
                    key_files=[iface_file],
                    evidence={"interface": iface_name},
                    significance=3.0,
                ))
        return areas

    def scan_dependencies(self, repo_path: Path) -> List[DecisionArea]:
        areas: List[DecisionArea] = []
        go_mod = repo_path / "go.mod"
        if not go_mod.exists():
            return areas

        try:
            content = go_mod.read_text(encoding="utf-8")
        except OSError:
            return areas

        in_require = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("require ("):
                in_require = True
                continue
            if stripped == ")":
                in_require = False
                continue

            dep_line = stripped if in_require else ""
            if not dep_line or dep_line.startswith("//"):
                continue

            is_indirect = "// indirect" in dep_line
            if is_indirect:
                continue

            parts = dep_line.split("//")[0].strip().split()
            if not parts:
                continue
            dep_path = parts[0]
            dep_version = parts[1] if len(parts) > 1 else ""

            if any(dep_path.startswith(scaffold) for scaffold in GO_SCAFFOLDING_DEPS):
                continue

            for sig_dep, description in GO_SIGNIFICANT_DEPS.items():
                if dep_path.startswith(sig_dep):
                    areas.append(DecisionArea(
                        name=f"Use {description}",
                        decision_type="technology_choice",
                        description=f"Direct dependency on `{dep_path}` ({dep_version}) — {description}",
                        key_files=["go.mod"],
                        evidence={"dependency": dep_path, "version": dep_version},
                        significance=2.0,
                    ))
                    break

        areas.sort(key=lambda a: a.significance, reverse=True)
        return areas[:MAX_DEPENDENCY_ADRS]

    def scan_comments(self, repo_path: Path) -> List[Dict]:
        results: List[Dict] = []
        patterns = [
            r"//\s*(TODO|HACK|NOTE|FIXME|DECISION|IMPORTANT):",
            r"//.*\b(because|instead of|workaround|trade-?off|decision)\b",
        ]
        for pattern in patterns:
            output = _run_rg(
                pattern, repo_path,
                include_glob="*.go", context=1, max_count=100
            )
            for line in output.splitlines():
                if ":" in line and not any(skip in line for skip in self.SKIP_DIRS):
                    results.append({"raw": line.strip()})
        return results

    # -- helpers --

    def _find_interfaces(self, repo_path: Path) -> List[Tuple[str, str, int]]:
        """Return (name, file, impl_count) for interfaces found."""
        output = _run_rg(
            r"^type\s+(\w+)\s+interface\s*\{", repo_path,
            include_glob="*.go"
        )
        interfaces = []
        seen = set()
        for line in output.splitlines():
            if any(skip in line for skip in self.SKIP_DIRS):
                continue
            match = re.search(r"^(.+?):\s*type\s+(\w+)\s+interface", line)
            if match and match.group(2) not in seen:
                filepath = match.group(1)
                name = match.group(2)
                seen.add(name)
                try:
                    rel = str(Path(filepath).relative_to(repo_path))
                except ValueError:
                    rel = filepath
                impl_count = self._count_implementations(repo_path, name)
                interfaces.append((name, rel, impl_count))
        return interfaces

    def _count_implementations(self, repo_path: Path, interface_name: str) -> int:
        output = _run_rg(
            rf"func\s+\(\w+\s+\*?\w+\)\s+{interface_name[:1]}",
            repo_path, include_glob="*.go", files_only=True
        )
        return len([l for l in output.splitlines() if l.strip()])

    @staticmethod
    def _looks_like_api_boundary(filepath: str) -> bool:
        api_indicators = ["pkg/api", "pkg/types", "api/", "apis/"]
        return any(ind in filepath for ind in api_indicators)


# ---------------------------------------------------------------------------
# Python Scanner
# ---------------------------------------------------------------------------

class PythonScanner:
    """Scans Python repositories for architectural patterns."""

    def scan_abstractions(self, repo_path: Path) -> List[DecisionArea]:
        areas: List[DecisionArea] = []

        output = _run_rg(
            r"^class\s+\w+.*\(.*(?:ABC|Protocol|BaseModel)\s*\)",
            repo_path, include_glob="*.py"
        )
        seen = set()
        for line in output.splitlines():
            match = re.search(r"^(.+?):\s*class\s+(\w+)", line)
            if match and match.group(2) not in seen:
                filepath = match.group(1)
                name = match.group(2)
                seen.add(name)
                try:
                    rel = str(Path(filepath).relative_to(repo_path))
                except ValueError:
                    rel = filepath
                areas.append(DecisionArea(
                    name=f"{name} abstraction",
                    decision_type="design_pattern",
                    description=f"Abstract base / protocol `{name}` defines an extension point",
                    key_files=[rel],
                    evidence={"class": name},
                    significance=3.0,
                ))
        return areas

    def scan_dependencies(self, repo_path: Path) -> List[DecisionArea]:
        areas: List[DecisionArea] = []

        for dep_file in ["requirements.txt", "requirements-dev.txt"]:
            path = repo_path / dep_file
            if not path.exists():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for line in content.splitlines():
                dep = re.split(r"[><=!~\[]", line.strip())[0].strip().lower()
                if dep in PYTHON_SIGNIFICANT_DEPS:
                    areas.append(DecisionArea(
                        name=f"Use {PYTHON_SIGNIFICANT_DEPS[dep]}",
                        decision_type="technology_choice",
                        description=f"Dependency on `{dep}` — {PYTHON_SIGNIFICANT_DEPS[dep]}",
                        key_files=[dep_file],
                        evidence={"dependency": dep, "source": dep_file},
                        significance=4.0,
                    ))

        pyproject = repo_path / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8")
                for dep, desc in PYTHON_SIGNIFICANT_DEPS.items():
                    if dep in content.lower():
                        areas.append(DecisionArea(
                            name=f"Use {desc}",
                            decision_type="technology_choice",
                            description=f"Dependency on `{dep}` — {desc}",
                            key_files=["pyproject.toml"],
                            evidence={"dependency": dep, "source": "pyproject.toml"},
                            significance=4.0,
                        ))
            except OSError:
                pass

        return areas

    def scan_comments(self, repo_path: Path) -> List[Dict]:
        results: List[Dict] = []
        output = _run_rg(
            r"#\s*(TODO|HACK|NOTE|FIXME|DECISION|IMPORTANT):",
            repo_path, include_glob="*.py", context=1, max_count=100
        )
        for line in output.splitlines():
            if ":" in line:
                results.append({"raw": line.strip()})
        return results


# ---------------------------------------------------------------------------
# TypeScript Scanner
# ---------------------------------------------------------------------------

class TypeScriptScanner:
    """Scans TypeScript/JavaScript repositories for architectural patterns."""

    SKIP_DIRS = {"node_modules", "dist", "build", ".next", "coverage"}

    def scan_abstractions(self, repo_path: Path) -> List[DecisionArea]:
        areas: List[DecisionArea] = []

        output = _run_rg(
            r"export\s+(interface|abstract\s+class|type)\s+\w+",
            repo_path, include_glob="*.{ts,tsx}"
        )
        seen = set()
        for line in output.splitlines():
            if any(skip in line for skip in self.SKIP_DIRS):
                continue
            match = re.search(r"^(.+?):\s*export\s+(?:interface|abstract\s+class|type)\s+(\w+)", line)
            if match and match.group(2) not in seen:
                filepath = match.group(1)
                name = match.group(2)
                seen.add(name)
                try:
                    rel = str(Path(filepath).relative_to(repo_path))
                except ValueError:
                    rel = filepath
                areas.append(DecisionArea(
                    name=f"{name} type contract",
                    decision_type="design_pattern",
                    description=f"Exported type/interface `{name}` defines a contract boundary",
                    key_files=[rel],
                    evidence={"type": name},
                    significance=2.0,
                ))
        return areas

    def scan_dependencies(self, repo_path: Path) -> List[DecisionArea]:
        areas: List[DecisionArea] = []
        pkg_json = repo_path / "package.json"
        if not pkg_json.exists():
            return areas

        try:
            import json
            content = json.loads(pkg_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return areas

        all_deps = {}
        all_deps.update(content.get("dependencies", {}))
        all_deps.update(content.get("devDependencies", {}))

        for dep, version in all_deps.items():
            if dep in TS_SIGNIFICANT_DEPS:
                areas.append(DecisionArea(
                    name=f"Use {TS_SIGNIFICANT_DEPS[dep]}",
                    decision_type="technology_choice",
                    description=f"Dependency on `{dep}` ({version}) — {TS_SIGNIFICANT_DEPS[dep]}",
                    key_files=["package.json"],
                    evidence={"dependency": dep, "version": version},
                    significance=4.0,
                ))
        return areas

    def scan_comments(self, repo_path: Path) -> List[Dict]:
        results: List[Dict] = []
        output = _run_rg(
            r"//\s*(TODO|HACK|NOTE|FIXME|DECISION|IMPORTANT):",
            repo_path, include_glob="*.{ts,tsx,js,jsx}",
            context=1, max_count=100
        )
        for line in output.splitlines():
            if any(skip in line for skip in self.SKIP_DIRS):
                continue
            if ":" in line:
                results.append({"raw": line.strip()})
        return results


# ---------------------------------------------------------------------------
# YAML Scanner (runs for all repo types)
# ---------------------------------------------------------------------------

class YAMLScanner:
    """Scans YAML files for CRDs, Kustomize, Helm, and CI patterns."""

    def scan_crds(self, repo_path: Path) -> List[DecisionArea]:
        areas: List[DecisionArea] = []

        output = _run_rg(
            r"kind:\s*CustomResourceDefinition",
            repo_path, include_glob="*.{yaml,yml}", files_only=True
        )
        for filepath in output.splitlines():
            filepath = filepath.strip()
            if not filepath:
                continue
            try:
                rel = str(Path(filepath).relative_to(repo_path))
            except ValueError:
                rel = filepath

            crd_name = self._extract_crd_name(Path(filepath))
            areas.append(DecisionArea(
                name=f"CRD: {crd_name}" if crd_name else f"Custom Resource Definition in {rel}",
                decision_type="api_design",
                description=f"Defines CRD `{crd_name or 'unknown'}` — custom API extension",
                key_files=[rel],
                evidence={"crd_name": crd_name or "unknown", "file": rel},
                significance=5.0,
            ))
        return areas

    def scan_deployment_patterns(self, repo_path: Path) -> List[DecisionArea]:
        areas: List[DecisionArea] = []

        kustomization = repo_path / "config" / "kustomization.yaml"
        if not kustomization.exists():
            kustomization = repo_path / "kustomization.yaml"
        if kustomization.exists():
            areas.append(DecisionArea(
                name="Kustomize for deployment configuration",
                decision_type="operational",
                description="Uses Kustomize for managing deployment manifests",
                key_files=[str(kustomization.relative_to(repo_path))],
                evidence={"tool": "kustomize"},
                significance=2.0,
            ))

        for helm_indicator in ["Chart.yaml", "charts/"]:
            matches = list(repo_path.glob(f"**/{helm_indicator}"))
            if matches:
                areas.append(DecisionArea(
                    name="Helm charts for deployment",
                    decision_type="operational",
                    description="Uses Helm charts for packaging and deployment",
                    key_files=[str(m.relative_to(repo_path)) for m in matches[:3]],
                    evidence={"tool": "helm"},
                    significance=2.0,
                ))
                break

        return areas

    def scan_ci_patterns(self, repo_path: Path) -> List[DecisionArea]:
        areas: List[DecisionArea] = []

        makefile = repo_path / "Makefile"
        if makefile.exists():
            try:
                content = makefile.read_text(encoding="utf-8", errors="replace")
                targets = re.findall(r"^([a-zA-Z_][\w-]*):", content, re.MULTILINE)
                if targets:
                    areas.append(DecisionArea(
                        name="Makefile-based build system",
                        decision_type="operational",
                        description=f"Build orchestrated via Makefile with {len(targets)} targets",
                        key_files=["Makefile"],
                        evidence={"targets": ", ".join(targets[:10])},
                        significance=2.0,
                    ))
            except OSError:
                pass

        hack_dir = repo_path / "hack"
        if hack_dir.is_dir():
            scripts = list(hack_dir.glob("*.sh")) + list(hack_dir.glob("*.py"))
            if scripts:
                areas.append(DecisionArea(
                    name="hack/ scripts for validation and tooling",
                    decision_type="constraint",
                    description=f"{len(scripts)} scripts in hack/ enforce conventions and run validations",
                    key_files=[str(s.relative_to(repo_path)) for s in scripts[:5]],
                    evidence={"script_count": str(len(scripts))},
                    significance=2.0,
                ))

        return areas

    @staticmethod
    def _extract_crd_name(filepath: Path) -> Optional[str]:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
            match = re.search(r"name:\s*(\S+\.[\w.]+)", content)
            if match:
                return match.group(1)
        except OSError:
            pass
        return None
