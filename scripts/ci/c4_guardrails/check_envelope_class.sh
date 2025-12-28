#!/usr/bin/env bash
# CI-C4-1: Every envelope declares exactly one class
# Reference: C4_CI_GUARDRAILS_DESIGN.md Section 2.1
#
# Checks:
# 1. EnvelopeClass enum exists with exactly 4 values
# 2. Envelope dataclass has envelope_class field
# 3. validate_envelope() checks for envelope_class

set -e

BACKEND_DIR="${BACKEND_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../backend" && pwd)}"
ENVELOPE_FILE="${BACKEND_DIR}/app/optimization/envelope.py"

echo "Checking: $ENVELOPE_FILE"

# Check 1: EnvelopeClass enum exists
if ! grep -q "class EnvelopeClass" "$ENVELOPE_FILE"; then
    echo "ERROR: EnvelopeClass enum not found"
    exit 1
fi
echo "  ✓ EnvelopeClass enum exists"

# Check 2: Four envelope classes defined
CLASSES=$(grep -E "^\s+(SAFETY|RELIABILITY|COST|PERFORMANCE)\s*=" "$ENVELOPE_FILE" | wc -l)
if [ "$CLASSES" -ne 4 ]; then
    echo "ERROR: Expected 4 envelope classes, found $CLASSES"
    exit 1
fi
echo "  ✓ Four envelope classes defined (SAFETY, RELIABILITY, COST, PERFORMANCE)"

# Check 3: envelope_class field in Envelope dataclass
if ! grep -q "envelope_class.*EnvelopeClass" "$ENVELOPE_FILE"; then
    echo "ERROR: envelope_class field not found in Envelope dataclass"
    exit 1
fi
echo "  ✓ envelope_class field exists in Envelope"

# Check 4: CI-C4-1 validation in validate_envelope
if ! grep -q "CI-C4-1" "$ENVELOPE_FILE"; then
    echo "ERROR: CI-C4-1 validation not found in validate_envelope()"
    exit 1
fi
echo "  ✓ CI-C4-1 validation present"

# Check 5: Validation rejects None envelope_class
if ! grep -A5 "CI-C4-1" "$ENVELOPE_FILE" | grep -q "envelope.envelope_class is None"; then
    echo "ERROR: validate_envelope() does not check for None envelope_class"
    exit 1
fi
echo "  ✓ Validation rejects None envelope_class"

echo "CI-C4-1: PASS"
exit 0
