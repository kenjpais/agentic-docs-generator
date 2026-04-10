# Agentic Documentation Metrics - Scoring Guide

**Understanding the Quality Score**

This document explains how the overall quality score is calculated and what different score ranges mean.

---

## Score Calculation

**Overall Quality Score** = Average of 4 metrics:

```
Score = (Navigation + Budget + Structure + Coverage) / 4
```

### Individual Metric Scores

1. **Navigation Depth** (Link distance from AGENTS.md)
   - ✅ **100 points**: All docs ≤3 hops, 0 unreachable
   - ❌ **50 points**: 1+ unreachable OR 1+ docs >3 hops

2. **Context Budget** (Lines loaded per workflow)
   - ✅ **100 points**: All workflows ≤ limit (default 700 lines)
   - ⚠️ **75 points**: 1+ workflows over limit

3. **Structure Compliance** (Required files exist)
   - ✅ **100 points**: All required files present, AGENTS.md ≤150 lines
   - ❌ **0 points**: Missing required files

4. **Documentation Coverage** (ADRs, concepts, exec-plans)
   - ✅ **100 points**: ≥3 ADRs, ≥3 concepts, ≥1 exec-plan
   - Lower scores based on what's missing

---

## Score Ranges

### 90-100: Excellent 🟢

**Status**: Production-ready, zero violations

**What this means**:
- ALL documents reachable in ≤3 hops
- ALL workflows under context budget
- Complete documentation coverage
- Perfect structure compliance

**Action**: Maintain with CI checks

**Example**:
```
Navigation:  100/100 ✅ (0 unreachable)
Budget:      100/100 ✅ (all workflows ≤700 lines)
Structure:   100/100 ✅ (all files present)
Coverage:    100/100 ✅ (3+ ADRs, 3+ concepts)
────────────────────────────────────────────
Overall:     100/100 (Excellent)
```

### 80-89: Good 🔵

**Status**: Acceptable, minor violations

**What this means**:
- 1-2 documents unreachable (e.g., symlinks, edge cases)
- 1-2 workflows slightly over budget (e.g., complex feature workflows)
- Structure and coverage are complete

**Action**: Accept as-is or fix if easy

**Example**:
```
Navigation:   50/100 ⚠️  (1 unreachable: README.md symlink)
Budget:       75/100 ⚠️  (1 workflow: 914/700 lines)
Structure:   100/100 ✅ (all files present)
Coverage:    100/100 ✅ (3 ADRs, 3 concepts, 1 exec-plan)
────────────────────────────────────────────
Overall:      81/100 (Good)
```

This is the **typical result after second pass** for most repositories.

### 70-79: Fair 🟡

**Status**: Functional but needs improvement

**What this means**:
- Multiple unreachable documents (3-5)
- Multiple workflows over budget (2-3)
- OR missing some coverage (only 1-2 ADRs)

**Action**: Run second pass to improve

**Example**:
```
Navigation:   50/100 ⚠️  (5 unreachable)
Budget:       75/100 ⚠️  (2 workflows over)
Structure:   100/100 ✅
Coverage:     75/100 ⚠️  (only 2 ADRs)
────────────────────────────────────────────
Overall:      75/100 (Fair)
```

### <70: Poor 🔴

**Status**: Significant issues, framework not properly implemented

**What this means**:
- Many unreachable documents (10+)
- Many workflows over budget
- Missing structure files
- Low coverage

**Action**: Re-run first pass, follow RULEBOOK carefully

**Example**:
```
Navigation:   50/100 ❌ (19 unreachable)
Budget:       50/100 ❌ (4 workflows over)
Structure:   100/100 ✅
Coverage:     50/100 ❌ (0 ADRs, 1 concept)
────────────────────────────────────────────
Overall:      63/100 (Poor)
```

This is typical **before second pass** for new implementations.

---

## Common Scenarios

### Scenario 1: "I have 81/100 but terminal shows violations"

