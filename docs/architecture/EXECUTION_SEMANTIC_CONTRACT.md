# Execution Semantic Contract (Phase 3.2)

**Status:** DRAFT
**Created:** 2025-12-30
**Phase:** 3.2 — Execution Model Semantics
**Reference:** PIN-251, PHASE3_SEMANTIC_CHARTER.md

---

## Purpose

This contract defines **what execution means** — the semantic boundaries between sync, async, deferred, and background execution.

**Core Question:**
> What does sync vs async mean in this system?
> Which layers are allowed to initiate async execution?
> What guarantees exist (ordering, retries, idempotency)?
> How do execution failures propagate semantically?

---

## The Four Execution Axes

### Axis 1: Execution Timing (WHEN)

**Definition:** Execution timing defines when code runs relative to the triggering event.

**Execution Timing Values:**

| Value | Meaning | Example |
|-------|---------|---------|
| `import-time` | Runs when module is imported | Module-level constants, class definitions |
| `request-time` | Runs during HTTP request lifecycle | API route handlers |
| `deferred` | Scheduled for later execution | Background tasks via FastAPI |
| `background-worker` | Long-running polling process | WorkerPool, RunRunner |
| `scheduled` | Triggered by cron/timer | Not yet implemented |

**Semantic Invariant:**
> **Import-time code MUST NOT perform I/O or state mutation.**
> Import-time is for definition only. Execution happens later.

---

### Axis 2: Execution Model (HOW)

**Definition:** Execution model defines whether code yields control during execution.

**Execution Model Values:**

| Value | Meaning | Pattern | Example |
|-------|---------|---------|---------|
| `sync` | Blocking, does not yield | `def func()` | Hash computation, pure functions |
| `async` | Non-blocking, yields on await | `async def func()` | DB queries, HTTP calls |
| `sync-over-async` | Sync wrapper around async | `loop.run_until_complete()` | Worker entrypoints |

**Semantic Invariants:**
1. **Async functions MUST NOT block the event loop**
   - No `time.sleep()` — use `asyncio.sleep()`
   - No blocking I/O — use async libraries
2. **Sync functions MUST NOT initiate async execution**
   - Exception: Explicit `sync-over-async` wrappers at worker boundaries
3. **Decision functions MUST be pure (sync and stateless)**
   - Policy decisions, role mapping, tier gating = pure computation

---

### Axis 3: Execution Guarantee (WHAT)

**Definition:** Execution guarantees define what promises the system makes about execution.

**Guarantee Types:**

| Guarantee | Meaning | Enforcement Location |
|-----------|---------|---------------------|
| `deterministic` | Same inputs → same outputs | WorkflowEngine via seed |
| `idempotent` | Multiple calls = one effect | IdempotencyStore via Redis |
| `at-least-once` | Will execute, may duplicate | Worker retry logic |
| `at-most-once` | Will not duplicate, may fail | Idempotency + no retry |
| `exactly-once` | One execution, guaranteed | Idempotency + checkpoint |
| `best-effort` | No guarantee | Fire-and-forget events |

**Guarantee Assignment by Component:**

| Component | Guarantee | Mechanism |
|-----------|-----------|-----------|
| WorkflowEngine.run() | `exactly-once` per step | Checkpoint + idempotency key |
| WorkerPool dispatch | `at-least-once` | Polling + DB state |
| SSE event emission | `best-effort` | In-memory queue |
| Cost record insertion | `exactly-once` | Idempotent upsert |
| Policy decision | `deterministic` | Pure function, no state |

---

### Axis 4: Failure Semantics (WHAT IF)

**Definition:** Failure semantics define how execution failures propagate.

**Failure Propagation Modes:**

| Mode | Behavior | Where Used |
|------|----------|------------|
| `abort` | Stop workflow on failure | Default step behavior |
| `continue` | Skip failed step, proceed | Optional per-step config |
| `retry` | Retry with backoff | Retryable errors only |
| `recover` | Attempt M9/M10 recovery | BusinessBuilderWorker |
| `bubble` | Propagate exception up | API layer errors |

**Failure Classification (M9 Pattern):**

| Error Code | Is Retryable | Backoff Base |
|------------|--------------|--------------|
| `TRANSIENT_ERROR` | Yes | 1000ms |
| `RATE_LIMIT_ERROR` | Yes | 5000ms |
| `BUDGET_EXCEEDED` | No | N/A |
| `POLICY_VIOLATION` | No | N/A |
| `SKILL_NOT_FOUND` | No | N/A |
| `UNKNOWN_ERROR` | No | N/A |

