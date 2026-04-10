# Using Agentic Framework Scripts

This repository uses scripts from the [openshift/agentic-guide](https://github.com/openshift/agentic-guide) framework.

## Scripts Location

Scripts are located in `agentic/scripts/` and were copied from the framework:

```
agentic/scripts/
├── measure-navigation-depth.py     # Link graph analysis
├── measure-context-budget.py       # Workflow context tracking
├── generate-metrics-dashboard.py   # HTML dashboard generator
├── measure-all-metrics.sh          # Comprehensive metrics runner
└── test-metrics.sh                 # Validation tests
```

## Updating Scripts

When the framework is updated, re-sync scripts.

### Safe to Update (No Customization)

These scripts can be blindly copied from the framework - they have no repository-specific customizations:

```bash
GUIDE_PATH="/path/to/agentic-guide"

# Safe to update (generic algorithms/visualization)
cp "$GUIDE_PATH/scripts/measure-navigation-depth.py" agentic/scripts/
cp "$GUIDE_PATH/scripts/generate-metrics-dashboard.py" agentic/scripts/
cp "$GUIDE_PATH/scripts/measure-all-metrics.sh" agentic/scripts/
cp "$GUIDE_PATH/scripts/test-metrics.sh" agentic/scripts/
chmod +x agentic/scripts/*.sh
```

### Contains Customizations (Review Before Update)

**⚠️ CAREFUL**: `measure-context-budget.py` contains **[REPO-NAME]-specific workflows**.

Before updating, review changes:

```bash
# Compare framework version with your customized version
diff "$GUIDE_PATH/scripts/measure-context-budget.py" agentic/scripts/measure-context-budget.py

# If framework has bug fixes you need, merge manually
# DO NOT blindly overwrite - you'll lose your workflow customizations
```

## Customizations for [REPO-NAME]

**IMPORTANT**: [REPO-NAME] has customized the framework scripts. Do NOT blindly overwrite `measure-context-budget.py` with framework updates.

### Workflows (Customized)

The `measure-context-budget.py` script includes **[REPO-NAME]-specific workflows** (customized from framework template).

**Example workflow** (yours will differ):
```python
Workflow(
    name="Feature Implementation",
    files=[
        'AGENTS.md',
        'ARCHITECTURE.md',
        'agentic/design-docs/core-beliefs.md',
        # [REPO-NAME]-specific domain concepts:
        'agentic/domain/concepts/your-concept-1.md',
        'agentic/domain/concepts/your-concept-2.md',
        # [REPO-NAME]-specific ADRs:
        'agentic/decisions/adr-0001-your-decision.md',
        'agentic/DESIGN.md',
        'agentic/DEVELOPMENT.md',
        'agentic/TESTING.md'
    ]
)
```

These workflows are customized per-repository and should NOT be overwritten when updating other scripts.

## Framework Documentation

Full documentation available in the framework repository:

- **Metrics Guide**: `agentic-guide/METRICS_GUIDE.md`
- **Installation**: `agentic-guide/INSTALLATION.md`
- **Scripts README**: `agentic-guide/scripts/README.md`
- **Scoring Guide**: `agentic-guide/SCORING_GUIDE.md`
- **Second Pass Guide**: `agentic-guide/SECOND_PASS_GUIDE.md`

## Version

**Framework Version**: [FRAMEWORK-VERSION]
**Repository Copy Date**: [COPY-DATE]

## Validation

Verify scripts are working correctly:

```bash
./agentic/scripts/test-metrics.sh
```

Should output:
```
✓ ALL TESTS PASSED
```

## Summary

| Script | Status | Update Strategy |
|--------|--------|-----------------|
| `measure-navigation-depth.py` | Generic | ✅ Safe to copy from framework |
| `generate-metrics-dashboard.py` | Generic | ✅ Safe to copy from framework |
| `measure-all-metrics.sh` | Generic | ✅ Safe to copy from framework |
| `test-metrics.sh` | Generic | ✅ Safe to copy from framework |
| `measure-context-budget.py` | **Customized** | ⚠️ Review diffs, merge manually |

---

**Note**: These scripts are templates from the framework. Changes made to `measure-context-budget.py` are local to [REPO-NAME] and won't affect other repositories using the framework.
