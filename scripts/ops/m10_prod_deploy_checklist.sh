#!/bin/bash
# M10 Production Deploy Checklist
# Run this script with owner present before production deploy

set -e

echo "=========================================="
echo "M10 Production Deploy Checklist"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓ PASS${NC}: $1"; }
fail() { echo -e "${RED}✗ FAIL${NC}: $1"; exit 1; }
warn() { echo -e "${YELLOW}⚠ WARN${NC}: $1"; }

# 1. Backup verification
echo "--- Step 1: Backup Verification ---"
DATE=$(date +%Y-%m-%d_%H%M)
BACKUP_FILE="/backups/pre_migration_${DATE}.dump"

if [ -n "$SKIP_BACKUP" ]; then
    warn "Skipping backup (SKIP_BACKUP set)"
else
    echo "Creating backup: $BACKUP_FILE"
    PGPASSWORD=novapass pg_dump -h localhost -p 5433 -U nova -d nova_aos \
      -Fc -f "$BACKUP_FILE" 2>/dev/null

    if [ -f "$BACKUP_FILE" ]; then
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        sha256sum "$BACKUP_FILE" > "${BACKUP_FILE}.sha256"
        pass "Backup created: $BACKUP_FILE ($SIZE)"
    else
        fail "Backup failed"
    fi
fi
echo ""

# 2. Metrics collector status
echo "--- Step 2: Metrics Collector Status ---"
if systemctl is-active --quiet m10-metrics-collector.service 2>/dev/null; then
    pass "Metrics collector running"
else
    warn "Metrics collector not running - starting..."
    sudo systemctl start m10-metrics-collector.service 2>/dev/null || warn "Could not start (may need manual intervention)"
fi
echo ""

# 3. Timers status
echo "--- Step 3: Timer Status ---"
for timer in m10-maintenance m10-synthetic-traffic m10-daily-stats; do
    if systemctl is-active --quiet ${timer}.timer 2>/dev/null; then
        pass "${timer}.timer active"
    else
        warn "${timer}.timer not active"
    fi
done
echo ""

# 4. Alert silence test
echo "--- Step 4: Alert Silence Test ---"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"

SILENCE_RESPONSE=$(curl -s -X POST "${ALERTMANAGER_URL}/api/v2/silences" \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {"name": "alertname", "value": "M10TestSilence", "isRegex": false}
    ],
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "endsAt": "'$(date -u -d "+1 minute" +%Y-%m-%dT%H:%M:%S.000Z)'",
    "createdBy": "deploy-script",
    "comment": "Test silence for deploy verification"
  }' 2>/dev/null)

SILENCE_ID=$(echo "$SILENCE_RESPONSE" | jq -r '.silenceID' 2>/dev/null)

if [ -n "$SILENCE_ID" ] && [ "$SILENCE_ID" != "null" ]; then
    pass "Silence created: $SILENCE_ID"
    # Clean up
    curl -s -X DELETE "${ALERTMANAGER_URL}/api/v2/silence/$SILENCE_ID" >/dev/null 2>&1
    pass "Silence removed"
else
    warn "Could not create silence (Alertmanager may be unreachable)"
fi
echo ""

# 5. Database connectivity
echo "--- Step 5: Database Connectivity ---"
TABLE_COUNT=$(PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -t -c \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'm10_recovery';" 2>/dev/null | tr -d ' ')

if [ "$TABLE_COUNT" -ge 10 ]; then
    pass "M10 schema has $TABLE_COUNT tables"
else
    warn "M10 schema has only $TABLE_COUNT tables (expected >=10)"
fi
echo ""

# 6. Redis connectivity
echo "--- Step 6: Redis Connectivity ---"
REDIS_PING=$(redis-cli PING 2>/dev/null)
if [ "$REDIS_PING" = "PONG" ]; then
    pass "Redis responding"
    AOF=$(redis-cli CONFIG GET appendonly 2>/dev/null | tail -1)
    if [ "$AOF" = "yes" ]; then
        pass "Redis AOF enabled"
    else
        warn "Redis AOF not enabled (data durability risk)"
    fi
else
    warn "Redis not responding"
fi
echo ""

# 7. Dead letter check
echo "--- Step 7: Dead Letter Check ---"
DL_COUNT=$(PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -t -c \
  "SELECT COUNT(*) FROM m10_recovery.dead_letter_archive;" 2>/dev/null | tr -d ' ')

if [ "$DL_COUNT" -eq 0 ]; then
    pass "No dead letters"
elif [ "$DL_COUNT" -lt 10 ]; then
    warn "Dead letters: $DL_COUNT (review with aos-dl top)"
else
    fail "Dead letters: $DL_COUNT (investigate before deploy)"
fi
echo ""

# Summary
echo "=========================================="
echo "Checklist Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Assign deploy owner in PR"
echo "2. Create Slack pager entry"
echo "3. Run: alembic upgrade head"
echo "4. Monitor for 48h"
echo ""
echo "Backup location: $BACKUP_FILE"
echo ""
