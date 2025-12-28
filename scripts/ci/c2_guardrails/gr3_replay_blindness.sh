#!/bin/bash
# =============================================================================
# GR-3: Replay Blindness (BLOCKER)
# =============================================================================
# Rule: Replay must not read or emit predictions. Replay is historical
#       truth, not foresight.
#
# Reference: PIN-222, I-C2-4
# Enforcement: BLOCKER - CI fails if replay references predictions
# =============================================================================

set -e

BACKEND_DIR="${1:-/root/agenticverz2.0/backend}"
REPLAY_DIR="$BACKEND_DIR/app/replay"

echo "GR-3: Checking replay blindness..."
echo "==================================="

# If replay directory doesn't exist, pass (no replay code yet)
if [ ! -d "$REPLAY_DIR" ]; then
    echo "GR-3 PASSED: No replay directory exists yet"
    exit 0
fi

VIOLATIONS=0

# Check for any prediction references in replay code
if grep -rE "(prediction_events|from app\.predictions|import.*prediction|PredictionEvent)" "$REPLAY_DIR" 2>/dev/null; then
    echo "VIOLATION: Prediction reference found in replay code"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# Also check replay-related files elsewhere
REPLAY_FILES=$(find "$BACKEND_DIR/app" -name "*replay*" -type f 2>/dev/null)
for file in $REPLAY_FILES; do
    if grep -E "(prediction_events|PredictionEvent)" "$file" 2>/dev/null; then
        echo "VIOLATION: Prediction reference found in $file"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

if [ $VIOLATIONS -gt 0 ]; then
    echo ""
    echo "GR-3 FAILED: $VIOLATIONS violation(s) detected"
    echo "Replay must be blind to predictions (I-C2-4)."
    exit 1
fi

echo "GR-3 PASSED: Replay does not reference predictions"
exit 0
