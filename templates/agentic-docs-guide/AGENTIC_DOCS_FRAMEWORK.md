# Agentic Documentation Framework for OpenShift Repositories

---

## 🎯 HOW TO USE THIS FRAMEWORK

**For AI Agents:** Follow the [AGENTIC_DOCS_RULEBOOK.md](./AGENTIC_DOCS_RULEBOOK.md) step-by-step.

**For Humans:** Read this document for philosophy, use RULEBOOK for implementation.

**Replace ALL placeholders:** `[REPO-NAME]`, `[Component1]`, `[Concept1]`, etc. must be replaced with actual values.

---

## ⚠️ VALIDATE BEFORE ADOPTING

**This framework is experimental.** Context files can reduce agent performance and increase costs. Before adopting:

### Benchmark Protocol (MANDATORY)

1. Select 25-50 historical PRs/issues (mix of bugs, features, refactoring)
2. Test 3 conditions: Baseline (code only), Minimal (AGENTS.md only), Full (complete framework)
3. Measure: Success rate, token cost, steps to solution
4. Accept only if: Success >baseline+10%, Cost <baseline+15%
5. If fails: Use minimal or abandon

Structured docs can hurt performance if done wrong. Test before committing.

---

## Executive Summary

This framework defines how OpenShift repositories should structure documentation for AI agents. Treat **repository knowledge as the system of record** and optimize for **agent legibility**.

**Key principle**: What an agent can't find effectively doesn't exist. Knowledge in Google Docs, Slack, or tribal knowledge is invisible.

**Directory**: Use `agentic/` to avoid conflicts with existing `docs/`.

**Approach**: Progressive disclosure via structured navigation.

---

## Core Principles

### 1. Repository Knowledge is the System of Record

Everything the agent needs must be in-repo, versioned, and discoverable. If it's not in the repository, it doesn't exist to the agent.

**Where knowledge goes:**
- Slack discussions → `agentic/decisions/`
- Google Docs → `agentic/design-docs/`
- Tribal knowledge → `agentic/references/`
- Active work → `agentic/exec-plans/active/`
- Past decisions → `agentic/exec-plans/completed/`

### 2. Optimize for Agent Legibility First

The repository should be optimized for how agents reason:

- **Structured, discoverable** - Clear entry points and navigation
- **Mechanically validated** - CI enforces doc structure and freshness
- **Progressive disclosure** - Start small, navigate deeper
- **Explicit relationships** - Links between concepts, not assumptions

### 3. Enforce Architecture, Not Taste

Enforce boundaries centrally, allow autonomy locally.

- **Strict boundaries** - Layered architecture, dependency rules
- **Mechanical enforcement** - Linters with remediation instructions
- **Golden principles** - Opinionated, mechanical rules that keep the codebase coherent
- **Local freedom** - Within boundaries, agents have autonomy
- **Continuous cleanup** - Background agents scan for drift and open refactoring PRs

### 4. Living Documentation

- **Doc gardening** - Recurring agent scans for staleness
- **CI validation** - Links, structure, freshness checks
- **Auto-generation** - Schemas, API docs from code
- **Quality grades** - Track documentation coverage

---

## Directory Structure for OpenShift Repositories

### Standard Layout (Use `agentic/` to Avoid Conflicts)

