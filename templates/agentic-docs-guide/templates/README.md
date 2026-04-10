# Agentic Framework Templates

This directory contains templates for files that should be created in repositories adopting the agentic documentation framework.

## Available Templates

### USING_FRAMEWORK_SCRIPTS.md

**Purpose**: Documents how scripts from the framework are used in a specific repository.

**Placeholders to replace**:
- `[REPO-NAME]` - Your repository name (e.g., "machine-config-operator")
- `[FRAMEWORK-VERSION]` - Framework version you're using (e.g., "1.1")
- `[COPY-DATE]` - Date when you copied scripts (e.g., "2026-03-27")

**Usage** (Agent-executable):
```bash
# Navigate to your repository
cd "$(git rev-parse --show-toplevel)"

# Auto-detect values
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
FRAMEWORK_VERSION="1.1"
COPY_DATE=$(date +%Y-%m-%d)

# Locate framework (adjust common paths as needed)
if [ -d "../agentic-guide" ]; then
    GUIDE_PATH="../agentic-guide"
else
    echo "Set GUIDE_PATH to agentic-guide location"
    exit 1
fi

# Copy template
cp "$GUIDE_PATH/templates/USING_FRAMEWORK_SCRIPTS.md" agentic/USING_FRAMEWORK_SCRIPTS.md

# Auto-detect OS and replace placeholders
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS (BSD sed)
    sed -i '' "s/\[REPO-NAME\]/$REPO_NAME/g" agentic/USING_FRAMEWORK_SCRIPTS.md
    sed -i '' "s/\[FRAMEWORK-VERSION\]/$FRAMEWORK_VERSION/g" agentic/USING_FRAMEWORK_SCRIPTS.md
    sed -i '' "s/\[COPY-DATE\]/$COPY_DATE/g" agentic/USING_FRAMEWORK_SCRIPTS.md
else
    # Linux (GNU sed)
    sed -i "s/\[REPO-NAME\]/$REPO_NAME/g" agentic/USING_FRAMEWORK_SCRIPTS.md
    sed -i "s/\[FRAMEWORK-VERSION\]/$FRAMEWORK_VERSION/g" agentic/USING_FRAMEWORK_SCRIPTS.md
    sed -i "s/\[COPY-DATE\]/$COPY_DATE/g" agentic/USING_FRAMEWORK_SCRIPTS.md
fi

# Verify replacement
if grep -E '\[REPO-NAME\]|\[FRAMEWORK-VERSION\]|\[COPY-DATE\]' agentic/USING_FRAMEWORK_SCRIPTS.md >/dev/null; then
    echo "❌ ERROR: Placeholders not replaced"
    exit 1
fi

echo "✅ Created agentic/USING_FRAMEWORK_SCRIPTS.md ($REPO_NAME, v$FRAMEWORK_VERSION)"
```

**What it provides**:
- Documents which framework version is in use
- Explains how to update scripts safely
- Lists which scripts are customized vs generic
- Provides update commands

**When to use**:
- When adopting the framework (recommended but optional)
- After copying scripts from framework to your repo
- To document for future maintainers

---

## Why Templates?

Templates provide:
1. **Consistency** - Same structure across all repos
2. **Clarity** - Clear placeholders to fill in
3. **Documentation** - Self-documenting setup process
4. **Maintenance** - Easy to identify what needs updating

---

## Adding New Templates

When creating new templates:
1. Use `[PLACEHOLDER]` format in ALL_CAPS with descriptive names
2. Document all placeholders in template comments
3. Provide usage examples
4. Update this README

---

**Framework Version**: 1.1
**Last Updated**: 2026-03-27
