# PIN-507 — First-Principles Audit Findings

**Status:** ACTIVE
**Date:** 2026-01-31
**Category:** Architecture / Audit
**Depends On:** PIN-506 (First-Principles System Physics), PIN-504 (Cross-Domain Resolution)
**Blocks:** Remediation work for Laws 4 and 5

---

## Purpose

Document the results of auditing the HOC system against the 9 laws defined in PIN-506. Identifies structural violations, grades each law, and defines remediation paths.

---

## Audit Scope

- All files under `backend/app/hoc/`
- All L4 handlers in `hoc_spine/orchestrator/handlers/`
- All coordinators in `hoc_spine/orchestrator/coordinators/`
- All L5_schemas files
- All enforcement scripts in `scripts/ops/`
- Audit performed post PIN-504 Phase 6 completion

---

## Scorecard

| # | Law | Status | Grade | Critical Issues |
|---|-----|--------|-------|-----------------|
| 1 | Single Authority | 2 pre-existing L6→L5 violations | **B** | L6 reaching up to L5 |
| 2 | Domain Sovereignty | Clean after PIN-504 | **A** | None |
| 3 | Orchestration Is Rare | 4 coordinators, all pure routing | **A** | None |
| 4 | Context Never Leaks | ~~3 session pass-throughs~~ REMEDIATED | **A** | Correct by construction |
| 5 | Speed From Predictability | ~~31+ getattr()~~ REMEDIATED | **A** | Explicit dispatch maps in all handlers |
| 6 | Types Are Contracts | 1 schema file has logic | **B** | recovery_decisions.py |
| 7 | Ownership in Filesystem | Headers present; 75 missing | **A-** | Legacy modules |
| 8 | Troubleshooting | Centralized logging; 1 silent catch | **A-** | lessons_coordinator bare except |
| 9 | Structural Enforcement | Both validators operational | **A** | None |

---

## Detailed Findings

### Law 1 — Single Authority

**Grade: A — CORRECT BY CONSTRUCTION** *(remediated 2026-02-01, was B)*

L4 handlers are the sole execution authority. No L5 engine reaches up to L4. Zero L6→L5 engine imports remain.

**Remediation applied (2026-02-01):**
- `ThresholdSignal` enum + `ThresholdEvaluationResult` extracted to `controls/L5_schemas/threshold_signals.py`
- `IncidentSeverityEngine` + severity policy extracted to `incidents/L5_schemas/severity_policy.py`
- `threshold_driver.py:271` now imports from L5_schemas (not L5_engines)
- `incident_aggregator.py:60` now imports from L5_schemas (not L5_engines)
- `threshold_engine.py` and `incident_severity_engine.py` retain tombstone re-exports for backward compat
- CI guard `check_l6_no_l5_engine_imports` prevents regression
- Sentinel test `test_law1_law6_boundaries.py::TestLaw1NoL6ToL5EngineImports` asserts invariant

---

### Law 2 — Domain Sovereignty

**Grade: A**

Zero module-level cross-domain imports in L5/L6 after PIN-504 Phase 6. All cross-domain access routes through L4 spine.

3 remaining lazy (function-scoped) cross-domain imports in policies engines are documented structural debt:
- `lessons_engine.py` → `incidents/L6_drivers/lessons_driver` (lazy inside `_get_driver()`)
- `policies_limits_query_engine.py` → `controls/L6_drivers/limits_read_driver` (lazy inside factory)
- `policy_limits_engine.py` → `controls/L6_drivers/policy_limits_driver` (lazy inside constructor)

These do not violate sovereignty at the module level but represent incomplete migration to DomainBridge injection.

---

### Law 3 — Orchestration Is Rare

**Grade: A**

4 coordinators exist. All verified as pure routing with zero business logic:

| Coordinator | Methods | Logic Type |
|---|---|---|
| AuditCoordinator | `record_incident_event`, `record_policy_event` | Parameter mapping + delegation |
| SignalCoordinator | `emit_and_update_risk` | Sequential dual emission |
| LessonsCoordinator | `record_evidence` | Single delegation, fail-open |
| DomainBridge | 4 accessor methods | Lazy import factory |

