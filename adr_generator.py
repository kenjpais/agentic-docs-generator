"""Generates ADRs from code-analyzed DecisionAreas (bootstrap mode)."""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from models import DecisionArea, RepoProfile
from prompt_loader import PromptLoader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_SNIPPET_LINES = 50
MAX_SNIPPET_FILES = 8
MAX_FULL_FILE_CHARS = 10000
MAX_TOTAL_CONTEXT_CHARS = 50000

ADR_TEMPLATE_CONTENT = """\
---
id: ADR-[number]
title: [Decision Title]
date: YYYY-MM-DD
status: [proposed | accepted | deprecated | superseded]
deciders: [team-name, @username]
supersedes: [ADR-XXX if applicable]
superseded-by: [ADR-XXX if applicable]
---

# [Decision Title]

## Status

[proposed | accepted | deprecated | superseded by ADR-XXX]

## Context

What is the issue or situation that motivates this decision?

## Decision

What is the change that we're proposing/announcing?

## Rationale

Why did we choose this option?

### Why This?
- Reason 1
- Reason 2

### Why Not Alternatives?
- Alternative A: [Why rejected]
- Alternative B: [Why rejected]

## Consequences

### Positive
- Benefit 1
- Benefit 2

### Negative
- Tradeoff 1
- Tradeoff 2

### Neutral
- Change 1

## Implementation

- **Location**: [Where in codebase]
- **Migration**: [How to transition]
- **Rollout**: [Deployment plan]

## Alternatives Considered

### Alternative 1: [Name]
**Pros**: [Benefits]
**Cons**: [Drawbacks]
**Why rejected**: [Reason]

## References

- [Related ADR](./adr-xxx.md)
- [Design doc](../design/xxx.md)
- [External reference](https://...)

## Notes

[Any additional context, history, or discussion points]
"""


