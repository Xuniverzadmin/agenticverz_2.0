#!/bin/bash
# CI-C5-1: Advisory-Only Output Check
#
# Verifies that all learning outputs are advisory only.
# Reference: C5_S1_CI_ENFORCEMENT.md, AC-S1-I1, AC-S1-B4

set -e

BACKEND_DIR="${BACKEND_DIR:-backend}"
LEARNING_DIR="$BACKEND_DIR/app/learning"

echo "CI-C5-1: Advisory-Only Output Check"
echo "===================================="

# Check if learning directory exists
if [ ! -d "$LEARNING_DIR" ]; then
    echo "  SKIP: Learning directory not found (not implemented yet)"
    exit 0
fi

FAILED=0

# Check 1: No direct envelope modification
echo ""
echo "Check 1: No direct envelope modification patterns..."
FORBIDDEN=$(grep -rn "envelope\.bounds\s*=" "$LEARNING_DIR" 2>/dev/null || true)
if [ -n "$FORBIDDEN" ]; then
    echo "  FAIL: Direct envelope modification found:"
    echo "$FORBIDDEN"
    FAILED=1
else
    echo "  PASS: No direct envelope modification"
fi

# Check 2: No coordinator apply calls
echo ""
echo "Check 2: No coordinator apply calls..."
# Exclude comments and docstrings (lines with # or lines that are part of docstrings)
FORBIDDEN=$(grep -rn "coordinator\.apply\|coordinator\.update" "$LEARNING_DIR" 2>/dev/null | grep -v "^\s*#\|^\s*-\|No coordinator" || true)
if [ -n "$FORBIDDEN" ]; then
    echo "  FAIL: Direct coordinator call found:"
    echo "$FORBIDDEN"
    FAILED=1
else
    echo "  PASS: No coordinator apply calls"
fi

# Check 3: Suggestion type must be advisory
echo ""
echo "Check 3: Suggestion type enforcement..."
# Check that suggestion_type is set to "advisory"
ADVISORY_CHECK=$(grep -rn 'suggestion_type.*=.*"advisory"' "$LEARNING_DIR" 2>/dev/null || true)
NON_ADVISORY=$(grep -rn 'suggestion_type.*=' "$LEARNING_DIR" 2>/dev/null | grep -v '"advisory"' | grep -v "Literal" || true)
if [ -n "$NON_ADVISORY" ]; then
    echo "  FAIL: Non-advisory suggestion type found:"
    echo "$NON_ADVISORY"
    FAILED=1
else
    echo "  PASS: All suggestion types are advisory"
fi

# Check 4: Forbidden language patterns in suggestion text
echo ""
echo "Check 4: Forbidden language detection..."
# These patterns should not appear in hardcoded suggestion text
PATTERNS="'should '|'must '|'will improve'|'recommends'|'apply this'"
# Check in string literals that look like suggestion text
FORBIDDEN_LANG=$(grep -rniE "(suggestion_text|return.*f\"|text.*=.*f\").*($PATTERNS)" "$LEARNING_DIR" 2>/dev/null || true)
if [ -n "$FORBIDDEN_LANG" ]; then
    echo "  WARN: Potential forbidden language in suggestions:"
    echo "$FORBIDDEN_LANG"
    echo "  (Manual review required)"
else
    echo "  PASS: No forbidden language patterns detected"
fi

# Check 5: Literal["advisory"] type annotation
echo ""
echo "Check 5: Type annotation enforcement..."
LITERAL_CHECK=$(grep -rn 'Literal\["advisory"\]' "$LEARNING_DIR" 2>/dev/null || true)
if [ -z "$LITERAL_CHECK" ]; then
    echo "  WARN: No Literal['advisory'] type annotation found"
    echo "  (Recommended for type safety)"
else
    echo "  PASS: Literal['advisory'] type annotation present"
fi

echo ""
echo "===================================="
if [ $FAILED -eq 0 ]; then
    echo "CI-C5-1: PASS"
    exit 0
else
    echo "CI-C5-1: FAIL"
    exit 1
fi