No coordinator contains domain-data decisions, retry logic, or stateful behavior.

---

### Law 4 — Execution Context Must Never Leak

**Grade: A — CORRECT BY CONSTRUCTION** *(remediated 2026-02-01, was D)*

~~3 violations where execution context (session) leaked through coordinators.~~ All remediated:

| File | Was | Now | Change |
|------|-----|-----|--------|
| `audit_coordinator.py` | Accepted `session`, created cross-domain audit services | **DELETED** (dead code — tombstone in `__init__.py`) | Handlers already inject audit services directly into L5 engines |
| `signal_coordinator.py` | Accepted `session`, passed to two domains | Context-free: accepts `emit_signals` + `update_risk` callables | Session binding in L4 entry point `emit_and_persist_threshold_signal` |
| `domain_bridge.py` | Factory methods accepted `session` | Returns factory callables (`lessons_driver_factory()`, etc.) | Handler binds session via returned factory |

**Enforcement:**
- **Structure:** Zero coordinator class methods accept `session` as parameter
- **Tooling:** `check_init_hygiene.py` enforces L6 cross-domain import ban (prevents L6 re-orchestration)
- **Proof:** `test_law4_context_ownership.py` sentinel test asserts invariant (3 tests)

**Callable contract (PIN-507):** Callables passed to coordinators must be side-effect isolated and non-catching. Exceptions propagate to handler (single blame point).

See: Law 4 Remediation section below for full details.

---

### Law 5 — Speed From Predictability

**Grade: D — CRITICAL**

**Primary violation: 31+ `getattr()` calls across all L4 handlers**

Every handler uses reflection-based dispatch:

```python
method = getattr(facade, method_name, None)  # runtime reflection
if method is None:
    return OperationResult.fail(...)
data = await method(**kwargs)
```

Files affected (every handler):
- `policies_handler.py` — 9 getattr() calls
- `incidents_handler.py` — 3 getattr() calls
- `controls_handler.py` — 2 getattr() calls
- `analytics_handler.py` — 2 getattr() calls
- `integrations_handler.py` — 3 getattr() calls
- `activity_handler.py` — 2 getattr() calls
- `logs_handler.py` — 4 getattr() calls
- `account_handler.py` — 2 getattr() calls
- `api_keys_handler.py` — 1 getattr() call

**Consequences:**
- No compile-time verification of method existence
- Unknown methods discovered only at runtime (string mismatch = 500 error)
- Runtime reflection on every request
- Pyright/mypy cannot verify call signatures

**Secondary violation: `__import__()` in hot paths**

| File | Count | Pattern |
|------|-------|---------|
| `analytics/L5_engines/cost_snapshots_engine.py` | 12+ | `__import__("sqlalchemy").text()` |

**Remediation Path:**
1. **Replace getattr() with explicit dispatch maps:**
   ```python
   METHODS = {
       "list_controls": facade.list_controls,
       "get_status": facade.get_status,
       ...
   }
   method = METHODS.get(method_name)
   ```
2. **Replace `__import__()` with proper top-level imports** in cost_snapshots_engine.py
3. **Consider typed handler classes** per operation instead of generic string dispatch

---

### Law 6 — Types Are Contracts

**Grade: A — CORRECT BY CONSTRUCTION** *(remediated 2026-02-01, was B)*

All L5_schemas files are compliant (pure data or `*_policy.py` pure decision functions).
Zero standalone functions remain in `hoc_spine/schemas/` (excluding pre-existing schema construction helpers).

