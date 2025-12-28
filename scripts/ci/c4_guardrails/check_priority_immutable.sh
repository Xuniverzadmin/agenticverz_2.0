#!/usr/bin/env bash
# CI-C4-3: Priority order is not overridable
# Reference: C4_CI_GUARDRAILS_DESIGN.md Section 2.3
#
# Checks:
# 1. ENVELOPE_CLASS_PRIORITY constant exists
# 2. Priority order is SAFETY=1, RELIABILITY=2, COST=3, PERFORMANCE=4
# 3. No dynamic priority modification
# 4. Priority is marked as FROZEN in comments

set -e

BACKEND_DIR="${BACKEND_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../backend" && pwd)}"
ENVELOPE_FILE="${BACKEND_DIR}/app/optimization/envelope.py"

echo "Checking: $ENVELOPE_FILE"

# Check 1: ENVELOPE_CLASS_PRIORITY constant exists
if ! grep -q "ENVELOPE_CLASS_PRIORITY" "$ENVELOPE_FILE"; then
    echo "ERROR: ENVELOPE_CLASS_PRIORITY constant not found"
    exit 1
fi
echo "  ✓ ENVELOPE_CLASS_PRIORITY constant exists"

# Check 2: Marked as FROZEN
if ! grep -B5 "ENVELOPE_CLASS_PRIORITY" "$ENVELOPE_FILE" | grep -qi "FROZEN"; then
    echo "ERROR: Priority order is not marked as FROZEN"
    exit 1
fi
echo "  ✓ Priority order marked as FROZEN"

# Check 3: SAFETY has priority 1 (highest)
if ! grep -A10 "ENVELOPE_CLASS_PRIORITY" "$ENVELOPE_FILE" | grep -q "SAFETY.*1"; then
    echo "ERROR: SAFETY does not have priority 1"
    exit 1
fi
echo "  ✓ SAFETY has priority 1 (highest)"

# Check 4: PERFORMANCE has priority 4 (lowest)
if ! grep -A10 "ENVELOPE_CLASS_PRIORITY" "$ENVELOPE_FILE" | grep -q "PERFORMANCE.*4"; then
    echo "ERROR: PERFORMANCE does not have priority 4"
    exit 1
fi
echo "  ✓ PERFORMANCE has priority 4 (lowest)"

# Check 5: get_envelope_priority() helper exists
if ! grep -q "def get_envelope_priority" "$ENVELOPE_FILE"; then
    echo "ERROR: get_envelope_priority() helper not found"
    exit 1
fi
echo "  ✓ get_envelope_priority() helper exists"

# Check 6: has_higher_priority() helper exists
if ! grep -q "def has_higher_priority" "$ENVELOPE_FILE"; then
    echo "ERROR: has_higher_priority() helper not found"
    exit 1
fi
echo "  ✓ has_higher_priority() helper exists"

# Check 7: No set_priority or modify_priority functions
if grep -qE "def (set|modify|update)_priority" "$ENVELOPE_FILE"; then
    echo "ERROR: Priority modification function found (forbidden)"
    exit 1
fi
echo "  ✓ No priority modification functions"

echo "CI-C4-3: PASS"
exit 0