**Semantic Invariants:**
1. **Retryable errors use exponential backoff with deterministic jitter**
   - Formula: `base_ms * 2^attempt + jitter(seed, attempt)`
   - Jitter is seeded for replay reproducibility
2. **Non-retryable errors propagate immediately**
   - No retry loop for policy/budget violations
3. **All failures produce structured outcomes**
   - Never throw raw exceptions to callers
   - `StepResult.from_error()` pattern

---

## Layer Execution Rules (Authoritative)

### L2 (API) — Request Boundary

**Execution Model:** `async`
**Trigger:** HTTP request
**Timing:** `request-time`

**Rules:**
1. All route handlers MUST be `async def`
2. May initiate deferred execution via `BackgroundTasks`
3. MUST NOT directly call worker execution synchronously
4. MUST return within request timeout

**Allowed Patterns:**
```python
@router.post("/run")
async def run_worker(background_tasks: BackgroundTasks):
    # Immediate response
    run_id = str(uuid.uuid4())
    # Deferred execution
    background_tasks.add_task(_execute_worker_async, run_id, request)
    return {"run_id": run_id, "status": "queued"}
```

**Forbidden Patterns:**
```python
# FORBIDDEN: Blocking sync call in async handler
@router.post("/run")
async def run_worker():
    result = sync_execute_worker()  # BLOCKS EVENT LOOP
```

---

### L4 (Domain) — Business Logic

**Execution Model:** `async` (operations), `sync` (decisions)
**Trigger:** Worker or API
**Timing:** `request-time` or `deferred`

**Rules:**
1. Decision functions (policy, role mapping) MUST be `sync` and pure
2. State-mutating operations MUST be `async`
3. MUST NOT initiate background tasks
4. MUST NOT import L2 (API) modules

**Decision Authority:**
> **All policy decisions MUST be synchronous pure functions.**
> Async in decision paths creates race conditions and non-determinism.

| Function Type | Model | Example |
|---------------|-------|---------|
| Policy evaluation | sync | `RBACEngine.evaluate()` |
| Role mapping | sync | `map_console_role_to_rbac()` |
| Tier gating | sync | `check_tier_access()` |
| DB read/write | async | `session.execute()` |
| External calls | async | `llm_service.invoke()` |

---

### L5 (Workers) — Background Execution

**Execution Model:** `sync-over-async` (entrypoint), `async` (internal)
**Trigger:** Worker pool or background task
**Timing:** `background-worker` or `deferred`

**Rules:**
1. Worker entrypoints MAY use `sync-over-async` pattern
2. Internal execution MUST be fully async
3. MUST handle graceful shutdown via signals
4. MUST checkpoint progress for resume

**Sync-Over-Async Pattern (AUTHORITATIVE):**
```python
class RunRunner:
    def run(self, run: Run) -> RunResult:
        """Sync entrypoint for ThreadPoolExecutor."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._execute(run))
        finally:
            loop.close()

    async def _execute(self, run: Run) -> RunResult:
        """Async internal execution."""
        # All actual work is async
```

**Why This Pattern:**
- `ThreadPoolExecutor` requires sync callables
- Async execution inside sync wrapper isolates event loop
- Each worker thread gets its own event loop

---

### L6 (Platform) — Infrastructure

**Execution Model:** Mixed (`sync` for pure, `async` for I/O)
**Trigger:** Any layer
**Timing:** Varies

**Rules:**
1. DB operations MUST be `async`
2. Redis operations MUST be `async`
3. Pure utilities (hashing, serialization) MUST be `sync`
4. MUST NOT depend on upper layers (L1-L5)

---

## Execution Guarantees (Authoritative)

### Guarantee 1: Deterministic Workflow Execution

**Mechanism:** Seeded execution with checkpoint
**Files:** `workflow/engine.py`, `workflow/checkpoint.py`

**Invariants:**
1. Same seed + same inputs → same outputs
2. Seed propagation: `step_seed = derive_seed(base_seed, step_index)`
3. Jitter is deterministic: `jitter = seeded_random(seed ^ attempt)`
4. Checkpoint captures state for resume

