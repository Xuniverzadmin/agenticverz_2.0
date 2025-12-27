# PIN-199: PB-S1 Retry Creates New Execution - Implementation

**Status:** 🏗️ FROZEN
**Created:** 2025-12-27
**Category:** Phase B / Truth Guarantee
**Milestone:** Phase B.1

---

## Summary

Implemented proper retry mechanism that creates NEW executions instead of mutating failed runs. Added immutability trigger to enforce PB-S1 truth guarantee at database level.

---

## Details

## Context

During PB-S1 verification, a critical violation was discovered: the existing `/admin/rerun` endpoint **MUTATED** failed runs by resetting their status from "failed" to "queued", violating the truth-grade system's immutability guarantees established in Phase A.5.

## Problem Statement

The original `/admin/rerun` endpoint performed:
```python
# VIOLATION: Mutates the original run
run.status = "queued"
run.started_at = None
run.completed_at = None
run.error_message = None
session.commit()
```

This violated **S1 (Execution Facts)** and **S6 (Trace Immutability)** guarantees:
- History was being rewritten
- Failed execution facts were erased
- Audit trail was broken

## Solution Implemented

### 1. Database Migration (053_pb_s1_retry_immutability.py)

Added retry linkage columns:
- `parent_run_id`: Links retry to original failed run
- `attempt`: Tracks retry attempt number (1 = original, 2+ = retry)
- `is_retry`: Boolean flag for fast filtering

Added immutability trigger:
```sql
CREATE FUNCTION prevent_worker_run_mutation()
RETURNS trigger AS $$
BEGIN
    IF OLD.status IN ('completed', 'failed') THEN
        IF (NEW.status != OLD.status OR ...) THEN
            RAISE EXCEPTION 'PB-S1 VIOLATION: Cannot mutate completed/failed worker_run';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

Added audit view:
```sql
CREATE VIEW retry_history AS
SELECT r.*, p.status as original_status, p.error as original_error
FROM worker_runs r
LEFT JOIN worker_runs p ON r.parent_run_id = p.id
WHERE r.is_retry = true;
```

### 2. New Endpoint: POST /admin/retry

```python
@app.post("/admin/retry")
async def retry_failed_run(payload: RetryRequest):
    """Creates NEW execution - never mutates original."""
    # Fetch original failed run
    original_run = await get_run(payload.run_id)

    # Create NEW retry run
    retry_run = WorkerRun(
        tenant_id=original_run.tenant_id,
        worker_id=original_run.worker_id,
        task=original_run.task,
        status="queued",
        parent_run_id=original_run.id,  # Link to original
        attempt=original_run.attempt + 1,
        is_retry=True,
    )
    await session.add(retry_run)
```

### 3. Deprecated: POST /admin/rerun

Marked as deprecated with warning:
```
WARNING: This endpoint MUTATES the original run, violating PB-S1 truth guarantees.
Use POST /admin/retry instead for proper retry semantics.
```

## Verification Results

```
============================================================
PB-S1 VERIFICATION: PASSED ✅
============================================================

[STEP 1] Schema has PB-S1 columns............... ✅
[STEP 2] Immutability trigger exists............ ✅
[STEP 3] Retry creates NEW run.................. ✅
[STEP 4] Mutation blocked by trigger............ ✅
[STEP 5] retry_history view accessible.......... ✅
```

### Evidence

```
Original Run: 9d5f5f49... | status=failed | attempt=1 | is_retry=false
Retry Run:    b3525d49... | status=queued | attempt=2 | is_retry=true
                          | parent_run_id → 9d5f5f49...
```

Mutation attempt:
```sql
UPDATE worker_runs SET status = 'test' WHERE id = '9d5f5f49...';
-- ERROR: PB-S1 VIOLATION: Cannot mutate completed/failed worker_run
```

## Files Changed

| File | Change |
|------|--------|
| `backend/alembic/versions/053_pb_s1_retry_immutability.py` | New migration |
| `backend/app/models/tenant.py` | Added retry fields, fixed datetime |
| `backend/app/main.py` | New `/admin/retry`, deprecated `/admin/rerun` |

## Truth Guarantees Enforced

| Guarantee | Mechanism | Enforcement |
|-----------|-----------|-------------|
| Retry = NEW execution | New row with new ID | Code |
| Original IMMUTABLE | DB trigger | Database |
| Parent linkage | parent_run_id FK | Schema |
| Attempt tracking | attempt counter | Schema |
| Audit trail | retry_history view | Database |

## API Changes

### New: POST /admin/retry
```json
// Request
{"run_id": "uuid", "reason": "optional reason"}

