"""Comprehensive agentic documentation generator following agentic-docs-guide framework."""

import os
from pathlib import Path
from typing import Dict, List
from models import Feature
from gemini_client import GeminiClient
from prompt_loader import PromptLoader
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgenticDocumentationGenerator:
    """Generates complete agentic documentation structure from features."""

    def __init__(self, gemini_client: GeminiClient, output_dir: str = "output"):
        """
        Initialize agentic documentation generator.

        Args:
            gemini_client: GeminiClient instance
            output_dir: Base directory for output files
        """
        self.gemini_client = gemini_client
        self.output_dir = Path(output_dir)
        self.prompt_loader = PromptLoader()

    def generate_full_documentation(self, features: List[Feature], repo_name: str,
                                    repo_owner: str) -> Dict[str, any]:
        """
        Generate complete agentic documentation structure for features.

        Args:
            features: List of Feature objects
            repo_name: Repository name
            repo_owner: Repository owner

        Returns:
            Dictionary with generated file paths
        """
        logger.info(f"Generating complete agentic documentation for {len(features)} features")

        # Create directory structure
        repo_dir = self.output_dir / repo_name / "agentic-docs"
        self._create_directory_structure(repo_dir)

        all_paths = {
            'root_files': {},
            'design_docs': [],
            'domain': [],
            'exec_plans': [],
            'decisions': [],
            'product_specs': [],
            'references': []
        }

        # Generate documentation for each feature
        for feature in features:
            paths = self._generate_feature_documentation(feature, repo_dir, repo_name, repo_owner)

            # Aggregate paths
            for key in ['design_docs', 'exec_plans', 'decisions']:
                if key in paths:
                    all_paths[key].extend(paths[key])

        # Generate repository-level documentation
        repo_paths = self._generate_repository_documentation(
            repo_dir, repo_name, repo_owner, features
        )
        all_paths['root_files'] = repo_paths

        # Generate index files
        self._generate_index_files(repo_dir, features, all_paths)

        logger.info(f"Complete agentic documentation generated at {repo_dir}")
        return all_paths

    def _create_directory_structure(self, base_dir: Path):
        """Create the agentic documentation directory structure."""
        structure = self.prompt_loader.get_output_structure()

        # Create main agentic directory
        base_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        dirs = [
            "design-docs", "design-docs/components",
            "domain", "domain/concepts", "domain/workflows",
            "exec-plans", "exec-plans/active", "exec-plans/completed",
            "product-specs",
            "decisions",
            "references",
            "generated"
        ]

        for dir_name in dirs:
            (base_dir / dir_name).mkdir(parents=True, exist_ok=True)

        logger.info(f"Created agentic documentation structure at {base_dir}")

    def _generate_feature_documentation(self, feature: Feature, base_dir: Path,
                                       repo_name: str, repo_owner: str) -> Dict[str, List[str]]:
        """Generate all documentation types for a single feature."""
        paths = {
            'design_docs': [],
            'exec_plans': [],
            'decisions': []
        }

        # Prepare context
        context = self._build_context(feature, repo_name, repo_owner)

        # 1. Generate ADR (Architecture Decision Record)
        adr_path = self._generate_adr(feature, base_dir / "decisions", context)
        if adr_path:
            paths['decisions'].append(str(adr_path))

        # 2. Generate Execution Plan
        exec_plan_path = self._generate_exec_plan(feature, base_dir / "exec-plans" / "completed", context)
        if exec_plan_path:
            paths['exec_plans'].append(str(exec_plan_path))

        # 3. Generate Design Document (if significant architectural changes)
        if self._has_architectural_significance(feature):
            design_doc_path = self._generate_design_doc(feature, base_dir / "design-docs", context)
            if design_doc_path:
                paths['design_docs'].append(str(design_doc_path))

        # 4. Generate Product Spec (if user-facing feature)
        if self._is_user_facing_feature(feature):
            product_spec_path = self._generate_product_spec(feature, base_dir / "product-specs", context)
            if product_spec_path:
                paths['product_specs'] = paths.get('product_specs', [])
                paths['product_specs'].append(str(product_spec_path))

        return paths

    def _build_context(self, feature: Feature, repo_name: str, repo_owner: str) -> Dict[str, str]:
        """Build context dictionary for prompt generation."""
        jira_context = feature.summary_context.get('jira_context', {})

        context = {
            'feature_title': feature.summary_context.get('feature_title', ''),
            'pr_number': feature.summary_context.get('pr_number', ''),
            'jira_key': feature.summary_context.get('jira_key', ''),
            'jira_title': jira_context.get('title', ''),
            'jira_description': jira_context.get('description', ''),
            'problem': feature.summary_context.get('problem', ''),
            'solution_summary': feature.summary_context.get('solution_summary', ''),
            'code_changes': feature.summary_context.get('code_changes', ''),
            'acceptance_criteria': jira_context.get('acceptance_criteria', ''),
            'key_discussions': jira_context.get('key_discussions', ''),
            'modified_files': '\n'.join([f"- {f}" for f in feature.summary_context.get('files_modified', [])]),
            'files_count': len(feature.summary_context.get('files_modified', [])),
            'additions': feature.summary_context.get('total_additions', 0),
            'deletions': feature.summary_context.get('total_deletions', 0),
            'affected_components': self._extract_components(feature.summary_context.get('files_modified', [])),
            'repo_name': repo_name,
            'repo_owner': repo_owner,
            'repo_description': f"{repo_owner}/{repo_name}",
            'language': self._detect_language(feature),
            'components': self._extract_components(feature.summary_context.get('files_modified', [])),
        }

        return context

    def _generate_adr(self, feature: Feature, decisions_dir: Path, context: Dict) -> Path:
        """Generate Architecture Decision Record."""
        try:
            logger.info(f"Generating ADR for PR #{feature.pr.number}")

            # Get prompt from loader
            prompt = self.prompt_loader.get_prompt('adr', context)

            # Generate with Gemini
            adr_content = self.gemini_client.generate(prompt)

            if not adr_content or len(adr_content) < 100:
                logger.warning("Generated ADR seems too short")
                return None

            # Save ADR
            adr_number = str(feature.pr.number).zfill(4)
            filename = f"adr-{adr_number}-{self._sanitize_filename(feature.pr.title)}.md"
            adr_path = decisions_dir / filename

            with open(adr_path, 'w', encoding='utf-8') as f:
                f.write(adr_content)

            logger.info(f"Saved ADR to {adr_path}")
            return adr_path

        except Exception as e:
            logger.error(f"Error generating ADR: {e}")
            return None

    def _generate_exec_plan(self, feature: Feature, exec_plans_dir: Path, context: Dict) -> Path:
        """Generate Execution Plan."""
        try:
            logger.info(f"Generating execution plan for PR #{feature.pr.number}")

            # Get prompt from loader
            prompt = self.prompt_loader.get_prompt('exec_plan', context)

            # Generate with Gemini
            exec_plan_content = self.gemini_client.generate(prompt)

            if not exec_plan_content or len(exec_plan_content) < 100:
                logger.warning("Generated exec plan seems too short")
                return None

            # Save exec plan
            filename = f"exec-{feature.pr.number:04d}-{self._sanitize_filename(feature.pr.title)}.md"
            exec_plan_path = exec_plans_dir / filename

            with open(exec_plan_path, 'w', encoding='utf-8') as f:
                f.write(exec_plan_content)

            logger.info(f"Saved execution plan to {exec_plan_path}")
            return exec_plan_path

        except Exception as e:
            logger.error(f"Error generating exec plan: {e}")
            return None

    def _generate_design_doc(self, feature: Feature, design_docs_dir: Path, context: Dict) -> Path:
        """Generate Design Document."""
        try:
            logger.info(f"Generating design doc for PR #{feature.pr.number}")

            prompt = self.prompt_loader.get_prompt('design_doc', context)
            design_doc_content = self.gemini_client.generate(prompt)

            if not design_doc_content:
                return None

            filename = f"design-{self._sanitize_filename(feature.pr.title)}.md"
            design_doc_path = design_docs_dir / filename

            with open(design_doc_path, 'w', encoding='utf-8') as f:
                f.write(design_doc_content)

            logger.info(f"Saved design doc to {design_doc_path}")
            return design_doc_path

        except Exception as e:
            logger.error(f"Error generating design doc: {e}")
            return None

    def _generate_product_spec(self, feature: Feature, product_specs_dir: Path, context: Dict) -> Path:
        """Generate Product Specification."""
        try:
            logger.info(f"Generating product spec for PR #{feature.pr.number}")

            # Add user stories context if available
            context['user_stories'] = self._extract_user_stories(feature)

            prompt = self.prompt_loader.get_prompt('product_spec', context)
            product_spec_content = self.gemini_client.generate(prompt)

            if not product_spec_content:
                return None

            filename = f"{self._sanitize_filename(feature.pr.title)}.md"
            product_spec_path = product_specs_dir / filename

            with open(product_spec_path, 'w', encoding='utf-8') as f:
                f.write(product_spec_content)

            logger.info(f"Saved product spec to {product_spec_path}")
            return product_spec_path

        except Exception as e:
            logger.error(f"Error generating product spec: {e}")
            return None

    def _generate_repository_documentation(self, base_dir: Path, repo_name: str,
                                          repo_owner: str, features: List[Feature]) -> Dict[str, str]:
        """Generate repository-level documentation files."""
        paths = {}

        # Generate AGENTS.md
        try:
            context = {
                'repo_name': repo_name,
                'repo_owner': repo_owner,
                'repo_description': f"OpenShift repository: {repo_name}",
                'language': 'Go',  # Default, could be detected
                'components': self._aggregate_components(features),
                'recent_features': self._summarize_features(features),
            }

            prompt = self.prompt_loader.get_prompt('agents_md', context)
            agents_md_content = self.gemini_client.generate(prompt)

            if agents_md_content:
                agents_md_path = base_dir / "AGENTS.md"
                with open(agents_md_path, 'w', encoding='utf-8') as f:
                    f.write(agents_md_content)
                paths['agents_md'] = str(agents_md_path)
                logger.info(f"Generated AGENTS.md")

        except Exception as e:
            logger.error(f"Error generating AGENTS.md: {e}")

        return paths

    def _generate_index_files(self, base_dir: Path, features: List[Feature], all_paths: Dict):
        """Generate index files for each documentation category."""
        # Generate decisions/index.md
        self._generate_decisions_index(base_dir / "decisions", all_paths.get('decisions', []))

        # Generate exec-plans/index.md
        self._generate_exec_plans_index(base_dir / "exec-plans", all_paths.get('exec_plans', []))

        # Generate design-docs/index.md
        self._generate_design_docs_index(base_dir / "design-docs", all_paths.get('design_docs', []))

    def _generate_decisions_index(self, decisions_dir: Path, adr_paths: List[str]):
        """Generate index file for ADRs."""
        index_content = "# Architecture Decision Records\n\n"
        index_content += "## All Decisions\n\n"

        for path in sorted(adr_paths):
            filename = Path(path).name
            title = filename.replace('adr-', '').replace('.md', '').replace('-', ' ').title()
            index_content += f"- [{title}]({filename})\n"

        index_path = decisions_dir / "index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)

        logger.info(f"Generated decisions index")

    def _generate_exec_plans_index(self, exec_plans_dir: Path, exec_plan_paths: List[str]):
        """Generate index file for execution plans."""
        index_content = "# Execution Plans\n\n"
        index_content += "## Completed Plans\n\n"

        for path in sorted(exec_plan_paths):
            filename = Path(path).relative_to(exec_plans_dir)
            title = filename.name.replace('exec-', '').replace('.md', '').replace('-', ' ').title()
            index_content += f"- [{title}]({filename})\n"

        index_path = exec_plans_dir / "index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)

        logger.info(f"Generated exec-plans index")

    def _generate_design_docs_index(self, design_docs_dir: Path, design_doc_paths: List[str]):
        """Generate index file for design documents."""
        index_content = "# Design Documentation\n\n"
        index_content += "## All Design Documents\n\n"

        for path in sorted(design_doc_paths):
            filename = Path(path).name
            title = filename.replace('design-', '').replace('.md', '').replace('-', ' ').title()
            index_content += f"- [{title}]({filename})\n"

        index_path = design_docs_dir / "index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)

        logger.info(f"Generated design-docs index")

    def _has_architectural_significance(self, feature: Feature) -> bool:
        """Determine if feature has architectural significance."""
        # Consider significant if:
        # - Changes multiple components
        # - Changes > 100 lines
        # - Touches core architecture files

        files_count = len(feature.pr.files_changed)
        total_changes = sum(f['changes'] for f in feature.pr.files_changed)

        architectural_keywords = ['architecture', 'design', 'api', 'interface', 'controller', 'operator']
        has_keywords = any(keyword in feature.pr.title.lower() for keyword in architectural_keywords)

        return files_count > 3 or total_changes > 100 or has_keywords

    def _is_user_facing_feature(self, feature: Feature) -> bool:
        """Determine if feature is user-facing."""
        user_keywords = ['user', 'ui', 'ux', 'interface', 'feature', 'enhancement']
        return any(keyword in feature.pr.title.lower() for keyword in user_keywords)

    def _extract_components(self, file_paths: List[str]) -> str:
        """Extract component names from file paths."""
        if not file_paths:
            return "N/A"

        components = set()
        for path in file_paths:
            parts = path.split('/')
            if len(parts) > 1:
                components.add(parts[0])

        return ', '.join(sorted(components)) if components else "N/A"

    def _aggregate_components(self, features: List[Feature]) -> str:
        """Aggregate components across all features."""
        all_components = set()
        for feature in features:
            files = feature.summary_context.get('files_modified', [])
            components = self._extract_components(files)
            if components != "N/A":
                all_components.update(components.split(', '))

        return ', '.join(sorted(all_components)) if all_components else "N/A"

    def _summarize_features(self, features: List[Feature]) -> str:
        """Create summary of recent features."""
        summaries = []
        for feature in features[:5]:  # Last 5 features
            summaries.append(f"- PR #{feature.pr.number}: {feature.pr.title}")
        return '\n'.join(summaries)

    def _detect_language(self, feature: Feature) -> str:
        """Detect programming language from file extensions."""
        files = feature.pr.files_changed
        extensions = {}

        for file in files:
            ext = Path(file['filename']).suffix
            extensions[ext] = extensions.get(ext, 0) + 1

        if not extensions:
            return "Unknown"

        # Return most common extension
        most_common = max(extensions.items(), key=lambda x: x[1])
        ext_map = {
            '.go': 'Go',
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.rb': 'Ruby',
        }

        return ext_map.get(most_common[0], 'Unknown')

    def _extract_user_stories(self, feature: Feature) -> str:
        """Extract user stories from Jira description."""
        description = feature.jira.description if feature.jira else ""

        # Simple extraction - look for "As a" patterns
        lines = description.split('\n')
        user_stories = [line for line in lines if 'as a' in line.lower()]

        return '\n'.join(user_stories) if user_stories else "No explicit user stories found"

    def _sanitize_filename(self, filename: str, max_length: int = 50) -> str:
        """Sanitize a string to be used as a filename."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '-')

        filename = filename.replace(' ', '-')

        while '--' in filename:
            filename = filename.replace('--', '-')

        if len(filename) > max_length:
            filename = filename[:max_length]

        filename = filename.strip('-')

        return filename.lower()
