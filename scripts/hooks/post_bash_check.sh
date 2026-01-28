#!/bin/bash
# Layer: L8 — Catalyst / Meta
# AUDIENCE: INTERNAL
# Role: Post-bash validation hook — checks DB authority for alembic commands

# This hook runs after Bash commands containing 'alembic'
# Exit 0 always (warnings only, non-blocking)

COMMAND="$1"

if echo "$COMMAND" | grep -qi "alembic"; then
    if [ -z "$DB_AUTHORITY" ]; then
        echo "⚠ DB_AUTHORITY not set. Declare authority before running alembic."
        echo "  Reference: docs/governance/DB_AUTH_001_INVARIANT.md"
    fi
    if [ -z "$DB_ROLE" ]; then
        echo "⚠ DB_ROLE not set. Declare role (staging|prod) before migrations."
        echo "  Reference: docs/memory-pins/PIN-462-db-role-migration-governance.md"
    fi
fi

exit 0
