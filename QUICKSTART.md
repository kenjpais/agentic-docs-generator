# Quick Start Guide

Get up and running with Agentic Documentation Generator in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Git
- API access to GitHub, Jira, and Google Gemini

## Step 1: Get API Credentials

### GitHub Token
1. Go to https://github.com/settings/tokens/new
2. Select scopes: `repo` (Full control of private repositories)
3. Generate token and copy it

### Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Create API key
3. Copy the key

## Step 2: Setup Project

```bash
# Clone or navigate to the project
cd agentic-docs-wo-kg

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

Add your credentials to `.env`:

```bash
# GitHub Configuration
GITHUB_TOKEN=ghp_your_github_token_here

# Jira Configuration
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_API_TOKEN=your_jira_token_here
JIRA_EMAIL=your.email@example.com

# Gemini Configuration
GEMINI_API_KEY=your_gemini_key_here
```

## Step 4: Run Your First Generation

```bash
# Generate docs for a repository (example)
python main.py --repo openshift/installer --limit 5
```

This will:
1. Fetch the last 5 merged PRs from openshift/installer
2. Find Jira tickets linked to those PRs
3. Generate ADRs and execution plans
4. Save everything to `output/installer/`

## Step 5: View Results

```bash
# List generated documentation
ls -la output/installer/

# View a generated ADR
cat output/installer/pr-*/adr.md

# View a generated execution plan
cat output/installer/pr-*/exec-plan.md
```

## Common Commands

```bash
# Generate docs with custom limit
python main.py --repo owner/repo --limit 20

# Use custom output directory
python main.py --repo owner/repo --output my-docs

# Use Makefile for convenience
make run REPO=owner/repo LIMIT=5

# Clean up cache and temp files
make clean
```

## Troubleshooting

### "GITHUB_TOKEN is required"
Make sure your `.env` file exists and contains valid tokens.

### "No merged PRs found"
- Check if the repository has merged PRs
- Verify repository name format: `owner/repo`
- Try increasing the `--limit` parameter

### "Could not fetch Jira ticket"
- Verify Jira base URL is correct
- Check Jira API token and email
- Ensure you have access to the Jira tickets

### "Error generating content"
- Check Gemini API key is valid
- Verify you have API quota available
- Check network connectivity

## Example Output Structure

```
output/
└── installer/
    ├── pr-123-add-aws-support/
    │   ├── adr.md          # Architecture Decision Record
    │   ├── exec-plan.md    # Execution Plan
    │   └── metadata.json   # Metadata
    └── pr-124-fix-azure-bug/
        ├── adr.md
        ├── exec-plan.md
        └── metadata.json
```

## Next Steps

1. **Customize Templates**: Edit `prompt_templates.py` to match your organization's documentation standards

2. **Adjust Settings**: Modify Gemini parameters in `gemini_client.py` for different output styles

3. **Batch Processing**: Process multiple repositories by running the script multiple times

4. **Integrate into CI/CD**: Add documentation generation to your deployment pipeline

5. **Explore Advanced Features**: Check `README.md` for all available options

## Getting Help

- Read the full `README.md` for detailed documentation
- Check `CONTRIBUTING.md` for development guidelines
- Review `PLAN.md` for architectural details
- Open an issue for bugs or questions

## Pro Tips

- **Start Small**: Test with `--limit 1` first to verify setup
- **Use Makefile**: `make run REPO=owner/repo` is quicker
- **Check Logs**: The tool logs detailed information for debugging
- **Save Outputs**: Keep generated docs in version control for history
- **Customize**: The templates are flexible - adapt them to your needs

Happy documenting! 🚀
