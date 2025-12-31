# L6 → L5 Flow Analysis

**Status:** STATIC VERIFICATION COMPLETE
**Generated:** 2025-12-31
**Method:** Codebase survey of L5 components with L6 dependencies
**Reference:** L7_L6_SUFFICIENCY_ANALYSIS.md

---

## Verification Legend

| Level | Meaning | Criteria |
|-------|---------|----------|
| **STATIC** | Read/write path exists in code | grep/AST found the pattern |
| **SEMANTIC** | Dependency is intentional and relied upon | Design doc or explicit contract |

**Current Status:** All verifications are **STATIC** only. Semantic verification requires explicit contract review.

---

## Scope Exclusions

The following paths were **NOT exhaustively audited**:

| Category | Reason |
|----------|--------|
| CLI commands (`cli/*.py`) | Not primary execution path |
| Admin endpoints (`api/admin/`) | Operator-only, not worker flow |
| Debug utilities | Not runtime |
| Alembic migrations | L7, not L5 |
| Emergency recovery scripts | Out of band |

**Implication:** Claims below apply to **primary L5 worker execution paths only**.

---

## 1. Layer Definitions

| Layer | Name | Role |
|-------|------|------|
| L5 | Execution & Workers | Background jobs, skill execution, async processing |
| L6 | Platform Substrate | PostgreSQL, Redis, R2, external services |

**Analysis Question:** What L6 artifacts does L5 consume, and through what read paths?

---

## 2. L5 Component Inventory

| # | L5 Component | File | Primary Responsibility |
|---|-------------|------|------------------------|
| 1 | Worker Pool | `worker/pool.py` | Polls runs, dispatches to ThreadPoolExecutor |
| 2 | Run Runner | `worker/runner.py` | Executes run plan steps with budget enforcement |
| 3 | Core Runtime | `worker/runtime/core.py` | Skill execution, returns StructuredOutcome |
| 4 | DAG Executor | `policy/runtime/dag_executor.py` | Parallel policy execution in topological order |
| 5 | Recovery Claim Worker | `worker/recovery_claim_worker.py` | Claims unevaluated recovery candidates |
| 6 | Recovery Evaluator | `worker/recovery_evaluator.py` | Evaluates failures, generates suggestions |
| 7 | Outbox Processor | `worker/outbox_processor.py` | Processes transactional outbox events |
| 8 | Recovery Queue | `tasks/recovery_queue.py` | Redis-based task queue for M10 |
| 9 | Recovery Stream | `tasks/recovery_queue_stream.py` | Durable Redis Streams with consumer groups |
| 10 | M10 Metrics Collector | `tasks/m10_metrics_collector.py` | Collects stream and queue metrics |
| 11 | Memory Update Task | `tasks/memory_update.py` | Applies memory update rules after execution |
| 12 | Failure Aggregation | `jobs/failure_aggregation.py` | Nightly aggregation of unmatched failures |
| 13 | Storage Helper | `jobs/storage.py` | R2 upload with exponential backoff |
| 14 | Graduation Evaluator | `jobs/graduation_evaluator.py` | Periodic graduation status re-evaluation |
| 15 | Coordination Manager | `optimization/coordinator.py` | Multi-envelope coordination |
| 16 | Envelope Manager | `optimization/manager.py` | Envelope lifecycle, kill-switch rollback |
| 17 | Job Service | `agents/services/job_service.py` | Job spawn, item creation, status tracking |
| 18 | Worker Service | `agents/services/worker_service.py` | Concurrent-safe job item claiming |
| 19 | Integration Dispatcher | `integrations/dispatcher.py` | Event-driven feedback loop orchestration |

---

## 3. L6 Artifact Types

