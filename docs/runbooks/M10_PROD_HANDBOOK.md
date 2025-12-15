# M10 Production Handbook

**Created:** 2025-12-09
**Status:** ACTIVE
**Scope:** M10 Recovery System Production Operations

---

## Quick Reference

| Component | Location | Port |
|-----------|----------|------|
| PostgreSQL | localhost | 5433 |
| Redis | localhost | 6379 |
| Grafana | localhost | 3000 |
| Prometheus | localhost | 9090 |
| Alertmanager | localhost | 9093 |

---

## 1. Orchestrator Operations

### Start/Stop Orchestrator Timer

```bash
# Check status
systemctl status m10-maintenance.timer

# Start/enable
sudo systemctl start m10-maintenance.timer
sudo systemctl enable m10-maintenance.timer

# Stop (emergency)
sudo systemctl stop m10-maintenance.timer

# View logs
journalctl -u m10-maintenance.service -n 100 --no-pager
```

### Manual Orchestrator Run

```bash
cd /root/agenticverz2.0
DATABASE_URL="$DATABASE_URL" PYTHONPATH=backend python3 -m scripts.ops.m10_orchestrator --json
```

### Orchestrator Tasks

The orchestrator runs these tasks sequentially every 5 minutes:
1. **dl_reconcile** - XACK orphaned pending entries in Redis
2. **matview_refresh** - Refresh materialized views
3. **outbox_process** - Process pending outbox events
4. **retention** - Archive old records
5. **reclaim_gc** - Clean up expired locks

---

## 2. Outbox Processor Operations

### Start Outbox Processor (Continuous)

```bash
DATABASE_URL="$DATABASE_URL" PYTHONPATH=backend \
  python3 -m app.worker.outbox_processor --debug
```

### Process Single Batch

```bash
DATABASE_URL="$DATABASE_URL" PYTHONPATH=backend \
  python3 -m app.worker.outbox_processor --once --batch-size 50
```

### Check Outbox Status

```bash
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "
  SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE processed_at IS NULL) as pending,
    COUNT(*) FILTER (WHERE processed_at IS NOT NULL) as processed
  FROM m10_recovery.outbox;
"
```

---

## 3. Dead Letter Inspection & Replay

### Inspect Dead Letters

```bash
# Count by failure reason
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "
  SELECT failure_reason, COUNT(*)
  FROM m10_recovery.dead_letter_archive
  GROUP BY failure_reason
  ORDER BY count DESC
  LIMIT 10;
"

# View recent dead letters
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "
  SELECT id, original_msg_id, failure_reason, failed_at
  FROM m10_recovery.dead_letter_archive
  ORDER BY failed_at DESC
  LIMIT 20;
"
```

### Safe Replay (with idempotency check)

```bash
DATABASE_URL="$DATABASE_URL" PYTHONPATH=backend \
  python3 -m scripts.ops.reconcile_dl --dry-run --json
```

To actually replay:

```bash
DATABASE_URL="$DATABASE_URL" PYTHONPATH=backend \
  python3 -m scripts.ops.reconcile_dl --json
```

---

## 4. Lock Management

### Check Active Locks

```bash
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "
  SELECT lock_name, holder_id, acquired_at, expires_at
  FROM m10_recovery.distributed_locks
  WHERE expires_at > NOW()
  ORDER BY acquired_at DESC;
"
```

### Force Release Stuck Lock

```bash
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "
  SELECT m10_recovery.release_lock('lock_name_here', 'holder_id_here');
"
```

### Cleanup Expired Locks

```bash
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "
  SELECT m10_recovery.cleanup_expired_locks();
"
```

---

## 5. Alert Silencing for Deploy

### Silence Alerts in Alertmanager

```bash
# Create silence for 1 hour (adjust -d duration as needed)
curl -X POST http://localhost:9093/api/v2/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {"name": "alertname", "value": "M10.*", "isRegex": true}
    ],
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "endsAt": "'$(date -u -d "+1 hour" +%Y-%m-%dT%H:%M:%SZ)'",
    "createdBy": "deploy-script",
    "comment": "M10 deploy maintenance window"
  }'
```

