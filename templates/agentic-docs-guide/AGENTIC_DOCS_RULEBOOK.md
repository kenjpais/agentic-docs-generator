# Agentic Documentation Rulebook for OpenShift Repositories
## Prescriptive Instructions for Creating Agent-Friendly Documentation

**Version**: 1.1
**Audience**: AI/LLM agents tasked with creating or updating repository documentation
**Goal**: Ensure consistent, navigable, agent-friendly documentation across ALL OpenShift repositories

---

## ⚠️ READ THIS FIRST: VALIDATION REQUIRED

**DO NOT implement this framework without validation.**

Context files can reduce performance and increase costs. Before implementing:

1. **Run benchmark**: 25-50 historical PRs/issues
2. **Compare**: Baseline (code only) vs. Minimal (AGENTS.md) vs. Full (complete framework)
3. **Measure**: Success rate, token cost, steps to solution
4. **Accept only if**: Success >baseline+10%, cost <baseline+15%

See [AGENTIC_DOCS_FRAMEWORK.md § Validation Protocol](./AGENTIC_DOCS_FRAMEWORK.md#validation-before-adoption) for details.

**This framework is experimental.**

---

## 🎯 CRITICAL: PLACEHOLDER CONVENTIONS

**YOU MUST REPLACE ALL PLACEHOLDERS IN FINAL DOCUMENTATION**

### Standard Placeholders (ALWAYS use these exact formats)

```
[REPO-NAME]           → Your repository name (e.g., "machine-config-operator")
[Component1]          → Your component names (e.g., "AuthController", "MachineConfigDaemon")
[Concept1]            → Your domain concepts (e.g., "MachineConfig", "Pod", "CustomResource")
[workflow-name]       → Workflow identifiers (lowercase-with-hyphens)
[feature-name]        → Feature identifiers (lowercase-with-hyphens)
[technology]          → Dependencies (e.g., "kubernetes", "rpm-ostree")
[source-dir]          → Source directory (e.g., "pkg", "cmd", "internal")
[test-dir]            → Test directory (e.g., "test", "tests")
[language]            → Programming language (e.g., "go", "python", "typescript")
YYYY-MM-DD            → Actual dates (e.g., "2026-03-18")
@[username]           → GitHub usernames (e.g., "@johndoe")
#[1234]               → Issue numbers (e.g., "#5628")
[path/to/file.ext]    → File paths (e.g., "pkg/controller/reconcile.go")

⚠️ **IMPORTANT**: DO NOT include line numbers in code references. Line numbers change frequently and create maintenance burden. Use file paths only.
```

### Validation Command (Run After Completing Documentation)

```bash
# This MUST return NO results (except markdown link syntax)
grep -r '\[REPO-NAME\]\|\[Component1\]\|\[Concept1\]' agentic/ AGENTS.md ARCHITECTURE.md

# If the above finds matches, you have NOT replaced all placeholders
```

### Example: Correct vs Incorrect

❌ **INCORRECT** (left placeholder):
```markdown
# [REPO-NAME] - Agent Navigation

## What This Repository Does
[1-2 sentence description]
```

✅ **CORRECT** (replaced placeholder):
```markdown
# machine-config-operator - Agent Navigation

## What This Repository Does
Manages operating system configuration and updates for OpenShift nodes via Kubernetes operators.
```

---

## ⚠️ CRITICAL: CHECK FOR REPOSITORY-TYPE-SPECIFIC GUIDANCE

**BEFORE starting Phase 1**, check if this repository type has additional requirements:

### For OpenShift Repositories

**Detection**: Check if `go.mod` contains `github.com/openshift/api` or `github.com/openshift/library-go`

**If OpenShift repository**:
1. ✅ **READ** [OPENSHIFT_SPECIFIC_GUIDANCE.md](./OPENSHIFT_SPECIFIC_GUIDANCE.md) **COMPLETELY**
2. ✅ **ADD** to your task list: Create OpenShift-specific reference files
3. ✅ **NOTE**: The following are **REQUIRED** (not optional):
   - `agentic/references/enhancement-index.md`
   - `agentic/references/openshift-apis.yaml`
   - `agentic/references/openshift-ecosystem.md`
   - `agentic/references/openshift-operator-patterns-llms.txt`
   - `agentic/references/openshift-docs-standards.md`
   - Enhancement references in ADR frontmatter
   - OpenShift markers in glossary (🔴 ⚫ 🟡)

**Why this matters**: OpenShift repositories need enhancement tracking, API inventory, and ecosystem context. Skipping these files results in incomplete documentation even with a passing quality score.

### For Other Repository Types

Check for additional guidance files:
```bash
ls *_SPECIFIC_GUIDANCE.md 2>/dev/null
```

If found, read them before starting Phase 1.

---

## Principles Before You Start

### Rule 0: Read These First (In Order)
1. **Check for repository-type-specific guidance** (see above)
2. Read this entire rulebook before making any changes
3. Understand the repository's purpose and architecture
4. Identify what documentation already exists
5. Plan your changes before executing
6. VERIFY you understand how to replace placeholders (see above)

### Rule 1: AGENTS.md is a Map, Not a Manual
- **Maximum length**: 150 lines
- **Purpose**: Table of contents that points to deeper knowledge
- **DO NOT**: Put detailed explanations in AGENTS.md
- **DO**: Link to detailed docs elsewhere

### Rule 2: Repository Knowledge is Source of Truth
- **Everything must be in-repo**: No references to Google Docs, Slack, or external systems
- **Everything must be versioned**: Part of git history
- **Everything must be discoverable**: From AGENTS.md in ≤3 hops

### Rule 3: Progressive Disclosure
- Start with high-level navigation
- Let readers drill down into details
- Each document should link to related concepts

### Rule 4: Mechanical Validation
- All documentation must be checkable by CI
- Links must be valid
- Structure must be consistent
- Staleness must be detectable

### Rule 5: Be Selective - Less Can Be More
- Context files can hurt performance if done wrong
- Only document what provides structure, rationale, navigation, or constraints
- Don't duplicate existing docs, code comments, or README
- Avoid narrative overviews and prescriptive instructions
- **When in doubt, leave it out** - measure what helps vs. hurts

### Rule 6: Metrics (Phase 7) Are Mandatory
Phase 7 metrics dashboard is required. "Estimated" scores are not acceptable. See Phase 7.

---

## Step-by-Step Implementation Process

⚠️ **ALL PHASES ARE MANDATORY** - Follow phases 1-7 in order. Skipping phases = incomplete work.

---

### Phase 1: Assessment (READ-ONLY)

⚠️ **DO NOT SKIP THIS PHASE** - Understanding the repository is foundational for all subsequent documentation.

#### Step 1.1: Understand the Repository

**Task**: Analyze the codebase to understand what you're documenting.

**Actions**:
```bash
# 1. Read existing documentation
read: README.md
read: CONTRIBUTING.md if exists
read: docs/README.md if exists
scan: docs/ directory

# 2. Understand the build system
read: Makefile
read: go.mod (for Go repos)
read: package.json (for JS repos)

# 3. Map the code structure
list: cmd/ directory (entry points)
list: pkg/ directory (packages)
list: test/ directory (test organization)

# 4. Identify components
find: main.go files
find: controller files
find: API definitions
```

**Output**: Create a mental model of:
- What the repository does (1 sentence)
- Main components (3-5 max)
- Key technologies (language, frameworks)
- Build/test commands

**Validation**:
- [ ] Can you explain the repo in one sentence?
- [ ] Can you list the main components?
- [ ] Do you know how to build and test?

#### Step 1.2: Inventory Existing Documentation

**Task**: Find all existing documentation.

**Actions**:
```bash
# Find all markdown files
find . -name "*.md" -not -path "./vendor/*" -not -path "./.git/*"

# Find all YAML/JSON config
find . -name "*.yaml" -o -name "*.yml" | grep -v vendor

# Check for existing structure
check: AGENTS.md exists?
check: ARCHITECTURE.md exists?
check: docs/ directory exists?
check: .github/workflows/ has doc validation?
```

**Output**: Create a list of:
- Existing documentation files and their purpose
- Gaps (what's missing)
- Misplaced docs (wrong location)
- Stale docs (outdated content)

**Validation**:
- [ ] You have a complete list of existing docs
- [ ] You know what's missing
- [ ] You can identify what needs to move

#### Step 1.3: Identify Domain Concepts

**Task**: Extract the business/technical concepts this repo deals with.

**Actions**:
```bash
# For Kubernetes operators
find: API definitions in vendor/github.com/openshift/api
read: CRD types (type *Spec, type *Status)

# For libraries
read: Public package interfaces
identify: Main abstractions

# For services
read: API endpoints
identify: Data models
```

**Output**: List of domain concepts (5-15 concepts), each with:
- Name (e.g., "CustomResource")
- Brief definition (1 sentence)
- Where it's defined in code
- Related concepts

**Validation**:
- [ ] Each concept has a clear definition
- [ ] You know where each is used in code
- [ ] You understand relationships between concepts

---

### Phase 2: Structure Creation (CREATE DIRECTORIES)

⚠️ **DO NOT SKIP THIS PHASE** - Directory structure is required for all subsequent content creation.

#### Step 2.1: Create Standard Directory Structure

**Task**: Create the canonical OpenShift documentation structure.

**Actions**:
```bash
# Create directory tree
create: agentic/ if not exists
create: agentic/design-docs/
create: agentic/design-docs/components/
create: agentic/domain/
create: agentic/domain/concepts/
create: agentic/domain/workflows/
create: agentic/exec-plans/
create: agentic/exec-plans/active/
create: agentic/exec-plans/completed/
create: agentic/decisions/
create: agentic/references/
create: agentic/generated/
```

**Validation**:
- [ ] All directories created
- [ ] No typos in directory names
- [ ] Consistent naming (lowercase, hyphens)

#### Step 2.2: Create Placeholder Files

**Task**: Create index files AND required top-level documentation files.

**Actions**:
```bash
# Create navigation files
create: agentic/design-docs/index.md
create: agentic/domain/index.md
create: agentic/decisions/index.md
create: agentic/references/index.md
create: agentic/exec-plans/tech-debt-tracker.md
create: agentic/generated/README.md  # ← Explains what goes here

# Create REQUIRED top-level files (ALL REPOS MUST HAVE THESE)
create: agentic/DESIGN.md
create: agentic/DEVELOPMENT.md
create: agentic/TESTING.md
create: agentic/RELIABILITY.md
create: agentic/SECURITY.md
create: agentic/QUALITY_SCORE.md
```

**Template for agentic/generated/README.md**:
```markdown
# Generated Documentation

**Purpose**: Auto-generated documentation that should NOT be manually edited.

## What Goes Here

- **metrics-catalog.md**: Auto-generated from Prometheus metrics in code
- **package-map.md**: Auto-generated dependency graph
- **api-reference.md**: Auto-generated API documentation
- **metrics-dashboard.html**: Quality metrics dashboard (from agentic/scripts/)

## How to Generate

```bash
# Metrics dashboard (quality score)
./agentic/scripts/measure-all-metrics.sh --html

# Add other generation commands here as needed
# Example: go doc -all > agentic/generated/api-reference.md
```

## Gitignore

Consider adding to `.gitignore` if files are large or regenerated frequently:
```
agentic/generated/metrics-dashboard.html
agentic/generated/package-map.md
```

## When to Regenerate

- **metrics-dashboard.html**: After each documentation update
- **Other generated docs**: As part of release process or CI
```

**Template for index.md files** (customize per directory):

**agentic/design-docs/index.md**:
```markdown
# Design Documentation

## Purpose
Architecture, design philosophy, and component documentation.

## Contents

**Core**:
- [Core Beliefs](./core-beliefs.md) - Operating principles and patterns

**Components** (add as you document them):
- [Component1](./components/component1.md) - Brief description
- [Component2](./components/component2.md) - Brief description

## When to Add Here

- **core-beliefs.md**: Operating principles (created in Phase 3)
- **components/**: One doc per major component (controller, service, daemon)
- **diagrams/**: Architecture diagrams (SVG or ASCII)

## Related Sections

- [Domain Concepts](../domain/) - What the components manipulate
- [ADRs](../decisions/) - Why components are designed this way
```

**agentic/domain/index.md**:
```markdown
# Domain Documentation

## Purpose
Concepts, glossary, and workflows in this system's domain.

## Contents

- [Glossary](./glossary.md) - Term definitions

**Concepts** (add as you document them):
- [Concept1](./concepts/concept1.md) - Brief description
- [Concept2](./concepts/concept2.md) - Brief description

**Workflows** (if applicable):
- [Workflow1](./workflows/workflow1.md) - Brief description

## When to Add Here

- **glossary.md**: All domain terms (alphabetical)
- **concepts/**: CRDs, packages, key interfaces (one file per concept)
- **workflows/**: Multi-step processes involving multiple components

## Related Sections

- [Components](../design-docs/components/) - Who implements these concepts
- [ADRs](../decisions/) - Why concepts are designed this way
```

**agentic/decisions/index.md**:
```markdown
# Architectural Decision Records

## Purpose
Document why architectural decisions were made.

## Active ADRs

### Accepted
- [ADR-0001: Decision Title](./adr-0001-decision-title.md) - YYYY-MM-DD
- [ADR-0002: Decision Title](./adr-0002-decision-title.md) - YYYY-MM-DD

### Proposed
- [ADR-NNNN: Pending Decision](./adr-NNNN-pending.md) - Under review

## Deprecated/Superseded

- [ADR-XXXX: Old Decision](./adr-xxxx-old.md) - Superseded by ADR-YYYY

## When to Add Here

Create an ADR when:
- Making a significant architectural choice
- Choosing between multiple viable alternatives
- Establishing a new pattern or practice
- Deprecating an existing approach

Use the [ADR template](./adr-template.md).

## Related Sections

- [Core Beliefs](../design-docs/core-beliefs.md) - Broader principles
- [Domain Concepts](../domain/concepts/) - What the decisions affect
```

**agentic/references/index.md**:
```markdown
# Reference Documentation

## Purpose
External knowledge, API catalogs, enhancement tracking, and standards.

## Contents

**OpenShift-Specific** (if applicable):
- [Enhancement Index](./enhancement-index.md) - Links to design docs
- [OpenShift APIs](./openshift-apis.yaml) - API inventory
- [OpenShift Ecosystem](./openshift-ecosystem.md) - Related operators
- [Operator Patterns](./openshift-operator-patterns-llms.txt) - Implementation patterns
- [Docs Standards](./openshift-docs-standards.md) - Reference links

**General**:
- Add other reference material as needed (upstream docs, standards, etc.)

## When to Add Here

Reference docs that agents should consult:
- Enhancement/design proposal links
- API catalogs and schemas
- External documentation pointers
- Standard patterns and conventions

## Related Sections

- [ADRs](../decisions/) - Reference enhancements in ADRs
- [Concepts](../domain/concepts/) - Reference APIs in concept docs
```

**Validation**:
- [ ] Every directory has an index.md
- [ ] Each index explains the directory's purpose
- [ ] Navigation is clear
- [ ] All 6 required top-level files exist (DESIGN.md, DEVELOPMENT.md, TESTING.md, RELIABILITY.md, SECURITY.md, QUALITY_SCORE.md)

#### Step 2.3: Copy Metrics Scripts (REQUIRED for Phase 7)

**Task**: Copy the metrics measurement scripts from agentic-guide to your repository.

**Actions**:
```bash
# Set the path to agentic-guide (adjust if needed)
GUIDE_PATH="/home/psundara/ws/src/github.com/openshift/agentic-guide"

# Create scripts directory
mkdir -p agentic/scripts

# Copy metrics scripts
cp "$GUIDE_PATH/scripts/"*.py agentic/scripts/
cp "$GUIDE_PATH/scripts/"*.sh agentic/scripts/
chmod +x agentic/scripts/*.sh

# Verify scripts were copied
ls -la agentic/scripts/
```

**Expected files**:
- `agentic/scripts/measure-all-metrics.sh` - Main metrics runner
- `agentic/scripts/measure-*.py` - Individual metric scripts

**Note**: These scripts are needed for Phase 7 (metrics dashboard generation). Without them, you cannot complete the first pass.

**Alternative**: If you prefer, you can run the scripts directly from agentic-guide:
```bash
/path/to/agentic-guide/scripts/measure-all-metrics.sh --html
```

**Validation**:
- [ ] Scripts directory created at `agentic/scripts/`
- [ ] All `.sh` and `.py` files copied
- [ ] Scripts are executable (`chmod +x`)
- [ ] `./agentic/scripts/measure-all-metrics.sh --help` works

---

### Phase 3: Core Documents (CRITICAL FILES)

#### Step 3.1: Create AGENTS.md

**Task**: Create the 100-line table of contents.

**Template Structure** (MUST FOLLOW):
```markdown
# [Repository Name] - Agent Navigation

> **Purpose**: Table of contents for AI agents. Points to deeper knowledge.
> **Do not expand this file**. Keep under 150 lines. Link to details instead.

## What This Repository Does

[1-2 sentence description]

## Quick Navigation by Intent

**I need to understand the system**
→ [ARCHITECTURE.md](./ARCHITECTURE.md)
→ [Core beliefs](./agentic/design-docs/core-beliefs.md)
→ [Components](./agentic/design-docs/components/)

**I'm implementing a feature** (MANDATORY WORKFLOW - follow in order)
0. INVESTIGATE the problem space first:
   - Read [ARCHITECTURE.md](./ARCHITECTURE.md) to understand system structure
   - Check relevant [design docs](./agentic/design-docs/) and [domain concepts](./agentic/domain/concepts/)
   - Review related [component documentation](./agentic/design-docs/components/)
   - **VERIFY data structures/formats** - Check reference docs for canonical output format
   - **VALIDATE assumptions** - Use grep/examples to confirm actual paths, field names, structures
   - **Review reference implementations** - Find similar code patterns in codebase
   - Ask clarifying questions if requirements are ambiguous
   - Only then read specific code files if needed
1. CREATE a plan in [active/](./agentic/exec-plans/active/) using [template](./agentic/exec-plans/template.md)
2. READ testing guide and relevant patterns before writing code
3. Implement with tests
4. Update plan status to completed

**I'm fixing a bug**
→ [Component map](./ARCHITECTURE.md#components)
→ [Debugging](./agentic/DEVELOPMENT.md#debugging)
→ [Tests](./agentic/TESTING.md)

**I need to understand a concept**
→ [Glossary](./agentic/domain/glossary.md)
→ [Concepts](./agentic/domain/concepts/)
→ [Workflows](./agentic/domain/workflows/)

## Repository Structure

```
[source-dir]/              # Main source (e.g., pkg/, cmd/, internal/)
├── [component1]/
├── [component2]/
└── [component3]/

[test-dir]/                # Tests (e.g., test/, tests/)
├── unit/
└── e2e/
```

## Component Boundaries

```
[ASCII diagram showing component relationships]
Example:
┌─────────────────────┐
│  [Component 1]      │  [Purpose]
└─────────────────────┘
         ↓
┌─────────────────────┐
│  [Component 2]      │  [Purpose]
└─────────────────────┘
```

## Core Concepts (Domain Model)

| Concept | Definition | Docs |
|---------|-----------|------|
| [Concept1] | [1-sentence definition] | [./agentic/domain/concepts/concept1.md] |
| [Concept2] | [1-sentence definition] | [./agentic/domain/concepts/concept2.md] |

## Key Invariants (ENFORCE THESE)

1. **[Invariant 1]**: [Description]
   - Validated by: [How it's enforced]
   - Why: [Rationale]

2. **[Invariant 2]**: [Description]
   - Validated by: [How it's enforced]
   - Why: [Rationale]

3. **All features require execution plans**: Must create plan in agentic/exec-plans/active/ before coding
   - Validated by: Code review
   - Why: Ensures design consideration and trackable decision history

## Critical Code Locations

| Purpose | File | Why Critical |
|---------|------|--------------|
| [Function1] | [path/to/file.ext] | [Explanation] |
| [Function2] | [path/to/file.ext] | [Explanation] |

## External Dependencies

- **[Dependency1]**: [Purpose]
- **[Dependency2]**: [Purpose]

## Build & Test

```bash
# Build
[build command, e.g., make build]

# Unit tests
[test command, e.g., make test]

# E2E tests
[e2e command, e.g., make test-e2e]
```

## Documentation Structure

```
agentic/
├── design-docs/   # Architecture, components
├── domain/        # Concepts, workflows
├── exec-plans/    # Active work, tech debt
├── product-specs/ # Feature specifications
├── decisions/     # ADRs
├── references/    # External knowledge
├── generated/     # Auto-generated docs
├── DESIGN.md      # Design philosophy
├── DEVELOPMENT.md # Dev setup
├── TESTING.md     # Test strategy
├── RELIABILITY.md # SLOs, observability
├── SECURITY.md    # Security model
└── QUALITY_SCORE.md
```

## When You're Stuck

1. Check [tech debt tracker](./agentic/exec-plans/tech-debt-tracker.md)
2. Check [quality score](./agentic/QUALITY_SCORE.md)
3. File a plan in [active plans](./agentic/exec-plans/active/)

## Last Updated

This file is validated by CI on every commit.
```

**Rules for AGENTS.md**:
1. **MUST be under 150 lines** - Be ruthless with brevity
2. **Every section links elsewhere** - No detailed explanations
3. **Use tables for structured data** - Easy to scan
4. **ASCII diagrams only** - No external images
5. **Command examples in code blocks** - Directly runnable
6. **No opinions** - Just facts and navigation

**MANDATORY POST-CREATION VALIDATION:**

```bash
# Step 1: Check length
lines=$(wc -l < AGENTS.md)
if [ $lines -gt 150 ]; then
    echo "❌ FAIL: AGENTS.md is $lines lines (max 150)"
    exit 1
else
    echo "✅ PASS: AGENTS.md is $lines lines"
fi

# Step 2: Check for unreplaced placeholders
if grep -q '\[REPO-NAME\]\|\[Component1\]\|\[Concept1\]' AGENTS.md; then
    echo "❌ FAIL: Found unreplaced placeholders in AGENTS.md"
    grep '\[.*\]' AGENTS.md | head -5
    exit 1
else
    echo "✅ PASS: No unreplaced placeholders"
fi

# Step 3: Validate links (requires markdown-link-check)
# Install: npm install -g markdown-link-check
markdown-link-check AGENTS.md

echo "✅ AGENTS.md validation complete"
```

**Manual Checklist**:
- [ ] File is under 150 lines (verified by script above)
- [ ] All `[PLACEHOLDERS]` replaced with actual values
- [ ] All links are valid (use relative paths like `./agentic/domain/glossary.md`)
- [ ] No detailed explanations (just pointers with links)
- [ ] Build/test commands are correct for THIS repo
- [ ] Critical code locations include file path (e.g., `pkg/controller/reconcile.go`)
- [ ] Every "intent" section has navigation path
- [ ] ASCII diagrams use only ASCII characters (no Unicode art)

#### Step 3.2: Create ARCHITECTURE.md

**Task**: Create navigation map with file paths (NOT narrative overview).

⚠️ **WARNING**: Narrative overviews ("The system sits between X and Y...") increase costs without improving outcomes. Focus on **structure** and **navigation**, not explanations.

**Template Structure**:
```markdown
# Architecture Overview

## System Context

**External Integrations:**

| System | Direction | Interface | File |
|--------|-----------|-----------|------|
| [External A] | Inbound | REST API | pkg/api/handler.go |
| [External B] | Outbound | gRPC | pkg/client/grpc.go |

**Avoid**: Long narrative about how this fits in ecosystem. Link to existing design docs if they exist.

## Domain Architecture

### Package Layering (ENFORCED)

```
[Directory tree showing dependencies]
Example:
vendor/
  └── github.com/[org]/api
        ↓ (types only)
pkg/
  ├── [package1]/      → [purpose]
  ├── [package2]/      → [purpose]
  └── [package3]/      → [purpose]
```

### Dependency Rules (ENFORCED BY LINTER)

1. [Package A] MUST NOT import [Package B]
2. [Package C] may import [Package D]
3. Cross-component communication via [APIs/interfaces] only

## Components

| Component | Entry Point | Critical Code | Purpose | Details |
|-----------|-------------|---------------|---------|---------|
| [Component1] | cmd/[comp1]/main.go | pkg/[comp1]/[file].go | [Brief purpose] | [link](./agentic/design-docs/components/[comp1].md) |
| [Component2] | cmd/[comp2]/main.go | pkg/[comp2]/[file].go | [Brief purpose] | [link](./agentic/design-docs/components/[comp2].md) |

**Avoid**: Paragraphs explaining each component. Use table for quick reference.

## Data Flow

Use structured list or ASCII diagram, minimize narrative:

```
User creates [Resource] → API validates → Queue
  ↓
[Controller A] reconciles (pkg/[controller]/reconcile.go)
  ↓
[Controller B] applies (pkg/[controller]/apply.go)
  ↓
Status updated
```

**Avoid**: "The controller watches for resources and when it detects a change, it begins a reconciliation loop..."

## Critical Code Locations

| Function | File | Why Critical |
|----------|------|--------------|
| [Function1] | [path/file.ext] | [Explanation] |
| [Function2] | [path/file.ext] | [Explanation] |

See [complete package map](./agentic/generated/package-map.md) for details.

## Related Documentation

- [Design docs](./agentic/design-docs/)
- [Domain concepts](./agentic/domain/)
- [ADRs](./agentic/decisions/)
```

**Rules for ARCHITECTURE.md**:
1. **Focus on structure**, not implementation details
2. **Show boundaries** clearly (what's in, what's out)
3. **Explain dependencies** and why they exist
4. **Link to details** rather than repeating them
5. **Use diagrams** for complex relationships

**MANDATORY POST-CREATION VALIDATION:**

```bash
# Check for unreplaced placeholders
if grep -q '\[Component1\]\|\[Package.*\]' ARCHITECTURE.md; then
    echo "❌ FAIL: Found unreplaced placeholders in ARCHITECTURE.md"
    grep '\[.*\]' ARCHITECTURE.md | grep -v '^\[.*\](.*)'  # Exclude markdown links
    exit 1
else
    echo "✅ PASS: No unreplaced placeholders"
fi

# Validate links
markdown-link-check ARCHITECTURE.md

echo "✅ ARCHITECTURE.md validation complete"
```

**Manual Checklist**:
- [ ] System boundaries are clear (what's IN this repo, what's OUT)
- [ ] Component relationships are explained (with ASCII diagram)
- [ ] Data flow is understandable (narrative + diagram)
- [ ] Links to detailed component docs exist (e.g., `./agentic/design-docs/components/component-name.md`)
- [ ] Dependency rules are explicit ("X MUST NOT import Y")
- [ ] Critical code locations table includes file path
- [ ] No `[PLACEHOLDER]` text remains

#### Step 3.3: Create agentic/design-docs/core-beliefs.md

**Task**: Document the operating principles and patterns.

**Template Structure**:
```markdown
# Core Beliefs - [Repository Name]

## Operating Principles

### 1. [Principle Name]
[1-2 sentence description]

**Implications**:
- Implication 1
- Implication 2

**Example**: [Concrete example from this repo]

### 2. [Next Principle]
...

## Non-Negotiable Constraints

### Security
- ✅ [Requirement 1]
- ✅ [Requirement 2]
- ❌ [Anti-pattern to avoid]

### Reliability
- ✅ [Requirement 1]
- ✅ [Requirement 2]

### Correctness
- ✅ [Requirement 1]
- ✅ [Requirement 2]

## Patterns We Use

### Verify Before Implementing Pattern
**What**: Always verify actual data structures, file paths, and output formats before making assumptions

**When to use**: Before writing any code that processes or generates data from the system

**How to verify**:
1. Check reference documentation (e.g., output format specs)
2. Use grep to search for actual usage patterns in codebase
3. Look at similar implementations
4. Test assumptions with actual data/files

**Example in this repo**: [File/location where this pattern is applied]

**Why important**: Prevents implementing based on incorrect assumptions, which wastes time fixing later

See: [Link to detailed pattern doc]

### [Pattern Name]
[Description of the pattern]

**When to use**: [Criteria]

**Example in this repo**: [File/location]

See: [Link to detailed pattern doc]

## Deprecated Patterns

### ❌ [Anti-Pattern Name]
**Don't**: [What not to do]
**Do**: [What to do instead]
**Why**: [Rationale]

## When to Break These Rules

[Guidance on exceptions]

1. Document in [agentic/decisions/]
2. Get consensus
3. Add to tech debt tracker
```

**Rules**:
1. **Be opinionated** - This is the philosophy guide
2. **Explain "why"** for every principle
3. **Give examples** from the actual codebase
4. **Mark anti-patterns** clearly
5. **Link to detailed docs** for patterns

**Validation**:
- [ ] Each principle has rationale
- [ ] Examples are from this repo
- [ ] Anti-patterns are marked with ❌
- [ ] Links to pattern docs exist

---

### Phase 4: Domain Documentation

#### Step 4.1: Create agentic/domain/glossary.md

**Task**: Define all domain-specific terminology.

**Template Structure**:
```markdown
# Glossary - [Repository Name]

> **Purpose**: Canonical definitions for all domain concepts.
> **Format**: Alphabetical order. Link to detailed docs.

## A

### [Term Starting with A]

**Definition**: [1-2 sentence definition]

**Type**: [CRD | Package | Concept | Pattern]

**Related**: [RelatedTerm1], [RelatedTerm2]

**Details**: [./concepts/term-a.md]

## B

### [Term Starting with B]
...

---

## See Also

- [Domain concepts](./concepts/) - Detailed explanations
- [Workflows](./workflows/) - How concepts interact
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - System structure
```

**Rules**:
1. **Alphabetical order** - Easy to scan
2. **Brief definitions** - 1-2 sentences max
3. **Link to details** - Don't duplicate
4. **Include type** - CRD, package, concept, etc.
5. **Show relationships** - What's related?

**Validation**:
- [ ] Terms are alphabetical
- [ ] Each term has a definition
- [ ] Links to detailed docs exist
- [ ] Related terms are cross-referenced

#### Step 4.2: Create Individual Concept Documents

**Task**: For each major domain concept (5-15 concepts), create a detailed doc.

**What to document**: CRDs, core packages, key interfaces, data structures, patterns

**Location**: `agentic/domain/concepts/[concept-name].md`

**Template Structure**:
```markdown
---
concept: [ConceptName]
type: [CRD | Package | Interface | Pattern]
related: [Concept1, Concept2, Concept3]
---

# [Concept Name]

## Definition

[2-3 sentence clear definition]

## Purpose

Why does this exist? What problem does it solve?

## Location in Code

- **API Definition**: [file path]
- **Implementation**: [file path]
- **Controller**: [file path] (if applicable)
- **Tests**: [file pattern]

## Lifecycle

```
[ASCII diagram or numbered steps showing lifecycle]
Example:
1. Created by [actor]
2. Processed by [component]
3. Applied by [component]
4. Status updated
```

## Key Fields / Properties

### [Field 1]
**Type**: [type]
**Purpose**: [explanation]
**Example**:
```yaml
[example]
```

### [Field 2]
...

## State Machine (if applicable)

```yaml
states:
  - [State1]: [Description]
  - [State2]: [Description]

transitions:
  - [State1] → [State2]: [Condition]
```

## Common Patterns

### [Pattern 1]
```yaml
[Example code/config]
```

**When to use**: [Scenario]

## Related Concepts

- [Concept1](./concept1.md) - [Relationship]
- [Concept2](./concept2.md) - [Relationship]

## Implementation Details

- **Logic**: See [file path]
- **Validation**: See [file path]
- **Tests**: See [file pattern]

## References

- [ADR](../../decisions/adr-xxx.md) - Why we chose this design
- [Upstream docs](link) - External reference
```

**Rules**:
1. **Start with YAML frontmatter** - Machine-readable metadata
2. **Clear definition first** - Don't assume knowledge
3. **Show code locations** - File paths only (DO NOT include line numbers - they change frequently)
4. **Include examples** - Real, runnable examples
5. **Link relationships** - Bidirectional links

**MANDATORY POST-CREATION VALIDATION:**

```bash
# For each concept file you create
concept_file="agentic/domain/concepts/[concept-name].md"  # Replace with actual filename

# Check YAML frontmatter
if ! head -n 1 "$concept_file" | grep -q "^---$"; then
    echo "❌ FAIL: Missing YAML frontmatter in $concept_file"
    exit 1
fi

# Check for placeholders
if grep -q '\[Concept.\]\|\[Field.\]' "$concept_file"; then
    echo "❌ FAIL: Unreplaced placeholders in $concept_file"
    exit 1
fi

echo "✅ $concept_file validation complete"
```

**Manual Checklist (for EACH concept doc)**:
- [ ] YAML frontmatter present (starts with `---`)
- [ ] Definition is clear and complete (no placeholders)
- [ ] Code locations include file path (e.g., `pkg/apis/types.go:45`)
- [ ] Examples are correct and runnable
- [ ] Related concepts are linked bidirectionally
- [ ] File named correctly: lowercase-with-hyphens.md
- [ ] Concept type specified in frontmatter (CRD | Package | Interface | Pattern)

#### Step 4.3: Create Workflow Documents (Optional)

**Task**: Document multi-step processes that involve multiple concepts.

**When to create**: If your system has complex workflows (e.g., "How a request flows through the system", "Deployment workflow", "Reconciliation loop")

**Location**: `agentic/domain/workflows/[workflow-name].md`

**Template Structure**:
```markdown
---
workflow: [WorkflowName]
components: [Component1, Component2, Component3]
related_concepts: [Concept1, Concept2]
---

# Workflow: [Workflow Name]

## Overview

[2-3 sentence description of what this workflow accomplishes]

## Participants

| Component | Role | Code Location |
|-----------|------|---------------|
| [Component1] | [What it does in this workflow] | [file path] |
| [Component2] | [What it does in this workflow] | [file path] |

## Steps

### 1. [Step Name]

**Trigger**: [What initiates this step]
**Actor**: [Component responsible]
**Action**: [What happens]

```
[Code snippet or pseudocode]
```

**Result**: [Output or state change]

### 2. [Next Step]
...

## Sequence Diagram

```
[User/System] → [Component A] → [Component B] → [Result]
   |                |                |
   v                v                v
[Action 1]      [Action 2]      [Action 3]
```

## Error Handling

| Failure Point | Detection | Recovery |
|---------------|-----------|----------|
| [Step X fails] | [How detected] | [What happens] |

## Related Concepts

- [Concept1](../concepts/concept1.md) - Used in step X
- [Concept2](../concepts/concept2.md) - Modified in step Y

## Code Locations

- **Start**: [file:function]
- **Key logic**: [file:function]
- **Completion**: [file:function]
```

**Example workflows**:
- Request processing flow
- Reconciliation loop
- Bootstrap sequence
- Upgrade workflow

**Validation**:
- [ ] Workflow has clear start and end
- [ ] All steps are in order
- [ ] Components are linked to their docs
- [ ] Error handling documented

#### Step 4.4: Create Component Documentation (Optional but Recommended)

**Task**: Document major components (controllers, services, daemons, operators).

**When to create**: For repositories with 3+ major components that have distinct responsibilities

**Location**: `agentic/design-docs/components/[component-name].md`

**Template Structure**:
```markdown
---
component: [ComponentName]
type: [Controller | Service | Daemon | Operator | CLI]
related: [Component2, Component3]
---

# Component: [Component Name]

## Purpose

[1-2 sentences: What does this component do and why does it exist?]

## Location

- **Entry Point**: [cmd/component/main.go]
- **Core Logic**: [pkg/component/]
- **Tests**: [test/component/]

## Responsibilities

1. **[Responsibility 1]**: [Description]
2. **[Responsibility 2]**: [Description]
3. **[Responsibility 3]**: [Description]

## Architecture

```
[ASCII diagram showing this component's internal structure]
Example:
┌─────────────────────────────────┐
│   [ComponentName]               │
│                                 │
│  ┌──────────┐   ┌───────────┐  │
│  │ Module A │ → │ Module B  │  │
│  └──────────┘   └───────────┘  │
└─────────────────────────────────┘
         ↓                ↑
    [Output]        [Input from X]
```

## Interfaces

### Input
- **[Interface 1]**: [Description, source]
  - Example: Watches CRD updates via Kubernetes API

### Output
- **[Interface 1]**: [Description, destination]
  - Example: Updates status via API, writes to filesystem

## Configuration

| Config Parameter | Type | Default | Purpose |
|------------------|------|---------|---------|
| [param-name] | [type] | [value] | [description] |

## Dependencies

- **[Dependency 1]**: [Why needed, version]
- **[Dependency 2]**: [Why needed, version]

## Observability

### Metrics
- `[metric_name]`: [Description]

### Logs
- Key log lines: [What to look for]

### Health Checks
- Liveness: [What's checked]
- Readiness: [What's checked]

## Related Components

- [Component2](./component2.md) - [Relationship]
- [Component3](./component3.md) - [Relationship]

## Related Concepts

- [Concept1](../domain/concepts/concept1.md) - [How used]

## Common Issues

**Issue**: [Problem]
**Cause**: [Root cause]
**Fix**: [Solution]

## Code Walkthrough

**Critical paths**:
1. **[Operation]**: Starts at [file:function], flows through [file:function]
2. **[Operation]**: Starts at [file:function], flows through [file:function]
```

**Validation**:
- [ ] Component purpose is clear
- [ ] Responsibilities are distinct
- [ ] Interfaces documented (input/output)
- [ ] Related to other components
- [ ] File paths provided

---

### Phase 5: Plans and Decisions

⚠️ **DO NOT SKIP** - Create initial content (2-3 ADRs, 1 exec-plan), not just templates. Required for first-time implementations.

**Required for Initial Implementation**:
- ✅ At least 2-3 ADRs documenting EXISTING architectural decisions
- ✅ At least 1 active exec-plan (can be "complete agentic docs" plan)
- ✅ At least 5 concept docs for core domain concepts
- ✅ CI validation workflow (not just planned)
- ✅ Quality score with initial baseline and progress tracking

**DO NOT**:
- ❌ Leave directories with only templates
- ❌ Create empty index files with "No content yet"
- ❌ Skip initial content creation with plan to "add later"
- ❌ Think "I'll create ADRs when decisions are made" - document existing decisions FIRST

**Validation Check**:

Before considering Phase 5 complete, run these commands:

```bash
# Should return at least 2-3 ADRs (not counting template)
find agentic/decisions -name "adr-*.md" -not -name "adr-template.md" | wc -l

# Should return at least 1 active plan
find agentic/exec-plans/active -name "*.md" | wc -l

# Should return at least 5 concept docs
find agentic/domain/concepts -name "*.md" | wc -l
```

If any check returns 0 or fewer than required, Phase 5 is **INCOMPLETE**.

**Expected Quality Score After Phase 5**: 85-90/100 (with initial content) vs 70-80/100 (templates only)

---

**If you are maintaining existing agentic documentation**:

Then the "when to add" guidance applies - add ADRs and exec-plans as new decisions
are made and new work is planned. You don't need to create initial content since it already exists.

---

#### Step 5.1: Create agentic/exec-plans/template.md

**Task**: Provide a standard template for execution plans.

**Template** (use exactly this):
```markdown
---
status: [active | completed | abandoned]
owner: @[username]
created: YYYY-MM-DD
target: YYYY-MM-DD
related_issues: [#1234, #5678]
related_prs: []
---

# Plan: [Feature/Project Name]

## Goal

[One sentence: what are we building and why?]

## Success Criteria

- [ ] Measurable outcome 1
- [ ] Measurable outcome 2
- [ ] Tests pass
- [ ] Documentation updated

## Context

Why now? What's the business need?

Link to relevant:
- Product specs: [link]
- Design docs: [link]
- ADRs: [link]

## Technical Approach

### Architecture Changes

[What components change? What's the data flow?]

### New Abstractions

[What new types, interfaces, or packages?]

### Dependencies

[What external changes do we need?]

## Implementation Phases

### Phase 1: [Name]
- [ ] Task 1
- [ ] Task 2

### Phase 2: [Name]
- [ ] Task 3
- [ ] Task 4

## Testing Strategy

- Unit tests: [coverage target]
- Integration tests: [scenarios]
- E2E tests: [user journeys]

## Rollout Plan

- Feature flag? [yes/no]
- Tech preview first? [yes/no]
- Rollback plan? [description]

## Decision Log

### YYYY-MM-DD: [Decision]
[Why we chose X instead of Y]

## Progress Notes

### YYYY-MM-DD
- [What happened]
- [Blockers]
- [Next steps]

## Completion Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] ADR filed if needed
- [ ] Tech debt addressed or tracked
- [ ] Plan moved to `completed/`
```

**Validation**:
- [ ] Template is complete
- [ ] YAML frontmatter is correct
- [ ] Sections are clear

#### Step 5.2: Create agentic/exec-plans/tech-debt-tracker.md

**Task**: Central registry of known technical debt.

**Template**:
```markdown
# Technical Debt Tracker

> **Purpose**: Track known issues, workarounds, and improvements needed
> **Update**: Add new debt immediately, remove when resolved

## High Priority

### [Debt Item 1]
**Status**: Open
**Owner**: @username
**Created**: YYYY-MM-DD
**Impact**: [What breaks or is painful]
**Workaround**: [Current mitigation]
**Fix**: [What needs to happen]
**Effort**: [S/M/L]
**Related**: [#issue, PR, doc]

## Medium Priority

### [Debt Item 2]
...

## Low Priority / Nice to Have

### [Debt Item 3]
...

## Resolved (Recent)

### [Debt Item 4]
**Resolved**: YYYY-MM-DD
**How**: [PR link, description]

---

## How to Use This

**Adding debt**:
1. Add to appropriate priority section
2. Fill all fields
3. Link to related issues/PRs

**Updating debt**:
1. Change status/owner as needed
2. Update workaround if changed
3. Move to "Resolved" when fixed

**Cleaning up**:
- Move resolved items after 30 days to archive
- Re-prioritize monthly
```

**Validation**:
- [ ] Template is clear
- [ ] Instructions are provided
- [ ] Structure is consistent

#### Step 5.3: Create ADR Template (agentic/decisions/adr-template.md)

**Task**: Standard format for architectural decisions.

**Template**:
```markdown
---
id: ADR-[number]
title: [Decision Title]
date: YYYY-MM-DD
status: [proposed | accepted | deprecated | superseded]
deciders: [team-name, @username]
supersedes: [ADR-XXX if applicable]
superseded-by: [ADR-XXX if applicable]
---

# [Decision Title]

## Status

[proposed | accepted | deprecated | superseded by ADR-XXX]

## Context

What is the issue or situation that motivates this decision?

## Decision

What is the change that we're proposing/announcing?

## Rationale

Why did we choose this option?

### Why This?
- Reason 1
- Reason 2

### Why Not Alternatives?
- Alternative A: [Why rejected]
- Alternative B: [Why rejected]

## Consequences

### Positive
- ✅ Benefit 1
- ✅ Benefit 2

### Negative
- ❌ Tradeoff 1
- ❌ Tradeoff 2

### Neutral
- ℹ️ Change 1

## Implementation

- **Location**: [Where in codebase]
- **Migration**: [How to transition]
- **Rollout**: [Deployment plan]

## Alternatives Considered

### Alternative 1: [Name]
**Pros**: [Benefits]
**Cons**: [Drawbacks]
**Why rejected**: [Reason]

### Alternative 2: [Name]
...

## References

- [Related ADR](./adr-xxx.md)
- [Design doc](../design/xxx.md)
- [External reference](https://...)

## Notes

[Any additional context, history, or discussion points]
```

**Validation**:
- [ ] YAML frontmatter is complete
- [ ] All sections are present
- [ ] Template is ready to copy

#### Step 5.4: Create Initial ADRs and Exec-Plans (MANDATORY FOR NEW IMPLEMENTATIONS)

**Task**: For NEW implementations, create initial content - don't leave directories with only templates.

**IMPORTANT**: This step is MANDATORY for initial implementations. Do not skip. This is where you document the architectural decisions that have ALREADY been made in the codebase.

---

**Part A: Create Initial ADRs (Minimum 2-3)**

1. **Identify Existing Architectural Decisions**:

   Look for decisions already made in the codebase:
   - Technology/framework choices (e.g., "Why Kubernetes controller-runtime?")
   - Design patterns enforced (e.g., "Why singleton configuration?")
   - Error handling philosophy (e.g., "Why fail-safe vs fail-closed?")
   - API design decisions (e.g., "Why CRD vs ConfigMap?")
   - Concurrency patterns (e.g., "Why leader election?")

   **Where to look**:
   - Existing README.md or CONTRIBUTING.md
   - Comments in critical code sections
   - Git commit messages for major changes
   - Dependencies in go.mod/package.json
   - Enforced constraints (e.g., validating webhooks)

2. **Create 2-3 ADRs Documenting These Decisions**:

   For each major decision, create `agentic/decisions/adr-NNNN-decision-title.md`:

   ```markdown
   ---
   id: ADR-0001
   title: [Decision Title - e.g., "Use Scheduling Gates for Pod Placement"]
   date: YYYY-MM-DD  # Estimate from git history or implementation date
   status: accepted
   deciders: [team-name]
   supersedes: null
   superseded-by: null
   ---

   # [Decision Title]

   ## Status

   Accepted (implemented)

   ## Context

   [What problem does this solve? What were the requirements?]

   Example: "We need to modify pod specs before scheduling but cannot do
   so synchronously in a webhook due to async image inspection calls."

   ## Decision

   [What was chosen?]

   Example: "Use Kubernetes Scheduling Gates (KEP-3521) to hold pods
   while setting nodeAffinity based on image inspection results."

   ## Rationale

   ### Why This?
   - Reason 1: [Concrete benefit - e.g., "Prevents race with scheduler"]
   - Reason 2: [Concrete benefit - e.g., "Kubernetes-native feature"]
   - Reason 3: [Concrete benefit - e.g., "No custom state management needed"]

   ### Why Not Alternatives?
   - Alternative A: [What you didn't choose and why]
     Example: "Synchronous webhook mutation - Can't do async operations"
   - Alternative B: [What you didn't choose and why]
     Example: "Custom resource for state - Added complexity, need GC"

   ## Consequences

   ### Positive
   - ✅ [Actual benefit realized in codebase]
   - ✅ [Actual benefit realized in codebase]

   ### Negative
   - ❌ [Actual tradeoff or limitation]
   - ❌ [Actual tradeoff or limitation]

   ### Neutral
   - ℹ️ [Side effects or considerations]

   ## Implementation

   - **Location**: [actual file path where this is implemented]
     Example: "controllers/podplacement/scheduling_gate_mutating_webhook.go:78"
   - **Status**: Already implemented in codebase
   - **Validation**: [How the decision is enforced]
     Example: "Webhook adds gate, controller removes it after processing"

   ## References

   - [Link to relevant code](../../path/to/file.go)
   - [Link to concept doc](../domain/concepts/scheduling-gate.md)
   - [External reference if applicable](https://github.com/kubernetes/enhancements/...)
   ```

3. **Examples of Good Initial ADRs**:
   - "ADR-0001: Use [Framework X] for [Purpose Y]"
   - "ADR-0002: Enforce Singleton Pattern for [Resource Z]"
   - "ADR-0003: Fail-Safe Error Handling Strategy"
   - "ADR-0004: Use [Pattern X] for [Concern Y]"

4. **Update agentic/decisions/index.md**:

   ```markdown
   ## Active ADRs

   ### Accepted

   - [ADR-0001: Decision Title](./adr-0001-decision-title.md) - YYYY-MM-DD
   - [ADR-0002: Decision Title](./adr-0002-decision-title.md) - YYYY-MM-DD
   - [ADR-0003: Decision Title](./adr-0003-decision-title.md) - YYYY-MM-DD
   ```

---

**Part B: Create Initial Exec-Plan (Minimum 1)**

**Option 1: Create Plan for Documentation Completion** (Recommended for initial implementations)

Create `agentic/exec-plans/active/complete-agentic-documentation.md`:

```markdown
---
status: active
owner: @team
created: YYYY-MM-DD
target: YYYY-MM-DD  # 30-60 days out
related_issues: []
related_prs: []
---

# Plan: Complete Agentic Documentation to 95/100 Quality Score

## Goal

Reach documentation quality score of 95/100 by addressing gaps identified
in initial implementation.

## Success Criteria

- [ ] Quality score ≥ 95/100
- [ ] CI validation passes on all PRs
- [ ] All code references use file paths (no line numbers)
- [ ] Component documentation complete for all major components
- [ ] No broken links
- [ ] Future enhancements tracked in tech debt tracker

## Context

Initial agentic documentation framework implemented on YYYY-MM-DD with
quality score of XX/100. Identified gaps:
- [List specific gaps from QUALITY_SCORE.md]

Link to:
- Quality Score: [../../QUALITY_SCORE.md](../../QUALITY_SCORE.md)
- Tech Debt Tracker: [../tech-debt-tracker.md](../tech-debt-tracker.md)

## Technical Approach

### Documentation Improvements

No code changes - documentation-only improvements.

### Tasks

1. Add component documentation
2. Add file path references to code (no line numbers)
3. Create workflow diagrams
4. Run CI and fix validation errors

## Implementation Phases

### Phase 1: Component Documentation (Week 1)
- [ ] Create component doc for [Component A]
- [ ] Create component doc for [Component B]
- [ ] Create component doc for [Component C]

### Phase 2: Code References (Week 2)
- [ ] Audit all code references for file paths (ensure no line numbers)
- [ ] Update references in ARCHITECTURE.md
- [ ] Update references in concept docs

### Phase 3: CI and Validation (Week 2)
- [ ] Run CI validation
- [ ] Fix any errors
- [ ] Verify all links work

## Testing Strategy

- Run ./validate-agentic-docs.yml locally
- Verify AGENTS.md stays under 150 lines
- Check all links with markdown-link-check

## Progress Notes

### YYYY-MM-DD
- Created initial framework
- Quality score: XX/100
- Next: Add component docs

## Completion Checklist

- [ ] Quality score ≥ 95/100
- [ ] All validation checks pass
- [ ] Plan moved to `completed/`
```

**Option 2: Create Plan for Current Development Work** (If applicable)

If there's ongoing feature development, create a plan for it instead:
- Document feature being developed
- Technical approach and phases
- Progress tracking

---

**MANDATORY VALIDATION FOR STEP 5.4**:

After completing this step, verify:

```bash
# Must return 2-3 (not counting template)
find agentic/decisions -name "adr-*.md" -not -name "*template*" | wc -l

# Must return 1 or more
find agentic/exec-plans/active -name "*.md" | wc -l

# Index must list ADRs
grep "ADR-" agentic/decisions/index.md
```

If any check fails, **Step 5.4 is incomplete**.

**Impact on Quality Score**:
- Without initial content: Freshness = 15/20, Total = ~75/100
- With initial content: Freshness = 19/20, Total = ~89/100
- Difference: **+14 points**

**Common Mistakes**:
- ❌ Creating only templates (not initial content)
- ❌ Waiting to "create ADRs later when decisions are made"
- ❌ Not documenting existing decisions already in codebase
- ❌ Leaving exec-plans/active/ empty

**Why This Matters**:
- ADRs explain "why the codebase is the way it is"
- Critical for onboarding new developers and AI agents
- Documents institutional knowledge before it's lost
- Raises quality score significantly

---

### Phase 6: Development Documentation

> **NOTE**: These files were already created in Phase 2, Step 2.2. This phase populates them with content.

#### Step 6.1: Populate agentic/DEVELOPMENT.md

**Task**: Complete developer setup and workflow guide in the DEVELOPMENT.md file created in Phase 2.

**Structure**:
```markdown
# Development Guide

## Prerequisites

- [Tool 1] version X+
- [Tool 2] version Y+
- [Access to Z]

## Initial Setup

1. Clone repository
```bash
git clone [repo-url]
cd [repo-name]
```

2. Install dependencies
```bash
[dependency install commands]
```

3. Build
```bash
[build commands]
```

## Development Workflow

### Making Changes

1. Create a branch
2. Make your changes
3. Run tests locally
4. Commit and push

### Running Tests

```bash
# Unit tests
[unit test command]

# Integration tests
[integration test command]

# E2E tests
[e2e test command]
```

### Local Testing

[How to test changes locally before committing]

## Debugging

### Debugging [Component 1]

1. [Step 1]
2. [Step 2]

### Debugging [Component 2]

1. [Step 1]
2. [Step 2]

### Common Issues

**Issue**: [Problem]
**Cause**: [Root cause]
**Fix**: [Solution]

## Code Organization

[Brief explanation of where things live]

See [ARCHITECTURE.md](../ARCHITECTURE.md) for details.

## Making a Pull Request

1. Ensure tests pass
2. Update documentation
3. Create PR with description
4. Address review feedback

See [CONTRIBUTING.md](../CONTRIBUTING.md) for full process.
```

**Validation**:
- [ ] Commands are tested and work
- [ ] Prerequisites are complete
- [ ] Debugging sections are helpful
- [ ] Links to other docs are present

#### Step 6.2: Populate agentic/TESTING.md

**Task**: Document test strategy and organization in the TESTING.md file created in Phase 2.

**Structure**:
```markdown
# Testing Strategy

## Test Pyramid

```
       /\
      /E2E\       [Small number, full system]
     /------\
    /  Integ \    [Medium number, component integration]
   /----------\
  /  Unit Tests \  [Large number, fast, isolated]
 /--------------\
```

## Test Organization

### Unit Tests

**Location**: `[test-dir]/*_test.[ext]`
**Run**: `[unit test command]`
**Coverage Target**: >80%

**Pattern**:
```[language]
[example test structure]
```

### Integration Tests

**Location**: [path]
**Run**: [command]

**Purpose**: [What they test]

### E2E Tests

**Location**: `test/e2e*/`
**Run**: `[e2e command]`

**Suites**:
- [Suite 1]: [Purpose]
- [Suite 2]: [Purpose]

## Writing Tests

### For New Features

1. Write unit tests for new code
2. Add integration tests for component interactions
3. Add E2E tests for user-facing changes

### For Bug Fixes

1. Write a failing test that reproduces the bug
2. Fix the bug
3. Verify test passes

## Running Tests Locally

```bash
# All tests
[all tests command]

# Specific test
[specific test command]

# With coverage
[coverage command]
```

## CI Test Execution

[Explanation of what runs in CI and when]

## Test Data

**Location**: [path to test fixtures]
**Format**: [description]

## Troubleshooting Test Failures

**Flaky tests**: [Process for handling]
**Timeout issues**: [Common solutions]
```

**Validation**:
- [ ] Test organization is clear
- [ ] Commands are correct
- [ ] Coverage targets specified
- [ ] Examples are provided

---

### Phase 6.5: Populate Remaining Required Files

> **CRITICAL**: These files were created in Phase 2, Step 2.2. They are **REQUIRED for ALL repositories**. This phase populates them with content specific to your repository.

#### Step 6.5.1: Populate agentic/DESIGN.md

**Task**: Document design philosophy and principles.

**Template Structure**:
```markdown
# Design Philosophy - [Repository Name]

## Overview

[2-3 sentences: What is the core design philosophy of this repository?]

## Design Principles

### 1. [Principle Name]
[Explanation of the principle]

**Why**: [Rationale]
**Example**: [Concrete example from this repo]

### 2. [Next Principle]
...

## Architecture Decisions

Key architectural decisions that shape this codebase:

1. **[Decision 1]**: [Brief explanation]
   - See: [ADR](./decisions/adr-NNNN.md)

2. **[Decision 2]**: [Brief explanation]
   - See: [ADR](./decisions/adr-NNNN.md)

## Design Patterns

### [Pattern Name]
**What**: [Description]
**When to use**: [Scenarios]
**Example**: [Location in code]

## Anti-Patterns to Avoid

### ❌ [Anti-Pattern Name]
**Don't**: [What to avoid]
**Do**: [What to do instead]
**Why**: [Rationale]

## Trade-offs

Document key trade-offs made in this design:

### [Trade-off 1]
**What we chose**: [Decision]
**What we gave up**: [Cost]
**Why**: [Rationale]

## Related Documentation

- [Core Beliefs](./design-docs/core-beliefs.md)
- [Architecture](../ARCHITECTURE.md)
- [ADRs](./decisions/)
```

**Validation**:
- [ ] Design principles documented
- [ ] Links to ADRs present
- [ ] Trade-offs explained
- [ ] Anti-patterns identified

#### Step 6.5.2: Populate agentic/RELIABILITY.md

**Task**: Document reliability requirements, SLOs, and operational procedures.

**Template Structure**:
```markdown
# Reliability - [Repository Name]

## Service Level Objectives (SLOs)

### Availability
**Target**: [e.g., 99.9% uptime]
**Measurement**: [How measured]
**Error Budget**: [e.g., 43 minutes/month]

### Latency
**Target**: [e.g., p95 < 500ms]
**Measurement**: [Metric name]

### Throughput
**Target**: [e.g., 1000 req/s]
**Measurement**: [Metric name]

## Observability

### Metrics

**Key Metrics** (Prometheus/OpenMetrics):
- `[metric_name]` - [Description]
  - Type: [Counter/Gauge/Histogram]
  - Labels: [label1, label2]
  - Use: [When to check this metric]

**Dashboards**:
- [Dashboard Name]: [Grafana link or description]

### Logging

**Log Levels**:
- Error: [When used]
- Warning: [When used]
- Info: [When used]
- Debug: [When used]

**Structured Logging Fields**:
- `component`: [Description]
- `operation`: [Description]

### Tracing

[If applicable: distributed tracing configuration]

## Alerts

### Critical Alerts

**Alert**: [Alert Name]
- **Condition**: [When it fires]
- **Impact**: [What's broken]
- **Response**: [What to do]
- **Runbook**: [Link or inline steps]

### Warning Alerts

**Alert**: [Alert Name]
- **Condition**: [When it fires]
- **Impact**: [Potential issue]
- **Response**: [What to check]

## Runbooks

### [Common Issue 1]
**Symptoms**: [How to recognize]
**Diagnosis**: [How to investigate]
**Resolution**: [How to fix]

### [Common Issue 2]
...

## Incident Response

1. **Detection**: [How incidents are detected]
2. **Triage**: [Initial assessment steps]
3. **Mitigation**: [Immediate actions]
4. **Resolution**: [Permanent fix]
5. **Post-mortem**: [Documentation process]

## Capacity Planning

**Current Capacity**: [Metrics]
**Growth Rate**: [Trend]
**Bottlenecks**: [Known limits]

## Disaster Recovery

**Backup**: [What's backed up, frequency]
**Recovery Time Objective (RTO)**: [Target]
**Recovery Point Objective (RPO)**: [Target]
**Recovery Procedure**: [Steps]

## Related Documentation

- [Architecture](../ARCHITECTURE.md)
- [Metrics Catalog](./generated/metrics-catalog.md)
- [Operations Guide](./DEVELOPMENT.md#operations)
```

**Validation**:
- [ ] SLOs defined and measurable
- [ ] Key metrics documented
- [ ] Alerts have runbooks
- [ ] Incident response process clear

#### Step 6.5.3: Populate agentic/SECURITY.md

**Task**: Document security model, threat analysis, and security controls.

**Template Structure**:
```markdown
# Security - [Repository Name]

## Security Model

### Trust Boundaries

[Diagram or description of trust boundaries in the system]

```
[External] → [API Gateway] → [Internal Services] → [Data Store]
  ^untrusted     ^auth         ^trusted            ^sensitive
```

### Threat Model

**Assets**:
1. [Asset 1] - [Why valuable, what protects it]
2. [Asset 2] - [Why valuable, what protects it]

**Threats**:
1. **[Threat Category]**: [Description]
   - **Attack Vector**: [How]
   - **Impact**: [Consequence]
   - **Mitigation**: [Controls in place]
   - **Risk Level**: [High/Medium/Low]

**Threat Modeling Framework**: [e.g., STRIDE, PASTA]

## Authentication & Authorization

### Authentication
**Mechanism**: [e.g., OAuth2, mTLS, ServiceAccount tokens]
**Implementation**: [Code location]
**Token Lifetime**: [Duration]

### Authorization
**Model**: [e.g., RBAC, ABAC]
**Implementation**: [Code location]

**Permissions**:
| Permission | Resource | Action | Who |
|------------|----------|--------|-----|
| [perm1] | [resource] | [action] | [role] |

## Data Protection

### Data Classification
- **Public**: [What data, handling]
- **Internal**: [What data, handling]
- **Confidential**: [What data, handling]
- **Restricted**: [What data, handling]

### Encryption
**At Rest**: [Encryption mechanism]
**In Transit**: [TLS version, cipher suites]
**Key Management**: [How keys are managed]

### Secrets Management
**Storage**: [e.g., Kubernetes Secrets, Vault]
**Rotation**: [Policy]
**Access Control**: [Who can access]

## Input Validation

**User Input**:
- [Field]: [Validation rules]
- [Field]: [Validation rules]

**API Input**:
- [Endpoint]: [Validation approach]
- [Endpoint]: [Validation approach]

**File Upload**:
- Size limits: [Limit]
- Type validation: [Allowed types]
- Content scanning: [Antivirus/malware checks]

## Secure Coding Practices

### Mandatory Checks
- [ ] Input validation on all external inputs
- [ ] Output encoding to prevent XSS
- [ ] Parameterized queries to prevent SQL injection
- [ ] CSRF protection for state-changing operations
- [ ] Rate limiting on public endpoints

### Code Review Focus
- Authentication bypass risks
- Authorization gaps
- Injection vulnerabilities
- Cryptographic misuse
- Sensitive data exposure

## Vulnerability Management

### Dependency Scanning
**Tool**: [e.g., Dependabot, Snyk]
**Frequency**: [Daily/Weekly]
**Response SLA**: [Time to patch]

### Security Testing
**SAST**: [Static analysis tool]
**DAST**: [Dynamic analysis tool]
**Penetration Testing**: [Frequency]

### Incident Response
**Security Incidents**:
1. **Detection**: [How detected]
2. **Containment**: [Immediate steps]
3. **Investigation**: [Forensics]
4. **Remediation**: [Fix and verify]
5. **Reporting**: [Who to notify, when]

## Compliance

**Standards**: [e.g., SOC 2, GDPR, PCI-DSS]
**Audit Logs**: [What's logged, retention]
**Compliance Checks**: [How verified]

## Security Contacts

**Security Team**: [Contact]
**Vulnerability Reports**: [Email/URL]
**Security Mailing List**: [List]

## Related Documentation

- [Architecture](../ARCHITECTURE.md)
- [Threat Model Details](./design-docs/threat-model.md)
- [Compliance](./design-docs/compliance.md)
```

**Validation**:
- [ ] Threat model documented
- [ ] Authentication/authorization clear
- [ ] Data protection mechanisms defined
- [ ] Incident response process documented
- [ ] Vulnerability management in place

---

### Phase 7: Automation and Validation

#### Step 7.1: Create CI Validation Workflow

**Task**: Create `.github/workflows/validate-agentic-docs.yml`

**Template**:
```yaml
name: Validate Agentic Documentation

on:
  pull_request:
    paths:
      - 'agentic/**'
      - '*.md'
      - '.github/workflows/validate-agentic-docs.yml'
  push:
    branches:
      - main
      - master

jobs:
  structure:
    name: Validate Structure
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check AGENTS.md length
        run: |
          lines=$(wc -l < AGENTS.md)
          echo "AGENTS.md has $lines lines"
          if [ $lines -gt 150 ]; then
            echo "❌ AGENTS.md too long ($lines lines). Keep under 150."
            exit 1
          fi
          echo "✅ AGENTS.md length OK"

      - name: Verify directory structure
        run: |
          required_dirs="design-docs domain exec-plans product-specs decisions references generated"
          for dir in $required_dirs; do
            if [ ! -d "agentic/$dir" ]; then
              echo "❌ Missing required directory: agentic/$dir"
              exit 1
            fi
          done
          echo "✅ Directory structure OK"

      - name: Check index files exist
        run: |
          required_indexes="design-docs/index.md domain/index.md product-specs/index.md decisions/index.md"
          for index in $required_indexes; do
            if [ ! -f "agentic/$index" ]; then
              echo "❌ Missing required index: agentic/$index"
              exit 1
            fi
          done
          echo "✅ Index files OK"

      - name: Check required top-level files exist
        run: |
          required_files="DESIGN.md DEVELOPMENT.md TESTING.md RELIABILITY.md SECURITY.md QUALITY_SCORE.md"
          for file in $required_files; do
            if [ ! -f "agentic/$file" ]; then
              echo "❌ Missing REQUIRED file: agentic/$file"
              echo "   These 6 files are mandatory for ALL repositories."
              exit 1
            fi
          done
          echo "✅ All required top-level files present"

  links:
    name: Validate Links
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check markdown links
        uses: lycheeverse/lychee-action@v1
        with:
          args: --verbose --no-progress 'agentic/**/*.md' '*.md'
          fail: true

  frontmatter:
    name: Validate Frontmatter
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check exec-plan frontmatter
        run: |
          for file in agentic/exec-plans/active/*.md agentic/exec-plans/completed/*.md; do
            if [ -f "$file" ]; then
              if ! head -n 1 "$file" | grep -q "^---$"; then
                echo "❌ $file missing YAML frontmatter"
                exit 1
              fi
            fi
          done
          echo "✅ Exec-plan frontmatter OK"

      - name: Check ADR frontmatter
        run: |
          for file in agentic/decisions/adr-*.md; do
            if [ -f "$file" ]; then
              if ! head -n 1 "$file" | grep -q "^---$"; then
                echo "❌ $file missing YAML frontmatter"
                exit 1
              fi
            fi
          done
          echo "✅ ADR frontmatter OK"

  freshness:
    name: Check Freshness
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check for stale TODOs
        run: |
          stale_count=0
          while IFS= read -r file; do
            last_modified=$(git log -1 --format=%ct "$file" 2>/dev/null || echo 0)
            now=$(date +%s)
            days=$(( ($now - $last_modified) / 86400 ))

            if [ $days -gt 30 ] && grep -q "TODO" "$file"; then
              echo "⚠️  $file has TODO and hasn't been updated in $days days"
              stale_count=$((stale_count + 1))
            fi
          done < <(find agentic -name "*.md" -type f)

          if [ $stale_count -gt 5 ]; then
            echo "❌ Too many stale TODOs ($stale_count). Update or move to tech-debt-tracker.md"
            exit 1
          fi
          echo "✅ TODO freshness OK"
```

**Validation**:
- [ ] Workflow file is valid YAML
- [ ] All checks are present
- [ ] Error messages are clear
- [ ] Runs on correct triggers

#### Step 7.2: Create QUALITY_SCORE.md with Progress Tracking

**Task**: Create agentic/QUALITY_SCORE.md with initial baseline and progress tracking section.

**Template** (adapt to your repo):

```markdown
# Documentation Quality Score

> **Last Updated**: YYYY-MM-DD
> **Score**: XX/100
> **Status**: [Good/Fair/Excellent] - [Brief description]

## Scoring Criteria

### 1. Navigation (20/20)

✅ **AGENTS.md exists and is < 150 lines**: [actual line count]
✅ **All concepts reachable in ≤3 hops**: Verified
✅ **Bidirectional links present**: Yes
✅ **No orphaned documents**: All linked from index files

**Score**: 20/20

### 2. Completeness (X/20)

✅ **Core concepts documented**: [List them]
✅ **All major workflows documented**: [List them]
⚠️ **[Gap if any]**: [Description]

**Score**: X/20

### 3. Freshness (X/20)

✅ **Templates provided**: exec-plans, ADRs
✅ **Tech debt tracker initialized**: Yes
✅ **ADRs created**: [Count] ADRs documenting key decisions
⚠️ **[Gap if any]**: [Description]

**Score**: X/20

### 4. Consistency (20/20)

✅ **No placeholder text**: All [REPO-NAME] replaced
✅ **Consistent formatting**: Markdown standards followed
✅ **YAML frontmatter where required**: All required docs have it
✅ **Relative paths for links**: All links use relative paths

**Score**: 20/20

### 5. Correctness (X/15)

✅ **Links are valid**: All internal links work
⚠️ **[Gap if any]**: [Description]

**Score**: X/15

### 6. Utility (10/10)

✅ **Practical examples**: Real code snippets
✅ **Troubleshooting guides**: Debug sections included
✅ **Metrics and monitoring**: Documented

**Score**: 10/10

### 7. Automation (X/15)

✅ **CI validation workflow created**: [Status]
⚠️ **[Gap if any]**: [Description]

**Score**: X/15

## Total Score: XX/100

**Interpretation**:
- **90-100**: Excellent - Comprehensive and well-maintained
- **80-89**: Good - Functional with room for improvement
- **70-79**: Fair - Significant gaps exist
- **60-69**: Poor - Major improvements needed
- **<60**: Critical - Documentation insufficient

---

## Recent Changes and Progress

> **Purpose**: Track documentation improvements over time
> **Update**: After each major documentation update

### Latest Update: YYYY-MM-DD

**Score Change**: XX/100 → YY/100 (+Z points)

**What Changed**:
- ✅ [Change 1]
- ✅ [Change 2]
- ✅ [Change 3]

**Files Added**:
```
agentic/decisions/
  - adr-0001-decision-name.md
  - adr-0002-decision-name.md

agentic/exec-plans/active/
  - plan-name.md
```

**Score Breakdown**:
| Category | Before | After | Change |
|----------|--------|-------|--------|
| Navigation | 20/20 | 20/20 | - |
| Completeness | X/20 | Y/20 | +Z |
| Freshness | X/20 | Y/20 | +Z |
| Consistency | 20/20 | 20/20 | - |
| Correctness | X/15 | Y/15 | +Z |
| Utility | 10/10 | 10/10 | - |
| Automation | X/15 | Y/15 | +Z |

**Next Steps** (to reach next milestone):
1. [Specific action with point value] (+N points) → Target score
2. [Specific action with point value] (+N points) → Target score
3. [Specific action with point value] (+N points) → Target score

---

### Previous Updates

#### YYYY-MM-DD: Initial Framework Implementation

**Score**: XX/100 (baseline)

**Created**:
- Complete directory structure ([N] directories)
- AGENTS.md ([N] lines) and ARCHITECTURE.md
- [N] concept docs
- [N] main documentation files
- Templates and index files
- CI validation workflow

**Initial Gaps**:
- [Gap 1] → -N points [Category]
- [Gap 2] → -N points [Category]

---

## Improvement Plan

### Completed ✅

[List completed improvements with dates and impact]

### High Priority (Next 30 Days)

[List high priority items with expected impact]

### Medium Priority (Next 60 Days)

[List medium priority items]

### Low Priority (Next 90 Days)

[List low priority items]

## Additional Quality Tracking (Manual - Not Scored)

> **Note**: This section is manual tracking, not measured by automated scripts.
> Update to reflect actual coverage (see Phase 7 Step 7.6 for audit instructions).

**Last Audited**: YYYY-MM-DD

### Code Component Documentation

- **[Component Type]**: X% documented (N/M components)
  - Examples: Controllers, Services, APIs, Commands
  - ✅ Documented: [List components with concept docs/ADRs]
  - ⚠️ Not yet: [List undocumented]
- **[Core Packages]**: X% documented (N/M packages)
- **[User Workflows]**: X% documented (N/M workflows)

### Link Health (Optional)

- **Status**: Not yet validated
- **Future**: Add link checker to CI

### Staleness (Optional)

- **Files with TODOs**: X
- **Last major update**: YYYY-MM-DD

## Validation Checklist

✅ **Structure**:
- [x] All required directories exist
- [x] All index files present
- [x] AGENTS.md < 150 lines

✅ **Content**:
- [x] No unreplaced placeholders
- [x] YAML frontmatter on required docs
- [x] All links use relative paths

✅ **Automation**:
- [x] CI workflow created
- [x] Link validation enabled
- [x] Freshness checks enabled

✅ **Navigation**:
- [x] Can reach any concept from AGENTS.md in ≤3 hops
- [x] Bidirectional links between related docs
- [x] No orphaned documentation

## Next Review Date

**Scheduled**: YYYY-MM-DD (3 months)

**Trigger for Early Review**:
- Major architectural changes
- New components added
- Significant API changes
- Quality score drops below [threshold]

## Related Documentation

- [AGENTS.md](../AGENTS.md) - Navigation entry point
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [Tech Debt Tracker](./exec-plans/tech-debt-tracker.md) - Known issues
```

**IMPORTANT**: The "Recent Changes and Progress" section is MANDATORY. Update it whenever you make significant documentation improvements. This provides a clear history of progress and helps track the evolution of documentation quality.

**Validation**:
- [ ] Initial quality score calculated
- [ ] Progress tracking section included
- [ ] Improvement plan defined
- [ ] Recent changes section populated

---

## Common Mistakes to Avoid

### ❌ MISTAKE 1: Making AGENTS.md Too Long

**Wrong**:
```markdown
# AGENTS.md (500 lines)

## [Concept]

[Concept] is a [long explanation spanning multiple paragraphs]...
```

**Right**:
```markdown
# AGENTS.md (100 lines)

## Core Concepts

| Concept | Definition | Docs |
|---------|-----------|------|
| [Concept] | [Brief definition] | [./agentic/domain/concepts/concept.md] |
```

### ❌ MISTAKE 2: Duplicating Content

**Wrong**:
- AGENTS.md explains concept (200 words)
- ARCHITECTURE.md explains concept (300 words)
- agentic/domain/concepts/concept.md explains it again (500 words)

**Right**:
- AGENTS.md: 1 sentence + link
- ARCHITECTURE.md: "See [detailed doc]"
- agentic/domain/concepts/concept.md: Full explanation (ONE place)

### ❌ MISTAKE 3: Broken Links

**Wrong**:
```markdown
See [design doc](./design.md)
# File is actually at agentic/design-docs/architecture.md
```

**Right**:
```markdown
See [design doc](./agentic/design-docs/architecture.md)
# Use correct relative path
```

### ❌ MISTAKE 4: Missing Frontmatter

**Wrong**:
```markdown
# Plan: Add Feature X

## Goal
...
```

**Right**:
```markdown
---
status: active
owner: @username
created: 2026-03-16
---

# Plan: Add Feature X

## Goal
...
```

### ❌ MISTAKE 5: Vague Code References

**Wrong**:
```markdown
The logic is in the controller package.
```

**Right**:
```markdown
The logic is in `pkg/controller/reconcile.go`
```

### ❌ MISTAKE 6: Assuming Data Structures Without Verification

**Wrong**:
```markdown
# In execution plan or implementation
"Pod logs are at /must-gather/*/logs/pods/*/*/*.log"
# Assumption made without checking actual output format
```

**Right**:
```markdown
# First, verify the actual structure:
# 1. Check reference docs (e.g., must-gather.md output format)
# 2. Grep for actual paths: grep -r "logs.*pod" codebase/
# 3. Look at similar implementations
#
# Verified path: /must-gather/namespaces/*/pods/*/*/logs/*.log
# Source: must-gather.md lines 225-235
```

**Why this matters**:
- Prevents implementing features based on wrong assumptions
- Saves time fixing incorrect paths/structures later
- Documents where the verified information came from

### ❌ MISTAKE 7: Creating Only Templates (NOT Initial Content)

**Wrong** (Initial implementation):
```bash
# After Phase 5:
find agentic/decisions -name "adr-*.md" | wc -l
# Result: 1 (only adr-template.md)

find agentic/exec-plans/active -name "*.md" | wc -l
# Result: 0 (empty directory)

# Quality Score: 75/100 (Freshness: 12/20)
```

**Right** (Initial implementation):
```bash
# After Phase 5:
find agentic/decisions -name "adr-*.md" | wc -l
# Result: 4 (template + 3 actual ADRs)

find agentic/exec-plans/active -name "*.md" | wc -l
# Result: 1 (documentation completion plan)

# Quality Score: 89/100 (Freshness: 19/20)
```

**Why This Matters**:
- Templates alone don't document anything
- Agents/developers need to understand EXISTING decisions
- Empty directories suggest incomplete work
- Quality score drops significantly (14-point difference)
- User has to manually request content creation

**How to Avoid**:
- Follow Step 5.4 completely
- Document 2-3 existing architectural decisions as ADRs
- Create at least 1 active exec-plan
- Update index.md files with content listings
- Run validation commands to verify

---

## Success Criteria

### Phase 1: Structure ✅
- [ ] All directories created
- [ ] Index files present
- [ ] CI workflow added

### Phase 2: Core Docs ✅
- [ ] AGENTS.md created (< 150 lines)
- [ ] ARCHITECTURE.md created
- [ ] agentic/design-docs/core-beliefs.md created
- [ ] All links valid

### Phase 3: Domain ✅
- [ ] Glossary created
- [ ] All major concepts documented
- [ ] Concept docs linked bidirectionally

### Phase 4: Exec-Plans & Decisions ✅
- [ ] Exec-plan template created
- [ ] ADR template created
- [ ] Tech debt tracker initialized
- [ ] Product specs directory created

### Phase 5: Initial Content (CRITICAL FOR NEW IMPLEMENTATIONS) ✅
- [ ] At least 2-3 ADRs created (not just template)
- [ ] At least 1 active exec-plan created
- [ ] decisions/index.md updated with ADR listings
- [ ] ADRs document EXISTING architectural decisions in codebase
- [ ] Validation commands pass (find ADRs >= 2, find active plans >= 1)

### Phase 6: Automation ✅
- [ ] CI validates structure
- [ ] CI checks links
- [ ] CI verifies frontmatter
- [ ] Quality score generated
- [ ] Background cleanup agents configured (garbage collection)

### Final Validation ✅
- [ ] All CI checks pass
- [ ] No broken links
- [ ] AGENTS.md < 150 lines
- [ ] Agent can navigate entire repo from AGENTS.md in ≤3 hops
- [ ] At least 2-3 ADRs exist (verify with: `find agentic/decisions -name "adr-*.md" -not -name "*template*" | wc -l`)
- [ ] At least 1 active exec-plan exists (verify with: `find agentic/exec-plans/active -name "*.md" | wc -l`)

---

## ⛔ STOP - Run Phase 7 (Metrics) Before Proceeding

**Do NOT** write summaries, commit messages, or "estimated" scores. **Run Phase 7 first.**

---

### Phase 7: Generate Metrics Dashboard (FIRST PASS COMPLETION) 🎯

🚨 **MANDATORY - DO NOT SKIP** 🚨

Measures ACTUAL quality score. "Estimated" scores are NOT acceptable. Without this, first pass is incomplete.

**Prerequisites**:
- ✅ Scripts copied in Phase 2 Step 2.3 (required!)
- ✅ All phases 1-6 completed
- ✅ Repository at `git rev-parse --show-toplevel` is your target repo

**If you skipped Step 2.3**: Go back and copy the scripts from agentic-guide first, or run them directly from agentic-guide.

#### Step 7.1: Run All Metrics with Dashboard Generation

```bash
# Navigate to repository root
cd "$(git rev-parse --show-toplevel)"

# Verify scripts exist (if missing, go back to Phase 2 Step 2.3)
if [ ! -f "./agentic/scripts/measure-all-metrics.sh" ]; then
    echo "❌ ERROR: Scripts not found. Run Phase 2 Step 2.3 first."
    exit 1
fi

# Generate comprehensive metrics with HTML dashboard
./agentic/scripts/measure-all-metrics.sh --html
```

**Output**:
- Terminal shows summary scores for each metric
- HTML dashboard created at `agentic/metrics-dashboard.html`

**If scripts fail to run**: Make sure you copied them correctly in Phase 2 Step 2.3. You can also run them directly from agentic-guide:
```bash
/path/to/agentic-guide/scripts/measure-all-metrics.sh --html
```

#### Step 7.2: Review Dashboard

```bash
# Open dashboard in browser
firefox agentic/metrics-dashboard.html
# Or: chrome agentic/metrics-dashboard.html
# Or: open agentic/metrics-dashboard.html  (macOS)
```

**Dashboard shows**:
- **Overall Quality Score**: 0-100 with color coding
- **Navigation Depth**: Unreachable documents, docs exceeding 3 hops
- **Context Budget**: Workflows over 700 lines
- **Structure Compliance**: Missing required files
- **Documentation Coverage**: ADR/concept/exec-plan counts

#### Step 7.3: Interpret Your Score

**90-100 (Excellent)** 🟢:
- ✅ First pass complete - no further action needed
- Consider sharing as example for other teams
- Set up CI to maintain quality
- **Second pass**: Optional (for perfectionists only)

**80-89 (Good)** 🔵:
- ✅ First pass complete - acceptable quality
- Minor issues identified in dashboard
- **Second pass**: Recommended if you want to reach 90+
- **Decision point**: Review dashboard, decide if improvements worth effort

**70-79 (Fair)** 🟡:
- ⚠️ First pass complete but significant gaps
- Dashboard highlights specific issues to fix
- **Second pass**: Strongly recommended
- **Action**: Follow [SECOND_PASS_GUIDE.md](./SECOND_PASS_GUIDE.md) to improve

**60-69 (Poor)** 🟠:
- ⚠️ First pass has major gaps
- Review dashboard for critical missing elements
- **Second pass**: Required
- **Action**: Fix critical issues first, then run second pass

**<60 (Critical)** 🔴:
- ❌ First pass incomplete or incorrect
- Dashboard shows fundamental structural problems
- **Action**: Review AGENTIC_DOCS_RULEBOOK.md, fix missing required elements
- Re-run metrics after fixes

#### Step 7.4: Document Your Score in QUALITY_SCORE.md

Update the "Recent Changes and Progress" section:

```markdown
### Latest Update: YYYY-MM-DD

**Score**: 0/100 → XX/100 (first pass implementation)

**What Changed**:
- ✅ Created complete agentic documentation structure
- ✅ Created AGENTS.md and ARCHITECTURE.md
- ✅ Created X ADRs, Y concept docs
- ✅ Generated metrics dashboard

**Next Steps**:
[Based on score, one of:]
- Score 90+: Maintain quality via CI
- Score 80-89: Consider second pass for optimization
- Score 70-79: Run second pass (SECOND_PASS_GUIDE.md)
- Score <70: Fix critical gaps first
```

#### Step 7.5: Decide on Second Pass

**Review the dashboard and choose**:

**Option A: Skip Second Pass** (score 85+, acceptable quality)
```bash
# Commit first pass implementation
git add agentic/ AGENTS.md ARCHITECTURE.md .github/
git commit -m "docs: implement agentic documentation framework

- Created complete structure (score: XX/100)
- Added AGENTS.md (YY lines), ARCHITECTURE.md
- Created Z ADRs, W concept docs
- Generated metrics dashboard

See agentic/metrics-dashboard.html for details

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Option B: Run Second Pass** (score <85, want improvement)
```bash
# Proceed to second pass refinement
# See SECOND_PASS_GUIDE.md for metrics-driven improvements:
# - Fix navigation depth violations
# - Optimize context budgets
# - Add missing coverage
# Target: 90+/100 (Excellent)
```

**Option C: Fix Critical Gaps** (score <70)
```bash
# Review dashboard for missing required elements
# Fix critical issues before second pass
# Common gaps:
# - Missing required top-level files (DESIGN.md, TESTING.md, etc.)
# - No ADRs or concept docs
# - AGENTS.md over 150 lines
# - Many broken links
```

#### Step 7.6: Update Manual Metrics in QUALITY_SCORE.md

⚠️ **IMPORTANT**: Automated scripts don't validate the "Quality Metrics" section in QUALITY_SCORE.md (controllers/packages/workflows percentages). These are manual tracking only.

**Action**: Open `agentic/QUALITY_SCORE.md`, find the "Quality Metrics" section, and:

1. **Identify major components** in your codebase (e.g., controllers, services, core packages)
2. **Count documented vs total**: Check which have concept docs or ADRs
3. **Update percentages**: Replace template placeholders with actual values
4. **Rename section**: Change header to "Additional Quality Tracking (Manual - Not Scored)"
5. **Add audit date**: Include "Last Audited: YYYY-MM-DD"

**Example**:
```markdown
## Additional Quality Tracking (Manual - Not Scored)

**Last Audited**: 2026-03-30

- **Controllers**: 67% (2/3 documented in concept docs)
- **Core Packages**: 100% (all critical packages have concept docs)
- **User Workflows**: 100% (primary workflows documented)
```

**Why**: Prevents stale placeholders like "60% documented" from misleading future maintainers.

---

#### Step 7.7: Archive Dashboard

```bash
# Add dashboard to git (optional - large file)
git add agentic/metrics-dashboard.html

# Or add to .gitignore (regenerate as needed)
echo "agentic/metrics-dashboard.html" >> .gitignore
```

**Validation**:
```bash
# MANDATORY: Verify Phase 7 complete
[ -f "agentic/metrics-dashboard.html" ] && echo "✅ Dashboard" || (echo "❌ No dashboard - run Step 7.1" && exit 1)
grep -q "Score.*TBD" agentic/QUALITY_SCORE.md && echo "❌ Update score from dashboard" && exit 1 || echo "✅ Score documented"
grep "OVERALL QUALITY SCORE" agentic/metrics-dashboard.html || echo "❌ Can't extract score"
```
**If any fails, GO BACK to Step 7.1.**

---

## 🎉 First Pass Complete!

**⛔ Verify Phase 7 first**: `[ -f "agentic/metrics-dashboard.html" ] && echo "✅" || echo "❌ GO BACK"`

**Your ACTUAL measured score** (from dashboard):
```bash
grep "OVERALL QUALITY SCORE" agentic/metrics-dashboard.html || echo "❌ No dashboard = Phase 7 incomplete"
```

**Next steps based on your ACTUAL MEASURED score from the dashboard**:

⚠️ **NOTE**: If you don't have an actual measured score, you did NOT complete Phase 7. Go back now.

| Score | Rating | Next Step |
|-------|--------|-----------|
| 90-100 | Excellent 🟢 | Set up CI, commit, done! |
| 80-89 | Good 🔵 | Optional: [SECOND_PASS_GUIDE.md](./SECOND_PASS_GUIDE.md) |
| 70-79 | Fair 🟡 | Recommended: [SECOND_PASS_GUIDE.md](./SECOND_PASS_GUIDE.md) |
| 60-69 | Poor 🟠 | Required: Fix gaps, then second pass |
| <60 | Critical 🔴 | Fix critical issues, re-run first pass |
| "TBD" or "Estimated" | ❌ INVALID | You did NOT run metrics. Go to Phase 7. |

**Questions?**
- Dashboard unclear? See [SCORING_GUIDE.md](./SCORING_GUIDE.md)
- Metrics confusing? See [METRICS_GUIDE.md](./METRICS_GUIDE.md)
- Need optimization? See [SECOND_PASS_GUIDE.md](./SECOND_PASS_GUIDE.md)

---

## Quick Reference

### What Goes Where

| I need to... | Create in | Guidance | Phase |
|-------------|-----------|----------|-------|
| Document a component | `agentic/design-docs/components/` | Step 4.4 | 4 |
| Document a concept (CRD, package, interface) | `agentic/domain/concepts/` | Step 4.2 | 4 |
| Document a workflow (multi-step process) | `agentic/domain/workflows/` | Step 4.3 | 4 |
| Define a term | `agentic/domain/glossary.md` | Step 4.1 | 4 |
| Create an ADR (architectural decision) | `agentic/decisions/` | Step 5.3 | 5 |
| Track active work | `agentic/exec-plans/active/` | Step 5.4 | 5 |
| Track tech debt | `agentic/exec-plans/tech-debt-tracker.md` | Step 5.2 | 5 |
| Link to enhancements (OpenShift) | `agentic/references/enhancement-index.md` | OpenShift guide § 1 | - |
| List APIs (OpenShift) | `agentic/references/openshift-apis.yaml` | OpenShift guide § 2 | - |
| Document operator patterns (OpenShift) | `agentic/references/openshift-operator-patterns-llms.txt` | OpenShift guide § 4 | - |
| Auto-generated docs | `agentic/generated/` | Step 2.2, Phase 7 | 2, 7 |

### File Naming Conventions
- Use lowercase
- Use hyphens for spaces: `custom-resource.md`
- Be descriptive: `auth-controller.md` not `controller.md`

### Link Formats
- Relative paths: `./agentic/domain/concepts/concept.md`
- Anchor links: `#section-name`
- Combined: `./ARCHITECTURE.md#component-boundaries`

### Code Reference Format
- With line: `pkg/controller/reconcile.go:89`
- Without line: `pkg/controller/reconcile.go`
- Pattern: `pkg/controller/*_test.go`

### Diagram Style
- ASCII art in markdown
- SVG files in agentic/design-docs/diagrams/
- Reference: `![Diagram](./diagrams/data-flow.svg)`

### Frontmatter Required
- Exec-plans (active/completed): status, owner, created, target
- ADRs: id, title, date, status, deciders
- Concept docs: concept, type, related
- Product specs: feature, status, owner

### Quality Thresholds
- Doc coverage: > 80%
- Link validity: 100% (no broken links)
- AGENTS.md length: < 150 lines
- Max navigation depth: 3 hops from AGENTS.md

---

## Final Checklist

Before marking documentation complete:

**Structure**:
- [ ] All directories exist
- [ ] All index files present
- [ ] CI workflow configured

**Core Files**:
- [ ] AGENTS.md (< 150 lines) ✅
- [ ] ARCHITECTURE.md ✅
- [ ] agentic/design-docs/core-beliefs.md ✅

**Required Top-Level Files** (ALL REPOS MUST HAVE):
- [ ] agentic/DESIGN.md ✅
- [ ] agentic/DEVELOPMENT.md ✅
- [ ] agentic/TESTING.md ✅
- [ ] agentic/RELIABILITY.md ✅
- [ ] agentic/SECURITY.md ✅
- [ ] agentic/QUALITY_SCORE.md ✅

**Domain Documentation**:
- [ ] Glossary complete
- [ ] All major concepts documented
- [ ] Workflows documented

**Exec-Plans & Decisions**:
- [ ] Template files created
- [ ] Tech debt tracker initialized
- [ ] At least 1 ADR for major decision
- [ ] Product specs directory created

**Validation**:
- [ ] All links work
- [ ] All frontmatter present
- [ ] CI passes
- [ ] Quality score > 80%

**Navigation**:
- [ ] Can reach any doc from AGENTS.md in ≤3 hops
- [ ] Bidirectional links present
- [ ] No orphaned docs

---

---

## 🎯 FINAL VALIDATION CHECKLIST

**Before considering documentation complete, ALL of these MUST be true:**

### For OpenShift Repositories

**If this is an OpenShift repository** (check: `grep "github.com/openshift" go.mod`):

```bash
# Check for OpenShift-specific documentation
[ -f "agentic/references/enhancement-index.md" ] || echo "⚠️  Consider creating enhancement index"
[ -f "agentic/references/openshift-apis.yaml" ] || echo "⚠️  Consider creating API inventory"
[ -f "agentic/references/openshift-ecosystem.md" ] || echo "⚠️  Consider creating ecosystem context"

# Check for OpenShift markers in glossary (if has OpenShift-specific terms)
grep -q "🔴\|⚫\|🟡" agentic/domain/glossary.md || echo "⚠️  Consider adding OpenShift term markers"

# Check for enhancement refs in ADRs (if features link to enhancements)
grep -r "enhancement-refs:\|enhancement:" agentic/decisions/ || echo "⚠️  Consider adding enhancement refs to ADRs"
```

**Note**: Not all OpenShift repos will have enhancements in openshift/enhancements or APIs in openshift/api. Many repos document their own enhancements locally. The checks above are guidelines, not hard requirements.

**Remember**: Check BOTH the repo's own docs/ directory AND external sources (openshift/enhancements, openshift/api) for relevant information.

### 🚨 MOST IMPORTANT: Benchmark Validation

```bash
# Run the 25-50 PR benchmark from FRAMEWORK.md
# Compare: Baseline vs. Minimal vs. Full
# Measure: Success rate, cost, steps to solution

# ONLY proceed if:
# - Success rate > baseline + 10%
# - Cost increase < 15%
# - No significant increase in agent confusion

# If fails: Use minimal approach or abandon framework
```

**Without benchmark validation, you're guessing. Don't skip this.**

### Structure
```bash
# Run validation script
./VALIDATION_SCRIPT.sh
# MUST exit with code 0 (success)
```

### Placeholder Replacement
```bash
# This MUST return NO results
grep -r '\[REPO-NAME\]\|\[Component1\]\|\[Concept1\]' agentic/ AGENTS.md ARCHITECTURE.md
```

### File Counts
```bash
# At minimum (more is OK):
# Directories: 13 (find agentic -type d | wc -l)
# Files: 18+ (find agentic -name "*.md" | wc -l plus root files)
```

### AGENTS.md Length
```bash
wc -l AGENTS.md  # MUST be ≤ 150
```

### Link Validity
```bash
# Install: npm install -g markdown-link-check
markdown-link-check AGENTS.md
markdown-link-check ARCHITECTURE.md
# MUST show 0 broken links
```

### YAML Frontmatter
```bash
# All exec-plans MUST start with ---
head -n1 agentic/exec-plans/active/*.md | grep "^---$"

# All ADRs MUST start with ---
head -n1 agentic/decisions/adr-*.md | grep "^---$"

# All concepts MUST start with ---
head -n1 agentic/domain/concepts/*.md | grep "^---$"
```

### CI Validation
```bash
# Workflow file exists
[ -f ".github/workflows/validate-agentic-docs.yml" ]

# Can parse YAML
yamllint .github/workflows/validate-agentic-docs.yml
```

---

## 📋 Process Adherence Audit

**Run after all phases to verify you followed the process (not just created output).**

```bash
#!/bin/bash
# Retrospective Process Audit - checks HOW you worked, not just WHAT you created

echo "==================================================================="
echo "PROCESS ADHERENCE AUDIT"
echo "==================================================================="

# Phase 1: Assessment
echo -e "\n[Phase 1] Can you explain repo in 1 sentence? (indicates you read it)"

# Phase 2: Structure
echo -e "\n[Phase 2] Checking directories and scripts..."
required_dirs="design-docs/components domain/concepts exec-plans/active decisions scripts"
missing=0
for dir in $required_dirs; do
  [ ! -d "agentic/$dir" ] && echo "❌ Missing: agentic/$dir" && missing=$((missing+1))
done
[ $missing -eq 0 ] && echo "✅ Directories exist" || echo "❌ $missing directories missing"

[ -f "agentic/scripts/measure-all-metrics.sh" ] && echo "✅ Scripts copied" || \
  echo "❌ Scripts missing (explains why Phase 7 skipped!)"

# Phase 3: Core Docs
echo -e "\n[Phase 3] Checking AGENTS.md..."
lines=$(wc -l < AGENTS.md)
[ $lines -le 150 ] && echo "✅ AGENTS.md: $lines lines" || echo "❌ AGENTS.md too long: $lines"

# Phase 4: Domain
echo -e "\n[Phase 4] Checking concepts..."
concepts=$(find agentic/domain/concepts -name "*.md" 2>/dev/null | wc -l)
[ $concepts -ge 5 ] && echo "✅ $concepts concept docs" || echo "❌ Only $concepts (need 5+)"

# Phase 5: Initial Content (CRITICAL)
echo -e "\n[Phase 5] Checking initial content (NOT just templates)..."
adrs=$(find agentic/decisions -name "adr-*.md" -not -name "*template*" 2>/dev/null | wc -l)
plans=$(find agentic/exec-plans/active -name "*.md" 2>/dev/null | wc -l)
[ $adrs -ge 2 ] && echo "✅ $adrs ADRs" || echo "❌ Only $adrs ADRs (need 2-3)"
[ $plans -ge 1 ] && echo "✅ $plans exec-plan" || echo "❌ No exec-plans (need 1+)"

# Phase 6: Required Files
echo -e "\n[Phase 6] Checking required top-level files..."
required="DESIGN.md DEVELOPMENT.md TESTING.md RELIABILITY.md SECURITY.md QUALITY_SCORE.md"
missing=0
for f in $required; do
  [ ! -f "agentic/$f" ] && echo "❌ Missing: $f" && missing=$((missing+1))
done
[ $missing -eq 0 ] && echo "✅ All 6 required files" || echo "❌ $missing files missing"

# Phase 7: Metrics (MOST CRITICAL)
echo -e "\n[Phase 7] Did you RUN metrics? (not estimate)"
if [ -f "agentic/metrics-dashboard.html" ]; then
  echo "✅ Dashboard exists"
  if grep -q "Score.*TBD\|Estimated.*Score" agentic/QUALITY_SCORE.md 2>/dev/null; then
    echo "❌ QUALITY_SCORE.md has TBD/Estimated (didn't update from dashboard!)"
  else
    echo "✅ Actual score documented"
    echo -e "\nYour measured score:"
    grep "OVERALL QUALITY SCORE" agentic/metrics-dashboard.html 2>/dev/null || echo "❌ Can't extract score"
  fi
else
  echo "❌ CRITICAL: No dashboard found - Phase 7 NOT completed!"
fi

echo -e "\n==================================================================="
echo "If any ❌ above, you did NOT complete the first pass."
echo "==================================================================="
```

**Red flags**: Missing directories, no scripts, <5 concepts, no ADRs, no exec-plans, missing top-level files, no dashboard.

---

## 🚀 QUICK START SCRIPT (Copy-Paste)

**Complete bootstrap in one command:**

```bash
#!/bin/bash
# Complete Agentic Documentation Bootstrap
# This creates structure, files, and runs validation

set -e

echo "🚀 Bootstrapping agentic documentation..."

# Create structure
mkdir -p agentic/{design-docs/components,domain/{concepts,workflows},exec-plans/{active,completed},product-specs,decisions,references,generated}

# Create all required files
for file in \
  "AGENTS.md" \
  "ARCHITECTURE.md" \
  "agentic/design-docs/index.md" \
  "agentic/design-docs/core-beliefs.md" \
  "agentic/domain/index.md" \
  "agentic/domain/glossary.md" \
  "agentic/product-specs/index.md" \
  "agentic/decisions/index.md" \
  "agentic/decisions/adr-template.md" \
  "agentic/references/index.md" \
  "agentic/exec-plans/template.md" \
  "agentic/exec-plans/tech-debt-tracker.md" \
  "agentic/DESIGN.md" \
  "agentic/DEVELOPMENT.md" \
  "agentic/TESTING.md" \
  "agentic/RELIABILITY.md" \
  "agentic/SECURITY.md" \
  "agentic/QUALITY_SCORE.md"  # ← Last 6 files REQUIRED for ALL repos
do
  touch "$file"
done

echo "✅ Structure and files created"
echo ""
echo "📝 Next steps:"
echo "1. Populate files using templates from AGENTIC_DOCS_RULEBOOK.md"
echo "2. Replace ALL [PLACEHOLDERS] with actual values"
echo "3. Run: ./VALIDATION_SCRIPT.sh"
echo "4. Fix any errors"
echo "5. Commit and push"
```

---

**End of Rulebook**

*When in doubt, optimize for agent legibility and progressive disclosure.*
*Keep AGENTS.md short. Link to details. Validate mechanically.*
*Replace ALL placeholders before committing.*
