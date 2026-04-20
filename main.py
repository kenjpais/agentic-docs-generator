#!/usr/bin/env python3
"""
Agentic Documentation Generator

Generates ADRs and execution plans from GitHub PRs and Jira tickets.
"""

import argparse
import os
import sys
import logging
from pathlib import Path

from local_git_client import LocalGitClient
from jira_client import JiraClient
from context_builder import ContextBuilder
from gemini_client import GeminiClient
from llm_client import create_llm_client
from doc_generator import DocumentationGenerator
from agentic_doc_generator import AgenticDocumentationGenerator
from utils import (
    load_environment_variables,
    validate_environment,
    ensure_output_directory,
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
        description='Generate agentic documentation from local git repository and Jira tickets'
    )
    parser.add_argument(
        'repo_path',
        help='Path to local git repository'
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
    parser.add_argument(
        '--mode',
        choices=['simple', 'full', 'bootstrap'],
        default='full',
        help='Documentation generation mode: simple (ADR+exec-plan per PR), '
             'full (complete agentic structure per PR), or '
             'bootstrap (code-first ADRs for existing architecture) (default: full)'
    )
    parser.add_argument(
        '--llm',
        choices=['gemini', 'claude', 'auto'],
        default='auto',
        help='LLM provider: gemini (direct API), claude (Vertex AI), '
             'or auto (detect from env vars) (default: auto)'
    )

    args = parser.parse_args()

    try:
        # Load environment variables
        logger.info("Starting agentic documentation generator")
        load_environment_variables(args.env_file)

        # Validate environment
        if not validate_environment(mode=args.mode):
            logger.error("Environment validation failed. Please check your .env file.")
            sys.exit(1)

        # Ensure output directory exists
        ensure_output_directory(args.output)

        # ---------------------------------------------------------------
        # Bootstrap mode: code-first ADR generation
        # ---------------------------------------------------------------
        if args.mode == 'bootstrap':
            from adr_bootstrap import generate_adrs

            logger.info(f"Bootstrap mode: analyzing codebase at {args.repo_path}")
            llm = create_llm_client(args.llm)

            generated_paths = generate_adrs(
                repo_path=args.repo_path,
                output_dir=args.output,
                llm_client=llm,
            )

            print("\n" + "=" * 70)
            print("Bootstrap ADR Generation Complete")
            print("=" * 70)
            print(f"\nRepository: {args.repo_path}")
            print(f"ADRs generated: {len(generated_paths)}")
            print(f"\nOutput: {Path(args.output).absolute()}")
            print("\nGenerated ADRs:")
            for p in generated_paths:
                print(f"  - {Path(p).name}")
            print("\n" + "=" * 70)

        # ---------------------------------------------------------------
        # Simple / Full modes: PR-based generation (existing behavior)
        # ---------------------------------------------------------------
        else:
            logger.info(f"Using local repository: {args.repo_path}")
            local_client = LocalGitClient(args.repo_path)
            repo_info = local_client.get_repo_info()
            repo_owner = repo_info['owner']
            repo_name = repo_info['name']
            logger.info(f"Repository: {repo_owner}/{repo_name}")

            logger.info(f"Fetching up to {args.limit} recent commits from local repository")
            commits = local_client.fetch_recent_commits(limit=args.limit)
            logger.info(f"Found {len(commits)} commits")

            jira_client = JiraClient()
            gemini_client = GeminiClient()

            if not commits:
                logger.warning("No commits found")
                sys.exit(0)

            logger.info("Linking commits to Jira tickets")
            context_builder = ContextBuilder(jira_client)
            features = context_builder.link_prs_to_jira(commits)
            logger.info(f"Created {len(features)} features with Jira links")

            if not features:
                logger.warning("No features with valid Jira links found")
                sys.exit(0)

            logger.info(f"Generating documentation (mode: {args.mode})")

            if args.mode == 'full':
                agentic_gen = AgenticDocumentationGenerator(gemini_client, args.output)
                all_paths = agentic_gen.generate_full_documentation(features, repo_name, repo_owner)
                generated_docs = [{'feature': f, 'files': all_paths} for f in features]
            else:
                doc_generator = DocumentationGenerator(gemini_client, args.output)
                generated_docs = []
                for i, feature in enumerate(features, 1):
                    logger.info(f"Processing feature {i}/{len(features)}")
                    try:
                        file_paths = doc_generator.generate_and_save(feature, repo_name)
                        generated_docs.append({'feature': feature, 'files': file_paths})
                    except Exception as e:
                        logger.error(f"Error generating docs for PR #{feature.pr.number}: {str(e)}")
                        continue

            print("\n" + "=" * 70)
            print("Documentation Generation Complete")
            print("=" * 70)
            print(f"\nMode: {args.mode.upper()}")
            print(f"Repository: {args.repo_path}")
            print(f"Total commits processed: {len(commits)}")
            print(f"Features with Jira links: {len(features)}")
            print(f"Documentation generated: {len(generated_docs)}")
            print(f"\nOutput directory: {Path(args.output).absolute()}")

            if args.mode == 'full':
                print("\nGenerated agentic documentation structure:")
                print(f"  - {repo_name}/agentic-docs/")
                print(f"    ├── AGENTS.md (repository navigation)")
                print(f"    ├── decisions/ (ADRs)")
                print(f"    ├── exec-plans/ (execution plans)")
                print(f"    ├── design-docs/ (design documentation)")
                print(f"    ├── product-specs/ (feature specifications)")
                print(f"    ├── domain/ (concepts and workflows)")
                print(f"    └── references/ (external knowledge)")

            if generated_docs and args.mode == 'simple':
                print("\nGenerated documentation:")
                for doc in generated_docs:
                    feature = doc['feature']
                    files = doc['files']
                    print(f"\n  PR #{feature.pr.number}: {feature.pr.title}")
                    print(f"    Jira: {feature.jira.key if feature.jira else 'N/A'}")
                    if 'directory' in files:
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
