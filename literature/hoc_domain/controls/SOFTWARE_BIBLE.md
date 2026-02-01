# Controls — Software Bible

**Domain:** controls  
**L2 Features:** 0  
**Scripts:** 21  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

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
| override_driver | L6 | `LimitOverrideService.request_override` | CANONICAL | 3 | L4:controls_handler (controls.overrides) | YES |
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
| `threshold_driver` | `LimitSnapshot` re-exported from `hoc_spine.schemas.threshold_types`. ~~`emit_and_persist_threshold_signal` delegates to `SignalCoordinator` (L4).~~ **Function deleted** (PIN-507 Law 4) — moved to L4 `signal_coordinator.py`. Cross-domain activity import removed. | PIN-504 Phases 1, 3; PIN-507 Law 4 |

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
