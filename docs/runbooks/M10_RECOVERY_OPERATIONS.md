# M10 Recovery Operations Runbook

## Overview

This runbook covers operations for the M10 Recovery Suggestion Engine enhancements.

## Migration Checklist

### Pre-Migration

1. **Backup database**
   ```bash
   pg_dump -Fc $DATABASE_URL > pre_m10_backup_$(date +%F).dump
   ```

2. **Check migration status**
   ```bash
   cd /root/agenticverz2.0/backend
   DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic current
   ```

### Apply Migrations

1. **Apply enhancement migration (019)**
   ```bash
   DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic upgrade 019_m10_recovery_enhancements
   ```

2. **Apply concurrent indexes (020) - during low traffic**
   ```bash
   DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic upgrade 020_m10_concurrent_indexes
   ```

### Post-Migration Verification

```sql
-- Verify schema exists
SELECT schema_name FROM information_schema.schemata
WHERE schema_name = 'm10_recovery';

-- Verify idempotency_key column
SELECT column_name FROM information_schema.columns
WHERE table_name = 'recovery_candidates' AND column_name = 'idempotency_key';

-- Verify materialized view
SELECT COUNT(*) FROM m10_recovery.mv_top_pending;

-- Verify retention jobs seeded
SELECT name, retention_days FROM m10_recovery.retention_jobs;

-- Verify archive tables
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'm10_recovery' AND table_name LIKE '%_archive';
```

---

## Worker Operations

### Start Recovery Claim Worker

```bash
cd /root/agenticverz2.0/backend

# Standard mode
PYTHONPATH=. python -m app.worker.recovery_claim_worker

# With custom batch size
PYTHONPATH=. python -m app.worker.recovery_claim_worker --batch-size 100 --poll-interval 5

# Debug mode
PYTHONPATH=. python -m app.worker.recovery_claim_worker --debug
```

### Monitor Worker Progress

```sql
-- Check claimed/executing candidates
SELECT execution_status, COUNT(*)
FROM recovery_candidates
GROUP BY execution_status;

-- Find stuck candidates (executing > 5 min)
SELECT id, created_at, execution_status
FROM recovery_candidates
WHERE execution_status = 'executing'
  AND updated_at < now() - interval '5 minutes';

-- Release stuck candidates
UPDATE recovery_candidates
SET execution_status = 'pending', updated_at = now()
WHERE execution_status = 'executing'
  AND updated_at < now() - interval '10 minutes';
```

---

## Materialized View Operations

### Refresh Materialized View

```sql
-- Standard refresh (blocks reads briefly)
REFRESH MATERIALIZED VIEW m10_recovery.mv_top_pending;

-- Concurrent refresh (no blocking, requires unique index)
REFRESH MATERIALIZED VIEW CONCURRENTLY m10_recovery.mv_top_pending;

-- Using function
SELECT m10_recovery.refresh_mv_top_pending();
```

### Schedule Refresh (cron)

```cron
# Refresh every 5 minutes
*/5 * * * * psql $DATABASE_URL -c "REFRESH MATERIALIZED VIEW CONCURRENTLY m10_recovery.mv_top_pending;" >> /var/log/agenticverz/mv_refresh.log 2>&1
```

---

## Retention & Archival

### Run Retention Archive Job

```bash
cd /root/agenticverz2.0/scripts/ops

# Dry run (see what would be archived)
python m10_retention_archive.py --dry-run

# Run archive with default 90-day retention
python m10_retention_archive.py

# Custom retention period
python m10_retention_archive.py --retention-days 60

# Specific job only
python m10_retention_archive.py --job provenance_archive

# JSON output for monitoring
python m10_retention_archive.py --json
```

### Verify Archive Results

```sql
-- Check archive counts
SELECT COUNT(*) as archived FROM m10_recovery.suggestion_provenance_archive;
SELECT COUNT(*) as archived FROM m10_recovery.suggestion_input_archive;

-- Check retention job metadata
SELECT name, last_run, rows_archived, rows_deleted
FROM m10_recovery.retention_jobs;
```

