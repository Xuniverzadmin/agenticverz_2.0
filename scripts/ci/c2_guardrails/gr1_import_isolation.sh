#!/bin/bash
# =============================================================================
# GR-1: Import Isolation (BLOCKER)
# =============================================================================
# Rule: Prediction code must never be imported into control, execution,
#       or replay paths.
#
# Reference: PIN-222 (C2 Implementation Specification)
# Enforcement: BLOCKER - CI fails if violation detected
# =============================================================================

set -e

BACKEND_DIR="${1:-/root/agenticverz2.0/backend}"

echo "GR-1: Checking import isolation..."
echo "=================================="

# Define forbidden paths (where predictions must not be imported)
FORBIDDEN_PATHS=(
    "app/worker/runtime"
    "app/replay"
    "app/control"
)

VIOLATIONS=0

for path in "${FORBIDDEN_PATHS[@]}"; do
    full_path="$BACKEND_DIR/$path"
    if [ -d "$full_path" ]; then
        # Check for prediction imports
        if grep -rE "(from app\.predictions|import.*predictions|prediction_events)" "$full_path" 2>/dev/null; then
            echo "VIOLATION: Prediction import found in $path"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    fi
done

if [ $VIOLATIONS -gt 0 ]; then
    echo ""
    echo "GR-1 FAILED: $VIOLATIONS violation(s) detected"
    echo "Predictions must not leak into control/execution/replay paths."
    exit 1
fi

echo "GR-1 PASSED: No prediction imports in forbidden paths"
exit 0
