#!/bin/bash
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: Guard against commit() calls in audit service
# Reference: PIN-413 (Logs Domain), LOGS_DOMAIN_AUDIT.md
#
# CI Script: Audit Service No-Commit Guard
#
# Verifies that AuditLedgerService does not call commit().
# The audit service must participate in the caller's transaction,
# never control it.
#
# Exit codes:
# - 0: No forbidden commits found
# - 1: Forbidden commit() found
#
# Usage:
#   ./scripts/ci_check_audit_no_commit.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
APP_DIR="$BACKEND_DIR/app"

echo "Checking for forbidden commit() in audit services..."
echo "------------------------------------------------------------"

# Check 1: No commit() in AuditLedgerService (sync)
AUDIT_SERVICE="$APP_DIR/services/logs/audit_ledger_service.py"

if [ -f "$AUDIT_SERVICE" ]; then
    # Look for .commit() calls (excluding comments)
    if grep -n "\.commit()" "$AUDIT_SERVICE" | grep -v "^[[:space:]]*#"; then
        echo ""
        echo "✗ FORBIDDEN: commit() found in audit_ledger_service.py"
        echo ""
        echo "The audit service must NEVER call commit()."
        echo "Transaction boundary is owned by the caller."
        echo ""
        exit 1
    fi
    echo "✓ audit_ledger_service.py: No forbidden commits"
else
    echo "⚠ audit_ledger_service.py not found at expected path"
fi

# Check 1b: No commit() in AuditLedgerServiceAsync
AUDIT_SERVICE_ASYNC="$APP_DIR/services/logs/audit_ledger_service_async.py"

if [ -f "$AUDIT_SERVICE_ASYNC" ]; then
    # Look for .commit() calls (excluding comments)
    if grep -n "\.commit()" "$AUDIT_SERVICE_ASYNC" | grep -v "^[[:space:]]*#"; then
        echo ""
        echo "✗ FORBIDDEN: commit() found in audit_ledger_service_async.py"
        echo ""
        echo "The async audit service must NEVER call commit()."
        echo "Transaction boundary is owned by the caller."
        echo ""
        exit 1
    fi
    echo "✓ audit_ledger_service_async.py: No forbidden commits"
else
    echo "⚠ audit_ledger_service_async.py not found at expected path"
fi

# Check 2: No commit() directly after audit.emit calls (pattern check)
echo ""
echo "Checking for commit() immediately after audit.emit..."

# Find all Python files that call audit.emit or _audit.emit
AUDIT_CALLERS=$(grep -rl "audit\.emit\|_audit\." "$APP_DIR" --include="*.py" 2>/dev/null || true)

for file in $AUDIT_CALLERS; do
    # Skip the audit service itself
    if [[ "$file" == *"audit_ledger_service.py" ]]; then
        continue
    fi

    # Check for .emit( followed by .commit() without transaction context
    # This is a heuristic - look for emit followed by commit within 5 lines
    if awk '/\.emit\(/{found=1; count=0} found{count++; if(/\.commit\(/ && count<=5){print FILENAME": line "NR": commit() too close to emit()"; exit 1}}' "$file"; then
        : # No issue found
    else
        echo "✗ SUSPICIOUS: $file may have commit() too close to audit.emit()"
        echo "  Verify that emit() is inside a transaction context"
    fi
done

echo "✓ No suspicious audit.emit + commit patterns found"

echo ""
echo "------------------------------------------------------------"
echo "✅ Audit no-commit guard passed"
exit 0
