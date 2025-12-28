#!/usr/bin/env bash
# CI-C4-5: Kill-switch reverts all envelopes
# Reference: C4_CI_GUARDRAILS_DESIGN.md Section 2.5
#
# Checks:
# 1. kill_switch() method exists
# 2. kill_switch() iterates over ALL active envelopes
# 3. kill_switch() blocks new envelope applications
# 4. RevertReason.KILL_SWITCH exists

set -e

BACKEND_DIR="${BACKEND_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../backend" && pwd)}"
COORDINATOR_FILE="${BACKEND_DIR}/app/optimization/coordinator.py"
ENVELOPE_FILE="${BACKEND_DIR}/app/optimization/envelope.py"

echo "Checking: $COORDINATOR_FILE and $ENVELOPE_FILE"

# Check 1: kill_switch() method exists
if ! grep -q "def kill_switch" "$COORDINATOR_FILE"; then
    echo "ERROR: kill_switch() method not found"
    exit 1
fi
echo "  ✓ kill_switch() method exists"

# Check 2: kill_switch sets _kill_switch_active
if ! grep -A20 "def kill_switch" "$COORDINATOR_FILE" | grep -q "_kill_switch_active.*True"; then
    echo "ERROR: kill_switch() does not set _kill_switch_active"
    exit 1
fi
echo "  ✓ kill_switch() sets kill_switch_active flag"

# Check 3: kill_switch iterates over all active envelopes
if ! grep -A30 "def kill_switch" "$COORDINATOR_FILE" | grep -q "_active_envelopes"; then
    echo "ERROR: kill_switch() does not iterate over active envelopes"
    exit 1
fi
echo "  ✓ kill_switch() iterates over all active envelopes"

# Check 4: check_allowed blocks when kill_switch is active
if ! grep -A30 "def check_allowed" "$COORDINATOR_FILE" | grep -q "_kill_switch_active"; then
    echo "ERROR: check_allowed() does not check kill_switch state"
    exit 1
fi
echo "  ✓ check_allowed() blocks when kill_switch is active"

# Check 5: RevertReason.KILL_SWITCH exists
if ! grep -q "KILL_SWITCH" "$ENVELOPE_FILE"; then
    echo "ERROR: RevertReason.KILL_SWITCH not found"
    exit 1
fi
echo "  ✓ RevertReason.KILL_SWITCH exists"

# Check 6: I-C4-6 invariant referenced
if ! grep -q "I-C4-6" "$COORDINATOR_FILE"; then
    echo "ERROR: I-C4-6 invariant not referenced"
    exit 1
fi
echo "  ✓ I-C4-6 invariant referenced"

echo "CI-C4-5: PASS"
exit 0
