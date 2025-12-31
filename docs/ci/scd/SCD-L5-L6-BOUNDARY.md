# Signal Circuit Discovery: L5↔L6 Boundary

**Status:** PHASE 1 DISCOVERY COMPLETE
**Date:** 2025-12-31
**Boundary:** L5 (Execution & Workers) ↔ L6 (Platform Substrate)
**Reference:** PRODUCT_DEVELOPMENT_CONTRACT_V3.md, EXECUTION_SEMANTIC_CONTRACT.md

---

## 1. Boundary Lock

```yaml
boundary_pair: L5↔L6
from_layer: L5 — Execution & Workers
to_layer: L6 — Platform Substrate (DB, Redis, External Services)
direction: bidirectional
crossing_type: persistence + polling + events + external calls
```

**Unique Characteristics:**
- L5 is pure execution - no decisions, only enforcement
- L6 is foundational - no imports from other layers
- All L5 state persistence goes through L6
- L6 provides: Database (PostgreSQL), Events (Redis/NATS), External HTTP

---

## 2. Declared Intent

| Field | Value |
|-------|-------|
| Contract Document | `docs/architecture/EXECUTION_SEMANTIC_CONTRACT.md` |
| Contract Version | DRAFT (Phase 3.2) |
| Intent Statement | "L5 workers persist state through L6; L5 does not decide, only enforces" |
| Enforcement Level | IMPLICIT (L5→L6 imports allowed by layer model) |

**Key L6 Components:**
- `db.py` - SQLAlchemy/SQLModel database connection and models
- `events/publisher.py` - In-memory event publishing
- `events/redis_publisher.py` - Redis-based event publishing
- External HTTP via httpx (outbox processor)

---

## 3. Expected Signals

### 3.1 L5 → L6 (Workers to Platform)

| Signal ID | Signal Name | Emitter | Consumer | Transport | Consequence |
|-----------|-------------|---------|----------|-----------|-------------|
| EXP-L5L6-001 | Run State Update | RunRunner | Run table (L6) | SQLAlchemy Session | Run status persisted |
| EXP-L5L6-002 | Provenance Write | RunRunner | Provenance table (L6) | SQLAlchemy Session | Execution trace recorded |
| EXP-L5L6-003 | Event Publish | WorkerPool/Runner | Event Publisher (L6) | publish() call | Observers notified |
| EXP-L5L6-004 | External HTTP | OutboxProcessor | External endpoints | httpx client | Webhook delivered |
| EXP-L5L6-005 | Memory Update | RunRunner | Memory table (L6) | SQLAlchemy Session | Agent memory persisted |

### 3.2 L6 → L5 (Platform to Workers)

| Signal ID | Signal Name | Emitter | Consumer | Transport | Consequence |
|-----------|-------------|---------|----------|-----------|-------------|
| EXP-L6L5-001 | Queued Runs | Run table (L6) | WorkerPool poll | SQLAlchemy query | Runs dispatched to workers |
| EXP-L6L5-002 | Agent Config | Agent table (L6) | RunRunner | SQLAlchemy get() | Budget context loaded |
| EXP-L6L5-003 | Outbox Events | Outbox table (L6) | OutboxProcessor | SQLAlchemy query | Events delivered |

---

## 4. Reality Inspection

### 4.1 L5 File Inventory

| File | Purpose | L6 Dependencies |
|------|---------|-----------------|
| `pool.py` | Worker pool, run polling | `db.py` (Run, engine, Session) |
| `runner.py` | Run execution | `db.py` (Run, Agent, Memory, Provenance), events |
| `recovery_claim_worker.py` | Recovery claim processing | `db.py`, SQLAlchemy text queries |
| `recovery_evaluator.py` | Recovery evaluation | `db.py`, SQLAlchemy text queries |
| `outbox_processor.py` | Transactional outbox | `db.py`, httpx |
| `simulate.py` | Cost simulation | `db.py` (models only) |
| `runtime/core.py` | Runtime primitives | None direct |

### 4.2 L6 Access Patterns

| Pattern | Location | Compliant? |
|---------|----------|------------|
| Direct `Session(engine)` usage | `pool.py:99`, `runner.py:90` | YES (allowed) |
| Direct `session.exec()` queries | `pool.py:108`, recovery files | YES (allowed) |
| `from sqlalchemy import text` | Multiple files | YES (allowed) |
| `httpx.AsyncClient` | `outbox_processor.py:94` | YES (L6 external) |
| Event publisher | `pool.py:59`, `runner.py` | YES (L6 events) |

### 4.3 Transport Audit

