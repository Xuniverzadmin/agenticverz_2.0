# Phase 1 Addenda — Execution & State Authority

**Status:** FINAL
**Created:** 2025-12-30
**Reference:** PIN-250 (Structural Truth Extraction Lifecycle)
**Purpose:** Close remaining Phase 1 gaps before Phase 2

---

## Addendum A: Execution Authority Table

**Question answered:** Who is allowed to initiate execution?

| Trigger | Owner | Initiates Via | Allowed Layers | Actual Layers |
|---------|-------|---------------|----------------|---------------|
| HTTP Request | External Client | uvicorn/gunicorn | L2 only | L2 (api/) |
| Worker Poll | WorkerPool (self) | DB polling loop | L5 only | L5 (worker/pool.py) |
| Background Task | FastAPI lifespan | `asyncio.create_task` | L2 (owned by main.py) | L2 (main.py) |
| Timer/Scheduler | **NONE WIRED** | N/A | L5 (if existed) | **GAP** |
| Import-time | Process start | Module load | **NONE (should be zero)** | **VIOLATION: main.py** |

### Import-Time Execution Violations

These execute on every process start (should be zero):

| Location | What Executes | Severity |
|----------|---------------|----------|
| `main.py:51` | `RateLimiter()` | MEDIUM |
| `main.py:52` | `ConcurrentRunsLimiter()` | MEDIUM |
| `main.py:53` | `BudgetTracker()` | MEDIUM |
| `main.py:59` | `init_db()` | **HIGH** — DB connection at import |
| `main.py:62` | `get_planner()` | LOW |

### Execution Initiation Truth

```
┌───────────────────────────────────────────────────────────────┐
│                 EXECUTION INITIATION POINTS                    │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  EXTERNAL TRIGGER (HTTP)                                       │
│  ────────────────────────                                      │
│  Client → uvicorn → main.py → api/* routers                   │
│                                                                │
│  SELF-INITIATED (Worker)                                       │
│  ───────────────────────                                       │
│  worker/pool.py → DB poll → ThreadPoolExecutor → runner.py    │
│                                                                │
│  BACKGROUND (FastAPI)                                          │
│  ────────────────────                                          │
│  main.py lifespan → asyncio.create_task(update_queue_depth)   │
│                                                                │
│  IMPORT-TIME (VIOLATION)                                       │
│  ───────────────────────                                       │
│  Process start → main.py → init_db(), RateLimiter(), etc.     │
│                                                                │
│  SCHEDULER (NOT WIRED)                                         │
│  ─────────────────────                                         │
│  jobs/ exists but has no scheduler — files are orphaned        │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

### Jobs Module Investigation

`jobs/` contains:
- `graduation_evaluator.py`
- `failure_aggregation.py`
- `storage.py`

But `jobs/__init__.py` is 7 lines with no exports and **no scheduler wiring**.

**Finding:** Jobs are defined but never scheduled. This is either:
1. Dead code
2. Incomplete feature
3. Manually triggered (not automated)

---

## Addendum B: State Write Authority Table

**Question answered:** Who may write to each state tier?

### Postgres Write Authority (Truth Tier)

**81 files write to Postgres** — this is too dispersed.

| Layer | Files Writing | Should Write? | Finding |
|-------|---------------|---------------|---------|
| L2 (api/) | 19 files | **NO** — L2 is glue | **VIOLATION** |
| L4 (domain/) | 25+ files | YES | Correct |
| L5 (worker/) | 6 files | YES (execution) | Correct |
| L6 (services/) | 12 files | YES (platform) | Correct |
| L3 (auth/) | 2 files | Conditional | Review needed |

**Critical Finding: L2 writes directly to database.**

API files performing DB writes:
- `api/guard.py`
- `api/ops.py`
- `api/policy.py`
- `api/workers.py`
- `api/traces.py`
- `api/recovery.py`
- `api/memory_pins.py`
- `api/v1_killswitch.py`
- `api/v1_proxy.py`
- `api/integration.py`
- `api/founder_actions.py`
- `api/onboarding.py`
- `api/cost_intelligence.py`
- (and more)

This explains **why L2 "collapsed"** — API routes absorbed domain write logic instead of delegating.

### Redis Write Authority (Advisory Tier)

**5 files write to Redis** — appropriately limited.

| File | Purpose | Acceptable? |
|------|---------|-------------|
| `traces/idempotency.py` | Trace deduplication | YES (L6) |
| `tasks/recovery_queue.py` | Recovery queue | YES (L5) |
| `tasks/recovery_queue_stream.py` | Recovery stream | YES (L5) |
| `agents/services/blackboard_service.py` | Agent blackboard | YES (L4) |
| `memory/embedding_cache.py` | Embedding cache | YES (L6) |

Redis write authority is **correctly bounded**.

### In-Process Write Authority (Cache Tier)

| Singleton | Location | Write Authority | Multi-Worker Safe |
|-----------|----------|-----------------|-------------------|
| `rate_limiter` | main.py | main.py only | NO |
| `concurrent_limiter` | main.py | main.py only | NO |
| `budget_tracker` | main.py | main.py only | NO |
| `_engine` | db.py | db.py only | YES (per-process) |
| `RBACEngine._instance` | auth/rbac_engine.py | RBAC only | NO |
| `GuardCache._instance` | utils/guard_cache.py | Guard only | NO |

In-process singletons are **per-process only** — acceptable for caches, problematic for rate limiting.

### State Write Authority Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    STATE WRITE AUTHORITY                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  POSTGRES (Truth)                                                │
│  ─────────────────                                               │
│  ALLOWED:    L4 (Domain), L5 (Worker), L6 (Platform)            │
│  FORBIDDEN:  L2 (API), L3 (Adapter)                             │
│  VIOLATION:  19+ API files write directly                        │
│                                                                  │
│  REDIS (Advisory)                                                │
│  ────────────────                                                │
│  ALLOWED:    L4, L5, L6                                         │
│  FORBIDDEN:  L2, L3                                             │
│  STATUS:     COMPLIANT (5 files, all appropriate)               │
│                                                                  │
│  IN-PROCESS (Cache)                                              │
│  ──────────────────                                              │
│  ALLOWED:    Owner module only                                  │
│  FORBIDDEN:  Cross-module writes                                │
│  STATUS:     COMPLIANT (but per-process = multi-worker risk)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Addendum C: L2 Collapse Analysis

**Finding:** API is the only L2 directory, but it performs L4 functions.

### Evidence of L2 Collapse

1. **No `__init__.py`** — api/ is a bag of files, not a package
2. **33 route files** — excessive for "thin translation"
3. **19+ files write to DB** — L2 absorbed domain write logic
4. **Direct service imports** — api/ imports L4/L6 directly, no L3 adapter

### L2 Collapse Pattern

```
EXPECTED:                          ACTUAL:
┌─────────┐                        ┌─────────┐
│   L2    │ ─── thin ───>          │   L2    │ ─── FAT ───>
│  (API)  │     adapter            │  (API)  │   (absorbed L4)
└────┬────┘                        └────┬────┘
     │                                  │
     ▼                                  ▼
