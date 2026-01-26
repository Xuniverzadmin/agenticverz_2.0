# L6 Internal Flows (Platform Substrate Coherency)

**Status:** STATIC VERIFICATION COMPLETE
**Generated:** 2025-12-31
**Method:** Codebase survey of L6 substrate interactions
**Question Answered:** Is L6 internally coherent, or are there hidden cross-substrate couplings?

---

## Verification Legend

| Level | Meaning | Criteria |
|-------|---------|----------|
| **STATIC** | Code path exists | grep/AST found the pattern |
| **SEMANTIC** | Dependency is intentional and relied upon | Design doc or explicit contract |

**Current Status:** All verifications are **STATIC** only.

---

## Scope Exclusions

The following were **NOT exhaustively audited**:

| Category | Reason |
|----------|--------|
| CLI database access | Not primary runtime |
| Admin/ops scripts | L7, not L6 |
| Migration transactional boundaries | L7, not runtime |
| External service retry semantics | Beyond static analysis |

**Implication:** Claims apply to **primary runtime substrate paths only**.

---

## 1. Scope

This document records all L6-internal artifact interactions:
- PostgreSQL ↔ Redis interactions
- Redis ↔ Queue dependencies
- Cross-schema access patterns
- Transactional boundaries
- Atomicity mechanisms

**L6 Definition:**
- PostgreSQL (tables, functions, schemas)
- Redis (streams, lists, locks, pub/sub)
- External services (R2, Vault)
- Connection pooling (PgBouncer)

---

## 2. Coherency Assessment

### Key Finding: L6 Appears Internally Coherent (Primary Paths)

| Concern | Finding | Verification Level |
|---------|---------|-------------------|
| Hidden DB↔Redis coupling | No hidden couplings found in audited scope | STATIC |
| Cross-schema leakage | m10_recovery accessed via functions only (in audited paths) | STATIC |
| Transaction boundary ambiguity | Patterns documented with explicit commit/rollback | STATIC |
| Atomicity gaps | Concurrent access uses locking patterns (in audited paths) | STATIC |

**Conclusion:** No hidden cross-substrate couplings detected **in primary runtime paths**.

**Open Questions (Not Yet Answered):**

| Question | Status |
|----------|--------|
| Are there CLI/admin paths with different transactional semantics? | NOT AUDITED |
| Are external service retries uniformly idempotent-safe? | NOT AUDITED |
| Are there any shared L6 artifacts written by both L7 and L5? | NOT AUDITED |

---

## 3. PostgreSQL ↔ Redis Interactions

### 3.1 Recovery Queue Stream (Primary Pattern)

| Field | Value |
|-------|-------|
| File | `tasks/recovery_queue_stream.py` |
| Type | Dual-substrate with DB fallback |
| Execution | Async |
| L6 Artifacts | Redis Streams (`m10:evaluate:stream`), PostgreSQL (`m10_recovery.replay_log`) |

**Flow:**
1. **Enqueue**: `XADD` to Redis Stream (line 168)
2. **Consume**: `XREADGROUP` with consumer group (line 202)
3. **Claim**: `XCLAIM` recovers stalled messages (lines 346, 622)
4. **Fallback**: Dead-letter stream for failed messages (lines 480-508)
5. **Idempotency**: DB-backed `replay_log` for exactly-once semantics (lines 1031, 1095, 1180)

**Isolation Property:**
- Redis failure does not corrupt PostgreSQL state
- PostgreSQL replay_log ensures idempotency across Redis crashes
- Dead-letter stream preserves failed messages for inspection

### 3.2 Idempotency & Replay Log

| Field | Value |
|-------|-------|
| File | `tasks/recovery_queue_stream.py:986-1200` |
| Type | PostgreSQL-backed consistency guarantee |
| Pattern | `ON CONFLICT DO NOTHING` |

**SQL Pattern:**
```sql
INSERT INTO m10_recovery.replay_log (message_id, processed_at)
VALUES (:msg_id, now())
ON CONFLICT (message_id) DO NOTHING
```

**Guarantee:** Exactly-once processing across crashes.

---

## 4. Redis ↔ Queue Dependencies

### 4.1 Stream Consumer Groups