### List Active Silences

```bash
curl -s http://localhost:9093/api/v2/silences | jq '.[] | select(.status.state == "active")'
```

### Delete a Silence

```bash
curl -X DELETE http://localhost:9093/api/v2/silence/{silence-id}
```

---

## 6. Rollback Procedures

### Migration 022 Rollback

**DANGER: This deletes M10 tables. Ensure backup exists first.**

```bash
# 1. Take backup FIRST
PGPASSWORD=novapass pg_dump -h localhost -p 5433 -U nova -d nova_aos \
  -Fc -f /backups/m10_pre_rollback_$(date +%F_%H%M).dump

# 2. Stop orchestrator
sudo systemctl stop m10-maintenance.timer

# 3. Downgrade migration
cd /root/agenticverz2.0/backend
DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic downgrade -1

# 4. Verify
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "
  SELECT table_name FROM information_schema.tables
  WHERE table_schema = 'm10_recovery';
"
```

### Restore from Backup

```bash
# 1. Stop all M10 services
sudo systemctl stop m10-maintenance.timer

# 2. Restore
PGPASSWORD=novapass pg_restore -h localhost -p 5433 -U nova -d nova_aos \
  --clean --if-exists /backups/m10_backup.dump

# 3. Restart services
sudo systemctl start m10-maintenance.timer
```

---

## 7. Redis Operations

### Check Redis Durability Settings

```bash
redis-cli CONFIG GET appendonly
redis-cli CONFIG GET appendfsync
redis-cli CONFIG GET maxmemory-policy
```

**Expected values:**
- `appendonly = yes`
- `appendfsync = everysec`
- `maxmemory-policy = noeviction`

### Check Redis Stream Status

```bash
# Queue depth
redis-cli XLEN m10:recovery:queue

# Consumer groups
redis-cli XINFO GROUPS m10:recovery:queue

# Pending messages
redis-cli XPENDING m10:recovery:queue m10_consumers
```

### Force Redis AOF Rewrite

```bash
redis-cli BGREWRITEAOF
```

---

## 8. Monitoring & Dashboards

### Prometheus Metrics

```bash
# Check M10 metrics
curl -s http://localhost:9090/api/v1/query?query=m10_outbox_pending | jq

# Check alert rules
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name | contains("m10"))'
```

### Grafana Dashboard

- URL: http://localhost:3000
- Dashboard: "M10 Recovery Dashboard"
- 40 panels covering queue depth, latency, dead letters, locks

### Active Alerts

```bash
curl -s http://localhost:9093/api/v2/alerts | jq '.[] | {alertname: .labels.alertname, state: .status.state}'
```

---

## 9. Health Checks

### Quick Health Check

```bash
# All-in-one health check
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "
SELECT
  (SELECT COUNT(*) FROM m10_recovery.outbox WHERE processed_at IS NULL) as outbox_pending,
  (SELECT COUNT(*) FROM m10_recovery.dead_letter_archive) as dead_letters,
  (SELECT COUNT(*) FROM m10_recovery.distributed_locks WHERE expires_at > NOW()) as active_locks,
  (SELECT COUNT(*) FROM m10_recovery.replay_log) as replay_log_entries;
"
```

### Lock Function Test

```bash
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "
  SELECT
    m10_recovery.acquire_lock('health_check', 'manual_test', 60) as acquired,
    m10_recovery.release_lock('health_check', 'manual_test') as released;
"
```

---

## 10. Alert Thresholds (PIN-058)

| Alert | Threshold | Action |
|-------|-----------|--------|
| M10QueueDepthCritical | >5000 for 5m | Scale workers or check for stuck consumers |
| M10NoStreamConsumers | ==0 for 5m | Restart outbox processor |
| M10OutboxPendingCritical | >1000 for 10m | Check outbox processor logs |
| M10OutboxLagHigh | >300s for 5m | Check for slow external endpoints |
| M10DeadLetterCritical | >100 for 15m | Investigate failure patterns, may need replay |
| M10MatviewVeryStale | >3600s for 5m | Run manual matview refresh |
| M10WorkerNoActivity | no claims + backlog for 10m | Restart worker, check Redis connectivity |

