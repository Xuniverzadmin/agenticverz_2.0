#!/usr/bin/env bash
# CI-C4-4: Same-parameter conflict is always rejected
# Reference: C4_CI_GUARDRAILS_DESIGN.md Section 2.4
#
# Checks:
# 1. Parameter index exists in CoordinationManager
# 2. check_allowed() checks for parameter conflicts
# 3. Same-parameter returns REJECTED, not PREEMPTED

set -e

BACKEND_DIR="${BACKEND_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../backend" && pwd)}"
COORDINATOR_FILE="${BACKEND_DIR}/app/optimization/coordinator.py"

echo "Checking: $COORDINATOR_FILE"

# Check 1: Parameter index exists
if ! grep -q "_parameter_index" "$COORDINATOR_FILE"; then
    echo "ERROR: _parameter_index not found in CoordinationManager"
    exit 1
fi
echo "  ✓ Parameter index exists"

# Check 2: check_allowed() checks parameter conflicts
if ! grep -A50 "def check_allowed" "$COORDINATOR_FILE" | grep -q "param_key.*_parameter_index"; then
    echo "ERROR: check_allowed() does not check parameter index"
    exit 1
fi
echo "  ✓ check_allowed() checks parameter conflicts"

# Check 3: Same-parameter conflict is REJECTED
if ! grep -A50 "def check_allowed" "$COORDINATOR_FILE" | grep -q "REJECTED"; then
    echo "ERROR: Same-parameter conflict does not return REJECTED"
    exit 1
fi
echo "  ✓ Same-parameter conflict returns REJECTED"

# Check 4: C4-R1 comment exists
if ! grep -q "C4-R1" "$COORDINATOR_FILE"; then
    echo "ERROR: C4-R1 rule not referenced in coordinator"
    exit 1
fi
echo "  ✓ C4-R1 rule referenced"

# Check 5: conflicting_envelope_id is set
if ! grep -A10 "Same-parameter" "$COORDINATOR_FILE" | grep -q "conflicting_envelope_id"; then
    echo "ERROR: conflicting_envelope_id not set for same-parameter rejection"
    exit 1
fi
echo "  ✓ conflicting_envelope_id is set"

echo "CI-C4-4: PASS"
exit 0
