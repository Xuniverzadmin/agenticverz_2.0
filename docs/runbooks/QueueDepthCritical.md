# QueueDepthCritical Runbook

**Severity:** Critical
**Alert:** `QueueDepthCritical`
**Condition:** `nova_runs_queued > 50` for 5 minutes

## What It Means

The run queue has more than 50 items backed up for at least 5 minutes. This indicates the system cannot keep up with incoming work.

## Impact

- Significant delay in goal processing
- Users/systems waiting for run completion will timeout or fail
- May cascade to upstream systems

## First Response (< 1 minute)

### 1. Check current queue depth

```bash
curl -s http://127.0.0.1:8000/metrics | grep nova_runs_queued
```

### 2. Check worker capacity

```bash
curl -s http://127.0.0.1:8000/metrics | grep nova_worker_pool_size
docker compose ps | grep worker
```

### 3. Check processing rate

```bash
curl -s http://127.0.0.1:8000/metrics | grep nova_runs_total
```

## Quick Recovery

### 1. Scale workers (if possible)

```bash
# Increase worker concurrency
docker compose down worker
# Edit docker-compose.yml: WORKER_CONCURRENCY: "8"
docker compose up -d worker
```

### 2. Check for stuck runs

```bash
# Look for runs in 'running' state for too long
API_KEY=your_key curl -s "http://127.0.0.1:8000/admin/failed-runs" -H "X-AOS-Key: $API_KEY" | jq .
```

### 3. Identify slow skills

```bash
curl -s http://127.0.0.1:8000/metrics | grep nova_skill_duration
```

If a specific skill is slow, it may be causing backlog.

## Root Cause Analysis

### Traffic spike?
- Check if incoming goal rate increased
- Review upstream systems for batch jobs or incidents

### Worker capacity issue?
- Workers may be underpowered
- Skills may be taking longer than expected
- Database queries may be slow

### External dependency slow?
- HTTP skills calling slow external APIs
- Calendar/email providers having issues

## Mitigation Options

1. **Increase concurrency** - More parallel workers
2. **Throttle incoming** - Rate limit goal submissions temporarily
3. **Prioritize** - If supported, process high-priority runs first
4. **Scale horizontally** - Add more worker containers

## Post-Incident

1. Review what caused the spike
2. Tune worker concurrency based on observed throughput
3. Consider adding auto-scaling rules
4. Update capacity planning

## Escalation

- If cannot recover within 15 minutes: Page infrastructure team
- If external dependency: Contact vendor/check status page
- If recurring: Escalate for capacity planning review

## Thresholds

| Level | Queue Depth | Duration | Action |
|-------|-------------|----------|--------|
| Warning | > 20 | 15m | Monitor, prepare to scale |
| Critical | > 50 | 5m | Immediate action required |
