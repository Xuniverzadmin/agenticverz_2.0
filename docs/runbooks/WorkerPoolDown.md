# WorkerPoolDown Runbook

**Severity:** Critical
**Alert:** `WorkerPoolDown`
**Condition:** `nova_worker_pool_size == 0` for 1 minute

## What It Means

The worker pool process is down or not reporting metrics. No runs can be processed while the worker is down.

## Impact

- Queued runs will not be processed
- Queue depth will increase
- Goals submitted to agents will remain in `queued` status indefinitely

## First Response (< 1 minute)

### 1. Check worker container status

```bash
docker compose ps | grep worker
```

Expected: `nova_worker` should show `Up`

### 2. Check worker logs

```bash
docker compose logs worker --tail 100
```

Look for:
- Python exceptions or tracebacks
- OOM (out of memory) kills
- Database connection errors
- Signal handling messages

### 3. Check backend health

```bash
curl -s http://127.0.0.1:8000/health | jq .
```

## Quick Recovery

### Restart the worker

```bash
docker compose restart worker
```

### If restart fails, recreate

```bash
docker compose up -d --force-recreate worker
```

### Check if recovered

```bash
docker compose logs worker --tail 20
curl -s http://127.0.0.1:8000/metrics | grep nova_worker_pool_size
```

## Deeper Investigation

### Check system resources

```bash
# Memory
free -h

# Disk
df -h

# Check for OOM kills
dmesg | grep -i "killed process" | tail -10
```

### Check database connectivity

```bash
docker compose exec db psql -U nova -d nova_aos -c "SELECT 1;"
```

### Check queue state

```bash
curl -s http://127.0.0.1:8000/metrics | grep nova_runs_queued
```

## Post-Incident

1. List failed runs during outage:
   ```bash
   API_KEY=your_key ./scripts/list-failed.sh
   ```

2. Rerun any failed runs:
   ```bash
   API_KEY=your_key ./scripts/rerun.sh <run_id> "recovery after worker outage"
   ```

3. Check provenance for runs that may need manual review

## Escalation

- If worker won't start after 15 minutes: Escalate to infrastructure team
- If database connection issues: Check PostgreSQL logs and disk space
- If recurring: Review worker memory limits and concurrency settings

## Related Alerts

- `QueueDepthCritical` - may fire if worker is down for extended period
- `BackendDown` - check if backend is also affected
