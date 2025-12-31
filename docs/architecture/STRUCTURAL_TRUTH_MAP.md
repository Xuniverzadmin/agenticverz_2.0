# Structural Truth Map — Backend

**Status:** Phase 2B COMPLETE (Post-Alignment)
**Created:** 2025-12-30
**Phase 1 Completed:** 2025-12-30
**Phase 2B Completed:** 2025-12-30
**Reference:** PIN-250 (Structural Truth Extraction Lifecycle)
**Addenda:** PHASE1_ADDENDA.md (Execution & State Authority)
**Completion Gate:** PHASE2_COMPLETION_GATE.md
**Scope:** backend/app/ (~400 Python files, 36 directories)

---

## Purpose

This document captures **what the codebase IS**, not what it claims to be.

> Metadata is not truth. Only behavior, dependencies, and call graphs are truth.

---

## Layer Classification Summary

### Layer Distribution

| Layer | Count | Directories |
|-------|-------|-------------|
| L2 (API) | 1 | api/ |
| L3 (Boundary Adapter) | 5 | contracts/, events/, planner/, planners/, skills/ |
| L4 (Domain Engine) | 12 | agents/, auth/, costsim/, discovery/, integrations/, learning/, optimization/, policy/, predictions/, routing/, schemas/, workflow/ |
| L5 (Execution/Workers) | 4 | jobs/, tasks/, worker/, workers/ |
| L6 (Platform Substrate) | 11 | config/, data/, memory/, middleware/, models/, observability/, secrets/, security/, services/, storage/, stores/ |
| L7/L8 (Ops/Meta) | 1 | specs/ |
| HYBRID | 2 | auth/ (L3+L4), utils/ (L3-L6) |

**Phase 2B Update:** api/ is no longer HYBRID. L2 collapse resolved — all DB writes now delegated to L4 services. See PHASE2_COMPLETION_GATE.md.

---

## Directory-Level Truth Map

### L2 — Product APIs

#### api/
- **Claimed:** API route handlers
- **Actual:** 33 route files, FastAPI routers
- **Layer:** L2 (HIGH)
- **Phase 2B Status:** ✅ RESOLVED — DB writes delegated to L4 services
- **Remaining Issue:** L3 adapter layer still missing (API → Service direct coupling)

---

### L3 — Boundary Adapters

#### contracts/
- **Claimed:** Frozen DTOs and contracts
- **Actual:** Clean domain separation (guard/ops)
- **Layer:** L3 (HIGH)
- **Issue:** None

#### events/
- **Claimed:** Event publishing adapters
- **Actual:** Abstract factory (Redis/NATS/logging backends)
- **Layer:** L3 (HIGH)
- **Issue:** ENV-based selection, no shutdown hooks

#### planner/ (singular)
- **Claimed:** Planner interface + stub
- **Actual:** Testing-only deterministic planner
- **Layer:** L3 (HIGH)
- **Issue:** **DUPLICATION** with planners/ module

#### planners/ (plural)
- **Claimed:** Production planner backends
- **Actual:** LLM backend factory (Anthropic/OpenAI)
- **Layer:** L3 (MEDIUM)
- **Issue:** **DUPLICATION** with planner/ module — which is authoritative?

#### skills/
- **Claimed:** Skill adapters
- **Actual:** Lazy-loaded skill registry (10 skills)
- **Layer:** L3→L4 (MEDIUM)
- **Issue:** Light abstraction, SkillInterface protocol

---

### L4 — Domain Engines

#### agents/
- **Claimed:** Agent services
- **Actual:** Multi-agent orchestration (6 services, well-separated)
- **Layer:** L4→L5 (HIGH)
- **Issue:** None — clean design

#### auth/
- **Claimed:** Authentication
- **Actual:** **HYBRID** — JWT parsing (L3) + RBAC rules (L4)
- **Layer:** L3/L4 (MEDIUM)
- **Issue:** **ARCHITECTURE VIOLATION** — should split into auth/providers/ (L3) + auth/rbac/ (L4)

#### costsim/
- **Claimed:** Cost simulation
- **Actual:** Dual circuit breaker (sync+async)
- **Layer:** L4→L5 (HIGH)
- **Issue:** Consolidation candidate (pick async-only)

#### discovery/
- **Claimed:** Discovery ledger
- **Actual:** Advisory log (DB append-only), Phase C signals
- **Layer:** L4 (HIGH)
- **Issue:** Naming confusion (`emit_signal()` suggests pub/sub, actually DB write)

#### integrations/
- **Claimed:** External integrations (L3 name)
- **Actual:** Pillar integration — internal domain coordination
- **Layer:** L4 (HIGH)
- **Issue:** **ACKNOWLEDGED** — name is historical (PIN-249), not L3

#### learning/
- **Claimed:** C5 learning subsystem
- **Actual:** Learning constraints and suggestions
- **Layer:** L4 (HIGH)
- **Issue:** Table restrictions defined but **NOT ENFORCED** at query time

#### optimization/
- **Claimed:** C3/C4 safety cage
- **Actual:** Envelope + killswitch framework (FROZEN contracts)
- **Layer:** L4 (HIGH)
- **Issue:** High governance — 6 certified invariants

#### policy/
- **Claimed:** Policy engine
- **Actual:** 22 exports, comprehensive GAP fixes
- **Layer:** L4 (HIGH)
- **Issue:** None — mature subsystem

#### predictions/
- **Claimed:** C2 prediction API
- **Actual:** Advisory-only canary (3 scenarios)
- **Layer:** L4 (HIGH)
- **Issue:** **SEMANTIC ENFORCEMENT GAP** — advisory language not linted

#### routing/
- **Claimed:** Routing engine
- **Actual:** M17/M18 cascade-aware routing
- **Layer:** L4 (HIGH)
- **Issue:** 25+ config constants, no validation mechanism

#### schemas/
- **Claimed:** Pydantic models
- **Actual:** M0 machine-native data structures (15+ exports)
- **Layer:** L4 (HIGH)
- **Issue:** Permission anomaly (600 on JSON files)