---

## 11. Emergency Procedures

### Complete M10 Stop (Emergency)

```bash
# Stop orchestrator
sudo systemctl stop m10-maintenance.timer
sudo systemctl stop m10-maintenance.service

# Verify stopped
systemctl status m10-maintenance.timer
```

### Kill Stuck Outbox Processor

```bash
# Find PID
ps aux | grep outbox_processor

# Kill
kill -TERM <pid>

# Force kill if needed
kill -9 <pid>
```

### Redis Emergency Flush (DANGER)

**Only use if Redis is corrupted and backup exists:**

```bash
# DANGER: This deletes all M10 queue data
redis-cli DEL m10:recovery:queue
redis-cli DEL m10:recovery:pending
```

---

## 12. Related Files

| File | Purpose |
|------|---------|
| `scripts/ops/m10_orchestrator.py` | Consolidated maintenance orchestrator |
| `app/worker/outbox_processor.py` | Outbox event processor |
| `scripts/ops/reconcile_dl.py` | Dead letter reconciliation |
| `scripts/ops/refresh_matview.py` | Materialized view refresh |
| `monitoring/rules/m10_recovery_alerts.yml` | 7 critical alerts |
| `monitoring/grafana/provisioning/dashboards/files/m10_recovery_dashboard.json` | 40-panel dashboard |

---

## 10. Operational Discipline

### Five Principles for Preventing Drift

#### 1. One Source of Truth
- **This runbook** (`docs/runbooks/M10_PROD_HANDBOOK.md`) is canonical
- Code in `scripts/ops/` is implementation only
- If code and docs disagree, update docs first

#### 2. Strict Gating
- All 10 P1 checks must pass in staging before M11
- JSON staging report must be pinned in PR
- No exceptions without explicit sign-off

#### 3. No Silent Deletions
- Every code removal gets explicit commit message
- Reference relevant runbook section: `cleanup: remove X per M10_PROD_HANDBOOK.md#section`
- See `docs/runbooks/DEPLOY_OWNERSHIP.md` for commit format

#### 4. Alert-First Testing
- Every change touching metrics must include test
- CI job `m10-tests` runs `tests/test_m10_metrics.py`
- Test asserts metric appears in `/metrics`

#### 5. 48h Pager Window
- Single owner assigned for 48h post-deploy
- No feature work during window
- See `docs/runbooks/DEPLOY_OWNERSHIP.md` for full protocol

### Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                M10 OPERATIONAL DISCIPLINE                    │
├─────────────────────────────────────────────────────────────┤
│ 1. DOCS FIRST     → This runbook is truth                    │
│ 2. GATE STRICT    → 10 P1 checks + JSON in PR                │
│ 3. NO SILENT DEL  → Commit message + runbook reference       │
│ 4. ALERT TESTS    → CI asserts metrics in /metrics           │
│ 5. 48H PAGER      → Single owner, no features post-deploy    │
└─────────────────────────────────────────────────────────────┘
```

---

## 11. Metrics Collector Operations

The metrics collector is a supervised daemon that populates Prometheus gauges.

### Start/Stop Metrics Collector

```bash
# Install service (one-time)
sudo cp /root/agenticverz2.0/deployment/systemd/m10-metrics-collector.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable m10-metrics-collector.service

# Start/stop
sudo systemctl start m10-metrics-collector.service
sudo systemctl stop m10-metrics-collector.service

# View logs
journalctl -u m10-metrics-collector.service -f
```

### Verify Metrics Are Being Collected

```bash
# Check service status
systemctl status m10-metrics-collector.service

