# OpenShift-Specific Agentic Documentation Guidance

**Purpose**: OpenShift-specific extensions to [AGENTIC_DOCS_FRAMEWORK.md](./AGENTIC_DOCS_FRAMEWORK.md)

---

## Discovery: Finding OpenShift Context

Before documenting, agents need to discover OpenShift-specific information.

⚠️ **IMPORTANT**: Check BOTH the repository's own documentation AND external sources (openshift/enhancements, openshift/api). Information may exist in both places.

### Step 1: Check Repository's Own Documentation

**Many OpenShift repos document their own enhancements and APIs in docs/**:

```bash
# Check for enhancement/design documents
find docs/ -name "*enhancement*" -o -name "*design*" 2>/dev/null
ls -la docs/enhancements/ 2>/dev/null

# Check for API documentation
find docs/ -name "*api*" -o -name "*crd*" 2>/dev/null

# Check README for links to designs
grep -i "enhancement\|design\|proposal" README.md
```

### Step 2: Check External OpenShift Repositories

**Even if repo has its own docs, also check external sources for additional context.**

### How to Find Related Repositories

**Check `go.mod` or dependency files**:
```bash
# Go repositories
grep "github.com/openshift" go.mod

# Common OpenShift dependencies to look for:
# - github.com/openshift/api (type definitions)
# - github.com/openshift/client-go (API clients)
# - github.com/openshift/library-go (operator patterns)
```

**Check import statements**:
```bash
# Find what APIs this repo uses
grep -r "github.com/openshift/api" --include="*.go" | grep import
grep -r "import.*openshift" --include="*.go"

# Find specific API groups used
grep -r "machine.openshift.io\|config.openshift.io\|operator.openshift.io" --include="*.go"
```

**Check for peer operators**:
```bash
# Look for references to other operators in comments or docs
grep -r "machine-config-operator\|cluster-.*-operator" --include="*.md" --include="*.go"

# Check README.md for related projects
grep -i "related\|depends\|requires" README.md
```

**Check cluster-version-operator**:
```bash
# See if this is a core operator by checking CVO manifests
# https://github.com/openshift/cluster-version-operator/tree/master/install
```

### How to Find Enhancement References

**Check BOTH local docs and openshift/enhancements repo.**

**Local docs** (this repository):
```bash
# Many repos have their own enhancement docs
ls docs/enhancements/ 2>/dev/null
find docs/ -name "*enhancement*" -o -name "*design*" 2>/dev/null
grep -r "enhancement\|KEP\|design doc" docs/ 2>/dev/null
```

**External repo** (openshift/enhancements):
```bash
# Search by repository name
# https://github.com/openshift/enhancements/search?q=[repo-name]

# Search by feature/concept
# https://github.com/openshift/enhancements/search?q=[feature-name]
```

**Check code comments**:
```bash
# Look for enhancement references in code
grep -r "enhancement\|enhancements.git" --include="*.go" --include="*.md"
grep -r "KEP-[0-9]\+" --include="*.go" --include="*.md"
```

**Check existing ADRs/docs**:
```bash
# Look in existing documentation
find . -name "*.md" -exec grep -l "openshift/enhancements" {} \;
```

### How to Find Documentation Links

**Standard OpenShift docs** (always applicable):
- Product: `https://docs.openshift.com/container-platform/latest/`
- API: `https://docs.openshift.com/container-platform/latest/rest_api/`
- Enhancements: `https://github.com/openshift/enhancements`

**Repo-specific docs**:
```bash
# Check for existing documentation
ls -la docs/ || echo "No docs directory"
cat README.md | grep -i "documentation\|docs"

# Check for API group documentation
# Format: https://docs.openshift.com/container-platform/latest/rest_api/[group]_apis/
# Example: https://docs.openshift.com/container-platform/latest/rest_api/machine_apis/
```

**Find upstream Kubernetes docs**:
```bash
# Check which K8s APIs are used
grep -r "k8s.io/api" go.mod

# Standard K8s docs: https://kubernetes.io/docs/
```

### How to Determine Repository Category

**Core Platform Operator** if:
- Listed in `openshift/cluster-version-operator/install/`
- Uses ClusterOperator status reporting
- Managed by cluster-version-operator

**Ecosystem Operator** if:
- Installed via OLM (Operator Lifecycle Manager)
- Uses OperatorCondition for status
- Not in CVO install manifests

**Check**:
```bash
# Look for ClusterOperator usage
grep -r "ClusterOperator\|config.openshift.io/v1" --include="*.go"

# Look for OLM/OperatorCondition
grep -r "OperatorCondition\|olm.operatorframework.io" --include="*.go"
```

---

## 1. Enhancement Tracking

Link all features to `openshift/enhancements` repository for design context.

### In ADRs

```yaml
---
id: ADR-[NNNN]
title: [Decision Title]
enhancement-refs:
  - repo: "openshift/enhancements"
    number: [NNNN]
    title: "[Enhancement Title]"
---
```

### In Exec-Plans

```yaml
---
status: active
enhancement: "openshift/enhancements#[NNNN]"
---
```

### In Concept Docs

```yaml
---
concept: [ConceptName]
enhancement: "openshift/enhancements#[NNNN]"
upstream-kep: "kubernetes/enhancements#[NNNN]" (if applicable)
---
```

### Enhancement Index

Create `agentic/references/enhancement-index.md`:

**Template**:
```markdown
# Enhancement Index

## Repository-Local Enhancements

**Check**: `docs/enhancements/` or `docs/` directory for enhancement docs in this repo.

| Enhancement | Feature | ADR | Concepts |
|-------------|---------|-----|----------|
| [Local Enhancement](../../docs/enhancements/feature.md) | [Name] | [Link to ADR] | [Links to concepts] |

## External Enhancements (openshift/enhancements)

**Note**: List enhancements from openshift/enhancements repo that are relevant to this repository. Check BOTH repo-local docs AND external enhancements - information may exist in both places.

| Enhancement | Feature | ADR | Concepts |
|-------------|---------|-----|----------|
| [#NNNN](https://github.com/openshift/enhancements/pull/NNNN) | [Name] | [Link] | [Links] |

## How to Use This Index

- **When implementing a feature**: Check if there's an enhancement doc (local or external) for design context
- **When documenting a decision**: Link to the relevant enhancement
- **When onboarding**: Read enhancements to understand "why" behind implementation
```

**Why this helps**: Provides design rationale and context for implementation decisions.

---

## 2. OpenShift API Tracking

Create `agentic/references/openshift-apis.yaml`:

```yaml
apis:
  - group: [api-group].openshift.io
    kind: [Kind]
    version: [version]
    source: vendor/github.com/openshift/api/[group]/[version]
    enhancement: "openshift/enhancements#[NNNN]"
    upstream: [true | false]

  - group: ""
    kind: [Kind]
    upstream: true
    modifications:
      - field: "[field.path]"
        enhancement: "openshift/enhancements#[NNNN]"

vendor-dependencies:
  - repo: github.com/openshift/api
    version: "[version]"
  - repo: github.com/openshift/library-go
    version: "[version]"
```

Reference in `ARCHITECTURE.md`:

```markdown
## OpenShift API Dependencies

See [API Inventory](./agentic/references/openshift-apis.yaml).

**Primary APIs**: [List with Enhancement links]
**Vendor**: openshift/api, openshift/client-go, openshift/library-go
```

**Why this helps**: Tells agents what APIs are available, where they're defined, and whether they're OpenShift-specific or upstream.

---

## 3. Cross-Repository Dependencies

In `ARCHITECTURE.md`:

```markdown
## OpenShift Ecosystem Dependencies

| Component | Relationship | Purpose |
|-----------|--------------|---------|
| openshift/api | Type definitions | [API groups] |
| openshift/library-go | Shared patterns | [Packages] |
| [related-operator] | [peer | coordinates-with] | [Description] |
```

Create `agentic/references/openshift-ecosystem.md`:

```markdown
# OpenShift Ecosystem Context

## Repository Category

**This repo is**: [Core Platform Operator | Ecosystem Operator | Library | API]

**Core Operators**: Report to ClusterOperator, managed by CVO
**Ecosystem Operators**: Use OperatorCondition, installed via OLM

## Dependencies for Pattern Examples

- **openshift/library-go**: [What to check for standard patterns]
- **openshift/api**: [What to check for type definitions]
- **[peer-operator]**: [What to check for similar implementations]
```

**Why this helps**: Directs agents to the right repos for finding implementation examples and patterns.

---

## 4. Operator Patterns

Create `agentic/references/openshift-operator-patterns-llms.txt`:

```markdown
# OpenShift Operator Patterns

## ClusterOperator Status (CORE OPERATORS ONLY)

**When**: Core platform operators managed by CVO
**NOT for**: Ecosystem operators, OLM-managed operators
**Location in this repo**: [file:line]

## OperatorCondition Status (ECOSYSTEM OPERATORS)

**When**: Non-core operators
**Location in this repo**: [file:line]

## Other Patterns

- Leader Election: library-go/pkg/operator/leaderelection
- Events/Logging: library-go/pkg/operator/events
- [Pattern]: [Location in this repo + library-go reference]
```

Reference from `agentic/design-docs/core-beliefs.md`:

```markdown
## OpenShift Patterns

**Used**:
- [Pattern] (library-go/[package])
- [ClusterOperator status - IF CORE] OR [OperatorCondition - IF ECOSYSTEM]

See: [OpenShift Operator Patterns](../references/openshift-operator-patterns-llms.txt)
```

**Why this helps**: Tells agents how to implement OpenShift-specific functionality correctly (e.g., status reporting).

---

## 5. Terminology

In `agentic/domain/glossary.md`, mark OpenShift-specific terms:

```markdown
### [Term] 🔴

**Definition**: [Definition]
**Type**: OpenShift API
**Not in upstream Kubernetes**: OpenShift extension
**Enhancement**: openshift/enhancements#[NNNN]
**Used by**: [Core operators only | All operators]

### [Term] ⚫

**Definition**: [Definition]
**Type**: Kubernetes Core
**Upstream**: true
**OpenShift Extensions**: [If any]

## OpenShift vs Kubernetes

| OpenShift | Kubernetes | Notes |
|-----------|------------|-------|
| [Term] | [Equivalent or "No equivalent"] | [Notes] |
```

**Markers**: 🔴 OpenShift-specific | ⚫ Kubernetes core | 🟡 Extended

**Why this helps**: Clarifies domain language so agents understand what's OpenShift-specific vs standard Kubernetes.

---

## 6. Documentation Links

Create `agentic/references/openshift-docs-standards.md`:

```markdown
# OpenShift Documentation Standards

**Product Docs**: https://docs.openshift.com/container-platform/latest/
**API Reference**: https://docs.openshift.com/container-platform/latest/rest_api/
**Enhancements**: https://github.com/openshift/enhancements
**Dev Guides**: https://github.com/openshift/enhancements/tree/master/dev-guide
**Kubernetes Docs**: https://kubernetes.io/docs/
```

**Why this helps**: Provides authoritative reference material for API usage and patterns.

---

## 7. Upstream Relationship

In `agentic/DESIGN.md`:

```markdown
## OpenShift and Kubernetes

**Built on**: Kubernetes [version]
**OpenShift adds**: [List API groups and features]

### Upstream Contributions

| Feature | KEP | Notes |
|---------|-----|-------|
| [Feature] | KEP-NNNN | [Context] |

### Where to Look for Examples

**Check Kubernetes** when:
- Implementing standard controller patterns
- Using core Kubernetes APIs
- Following controller-runtime patterns

**Check OpenShift** when:
- Using OpenShift-specific APIs (machine.openshift.io, config.openshift.io)
- Implementing operator patterns (library-go)
- Reporting status (ClusterOperator vs OperatorCondition)

**Check peer operators** (openshift/[similar-operator]) when:
- Implementing similar functionality
- Understanding OpenShift conventions
```

**Why this helps**: Directs agents where to look for implementation examples based on what they're trying to do.

---

## Required Files Checklist

- [ ] `agentic/references/enhancement-index.md` - Links features to design docs
- [ ] `agentic/references/openshift-apis.yaml` - API inventory and sources
- [ ] `agentic/references/openshift-ecosystem.md` - Where to find examples
- [ ] `agentic/references/openshift-operator-patterns-llms.txt` - How to implement patterns
- [ ] `agentic/references/openshift-docs-standards.md` - Reference links

## Required Sections Checklist

**ARCHITECTURE.md**: Ecosystem dependencies, related repos for examples
**agentic/DESIGN.md**: K8s relationship, where to look for patterns
**ADRs**: Enhancement refs for design context
**Concepts**: Enhancement refs, upstream vs OpenShift marker
**Glossary**: OpenShift-specific term markers (🔴 ⚫ 🟡)

## Validation

```bash
grep -r "enhancement:" agentic/decisions/ agentic/domain/concepts/
grep "🔴" agentic/domain/glossary.md
grep -i "openshift/api\|library-go" ARCHITECTURE.md
```

---

*Extends base framework - all standard requirements still apply (AGENTS.md <150 lines, CI validation, quality score >80%)*