| Transport | L5 File | L6 Component | Observable? |
|-----------|---------|--------------|-------------|
| SQLAlchemy Session | All L5 files | `db.py:engine` | YES (DB logs) |
| Event Publisher | pool.py, runner.py | `events/publisher.py` | YES (event logs) |
| HTTP Client | outbox_processor.py | External endpoints | YES (HTTP logs) |

### 4.4 State Flow

```
L5 (Workers) ←→ L6 (Platform)

WorkerPool.poll_and_dispatch():
  L5 → L6: SELECT from Run table (queued runs)
  L6 → L5: Run rows returned
  L5 → L6: UPDATE Run.status = "running"
  L5 → L6: publish("run.started")

RunRunner.run():
  L6 → L5: Load Agent (budget context)
  L5 → L6: UPDATE Run.status = "succeeded/failed"
  L5 → L6: INSERT Provenance record
  L5 → L6: UPDATE Memory (if applicable)
  L5 → L6: publish("run.completed")

OutboxProcessor.process():
  L6 → L5: SELECT from Outbox table (pending events)
  L5 → L6: httpx.post() to external webhooks
  L5 → L6: UPDATE Outbox.status = "sent"
```

---

## 5. End-to-End Circuit Walk

### Circuit 1: Run Polling and Dispatch

```
SIGNAL: Queued Run → Worker Execution

INTENT:
  → Declared at: EXECUTION_SEMANTIC_CONTRACT.md (Guarantee 3)
  → Statement: "At-Least-Once Worker Dispatch"

EMISSION:
  → Emitter: Run table (status = "queued")
  → Mechanism: Database state
  → Explicit: YES (Run.status column)

TRANSPORT:
  → Type: SQLAlchemy SELECT query
  → Observable: YES (pool.py logs, DB query logs)
  → Failure Mode: Empty result, retry on next poll

ADAPTER:
  → Location: pool.py:_fetch_queued_runs()
  → Purpose: Transform DB rows to Run objects

CONSUMPTION:
  → Consumer: WorkerPool dispatch loop
  → Explicit: YES (direct query)
  → Dependency Declared: YES (import from db)

CONSEQUENCE:
  → What happens on success: Run dispatched to ThreadPoolExecutor
  → What happens on failure: Run remains queued, next poll picks up
  → Observable: YES (worker logs)
```

### Circuit 2: Run State Persistence

```
SIGNAL: Run completion → State persisted

INTENT:
  → Declared at: EXECUTION_SEMANTIC_CONTRACT.md (Guarantee 5)
  → Statement: "Run state immutably recorded"

EMISSION:
  → Emitter: RunRunner.run() completion
  → Mechanism: session.add(run) + session.commit()
  → Explicit: YES

TRANSPORT:
  → Type: SQLAlchemy Session
  → Observable: YES (DB transaction logs)
  → Failure Mode: Transaction rollback

ADAPTER:
  → Location: runner.py (various session operations)
  → Purpose: Persist execution state to L6

CONSUMPTION:
  → Consumer: PostgreSQL database
  → Explicit: YES
  → Dependency Declared: YES (engine from db.py)

CONSEQUENCE:
  → What happens on success: Run status, provenance recorded
  → What happens on failure: Transaction rolled back, run may retry
  → Observable: YES (DB records)
```

---

## 6. Failure Classification

| Gap ID | Gap Description | Classification | Severity |
|--------|-----------------|----------------|----------|
| GAP-L5L6-001 | No L6 abstraction layer (workers use raw SQL) | DIRECT_COUPLING | P2 |
| GAP-L5L6-002 | Multiple `from sqlalchemy import text` in L5 | IMPLICIT_SIGNAL | P3 |
| GAP-L5L6-003 | No circuit breaker for external HTTP calls | MISSING_CONSUMER | P2 |
| GAP-L5L6-004 | No retry logic for transient DB failures | MISSING_ADAPTER | P2 |
| GAP-L5L6-005 | Event publisher coupling not explicit | IMPLICIT_SIGNAL | P3 |

### Classification Evidence

**GAP-L5L6-001 (DIRECT_COUPLING):**
L5 workers use raw SQLAlchemy Sessions and text queries without an abstraction layer.
This is allowed by layer model (L5 may import L6) but creates tight coupling.

**GAP-L5L6-002 (IMPLICIT_SIGNAL):**
Multiple L5 files use `from sqlalchemy import text` for raw SQL.
This bypasses model-based queries and makes signals harder to trace.
Locations: recovery_evaluator.py (3 places), recovery_claim_worker.py (1), outbox_processor.py (5)

