# Agentic Documentation - Second Pass Refinement Guide

**For AI Agents: Metrics-Driven Documentation Improvement**

**When to use this**: After completing initial agentic documentation implementation (AGENTIC_DOCS_RULEBOOK.md), run this second pass to achieve >80% quality score (Good rating).

**Note**: Scoring is strict - ANY violation results in penalty. 80-89 = Good, 90+ = Excellent.

---

## Prerequisites

✅ You have completed [AGENTIC_DOCS_RULEBOOK.md](./AGENTIC_DOCS_RULEBOOK.md) implementation (first pass)
✅ **⚠️ CRITICAL**: You have run Phase 7 from the rulebook (generated metrics dashboard)
✅ **You have the dashboard file** `agentic/metrics-dashboard.html` from first pass
✅ **You have reviewed your ACTUAL MEASURED score** in the dashboard (not an estimate!)
✅ **Your score is <90** and you want to improve it (otherwise second pass is optional)
✅ Structure validation passes (`./VALIDATION_SCRIPT.sh`)
✅ Metrics scripts are installed at `agentic/scripts/`

**⚠️ If you skipped Phase 7 in first pass:**
- Go back to [AGENTIC_DOCS_RULEBOOK.md Phase 7](./AGENTIC_DOCS_RULEBOOK.md#phase-7-generate-metrics-dashboard-first-pass-completion-)
- Run `./agentic/scripts/measure-all-metrics.sh --html`
- Review the dashboard to get your baseline score
- Then return here with your actual measured score

**Why run second pass?**
- Score 80-89 (Good): Optional, for reaching Excellent (90+)
- Score 70-79 (Fair): Recommended, to reach Good/Excellent
- Score <70 (Poor/Critical): Required, significant gaps exist

**If your score is 90+**: Congratulations! Second pass is optional - you already have excellent documentation.

---

## Phase 0: Customize Workflows for Your Repository (REQUIRED)

**CRITICAL**: Before measuring metrics, you MUST customize the workflows in `measure-context-budget.py` to match your repository's actual documentation.

### Why This Matters

The framework provides **generic template workflows** that reference placeholder files like `agentic/domain/glossary.md`. If you don't customize these, metrics will fail because:
- Your repository has different domain concepts
- Your ADRs have different names
- Generic placeholders don't exist in your repo

### Step 0.1: Edit Workflow Definitions

Open `agentic/scripts/measure-context-budget.py` and find the `WORKFLOWS` section (around line 80).

### Step 0.2: Replace Generic Placeholders

**Generic template** (won't work for your repo):
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

**Customized for YOUR repository**:
```python
Workflow(
    name="Feature Implementation",
    files=[
        'AGENTS.md',
        'ARCHITECTURE.md',
        # ✅ Replace with YOUR actual domain concepts:
        'agentic/domain/concepts/your-main-concept.md',
        'agentic/domain/concepts/your-secondary-concept.md',
        # ✅ Add YOUR key architectural decisions:
        'agentic/decisions/adr-0001-your-first-major-decision.md',
        'agentic/DESIGN.md',
        'agentic/DEVELOPMENT.md',
        'agentic/TESTING.md'
    ]
)
```

### Step 0.3: Identify Your Key Documents

For each workflow, include documents that agents would **actually load** for that task:

**Bug Fix (Simple)** - Minimal context:
- AGENTS.md (navigation)
- ARCHITECTURE.md (component map)
- agentic/DEVELOPMENT.md (debugging guide)

**Bug Fix (Complex)** - Add domain knowledge:
- Above, plus your 1-2 most referenced domain concepts
- Testing guide

**Feature Implementation** - Comprehensive:
- Above, plus core-beliefs.md
- Your 2-3 key domain concepts
- Your 1-2 most important ADRs
- Design, development, testing guides

**Understanding System** - Learning:
- AGENTS.md, ARCHITECTURE.md
- Core beliefs
- Domain glossary or key concepts

**Security Review** - Focused:
- AGENTS.md
- agentic/SECURITY.md
- Core beliefs (for context)

### Step 0.4: Verify Customization

```bash
# Check that all referenced files exist (OS-agnostic)
cd agentic/scripts
python3 -c "
import re, os
with open('measure-context-budget.py') as f:
    content = f.read()
    files = re.findall(r\"'([^']+\.md)'\", content)
    missing = [f for f in sorted(set(files)) if not os.path.exists(f'../../{f}')]
    if missing:
        print('⚠️  Missing files (create these in Phase 1):')
        for f in missing:
            print(f'   - {f}')
    else:
        print('✅ All workflow files exist')
"
cd ../..
```

**Expected**: Either "All workflow files exist" or a list of files to create. If missing files exist, you'll create them during normal documentation in Phase 1.

---

## Phase 1: Measure Current State

### Step 1: Run All Metrics

```bash
# Navigate to repository root (auto-detected)
cd "$(git rev-parse --show-toplevel)"

# Run comprehensive metrics with HTML dashboard
./agentic/scripts/measure-all-metrics.sh --html
```

**Review the output for:**
- Navigation depth violations
- Context budget violations
- Unreachable documents
- Missing documentation

### Step 2: Generate Dashboard

```bash
firefox agentic/metrics-dashboard.html
```

**Identify the top 3 gaps** based on color coding:
- 🔴 Red (0-60): Critical - fix immediately
- 🟡 Yellow (61-80): Warning - should fix
- 🔵 Blue (81-90): Good - optional improvement
- 🟢 Green (91-100): Excellent - no action needed

---

## Phase 2: Fix Navigation Depth Issues

**Target**: All documents reachable from AGENTS.md in ≤3 hops

### Step 2.1: Identify Unreachable Documents

Run:
```bash
python3 agentic/scripts/measure-navigation-depth.py
```

Look for section: **❌ UNREACHABLE DOCUMENTS**

Example output:
```
❌ UNREACHABLE DOCUMENTS
----------------------------------------------------------------------
  agentic/README.md
  agentic/RELIABILITY.md
  agentic/SECURITY.md
  agentic/decisions/index.md
  agentic/domain/index.md
```

### Step 2.2: Fix Strategy

**For each unreachable document, choose ONE:**

#### Option A: Link from AGENTS.md (1 hop)
Use for critical, frequently-needed docs.

```markdown
# AGENTS.md

## Security
- [Security Guidelines](./agentic/SECURITY.md) - Security review process
```

**Limitation**: AGENTS.md is limited to 150 lines - don't overload it.

#### Option B: Link from Intermediate Document (2-3 hops)
Use for specialized docs.

Example: Link `agentic/RELIABILITY.md` from `agentic/TESTING.md`:
```markdown
# agentic/TESTING.md

## Related
- [Reliability Standards](./RELIABILITY.md) - SLOs, monitoring, incident response
```

#### Option C: Link from Index Files
Use index files as hubs for related docs.

Example: `agentic/decisions/index.md`:
```markdown
# Architecture Decision Records

## Index
- [ADR-0001: Use Ignition for Configuration](./adr-0001-use-ignition-for-configuration.md)
- [ADR-0002: Separate MachineConfig and MachineConfigPool](./adr-0002-separate-mc-mcp.md)
- [Template](./adr-template.md) - Use this for new ADRs
```

Then link the index from AGENTS.md:
```markdown
# AGENTS.md

## Architecture Decisions
- [ADR Index](./agentic/decisions/index.md) - All architecture decision records
```

### Step 2.3: Fix Documents Exceeding Max Depth

Run:
```bash
python3 agentic/scripts/measure-navigation-depth.py
```

Look for: **⚠️ DOCS EXCEEDING 3 HOPS**

Example:
```
⚠️  DOCS EXCEEDING 3 HOPS
----------------------------------------------------------------------
  5 hops: docs/onclusterlayering-troubleshooting.md
  4 hops: docs/onclusterlayering-quickstart.md
```

**Fix**: Create shorter path by linking from an intermediate document.

Example:
- Current path: AGENTS.md → ARCHITECTURE.md → agentic/domain/concepts/on-cluster-layering.md → docs/onclusterlayering.md → docs/onclusterlayering-troubleshooting.md (5 hops)
- Better path: AGENTS.md → ARCHITECTURE.md → docs/onclusterlayering-troubleshooting.md (3 hops)

Add link in ARCHITECTURE.md:
```markdown
# ARCHITECTURE.md

## On-Cluster Layering
- [Troubleshooting Guide](./docs/onclusterlayering-troubleshooting.md)
```

### Step 2.4: Validate Fix

```bash
python3 agentic/scripts/measure-navigation-depth.py
```

Should show:
```
✅ PASSED: All docs ≤3 hops, 0 unreachable
```

---

## Phase 3: Fix Context Budget Issues

**Target**: All workflows ≤700 lines (tune based on benchmarking)

### Step 3.1: Identify Over-Budget Workflows

Run:
```bash
python3 agentic/scripts/measure-context-budget.py
```

Look for: **Status: ❌ OVER**

Example:
```
Feature Implementation
  Implement a new feature with design review
  Status: ❌ OVER (1174/700 lines, 9 files)
  Files loaded:
    -   92 lines: AGENTS.md
    -  126 lines: ARCHITECTURE.md
    -  138 lines: agentic/design-docs/core-beliefs.md
    -  182 lines: agentic/domain/concepts/machine-config.md
    -  214 lines: agentic/domain/concepts/machine-config-pool.md
    -   85 lines: agentic/decisions/adr-0001-use-ignition-for-configuration.md
    -   82 lines: agentic/DESIGN.md
    -  139 lines: agentic/DEVELOPMENT.md
    -  116 lines: agentic/TESTING.md
```

Total: 1174 lines (over by 474 lines)

### Step 3.2: Fix Strategy

**Choose ONE approach:**

#### Option A: Split Large Files (Recommended)
Identify largest files (>150 lines) and split them.

Example: Split `agentic/domain/concepts/machine-config-pool.md` (214 lines):
```
agentic/domain/concepts/machine-config-pool.md (50 lines - overview)
agentic/domain/concepts/machine-config-pool-architecture.md (80 lines)
agentic/domain/concepts/machine-config-pool-operations.md (84 lines)
```

Update workflow to only load overview:
```python
Workflow(
    name="Feature Implementation",
    files=[
        'AGENTS.md',
        'ARCHITECTURE.md',
        'agentic/design-docs/core-beliefs.md',
        'agentic/domain/concepts/machine-config-pool.md',  # Now only 50 lines
        # ... removed detailed files
    ]
)
```

#### Option B: Remove Non-Essential Files
Review workflow definition - are ALL files necessary?

Example: Remove ADR if not critical for feature implementation:
```python
# Before (1174 lines)
files=[
    'AGENTS.md',
    'ARCHITECTURE.md',
    'agentic/design-docs/core-beliefs.md',
    'agentic/domain/concepts/machine-config.md',
    'agentic/domain/concepts/machine-config-pool.md',
    'agentic/decisions/adr-0001-use-ignition-for-configuration.md',  # 85 lines - remove?
    'agentic/DESIGN.md',
    'agentic/DEVELOPMENT.md',
    'agentic/TESTING.md',
]

# After (1089 lines) - still over
```

#### Option C: Increase Budget Limit (Last Resort)
Only if benchmarking proves higher budget is acceptable.

```bash
python3 agentic/scripts/measure-context-budget.py --max-budget 1200
```

**CRITICAL**: Must validate with 25-50 task benchmark that higher budget doesn't hurt performance.

### Step 3.3: Validate Fix

```bash
python3 agentic/scripts/measure-context-budget.py
```

Should show:
```
✅ PASSED: All workflows ≤700 lines
```

---

## Phase 4: Improve Documentation Coverage

**Target**: At least 3 ADRs, 3 domain concepts, 1 active exec-plan

### Step 4.1: Check Current Coverage

Run:
```bash
./agentic/scripts/measure-all-metrics.sh
```

Look for: **4. DOCUMENTATION COVERAGE**

Example:
```
  ADRs documented: 1       ← Need 2 more
  Domain concepts: 2       ← Need 1 more
  Execution plans: 0 active, 0 completed  ← Need 1 active
  Coverage score: 60/100 🟡 WARNING
```

### Step 4.2: Add Missing ADRs

**Identify 2-3 significant architectural decisions** from git history or code:

```bash
# Find major architectural choices
git log --all --oneline --grep="architecture\|design\|decision" | head -20
```

**Create ADRs** for each:
```bash
cd agentic/decisions
cp adr-template.md adr-0002-separate-controller-daemon.md
```

Fill in:
```markdown
---
status: accepted
date: 2025-11-15
deciders: @architect1, @lead-developer
---

# ADR-0002: Separate Controller and Daemon Components

## Context
We need to manage both cluster-wide config (controller) and per-node operations (daemon).

## Decision
Split into MachineConfigController (watches API) and MachineConfigDaemon (runs on nodes).

## Consequences
- **Positive**: Clear separation of concerns, independent scaling
- **Negative**: More complexity in deployment
```

### Step 4.3: Add Missing Domain Concepts

**Identify 2-3 core domain concepts** not yet documented:

```bash
# Look for commonly-used types/structs
grep -r "type.*struct" pkg/ | head -20
```

**Create concept docs**:
```bash
cd agentic/domain/concepts
touch machine-config-daemon.md
```

Fill in with YAML frontmatter:
```markdown
---
aliases: [MCD, daemon]
related: [machine-config.md, machine-config-pool.md]
---

# MachineConfigDaemon

## What It Is
Per-node agent that applies MachineConfigs to the operating system.

## How It Works
...
```

### Step 4.4: Create Active Exec-Plan

**For current or planned work**, create an exec-plan:

```bash
cd agentic/exec-plans/active
cp ../template.md improve-logging-2026-03.md
```

Fill in:
```markdown
---
status: active
created: 2026-03-27
updated: 2026-03-27
assignee: @your-username
---

# Improve Logging for Debugging

## Goal
Add structured logging to MachineConfigDaemon for easier debugging.

## Context
Current logs are unstructured, making debugging difficult.

## Plan
1. Adopt zap structured logger
2. Add trace IDs to all operations
3. Log state transitions

## Acceptance Criteria
- [ ] All operations use structured logging
- [ ] Trace IDs in all log lines
- [ ] State transitions logged
```

### Step 4.5: Validate Coverage

```bash
./agentic/scripts/measure-all-metrics.sh
```

Should show:
```
  ADRs documented: 3
  Domain concepts: 3
  Execution plans: 1 active
  Coverage score: 100/100 ✅ GOOD
```

---

## Phase 5: Final Validation and Metrics Re-measurement

⚠️ **MANDATORY**: You MUST re-run Phase 7 (metrics dashboard) to measure improvement from second pass.

### Step 5.1: Re-run All Metrics (Phase 7 from Rulebook)

This is the **same Phase 7 from the first pass** - you're running it again to measure improvement.

```bash
# Navigate to repository root
cd "$(git rev-parse --show-toplevel)"

# Re-generate metrics dashboard with improvements
./agentic/scripts/measure-all-metrics.sh --html
```

**What this does**:
- Re-calculates all metrics based on your second pass changes
- Generates updated `agentic/metrics-dashboard.html`
- Shows before/after comparison in your commit message

### Step 5.2: Review Updated Dashboard

Open the regenerated dashboard:
```bash
firefox agentic/metrics-dashboard.html
# Or: chrome agentic/metrics-dashboard.html
# Or: open agentic/metrics-dashboard.html  (macOS)
```

**Check improvements**:

**Target scores:**
- 🟢 Navigation Depth: 100 (all docs ≤3 hops, 0 unreachable) or 🔵 50 (1-2 minor violations)
- 🟢 Context Budget: 100 (all workflows ≤700 lines) or 🔵 75 (1-2 workflows slightly over)
- 🟢 Structure Compliance: 100 (always passes after first pass)
- 🟢 Documentation Coverage: 100 (≥3 ADRs, ≥3 concepts, ≥1 exec-plan)

**Overall targets:**
- **≥90**: Excellent - no violations
- **≥80**: Good - minor violations acceptable (e.g., 1 unreachable, 1 over-budget)
- **≥70**: Fair - needs improvement
- **<70**: Poor - significant issues

### Step 5.3: Run Validation Tests

```bash
./agentic/scripts/test-metrics.sh
```

Should show:
```
✓ ALL TESTS PASSED
```

### Step 5.4: Update QUALITY_SCORE.md with New Measurements

Document your improvement in `agentic/QUALITY_SCORE.md`:

```markdown
### Second Pass Completion: YYYY-MM-DD

**Score Change**: X/100 → Y/100 (+Z points)

**What Changed**:
- Fixed navigation depth violations (before: N unreachable, after: M unreachable)
- Fixed context budget violations (before: N over, after: M over)
- Added N ADRs, M concepts, K exec-plans

**Measured by**: ./agentic/scripts/measure-all-metrics.sh --html
**Dashboard**: agentic/metrics-dashboard.html (generated YYYY-MM-DD)
```

**Also update manual metrics** (if you haven't already):
- Find "Quality Metrics" section in QUALITY_SCORE.md
- Replace placeholder percentages (e.g., "60% documented") with actual values
- Rename section to "Additional Quality Tracking (Manual - Not Scored)"
- Add "Last Audited: YYYY-MM-DD"

This prevents stale placeholders from misleading future maintainers.

### Step 5.5: Commit Changes

⚠️ **Use your ACTUAL MEASURED scores** from the dashboard (not estimates!)

```bash
git add agentic/ AGENTS.md ARCHITECTURE.md
git commit -m "docs: second pass - improve metrics to Y/100

- Fixed navigation depth: linked N unreachable docs
- Fixed context budget: split large files (saved N lines)
- Added N ADRs, M concepts, K exec-plans
- Overall quality score: X/100 → Y/100 (+Z improvement)

Measured by: ./agentic/scripts/measure-all-metrics.sh --html
Dashboard: agentic/metrics-dashboard.html

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Troubleshooting

### "Navigation depth won't improve"

**Problem**: Documents remain unreachable even after adding links.

**Solution**:
1. Verify link syntax: `[Text](./relative/path.md)`
2. Check file exists at that path
3. Re-run measurement script (it caches nothing)

### "Context budget still over after splitting"

**Problem**: Workflows still exceed 700 lines after splitting files.

**Solution**:
1. Check workflow definition in `measure-context-budget.py` - did you update it?
2. Split files more aggressively (aim for <100 lines per file)
3. Consider if ALL files in workflow are necessary

### "Coverage won't reach 100%"

**Problem**: Need more ADRs/concepts but can't find them.

**Solution**:
1. Document FUTURE decisions as ADRs with `status: proposed`
2. Document common questions as concept docs
3. Coverage of 80%+ is acceptable - don't force it

---

## Summary Checklist

After completing second pass:

- [ ] All documents reachable in ≤3 hops from AGENTS.md (or 1-2 acceptable exceptions)
- [ ] Zero or minimal unreachable documents
- [ ] All workflows ≤700 lines (or 1-2 slightly over with justification)
- [ ] At least 3 ADRs documented
- [ ] At least 3 domain concepts documented
- [ ] At least 1 active exec-plan
- [ ] **⚠️ MANDATORY**: Metrics dashboard regenerated (`./agentic/scripts/measure-all-metrics.sh --html`)
- [ ] **⚠️ MANDATORY**: Dashboard reviewed in browser and actual score documented
- [ ] Overall quality score ≥80% (Good rating) - from ACTUAL measurement, not estimate
- [ ] `test-metrics.sh` passes all tests
- [ ] QUALITY_SCORE.md updated with actual measured scores
- [ ] Changes committed with actual measured scores in commit message

---

## 🎉 Second Pass Complete!

**⚠️ CONFIRMATION**: Did you run Phase 5 Step 5.1 (re-run metrics dashboard)?
- ❌ **NO** → Go back and run `./agentic/scripts/measure-all-metrics.sh --html` now
- ✅ **YES** → Continue below with your actual measured improvement

---

## Next Steps

**For repositories <70% after second pass (measured):**
- Run 25-50 task benchmark to validate framework is helping
- Consider if framework is appropriate for your repo type
- Review AGENTIC_DOCS_FRAMEWORK.md for philosophy

**For repositories 70-89% (Fair/Good) - measured:**
- Acceptable for most repositories
- Consider fixing remaining violations if they're easy
- Set up CI to prevent regression (see INSTALLATION.md)
- Monitor metrics monthly (re-run dashboard quarterly)

**For repositories ≥90% (Excellent) - measured:**
- Outstanding! Zero violations
- Set up CI to maintain quality (see INSTALLATION.md)
- Share as example for other teams
- Update as codebase evolves
- Re-run dashboard quarterly to track drift

---

**Framework Version**: 1.0
**Last Updated**: 2026-03-27
