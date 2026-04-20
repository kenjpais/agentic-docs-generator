"""Pass 2: Generate ADR markdown files from DecisionAreas with full code context."""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import DecisionArea, RepoProfile
from .prompts import build_adr_prompt, ADR_TEMPLATE_CONTENT
import logging

logger = logging.getLogger(__name__)

MAX_FILES_PER_ADR = 8
MAX_FILE_CHARS = 10000
MAX_TOTAL_CONTEXT_CHARS = 50000


class ADRGenerator:
    """Generates ADR files from DecisionArea objects."""

    def __init__(self, llm_client, output_dir: str = "output"):
        self.llm = llm_client
        self.output_dir = Path(output_dir)

    def generate_adrs(self, decision_areas: List[DecisionArea],
                      profile: RepoProfile) -> List[str]:
        repo_dir = self.output_dir / profile.name / "agentic" / "decisions"
        repo_dir.mkdir(parents=True, exist_ok=True)

        generated: List[str] = []
        self._write_adr_template(repo_dir)

        for idx, area in enumerate(decision_areas, start=1):
            path = self._generate_one(area, idx, profile, repo_dir)
            if path:
                generated.append(str(path))

        self._write_index(repo_dir, generated)
        logger.info(f"Generated {len(generated)} ADRs in {repo_dir}")
        return generated

    # ------------------------------------------------------------------
    # Single ADR
    # ------------------------------------------------------------------

    def _generate_one(self, area: DecisionArea, num: int,
                      profile: RepoProfile, out_dir: Path) -> Optional[Path]:
        try:
            logger.info(f"Generating ADR-{num:04d}: {area.name}")
            context = self._build_context(area, profile)
            prompt = build_adr_prompt(context)
            body = self.llm.generate(prompt)

            if not body or len(body) < 80:
                logger.warning(f"ADR body too short for {area.name}, skipping")
                return None

            body = self._clean_body(body)
            frontmatter = self._build_frontmatter(area, num, profile)
            slug = self._slugify(area.name)
            filepath = out_dir / f"adr-{num:04d}-{slug}.md"
            filepath.write_text(frontmatter + body, encoding="utf-8")
            logger.info(f"Wrote {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to generate ADR for {area.name}: {e}")
            return None

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------

    def _build_context(self, area: DecisionArea, profile: RepoProfile) -> Dict:
        history = area.history or {}
        evidence_lines = [f"- {k}: {v}" for k, v in area.evidence.items()]
        code = self._read_full_files(area, Path(profile.path))

        enh_summary = ""
        if area.enhancement:
            enh = area.enhancement
            enh_summary = (f"Title: {enh.get('title','N/A')}\n"
                           f"URL: {enh.get('url','N/A')}\n"
                           f"Content:\n{enh.get('body','')[:1500]}")

        return {
            "decision_name": area.name,
            "decision_type": area.decision_type,
            "description": area.description,
            "key_files_formatted": "\n".join(f"- {f}" for f in area.key_files),
            "evidence_formatted": "\n".join(evidence_lines) or "N/A",
            "code_snippets": code or "Not available",
            "introducing_date": history.get("date", "Unknown"),
            "introducing_subject": history.get("subject", "N/A"),
            "pr_description": history.get("pr_description", "N/A"),
            "jira_description": history.get("jira_description", "N/A"),
            "enhancement_summary": enh_summary or "Not available",
            "owners": ", ".join(area.owners) if area.owners else "Unknown",
            "repo_type": profile.repo_type,
            "openshift_category": profile.openshift_category,
            "primary_language": profile.primary_language,
        }

    def _read_full_files(self, area: DecisionArea, repo: Path) -> str:
        sections: List[str] = []
        total = 0
        for fp in area.key_files[:MAX_FILES_PER_ADR]:
            if total >= MAX_TOTAL_CONTEXT_CHARS:
                break
            full = repo / fp
            if not full.exists() or not full.is_file():
                continue
            try:
                content = full.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if len(content) > MAX_FILE_CHARS:
                content = content[:MAX_FILE_CHARS] + f"\n// ... truncated ({len(content)} chars)"
            sections.append(f"=== {fp} ===\n{content}\n")
            total += len(content)
        return "\n".join(sections)

    # ------------------------------------------------------------------
    # Frontmatter
    # ------------------------------------------------------------------

    def _build_frontmatter(self, area: DecisionArea, num: int, profile: RepoProfile) -> str:
        history = area.history or {}
        components = set()
        for f in area.key_files:
            parts = Path(f).parts
            if len(parts) >= 2 and parts[0] not in (".", "go.mod", "package.json"):
                components.add(parts[0] if len(parts) < 3 else "/".join(parts[:2]))

        date = history.get("date", datetime.now().strftime("%Y-%m-%d"))
        jira_key = history.get("jira_key", "")
        owners_str = ", ".join(area.owners) if area.owners else profile.owner
        comp_str = ", ".join(sorted(components)) if components else "unknown"

        fm = (f"---\nid: ADR-{num:04d}\ntitle: \"{area.name}\"\ndate: {date}\n"
              f"status: accepted\ndeciders: [{owners_str}]\ncomponents: [{comp_str}]\n")
        if jira_key:
            fm += f"jira: {jira_key}\n"
        if area.enhancement:
            enh = area.enhancement
            if enh.get("type") == "pr":
                fm += (f"\nenhancement-refs:\n  - repo: \"openshift/enhancements\"\n"
                       f"    number: {enh.get('number','')}\n"
                       f"    title: \"{enh.get('title','')}\"\n")
            elif enh.get("url"):
                fm += (f"\nenhancement-refs:\n  - url: \"{enh.get('url','')}\"\n"
                       f"    title: \"{enh.get('title','')}\"\n")
        fm += "supersedes: \"\"\nsuperseded-by: \"\"\n---\n\n"
        return fm

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_body(body: str) -> str:
        body = body.strip()
        if body.startswith("```"):
            lines = body.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            body = "\n".join(lines).strip()
        if body.startswith("---"):
            parts = body.split("---", 2)
            if len(parts) >= 3:
                body = parts[2].strip()
        return body + "\n"

    @staticmethod
    def _slugify(name: str, max_len: int = 50) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")
        return slug[:max_len].rstrip("-") if len(slug) > max_len else slug

    def _write_adr_template(self, out_dir: Path):
        (out_dir / "adr-template.md").write_text(ADR_TEMPLATE_CONTENT, encoding="utf-8")

    def _write_index(self, out_dir: Path, paths: List[str]):
        lines = ["# Architectural Decision Records\n",
                 "## Purpose\n",
                 "Document why architectural decisions were made.\n",
                 "## Accepted\n"]
        for p in sorted(paths):
            fn = Path(p).name
            m = re.match(r"adr-(\d+)-(.*?)\.md", fn)
            if m:
                lines.append(f"- [ADR-{m.group(1)}: {m.group(2).replace('-',' ').title()}](./{fn})")
        lines += ["", "## When to Add Here\n",
                   "Create an ADR when:",
                   "- Making a significant architectural choice",
                   "- Choosing between multiple viable alternatives",
                   "- Establishing a new pattern or practice",
                   "- Deprecating an existing approach\n",
                   "Use the [ADR template](./adr-template.md).\n"]
        (out_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")
