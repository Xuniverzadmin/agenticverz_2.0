# HOC Spine — System Runtime Gaps & Closure Plan

**Date:** 2026-02-07
**Status:** PLAN (updated with execution evidence)
**Scope:** `backend/app/hoc/cus/hoc_spine/` runtime correctness gaps
**References:** HOC_SPINE_CONSTITUTION.md, PIN-520

---

## Status Update (2026-02-07)

| Gap | Status | Closure Evidence |
|-----|--------|------------------|
| G1 | **CLOSED** | `backend/app/hoc/cus/hoc_spine/orchestrator/run_governance_facade.py:335-383`, `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/__init__.py:182-186` |
| G2a | **CLOSED** | `backend/app/hoc/cus/hoc_spine/drivers/ledger.py:66-168` |
| G2b | **CLOSED** | `backend/app/hoc/cus/hoc_spine/drivers/decisions.py:201-313` |
| G3 | **CLOSED** | `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/activity_handler.py:218-275` |
| G4 | **CLOSED** | `backend/app/hoc/cus/hoc_spine/services/dispatch_audit.py` (DispatchRecord + builder), `backend/app/hoc/cus/hoc_spine/services/audit_store.py:record_dispatch()`, `backend/app/hoc/cus/hoc_spine/orchestrator/operation_registry.py:_audit_dispatch()` (Phase A.6) |
| G5 | **CLOSED** | `backend/app/hoc/api/infrastructure/` deleted — 4 files were stale copies of `app/middleware/` (zero callers, header-only diffs). Canonical versions live in `app/middleware/{rate_limit,slow_requests,tenancy,tenant}.py` |

---

## Part 1 — Gap Inventory (Evidence-Based)

### Gap G1: RunGovernanceFacade is a Null Facade at Runtime

**Severity:** HIGH — governance records silently skipped  
**Status:** **CLOSED (Batch 1 complete)**

Resolved by wiring the facade at startup with real engines and enforcing a
fail-fast getter if called before wiring.

**Closure Evidence:**

| Location | Line | Evidence |
|----------|------|----------|
| `orchestrator/run_governance_facade.py` | 335-361 | `wire_run_governance_facade()` injects real engines |
| `orchestrator/run_governance_facade.py` | 364-383 | `get_run_governance_facade()` fails fast if unwired |
| `orchestrator/handlers/__init__.py` | 182-186 | `bootstrap_hoc_spine()` wires facade at startup |

**Runtime consequence (previous):** silent no-op for policy evaluations and lessons.  
**Current state:** facade is wired at startup and fail-fast if called before wiring.

#### Acceptance Criteria: "Runtime must not silently no-op"

1. `get_run_governance_facade()` must return a facade with **real** injected
   engines (LessonsEnginePort, PolicyEvaluationPort).
2. Calling `facade.create_policy_evaluation(...)` must produce a non-None
   `policy_evaluation_id` when invoked with valid params and a reachable DB.
3. Calling any lessons method must either produce a result or raise (not
   silently return `None` from a swallowed `NotImplementedError`).

#### Guard Test (Implemented)

```python
# tests/hoc_spine/test_run_governance_facade_wiring.py

def test_facade_is_not_null():
    """RunGovernanceFacade must not be constructed with None engines."""
    from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import (
        get_run_governance_facade,
    )
    facade = get_run_governance_facade()
    assert facade._lessons_engine is not None, (
        "LessonsEnginePort not injected — facade is a null stub"
    )
    assert facade._policy_evaluator is not None, (
        "PolicyEvaluationPort not injected — facade is a null stub"
    )


def test_policy_evaluation_does_not_silently_noop():
    """create_policy_evaluation must not swallow NotImplementedError."""
    from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import (
        get_run_governance_facade,
    )
    facade = get_run_governance_facade()

    # If engines are None, this MUST raise, not return None silently
    try:
        result = facade.create_policy_evaluation(
            run_id="test-run-001",
            tenant_id="test-tenant",
            run_status="succeeded",
        )
        # If we get here, result must be a real policy_evaluation_id
        assert result is not None, (
            "create_policy_evaluation returned None — governance silently no-oped"
        )
    except NotImplementedError:
        # Acceptable: not-wired facade raises instead of silently swallowing
        pass
```

---

### Gap G2: hoc_spine Driver Transaction Impurity

**Severity:** HIGH — violates Constitution §2.6: "Drivers never commit"  
**Status:** **CLOSED (Batch 2 complete)**

Resolved by removing driver-owned engines and commits. All driver functions now
require a caller-provided connection; L4 owns transaction boundaries.

#### G2a: `drivers/ledger.py` — standalone commit path

**Closure Evidence:**
| Location | Line | Evidence |
|----------|------|----------|
| `drivers/ledger.py` | 66-168 | `emit_signal()` requires connection, executes only, no commit |

