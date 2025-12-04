# Workflow Recovery Runbook

**Version:** 1.0.0
**Last Updated:** 2025-12-01
**Severity Levels:** P0 (Critical), P1 (High), P2 (Medium)

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Reference](#quick-reference)
3. [Incident Response](#incident-response)
4. [Recovery Procedures](#recovery-procedures)
5. [Emergency Controls](#emergency-controls)
6. [Golden File Recovery](#golden-file-recovery)
7. [Monitoring & Alerts](#monitoring--alerts)

---

## Overview

This runbook covers recovery procedures for the AOS Workflow Engine v1:

- **Checkpoint Store:** PostgreSQL-backed persistence for workflow resume
- **Golden File Pipeline:** HMAC-signed replay verification
- **Policy Enforcement:** Budget and rate limit controls
- **Planner Sandbox:** Security validation for planner outputs

---

## Quick Reference

### Emergency Stop

```bash
# Enable emergency stop (blocks all workflow execution)
export WORKFLOW_EMERGENCY_STOP=true
systemctl restart nova_worker

# Disable emergency stop
export WORKFLOW_EMERGENCY_STOP=false
systemctl restart nova_worker
```

### CLI Tool Quick Reference

```bash
# Inspect a workflow run (checkpoint + golden + recovery hints)
aos-workflow inspect --run <run_id>

# List all running workflows
aos-workflow list-running

# View last N golden events
aos-workflow golden-tail --run <run_id> --lines 30

# Show workflow spec statistics
aos-workflow stats --spec <spec_id>

# Local replay from golden file
aos-workflow replay-local --run <run_id>
```

### Inspect Running Workflows

```bash
# Using CLI tool
aos-workflow list-running
```

```sql
-- List running workflows
SELECT run_id, workflow_id, next_step_index, updated_at, version
FROM workflow_checkpoints
WHERE status = 'running'
ORDER BY updated_at DESC
LIMIT 50;

-- Find stale workflows (running > 1 hour)
SELECT run_id, workflow_id, next_step_index,
       EXTRACT(EPOCH FROM (NOW() - updated_at))/60 AS minutes_stale
FROM workflow_checkpoints
WHERE status = 'running'
  AND updated_at < NOW() - INTERVAL '1 hour';
```

### Force Resume from Checkpoint

```bash
# CLI tool (if available)
aos workflow resume --run-id <run_id>

# Direct API call
curl -X POST http://localhost:8000/workflows/<run_id>/resume \
  -H "Authorization: Bearer $AOS_API_KEY"
```

---

## Incident Response

### Workflow Failure Rate High (P1)

**Alert:** `WorkflowFailureRateHigh`
**Threshold:** >10% failures in 5 minutes

**Steps:**

1. Check recent error codes:
   ```sql
   SELECT status, COUNT(*)
   FROM workflow_checkpoints
   WHERE updated_at > NOW() - INTERVAL '5 minutes'
   GROUP BY status;
   ```

2. Check for common error patterns:
   ```bash
   grep "POLICY_VIOLATION\|SKILL_NOT_FOUND\|EXECUTION_ERROR" /var/log/nova/worker.log | tail -50
   ```

3. If budget-related:
   - Check `PolicyEnforcer` thresholds
   - Review recent step costs

4. If skill-related:
   - Check skill registry
   - Verify external service availability

### Replay Failures (P0)

**Alert:** `WorkflowReplayFailure`
**Threshold:** Any failures in 5 minutes
**Runbook Link:** #replay-failure

**This is critical - determinism may be compromised!**

**Steps:**

1. **Immediately** inspect the failing run:
   ```bash
   aos-workflow inspect --run <run_id>
   ```

2. Check golden file for unexpected events:
   ```bash
   aos-workflow golden-tail --run <run_id> --lines 50

   # Look for external calls that may have leaked
   grep -i "http\|external" /tmp/golden/<run_id>.steps.jsonl | head -20
   ```

3. Compare budget snapshot in golden header:
   ```bash
   head -1 /tmp/golden/<run_id>.steps.jsonl | jq .data.budget_snapshot
   ```

4. SQL diagnostics:
   ```sql
   -- Find recent failed replays
   SELECT run_id, workflow_id, status, last_result_hash, updated_at
   FROM workflow_checkpoints
   WHERE status = 'failed'
   ORDER BY updated_at DESC
   LIMIT 20;

   -- Check for hash mismatches (indicates non-determinism)
   SELECT run_id, last_result_hash, version
   FROM workflow_checkpoints
   WHERE updated_at > NOW() - INTERVAL '1 hour'
   ORDER BY updated_at DESC;
   ```

5. Check for non-deterministic code:
   - `datetime.now()` without timezone
   - `random.*` without seed
   - Unordered dict iterations

6. If seed mismatch: Verify `GOLDEN_SECRET` is set consistently across replicas

7. After investigation, if safe to proceed, re-enable workflows:
   ```bash
   export WORKFLOW_EMERGENCY_STOP=false
   systemctl restart nova_worker
   ```

### Checkpoint Save Failures (P0)

**Alert:** `WorkflowCheckpointSaveFailure`
**Threshold:** Any failures in 5 minutes
**Runbook Link:** #checkpoint-failure

**Steps:**

1. Check PostgreSQL connectivity:
   ```bash
   pg_isready -h localhost -p 5433
   psql -h localhost -d nova_aos -c "SELECT 1;"
   ```

2. Verify disk space:
   ```bash
   df -h /var/lib/postgresql
   ```

3. Check for blocking queries:
   ```sql
   SELECT pid, query, state, wait_event_type, wait_event
   FROM pg_stat_activity
   WHERE state = 'active'
   AND query NOT LIKE '%pg_stat_activity%';

   -- Check for locks
   SELECT l.pid, l.locktype, l.mode, l.granted, a.query
   FROM pg_locks l
   JOIN pg_stat_activity a ON l.pid = a.pid
   WHERE l.relation = 'workflow_checkpoints'::regclass;
   ```

4. Check for version conflicts:
   ```bash
   grep "CheckpointVersionConflictError" /var/log/nova/worker.log | tail -20
   ```

5. Check connection pool:
   ```sql
   SELECT count(*) FROM pg_stat_activity
   WHERE datname = 'nova_aos';
   ```

6. If version conflicts are frequent:
   - Review concurrent worker count
   - Consider implementing distributed locking

### Checkpoint Latency Critical (P0)

**Alert:** `WorkflowCheckpointLatencyCritical`
**Threshold:** p99 > 1s for 2 minutes
**Runbook Link:** #checkpoint-slow

**Steps:**

1. Check current checkpoint metrics:
   ```bash
   curl -s localhost:8000/metrics | grep workflow_checkpoint_duration
   ```

2. Check database load:
   ```sql
   SELECT * FROM pg_stat_activity WHERE state = 'active';
   ```

3. Find slow checkpoint operations:
   ```sql
   SELECT run_id,
          EXTRACT(EPOCH FROM (updated_at - created_at)) as duration_sec,
          pg_column_size(step_outputs_json) as payload_bytes
   FROM workflow_checkpoints
   ORDER BY duration_sec DESC NULLS LAST
   LIMIT 20;
   ```

4. Check index health:
   ```sql
   SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
   FROM pg_stat_user_indexes
   WHERE tablename = 'workflow_checkpoints';
   ```

5. If payload too large: Enable batch checkpointing, reduce step output size
6. If index bloat: `REINDEX workflow_checkpoints;`
7. If DB resource-constrained: Scale database vertically
8. Consider emergency workflow pause if impact is severe

### Golden File Mismatch (P1)

**Alert:** `WorkflowGoldenFileMismatch`

**Steps:**

1. Locate the mismatched golden file:
   ```bash
   ls -lt /var/lib/nova/golden/*.steps.jsonl | head -5
   ```

2. Verify signature:
   ```bash
   python -c "
   from app.workflow.golden import GoldenRecorder
   recorder = GoldenRecorder('/var/lib/nova/golden', secret='$GOLDEN_SECRET')
   print(recorder.verify_golden('<filepath>'))
   "
   ```

3. If signature invalid (tampering detected):
   - Check for unauthorized file access
   - Restore from backup
   - Rotate `GOLDEN_SECRET`

4. If signature valid but content differs:
   - Compare with canonical comparison
   - Check for non-deterministic operations

---

## Recovery Procedures

### Resume Workflow from Last Checkpoint

```python
from app.workflow.checkpoint import CheckpointStore
from app.workflow.engine import WorkflowEngine, WorkflowSpec

async def resume_workflow(run_id: str):
    store = CheckpointStore()
    checkpoint = await store.load(run_id)

    if not checkpoint:
        print(f"No checkpoint found for {run_id}")
        return

    print(f"Resuming from step {checkpoint.next_step_index}")
    print(f"Previous outputs: {list(checkpoint.step_outputs.keys())}")

    # Load original spec and resume
    engine = WorkflowEngine(registry, store)
    result = await engine.run(
        spec=load_spec(checkpoint.workflow_id),
        run_id=run_id,
        seed=original_seed,  # Must use original seed!
    )
    return result
```

### Manual Checkpoint Update

**Use with caution - can break replay!**

```sql
-- Update checkpoint status (e.g., mark as failed)
UPDATE workflow_checkpoints
SET status = 'failed',
    updated_at = NOW(),
    version = version + 1
WHERE run_id = '<run_id>'
  AND version = <expected_version>;

-- Delete stuck checkpoint
DELETE FROM workflow_checkpoints
WHERE run_id = '<run_id>'
  AND status = 'running'
  AND updated_at < NOW() - INTERVAL '2 hours';
```

### Restore Golden Files from Backup

```bash
# List available backups
ls -lt /var/backups/nova/golden/

# Restore specific date
tar -xzf /var/backups/nova/golden/golden_2025-12-01.tar.gz \
    -C /var/lib/nova/golden/

# Re-sign restored files (if key unchanged)
python -c "
import os
from app.workflow.golden import GoldenRecorder
recorder = GoldenRecorder('/var/lib/nova/golden', secret='$GOLDEN_SECRET')
for f in os.listdir('/var/lib/nova/golden'):
    if f.endswith('.steps.jsonl'):
        recorder.sign_golden(os.path.join('/var/lib/nova/golden', f))
        print(f'Re-signed: {f}')
"
```

### Rotate Golden Secret

**When:** Suspected secret exposure, routine rotation

```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -hex 32)

# 2. Re-sign all golden files with new secret
python -c "
import os
from app.workflow.golden import GoldenRecorder
old_recorder = GoldenRecorder('/var/lib/nova/golden', secret='$GOLDEN_SECRET')
new_recorder = GoldenRecorder('/var/lib/nova/golden', secret='$NEW_SECRET')

for f in os.listdir('/var/lib/nova/golden'):
    if f.endswith('.steps.jsonl'):
        filepath = os.path.join('/var/lib/nova/golden', f)
        # Verify with old secret first
        if old_recorder.verify_golden(filepath):
            new_recorder.sign_golden(filepath)
            print(f'Re-signed: {f}')
        else:
            print(f'WARN: Could not verify {f} with old secret')
"

# 3. Update secret in environment
echo "GOLDEN_SECRET=$NEW_SECRET" >> /etc/nova/secrets

# 4. Restart workers
systemctl restart nova_worker
```

---

## Emergency Controls

### Enable/Disable Workflow Engine

```bash
# Disable (blocks new workflows, running ones complete)
export WORKFLOW_ENGINE_ENABLED=false
systemctl restart nova_worker

# Enable
export WORKFLOW_ENGINE_ENABLED=true
systemctl restart nova_worker
```

### Emergency Budget Override

```bash
# Temporarily increase workflow ceiling
export DEFAULT_WORKFLOW_CEILING_CENTS=10000
systemctl restart nova_worker

# Reset to default
unset DEFAULT_WORKFLOW_CEILING_CENTS
systemctl restart nova_worker
```

### Disable Specific Skill

```sql
-- Mark skill as disabled in registry
UPDATE skill_registry
SET enabled = false,
    disabled_reason = 'Emergency disable due to incident INC-123'
WHERE skill_id = '<problematic_skill>';
```

---

## Golden File Recovery

### Replay Workflow Locally

```bash
# Load golden file and replay
python -c "
from app.workflow.golden import GoldenRecorder
from app.workflow.engine import WorkflowEngine, WorkflowSpec

recorder = GoldenRecorder('./golden', secret='test-secret')
events = recorder.load_golden('<run_id>.steps.jsonl')

# Extract spec and seed from run_start event
run_start = events[0]
seed = run_start.data['seed']
spec_id = run_start.data['spec_id']

print(f'Replaying {spec_id} with seed {seed}')
print(f'Steps: {len([e for e in events if e.event_type == \"step\"])}')

# Run replay
engine = WorkflowEngine(registry, checkpoint_store, golden=recorder)
result = await engine.run(spec, run_id='replay-test', seed=seed, replay=True)

# Compare results
for i, event in enumerate(events):
    if event.event_type == 'step':
        original_hash = event.data.get('output_hash')
        replay_hash = result.step_results[event.data['index']].content_hash()
        match = '✓' if original_hash == replay_hash else '✗'
        print(f'{match} Step {event.data[\"step_id\"]}: {original_hash} vs {replay_hash}')
"
```

### Diff Golden Files

```bash
# Using canonical comparison
python -c "
from app.workflow.golden import GoldenRecorder

recorder = GoldenRecorder('.', secret='test')
result = recorder.compare_golden(
    'actual.steps.jsonl',
    'expected.steps.jsonl',
    ignore_timestamps=True
)

if result['match']:
    print('✓ Golden files match')
else:
    print(f'✗ Found {len(result[\"diffs\"])} differences:')
    for diff in result['diffs']:
        print(f'  - {diff[\"type\"]} at {diff.get(\"index\", \"N/A\")}')
"
```

---

## Monitoring & Alerts

### Key Metrics to Watch

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| `nova_workflow_runs_total{status="failed"}` rate | <1/min | >5/min | >20/min |
| `nova_workflow_replay_failures_total` | 0 | >0 | >5 |
| `nova_workflow_checkpoint_save_seconds` p99 | <200ms | >500ms | >1s |
| `nova_workflow_running_age_seconds` max | <300s | >600s | >3600s |

### Prometheus Queries

```promql
# Workflow failure rate
rate(nova_workflow_runs_total{status="failed"}[5m]) /
rate(nova_workflow_runs_total[5m])

# Checkpoint latency
histogram_quantile(0.99, rate(nova_workflow_checkpoint_save_seconds_bucket[5m]))

# Stale workflows count
count(nova_workflow_running_age_seconds > 3600)

# Golden mismatches trend
increase(nova_workflow_golden_mismatches_total[1h])
```

### Log Queries

```bash
# Recent errors
journalctl -u nova_worker --since "10 minutes ago" | grep -E "ERROR|CRITICAL"

# Checkpoint operations
journalctl -u nova_worker --since "10 minutes ago" | grep "checkpoint"

# Golden file operations
journalctl -u nova_worker --since "10 minutes ago" | grep "golden"
```

---

## Contacts

- **On-Call SRE:** Page via PagerDuty
- **Backend Team Lead:** @backend-lead
- **Security Team:** For TAMPER_DETECTED alerts

---

## Related Runbooks

- [Budget Exceeded](budget-exceeded.md)
- [Planner Sandbox](planner-sandbox.md)
- [Security Incident](security-incident.md)
- [Worker Saturation](worker-saturation.md)