**This is correct!** Scoring is strict:

- ANY unreachable doc = -50 points on Navigation
- ANY over-budget workflow = -25 points on Budget

81/100 = "Good" rating means you have 1-2 minor violations, which is acceptable.

### Scenario 2: "My terminal shows 100/100 but HTML shows 62/100"

**Bug (fixed in v1.1)**:

- Old versions checked exit codes, not actual violations
- Fixed: Both now parse output text for PASSED/FAILED
- Update scripts from agentic-guide v1.1+

### Scenario 3: "Can I increase the budget limit to pass?"

**Yes, but**:

1. First try splitting large files (recommended)
2. If truly necessary, increase limit:
   ```bash
   python3 agentic/scripts/measure-context-budget.py --max-budget 1000
   ```
3. **MUST** validate with 25-50 task benchmark
4. Document why higher limit is needed

### Scenario 4: "One symlink is unreachable - is 81/100 acceptable?"

**Yes!** This is a known edge case:

- README.md → docs/README.md symlink
- Link graph follows symlink, but file appears at root
- 81/100 (Good) is acceptable for this scenario

---

## Improving Your Score

### From Poor (<70) → Fair (70-79)

**Focus**: Complete first pass properly

1. Run `./VALIDATION_SCRIPT.sh` - must pass
2. Create 3 ADRs (not just templates)
3. Create 3 concept docs
4. Link major sections from AGENTS.md

**Time**: 1-2 hours

### From Fair (70-79) → Good (80-89)

**Focus**: Fix major violations

1. Run [SECOND_PASS_GUIDE.md](./SECOND_PASS_GUIDE.md)
2. Link unreachable docs from AGENTS.md or indexes
3. Split 1-2 largest files
4. Complete coverage (3+ ADRs, concepts, exec-plans)

**Time**: 30-60 minutes

### From Good (80-89) → Excellent (90-100)

**Focus**: Zero violations

1. Fix remaining unreachable docs
2. Split files to get ALL workflows under budget
3. Verify with strict limits

**Time**: 30-60 minutes

**Worth it?** Only if:
- You want "Excellent" badge
- Repository is a template/example for others
- CI will enforce 90+ as quality gate

Most repositories **don't need 90+** - Good (80-89) is production-ready.

---

## CI Integration

### Block on <80

```yaml
- name: Check metrics quality
  run: |
    SCORE=$(./agentic/scripts/measure-all-metrics.sh | grep "OVERALL" | awk '{print $4}' | cut -d'/' -f1)
    if [ $SCORE -lt 80 ]; then
      echo "❌ Quality score too low: $SCORE/100 (need ≥80)"
      exit 1
    fi
```

### Block on <90 (strict)

```yaml
- name: Check metrics quality (strict)
  run: |
    python3 agentic/scripts/measure-navigation-depth.py --fail-on-violation
    python3 agentic/scripts/measure-context-budget.py --fail-on-violation
```

### Warning only

```yaml
- name: Check metrics quality
  run: ./agentic/scripts/measure-all-metrics.sh
  continue-on-error: true
```

---

## Frequently Asked Questions

### Why is scoring so strict?

**ANY violation = penalty** encourages fixing issues rather than accumulating tech debt.

### What's a "realistic" target score?

- **First pass complete**: 60-70 (Poor/Fair)
- **After second pass**: 80-89 (Good)
- **Perfect implementation**: 90-100 (Excellent)

Most teams target **80+** and accept 1-2 minor violations.

### Should I always aim for 100/100?

**No.** Diminishing returns:

- 80 → 90: Moderate effort, nice to have
- 90 → 100: High effort, rarely worth it

**Exception**: Template repositories or examples for other teams.

### Can scores change over time?

**Yes**, as you add documentation:

- New files may become unreachable
- New workflows may exceed budget
- Run metrics monthly to catch drift

---

**Framework Version**: 1.1
**Last Updated**: 2026-03-27
