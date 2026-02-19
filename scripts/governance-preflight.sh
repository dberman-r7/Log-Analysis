#!/bin/bash
# Governance Pre-Flight Check
# Run this before starting work to ensure governance compliance

set -e

echo "========================================="
echo "  Governance Pre-Flight Check"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}✗ Not in a git repository${NC}"
    exit 1
fi

echo -e "${GREEN}✓ In git repository${NC}"

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo ""
echo "Current branch: ${CURRENT_BRANCH}"

if [ "$CURRENT_BRANCH" = "main" ]; then
    echo -e "${YELLOW}⚠ WARNING: You are on the main branch${NC}"
    echo "  Create a feature branch before making changes:"
    echo "  git checkout -b feat/REQ-XXX-description"
    echo ""
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠ You have uncommitted changes${NC}"
    git status --short
    echo ""
fi

# Check for implementation plans
echo ""
echo "Checking for active implementation plans..."
IMPL_PLANS=$(find docs/processes/implementation-plans -name "IP-*.md" -type f 2>/dev/null | grep -v "README" || true)

if [ -n "$IMPL_PLANS" ]; then
    echo -e "${GREEN}✓ Found implementation plans:${NC}"
    echo "$IMPL_PLANS" | while read -r plan; do
        STATUS=$(grep "^**Status**:" "$plan" | head -1 | sed 's/.*: //' || echo "UNKNOWN")
        echo "  - $(basename "$plan") [${STATUS}]"
    done
else
    echo -e "${YELLOW}⚠ No implementation plans found${NC}"
fi

# Check for active CRs
echo ""
echo "Checking for recent change requests..."
RECENT_CRS=$(find docs/processes/change-requests -name "CR-*.md" -type f -mtime -7 2>/dev/null | grep -v "README" || true)

if [ -n "$RECENT_CRS" ]; then
    echo -e "${GREEN}✓ Found recent CRs (last 7 days):${NC}"
    echo "$RECENT_CRS" | while read -r cr; do
        STATUS=$(grep "^**Status**:" "$cr" | head -1 | sed 's/.*: //' || echo "UNKNOWN")
        echo "  - $(basename "$cr") [${STATUS}]"
    done
else
    echo "  No recent CRs found"
fi

# Quick governance reminders
echo ""
echo "========================================="
echo "  Quick Governance Reminders"
echo "========================================="
echo ""
echo "1. Perform QIA (Quick Impact Assessment) first"
echo "   - Functional change? YES/NO"
echo "   - CR-required triggers? YES/NO"
echo "   - CR required? YES/NO"
echo ""
echo "2. Create/update implementation plan for code changes"
echo "   Location: docs/processes/implementation-plans/"
echo ""
echo "3. If CR required: Create CR + IA, wait for ATP"
echo "   Location: docs/processes/change-requests/"
echo ""
echo "4. Always use feature branch + PR (no direct commits to main)"
echo ""
echo "5. Follow TDD: RED → GREEN → REFACTOR"
echo ""
echo "6. Complete DoD before requesting review"
echo ""

# Quick links
echo "========================================="
echo "  Quick Links"
echo "========================================="
echo ""
echo "Governance Framework:"
echo "  .github/copilot-instructions.md"
echo ""
echo "Change Management:"
echo "  docs/processes/change-management.md"
echo ""
echo "Definition of Done:"
echo "  docs/processes/definition-of-done.md"
echo ""
echo "Decision Trees:"
echo "  docs/processes/decision-trees/"
echo ""
echo "Steering Files:"
echo "  .kiro/steering/"
echo ""

echo "========================================="
echo "  Pre-Flight Check Complete"
echo "========================================="
echo ""
