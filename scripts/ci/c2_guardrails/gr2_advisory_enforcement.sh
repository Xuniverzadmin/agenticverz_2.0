#!/bin/bash
# =============================================================================
# GR-2: Advisory Enforcement (BLOCKER)
# =============================================================================
# Rule: All predictions must have advisory = TRUE. The CHECK constraint
#       must exist and never be weakened.
#
# Reference: PIN-222, I-C2-1
# Enforcement: BLOCKER - CI fails if constraint missing or weakened
# =============================================================================

set -e

BACKEND_DIR="${1:-/root/agenticverz2.0/backend}"
MIGRATIONS_DIR="$BACKEND_DIR/alembic/versions"

echo "GR-2: Checking advisory enforcement..."
echo "======================================"

VIOLATIONS=0

# Check 1: The hardening migration must exist with the constraint
if ! grep -l "chk_prediction_advisory" "$MIGRATIONS_DIR"/*.py >/dev/null 2>&1; then
    echo "VIOLATION: chk_prediction_advisory constraint not found in migrations"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# Check 2: No code should set is_advisory=False or advisory=False
if grep -rE "(is_advisory\s*=\s*False|advisory\s*=\s*False)" "$BACKEND_DIR/app" 2>/dev/null; then
    echo "VIOLATION: Code found that sets advisory to False"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# Check 3: No migration should drop the advisory constraint outside downgrade()
# Strategy: For each migration file, check if drop appears in upgrade() section
for migration in "$MIGRATIONS_DIR"/*.py; do
    if grep -q "drop.*chk_prediction_advisory" "$migration" 2>/dev/null; then
        # Check if drop appears BEFORE "def downgrade" (meaning it's in upgrade)
        # Use awk: print lines from start until "def downgrade", then grep for drop
        if awk '/^def upgrade/,/^def downgrade/' "$migration" 2>/dev/null | grep -q "drop.*chk_prediction_advisory"; then
            echo "VIOLATION: Migration $migration drops advisory constraint in upgrade()"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    fi
done

if [ $VIOLATIONS -gt 0 ]; then
    echo ""
    echo "GR-2 FAILED: $VIOLATIONS violation(s) detected"
    echo "Advisory constraint must be enforced (I-C2-1)."
    exit 1
fi

echo "GR-2 PASSED: Advisory constraint is properly enforced"
exit 0