#### workflow/
- **Claimed:** Workflow engine
- **Actual:** Deterministic engine (checkpoints, replay, sandbox)
- **Layer:** L4 (HIGH)
- **Issue:** None — mature design

---

### L5 — Execution & Workers

#### jobs/
- **Claimed:** Background jobs
- **Actual:** **SEVERELY UNDERDEVELOPED** — 7 lines, no jobs exported
- **Layer:** L5 (MEDIUM)
- **Issue:** **INCOMPLETE** — either populate or delete

#### tasks/
- **Claimed:** Tasks module
- **Actual:** 4 files exist (`m10_metrics_collector.py`, `memory_update.py`, `recovery_queue.py`, `recovery_queue_stream.py`) but `__init__.py` has no exports
- **Layer:** L5 (MEDIUM)
- **Issue:** **Silent module** — files exist but aren't wired into package exports

#### worker/
- **Claimed:** Worker pool
- **Actual:** Pool management with lazy imports
- **Layer:** L5 (HIGH)
- **Issue:** Confusing API (requires get_worker_pool())

#### workers/
- **Claimed:** Worker implementations
- **Actual:** business_builder submodule only
- **Layer:** L5 (LOW)
- **Issue:** **NO __init__.py**, naming conflicts with worker/

---

### L6 — Platform Substrate

#### config/
- **Claimed:** Runtime configuration
- **Actual:** Feature flags + secrets centralization
- **Layer:** L6 (HIGH)
- **Issue:** Flag sync debt (file→DB migration)

#### data/
- **Claimed:** Static data
- **Actual:** failure_catalog.json only
- **Layer:** L6 (HIGH)
- **Issue:** None

#### memory/
- **Claimed:** Agent memory storage
- **Actual:** Persistent storage (PostgreSQL only)
- **Layer:** L6 (HIGH)
- **Issue:** Expandable design, single impl

#### middleware/
- **Claimed:** FastAPI middleware
- **Actual:** Tenancy + rate limiting
- **Layer:** L6 (HIGH)
- **Issue:** Legacy API debt (old + new TenancyMiddleware)

#### models/
- **Claimed:** Database models
- **Actual:** Async SQLModel definitions
- **Layer:** L6 (MEDIUM)
- **Issue:** **SPLIT IMPLEMENTATION** — async (models/) vs sync (db.py)

#### observability/
- **Claimed:** Observability (empty export)
- **Actual:** cost_tracker.py exists but not exported
- **Layer:** L4-L5 (MEDIUM)
- **Issue:** **MODULE HIDDEN** — no __init__.py exports

#### secrets/
- **Claimed:** Vault client
- **Actual:** KV v2 wrapper (HashiCorp Vault)
- **Layer:** L6 (HIGH)
- **Issue:** Permission anomaly (700 dir), hardcoded timeout

#### security/
- **Claimed:** Security utilities
- **Actual:** Embedding secret redaction
- **Layer:** L6 (HIGH)
- **Issue:** Permission anomaly (600), pattern registry missing

#### services/
- **Claimed:** Business services
- **Actual:** 11 services (3 original + 8 write services from Phase 2B)
- **Layer:** L4 (HIGH)
- **Phase 2B Status:** ✅ EXPANDED — 8 write-only services added
- **Write Services Created:**
  - `GuardWriteService` (sync) — KillSwitchState, Incident
  - `UserWriteService` (sync) — User
  - `TenantService` (sync, extended) — Tenant, TenantMembership
  - `CostWriteService` (sync) — FeatureTag, CostRecord, CostBudget
  - `FounderActionWriteService` (sync) — FounderAction
  - `OpsWriteService` (sync) — ops_customer_segments
  - `WorkerWriteServiceAsync` (async) — WorkerRun, CostRecord, CostAnomaly
  - `RecoveryWriteService` (sync) — recovery_candidates, suggestion_provenance
- **Issue:** None — clean write ownership pattern

#### storage/
- **Claimed:** Artifact storage
- **Actual:** S3/Local backend abstraction
- **Layer:** L6 (HIGH)
- **Issue:** None — clean design

#### stores/
- **Claimed:** Store factory
- **Actual:** M11 multi-store coordination
- **Layer:** L6 (HIGH)
- **Issue:** Configuration auto-detection ambiguity

---

### L7/L8 — Ops & Meta

#### specs/
- **Claimed:** Contract specifications
- **Actual:** 7 frozen Markdown files
- **Layer:** L7-L8 (HIGH)
- **Issue:** All files 600 permissions

---

### HYBRID / BOUNDARY

#### runtime/
- **Claimed:** Runtime utilities
- **Actual:** failure_catalog + replay
- **Layer:** L4 (MEDIUM)
- **Issue:** **MISSING __init__.py** — no clean exports

#### traces/
- **Claimed:** Trace storage
- **Actual:** **STORAGE DUALITY** — SQLite + PostgreSQL
- **Layer:** L6 (HIGH)
- **Issue:** Redis idempotency (loss = idempotency loss)

#### utils/
- **Claimed:** Utility functions
- **Actual:** Lazy import adapters (18+ functions)
- **Layer:** L3-L6 (MEDIUM)
- **Issue:** Wrapper pattern (indirection), mixed concerns

---

## Critical Structural Issues

### P1 — Architecture Violations

| ID | Issue | Location | Impact | Phase 2B Status |
|----|-------|----------|--------|-----------------|
| STI-001 | API lacks L3 adapter | api/ | HTTP changes cascade to domain | **PARTIAL** — DB writes extracted; L3 adapter pending |
| STI-002 | Auth mixes L3+L4 | auth/ | RBAC/provider coupling | Pending (Phase 2C) |
| STI-003 | Module duplication | planner/ vs planners/ | Import ambiguity | Pending (Phase 2D) |
| STI-004 | Hidden module | observability/ | Dead or unreachable code | Pending |
| STI-005 | Empty module | tasks/ | Dead placeholder | **RESOLVED** (Phase 2A) |