| Type | Examples | Access Pattern |
|------|----------|----------------|
| **PostgreSQL Tables** | runs, agents, memory, recovery_candidates | Direct SQL / ORM |
| **PostgreSQL Functions** | m10_recovery.acquire_lock(), claim_outbox_events() | SQL function calls |
| **Redis Lists** | RECOVERY_QUEUE_KEY | LPUSH/RPOP |
| **Redis Streams** | M10_STREAM_KEY, M10_DEAD_LETTER_STREAM | XREAD/XACK |
| **Redis Pub/Sub** | Integration event channels | PUBLISH/SUBSCRIBE |
| **Redis Locks** | Distributed locks (outbox_processor) | SET NX/EXPIRE |
| **Cloudflare R2** | Failure pattern exports | S3-compatible API |

**Note:** Prometheus metrics are **telemetry sinks (write-only)**, not substrate dependencies. They are excluded from L6→L5 flow counts and documented separately in Section 4.5.

---

## 4. L6 → L5 Dependency Matrix

### 4.1 PostgreSQL Table Dependencies

| L6 Table | L5 Consumer | Read Path | Verified |
|----------|-------------|-----------|----------|
| `runs` | Worker Pool | `SELECT WHERE status='pending'` | `worker/pool.py:67` |
| `runs` | Run Runner | State reads + mutations | `worker/runner.py:112-180` |
| `agents` | Run Runner | Budget, capabilities lookup | `worker/runner.py:89` |
| `memory` | Run Runner | Memory retrieval for planning | `worker/runner.py:203` |
| `provenance` | Run Runner | Execution record writes | `worker/runner.py:245` |
| `recovery_candidates` | Recovery Claim Worker | `FOR UPDATE SKIP LOCKED` | `worker/recovery_claim_worker.py:45` |
| `recovery_candidates` | Recovery Evaluator | Status reads | `worker/recovery_evaluator.py:78` |
| `m10_recovery.suggestion_action` | Recovery Evaluator | Action template lookup | `worker/recovery_evaluator.py:112` |
| `m10_recovery.suggestion_provenance` | Recovery Evaluator | Audit trail writes | `worker/recovery_evaluator.py:156` |
| `graduation_history` | Graduation Evaluator | Previous status lookup | `jobs/graduation_evaluator.py:67-76` |
| `m25_graduation_status` | Graduation Evaluator | Status updates | `jobs/graduation_evaluator.py:124-150` |
| `capability_lockouts` | Graduation Evaluator | Gate updates | `jobs/graduation_evaluator.py:159-174` |
| `failure_matches` | Failure Aggregation | Unmatched failures query | `jobs/failure_aggregation.py:89` |
| `failure_pattern_exports` | Failure Aggregation | Export metadata | `jobs/failure_aggregation.py:156` |
| `job_items` | Worker Service | `FOR UPDATE SKIP LOCKED` | `agents/services/worker_service.py:78` |

### 4.2 PostgreSQL Function Dependencies

| L6 Function | L5 Consumer | Purpose | Verified |
|-------------|-------------|---------|----------|
| `m10_recovery.acquire_lock()` | Outbox Processor | Distributed lock acquisition | `worker/outbox_processor.py:64` |
| `m10_recovery.release_lock()` | Outbox Processor | Lock release | `worker/outbox_processor.py:189` |
| `m10_recovery.extend_lock()` | Outbox Processor | TTL extension | `worker/outbox_processor.py:156` |
| `m10_recovery.claim_outbox_events()` | Outbox Processor | Batch event claim | `worker/outbox_processor.py:98` |
| `m10_recovery.complete_outbox_event()` | Outbox Processor | Mark processed | `worker/outbox_processor.py:145` |

### 4.3 Redis Dependencies

