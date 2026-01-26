# Phase 2: Structural Alignment Plan (v2)

**Status:** CONDITIONALLY APPROVED — Requirements met below
**Created:** 2025-12-30
**Revised:** 2025-12-30
**Reference:** PIN-250, PHASE1_ADDENDA.md
**Prerequisite:** Phase 1 COMPLETE (with Addenda)

---

## Revision Summary

| Issue | Original | Corrected |
|-------|----------|-----------|
| Task 1/Task 3 order | Auth before API | API before Auth |
| Task 1 constraints | Intent-based | Document every move |
| Rollback structure | "git revert" | Checkpoint commits, batched |
| Blast radius | ~29 files at once | ≤10 files per sub-step |

---

## Governing Principle

> **Phase 2 rearranges structure. It does not change behavior.**
>
> If a test fails after Phase 2, the test was wrong or the move was wrong.
> Business logic must be identical before and after.

---

## Explicit Non-Goals (UNCHANGED)

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
| "While we're here" fixes | Scope creep |

**Enforcement:** If a change cannot be described as "moving X from A to B", it is forbidden.

---

## Corrected Execution Order

```
┌─────────────────────────────────────────────────────────────────┐
│                 PHASE 2 EXECUTION ORDER (CORRECTED)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PHASE 2A — Foundation (Safe, unblockers)                       │
│  ─────────────────────────────────────────                      │
│  Task 2: Import-time removal (~9 files)                         │
│  Task 5: Jobs documentation (1 file)                            │
│  Task 4: Tasks wiring decision (0-1 files)                      │
│                                                                  │
│  PHASE 2B — Root Cause Extraction (Isolated, batched)           │
│  ───────────────────────────────────────────────────            │
│  Task 1: API DB Write Extraction (~29 files, in 3 batches)      │
│                                                                  │
│  PHASE 2C — Boundary Clarification                              │
│  ─────────────────────────────────                              │
│  Task 3: Auth L3/L4 split (~46 files)                           │
│                                                                  │
│  PHASE 2D — Cosmetic Debt                                       │
│  ─────────────────────────                                      │
│  Task 6: Planner consolidation (4-5 files)                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Rationale for order:**
- Phase 2A removes temporal violations (safe, unlocks reasoning)
- Phase 2B extracts API writes (root cause must be fixed first)
- Phase 2C splits auth (now auth protects services, not routes)
- Phase 2D cosmetic (lowest risk, last)

---

## PHASE 2A — Foundation

### Task 2: Import-Time Removal

**Priority:** P1
**Files:** ~9
**Risk:** LOW
**Commit Group:** `phase2a-import-time`

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
    init_db()
    planner = get_planner()
    yield
```

#### Rollback Criteria

- [ ] `python -c "from app.main import app"` does NOT create DB connection
- [ ] All existing tests pass
- [ ] No new imports added

---

### Task 5: Jobs Documentation

**Priority:** P2
**Files:** 1
**Risk:** NONE
**Commit Group:** `phase2a-jobs-doc`

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

#### Rollback Criteria

- [ ] No behavior change (comment only)

---

### Task 4: Tasks Wiring Decision

**Priority:** P2
**Files:** 0-1
**Risk:** LOW
**Commit Group:** `phase2a-tasks-wire`

#### Investigation First

```bash
grep -r "from app.tasks" backend/app/ --include="*.py"
grep -r "import app.tasks" backend/app/ --include="*.py"
```

#### Decision Matrix

| Finding | Action |
|---------|--------|
| Files are imported directly | Wire exports in `__init__.py` |
| Files are not imported | Document as orphaned (no code change) |

#### Rollback Criteria

- [ ] If wired: imports work
- [ ] If documented: no code changes

---

## PHASE 2B — Root Cause Extraction

### Task 1: API DB Write Extraction

**Priority:** P0 — ROOT CAUSE
**Files:** ~29 (in 3 batches of ≤10)
**Risk:** HIGH (requires hard constraints)
**Commit Groups:** `phase2b-api-batch1`, `phase2b-api-batch2`, `phase2b-api-batch3`

#### Hard Constraint: Structural Diff Invariant

**For every API file touched, I MUST document:**

| Field | Requirement |
|-------|-------------|
| File | Which API file |
| Existing DB Write(s) | What `session.add/commit` calls exist |
| New Owner Function | What function now owns the write |
| New Owner Layer | L4 (Domain) or L6 (Platform) |
| Call Path Before | `api/X.py` → `session.add()` |
| Call Path After | `api/X.py` → `service.create()` → `session.add()` |

