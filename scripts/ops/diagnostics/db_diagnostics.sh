#!/bin/bash
#
# AOS Database Diagnostics Script
# Quick health check for PostgreSQL and approval_requests table
#
# Usage: ./db_diagnostics.sh [--json]
#

set -euo pipefail

# Database connection
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5433}"
DB_NAME="${DB_NAME:-nova_aos}"
DB_USER="${DB_USER:-nova}"
DB_PASS="${DB_PASS:-novapass}"

OUTPUT_JSON="${1:-}"

run_query() {
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$1" 2>/dev/null
}

run_query_formatted() {
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$1" 2>/dev/null
}

echo "=============================================="
echo "AOS Database Diagnostics - $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="
echo ""

# 1. Connection Stats
echo "=== Connection Statistics ==="
run_query_formatted "
SELECT
    count(*) FILTER (WHERE state = 'active') as active,
    count(*) FILTER (WHERE state = 'idle') as idle,
    count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_txn,
    count(*) FILTER (WHERE state IS NULL) as null_state,
    count(*) as total
FROM pg_stat_activity
WHERE datname = '$DB_NAME';
"

# 2. Connection Pool Usage (if using connection limits)
echo "=== Connection Limits ==="
run_query_formatted "
SELECT
    setting as max_connections,
    (SELECT count(*) FROM pg_stat_activity) as current_connections,
    setting::int - (SELECT count(*) FROM pg_stat_activity) as available
FROM pg_settings
WHERE name = 'max_connections';
"

# 3. Lock Contention
echo "=== Lock Contention (blocked queries) ==="
BLOCKED=$(run_query "SELECT count(*) FROM pg_locks WHERE NOT granted;" | tr -d ' ')
echo "Blocked queries: $BLOCKED"
if [[ "$BLOCKED" -gt 0 ]]; then
    run_query_formatted "
    SELECT
        blocked_locks.pid AS blocked_pid,
        blocked_activity.usename AS blocked_user,
        blocking_locks.pid AS blocking_pid,
        blocking_activity.usename AS blocking_user,
        blocked_activity.query AS blocked_statement
    FROM pg_catalog.pg_locks blocked_locks
    JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
    JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
        AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
        AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
        AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
        AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
        AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
        AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
        AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
        AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
        AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
        AND blocking_locks.pid != blocked_locks.pid
    JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
    WHERE NOT blocked_locks.granted
    LIMIT 5;
    "
fi
echo ""

# 4. Long Running Queries
echo "=== Long Running Queries (>5s) ==="
run_query_formatted "
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    state,
    substring(query, 1, 80) AS query_preview
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds'
  AND state != 'idle'
  AND query NOT LIKE '%pg_stat_activity%'
ORDER BY duration DESC
LIMIT 5;
"

# 5. Table Statistics
echo "=== Approval Requests Table Stats ==="
run_query_formatted "
SELECT
    relname as table_name,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    last_vacuum,
    last_autovacuum,
    last_analyze
FROM pg_stat_user_tables
WHERE relname = 'approval_requests';
"

# 6. Table Sizes
echo "=== Table Sizes ==="
run_query_formatted "
SELECT
    relname as table_name,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
    pg_size_pretty(pg_relation_size(relid)) as data_size,
    pg_size_pretty(pg_total_relation_size(relid) - pg_relation_size(relid)) as index_size
FROM pg_catalog.pg_statio_user_tables
WHERE relname IN ('approval_requests', 'archived_approval_requests', 'feature_flags', 'policy_approval_levels')
ORDER BY pg_total_relation_size(relid) DESC;
"

# 7. Index Usage
echo "=== Index Usage (approval_requests) ==="
run_query_formatted "
SELECT
    indexrelname as index_name,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE relname = 'approval_requests'
ORDER BY idx_scan DESC;
"

# 8. Approval Request Status Distribution
echo "=== Approval Request Status Distribution ==="
run_query_formatted "
SELECT
    status,
    count(*) as count,
    round(100.0 * count(*) / sum(count(*)) over(), 2) as percentage
FROM approval_requests
GROUP BY status
ORDER BY count DESC;
"

# 9. Recent Activity (last hour)
echo "=== Recent Activity (last hour) ==="
run_query_formatted "
SELECT
    date_trunc('minute', created_at) as minute,
    count(*) as requests_created
FROM approval_requests
WHERE created_at > now() - interval '1 hour'
GROUP BY date_trunc('minute', created_at)
ORDER BY minute DESC
LIMIT 10;
"

# 10. Escalation Queue
echo "=== Pending Escalations ==="
run_query_formatted "
SELECT
    count(*) as pending_count,
    min(expires_at) as earliest_expiry,
    max(expires_at) as latest_expiry
FROM approval_requests
WHERE status = 'pending'
  AND expires_at < now();
"

# 11. Webhook Delivery Stats
echo "=== Webhook Delivery Stats ==="
run_query_formatted "
SELECT
    last_webhook_status as status,
    count(*) as count,
    avg(webhook_attempts)::numeric(10,2) as avg_attempts
FROM approval_requests
WHERE webhook_url IS NOT NULL
GROUP BY last_webhook_status
ORDER BY count DESC;
"

# 12. Database Age & Transaction Wraparound Risk
echo "=== Transaction ID Wraparound Check ==="
run_query_formatted "
SELECT
    datname,
    age(datfrozenxid) as xid_age,
    current_setting('autovacuum_freeze_max_age')::int as freeze_threshold,
    CASE
        WHEN age(datfrozenxid) > current_setting('autovacuum_freeze_max_age')::int * 0.8
        THEN 'WARNING: Near freeze threshold'
        ELSE 'OK'
    END as status
FROM pg_database
WHERE datname = '$DB_NAME';
"

echo ""
echo "=============================================="
echo "Diagnostics complete"
echo "=============================================="

# JSON output option
if [[ "$OUTPUT_JSON" == "--json" ]]; then
    echo ""
    echo "=== JSON Summary ==="
    ACTIVE=$(run_query "SELECT count(*) FROM pg_stat_activity WHERE state = 'active' AND datname = '$DB_NAME';" | tr -d ' ')
    TOTAL_CONN=$(run_query "SELECT count(*) FROM pg_stat_activity WHERE datname = '$DB_NAME';" | tr -d ' ')
    APPROVAL_COUNT=$(run_query "SELECT count(*) FROM approval_requests;" | tr -d ' ')
    PENDING=$(run_query "SELECT count(*) FROM approval_requests WHERE status = 'pending';" | tr -d ' ')
    TABLE_SIZE=$(run_query "SELECT pg_total_relation_size('approval_requests');" | tr -d ' ')

    cat <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "connections": {
    "active": $ACTIVE,
    "total": $TOTAL_CONN,
    "blocked": $BLOCKED
  },
  "approval_requests": {
    "total": $APPROVAL_COUNT,
    "pending": $PENDING,
    "table_size_bytes": $TABLE_SIZE
  },
  "health": "$([ "$BLOCKED" -eq 0 ] && echo 'healthy' || echo 'degraded')"
}
EOF
fi