### P2 — Code Quality Issues

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| STI-006 | Runtime missing __init__.py | runtime/ | No public API |
| STI-007 | Workers missing __init__.py | workers/ | Discovery barrier |
| STI-008 | Dual storage implementations | models/ + db.py, traces/ | Schema drift risk |
| STI-009 | Learning restrictions unenforced | learning/ | Table mutation risk |
| STI-010 | Jobs underdeveloped | jobs/ | Incomplete feature |

### P3 — Governance Gaps

| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| STI-011 | Semantic enforcement gap | predictions/ | Advisory language not linted |
| STI-012 | Permission anomalies | schemas/, secrets/, security/, specs/ | Container deployment risk |
| STI-013 | Config auto-detection | stores/ | Silent degradation |
| STI-014 | Legacy API debt | middleware/ | Migration incomplete |

---

## Correctly Implemented Patterns

| Directory | Pattern | Notes |
|-----------|---------|-------|
| agents/ | Service-oriented design | 6 services, well-separated |
| contracts/ | Frozen DTOs | Proper domain separation |
| policy/ | Comprehensive versioning | Provenance tracking |
| workflow/ | Deterministic engine | Checkpoints, replay, sandbox |
| skills/ | Lazy-loading | Avoids heavy dependencies |
| services/ | Factory pattern | get_X_service() |
| optimization/ | Frozen contracts | C3/C4 invariants certified |
| storage/ | Backend abstraction | S3/Local, clean interface |

---

## Naming Collisions

| Pair | Issue | Resolution |
|------|-------|------------|
| planner/ vs planners/ | Both provide planner functionality | Consolidate |
| worker/ vs workers/ | Singular pool vs plural impls | Rename workers/ to worker_impls/ |
| traces/ dual storage | SQLite + PostgreSQL exported | Pick authoritative |
| models/ vs db.py | Async vs sync models | Consolidate |

---

## Layer Confidence Matrix

| Layer | HIGH | MEDIUM | LOW | UNKNOWN |
|-------|------|--------|-----|---------|
| L2 | 1 | 0 | 0 | 0 |
| L3 | 3 | 2 | 0 | 0 |
| L4 | 10 | 2 | 0 | 0 |
| L5 | 1 | 1 | 1 | 1 |
| L6 | 10 | 1 | 0 | 0 |
| L7-L8 | 1 | 0 | 0 | 0 |
| HYBRID | 0 | 2 | 0 | 0 |

**Overall Assessment:** HIGH confidence in structural classification for 26/36 directories.

---

## Dependency Direction Map

### Dependency Flow Diagram

```
L2 (api/)
    │
    ├──► L3 (auth/, contracts/)
    │
    ├──► L4 (services/, policy/, routing/)
    │
    └──► L5 (worker/)
              │
              └──► L6 (models/, stores/, db)
```

### Dependency Matrix

| FROM↓ TO→ | api | auth | contracts | services | worker | models | config | stores |
|-----------|-----|------|-----------|----------|--------|--------|--------|--------|
| api (L2)  | -   | ✓    | ✓         | ✓        | ✓      | ✓      | -      | -      |
| auth (L3) | -   | -    | -         | -        | -      | ✓      | -      | -      |
| contracts | -   | -    | -         | -        | -      | -      | -      | -      |
| services  | -   | -    | -         | -        | -      | ✓      | -      | -      |
| worker    | -   | -    | ✓         | -        | -      | -      | -      | -      |
| policy    | -   | -    | ✓         | -        | -      | -      | -      | -      |
| models    | -   | -    | -         | -        | -      | -      | -      | -      |

### Architectural Health Assessment

**Status:** Structurally intelligible, not yet aligned.

| Metric | Status | Finding |
|--------|--------|---------|
| Circular Dependencies | NONE | No cycles detected |
| Layer Violations | 5 observed | Not yet resolved (Phase 2 work) |
| Import Clarity | Well-structured | DAG confirmed |
| Separation of Concerns | Mixed | L2 collapse identified |
| Testability | Good | Structure supports testing |

**Note:** Scores removed per Phase 1 discipline. Phase 1 observes; it does not grade.

### Contracts Layer Reclassification

The `contracts/` directory is imported by L4 and L5 layers, suggesting it functions as a **shared interface layer** rather than pure L3.

**Recommendation:** Reclassify as "L3.5 Shared Interface" to reflect actual role as cross-cutting decision and DTO layer.

---

## Phase 1 Deliverable Checklist

- [x] Directory-level truth map
- [x] Dependency-direction map
- [x] Runtime-trigger map (Phase 1.3) — COMPLETE
- [ ] State ownership map (Phase 1.4)
- [ ] Policy enforcement map (Phase 1.5)
- [ ] Glue vs Domain classification (Phase 1.6)

---

## Runtime-Trigger Map (Phase 1.3)

**Completed:** 2025-12-30
**Purpose:** Classify each directory by when code executes.

### Trigger Types

| Type | Definition | Example |
|------|------------|---------|
| **Import-time** | Runs when module is imported | Global instances, decorators |
| **Request-time** | Runs on HTTP request | Route handlers, middleware |
| **Async/Worker** | Background/deferred execution | Workers, queues, schedulers |
| **Mixed** | Multiple execution modes | Adapters called by both API and workers |

### Runtime-Trigger Classification

#### Import-Time Execution

| Directory | Trigger | Evidence | Risk |
|-----------|---------|----------|------|
| `main.py` | import | `rate_limiter = RateLimiter()`, `init_db()`, `planner = get_planner()` | **HIGH** — DB init at import |
| `config/` | import | Loads `feature_flags.json` at import | LOW |
| `models/` | import | SQLAlchemy model registration | LOW |
| `schemas/` | import | Pydantic model registration | LOW |
| `contracts/` | import | DTO/contract class definition | LOW |
| `specs/` | none | Static markdown files | NONE |

#### Request-Time Execution

