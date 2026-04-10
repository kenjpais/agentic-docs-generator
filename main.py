#!/usr/bin/env python3
"""
Agentic Documentation Generator

Generates ADRs and execution plans from GitHub PRs and Jira tickets.
"""

import argparse
import sys
import logging
from pathlib import Path

from github_client import GitHubClient
from jira_client import JiraClient
from context_builder import ContextBuilder
from gemini_client import GeminiClient
from doc_generator import DocumentationGenerator
from utils import (
    load_environment_variables,
    validate_environment,
    ensure_output_directory,
    parse_repo_identifier,
    format_summary
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description='Generate agentic documentation from GitHub PRs and Jira tickets'
    )
    parser.add_argument(
        '--repo',
        required=True,
        help='Repository identifier (format: owner/repo)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of PRs to fetch (default: 10)'
    )
    parser.add_argument(
        '--output',
        default='output',
        help='Output directory (default: output)'
    )
    parser.add_argument(
        '--env-file',
        default='.env',
        help='Path to .env file (default: .env)'
    )
    parser.add_argument(
        '--skip-jira',
        action='store_true',
        help='Skip PRs without Jira tickets (default: True)'
    )

    args = parser.parse_args()

    try:
        # Load environment variables
        logger.info("Starting agentic documentation generator")
        load_environment_variables(args.env_file)

        # Validate environment
        if not validate_environment():
            logger.error("Environment validation failed. Please check your .env file.")
            sys.exit(1)

        # Parse repository identifier
        repo_owner, repo_name = parse_repo_identifier(args.repo)
        logger.info(f"Target repository: {repo_owner}/{repo_name}")

        # Ensure output directory exists
        ensure_output_directory(args.output)

        # Initialize clients
        logger.info("Initializing API clients")
        github_client = GitHubClient()
        jira_client = JiraClient()
        gemini_client = GeminiClient()

        # Fetch merged PRs
        logger.info(f"Fetching up to {args.limit} merged PRs")
        prs = github_client.fetch_merged_prs(repo_owner, repo_name, limit=args.limit)
        logger.info(f"Found {len(prs)} merged PRs")

        if not prs:
            logger.warning("No merged PRs found")
            sys.exit(0)

        # Build features by linking PRs to Jira
        logger.info("Linking PRs to Jira tickets")
        context_builder = ContextBuilder(github_client, jira_client)
        features = context_builder.link_prs_to_jira(prs)
        logger.info(f"Created {len(features)} features with Jira links")

        if not features:
            logger.warning("No features with valid Jira links found")
            sys.exit(0)

        # Generate documentation
        logger.info("Generating documentation")
        doc_generator = DocumentationGenerator(gemini_client, args.output)

        generated_docs = []
        for i, feature in enumerate(features, 1):
            logger.info(f"Processing feature {i}/{len(features)}")
            try:
                file_paths = doc_generator.generate_and_save(feature, repo_name)
                generated_docs.append({
                    'feature': feature,
                    'files': file_paths
                })
            except Exception as e:
                logger.error(f"Error generating docs for PR #{feature.pr.number}: {str(e)}")
                continue

        # Print summary
        print("\n" + "=" * 70)
        print("Documentation Generation Complete")
        print("=" * 70)
        print(f"\nTotal PRs fetched: {len(prs)}")
        print(f"Features with Jira links: {len(features)}")
        print(f"Documentation generated: {len(generated_docs)}")
        print(f"\nOutput directory: {Path(args.output).absolute()}")

        if generated_docs:
            print("\nGenerated documentation:")
            for doc in generated_docs:
                feature = doc['feature']
                files = doc['files']
                print(f"\n  PR #{feature.pr.number}: {feature.pr.title}")
                print(f"    Jira: {feature.jira.key if feature.jira else 'N/A'}")
                print(f"    Location: {files['directory']}")

        print("\n" + "=" * 70)
        logger.info("Documentation generation complete")

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
