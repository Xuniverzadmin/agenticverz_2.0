# M10 Migration 022 Runbook - Production Hardening

**Migration**: `022_m10_production_hardening`
**Purpose**: Add leader election, replay log, DL archive, and outbox tables
**Risk Level**: MEDIUM (adds tables/functions, no data migration)
**Estimated Duration**: 5-10 minutes

---

## Pre-Migration Checklist

### 1. Verify Environment

```bash
# Check current migration state
cd /root/agenticverz2.0/backend
DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic current

# Expected: 021_m10_durable_queue_fallback (or earlier)
```

### 2. Create Database Backup

**CRITICAL: Do not skip this step**

```bash
# Set variables
export PROD_DB_URL="postgresql://..."  # Your production DB URL
export BACKUP_FILE="backup_pre_m10_022_$(date +%Y%m%d_%H%M%S).dump"

# Create backup
pg_dump -Fc -f "$BACKUP_FILE" "$PROD_DB_URL"

# Verify backup size (should be > 0)
ls -lh "$BACKUP_FILE"

# Test backup is valid (read table list)
pg_restore -l "$BACKUP_FILE" | head -20
```

### 3. Verify Redis Config (Required for Streams)

```bash
# Run Redis config check
cd /root/agenticverz2.0/backend
python -m scripts.ops.check_redis_config --json

# Must pass:
# - appendonly = yes
# - maxmemory-policy = noeviction
```

### 4. Schedule Maintenance Window

