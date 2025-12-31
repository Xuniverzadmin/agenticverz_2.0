# Worker Lifecycle Semantic Contract

**Status:** ✅ APPROVED — FROZEN
**Phase:** 3.3 (CLOSED 2025-12-30)
**Approved:** 2025-12-30
**Created:** 2025-12-30
**Predecessor:** EXECUTION_SEMANTIC_CONTRACT.md

---

## Purpose

This contract defines the **semantic meaning** of workers and their lifecycle states.

**Core Principle:**
> A worker is not a process. A worker is a **semantic boundary** that owns a specific type of work and guarantees specific properties about that work.

---

## Semantic Axes (4 Axes)

### Axis 1: Representation (WHAT)

**Question:** What does a worker represent?

| Concept | Semantic Meaning |
|---------|------------------|
| Worker | A processing boundary that owns a specific type of work |
| Run | A unit of work with a goal, plan, and deterministic lifecycle |
| Step | An atomic operation within a run |
| Checkpoint | A recovery point for resume-after-failure |

**Key Distinction:**
- **Worker** = boundary (owns dispatch, isolation, concurrency)
- **Run** = work unit (owns goal, plan, state)
- **Runtime** = execution context (owns skills, budget, state queries)

### Axis 2: Authority (WHO OWNS WHAT)

**Question:** Who has authority over what state?

| Authority Holder | Owns | Cannot Touch |
|------------------|------|--------------|
| WorkerPool | Run claim (queued → running) | Run completion, step execution |
| RunRunner | Run lifecycle (running → succeeded/failed/halted) | Other runs, pool state |
| OutboxProcessor | External side-effect delivery | Run state, DB mutations |
| WorkflowEngine | Step execution, checkpoint state | Run dispatch, external delivery |
| RecoveryWorkers | Recovery candidate state | Run execution, policy decisions |

**Authority Rule:**
> Authority is exclusive. Two workers cannot own the same state transition.

### Axis 3: Lifecycle (WHEN)

**Question:** What are the lifecycle states and their semantic meaning?

#### Run States

| State | Semantic Meaning | Transition Authority |
|-------|------------------|---------------------|
| `queued` | Work submitted, awaiting dispatch | API (creation only) |
| `running` | Work in progress, resources allocated | WorkerPool (claim) |
| `succeeded` | Work completed, all steps executed | RunRunner (completion) |
| `failed` | Work permanently failed, no more retries | RunRunner (exhaustion) |
| `retry` | Work temporarily failed, will be retried | RunRunner (transient) |
| `halted` | Work stopped cleanly by policy, partial completion | RunRunner (policy) |

**State Semantics:**

1. **queued** — Intent declared, not yet committed
   - No resources allocated
   - Can be cancelled without side effects
   - Ordered by (priority DESC, created_at ASC)

2. **running** — Resources committed
   - Worker thread allocated
   - Budget tracking active
   - Steps executing sequentially

3. **succeeded** — Contract fulfilled
   - All steps completed
   - Provenance record created
   - Final and immutable

4. **failed** — Contract broken after best effort
   - Max attempts exhausted
   - Error recorded
   - Final and immutable

5. **retry** — Contract interrupted, will resume
   - Exponential backoff scheduled
   - State preserved
   - Will transition to running again

6. **halted** — Contract cleanly stopped
   - Policy limit reached (budget, time, step count)
   - Partial results preserved
   - NOT a failure — deliberate stop
   - Final and immutable

#### State Transition Rules

```
        ┌──────────────────────────────────────────────────────┐
        │                                                      │
        ▼                                                      │
    [queued] ──────► [running] ──────► [succeeded]             │
                        │                                      │
                        ├──────────► [failed]                  │
                        │                                      │
                        ├──────────► [halted]                  │
                        │                                      │
                        └──────────► [retry] ──────────────────┘
```

**Invariants:**
- `succeeded`, `failed`, `halted` are **terminal** (no outbound transitions)
- `retry` always transitions back to `running` (via pool dispatch)
- `running` is the only state where work executes

