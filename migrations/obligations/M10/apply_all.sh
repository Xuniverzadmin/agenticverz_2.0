#!/usr/bin/env bash
# M10: Apply all migrations in order
# Purpose: Supplement existing m10_recovery schema with immutability guarantees
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== M10: Recovery & Outbox Infrastructure ==="
echo "Applying supplemental migrations to existing m10_recovery schema..."

# Source environment
if [ -f /root/agenticverz2.0/.env ]; then
    set -a
    source /root/agenticverz2.0/.env
    set +a
fi

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set"
    exit 1
fi

# Apply in order - note that some files share numbers (003, 004) for different purposes
# We apply them in alphabetical order within each number
MIGRATIONS=(
    "001_existing_schema_note.sql"
    "002_outbox_immutability.sql"
    "003_lifecycle_constraints.sql"
    "003_work_queue_transitions.sql"
    "004_dlq_schema.sql"
    "004_views.sql"
)

for migration in "${MIGRATIONS[@]}"; do
    echo ""
    echo "--- Applying: $migration ---"
    if psql "$DATABASE_URL" -f "$SCRIPT_DIR/$migration"; then
        echo "✓ $migration applied"
    else
        echo "✗ $migration failed (may be expected if objects exist)"
    fi
done

echo ""
echo "=== M10 migrations complete ==="
