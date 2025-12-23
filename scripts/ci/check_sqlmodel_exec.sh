#!/bin/bash
# =============================================================================
# M26 Prevention Mechanism #1: Raw SQL Misuse Guard
# =============================================================================
#
# INVARIANT: session.exec() may ONLY be used with ORM queries (select, insert)
#            session.execute() MUST be used with text() raw SQL
#
# This catches the error BEFORE deploy, not at runtime.
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "======================================"
echo "M26 SQL Misuse Guard"
echo "======================================"

BACKEND_DIR="${1:-/root/agenticverz2.0/backend}"
FAILED=0

# Direct pattern search: session.exec followed by text( within 3 lines
# This catches the dangerous pattern
violations=$(grep -rn "\.exec(" "$BACKEND_DIR/app" --include="*.py" 2>/dev/null | while read line; do
    file=$(echo "$line" | cut -d: -f1)
    linenum=$(echo "$line" | cut -d: -f2)

    # Skip if it's session.execute (the correct form)
    if echo "$line" | grep -q "\.execute("; then
        continue
    fi

    # Check if text( appears in the next 5 lines
    end=$((linenum + 5))
    context=$(sed -n "${linenum},${end}p" "$file" 2>/dev/null)

    if echo "$context" | grep -q "text("; then
        echo "$file:$linenum"
    fi
done)

if [[ -n "$violations" ]]; then
    echo -e "${RED}FAIL: session.exec() used with text() detected${NC}"
    echo -e "${RED}Violations:${NC}"
    echo "$violations" | while read v; do
        echo "  - $v"
    done
    echo ""
    echo "FIX: Change session.exec(text(...), params) to session.execute(text(...), params)"
    exit 1
else
    echo -e "${GREEN}PASS: No session.exec(text()) misuse detected${NC}"
fi

echo ""
echo -e "${GREEN}======================================"
echo "SQL Misuse Guard: COMPLETE"
echo "======================================${NC}"
