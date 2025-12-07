#!/bin/bash
# scripts/ops/trace_retention_cron.sh
# Run trace retention (archive old traces, delete very old ones)
# Scheduled via system cron at 04:00 UTC daily

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="/var/log/aos/trace_retention.log"
LOCK_FILE="/var/run/aos_trace_retention.lock"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Prevent concurrent runs
if [ -f "$LOCK_FILE" ]; then
    echo "$(date -Iseconds) [WARN] Lock file exists, skipping run" >> "$LOG_FILE"
    exit 0
fi
trap "rm -f $LOCK_FILE" EXIT
touch "$LOCK_FILE"

log() {
    echo "$(date -Iseconds) $1" >> "$LOG_FILE"
}

log "[INFO] Starting trace retention job"

# Load environment
if [ -f /root/agenticverz2.0/.env ]; then
    set -a
    source /root/agenticverz2.0/.env
    set +a
fi

# Database connection
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-6432}"
DB_USER="${DB_USER:-nova}"
DB_NAME="${DB_NAME:-nova_aos}"
DB_PASSWORD="${PGPASSWORD:-novapass}"

# Run retention function
export PGPASSWORD="$DB_PASSWORD"
result=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT aos_run_trace_retention_with_log();" 2>&1)

if [ $? -eq 0 ]; then
    log "[INFO] Retention completed successfully"

    # Get latest log entry
    stats=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
        "SELECT archived_count, deleted_count, duration_ms FROM aos_traces_retention_log ORDER BY run_at DESC LIMIT 1;" 2>&1)
    log "[INFO] Stats: $stats"
else
    log "[ERROR] Retention failed: $result"
    exit 1
fi

log "[INFO] Trace retention job complete"