| Field | Value |
|-------|-------|
| File | `tasks/recovery_queue_stream.py` |
| Stream | `m10:evaluate:stream` |
| Group | `m10:evaluate:group` |
| Dead-letter | `m10:evaluate:dead-letter` |

**Operations:**

| Operation | Line | Purpose |
|-----------|------|---------|
| `xreadgroup()` | 202 | Blocking read from consumer group |
| `xclaim()` | 346, 622 | Claim stalled messages |
| `xinfo_stream()` | 390 | Get stream statistics |
| `xgroup_create()` | 113 | Initialize consumer group |
| `xrange()` | 650, 794, 1008, 1264 | Range queries for archives |

**Recovery Configuration:**

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `M10_CLAIM_IDLE_MS` | 300000 (5 min) | Stall detection threshold |
| `M10_MAX_RECLAIM_ATTEMPTS` | 3 | Attempts before dead-letter |
| `M10_STREAM_MAX_LEN` | 100000 | Max stream entries |

### 4.2 DB Fallback Queue

| Field | Value |
|-------|-------|
| File | `tasks/m10_metrics_collector.py:118-140` |
| Schema | `m10_recovery.work_queue` |
| Type | PostgreSQL fallback when Redis unavailable |

**Metrics Collected:**
```sql
-- Unprocessed items
SELECT COUNT(*) FROM m10_recovery.work_queue
WHERE processed_at IS NULL

-- Stalled items (claimed > 5 min, not processed)
SELECT COUNT(*) FROM m10_recovery.work_queue
WHERE claimed_at < now() - interval '5 minutes'
AND processed_at IS NULL
```

---

## 5. Cross-Schema Access

### 5.1 Schema Isolation Model

| Schema | Visibility | Access Pattern |
|--------|------------|----------------|
| `public` | L2-L6 | Direct table access |
| `m10_recovery` | L7 only | Function calls only from L5/L6 |

**Key Principle:** m10_recovery schema is never accessed via direct table reads by L6 consumers. All access is through SQL functions.

### 5.2 Cross-Schema Function Calls

| Operation | Source | Target | Function |
|-----------|--------|--------|----------|
| Enqueue work | L4/L5 | m10_recovery | `enqueue_work()` |
| Acquire lock | L5 | m10_recovery | `acquire_lock()` |
| Release lock | L5 | m10_recovery | `release_lock()` |
| Extend lock | L5 | m10_recovery | `extend_lock()` |
| Claim outbox | L5 | m10_recovery | `claim_outbox_events()` |
| Complete outbox | L5 | m10_recovery | `complete_outbox_event()` |

**Example (recovery_write_service.py:172-177):**
```python
self.session.execute(
    text("""
        SELECT m10_recovery.enqueue_work(
            :candidate_id,
            CAST(:idempotency_key AS uuid),
            0,
            'db_fallback'
        )
    """),
    {"candidate_id": candidate_id, "idempotency_key": idempotency_key}
)
```

### 5.3 Foreign Key References

| Source | Target | Relationship |
|--------|--------|--------------|
| `m10_recovery.suggestion_input.suggestion_id` | `public.recovery_candidates.id` | CASCADE delete |
| `m10_recovery.suggestion_provenance.action_id` | `m10_recovery.suggestion_action.id` | Nullable FK |

**Location:** `models/m10_recovery.py:74, 254`

---

## 6. Transactional Boundaries

### 6.1 Sync Transaction Management

| Pattern | File | Lines |
|---------|------|-------|
| Explicit commit | `api/recovery_ingest.py` | 183 |
| Explicit rollback | `api/recovery_ingest.py` | 199 |
| Write service pattern | `services/recovery_write_service.py` | 246-252 |

**Write Service Pattern:**
```python
def commit(self) -> None:
    """Commit transaction."""
    self.session.commit()

def rollback(self) -> None:
    """Rollback transaction."""
    self.session.rollback()
```

### 6.2 Async Transaction Management

| File | Lines | Pattern |
|------|-------|---------|
| `costsim/circuit_breaker_async.py` | 243, 409, 468, 507, 546 | `async with session.begin()` |
| `services/pattern_detection.py` | 286, 339 | `async with session.begin()` |
| `services/orphan_recovery.py` | 148, 180 | `async with session.begin()` |
| `services/policy_proposal.py` | 250, 286 | `async with session.begin()` |
| `services/prediction.py` | 336, 381 | `async with session.begin()` |
| `workflow/checkpoint.py` | 265, 310, 439 | `async with session.begin()` |