**GAP-L5L6-003 (MISSING_CONSUMER):**
outbox_processor.py makes external HTTP calls without circuit breaker.
Transient failures in external endpoints could cause unbounded retries.

**GAP-L5L6-004 (MISSING_ADAPTER):**
No explicit retry logic for transient database failures (connection loss, timeout).
SQLAlchemy pool_pre_ping provides some protection but not full retry.

**GAP-L5L6-005 (IMPLICIT_SIGNAL):**
Event publisher coupling is via `get_publisher()` factory.
Publisher type (in-memory vs Redis) is runtime-determined, not explicit.

---

## 7. Risk Statement

```
RISK SUMMARY:
  - Circuit Status: COMPLETE (signals found and documented)
  - Gap Count: 5
  - Critical Gaps: None (all P2/P3)
  - Blocking for Phase 2: NO
  - Human Action Required: NO (all gaps are code-level)

RISK NARRATIVE:
  The L5↔L6 boundary is well-established and compliant with the layer model.
  L5 workers correctly import from L6 (db, events) and use L6 for all
  persistence and external communication.

  The gaps found are architectural quality issues, not structural violations:
  - Raw SQL usage (allowed but less traceable)
  - Missing circuit breaker for external calls
  - Missing explicit retry for DB failures
  - Implicit event publisher coupling

  These gaps do not block Phase 2 but should be addressed in Phase 3
  (Infrastructure Hardening).
```

---

## 8. Registry Entry

```yaml
boundary: L5↔L6
circuit_status: COMPLETE
signals_expected: 8 (5 L5→L6 + 3 L6→L5)
signals_found: 8
gaps:
  - id: GAP-L5L6-001
    type: DIRECT_COUPLING
    severity: P2
    description: No L6 abstraction layer (workers use raw SQL)
  - id: GAP-L5L6-002
    type: IMPLICIT_SIGNAL
    severity: P3
    description: Multiple raw SQL text queries in L5
  - id: GAP-L5L6-003
    type: MISSING_CONSUMER
    severity: P2
    description: No circuit breaker for external HTTP calls
  - id: GAP-L5L6-004
    type: MISSING_ADAPTER
    severity: P2
    description: No retry logic for transient DB failures
  - id: GAP-L5L6-005
    type: IMPLICIT_SIGNAL
    severity: P3
    description: Event publisher coupling not explicit
enforcement:
  layer_model_compliant: YES (L5 may import L6)
  persistence_via_l6: YES
  events_via_l6: YES
  external_calls_via_l6: YES
phase_1_complete: YES
phase_1_blocker: NO
owner: NEEDS_ASSIGNMENT (Infrastructure Team)
```

---

## 9. Hard Rules (Verification)

| Rule | Check | Status |
|------|-------|--------|
| Did I observe, not fix? | Documented gaps, did not modify code | YES |
| Did I document what IS, not what SHOULD BE? | Reality section reflects current state | YES |
| Did I trace at least one full circuit? | 2 circuits traced (polling, state persistence) | YES |
| Did I classify all gaps found? | 5 gaps classified with codes | YES |
| Did I note human-only signals? | No human-only signals at this boundary | N/A |
| Did I check both directions if bidirectional? | L5→L6 and L6→L5 both documented | YES |

---

## 10. Completion Test

| Question | Can Answer? |
|----------|-------------|
| What signals cross this boundary? | YES (8 signals documented) |
| Where are they emitted? | YES (L5 worker files, L6 tables) |
| Where are they consumed? | YES (L6 DB, L5 workers) |
| What happens if any signal is missing? | YES (run stuck, state not persisted) |
| Which gaps block Phase 2? | NONE |

**Checklist Status: COMPLETE**

---

## L6 Component Summary

| Component | Type | Used By (L5) | Signal Type |
|-----------|------|--------------|-------------|
| `db.py:engine` | Database | All L5 files | Persistence |
| `db.py:Session` | ORM | All L5 files | Queries/Updates |
| `db.Run` | Model | pool.py, runner.py | State object |
| `db.Agent` | Model | runner.py | Config object |
| `db.Provenance` | Model | runner.py | Trace object |
| `db.Memory` | Model | runner.py | State object |
| `events/publisher.py` | Events | pool.py, runner.py | Notifications |
| httpx | HTTP Client | outbox_processor.py | External calls |

---

## Related Documents

| Document | Relationship |
|----------|--------------|
| EXECUTION_SEMANTIC_CONTRACT.md | L5 execution semantics |
| SCD-L4-L5-BOUNDARY.md | Adjacent boundary (upstream) |
| CI_SIGNAL_REGISTRY.md | CI workflow inventory |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-31 | Initial SCD for L5↔L6 boundary |
