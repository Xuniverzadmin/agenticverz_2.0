#!/usr/bin/env bash
# =============================================================================
# RC-1: Forbidden Language Check
# =============================================================================
# Scans O4 UI files for forbidden words that violate advisory semantics.
#
# Reference: docs/contracts/O4_RECERTIFICATION_CHECKS.md
# =============================================================================

set -e

echo "=== RC-1: Forbidden Language Check ==="

# Define paths (adjust for actual frontend structure)
O4_PATHS=(
    "frontend/src/insights"
    "frontend/src/oversight"
    "frontend/src/components/predictions"
    "frontend/src/components/advisory"
)

# Check if paths exist (may not exist yet during development)
EXISTING_PATHS=()
for path in "${O4_PATHS[@]}"; do
    if [ -d "$path" ]; then
        EXISTING_PATHS+=("$path")
    fi
done

if [ ${#EXISTING_PATHS[@]} -eq 0 ]; then
    echo "⚠️  No O4 UI paths exist yet. Skipping check."
    echo "    (This is expected before UI implementation)"
    exit 0
fi

# Forbidden patterns (case-insensitive)
FORBIDDEN_PATTERNS=(
    "violation"
    "will happen"
    "risk level"
    "action required"
    "recommended"
    "urgent"
    "warning"
    "alert"
    "critical"
    "all clear"
    "no risk"
    "system healthy"
)

FOUND=0

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    echo "Checking for: '$pattern'"

    MATCHES=$(grep -riE "$pattern" "${EXISTING_PATHS[@]}" 2>/dev/null | \
              grep -vE "\.test\.|\.spec\.|\.md$|// RC-1 allowed|# RC-1 allowed" || true)

    if [ -n "$MATCHES" ]; then
        echo "❌ FORBIDDEN LANGUAGE FOUND:"
        echo "$MATCHES"
        FOUND=1
    fi
done

echo ""

if [ $FOUND -eq 1 ]; then
    echo "============================================================"
    echo "❌ RC-1 FAILED: Forbidden language detected"
    echo "============================================================"
    echo ""
    echo "Fix: Replace with approved copy from O4_UI_COPY_BLOCKS.md"
    exit 1
else
    echo "============================================================"
    echo "✅ RC-1 PASSED: No forbidden language found"
    echo "============================================================"
    exit 0
fi
