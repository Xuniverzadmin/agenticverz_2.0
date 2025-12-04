# PIN-014: M4 Workflow Engine Technical Review

**Serial:** PIN-014
**Title:** M4 Workflow Engine v1 - Deep Technical Review
**Category:** Architecture / Technical Review
**Status:** ACTIVE
**Created:** 2025-12-01
**Author:** Claude Code Review

---

## Executive Summary

This document provides a comprehensive technical review of the M4 "Workflow Engine v1 + Hardening" milestone. The review evaluates alignment with system vision, identifies issues by severity, and provides required fixes with acceptance criteria.

**Verdict:** CONDITIONAL PASS - NOT PRODUCTION-READY

M4 delivers solid architectural foundations but has **5 P0 blockers** and **7 P1 issues** that must be resolved before production deployment.

---

## 1. Alignment Check

### Vision Pillars Assessment

| Pillar | Status | Evidence |
|--------|--------|----------|
| Deterministic state | ✅ ALIGNED | Seed propagation via `_derive_seed()`, canonical JSON |
| Replayable runs | ⚠️ PARTIAL | Golden pipeline exists but P0-3 (duration leakage) risks replay |
| Budget & cost contracts | ✅ ALIGNED | PolicyEnforcer with per-step/workflow ceilings |
| Skill contracts | ✅ ALIGNED | Planner sandbox validates forbidden skills |
| System policies | ✅ ALIGNED | Emergency stop, idempotency requirements |
| Observability | ✅ ALIGNED | Prometheus metrics, 15 alert rules, health endpoints |
| Planner modularity | ✅ ALIGNED | PlannerSandbox validates planner outputs |
| Zero silent failures | ⚠️ PARTIAL | Error taxonomy comprehensive but classification too broad |

### Milestone Alignment

| Previous Milestone | Integration Status |
|--------------------|-------------------|
| M0: Schemas | ✅ Error taxonomy uses M0 categories |
| M1: Runtime | ✅ Engine uses runtime interfaces |
| M2: Skills | ✅ Registry integration via `SkillRegistry` protocol |
| M2.5: Planner | ✅ PlannerSandbox validates planner outputs |
| M3: Core Skills | ✅ Skills invoked through engine's `_execute_step` |

### Future Milestone Compatibility

| Future Milestone | Compatibility |
|------------------|---------------|
| M5: Failure Catalog | ✅ Error taxonomy ready for extension |
| M5.5: Simulation | ⚠️ `runtime.simulate()` not integrated |
| M6: Feature Freeze | ✅ Metrics foundation ready |
| M7: Memory | ⚠️ No memory hooks in StepContext |

---

## 2. Issues & Inconsistencies Found

### P0 – Production Blockers

#### P0-1: Checkpoint Store Methods Are Sync, Not Async

**Location:** `backend/app/workflow/checkpoint.py:151-365`

**Issue:** All methods marked `async def save()`, `async def load()` use synchronous SQLModel sessions (`with Session(self.engine)`). These block the event loop.

**Impact:** Under concurrent load, checkpoint operations serialize, creating bottlenecks and breaking async workflow engine design.

**Evidence:**
```python
async def save(self, ...):
    # ...
    with Session(self.engine) as session:  # BLOCKING!
        existing = session.get(WorkflowCheckpoint, run_id)
```

---

#### P0-2: No Backoff/Jitter in Engine Retry Logic

**Location:** `backend/app/workflow/engine.py:553-621`

**Issue:** The `_execute_step` retry loop immediately retries on failure. The `backoff_base_ms` defined in error metadata is never used.

**Impact:** Retries hammer failing services, causing cascading failures. Violates deterministic retry timing.

**Evidence:**
```python
for attempt in range(max_attempts):
    try:
        # execute skill
    except Exception as e:
        # NO BACKOFF - immediately continues to next attempt
        if attempt < max_attempts - 1 and last_error.is_retryable:
            continue  # <-- Missing await asyncio.sleep(backoff)
```

---

#### P0-3: Duration Fields Leak into Golden Output Hash

**Location:** `backend/app/workflow/engine.py:446-447`, `backend/app/workflow/golden.py:188-190`

**Issue:** `duration_ms` is computed from wall-clock time, stored in `StepResult`, and recorded in golden files via `result.to_dict()`. The `output_hash` includes this non-deterministic field.

