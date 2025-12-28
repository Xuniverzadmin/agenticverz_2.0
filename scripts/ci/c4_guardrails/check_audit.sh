#!/usr/bin/env bash
# CI-C4-6: Coordination audit is emitted
# Reference: C4_CI_GUARDRAILS_DESIGN.md Section 2.6
#
# Checks:
# 1. CoordinationAuditRecord class exists
# 2. _emit_audit_record() method exists
# 3. Every decision path emits an audit record
# 4. Audit trail is queryable

set -e

BACKEND_DIR="${BACKEND_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../backend" && pwd)}"
COORDINATOR_FILE="${BACKEND_DIR}/app/optimization/coordinator.py"
ENVELOPE_FILE="${BACKEND_DIR}/app/optimization/envelope.py"

echo "Checking: $COORDINATOR_FILE and $ENVELOPE_FILE"

# Check 1: CoordinationAuditRecord class exists
if ! grep -q "class CoordinationAuditRecord" "$ENVELOPE_FILE"; then
    echo "ERROR: CoordinationAuditRecord class not found"
    exit 1
fi
echo "  ✓ CoordinationAuditRecord class exists"

# Check 2: CoordinationAuditRecord has required fields
for field in "audit_id" "envelope_id" "envelope_class" "decision" "reason" "timestamp"; do
    if ! grep -A20 "class CoordinationAuditRecord" "$ENVELOPE_FILE" | grep -q "$field"; then
        echo "ERROR: CoordinationAuditRecord missing field: $field"
        exit 1
    fi
done
echo "  ✓ CoordinationAuditRecord has required fields"

# Check 3: _emit_audit_record() method exists
if ! grep -q "def _emit_audit_record" "$COORDINATOR_FILE"; then
    echo "ERROR: _emit_audit_record() method not found"
    exit 1
fi
echo "  ✓ _emit_audit_record() method exists"

# Check 4: _audit_trail storage exists
if ! grep -q "_audit_trail" "$COORDINATOR_FILE"; then
    echo "ERROR: _audit_trail storage not found"
    exit 1
fi
echo "  ✓ _audit_trail storage exists"

# Check 5: get_audit_trail() method exists
if ! grep -q "def get_audit_trail" "$COORDINATOR_FILE"; then
    echo "ERROR: get_audit_trail() method not found"
    exit 1
fi
echo "  ✓ get_audit_trail() method exists"

# Check 6: check_allowed() emits audit
if ! grep -A60 "def check_allowed" "$COORDINATOR_FILE" | grep -q "_emit_audit_record"; then
    echo "ERROR: check_allowed() does not emit audit record"
    exit 1
fi
echo "  ✓ check_allowed() emits audit record"

# Check 7: apply() emits audit
if ! grep -A60 "def apply" "$COORDINATOR_FILE" | grep -q "_emit_audit_record"; then
    echo "ERROR: apply() does not emit audit record"
    exit 1
fi
echo "  ✓ apply() emits audit record"

# Check 8: I-C4-7 invariant referenced
if ! grep -q "I-C4-7" "$COORDINATOR_FILE"; then
    echo "ERROR: I-C4-7 invariant not referenced"
    exit 1
fi
echo "  ✓ I-C4-7 invariant referenced"

echo "CI-C4-6: PASS"
exit 0