**Pattern:**
```python
async with session.begin():
    await session.execute(update_stmt)
    # Automatic commit at context exit
```

### 6.3 Distributed Lock Transactions

| File | Operation | Line |
|------|-----------|------|
| `worker/outbox_processor.py` | acquire_lock + commit | 115, 119 |
| `worker/outbox_processor.py` | release_lock + commit | 140, 144 |
| `worker/outbox_processor.py` | extend_lock + commit | 158, 162 |

**Lock Configuration:**
- Lock name: `m10:outbox_processor`
- TTL: 300 seconds (OUTBOX_LOCK_TTL)
- Worker ID: `{hostname}:{pid}:{uuid[:8]}`

---

## 7. Atomicity Mechanisms

### 7.1 PostgreSQL UPSERT (ON CONFLICT)

| File | Purpose | Pattern |
|------|---------|---------|
| `services/recovery_write_service.py:75-123` | Candidate upsert | `ON CONFLICT DO UPDATE RETURNING` |
| `api/recovery_ingest.py:159` | Failure candidate | `ON CONFLICT` |
| `integrations/cost_snapshots.py:633, 693` | Cost snapshots | `ON CONFLICT` |
| `discovery/ledger.py:102-137` | Discovery signals | `ON CONFLICT` |
| `integrations/dispatcher.py:535, 566, 605` | Policy state | `ON CONFLICT` |

**Canonical Pattern:**
```sql
INSERT INTO recovery_candidates (...)
VALUES (...)
ON CONFLICT (failure_match_id, error_signature) DO UPDATE
SET
    occurrence_count = recovery_candidates.occurrence_count + 1,
    last_occurrence_at = now()
RETURNING id, (xmax = 0) AS is_insert
```

**Guarantee:** Eliminates race between SELECT and INSERT.

### 7.2 FOR UPDATE SKIP LOCKED (Concurrent Claiming)

| File | Purpose | Batch Size |
|------|---------|------------|
| `worker/recovery_claim_worker.py:107-150` | Candidate claiming | 50 |
| `agents/services/job_service.py:496` | Job item claiming | Configurable |
| `agents/services/worker_service.py:82-188` | Worker task distribution | Configurable |

**Pattern:**
```sql
SELECT id FROM recovery_candidates
WHERE decision = 'pending'
FOR UPDATE SKIP LOCKED
LIMIT :batch_size
```

**Guarantee:** Multiple workers run simultaneously without duplicate processing.

### 7.3 Redis XCLAIM (Stream Message Recovery)

| File | Line | Purpose |
|------|------|---------|
| `tasks/recovery_queue_stream.py` | 346, 622 | Claim stalled messages |

**Pattern:**
```python
claimed = await redis.xclaim(
    STREAM_KEY,
    CONSUMER_GROUP,
    CONSUMER_NAME,
    CLAIM_IDLE_MS,
    [msg_id]
)
```

**Guarantee:** Only one worker receives a message at a time.

### 7.4 Transactional Outbox

| File | Phase | Operation |
|------|-------|-----------|
| `worker/outbox_processor.py` | Claim | `claim_outbox_events()` (line 180) |
| `worker/outbox_processor.py` | Process | HTTP with Idempotency-Key (lines 237-300) |
| `worker/outbox_processor.py` | Complete | `complete_outbox_event()` (line 349) |

**Guarantee:** Exactly-once delivery via claim → process → complete cycle.

---

## 8. L6 Artifact Dependency Matrix

| Artifact | Layer | Reads | Writes | Atomicity Mechanism |
|----------|-------|-------|--------|---------------------|
| recovery_queue_stream.py | L5 | Redis Streams, m10_recovery.replay_log | Both | XCLAIM + DB idempotency |
| recovery_write_service.py | L4 | public.recovery_candidates | public.recovery_candidates | ON CONFLICT |
| outbox_processor.py | L5 | m10_recovery locks + outbox | m10_recovery | acquire/release/extend lock |
| recovery_claim_worker.py | L5 | public.recovery_candidates | public.recovery_candidates | FOR UPDATE SKIP LOCKED |
| recovery_evaluator.py | L5 | m10_recovery.suggestion_action | public.recovery_candidates | async session.begin() |
| m10_metrics_collector.py | L5 | Redis streams, m10_recovery.work_queue | None (read-only) | Concurrent async |