### Schedule Retention (DEPRECATED - Now Handled by Orchestrator)

> **Note:** As of PIN-058, retention is handled by the consolidated m10-maintenance.timer orchestrator.
> The individual retention timer is no longer needed. See the "M10 Maintenance Orchestrator" section below.

---

## M10 Maintenance Orchestrator (PIN-058)

As of PIN-058, the 5 separate systemd timers were consolidated into a single orchestrator.

### Timer Status

```bash
# Check orchestrator timer status
systemctl status m10-maintenance.timer

# View recent runs
journalctl -u m10-maintenance.service --since "1 hour ago"

# List all M10 timers (should only show m10-maintenance)
systemctl list-timers 'm10*'
```

### Manual Orchestrator Run

```bash
cd /root/agenticverz2.0

# Run all maintenance tasks
DATABASE_URL="$DATABASE_URL" PYTHONPATH=backend python3 scripts/ops/m10_orchestrator.py

# Dry run (no changes)
DATABASE_URL="$DATABASE_URL" PYTHONPATH=backend python3 scripts/ops/m10_orchestrator.py --dry-run

# Run specific tasks only
DATABASE_URL="$DATABASE_URL" PYTHONPATH=backend python3 scripts/ops/m10_orchestrator.py --tasks outbox,matview

# JSON output for monitoring
DATABASE_URL="$DATABASE_URL" PYTHONPATH=backend python3 scripts/ops/m10_orchestrator.py --json
```

### Tasks Run by Orchestrator

| Task | Description | Frequency |
|------|-------------|-----------|
| outbox | Process pending outbox events | Every run |
| dl_reconcile | Reconcile dead-letter entries | Every run |
| matview | Refresh materialized views | Every run (if stale > 5m) |
| retention | Archive old records | Every run (30-day retention) |
| reclaim_gc | Clean up stale locks | Every run |

### Systemd Unit Files

**Timer:** `/etc/systemd/system/m10-maintenance.timer`
```ini
[Unit]
Description=M10 Maintenance Orchestrator Timer

[Timer]
OnCalendar=*:0/5
AccuracySec=30s
Persistent=true

[Install]
WantedBy=timers.target
```

**Service:** `/etc/systemd/system/m10-maintenance.service`
```ini
[Unit]
Description=M10 Maintenance Orchestrator
After=network.target postgresql.service redis.service

[Service]
Type=oneshot
User=root
WorkingDirectory=/root/agenticverz2.0
ExecStart=/usr/bin/python3 scripts/ops/m10_orchestrator.py
Environment=DATABASE_URL=postgresql://nova:novapass@localhost:5433/nova_aos
Environment=PYTHONPATH=/root/agenticverz2.0/backend
TimeoutStartSec=600

[Install]
WantedBy=multi-user.target
```

---

## Outbox Processor Operations

The outbox processor handles exactly-once external side-effects using the transactional outbox pattern.

### Start Outbox Processor

```bash
cd /root/agenticverz2.0/backend

# Run as worker (continuous)
DATABASE_URL="$DATABASE_URL" PYTHONPATH=. python -m app.worker.outbox_processor

# One-time processing
DATABASE_URL="$DATABASE_URL" PYTHONPATH=. python -m app.worker.outbox_processor --once

# With custom batch size
DATABASE_URL="$DATABASE_URL" PYTHONPATH=. python -m app.worker.outbox_processor --batch-size 50
```

### Monitor Outbox

```sql
-- Outbox status overview
SELECT
    CASE
        WHEN processed_at IS NOT NULL THEN 'processed'
        WHEN next_retry_at > now() THEN 'retrying'
        ELSE 'pending'
    END as status,
    COUNT(*) as count,
    AVG(retry_count) as avg_retries
FROM m10_recovery.outbox
GROUP BY 1;

-- Oldest pending lag
SELECT EXTRACT(EPOCH FROM (now() - MIN(created_at)))
FROM m10_recovery.outbox
WHERE processed_at IS NULL;

-- Recent failures
SELECT id, event_type, retry_count, last_error, updated_at
FROM m10_recovery.outbox
WHERE last_error IS NOT NULL
ORDER BY updated_at DESC
LIMIT 10;
```