```
<repo>/
├── AGENTS.md                          # 100-line table of contents (CRITICAL)
├── ARCHITECTURE.md                    # Top-level system map
├── README.md                          # Human-facing overview (existing)
├── CONTRIBUTING.md                    # Contribution guidelines (existing)
│
├── docs/                              # EXISTING DOCS (preserve as-is)
│   └── [legacy documentation]
│
├── agentic/                           # AGENT-STRUCTURED DOCS
│   ├── design-docs/                   # Architectural design
│   │   ├── index.md                   # Catalog of all designs
│   │   ├── core-beliefs.md            # Operating principles (CRITICAL)
│   │   ├── component-architecture.md  # Component breakdown
│   │   ├── data-flow.md               # How data moves
│   │   └── components/                # Per-component deep dives
│   │
│   ├── domain/                        # Business/technical concepts
│   │   ├── index.md                   # Domain model map
│   │   ├── glossary.md                # Terminology (YAML preferred)
│   │   ├── concepts/                  # Detailed concept docs
│   │   │   └── [concept].md
│   │   └── workflows/                 # User/system flows
│   │       └── [workflow].md
│   │
│   ├── exec-plans/                    # Execution plans (CRITICAL)
│   │   ├── template.md                # Standard format
│   │   ├── active/                    # Work in progress
│   │   ├── completed/                 # Historical record
│   │   └── tech-debt-tracker.md       # Known issues
│   │
│   ├── product-specs/                 # Product specifications
│   │   ├── index.md                   # Feature catalog
│   │   └── [feature-name].md          # Per-feature specs
│   │
│   ├── decisions/                     # ADRs (lightweight)
│   │   ├── index.md                   # ADR catalog
│   │   ├── adr-template.md            # Standard format
│   │   └── adr-NNNN-[title].md
│   │
│   ├── references/                    # External knowledge
│   │   └── [technology]-llms.txt      # LLM-friendly primers
│   │
│   ├── generated/                     # Auto-generated docs
│   │   ├── api-reference.md           # From code
│   │   ├── package-map.md             # From packages
│   │   └── metrics-catalog.md         # From instrumentation
│   │
│   ├── DESIGN.md                      # Design philosophy (REQUIRED)
│   ├── DEVELOPMENT.md                 # Dev environment setup (REQUIRED)
│   ├── TESTING.md                     # Test strategy (REQUIRED)
│   ├── RELIABILITY.md                 # SLOs, observability, reliability (REQUIRED)
│   ├── SECURITY.md                    # Security model, threat model (REQUIRED)
│   └── QUALITY_SCORE.md               # Coverage/completeness tracking (REQUIRED)
│
└── .github/workflows/
    └── validate-agentic-docs.yml      # CI for doc quality
```

**Why `agentic/` instead of `docs/`?**
- Most OpenShift repos already have `docs/` directories
- Avoids reorganization of existing documentation
- Clear namespace separation: existing docs + agent-structured docs
- Visible and discoverable in file browsers

---

## The Critical Files

### 1. AGENTS.md (Table of Contents)

**Purpose**: Single entry point for agents. Points to everything else.
**Length**: ≈100 lines (max 150)
**Tone**: Directive, structured, navigational

**Must contain:**
- What this repository does (1-2 sentences)
- Quick navigation by intent ("I need to understand X" → link)
- Repository structure overview
- Component boundaries (ASCII diagram)
- Core concepts (table with links)
- Key invariants (enforced rules)
- Critical code locations (file path)
- Build & test commands

**Must NOT contain:**
- Detailed explanations (link to `agentic/` instead)
- Long code examples
- Design rationale (goes in `agentic/design-docs/core-beliefs.md`)

### 2. ARCHITECTURE.md (System Map)

**Purpose**: Navigation map with file paths (NOT narrative overview)
**Format**: Tables and structured lists, minimal prose

⚠️ **WARNING**: Narrative overviews ("The system sits between X and Y...") increase token costs without improving task success. Focus on **structure** and **navigation**, not explanations.

**Must contain:**
- Critical code locations **table** (file paths)
- Package layering with **enforced dependency rules**
- Component **entry points** (file paths)
- Data flow (structured list or diagram, not narrative)

**Must NOT contain:**
- Long narrative descriptions of what the system does
- Comprehensive explanations (link to detailed docs instead)
- Generic architectural overviews
- Content that duplicates README.md or existing docs/

**Example - GOOD:**
```markdown
| Component | Entry Point | Critical Code | Purpose |
|-----------|-------------|---------------|---------|
| Operator | cmd/operator/main.go | pkg/operator/sync.go | Lifecycle mgmt |
| Controller | cmd/controller/main.go | pkg/controller/render.go | Config rendering |
```

**Example - BAD:**
```markdown
The Operator orchestrates the lifecycle of all other components,
managing their deployment and configuration across the cluster in a
coordinated fashion...
```

### 3. agentic/design-docs/core-beliefs.md (Operating Principles)

**Purpose**: Encode team philosophy and constraints
**Critical for**: Teaching agents "what good looks like"

**Must contain:**
- Operating principles with rationale
- Non-negotiable constraints (security, reliability, correctness)
- Standard patterns with examples
- Anti-patterns to avoid
- "Golden principles" - opinionated, mechanical rules
- When to break the rules

### 4. agentic/exec-plans/template.md (Execution Plan Format)

**Purpose**: Standard structure for all non-trivial work

**Must contain:**
- YAML frontmatter (status, owner, dates, related issues/PRs)
- Goal (one sentence)
- Success criteria (checkboxes)
- Technical approach
- Implementation phases
- Decision log (track pivots and why)
- Progress notes