**Impact:** Golden file replay comparisons may fail due to timing variance.

**Evidence:**
```python
# golden.py:190
"output_hash": hashlib.sha256(_canonical_json(output).encode()).hexdigest()[:16],
# output contains duration_ms from result.to_dict()
```

---

#### P0-4: Missing/Inconsistent Metric Labels

**Location:** `backend/app/workflow/engine.py:507-508`

**Issue:** When `agent_id` is None, `tenant_hash` becomes "unknown". Alerts expecting both `spec_id` and `tenant_hash` may not fire correctly.

**Impact:** `WorkflowFailureRateHigh` alert grouping by `spec_id` may malfunction.

---

#### P0-5: Golden File Signature TOCTOU Vulnerability

**Location:** `backend/app/workflow/golden.py:237-246`

**Issue:** `record_run_end` appends the final event, then calls `sign_golden()`. If process crashes between append and sign, golden file is unsigned.

**Impact:** Corrupt/incomplete golden files. Signature verification fails on legitimate files.

**Evidence:**
```python
async def record_run_end(self, run_id: str, status: str) -> None:
    event = GoldenEvent(...)
    await self._append(run_id, event)  # <-- Write event
    # CRASH WINDOW HERE
    filepath = self._filepath(run_id)
    self.sign_golden(filepath)  # <-- Sign separately
```

---

### P1 – High Severity

#### P1-1: Checkpoint Version Locking Not Used by Engine

**Location:** `backend/app/workflow/engine.py:463-469`

**Issue:** Engine calls `checkpoint.save()` without passing `expected_version`. The optimistic locking mechanism exists but is unused.

**Impact:** Concurrent executions of same `run_id` can clobber checkpoints.

---

#### P1-2: Policy Enforcer Budget Dict Is Per-Instance

**Location:** `backend/app/workflow/policies.py:95`

**Issue:** `_workflow_costs` is an instance dict. In multi-worker deployment, costs aren't shared.

**Impact:** Budget enforcement is per-worker, not per-workflow. Workflows can exceed limits across workers.

---

#### P1-3: InMemoryCheckpointStore Race Condition

**Location:** `backend/app/workflow/checkpoint.py:440-490`

**Issue:** Lock covers dict update but not full read-modify-write between `load()` and `save()`.

**Impact:** Race condition in concurrent unit tests.

---

#### P1-4: External Guard Doesn't Patch Async HTTP Clients

**Location:** `backend/app/workflow/external_guard.py:229-255`

**Issue:** Patches `requests.Session` and `httpx.Client` but not `httpx.AsyncClient`.

**Impact:** Async HTTP calls bypass guard in CI tests.

---

#### P1-5: Health Readiness Check Doesn't Ping Database

**Location:** `backend/app/workflow/health.py:113-115`

**Issue:** `readyz` uses `hasattr(_checkpoint_store, 'load')` which always returns True. Never tests actual DB connectivity.

**Impact:** Pod marked ready even when database is down.

---

#### P1-6: Status Field Mismatch Between Code and Migration

**Location:** `checkpoint.py:62` vs `alembic/versions/001_create_workflow_checkpoints.py:72-73`

**Issue:**
- Code uses statuses: `running`, `completed`, `aborted`, `failed`, `budget_exceeded`, `sandbox_rejected`, `policy_violation`, `emergency_stopped`
- Migration constraint allows: `running`, `completed`, `failed`, `aborted`, `paused`, `timeout`

**Impact:** Code sets statuses that violate DB constraint.

---

#### P1-7: Planner Sandbox Pattern Escaping Issues

**Location:** `backend/app/workflow/planner_sandbox.py:79-88`

**Issue:** Pattern `r"\.\.\/` should be `r"\.\.\/"`. Backtick pattern can match legitimate strings.

**Impact:** False positives/negatives in injection detection.

---

### P2 – Important But Not Urgent

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| P2-1 | Metrics stubs don't match real API | `metrics.py:117-147` | Tests may break with Prometheus |
| P2-2 | Case-insensitive volatile key matching | `canonicalize.py:164` | Non-deterministic canonicalization |
| P2-3 | Golden dir created with default umask | `golden.py:104` | Potential PII exposure |
| P2-4 | CLI hardcoded `/tmp/golden` path | `cli/aos_workflow.py` | CLI won't find production files |
| P2-5 | `EXECUTION_ERROR` fallback too broad | `errors.py:700-706` | Root cause obscured in metrics |
| P2-6 | No tenant isolation in `list_running` | `checkpoint.py:369-406` | Cross-tenant data leak |
| P2-7 | Missing index on `workflow_id` | Migration file | Slow queries by workflow spec |