### Troubleshooting Outbox

**Issue: Outbox processor not processing**

1. Check lock status:
   ```sql
   SELECT * FROM m10_recovery.distributed_locks
   WHERE lock_name = 'm10:outbox_processor';
   ```

2. Release stale lock:
   ```sql
   DELETE FROM m10_recovery.distributed_locks
   WHERE lock_name = 'm10:outbox_processor'
     AND expires_at < NOW();
   ```

**Issue: Events stuck in retry**

1. Check retry count:
   ```sql
   SELECT id, event_type, retry_count, next_retry_at, last_error
   FROM m10_recovery.outbox
   WHERE processed_at IS NULL AND retry_count > 0
   ORDER BY retry_count DESC
   LIMIT 10;
   ```

2. Reset retry count for stuck events:
   ```sql
   UPDATE m10_recovery.outbox
   SET retry_count = 0, next_retry_at = NOW(), last_error = NULL
   WHERE id IN (SELECT id FROM m10_recovery.outbox WHERE retry_count >= 5 AND processed_at IS NULL);
   ```

---

## Ingest Endpoint Operations

### Test Ingest Endpoint

```bash
# Basic ingest
curl -X POST http://localhost:8000/api/v1/recovery/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "failure_match_id": "'$(uuidgen)'",
    "failure_payload": {
      "error_type": "TIMEOUT",
      "raw": "Connection timed out after 30s"
    },
    "source": "test"
  }'

# With idempotency key
IDEM_KEY=$(uuidgen)
curl -X POST http://localhost:8000/api/v1/recovery/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "failure_match_id": "'$(uuidgen)'",
    "failure_payload": {"error_type": "TEST", "raw": "Test"},
    "idempotency_key": "'$IDEM_KEY'"
  }'
```

### Monitor Ingest Queue

```sql
-- Pending evaluation backlog
SELECT COUNT(*) as pending
FROM recovery_candidates
WHERE decision = 'pending'
  AND (confidence IS NULL OR confidence <= 0.2);

-- Recent ingests
SELECT id, error_code, confidence, created_at
FROM recovery_candidates
ORDER BY created_at DESC
LIMIT 10;
```

---

## Troubleshooting

### Issue: Worker not claiming rows

1. Check for locked rows:
   ```sql
   SELECT pid, query, state, wait_event
   FROM pg_stat_activity
   WHERE query LIKE '%recovery_candidates%';
   ```

2. Check confidence threshold:
   ```sql
   SELECT confidence, COUNT(*)
   FROM recovery_candidates
   WHERE decision = 'pending'
   GROUP BY confidence;
   ```

### Issue: Materialized view stale

1. Check last refresh:
   ```sql
   SELECT schemaname, matviewname,
          pg_size_pretty(pg_total_relation_size(schemaname || '.' || matviewname))
   FROM pg_matviews
   WHERE schemaname = 'm10_recovery';
   ```

2. Force refresh:
   ```sql
   REFRESH MATERIALIZED VIEW m10_recovery.mv_top_pending;
   ```

### Issue: Duplicate ingests

1. Check for missing idempotency_key:
   ```sql
   SELECT COUNT(*) as without_key
   FROM recovery_candidates
   WHERE idempotency_key IS NULL;
   ```

2. Find duplicates by failure_match_id:
   ```sql
   SELECT failure_match_id, COUNT(*) as cnt
   FROM recovery_candidates
   GROUP BY failure_match_id
   HAVING COUNT(*) > 1;
   ```

---

## Metrics to Monitor

- `recovery_candidates` count by decision status
- Worker claim rate (rows/second)
- Materialized view age (time since last refresh)
- Archive job success/failure
- Ingest endpoint latency (p99)

---

## Deployment Checklist

### Pre-Deployment

1. **Ensure pgcrypto present**
   ```bash
   psql $DATABASE_URL -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
   ```

2. **Backup database**
   ```bash
   pg_dump -Fc $DATABASE_URL > pre_m10_phase3_backup_$(date +%F).dump
   ```

3. **Check current migration**
   ```bash
   DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic current
   ```

