# PIN-499: Controls Domain Canonical Consolidation

**Status:** COMPLETE
**Date:** 2026-01-31
**Domain:** controls
**Scope:** 28 files (11 L5_engines, 4 L5_schemas, 10 L6_drivers, 2 adapters, 1 __init__.py)

---

## Actions Taken

### 1. Naming Violations Fixed (9 renames)

**L5 (6):**

| Old Name | New Name |
|----------|----------|
| alert_fatigue.py | alert_fatigue_engine.py |
| cb_sync_wrapper.py | cb_sync_wrapper_engine.py |
| cost_safety_rails.py | cost_safety_rails_engine.py |
| decisions.py | decisions_engine.py |
| killswitch.py | killswitch_engine.py |
| s2_cost_smoothing.py | s2_cost_smoothing_engine.py |

**L6 (3):**

| Old Name | New Name |
|----------|----------|
| circuit_breaker.py | circuit_breaker_driver.py |
| circuit_breaker_async.py | circuit_breaker_async_driver.py |
| scoped_execution.py | scoped_execution_driver.py |

### 2. Structural Fix: L5_controls/ Relocated (2 files)

| Old Path | New Path |
|----------|----------|
| L5_controls/engines/customer_killswitch_read_engine.py | L5_engines/customer_killswitch_read_engine.py |
| L5_controls/drivers/killswitch_read_driver.py | L6_drivers/killswitch_read_driver.py |

`L5_controls/` directory deleted after relocation.

### 3. Import Path Fix (1)

- `customer_killswitch_adapter.py`: `controls.L5_controls.engines.customer_killswitch_read_engine` → `controls.L5_engines.customer_killswitch_read_engine`

### 4. Header Issues — None

`controls/__init__.py` already L5. No correction needed.

### 5. Legacy Connections — None Active

Two `app.services` references exist in docstring Usage examples only:
- `alert_fatigue_engine.py` line 37 (docstring)
- `controls_facade.py` line 42 (docstring)

### 6. Cross-Domain Imports (Deferred to Rewiring)

| File | Target Domain | Type |
|------|--------------|------|
| customer_killswitch_read_engine.py | policies | L5→policies.controls.drivers |
| customer_killswitch_adapter.py | **general (ABOLISHED)** | adapter→general.L5_controls — **DEAD IMPORT: `cus/general/` was abolished per PIN-485. This import points to a non-existent directory. Must be repointed to `hoc_spine.*` during cleansing cycle.** |
| threshold_driver.py | activity | L6→activity.L6_drivers (lazy, function-scoped) |

### 7. L6→L5 Runtime Import (Documented)

`threshold_driver.py` line 287: imports `ThresholdSignal` from `L5_engines.threshold_engine` inside function body. Lazy/function-scoped, not circular at module level.

### 8. Layer Anomaly (Documented)

`budget_enforcement_engine.py` declares `# Layer: L4` but lives in L5_engines/. Intentional per PIN-257 (Phase R-3). Not modified.

---

## Artifacts

| Artifact | Path |
|----------|------|
| Literature | `literature/hoc_domain/controls/CONTROLS_CANONICAL_SOFTWARE_LITERATURE.md` |
| Tally Script | `scripts/ops/hoc_controls_tally.py` |
| PIN | This file |

## Tally Result

40/40 checks PASS.

## L4 Handler

`controls_handler.py` — 2 operations registered:

| Operation | Target |
|-----------|--------|
| controls.query | ControlsFacade |
| controls.thresholds | ThresholdEngine |

No import updates required — handler imports `controls_facade` and `threshold_engine` which were not renamed.
