# Agentic Documentation Metrics Scripts

Automated measurement tools for agentic documentation quality.

## Purpose

These scripts provide **measurable, automated validation** that agentic documentation follows best practices from the [OpenAI Harness Engineering](https://openai.com/index/harness-engineering/) framework.

## Scripts

| Script | Purpose | CI-Ready |
|--------|---------|----------|
| `measure-navigation-depth.py` | Link graph analysis from AGENTS.md | ✅ Yes |
| `measure-context-budget.py` | Workflow context line counts | ✅ Yes |
| `generate-metrics-dashboard.py` | HTML dashboard generator | ⚠️ Optional |
| `measure-all-metrics.sh` | Comprehensive metrics runner | ⚠️ Optional |
| `test-metrics.sh` | Validation test suite | ✅ Yes |

## ⚠️ Common Mistakes

**DON'T run .sh files with python:**

```bash
# ❌ WRONG - will cause confusing syntax errors
python3 measure-all-metrics.sh
cd agentic/scripts && python3 measure-all-metrics.sh --html

# ✅ CORRECT - use bash or ./
./agentic/scripts/measure-all-metrics.sh
bash agentic/scripts/measure-all-metrics.sh --html
```

**File types:**
- `.sh` files = **Bash scripts** → use `./script.sh` or `bash script.sh`
- `.py` files = **Python scripts** → use `python3 script.py`

**Typical error when using wrong interpreter:**
```
SyntaxError: closing parenthesis ')' does not match opening parenthesis '['
```
This means you tried to run a `.sh` file with `python3`.

## Installation

### For Repository Adoption

```bash
# From your repository root
cd /path/to/your-repo

# Method 1: Copy scripts (recommended)
mkdir -p agentic/scripts
cp /path/to/agentic-guide/scripts/*.py agentic/scripts/
cp /path/to/agentic-guide/scripts/*.sh agentic/scripts/
chmod +x agentic/scripts/*.sh

# Method 2: Symlink (for development)
ln -s /path/to/agentic-guide/scripts agentic/scripts
```

## Quick Start

```bash
# View all metrics
./agentic/scripts/measure-all-metrics.sh

# Generate HTML dashboard
./agentic/scripts/measure-all-metrics.sh --html
firefox agentic/metrics-dashboard.html

# Run validation tests
./agentic/scripts/test-metrics.sh
```

## Usage

### Navigation Depth Analysis

Measures link distance from AGENTS.md to all documentation.

```bash
python3 agentic/scripts/measure-navigation-depth.py --max-depth 3
```

**Target**: All docs reachable in ≤3 hops

### Context Budget Analysis

Measures documentation lines loaded for typical workflows.

```bash
python3 agentic/scripts/measure-context-budget.py --max-budget 700
```

**Target**: ≤700 lines for feature workflows

### HTML Dashboard

Generates visual metrics dashboard.

```bash
python3 agentic/scripts/generate-metrics-dashboard.py --open
```

### Comprehensive Metrics

Runs all metrics and generates reports.

```bash
./agentic/scripts/measure-all-metrics.sh --generate-reports
```

### Validation Tests

Verifies metrics calculations are correct.

```bash
./agentic/scripts/test-metrics.sh
```

## CI Integration

### Minimal (Structure Only)

```yaml
- name: Validate structure
  run: ./VALIDATION_SCRIPT.sh
```

### Full (With Metrics)

```yaml
- name: Measure navigation
  run: python3 agentic/scripts/measure-navigation-depth.py --fail-on-violation

- name: Measure budget
  run: python3 agentic/scripts/measure-context-budget.py --fail-on-violation
```

## Customization

### Repository-Specific Workflows (REQUIRED)

**CRITICAL**: You MUST customize workflows in `measure-context-budget.py` for your repository.

The framework provides generic placeholders. Replace them with your actual documentation:

```python
WORKFLOWS = [
    Workflow(
        name="Feature Implementation",
        description="Implement a new feature with design review",
        files=[
            'AGENTS.md',
            'ARCHITECTURE.md',
            'agentic/design-docs/core-beliefs.md',
            # ❌ Generic: 'agentic/domain/glossary.md'
            # ✅ Replace with your actual domain concepts:
            'agentic/domain/concepts/your-core-concept.md',
            'agentic/domain/concepts/your-other-concept.md',
            # ✅ Add your repository-specific ADRs:
            'agentic/decisions/adr-0001-your-key-decision.md',
            'agentic/DESIGN.md',
            'agentic/DEVELOPMENT.md',
            'agentic/TESTING.md'
        ]
    ),
]
```

**Why required**: Generic workflows will reference files that don't exist in your repo, causing metrics to fail.

### Adjust Limits

```bash
# Stricter navigation (2 hops)
python3 agentic/scripts/measure-navigation-depth.py --max-depth 2

# Higher budget (1000 lines)
python3 agentic/scripts/measure-context-budget.py --max-budget 1000
```

## Scoring Interpretation

**Overall Quality Score** = Average of 4 metrics:
- **Navigation Depth**: 100 (pass) or 50 (fail)
- **Context Budget**: 100 (pass) or 75 (fail)
- **Structure Compliance**: 100 (pass) or 0 (fail)
- **Documentation Coverage**: 100 (good) or lower

**Score Ranges**:
- **90-100**: Excellent (no violations)
- **80-89**: Good (minor violations acceptable)
- **70-79**: Fair (needs improvement)
- **<70**: Poor (significant issues)

**Example**: 1 unreachable doc + 1 over-budget workflow = 81/100 (Good)
```
Navigation:  50/100 (1 unreachable)
Budget:      75/100 (1 over)
Structure:  100/100 (pass)
Coverage:   100/100 (pass)
───────────────────────────
Overall:     81/100 (Good)
```

## Validation

All scripts include validation tests:

```bash
./agentic/scripts/test-metrics.sh
```

Should output:
```
✓ PASS: Total (34) = Reachable (17) + Unreachable (17)
✓ PASS: Max depth (5) is reasonable
✓ PASS: Found 5 workflows
✓ PASS: AGENTS.md exists and is 119 lines (≤150)
✓ PASS: All required scripts found
✓ PASS: Dashboard generated successfully

✓ ALL TESTS PASSED
```

## Dependencies

- **Python 3.11+** (for scripts)
- **Bash** (for shell scripts)
- **Git** (for repo detection)

No external Python packages required - uses only stdlib!

## Troubleshooting

### Scripts Not Found

```bash
# Verify scripts are in place
ls -la agentic/scripts/

# If missing, copy from framework
cp /path/to/agentic-guide/scripts/* agentic/scripts/
```

### Permission Denied

```bash
chmod +x agentic/scripts/*.sh
```

### Math Doesn't Add Up

Run validation:
```bash
./agentic/scripts/test-metrics.sh
```

If validation fails, scripts may be outdated. Re-copy from framework.

## Documentation

- **Complete guide**: [../METRICS_GUIDE.md](../METRICS_GUIDE.md)
- **Framework**: [../AGENTIC_DOCS_FRAMEWORK.md](../AGENTIC_DOCS_FRAMEWORK.md)
- **Rulebook**: [../AGENTIC_DOCS_RULEBOOK.md](../AGENTIC_DOCS_RULEBOOK.md)

## Contributing

These scripts are part of the agentic-guide framework. To contribute:

1. Test changes against multiple repositories
2. Ensure `test-metrics.sh` passes
3. Update documentation
4. Submit PR to `openshift/agentic-guide`

## Version

**Framework Version**: 1.0
**Last Updated**: 2026-03-27

---

**Questions?** See [METRICS_GUIDE.md](../METRICS_GUIDE.md) or file an issue.