### Apply Migrations (Phase 3)

1. **Apply durable queue migration (021)**
   ```bash
   DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic upgrade 021_m10_durable_queue_fallback
   ```

2. **Verify migration success**
   ```sql
   -- Check work_queue table
   SELECT COUNT(*) FROM m10_recovery.work_queue;

   -- Check functions exist
   SELECT proname FROM pg_proc
   WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'm10_recovery')
     AND proname IN ('enqueue_work', 'claim_work', 'complete_work', 'release_stalled_work');

   -- Check matview freshness tracking
   SELECT * FROM m10_recovery.matview_freshness;

   -- Check unique index
   SELECT indexname FROM pg_indexes
   WHERE tablename = 'recovery_candidates' AND indexname = 'uq_rc_fmid_sig';
   ```

### Deploy Backend

1. **Deploy with feature flag OFF**
   ```bash
   docker compose up -d --build backend
   ```

2. **Run smoke ingest test**
   ```bash
   curl -X POST http://localhost:8000/api/v1/recovery/ingest \
     -H "Content-Type: application/json" \
     -d '{"failure_match_id": "'$(uuidgen)'", "failure_payload": {"error_type": "SMOKE_TEST"}}'
   ```

### Enable Redis Stream Consumer

1. **Start stream consumer service**
   ```bash
   # Via docker
   docker compose up -d recovery_worker

   # Or manually
   PYTHONPATH=. python -m app.worker.recovery_claim_worker --use-stream
   ```

2. **Monitor stream health**
   ```bash
   # Redis stream info
   redis-cli XINFO STREAM m10:evaluate:stream
   redis-cli XLEN m10:evaluate:stream
   redis-cli XPENDING m10:evaluate:stream m10:evaluate:group
   ```

### Enable Matview Refresh Cron

1. **Add tracked refresh cron**
   ```cron
   */5 * * * * psql $DATABASE_URL -c "SELECT m10_recovery.refresh_mv_tracked('mv_top_pending');" >> /var/log/agenticverz/mv_refresh.log 2>&1
   ```

2. **Verify refresh works**
   ```sql
   SELECT * FROM m10_recovery.matview_freshness;
   ```

### Enable Prometheus Alerts

1. **Verify alert rules loaded**
   ```bash
   curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name | startswith("m10"))'
   ```

2. **Check alert status**
   ```bash
   curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.component == "m10_recovery")'
   ```

### Post-Deployment Verification

```bash
# Check metrics exposed
curl -s http://localhost:8000/metrics | grep recovery_

# Check Redis stream
redis-cli XINFO STREAM m10:evaluate:stream

# Check DB fallback queue
psql $DATABASE_URL -c "SELECT COUNT(*) FROM m10_recovery.work_queue WHERE processed_at IS NULL;"

# Check matview freshness
psql $DATABASE_URL -c "SELECT * FROM m10_recovery.matview_freshness;"
```

---

## Redis Stream Operations

### Monitor Stream

```bash
# Stream info
redis-cli XINFO STREAM m10:evaluate:stream

# Stream length
redis-cli XLEN m10:evaluate:stream

# Pending messages (unacknowledged)
redis-cli XPENDING m10:evaluate:stream m10:evaluate:group

# Consumer info
redis-cli XINFO GROUPS m10:evaluate:stream
```

### Recover Stalled Messages

```bash
# Claim messages pending > 60 seconds
redis-cli XCLAIM m10:evaluate:stream m10:evaluate:group worker-recovery 60000 <MESSAGE_ID>

# Or use the Python function
PYTHONPATH=. python -c "
import asyncio
from app.tasks.recovery_queue_stream import claim_stalled_messages
asyncio.run(claim_stalled_messages(idle_ms=60000))
"
```

### Trim Stream (if too large)

```bash
# Trim to keep last 100000 messages
redis-cli XTRIM m10:evaluate:stream MAXLEN ~ 100000
```

---

## DB Fallback Queue Operations

### Monitor Queue

