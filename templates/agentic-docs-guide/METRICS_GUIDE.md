# Agentic Documentation Metrics Guide

Complete guide for measuring documentation quality in repositories using the agentic framework.

## Quick Start

```bash
# 1. Copy scripts to your repo
cp -r /path/to/agentic-guide/scripts/ your-repo/agentic/scripts/

# 2. Run metrics
cd your-repo
./agentic/scripts/measure-all-metrics.sh

# 3. Generate HTML dashboard
./agentic/scripts/measure-all-metrics.sh --html
firefox agentic/metrics-dashboard.html
```

## Overview

The metrics framework provides **automated, measurable validation** of agentic documentation quality through:

1. **Navigation Depth**: Link graph analysis from AGENTS.md
2. **Context Budget**: Documentation lines loaded per workflow
3. **Structure Compliance**: Required files/directories exist
4. **Documentation Coverage**: ADR, concept, and plan counts

## Installation

### Method 1: Copy Scripts (Recommended)

```bash
# From your repository root
GUIDE_PATH="/path/to/agentic-guide"
mkdir -p agentic/scripts
cp "$GUIDE_PATH/scripts/"*.py agentic/scripts/
cp "$GUIDE_PATH/scripts/"*.sh agentic/scripts/
chmod +x agentic/scripts/*.sh
```

### Method 2: Symlink (For Development)

```bash
# Link to framework scripts (updates automatically)
mkdir -p agentic
ln -s /path/to/agentic-guide/scripts agentic/scripts
```

### Method 3: Git Submodule

```bash
git submodule add https://github.com/openshift/agentic-guide.git .agentic-framework
ln -s .agentic-framework/scripts agentic/scripts
```

## Scripts Provided

### 1. `measure-navigation-depth.py`

**Purpose**: Analyze link graph from AGENTS.md

**Usage**:
```bash
python3 agentic/scripts/measure-navigation-depth.py [OPTIONS]

Options:
  --max-depth N         Maximum hop count (default: 3)
  --verbose            Show all document depths
  --fail-on-violation  Exit with error if violations found
```

**Output**:
- Total documents found
- Reachable from AGENTS.md
- Unreachable documents (list)
- Max/average navigation depth
- Documents exceeding depth limit

**Example**:
```
SUMMARY
  Total documents found:     34
  Reachable documents:       17
  Unreachable documents:     17
  Max observed depth:        5 hops
  Docs exceeding limit:      2
```

### 2. `measure-context-budget.py`

**Purpose**: Measure documentation lines loaded for typical workflows

**Usage**:
```bash
python3 agentic/scripts/measure-context-budget.py [OPTIONS]

Options:
  --max-budget N       Maximum lines per workflow (default: 700)
  --fail-on-violation  Exit with error if budget exceeded
```

**Customization**: Edit `WORKFLOWS` list in the script to add repo-specific workflows.

**Output**:
- Per-workflow line counts
- Pass/fail status
- File breakdown for failing workflows

**Example**:
```
Feature Implementation
  Status: ❌ OVER (1174/700 lines, 9 files)
  Files loaded:
    -  214 lines: agentic/domain/concepts/machine-config-pool.md
    -  182 lines: agentic/domain/concepts/machine-config.md
```

### 3. `generate-metrics-dashboard.py`

**Purpose**: Generate HTML dashboard with visual metrics

**Usage**:
```bash
python3 agentic/scripts/generate-metrics-dashboard.py [OPTIONS]

Options:
  --output PATH  Output HTML file (default: agentic/metrics-dashboard.html)
  --open        Open in browser after generation
```

**Output**: Beautiful HTML dashboard with:
- Circular score display (0-100)
- Color-coded metrics cards
- Workflow breakdown
- Progress bars
- Responsive design

### 4. `measure-all-metrics.sh`

**Purpose**: Run all metrics and generate reports

**Usage**:
```bash
./agentic/scripts/measure-all-metrics.sh [OPTIONS]

Options:
  --generate-reports  Generate METRICS_REPORT.md and update QUALITY_SCORE.md
  --html             Generate HTML dashboard
  --help             Show help message
```

**Output**:
- Terminal dashboard with all metrics
- Optional: METRICS_REPORT.md
- Optional: metrics-dashboard.html

### 5. `test-metrics.sh`

**Purpose**: Validate metrics calculations are correct

**Usage**:
```bash
./agentic/scripts/test-metrics.sh
```

**Tests**:
1. Math consistency (total = reachable + unreachable)
2. Reasonable depth (≤10 hops)
3. Workflows defined (≥3)
4. AGENTS.md valid (≤150 lines)
5. Scripts exist
6. Dashboard generates

## Metrics Explained

### Navigation Depth

**What it measures**: Link distance from AGENTS.md to all documentation

**Why it matters**:
- Enforces progressive disclosure
- Prevents deep link chains
- Ensures discoverability

**Targets**:
- Max depth: ≤3 hops
- Average depth: ≤2 hops
- Unreachable: 0

**Calculation**:
1. Parse all markdown files
2. Build directed graph of links
3. BFS from AGENTS.md
4. Report shortest path to each doc

**How to fix violations**:
- **Unreachable docs**: Add links from AGENTS.md or index files
- **Docs >3 hops**: Create intermediate index or link directly

### Context Budget

**What it measures**: Total documentation lines loaded for typical workflows

**Why it matters**:
- Prevents context window overflow
- Correlates with agent performance
- Identifies bloated documentation