| Directory | Trigger | Execution | Evidence |
|-----------|---------|-----------|----------|
| `api/` | HTTP request | sync | FastAPI routers (`@router.get`, `@router.post`) |
| `middleware/` | HTTP request | sync | `TenantMiddleware`, `RateLimitMiddleware` |
| `auth/` | HTTP request | sync | `verify_api_key()`, RBAC middleware |
| `policy/` | api \| worker | sync | Policy engine evaluation |
| `routing/` | api \| worker | sync | CARE routing decisions |
| `predictions/` | api | sync | C2 prediction queries |
| `discovery/` | api | sync | Discovery ledger writes |

#### Async/Worker Execution

| Directory | Trigger | Execution | Evidence |
|-----------|---------|-----------|----------|
| `worker/pool.py` | process start | async | `ThreadPoolExecutor`, polls `runs` table |
| `worker/runner.py` | worker | async | `RunRunner` executes plans |
| `tasks/` | worker | async | Redis queue processing |
| `costsim/alert_worker.py` | worker | async | Alert delivery with backoff |
| `jobs/` | scheduler | async | Background aggregation jobs |
| `integrations/dispatcher.py` | worker | async | Event dispatch orchestration |

#### Mixed Execution (API + Worker)

| Directory | Trigger | Execution | Note |
|-----------|---------|-----------|------|
| `events/` | api \| worker | async | Publisher adapters (Redis/NATS) |
| `services/` | api \| worker | sync | Business services (TenantService, EventEmitter) |
| `memory/` | api \| worker | sync | Memory service (query + update) |
| `workflow/` | api \| worker | sync | Workflow engine (request creates, worker executes) |
| `skills/` | worker (primary) | sync | Skill execution during run |
| `agents/` | api \| worker | sync | Agent orchestration |
| `costsim/` | api \| worker | mixed | CB for api (sync), alert worker (async) |
| `optimization/` | api \| worker | sync | Envelope/killswitch checks |
| `learning/` | api \| worker | sync | Learning constraint checks |

#### Platform Substrate (No Direct Trigger)

| Directory | Trigger | Note |
|-----------|---------|------|
| `data/` | none | Static JSON (failure_catalog.json) |
| `storage/` | caller | Called by services/workers |
| `stores/` | caller | Store factory, called on demand |
| `traces/` | caller | Trace storage, called by runners |
| `secrets/` | caller | Vault client, called on demand |
| `security/` | caller | Sanitization utilities |
| `utils/` | caller | Utility functions, no self-trigger |

### Import-Time Risk Analysis

**HIGH RISK** (Runs on every process start):

| Location | What Runs | Impact |
|----------|-----------|--------|
| `main.py:51` | `RateLimiter()` | In-memory limiter instance |
| `main.py:52` | `ConcurrentRunsLimiter()` | In-memory limiter instance |
| `main.py:53` | `BudgetTracker()` | In-memory tracker instance |
| `main.py:59` | `init_db()` | **DB CONNECTION** at import |
| `main.py:62` | `get_planner()` | Planner backend init |

**Recommendation:** Move import-time initialization to `@app.on_event("startup")` or async lifespan handler.

### Worker Lifecycle

```
Process Start
     │
     ▼
Import main.py → init_db(), planner, limiters created
     │
     ▼
Import worker/ → Lazy (uses get_worker_pool())
     │
     ▼
Worker poll loop starts
     │
     ├──► Fetch queued runs from DB
     │
     ├──► Submit to ThreadPoolExecutor
     │
     └──► RunRunner.execute() for each run
              │
              ├──► Skill execution
              ├──► Memory updates
              ├──► Trace persistence
              └──► Event emission
```

### Temporal Boundary Violations (Detected)

| ID | Location | Violation | Resolution |
|----|----------|-----------|------------|
| TBV-001 | `main.py` | DB init at import-time | Move to lifespan handler |
| TBV-002 | `api/guard.py` imports `worker/` | L2 importing L5 | Add L3 adapter |
| TBV-003 | Some API routes `await` worker results | Sync blocking on async | Proper async boundary |

### Lazy Import Patterns (Correct)

| Directory | Pattern | Why |
|-----------|---------|-----|
| `worker/` | `get_worker_pool()` | Avoids sqlmodel at import |
| `skills/` | `load_skill()` on demand | Avoids heavy deps (httpx, anthropic) |
| `planners/` | Factory function | Avoids LLM client init at import |

---

## State Ownership Map (Phase 1.4)

**Completed:** 2025-12-30
**Purpose:** Identify which directories own state and what type.

### State Classification

| Type | Definition | Persistence | Recovery |
|------|------------|-------------|----------|
| **DB** | PostgreSQL tables | Persistent | Durable |
| **Redis** | Redis keys/streams | Ephemeral | Advisory only |
| **In-Memory** | Module-level singletons | Process lifetime | Lost on restart |

### Database State Owners

#### Core Domain (`db.py`) — L6

| Model | Table | Purpose | Owner |
|-------|-------|---------|-------|
| `Agent` | `agent` | Agent definitions | Platform |
| `Memory` | `memory` | Agent memory entries | Platform |
| `Run` | `run` | Execution instances | Platform |
| `Provenance` | `provenance` | Audit trail | Platform |
| `FeatureFlag` | `featureflag` | Runtime flags | Platform |
| `PolicyApprovalLevel` | `policyapprovallevel` | Approval config | Policy |
| `ApprovalRequest` | `approvalrequest` | Pending approvals | Policy |
| `CostSimCBState` | `costsimcbstate` | Circuit breaker state | CostSim |
| `CostSimCBIncident` | `costsimcbincident` | CB incidents | CostSim |
| `StatusHistory` | `statushistory` | Status changes | Platform |
| `FailureMatch` | `failurematch` | Recovery matches | Recovery |
| `FeatureTag` | `featuretag` | Feature tracking | Platform |
| `CostRecord` | `costrecord` | Cost entries | CostSim |
| `CostAnomaly` | `costanomaly` | Anomaly detection | CostSim |
| `CostBreachHistory` | `costbreachhistory` | Budget breaches | CostSim |
| `CostDriftTracking` | `costdrifttracking` | Cost drift | CostSim |
| `CostBudget` | `costbudget` | Budget limits | CostSim |
| `CostDailyAggregate` | `costdailyaggregate` | Daily rollups | CostSim |

