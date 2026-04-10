# Installing Agentic Framework in Your Repository

Quick guide to adopting the agentic documentation framework.

## Prerequisites

- Git repository
- Python 3.11+ (for metrics)
- Bash (for validation)

## Installation Steps

### Overview

1. **Copy scripts** - Get framework files into your repo
2. **Customize workflows** - ⚠️ REQUIRED: Match your docs
3. **Create structure** - Set up directories
4. **Populate content** - Write your documentation
5. **Validate** - Run checks
6. **Measure** - Generate metrics
7. **Document usage** - Record framework version (optional)
8. **Set up CI** - Automate validation

### Step 1: Copy Framework Scripts

```bash
# Navigate to your repository root
cd "$(git rev-parse --show-toplevel)"

# Auto-detect framework location (common paths)
if [ -d "../agentic-guide" ]; then
    GUIDE_PATH="../agentic-guide"
elif [ -d "$HOME/ws/src/github.com/openshift/agentic-guide" ]; then
    GUIDE_PATH="$HOME/ws/src/github.com/openshift/agentic-guide"
else
    echo "❌ ERROR: Cannot locate agentic-guide."
    echo "Please set GUIDE_PATH manually or clone from:"
    echo "  git clone https://github.com/openshift/agentic-guide.git ../agentic-guide"
    exit 1
fi

echo "Using framework at: $GUIDE_PATH"

# Copy validation script to repo root
cp "$GUIDE_PATH/VALIDATION_SCRIPT.sh" .
chmod +x VALIDATION_SCRIPT.sh

# Copy metrics scripts to agentic/
mkdir -p agentic/scripts
cp "$GUIDE_PATH/scripts/"*.py agentic/scripts/
cp "$GUIDE_PATH/scripts/"*.sh agentic/scripts/
chmod +x agentic/scripts/*.sh

echo "✅ Scripts copied successfully"
```

### Step 2: Customize Workflows (⚠️ REQUIRED)

**CRITICAL**: The framework provides generic template workflows. You MUST customize them for your repository or metrics will fail.

#### Why Required

Generic workflows reference placeholder files like `agentic/domain/glossary.md` that may not exist in your repo. You must replace these with your actual:
- Domain concepts (e.g., `agentic/domain/concepts/your-core-concept.md`)
- Key ADRs (e.g., `agentic/decisions/adr-0001-your-decision.md`)
- Repository-specific guides

#### How to Customize

Edit `agentic/scripts/measure-context-budget.py`:

```bash
# Open the workflow configuration file
$EDITOR agentic/scripts/measure-context-budget.py
```

Find the `WORKFLOWS` list (around line 80) and replace generic placeholders:

**Before (Generic - Will Fail)**:
```python
Workflow(
    name="Feature Implementation",
    files=[
        'AGENTS.md',
        'ARCHITECTURE.md',
        'agentic/domain/glossary.md',  # ❌ Generic placeholder
        'agentic/DESIGN.md',
    ]
)
```

**After (Your Repository)**:
```python
Workflow(
    name="Feature Implementation",
    files=[
        'AGENTS.md',
        'ARCHITECTURE.md',
        'agentic/design-docs/core-beliefs.md',
        # ✅ YOUR core domain concepts:
        'agentic/domain/concepts/your-main-entity.md',
        'agentic/domain/concepts/your-main-process.md',
        # ✅ YOUR key architectural decisions:
        'agentic/decisions/adr-0001-your-tech-choice.md',
        'agentic/DESIGN.md',
        'agentic/DEVELOPMENT.md',
        'agentic/TESTING.md'
    ]
)
```

#### What to Include in Workflows

**Bug Fix (Simple)** - Minimal context (3 files):
- `AGENTS.md`, `ARCHITECTURE.md`, `agentic/DEVELOPMENT.md`

**Bug Fix (Complex)** - Add domain knowledge (5 files):
- Above + 1-2 key domain concepts + `TESTING.md`

**Feature Implementation** - Comprehensive (7-9 files):
- Above + `core-beliefs.md` + 2-3 domain concepts + 1-2 key ADRs + `DESIGN.md`

**Understanding System** - Learning (4 files):
- `AGENTS.md`, `ARCHITECTURE.md`, `core-beliefs.md`, key glossary/concepts

**Security Review** - Focused (3 files):
- `AGENTS.md`, `SECURITY.md`, `core-beliefs.md`

#### Verify Customization

After editing, verify all referenced files will exist:

```bash
# Check workflow references (do this AFTER creating docs in Step 4)
cd agentic/scripts
python3 -c "
import re
with open('measure-context-budget.py') as f:
    content = f.read()
    files = re.findall(r\"'([^']+\.md)'\", content)
    for file in sorted(set(files)):
        import os
        if not os.path.exists(f'../../{file}'):
            print(f'⚠️  Will need to create: {file}')
"
```

