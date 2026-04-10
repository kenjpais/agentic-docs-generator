# Agentic Documentation Framework - README

**For AI Agents and Human Developers**

This directory contains the complete framework for creating AI-agent-friendly documentation in OpenShift repositories, based on OpenAI's harness engineering principles.

---

## 📚 Files in This Framework

| File | Purpose | Audience |
|------|---------|----------|
| **AGENTIC_DOCS_FRAMEWORK.md** | Philosophy, principles, and overview | Humans understanding WHY |
| **AGENTIC_DOCS_RULEBOOK.md** | Step-by-step implementation guide | AI agents doing the WORK |
| **SECOND_PASS_GUIDE.md** | Metrics-driven refinement to >80% quality | AI agents (after first pass) |
| **METRICS_GUIDE.md** | Metrics measurement and validation | Both (run to measure quality) |
| **SCORING_GUIDE.md** | Understanding quality scores (NEW!) | Both (interpret results) |
| **VALIDATION_SCRIPT.sh** | Structure validation script | Both (run after implementation) |
| **AGENTIC_DOCS_README.md** | This file - navigation guide | Both |
| **scripts/** | Metrics measurement tools | Both (copy to your repo) |

---

## 🚀 Quick Start

### For AI Agents

**Your instructions are simple:**

**First Pass (Structure):**
1. **Read** [AGENTIC_DOCS_RULEBOOK.md](./AGENTIC_DOCS_RULEBOOK.md) in full
2. **Follow** each phase step-by-step
3. **Replace** ALL placeholders with actual values (see placeholder conventions in RULEBOOK)
4. **Validate** using `./VALIDATION_SCRIPT.sh`
5. **Fix** any errors reported
6. **Commit** only when validation passes

**Second Pass (Quality):**
7. **Run metrics**: `./agentic/scripts/measure-all-metrics.sh --html`
8. **Read** [SECOND_PASS_GUIDE.md](./SECOND_PASS_GUIDE.md) in full
9. **Fix gaps**: Navigation depth, context budget, coverage
10. **Re-validate**: Achieve >90% quality score
11. **Commit** improvements

**Critical rules:**
- ✅ NEVER leave `[PLACEHOLDERS]` in final documentation
- ✅ AGENTS.md MUST be < 150 lines
- ✅ ALL files MUST use relative paths for links
- ✅ YAML frontmatter REQUIRED on exec-plans, ADRs, and concept docs
- ✅ **CREATE INITIAL CONTENT** - At least 2-3 ADRs and 1 exec-plan (not just templates)
- ✅ Run validation script before committing

---

### For Humans

**If you're implementing this framework:**

1. **Understand WHY**: Read [AGENTIC_DOCS_FRAMEWORK.md](./AGENTIC_DOCS_FRAMEWORK.md)
2. **Understand HOW**: Skim [AGENTIC_DOCS_RULEBOOK.md](./AGENTIC_DOCS_RULEBOOK.md)
3. **Bootstrap**: Run the quick start script from RULEBOOK
4. **Populate**: Use templates and replace placeholders
5. **Validate**: Run `./VALIDATION_SCRIPT.sh`
6. **Iterate**: Fix errors until validation passes

**If you're using existing agentic docs:**

- Entry point: `AGENTS.md` (≈100 lines, table of contents)
- Navigate from there to find what you need
- Everything is ≤3 hops from AGENTS.md

---

## 🎯 Expected Outcomes

### What You'll Create

After following this framework, your repository will have:

```
<your-repo>/
├── AGENTS.md                    # 100-line navigation entry point
├── ARCHITECTURE.md              # System map with dependency rules
│
├── docs/                        # Your existing docs (untouched)
│
├── agentic/                     # Agent-structured knowledge base
│   ├── design-docs/
│   │   ├── index.md
│   │   ├── core-beliefs.md      # Golden principles
│   │   └── components/
│   ├── domain/
│   │   ├── glossary.md          # Canonical terminology
│   │   ├── concepts/            # Detailed concept docs
│   │   └── workflows/
│   ├── exec-plans/
│   │   ├── template.md
│   │   ├── active/              # Work in progress
│   │   ├── completed/           # Historical record
│   │   └── tech-debt-tracker.md
│   ├── product-specs/
│   ├── decisions/               # ADRs
│   ├── references/              # [tech]-llms.txt files
│   ├── generated/               # Auto-generated docs
│   ├── DESIGN.md
│   ├── DEVELOPMENT.md
│   ├── TESTING.md
│   ├── RELIABILITY.md
│   ├── SECURITY.md
│   └── QUALITY_SCORE.md
│
└── .github/workflows/
    └── validate-agentic-docs.yml
```

### Success Metrics

✅ **Navigation**: Any concept reachable from AGENTS.md in ≤3 hops
✅ **Freshness**: CI validates docs on every commit
✅ **Completeness**: Quality score > 80%
✅ **Consistency**: Zero placeholder text remains
✅ **Legibility**: Agents can find and understand any concept

---

## 🔍 Key Principles (from OpenAI)

### What Failed
❌ **"One Big AGENTS.md"** - Giant instruction files crowd out context

### What Works
✅ **Progressive Disclosure** - AGENTS.md as 100-line table of contents
✅ **Repository = Source of Truth** - Everything versioned, discoverable
✅ **Mechanical Enforcement** - CI validates, background agents clean up
✅ **Golden Principles** - Human taste captured once, enforced continuously
✅ **Plans as First-Class** - Active plans, completed plans, tech debt tracking

**Quote from OpenAI**:
> "Give Codex a map, not a 1,000-page instruction manual. Anything the agent can't access in-context effectively doesn't exist."

---

## 📋 Validation

### Structure Validation

```bash
# Run this before committing
./VALIDATION_SCRIPT.sh

# Should output:
# ✅ VALIDATION PASSED
#    Errors: 0
#    Warnings: 0
```

### Metrics Validation (NEW!)

```bash
# Copy metrics scripts to your repo
mkdir -p agentic/scripts
cp scripts/*.py agentic/scripts/
cp scripts/*.sh agentic/scripts/
chmod +x agentic/scripts/*.sh

# Run all metrics
./agentic/scripts/measure-all-metrics.sh

# Generate HTML dashboard
./agentic/scripts/measure-all-metrics.sh --html

# Validate metrics are correct
./agentic/scripts/test-metrics.sh
```

**See**: [METRICS_GUIDE.md](./METRICS_GUIDE.md) for complete documentation

### Manual Checks

```bash
# 1. Check AGENTS.md length
wc -l AGENTS.md  # Must be ≤ 150

# 2. Check for unreplaced placeholders
grep -r '\[REPO-NAME\]\|\[Component1\]' agentic/ AGENTS.md ARCHITECTURE.md
# Should return NO results

# 3. Validate links
npm install -g markdown-link-check
markdown-link-check AGENTS.md
# Should show 0 broken links

# 4. Check YAML frontmatter
head -n1 agentic/exec-plans/active/*.md | grep "^---$"
head -n1 agentic/decisions/adr-*.md | grep "^---$"
head -n1 agentic/domain/concepts/*.md | grep "^---$"
# All should start with ---
```

---

## 🤝 For OpenShift Project

### Consistency Across Repos

This framework is designed for **consistent results across all OpenShift repositories**:

- Same directory structure everywhere
- Same placeholder conventions
- Same validation process
- Same CI enforcement

**Benefits:**
- Agents trained on one repo work immediately on others
- New contributors onboard faster
- Cross-repo searches and analysis become possible
- Documentation quality is measurable and comparable

### Repo-Type Variations

The framework supports variations by repo type:

- **Operators**: Add CRD design docs, controller architecture
- **Libraries**: Add API design, stability guarantees, versioning
- **Services**: Add reliability, security, frontend patterns

See [AGENTIC_DOCS_FRAMEWORK.md](./AGENTIC_DOCS_FRAMEWORK.md#repo-type-specific-adaptations) for details.

---

## 📖 Example Workflow

### Agent Implementing a Feature

1. **Start**: Read `AGENTS.md` (≈2 min)
2. **Investigate**: Read ARCHITECTURE.md, relevant design docs, and domain concepts (2-3 hops)
3. **Validate**: Check assumptions about data structures, file formats, and patterns
4. **Clarify**: Ask questions if requirements are ambiguous
5. **Check**: Review core-beliefs.md for golden principles
6. **Plan**: Create exec-plan in `agentic/exec-plans/active/`
7. **Implement**: Write code following patterns
8. **Validate**: Tests pass, docs updated
9. **Complete**: Move plan to `completed/`, update quality score

**Total navigation**: ≤3 hops from AGENTS.md to any needed concept

---

## 🐛 Troubleshooting

### Validation Script Fails

**Error: "AGENTS.md too long"**
- Solution: Remove detailed explanations, link to `agentic/` instead
- Max: 150 lines

**Error: "Unreplaced placeholders found"**
- Solution: Search for `[REPO-NAME]`, `[Component1]`, etc. and replace with actual values
- Command: `grep -r '\[.*\]' AGENTS.md | grep -v '](.*)'`

**Error: "Missing YAML frontmatter"**
- Solution: Ensure first line of file is `---`
- Required for: exec-plans, ADRs, concept docs

**Error: "Broken links"**
- Solution: Use relative paths like `./agentic/domain/glossary.md`
- Test: `markdown-link-check filename.md`

### Common Mistakes

❌ Leaving placeholders like `[REPO-NAME]` in final docs
❌ Making AGENTS.md > 150 lines
❌ Using absolute paths in links
❌ Forgetting YAML frontmatter
❌ Not running validation script before committing

---

## 📞 Support

### For Questions

1. **Re-read** the relevant section in RULEBOOK
2. **Check** the templates for examples
3. **Validate** using the validation script
4. **Review** this README for common issues

### For Feedback

OpenShift project maintainers: File issues or PRs to improve this framework.

---

## 🎓 Learning Resources

### OpenAI Harness Engineering Article

The foundational article: https://openai.com/index/harness-engineering/

Key takeaways:
- "One big AGENTS.md" approach failed
- Progressive disclosure works
- Repository knowledge as system of record
- Golden principles for continuous enforcement
- Garbage collection for technical debt

### Related Concepts

- **Progressive Disclosure**: Start small, navigate deeper
- **Agent Legibility**: Optimize for how agents reason
- **Mechanical Enforcement**: CI and linters, not humans
- **Living Documentation**: Auto-updated, validated continuously

---

## 📝 Version History

**1.0** - Initial framework based on OpenAI harness engineering principles
- Complete directory structure
- Placeholder conventions
- Validation automation
- Repo-type specific guidance

---

## ✅ Quick Reference

### File Naming
- Lowercase with hyphens: `custom-resource.md`
- Concept files: `agentic/domain/concepts/[concept-name].md`
- ADRs: `agentic/decisions/adr-NNNN-[title].md`
- Exec-plans: `agentic/exec-plans/active/[feature-name].md`

### Placeholder Format
```
[REPO-NAME]      → machine-config-operator
[Component1]     → AuthController
[Concept1]       → MachineConfig
YYYY-MM-DD       → 2026-03-18
@[username]      → @johndoe
```

### Commands
```bash
# Bootstrap
mkdir -p agentic/{design-docs/components,domain/{concepts,workflows},exec-plans/{active,completed},product-specs,decisions,references,generated}

# Validate
./VALIDATION_SCRIPT.sh

# Check length
wc -l AGENTS.md

# Check placeholders
grep -r '\[REPO-NAME\]' .

# Check links
markdown-link-check AGENTS.md
```

---

**Ready to start?**

→ Agents: Go to [AGENTIC_DOCS_RULEBOOK.md](./AGENTIC_DOCS_RULEBOOK.md) and follow Phase 1
→ Humans: Read [AGENTIC_DOCS_FRAMEWORK.md](./AGENTIC_DOCS_FRAMEWORK.md) for context