**No undocumented moves. Period.**

#### Batch Structure

**Batch 1 (≤10 files):** Guard & Customer-facing
- api/guard.py
- api/customer_visibility.py
- api/onboarding.py
- api/tenants.py (if enabled)
- (list remaining after investigation)

**Batch 2 (≤10 files):** Ops & Founder-facing
- api/ops.py
- api/founder_actions.py
- api/founder_timeline.py
- (list remaining after investigation)

**Batch 3 (≤10 files):** Domain & System
- api/policy.py
- api/traces.py
- api/workers.py
- api/v1_killswitch.py
- api/v1_proxy.py
- (list remaining after investigation)

#### Pre-Execution Requirement

Before executing any batch, I will produce a **Structural Diff Table**:

```markdown
## Batch N Structural Diff

| File | DB Write | New Owner | Layer | Before | After |
|------|----------|-----------|-------|--------|-------|
| api/guard.py:142 | session.add(Agent) | guard_service.create_agent() | L4 | direct | via service |
| api/guard.py:287 | session.commit() | guard_service.update_status() | L4 | direct | via service |
| ... | ... | ... | ... | ... | ... |
```

**This table must be approved before I touch any code.**

#### Service Facade Pattern

New service files will be:
- < 200 LOC each
- L4 (Domain) layer
- No business logic (just delegation + session management)
- Named: `{domain}_write_service.py` or similar

#### Rollback Criteria

- [ ] All existing tests pass after each batch
- [ ] No `session.add()` or `session.commit()` in API files after completion
- [ ] Each service file is < 200 LOC
- [ ] Each service file has layer header (L4)
- [ ] Import paths: API → L4 Service → L6 (no API → L6)

---

## PHASE 2C — Boundary Clarification

### Task 3: Auth L3/L4 Split

**Priority:** P1
**Files:** ~46
**Risk:** MEDIUM
**Commit Group:** `phase2c-auth-split`

**BLOCKED UNTIL:** Task 1 (API extraction) complete

#### Why This Order Matters

> Auth boundaries cannot be correctly split while API still mutates domain truth.

After Task 1:
- API routes call services
- Services own DB writes
- Auth can protect services (correct)

Before Task 1:
- API routes own DB writes
- Auth protects routes (leaky abstraction)
- Splitting auth would encode wrong boundary

#### Target Structure

```
auth/
├── providers/            # L3 — External verification
│   ├── __init__.py
│   ├── clerk.py
│   ├── oauth.py
│   └── oidc.py
├── rbac/                 # L4 — Authorization rules
│   ├── __init__.py
│   ├── engine.py
│   ├── rules.py
│   ├── role_mapping.py
│   ├── tier_gating.py
│   └── shadow_audit.py
├── middleware/           # L6 — Request pipeline
│   ├── __init__.py
│   ├── rbac_middleware.py
│   ├── jwt_auth.py
│   ├── tenant_auth.py
│   └── console_auth.py
└── __init__.py           # Re-exports for backwards compat
```

#### Rollback Criteria

- [ ] All existing tests pass
- [ ] `from app.auth import X` works for all current exports
- [ ] No circular imports
- [ ] Each subdirectory only imports from allowed layers

---

## PHASE 2D — Cosmetic Debt

### Task 6: Planner Consolidation

**Priority:** P3
**Files:** 4-5
**Risk:** LOW
**Commit Group:** `phase2d-planner`

**BLOCKED UNTIL:** Task 3 complete

#### Action

1. Investigate actual usage of planner/ vs planners/
2. Add layer headers to planners/ files
3. Document coexistence or mark one deprecated

#### Rollback Criteria

- [ ] No import paths changed
- [ ] Both modules still functional

---

## Commit Structure

| Phase | Commit Group | Checkpoint |
|-------|--------------|------------|
| 2A | `phase2a-import-time` | System runnable after |
| 2A | `phase2a-jobs-doc` | System runnable after |
| 2A | `phase2a-tasks-wire` | System runnable after |
| 2B | `phase2b-api-batch1` | System runnable after |
| 2B | `phase2b-api-batch2` | System runnable after |
| 2B | `phase2b-api-batch3` | System runnable after |
| 2C | `phase2c-auth-split` | System runnable after |
| 2D | `phase2d-planner` | System runnable after |

**Rule:** No cross-task commits. Each checkpoint must leave system runnable (see definition below).

---

