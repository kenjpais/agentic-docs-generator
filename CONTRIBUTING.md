# Contributing to Agentic Documentation Generator

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/yourusername/agentic-docs-generator.git
   cd agentic-docs-generator
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your test credentials
   ```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Keep functions focused and modular
- Maximum line length: 100 characters

## Project Structure

```
├── github_client.py      # GitHub API integration
├── jira_client.py        # Jira API integration
├── context_builder.py    # Context building logic
├── gemini_client.py      # LLM integration
├── prompt_templates.py   # Prompt templates
├── doc_generator.py      # Documentation generation
├── models.py             # Data models
├── utils.py              # Utility functions
└── main.py               # CLI entry point
```

## Making Changes

1. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clean, well-documented code
   - Add logging for debugging
   - Handle errors gracefully
   - Update tests if applicable

3. **Test your changes:**
   ```bash
   python main.py --repo test-org/test-repo --limit 1
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

5. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request:**
   - Describe your changes clearly
   - Reference any related issues
   - Include screenshots if applicable

## Types of Contributions

### Bug Fixes
- Identify the bug and its root cause
- Write a test that reproduces the bug
- Fix the bug and ensure the test passes
- Update documentation if needed

### New Features
- Discuss the feature in an issue first
- Ensure it aligns with project goals
- Implement with tests
- Update README and documentation

### Documentation
- Fix typos or unclear explanations
- Add examples and use cases
- Improve installation instructions
- Add comments to complex code

### Performance Improvements
- Profile the code to identify bottlenecks
- Implement optimizations
- Benchmark improvements
- Document the changes

## Testing Guidelines

When tests are implemented, follow these guidelines:

```python
# Example test structure
def test_github_client_fetch_prs():
    """Test GitHub client PR fetching."""
    client = GitHubClient(token="test_token")
    prs = client.fetch_merged_prs("owner", "repo", limit=5)
    assert len(prs) <= 5
    assert all(pr.merged_at is not None for pr in prs)
```

## Adding New API Integrations

If adding support for new APIs (e.g., GitLab, Azure DevOps):

1. Create a new client file (e.g., `gitlab_client.py`)
2. Follow the existing client pattern
3. Implement required methods
4. Add configuration to `.env.example`
5. Update README with setup instructions

## Updating Documentation Templates

To modify ADR or execution plan templates:

1. Edit `prompt_templates.py`
2. Update both the template and prompt builder
3. Test with real data
4. Update examples in README

## Error Handling

Always handle errors gracefully:

```python
try:
    result = some_operation()
except SpecificException as e:
    logger.error(f"Descriptive error message: {str(e)}")
    # Handle or re-raise appropriately
```

## Logging

Use appropriate log levels:

```python
logger.debug("Detailed debugging information")
logger.info("General informational messages")
logger.warning("Warning messages")
logger.error("Error messages")
```

## Commit Message Guidelines

Follow these conventions:

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat: Add support for GitLab repositories

- Implement GitLab client
- Add configuration options
- Update documentation

Closes #123
```

## Review Process

1. All contributions require review
2. Address reviewer feedback promptly
3. Keep discussions constructive
4. Be patient and respectful

## Questions?

If you have questions:

1. Check existing documentation
2. Search closed issues
3. Open a new issue with the "question" label
4. Be specific and provide context

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help maintain a positive community

Thank you for contributing! 🎉