```sql
-- Queue depth
SELECT COUNT(*) FROM m10_recovery.work_queue WHERE processed_at IS NULL;

-- Stalled items (claimed but not processed)
SELECT COUNT(*) FROM m10_recovery.work_queue
WHERE claimed_at IS NOT NULL AND processed_at IS NULL
  AND claimed_at < now() - interval '5 minutes';

-- Queue by method
SELECT method, COUNT(*) FROM m10_recovery.work_queue
WHERE processed_at IS NULL
GROUP BY method;
```

### Release Stalled Work

```sql
-- Release items stalled > 5 minutes
SELECT m10_recovery.release_stalled_work(300);
```

### Manual Claim (for debugging)

```sql
-- Claim 10 items
SELECT * FROM m10_recovery.claim_work('manual_worker', 10);

-- Complete a work item
SELECT m10_recovery.complete_work(<work_id>, TRUE, NULL);

-- Fail a work item (release for retry)
SELECT m10_recovery.complete_work(<work_id>, FALSE, 'Manual failure');
```

---

## Troubleshooting (Extended)

### Issue: Redis Stream not consuming

1. **Check consumer group exists**
   ```bash
   redis-cli XINFO GROUPS m10:evaluate:stream
   ```

2. **Create consumer group if missing**
   ```bash
   redis-cli XGROUP CREATE m10:evaluate:stream m10:evaluate:group $ MKSTREAM
   ```

3. **Check pending messages**
   ```bash
   redis-cli XPENDING m10:evaluate:stream m10:evaluate:group - + 10
   ```

### Issue: DB fallback queue growing

1. **Check if workers are consuming**
   ```sql
   SELECT claimed_by, COUNT(*)
   FROM m10_recovery.work_queue
   WHERE processed_at IS NULL
   GROUP BY claimed_by;
   ```

2. **Release stalled work**
   ```sql
   SELECT m10_recovery.release_stalled_work(300);
   ```

3. **Check for errors**
   ```sql
   SELECT error_message, COUNT(*)
   FROM m10_recovery.work_queue
   WHERE error_message IS NOT NULL
   GROUP BY error_message
   ORDER BY COUNT(*) DESC;
   ```

### Issue: Matview refresh failing

1. **Check refresh log**
   ```sql
   SELECT * FROM m10_recovery.matview_refresh_log
   ORDER BY started_at DESC
   LIMIT 10;
   ```

2. **Check for locks**
   ```sql
   SELECT pid, query, state, wait_event
   FROM pg_stat_activity
   WHERE query LIKE '%mv_top_pending%';
   ```

3. **Manual non-concurrent refresh**
   ```sql
   REFRESH MATERIALIZED VIEW m10_recovery.mv_top_pending;
   ```

---

## Alert Thresholds (PIN-058 Simplified)

**Note:** As of PIN-058, alerts were reduced from 23 to 7 critical alerts to prevent alert fatigue.

| Alert | Threshold | Severity | Action |
|-------|-----------|----------|--------|
| M10QueueDepthCritical | queue > 5000 for 5m | Critical | Scale workers immediately |
| M10NoStreamConsumers | consumers == 0 for 5m | Critical | Start workers |
| M10OutboxPendingCritical | pending > 1000 for 10m | Critical | Check outbox processor |
| M10OutboxLagHigh | lag > 300s for 5m | Critical | Restart outbox processor |
| M10DeadLetterCritical | dead_letter > 100 for 15m | Critical | Investigate systemic failures |
| M10MatviewVeryStale | matview_age > 3600s for 5m | Critical | Manual refresh |
| M10WorkerNoActivity | no claims + backlog for 10m | Critical | Check worker health |

---

## Redis HA & Persistence Requirements

### Persistence Configuration

For production deployments, Redis must be configured with persistence to prevent message loss during restarts.

**Recommended redis.conf settings:**

```conf
# AOF persistence (recommended for durability)
appendonly yes
appendfsync everysec
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# RDB persistence (as backup)
save 900 1
save 300 10
save 60 10000

# Stream-specific settings
stream-node-max-bytes 4096
stream-node-max-entries 100

# Memory settings
maxmemory 1gb
maxmemory-policy noeviction  # CRITICAL: Don't evict stream data
```

