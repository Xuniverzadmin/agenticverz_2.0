# Controls — Software Bible

**Domain:** controls  
**L2 Features:** 0  
**Scripts:** 21  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Reality Delta (2026-02-16, L2.1 Facade Activation Wiring)

- Public facade activation path for controls is now explicitly wired at L2.1:
- backend/app/hoc/api/facades/cus/controls/controls_fac.py
- L2 public boundary module for domain-scoped facade entry is present at:
- backend/app/hoc/api/cus/controls/controls_public.py
- Runtime chain is fixed as:
- app.py -> app.hoc.api.facades.cus -> domain facade bundle -> controls_public.py -> L4 registry.execute(...)
- Current status: controls_public.py remains scaffold-only (no behavior change yet); existing domain routers stay active during incremental rollout.

## Reality Delta (2026-02-08)

- L5/L6 purity: `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --domain controls --json --advisory` reports 0 blocking, 0 advisory.
- Execution boundary (pairing): `PYTHONPATH=. python3 backend/scripts/ops/l5_spine_pairing_gap_detector.py --json` reports `total_l5_engines: 69`, `wired_via_l4: 69`, `direct_l2_to_l5: 0`, `orphaned: 0`.
- Strict T0 invariant: controls `L6_drivers/` contain no `hoc_spine` imports.

## Reality Delta (2026-02-11)

- Canonical UC alignment now includes `UC-004`, `UC-005`, `UC-014`, and `UC-015` as architecture `GREEN`.
- Controls evaluation evidence contract is now part of UC-MON storage/event verification (`control_set_version`, `override_ids_applied`, `resolver_version`, `decision`).
- Override lifecycle closure is now tracked in canonical usecase linkage and batch evidence docs.

## Reality Delta (2026-02-12)

- Controls participates in expanded closure via `UC-021` (policies limits query lifecycle) through `controls/L6_drivers/limits_read_driver.py`.
- Cross-domain usage for that flow remains orchestrated at L4 with no direct L2->L6 bypass.
- Architecture closure for `UC-021` is reflected in canonical usecase registry/linkage, while production readiness remains tracked separately.

## Reality Delta (2026-02-12, Wave-3 Script Coverage Audit)