**Remediation applied (2026-02-01):**
- `combine_confidences`, `should_select_action`, `should_auto_execute` moved to `hoc_spine/utilities/recovery_decisions.py`
- `evaluate_rules()` deleted from schemas — it was hidden cross-domain orchestration (schemas → incidents L5_engines)
- `recovery_decisions.py` in schemas now re-exports from utilities (tombstone for backward compat)
- `recovery_evaluation_engine.py:57` rewired to import from utilities + direct recovery_rule_engine
- New architectural stratum: `hoc_spine/utilities/` for cross-domain pure decision functions
- Domain-specific pure logic convention: `L5_schemas/*_policy.py` files
- CI guard `check_schemas_no_standalone_funcs` prevents regression (with exemption list for schema factories)
- CI guard `check_utilities_purity` prevents utilities from importing engines/drivers/DB
- Sentinel test `test_law1_law6_boundaries.py::TestLaw6SchemaPurity` asserts invariant

---

### Law 7 — Ownership in Filesystem

**Grade: A-**

5/5 sampled key files have complete headers (Layer, AUDIENCE, Role, Callers, Allowed/Forbidden Imports):
- `api/cus/policies/override.py` (L2) — lines 1-10
- `hoc_spine/orchestrator/handlers/controls_handler.py` (L4) — lines 1-12
- `hoc_spine/orchestrator/coordinators/lessons_coordinator.py` (L4) — lines 1-12
- `hoc_spine/orchestrator/coordinators/domain_bridge.py` (L4) — lines 1-12
- `controls/L5_schemas/override_types.py` (L5) — lines 1-6

**Warning:** 75 files missing `# Layer:` headers per BLCA scan. These are mostly supporting/legacy modules. Not blocking but reduces filesystem-as-documentation fidelity.

---

### Law 8 — Troubleshooting Collapses Search Space

**Grade: A-**

**Compliant:**
- All L4 handlers route through `OperationRegistry` which logs:
  - Registration: `operation_registry.py:234`
  - Exceptions with full context: `:299-308` (includes `exc_info=True`)
  - Success/failure audit: `:394-396`
- `audit_coordinator.py` and `signal_coordinator.py` have logger instances

**1 warning:**

| File | Lines | Issue |
|------|-------|-------|
| `lessons_coordinator.py` | 69-71 | Bare `except Exception: pass` — intentional fail-open but **zero logging** of swallowed exception |

At 3am, a lessons engine failure is completely invisible. The fail-open design is correct (learning must not block incident creation), but the exception should be logged at DEBUG level.

---

### Law 9 — Structural Enforcement

**Grade: A**

| Validator | Location | Status | Current Result |
|---|---|---|---|
| `hoc_cross_domain_validator.py` | `scripts/ops/` | 5 rules (D1, E1, E2, C1, I1), `--ci` mode | **0 violations** |
| `layer_validator.py` (BLCA) | `scripts/ops/` | Full layer boundary checks, `--ci` mode | 628 violations (pre-existing debt, PIN-438) |

Cross-domain validator tracks baselines, detects regressions (exit code 3), supports `--trend` history. Both validators have CI-compatible exit codes.

---

## Priority Remediation Queue

| Priority | Law | Issue | Effort | Impact |
|----------|-----|-------|--------|--------|
| ~~P0~~ ✅ | Law 5 | ~~Replace 31 `getattr()` with explicit dispatch maps~~ **DONE** | — | Compile-time safety, predictable dispatch |
| ~~P0~~ ✅ | Law 4 | ~~Remove session from coordinator signatures~~ **DONE** | — | Correct by construction |
| ~~P1~~ ✅ | Law 1 | ~~Extract `ThresholdSignal` enum to L5_schemas~~ **DONE** | — | Clean L6→L5 boundary |
| ~~P1~~ ✅ | Law 6 | ~~Move recovery_decisions.py functions to utility module~~ **DONE** | — | Schema purity |
| ~~P1~~ ✅ | Law 1 | ~~Extract severity calculation from incident_aggregator~~ **DONE** | — | Clean L6→L5 boundary |
| **P2** | Law 8 | Add debug logging to lessons_coordinator bare except | Trivial | 3am visibility |
| ~~P2~~ ✅ | Law 5 | ~~Replace `__import__()` in cost_snapshots_engine~~ **DONE** | — | Predictable imports |
| **P3** | Law 7 | Add headers to 75 missing files | Low | Filesystem documentation |

