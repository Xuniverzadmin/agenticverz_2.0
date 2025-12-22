# M4 Workflow Engine Runbook

**Version:** 1.0
**Last Updated:** 2025-12-02
**Owner:** AOS Platform Team

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Health Checks](#health-checks)
4. [Common Operations](#common-operations)
5. [Incident Response](#incident-response)
6. [Troubleshooting](#troubleshooting)
7. [Tabletop Exercise Checklist](#tabletop-exercise-checklist)

---

## Overview

The M4 Workflow Engine provides deterministic, replayable workflow execution with:
- Multi-step workflow orchestration
- Checkpoint-based state persistence
- Golden file recording for replay verification
- Policy enforcement (budgets, rate limits)
- Shadow replay validation

### Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| WorkflowEngine | Orchestrates workflow execution | `backend/app/workflow/engine.py` |
| CheckpointStore | Persists workflow state | `backend/app/workflow/checkpoint.py` |
| GoldenRecorder | Records deterministic outputs | `backend/app/workflow/golden.py` |
| PolicyEnforcer | Enforces budgets/limits | `backend/app/workflow/policies.py` |
| PlannerSandbox | Safe planner execution | `backend/app/workflow/planner_sandbox.py` |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Workflow Engine                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────────┐  ┌────────────────┐        │
│  │ Planner  │→ │ StepExecutor │→ │ GoldenRecorder │        │
│  │ Sandbox  │  │              │  │                │        │
│  └──────────┘  └──────────────┘  └────────────────┘        │
│       ↓              ↓                   ↓                  │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────┐        │
│  │ Policy   │  │ Checkpoint   │  │ Prometheus     │        │
│  │ Enforcer │  │ Store        │  │ Metrics        │        │
│  └──────────┘  └──────────────┘  └────────────────┘        │
└─────────────────────────────────────────────────────────────┘
         ↓                ↓                   ↓
    ┌─────────┐    ┌───────────┐      ┌────────────┐
    │  Redis  │    │ PostgreSQL│      │ Golden Dir │
    └─────────┘    └───────────┘      └────────────┘
```

---

## Health Checks

### 1. Service Status

```bash
# Check all services
docker compose ps

# Check backend health
curl -sf http://localhost:8000/health | jq .

# Check worker status
curl -sf http://localhost:8000/workers/status | jq .
```

### 2. Shadow Run Status

```bash
# Quick status check
/root/agenticverz2.0/scripts/stress/check_shadow_status.sh

# 4-hour sanity check
/root/agenticverz2.0/scripts/stress/shadow_sanity_check.sh

# Watch live logs
tail -f /var/lib/aos/shadow_24h_*.log
```

### 3. Database Connectivity

```bash
# PostgreSQL
PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "SELECT 1;"

# Redis
redis-cli ping
```

### 4. Prometheus Metrics

```bash
# Check if Prometheus is up
curl -sf http://localhost:9090/-/ready

# Check workflow metrics
curl -sf 'http://localhost:9090/api/v1/query?query=workflow_executions_total' | jq .

# Check for firing alerts
curl -sf 'http://localhost:9090/api/v1/alerts' | jq '.data.alerts[] | select(.state=="firing")'
```

---

## Common Operations

### Start Shadow Simulation

```bash
# Quick test (3 cycles)
/root/agenticverz2.0/scripts/stress/run_shadow_simulation.sh --quick --verbose

# Full 24-hour run
export SHADOW_HOOK="https://webhook.site/<your-uuid>"
nohup /root/agenticverz2.0/scripts/stress/run_shadow_simulation.sh \
    --hours 24 --workers 3 --verbose \
    > /var/lib/aos/shadow_24h_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

### Analyze Shadow Results

```bash
# Summarize shadow directory
python3 /root/agenticverz2.0/scripts/stress/golden_diff_debug.py \
    --summary-dir /tmp/shadow_simulation_* \
    --output /tmp/shadow_summary.json

# Compare two golden files
python3 /root/agenticverz2.0/scripts/stress/golden_diff_debug.py \
    --golden-a /path/to/golden_a.json \
    --golden-b /path/to/golden_b.json \
    --verbose
```

### Rotate Golden HMAC Key

```bash
# Generate new key
NEW_KEY=$(openssl rand -hex 32)
echo "New HMAC Key: $NEW_KEY"

# Update environment
export GOLDEN_HMAC_SECRET="$NEW_KEY"

# Resign existing golden files
python3 -c "
from pathlib import Path
import json
import hmac
import hashlib

GOLDEN_DIR = Path('/var/lib/aos/golden')
NEW_SECRET = '$NEW_KEY'.encode()

for f in GOLDEN_DIR.glob('*.json'):
    data = json.loads(f.read_text())
    content = json.dumps({k:v for k,v in data.items() if k != 'signature'}, sort_keys=True)
    data['signature'] = hmac.new(NEW_SECRET, content.encode(), hashlib.sha256).hexdigest()
    f.write_text(json.dumps(data, indent=2))
    print(f'Resigned: {f.name}')
"
```

### Archive Golden Files

```bash
# Create archive
ARCHIVE_NAME="golden_archive_$(date +%Y%m%d_%H%M%S).tgz"
tar -czf "/var/lib/aos/archives/$ARCHIVE_NAME" -C /var/lib/aos/golden .

# Verify archive
tar -tzf "/var/lib/aos/archives/$ARCHIVE_NAME" | head -20

# Clean old golden files (keep last 7 days)
find /var/lib/aos/golden -name "*.json" -mtime +7 -delete
```

---

## Incident Response

### Mismatch Detected During Shadow Run

**Severity:** HIGH
**Response Time:** Immediate

1. **Stop new workflows:**
   ```bash
   /root/agenticverz2.0/scripts/ops/disable-workflows.sh enable
   ```

2. **Collect artifacts:**
   ```bash
   INCIDENT_DIR="/tmp/incident_$(date +%s)"
   mkdir -p "$INCIDENT_DIR"

   # Copy shadow artifacts
   cp -r /tmp/shadow_simulation_* "$INCIDENT_DIR/" 2>/dev/null || true
   cp /var/lib/aos/shadow_24h_*.log "$INCIDENT_DIR/" 2>/dev/null || true

   # Create tarball
   tar -czf "$INCIDENT_DIR.tgz" "$INCIDENT_DIR"
   echo "Artifacts: $INCIDENT_DIR.tgz"
   ```

3. **Analyze mismatch:**
   ```bash
   python3 /root/agenticverz2.0/scripts/stress/golden_diff_debug.py \
       --summary-dir /tmp/shadow_simulation_* \
       --verbose \
       --output "$INCIDENT_DIR/analysis.json"
   ```

4. **Common root causes:**
   - Seed mismatch → Check seed propagation in skill
   - Volatile field leak → Add field to VOLATILE_FIELDS list
   - Unseeded RNG → Replace `random.random()` with seeded version
   - External call variation → Mock or determinize external call

5. **Re-run targeted test:**
   ```bash
   # Run 10 iterations of failing workflow type
   python3 -c "
   import asyncio
   from backend.app.workflow.engine import WorkflowEngine

   async def test():
       engine = WorkflowEngine()
       for i in range(10):
           result = await engine.run(workflow_type='<failing_type>', seed=12345+i)
           print(f'Iteration {i}: {result.workflow_hash}')

   asyncio.run(test())
   "
   ```

6. **Re-enable after fix:**
   ```bash
   /root/agenticverz2.0/scripts/ops/disable-workflows.sh disable
   ```

### Checkpoint Store Failure

**Severity:** MEDIUM
**Response Time:** 15 minutes

1. **Check PostgreSQL:**
   ```bash
   docker compose logs db --tail 100
   PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "SELECT COUNT(*) FROM checkpoints;"
   ```

2. **Check for deadlocks:**
   ```bash
   PGPASSWORD=novapass psql -h localhost -p 5433 -U nova -d nova_aos -c "
   SELECT pid, state, query, wait_event_type, wait_event
   FROM pg_stat_activity
   WHERE state != 'idle'
   ORDER BY query_start;
   "
   ```

3. **Restart if needed:**
   ```bash
   docker compose restart db
   sleep 10
   docker compose restart backend worker
   ```

### Budget Store (Redis) Failure

**Severity:** MEDIUM
**Response Time:** 15 minutes

1. **Check Redis:**
   ```bash
   redis-cli ping
   redis-cli info memory
   redis-cli dbsize
   ```

2. **Check budget keys:**
   ```bash
   redis-cli keys "budget:*" | head -20
   redis-cli keys "rate:*" | head -20
   ```

3. **Restart Redis:**
   ```bash
   docker compose restart redis
   ```

---

## Troubleshooting

### Workflow Execution Slow

1. Check step durations in logs
2. Check external service latency
3. Check Redis/PostgreSQL connection pool
4. Review Prometheus `workflow_step_duration_seconds` histogram

### Golden File Signature Invalid

1. Verify HMAC secret matches
2. Check for content modification after signing
3. Re-sign with `golden_diff_debug.py` analysis

### Checkpoint Resume Fails

1. Check checkpoint exists in database
2. Verify version compatibility
3. Check for schema migrations

---

## Tabletop Exercise Checklist

Use this checklist for runbook tabletop exercises.

### Pre-Exercise Setup

- [ ] Ensure test environment is isolated
- [ ] Backup production data if testing on prod-like env
- [ ] Notify team of exercise window

### Exercise Steps

| # | Step | Command | Expected Result | Actual | Pass? |
|---|------|---------|-----------------|--------|-------|
| 1 | Check service health | `curl http://localhost:8000/health` | `{"status": "healthy"}` | | |
| 2 | Run quick shadow test | `./scripts/stress/run_shadow_simulation.sh --quick` | 0 mismatches | | |
| 3 | Check sanity script | `./scripts/stress/shadow_sanity_check.sh` | All checks pass | | |
| 4 | Simulate emergency stop | `./scripts/ops/disable-workflows.sh enable` | Stop file created | | |
| 5 | Verify stop status | `./scripts/ops/disable-workflows.sh status` | Status: STOPPED | | |
| 6 | Re-enable workflows | `./scripts/ops/disable-workflows.sh disable` | Stop file removed | | |
| 7 | Run golden diff | `python3 scripts/stress/golden_diff_debug.py --summary-dir /tmp/shadow_*` | JSON summary | | |
| 8 | Check Prometheus alerts | `curl http://localhost:9090/api/v1/alerts` | No firing alerts | | |
| 9 | Verify checkpoint DB | `psql -c "SELECT COUNT(*) FROM checkpoints"` | Row count returned | | |
| 10 | Check Redis connectivity | `redis-cli ping` | PONG | | |

### Post-Exercise

- [ ] Document any issues found
- [ ] Update runbook if procedures were unclear
- [ ] Sign off on exercise completion

### Sign-Off

```
Exercise Date: ________________
Conducted By:  ________________
Result:        [ ] PASS  [ ] FAIL
Notes:
_______________________________________________
_______________________________________________

Signature: ________________  Date: ____________
```

---

## References

- [PIN-013: M4 Workflow Engine Completion](../memory-pins/PIN-013-m4-workflow-engine-completion.md)
- [PIN-014: M4 Technical Review](../memory-pins/PIN-014-m4-technical-review.md)
- [PIN-015: M4 Validation & Maturity Gates](../memory-pins/PIN-015-m4-validation-maturity-gates.md)
- [Determinism Spec](../../backend/app/specs/determinism_and_replay.md)
- [Error Taxonomy](../../backend/app/specs/error_taxonomy.md)
