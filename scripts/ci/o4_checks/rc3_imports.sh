#!/usr/bin/env bash
# =============================================================================
# RC-3: Import Isolation Check
# =============================================================================
# Ensures O4 components are NOT imported into forbidden areas.
#
# Forbidden areas:
#   - incidents pages
#   - enforcement pages
#   - ops/actions pages
#   - dashboard
#
# Reference: docs/contracts/O4_RECERTIFICATION_CHECKS.md
# =============================================================================

set -e

echo "=== RC-3: Import Isolation Check ==="

# Define forbidden areas (O4 must NOT be imported here)
FORBIDDEN_AREAS=(
    "frontend/src/incidents"
    "frontend/src/enforcement"
    "frontend/src/ops"
    "frontend/src/dashboard"
    "frontend/src/actions"
    "frontend/src/controls"
)

# Check if any forbidden areas exist
EXISTING_AREAS=()
for area in "${FORBIDDEN_AREAS[@]}"; do
    if [ -d "$area" ]; then
        EXISTING_AREAS+=("$area")
    fi
done

if [ ${#EXISTING_AREAS[@]} -eq 0 ]; then
    echo "⚠️  No forbidden areas exist yet. Skipping check."
    echo "    (This is expected before full UI implementation)"
    exit 0
fi

# O4 component patterns to detect
O4_PATTERNS=(
    "from.*insights"
    "from.*oversight"
    "from.*predictions"
    "from.*advisory"
    "PredictionCard"
    "AdvisoryPanel"
    "AdvisoryBanner"
    "ContainmentBanner"
)

FOUND=0

for pattern in "${O4_PATTERNS[@]}"; do
    echo "Checking for: '$pattern' in forbidden areas..."

    MATCHES=$(grep -riE "$pattern" "${EXISTING_AREAS[@]}" 2>/dev/null | \
              grep -vE "\.test\.|\.spec\.|\.md$" || true)

    if [ -n "$MATCHES" ]; then
        echo "❌ O4 COMPONENT IN FORBIDDEN AREA:"
        echo "$MATCHES"
        FOUND=1
    fi
done

echo ""

if [ $FOUND -eq 1 ]; then
    echo "============================================================"
    echo "❌ RC-3 FAILED: O4 components imported into forbidden areas"
    echo "============================================================"
    echo ""
    echo "Fix: O4 components must be isolated to /insights or /oversight"
    exit 1
else
    echo "✅ No O4 components in forbidden areas"
    echo ""
    echo "============================================================"
    echo "✅ RC-3 PASSED: Import isolation verified"
    echo "============================================================"
    exit 0
fi