**Targets** (based on OpenAI harness engineering):
- Bug fix (simple): ≤400 lines
- Bug fix (complex): ≤700 lines
- Feature implementation: ≤700 lines
- System understanding: ≤500 lines

**Calculation**:
1. Define workflow navigation paths
2. Load all files in path
3. Count non-empty lines (excluding frontmatter)
4. Report total and per-file breakdown

**How to fix violations**:
- Split large files (>200 lines)
- Remove unnecessary links
- Benchmark if higher budget helps performance
- Use progressive disclosure

### Structure Compliance

**What it measures**: Required files and directories exist

**Checks**:
- AGENTS.md ≤150 lines
- Required directories exist
- Index files present
- YAML frontmatter on required docs

### Documentation Coverage

**What it measures**: Completeness across categories

**Metrics**:
- ADRs: ≥3
- Domain concepts: ≥2
- Execution plans: ≥1

## Customization

### Repository-Specific Workflows

Edit `measure-context-budget.py`:

```python
WORKFLOWS = [
    # Standard workflows
    Workflow(
        name="Bug Fix (Simple)",
        description="Find and fix a bug",
        files=[
            'AGENTS.md',
            'ARCHITECTURE.md',
            'agentic/DEVELOPMENT.md'
        ]
    ),

    # Add your repo-specific workflow
    Workflow(
        name="CRD Design Review",
        description="Review a new Custom Resource Design",
        files=[
            'AGENTS.md',
            'agentic/design-docs/crd-patterns.md',
            'agentic/references/k8s-api-conventions.md'
        ]
    ),
]
```

### Navigation Depth Limits

Adjust based on repo complexity:

```bash
# Simpler repo - stricter limit
python3 agentic/scripts/measure-navigation-depth.py --max-depth 2

# Complex repo - relaxed limit
python3 agentic/scripts/measure-navigation-depth.py --max-depth 4
```

### Context Budget Limits

Adjust based on benchmarking:

```bash
# Lower budget for faster agents
python3 agentic/scripts/measure-context-budget.py --max-budget 500

# Higher budget if justified by performance data
python3 agentic/scripts/measure-context-budget.py --max-budget 1000
```

## CI Integration

### GitHub Actions

Create `.github/workflows/validate-agentic-docs.yml`:

```yaml
name: Validate Agentic Documentation

on:
  pull_request:
    paths:
      - 'agentic/**'
      - '*.md'

jobs:
  metrics:
    name: Measure Navigation Metrics
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Measure navigation depth
        run: |
          python3 agentic/scripts/measure-navigation-depth.py --max-depth 3 --fail-on-violation

      - name: Measure context budget
        run: |
          python3 agentic/scripts/measure-context-budget.py --max-budget 700 --fail-on-violation

      - name: Generate dashboard
        run: |
          python3 agentic/scripts/generate-metrics-dashboard.py --output docs/metrics.html

      - name: Upload dashboard
        uses: actions/upload-artifact@v3
        with:
          name: metrics-dashboard
          path: docs/metrics.html
```

## Validation Protocol (REQUIRED)

Before adopting, **measure impact on agent performance**:

### 1. Select Benchmark Set

25-50 historical PRs/issues (mix of bugs, features, refactoring)

### 2. Test Conditions

- **Baseline**: Code only
- **Minimal**: AGENTS.md only
- **Full**: Complete agentic framework

### 3. Measure

- Success rate (tests pass, correct solution)
- Token cost per task
- Steps to solution

### 4. Accept Only If

- Success >baseline+10% OR
- Cost <baseline-15% OR
- Metrics improve AND success within 5% of baseline

### 5. If Fails

Use minimal approach or abandon. **No vibes, only data.**

## Troubleshooting

### "Navigation depth script not found"

```bash
# Check script location
ls -la agentic/scripts/measure-navigation-depth.py

# If missing, copy from framework
cp /path/to/agentic-guide/scripts/*.py agentic/scripts/
```

### "Total ≠ Reachable + Unreachable"

This indicates a bug in the script. Run validation:

```bash
./agentic/scripts/test-metrics.sh
```

If tests fail, the scripts may be outdated. Update from framework.

### "Context budget seems wrong"

Check that frontmatter is being excluded:

```bash
python3 -c "
from pathlib import Path
with open('agentic/DESIGN.md') as f:
    lines = [l.strip() for l in f if l.strip()]
    # Should exclude --- frontmatter ---
    print(f'Total lines: {len(lines)}')
"
```

### "Workflows not found"

Edit `WORKFLOWS` list in `measure-context-budget.py` to match your repo structure.

## FAQ

**Q: Why 3 hops specifically?**

A: Based on OpenAI's harness engineering research. Keeps context budgets ~400-700 lines.

**Q: Can I change the limits?**

A: Yes! Pass `--max-depth` and `--max-budget` flags. But benchmark first - arbitrary changes may hurt performance.

**Q: What if metrics pass but agent performance is poor?**

A: Metrics are necessary but not sufficient. Run benchmarking protocol. Real performance trumps metrics.

**Q: How often should I measure?**

A:
- Every PR (CI automation)
- After restructuring docs (manual)
- Quarterly benchmarking (comprehensive)

## References

- [OpenAI Harness Engineering](https://openai.com/index/harness-engineering/)
- [AGENTIC_DOCS_FRAMEWORK.md](./AGENTIC_DOCS_FRAMEWORK.md)
- [AGENTIC_DOCS_RULEBOOK.md](./AGENTIC_DOCS_RULEBOOK.md)

---

**Framework Version**: 1.0
**Last Updated**: 2026-03-27