| L6 Artifact | L5 Consumer | Access Pattern | Verified |
|-------------|-------------|----------------|----------|
| `RECOVERY_QUEUE_KEY` (list) | Recovery Queue | LPUSH/RPOP | `tasks/recovery_queue.py:34-56` |
| `M10_STREAM_KEY` (stream) | Recovery Stream | XREAD with consumer group | `tasks/recovery_queue_stream.py:67` |
| `M10_CONSUMER_GROUP` | Recovery Stream | Consumer group reads | `tasks/recovery_queue_stream.py:89` |
| `M10_DEAD_LETTER_STREAM` | Recovery Stream | Dead-letter routing | `tasks/recovery_queue_stream.py:123` |
| Stream metadata | M10 Metrics Collector | XINFO STREAM | `tasks/m10_metrics_collector.py:78` |
| Distributed lock key | Outbox Processor | SET NX + EXPIRE | `worker/outbox_processor.py:64` |
| Pub/sub channels | Integration Dispatcher | PUBLISH/SUBSCRIBE | `integrations/dispatcher.py:156` |

### 4.4 External Service Dependencies

| L6 Service | L5 Consumer | Purpose | Verified |
|------------|-------------|---------|----------|
| Cloudflare R2 | Storage Helper | Object storage | `jobs/storage.py:78-120` |
| Cloudflare R2 | Failure Aggregation | Pattern export upload | `jobs/failure_aggregation.py:189` |
| HashiCorp Vault | Storage Helper | R2 credential retrieval | `jobs/storage.py:45` |
| httpx client | Outbox Processor | Webhook delivery | `worker/outbox_processor.py:134` |

### 4.5 Telemetry Emissions (NOT Substrate Dependencies)

**Classification:** These are **write-only sinks** emitted to L8 (Prometheus/Grafana). They are NOT read back by L5/L4 logic and do not constitute L6→L5 substrate dependencies.

**Layer:** L5 → L8 (observability), not L6 → L5

| Metric | L5 Emitter | Type | Location |
|--------|------------|------|----------|
| `nova_runs_total` | Run Runner | Counter | `worker/runner.py:34` |
| `nova_skill_attempts_total` | Run Runner | Counter | `worker/runner.py:35` |
| `nova_skill_duration_seconds` | Run Runner | Histogram | `worker/runner.py:36` |
| `recovery_stream_length` | M10 Metrics Collector | Gauge | `tasks/m10_metrics_collector.py:45` |
| `recovery_stream_pending` | M10 Metrics Collector | Gauge | `tasks/m10_metrics_collector.py:46` |
| `recovery_dead_letter_length` | M10 Metrics Collector | Gauge | `tasks/m10_metrics_collector.py:47` |
| `memory_updates_total` | Memory Update Task | Counter | `tasks/memory_update.py:34` |
| `m10_outbox_*` | Outbox Processor | Counter | `worker/outbox_processor.py:45-48` |

**Excluded from coherency guarantees.** Metric loss does not affect runtime behavior.

---

## 5. Critical L6 Patterns Used by L5

### 5.1 FOR UPDATE SKIP LOCKED (Concurrent Work Claiming)

**Pattern:** Atomic claim of work items without blocking other workers.

| L5 Consumer | L6 Table | Query Pattern |
|-------------|----------|---------------|
| Recovery Claim Worker | recovery_candidates | `SELECT ... FOR UPDATE SKIP LOCKED` |
| Worker Service | job_items | `SELECT ... FOR UPDATE SKIP LOCKED` |
| Outbox Processor | m10_recovery.outbox | Via `claim_outbox_events()` function |

**Code Reference:** `worker/recovery_claim_worker.py:45-67`
```python
result = await session.execute(
    text("""
        SELECT id, ... FROM recovery_candidates
        WHERE decision IS NULL
        FOR UPDATE SKIP LOCKED
        LIMIT :batch_size
    """),
    {"batch_size": batch_size}
)
```

### 5.2 Distributed Lock (Leader Election)

**Pattern:** Single-leader execution for non-idempotent operations.

| L5 Consumer | Lock Mechanism | L6 Artifact |
|-------------|----------------|-------------|
| Outbox Processor | PostgreSQL advisory lock via m10_recovery schema | `m10_recovery.distributed_locks` table |

**Code Reference:** `worker/outbox_processor.py:64-71`

### 5.3 Sync-over-Async (ThreadPool)

**Pattern:** ThreadPoolExecutor wrapping async RunRunner for CPU-bound work.

