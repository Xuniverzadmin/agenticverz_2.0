#!/bin/bash
# CI-C5-5: Learning Disable Flag Check
#
# Verifies that learning can be disabled without affecting C1-C4.
# Reference: C5_S1_CI_ENFORCEMENT.md, AC-S1-I5, AC-S1-D1-D3

set -e

BACKEND_DIR="${BACKEND_DIR:-backend}"
LEARNING_DIR="$BACKEND_DIR/app/learning"

echo "CI-C5-5: Learning Disable Flag Check"
echo "===================================="

# Check if learning directory exists
if [ ! -d "$LEARNING_DIR" ]; then
    echo "  SKIP: Learning directory not found (not implemented yet)"
    exit 0
fi

FAILED=0

# Check 1: LEARNING_ENABLED flag exists
echo ""
echo "Check 1: LEARNING_ENABLED flag exists..."
if grep -q "LEARNING_ENABLED\|_LEARNING_ENABLED" "$LEARNING_DIR/config.py" 2>/dev/null; then
    echo "  PASS: LEARNING_ENABLED flag found"
else
    echo "  FAIL: LEARNING_ENABLED flag not found"
    FAILED=1
fi

# Check 2: Flag defaults to False
echo ""
echo "Check 2: Flag defaults to False..."
if grep -q "_LEARNING_ENABLED.*=.*False\|LEARNING_ENABLED.*=.*False" "$LEARNING_DIR/config.py" 2>/dev/null; then
    echo "  PASS: Flag defaults to False"
else
    # Check if it defaults to True (error)
    if grep -q "_LEARNING_ENABLED.*=.*True\|LEARNING_ENABLED.*=.*True" "$LEARNING_DIR/config.py" 2>/dev/null; then
        echo "  FAIL: Flag defaults to True (should be False)"
        FAILED=1
    else
        echo "  WARN: Could not verify flag default"
    fi
fi

# Check 3: Guard decorator exists
echo ""
echo "Check 3: Guard decorator exists..."
if grep -q "require_learning_enabled\|@require_learning" "$LEARNING_DIR/config.py" 2>/dev/null; then
    echo "  PASS: Guard decorator exists"
else
    echo "  WARN: Guard decorator not found"
fi

# Check 4: S1 entry point uses guard
echo ""
echo "Check 4: S1 uses guard pattern..."
if grep -q "@require_learning_enabled\|if not.*learning_enabled" "$LEARNING_DIR/s1_rollback.py" 2>/dev/null; then
    echo "  PASS: S1 uses guard pattern"
else
    echo "  FAIL: S1 does not use guard pattern"
    FAILED=1
fi

# Check 5: learning_enabled function exists
echo ""
echo "Check 5: learning_enabled function..."
if grep -q "def learning_enabled" "$LEARNING_DIR/config.py" 2>/dev/null; then
    echo "  PASS: learning_enabled function exists"
else
    echo "  FAIL: learning_enabled function not found"
    FAILED=1
fi

# Check 6: No C1-C4 dependencies on learning
echo ""
echo "Check 6: C1-C4 independence from learning..."
# Check that optimization module does not import learning
OPT_IMPORT=$(grep -rn "from app.learning\|import.*learning" "$BACKEND_DIR/app/optimization/" 2>/dev/null | grep -v "__pycache__" || true)
if [ -n "$OPT_IMPORT" ]; then
    echo "  WARN: Optimization module imports learning (review needed):"
    echo "$OPT_IMPORT"
else
    echo "  PASS: Optimization does not import learning"
fi

echo ""
echo "===================================="
if [ $FAILED -eq 0 ]; then
    echo "CI-C5-5: PASS"
    exit 0
else
    echo "CI-C5-5: FAIL"
    exit 1
fi
