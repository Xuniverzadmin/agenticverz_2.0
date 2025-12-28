#!/bin/bash
# CI-C4-9: Audit Replay Safety Check
# Reference: C4_COORDINATION_AUDIT_SCHEMA.md Section 7
#
# Ensures emit_traces is checked before audit emission
# Replay mode must not create duplicate audit records

set -e

BACKEND_DIR="${BACKEND_DIR:-backend}"
AUDIT_FILE="$BACKEND_DIR/app/optimization/audit_persistence.py"

echo "🔍 CI-C4-9: Checking audit replay safety..."

if [ ! -f "$AUDIT_FILE" ]; then
    echo "❌ CI-C4-9 FAILED: audit_persistence.py not found at $AUDIT_FILE"
    exit 1
fi

# Check for emit_traces parameter in persist function
EMIT_TRACES_PARAM=$(grep -n "emit_traces.*bool" "$AUDIT_FILE" || true)

if [ -z "$EMIT_TRACES_PARAM" ]; then
    echo "❌ CI-C4-9 FAILED: emit_traces parameter not found in audit_persistence.py"
    echo ""
    echo "The persist_audit_record function MUST accept an emit_traces parameter"
    echo "to support replay mode."
    exit 1
fi

# Check for emit_traces guard in persist function
EMIT_TRACES_CHECK=$(grep -n "if not emit_traces" "$AUDIT_FILE" || true)

if [ -z "$EMIT_TRACES_CHECK" ]; then
    echo "❌ CI-C4-9 FAILED: emit_traces guard not found in audit_persistence.py"
    echo ""
    echo "The persist_audit_record function MUST check emit_traces before persisting."
    echo "Expected: 'if not emit_traces: return'"
    exit 1
fi

# Check coordinator passes emit_traces to persist function
COORDINATOR_FILE="$BACKEND_DIR/app/optimization/coordinator.py"

if [ -f "$COORDINATOR_FILE" ]; then
    COORD_EMIT_TRACES=$(grep -n "emit_traces" "$COORDINATOR_FILE" || true)

    if [ -z "$COORD_EMIT_TRACES" ]; then
        echo "⚠️  Warning: emit_traces not found in coordinator.py"
        echo "The CoordinationManager should accept emit_traces for replay mode."
    fi
fi

echo "✅ CI-C4-9 PASSED: Audit replay safety verified"
echo ""
echo "emit_traces parameter found at:"
echo "$EMIT_TRACES_PARAM"
echo ""
echo "emit_traces guard found at:"
echo "$EMIT_TRACES_CHECK"