**Replay Contract:**
```
Given:
  - seed = 12345
  - inputs = {task: "Build landing page"}
  - checkpoint = None (fresh)

Then:
  - Step 0 uses seed = derive_seed(12345, 0)
  - Step 1 uses seed = derive_seed(12345, 1)
  - Replay with same seed produces identical step_seeds
```

---

### Guarantee 2: Idempotent Trace Emission

**Mechanism:** Redis Lua script with hash comparison
**Files:** `traces/idempotency.py`

**Invariants:**
1. First call with key → `NEW` (lock acquired)
2. Same hash with same key → `DUPLICATE` (safe replay)
3. Different hash with same key → `CONFLICT` (reject)

**Idempotency Contract:**
```
check(key="run-123", data={task: "X"}) → NEW
check(key="run-123", data={task: "X"}) → DUPLICATE (same hash)
check(key="run-123", data={task: "Y"}) → CONFLICT (different hash)
```

---

### Guarantee 3: At-Least-Once Worker Dispatch

**Mechanism:** Database polling + status tracking
**Files:** `worker/pool.py`, `worker/runner.py`

**Invariants:**
1. Runs in `pending` status will be picked up
2. Worker crash → run stays `pending` → re-picked
3. Successful completion → status = `completed`
4. Idempotency key prevents duplicate effects

**Worker Lifecycle:**
```
DB State:   pending → running → completed/failed
Worker:     poll → claim → execute → update
Crash:      running → (timeout) → pending (re-poll)
```

---

### Guarantee 4: Exactly-Once Step Execution

**Mechanism:** Checkpoint + idempotency key per step
**Files:** `workflow/engine.py`, `workflow/checkpoint.py`

**Invariants:**
1. Step has idempotency_key → checked before execution
2. Checkpoint saves `next_step_index` after success
3. Resume skips completed steps
4. Version-based optimistic locking prevents conflicts

---

## Execution Prohibitions (Forbidden)

### Prohibition 1: Async in Decision Paths

**Forbidden:**
```python
async def evaluate_policy(ctx):
    # FORBIDDEN: Decision is async
    result = await some_async_check()
    return result
```

**Correct:**
```python
def evaluate_policy(ctx):
    # CORRECT: Decision is sync and pure
    return PolicyDecision(allowed=ctx.role in ALLOWED_ROLES)
```

**Reason:** Async decisions create race conditions and make replay non-deterministic.

---

### Prohibition 2: Blocking in Async Context

**Forbidden:**
```python
async def fetch_data():
    time.sleep(1)  # FORBIDDEN: Blocks event loop
    requests.get(url)  # FORBIDDEN: Blocking HTTP
```

**Correct:**
```python
async def fetch_data():
    await asyncio.sleep(1)  # CORRECT: Yields
    async with httpx.AsyncClient() as client:
        await client.get(url)  # CORRECT: Async HTTP
```

---

### Prohibition 3: Import-Time Side Effects

**Forbidden:**
```python
# At module level
connection = create_db_connection()  # FORBIDDEN: Import-time I/O
cached_config = fetch_config()  # FORBIDDEN: Import-time HTTP
```

**Correct:**
```python
# At module level
_connection = None  # Placeholder only

def get_connection():
    global _connection
    if _connection is None:
        _connection = create_db_connection()
    return _connection
```

---

### Prohibition 4: Cross-Layer Async Leaks

**Forbidden:**
```python
# In L5 worker
from app.api.workers import some_handler  # FORBIDDEN: L5 imports L2
await some_handler(request)  # FORBIDDEN: Worker calls API
```

**Correct:**
```python
# In L5 worker
from app.services.worker_write_service import WorkerWriteService
await write_service.upsert_run(...)  # CORRECT: L5 calls L4
```

---

## Execution Context Constraints

| Context | Allowed Execution | Forbidden Execution |
|---------|-------------------|---------------------|
| **API Handler** | async, deferred | sync blocking, sync-over-async |
| **Background Task** | async | sync blocking |
| **Worker Thread** | sync-over-async, async internal | Raw sync blocking |
| **Domain Service** | async (operations), sync (decisions) | Background task initiation |
| **Platform Utility** | sync (pure), async (I/O) | Upper layer imports |

---

## Semantic Ambiguities Resolved

### Ambiguity 1: When is sync-over-async allowed?

**Resolution:**
> Sync-over-async is ONLY allowed at worker entrypoints where ThreadPoolExecutor requires sync callables.