---

## 3. Required Fixes

### P0 Fixes (Must Complete Before Production)

#### Fix P0-1: Make Checkpoint Store Actually Async

```python
# checkpoint.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

class CheckpointStore:
    def __init__(self, engine_url: Optional[str] = None):
        url = engine_url or os.getenv("DATABASE_URL")
        async_url = url.replace("postgresql://", "postgresql+asyncpg://")
        self.engine = create_async_engine(async_url, echo=False)

    async def save(self, ...):
        async with AsyncSession(self.engine) as session:
            existing = await session.get(WorkflowCheckpoint, run_id)
            # ... async operations
            await session.commit()
```

**Tests to add:**
- `test_checkpoint_async_concurrent` - 50 concurrent saves
- `test_checkpoint_no_event_loop_blocking`

---

#### Fix P0-2: Implement Exponential Backoff with Jitter

```python
# engine.py - in _execute_step
import random

for attempt in range(max_attempts):
    try:
        # ... execute skill ...
    except Exception as e:
        last_error = classify_exception(e, context)
        if attempt < max_attempts - 1 and last_error.is_retryable:
            # Use seeded random for determinism
            rng = random.Random(ctx.seed + attempt)
            backoff_ms = last_error.backoff_base_ms * (2 ** attempt)
            jitter = rng.randint(0, backoff_ms // 2)
            await asyncio.sleep((backoff_ms + jitter) / 1000.0)
            continue
```

**Tests to add:**
- `test_retry_uses_exponential_backoff`
- `test_retry_jitter_is_deterministic_with_seed`

---

#### Fix P0-3: Exclude Duration from Golden Output Hash

```python
# golden.py - in record_step()
VOLATILE_OUTPUT_FIELDS = {'duration_ms', 'latency_ms', 'elapsed_ms'}

output_for_hash = {k: v for k, v in output.items() if k not in VOLATILE_OUTPUT_FIELDS}
step_data["output_hash"] = hashlib.sha256(_canonical_json(output_for_hash).encode()).hexdigest()[:16]
```

**Tests to add:**
- `test_golden_hash_excludes_duration`
- `test_golden_replay_with_varying_durations`

---

#### Fix P0-4: Ensure Consistent Metric Labels

```python
# engine.py:507-508
record_workflow_failure(
    error_code=error_code,
    spec_id=spec.id,
    tenant_id=agent_id or "system"  # Never "unknown"
)
```

---

#### Fix P0-5: Atomic Golden File Write with Signature

```python
# golden.py
import tempfile

async def record_run_end(self, run_id: str, status: str) -> None:
    event = GoldenEvent(...)

    # Write to temp file
    final_path = self._filepath(run_id)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=self.dir, suffix='.tmp')

    try:
        # Copy existing content + new event to temp
        if os.path.exists(final_path):
            with open(final_path, 'rb') as src:
                os.write(tmp_fd, src.read())
        os.write(tmp_fd, (_canonical_json(event.to_dict()) + "\n").encode())
        os.close(tmp_fd)

        # Sign temp file
        sig = self.sign_golden(tmp_path)

        # Atomic rename
        os.rename(tmp_path, final_path)
        os.rename(tmp_path + ".sig", final_path + ".sig")
    except:
        os.unlink(tmp_path)
        raise
```

---

### P1 Fixes

#### Fix P1-1: Use Optimistic Locking in Engine

```python
# engine.py
ck = await self.checkpoint.load(run_id)
expected_version = ck.version if ck else None

await self.checkpoint.save(
    run_id=run_id,
    next_step_index=idx + 1,
    # ...
    expected_version=expected_version,
)
```

---

#### Fix P1-4: Patch Async HTTP Clients

```python
# external_guard.py
if self.block_httpx:
    try:
        import httpx
        # Sync client
        httpx_sync_patch = patch.object(httpx.Client, "request", ...)
        # Async client
        httpx_async_patch = patch.object(httpx.AsyncClient, "request", ...)
        self._patches.extend([httpx_sync_patch, httpx_async_patch])
```

---