#### Tenant Domain (`models/tenant.py`) — L6

| Model | Table | Purpose | Owner |
|-------|-------|---------|-------|
| `Tenant` | `tenant` | Tenant definitions | Tenancy |
| `User` | `user` | User accounts | Auth |
| `TenantMembership` | `tenantmembership` | User-tenant mapping | Auth |
| `APIKey` | `apikey` | API credentials | Auth |
| `Subscription` | `subscription` | Billing plans | Billing |
| `UsageRecord` | `usagerecord` | Usage metering | Billing |
| `WorkerRegistry` | `workerregistry` | Worker instances | Worker |
| `WorkerConfig` | `workerconfig` | Worker settings | Worker |
| `WorkerRun` | `workerrun` | Worker execution | Worker |
| `AuditLog` | `auditlog` | Audit entries | Platform |
| `FounderAction` | `founderaction` | Founder ops | Platform |

#### CostSim Async (`models/costsim_cb.py`) — L6

| Model | Table | Purpose | Note |
|-------|-------|---------|------|
| `CostSimCBStateModel` | `costsim_cb_state` | Async CB state | **DUPLICATION** with db.py |
| `CostSimCBIncidentModel` | `costsim_cb_incident` | Async CB incidents | **DUPLICATION** with db.py |
| `CostSimProvenanceModel` | `costsim_provenance` | Cost provenance | Async-only |
| `CostSimCanaryReportModel` | `costsim_canary_report` | Canary results | Async-only |
| `CostSimAlertQueueModel` | `costsim_alert_queue` | Alert delivery | Async-only |

#### Killswitch (`models/killswitch.py`) — L4

| Model | Table | Purpose |
|-------|-------|---------|
| `KillSwitchState` | `killswitchstate` | Emergency stop state |
| `ProxyCall` | `proxycall` | Proxied API calls |
| `Incident` | `incident` | Killswitch incidents |
| `IncidentEvent` | `incidentevent` | Incident timeline |
| `DefaultGuardrail` | `defaultguardrail` | Default protections |

### Redis State Owners (Advisory Only)

**Invariant:** Redis loss must not change system behavior.

| Directory | Key Pattern | Purpose | Fallback |
|-----------|-------------|---------|----------|
| `stores/` | `budget:*` | Budget tracking | InMemoryBudgetStore |
| `stores/` | `idempotency:*` | Duplicate detection | InMemoryIdempotencyStore |
| `events/publisher.py` | `events:*` | Pub/sub channels | LoggingPublisher |
| `tasks/recovery_queue.py` | `m10:evaluate` | Recovery queue | DB polling |
| `tasks/recovery_queue_stream.py` | `m10:stream:*` | Recovery stream | DB polling |
| `traces/idempotency.py` | `trace:idem:*` | Trace dedup | None (accept duplicates) |

### In-Memory State Owners (Singletons)

**Risk:** All in-memory state is lost on process restart.

| Location | Variable | Purpose | Multi-Worker Safe |
|----------|----------|---------|-------------------|
| `main.py:51` | `rate_limiter` | Rate limiting | ❌ Per-process |
| `main.py:52` | `concurrent_limiter` | Concurrency limits | ❌ Per-process |
| `main.py:53` | `budget_tracker` | Budget tracking | ❌ Per-process |
| `main.py:62` | `planner` | Planner instance | ✅ Stateless |
| `db.py:36-38` | `_engine`, `_async_engine` | DB connections | ✅ Per-process OK |
| `stores/__init__.py` | `_budget_store_instance` | Budget store | ✅ Redis-backed |
| `stores/__init__.py` | `_checkpoint_store_instance` | Checkpoint store | ✅ DB-backed |
| `stores/__init__.py` | `_r2_client_instance` | S3/R2 client | ✅ Stateless |
| `events/publisher.py` | `_publisher_instance` | Event publisher | ✅ Redis-backed |
| `worker/__init__.py` | `_worker_pool_class` | Lazy import cache | ✅ Immutable |
| `memory/iaec.py` | `_iaec_instance` | Embedding composer | ✅ Stateless |
| `auth/rbac_engine.py` | `RBACEngine._instance` | RBAC singleton | ❌ Per-process |
| `services/scoped_execution.py` | `ScopedExecutor._instance` | Scoped executor | ❌ Per-process |
| `skills/__init__.py` | `_loaded_skills` | Skill cache | ✅ Immutable |
| `runtime/failure_catalog.py` | `_catalog_instance` | Failure catalog | ✅ Static data |
| `costsim/sandbox.py` | `_sandbox_instance` | Cost sandbox | ❌ Per-process |
| `planner/__init__.py` | `_StubPlanner` | Lazy import | ✅ Immutable |
| `utils/guard_cache.py` | `GuardCache._instance` | Guard cache | ❌ Per-process |

### State Ownership Issues

| ID | Issue | Location | Severity |
|----|-------|----------|----------|
| SOI-001 | **Model duplication** | `db.py` vs `models/costsim_cb.py` | HIGH — Same tables, different models |
| SOI-002 | Per-process rate limiting | `main.py` | MEDIUM — Multi-worker inconsistency |
| SOI-003 | Per-process budget tracking | `main.py` | MEDIUM — Multi-worker inconsistency |
| SOI-004 | Per-process RBAC cache | `auth/rbac_engine.py` | LOW — Cache coherence |
| SOI-005 | Per-process guard cache | `utils/guard_cache.py` | LOW — Cache coherence |

