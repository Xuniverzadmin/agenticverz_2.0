#!/bin/bash
# C3 Guardrails CI Script
# Reference: PIN-225, C3_ENVELOPE_ABSTRACTION.md, C3_KILLSWITCH_ROLLBACK_MODEL.md
#
# Guards:
# - CI-C3-1: No envelope without validation
# - CI-C3-2: No envelope without revert callback (warning)
# - CI-C3-3: Kill-switch must remain testable
# - CI-C3-4: No prediction → No action (baseline behavior)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "=== C3 Guardrails CI ==="
echo "Reference: PIN-225, C3_ENVELOPE_ABSTRACTION.md"
echo ""

FAILED=0
WARNED=0

# CI-C3-1: No envelope without validation
echo "CI-C3-1: Checking envelope validation enforcement..."
if grep -rn "manager.apply" "$REPO_ROOT/backend/app" --include="*.py" 2>/dev/null | grep -v "test_" | grep -v "__pycache__"; then
    echo "  WARNING: Found envelope applications outside optimization module"
    echo "  All envelope applications must use EnvelopeManager.apply() which validates"
    WARNED=$((WARNED + 1))
fi
# Verify validation is called in manager
if grep -q "validate_envelope" "$REPO_ROOT/backend/app/optimization/manager.py"; then
    echo "  PASS: EnvelopeManager validates envelopes before application"
else
    echo "  FAIL: EnvelopeManager must call validate_envelope before apply"
    FAILED=$((FAILED + 1))
fi

# CI-C3-2: No envelope without revert policy (V5)
echo ""
echo "CI-C3-2: Checking revert policy enforcement..."
if grep -q "V5.*revert_on.*required" "$REPO_ROOT/backend/app/optimization/envelope.py"; then
    echo "  PASS: V5 enforces revert_on policy"
else
    echo "  FAIL: V5 must enforce revert_on policy"
    FAILED=$((FAILED + 1))
fi

# CI-C3-3: Kill-switch must remain testable
echo ""
echo "CI-C3-3: Checking kill-switch testability..."
if grep -q "reset_killswitch_for_testing" "$REPO_ROOT/backend/app/optimization/killswitch.py"; then
    echo "  PASS: Kill-switch is testable (reset function exists)"
else
    echo "  FAIL: Kill-switch must have reset_killswitch_for_testing function"
    FAILED=$((FAILED + 1))
fi
if grep -q "reset_manager_for_testing" "$REPO_ROOT/backend/app/optimization/manager.py"; then
    echo "  PASS: EnvelopeManager is testable (reset function exists)"
else
    echo "  FAIL: EnvelopeManager must have reset_manager_for_testing function"
    FAILED=$((FAILED + 1))
fi

# CI-C3-4: No prediction → No action (baseline behavior)
echo ""
echo "CI-C3-4: Checking baseline behavior on low confidence..."
if grep -q "min_confidence" "$REPO_ROOT/backend/app/optimization/manager.py"; then
    echo "  PASS: Manager checks prediction confidence threshold"
else
    echo "  FAIL: Manager must check min_confidence threshold"
    FAILED=$((FAILED + 1))
fi

# Run unit tests
echo ""
echo "Running C3 failure tests..."
cd "$REPO_ROOT/backend"
if python3 -m pytest tests/optimization/test_c3_failure_scenarios.py -v --tb=short -q 2>&1 | tail -20; then
    echo "  PASS: All C3 failure tests passed"
else
    echo "  FAIL: C3 failure tests failed"
    FAILED=$((FAILED + 1))
fi

# Summary
echo ""
echo "=== C3 Guardrails Summary ==="
echo "Failed: $FAILED"
echo "Warned: $WARNED"

if [ $FAILED -gt 0 ]; then
    echo ""
    echo "C3 GUARDRAILS FAILED"
    exit 1
fi

echo ""
echo "C3 GUARDRAILS PASSED"
exit 0