class ADRGenerator:
    """Generates ADR files from DecisionArea objects."""

    def __init__(self, llm_client, output_dir: str = "output"):
        self.gemini_client = llm_client
        self.output_dir = Path(output_dir)
        self.prompt_loader = PromptLoader()

    def generate_adrs(
        self,
        decision_areas: List[DecisionArea],
        profile: RepoProfile,
    ) -> List[str]:
        """Generate ADR files for all decision areas.

        Returns list of generated file paths.
        """
        repo_dir = self.output_dir / profile.name / "agentic" / "decisions"
        repo_dir.mkdir(parents=True, exist_ok=True)

        generated_paths: List[str] = []

        self._write_adr_template(repo_dir)

        for idx, area in enumerate(decision_areas, start=1):
            path = self._generate_single_adr(area, idx, profile, repo_dir)
            if path:
                generated_paths.append(str(path))

        self._write_index(repo_dir, decision_areas, generated_paths)

        logger.info(f"Generated {len(generated_paths)} ADRs in {repo_dir}")
        return generated_paths

    # ------------------------------------------------------------------
    # Single ADR generation
    # ------------------------------------------------------------------

    def _generate_single_adr(
        self,
        area: DecisionArea,
        adr_number: int,
        profile: RepoProfile,
        output_dir: Path,
    ) -> Optional[Path]:
        try:
            logger.info(f"Generating ADR-{adr_number:04d}: {area.name}")

            context = self._build_context(area, profile)
            prompt = self.prompt_loader.get_prompt("adr_from_code", context)
            body = self.gemini_client.generate(prompt)

            if not body or len(body) < 80:
                logger.warning(f"ADR body too short for {area.name}, skipping")
                return None

            body = self._clean_body(body)
            frontmatter = self._build_frontmatter(area, adr_number, profile)
            content = frontmatter + body

            slug = self._slugify(area.name)
            filename = f"adr-{adr_number:04d}-{slug}.md"
            filepath = output_dir / filename

            filepath.write_text(content, encoding="utf-8")
            logger.info(f"Wrote {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to generate ADR for {area.name}: {e}")
            return None

    # ------------------------------------------------------------------
    # Context building
    # ------------------------------------------------------------------

    def _build_context(self, area: DecisionArea, profile: RepoProfile) -> Dict:
        history = area.history or {}

        evidence_lines = []
        for key, value in area.evidence.items():
            evidence_lines.append(f"- {key}: {value}")

        code_snippets = self._read_full_files(area, Path(profile.path))

        enhancement_summary = ""
        if area.enhancement:
            enh = area.enhancement
            enhancement_summary = (
                f"Title: {enh.get('title', 'N/A')}\n"
                f"URL: {enh.get('url', 'N/A')}\n"
                f"Content:\n{enh.get('body', 'Not available')[:1500]}"
            )

        return {
            "decision_name": area.name,
            "decision_type": area.decision_type,
            "description": area.description,
            "key_files_formatted": "\n".join(f"- {f}" for f in area.key_files),
            "evidence_formatted": "\n".join(evidence_lines) or "N/A",
            "code_snippets": code_snippets or "Not available",
            "introducing_date": history.get("date", "Unknown"),
            "introducing_subject": history.get("subject", "N/A"),
            "pr_description": history.get("pr_description", "N/A"),
            "jira_description": history.get("jira_description", "N/A"),
            "enhancement_summary": enhancement_summary or "Not available",
            "owners": ", ".join(area.owners) if area.owners else "Unknown",
            "repo_type": profile.repo_type,
            "openshift_category": profile.openshift_category,
            "primary_language": profile.primary_language,
            "framework_guidelines": "",
        }

    def _read_full_files(self, area: DecisionArea, repo_path: Path) -> str:
        """Read full file contents for the LLM, up to MAX_TOTAL_CONTEXT_CHARS."""
        sections: List[str] = []
        total_chars = 0

        for filepath in area.key_files[:MAX_SNIPPET_FILES]:
            if total_chars >= MAX_TOTAL_CONTEXT_CHARS:
                break
            full_path = repo_path / filepath
            if not full_path.exists() or not full_path.is_file():
                continue
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            if len(content) > MAX_FULL_FILE_CHARS:
                content = content[:MAX_FULL_FILE_CHARS] + (
                    f"\n// ... truncated ({len(content)} total chars)"
                )

            sections.append(f"=== {filepath} ===")
            sections.append(content)
            sections.append("")
            total_chars += len(content)

        return "\n".join(sections)

    # ------------------------------------------------------------------
    # Frontmatter injection
    # ------------------------------------------------------------------

    def _build_frontmatter(
        self, area: DecisionArea, adr_number: int, profile: RepoProfile
    ) -> str:
        history = area.history or {}

        components = set()
        for f in area.key_files:
            parts = Path(f).parts
            if len(parts) >= 2 and parts[0] not in (".", "go.mod", "package.json",
                                                      "requirements.txt", "Makefile"):
                components.add(parts[0] if len(parts) < 3 else "/".join(parts[:2]))

        date = history.get("date", datetime.now().strftime("%Y-%m-%d"))
        jira_key = history.get("jira_key", "")

        enhancement_refs = ""
        if area.enhancement:
            enh = area.enhancement
            if enh.get("type") == "pr":
                enhancement_refs = (
                    f"\nenhancement-refs:\n"
                    f"  - repo: \"openshift/enhancements\"\n"
                    f"    number: {enh.get('number', '')}\n"
                    f"    title: \"{enh.get('title', '')}\""
                )
            elif enh.get("url"):
                enhancement_refs = (
                    f"\nenhancement-refs:\n"
                    f"  - url: \"{enh.get('url', '')}\"\n"
                    f"    title: \"{enh.get('title', '')}\""
                )

        owners_str = ", ".join(area.owners) if area.owners else profile.owner
        components_str = ", ".join(sorted(components)) if components else "unknown"

        frontmatter = (
            f"---\n"
            f"id: ADR-{adr_number:04d}\n"
            f"title: \"{area.name}\"\n"
            f"date: {date}\n"
            f"status: accepted\n"
            f"deciders: [{owners_str}]\n"
            f"components: [{components_str}]\n"
        )

        if jira_key:
            frontmatter += f"jira: {jira_key}\n"
        if enhancement_refs:
            frontmatter += enhancement_refs + "\n"

        frontmatter += (
            f"supersedes: \"\"\n"
            f"superseded-by: \"\"\n"
            f"---\n\n"
        )
        return frontmatter

    # ------------------------------------------------------------------
    # Output helpers
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
        if len(slug) > max_len:
            slug = slug[:max_len].rstrip("-")
        return slug

    def _write_adr_template(self, output_dir: Path):
        path = output_dir / "adr-template.md"
        path.write_text(ADR_TEMPLATE_CONTENT, encoding="utf-8")
        logger.info(f"Wrote ADR template to {path}")

    def _write_index(
        self,
        output_dir: Path,
        areas: List[DecisionArea],
        generated_paths: List[str],
    ):
        lines = [
            "# Architectural Decision Records\n",
            "## Purpose\n",
            "Document why architectural decisions were made.\n",
            "## Accepted\n",
        ]

        for path_str in sorted(generated_paths):
            filename = Path(path_str).name
            match = re.match(r"adr-(\d+)-(.*?)\.md", filename)
            if match:
                number = match.group(1)
                title = match.group(2).replace("-", " ").title()
                lines.append(f"- [ADR-{number}: {title}](./{filename})")

        lines.append("")
        lines.append("## When to Add Here\n")
        lines.append("Create an ADR when:")
        lines.append("- Making a significant architectural choice")
        lines.append("- Choosing between multiple viable alternatives")
        lines.append("- Establishing a new pattern or practice")
        lines.append("- Deprecating an existing approach\n")
        lines.append("Use the [ADR template](./adr-template.md).\n")

        index_path = output_dir / "index.md"
        index_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Wrote ADR index to {index_path}")