┌─────────┐                        ┌─────────┐
│   L3    │                        │  SKIP   │ ← missing
│(Adapter)│                        └────┬────┘
└────┬────┘                             │
     │                                  │
     ▼                                  ▼
┌─────────┐                        ┌─────────┐
│   L4    │                        │   L4    │
│(Domain) │                        │(Domain) │
└─────────┘                        └─────────┘
```

### Root Cause

API routes call domain services directly AND perform mutations directly:
- `api/guard.py` → reads/writes agent state
- `api/ops.py` → reads/writes founder data
- `api/policy.py` → reads/writes policy state

This means **L2 is functionally L2+L4 hybrid**, not pure L2.

---

## Addendum D: Hybrid Directory Ranking

**Question:** Which hybrids are inevitable vs. which are lazy boundaries?

| Directory | Current State | Inevitability | Recommendation |
|-----------|---------------|---------------|----------------|
| `auth/` | L3 providers + L4 RBAC | **Separable** | Split: providers/ vs rbac/ |
| `api/` | L2 routes + L4 writes | **Should NOT be hybrid** | Extract writes to services |
| `skills/` | L3 interface + L4 behavior | **Inevitable** — skills ARE domain | Accept as L3.5 |
| `services/` | L4 logic + L6 wiring | **Mostly separable** | Per-file review |
| `worker/` | L5 pool + L5 execution | **Inevitable** — single concern | Accept as L5 |
| `tasks/` | L5 queue + L4 logic | **Separable** | Queue mechanics vs. business logic |
| `integrations/` | L3 name + L4 function | **Misnamed** | Rename to bridges/ or accept |

### Ranking

| Rank | Directory | Verdict |
|------|-----------|---------|
| 1 | `api/` | **MUST split** — L2 should not write to DB |
| 2 | `auth/` | **SHOULD split** — clear L3/L4 boundary |
| 3 | `services/` | **REVIEW** — per-file assessment needed |
| 4 | `tasks/` | **OPTIONAL** — small concern |
| 5 | `integrations/` | **ACCEPT** — just rename or document |
| 6 | `skills/` | **ACCEPT** — inevitable hybrid |
| 7 | `worker/` | **ACCEPT** — single L5 concern |

---

## Phase 1 Completion Gate

### Original Deliverables (6)

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | Directory-level truth map | COMPLETE |
| 2 | Dependency-direction map | COMPLETE |
| 3 | Runtime-trigger map | COMPLETE |
| 4 | State ownership map | COMPLETE |
| 5 | Policy enforcement map | COMPLETE |
| 6 | Glue vs Domain classification | COMPLETE |

### Additional Addenda (4)

| # | Addendum | Status |
|---|----------|--------|
| A | Execution Authority Table | COMPLETE |
| B | State Write Authority Table | COMPLETE |
| C | L2 Collapse Analysis | COMPLETE |
| D | Hybrid Directory Ranking | COMPLETE |

### Phase 1 Now Complete

With these addenda:
- Execution authority is explicit
- State write authority is mapped
- L2 collapse is diagnosed (not fixed)
- Hybrids are ranked by inevitability

**Phase 1 is now 100% complete.**

---

## Overclaims to Remove from STRUCTURAL_TRUTH_MAP.md

The following should be struck or modified:

| Line | Overclaim | Correction |
|------|-----------|------------|
| "Architectural Health: 9.2/10" | Fabricated score | "Structurally intelligible, not yet aligned" |
| "Layer violations: 5 (all justified)" | Phase 2 language | "Layer violations: 5 (observed, not yet resolved)" |
| "tasks/ (empty)" | Incorrect | "tasks/ (4 files, empty __init__.py, no exports)" |
| L3 classification for planner/planners | Overly generous | "L3 (MEDIUM confidence — executes logic)" |

---

## What Phase 2 Now Knows

1. **API writes to DB directly** — this is the #1 structural problem
2. **Import-time execution exists** — DB init at import is HIGH risk
3. **Jobs are orphaned** — defined but never scheduled
4. **Hybrids have clear ranking** — api/ is most urgent to split
5. **Redis authority is clean** — no action needed

Phase 2 can now proceed with surgical precision.