---

## Acceptance Criteria for Remediation

- Law 4: Zero coordinator accepts `session` as parameter ✅ VERIFIED 2026-02-01
- Law 5: Zero `getattr()` calls in L4 handler dispatch paths ✅ VERIFIED 2026-02-01
- Law 6: Zero functions in `hoc_spine/schemas/` files (excluding schema construction helpers) ✅ VERIFIED 2026-02-01
- Law 1: Zero L6→L5 engine imports (module-level or lazy) ✅ VERIFIED 2026-02-01
- Law 8: Zero bare `except: pass` without logging

---

## Law 5 Remediation — Completed 2026-02-01

**Scope:** Replace reflection-based dispatch with explicit dispatch maps; remove `__import__()` calls.

### Part A — L4 Handler Dispatch Maps (9 files, 18 handler classes)

All `getattr(facade, method_name, None)` replaced with local `dispatch = { "method_name": facade.method_name, ... }` dictionaries. All `asyncio.iscoroutinefunction()` eliminated via explicit sync/async split.

| File | Classes Modified | Dispatch Type |
|------|-----------------|---------------|
| `controls_handler.py` | `ControlsQueryHandler`, `ControlsOverrideHandler` | All async |
| `api_keys_handler.py` | `ApiKeysQueryHandler` | All async |
| `overview_handler.py` | `OverviewQueryHandler` | All async |
| `account_handler.py` | `AccountQueryHandler`, `AccountNotificationsHandler` | All async |
| `analytics_handler.py` | `AnalyticsQueryHandler`, `AnalyticsDetectionHandler` | All async |
| `activity_handler.py` | `ActivityQueryHandler`, `ActivityTelemetryHandler` | All async |
| `incidents_handler.py` | `IncidentsQueryHandler`, `IncidentsExportHandler`, `IncidentsWriteHandler` | All async (Write is sync call) |
| `integrations_handler.py` | `IntegrationsQueryHandler`, `IntegrationsConnectorsHandler`, `IntegrationsDataSourcesHandler` | All async |
| `logs_handler.py` | `LogsQueryHandler` (mixed), `LogsEvidenceHandler`, `LogsCertificateHandler` (sync), `LogsPdfHandler` (sync) | Mixed |
| `policies_handler.py` | `PoliciesQueryHandler`, `PoliciesEnforcementHandler`, `PoliciesGovernanceHandler` (sync), `PoliciesLessonsHandler` (sync), `PoliciesPolicyFacadeHandler` (mixed), `PoliciesLimitsHandler`, `PoliciesRulesHandler`, `PoliciesRateLimitsHandler`, `PoliciesSimulateHandler` | Mixed |

**Already correct (no changes needed):** `ControlsThresholdHandler`, `LogsReplayHandler`, `LogsEvidenceReportHandler`, `ActivitySignalFingerprintHandler`, `ActivitySignalFeedbackHandler`

### Part B — `__import__()` Removal

`cost_snapshots_engine.py`: Added `from sqlalchemy import text` at top; replaced 13 `__import__("sqlalchemy").text(...)` → `text(...)`. Updated header comment per D4.

### Verification Results

- `grep -r 'getattr(' handlers/` → **0 matches**
- `grep -r '__import__' cost_snapshots_engine.py` → **0 matches**
- `grep -r 'iscoroutinefunction' handlers/` → **0 matches**

---

## Law 0 Follow-on Remediation — 2026-02-01

**Scope:** Fix broken test collection and Makefile toolchain hardening. Distinct from Law 5 remediation above.

Initial fixes unmasked a cascade of deeper failures hidden by eager `__init__` re-exports. Each fix revealed the next broken import in the chain. Total: 10 source files fixed, 2 test files rewired, 1 Makefile, 1 sentinel test file created, 3 `__init__.py` stale re-exports cleaned.

### Source Import Fixes (10 files)