### Axis 4: Guarantees (WHAT IS PROMISED)

**Question:** What guarantees does each worker provide?

| Worker | Guarantee | Scope |
|--------|-----------|-------|
| WorkerPool | At-least-once dispatch | Per run |
| RunRunner | Exactly-once completion recording | Per run |
| OutboxProcessor | Exactly-once external delivery | Per event |
| WorkflowEngine | Deterministic replay | Per workflow |
| RecoveryWorkers | At-least-once evaluation | Per candidate |

---

## Semantic Contracts by Worker Type

### WorkerPool Semantics

```
SEMANTIC CONTRACT: WorkerPool

REPRESENTATION:
  - Dispatcher that polls for queued runs
  - Does NOT execute runs (delegates to RunRunner)

AUTHORITY:
  - Claims runs (queued/retry → running)
  - Tracks active runs (in-memory, non-authoritative)

GUARANTEES:
  - At-least-once dispatch (run will be dispatched at least once)
  - Graceful shutdown (waits for running tasks before exit)
  - Concurrent-safe (multiple pools can run)

PROHIBITIONS:
  - Cannot execute run logic
  - Cannot modify run outcome (succeeded/failed)
  - Cannot skip runs (FIFO with priority)

FAILURE MODE:
  - Pool crash: Running runs may be re-dispatched (idempotency required)
  - DB unavailable: Poll loop retries with backoff
```

### RunRunner Semantics

```
SEMANTIC CONTRACT: RunRunner

REPRESENTATION:
  - Executor for a single run's plan steps
  - Owns the entire lifecycle from running to terminal

AUTHORITY:
  - Run state mutations (status, attempts, timestamps)
  - Provenance record creation
  - Budget enforcement (hard budget halt)

GUARANTEES:
  - Exactly-once completion recording (DB transaction)
  - Deterministic step execution (seeded RNG, replay-safe)
  - Clean halt on policy limits (not crash, not failure)

PROHIBITIONS:
  - Cannot dispatch other runs
  - Cannot modify pool state
  - Cannot bypass budget limits

FAILURE MODE:
  - Transient error: Increment attempts, schedule retry
  - Permanent error: Mark failed after max_attempts
  - Budget exhausted: Mark halted (clean stop, not failure)
```

### OutboxProcessor Semantics

```
SEMANTIC CONTRACT: OutboxProcessor

REPRESENTATION:
  - External side-effect delivery worker
  - Transactional outbox pattern implementation

AUTHORITY:
  - Outbox event claiming (FOR UPDATE SKIP LOCKED)
  - External HTTP/webhook delivery
  - Dead-letter after max retries

GUARANTEES:
  - Exactly-once delivery (idempotency keys)
  - Concurrent-safe (distributed lock + skip locked)
  - Ordered delivery per aggregate (FIFO within aggregate_id)

PROHIBITIONS:
  - Cannot modify run state
  - Cannot execute skills
  - Cannot create new outbox events

FAILURE MODE:
  - HTTP failure: Retry with exponential backoff
  - Max retries: Move to dead-letter
  - Lock contention: Skip and retry next poll
```

### WorkflowEngine Semantics

```
SEMANTIC CONTRACT: WorkflowEngine

REPRESENTATION:
  - Deterministic workflow execution engine
  - Checkpoint and resume capability

AUTHORITY:
  - Step execution ordering
  - Checkpoint state persistence
  - Step result aggregation

GUARANTEES:
  - Deterministic execution (same seed → same outputs)
  - Checkpoint recovery (resume from last checkpoint)
  - Golden-file compatibility (CI replay verification)

PROHIBITIONS:
  - Cannot use non-deterministic operations without seed
  - Cannot skip policy enforcement between steps
  - Cannot modify step results post-execution

FAILURE MODE:
  - Step failure: Apply on_error policy (abort/continue/retry)
  - Checkpoint failure: Abort with checkpoint-save-failed error
```

---

## Ambiguities Resolved

