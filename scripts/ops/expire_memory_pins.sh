#!/usr/bin/env bash
#
# expire_memory_pins.sh - Clean up expired memory pins
#
# Usage:
#   ./expire_memory_pins.sh                    # Use DATABASE_URL from env
#   ./expire_memory_pins.sh --dry-run          # Show what would be deleted
#   ./expire_memory_pins.sh --via-api          # Use API endpoint instead of SQL
#
# Environment:
#   DATABASE_URL - PostgreSQL connection string (for direct SQL)
#   API_BASE     - API base URL (for --via-api mode, default: http://127.0.0.1:8000)
#
# Recommended cron schedule:
#   0 * * * * /root/agenticverz2.0/scripts/ops/expire_memory_pins.sh >> /var/log/aos/expire_pins.log 2>&1
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_PREFIX="[$(date '+%Y-%m-%d %H:%M:%S')] expire_memory_pins:"

# Defaults
DRY_RUN=false
VIA_API=false
API_BASE="${API_BASE:-http://127.0.0.1:8000}"
DATABASE_URL="${DATABASE_URL:-postgresql://nova:novapass@localhost:6432/nova_aos}"

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --via-api)
            VIA_API=true
            shift
            ;;
        --api-base)
            API_BASE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "$LOG_PREFIX Starting TTL cleanup"

if [ "$VIA_API" = true ]; then
    # Use API endpoint
    echo "$LOG_PREFIX Using API endpoint: ${API_BASE}/api/v1/memory/pins/cleanup"

    if [ "$DRY_RUN" = true ]; then
        echo "$LOG_PREFIX [DRY-RUN] Would call POST ${API_BASE}/api/v1/memory/pins/cleanup"
        # Just show what would expire
        PGPASSWORD="${DATABASE_URL##*:}" psql "$DATABASE_URL" -t -c \
            "SELECT COUNT(*) FROM system.memory_pins WHERE expires_at IS NOT NULL AND expires_at < now();" 2>/dev/null || echo "0"
    else
        RESPONSE=$(curl -s -X POST "${API_BASE}/api/v1/memory/pins/cleanup" \
            -H "Content-Type: application/json")
        DELETED=$(echo "$RESPONSE" | jq -r '.deleted_count // "unknown"')
        echo "$LOG_PREFIX Deleted $DELETED expired pins via API"
    fi
else
    # Direct SQL cleanup
    if [ "$DRY_RUN" = true ]; then
        echo "$LOG_PREFIX [DRY-RUN] Would delete expired pins"
        EXPIRED_COUNT=$(PGPASSWORD="${DATABASE_URL##*:}" psql "$DATABASE_URL" -t -c \
            "SELECT COUNT(*) FROM system.memory_pins WHERE expires_at IS NOT NULL AND expires_at < now();" 2>/dev/null || echo "0")
        echo "$LOG_PREFIX Found ${EXPIRED_COUNT// /} expired pins that would be deleted"
    else
        # Delete expired pins and report count
        DELETED=$(PGPASSWORD="${DATABASE_URL##*:}" psql "$DATABASE_URL" -t -c \
            "DELETE FROM system.memory_pins WHERE expires_at IS NOT NULL AND expires_at < now() RETURNING id;" 2>/dev/null | wc -l || echo "0")
        echo "$LOG_PREFIX Deleted ${DELETED// /} expired pins via SQL"
    fi
fi

echo "$LOG_PREFIX Cleanup complete"