| # | File | Old Import | New Import | Root Cause |
|---|------|-----------|------------|------------|
| 1 | `app/services/incident_write_engine.py:29` | `app.services.logs.audit_ledger_service` | `app.hoc.cus.logs.L5_engines.audit_ledger_engine` | Service relocated to HOC |
| 2 | `app/worker/runner.py:48` | `..services.incidents.facade` (submodule) | `..services.incidents` (package `__init__`) | Facade exported from `__init__`, no `.facade` submodule |
| 3 | `app/hoc/cus/logs/L6_drivers/export_bundle_store.py:43` | `from app.db import Incident` | `from app.models.killswitch import Incident` | `Incident` is L7 model, never was in `app.db` |
| 4 | `app/hoc/cus/logs/L5_engines/__init__.py:14` | `LogsDomainFacade, get_logs_domain_facade` | `LogsFacade, get_logs_facade` | Class name wrong in `__init__` (actual: `LogsFacade`) |
| 5 | `app/hoc/cus/integrations/L5_engines/__init__.py:34` | `from .learning_proof_engine import ...` | Removed (16 re-exports) | Module moved to `policies/L5_engines/` during PIN-498 |
| 6 | `app/hoc/cus/integrations/L5_schemas/__init__.py:13` | `from .cost_snapshot_schemas import ...` | Removed (8 re-exports) | Module lives in `analytics/L5_schemas/`, wrong domain |
| 7 | `app/hoc/cus/integrations/L5_engines/cost_bridges_engine.py:41` | `from ..schemas.loop_events import` | `from app.hoc.cus.integrations.L5_schemas.loop_events import` | Relative `..schemas` resolved to non-existent path |
| 8 | `app/services/policy/__init__.py:45` | `from .lessons_engine import LessonsLearnedEngine` | Removed | Shim is disconnected (PIN-468); class moved to HOC |
| 9 | `app/api/policy_layer.py:38` | `from app.services.policy.facade import` | `from app.services.policy import` | `facade.py` renamed to `policy_driver.py`; `__init__` re-exports |
| 10a | `app/services/limits/policy_limits_service.py:43` | `app.services.logs.audit_ledger_service_async` | `app.hoc.cus.logs.L6_drivers.audit_ledger_driver` | `app.services.logs` abolished |
| 10b | `app/services/limits/policy_rules_service.py:44` | `app.services.logs.audit_ledger_service_async` | `app.hoc.cus.logs.L6_drivers.audit_ledger_driver` | `app.services.logs` abolished |
| 10c | `app/services/policy_proposal.py:39` | `app.services.logs.audit_ledger_service_async` | `app.hoc.cus.logs.L6_drivers.audit_ledger_driver` | `app.services.logs` abolished |
| 10d | `app/services/governance/facade.py:552` | `from app.services.policy.facade import` | `from app.services.policy import` | Same as #9 |

**Transitional dependencies:** Files #1, #10a-c now import from HOC (`services→hoc`). These are documented transitional exceptions with comments at each import site. Permanent fix: migrate these legacy service files into HOC L5.

### Test Import Rewires (2 files)

| File | Old Import | New Import | Root Cause |
|------|-----------|------------|------------|
| `tests/test_m25_integration_loop.py:23` | `app.integrations.L3_adapters` | `app.integrations.bridges` | L3 abolished (PIN-485); classes live in `bridges` |
| `tests/test_m25_policy_overreach.py:12` | `app.integrations.L3_adapters` | `app.integrations.events` | L3 abolished (PIN-485); `ConfidenceCalculator` lives in `events` |

### Eager `__init__` Warnings Added (2 files)

- `app/hoc/cus/logs/L5_engines/__init__.py` — WARNING docstring: eager re-exports cause full domain load
- `app/hoc/cus/logs/L6_drivers/__init__.py` — WARNING docstring: eager re-exports cause full domain load

Known Law 0 risk: eager domain-wide imports mask downstream failures. Deferred refactor to lazy imports.

### L6→L7 Import Boundary Comment (1 file)

`app/hoc/cus/logs/L6_drivers/export_bundle_store.py` — Added boundary invariant comment: L6 drivers must not import L7 models via `app.db`.