### State Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    STATE HIERARCHY                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  In-Memory  │    │    Redis    │    │  PostgreSQL │      │
│  │  (Process)  │    │  (Advisory) │    │   (Truth)   │      │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘      │
│         │                   │                   │            │
│         ▼                   ▼                   ▼            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │ rate_limiter│    │budget:*     │    │ Agent       │      │
│  │ concurrent_ │    │idempotency:*│    │ Run         │      │
│  │ limiter     │    │events:*     │    │ Provenance  │      │
│  │ budget_     │    │m10:*        │    │ Tenant      │      │
│  │ tracker     │    └─────────────┘    │ Incident    │      │
│  └─────────────┘                        │ ...         │      │
│                                         └─────────────┘      │
│                                                              │
│  Lifetime:        │  Lifetime:          │  Lifetime:         │
│  Process restart  │  Ephemeral          │  Permanent         │
│  = LOST           │  = Advisory         │  = Truth           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Recommendations

1. **Consolidate CostSim models** — Pick db.py OR models/costsim_cb.py
2. **Centralize rate limiting** — Move to Redis or DB for multi-worker
3. **Document singleton lifecycle** — Clear restart behavior docs
4. **Add health checks** — Monitor in-memory state staleness

---

## Policy Enforcement Map (Phase 1.5)

**Completed:** 2025-12-30
**Purpose:** Document where policies are enforced and by whom.

### Enforcement Categories

| Category | When | Who Decides |
|----------|------|-------------|
| **Auth** | Request entry | Middleware |
| **RBAC** | Per-resource | Engine |
| **Policy** | Business rules | PolicyEngine |
| **Optimization** | Envelope execution | Coordinator |
| **Budget** | Resource spend | BudgetTracker |
| **External** | Outbound calls | ExternalGuard |

### Auth Enforcement Layer (L3/L6)

**Location:** `auth/`

| Enforcer | File | Scope | Mechanism |
|----------|------|-------|-----------|
| `verify_api_key()` | `__init__.py` | API key validation | Header check |
| `verify_console_token()` | `console_auth.py` | Console JWT | Depends() |
| `verify_fops_token()` | `console_auth.py` | Founder JWT | Depends() |
| `validate_token()` | `oidc_provider.py` | OIDC validation | Token decode |
| `tier_gated()` | `tier_gating.py` | Tier enforcement | Decorator |
| `guard_founder_isolation()` | `role_mapping.py` | Founder isolation | Context check |

### RBAC Enforcement Layer (L4)

**Location:** `auth/rbac_*.py`

| Enforcer | File | Scope | Mechanism |
|----------|------|-------|-----------|
| `RBACMiddleware` | `rbac_middleware.py` | All requests | ASGIMiddleware |
| `RBACEngine.check()` | `rbac_engine.py` | Permission check | Policy lookup |
| `enforce()` | `rbac_middleware.py` | Policy enforcement | Decision emit |
| `check_permission()` | `rbac_engine.py` | Resource+action | Rule evaluation |
| `get_policy_for_path()` | `rbac_engine.py` | Route lookup | Path matching |
| `check_approver_permission()` | `rbac.py` | Approval flow | Context check |

### Policy Engine Enforcement (L4)

**Location:** `policy/engine.py`

| Enforcer | Method | Scope | When |
|----------|--------|-------|------|
| `PolicyEngine.evaluate()` | Async | Full policy check | Agent decisions |
| `PolicyEngine.pre_check()` | Async | Pre-execution check | Before action |
| `_check_ethical_constraints()` | Internal | Ethics rules | All requests |
| `_check_safety_rules()` | Internal | Safety rules | All requests |
| `_check_risk_ceilings()` | Internal | Risk limits | All requests |
| `_check_cooldown()` | Internal | Rate control | Per-action |

**Policy Submodules:**

| Module | Purpose | Enforcement |
|--------|---------|-------------|
| `policy/validators/prevention_engine.py` | Prevention rules | Pre-action |
| `policy/validators/prevention_hook.py` | Response validation | Post-action |
| `policy/compiler/` | Rule compilation | Build-time |
| `policy/optimizer/` | Rule optimization | Build-time |

### Optimization Enforcement (L4)

**Location:** `optimization/`

| Enforcer | File | Scope | Invariant |
|----------|------|-------|-----------|
| `Coordinator.check_allowed()` | `coordinator.py` | Envelope execution | C4 rules |
| `validate_envelope()` | `envelope.py` | Envelope validity | Schema |
| `validate_s2_envelope()` | `envelopes/s2_*.py` | S2 rules | Cost smoothing |
| `EnvelopeManager` | `manager.py` | Envelope lifecycle | State machine |
| `KillSwitch` | `killswitch.py` | Emergency stop | Global gate |

### Workflow Enforcement (L4/L5)

**Location:** `workflow/`

| Enforcer | File | Scope | When |
|----------|------|-------|------|
| `check_can_execute()` | `policies.py` | Execution permission | Pre-run |
| `_check_agent_budget()` | `policies.py` | Budget check | Per-step |
| `ExternalGuard` | `external_guard.py` | Outbound calls | Socket-level |
| `check_external_call_allowed()` | `external_guard.py` | URL validation | Per-call |
| `block_external_calls()` | `external_guard.py` | Sandbox mode | Context mgr |
| `validate_plan()` | `planner_sandbox.py` | Plan validity | Pre-exec |
| `validate_step_structure()` | `planner_sandbox.py` | Step schema | Per-step |

### Middleware Enforcement (L6)

**Location:** `middleware/`

| Enforcer | File | Scope | Mechanism |
|----------|------|-------|-----------|
| `TenantMiddleware` | `tenancy.py` | Tenant isolation | Context var |
| `RateLimitMiddleware` | `rate_limit.py` | Request rate | Token bucket |
| `check_rate_limit()` | `rate_limit.py` | Per-tenant | Tier lookup |

### API-Level Enforcement (L2)

**Location:** `api/`

| Enforcer | File | Scope |
|----------|------|-------|
| `check_run_quota()` | `tenants.py` | Run limits |
| `check_token_quota()` | `tenants.py` | Token limits |
| `check_idempotency()` | `traces.py` | Duplicate prevention |
| `get_guard_status()` | `guard.py` | Protection status |

### Enforcement Flow Diagram