#### Fix P1-5: Add Real DB Ping to Readiness

```python
# health.py
if _checkpoint_store:
    try:
        async with AsyncSession(_checkpoint_store.engine) as session:
            await session.execute(text("SELECT 1"))
        checks["checkpoint_store"] = True
    except Exception:
        checks["checkpoint_store"] = False
```

---

#### Fix P1-6: Align Status Values

```sql
-- Update migration constraint
CHECK (status IN (
    'running', 'completed', 'failed', 'aborted',
    'budget_exceeded', 'sandbox_rejected',
    'policy_violation', 'emergency_stopped'
))
```

---

## 4. Acceptance Gates Before Production

| Gate | Requirement | Status |
|------|-------------|--------|
| P0-1 | Async checkpoint operations | ❌ BLOCKED |
| P0-2 | Retry backoff with jitter | ❌ BLOCKED |
| P0-3 | Duration excluded from golden hash | ❌ BLOCKED |
| P0-4 | Consistent metric labels | ❌ BLOCKED |
| P0-5 | Atomic golden writes | ❌ BLOCKED |
| P1-1 | Optimistic locking in engine | ❌ BLOCKED |
| P1-4 | Async HTTP client guard | ❌ BLOCKED |
| P1-6 | Status enum alignment | ❌ BLOCKED |
| Tests | All fixes have test coverage | ❌ PENDING |
| Stress | 100x golden replay passing | ❌ PENDING |
| Nightly | 1 week CI with 0 failures | ❌ PENDING |

---

## 5. Verdict

### Status: CONDITIONAL PASS - REVISE REQUIRED

**What's Working:**
- ✅ Deterministic seed propagation architecture
- ✅ Checkpoint persistence design (version-based locking)
- ✅ Golden file pipeline with HMAC signing
- ✅ Comprehensive error taxonomy (50+ codes)
- ✅ External call guard for CI isolation
- ✅ Planner sandbox validation
- ✅ Prometheus metrics and alerts
- ✅ 640+ tests with stress coverage

**What's Blocking:**
- ❌ Checkpoint operations block event loop (P0-1)
- ❌ No retry backoff implementation (P0-2)
- ❌ Duration leaks into golden hashes (P0-3)
- ❌ Golden file signature not atomic (P0-5)
- ❌ Optimistic locking not used by engine (P1-1)

### Recommendation

**REVISE** the milestone:
1. Fix all P0 issues (5 items)
2. Fix critical P1 issues (P1-1, P1-4, P1-6)
3. Add test coverage for each fix
4. Re-run 100x golden stress
5. Run nightly CI for 1 week
6. Re-submit for review

The architectural decisions are sound. Implementation needs hardening before production traffic.

---

## 6. Test Coverage Requirements

### New Tests Required

| Test | Purpose | Priority |
|------|---------|----------|
| `test_checkpoint_async_concurrent` | 50 concurrent async saves | P0 |
| `test_retry_uses_exponential_backoff` | Verify backoff timing | P0 |
| `test_retry_jitter_deterministic` | Jitter uses seed | P0 |
| `test_golden_hash_excludes_duration` | Duration not in hash | P0 |
| `test_golden_atomic_write` | Crash safety | P0 |
| `test_checkpoint_uses_version` | Engine uses locking | P1 |
| `test_async_http_blocked` | AsyncClient blocked | P1 |
| `test_readyz_pings_db` | Real connectivity check | P1 |

---

## 7. File Changes Required

| File | Change Type | Priority |
|------|-------------|----------|
| `checkpoint.py` | Convert to async SQLAlchemy | P0 |
| `engine.py` | Add backoff, use version locking | P0 |
| `golden.py` | Atomic writes, exclude duration | P0 |
| `metrics.py` | Fix label consistency | P0 |
| `external_guard.py` | Add async client patching | P1 |
| `health.py` | Real DB ping | P1 |
| `001_create_workflow_checkpoints.py` | Fix status constraint | P1 |
| `planner_sandbox.py` | Fix regex escaping | P1 |

---

## References

- PIN-008: v1 Milestone Plan (Full Detail)
- PIN-013: M4 Workflow Engine Completion Report
- `backend/app/workflow/` - All M4 source files
- `backend/tests/workflow/` - M4 test suite
- `monitoring/alerts/workflow-alerts.yml` - Alert rules

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-01 | Initial technical review completed |
