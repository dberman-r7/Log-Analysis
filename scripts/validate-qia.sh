#!/bin/bash
# Validate QIA (Quick Impact Assessment) Format

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <implementation-plan-file>"
    echo "Example: $0 docs/processes/implementation-plans/IP-2026-02-19-001-feature.md"
    exit 1
fi

FILE="$1"

if [ ! -f "$FILE" ]; then
    echo "Error: File not found: $FILE"
    exit 1
fi

echo "Validating QIA in: $FILE"
echo ""

# Check for QIA section
if ! grep -q "## Quick Impact Assessment (QIA)" "$FILE"; then
    echo "✗ Missing QIA section"
    echo "  Expected: ## Quick Impact Assessment (QIA)"
    exit 1
fi

echo "✓ QIA section found"

# Check for required QIA fields
REQUIRED_FIELDS=(
    "Functional change?"
    "Touches CR-required triggers?"
    "CR required?"
)

MISSING=0
for field in "${REQUIRED_FIELDS[@]}"; do
    if ! grep -q "$field" "$FILE"; then
        echo "✗ Missing QIA field: $field"
        MISSING=1
    else
        echo "✓ Found: $field"
    fi
done

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "QIA validation failed. Please ensure all required fields are present."
    exit 1
fi

# Check for YES/NO answers
if ! grep -E "Functional change\?" "$FILE" | grep -qE "\[YES|NO\]"; then
    echo "⚠ Warning: 'Functional change?' should have [YES] or [NO] answer"
fi

if ! grep -E "Touches CR-required triggers\?" "$FILE" | grep -qE "\[YES|NO\]"; then
    echo "⚠ Warning: 'Touches CR-required triggers?' should have [YES] or [NO] answer"
fi

if ! grep -E "CR required\?" "$FILE" | grep -qE "\[YES|NO\]"; then
    echo "⚠ Warning: 'CR required?' should have [YES] or [NO] answer"
fi

# Check for rationale
if ! grep -q "Rationale:" "$FILE"; then
    echo "⚠ Warning: Missing rationale for CR decision"
fi

echo ""
echo "✓ QIA validation complete"
