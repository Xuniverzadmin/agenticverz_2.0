# Controls Domain — Canonical Software Literature

**Domain:** controls
**Generated:** 2026-01-31
**Reference:** PIN-499
**Total Files:** 28 (11 L5_engines, 4 L5_schemas, 10 L6_drivers, 2 adapters, 1 __init__.py)

---

## Consolidation Actions (2026-01-31)

### Naming Violations Fixed (9 renames)

**L5 (6):**

| # | Old Name | New Name |
|---|----------|----------|
| N1 | alert_fatigue.py | alert_fatigue_engine.py |
| N2 | cb_sync_wrapper.py | cb_sync_wrapper_engine.py |
| N3 | cost_safety_rails.py | cost_safety_rails_engine.py |
| N4 | decisions.py | decisions_engine.py |
| N5 | killswitch.py | killswitch_engine.py |
| N6 | s2_cost_smoothing.py | s2_cost_smoothing_engine.py |

**L6 (3):**

| # | Old Name | New Name |
|---|----------|----------|
| N7 | circuit_breaker.py | circuit_breaker_driver.py |
| N8 | circuit_breaker_async.py | circuit_breaker_async_driver.py |
| N9 | scoped_execution.py | scoped_execution_driver.py |

### Structural Fix: L5_controls/ Relocated (2 files)

Non-standard `L5_controls/` directory contained engine and driver in nested subdirs. Relocated to standard topology:

| Old Path | New Path |
|----------|----------|
| L5_controls/engines/customer_killswitch_read_engine.py | L5_engines/customer_killswitch_read_engine.py |
| L5_controls/drivers/killswitch_read_driver.py | L6_drivers/killswitch_read_driver.py |

`L5_controls/` directory deleted after relocation.

### Import Path Fix (1)

| File | Old Import | New Import |
|------|-----------|------------|
| adapters/customer_killswitch_adapter.py | `...controls.L5_controls.engines.customer_killswitch_read_engine` | `...controls.L5_engines.customer_killswitch_read_engine` |

### Header Issues — None

`controls/__init__.py` already declares `# Layer: L5 — Domain Package`. Correct.

### Legacy Connections — None Active

Two `app.services` references exist but both are inside docstring Usage examples (not active imports):
- `alert_fatigue_engine.py` line 37: docstring
- `controls_facade.py` line 42: docstring

### New L5_schemas File (PIN-504 Phase 6)

| File | Contents | Purpose |
|------|----------|---------|
| `L5_schemas/override_types.py` | `LimitOverrideServiceError`, `LimitNotFoundError`, `OverrideNotFoundError`, `OverrideValidationError`, `StackingAbuseError` | Error types extracted from `L6_drivers/override_driver.py` so L2 can import without L6 dependency |

### Cross-Domain Imports (3 — Documented, Deferred to Rewiring)

| File | Target Domain | Import Path |
|------|--------------|-------------|
| customer_killswitch_read_engine.py | policies | `app.hoc.cus.policies.controls.drivers.killswitch_read_driver` |
| customer_killswitch_adapter.py | **general (ABOLISHED)** | `app.hoc.cus.general.L5_controls.engines.guard_write_engine` — **DEAD IMPORT: `cus/general/` abolished per PIN-485. Must repoint to `hoc_spine.*` during cleansing cycle.** |
| ~~threshold_driver.py~~ | ~~activity~~ | ~~`app.hoc.cus.activity.L6_drivers.run_signal_driver`~~ **REMOVED** (PIN-507 Law 4) |

**Correct architecture:** Cross-domain access should go through L4 spine. `threshold_driver.py` cross-domain import remediated (PIN-507 Law 4 — signal emission moved to L4). All L6→L5 engine imports remediated (PIN-507 Law 1).

### ~~L6→L5 Runtime Import~~ — REMEDIATED (PIN-507 Law 1, 2026-02-01)

~~`threshold_driver.py` line 287 imports `ThresholdSignal` from `L5_engines.threshold_engine`~~ **FIXED.** `ThresholdSignal` extracted to `controls/L5_schemas/threshold_signals.py`. `threshold_driver.py` now imports from L5_schemas (not L5_engines). CI guard `check_l6_no_l5_engine_imports` prevents regression.

### Layer Anomaly (1 — Documented)

`budget_enforcement_engine.py` declares `# Layer: L4 — Domain Engine (System Truth)` but lives in L5_engines/. Intentional per PIN-257 (Phase R-3 L5→L4 Violation Fix). Governance: correct per PHASE_R_L5_L4_VIOLATIONS.md.

