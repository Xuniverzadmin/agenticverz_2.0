#!/usr/bin/env bash
# NOVA Agent Manager - PostgreSQL Backup Script
# Runs daily via cron, keeps last 14 backups
set -euo pipefail

BACKUP_DIR=/opt/agenticverz/backups
PROJECT_DIR=/root/agenticverz2.0
mkdir -p "$BACKUP_DIR"

TS=$(date -u +"%Y%m%dT%H%M%SZ")
BACKUP_FILE="$BACKUP_DIR/nova_aos_${TS}.sql.gz"

echo "[$(date -Iseconds)] Starting backup..."

# Get container ID and run pg_dump
cd "$PROJECT_DIR"
docker compose exec -T db pg_dump -U nova nova_aos | gzip > "$BACKUP_FILE"

# Verify backup size
SIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || echo "0")
if [ "$SIZE" -lt 100 ]; then
    echo "[$(date -Iseconds)] ERROR: Backup file too small ($SIZE bytes), likely failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi

echo "[$(date -Iseconds)] Backup completed: $BACKUP_FILE ($SIZE bytes)"

# Keep only last 14 backups
cd "$BACKUP_DIR"
ls -1t nova_aos_*.sql.gz 2>/dev/null | tail -n +15 | xargs -r rm -f

# List current backups
echo "[$(date -Iseconds)] Current backups:"
ls -lh "$BACKUP_DIR"/nova_aos_*.sql.gz 2>/dev/null || echo "  (none)"