| Location | Sync-Over-Async | Reason |
|----------|-----------------|--------|
| `RunRunner.run()` | ALLOWED | ThreadPool requires sync |
| API handlers | FORBIDDEN | Already in async context |
| Domain services | FORBIDDEN | Should be pure async or sync |

---

### Ambiguity 2: Who owns transaction boundaries?

**Resolution:**
> L4 domain services own transaction boundaries via `session.commit()`.

| Layer | Transaction Role |
|-------|------------------|
| L2 (API) | Opens session via `get_async_session()` |
| L4 (Service) | Calls `commit()` after operations |
| L6 (Platform) | Provides session factory |

**Contract:**
```python
async with get_async_session() as session:
    service = WorkerWriteServiceAsync(session)
    await service.upsert_worker_run(...)
    await service.commit()  # Service owns commit
```

---

### Ambiguity 3: How do retries affect determinism?

**Resolution:**
> Retries are deterministic because jitter is seeded.

**Retry Determinism Contract:**
```
Given:
  - step_seed = 12345
  - attempt = 2
  - base_ms = 1000

Then:
  - jitter = deterministic_jitter(12345, 2, 1000)
  - backoff = 1000 * 2^2 + jitter
  - Same seed + same attempt → same backoff
```

---

### Ambiguity 4: What happens when Redis is unavailable?

**Resolution:**
> Idempotency store fails open (allows through).

**Failover Behavior:**
```python
try:
    result = await redis_store.check(key, data)
except Exception:
    # Fail open: allow through
    return IdempotencyResponse(result=IdempotencyResult.NEW)
```

**Reason:** Availability over consistency for idempotency checks.

---

## Layer Assignment (Execution Authority)

| File | Execution Model | Layer | Authority |
|------|-----------------|-------|-----------|
| `api/workers.py` | async + deferred | L2 | Request boundary |
| `workflow/engine.py` | async | L4 | Deterministic execution |
| `services/*_async.py` | async | L4 | DB write authority |
| `workers/*/worker.py` | async | L5 | Background execution |
| `worker/pool.py` | sync-over-async | L5 | Worker dispatch |
| `worker/runner.py` | sync-over-async | L5 | Run execution |
| `traces/idempotency.py` | async | L6 | Idempotency authority |
| `traces/store.py` | async | L6 | Trace persistence |

---

## Completion Criteria

Phase 3.2 Execution Semantics is **COMPLETE** when:

1. All execution axes defined (timing, model, guarantee, failure)
2. Layer execution rules documented
3. Execution guarantees documented with mechanisms
4. Execution prohibitions documented
5. Ambiguities resolved
6. Human review approves this contract

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-30 | Contract drafted | Discovery phase complete |
| 2025-12-30 | 4 execution axes defined | WHEN, HOW, WHAT, WHAT IF |
| 2025-12-30 | 4 guarantees documented | Determinism, idempotency, at-least-once, exactly-once |
| 2025-12-30 | 4 prohibitions documented | Async decisions, blocking, import-time I/O, cross-layer leaks |
| 2025-12-30 | 4 ambiguities resolved | sync-over-async, transactions, retries, Redis failover |

---

## Forward Rule (MANDATORY)

**Adopted:** 2025-12-30

> **Any semantic-boundary file (execution, async/sync, retry, worker entrypoint) must include an explicit semantic header before modification.**

**Semantic-Boundary Files Include:**
- Files that initiate execution
- Files that wrap async/sync transitions
- Files that own retries or idempotency
- Worker entrypoints
- L4/L5/L6 files that cross layer boundaries

**This is NOT a mass refactor mandate.**
Headers are added **on modification only**, not retroactively.

---

## Review Required

**Status:** DRAFT — Awaiting Semantic Spot Audit (ARCH-GOV-014)

**Pre-Approval Gate (MANDATORY):**
Per ARCH-GOV-014, phase approval requires a Semantic Spot Audit verifying code-level alignment with declared semantics.

**Audit Scope:**
- Minimum 5 files from execution-related code
- Must span multiple layers (L2, L4, L5, L6)
- Must include: semantically neutral, authority, and boundary files

**To Trigger Audit:** Say "Run Semantic Spot Audit"

**After Audit Passes:**
- Say "Execution Semantic Contract approved — proceed to Phase 3.3"

**To Revise:** Say "Execution Semantics needs revision — [specify concerns]"