When `session=None` (standalone mode), `emit_signal()` creates a raw connection
from `get_engine()` and commits internally. The session-aware path (line 189-195)
correctly uses `session.flush()` without committing — but the standalone path
violates driver purity.

#### G2b: `drivers/decisions.py` — internal engine ownership

**Closure Evidence:**
| Location | Line | Evidence |
|----------|------|----------|
| `drivers/decisions.py` | 201-313 | `DecisionRecordService` uses injected connection only |

`DecisionRecordService` creates its own `sqlalchemy.Engine` via `create_engine(DATABASE_URL)`
and manages all transaction boundaries internally. Every `engine.begin()` block
auto-commits on exit. This is a complete bypass of L4 transaction ownership.

#### Driver Purity Acceptance Criteria

Per Constitution §2.6 and PIN-520 Phase 3.2.3:

1. **No `session.commit()`, `session.rollback()`** in any `hoc_spine/drivers/*.py` file.
2. **No `create_engine()`** in any `hoc_spine/drivers/*.py` file.
3. **No `engine.begin()`** in any `hoc_spine/drivers/*.py` file.
4. All driver functions must accept an injected `session` or `connection` parameter.
5. L4 handlers/coordinators own all commit boundaries.

**AST scan command (verification):**
```bash
cd backend && PYTHONPATH=. python3 -c "
import ast, pathlib
drivers = pathlib.Path('app/hoc/cus/hoc_spine/drivers')
violations = []
for f in drivers.glob('*.py'):
    if f.name == '__init__.py': continue
    tree = ast.parse(f.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in ('commit', 'rollback', 'begin'):
            violations.append(f'{f.name}:{node.lineno} — .{node.attr}()')
        if isinstance(node, ast.Name) and node.id == 'create_engine':
            violations.append(f'{f.name}:{node.lineno} — create_engine')
for v in sorted(violations):
    print(v)
print(f'Total: {len(violations)} violations')
"
```

---

### Gap G3: ActivityDiscoveryHandler Calls Committing Driver Without Session

**Severity:** MEDIUM — L4 handler triggers driver's standalone commit path  
**Status:** **CLOSED (Batch 3a complete)**

| Location | Line | Evidence |
|----------|------|----------|
| `orchestrator/handlers/activity_handler.py` | 218-275 | L4 creates connection, passes to driver, commits writes |

`ActivityDiscoveryHandler.execute()` calls `emit_signal()` from `ledger.py`
without passing `session=ctx.session`. Since `session` defaults to `None`,
`ledger.py` takes the standalone path (line 196-204) — creating its own engine
connection and committing internally.

This means the discovery signal write happens **outside** the L4 transaction
boundary. If the broader operation fails after `emit_signal()`, the signal
persists anyway (no atomicity).

**Fix pattern:** L4 owns connection lifecycle and commit.

---

### Gap G4: Consequences & Audit Integration are Stubs — **CLOSED (2026-02-07)**

**Severity:** LOW — structural gaps but not runtime failures

**Resolution (Phase A.6):**

1. Created `hoc_spine/services/dispatch_audit.py` — pure `DispatchRecord` dataclass
   and `build_dispatch_record()` builder (no side effects, no I/O).
2. Extended `audit_store.py` with `record_dispatch(record)` and
   `get_dispatch_records()` — in-memory + optional Redis persistence.
3. Extended `_audit_dispatch()` in `operation_registry.py` — after structured
   logging, builds a `DispatchRecord` and persists to `AuditStore`. Wrapped in
   try/except so audit persistence never breaks dispatch (non-blocking).

Post-commit only — dispatch recording never participates in the operation's
transaction (Constitution §2.3).

**Remaining (not blocking):** Consequences layer has a single adapter
(`export_bundle_adapter.py`). Additional adapters and post-commit hooks are
future work (not required for G4 closure).

---

### Gap G5: `api/infrastructure/` is Not Under an Audience Root — **CLOSED (2026-02-07)**

**Severity:** LOW — structural, not a runtime issue

**Resolution:** All 4 files were **stale copies** of their canonical counterparts in
`app/middleware/`. Zero imports pointed to `app.hoc.api.infrastructure` — all callers
use `app.middleware.*` instead. Diffs confirmed header-only differences (infrastructure
copies had outdated L2/CUSTOMER headers; middleware versions have correct L6 layer).

**Action taken:** Deleted all 4 files and removed the `infrastructure/` directory.

| Deleted File | Canonical Location |
|-------------|-------------------|
| `infrastructure/rate_limit.py` | `app/middleware/rate_limit.py` (L6) |
| `infrastructure/slow_requests.py` | `app/middleware/slow_requests.py` (L2) |
| `infrastructure/tenancy.py` | `app/middleware/tenancy.py` (L6) |
| `infrastructure/tenant.py` | `app/middleware/tenant.py` (L6) |

