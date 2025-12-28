#!/bin/bash
# CI-C5-4: Suggestion Versioning Check
#
# Verifies that all suggestions are versioned and immutable.
# Reference: C5_S1_CI_ENFORCEMENT.md, AC-S1-I4, AC-S1-M1-M3

set -e

BACKEND_DIR="${BACKEND_DIR:-backend}"
LEARNING_DIR="$BACKEND_DIR/app/learning"
ALEMBIC_DIR="$BACKEND_DIR/alembic/versions"

echo "CI-C5-4: Suggestion Versioning Check"
echo "===================================="

# Check if learning directory exists
if [ ! -d "$LEARNING_DIR" ]; then
    echo "  SKIP: Learning directory not found (not implemented yet)"
    exit 0
fi

FAILED=0

# Check 1: Version field in suggestion model
echo ""
echo "Check 1: Version field in suggestion model..."
if grep -q "version.*int\|version:.*Int" "$LEARNING_DIR/suggestions.py" 2>/dev/null; then
    echo "  PASS: Version field present in model"
else
    echo "  FAIL: Version field not found in suggestion model"
    FAILED=1
fi

# Check 2: No UPDATE patterns in S1
echo ""
echo "Check 2: No direct UPDATE patterns..."
UPDATE=$(grep -rniE "\.update\(|UPDATE.*learning_suggestions" "$LEARNING_DIR/s1_rollback.py" 2>/dev/null || true)
if [ -n "$UPDATE" ]; then
    echo "  FAIL: Direct UPDATE on suggestions found:"
    echo "$UPDATE"
    FAILED=1
else
    echo "  PASS: No direct UPDATE patterns in S1"
fi

# Check 3: No DELETE patterns
echo ""
echo "Check 3: No DELETE patterns..."
DELETE=$(grep -rniE "\.delete\(|DELETE.*learning_suggestions" "$LEARNING_DIR" 2>/dev/null || true)
if [ -n "$DELETE" ]; then
    echo "  FAIL: DELETE on suggestions found:"
    echo "$DELETE"
    FAILED=1
else
    echo "  PASS: No DELETE patterns"
fi

# Check 4: Immutability trigger in migration
echo ""
echo "Check 4: Immutability trigger in migration..."
if [ -d "$ALEMBIC_DIR" ]; then
    TRIGGER=$(grep -rn "prevent_suggestion_mutation" "$ALEMBIC_DIR"/*learning*.py 2>/dev/null || true)
    if [ -n "$TRIGGER" ]; then
        echo "  PASS: Immutability trigger found in migration"
    else
        echo "  WARN: Immutability trigger not found in migrations"
    fi
else
    echo "  INFO: Alembic directory not found"
fi

# Check 5: UUID generation for IDs
echo ""
echo "Check 5: UUID generation for suggestion IDs..."
if grep -q "uuid.uuid4\|gen_random_uuid" "$LEARNING_DIR/suggestions.py" 2>/dev/null; then
    echo "  PASS: UUID generation present"
else
    echo "  WARN: UUID generation not explicitly found"
fi

# Check 6: Timestamp field present
echo ""
echo "Check 6: Timestamp field..."
if grep -q "created_at.*datetime\|created_at:.*DateTime" "$LEARNING_DIR/suggestions.py" 2>/dev/null; then
    echo "  PASS: Timestamp field present"
else
    echo "  WARN: Timestamp field not found"
fi

echo ""
echo "===================================="
if [ $FAILED -eq 0 ]; then
    echo "CI-C5-4: PASS"
    exit 0
else
    echo "CI-C5-4: FAIL"
    exit 1
fi
