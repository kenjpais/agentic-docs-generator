"""Pass 1: LLM-driven discovery of architectural decisions from source code."""

import json
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional

from models import DecisionArea, RepoProfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_FILE_CHARS = 8000
MAX_TOTAL_CHARS = 120000


class DiscoveryAgent:
    """Uses an LLM to identify architectural decisions from full source code."""

    def __init__(self, llm_client, prompts_config: Optional[Dict] = None):
        self.llm = llm_client
        self.prompts_config = prompts_config or {}

    def discover(self, repo_path: str, profile: RepoProfile) -> List[DecisionArea]:
        repo = Path(repo_path)
        logger.info(f"Pass 1: Collecting key files from {profile.name}")

        files_content = self._collect_key_files(repo, profile)
        if not files_content:
            logger.warning("No key files found for discovery")
            return []

        total_chars = sum(len(c) for c in files_content.values())
        logger.info(f"Collected {len(files_content)} files ({total_chars} chars) for discovery")

        prompt = self._build_discovery_prompt(files_content, profile)
        logger.info("Sending discovery prompt to LLM...")

        try:
            response = self.llm.generate(prompt)
        except Exception as e:
            logger.error(f"LLM discovery call failed: {e}")
            return []

        areas = self._parse_response(response, repo)
        logger.info(f"Pass 1 discovered {len(areas)} decision areas")
        return areas

    # ------------------------------------------------------------------
    # File collection — language/repo-type aware
    # ------------------------------------------------------------------

    def _collect_key_files(self, repo: Path, profile: RepoProfile) -> Dict[str, str]:
        files: Dict[str, str] = {}
        total = [0]

        def _add(rel_path: str, content: str):
            if not content or total[0] + len(content) > MAX_TOTAL_CHARS:
                return
            truncated = content[:MAX_FILE_CHARS]
            if len(content) > MAX_FILE_CHARS:
                truncated += f"\n// ... truncated ({len(content)} total chars)"
            files[rel_path] = truncated
            total[0] += len(truncated)

        for name in ["README.md", "CONTRIBUTING.md"]:
            p = repo / name
            if p.exists():
                _add(name, self._read(p))

        if profile.primary_language in ("go", "mixed"):
            self._collect_go_files(repo, _add)
        if profile.primary_language in ("python", "mixed"):
            self._collect_python_files(repo, _add)
        if profile.primary_language in ("typescript", "mixed"):
            self._collect_ts_files(repo, _add)

        docs = repo / "docs"
        if docs.is_dir():
            for md in sorted(docs.rglob("*.md"))[:5]:
                rel = str(md.relative_to(repo))
                _add(rel, self._read(md, max_lines=500))

        return files

    def _collect_go_files(self, repo: Path, _add: Callable):
        go_mod = repo / "go.mod"
        if go_mod.exists():
            content = self._read(go_mod)
            _add("go.mod", self._strip_indirect_deps(content))

        for api_dir in ["api", "pkg/apis", "apis"]:
            d = repo / api_dir
            if d.is_dir():
                for f in sorted(d.rglob("*_types.go")):
                    _add(str(f.relative_to(repo)), self._read(f))

        cmd_dir = repo / "cmd"
        if cmd_dir.is_dir():
            for main_go in sorted(cmd_dir.rglob("main.go"))[:3]:
                _add(str(main_go.relative_to(repo)), self._read(main_go))

        for controller_root in ["pkg/controller", "pkg/operator", "pkg/controllers"]:
            d = repo / controller_root
            if not d.is_dir():
                continue
            for subdir in sorted(d.iterdir()):
                if not subdir.is_dir():
                    continue
                ctrl_file = self._find_controller_file(subdir)
                if ctrl_file:
                    _add(str(ctrl_file.relative_to(repo)), self._read(ctrl_file))
                for keyword in ["configmap", "statefulset", "daemonset", "deployment"]:
                    matched = self._find_file_matching(subdir, keyword)
                    if matched:
                        _add(str(matched.relative_to(repo)), self._read(matched))

    def _collect_python_files(self, repo: Path, _add: Callable):
        for name in ["requirements.txt", "pyproject.toml", "setup.py", "setup.cfg"]:
            p = repo / name
            if p.exists():
                _add(name, self._read(p))
        for pattern in ["main.py", "app.py", "cli.py", "models.py", "config.py"]:
            p = repo / pattern
            if p.exists():
                _add(pattern, self._read(p))
        src = repo / "src"
        if src.is_dir():
            for f in sorted(src.rglob("*.py"))[:10]:
                _add(str(f.relative_to(repo)), self._read(f))

    def _collect_ts_files(self, repo: Path, _add: Callable):
        for name in ["package.json", "tsconfig.json"]:
            p = repo / name
            if p.exists():
                _add(name, self._read(p))
        src = repo / "src"
        if src.is_dir():
            for f in sorted(src.rglob("*.ts"))[:10]:
                if "node_modules" not in str(f):
                    _add(str(f.relative_to(repo)), self._read(f))

    # ------------------------------------------------------------------
    # Discovery prompt
    # ------------------------------------------------------------------

    def _build_discovery_prompt(self, files_content: Dict[str, str], profile: RepoProfile) -> str:
        system = (
            f"You are an expert software architect analyzing the source code of an "
            f"OpenShift {profile.repo_type} repository.\n"
            f"Primary language: {profile.primary_language}. "
            f"Category: {profile.openshift_category}.\n\n"
            f"Read ALL the source code below carefully and identify 5-8 significant "
            f"architectural decisions embedded in this codebase.\n\n"
            f"A 'decision' is a DESIGN CHOICE that shapes the architecture — "
            f"NOT a library dependency, NOT a file existing, NOT build tooling.\n\n"
        )

        examples = self._get_decision_examples(profile)

        instructions = (
            f"Examples of real decisions to look for:\n{examples}\n\n"
            f"For each decision, return a JSON array (and NOTHING else — no markdown, "
            f"no explanation, just valid JSON):\n"
            f"[\n"
            f"  {{\n"
            f'    "title": "Specific descriptive title for THIS repo",\n'
            f'    "summary": "2-3 sentences explaining what was decided and why it matters",\n'
            f'    "key_files": ["path/to/file1.go", "path/to/file2.go"],\n'
            f'    "decision_type": "deployment_topology|api_design|controller_coordination|'
            f'security_model|config_generation|operational_pattern|technology_choice|'
            f'abstraction_design|workflow_model"\n'
            f"  }}\n"
            f"]\n\n"
            f"RULES:\n"
            f"- DO NOT list standard framework dependencies (controller-runtime, client-go, "
            f"cobra, library-go, React, Redux) as decisions\n"
            f"- DO NOT list build tooling (Makefile, hack/ scripts, CI config) as decisions\n"
            f"- DO NOT list 'uses Kubernetes' or 'uses OpenShift' as decisions\n"
            f"- Focus on what makes THIS repository's architecture UNIQUE\n"
            f"- Each decision must reference specific files from the source code below\n"
            f"- Return ONLY valid JSON, no other text\n\n"
        )

        code_section = "SOURCE CODE:\n\n"
        for filepath, content in files_content.items():
            code_section += f"=== {filepath} ===\n{content}\n\n"

        return system + instructions + code_section

    @staticmethod
    def _get_decision_examples(profile: RepoProfile) -> str:
        common = (
            "- How the CRD API surface is designed (singleton, scoping, validation, immutability)\n"
            "- What security model is applied (SCCs, RBAC, mutual TLS, attestation)\n"
        )
        if profile.repo_type == "operator":
            return (
                common +
                "- How operands are deployed (StatefulSet vs DaemonSet vs Deployment, sidecar patterns)\n"
                "- How controllers coordinate and report status to the platform\n"
                "- How configuration is generated and delivered to managed components\n"
                "- What operational modes exist (create-only, degraded, upgrade blocking)\n"
                "- How upstream project integration works (vendoring, embedding, wrapping)\n"
            )
        elif profile.repo_type == "library":
            return (
                "- What abstractions are exported and what contracts they enforce\n"
                "- What extension points exist for consumers\n"
                "- What patterns are standardized (factory, builder, observer)\n"
                "- What versioning or compatibility strategy is used\n"
            )
        elif profile.repo_type == "installer":
            return (
                "- What pipeline/workflow model is used for installation\n"
                "- What abstraction layers exist (platform, provider, asset)\n"
                "- What validation and error handling strategy is applied\n"
                "- How multi-cloud/multi-platform support is structured\n"
            )
        elif profile.repo_type == "console":
            return (
                common +
                "- What plugin architecture is used\n"
                "- What state management pattern is applied\n"
                "- What API integration and proxy strategy exists\n"
                "- What component composition model is used\n"
            )
        else:
            return common + "- Any significant structural or design patterns\n"

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(self, response: str, repo: Path) -> List[DecisionArea]:
        response = response.strip()
        if response.startswith("```"):
            lines = response.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response = "\n".join(lines).strip()

        try:
            decisions = json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", response, re.DOTALL)
            if match:
                try:
                    decisions = json.loads(match.group())
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse discovery JSON:\n{response[:500]}")
                    return []
            else:
                logger.error(f"No JSON array in discovery response:\n{response[:500]}")
                return []

        if not isinstance(decisions, list):
            logger.error("Discovery response is not a JSON array")
            return []

        areas = []
        for d in decisions:
            if not isinstance(d, dict) or "title" not in d:
                continue
            key_files = d.get("key_files", [])
            valid_files = [f for f in key_files if (repo / f).exists()]

            areas.append(DecisionArea(
                name=d["title"],
                decision_type=d.get("decision_type", "design_pattern"),
                description=d.get("summary", ""),
                key_files=valid_files if valid_files else key_files[:5],
                significance=8.0,
            ))

        return areas

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read(path: Path, max_lines: int = 0) -> str:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            if max_lines > 0:
                return "\n".join(content.splitlines()[:max_lines])
            return content
        except OSError:
            return ""

    @staticmethod
    def _strip_indirect_deps(go_mod_content: str) -> str:
        return "\n".join(
            line for line in go_mod_content.splitlines()
            if "// indirect" not in line
        )

    @staticmethod
    def _find_controller_file(directory: Path) -> Optional[Path]:
        for name in ["controller.go", "reconciler.go"]:
            f = directory / name
            if f.exists():
                return f
        for f in sorted(directory.glob("*.go")):
            if not f.name.endswith("_test.go"):
                return f
        return None

    @staticmethod
    def _find_file_matching(directory: Path, keyword: str) -> Optional[Path]:
        for f in sorted(directory.glob("*.go")):
            if keyword in f.name.lower() and not f.name.endswith("_test.go"):
                return f
        return None
