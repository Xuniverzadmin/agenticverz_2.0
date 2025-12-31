# Phase 2: Structural Alignment Plan (DRAFT)

**Status:** DRAFT — Awaiting Challenge
**Created:** 2025-12-30
**Reference:** PIN-250, PHASE1_ADDENDA.md
**Prerequisite:** Phase 1 COMPLETE (with Addenda)

---

## Governing Principle

> **Phase 2 rearranges structure. It does not change behavior.**
>
> If a test fails after Phase 2, the test was wrong or the move was wrong.
> Business logic must be identical before and after.

---

## Scope Boundaries

### What Phase 2 IS

- Moving responsibility between layers
- Splitting files that mix concerns
- Removing import-time execution
- Introducing adapters where **proven necessary by Phase 1**
- Updating import paths

### What Phase 2 IS NOT

- Behavior changes
- Optimizations
- Feature additions
- CI definition
- "Improvements"
- Cleanup unrelated to Phase 1 findings

---

## Explicit Non-Goals

| Non-Goal | Why Forbidden |
|----------|---------------|
| Define CI gates | CI would encode broken structure |
| Improve code quality | Scope creep; not structural |
| Add error handling | Behavior change |
| Refactor business logic | Semantic change |
| Touch AI Console | Product work, not structural |
| Add tests for new structure | Phase 3 work |
| Remove dead code | Requires behavioral judgment |
| Optimize performance | Not structural |
| Update documentation | Phase 3 work |
| Add type hints | Not structural |

**Enforcement:** If a change cannot be described as "moving X from A to B", it is forbidden.

---

## Alignment Tasks (Ordered by Priority)

### Task 1: API DB Write Extraction

**Priority:** P0 — Root cause of L2 collapse
**Finding Reference:** Addendum B (19+ API files write to Postgres)
**Goal:** API routes must not write to database directly.

#### Current State (WRONG)

```
api/guard.py ──► session.add() ──► Postgres
api/ops.py ──► session.commit() ──► Postgres
api/policy.py ──► session.add() ──► Postgres
(16 more files)
```

#### Target State (CORRECT)

```
api/guard.py ──► guard_service.create() ──► Postgres
api/ops.py ──► ops_service.update() ──► Postgres
api/policy.py ──► policy_service.write() ──► Postgres
```

#### File Estimates

| Action | Files Affected | Lines Changed (est.) |
|--------|----------------|---------------------|
| Create service facades | ~10 new files | ~1500 new |
| Update API routes | ~19 files | ~2000 modified |
| Update imports | ~19 files | ~100 modified |

**Total:** ~29 files touched, ~10 new service files

#### Rollback Criteria

- [ ] All existing tests pass unchanged
- [ ] No new imports from L2 → L6 (only L2 → L4)
- [ ] API files have zero `session.add()` or `session.commit()` calls
- [ ] Service files are < 200 LOC each (thin facades)

#### What This Task Does NOT Do

- Does not change what data is written
- Does not change when writes occur
- Does not add validation
- Does not add error handling beyond what exists
- Does not optimize queries

---

### Task 2: Import-Time Execution Removal

**Priority:** P1 — Temporal violation
**Finding Reference:** Addendum A (main.py:51-62)
**Goal:** Zero code executes at import time.

#### Current State (WRONG)

```python
# main.py (lines 51-62)
rate_limiter = RateLimiter()        # Executes at import
concurrent_limiter = ConcurrentRunsLimiter()  # Executes at import
budget_tracker = BudgetTracker()    # Executes at import
init_db()                           # DB CONNECTION at import
planner = get_planner()             # Executes at import
```

#### Target State (CORRECT)

```python
# main.py
rate_limiter: Optional[RateLimiter] = None
concurrent_limiter: Optional[ConcurrentRunsLimiter] = None
budget_tracker: Optional[BudgetTracker] = None
planner: Optional[PlannerProtocol] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rate_limiter, concurrent_limiter, budget_tracker, planner
    rate_limiter = RateLimiter()
    concurrent_limiter = ConcurrentRunsLimiter()
    budget_tracker = BudgetTracker()
    await init_db_async()  # Or sync in lifespan
    planner = get_planner()
    yield
    # cleanup if needed
```

#### File Estimates

