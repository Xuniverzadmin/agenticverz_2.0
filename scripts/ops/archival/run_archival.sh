#!/bin/bash
#
# AOS Approval Request Archival Job
# Archives resolved approval requests older than retention period
#
# Usage: ./run_archival.sh [options]
#        --dry-run        Preview what would be archived (no changes)
#        --limit N        Limit archival to N records (default: unlimited)
#        --retention N    Override retention days (default: 90)
#        --vacuum         Run VACUUM ANALYZE after archival
#
# Cron example (daily at 3 AM):
#   0 3 * * * /root/agenticverz2.0/scripts/ops/archival/run_archival.sh >> /var/log/aos/archival.log 2>&1
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${LOG_FILE:-/var/log/aos/archival.log}"

# Defaults
DRY_RUN=false
LIMIT=""
RETENTION_DAYS=90
VACUUM_AFTER=false

# Database connection
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5433}"
DB_NAME="${DB_NAME:-nova_aos}"
DB_USER="${DB_USER:-nova}"
DB_PASS="${DB_PASS:-novapass}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        --retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --vacuum)
            VACUUM_AFTER=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --dry-run        Preview what would be archived (no changes)"
            echo "  --limit N        Limit archival to N records"
            echo "  --retention N    Override retention days (default: 90)"
            echo "  --vacuum         Run VACUUM ANALYZE after archival"
            echo ""
            echo "Environment variables:"
            echo "  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS"
            echo "  PUSHGATEWAY_URL  (optional: push metrics)"
            exit 0
            ;;
        *)
            # Legacy: first positional arg is retention days
            if [[ "$1" =~ ^[0-9]+$ ]]; then
                RETENTION_DAYS="$1"
            else
                echo "Unknown argument: $1"
                exit 2
            fi
            shift
            ;;
    esac
done

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

run_sql() {
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$1" 2>/dev/null | tr -d ' \n'
}

run_sql_formatted() {
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$1" 2>/dev/null
}

log "=== Starting archival job ==="
log "Retention period: ${RETENTION_DAYS} days"
log "Dry run: ${DRY_RUN}"
if [[ -n "$LIMIT" ]]; then
    log "Limit: ${LIMIT} records"
fi

# Build WHERE clause
WHERE_CLAUSE="status IN ('approved', 'rejected', 'expired') AND resolved_at < NOW() - INTERVAL '${RETENTION_DAYS} days'"

# Get pre-archival stats
PRE_COUNT=$(run_sql "SELECT COUNT(*) FROM approval_requests WHERE ${WHERE_CLAUSE};")

log "Records eligible for archival: ${PRE_COUNT:-0}"

if [[ "${PRE_COUNT:-0}" -eq 0 ]]; then
    log "No records to archive. Exiting."
    exit 0
fi

# DRY RUN MODE
if [[ "$DRY_RUN" == "true" ]]; then
    log "=== DRY RUN MODE - NO CHANGES WILL BE MADE ==="
    log ""
    log "Records that WOULD be archived:"

    LIMIT_CLAUSE=""
    if [[ -n "$LIMIT" ]]; then
        LIMIT_CLAUSE="LIMIT ${LIMIT}"
    fi

    # Show sample records
    run_sql_formatted "
SELECT id, tenant_id, status, resolved_at, created_at
FROM approval_requests
WHERE ${WHERE_CLAUSE}
ORDER BY resolved_at ASC
${LIMIT_CLAUSE:-LIMIT 20};
"

    log ""
    log "Summary:"
    log "  Total eligible: ${PRE_COUNT}"
    if [[ -n "$LIMIT" ]]; then
        WOULD_ARCHIVE=$((PRE_COUNT < LIMIT ? PRE_COUNT : LIMIT))
        log "  Would archive: ${WOULD_ARCHIVE} (limited)"
    else
        log "  Would archive: ${PRE_COUNT}"
    fi

    # Show by status breakdown
    log ""
    log "By status:"
    run_sql_formatted "
SELECT status, COUNT(*) as count
FROM approval_requests
WHERE ${WHERE_CLAUSE}
GROUP BY status
ORDER BY count DESC;
"

    # Show by tenant breakdown
    log ""
    log "By tenant (top 10):"
    run_sql_formatted "
SELECT tenant_id, COUNT(*) as count
FROM approval_requests
WHERE ${WHERE_CLAUSE}
GROUP BY tenant_id
ORDER BY count DESC
LIMIT 10;
"

    log ""
    log "=== DRY RUN COMPLETE - No changes made ==="
    exit 0
