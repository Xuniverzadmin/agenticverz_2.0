#!/bin/bash
# CI-C5-2: Human Approval Gate Check
#
# Verifies that no learned change applies without explicit human approval.
# Reference: C5_S1_CI_ENFORCEMENT.md, AC-S1-I2, AC-S1-H1-H4

set -e

BACKEND_DIR="${BACKEND_DIR:-backend}"
LEARNING_DIR="$BACKEND_DIR/app/learning"

echo "CI-C5-2: Human Approval Gate Check"
echo "===================================="

# Check if learning directory exists
if [ ! -d "$LEARNING_DIR" ]; then
    echo "  SKIP: Learning directory not found (not implemented yet)"
    exit 0
fi

FAILED=0

# Check 1: No auto-approval logic
echo ""
echo "Check 1: No auto-approval patterns..."
# Look for patterns that set approved=True without human action
AUTO_APPROVE=$(grep -rn "approved\s*=\s*True" "$LEARNING_DIR/s1_rollback.py" 2>/dev/null | grep -v "# Always False" || true)
if [ -n "$AUTO_APPROVE" ]; then
    echo "  FAIL: Auto-approval detected:"
    echo "$AUTO_APPROVE"
    FAILED=1
else
    echo "  PASS: No auto-approval in S1"
fi

# Check 2: No confidence-based approval
echo ""
echo "Check 2: No confidence-based approval..."
CONF_APPROVE=$(grep -rn "if.*confidence.*approved\s*=" "$LEARNING_DIR" 2>/dev/null || true)
if [ -n "$CONF_APPROVE" ]; then
    echo "  FAIL: Confidence-based approval detected:"
    echo "$CONF_APPROVE"
    FAILED=1
else
    echo "  PASS: No confidence-based approval"
fi

# Check 3: Applied flag defaults to False
echo ""
echo "Check 3: Applied flag default..."
APPLIED_TRUE=$(grep -rn "applied.*=.*True" "$LEARNING_DIR/s1_rollback.py" 2>/dev/null | grep -v "mark_applied" || true)
if [ -n "$APPLIED_TRUE" ]; then
    echo "  FAIL: Applied flag defaulting to True:"
    echo "$APPLIED_TRUE"
    FAILED=1
else
    echo "  PASS: Applied flag defaults to False"
fi

# Check 4: Status starts as pending_review
echo ""
echo "Check 4: Status default..."
if grep -q "status.*=.*SuggestionStatus.PENDING_REVIEW\|status.*pending_review" "$LEARNING_DIR/s1_rollback.py" 2>/dev/null; then
    echo "  PASS: Status defaults to pending_review"
else
    echo "  WARN: Could not verify status default"
fi

# Check 5: Human action methods exist
echo ""
echo "Check 5: Human action methods..."
if grep -q "def acknowledge\|def dismiss\|def mark_applied" "$LEARNING_DIR/suggestions.py" 2>/dev/null; then
    echo "  PASS: Human action methods present"
else
    echo "  WARN: Human action methods not found"
fi

echo ""
echo "===================================="
if [ $FAILED -eq 0 ]; then
    echo "CI-C5-2: PASS"
    exit 0
else
    echo "CI-C5-2: FAIL"
    exit 1
fi