---

## Part 2 — Three-Batch Execution Plan

### Batch 1: Wire RunGovernanceFacade at Startup

**Goal:** `get_run_governance_facade()` returns a facade with real engines injected.

**Work:**

1. Create a bootstrap wiring function in `run_governance_facade.py` (or a new
   `bootstrap_governance.py`):
   ```python
   def bootstrap_run_governance_facade() -> RunGovernanceFacade:
       from app.hoc.cus.policies.L5_engines.engine import create_policy_evaluation_sync
       from app.hoc.cus.hoc_spine.services.lessons_engine import get_lessons_engine
       return RunGovernanceFacade(
           lessons_engine=get_lessons_engine(),
           policy_evaluator=create_policy_evaluation_sync,
       )
   ```
2. Replace the lazy singleton in `get_run_governance_facade()` to require
   prior wiring (fail-fast if called too early).

**Status:** **COMPLETE (2026-02-07)**

**Evidence:**
- Wiring function: `backend/app/hoc/cus/hoc_spine/orchestrator/run_governance_facade.py:335-361`
- Fail-fast getter: `backend/app/hoc/cus/hoc_spine/orchestrator/run_governance_facade.py:364-383`
- Startup call: `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/__init__.py:182-186`
3. Wire into `main.py` lifespan startup (after `bootstrap_hoc_spine()`).
4. Remove the `except Exception` swallow in `create_policy_evaluation()` — let
   `NotImplementedError` propagate so it's caught by tests.
5. Add the two failing tests from the spec above.

**Pre-check:** Verify `LessonsEnginePort` and `PolicyEvaluationPort` protocol
signatures match the real engine implementations (check `schemas/protocols.py`).

**Gates after Batch 1:**

```bash
cd backend && PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
cd backend && PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py --ci
cd backend && PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py
cd backend && PYTHONPATH=. python3 -m pytest tests/hoc_spine/test_run_governance_facade_wired.py -v
cd backend && PYTHONPATH=. python3 -m pytest tests/hoc_spine/test_hoc_spine_import_guard.py -v
```

---

### Batch 2: Driver Transaction Purity (ledger.py + decisions.py)

**Goal:** Zero `commit`/`rollback`/`create_engine`/`engine.begin` in
`hoc_spine/drivers/*.py`.

#### Batch 2a: Refactor `ledger.py`

1. Remove the standalone commit path (lines 196-204).
2. Make `session` a **required** parameter (no `Optional`, no `None` default).
3. Remove `from app.db import get_engine` — ledger must not own an engine.
4. The function uses `session.execute(upsert_sql, params)` + `session.flush()`
   only (existing session-aware path, line 189-195).
5. Update all callers to pass `session`.

#### Batch 2b: Refactor `decisions.py`

1. Refactor `DecisionRecordService` to accept an injected `session` or
   `connection` instead of owning a `create_engine()`.
2. Replace all `engine.begin()` blocks with session-based execution.
3. Create an L4 handler (`DecisionRecordHandler` or extend `SystemHandler`)
   that owns the commit boundary.
4. Helper functions (`emit_routing_decision`, `emit_budget_decision`, etc.)
   must accept a `session` parameter; L4 callers pass it.
5. Remove `create_engine` import and `_get_engine()` method.

**Note:** `decisions.py` is a large file (1358 lines). The refactor must
preserve the `DecisionRecord` model and all enum types (they're used by
callers). Only the persistence/emission layer changes.

**Status:** **COMPLETE (2026-02-07)**

**Evidence:**
- Ledger purity: `backend/app/hoc/cus/hoc_spine/drivers/ledger.py:66-168`
- Decisions purity: `backend/app/hoc/cus/hoc_spine/drivers/decisions.py:201-313`

**Gates after Batch 2:**

```bash
cd backend && PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
cd backend && PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py --ci
cd backend && PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py

# AST scan — must report 0 violations
cd backend && PYTHONPATH=. python3 -c "
import ast, pathlib
drivers = pathlib.Path('app/hoc/cus/hoc_spine/drivers')
violations = []
for f in drivers.glob('*.py'):
    if f.name == '__init__.py': continue
    tree = ast.parse(f.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in ('commit', 'rollback', 'begin'):
            violations.append(f'{f.name}:{node.lineno} — .{node.attr}()')
        if isinstance(node, ast.Name) and node.id == 'create_engine':
            violations.append(f'{f.name}:{node.lineno} — create_engine')
for v in sorted(violations):
    print(v)
print(f'Total: {len(violations)} violations')
"

cd backend && PYTHONPATH=. python3 -m pytest tests/hoc_spine/ -v
```