### HA Architecture Options

#### Option 1: Redis Sentinel (Recommended for M10)

For high availability without complex clustering:

```yaml
# docker-compose.redis-sentinel.yml
services:
  redis-master:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_master_data:/data

  redis-replica-1:
    image: redis:7-alpine
    command: redis-server --appendonly yes --replicaof redis-master 6379

  redis-replica-2:
    image: redis:7-alpine
    command: redis-server --appendonly yes --replicaof redis-master 6379

  sentinel-1:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
    volumes:
      - ./sentinel.conf:/etc/redis/sentinel.conf
```

**sentinel.conf:**
```conf
sentinel monitor mymaster redis-master 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel failover-timeout mymaster 60000
sentinel parallel-syncs mymaster 1
```

#### Option 2: Redis Cluster

For horizontal scaling with very high message volumes:

```bash
# Create 6-node cluster (3 masters + 3 replicas)
redis-cli --cluster create \
  redis-1:6379 redis-2:6379 redis-3:6379 \
  redis-4:6379 redis-5:6379 redis-6:6379 \
  --cluster-replicas 1
```

**Note:** Stream consumer groups work within a single shard. M10 uses a single stream key, so cluster provides HA but not horizontal stream scaling.

### Production Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| AOF persistence enabled | Required | `appendonly yes` |
| Max memory policy = noeviction | Required | Prevents data loss |
| Replica configured | Recommended | For HA failover |
| Sentinel/Cluster | Recommended | Automatic failover |
| Monitoring | Required | Track memory, replication lag |
| Backup schedule | Recommended | Daily RDB snapshots to S3 |

### Monitoring Redis Health

```bash
# Check persistence status
redis-cli INFO persistence

# Check replication
redis-cli INFO replication

# Check stream memory usage
redis-cli MEMORY USAGE m10:evaluate:stream

# Check consumer lag
redis-cli XPENDING m10:evaluate:stream m10:evaluate:group

# Check AOF status
redis-cli INFO aof
```

### Disaster Recovery

#### If Redis loses data:

1. **DB fallback queue has pending work:**
   ```sql
   -- Check pending DB queue items
   SELECT COUNT(*) FROM m10_recovery.work_queue WHERE processed_at IS NULL;
   ```

2. **Recreate consumer group:**
   ```bash
   redis-cli XGROUP CREATE m10:evaluate:stream m10:evaluate:group $ MKSTREAM
   ```

3. **Re-enqueue from DB fallback:**
   ```sql
   -- Get items that need re-evaluation
   SELECT candidate_id FROM m10_recovery.work_queue
   WHERE processed_at IS NULL AND claimed_at IS NULL;
   ```

4. **Verify stream recovery:**
   ```bash
   redis-cli XINFO STREAM m10:evaluate:stream
   redis-cli XINFO GROUPS m10:evaluate:stream
   ```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `M10_STREAM_KEY` | `m10:evaluate:stream` | Stream key name |
| `M10_CONSUMER_GROUP` | `m10:evaluate:group` | Consumer group name |
| `M10_STREAM_MAX_LEN` | `100000` | Max stream length (MAXLEN ~) |
| `M10_CLAIM_IDLE_MS` | `60000` | Idle time before XCLAIM (ms) |
| `M10_MAX_RECLAIM_ATTEMPTS` | `3` | Max reclaims before dead-letter |
| `M10_DEAD_LETTER_STREAM` | `m10:evaluate:dead-letter` | Dead-letter stream key |

---

## Dead-Letter Operations

### Monitor Dead-Letter Stream

```bash
# Dead-letter stream length
redis-cli XLEN m10:evaluate:dead-letter

# View dead-lettered messages
redis-cli XRANGE m10:evaluate:dead-letter - + COUNT 10

# Check dead-letter reasons
redis-cli XRANGE m10:evaluate:dead-letter - + COUNT 100 | grep reason
```

### Replay Dead-Lettered Message

