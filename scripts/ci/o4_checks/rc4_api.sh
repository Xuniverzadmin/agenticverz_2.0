#!/usr/bin/env bash
# =============================================================================
# RC-4: API Method Check
# =============================================================================
# Ensures O4 UI only makes GET requests to prediction endpoints.
# POST/PUT/DELETE/PATCH are forbidden.
#
# Reference: docs/contracts/O4_RECERTIFICATION_CHECKS.md
# =============================================================================

set -e

echo "=== RC-4: API Method Check ==="

# Define O4 paths
O4_PATHS=(
    "frontend/src/insights"
    "frontend/src/oversight"
    "frontend/src/components/predictions"
    "frontend/src/components/advisory"
    "frontend/src/api/predictions"
    "frontend/src/services/predictions"
)

# Check if paths exist
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

# Forbidden API patterns
WRITE_PATTERNS=(
    "\.post\("
    "\.put\("
    "\.delete\("
    "\.patch\("
    "POST.*prediction"
    "PUT.*prediction"
    "DELETE.*prediction"
    "PATCH.*prediction"
    "method:.*POST"
    "method:.*PUT"
    "method:.*DELETE"
    "method:.*PATCH"
)

FOUND=0

for pattern in "${WRITE_PATTERNS[@]}"; do
    echo "Checking for: '$pattern'"

    MATCHES=$(grep -riE "$pattern" "${EXISTING_PATHS[@]}" 2>/dev/null | \
              grep -iE "prediction|advisory" | \
              grep -vE "\.test\.|\.spec\.|\.md$" || true)

    if [ -n "$MATCHES" ]; then
        echo "❌ WRITE OPERATION DETECTED:"
        echo "$MATCHES"
        FOUND=1
    fi
done

echo ""

if [ $FOUND -eq 1 ]; then
    echo "============================================================"
    echo "❌ RC-4 FAILED: Write operation detected in O4 UI"
    echo "============================================================"
    echo ""
    echo "Fix: O4 is read-only. Only GET /api/v1/c2/predictions allowed."
    exit 1
else
    echo "✅ No write operations in O4"
    echo ""
    echo "============================================================"
    echo "✅ RC-4 PASSED: API method compliance verified"
    echo "============================================================"
    exit 0
fi
