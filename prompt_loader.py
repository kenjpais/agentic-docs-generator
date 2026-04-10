"""Prompt loader for agentic documentation generation."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptLoader:
    """Loads and manages prompts from YAML configuration."""

    def __init__(self, prompts_file: str = "prompts.yaml"):
        """
        Initialize prompt loader.

        Args:
            prompts_file: Path to prompts YAML file
        """
        self.prompts_file = Path(prompts_file)
        self.prompts_config = self._load_prompts()
        self.framework_content = self._load_framework_files()

    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts configuration from YAML."""
        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded prompts from {self.prompts_file}")
            return config
        except Exception as e:
            logger.error(f"Error loading prompts file: {e}")
            raise

    def _load_framework_files(self) -> Dict[str, str]:
        """Load framework documentation files."""
        framework_content = {}
        framework_files = self.prompts_config.get('framework_files', {})

        for name, filepath in framework_files.items():
            try:
                file_path = Path(filepath)
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        framework_content[name] = f.read()
                    logger.debug(f"Loaded framework file: {name}")
                else:
                    logger.warning(f"Framework file not found: {filepath}")
                    framework_content[name] = ""
            except Exception as e:
                logger.error(f"Error loading framework file {name}: {e}")
                framework_content[name] = ""

        return framework_content

    def get_framework_guidelines(self, doc_type: str = "general") -> str:
        """
        Get relevant framework guidelines for a documentation type.

        Args:
            doc_type: Type of documentation (adr, exec_plan, etc.)

        Returns:
            Relevant framework guidelines as string
        """
        # Extract relevant sections from framework
        main_framework = self.framework_content.get('main_framework', '')

        if doc_type == 'adr':
            # Extract ADR-specific guidance
            guidelines = self._extract_section(main_framework, "ADR", "decisions/")
        elif doc_type == 'exec_plan':
            # Extract exec-plan specific guidance
            guidelines = self._extract_section(main_framework, "exec-plans", "Execution Plans")
        elif doc_type == 'agents_md':
            # Extract AGENTS.md specific guidance
            guidelines = self._extract_section(main_framework, "AGENTS.md", "Table of Contents")
        else:
            # Return general guidelines
            guidelines = main_framework[:2000]  # First 2000 chars as overview

        return guidelines

    def _extract_section(self, content: str, *keywords: str) -> str:
        """Extract relevant section from content based on keywords."""
        lines = content.split('\n')
        relevant_lines = []
        in_relevant_section = False
        section_depth = 0

        for line in lines:
            # Check if line contains any keyword
            if any(keyword.lower() in line.lower() for keyword in keywords):
                in_relevant_section = True
                section_depth = line.count('#')

            if in_relevant_section:
                # Stop if we hit a section of equal or higher level
                if line.startswith('#') and line.count('#') <= section_depth and len(relevant_lines) > 10:
                    break
                relevant_lines.append(line)

        result = '\n'.join(relevant_lines[:150])  # Limit to 150 lines
        return result if result else content[:1000]

    def get_prompt(self, prompt_type: str, context: Dict[str, Any]) -> str:
        """
        Get a formatted prompt for a specific documentation type.

        Args:
            prompt_type: Type of prompt (adr, exec_plan, etc.)
            context: Context dictionary with variables

        Returns:
            Formatted prompt string
        """
        prompts = self.prompts_config.get('prompts', {})
        prompt_config = prompts.get(prompt_type)

        if not prompt_config:
            raise ValueError(f"Prompt type '{prompt_type}' not found in configuration")

        # Get framework guidelines
        framework_guidelines = self.get_framework_guidelines(prompt_type)
        context['framework_guidelines'] = framework_guidelines

        # Get system instruction and user prompt
        system_instruction = prompt_config.get('system_instruction', '')
        user_prompt = prompt_config.get('user_prompt', '')

        # Format the prompts with context
        try:
            formatted_system = system_instruction.format(**context)
            formatted_user = user_prompt.format(**context)
        except KeyError as e:
            logger.error(f"Missing context variable: {e}")
            # Fill in missing variables with empty strings
            safe_context = {k: v or '' for k, v in context.items()}
            formatted_system = system_instruction.format(**safe_context)
            formatted_user = user_prompt.format(**safe_context)

        # Combine system instruction and user prompt
        full_prompt = f"{formatted_system}\n\n{formatted_user}"

        return full_prompt

    def get_output_structure(self) -> Dict[str, Any]:
        """Get the output structure configuration."""
        return self.prompts_config.get('output_structure', {})

    def list_available_prompts(self) -> list:
        """List all available prompt types."""
        return list(self.prompts_config.get('prompts', {}).keys())