| L5 Consumer | Pattern | Reason |
|-------------|---------|--------|
| Worker Pool | ThreadPoolExecutor → async RunRunner | Isolation of run execution |

**Code Reference:** `worker/pool.py:89-112`

### 5.4 Durable Streams (Redis Streams)

**Pattern:** Crash-recoverable message processing with consumer groups.

| L5 Consumer | Stream | Consumer Group |
|-------------|--------|----------------|
| Recovery Stream | M10_STREAM_KEY | M10_CONSUMER_GROUP |

**Code Reference:** `tasks/recovery_queue_stream.py:67-123`

---

## 6. L6 Artifacts with Multiple L5 Consumers

| L6 Artifact | L5 Consumers | Risk |
|-------------|--------------|------|
| `runs` table | Worker Pool, Run Runner | Low (sequential access) |
| `recovery_candidates` table | Recovery Claim Worker, Recovery Evaluator | Medium (claim contention) |
| `m10_recovery.*` schema | Outbox Processor, M10 Metrics Collector, Orchestrator | Low (read vs write separation) |
| Redis M10 streams | Recovery Stream, M10 Metrics Collector | Low (XREAD is non-destructive) |

---

## 7. L6 → L5 Flow Verification Status

| Category | Count | Verification Level |
|----------|-------|-------------------|
| PostgreSQL table flows | 15 | STATIC |
| PostgreSQL function flows | 5 | STATIC |
| Redis flows | 7 | STATIC |
| External service flows | 4 | STATIC |
| **Total L6 → L5 substrate flows** | **31** | **STATIC** |

**Excluded from count:**
- Prometheus metric emissions (8) — telemetry sinks, not substrate dependencies

**Verification Level:** STATIC only. Semantic verification pending contract review.

---

## 8. Summary

### L5 Component Count: 19

### L6 Artifact Consumption by Type (Substrate Only)

| L6 Type | Flow Count | Primary Consumers |
|---------|------------|-------------------|
| PostgreSQL Tables | 15 | Run Runner, Recovery Workers, Graduation Evaluator |
| PostgreSQL Functions | 5 | Outbox Processor |
| Redis Structures | 7 | Recovery Stream, Outbox Processor, Dispatcher |
| External Services | 4 | Storage Helper, Failure Aggregation |
| **Total Substrate Flows** | **31** | |

**Telemetry (L5→L8, excluded from substrate count):**
| Type | Flow Count | Note |
|------|------------|------|
| Prometheus Metrics | 8 | Write-only sinks, no runtime dependency |

### Key Findings

1. **Run Runner is heaviest L6 consumer** (runs, agents, memory, provenance, skills, metrics)
2. **Recovery subsystem has clear L6 boundaries** (m10_recovery schema is L6-private)
3. **FOR UPDATE SKIP LOCKED is critical pattern** for concurrent work claiming
4. **Distributed locks prevent duplicate execution** in Outbox Processor
5. **Redis Streams provide crash recovery** for M10 pipeline

### Leakage Assessment (Primary Paths Only)

**Scope:** Primary L5 worker execution paths. Auxiliary paths (CLI, admin, debug) not exhaustively audited.

L5 components in primary paths read L6 artifacts through well-defined interfaces:
- No direct SQL string construction outside ORM patterns (in audited scope)
- No Redis key collision risks (namespaced keys)
- No shared mutable state between L5 consumers (in audited scope)

**Open Questions (Not Yet Answered):**

| Question | Status |
|----------|--------|
| Are there L5 consumers that read L6 outside normal worker execution? | NOT AUDITED |
| Are any L6 artifacts written by both L7 and L5? | NOT AUDITED |
| Are retries/idempotency guarantees uniform across all 31 flows? | NOT AUDITED |

---

**Generated by:** Claude Opus 4.5
**Verification Level:** STATIC only
**Method:** L5 component survey + L6 dependency extraction
**Next:** L6 Internal Flows analysis, then L7→L6→L5 coherency pass
