#!/usr/bin/env bash
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Convenience wrapper for shadow_validate_v2.py
# Reference: ACTIVITY_DOMAIN_V2_MIGRATION_PLAN.md (Phase 3)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment if available
if [ -f "/root/agenticverz2.0/.env" ]; then
    set -a
    source /root/agenticverz2.0/.env
    set +a
fi

# Validate required environment
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is required."
    echo "Set it or source your .env file first."
    exit 1
fi

# Get tenant ID - use argument or default
TENANT_ID="${1:-demo-tenant}"

echo "Running Activity Domain V2 Shadow Validation"
echo "============================================="
echo "Database: ${DATABASE_URL:0:30}..."
echo "Tenant: $TENANT_ID"
echo ""

# Run the validation
python3 "$SCRIPT_DIR/shadow_validate_v2.py" \
    --database-url "$DATABASE_URL" \
    --tenant-id "$TENANT_ID" \
    "${@:2}"

exit $?