---

## Repo-Type Specific Adaptations

**The 6 base files (DESIGN.md, DEVELOPMENT.md, TESTING.md, RELIABILITY.md, SECURITY.md, QUALITY_SCORE.md) are REQUIRED for ALL repos.** The sections below describe additional content per repo type.

### For Kubernetes Operator Repositories

**Additional reference docs** (add to `agentic/references/`):
- `controller-runtime-llms.txt` - How controller-runtime works
- `openshift-operator-patterns-llms.txt` - OCP-specific patterns
- `reconciliation-loops-llms.txt` - Controller pattern deep dive

**Additional design docs** (add to `agentic/design-docs/`):
- `crd-design.md` - Custom resource design decisions
- `controller-architecture.md` - Controller structure

**Top-level content focus**:
- `RELIABILITY.md` - Emphasize SLOs, controller metrics, leader election
- `SECURITY.md` - Document RBAC, admission webhooks, certificate management
- `DESIGN.md` - Explain operator patterns, reconciliation philosophy

### For Library Repositories

**Additional design docs** (add to `agentic/design-docs/`):
- `api-design.md` - Public API philosophy
- `stability-guarantees.md` - What we promise
- `versioning-policy.md` - SemVer and compatibility

**Additional product specs** (add to `agentic/product-specs/`):
- Library usage examples
- Integration patterns

**Top-level content focus**:
- `DESIGN.md` - API design principles, versioning philosophy
- `RELIABILITY.md` - Stability guarantees, deprecation policy
- `SECURITY.md` - Input validation, dependency management

Focus `agentic/domain/concepts/` on public interfaces.

### For Service Repositories

**Additional top-level docs**:
- `agentic/FRONTEND.md` (if applicable) - UI patterns, component library

**Additional product specs** (add to `agentic/product-specs/`):
- User journeys
- Feature specifications

**Top-level content focus**:
- `DESIGN.md` - Service design philosophy, API design
- `RELIABILITY.md` - SLOs, monitoring, alerts, runbooks, incident response
- `SECURITY.md` - Threat model, auth/authz, data protection

---

## What NOT to Document

⚠️ **More documentation ≠ better outcomes.** Be selective about what to add.

### Don't Add:

1. **Comprehensive overviews** - Narrative descriptions add cost without value. Use tables with file paths instead.

2. **Prescriptive instructions** - "Always use X" causes over-compliance. Document patterns with rationale (WHY, not MUST).

3. **Duplicate existing documentation** - Redundant and goes stale. Link with `See: [existing doc](path)`.

4. **Generic build/test commands** - If in README.md, link to it. Only add if complex.

5. **Exhaustive examples** - Agents explore anyway. Use 1-2 canonical examples with file paths.

6. **Step-by-step tutorials** - Better suited for docs/ or wiki. Link to existing tutorials.

### When to Add Documentation

Only add if it provides:
- **Structure**: Glossary, concept relationships, domain model
- **Rationale**: ADRs explaining WHY decisions were made
- **Navigation**: file path references to critical code
- **Constraints**: Invariants that MUST be enforced (with enforcement mechanism)

**If it doesn't fit these categories, don't add it.**

---

## Progressive Loading Strategy

⚠️ **CRITICAL**: Agents should NOT load all documentation at once. Progressive navigation is key to avoiding lost-in-the-middle problems.

### How Agents Should Navigate

**Example Navigation Flow:**

```
AGENTS.md (~150 lines) → Identify component → Load concept doc (~100 lines)
                                           → Load code at file path
                                           → If needed, load relevant ADR (~150 lines)

Total context: ~400 lines for bug fixes, ~700 lines for features
```

### Anti-Pattern (Don't Do This)

❌ Load entire agentic/ directory into context
❌ Read all ADRs before starting
❌ Load ARCHITECTURE.md + all concepts + all workflows upfront

**Result**: 2000+ lines, lost-in-the-middle, reduced performance

### Enforce via AGENTS.md Structure

**Good - Sequential guidance:**
```markdown
**I'm fixing a bug**
→ [Component map](./ARCHITECTURE.md#components)
→ [Debugging guide](./agentic/DEVELOPMENT.md#debugging)
```

**Bad - Encourages bulk loading:**
```markdown
→ See agentic/ directory for comprehensive documentation
```

---

## Mechanical Enforcement

### CI Validation (.github/workflows/validate-agentic-docs.yml)

