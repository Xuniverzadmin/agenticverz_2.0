# NoRunsProcessed Runbook

**Severity:** Warning
**Alert:** `NoRunsProcessed`
**Condition:** `sum(increase(nova_runs_total[15m])) == 0` for 5 minutes

## What It Means

No runs have been processed in the last 15 minutes. This could indicate:
1. No incoming work (normal during low-activity periods)
2. Worker is stuck or not processing
3. Upstream ingestion is failing

## Impact

- May be normal during off-hours or maintenance
- If unexpected, indicates processing pipeline issue
- Queued runs may be backing up

## First Response (< 1 minute)

### 1. Check if there's work to process

```bash
curl -s http://127.0.0.1:8000/metrics | grep nova_runs_queued
```

- If `nova_runs_queued == 0`: No work pending (alert may be benign)
- If `nova_runs_queued > 0`: Work exists but not being processed (investigate)

### 2. Check worker status

```bash
docker compose ps | grep worker
docker compose logs worker --tail 50
```

### 3. Check recent run activity

```bash
curl -s http://127.0.0.1:8000/metrics | grep nova_runs_total
```

## Decision Tree

```
Is nova_runs_queued == 0?
├── YES → No work pending. Check upstream ingestion or this may be normal.
└── NO (queue > 0) → Work exists but not processing
    ├── Is worker running?
    │   ├── YES → Worker may be stuck. Check logs, restart if needed.
    │   └── NO → See WorkerPoolDown runbook
    └── Is backend healthy?
        ├── YES → Focus on worker
        └── NO → See BackendDown runbook
```

## Quick Recovery

### If queue has items but worker isn't processing

```bash
# Restart worker
docker compose restart worker

# Wait 30 seconds, then check
sleep 30
curl -s http://127.0.0.1:8000/metrics | grep nova_runs
```

### If queue is empty (check upstream)

```bash
# Check if agents exist and can receive goals
API_KEY=your_key curl -s http://127.0.0.1:8000/agents -H "X-AOS-Key: $API_KEY" | jq .

# Test submitting a goal
API_KEY=your_key curl -s -X POST "http://127.0.0.1:8000/agents/<agent_id>/goals" \
  -H "Content-Type: application/json" \
  -H "X-AOS-Key: $API_KEY" \
  -d '{"goal": "health check test"}' | jq .
```

## When This Alert Is Expected

- During scheduled maintenance windows
- Off-hours if no automated jobs are running
- After initial deployment before traffic is routed
- During testing/development with low activity

Consider silencing during known low-activity periods:

```bash
# Create 6-hour silence
./scripts/test-alerts.sh status  # to see current alerts
# Then use Alertmanager API to create silence
```

## Post-Incident

1. Review logs for the quiet period:
   ```bash
   docker compose logs worker --since "15m ago"
   docker compose logs backend --since "15m ago"
   ```

2. Check if any runs failed silently:
   ```bash
   API_KEY=your_key ./scripts/list-failed.sh
   ```

## Escalation

- If queue is growing and worker is running: Check for deadlocks, escalate to dev team
- If upstream ingestion is failing: Escalate to the service feeding goals
- If recurring unexpectedly: Review system capacity and job scheduling

## Related Alerts

- `WorkerPoolDown` - worker not running
- `QueueDepthWarning` - queue building up (may fire after this)