**Expected output**: List of docs you need to create in Step 4. If empty, all workflow files already exist.

### Step 3: Create Directory Structure

```bash
# Create agentic directories
mkdir -p agentic/{design-docs/components,domain/{concepts,workflows},exec-plans/{active,completed},decisions,product-specs,references,generated}

# Create required files
touch agentic/{DESIGN.md,DEVELOPMENT.md,TESTING.md,RELIABILITY.md,SECURITY.md,QUALITY_SCORE.md}
touch agentic/design-docs/{index.md,core-beliefs.md}
touch agentic/domain/{index.md,glossary.md}
touch agentic/exec-plans/{template.md,tech-debt-tracker.md}
touch agentic/decisions/{index.md,adr-template.md}
touch agentic/product-specs/index.md
touch agentic/references/index.md

# Create top-level files (if they don't exist)
touch AGENTS.md ARCHITECTURE.md
```

### Step 4: Populate Templates

Follow the [AGENTIC_DOCS_RULEBOOK.md](./AGENTIC_DOCS_RULEBOOK.md) to populate each file with content.

**Critical**:
- Replace ALL `[PLACEHOLDERS]` with actual values
- AGENTS.md must be <150 lines
- Create at least 2-3 ADRs
- Create at least 1 active exec-plan
- **Create the concept docs you referenced in Step 2's workflows**

### Step 5: Validate Structure

```bash
# Run structure validation
./VALIDATION_SCRIPT.sh

# Should see:
# ✅ VALIDATION PASSED
```

### Step 6: Run Metrics and Generate Dashboard

**Purpose**: Generate metrics dashboard to visualize first pass quality and decide if second pass needed.

**IMPORTANT**: These are **shell scripts (.sh)**, not Python scripts. Use `./` or `bash`, NOT `python3`.

```bash
# ✅ CORRECT - Run the shell script directly (uses #!/bin/bash shebang)
./agentic/scripts/measure-all-metrics.sh --html

# ❌ WRONG - DO NOT run with python3 (will fail with syntax errors)
# python3 agentic/scripts/measure-all-metrics.sh  # DON'T DO THIS!

# Open dashboard in browser
firefox agentic/metrics-dashboard.html
# Or: chrome agentic/metrics-dashboard.html
# Or: open agentic/metrics-dashboard.html  (macOS)

# ✅ Validate metrics calculations (also a shell script)
./agentic/scripts/test-metrics.sh
```

**Dashboard shows**:
- Overall quality score (0-100)
- Navigation depth issues
- Context budget violations
- Documentation coverage gaps

**Interpret your score**:
- **90-100** (Excellent 🟢): First pass complete, no second pass needed
- **80-89** (Good 🔵): First pass complete, second pass optional
- **70-79** (Fair 🟡): Second pass recommended
- **<70** (Poor/Critical 🟠🔴): Fix gaps, then run second pass

**Expected**: If you customized workflows in Step 2 correctly, all workflow files should be found. If you see "Missing files" warnings, create those concept docs.

**Next step decision**:
- Score 85+: Proceed to Step 8 (commit)
- Score <85: Consider [SECOND_PASS_GUIDE.md](./SECOND_PASS_GUIDE.md) for optimization

### Step 6.1: Document Framework Usage (Recommended)

**Purpose**: Creates a record of which framework version you're using and how to update scripts.

**Skip this step if**: You don't want to track framework versioning (not recommended).

**Execute**:

```bash
# Auto-detect repository name
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
FRAMEWORK_VERSION="1.1"
COPY_DATE=$(date +%Y-%m-%d)

# Locate framework path (adjust if different)
if [ -d "../agentic-guide" ]; then
    GUIDE_PATH="../agentic-guide"
elif [ -d "$HOME/ws/src/github.com/openshift/agentic-guide" ]; then
    GUIDE_PATH="$HOME/ws/src/github.com/openshift/agentic-guide"
else
    echo "❌ ERROR: Cannot locate agentic-guide. Set GUIDE_PATH manually."
    exit 1
fi

# Copy template
cp "$GUIDE_PATH/templates/USING_FRAMEWORK_SCRIPTS.md" agentic/USING_FRAMEWORK_SCRIPTS.md

# Auto-detect OS and use appropriate sed
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

# Verify placeholders were replaced
if grep -E '\[REPO-NAME\]|\[FRAMEWORK-VERSION\]|\[COPY-DATE\]' agentic/USING_FRAMEWORK_SCRIPTS.md >/dev/null; then
    echo "❌ ERROR: Placeholders not replaced. Check sed commands."
    exit 1
fi

echo "✅ Created agentic/USING_FRAMEWORK_SCRIPTS.md"
echo "   Repository: $REPO_NAME"
echo "   Framework: $FRAMEWORK_VERSION"
echo "   Date: $COPY_DATE"
```

**What this provides**:
- Auto-detected repository name from git
- Framework version tracking
- Clear update instructions for future maintainers
- Safe vs unsafe script update guidance

