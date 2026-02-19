#!/bin/bash
# Check if implementation plan exists and is up-to-date

set -e

IMPL_PLAN_DIR="docs/processes/implementation-plans"

echo "Checking for implementation plans..."
echo ""

# Check if directory exists
if [ ! -d "$IMPL_PLAN_DIR" ]; then
    echo "✗ Implementation plan directory not found: $IMPL_PLAN_DIR"
    exit 1
fi

# Find all implementation plans
PLANS=$(find "$IMPL_PLAN_DIR" -name "IP-*.md" -type f | grep -v "README" || true)

if [ -z "$PLANS" ]; then
    echo "⚠ No implementation plans found"
    echo ""
    echo "If you're making code changes, create an implementation plan:"
    echo "  Location: $IMPL_PLAN_DIR/"
    echo "  Template: docs/processes/templates/implementation-plan-template.md"
    exit 0
fi

echo "Found implementation plans:"
echo ""

# Check each plan
while IFS= read -r plan; do
    BASENAME=$(basename "$plan")
    echo "Plan: $BASENAME"
    
    # Extract status
    STATUS=$(grep "^**Status**:" "$plan" | head -1 | sed 's/.*: //' || echo "UNKNOWN")
    echo "  Status: $STATUS"
    
    # Check for QIA
    if grep -q "## Quick Impact Assessment (QIA)" "$plan"; then
        echo "  ✓ Has QIA"
    else
        echo "  ✗ Missing QIA"
    fi
    
    # Check for checklist
    if grep -q "## Implementation Checklist" "$plan"; then
        TOTAL=$(grep -c "^- \[" "$plan" || echo "0")
        DONE=$(grep -c "^- \[x\]" "$plan" || echo "0")
        echo "  ✓ Has checklist ($DONE/$TOTAL items complete)"
    else
        echo "  ✗ Missing checklist"
    fi
    
    # Check for progress log
    if grep -q "## Progress Log" "$plan"; then
        echo "  ✓ Has progress log"
    else
        echo "  ✗ Missing progress log"
    fi
    
    # Check last modified
    if [ "$(uname)" = "Darwin" ]; then
        LAST_MOD=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$plan")
    else
        LAST_MOD=$(stat -c "%y" "$plan" | cut -d'.' -f1)
    fi
    echo "  Last modified: $LAST_MOD"
    
    echo ""
done <<< "$PLANS"

echo "========================================="
echo "Reminder: Update implementation plans as you work"
echo "- Mark items complete: [ ] → [x]"
echo "- Add progress log entries with timestamps"
echo "- Update status: DRAFT → IN_PROGRESS → COMPLETE"
echo "========================================="
