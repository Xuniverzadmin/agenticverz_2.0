#!/bin/bash
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: ci
#   Execution: sync
# Role: CI guard for forbidden dispatcher=None pattern
# Callers: CI pipeline
# Allowed Imports: None (shell script)
# Forbidden Imports: None
# Reference: CROSS_DOMAIN_GOVERNANCE.md

# =============================================================================
# CI Guard: dispatcher=None Pattern Detection
# =============================================================================
#
# DOCTRINE (from CROSS_DOMAIN_GOVERNANCE.md):
#   Rule 2: No Optional Dependencies
#   - Governance code cannot depend on optional services
#   - dispatcher=None patterns are forbidden
#
# This script fails the build if `dispatcher=None` appears in production code
# (app/ directory), excluding docstrings and comments that explain the rule.
#
# Exit codes:
#   0 - No violations found
#   1 - Violations found (fails CI)
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
APP_DIR="$BACKEND_DIR/app"

echo "================================================================="
echo "CI Guard: dispatcher=None Pattern Detection"
echo "================================================================="
echo ""
echo "DOCTRINE: Governance code cannot depend on optional services."
echo "          dispatcher=None patterns are forbidden."
echo ""
echo "Scanning: $APP_DIR"
echo ""

# Search for dispatcher=None in Python files
# Exclude:
#   - Lines that are pure comments (start with #)
#   - The governance.py file which explains the rule
#   - Test files (in tests/ directory)
VIOLATIONS=$(grep -rn "dispatcher=None" "$APP_DIR" --include="*.py" 2>/dev/null | \
    grep -v "^[^:]*:[^:]*:#" | \
    grep -v "governance.py" || true)

if [ -z "$VIOLATIONS" ]; then
    echo "PASS: No dispatcher=None violations found."
    echo ""
    echo "All governance code properly requires dependencies."
    exit 0
else
    echo "FAIL: dispatcher=None violations detected!"
    echo ""
    echo "The following files contain forbidden dispatcher=None patterns:"
    echo "-----------------------------------------------------------------"
    echo "$VIOLATIONS"
    echo "-----------------------------------------------------------------"
    echo ""
    echo "DOCTRINE VIOLATION (CROSS_DOMAIN_GOVERNANCE.md Rule 2):"
    echo "  Governance operations are MANDATORY."
    echo "  They must succeed or raise GovernanceError."
    echo "  Optional dispatchers are forbidden."
    echo ""
    echo "FIX: Replace dispatcher=None with required db_session parameter"
    echo "     and use mandatory governance functions from:"
    echo "       app/services/governance/cross_domain.py"
    echo ""
    exit 1
fi