### Import Surface Sentinel Test (1 new file)

`tests/governance/t0/test_import_surface_sentinels.py` — 8 tests exercising top-level package imports for logs, incidents, and integrations domains. Prevents future masked import failures from hiding behind eager `__init__` chains. 1 xfail: pre-existing `ValidatorVerdict` undefined in `contract_engine.py` (HOC spine TODO, out of scope).

### Makefile Toolchain Fix

`backend/Makefile`: All 7 occurrences of `python ` → `python3 `. No other files in the repo use bare `python` for invocation.

### Unblocked Tests

- `test_founder_review_invariants.py` — 38 tests, all pass
- `test_category7_legacy_routes.py` — 40 tests, all pass
- `test_phase5a_governance.py` — 29 tests, all pass
- `test_m25_integration_loop.py` — 26 tests, all pass
- `test_m25_policy_overreach.py` — 16 tests, all pass

### Verification

- `pytest --collect-only` → **0 collection errors** (was 7 before session)
- Governance tests: **648 passed, 1 xfailed** (was 641)
- All 5 formerly-broken test files collect and execute: **149 tests pass**

### Known Remaining Issue (Out of Scope)

`app/hoc/hoc_spine/authority/contracts/contract_engine.py:352` — `ValidatorVerdict` undefined at class-definition time. Pre-existing bug with TODO comment. Detected by sentinel test (xfailed). Requires injecting `ValidatorVerdict` from CRM validator engine via orchestrator context.

---

## Structural Guardrails (2026-02-01)

Six structural gaps were identified from first-principles analysis and addressed with mechanical enforcement:

### Gap 1–2: `__init__.py` Constraints + Static Hygiene Rule

**Artifact:** `scripts/ci/check_init_hygiene.py`
**Makefile target:** `make init-hygiene` (integrated into `ci-test` and `ci-full`)

Enforces seven invariants:
1. **Stale re-export detection:** `__init__.py` relative imports must reference modules that exist on disk
2. **L6→L7 boundary:** L6 drivers must not import L7 models via `app.db` — use `app.models.*`
3. **Abolished path detection:** No imports from paths in `ABOLISHED_PATHS` list
4. **L6 cross-domain import ban (Law 4):** L6 drivers must not import from sibling domain L5/L6 — cross-domain orchestration belongs at L4
5. **L6→L5 engine import ban (Law 1):** L6 drivers must not import from L5_engines — may only import L5_schemas
6. **Schema purity (Law 6):** `hoc_spine/schemas/` must not contain standalone functions (pre-existing schema factories exempted)
7. **Utilities purity (Law 1+6):** `hoc_spine/utilities/` must not import L5_engines, L6_drivers, or app.db

Known exceptions: `hoc/int/` and `hoc/api/int/` paths are reported as warnings (pre-existing, not yet remediated).

### Gap 3: Canonical Authority Map

Authority is enforced mechanically via the CI script's `ABOLISHED_PATHS` and `L7_MODELS_VIA_DB` lists. Per-domain authority tables are documented in each domain's `SOFTWARE_BIBLE.md` under the "Law 0 Import Hygiene" sections added in this session.

### Gap 4: Comprehensive Import Surface Testing

**Artifact:** `tests/governance/t0/test_import_surface_sentinels.py`

Two-strategy sentinel test:
1. **Static tests:** Known-critical import paths for logs, incidents, integrations domains
2. **Dynamic discovery:** `_discover_hoc_submodules()` walks all `.py` files under `app/hoc/cus/`, converts to module names, and attempts `importlib.import_module()` on each

Results: 239 modules import successfully, 47 xfailed (pre-existing issues documented in `KNOWN_XFAILS` and `KNOWN_ERROR_XFAILS`).

### Gap 5: Mechanical Layer Boundary Enforcement

L6→L7 boundary is enforced by `check_init_hygiene.py` check #2. Two violations were found and fixed during this session:
- `logs/L6_drivers/export_bundle_store.py` — `Incident` moved from `app.db` to `app.models.killswitch`
- `incidents/L6_drivers/export_bundle_driver.py` — same pattern

