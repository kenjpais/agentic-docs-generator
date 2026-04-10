#!/bin/bash
# Agentic Documentation Validation Script
# Run this to verify your agentic documentation is complete and correct
# Usage: ./VALIDATION_SCRIPT.sh

set -e  # Exit on first error

echo "🔍 Validating Agentic Documentation Structure..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0
warnings=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $1 exists"
    else
        echo -e "${RED}❌${NC} $1 MISSING"
        ((errors++))
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅${NC} $1/ exists"
    else
        echo -e "${RED}❌${NC} $1/ MISSING"
        ((errors++))
    fi
}

# Function to check for placeholders
check_placeholders() {
    local file=$1
    if [ ! -f "$file" ]; then
        return
    fi

    # Look for common placeholders (excluding markdown link syntax)
    if grep -E '\[(REPO-NAME|Component[0-9]|Concept[0-9]|Package[0-9]|workflow-name|feature-name|technology|source-dir|test-dir|language)\]' "$file" | grep -v '^\[.*\]('; then
        echo -e "${RED}❌${NC} $file contains unreplaced placeholders:"
        grep -E '\[(REPO-NAME|Component[0-9]|Concept[0-9])\]' "$file" | head -3
        ((errors++))
    else
        echo -e "${GREEN}✅${NC} $file: No unreplaced placeholders"
    fi
}

# Function to check file length
check_length() {
    local file=$1
    local max_lines=$2

    if [ ! -f "$file" ]; then
        return
    fi

    local lines=$(wc -l < "$file")
    if [ $lines -gt $max_lines ]; then
        echo -e "${RED}❌${NC} $file is $lines lines (max $max_lines)"
        ((errors++))
    else
        echo -e "${GREEN}✅${NC} $file is $lines lines (limit: $max_lines)"
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Checking Directory Structure"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_dir "agentic"
check_dir "agentic/design-docs"
check_dir "agentic/design-docs/components"
check_dir "agentic/domain"
check_dir "agentic/domain/concepts"
check_dir "agentic/domain/workflows"
check_dir "agentic/exec-plans"
check_dir "agentic/exec-plans/active"
check_dir "agentic/exec-plans/completed"
check_dir "agentic/product-specs"
check_dir "agentic/decisions"
check_dir "agentic/references"
check_dir "agentic/generated"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Checking Required Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_file "AGENTS.md"
check_file "ARCHITECTURE.md"
check_file "agentic/design-docs/index.md"
check_file "agentic/design-docs/core-beliefs.md"
check_file "agentic/domain/index.md"
check_file "agentic/domain/glossary.md"
check_file "agentic/product-specs/index.md"
check_file "agentic/decisions/index.md"
check_file "agentic/decisions/adr-template.md"
check_file "agentic/exec-plans/template.md"
check_file "agentic/exec-plans/tech-debt-tracker.md"
check_file "agentic/references/index.md"
check_file "agentic/DESIGN.md"
check_file "agentic/DEVELOPMENT.md"
check_file "agentic/TESTING.md"
check_file "agentic/RELIABILITY.md"
check_file "agentic/SECURITY.md"
check_file "agentic/QUALITY_SCORE.md"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Checking File Lengths"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_length "AGENTS.md" 150

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Checking for Unreplaced Placeholders"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_placeholders "AGENTS.md"
check_placeholders "ARCHITECTURE.md"
check_placeholders "agentic/design-docs/core-beliefs.md"
check_placeholders "agentic/domain/glossary.md"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Checking YAML Frontmatter"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check exec-plans
if ls agentic/exec-plans/active/*.md 1> /dev/null 2>&1; then
    for file in agentic/exec-plans/active/*.md; do
        if head -n 1 "$file" | grep -q "^---$"; then
            echo -e "${GREEN}✅${NC} $file has YAML frontmatter"
        else
            echo -e "${RED}❌${NC} $file MISSING YAML frontmatter"
            ((errors++))
        fi
    done
else
    echo -e "${YELLOW}⚠️${NC}  No active exec-plans found (this is OK if just starting)"
    ((warnings++))
fi

# Check concept docs
if ls agentic/domain/concepts/*.md 1> /dev/null 2>&1; then
    for file in agentic/domain/concepts/*.md; do
        if head -n 1 "$file" | grep -q "^---$"; then
            echo -e "${GREEN}✅${NC} $file has YAML frontmatter"
        else
            echo -e "${RED}❌${NC} $file MISSING YAML frontmatter"
            ((errors++))
        fi
    done
else
    echo -e "${YELLOW}⚠️${NC}  No concept docs found yet"
    ((warnings++))
fi

# Check ADRs
if ls agentic/decisions/adr-*.md 1> /dev/null 2>&1; then
    for file in agentic/decisions/adr-*.md; do
        if head -n 1 "$file" | grep -q "^---$"; then
            echo -e "${GREEN}✅${NC} $file has YAML frontmatter"
        else
            echo -e "${RED}❌${NC} $file MISSING YAML frontmatter"
            ((errors++))
        fi
    done
else
    echo -e "${YELLOW}⚠️${NC}  No ADRs found yet"
    ((warnings++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✅ VALIDATION PASSED${NC}"
    echo "   Errors: $errors"
    echo "   Warnings: $warnings"
    exit 0
else
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    echo "   Errors: $errors"
    echo "   Warnings: $warnings"
    echo ""
    echo "Fix the errors above and re-run this script."
    exit 1
fi