---

### Batch 3: Fix ActivityDiscoveryHandler + Wire AuditStore (Optional)

**Goal:** L4 handler passes session to ledger driver; optionally integrate
AuditStore into OperationRegistry.

#### Batch 3a: Fix ActivityDiscoveryHandler (Required)

1. In `activity_handler.py` line 243, pass `session=ctx.session` (or extract
   a sync session from `ctx.params` if ledger.py requires sync Session).
2. Since `ledger.py` (after Batch 2a) requires `session`, this is now mandatory.
3. If `ctx.session` is `AsyncSession` but ledger.py uses sync `Session`, use
   the sync session pattern documented in `OperationContext` (pass via
   `ctx.params["sync_session"]`).

#### Batch 3b: AuditStore Integration (Optional — Phase A.6)

1. In `operation_registry.py`, extend `_audit_dispatch()` to call
   `get_audit_store().add_dispatch_record(...)` after logging.
2. Only for post-commit hooks — do not make AuditStore a transaction
   participant (per Constitution §2.3: consequences are post-commit).
3. Define minimal consequences hook: operation name, outcome, duration, tenant.

**Status:** **3a COMPLETE (2026-02-07)** / **3b COMPLETE (2026-02-07)**

**Evidence (3a):**
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/activity_handler.py:218-275`

**Evidence (3b):**
- `backend/app/hoc/cus/hoc_spine/services/dispatch_audit.py` (DispatchRecord + build_dispatch_record)
- `backend/app/hoc/cus/hoc_spine/services/audit_store.py:record_dispatch()` + `get_dispatch_records()`
- `backend/app/hoc/cus/hoc_spine/orchestrator/operation_registry.py:_audit_dispatch()` (AuditStore persistence)

**Gates after Batch 3:**

```bash
cd backend && PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci
cd backend && PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py --ci
cd backend && PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py
cd backend && PYTHONPATH=. python3 -m pytest tests/hoc_spine/ -v
# Route snapshot must be unchanged
cd backend && PYTHONPATH=. python3 -c "
from app.main import app
routes = [r for r in app.routes if hasattr(r, 'path')]
print('total_routes', len(routes))
"
```

---

## Part 3 — Execution Order & Dependencies

```
Batch 1 (RunGovernanceFacade wiring)
  ├── Independent — can start immediately
  └── Pre-req for: nothing (standalone)

Batch 2 (Driver transaction purity)
  ├── 2a (ledger.py) — independent
  ├── 2b (decisions.py) — independent of 2a
  └── Pre-req for: Batch 3a (handler needs refactored ledger)

Batch 3a (ActivityDiscoveryHandler session fix)
  ├── Depends on: Batch 2a (ledger.py must accept required session)
  └── Pre-req for: nothing

Batch 3b (AuditStore integration — Phase A.6) ✅ COMPLETE
  ├── Independent of all other batches
  └── dispatch_audit.py + audit_store.record_dispatch + _audit_dispatch extension
```

**Recommended execution (historical):** Batch 1 and Batch 2 in parallel; Batch 3a after Batch 2a.
Batch 3b is now complete.

---

## Part 4 — Summary of All Evidence Locations

| Gap | File | Lines | Description |
|-----|------|-------|-------------|
| G1 | `orchestrator/run_governance_facade.py` | 335-383 | Wired facade + fail-fast getter |
| G1 | `orchestrator/handlers/__init__.py` | 182-186 | Wiring invoked at startup |
| G2a | `drivers/ledger.py` | 66-168 | Connection-required driver, no commit |
| G2b | `drivers/decisions.py` | 201-313 | Connection-required driver, no engine ownership |
| G3 | `orchestrator/handlers/activity_handler.py` | 218-275 | L4 owns connection lifecycle + commit |
| G4 | `services/dispatch_audit.py` | 1-126 | DispatchRecord + build_dispatch_record (pure builder) |
| G4 | `services/audit_store.py` | record_dispatch() | Dispatch persistence (in-memory + Redis) |
| G4 | `consequences/ports.py` | 1-64 | ConsequenceAdapter protocol |
| G4 | `consequences/pipeline.py` | 1-160 | ConsequencePipeline (register/freeze/run) |
| G4 | `consequences/adapters/dispatch_metrics_adapter.py` | 1-180 | DispatchMetricsAdapter (real adapter) |
| G4 | `orchestrator/handlers/__init__.py` | 188-205 | Pipeline wiring + freeze at startup |
| G4 | `orchestrator/operation_registry.py` | _audit_dispatch() | Logging + AuditStore persistence + consequences |
| G5 | `api/infrastructure/` (DELETED) | — | 4 stale copies deleted; canonical in `app/middleware/` |

---

## Open Tasks (Tracked — No Residual Risk Untracked)

None.
