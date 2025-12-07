#!/usr/bin/env bash
# ops/check_pgbouncer.sh
# Quick PgBouncer health verification script
#
# Usage:
#   ./check_pgbouncer.sh [host] [user]
#   ./check_pgbouncer.sh localhost pgbouncer
#   PGPASSWORD=xxx ./check_pgbouncer.sh

set -e

PGB_HOST="${1:-localhost}"
PGB_PORT="${2:-6432}"
PGB_USER="${3:-pgbouncer}"
PGB_DATABASE="${4:-pgbouncer}"

echo "=== PgBouncer Health Check ==="
echo "Host: $PGB_HOST:$PGB_PORT"
echo "User: $PGB_USER"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "ERROR: psql command not found"
    exit 1
fi

echo "--- SHOW STATS ---"
psql -h "$PGB_HOST" -p "$PGB_PORT" -U "$PGB_USER" -d "$PGB_DATABASE" -c "SHOW STATS;" 2>&1 || {
    echo "ERROR: Failed to get stats"
    exit 1
}

echo ""
echo "--- SHOW POOLS ---"
psql -h "$PGB_HOST" -p "$PGB_PORT" -U "$PGB_USER" -d "$PGB_DATABASE" -c "SHOW POOLS;" 2>&1 || {
    echo "ERROR: Failed to get pools"
    exit 1
}

echo ""
echo "--- SHOW DATABASES ---"
psql -h "$PGB_HOST" -p "$PGB_PORT" -U "$PGB_USER" -d "$PGB_DATABASE" -c "SHOW DATABASES;" 2>&1 || {
    echo "ERROR: Failed to get databases"
    exit 1
}

echo ""
echo "--- SHOW CLIENTS ---"
psql -h "$PGB_HOST" -p "$PGB_PORT" -U "$PGB_USER" -d "$PGB_DATABASE" -c "SHOW CLIENTS;" 2>&1 || {
    echo "ERROR: Failed to get clients"
    exit 1
}

echo ""
echo "=== PgBouncer Health Check PASSED ==="
