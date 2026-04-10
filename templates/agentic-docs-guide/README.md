# Agentic Documentation Framework

A structured approach to organizing repository knowledge for AI agents and human developers, based on [OpenAI's Harness Engineering](https://openai.com/index/harness-engineering/) principles.

## Quick Start

### For New Repositories

```bash
# 1. Copy scripts
cp -r /path/to/agentic-guide/VALIDATION_SCRIPT.sh your-repo/
cp -r /path/to/agentic-guide/scripts/ your-repo/agentic/scripts/

# 2. Follow the rulebook (creates structure + content)
# See AGENTIC_DOCS_RULEBOOK.md

# 3. Generate metrics dashboard (end of first pass)
cd your-repo
./agentic/scripts/measure-all-metrics.sh --html
firefox agentic/metrics-dashboard.html

# 4. Based on score, decide if second pass needed
# See dashboard for recommendations
```

### For Existing Repositories

```bash
# 1. Read the framework
cat AGENTIC_DOCS_FRAMEWORK.md

# 2. Follow installation guide
cat INSTALLATION.md

# 3. Validate and generate dashboard
./VALIDATION_SCRIPT.sh
./agentic/scripts/measure-all-metrics.sh --html
firefox agentic/metrics-dashboard.html  # Review your score

# 4. Decide: Second pass needed?
# - Score 90+: Done!
# - Score 80-89: Optional second pass
# - Score <80: Run SECOND_PASS_GUIDE.md
```

## Documentation

| File | Purpose |
|------|---------|
| [AGENTIC_DOCS_README.md](./AGENTIC_DOCS_README.md) | Start here - overview and navigation |
| [AGENTIC_DOCS_FRAMEWORK.md](./AGENTIC_DOCS_FRAMEWORK.md) | Philosophy and principles |
| [AGENTIC_DOCS_RULEBOOK.md](./AGENTIC_DOCS_RULEBOOK.md) | Step-by-step implementation guide |
| [METRICS_GUIDE.md](./METRICS_GUIDE.md) | Measurement and validation |
| [INSTALLATION.md](./INSTALLATION.md) | How to install in your repo |
| [VALIDATION_SCRIPT.sh](./VALIDATION_SCRIPT.sh) | Structure validation |
| [scripts/](./scripts/) | Metrics measurement tools |

## Key Concepts

**Problem**: Traditional docs fail AI agents because knowledge is scattered, no clear entry point, no decision history.

**Solution**: Treat repository as self-documenting knowledge system with:
- **Progressive disclosure**: AGENTS.md → navigate deeper
- **Execution plans**: Track all work from planning to completion
- **Architectural decisions**: Record why, not just what
- **Mechanical validation**: CI enforces quality
- **Measurable metrics**: Navigation depth, context budget, coverage
- **Visual dashboard**: HTML dashboard shows quality score at a glance

## Features

✅ **Structured navigation** - AGENTS.md as entry point (≤150 lines)
✅ **Progressive disclosure** - All concepts reachable in ≤3 hops
✅ **Execution tracking** - Plans for features, completed records
✅ **Decision records** - ADRs capture architectural choices
✅ **Automated validation** - CI enforces structure
✅ **Quality metrics** - Navigation depth, context budget, coverage
✅ **HTML dashboard** - Visual quality tracking

## Installation

See [INSTALLATION.md](./INSTALLATION.md) for complete guide.

### ⚠️ **CRITICAL: Customization Required**

This framework provides **generic templates**. You MUST customize for your repository:

**What to customize**:
1. **Workflows** in `scripts/measure-context-budget.py`:
   - Replace `agentic/domain/glossary.md` with YOUR core concepts
   - Add YOUR key ADRs and domain-specific docs
   - Match YOUR team's actual documentation usage patterns

2. **Content** in your repo:
   - Write YOUR architecture, design principles, concepts
   - Create YOUR ADRs for decisions made
   - Document YOUR domain-specific knowledge

**What NOT to customize**:
- Script logic (navigation depth, scoring algorithms)
- Directory structure (keep standard layout)
- Validation rules (AGENTS.md ≤150 lines, etc.)

**Why required**: Generic placeholders reference non-existent files. Customization ensures metrics measure YOUR actual documentation.

### Quick Start

```bash
# 1. Navigate to your repository
cd "$(git rev-parse --show-toplevel)"

# 2. Auto-detect and copy framework scripts
if [ -d "../agentic-guide" ]; then
    GUIDE_PATH="../agentic-guide"
else
    echo "Clone framework: git clone https://github.com/openshift/agentic-guide.git ../agentic-guide"
    exit 1
fi

cp "$GUIDE_PATH/VALIDATION_SCRIPT.sh" .
mkdir -p agentic/scripts
cp -r "$GUIDE_PATH/scripts/"* agentic/scripts/
chmod +x VALIDATION_SCRIPT.sh agentic/scripts/*.sh

# 3. CUSTOMIZE workflows (REQUIRED - see INSTALLATION.md Step 2)
$EDITOR agentic/scripts/measure-context-budget.py

# 4. Follow the rulebook to create content
# See AGENTIC_DOCS_RULEBOOK.md

# 5. Validate
./VALIDATION_SCRIPT.sh
./agentic/scripts/measure-all-metrics.sh
```

## Metrics & Validation

**NEW**: Automated measurement of documentation quality!

```bash
# Run all metrics (shell scripts - use ./ not python3)
./agentic/scripts/measure-all-metrics.sh

# Generate HTML dashboard
./agentic/scripts/measure-all-metrics.sh --html

# Validate calculations
./agentic/scripts/test-metrics.sh
```

**Note**: These are shell scripts (`.sh`), not Python. Use `./script.sh` or `bash script.sh`, **not** `python3 script.sh`.

**Measures**:
- **Navigation Depth**: Link distance from AGENTS.md (target: ≤3 hops)
- **Context Budget**: Lines loaded per workflow (target: ≤700)
- **Structure Compliance**: Required files exist
- **Documentation Coverage**: ADR/concept/plan counts

See [METRICS_GUIDE.md](./METRICS_GUIDE.md) and [scripts/README.md](./scripts/README.md)

## For OpenShift Repositories

See [OPENSHIFT_SPECIFIC_GUIDANCE.md](./OPENSHIFT_SPECIFIC_GUIDANCE.md) for:
- CRD documentation patterns
- Operator-specific guidance
- OpenShift conventions
- Example implementations

## Examples

- **machine-config-operator**: Full implementation with metrics
- *(More examples coming soon)*

## Contributing

1. Test changes against multiple repositories
2. Update documentation
3. Ensure metrics validation passes
4. Submit PR

## Support

**Questions?** Check:
1. [AGENTIC_DOCS_README.md](./AGENTIC_DOCS_README.md) - Overview
2. [INSTALLATION.md](./INSTALLATION.md) - Setup guide
3. [METRICS_GUIDE.md](./METRICS_GUIDE.md) - Measurement guide
4. File an issue in this repository

## Version

**Framework Version**: 1.1
**Last Updated**: 2026-03-27

**v1.1 Changes**:
- ⚠️ Breaking: Workflows now generic (must customize for your repo)
- ✅ Fixed: Scoring bug (terminal now matches HTML)
- ✅ Added: SECOND_PASS_GUIDE.md for quality improvement
- ✅ Added: SCORING_GUIDE.md for interpreting results

---

**Key Principle**: *What an agent can't find effectively doesn't exist.*
