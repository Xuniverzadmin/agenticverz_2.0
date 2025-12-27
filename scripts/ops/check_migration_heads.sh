#!/bin/bash
# check_migration_heads.sh - CI/Pre-commit check for migration fork prevention
#
# ENFORCEMENT: This script MUST be run before creating any new migration.
# RULE: BL-MIG-002 - Single migration head required
#
# Exit codes:
#   0 - Single head (OK)
#   1 - Multiple heads detected (BLOCKED)
#   2 - Error running alembic

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/../../backend"

cd "$BACKEND_DIR"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    # Try to source .env
    if [ -f "../.env" ]; then
        set -a
        source "../.env"
        set +a
    fi
fi

# Get heads
HEADS=$(alembic heads 2>/dev/null | grep -v "^INFO" | grep -v "^$" || echo "ERROR")

if [ "$HEADS" = "ERROR" ]; then
    echo "❌ ERROR: Could not run 'alembic heads'"
    exit 2
fi

# Count heads
HEAD_COUNT=$(echo "$HEADS" | wc -l)

if [ "$HEAD_COUNT" -gt 1 ]; then
    echo "❌ BL-MIG-002 VIOLATION: Multiple migration heads detected!"
    echo ""
    echo "Current heads:"
    echo "$HEADS" | sed 's/^/  - /'
    echo ""
    echo "REQUIRED ACTION:"
    echo "  1. Create a merge migration: alembic merge heads -m 'merge_description'"
    echo "  2. Apply the merge: alembic upgrade head"
    echo "  3. Verify single head: alembic heads"
    echo ""
    echo "PREVENTION:"
    echo "  - Always run 'alembic heads' before creating new migrations"
    echo "  - Never skip revisions in down_revision"
    echo "  - Use merge migrations when features branch"
    exit 1
fi

echo "✅ Single migration head: $HEADS"
exit 0
