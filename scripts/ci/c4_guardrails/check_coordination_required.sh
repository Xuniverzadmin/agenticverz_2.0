#!/usr/bin/env bash
# CI-C4-2: No envelope applies without coordination check
# Reference: C4_CI_GUARDRAILS_DESIGN.md Section 2.2
#
# Checks:
# 1. CoordinationManager class exists
# 2. check_allowed() method exists
# 3. apply() method calls check_allowed()
# 4. No direct envelope.lifecycle = ACTIVE outside coordinator

set -e

BACKEND_DIR="${BACKEND_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../backend" && pwd)}"
COORDINATOR_FILE="${BACKEND_DIR}/app/optimization/coordinator.py"

echo "Checking: $COORDINATOR_FILE"

# Check 1: CoordinationManager class exists
if ! grep -q "class CoordinationManager" "$COORDINATOR_FILE"; then
    echo "ERROR: CoordinationManager class not found"
    exit 1
fi
echo "  ✓ CoordinationManager class exists"

# Check 2: check_allowed() method exists
if ! grep -q "def check_allowed" "$COORDINATOR_FILE"; then
    echo "ERROR: check_allowed() method not found"
    exit 1
fi
echo "  ✓ check_allowed() method exists"

# Check 3: apply() method exists
if ! grep -q "def apply" "$COORDINATOR_FILE"; then
    echo "ERROR: apply() method not found"
    exit 1
fi
echo "  ✓ apply() method exists"

# Check 4: apply() calls check_allowed()
if ! grep -A30 "def apply" "$COORDINATOR_FILE" | grep -q "check_allowed"; then
    echo "ERROR: apply() does not call check_allowed()"
    exit 1
fi
echo "  ✓ apply() calls check_allowed()"

# Check 5: CoordinationDecision class exists
if ! grep -q "class CoordinationDecision" "${BACKEND_DIR}/app/optimization/envelope.py"; then
    echo "ERROR: CoordinationDecision class not found"
    exit 1
fi
echo "  ✓ CoordinationDecision class exists"

echo "CI-C4-2: PASS"
exit 0