---

## Domain Persona (from __init__.py)

Controls domain handles customer-facing control configurations:
- Token usage limits and thresholds
- Cost usage limits and budgets
- Credit usage tracking and alerts
- RAG access auditing (LLM verification before inference)

---

## L5_engines (11 files)

### __init__.py
- **Role:** Package init

### alert_fatigue_engine.py *(renamed from alert_fatigue.py)*
- **Role:** Alert deduplication and fatigue control (Redis-backed)
- **Callers:** AlertEmitter (L3), EventReactor (L5)

### budget_enforcement_engine.py
- **Role:** Budget enforcement decision-making (System Truth)
- **Layer Anomaly:** Declares L4 but lives in L5_engines (intentional per PIN-257)

### cb_sync_wrapper_engine.py *(renamed from cb_sync_wrapper.py)*
- **Role:** Circuit breaker synchronous wrapper

### controls_facade.py
- **Role:** Controls facade — centralized access to control operations
- **Callers:** L4 controls_handler (controls.query)

### cost_safety_rails_engine.py *(renamed from cost_safety_rails.py)*
- **Role:** Cost safety rails enforcement

### customer_killswitch_read_engine.py *(relocated from L5_controls/engines/)*
- **Role:** Customer killswitch read operations
- **Cross-domain:** Imports from policies domain

### decisions_engine.py *(renamed from decisions.py)*
- **Role:** Control decision logic

### killswitch_engine.py *(renamed from killswitch.py)*
- **Role:** Killswitch activation/deactivation logic

### s2_cost_smoothing_engine.py *(renamed from s2_cost_smoothing.py)*
- **Role:** S2 cost smoothing algorithm

### threshold_engine.py
- **Role:** Threshold evaluation and signal emission
- **Status:** Tombstone re-exports removed (PIN-508 Phase 4A)
- **Callers:** L4 controls_handler (controls.thresholds)

---

## L5_schemas (4 files)

### __init__.py
- **Role:** Schemas package init

### overrides.py
- **Role:** Override configuration schemas

### policy_limits.py
- **Role:** Policy limits schema definitions

### simulation.py
- **Role:** Simulation schema definitions

---

## L6_drivers (10 files)

### __init__.py
- **Role:** Package init

### budget_enforcement_driver.py
- **Role:** Budget enforcement DB operations

### circuit_breaker_driver.py *(renamed from circuit_breaker.py)*
- **Role:** Circuit breaker state persistence (sync)

### circuit_breaker_async_driver.py *(renamed from circuit_breaker_async.py)*
- **Role:** Circuit breaker state persistence (async)

### killswitch_read_driver.py *(relocated from L5_controls/drivers/)*
- **Role:** Killswitch read DB operations

### limits_read_driver.py
- **Role:** Limits read DB operations

### override_driver.py
- **Role:** Override persistence

### policy_limits_driver.py
- **Role:** Policy limits DB operations

### scoped_execution_driver.py *(renamed from scoped_execution.py)*
- **Role:** Scoped execution context and risk assessment

### threshold_driver.py
- **Role:** Threshold state persistence and signal emission
- **Cross-domain:** ~~Imports activity domain (lazy)~~ REMOVED (PIN-507 Law 4 — signal emission moved to L4 `signal_coordinator.py`)
- **L6→L5:** ~~Imports ThresholdSignal from threshold_engine~~ FIXED (PIN-507 Law 1 — now imports from `controls/L5_schemas/threshold_signals.py`)

---

## adapters (2 files)

### __init__.py
- **Role:** Package init

### customer_killswitch_adapter.py
- **Role:** L2 boundary adapter for killswitch operations
- **Cross-domain:** Imports from general domain

---

## L4 Handler

**File:** `hoc/cus/hoc_spine/orchestrator/handlers/controls_handler.py`
**Operations:** 2

| Operation | Handler Class | Target |
|-----------|--------------|--------|
| controls.query | ControlsQueryHandler | ControlsFacade |
| controls.thresholds | ControlsThresholdHandler | ThresholdEngine |

No L4 handler import updates required — handler imports `controls_facade` and `threshold_engine` which were not renamed.

---

## Cleansing Cycle (2026-01-31) — PIN-503

### Cat A: Dead Import Repointed (1)

| File | Old Import | New Import |
|------|-----------|------------|
| `adapters/customer_killswitch_adapter.py` | `app.hoc.cus.general.L5_controls.engines.guard_write_engine.GuardWriteService` | `app.hoc.cus.hoc_spine.authority.guard_write_engine.GuardWriteService` |

