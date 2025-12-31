# Worker Pool Production Deployment Runbook

**Date:** 2025-12-30
**Risk Level:** MEDIUM
**Downtime:** Zero (rolling deployment)
**Reference:** PIN-052

---

## Overview

The AOS Worker Pool handles asynchronous run execution with:
- Configurable concurrency via ThreadPoolExecutor
- Batch polling for queued runs
- Graceful shutdown on SIGTERM/SIGINT
- Automatic retry with backoff

---

## Configuration Parameters

| Parameter | Env Variable | Default | Description |
|-----------|-------------|---------|-------------|
| Poll Interval | `WORKER_POLL_INTERVAL` | 2.0s | Seconds between queue checks |
| Concurrency | `WORKER_CONCURRENCY` | 4 | Max parallel run executions |
| Batch Size | `WORKER_BATCH_SIZE` | 8 | Max runs fetched per poll |

### Production Recommended Settings

```bash
# For high-throughput environments
WORKER_POLL_INTERVAL=1.0
WORKER_CONCURRENCY=8
WORKER_BATCH_SIZE=16

# For resource-constrained environments
WORKER_POLL_INTERVAL=5.0
WORKER_CONCURRENCY=2
WORKER_BATCH_SIZE=4
```

---

## Pre-Deployment Checklist

### 1. Verify Current Worker State

```bash
# Check running worker containers
docker compose ps nova_worker

# Check worker logs for errors
docker compose logs nova_worker --tail 50 | grep -E "(error|ERROR|exception)"

# Check active runs in database
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "SELECT status, COUNT(*) FROM runs GROUP BY status;"
```

### 2. Check Queue Backlog

```bash
# Count queued runs
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "SELECT COUNT(*) as queued FROM runs WHERE status = 'queued';"

# Check oldest queued run
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "SELECT id, created_at, agent_id FROM runs WHERE status = 'queued' ORDER BY created_at ASC LIMIT 5;"
```

### 3. Verify Database Connectivity

```bash
# Test connection from worker container
docker compose exec nova_worker python3 -c "
from app.db import engine
from sqlmodel import Session, select
from app.db import Run
with Session(engine) as s:
    count = s.exec(select(Run).limit(1)).first()
    print('DB connected:', count is not None or 'empty but connected')
"
```

---

## Deployment Steps

### Step 1: Update Configuration (if changing)

```bash
# Edit .env or docker-compose.yml
# Example: Increase concurrency
echo "WORKER_CONCURRENCY=8" >> /root/agenticverz2.0/.env
```

### Step 2: Deploy with Rolling Update

```bash
cd /root/agenticverz2.0

# Build new worker image
docker compose build nova_worker

# Stop old worker gracefully (waits for running tasks)
docker compose stop nova_worker

# Wait for graceful shutdown
sleep 10

# Start new worker
docker compose up -d nova_worker

# Verify startup
docker compose logs nova_worker --tail 20
```

### Step 3: Verify Deployment

```bash
# Check worker is running
docker compose ps nova_worker

# Verify pool started
docker compose logs nova_worker 2>&1 | grep "worker_pool_starting"

# Check concurrency
docker compose logs nova_worker 2>&1 | grep "concurrency"

# Verify skills loaded
docker compose logs nova_worker 2>&1 | grep "skills_initialized"
```

---

## Graceful Shutdown Verification

The worker supports graceful shutdown. Verify it works:

```bash
# Send SIGTERM (graceful)
docker compose kill -s SIGTERM nova_worker

# Watch logs - should see:
# - "worker_pool_signal_received"
# - "worker_pool_shutting_down"
# - "worker_pool_stopped" with graceful: True
docker compose logs nova_worker --tail 20

# Restart after verification
docker compose up -d nova_worker
```

---

## Monitoring

### Key Metrics

| Metric | Alert Threshold | Description |
|--------|-----------------|-------------|
| `nova_worker_pool_size` | N/A | Current pool size |
| `nova_runs_queued` | > 100 | Queue depth |
| `nova_run_duration_seconds` | p99 > 300s | Run latency |
| `nova_worker_errors_total` | > 10/min | Worker errors |

### Log Patterns to Monitor

```bash
# Successful dispatch
docker compose logs nova_worker 2>&1 | grep "run_dispatched"

# Errors
docker compose logs nova_worker 2>&1 | grep -E "(error|ERROR|exception)"

# Poll errors (needs investigation)
docker compose logs nova_worker 2>&1 | grep "worker_pool_poll_error"
```

---

## Scaling Procedures

### Scale Up (More Capacity)

```bash
# Option 1: Increase concurrency (recommended first)
export WORKER_CONCURRENCY=12
docker compose up -d --build nova_worker

# Option 2: Add more worker replicas (if needed)
docker compose up -d --scale nova_worker=3
```

### Scale Down

```bash
# Reduce concurrency
export WORKER_CONCURRENCY=2
docker compose up -d --build nova_worker

# Or reduce replicas (graceful - completes running tasks)
docker compose up -d --scale nova_worker=1
```

---

## Troubleshooting

### Issue: Worker Not Processing Runs

```bash
# 1. Check worker is running
docker compose ps nova_worker

# 2. Check database connection
docker compose logs nova_worker 2>&1 | grep -E "(DATABASE|connection)"

# 3. Check for queued runs
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "SELECT * FROM runs WHERE status = 'queued' LIMIT 5;"

# 4. Check worker is polling
docker compose logs nova_worker --tail 100 2>&1 | grep -E "(poll|fetch)"
```

### Issue: Runs Stuck in "running" State

```bash
# Find stuck runs (running > 30 minutes)
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "SELECT id, started_at, agent_id FROM runs
   WHERE status = 'running'
   AND started_at < now() - interval '30 minutes';"

# Reset stuck runs to queued (use with caution)
PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c \
  "UPDATE runs SET status = 'queued', started_at = NULL
   WHERE status = 'running'
   AND started_at < now() - interval '60 minutes'
   RETURNING id;"
```

### Issue: High Queue Backlog

```bash
# Check queue growth rate
watch -n 5 "PGPASSWORD=$PGPASSWORD psql -h $PGHOST -U $PGUSER -d $PGDATABASE -c 'SELECT COUNT(*) FROM runs WHERE status = \\'queued\\';'"

# Temporarily increase concurrency
export WORKER_CONCURRENCY=16
export WORKER_BATCH_SIZE=32
docker compose up -d --build nova_worker

# Monitor drain rate
docker compose logs -f nova_worker 2>&1 | grep "run_dispatched"
```

### Issue: Worker Crashes on Startup

```bash
# Check for import errors
docker compose logs nova_worker 2>&1 | head -50

# Common causes:
# - Missing DATABASE_URL
# - Invalid skill configurations
# - Missing dependencies

# Test startup manually
docker compose run --rm nova_worker python3 -m app.worker.pool
```

---

## Rollback Procedure

If issues occur after deployment:

```bash
# Stop new worker
docker compose stop nova_worker

# Revert to previous image (if tagged)
docker compose pull nova_worker:previous
docker compose up -d nova_worker

# Or rebuild from previous commit
git checkout HEAD~1 -- backend/app/worker/
docker compose up -d --build nova_worker
```

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Platform Engineer | | | |
| SRE | | | |
| Tech Lead | | | |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-30 | Initial runbook created |