```
┌───────────────────────────────────────────────────────────────────┐
│                    ENFORCEMENT HIERARCHY                           │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  HTTP Request                                                      │
│       │                                                            │
│       ▼                                                            │
│  ┌─────────────┐                                                   │
│  │ Auth Check  │ ← verify_api_key() / verify_console_token()      │
│  └──────┬──────┘                                                   │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────┐                                                   │
│  │ Rate Limit  │ ← RateLimitMiddleware                            │
│  └──────┬──────┘                                                   │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────┐                                                   │
│  │ RBAC Check  │ ← RBACMiddleware.check()                         │
│  └──────┬──────┘                                                   │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────┐                                                   │
│  │ Tier Gate   │ ← tier_gated() decorator                         │
│  └──────┬──────┘                                                   │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────┐                                                   │
│  │ Route Logic │ ← API handler                                    │
│  └──────┬──────┘                                                   │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────┐                                                   │
│  │ Policy Eval │ ← PolicyEngine.evaluate()                        │
│  └──────┬──────┘                                                   │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────┐                                                   │
│  │ Budget Check│ ← check_agent_budget()                           │
│  └──────┬──────┘                                                   │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────┐                                                   │
│  │ External    │ ← ExternalGuard (socket-level)                   │
│  │ Guard       │                                                   │
│  └──────┬──────┘                                                   │
│         │                                                          │
│         ▼                                                          │
│     Execution                                                      │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

### Enforcement Point Count by Layer

| Layer | Count | Primary Enforcers |
|-------|-------|-------------------|
| L2 (API) | 4 | Quota checks, idempotency |
| L3 (Auth) | 6 | Token validation, tier gates |
| L4 (Domain) | 15+ | Policy engine, RBAC, optimization |
| L5 (Worker) | 3 | External guard, budget |
| L6 (Platform) | 3 | Rate limit, tenant isolation |

### Enforcement Issues

| ID | Issue | Location | Severity |
|----|-------|----------|----------|
| PEI-001 | Multiple RBAC implementations | `rbac_middleware.py` vs `rbac_engine.py` | MEDIUM — Consolidate |
| PEI-002 | Policy engine sync/async mix | `policy/engine.py` | LOW — By design |
| PEI-003 | External guard socket patching | `workflow/external_guard.py` | LOW — Sandbox feature |
| PEI-004 | Rate limiting per-process | `middleware/rate_limit.py` | MEDIUM — Multi-worker |

---

## Glue vs Domain Classification (Phase 1.6)

**Completed:** 2025-12-30
**Purpose:** Distinguish orchestration code from business logic code.

### Classification Criteria

| Type | Definition | Characteristics |
|------|------------|-----------------|
| **Domain** | Business logic, rules, decisions | Contains if/then rules, calculations, validation |
| **Glue** | Orchestration, wiring, translation | Connects components, no business decisions |
| **Hybrid** | Both orchestration and business logic | Should be split in Phase 2 |
| **Infra** | Infrastructure, no business semantics | Database, network, serialization |

### Directory Classification

#### Pure Domain (Business Logic)

| Directory | Type | Evidence |
|-----------|------|----------|
| `policy/` | **DOMAIN** | Rule evaluation, constraints, ethics checks |
| `optimization/` | **DOMAIN** | Envelope logic, killswitch, C3/C4 invariants |
| `routing/` | **DOMAIN** | CARE routing decisions, learning, SLA scoring |
| `learning/` | **DOMAIN** | C5 learning rules, rollback constraints |
| `predictions/` | **DOMAIN** | C2 prediction logic, canary scenarios |
| `discovery/` | **DOMAIN** | Discovery ledger, eligibility rules |
| `costsim/` | **DOMAIN** | Circuit breaker, cost rules, anomaly detection |
| `workflow/` | **DOMAIN** | Deterministic engine, checkpoints, replay |
| `agents/` | **DOMAIN** | Agent orchestration, SBA coordination |

#### Pure Glue (Orchestration)

| Directory | Type | Evidence |
|-----------|------|----------|
| `api/` | **GLUE** | Route handlers, request/response translation |
| `events/` | **GLUE** | Publisher adapters, no business logic |
| `planner/` | **GLUE** | Planner interface, stub adapter |
| `planners/` | **GLUE** | LLM backend adapters |
| `middleware/` | **GLUE** | Request pipeline, no decisions |
| `utils/` | **GLUE** | Helpers, wrappers, no business logic |
| `contracts/` | **GLUE** | DTOs, data contracts, no logic |
| `schemas/` | **GLUE** | Pydantic models, validation only |

#### Pure Infrastructure

| Directory | Type | Evidence |
|-----------|------|----------|
| `models/` | **INFRA** | Database model definitions |
| `db.py` | **INFRA** | Database connection, ORM models |
| `config/` | **INFRA** | Configuration loading |
| `secrets/` | **INFRA** | Vault client, no business logic |
| `storage/` | **INFRA** | S3/local abstraction |
| `stores/` | **INFRA** | Store factory, no business logic |
| `traces/` | **INFRA** | Trace persistence, no business logic |
| `data/` | **INFRA** | Static data files |
| `memory/` | **INFRA** | Memory storage, no business rules |
| `security/` | **INFRA** | Sanitization utilities |
| `specs/` | **INFRA** | Contract specifications (docs) |

#### Hybrid (Needs Splitting)

| Directory | Domain Part | Glue Part | Recommendation |
|-----------|------------|-----------|----------------|
| `auth/` | RBAC rules, tier logic | JWT parsing, providers | Split: `auth/rbac/` (L4) + `auth/providers/` (L3) |
| `skills/` | Skill behavior, contracts | Skill loading, registry | OK — clear separation exists |
| `services/` | Some business logic | Service wiring | Review per-service |
| `worker/` | Execution logic | Pool management | OK — clear runner/pool split |
| `tasks/` | Recovery logic | Queue mechanics | OK — mechanics in queue files |
| `jobs/` | Aggregation logic | Job scheduling | Minimal, acceptable |
| `integrations/` | Bridge logic | Event dispatch | High domain content |

### Classification Matrix

```
┌───────────────────────────────────────────────────────────────────┐
│              GLUE vs DOMAIN CLASSIFICATION                         │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  PURE DOMAIN (9)          HYBRID (7)           PURE GLUE (8)      │
│  ┌─────────────┐          ┌─────────────┐      ┌─────────────┐    │
│  │ policy/     │          │ auth/       │      │ api/        │    │
│  │ optimization│          │ skills/     │      │ events/     │    │
│  │ routing/    │          │ services/   │      │ planner/    │    │
│  │ learning/   │          │ worker/     │      │ planners/   │    │
│  │ predictions/│          │ tasks/      │      │ middleware/ │    │
│  │ discovery/  │          │ jobs/       │      │ utils/      │    │
│  │ costsim/    │          │ integrations│      │ contracts/  │    │
│  │ workflow/   │          └─────────────┘      │ schemas/    │    │
│  │ agents/     │                               └─────────────┘    │
│  └─────────────┘                                                   │
│                                                                    │
│  PURE INFRA (11)                                                   │
│  ┌─────────────────────────────────────────────┐                  │
│  │ models/ db.py config/ secrets/ storage/     │                  │
│  │ stores/ traces/ data/ memory/ security/     │                  │
│  │ specs/                                       │                  │
│  └─────────────────────────────────────────────┘                  │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