**Must validate:**
1. AGENTS.md length (< 150 lines)
2. All links are valid (no broken references)
3. Required directories exist (`agentic/{design-docs,domain,exec-plans,product-specs,decisions,references,generated}`)
4. **Required top-level files exist** (`agentic/{DESIGN.md,DEVELOPMENT.md,TESTING.md,RELIABILITY.md,SECURITY.md,QUALITY_SCORE.md}`)
5. Exec-plans/ADRs have YAML frontmatter
6. Index files exist in each directory
7. No stale TODOs (> 30 days without update)
8. Golden principles are documented in core-beliefs.md

### Doc Gardening & Garbage Collection (Automated Maintenance)

**Background agent tasks** (recurring):
1. Find stale code references (file path that no longer exist)
2. Check for undocumented components
3. Validate glossary completeness
4. Update package map (auto-generated)
5. Check ADR freshness
6. Scan for violations of "golden principles"
7. Open targeted refactoring pull requests
8. Update quality grades based on current state

This functions like **garbage collection** for technical debt.

### Quality Scoring

Track in `agentic/QUALITY_SCORE.md`:
- **Coverage**: % of components/concepts documented
- **Freshness**: % of docs updated in last 90 days
- **Completeness**: Required files present
- **Linkage**: Broken links, orphaned docs, max depth from AGENTS.md

**Target**: >80% overall score

### Context Usage Monitoring (Experimental)

**Problem**: Agents can struggle with large contexts due to "lost-in-the-middle" problems.

**Approach**: Monitor context size per task type to understand what works.

#### Baseline Targets (Starting Points)

| Task Type | Suggested Starting Range | Notes |
|-----------|-------------------------|-------|
| Bug fix | 200-400 lines | Measure actual usage, adjust as needed |
| Feature implementation | 400-600 lines | May need more for complex features |
| Code understanding | 150-300 lines | Varies by complexity |
| Refactoring | 300-500 lines | Depends on scope |

**These are guidelines, not hard limits.** Track what actually helps vs. hurts in your benchmarking.

#### How to Monitor

Add to `agentic/QUALITY_SCORE.md`:

```markdown
## Context Usage Analysis (sample of recent tasks)

| Task Type | Avg Context | Success Rate | Notes |
|-----------|-------------|--------------|-------|
| Bug fixes (n=10) | 285 lines | 90% | Within expected range |
| Features (n=10) | 620 lines | 75% | Higher context, lower success - investigate |
| Understanding (n=5) | 180 lines | 95% | Efficient |

**Findings**: Feature tasks may be loading too much context. Test with less.
```

#### What to Track

- Context size correlation with success rate
- Which docs get loaded most frequently
- Where agents get stuck (too much vs. too little info)
- Cost vs. value tradeoff per task type

**Goal**: Learn what helps, iterate on structure. Context size is a **diagnostic**, not a constraint.

---

## Success Metrics

### For a Well-Documented Repo

- ✅ Agent can navigate from AGENTS.md to any concept in ≤3 hops
- ✅ New contributors (human/agent) productive in <1 day
- ✅ Documentation validated on every commit
- ✅ Stale docs detected and fixed automatically
- ✅ Quality score >80% across all domains

### Measured via Benchmarking (See Validation Protocol)

**Task Completion:**
- **Metric**: % of historical tasks completed successfully (tests pass, correct solution)
- **Target**: >85% (baseline + 10%)
- **Measurement**: 50 historical PR/issue benchmark

**Efficiency:**
- **Metric**: Average steps to solution
- **Target**: No more than 15% increase vs. baseline (some overhead acceptable for better outcomes)
- **Measurement**: Agent trace analysis

**Cost:**
- **Metric**: Token usage per task
- **Target**: <15% increase vs. baseline
- **Measurement**: LLM API costs

**Pattern Adherence:**
- **Metric**: % of solutions following core-beliefs.md patterns (when applicable)
- **Target**: >90%
- **Measurement**: Manual code review of sample tasks

**Documentation Health:**
- **Metric**: Quality score (see QUALITY_SCORE.md)
- **Target**: >80%
- **Measurement**: Automated checks (CI validation)

**Validation Frequency:** Run benchmark quarterly. If metrics degrade below targets, audit and prune ineffective documentation.

---

## Migration Guide

### Phase 1: Structure (Week 1)

**Exact Commands (Copy-Paste Ready):**