| Action | Files Affected | Lines Changed (est.) |
|--------|----------------|---------------------|
| Modify main.py | 1 file | ~50 modified |
| Update callers of globals | ~5 files | ~20 modified |
| Add null checks where needed | ~3 files | ~15 modified |

**Total:** ~9 files touched

#### Rollback Criteria

- [ ] `python -c "from app.main import app"` does NOT create DB connection
- [ ] All existing tests pass
- [ ] Startup time is measurable (not blocked by import)

#### What This Task Does NOT Do

- Does not change what gets initialized
- Does not add new initialization
- Does not change initialization order (just timing)

---

### Task 3: Auth L3/L4 Split

**Priority:** P1 — Clear boundary violation
**Finding Reference:** Phase 1 Directory Map (auth mixes L3+L4)
**Goal:** Separate verification (L3) from authorization rules (L4).

#### Current State (WRONG)

```
auth/
├── clerk_provider.py     # L3 ✓
├── oauth_providers.py    # L3 ✓
├── oidc_provider.py      # L3 ✓
├── rbac.py               # L4 ✓
├── rbac_engine.py        # L4 ✓
├── rbac_middleware.py    # L6 (mixed)
├── role_mapping.py       # L4 ✓
├── tier_gating.py        # L4 ✓
├── shadow_audit.py       # L4 ✓
├── jwt_auth.py           # L6 ✓
├── tenant_auth.py        # L6 ✓
└── console_auth.py       # L6 ✓
```

#### Target State (CORRECT)

```
auth/
├── providers/            # NEW — L3 only
│   ├── __init__.py
│   ├── clerk.py          # from clerk_provider.py
│   ├── oauth.py          # from oauth_providers.py
│   └── oidc.py           # from oidc_provider.py
├── rbac/                 # NEW — L4 only
│   ├── __init__.py
│   ├── engine.py         # from rbac_engine.py
│   ├── rules.py          # from rbac.py
│   ├── role_mapping.py   # unchanged
│   ├── tier_gating.py    # unchanged
│   └── shadow_audit.py   # unchanged
├── middleware/           # NEW — L6 only
│   ├── __init__.py
│   ├── rbac_middleware.py
│   ├── jwt_auth.py
│   ├── tenant_auth.py
│   └── console_auth.py
└── __init__.py           # Re-exports for backwards compat
```

#### File Estimates

| Action | Files Affected | Lines Changed (est.) |
|--------|----------------|---------------------|
| Create subdirectories | 3 new dirs | 0 |
| Move files | 12 files | 0 (just move) |
| Create __init__.py files | 4 new files | ~80 new |
| Update imports in auth/ | 12 files | ~60 modified |
| Update external imports | ~30 files | ~90 modified |

**Total:** ~46 files touched, 4 new files

#### Rollback Criteria

- [ ] All existing tests pass unchanged
- [ ] `from app.auth import X` still works for all public exports
- [ ] No circular imports introduced
- [ ] Each subdirectory imports only from allowed layers

#### What This Task Does NOT Do

- Does not change any auth logic
- Does not add new auth methods
- Does not change RBAC rules
- Does not modify middleware behavior

---

### Task 4: Silent Module Wiring (tasks/)

**Priority:** P2 — Structural clarity
**Finding Reference:** Addendum A (tasks/ has no exports)
**Goal:** Either wire exports or document intentional isolation.

#### Investigation Required First

Before acting, determine:

1. Are these files imported directly (`from app.tasks.recovery_queue import ...`)?
2. Or are they orphaned?

```bash
# Run this to check usage
grep -r "from app.tasks" backend/app/ --include="*.py"
grep -r "import app.tasks" backend/app/ --include="*.py"
```

#### If Used Directly

Add proper exports to `__init__.py`:

```python
# tasks/__init__.py
from .m10_metrics_collector import M10MetricsCollector
from .memory_update import MemoryUpdateTask
from .recovery_queue import RecoveryQueue
from .recovery_queue_stream import RecoveryQueueStream

__all__ = [...]
```

#### If Orphaned

Document as dead code for future removal (not Phase 2 work).

#### File Estimates

| Scenario | Files Affected |
|----------|----------------|
| If wiring | 1 file (tasks/__init__.py) |
| If documenting | 0 files (just add note) |

**Total:** 0-1 files

#### Rollback Criteria

- [ ] If wired: imports work as expected
- [ ] If documented: no code changes needed

---

### Task 5: Orphaned Jobs Documentation

