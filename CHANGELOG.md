# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-10

### Added
- Initial release of Agentic Documentation Generator
- GitHub API integration for fetching merged pull requests
- Jira API integration for fetching ticket information
- Automatic PR-to-Jira linking via pattern matching
- Context builder for creating comprehensive feature contexts
- Google Gemini integration for LLM-powered documentation generation
- ADR (Architecture Decision Record) generation
- Execution plan generation
- CLI interface with multiple options
- Structured output with metadata tracking
- Comprehensive error handling and logging
- Environment variable configuration via .env file
- Modular, extensible architecture
- Documentation templates following agentic-docs-guide structure

### Features
- Fetch up to N merged PRs from any GitHub repository
- Extract Jira IDs from PR titles, descriptions, or branch names
- Generate detailed ADRs with context and decision rationale
- Generate execution plans with implementation steps
- Organize output by repository and feature
- Save metadata for each generated documentation
- Code change summarization
- Jira discussion extraction
- Retry logic with exponential backoff for API calls

### Documentation
- Comprehensive README with setup instructions
- CONTRIBUTING guide for developers
- Example .env file
- Makefile for common tasks
- Code examples and usage patterns

### Development
- Python 3.8+ support
- Type hints for better code quality
- Logging throughout the application
- Basic test structure with pytest
- .gitignore for Python projects
- Virtual environment support

## [Unreleased]

### Planned
- Multi-repository batch processing
- Web dashboard for viewing documentation
- Vector database integration for historical context
- Continuous documentation pipeline (CI/CD integration)
- Support for other LLM providers (Claude, GPT-4)
- Custom Jira field mapping configuration
- Documentation versioning
- Automated PR commenting with generated docs
- GitLab and Azure DevOps support
- Enhanced test coverage
- Performance optimizations
- Caching layer for API responses

---

[1.0.0]: https://github.com/yourusername/agentic-docs-generator/releases/tag/v1.0.0