```bash
# Using Python
PYTHONPATH=. python -c "
import asyncio
from app.tasks.recovery_queue_stream import replay_dead_letter
msg_id = 'YOUR_MESSAGE_ID'
result = asyncio.run(replay_dead_letter(msg_id))
print(f'Replayed as: {result}')
"
```

### Bulk Replay Dead-Letters

```bash
# Replay all dead-lettered messages
PYTHONPATH=. python -c "
import asyncio
import redis.asyncio as aioredis

async def replay_all():
    r = aioredis.from_url('redis://localhost:6379/0')
    msgs = await r.xrange('m10:evaluate:dead-letter', '-', '+')
    for msg_id, fields in msgs:
        # Re-enqueue original fields
        orig_fields = {k[5:]: v for k, v in fields.items() if k.startswith('orig_')}
        if orig_fields:
            new_id = await r.xadd('m10:evaluate:stream', orig_fields)
            await r.xdel('m10:evaluate:dead-letter', msg_id)
            print(f'Replayed {msg_id} -> {new_id}')
    await r.close()

asyncio.run(replay_all())
"
```

### Investigate Dead-Letter Causes

```bash
# Group by reason
redis-cli XRANGE m10:evaluate:dead-letter - + | \
  grep -oP 'reason.*?(?=consumer)' | sort | uniq -c | sort -rn
```

---

## Metrics Collection

### Start Metrics Collector

```bash
# One-time collection
PYTHONPATH=. python -m app.tasks.m10_metrics_collector

# As background service (add to supervisor/systemd)
PYTHONPATH=. python -c "
import asyncio
from app.tasks.m10_metrics_collector import run_metrics_collector
asyncio.run(run_metrics_collector(interval=30))
"
```

### Grafana Dashboard

The M10 Recovery Dashboard is available at:
- Grafana: http://localhost:3000/d/m10-recovery
- Provisioned from: `monitoring/grafana/provisioning/dashboards/files/m10_recovery_dashboard.json`

**Dashboard Panels:**
1. **Overview Row:** Total queue depth, active consumers, matview age, pending ACKs, candidates pending, DB stalled
2. **Ingest Row:** Ingest rate by status, ingest latency percentiles
3. **Queue Row:** Queue depth (stacked Redis + DB), enqueue rate
4. **Worker Row:** Worker claims, processed rate, processing time
5. **Suggestions & Matview Row:** Suggestions by decision, matview age, refresh duration
6. **Alerts Row:** Active M10 alerts

---

## Related Files

| File | Purpose |
|------|---------|
| `alembic/versions/019_m10_recovery_enhancements.py` | Enhancement migration |
| `alembic/versions/020_m10_concurrent_indexes.py` | Concurrent indexes |
| `alembic/versions/021_m10_durable_queue_fallback.py` | Durable queue + DB fallback |
| `alembic/versions/022_m10_production_hardening.py` | Production hardening (locks, outbox, dead-letter) |
| `alembic/versions/023_m10_archive_partitioning.py` | Archive partitioning (DEFERRED - apply when >100K rows) |
| `app/api/recovery_ingest.py` | Idempotent ingest endpoint |
| `app/tasks/recovery_queue_stream.py` | Redis Streams queue + dead-letter |
| `app/tasks/m10_metrics_collector.py` | Prometheus metrics collection |
| `app/worker/recovery_claim_worker.py` | FOR UPDATE SKIP LOCKED worker |
| `app/worker/outbox_processor.py` | Transactional outbox processor |
| `scripts/ops/m10_orchestrator.py` | Consolidated maintenance orchestrator |
| `scripts/ops/m10_retention_archive.py` | Retention archive job |
| `scripts/ops/m10_load_chaos_test.py` | Load and chaos testing |
| `monitoring/rules/m10_recovery_alerts.yml` | Prometheus alert rules (7 critical alerts) |
| `monitoring/grafana/provisioning/dashboards/files/m10_recovery_dashboard.json` | Grafana dashboard |
| `deployment/systemd/m10-maintenance.timer` | Consolidated systemd timer |
| `deployment/systemd/m10-maintenance.service` | Maintenance service unit |
| `docs/memory-pins/PIN-058-m10-simplification-analysis.md` | Simplification analysis & redo report |