**Priority:** P2 — Structural clarity
**Finding Reference:** Addendum A (jobs defined but never scheduled)
**Goal:** Document that jobs/ is incomplete, do NOT attempt to wire.

#### Action

Add header comment to `jobs/__init__.py`:

```python
# STRUCTURAL NOTE (Phase 2):
# This module contains job definitions that are NOT currently scheduled.
# No scheduler is wired. These are either:
# - Future work (incomplete)
# - Dead code (to be removed in future phase)
# Do not attempt to "fix" by adding scheduler — that is behavior change.
```

#### File Estimates

| Action | Files Affected |
|--------|----------------|
| Add documentation comment | 1 file |

**Total:** 1 file

#### Rollback Criteria

- [ ] No behavior change (comment only)

---

### Task 6: planner/ vs planners/ Consolidation

**Priority:** P3 — Naming confusion
**Finding Reference:** Phase 1 Directory Map (module duplication)
**Goal:** Clarify which is authoritative, add headers to planners/.

#### Investigation Required First

Determine actual usage:

```bash
grep -r "from app.planner " backend/app/ --include="*.py" | wc -l
grep -r "from app.planners " backend/app/ --include="*.py" | wc -l
```

#### Options

| Option | When | Action |
|--------|------|--------|
| A | planner/ is used more | Add "DEPRECATED" to planners/ |
| B | planners/ is used more | Add "DEPRECATED" to planner/ |
| C | Both actively used | Document coexistence, add headers |

#### File Estimates

| Scenario | Files Affected |
|----------|----------------|
| Option A or B | ~5 files (deprecation notices) |
| Option C | ~4 files (headers only) |

**Total:** 4-5 files

#### Rollback Criteria

- [ ] No import paths changed
- [ ] No functionality changed
- [ ] Both modules still work

---

## Execution Order

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2 EXECUTION ORDER                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Week 1: Foundation                                              │
│  ───────────────────                                             │
│  Task 2: Import-time removal (9 files)                          │
│  Task 5: Jobs documentation (1 file)                            │
│  Task 4: Tasks investigation + wiring (0-1 files)               │
│                                                                  │
│  Week 2: Auth Restructure                                        │
│  ─────────────────────────                                       │
│  Task 3: Auth L3/L4 split (46 files)                            │
│                                                                  │
│  Week 3-4: API Extraction                                        │
│  ─────────────────────────                                       │
│  Task 1: API DB write extraction (29 files)                     │
│                                                                  │
│  Week 5: Cleanup                                                 │
│  ─────────────────────                                           │
│  Task 6: Planner consolidation (4-5 files)                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Note:** "Week" is organizational, not a time estimate.

---

## Global Rollback Criteria

Before any task is considered complete:

- [ ] All existing tests pass unchanged
- [ ] No new test files created (Phase 3 work)
- [ ] No behavior observable to API clients has changed
- [ ] Import paths are backwards compatible OR all callers updated
- [ ] No CI configuration changes
- [ ] No new dependencies added
- [ ] Layer headers present on all moved/created files

---

## What Happens If Phase 2 Fails

If any task cannot be completed without behavior change:

1. **STOP** — do not proceed with that task
2. **Document** — record what blocked completion
3. **Defer** — move to Phase 3 with explicit dependency
4. **Continue** — proceed with other tasks

Phase 2 is not "all or nothing". Partial completion is acceptable if it preserves truth.

---

## Estimated Total Impact

| Metric | Estimate |
|--------|----------|
| Files touched | ~90 files |
| New files created | ~14 files |
| Files deleted | 0 |
| Behavior changes | 0 |
| CI changes | 0 |
| Test changes | 0 |

---

## Explicit Approval Gates

Before executing each task, require:

1. Confirmation that prerequisites are met
2. List of exact files to be touched
3. Verification that rollback criteria are measurable

**No task executes without explicit "proceed" from human.**

---

## Questions for Challenger

1. Is the execution order correct? (Import-time → Auth → API)
2. Is Task 1 (API extraction) too aggressive for Phase 2?
3. Should Task 3 (Auth split) be deferred to reduce risk?
4. Are the rollback criteria sufficient?
5. What am I missing?

---

## Resume Command

After challenge is complete, say:

**"Phase 2 plan approved — begin with Task 2 (import-time removal)"**

Or modify:

**"Phase 2 plan approved with modifications: [list changes]"**