- Wave-3 script coverage (`controls + account`) has been independently audited and reconciled.
- Controls target-scope classification is complete:
- `8` scripts marked `UC_LINKED`
- `15` scripts marked `NON_UC_SUPPORT`
- `0` target-scope residual scripts in Wave-3 controls target list.
- Deterministic gates remain clean post-wave and governance suite now runs `250` passing tests in `test_uc018_uc032_expansion.py`.
- Canonical audit artifacts:
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_3_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_3_AUDIT_2026-02-12.md`

## Script Registry

Each script's unique contribution and canonical function.

| Script | Layer | Canonical Function | Role | Decisions | Callers | Unique? |
|--------|-------|--------------------|------|-----------|---------|---------|
| alert_fatigue | L5 | `AlertFatigueController.check_alert` | CANONICAL | 5 | ?:alert_fatigue, circuit_breaker, scoped_execution | YES |
| budget_enforcement_engine | L5 | `BudgetEnforcementEngine.process_pending_halts` | CANONICAL | 7 | ?:main | YES |
| cb_sync_wrapper | L5 | `_get_executor` | LEAF | 1 | ?:__init__ | ?:circuit_breaker_async | ?:cb_sync_wrapper | L6:circuit_breaker_async | ?:test_integration_real_db, circuit_breaker_async | YES |
| controls_facade | L5 | `ControlsFacade.get_status` | CANONICAL | 5 | L4:controls_handler, circuit_breaker, cost_safety_rails +1 | YES |
| cost_safety_rails | L5 | `CostSafetyRails.can_auto_apply_policy` | CANONICAL | 5 | ?:test_m27_cost_loop | YES |
| customer_killswitch_read_engine | L5 | `CustomerKillswitchReadService.get_killswitch_status` | ENTRY | 0 | L3:customer_killswitch_adapter | **OVERLAP** |
| decisions | L5 | `ProtectionResult.to_error_response` | LEAF | 3 | ?:overview | ?:protection_gate | ?:protection_dependencies | ?:workers | ?:engine | ?:__init__ | ?:provider | ?:memory_service | ?:care | ?:budget_tracker | YES |
| killswitch | L5 | `KillSwitch.__init__` | LEAF | 0 | ?:manager | ?:__init__ | ?:incidents | ?:guard | ?:v1_proxy | ?:ops | ?:v1_killswitch | ?:replay | L3:customer_killswitch_adapter | ?:incident_write_engine, circuit_breaker | YES |
| killswitch_read_driver | L5 | `KillswitchReadDriver.get_killswitch_status` | CANONICAL | 1 | L5:__init__ | L5:customer_killswitch_read_engine, customer_killswitch_read_engine | **OVERLAP** |
| overrides | L5 | `LimitOverrideRequest.validate_override_value` | LEAF | 1 | ?:override | ?:__init__ | ?:override_service | L6:override_driver | L2:override | YES |
| policy_limits | L5 | `CreatePolicyLimitRequest.validate_reset_period` | WRAPPER | 0 | ?:policy_limits_crud | ?:__init__ | ?:policy_limits_service | L5:policy_limits_engine | L2:policy_limits_crud | ?:test_limit_enhancements | YES |
| s2_cost_smoothing | L5 | `calculate_s2_bounded_value` | LEAF | 0 | ?:__init__ | ?:test_c3_s3_failure_matrix | ?:test_c3_s2_cost_smoothing | YES |
| threshold_engine | L5 | `LLMRunThresholdResolver.resolve` | CANONICAL | 8 | ?:policy_limits_crud | ?:runner | L5:__init__ | L6:threshold_driver | L4:controls_handler | YES |
| budget_enforcement_driver | L6 | `BudgetEnforcementDriver._get_engine` | LEAF | 2 | L5:budget_enforcement_engine, budget_enforcement_engine | YES |
| circuit_breaker | L6 | `CircuitBreaker.reset` | CANONICAL | 2 | ?:__init__ | ?:canary | ?:circuit_breaker | L5:canary | ?:check_priority5_intent | ?:conftest | ?:test_circuit_breaker, cb_sync_wrapper, circuit_breaker_async +1 | YES |
| circuit_breaker_async | L6 | `is_v2_disabled` | CANONICAL | 9 | ?:__init__ | ?:circuit_breaker_async | ?:sandbox | ?:canary | ?:cb_sync_wrapper | L5:sandbox | L5:canary | L5:cb_sync_wrapper | ?:check_priority5_intent | ?:test_circuit_breaker_async, cb_sync_wrapper, circuit_breaker +1 | YES |
| limits_read_driver | L6 | `LimitsReadDriver.fetch_limits` | CANONICAL | 12 | L6:__init__ | L5:policies_limits_query_engine | YES |
| override_driver | L6 | `LimitOverrideService.request_override` | CANONICAL | 5 | L4:controls_handler (controls.overrides) | YES | DB-backed (PIN-512 Cat-C P0, was in-memory dict) |
| policy_limits_driver | L6 | `PolicyLimitsDriver.fetch_limit_by_id` | ENTRY | 0 | L5:policy_limits_engine, circuit_breaker, circuit_breaker_async | YES |
| scoped_execution | L6 | `execute_with_scope` | CANONICAL | 6 | ?:recovery | ?:scoped_execution | L2:recovery, budget_enforcement_driver, circuit_breaker +5 | YES |
| threshold_driver | L6 | `ThresholdDriver.get_threshold_limit_by_scope` | CANONICAL | 2 | ?:runner | L6:__init__ | L5:threshold_engine, threshold_engine | YES |

## Overlapping Scripts (same purpose, same layer)

These scripts may serve duplicate purposes within the domain.

- `customer_killswitch_read_engine` — canonical: `CustomerKillswitchReadService.get_killswitch_status` (ENTRY)
- `killswitch_read_driver` — canonical: `KillswitchReadDriver.get_killswitch_status` (CANONICAL)

## L2 Feature Chains

| Status | Count |
|--------|-------|
| COMPLETE (L2→L4→L5→L6) | 0 |
| GAP (L2→L5 direct) | 0 |

## Canonical Algorithm Inventory

| Function | File | Role | Decisions | Stmts | Persistence | Delegates To |
|----------|------|------|-----------|-------|-------------|--------------|
| `AlertFatigueController._check_domain_cooldown` | alert_fatigue | SUPERSET | 2 | 8 | no | alert_fatigue:TenantFatigueSettings.get_domain_cooldown |
| `AlertFatigueController.check_alert` | alert_fatigue | CANONICAL | 5 | 5 | no | alert_fatigue:AlertFatigueController._check_deduplication |  |
| `AlertFatigueController.record_alert_sent` | alert_fatigue | SUPERSET | 2 | 3 | no | alert_fatigue:AlertFatigueController._cleanup_old_records |
| `BoundExecutionScope.can_execute` | scoped_execution | SUPERSET | 3 | 4 | no | scoped_execution:BoundExecutionScope.is_valid |
| `BudgetEnforcementEngine.process_pending_halts` | budget_enforcement_engine | CANONICAL | 7 | 6 | no | budget_enforcement_driver:BudgetEnforcementDriver.dispose |  |
| `CircuitBreaker._auto_recover` | circuit_breaker | SUPERSET | 2 | 14 | no | circuit_breaker:CircuitBreaker._get_or_create_state | circui |
| `CircuitBreaker._get_or_create_state` | circuit_breaker | SUPERSET | 3 | 5 | yes | policy_limits_driver:PolicyLimitsDriver.flush |
| `CircuitBreaker._trip` | circuit_breaker | SUPERSET | 2 | 19 | yes | circuit_breaker:CircuitBreaker._get_or_create_state | circui |
| `CircuitBreaker.is_disabled` | circuit_breaker | SUPERSET | 5 | 5 | no | circuit_breaker:CircuitBreaker._auto_recover | circuit_break |
| `CircuitBreaker.report_drift` | circuit_breaker | SUPERSET | 3 | 5 | no | circuit_breaker:CircuitBreaker._get_or_create_state | circui |
| `CircuitBreaker.reset` | circuit_breaker | CANONICAL | 2 | 17 | no | circuit_breaker:CircuitBreaker._get_or_create_state | circui |
| `ControlsFacade.disable_control` | controls_facade | SUPERSET | 2 | 11 | no | controls_facade:ControlsFacade._ensure_default_controls |
| `ControlsFacade.enable_control` | controls_facade | SUPERSET | 2 | 11 | no | controls_facade:ControlsFacade._ensure_default_controls |
| `ControlsFacade.get_status` | controls_facade | CANONICAL | 5 | 10 | no | controls_facade:ControlsFacade._ensure_default_controls |
| `ControlsFacade.list_controls` | controls_facade | SUPERSET | 3 | 5 | no | controls_facade:ControlsFacade._ensure_default_controls |
| `ControlsFacade.update_control` | controls_facade | SUPERSET | 4 | 9 | no | controls_facade:ControlsFacade._ensure_default_controls |
| `CostSafetyRails.can_auto_apply_policy` | cost_safety_rails | CANONICAL | 5 | 7 | no | cost_safety_rails:CostSafetyRails._get_action_count |
| `CostSafetyRails.can_auto_apply_recovery` | cost_safety_rails | SUPERSET | 2 | 4 | no | cost_safety_rails:CostSafetyRails._get_action_count |
| `CostSafetyRails.can_auto_apply_routing` | cost_safety_rails | SUPERSET | 2 | 4 | no | cost_safety_rails:CostSafetyRails._get_action_count |
| `KillswitchReadDriver.get_killswitch_status` | killswitch_read_driver | CANONICAL | 1 | 6 | no | killswitch_read_driver:KillswitchReadDriver._get_active_guar |
| `LLMRunEvaluator.evaluate_completed_run` | threshold_engine | SUPERSET | 4 | 7 | no | threshold_engine:LLMRunThresholdResolver.resolve | threshold |
| `LLMRunEvaluator.evaluate_live_run` | threshold_engine | SUPERSET | 2 | 7 | no | threshold_engine:LLMRunThresholdResolver.resolve | threshold |
| `LLMRunEvaluatorSync.evaluate_completed_run` | threshold_engine | SUPERSET | 4 | 7 | no | threshold_engine:LLMRunThresholdResolver.resolve | threshold |
| `LLMRunThresholdResolver.resolve` | threshold_engine | CANONICAL | 8 | 5 | no | threshold_driver:ThresholdDriver.get_active_threshold_limits |
| `LLMRunThresholdResolverSync.resolve` | threshold_engine | SUPERSET | 8 | 2 | no | threshold_driver:ThresholdDriver.get_active_threshold_limits |
| `LimitOverrideService.cancel_override` | override_driver | SUPERSET | 2 | 5 | no | override_driver:LimitOverrideService._to_response |
| `LimitOverrideService.request_override` | override_driver | CANONICAL | 3 | 13 | no | override_driver:LimitOverrideService._get_limit | override_d |
| `LimitsReadDriver.fetch_limits` | limits_read_driver | CANONICAL | 12 | 20 | yes | scoped_execution:ScopedExecutionContext.execute |
| `SafeCostLoopOrchestrator.process_anomaly_safe` | cost_safety_rails | SUPERSET | 5 | 6 | no | controls_facade:ControlsFacade.get_status | cost_safety_rail |
| `ScopedExecutionContext._dry_run_validate` | scoped_execution | SUPERSET | 3 | 5 | no | scoped_execution:ScopedExecutionContext._compute_hash | scop |
| `ThresholdDriver.get_threshold_limit_by_scope` | threshold_driver | CANONICAL | 2 | 6 | yes | scoped_execution:ScopedExecutionContext.execute |
| `_auto_recover` | circuit_breaker_async | SUPERSET | 2 | 12 | no | circuit_breaker_async:_build_enable_alert_payload | circuit_ |
| `_get_or_create_state` | circuit_breaker_async | SUPERSET | 2 | 6 | yes | policy_limits_driver:PolicyLimitsDriver.flush | scoped_execu |
| `_try_auto_recover` | circuit_breaker_async | SUPERSET | 6 | 3 | yes | circuit_breaker_async:_build_enable_alert_payload | circuit_ |
| `enable_v2` | circuit_breaker_async | SUPERSET | 2 | 1 | no | circuit_breaker:CircuitBreaker._get_or_create_state | circui |
| `execute_with_scope` | scoped_execution | CANONICAL | 6 | 9 | no | scoped_execution:BoundExecutionScope.can_execute | scoped_ex |
| `is_v2_disabled` | circuit_breaker_async | CANONICAL | 9 | 3 | yes | circuit_breaker_async:_try_auto_recover | scoped_execution:S |
| `report_drift` | circuit_breaker_async | SUPERSET | 3 | 3 | no | circuit_breaker:CircuitBreaker._get_or_create_state | circui |

## Wrapper Inventory

_77 thin delegation functions._

- `alert_fatigue.AlertCheckResult.to_dict` → ?
- `alert_fatigue.AlertFatigueController.set_tenant_settings` → ?
- `alert_fatigue.AlertFatigueController.should_send_alert` → alert_fatigue:AlertFatigueController.check_alert
- `alert_fatigue.AlertRecord.age` → ?
- `decisions.AnomalySignal.to_signal_response` → ?
- `circuit_breaker_async.AsyncCircuitBreaker.disable_v2` → circuit_breaker:CircuitBreaker.disable_v2
- `circuit_breaker_async.AsyncCircuitBreaker.enable_v2` → circuit_breaker:CircuitBreaker.enable_v2
- `circuit_breaker_async.AsyncCircuitBreaker.get_state` → circuit_breaker:CircuitBreaker.get_state
- `circuit_breaker_async.AsyncCircuitBreaker.is_closed` → circuit_breaker:CircuitBreaker.is_open
- `circuit_breaker_async.AsyncCircuitBreaker.is_disabled` → circuit_breaker:is_v2_disabled
- `circuit_breaker_async.AsyncCircuitBreaker.is_open` → cb_sync_wrapper:is_v2_disabled_sync
- `circuit_breaker_async.AsyncCircuitBreaker.report_drift` → circuit_breaker:CircuitBreaker.report_drift
- `circuit_breaker_async.AsyncCircuitBreaker.report_schema_error` → circuit_breaker:CircuitBreaker.report_schema_error
- `circuit_breaker_async.AsyncCircuitBreaker.reset` → circuit_breaker:CircuitBreaker.enable_v2
- `circuit_breaker_async.AsyncCircuitBreaker.reset_v2` → circuit_breaker:CircuitBreaker.reset
- `budget_enforcement_driver.BudgetEnforcementDriver.__init__` → ?
- `budget_enforcement_engine.BudgetEnforcementEngine.__init__` → ?
- `circuit_breaker.CircuitBreaker.enable_v2` → circuit_breaker:CircuitBreaker.reset
- `circuit_breaker.CircuitBreaker.get_state` → circuit_breaker:CircuitBreaker._get_or_create_state
- `circuit_breaker.CircuitBreaker.is_closed` → circuit_breaker:CircuitBreaker.is_open
- `circuit_breaker.CircuitBreaker.is_open` → circuit_breaker:CircuitBreaker._get_or_create_state
- `controls_facade.ControlConfig.to_dict` → ?
- `controls_facade.ControlStatusSummary.to_dict` → ?
- `controls_facade.ControlsFacade.__init__` → ?
- `policy_limits.CreatePolicyLimitRequest.validate_reset_period` → ?
- `policy_limits.CreatePolicyLimitRequest.validate_window_seconds` → ?
- `customer_killswitch_read_engine.CustomerKillswitchReadService.__init__` → killswitch_read_driver:get_killswitch_read_driver
- `decisions.Decision.blocks_request` → ?
- `decisions.Decision.is_warning_only` → ?
- `killswitch.KillSwitch.get_events` → ?
- _...and 47 more_

---

## PIN-504 Amendments (2026-01-31)

| Script | Change | Reference |
|--------|--------|-----------|
| `threshold_driver` | `LimitSnapshot` re-exported from `hoc.cus.hoc_spine.schemas.threshold_types`. ~~`emit_and_persist_threshold_signal` delegates to `SignalCoordinator` (L4).~~ **Function deleted** (PIN-507 Law 4) — moved to L4 `signal_coordinator.py`. Cross-domain activity import removed. | PIN-504 Phases 1, 3; PIN-507 Law 4 |

## PIN-507 Law 5 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| L4 `controls_handler.py` | `ControlsQueryHandler`: Replaced `getattr()` dispatch with explicit map (6 methods). `ControlsOverrideHandler`: Replaced `getattr()` dispatch with explicit map (4 methods). Zero reflection in dispatch paths. | PIN-507 Law 5 |

## PIN-507 Law 4 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| `threshold_driver` | `emit_and_persist_threshold_signal` deleted — cross-domain orchestration moved to L4 `signal_coordinator.py`. Activity domain import removed. | PIN-507 Law 4 |

## PIN-507 Law 1 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| `threshold_engine` | `ThresholdSignal` + `ThresholdEvaluationResult` extracted to `controls/L5_schemas/threshold_signals.py`. Tombstone re-exports retained for backward compat. Unused `Enum` import removed. | PIN-507 Law 1 |
| `threshold_driver` | `ThresholdSignal` import changed from `L5_engines.threshold_engine` (lazy) → `L5_schemas.threshold_signals` (module-level). L6→L5 engine reach eliminated. | PIN-507 Law 1 |
| **NEW** `L5_schemas/threshold_signals.py` | Created: `ThresholdSignal(str, Enum)`, `ThresholdEvaluationResult(dataclass)`. Canonical home for threshold signal types. | PIN-507 Law 1 |

## PIN-508 Tombstone Cleanup (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| `threshold_engine` | Tombstone re-exports of `ThresholdSignal` and `ThresholdEvaluationResult` **DELETED** (Phase 4A). Canonical home in `controls/L5_schemas/threshold_signals.py` — no callers imported via tombstone. | PIN-508 Phase 4A |

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

## PIN-513 Topology Completion & Hygiene (2026-02-01)

### Phase 1B — Stale L3_adapters Docstring Fix

| File | Change | Reference |
|------|--------|-----------|
| `controls/__init__.py:15` | Layer structure docstring fixed: `L3_adapters/` → `adapters/` (L3 abolished per PIN-485) | PIN-513 Phase 1B |

### PIN-513 Phase A & C — Controls Domain Changes (2026-02-01)

**Phase A: Dead Code Marking**

- `alert_fatigue_engine.py`: MARKED_FOR_DELETION — superseded by `hoc_spine/services/fatigue_controller.py`
- `decisions_engine.py`: MARKED_FOR_DELETION — duplicate of `app/protection/decisions.py`

**Phase C: Costsim Cutover (Import Rewiring)**

| Script | Change | Reference |
|--------|--------|-----------|
| `circuit_breaker_driver` (L6) | Rewired 1 import: `config` → `config_engine` | PIN-513 Phase C |
| `circuit_breaker_async_driver` (L6) | Rewired 3 imports: `config` → `config_engine`, `metrics` → `metrics_engine`, `cb_sync_wrapper` → `cb_sync_wrapper_engine` | PIN-513 Phase C |
| `cb_sync_wrapper_engine` (L5) | Rewired 2 imports: `circuit_breaker_async` → `circuit_breaker_async_driver` (×2 inline) | PIN-513 Phase C |

### PIN-513 TRANSITIONAL Resolution — get_circuit_breaker alias (2026-02-01)

Added `get_circuit_breaker = get_async_circuit_breaker` alias to `circuit_breaker_async_driver.py` — drop-in replacement for legacy `app.costsim.circuit_breaker.get_circuit_breaker()`. Enables 3 callers (api/costsim ×2, canary_engine) to sever their TRANSITIONAL `app.costsim` imports.

### PIN-513 Phase 8 — Zero-Caller Wiring (2026-02-01)

| Component | L4 Owner | Action |
|-----------|----------|--------|
| `scoped_execution_driver` (L6) | **NEW** `hoc_spine/orchestrator/coordinators/execution_coordinator.py` | L4 coordinator: `create_scope()` and `execute_with_scope()` delegate to `create_recovery_scope()` and `execute_with_scope()` from scoped_execution_driver |

**Signature audit fix:** `execution_coordinator.py` — changed `allowed_actions: List[str]` → `action: str`; `action_id` → `action`; `params` → `parameters`. All call sites verified.

---

### PIN-513 Phase 9 Batch 2A Amendment (2026-02-01)

**Scope:** 33 controls symbols reclassified.

| Category | Count | Details |
|----------|-------|---------|
| PHANTOM_NO_HOC_COPY | 13 | cost_safety_rails_engine (4), killswitch_engine (4), s2_cost_smoothing_engine (5) — files exist only in legacy |
| TOPOLOGY_DEAD | 7 | alert_fatigue_engine (4), decisions_engine (3) — superseded by canonical locations |
| WIRED (new) | 11 | circuit_breaker_handler.py owns cb_sync (3), cb_async (8) symbols |
| Already wired | 2 | scoped_execution_driver (Phase 8) |

**Files created:**
- `hoc_spine/orchestrator/handlers/circuit_breaker_handler.py` — L4 single authority for all circuit breaker ops (15 symbols: async 8, sync 4, session-bound 3+1)

**Files tombstoned:**
- `controls/L5_engines/alert_fatigue_engine.py` — TOPOLOGY_DEAD (canonical: app/protection/alert_fatigue.py)
- `controls/L5_engines/decisions_engine.py` — TOPOLOGY_DEAD (canonical: app/protection/decisions.py)

---

### PIN-513 Phase 9 Batch 4 Amendment (2026-02-01)

**Deletions:**
- `controls/L5_engines/alert_fatigue_engine.py` — DELETED (was TOPOLOGY_DEAD, canonical: hoc_spine/services/fatigue_controller.py)
- `controls/L5_engines/decisions_engine.py` — DELETED (was TOPOLOGY_DEAD, canonical: app/protection/decisions.py)
- `controls/L5_engines/customer_killswitch_read_engine.py` — DELETED (zero-logic passthrough, zero callers)
- `controls/adapters/customer_killswitch_adapter.py` — DELETED (zero callers, HOC copy unused)

**Final status:** Zero UNWIRED controls symbols remain. Zero TOPOLOGY_DEAD files remain.

### PIN-513 Phase 9 Batch 5 Amendment (2026-02-01)

**CI invariant hardening — controls domain impact:**

- `circuit_breaker_async_driver.py` and `circuit_breaker_driver.py` already caught by existing check 5 (L6→L5 engine ban) — no new allowlist entry needed
- Check 29 extends L6→L5 enforcement to `int/` and `fdr/` driver trees (controls is `cus/`, already covered by check 5)

**Total CI checks enforcing controls invariants:** checks 4, 5, 27, 29 (30 total system-wide).

---

## PIN-519 System Run Introspection (2026-02-03)

### Modified Files

| File | Change | Reference |
|------|--------|-----------|
| `limits_read_driver.py` | Added `fetch_limit_breaches_for_run(tenant_id, run_id)` method | PIN-519 |

### New Capabilities Exposed via ControlsBridge

| Capability | L6 Driver | Purpose |
|------------|-----------|---------|
| `limit_breaches_capability()` | `limits_read_driver.LimitsReadDriver` | Run-scoped limit breach queries |

### Canonical Algorithm Addition

| Function | File | Role | Reference |
|----------|------|------|-----------|
| `LimitsReadDriver.fetch_limit_breaches_for_run` | limits_read_driver | CANONICAL | PIN-519 |