fi

# REAL ARCHIVAL
log "Running archival..."

# Build limit clause
LIMIT_CLAUSE=""
if [[ -n "$LIMIT" ]]; then
    LIMIT_CLAUSE="LIMIT ${LIMIT}"
fi

# Check if archive_old_approval_requests function exists
FUNC_EXISTS=$(run_sql "SELECT EXISTS(SELECT 1 FROM pg_proc WHERE proname = 'archive_old_approval_requests');")

if [[ "$FUNC_EXISTS" == "t" ]]; then
    # Use the stored function
    ARCHIVED=$(run_sql "SELECT archive_old_approval_requests(${RETENTION_DAYS});")
    log "Archived ${ARCHIVED:-0} records (via stored function)"
else
    # Manual archival with transaction
    log "Using manual archival (stored function not found)"

    ARCHIVED=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
BEGIN;

-- Count before
SELECT COUNT(*) FROM approval_requests WHERE ${WHERE_CLAUSE};

-- Insert into archive
INSERT INTO archived_approval_requests
    (id, policy_type, skill_id, tenant_id, agent_id, requested_by, justification,
     required_level, current_level, status, expires_at, resolved_at,
     payload_json, approvers_json, status_history_json, webhook_url,
     webhook_secret_hash, webhook_attempts, last_webhook_status,
     correlation_id, escalate_to, created_at, updated_at, archived_at)
SELECT
    id, policy_type, skill_id, tenant_id, agent_id, requested_by, justification,
    required_level, current_level, status, expires_at, resolved_at,
    payload_json, approvers_json, status_history_json, webhook_url,
    webhook_secret_hash, webhook_attempts, last_webhook_status,
    correlation_id, escalate_to, created_at, updated_at, NOW()
FROM approval_requests
WHERE ${WHERE_CLAUSE}
ORDER BY resolved_at ASC
${LIMIT_CLAUSE};

-- Delete from main table
DELETE FROM approval_requests
WHERE id IN (
    SELECT id FROM approval_requests
    WHERE ${WHERE_CLAUSE}
    ORDER BY resolved_at ASC
    ${LIMIT_CLAUSE}
);

COMMIT;
" 2>/dev/null | head -1 | tr -d ' ')

    log "Archived ${ARCHIVED:-0} records (manual)"
fi

# Verify
REMAINING=$(run_sql "SELECT COUNT(*) FROM approval_requests WHERE ${WHERE_CLAUSE};")
ARCHIVE_TOTAL=$(run_sql "SELECT COUNT(*) FROM archived_approval_requests;")

log "Remaining in main table: ${REMAINING:-0}"
log "Total in archive table: ${ARCHIVE_TOTAL:-0}"

# Get table sizes
MAIN_SIZE=$(run_sql "SELECT pg_size_pretty(pg_total_relation_size('approval_requests'));")
ARCHIVE_SIZE=$(run_sql "SELECT pg_size_pretty(pg_total_relation_size('archived_approval_requests'));" 2>/dev/null || echo "N/A")

log "Main table size: ${MAIN_SIZE}"
log "Archive table size: ${ARCHIVE_SIZE}"

# Optional: VACUUM after archival
if [[ "$VACUUM_AFTER" == "true" ]]; then
    log "Running VACUUM ANALYZE on approval_requests..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
        "VACUUM ANALYZE approval_requests;" 2>/dev/null
    log "VACUUM complete"
fi

log "=== Archival job complete ==="

# Send metric to Prometheus (if pushgateway available)
if [[ -n "${PUSHGATEWAY_URL:-}" ]]; then
    cat <<EOF | curl -s --data-binary @- "${PUSHGATEWAY_URL}/metrics/job/aos_archival"
# HELP aos_archival_records_total Total records archived
# TYPE aos_archival_records_total gauge
aos_archival_records_total ${ARCHIVED:-0}
# HELP aos_archival_last_run_timestamp Unix timestamp of last archival run
# TYPE aos_archival_last_run_timestamp gauge
aos_archival_last_run_timestamp $(date +%s)
# HELP aos_archival_remaining_eligible Remaining eligible records after archival
# TYPE aos_archival_remaining_eligible gauge
aos_archival_remaining_eligible ${REMAINING:-0}
EOF
    log "Pushed metrics to Prometheus Pushgateway"
fi

exit 0
