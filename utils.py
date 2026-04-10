"""Utility functions for the agentic documentation generator."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_environment_variables(env_file: str = ".env") -> bool:
    """
    Load environment variables from .env file.

    Args:
        env_file: Path to .env file

    Returns:
        True if successful, False otherwise
    """
    env_path = Path(env_file)
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_file}")
        return True
    else:
        logger.warning(f"No {env_file} file found")
        return False


def validate_environment() -> bool:
    """
    Validate that all required environment variables are set.

    Returns:
        True if all required variables are set, False otherwise
    """
    required_vars = [
        'GITHUB_TOKEN',
        'JIRA_BASE_URL',
        'GEMINI_API_KEY'
    ]

    optional_vars = ['JIRA_API_TOKEN', 'JIRA_EMAIL']

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False

    # Log info about optional Jira auth
    if not os.getenv('JIRA_API_TOKEN') or not os.getenv('JIRA_EMAIL'):
        logger.info("Jira authentication not configured - will access public Jira tickets only")

    logger.info("All required environment variables are set")
    return True


def ensure_output_directory(output_dir: str = "output") -> Path:
    """
    Ensure output directory exists.

    Args:
        output_dir: Path to output directory

    Returns:
        Path object for output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ready: {output_path.absolute()}")
    return output_path


def parse_repo_identifier(repo_identifier: str) -> tuple:
    """
    Parse repository identifier into owner and name.

    Args:
        repo_identifier: Repository identifier (e.g., 'owner/repo')

    Returns:
        Tuple of (owner, repo_name)
    """
    if '/' in repo_identifier:
        parts = repo_identifier.split('/')
        if len(parts) == 2:
            return parts[0], parts[1]

    raise ValueError(
        f"Invalid repository identifier: {repo_identifier}. "
        "Expected format: 'owner/repo'"
    )


def format_summary(features: list) -> str:
    """
    Format a summary of generated documentation.

    Args:
        features: List of Feature objects

    Returns:
        Formatted summary string
    """
    if not features:
        return "No features processed"

    summary_lines = [
        f"\nDocumentation Generation Summary",
        f"=" * 50,
        f"Total features processed: {len(features)}",
        ""
    ]

    for i, feature in enumerate(features, 1):
        jira_key = feature.jira.key if feature.jira else "N/A"
        summary_lines.append(
            f"{i}. PR #{feature.pr.number}: {feature.pr.title[:60]}..."
        )
        summary_lines.append(f"   Jira: {jira_key}")
        summary_lines.append(f"   Files modified: {len(feature.pr.files_changed)}")
        summary_lines.append("")

    return "\n".join(summary_lines)