`cus/general/` was abolished per PIN-485. `GuardWriteService` migrated to `hoc_spine/authority/`.

### Cat B: Legacy `app.services` Docstring References — Corrected (2)

| File | Old Docstring Reference | New Docstring Reference |
|------|------------------------|------------------------|
| `alert_fatigue_engine.py` | `from app.services.alert_fatigue import ...` | `from app.hoc.cus.controls.L5_engines.alert_fatigue_engine import ...` |
| `controls_facade.py` | `from app.services.controls.facade import ...` | `from app.hoc.cus.controls.L5_engines.controls_facade import ...` |

Not active imports — docstring Usage examples. Updated to HOC paths to eliminate false positives.

### Cat D: L2→L5 Bypass Violations (7 — DOCUMENT ONLY)

| L2 File | Line(s) | Import | Domains Reached |
|---------|---------|--------|-----------------|
| `policies/simulate.py` | 36 | `controls.L5_schemas.simulation` | controls L5_schemas |
| `policies/override.py` | 43 | `controls.L6_drivers.override_driver` | controls L6 |
| `recovery/recovery.py` | 893, 994, 1047, 1159, 1184 | `controls.L6_drivers.scoped_execution` | controls L6 |

**Deferred:** Requires Loop Model infrastructure (PIN-487 Part 2).

### Cat E: Cross-Domain L5→L5/L6 Violations (Inbound — 4)

Other domains importing from controls:

| Source File | Source Domain | Import Target |
|------------|--------------|--------------|
| `activity/L5_engines/__init__.py` | activity | `controls.L5_engines.threshold_engine` |
| `activity/L6_drivers/__init__.py` | activity | `controls.L6_drivers.threshold_driver` |
| `policies/L5_engines/policies_limits_query_engine.py` | policies | `controls.L6_drivers.limits_read_driver` |
| `policies/L5_engines/policy_limits_engine.py` | policies | `controls.L6_drivers.policy_limits_driver`, `controls.L5_schemas.policy_limits` |
| `policies/L6_drivers/__init__.py` | policies | `controls.L6_drivers.limits_read_driver` |

**Deferred:** Requires L4 Coordinator to mediate cross-domain reads.

### Tally

43/43 checks PASS (40 consolidation + 3 cleansing).

---

## PIN-507 Law 5 Remediation (2026-02-01)

**L4 Handler Update:** All `getattr()`-based reflection dispatch in this domain's L4 handler replaced with explicit `dispatch = {}` maps. All `asyncio.iscoroutinefunction()` eliminated via explicit sync/async split. Zero `__import__()` calls remain. See PIN-507 for full audit trail.

## PIN-507 Law 4 Remediation (2026-02-01)

`emit_and_persist_threshold_signal` deleted from `threshold_driver.py` — cross-domain orchestration (controls→activity) moved to L4 `signal_coordinator.py`. Activity domain import (`run_signal_driver`) removed from this L6 driver. `emit_threshold_signal_sync` retained (pure L6 single-domain DB write). CI guard added to `check_init_hygiene.py` to prevent future L6 cross-domain imports.

## PIN-508 Tombstone Cleanup (2026-02-01)

### Tombstone Re-exports Removed (Phase 4A)

| File | Symbols Removed | Reason |
|------|-----------------|--------|
| `L5_engines/threshold_engine.py` | `ThresholdSignal` (tombstone re-export), `ThresholdEvaluationResult` (tombstone re-export) | Canonical home moved to `controls/L5_schemas/threshold_signals.py` (PIN-507 Law 1). Tombstone re-exports deleted — L6 drivers now import directly from schemas layer. No external callers remain. |

**Verification:** Grep `threshold_engine` in all controls files — no active imports of tombstones remain. All `threshold_driver.py` imports changed to `threshold_signals.py` during PIN-507 remediation.

## PIN-510 Phase 1D — Killswitch Driver Import Fix (2026-02-01)

- `customer_killswitch_read_engine.py` import fixed from stale `policies.controls.drivers` path to canonical `controls.L6_drivers.killswitch_read_driver`
- `policies/L5_controls/drivers/__init__.py` re-export also fixed to canonical path
- Driver already resided at `controls/L6_drivers/killswitch_read_driver.py` — no file move needed
- Reference: `docs/memory-pins/PIN-510-domain-remediation-queue.md`

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`
