# Agentic Documentation Generator

An automated tool that generates high-quality Architecture Decision Records (ADRs) and execution plans from GitHub Pull Requests and Jira tickets using Google's Gemini LLM.

## Overview

This tool helps engineering teams automatically document their work by:

1. Fetching merged Pull Requests from GitHub repositories
2. Linking PRs to their associated Jira tickets
3. Building comprehensive context from code changes and Jira discussions
4. Generating structured ADRs and execution plans using Gemini AI
5. Saving documentation in a well-organized directory structure

## Features

- **Automated PR Fetching**: Retrieves recently merged PRs from any GitHub repository
- **Smart Jira Linking**: Automatically extracts Jira ticket IDs from PR titles, descriptions, or branch names
- **Context-Rich Documentation**: Combines code changes, Jira requirements, and discussions into comprehensive context
- **AI-Powered Generation**: Uses Google Gemini to generate technical, precise documentation
- **Structured Output**: Organizes documentation by repository and feature with metadata
- **Modular Architecture**: Easy to extend and customize for different workflows

## Architecture

The system consists of the following modules:

```
├── github_client.py      # GitHub API integration
├── jira_client.py        # Jira API integration
├── context_builder.py    # Links PRs to Jira and builds context
├── gemini_client.py      # Gemini LLM integration
├── prompt_templates.py   # Documentation templates and prompts
├── doc_generator.py      # Documentation generation and saving
├── models.py             # Data models
├── utils.py              # Utility functions
└── main.py               # CLI entry point
```

## Prerequisites

- Python 3.8 or higher
- GitHub Personal Access Token with `repo` scope
- Jira API Token and account access
- Google Gemini API Key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agentic-docs-wo-kg
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API credentials
```

## Configuration

Create a `.env` file with the following variables:

```bash
# GitHub Configuration
GITHUB_TOKEN=your_github_personal_access_token

# Jira Configuration
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_API_TOKEN=your_jira_api_token
JIRA_EMAIL=your_email@example.com

# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key
```

### Getting API Credentials

**GitHub Token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` scope
3. Copy the token to your `.env` file

**Jira API Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create API token
3. Copy token and your email to `.env` file

**Gemini API Key:**
1. Go to https://makersuite.google.com/app/apikey
2. Create API key
3. Copy to `.env` file

## Usage

Basic usage:

```bash
python main.py --repo owner/repo-name
```

### Command-line Options

```
--repo REPO          Repository identifier (format: owner/repo) [REQUIRED]
--limit LIMIT        Maximum number of PRs to fetch (default: 10)
--output OUTPUT      Output directory (default: output)
--env-file ENV_FILE  Path to .env file (default: .env)
--skip-jira          Skip PRs without Jira tickets (default: True)
```

### Examples

Generate documentation for the latest 10 PRs:
```bash
python main.py --repo openshift/installer
```

Generate documentation for 20 PRs:
```bash
python main.py --repo openshift/installer --limit 20
```

Custom output directory:
```bash
python main.py --repo openshift/installer --output docs/generated
```

## Output Structure

Documentation is organized as follows:

```
output/
└── repo-name/
    ├── pr-123-feature-name/
    │   ├── adr.md           # Architecture Decision Record
    │   ├── exec-plan.md     # Execution Plan
    │   └── metadata.json    # Feature metadata
    └── pr-124-another-feature/
        ├── adr.md
        ├── exec-plan.md
        └── metadata.json
```

### Generated Files

**ADR (Architecture Decision Record):**
- Context and problem statement
- Decision drivers
- Chosen solution
- Implementation details
- Consequences and tradeoffs

**Execution Plan:**
- Problem statement
- Acceptance criteria
- Implementation steps
- Technical details
- Testing approach
- Rollback plan

**Metadata:**
- PR number and title
- Jira ticket reference
- Merge timestamp
- Code change statistics

## Customization

### Updating Documentation Templates

Edit `prompt_templates.py` to customize ADR and execution plan structures:

```python
ADR_TEMPLATE = """
# Your custom ADR structure
...
"""

EXEC_PLAN_TEMPLATE = """
# Your custom execution plan structure
...
"""
```

### Adjusting Gemini Parameters

Edit `gemini_client.py` to modify generation parameters:

```python
generation_config=genai.types.GenerationConfig(
    temperature=0.7,      # Adjust creativity (0.0 - 1.0)
    top_p=0.8,           # Adjust diversity
    top_k=40,            # Top-k sampling
    max_output_tokens=2048  # Maximum response length
)
```

### Adding Custom Fields

Extend the data models in `models.py` to capture additional information from GitHub or Jira.

## Troubleshooting

**Authentication Errors:**
- Verify all API tokens in `.env` are correct
- Check token permissions/scopes
- Ensure Jira base URL is correct

**No PRs Found:**
- Verify repository name format (`owner/repo`)
- Check if repository has merged PRs
- Increase `--limit` parameter

**Empty Documentation:**
- Check Gemini API quota
- Review prompt templates for issues
- Verify network connectivity

**Jira Ticket Not Found:**
- Verify Jira ID pattern in PR titles
- Check Jira API permissions
- Review Jira base URL configuration

## Development

### Project Structure

Following the modular design from `PLAN.md`:

1. **Data Ingestion**: `github_client.py`, `jira_client.py`
2. **Data Correlation**: `context_builder.py`
3. **Processing**: `prompt_templates.py`
4. **LLM Interface**: `gemini_client.py`
5. **Documentation**: `doc_generator.py`
6. **CLI**: `main.py`

### Running Tests

```bash
# Add tests in tests/ directory
pytest tests/
```

### Contributing

1. Follow the existing code structure
2. Add logging for debugging
3. Handle errors gracefully
4. Update documentation for new features

## Future Enhancements

- [ ] Multi-repository batch processing
- [ ] Web dashboard for viewing documentation
- [ ] Vector database integration for historical context
- [ ] Continuous documentation pipeline (CI/CD integration)
- [ ] Support for other LLM providers (Claude, GPT-4)
- [ ] Custom field mapping for Jira
- [ ] Documentation versioning
- [ ] Automated PR commenting with generated docs

## License

[Your License Here]

## Support

For issues and questions:
- Create an issue in the repository
- Check existing documentation
- Review logs in the console output

## Acknowledgments

- Built for Red Hat OpenShift documentation automation
- Follows agentic-docs-guide structure: https://github.com/Prashanth684/agentic-docs-guide/
- Powered by Google Gemini AI