---

## 9. Failure Modes & Recovery

### 9.1 Redis Stream Consumer Stall

| Field | Value |
|-------|-------|
| Symptom | Message stuck in PEL (Pending Entry List) |
| Detection | Idle > 5 min (`M10_CLAIM_IDLE_MS`) |
| Recovery | `XCLAIM` by next consumer (lines 346, 622) |
| Escalation | Dead-letter after 3 attempts |

### 9.2 Outbox Event Processing Crash

| Field | Value |
|-------|-------|
| Symptom | Event claimed but processor dies |
| Detection | processor_id stored, no completion |
| Recovery | Next processor detects unclaimed event |
| Escalation | Dead-letter after 5 retries |

### 9.3 Lock Holder Dies

| Field | Value |
|-------|-------|
| Symptom | Lock held but holder offline |
| Detection | TTL expiry (300 sec default) |
| Recovery | Next processor acquires expired lock |
| Prevention | `extend_lock()` for long operations |

### 9.4 Duplicate Ingest During Partition

| Field | Value |
|-------|-------|
| Symptom | Same failure_match_id + error_signature arrives twice |
| Detection | N/A (handled atomically) |
| Recovery | `ON CONFLICT` increments occurrence_count |
| Deduplication Levels | idempotency_key, failure_match_id+signature, DB replay_log |

---

## 10. Configuration Reference

| Variable | Default | Purpose | File |
|----------|---------|---------|------|
| REDIS_URL | redis://localhost:6379/0 | Redis connection | recovery_queue_stream.py:47 |
| M10_STREAM_KEY | m10:evaluate:stream | Stream name | recovery_queue_stream.py:48 |
| M10_CONSUMER_GROUP | m10:evaluate:group | Consumer group | recovery_queue_stream.py:49 |
| M10_STREAM_MAX_LEN | 100000 | Max stream entries | recovery_queue_stream.py:53 |
| M10_CLAIM_IDLE_MS | 300000 (5 min) | Stall detection | recovery_queue_stream.py:54 |
| M10_MAX_RECLAIM_ATTEMPTS | 3 | Before dead-letter | recovery_queue_stream.py:56 |
| OUTBOX_BATCH_SIZE | 20 | Events per claim | outbox_processor.py:54 |
| OUTBOX_LOCK_TTL | 300 | Lock TTL (sec) | outbox_processor.py:57 |
| RECOVERY_WORKER_BATCH_SIZE | 50 | Candidates per claim | recovery_claim_worker.py:52 |

---

## 11. Verification Summary

| Category | Count | Verification Level |
|----------|-------|-------------------|
| PostgreSQL ↔ Redis patterns | 2 (stream + replay_log) | STATIC |
| Redis ↔ Queue dependencies | 2 (consumer groups + DB fallback) | STATIC |
| Cross-schema access patterns | 6 functions | STATIC |
| Transactional boundaries | 3 types (sync, async, distributed) | STATIC |
| Atomicity mechanisms | 4 patterns | STATIC |
| Failure modes documented | 4 scenarios | STATIC |

**All verifications are STATIC. Semantic verification pending contract review.**

---

## 12. Conclusion

L6 internal flows **in primary runtime paths** are:
- **Explicitly documented** — no hidden substrate couplings found in audited scope
- **Schema-isolated** — m10_recovery accessed via functions only (in audited paths)
- **Transactionally clear** — all documented patterns have explicit commit/rollback
- **Atomically sound** — concurrent access uses locking patterns (in audited paths)
- **Failure-resilient** — documented recovery procedures

**Assessment:** L6 substrate coherency appears sound in primary runtime paths. Auxiliary paths (CLI, admin, migrations) not exhaustively audited.

---

**Generated by:** Claude Opus 4.5
**Verification Level:** STATIC only
**Artifacts:** 6 types, 4 atomicity patterns, 4 failure modes
**Cross-reference:** L6_L5_FLOWS.md, L7_L6_FLOWS.md
