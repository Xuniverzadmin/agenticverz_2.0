# Phase 2: Structural Alignment Plan

**Status:** PLANNING
**Created:** 2025-12-30
**Reference:** PIN-250-structural-truth-extraction-lifecycle.md
**Prerequisite:** Phase 1 Complete (STRUCTURAL_TRUTH_MAP.md)

---

## Objective

Make structure match reality with minimal semantic churn.

**Constraints:**
- No new business logic
- Changes must be structural, not behavioral
- Each change must reference Phase 1 finding

---

## Issue Analysis Summary

### P1 Issues (Critical)

| ID | Issue | Location | Phase 1 Finding | Proposed Resolution |
|----|-------|----------|-----------------|---------------------|
| P1-AUTH | Auth mixes L3+L4+L6 | `auth/` | Files properly classified but co-located | Create subdirectory structure |
| P1-PLANNER | Module duplication | `planner/` vs `planners/` | Two modules with similar names, different purposes | Consolidate with clear naming |
| P1-OBSERVABILITY | Hidden module | `observability/` | Single file, no `__init__.py` | Add proper package structure |
| P1-TASKS | Silent module | `tasks/` | 4 files with empty `__init__.py` | Wire exports or document isolation |
| P1-API | API lacks L3 adapter | `api/` | Direct L2→L4 coupling | Add thin adapter layer |

### P2 Issues (State/Temporal)

| ID | Issue | Location | Phase 1 Finding |
|----|-------|----------|-----------------|
| SOI-001 | Model duplication | `db.py` vs `models/costsim_cb.py` | Dual definition of CostBudget |
| SOI-002 | Per-process rate limiting | `main.py` | RateLimiter state per process |
| TBV-001 | DB init at import-time | `main.py` | `init_db()` called at import |

---

## Structural Alignment Tasks

### Task 1: Auth Directory Structure

**Finding Reference:** Phase 1 - Auth mixes L3+L4 in single directory

**Current State:**
```
auth/
├── __init__.py
├── clerk_provider.py      # L3 - Provider
├── oauth_providers.py     # L3 - Provider
├── oidc_provider.py       # L3 - Provider
├── rbac.py                # L4 - Domain
├── rbac_engine.py         # L4 - Domain
├── role_mapping.py        # L4 - Domain
├── tier_gating.py         # L4 - Domain
├── shadow_audit.py        # L4 - Domain
├── jwt_auth.py            # L6 - Platform
├── rbac_middleware.py     # L6 - Platform
├── tenant_auth.py         # L6 - Platform
└── console_auth.py        # L6 - Platform
```

**Classification:**
- L3 Providers (3 files): clerk_provider, oauth_providers, oidc_provider
- L4 Domain (5 files): rbac, rbac_engine, role_mapping, tier_gating, shadow_audit
- L6 Platform (4 files): jwt_auth, rbac_middleware, tenant_auth, console_auth

**Options:**

| Option | Description | Risk | Import Changes |
|--------|-------------|------|----------------|
| A | Keep flat (document only) | Low | None |
| B | Create subdirs (providers/, domain/, infra/) | Medium | Many |
| C | Extract L3 to separate package | High | Very many |

**Recommendation:** Option A (document) or Option B if we want physical separation.

**Behavioral Impact:** None (imports change, behavior same)

---

### Task 2: Planner Module Consolidation

**Finding Reference:** Phase 1 - Module duplication (planner/ vs planners/)

**Current State:**
```
planner/                    # L3 Boundary Adapter (has header)
├── __init__.py            # Lazy imports for StubPlanner
├── interface.py           # PlannerInterface protocol
└── stub_planner.py        # StubPlanner + LegacyStubPlanner

planners/                   # No header! (governance violation)
├── __init__.py            # get_planner() factory
├── anthropic_adapter.py   # AnthropicPlanner
├── stub_adapter.py        # Another StubPlanner
└── test_planners.py       # Tests (wrong location!)
```

**Issues:**
1. Confusing naming (`planner` vs `planners`)
2. `planners/` lacks layer headers
3. Two `StubPlanner` implementations
4. Test file in source directory

**Proposed Resolution:**
1. Add headers to `planners/` files
2. Rename `planners/` → `planner_adapters/` (clearer distinction)
3. Remove redundant StubPlanner OR document why both exist
4. Move `test_planners.py` to `tests/`

**Behavioral Impact:** Import path changes; functionality unchanged

---

### Task 3: Tasks Module Wiring

**Finding Reference:** Phase 1 - Empty tasks/ module

**Current State:**
```
tasks/
├── __init__.py                  # "# Tasks module" (no exports!)
├── m10_metrics_collector.py     # NOT exported
├── memory_update.py             # NOT exported
├── recovery_queue.py            # NOT exported
└── recovery_queue_stream.py     # NOT exported
```

**Issue:** `__init__.py` doesn't export any modules. Files exist but aren't wired.

**Investigation Needed:**
- Are these files actively used via direct imports (`from app.tasks.recovery_queue import ...`)?
- Or are they dead code?

**Resolution Options:**

| Option | When to Use |
|--------|-------------|
| Wire exports | Files are actively used |
| Document isolation | Intentional isolation |
| Delete | Dead code |

---

### Task 4: Observability Module Structure

**Finding Reference:** Phase 1 - Hidden observability/ module

**Current State:**
```
observability/
├── __pycache__/
└── cost_tracker.py    # Single file, no __init__.py
```

**Issue:** No `__init__.py`, can only be imported as `from app.observability.cost_tracker import ...`

**Resolution:**
1. Add `__init__.py` with proper exports
2. Add layer header to `cost_tracker.py`

---

### Task 5: Model Duplication (costsim)

**Finding Reference:** SOI-001 - Model duplication

**Location:** `db.py` vs `models/costsim_cb.py`

**Investigation Needed:**
- Confirm both define CostBudget
- Determine which is authoritative
- Plan migration to single source of truth

---

## Execution Order

Phase 2 should execute in this order to minimize risk:

1. **Task 4: observability/** - Lowest risk (add `__init__.py`)
2. **Task 3: tasks/** - Investigation + wiring
3. **Task 5: costsim model** - Investigation + consolidation
4. **Task 2: planner/planners** - Consolidation
5. **Task 1: auth/** - Document or restructure (highest risk)
6. **Task 6: api/ adapter** - Add L3 layer (new code, requires ARTIFACT_INTENT)

---

## Validation Checklist

Each structural change must pass:

- [ ] No behavior change (tests still pass)
- [ ] Import paths updated in all callers
- [ ] `__init__.py` exports maintained
- [ ] Layer headers added/updated
- [ ] No new dependencies introduced

---

## Approval Required

This plan requires approval before execution begins.

**Resume Command:**
Say: **"Approve Phase 2 plan - begin with Task 4 (observability)"**

Or modify the plan:
- "Modify Phase 2 - skip auth restructuring"
- "Modify Phase 2 - prioritize planner consolidation"
