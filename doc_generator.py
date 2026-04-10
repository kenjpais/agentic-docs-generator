"""Documentation generator for ADRs and execution plans."""

import os
from pathlib import Path
from models import Feature
from gemini_client import GeminiClient
from prompt_templates import PromptBuilder
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """Generates ADRs and execution plans from features."""

    def __init__(self, gemini_client: GeminiClient, output_dir: str = "output"):
        """
        Initialize documentation generator.

        Args:
            gemini_client: GeminiClient instance
            output_dir: Base directory for output files
        """
        self.gemini_client = gemini_client
        self.output_dir = Path(output_dir)
        self.prompt_builder = PromptBuilder()

    def generate_adr(self, feature: Feature) -> str:
        """
        Generate ADR for a feature.

        Args:
            feature: Feature object

        Returns:
            Generated ADR content
        """
        logger.info(f"Generating ADR for PR #{feature.pr.number}")

        # Build prompt
        prompt = self.prompt_builder.build_adr_prompt(feature.summary_context)

        # Generate with Gemini
        adr_content = self.gemini_client.generate(prompt)

        # Basic validation
        if not adr_content or len(adr_content) < 100:
            logger.warning("Generated ADR seems too short, might be incomplete")

        return adr_content

    def generate_exec_plan(self, feature: Feature) -> str:
        """
        Generate execution plan for a feature.

        Args:
            feature: Feature object

        Returns:
            Generated execution plan content
        """
        logger.info(f"Generating execution plan for PR #{feature.pr.number}")

        # Build prompt
        prompt = self.prompt_builder.build_exec_plan_prompt(feature.summary_context)

        # Generate with Gemini
        exec_plan_content = self.gemini_client.generate(prompt)

        # Basic validation
        if not exec_plan_content or len(exec_plan_content) < 100:
            logger.warning("Generated exec plan seems too short, might be incomplete")

        return exec_plan_content

    def save_documentation(self, feature: Feature, repo_name: str,
                          adr_content: str, exec_plan_content: str) -> dict:
        """
        Save generated documentation to files.

        Args:
            feature: Feature object
            repo_name: Repository name
            adr_content: ADR content
            exec_plan_content: Execution plan content

        Returns:
            Dictionary with file paths
        """
        # Create feature directory
        feature_name = self._sanitize_filename(feature.pr.title)
        feature_dir = self.output_dir / repo_name / f"pr-{feature.pr.number}-{feature_name}"
        feature_dir.mkdir(parents=True, exist_ok=True)

        # Save ADR
        adr_path = feature_dir / "adr.md"
        with open(adr_path, 'w', encoding='utf-8') as f:
            f.write(adr_content)
        logger.info(f"Saved ADR to {adr_path}")

        # Save execution plan
        exec_plan_path = feature_dir / "exec-plan.md"
        with open(exec_plan_path, 'w', encoding='utf-8') as f:
            f.write(exec_plan_content)
        logger.info(f"Saved execution plan to {exec_plan_path}")

        # Save metadata
        metadata_path = feature_dir / "metadata.json"
        import json
        metadata = {
            "pr_number": feature.pr.number,
            "pr_title": feature.pr.title,
            "jira_key": feature.jira.key if feature.jira else None,
            "merged_at": feature.pr.merged_at.isoformat() if feature.pr.merged_at else None,
            "files_modified": len(feature.pr.files_changed),
            "additions": feature.summary_context.get('total_additions', 0),
            "deletions": feature.summary_context.get('total_deletions', 0)
        }
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")

        return {
            "adr": str(adr_path),
            "exec_plan": str(exec_plan_path),
            "metadata": str(metadata_path),
            "directory": str(feature_dir)
        }

    def generate_and_save(self, feature: Feature, repo_name: str) -> dict:
        """
        Generate and save all documentation for a feature.

        Args:
            feature: Feature object
            repo_name: Repository name

        Returns:
            Dictionary with file paths
        """
        logger.info(f"Generating documentation for feature: {feature.pr.title}")

        # Generate ADR
        adr_content = self.generate_adr(feature)

        # Generate execution plan
        exec_plan_content = self.generate_exec_plan(feature)

        # Save to files
        file_paths = self.save_documentation(
            feature, repo_name, adr_content, exec_plan_content
        )

        logger.info(f"Documentation generated successfully for PR #{feature.pr.number}")
        return file_paths

    def _sanitize_filename(self, filename: str, max_length: int = 50) -> str:
        """
        Sanitize a string to be used as a filename.

        Args:
            filename: Original filename
            max_length: Maximum length for filename

        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '-')

        # Replace spaces with hyphens
        filename = filename.replace(' ', '-')

        # Remove multiple consecutive hyphens
        while '--' in filename:
            filename = filename.replace('--', '-')

        # Truncate if too long
        if len(filename) > max_length:
            filename = filename[:max_length]

        # Remove trailing hyphens
        filename = filename.strip('-')

        return filename.lower()