## Minimum Runnable Definition

**Added per conditional approval requirement.**

After each checkpoint commit, the system must satisfy ALL of the following:

| Check | Method | Pass Criteria |
|-------|--------|---------------|
| **Import succeeds** | `python -c "from app.main import app"` | No exceptions |
| **Server boots** | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | Process starts, no crash |
| **Core router loads** | `curl http://localhost:8000/health` | Returns 200 |
| **Auth initializes** | `curl http://localhost:8000/api/v1/runtime/capabilities` | Returns 401 (auth working) or 200 (with key) |
| **Representative endpoint** | One endpoint per batch group responds | 200, 401, or 403 (not 500) |

**Failure mode:** If ANY check fails after a commit, that commit is rolled back before proceeding.

**Not required:**
- All tests pass (that's Phase 3)
- All endpoints work perfectly
- CI green (no CI yet)

This is a **smoke test**, not a full verification. It ensures the system is not bricked.

---

## Batch Independence Validation (Task 1 Pre-Requisite)

**Added per conditional approval requirement.**

Before executing Task 1 batches, I must validate batch independence.

### Validation Method

```bash
# Check if Batch 1 files are imported by Batch 2/3 files
grep -l "from app.api.guard import\|from app.api.customer_visibility import\|from app.api.onboarding import" \
  backend/app/api/ops.py backend/app/api/founder_actions.py backend/app/api/policy.py \
  backend/app/api/traces.py backend/app/api/workers.py backend/app/api/v1_*.py

# Check if Batch 1 services will be called by Batch 2/3 routes
# (after extraction — hypothetical check)
```

### Decision Matrix

| Finding | Action |
|---------|--------|
| No cross-batch imports | Proceed with proposed batch order |
| Batch 1 → Batch 2 coupling | Move coupled files to same batch |
| Batch 1 → Batch 3 coupling | Move coupled files to same batch |
| Complex coupling | Redefine batches based on actual dependency graph |

### Documentation Requirement

Before Task 1 Batch 1 execution, I will produce:

```markdown
## Batch Independence Report

**Validation performed:** [date]
**Method:** grep for cross-batch imports + manual review

### Findings
- Batch 1 files imported by Batch 2: [list or NONE]
- Batch 1 files imported by Batch 3: [list or NONE]
- Batch 2 files imported by Batch 3: [list or NONE]

### Decision
[Proceed as planned / Reorder batches / Merge batches]

### Rationale
[Why this ordering is safe]
```

**This report must be produced and acknowledged before any Task 1 code is touched.**

---

## Blast Radius Caps

| Task | Max Files Per Sub-step |
|------|------------------------|
| Task 1 (API) | ≤10 files per batch |
| Task 3 (Auth) | ≤15 files per commit |
| Others | No cap needed (small) |

---

## Approval Gates

### Before Phase 2A

- [ ] Confirm plan is approved
- [ ] List exact files for Task 2

### Before Phase 2B (Each Batch)

- [ ] Produce Structural Diff Table
- [ ] Table approved by human
- [ ] Previous batch tests pass

### Before Phase 2C

- [ ] Task 1 fully complete
- [ ] All API files have zero direct DB writes
- [ ] Confirm auth split file list

### Before Phase 2D

- [ ] Task 3 complete
- [ ] Confirm planner investigation results

---

## Estimated Impact (Revised)

| Metric | Estimate |
|--------|----------|
| Files touched | ~90 files |
| New files created | ~14 files |
| Files deleted | 0 |
| Behavior changes | 0 |
| CI changes | 0 |
| Test changes | 0 |
| Commit groups | 8 |
| Approval gates | 4+ |

---

## What Happens If Any Task Fails

1. **STOP** — do not proceed with that task
2. **Document** — record what blocked completion
3. **Defer** — move to Phase 3 with explicit dependency
4. **Continue** — proceed with independent tasks only

Phase 2 is not "all or nothing". Partial completion is acceptable if it preserves truth.

---

## Questions Addressed

| Original Question | Answer |
|-------------------|--------|
| Is Task 1 too aggressive? | Mitigated by batching (≤10 files each) |
| Should Task 3 be deferred? | No — but must come AFTER Task 1 |
| Is execution order correct? | Now yes: 2A → 2B → 2C → 2D |
| Are rollback criteria sufficient? | Now yes: checkpoint commits + batch caps |

---

## Resume Command

After final approval:

**"Phase 2 plan approved — begin Phase 2A Task 2 (import-time removal)"**