### Gap 6: Migration Exhaustiveness Rule

**Rule:** Every PIN that moves, renames, or abolishes a module MUST include a call-site exhaustiveness check. The check must:
1. `grep -r` for all import references to the old path
2. Rewire every call site (not just the "main" one)
3. Verify with `pytest --collect-only` that zero collection errors result

This rule is enforced mechanically by `check_init_hygiene.py`'s `ABOLISHED_PATHS` list — any PIN that abolishes a path adds it to this list, and CI fails if any file still imports from it.

## Law 4 Remediation — Completed 2026-02-01

**Scope:** Remove session from all coordinator signatures. Enforce by structure, tooling, and proof.

### Part 1 — Delete `audit_coordinator.py` (dead code)

`audit_coordinator.py` was unused — all L4 handlers already create audit services directly (`AuditLedgerService(ctx.session)` in `incidents_handler.py:129`, `AuditLedgerServiceAsync(ctx.session)` in `policies_handler.py:278`). Grep confirmed zero handler imports of `audit_coordinator`, `get_audit_coordinator`, or `AuditCoordinator`.

- **Deleted:** `app/hoc/hoc_spine/orchestrator/coordinators/audit_coordinator.py`
- **Tombstone:** Added to `coordinators/__init__.py` — prevents silent re-introduction

### Part 2 — Refactor `signal_coordinator.py` to context-free callables

`SignalCoordinator.emit_and_update_risk()` rewritten:
- **Before:** `(self, session, tenant_id, run_id, state, signals, params_used)` — passed session to two domains
- **After:** `(self, *, emit_signals: Callable, update_risk: Callable)` — pure topology, zero context

New L4 entry point `emit_and_persist_threshold_signal()` added to `signal_coordinator.py`:
- Binds session to callables via lambdas
- Delegates to coordinator for topology (emit first, then update risk)
- This is the ONLY place where session meets cross-domain topology

`emit_and_persist_threshold_signal` deleted from `threshold_driver.py` (L6 → L4 promotion). Tombstone left at deletion site.

**Callers updated:**
- `app/worker/runner.py:567` — imports from `signal_coordinator` instead of `threshold_driver`
- `app/hoc/int/analytics/engines/runner.py:567` — same

### Part 3 — Refactor `domain_bridge.py` to factory callables

Session-accepting methods replaced with factory callables:
- `lessons_driver(session)` → `lessons_driver_factory()` returns `lambda session: LessonsDriver(session)`
- `limits_read_driver(session)` → `limits_read_driver_factory()` returns factory
- `policy_limits_driver(session)` → `policy_limits_driver_factory()` returns factory

`logs_read_service()` unchanged (already session-free).

### Part 4 — CI: L6 Cross-Domain Import Guard

Added `check_l6_cross_domain_imports()` to `scripts/ci/check_init_hygiene.py`:
- Scans all `cus/*/L6_drivers/*.py` files
- Flags any `from ... hoc.cus.{other_domain}. ...` import
- Prevents L6 re-orchestration regression
- Starts clean: 0 existing violations

### Part 5 — Sentinel Test

Created `tests/governance/t0/test_law4_context_ownership.py`:
- `test_no_session_in_coordinator_signatures` — AST-walks all coordinator classes
- `test_no_l6_cross_domain_imports` — scans all L6 drivers for sibling domain imports
- `test_audit_coordinator_deleted` — asserts tombstone holds

### Verification

- `grep -rn "session" coordinators/*.py` in class method signatures → **0 hits**
- `test_law4_context_ownership.py` → **3 passed**
- `check_init_hygiene.py --ci` → **0 blocking violations**
- `test_import_surface_sentinels.py` → **240 passed, 46 xfailed**
- Full governance suite → **2250 passed, 46 xfailed**

---

### Additional Fix: `credentials/__init__.py` Stale Import