# Check metrics endpoint
curl -s http://localhost:8000/metrics | grep -E "^m10_|^recovery_"
```

### Alert: M10MetricsCollectorDown

If this alert fires:
1. Check service status: `systemctl status m10-metrics-collector.service`
2. Check logs: `journalctl -u m10-metrics-collector.service -n 50`
3. Restart if needed: `sudo systemctl restart m10-metrics-collector.service`

**Risk:** Without metrics collector, all M10 alerts are blind.

---

## 12. Risk Mitigations

### Risk 1: Metrics Blind Spot After Deploy

**Issue:** Alerts loaded but dormant until metrics collector runs.

**Mitigation:**
- `m10-metrics-collector.service` is a supervised systemd service
- Alert `M10MetricsCollectorDown` fires if no metrics for 2 minutes
- Include metrics collector start in deploy checklist

### Risk 2: Data Growth / Retention

**Issue:** Partitioning deferred; archive tables may grow unbounded.

**Mitigation:**
- Alert `M10ArchiveGrowthHigh` fires at >10k combined rows
- Run retention job manually if alert fires:
  ```bash
  DATABASE_URL="$DATABASE_URL" PYTHONPATH=backend \
    python3 -m scripts.ops.m10_retention_archive --dry-run
  ```
- If sustained growth, enable partitioning (migration 023)

### Risk 3: Outbox External Endpoint Issues

**Issue:** External endpoints may rate-limit or fail; idempotency helps but doesn't prevent delays.

**Mitigation:**
- Configure per-target throttle in outbox processor:
  ```python
  # app/worker/outbox_processor.py
  TARGET_THROTTLE = {
      "slack": {"rpm": 60, "timeout": 10},
      "webhook": {"rpm": 100, "timeout": 30},
      "email": {"rpm": 30, "timeout": 20},
  }
  ```
- Alert `M10OutboxLagHigh` fires if oldest event >5 min old
- Alert `M10OutboxPendingCritical` fires if >1000 pending

### Risk 4: Rollback Without Tested Restore

**Issue:** Production restore more complex than staging test.

**Mitigation:**
- Pre-migration snapshot is MANDATORY before applying new migrations
- Keep tested restore procedure in separate runbook (below)
- Schedule maintenance window for migrations

### Pre-Migration Snapshot Procedure

```bash
# 1. Create pre-migration snapshot
DATE=$(date +%Y-%m-%d_%H%M)
PGPASSWORD=novapass pg_dump -h localhost -p 5433 -U nova -d nova_aos \
  -Fc -f "/backups/pre_migration_${DATE}.dump"

# 2. Verify dump
pg_restore --list "/backups/pre_migration_${DATE}.dump" | head -20

# 3. Record in migration log
echo "${DATE}: Pre-migration snapshot for migration XXX" >> /backups/migration_log.txt

# 4. Test restore (on staging DB)
PGPASSWORD=novapass createdb -h localhost -p 5433 -U nova nova_aos_restore_test
PGPASSWORD=novapass pg_restore -h localhost -p 5433 -U nova \
  -d nova_aos_restore_test "/backups/pre_migration_${DATE}.dump"

# 5. Verify restore
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos_restore_test \
  -c "SELECT COUNT(*) FROM m10_recovery.outbox"

# 6. Clean up test DB
PGPASSWORD=novapass dropdb -h localhost -p 5433 -U nova nova_aos_restore_test
```

### Rollback Procedure

If migration fails and rollback is needed:

```bash
# 1. Stop services
sudo systemctl stop m10-maintenance.timer
sudo systemctl stop m10-metrics-collector.service

# 2. Drop failed schema changes (if partial)
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos \
  -c "DROP SCHEMA m10_recovery CASCADE;"

# 3. Restore from pre-migration snapshot
PGPASSWORD=novapass pg_restore -h localhost -p 5433 -U nova \
  -d nova_aos --clean "/backups/pre_migration_YYYY-MM-DD_HHMM.dump"

# 4. Verify restore
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos \
  -c "SELECT COUNT(*) FROM m10_recovery.outbox"

# 5. Restart services
sudo systemctl start m10-maintenance.timer
sudo systemctl start m10-metrics-collector.service
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-09 | Added risk mitigations section (4 risks + procedures) |
| 2025-12-09 | Added metrics collector operations section |
| 2025-12-09 | Added operational discipline section (5 principles) |
| 2025-12-09 | Initial creation for PIN-058 simplification |
