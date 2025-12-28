# PIN-202: PB-S2 Crash & Resume - FROZEN

**Status:** FROZEN
**Date:** 2025-12-27
**Phase:** A.5 (Truth Certification)

---

## PB-S2 Guarantee

> **Orphaned runs are never silently lost. The system tells the truth about crashes.**

---

## Implementation Summary

### What Was Implemented

| Component | Location | Purpose |
|-----------|----------|---------|
| Orphan Recovery Service | `backend/app/services/orphan_recovery.py` | Detect and mark orphaned runs on startup |
| Startup Integration | `backend/app/main.py:325-347` | Call recovery before accepting requests |
| Crashed Status | `backend/app/models/tenant.py:444-445` | Document "crashed" as valid terminal status |
| Immutability Extension | Migration 055 | Protect crashed runs from mutation |

### Recovery Logic

1. **On startup**, detect runs in "queued" or "running" status older than 30 minutes
2. **Mark as "crashed"** with factual error message
3. **Set completed_at** to record when crash was detected
4. **Log for operator visibility**

### Truth Guarantees

| Guarantee | Enforcement |
|-----------|-------------|
| Crashed runs are immutable | DB trigger blocks mutation |
| Crash is a fact, not inference | Status derived from observation |
| No silent recovery | All recovery logged with run IDs |
| Retry via PB-S1 | Create NEW run with parent linkage |

---

## Verification Evidence

### Test Results (2025-12-27)

```
Orphaned runs detected: 3
- 496c2b70-9032-47a5-9b68-68278322b4a7 (running 17.7h) → crashed
- b3525d49-5985-4f77-9a72-61d02a0af6bd (queued 4.5h) → crashed
- 0d489f19-20a9-4f08-8c28-1462a3263299 (queued 1.9h) → crashed

Immutability test:
UPDATE worker_runs SET status = 'running' WHERE id = '496c2b70...'
→ ERROR: TRUTH_VIOLATION: Cannot mutate completed/failed/crashed worker_run
```

---

## Related Artifacts

| Artifact | Location |
|----------|----------|
| Recovery service | `backend/app/services/orphan_recovery.py` |
| Migration 055 | `backend/alembic/versions/055_pb_s2_crashed_status.py` |
| Behavior rules | BL-ACC-001, BL-RDY-001, BL-EXEC-001 |
| Boot contract update | `CLAUDE_BOOT_CONTRACT.md` |

---

## What Cannot Change (FROZEN)

1. **"crashed" is a valid terminal status** - cannot be removed
2. **Crashed runs are immutable** - trigger cannot be weakened
3. **Recovery runs on startup** - cannot be made optional
4. **Recovery is logged** - cannot be silent

---

## What May Evolve (Phase B)

1. Configurable orphan threshold (currently 30 minutes)
2. Long-running job exceptions
3. Automatic retry of crashed runs (via PB-S1)
4. Ops console visibility for crashed runs

---

## CI Test Requirements (Step 3)

The following tests must be added to CI:

```python
def test_pb_s2_orphan_detection():
    """Runs stuck in queued/running are detected after threshold."""

def test_pb_s2_status_transition():
    """Orphaned runs transition to 'crashed' status."""

def test_pb_s2_crashed_immutability():
    """Crashed runs cannot be mutated."""

def test_pb_s2_recovery_idempotent():
    """Multiple restarts don't create duplicate recovery."""
```

---

## FROZEN Declaration

This PIN is FROZEN. The guarantees above are constitutional.

Phase B work may extend but not weaken these guarantees.

---

*Generated: 2025-12-27*
*Reference: PIN-199 (PB-S1), behavior_library.yaml*