`app/hoc/cus/integrations/L5_engines/credentials/__init__.py` had `from .types import Credential` but `types.py` lives in the parent package (`L5_engines/types.py`). Fixed to absolute import.

---

## Law 1 + Law 6 Remediation — Completed 2026-02-01

**Scope:** Eliminate L6→L5 engine upward reach (Law 1) and remove behavior from schema files (Law 6). Enforce by structure, tooling, and proof.

### Part 1 — Create `hoc_spine/utilities/` stratum

New architectural category for cross-domain pure decision functions. Boundary contract enforced by `check_utilities_purity` CI guard:
- MUST NOT import from L5_engines, L6_drivers, or app.db
- MAY import from hoc_spine/schemas, L5_schemas, stdlib

**Created:** `app/hoc/hoc_spine/utilities/__init__.py`

### Part 2 — Extract ThresholdSignal to L5_schemas (Law 1)

`ThresholdSignal(str, Enum)` and `ThresholdEvaluationResult(dataclass)` moved from `controls/L5_engines/threshold_engine.py` → `controls/L5_schemas/threshold_signals.py`. These are types, not engine logic.

- **Created:** `controls/L5_schemas/threshold_signals.py`
- **Modified:** `threshold_engine.py` — replaced definitions with tombstone re-export, removed unused `Enum` import
- **Modified:** `threshold_driver.py:271` — import from L5_schemas (not L5_engines)

### Part 3 — Extract severity policy to L5_schemas (Law 1)

`IncidentSeverityEngine`, `SeverityConfig`, `TRIGGER_SEVERITY_MAP`, `DEFAULT_SEVERITY`, `generate_incident_title` moved from `incidents/L5_engines/incident_severity_engine.py` → `incidents/L5_schemas/severity_policy.py`. This is pure stateless policy (no DB, no I/O).

- **Created:** `incidents/L5_schemas/severity_policy.py`
- **Modified:** `incident_severity_engine.py` — replaced with tombstone re-exports
- **Modified:** `incident_aggregator.py:60` — import from L5_schemas (not L5_engines)

### Part 4 — Move recovery decisions to utilities (Law 6)

`combine_confidences`, `should_select_action`, `should_auto_execute` moved from `hoc_spine/schemas/recovery_decisions.py` → `hoc_spine/utilities/recovery_decisions.py`. These are algorithms (behavior), not type definitions.

`evaluate_rules()` **deleted** from schemas — it was hidden cross-domain orchestration (schemas → incidents L5_engines).

- **Created:** `hoc_spine/utilities/recovery_decisions.py`
- **Modified:** `hoc_spine/schemas/recovery_decisions.py` — re-export surface + tombstone for evaluate_rules
- **Modified:** `recovery_evaluation_engine.py:57` — imports from utilities + direct recovery_rule_engine

### Part 5 — CI Guards (3 new checks)

Added to `scripts/ci/check_init_hygiene.py` (now 7 invariants total):

| # | Guard | Law | What it prevents |
|---|-------|-----|-----------------|
| 5 | `check_l6_no_l5_engine_imports` | Law 1 | L6 reaching up to L5_engines |
| 6 | `check_schemas_no_standalone_funcs` | Law 6 | Behavior in hoc_spine/schemas/ (exemption list for schema factories) |
| 7 | `check_utilities_purity` | Law 1+6 | Utilities importing engines/drivers/DB |

### Part 6 — Sentinel Tests

**Created:** `tests/governance/t0/test_law1_law6_boundaries.py` — 4 tests:
1. `test_no_l6_imports_l5_engines` — Law 1 invariant
2. `test_no_standalone_functions_in_schemas` — Law 6 invariant
3. `test_utilities_no_forbidden_imports` — utilities purity
4. `test_no_l6_cross_domain_imports` — Law 1 cross-domain (mirrors Law 4 test)

### Verification

- `check_init_hygiene.py --ci` → **0 blocking violations** (7 invariants)
- `test_law1_law6_boundaries.py` → **4 passed**
- `test_law4_context_ownership.py` → **3 passed**
- Full governance suite → **2256 passed, 46 xfailed**