```bash
#!/bin/bash
# Agentic Documentation Structure Bootstrap
# Run this from repository root

set -e  # Exit on error

echo "Creating agentic documentation structure..."

# Create directory structure (exactly as specified)
mkdir -p agentic/design-docs/components
mkdir -p agentic/domain/concepts
mkdir -p agentic/domain/workflows
mkdir -p agentic/exec-plans/active
mkdir -p agentic/exec-plans/completed
mkdir -p agentic/product-specs
mkdir -p agentic/decisions
mkdir -p agentic/references
mkdir -p agentic/generated

# Create index files
touch agentic/design-docs/index.md
touch agentic/domain/index.md
touch agentic/product-specs/index.md
touch agentic/decisions/index.md
touch agentic/references/index.md

# Create critical files
touch AGENTS.md
touch ARCHITECTURE.md
touch agentic/design-docs/core-beliefs.md
touch agentic/exec-plans/template.md
touch agentic/exec-plans/tech-debt-tracker.md

# Create top-level domain docs (REQUIRED FOR ALL REPOS)
touch agentic/DESIGN.md
touch agentic/DEVELOPMENT.md
touch agentic/TESTING.md
touch agentic/RELIABILITY.md
touch agentic/SECURITY.md
touch agentic/QUALITY_SCORE.md

echo "✅ Structure created successfully"
echo "Next: Populate files using templates from AGENTIC_DOCS_RULEBOOK.md"
```

**Validation:**
```bash
# Verify structure was created correctly
[ -d "agentic/design-docs/components" ] && echo "✅ design-docs" || echo "❌ design-docs missing"
[ -d "agentic/domain/concepts" ] && echo "✅ domain" || echo "❌ domain missing"
[ -d "agentic/exec-plans/active" ] && echo "✅ exec-plans" || echo "❌ exec-plans missing"
[ -d "agentic/product-specs" ] && echo "✅ product-specs" || echo "❌ product-specs missing"
[ -f "AGENTS.md" ] && echo "✅ AGENTS.md" || echo "❌ AGENTS.md missing"
[ -f "ARCHITECTURE.md" ] && echo "✅ ARCHITECTURE.md" || echo "❌ ARCHITECTURE.md missing"

# Verify ALL required top-level files exist (CRITICAL)
for file in DESIGN.md DEVELOPMENT.md TESTING.md RELIABILITY.md SECURITY.md QUALITY_SCORE.md; do
  [ -f "agentic/$file" ] && echo "✅ agentic/$file" || echo "❌ agentic/$file missing (REQUIRED)"
done
```

### Phase 2: Core Docs (Week 2)

**Step-by-step:**
1. Copy AGENTS.md template from RULEBOOK → Replace ALL `[PLACEHOLDERS]`
2. Copy ARCHITECTURE.md template from RULEBOOK → Replace ALL `[PLACEHOLDERS]`
3. Copy core-beliefs.md template from RULEBOOK → Replace ALL `[PLACEHOLDERS]`
4. Verify: `grep -r '\[.*\]' AGENTS.md ARCHITECTURE.md` should return ONLY markdown links, NO placeholders
5. Link to existing `docs/` where relevant (e.g., `See also: [Legacy Docs](./docs/README.md)`)

**Validation Checklist:**
- [ ] AGENTS.md < 150 lines (run: `wc -l AGENTS.md`)
- [ ] No `[PLACEHOLDER]` text remains (run: `grep '\[REPO-NAME\]' AGENTS.md` should be empty)
- [ ] All links valid (run: `markdown-link-check AGENTS.md`)
- [ ] Core beliefs contains golden principles section

### Phase 3: Domain (Week 3)

**Step-by-step:**
1. Copy glossary.md template → Populate with YOUR domain terms (alphabetical)
2. For each major concept (5-10):
   - Copy concept template to `agentic/domain/concepts/[concept-name].md`
   - Replace ALL placeholders
   - Add YAML frontmatter
3. For each workflow (3-5):
   - Copy workflow template to `agentic/domain/workflows/[workflow-name].md`
   - Document step-by-step
4. Create product specs:
   - One file per feature in `agentic/product-specs/[feature-name].md`

**Validation Checklist:**
- [ ] Glossary is alphabetical
- [ ] Each concept has YAML frontmatter (run: `head -n1 agentic/domain/concepts/*.md | grep '^---$'`)
- [ ] All concepts linked from glossary
- [ ] No placeholder text remains (run: `grep -r '\[Concept1\]' agentic/domain/`)

