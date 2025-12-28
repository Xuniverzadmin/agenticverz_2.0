#!/usr/bin/env bash
# C4 CI Guardrails - Run All Checks
# Reference: C4_CI_GUARDRAILS_DESIGN.md, PIN-230
#
# These guardrails enforce C4 coordination invariants:
# CI-C4-1: Every envelope declares exactly one class
# CI-C4-2: No envelope applies without coordination check
# CI-C4-3: Priority order is not overridable
# CI-C4-4: Same-parameter conflict is always rejected
# CI-C4-5: Kill-switch reverts all envelopes
# CI-C4-6: Coordination audit is emitted
# CI-C4-7: Audit immutability (no UPDATE/DELETE)
# CI-C4-8: Audit isolation (no learning imports in coordinator)
# CI-C4-9: Audit replay safety (emit_traces respected)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/../../../backend"

echo "=========================================="
echo "C4 CI GUARDRAILS - Multi-Envelope Coordination"
echo "=========================================="
echo ""

FAILED=0
PASSED=0

run_check() {
    local name="$1"
    local script="$2"

    echo "----------------------------------------"
    echo "CHECK: $name"
    echo "----------------------------------------"

    if bash "$script"; then
        echo "✅ PASS: $name"
        PASSED=$((PASSED + 1))
    else
        echo "❌ FAIL: $name"
        FAILED=$((FAILED + 1))
    fi
    echo ""
}

# CI-C4-1: Envelope class declaration
run_check "CI-C4-1: Envelope class declaration" "${SCRIPT_DIR}/check_envelope_class.sh"

# CI-C4-2: Coordination check required
run_check "CI-C4-2: Coordination check required" "${SCRIPT_DIR}/check_coordination_required.sh"

# CI-C4-3: Priority order immutable
run_check "CI-C4-3: Priority order immutable" "${SCRIPT_DIR}/check_priority_immutable.sh"

# CI-C4-4: Same-parameter rejection
run_check "CI-C4-4: Same-parameter rejection" "${SCRIPT_DIR}/check_same_parameter.sh"

# CI-C4-5: Kill-switch all-revert
run_check "CI-C4-5: Kill-switch all-revert" "${SCRIPT_DIR}/check_killswitch.sh"

# CI-C4-6: Coordination audit
run_check "CI-C4-6: Coordination audit" "${SCRIPT_DIR}/check_audit.sh"

# CI-C4-7: Audit immutability
run_check "CI-C4-7: Audit immutability" "${SCRIPT_DIR}/check_audit_immutability.sh"

# CI-C4-8: Audit isolation
run_check "CI-C4-8: Audit isolation" "${SCRIPT_DIR}/check_audit_isolation.sh"

# CI-C4-9: Audit replay safety
run_check "CI-C4-9: Audit replay safety" "${SCRIPT_DIR}/check_audit_replay_safety.sh"

echo "=========================================="
echo "C4 CI GUARDRAILS SUMMARY"
echo "=========================================="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -gt 0 ]; then
    echo "❌ C4 GUARDRAILS FAILED"
    exit 1
else
    echo "✅ C4 GUARDRAILS PASSED"
    exit 0
fi