### Glue-to-Domain Ratio

| Layer | Glue | Domain | Infra | Ratio |
|-------|------|--------|-------|-------|
| L2 | 1 (api) | 0 | 0 | 100% Glue |
| L3 | 4 (events, planner, planners, contracts) | 0 | 0 | 100% Glue |
| L4 | 0 | 9 (policy, routing, etc.) | 0 | 100% Domain |
| L5 | 0 | 0 | 0 | Hybrid (worker/tasks) |
| L6 | 2 (middleware, utils) | 0 | 9 (models, stores, etc.) | 18% Glue / 82% Infra |

### Classification Issues

| ID | Issue | Location | Recommendation |
|----|-------|----------|----------------|
| GDI-001 | Auth mixes RBAC rules with providers | `auth/` | Split L3/L4 |
| GDI-002 | Services contain domain logic | `services/*.py` | Per-file review |
| GDI-003 | Integrations is misnamed | `integrations/` | Acknowledge or rename to `bridges/` |
| GDI-004 | Utils has mixed concerns | `utils/` | Split by purpose |

### Domain Concentration

The **core domain logic** is concentrated in 9 directories:

1. `policy/` — Constitutional governance
2. `optimization/` — Envelope safety cage
3. `routing/` — CARE-L routing
4. `learning/` — C5 learning
5. `predictions/` — C2 predictions
6. `discovery/` — Discovery ledger
7. `costsim/` — Cost simulation
8. `workflow/` — Workflow engine
9. `agents/` — Agent orchestration

**Insight:** These 9 directories contain ~80% of business logic. The rest is orchestration or infrastructure.

---

## Phase 1 Completion Summary

**Completed:** 2025-12-30
**Scope:** Backend (~400 files, 36 directories)

### Deliverables

| # | Deliverable | Status | Key Finding |
|---|-------------|--------|-------------|
| 1 | Directory-level truth map | ✅ DONE | 36 directories classified |
| 2 | Dependency-direction map | ✅ DONE | Zero circular deps, 9.2/10 health |
| 3 | Runtime-trigger map | ✅ DONE | 3 temporal violations identified |
| 4 | State ownership map | ✅ DONE | 5 state ownership issues |
| 5 | Policy enforcement map | ✅ DONE | 30+ enforcement points |
| 6 | Glue vs Domain classification | ✅ DONE | 9 pure domain, 8 pure glue |

### Critical Issues Summary

| Priority | Count | Examples |
|----------|-------|----------|
| P1 | 5 | API lacks L3 adapter, auth mixes L3+L4, module duplication |
| P2 | 5 | Missing __init__.py, dual storage, unenforced restrictions |
| P3 | 4 | Semantic gaps, permission anomalies, legacy debt |

### Health Metrics

| Metric | Value | Target |
|--------|-------|--------|
| Circular dependencies | 0 | 0 |
| Layer confidence HIGH | 72% | >80% |
| Structural issues | 14 | 0 |
| Glue/Domain clarity | 24/35 pure | 100% |

### Next Phase (Phase 2: Structural Alignment)

Phase 2 will address issues found in Phase 1:
1. Split `auth/` into L3 providers + L4 RBAC
2. Consolidate `planner/` vs `planners/`
3. Add L3 adapter for `api/` → `services/`
4. Resolve empty `tasks/` module
5. Fix model duplication in `costsim`

---

## Phase 2B Alignment Summary

**Completed:** 2025-12-30
**Reference:** PHASE2_COMPLETION_GATE.md

### What Changed

| Before (Phase 1) | After (Phase 2B) |
|------------------|------------------|
| api/ performed direct DB writes (L2 collapse) | api/ delegates all writes to L4 services |
| 3 services in services/ | 11 services (8 write-only added) |
| Write ownership unclear | Write ownership explicit per entity |
| API = HYBRID (L2+L4) | API = pure L2 (orchestration only) |

### Structural Guarantees (Now True)

1. **No DB writes in L2 APIs** — All API files perform orchestration only
2. **All DB writes owned by L4 services** — 8 dedicated write services
3. **Execution semantics preserved** — Async remains async, sync remains sync
4. **No structural work remains in Phase 2B** — All batches complete

### Technical Debt Documented (Deferred to Phase 3)

- Async routes using sync DB sessions (recovery files)
- Auth L3/L4 split (Phase 2C)
- Cosmetic naming debt (Phase 2D)

---

## References

- PIN-250: Structural Truth Extraction Lifecycle
- PIN-249: Protective Governance & Housekeeping Normalization
- PIN-248: Codebase Inventory & Layer System
- PIN-245: Integration Integrity System
- PHASE2_COMPLETION_GATE.md: Phase 2 closure artifact
- docs/REPO_STRUCTURE.md: Full repository tree