### Step 8: Set Up CI

Create `.github/workflows/validate-agentic-docs.yml`:

```yaml
name: Validate Agentic Documentation

on:
  pull_request:
    paths:
      - 'agentic/**'
      - '*.md'
  push:
    branches: [main, master]

jobs:
  structure:
    name: Validate Structure
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run validation
        run: ./VALIDATION_SCRIPT.sh

  metrics:
    name: Measure Metrics
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Navigation depth
        run: |
          python3 agentic/scripts/measure-navigation-depth.py --max-depth 3 --fail-on-violation

      - name: Context budget
        run: |
          python3 agentic/scripts/measure-context-budget.py --max-budget 700 --fail-on-violation
```

## Installation Methods

### Method 1: Copy (Recommended)

**Pros**: Independent, no external dependencies
**Cons**: Need to manually sync updates

```bash
cp -r /path/to/agentic-guide/scripts/ agentic/scripts/
```

### Method 2: Git Submodule

**Pros**: Automatic updates
**Cons**: Requires git submodule knowledge

```bash
git submodule add https://github.com/openshift/agentic-guide.git .agentic-framework
ln -s .agentic-framework/scripts agentic/scripts
```

### Method 3: Symlink (Development Only)

**Pros**: Live updates during development
**Cons**: Breaks if framework moves

```bash
ln -s /path/to/agentic-guide/scripts agentic/scripts
```

## Quick Start Checklist

- [ ] Copy scripts to repository (Step 1)
- [ ] **Customize workflows** in `measure-context-budget.py` (Step 2 - REQUIRED)
- [ ] Create directory structure (Step 3)
- [ ] Create AGENTS.md (<150 lines) (Step 4)
- [ ] Create ARCHITECTURE.md (Step 4)
- [ ] Populate agentic/ files (Step 4)
- [ ] Replace all `[PLACEHOLDERS]` (Step 4)
- [ ] Create 2-3 ADRs (Step 4)
- [ ] Create 1 active exec-plan (Step 4)
- [ ] Run `./VALIDATION_SCRIPT.sh` (should pass) (Step 5)
- [ ] **Generate metrics dashboard** `./agentic/scripts/measure-all-metrics.sh --html` (Step 6)
- [ ] **Review dashboard** in browser, check score (Step 6)
- [ ] Run `./agentic/scripts/test-metrics.sh` (should pass) (Step 6)
- [ ] Create `USING_FRAMEWORK_SCRIPTS.md` (Step 6.1 - Recommended)
- [ ] **Decide**: Second pass needed based on score? (Step 6)
- [ ] Set up CI workflow (Step 8)
- [ ] **Benchmark** (25-50 tasks) to validate impact

## Verification

After installation, run:

```bash
# Structure check
./VALIDATION_SCRIPT.sh

# Metrics check
./agentic/scripts/measure-all-metrics.sh

# Test validation
./agentic/scripts/test-metrics.sh
```

All three should pass with no errors.

## Post-Installation

1. **Document in README**: Add link to `agentic/README.md`
2. **Team onboarding**: Share AGENTS.md entry point
3. **Establish workflow**: Require exec-plans for features
4. **Monitor metrics**: Weekly/monthly dashboard review
5. **Benchmark quarterly**: Validate impact on agent performance

## Updating Scripts

When framework scripts are updated:

```bash
# Re-copy from framework
cp /path/to/agentic-guide/scripts/* agentic/scripts/

# Verify still working
./agentic/scripts/test-metrics.sh
```

## Troubleshooting

### "Scripts not found"

```bash
# Verify scripts were copied
ls -la agentic/scripts/

# Re-copy if missing
cp /path/to/agentic-guide/scripts/* agentic/scripts/
chmod +x agentic/scripts/*.sh
```

### "Validation fails"

```bash
# Check what's missing
./VALIDATION_SCRIPT.sh

# Common issues:
# - Unreplaced [PLACEHOLDERS]
# - Missing required files
# - AGENTS.md >150 lines
```

### "Metrics seem wrong"

```bash
# Run validation tests
./agentic/scripts/test-metrics.sh

# If tests fail, scripts may be outdated
# Re-copy from framework
```

## Support

- **Framework docs**: [AGENTIC_DOCS_FRAMEWORK.md](./AGENTIC_DOCS_FRAMEWORK.md)
- **Step-by-step**: [AGENTIC_DOCS_RULEBOOK.md](./AGENTIC_DOCS_RULEBOOK.md)
- **Metrics guide**: [METRICS_GUIDE.md](./METRICS_GUIDE.md)
- **OpenShift-specific**: [OPENSHIFT_SPECIFIC_GUIDANCE.md](./OPENSHIFT_SPECIFIC_GUIDANCE.md)

---

**Framework Version**: 1.0
**Last Updated**: 2026-03-27
