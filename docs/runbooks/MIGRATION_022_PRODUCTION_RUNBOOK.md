# Migration 022 Production Runbook

**Migration:** `022_m10_production_hardening`
**Date:** 2025-12-30
**Risk Level:** MEDIUM
**Downtime:** Zero (online migration)
**Reference:** PIN-052

---

## Summary

Migration 022 adds M10 production hardening infrastructure:

| Component | Purpose |
|-----------|---------|
| `distributed_locks` | Leader election for reconcile/matview jobs |
| `replay_log` | Durable idempotency for dead-letter replays |
| `dead_letter_archive` | Archive DL messages before Redis trim |
| `outbox` | Transactional outbox for external side-effects |
| 9 stored functions | Lock management, replay, archive, outbox operations |

---

## Pre-Migration Checklist

### 1. Verify Current State

```bash
# Check current migration head
cd /root/agenticverz2.0/backend
source ../.env

alembic current
# Expected: 021_m10_durable_queue_fallback (head)

# Verify m10_recovery schema exists
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'm10_recovery';"
```

### 2. Verify No Active Locks

```bash
# Check for active transactions on m10_recovery schema
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "SELECT pid, state, query FROM pg_stat_activity WHERE query LIKE '%m10_recovery%' AND state != 'idle';"
```

### 3. Create Backup Point

```bash
# Note the current timestamp for point-in-time recovery if needed
echo "Migration start: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Optional: Create pg_dump of m10_recovery schema
PGPASSWORD=$PGPASSWORD pg_dump -h $PGHOST -U $PGUSER -d $PGDATABASE \
  --schema=m10_recovery --no-owner --no-privileges \
  -f /tmp/m10_recovery_pre_022_$(date +%Y%m%d_%H%M%S).sql
```

### 4. Verify Worker State

```bash
# Check worker status (should be running but idle is preferred)
docker compose ps nova_worker

# Optional: Pause worker during migration for safety
docker compose stop nova_worker
```

---

## Migration Execution

### Step 1: Dry Run (Recommended)

```bash
cd /root/agenticverz2.0/backend

# Generate SQL without executing
alembic upgrade --sql 021_m10_durable_queue_fallback:022_m10_production_hardening > /tmp/migration_022.sql

# Review the generated SQL
less /tmp/migration_022.sql
```

### Step 2: Execute Migration

```bash
# Run the migration
alembic upgrade 022_m10_production_hardening

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade 021_m10_durable_queue_fallback -> 022_m10_production_hardening, 022_m10_production_hardening - Leader election, replay log, DL archive, outbox
```

### Step 3: Verify Migration

```bash
# Confirm current head
alembic current
# Expected: 022_m10_production_hardening (head)

# Verify tables created
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "SELECT table_name FROM information_schema.tables WHERE table_schema = 'm10_recovery' ORDER BY table_name;"

# Expected tables:
# - dead_letter_archive
# - distributed_locks
# - outbox
# - replay_log
# (plus existing tables from earlier migrations)
```

---

## Post-Migration Verification

### 1. Verify Tables Structure

```bash
# Check distributed_locks
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "\d m10_recovery.distributed_locks"

# Check replay_log
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "\d m10_recovery.replay_log"

# Check dead_letter_archive
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "\d m10_recovery.dead_letter_archive"

# Check outbox
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "\d m10_recovery.outbox"
```

### 2. Verify Functions Created

```bash
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'm10_recovery' ORDER BY routine_name;"

# Expected functions:
# - acquire_lock
# - archive_dead_letter
# - claim_outbox_events
# - cleanup_expired_locks
# - complete_outbox_event
# - extend_lock
# - publish_outbox
# - record_replay
# - release_lock
```

### 3. Test Lock Functions

```bash
# Test acquiring a lock
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "SELECT m10_recovery.acquire_lock('test:runbook', 'runbook-test', 60);"
# Expected: t (true)

# Test extending lock
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "SELECT m10_recovery.extend_lock('test:runbook', 'runbook-test', 120);"
# Expected: t (true)

# Test releasing lock
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "SELECT m10_recovery.release_lock('test:runbook', 'runbook-test');"
# Expected: t (true)
```

### 4. Restart Services

```bash
# If worker was stopped, restart it
docker compose start nova_worker

# Restart backend to pick up new schema
docker compose restart nova_backend

# Verify health
curl http://localhost:8000/health
```

---

## Rollback Procedure

If issues are encountered, rollback to 021:

```bash
cd /root/agenticverz2.0/backend

# Downgrade migration
alembic downgrade 021_m10_durable_queue_fallback

# Verify rollback
alembic current
# Expected: 021_m10_durable_queue_fallback (head)

# Verify tables removed
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "SELECT table_name FROM information_schema.tables WHERE table_schema = 'm10_recovery' AND table_name IN ('distributed_locks', 'replay_log', 'dead_letter_archive', 'outbox');"
# Expected: 0 rows
```

---

## Monitoring After Migration

### Key Metrics to Watch

| Metric | Alert Threshold | Description |
|--------|-----------------|-------------|
| `m10_locks_acquired_total` | N/A | Total lock acquisitions |
| `m10_locks_failed_total` | > 10/min | Failed lock acquisitions |
| `m10_replay_duplicates_total` | > 5/min | Duplicate replay attempts |
| `m10_outbox_pending_gauge` | > 100 | Pending outbox events |
| `m10_outbox_retry_total` | > 20/min | Outbox retry rate |

### Dashboard Panels

Check Grafana dashboard: **M10 Recovery Operations**

---

## Troubleshooting

### Issue: Lock Contention

```sql
-- Check active locks
SELECT * FROM m10_recovery.distributed_locks
WHERE expires_at > now()
ORDER BY acquired_at DESC;

-- Force release stale lock (use with caution)
DELETE FROM m10_recovery.distributed_locks
WHERE lock_name = 'stuck:lock' AND expires_at < now();
```

### Issue: Replay Duplicates

```sql
-- Check recent replays
SELECT * FROM m10_recovery.replay_log
ORDER BY replayed_at DESC
LIMIT 20;

-- Check for duplicate original_msg_id
SELECT original_msg_id, COUNT(*)
FROM m10_recovery.replay_log
GROUP BY original_msg_id
HAVING COUNT(*) > 1;
```

### Issue: Outbox Backlog

```sql
-- Check pending outbox events
SELECT event_type, COUNT(*), MIN(created_at) as oldest
FROM m10_recovery.outbox
WHERE processed_at IS NULL
GROUP BY event_type
ORDER BY oldest;

-- Check failed events
SELECT * FROM m10_recovery.outbox
WHERE processed_at IS NULL
  AND retry_count > 3
ORDER BY created_at
LIMIT 10;
```

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| DBA | | | |
| Ops Engineer | | | |
| Tech Lead | | | |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Initial runbook created |