### Phase 4: Automation (Week 4)

**Step-by-step:**
1. Copy CI workflow from RULEBOOK to `.github/workflows/validate-agentic-docs.yml`
2. Test locally:
   ```bash
   # Manual validation before pushing
   wc -l AGENTS.md  # Must be < 150
   find agentic -name "*.md" -exec markdown-link-check {} \;
   ```
3. Create quality score:
   - Copy QUALITY_SCORE.md template
   - Run initial scoring: `make quality-score` (create this target)
4. Set up weekly doc gardening (GitHub Actions schedule or cron)
5. Document golden principles in core-beliefs.md

**Validation Checklist:**
- [ ] CI workflow exists and runs on PR
- [ ] Quality score calculates correctly
- [ ] Doc gardening scheduled (weekly minimum)
- [ ] All checks pass locally before first commit

### Phase 5: Enrichment (Ongoing)
- Convert tribal knowledge to docs
- File active plans for ongoing work
- Create ADRs for past decisions
- Build references for common questions

---

## Summary: What Works and What to Avoid

### What Works

1. **Short AGENTS.md** - ~100 lines, table of contents only
2. **Progressive disclosure** - Navigate, don't overwhelm
3. **Mechanical enforcement** - CI validates, background agents clean up
4. **Repository as source of truth** - Everything versioned, discoverable
5. **Plans as first-class artifacts** - Active, completed, tech debt
6. **Quality grades** - Track coverage, completeness
7. **Golden principles** - Opinionated rules enforced continuously
8. **Garbage collection** - Background agents scan for drift, open cleanup PRs

### What to Avoid

1. ❌ Monolithic documentation files
2. ❌ Knowledge in Slack/Docs/tribal knowledge
3. ❌ Undiscoverable conventions
4. ❌ Stale, unvalidated docs
5. ❌ Overwhelming agents with context
6. ❌ Narrative overviews that don't help navigation
7. ❌ Prescriptive instructions that cause over-compliance
8. ❌ Redundant documentation already in code/comments
9. ❌ Assuming more documentation = better outcomes

---

## Implementation Details

For step-by-step implementation instructions, templates, and validation checklists, see [AGENTIC_DOCS_RULEBOOK.md](./AGENTIC_DOCS_RULEBOOK.md).

---

## Conclusion

**This framework is experimental.** We're betting that structured navigation helps agents, but this is unproven at scale.

**Validate before adopting**: Context files can reduce performance. Use the Benchmark Protocol above before committing.

**The approach**: Treat repository knowledge as a navigable graph with clear entry points, progressive disclosure, and mechanical validation.

**The goal**: Help agents navigate codebases more effectively than with code alone—but only if validation proves it helps. If benchmarking shows it doesn't, use minimal docs or abandon.

**Implementation**: See [AGENTIC_DOCS_RULEBOOK.md](./AGENTIC_DOCS_RULEBOOK.md) for templates and step-by-step instructions.

**Test first, commit second. No vibes, only data.**

---

## Quick Start for Agents

⚠️ **STOP**: Before implementing, read [Validation Protocol](#validation-before-adoption). You **must** benchmark before full adoption.

**To implement this framework in a repository:**

```bash
# 1. Bootstrap structure
mkdir -p agentic/{design-docs/components,domain/{concepts,workflows},exec-plans/{active,completed},product-specs,decisions,references,generated}

# 2. Create all required files (see Phase 1 scripts above)

# 3. Copy templates from RULEBOOK and replace ALL [PLACEHOLDERS]

# 4. Validate
./VALIDATION_SCRIPT.sh

# 5. Commit and enable CI
git add agentic/ AGENTS.md ARCHITECTURE.md .github/workflows/validate-agentic-docs.yml
git commit -m "Add agentic documentation structure"
```

**Critical Success Factors:**
1. ✅ Replace ALL placeholders (run: `grep -r '\[REPO-NAME\]' .` should be empty)
2. ✅ AGENTS.md < 150 lines (run: `wc -l AGENTS.md`)
3. ✅ All links valid (run: `markdown-link-check *.md`)
4. ✅ YAML frontmatter on exec-plans, ADRs, concepts
5. ✅ Validation script passes (run: `./VALIDATION_SCRIPT.sh`)

**For any questions**, refer back to [AGENTIC_DOCS_RULEBOOK.md](./AGENTIC_DOCS_RULEBOOK.md) for detailed templates and examples.
