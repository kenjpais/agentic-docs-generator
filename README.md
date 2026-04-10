# Agentic Documentation Generator

An automated tool that generates comprehensive agentic documentation for software repositories following the [agentic-docs-guide framework](https://github.com/Prashanth684/agentic-docs-guide). Analyzes local git repositories to extract commit history, links to Jira tickets, and generates complete documentation structures using Google's Gemini LLM.

## Overview

This tool helps engineering teams automatically document their work by:

1. Analyzing commits from local git repositories (no GitHub API required)
2. Extracting Jira ticket IDs from commit messages
3. Fetching Jira ticket details and acceptance criteria
4. Building comprehensive context from code changes and Jira discussions
5. Generating structured agentic documentation using Gemini AI
6. Following the complete agentic-docs-guide framework structure
7. Creating repository navigation and living documentation

**Why local repositories?**
- ✅ No GitHub API rate limits (5000 requests/hour)
- ✅ Works with private repositories without special permissions
- ✅ Faster processing - direct access to git data
- ✅ Can process unlimited commits
- ✅ No network latency or API quota concerns

## Features

### Documentation Generation
- **Complete Agentic Structure**: Generates full documentation following agentic-docs-guide framework
- **AGENTS.md**: Single entry point for repository navigation
- **ADRs**: Architecture Decision Records in `decisions/`
- **Execution Plans**: Implementation documentation in `exec-plans/`
- **Design Documentation**: Architectural designs in `design-docs/`
- **Product Specifications**: Feature specs in `product-specs/`
- **Domain Models**: Concepts and workflows in `domain/`

### Intelligent Features
- **Automated PR Fetching**: Retrieves recently merged PRs from any GitHub repository
- **Smart Jira Linking**: Automatically extracts Jira ticket IDs from PR titles, descriptions, or branch names
- **Context-Rich Documentation**: Combines code changes, Jira requirements, and discussions
- **AI-Powered Generation**: Uses Google Gemini to generate technical, precise documentation
- **Framework Integration**: Prompts include relevant agentic-docs-guide guidelines
- **Flexible Modes**: Simple (ADR+exec-plan only) or Full (complete structure)
- **YAML-Based Prompts**: Easy to customize and version control
- **Modular Architecture**: Easy to extend and customize

## Architecture

The system consists of the following modules:

```
├── main.py                        # CLI entry point with mode selection
├── local_git_client.py            # Local git repository integration
├── jira_client.py                 # Jira API integration (with public access)
├── context_builder.py             # Links commits to Jira and builds context
├── gemini_client.py               # Gemini LLM integration (google-genai)
├── prompt_loader.py               # Load prompts from YAML configuration
├── prompts.yaml                   # Centralized prompt configuration
├── doc_generator.py               # Simple doc generation (ADR+exec-plan)
├── agentic_doc_generator.py       # Full agentic structure generation
├── models.py                      # Data models
├── utils.py                       # Utility functions
└── templates/agentic-docs-guide/  # Framework templates and guidelines
```

### Documentation Modes

**Simple Mode** (`--mode simple`):
- Generates ADRs and execution plans only
- Organized by commit in traditional structure
- Quick generation for basic documentation needs

**Full Mode** (`--mode full`, default):
- Generates complete agentic documentation structure
- Follows agentic-docs-guide framework
- Creates AGENTS.md, design docs, product specs, domain models
- Organized in standardized agentic/ directory structure

### How It Works

1. **Local Git Analysis**: Uses `git log`, `git show`, and `git diff` to extract commit data
2. **Jira ID Extraction**: Parses commit messages for Jira ticket IDs (e.g., OCPBUGS-123, CORS-456)
3. **Jira Integration**: Fetches ticket details, acceptance criteria, and discussions
4. **Context Building**: Combines code changes and Jira information
5. **AI Generation**: Uses Gemini to generate comprehensive documentation
6. **Framework Compliance**: Follows agentic-docs-guide structure exactly

## Prerequisites

- Python 3.8 or higher
- Git installed (for reading local repositories)
- Google Gemini API Key (required)
- Jira base URL (for public or authenticated access)
- **Optional** (for private Jira):
  - Jira API Token and email

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
# Jira Configuration
JIRA_BASE_URL=https://issues.redhat.com
JIRA_API_TOKEN=your_jira_api_token  # Optional for public Jira
JIRA_EMAIL=your_email@example.com   # Optional for public Jira

# Gemini Configuration (Required)
GEMINI_API_KEY=your_gemini_api_key
```

### Getting API Credentials

**Gemini API Key** (Required):
1. Go to https://makersuite.google.com/app/apikey
2. Create API key
3. Copy to `.env` file as `GEMINI_API_KEY`

**Jira Configuration** (Required for Jira base URL, optional for authentication):
- **JIRA_BASE_URL**: Your Jira instance URL (e.g., `https://issues.redhat.com`)
- **JIRA_API_TOKEN**: Only required for private Jira instances
  1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
  2. Create API token
  3. Copy token to `.env` file
- **JIRA_EMAIL**: Only required for private Jira instances (your Jira email)

**Note**: For public Jira instances like Red Hat's, only `JIRA_BASE_URL` is required.

## Usage

### Basic Usage

```bash
python main.py /path/to/local/repo
```

### Command-line Options

```
repo_path             Path to local git repository (required positional argument)
--limit LIMIT         Maximum number of commits to fetch (default: 10)
--output OUTPUT       Output directory (default: output)
--mode MODE           Documentation mode: simple or full (default: full)
--env-file ENV_FILE   Path to .env file (default: .env)
--skip-jira           Skip commits without Jira tickets (default: True)
```

### Examples

**Step 1: Clone the repository**
```bash
git clone https://github.com/openshift/installer.git /tmp/installer
```

**Step 2: Generate documentation**

Full agentic documentation (default):
```bash
python main.py /tmp/installer --limit 10
```

Simple documentation (ADR + exec-plan only):
```bash
python main.py /tmp/installer --mode simple --limit 10
```

Process more commits:
```bash
python main.py /tmp/installer --limit 50
```

Custom output directory:
```bash
python main.py /tmp/installer --output docs/generated
```

Quick test with 1 commit:
```bash
python main.py /tmp/installer --limit 1
```

Generate for 20 PRs with custom output:
```bash
python main.py --repo openshift/installer --limit 20 --output docs/generated
```

Quick test with 1 PR:
```bash
python main.py --repo openshift/installer --limit 1 --mode full
```

## Output Structure

### Full Mode (Agentic Documentation)

Following the agentic-docs-guide framework:

```
output/
└── repo-name/
    └── agentic-docs/
        ├── AGENTS.md                    # Repository navigation (entry point)
        ├── ARCHITECTURE.md              # System map (auto-generated)
        ├── decisions/
        │   ├── index.md                 # ADR catalog
        │   ├── adr-0001-feature.md      # Individual ADRs
        │   └── adr-template.md
        ├── exec-plans/
        │   ├── index.md                 # Execution plan catalog
        │   ├── active/                  # Work in progress
        │   ├── completed/               # Historical record
        │   │   ├── exec-0001-feature.md
        │   │   └── ...
        │   └── template.md
        ├── design-docs/
        │   ├── index.md                 # Design catalog
        │   ├── core-beliefs.md          # Operating principles
        │   ├── component-architecture.md
        │   └── components/              # Per-component docs
        ├── product-specs/
        │   ├── index.md                 # Feature catalog
        │   └── feature-name.md          # Product specifications
        ├── domain/
        │   ├── index.md                 # Domain model map
        │   ├── glossary.md              # Terminology
        │   ├── concepts/                # Domain concepts
        │   └── workflows/               # User/system flows
        ├── references/                  # External knowledge
        └── generated/                   # Auto-generated docs
```

### Simple Mode

Traditional structure (backward compatible):

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

**AGENTS.md** (Full mode only):
- Repository overview
- Quick navigation by intent
- Component boundaries
- Core concepts
- Critical code locations
- Build and test commands

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

### Updating Documentation Prompts

All prompts are now in `prompts.yaml` for easy customization:

```yaml
prompts:
  adr:
    name: "Architecture Decision Record"
    system_instruction: |
      Your custom system instruction here...
    
    user_prompt: |
      Your custom prompt template here...
      Use {feature_title}, {pr_number}, etc. for variables
```

Available prompt types:
- `adr`: Architecture Decision Records
- `exec_plan`: Execution Plans
- `agents_md`: AGENTS.md repository navigation
- `design_doc`: Design Documentation
- `product_spec`: Product Specifications
- `domain_concept`: Domain Concepts
- `tech_debt`: Technical Debt Tracker

### Customizing Framework Guidelines

The `prompt_loader.py` automatically injects relevant framework guidelines into prompts. To customize:

1. Edit files in `templates/agentic-docs-guide/`
2. Modify `framework_files` section in `prompts.yaml`
3. Adjust `get_framework_guidelines()` in `prompt_loader.py`

### Adjusting Gemini Parameters

Edit `gemini_client.py` to modify generation parameters:

```python
config=types.GenerateContentConfig(
    temperature=0.7,        # Creativity (0.0 - 1.0)
    top_p=0.8,             # Diversity
    top_k=40,              # Top-k sampling
    max_output_tokens=2048 # Maximum response length
)
```

### Adding Custom Fields

Extend the data models in `models.py` to capture additional information from GitHub or Jira.

### Customizing Output Structure

Modify the `output_structure` section in `prompts.yaml` to change the generated directory structure.

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