// Response
{
  "original_run_id": "9d5f...",
  "retry_run_id": "b352...",
  "attempt": 2,
  "status": "queued",
  "original_status": "failed",
  "reason": "manual_retry"
}
```

### Deprecated: POST /admin/rerun
Returns warning in response. Will be removed in future version.

## Invariants

1. **IMMUTABLE**: Completed/failed runs cannot be modified (trigger-enforced)
2. **APPEND-ONLY**: Retries add new rows, never update existing
3. **LINKED**: Every retry has parent_run_id pointing to original
4. **TRACEABLE**: Full retry chain visible via retry_history view

## References

- PIN-193: S1 Execution Facts (acceptance gate)
- PIN-194: S2 Costs (acceptance gate)
- PIN-195: S3 Policy (acceptance gate)
- PIN-196: S4 Failures (acceptance gate)
- PIN-197: S5 Memory (acceptance gate)
- PIN-198: S6 Traces (acceptance gate)

---


---

## Post-Implementation Analysis

### Update (2025-12-27)

## Post-Implementation Analysis (2025-12-27)

### System Truth Assessment

**Verdict:** PB-S1 is genuinely closed, because the database now enforces truth even if the application or AI is wrong.

### Enforcement Layers Verified

| Layer | Enforcement | Result |
|-------|-------------|--------|
| **API** | \`/admin/retry\` creates new execution | ✅ Correct behavior |
| **API** | \`/admin/rerun\` returns HTTP 410 Gone | ✅ Hard-disabled |
| **DB Schema** | \`parent_run_id\`, \`attempt\`, \`is_retry\` | ✅ Explicit lineage |
| **DB Trigger** | \`prevent_worker_run_mutation()\` | ✅ **Mechanical truth** |

### Critical Milestone

The line that proves the architecture direction is correct:
\`\`\`
ERROR: PB-S1 VIOLATION: Cannot mutate completed/failed worker_run
\`\`\`

This means:
- A future developer
- A rushed hotfix
- A careless AI
- A compromised admin endpoint

**Cannot violate PB-S1 even if they try.**

### Cross-Table Immutability Status

| Table | Protected | Trigger |
|-------|-----------|---------|
| \`worker_runs\` | ✅ YES | \`prevent_worker_run_mutation()\` |
| \`aos_traces\` | ✅ YES | \`restrict_trace_update()\` (S6) |
| \`aos_trace_steps\` | ✅ YES | \`enforce_trace_step_immutability()\` (S6) |

### Hidden Risks Addressed

1. **Legacy \`/admin/rerun\` usage** → Hard-disabled with HTTP 410
2. **Cross-table gaps** → Traces already protected by S6 triggers
3. **Worker-side assumptions** → CI tests verify independent execution

### CI Tests Added

File: \`backend/tests/test_pb_s1_invariants.py\`

- \`test_mutation_of_failed_run_is_rejected\`
- \`test_mutation_of_completed_run_is_rejected\`
- \`test_immutability_trigger_exists\`
- \`test_retry_creates_new_row_not_mutation\`
- \`test_rerun_endpoint_returns_410_gone\`

### What This Unlocks

**Now Possible:**
- PB-S2 (Crash & Resume)
- Cost attribution correctness
- Incident lineage
- Policy derivation
- Prediction (advisory only)
- Learning without poisoning history

**Still Forbidden:**
- Auto-retry (silent)
- Self-healing
- Silent recovery
- Outcome rewriting

### FROZEN Status

PB-S1 is now a **constitutional invariant**. See \`docs/memory-pins/PB-S1-FROZEN.md\`.

**Philosophy encoded into physics.**

## Related PINs

- [PIN-193](PIN-193-.md)
- [PIN-194](PIN-194-.md)
- [PIN-195](PIN-195-.md)
- [PIN-196](PIN-196-.md)
- [PIN-197](PIN-197-.md)
- [PIN-198](PIN-198-.md)