- **Recommended**: Low-traffic period (weeknight or weekend)
- **Duration**: 15-30 minutes including verification
- **Impact**: Minimal (adds tables, doesn't modify existing data)

---

## Migration Steps

### Step 1: Apply to Staging First

```bash
# Connect to staging
export STAGING_DB_URL="postgresql://..."

# Apply migration
cd /root/agenticverz2.0/backend
DATABASE_URL="$STAGING_DB_URL" PYTHONPATH=. alembic upgrade 022_m10_production_hardening

# Verify
DATABASE_URL="$STAGING_DB_URL" PYTHONPATH=. alembic current
# Expected: 022_m10_production_hardening
```

### Step 2: Run Staging Smoke Tests

```bash
# Run leader election tests
DATABASE_URL="$STAGING_DB_URL" PYTHONPATH=. pytest tests/test_m10_leader_election.py -v

# Run chaos tests
DATABASE_URL="$STAGING_DB_URL" PYTHONPATH=. pytest tests/test_m10_recovery_chaos.py -v -k "not high_volume"

# Test lock functions manually
PGPASSWORD="..." psql -h staging-host -U user -d dbname -c "SELECT m10_recovery.acquire_lock('test:lock', 'test-holder', 60)"
# Expected: t (true)

PGPASSWORD="..." psql -h staging-host -U user -d dbname -c "SELECT m10_recovery.release_lock('test:lock', 'test-holder')"
# Expected: t (true)
```

### Step 3: Apply to Production

```bash
# Enter maintenance mode (optional)
# curl -X POST http://localhost:8000/admin/maintenance/enable

# Apply migration
cd /root/agenticverz2.0/backend
DATABASE_URL="$PROD_DB_URL" PYTHONPATH=. alembic upgrade 022_m10_production_hardening

# Verify
DATABASE_URL="$PROD_DB_URL" PYTHONPATH=. alembic current
# Expected: 022_m10_production_hardening
```

### Step 4: Verify Tables Created

```bash
psql "$PROD_DB_URL" -c "
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'm10_recovery'
AND table_name IN ('distributed_locks', 'replay_log', 'dead_letter_archive', 'outbox')
ORDER BY table_name;
"
# Expected: 4 rows (all 4 tables)
```

### Step 5: Verify Functions Created

```bash
psql "$PROD_DB_URL" -c "
SELECT routine_name FROM information_schema.routines
WHERE routine_schema = 'm10_recovery'
AND routine_name IN ('acquire_lock', 'release_lock', 'extend_lock', 'record_replay',
                     'archive_dead_letter', 'publish_outbox', 'claim_outbox_events',
                     'complete_outbox_event', 'cleanup_expired_locks')
ORDER BY routine_name;
"
# Expected: 9 rows (all functions)
```

---

## Post-Migration Verification

### 1. Test Lock Acquisition

```bash
# Test acquire/release cycle
psql "$PROD_DB_URL" -c "
DO \$\$
DECLARE
    acquired BOOLEAN;
    released BOOLEAN;
BEGIN
    SELECT m10_recovery.acquire_lock('migration:test', 'runbook', 60) INTO acquired;
    IF NOT acquired THEN
        RAISE EXCEPTION 'Failed to acquire lock';
    END IF;

    SELECT m10_recovery.release_lock('migration:test', 'runbook') INTO released;
    IF NOT released THEN
        RAISE EXCEPTION 'Failed to release lock';
    END IF;

    RAISE NOTICE 'Lock test PASSED';
END \$\$;
"
```

### 2. Test Replay Log Idempotency

```bash
psql "$PROD_DB_URL" -c "
SELECT * FROM m10_recovery.record_replay(
    'test-orig-msg-001',
    'test-dl-msg-001',
    NULL,
    NULL,
    'test-new-msg-001',
    'runbook'
);
"
# Expected: (f, <some_id>)  -- first insert

psql "$PROD_DB_URL" -c "
SELECT * FROM m10_recovery.record_replay(
    'test-orig-msg-001',  -- Same ID
    'test-dl-msg-002',
    NULL,
    NULL,
    'test-new-msg-002',
    'runbook'
);
"
# Expected: (t, <same_id>)  -- idempotent return

# Cleanup test data
psql "$PROD_DB_URL" -c "DELETE FROM m10_recovery.replay_log WHERE original_msg_id = 'test-orig-msg-001';"
```

### 3. Verify Services Running

```bash
# Check reconcile job can acquire lock
python -m scripts.ops.reconcile_dl --dry-run --json

# Check matview refresh can acquire lock
python -m scripts.ops.refresh_matview --status --json
```

### 4. Check Prometheus Metrics

```bash
# After a few minutes, verify metrics appear
curl -s http://localhost:8000/metrics | grep m10_lock
curl -s http://localhost:8000/metrics | grep m10_outbox
curl -s http://localhost:8000/metrics | grep m10_archive
```

---

## Rollback Procedure

### If Migration Fails During Execution

```bash
# Check Alembic state
DATABASE_URL="$PROD_DB_URL" PYTHONPATH=. alembic current

# If partial, manual cleanup may be needed
# The migration is designed to be idempotent (IF NOT EXISTS)
```

### If Application Issues After Migration

```bash
# 1. Stop services using new features
systemctl stop m10-outbox-processor
systemctl stop m10-dl-reconcile
systemctl stop m10-matview-refresh

# 2. Rollback migration
DATABASE_URL="$PROD_DB_URL" PYTHONPATH=. alembic downgrade 021_m10_durable_queue_fallback

# 3. Verify rollback
DATABASE_URL="$PROD_DB_URL" PYTHONPATH=. alembic current
# Expected: 021_m10_durable_queue_fallback
```

### If Database Corruption (Emergency)

```bash
# 1. Stop all services
systemctl stop nova-worker nova-backend

# 2. Restore from backup
pg_restore -c -d "$PROD_DB_URL" "$BACKUP_FILE"

# 3. Verify restoration
DATABASE_URL="$PROD_DB_URL" PYTHONPATH=. alembic current

# 4. Restart services
systemctl start nova-backend nova-worker
```

---

## Systemd Timer Setup (Post-Migration)

After successful migration, install the systemd timers:

```bash
# Copy service files
sudo cp /root/agenticverz2.0/deployment/systemd/m10-*.{service,timer} /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable timers
sudo systemctl enable m10-outbox-processor.timer
sudo systemctl enable m10-dl-reconcile.timer
sudo systemctl enable m10-matview-refresh.timer
sudo systemctl enable m10-retention-cleanup.timer
sudo systemctl enable m10-reclaim-gc.timer

# Start timers
sudo systemctl start m10-outbox-processor.timer
sudo systemctl start m10-dl-reconcile.timer
sudo systemctl start m10-matview-refresh.timer
sudo systemctl start m10-retention-cleanup.timer
sudo systemctl start m10-reclaim-gc.timer

# Verify timers
systemctl list-timers | grep m10
```

---

## Troubleshooting

### Lock Acquisition Failing

```bash
# Check for stale locks
psql "$PROD_DB_URL" -c "SELECT * FROM m10_recovery.distributed_locks;"

# Cleanup expired locks
psql "$PROD_DB_URL" -c "SELECT m10_recovery.cleanup_expired_locks();"

# Force release a specific lock (use with caution)
psql "$PROD_DB_URL" -c "DELETE FROM m10_recovery.distributed_locks WHERE lock_name = 'stuck:lock';"
```

### Replay Log Growing Too Fast

```bash
# Check replay log size
psql "$PROD_DB_URL" -c "SELECT COUNT(*) FROM m10_recovery.replay_log;"

# Check retention cleanup is running
journalctl -u m10-retention-cleanup.service --since "1 day ago"

# Manual cleanup (if needed)
psql "$PROD_DB_URL" -c "DELETE FROM m10_recovery.replay_log WHERE replayed_at < now() - interval '30 days';"
```

### Outbox Events Not Processing

```bash
# Check pending events
psql "$PROD_DB_URL" -c "SELECT COUNT(*), event_type FROM m10_recovery.outbox WHERE processed_at IS NULL GROUP BY event_type;"

# Check outbox processor logs
journalctl -u m10-outbox-processor.service -f

# Check for lock contention
psql "$PROD_DB_URL" -c "SELECT * FROM m10_recovery.distributed_locks WHERE lock_name LIKE 'm10:outbox%';"
```

---

## Alert Silencing Guidelines

During migrations, deploys, and large-scale tests, you may need to temporarily silence M10 alerts to prevent noise. Use these templates with Alertmanager.

### When to Silence Alerts

| Scenario | Recommended Silence Duration | Alerts to Silence |
|----------|------------------------------|-------------------|
| Migration 022 deployment | 30 minutes | All M10 alerts |
| Scheduled maintenance | Duration + 15 min buffer | All M10 alerts |
| Chaos/scale testing | Test duration + 10 min | M10WorkerFailureRateHigh, M10QueueDepthHigh |
| Outbox processor restart | 10 minutes | M10OutboxPendingHigh, M10OutboxLagHigh |
| DL reconcile debugging | 15 minutes | M10DeadLetterGrowing |

### Alertmanager CLI Silence Commands

```bash
# Install amtool if not present
# go install github.com/prometheus/alertmanager/cmd/amtool@latest

# Set Alertmanager URL
export ALERTMANAGER_URL=http://localhost:9093

# Silence ALL M10 alerts for 30 minutes (migration window)
amtool silence add \
  --alertmanager.url="$ALERTMANAGER_URL" \
  --author="$(whoami)" \
  --comment="M10 migration 022 deployment" \
  --duration="30m" \
  'alertname=~"M10.*"'

# Silence specific alerts during chaos testing (1 hour)
amtool silence add \
  --alertmanager.url="$ALERTMANAGER_URL" \
  --author="$(whoami)" \
  --comment="M10 chaos testing" \
  --duration="1h" \
  'alertname=~"M10WorkerFailureRateHigh|M10QueueDepthHigh"'

# Silence outbox alerts during processor restart
amtool silence add \
  --alertmanager.url="$ALERTMANAGER_URL" \
  --author="$(whoami)" \
  --comment="Outbox processor restart" \
  --duration="10m" \
  'alertname=~"M10Outbox.*"'

# Silence lock alerts during leader election testing
amtool silence add \
  --alertmanager.url="$ALERTMANAGER_URL" \
  --author="$(whoami)" \
  --comment="Leader election testing" \
  --duration="15m" \
  'alertname=~"M10Lock.*"'
```

### List and Expire Silences

```bash
# List active silences
amtool silence query --alertmanager.url="$ALERTMANAGER_URL"

# Expire a silence by ID
amtool silence expire --alertmanager.url="$ALERTMANAGER_URL" <SILENCE_ID>

# Expire ALL silences (use with caution)
amtool silence expire --alertmanager.url="$ALERTMANAGER_URL" $(amtool silence query -q)
```

### HTTP API Alternative (without amtool)

```bash
# Create silence via HTTP API
curl -X POST "$ALERTMANAGER_URL/api/v2/silences" \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {"name": "alertname", "value": "M10.*", "isRegex": true}
    ],
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "endsAt": "'$(date -u -d "+30 minutes" +%Y-%m-%dT%H:%M:%SZ)'",
    "createdBy": "'"$(whoami)"'",
    "comment": "M10 migration 022 deployment"
  }'

# List silences via HTTP
curl -s "$ALERTMANAGER_URL/api/v2/silences" | jq '.[] | {id, status, comment}'

# Delete silence via HTTP
curl -X DELETE "$ALERTMANAGER_URL/api/v2/silence/<SILENCE_ID>"
```

### Pre-Deploy Silence Script

Create a helper script for consistent silencing:

```bash
#!/bin/bash
# silence_m10_alerts.sh - Create silence for M10 deployments

ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
DURATION="${1:-30m}"
COMMENT="${2:-M10 deployment}"

echo "Creating silence for M10 alerts..."
echo "Duration: $DURATION"
echo "Comment: $COMMENT"

SILENCE_ID=$(amtool silence add \
  --alertmanager.url="$ALERTMANAGER_URL" \
  --author="$(whoami)" \
  --comment="$COMMENT" \
  --duration="$DURATION" \
  'alertname=~"M10.*"' 2>&1 | tail -1)

echo "Silence created: $SILENCE_ID"
echo "To expire early: amtool silence expire --alertmanager.url=$ALERTMANAGER_URL $SILENCE_ID"
```

### Post-Deploy Verification

After removing silence (or when it expires):

```bash
# Verify no firing alerts
amtool alert query --alertmanager.url="$ALERTMANAGER_URL" | grep M10

# Check Prometheus for pending alerts
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname | startswith("M10"))'
```

### Best Practices

1. **Always set an expiry** - Never create indefinite silences
2. **Document the reason** - Use descriptive comments
3. **Verify removal** - Check alerts fire correctly after silence expires
4. **Notify team** - Inform on-call when silencing during incidents
5. **Log silences** - Keep a record of when and why silences were created

---

## Contacts

- **On-Call**: Check PagerDuty/Opsgenie rotation
- **Database Team**: [team-db@company.com]
- **M10 Owner**: [m10-owner@company.com]

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2025-12-09 | Claude | Added alert silencing guidelines section |
| 2025-12-09 | Claude | Initial runbook for migration 022 |