### Ambiguity 1: What is "halted" vs "failed"?

**Resolution:**
- **halted** = Clean policy stop. Work stopped because a limit was reached, not because of error.
- **failed** = Error after best effort. Max retries exhausted, error recorded.

**Semantic Distinction:**
```
halted: "I stopped because you told me to stop"
failed: "I stopped because I couldn't continue"
```

### Ambiguity 2: Can a run be retried after "halted"?

**Resolution:** No. Halted is terminal.

**Rationale:** Halted means a policy decision was made. Re-running would require a new run with different policy (higher budget, etc.).

### Ambiguity 3: Who owns retry scheduling?

**Resolution:** RunRunner owns retry scheduling. WorkerPool only dispatches.

**Flow:**
1. RunRunner catches transient error
2. RunRunner sets status=retry, next_attempt_at=<backoff>
3. WorkerPool polls, finds retry run with next_attempt_at <= now
4. WorkerPool dispatches (increments attempts)
5. RunRunner executes again

### Ambiguity 4: What happens to partial results on halt?

**Resolution:** Partial results are preserved.

**Contract:**
- tool_calls_json contains all completed steps
- Provenance record created with status=halted
- Error message indicates halt reason (budget, policy)

---

## Prohibitions

### P1: No Orphan Work Units

A run MUST NOT exist in `running` status indefinitely.

**Enforcement:**
- Stale run detection (running for > threshold)
- Worker heartbeat tracking
- Automatic recovery claim for orphans

### P2: No Silent State Changes

All state transitions MUST be recorded in the database before being acted upon.

**Enforcement:**
- DB write before external action
- No in-memory-only state for authoritative data

### P3: No Cross-Worker State Mutation

Workers MUST NOT modify state owned by other workers.

**Enforcement:**
- Authority boundaries in code
- DB constraints (status transition checks)

### P4: No Non-Deterministic Retries

Retry logic MUST be deterministic (seeded backoff, reproducible jitter).

**Enforcement:**
- _deterministic_jitter() in workflow engine
- Seeded RNG for all retry calculations

---

## Lifecycle Invariants

### LI-1: Terminal State Immutability

Once a run reaches `succeeded`, `failed`, or `halted`, its status CANNOT change.

### LI-2: Attempt Monotonicity

`attempts` MUST only increase, never decrease.

### LI-3: Timestamp Ordering

`created_at <= started_at <= completed_at` (when all are present)

### LI-4: Provenance Completeness

Every terminal run MUST have a provenance record.

### LI-5: Idempotency Key Uniqueness

No two runs with the same `idempotency_key` can exist in non-terminal state.

---

## References

- EXECUTION_SEMANTIC_CONTRACT.md: Execution model guarantees
- AUTH_SEMANTIC_CONTRACT.md: Authorization semantics
- PIN-251: Phase 3 Semantic Alignment
- PIN-005: Machine-Native Architecture

---

## Session Handoff

**Status:** ✅ APPROVED — FROZEN (2025-12-30)

> **PHASE 3.3 CLOSED:** This contract is now frozen and immutable.
> Worker Lifecycle semantics are locked. Future changes require formal amendment process.

**Ambiguities Resolved:** 4
**Prohibitions Defined:** 4
**Lifecycle Invariants:** 5

**Ratification Sequence (COMPLETE):**
1. ✅ Discovery notes produced (Pre-Phase 3.3)
2. ✅ Phase 3.3 formally entered (Gate satisfied)
3. ✅ Affordance Check against Semantic Auditor (65 signals, all classified)
4. ✅ SSA on worker files (4/4 core files MATCH)
5. ✅ Final review for tightenings (1 deferred to Phase 3.5)
6. ✅ APPROVED and FROZEN

**Approval Notes:**
- Auditor signals acknowledged as observational (not violations)
- WRITE_OUTSIDE_WRITE_SERVICE in workers is correct by definition
- Transaction Authority exclusion to be codified in Phase 3.5
- No semantic gaps remain within scope
