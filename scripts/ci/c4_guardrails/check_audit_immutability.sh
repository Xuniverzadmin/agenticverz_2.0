#!/bin/bash
# CI-C4-7: Audit Immutability Check
# Reference: C4_COORDINATION_AUDIT_SCHEMA.md Section 10
#
# Ensures no UPDATE statements on coordination_audit_records
# Audit records are append-only and immutable

set -e

BACKEND_DIR="${BACKEND_DIR:-backend}"

echo "🔍 CI-C4-7: Checking audit immutability..."

# Check for UPDATE on coordination_audit_records
UPDATE_MATCHES=$(grep -rn "UPDATE.*coordination_audit_records\|\.update.*coordination_audit" "$BACKEND_DIR/app" 2>/dev/null | grep -v "__pycache__\|\.pyc" || true)

if [ -n "$UPDATE_MATCHES" ]; then
    echo "❌ CI-C4-7 FAILED: Found UPDATE on coordination_audit_records"
    echo ""
    echo "Matches found:"
    echo "$UPDATE_MATCHES"
    echo ""
    echo "Coordination audit records are IMMUTABLE."
    echo "Updates are forbidden by design."
    exit 1
fi

# Check for DELETE on coordination_audit_records (except in tests)
DELETE_MATCHES=$(grep -rn "DELETE.*coordination_audit_records\|\.delete.*coordination_audit" "$BACKEND_DIR/app" 2>/dev/null | grep -v "__pycache__\|\.pyc\|tests/" || true)

if [ -n "$DELETE_MATCHES" ]; then
    echo "❌ CI-C4-7 FAILED: Found DELETE on coordination_audit_records"
    echo ""
    echo "Matches found:"
    echo "$DELETE_MATCHES"
    echo ""
    echo "Coordination audit records must not be deleted in production code."
    exit 1
fi

echo "✅ CI-C4-7 PASSED: No audit mutation detected"
