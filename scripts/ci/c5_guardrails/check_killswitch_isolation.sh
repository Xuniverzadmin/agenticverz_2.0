#!/bin/bash
# CI-C5-6: Kill-Switch Isolation Check
#
# Verifies that kill-switch behavior is completely unchanged by learning.
# Reference: C5_S1_CI_ENFORCEMENT.md, AC-S1-I6, AC-S1-B2-B3

set -e

BACKEND_DIR="${BACKEND_DIR:-backend}"
LEARNING_DIR="$BACKEND_DIR/app/learning"
KILLSWITCH_FILE="$BACKEND_DIR/app/optimization/killswitch.py"
COORDINATOR_FILE="$BACKEND_DIR/app/optimization/coordinator.py"

echo "CI-C5-6: Kill-Switch Isolation Check"
echo "===================================="

# Check if learning directory exists
if [ ! -d "$LEARNING_DIR" ]; then
    echo "  SKIP: Learning directory not found (not implemented yet)"
    exit 0
fi

FAILED=0

# Check 1: No kill-switch imports in learning module
echo ""
echo "Check 1: No kill-switch imports in learning..."
# Exclude comments and docstrings (lines with # or lines that are docstring explanations)
KS_IMPORT=$(grep -rn "from app\.optimization\.killswitch\|import killswitch" "$LEARNING_DIR" 2>/dev/null | grep -v "__pycache__\|^\s*#\|^\s*-\|MUST NOT" || true)
if [ -n "$KS_IMPORT" ]; then
    echo "  FAIL: Kill-switch import found in learning module:"
    echo "$KS_IMPORT"
    FAILED=1
else
    echo "  PASS: No kill-switch imports in learning"
fi

# Check 2: No coordinator core imports in learning
echo ""
echo "Check 2: No coordinator imports in learning..."
# Allow imports of data types (CoordinationAuditRecord, etc) but not the manager
COORD_IMPORT=$(grep -rn "from app\.optimization\.coordinator import.*Manager\|from app\.optimization import coordinator" "$LEARNING_DIR" 2>/dev/null | grep -v "__pycache__" || true)
if [ -n "$COORD_IMPORT" ]; then
    echo "  FAIL: Coordinator manager import found in learning module:"
    echo "$COORD_IMPORT"
    FAILED=1
else
    echo "  PASS: No coordinator manager imports in learning"
fi

# Check 3: No learning imports in kill-switch
echo ""
echo "Check 3: No learning imports in kill-switch..."
if [ -f "$KILLSWITCH_FILE" ]; then
    LEARNING_IN_KS=$(grep -n "from app\.learning\|import.*learning" "$KILLSWITCH_FILE" 2>/dev/null || true)
    if [ -n "$LEARNING_IN_KS" ]; then
        echo "  FAIL: Learning import found in killswitch module:"
        echo "$LEARNING_IN_KS"
        FAILED=1
    else
        echo "  PASS: No learning imports in killswitch"
    fi
else
    echo "  INFO: Killswitch file not found at expected path"
fi

# Check 4: No learning imports in coordinator core paths
echo ""
echo "Check 4: No learning imports in coordinator..."
if [ -f "$COORDINATOR_FILE" ]; then
    LEARNING_IN_COORD=$(grep -n "from app\.learning\|import.*learning" "$COORDINATOR_FILE" 2>/dev/null || true)
    if [ -n "$LEARNING_IN_COORD" ]; then
        echo "  FAIL: Learning import found in coordinator module:"
        echo "$LEARNING_IN_COORD"
        FAILED=1
    else
        echo "  PASS: No learning imports in coordinator"
    fi
else
    echo "  INFO: Coordinator file not found at expected path"
fi

# Check 5: Learning does not reference kill-switch state
echo ""
echo "Check 5: No kill-switch state access in learning..."
# Exclude tables.py which lists forbidden tables (not actual access)
KS_STATE=$(grep -rni "kill_switch_active\|killswitch_state\|fire_killswitch" "$LEARNING_DIR" 2>/dev/null | grep -v "__pycache__\|tables\.py" || true)
if [ -n "$KS_STATE" ]; then
    echo "  FAIL: Kill-switch state access in learning:"
    echo "$KS_STATE"
    FAILED=1
else
    echo "  PASS: No kill-switch state access in learning"
fi

# Check 6: Verify envelope imports are type-only
echo ""
echo "Check 6: Envelope imports are for types only..."
# Check that envelope imports are for data types, not managers
ENVELOPE_IMPORT=$(grep -n "from app\.optimization\.envelope import" "$LEARNING_DIR/s1_rollback.py" 2>/dev/null || true)
if [ -n "$ENVELOPE_IMPORT" ]; then
    # Verify it's importing types like CoordinationAuditRecord, not EnvelopeManager
    if echo "$ENVELOPE_IMPORT" | grep -q "Manager"; then
        echo "  FAIL: Manager import from envelope module"
        FAILED=1
    else
        echo "  PASS: Envelope imports are for type definitions only"
    fi
else
    echo "  INFO: No envelope imports found (may use passed-in data)"
fi

echo ""
echo "===================================="
if [ $FAILED -eq 0 ]; then
    echo "CI-C5-6: PASS"
    exit 0
else
    echo "CI-C5-6: FAIL"
    exit 1
fi
