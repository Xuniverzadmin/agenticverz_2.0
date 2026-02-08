# Controls — Domain Capability

**Domain:** controls  
**Total functions:** 211  
**Generator:** `scripts/ops/hoc_capability_doc_generator.py`

---

## Reality Delta (2026-02-08)

- L5/L6 purity: `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --domain controls --json --advisory` reports 0 blocking, 0 advisory.
- Execution boundary (pairing): `PYTHONPATH=. python3 backend/scripts/ops/l5_spine_pairing_gap_detector.py --json` reports `total_l5_engines: 69`, `wired_via_l4: 69`, `direct_l2_to_l5: 0`, `orphaned: 0`.
- Strict T0 invariant: controls `L6_drivers/` contain no `hoc_spine` imports.

## 1. Domain Purpose

Customer-configurable controls, feature flags, and operational knobs. Provides governance levers without code changes.

## 2. Customer-Facing Operations

| Function | File | L4 Wired | Entry Point | Side Effects |
|----------|------|----------|-------------|--------------|
| `ControlConfig.to_dict` | controls_facade | Yes | L4:controls_handler | pure |
| `ControlStatusSummary.to_dict` | controls_facade | Yes | L4:controls_handler | pure |
| `ControlsFacade.disable_control` | controls_facade | Yes | L4:controls_handler | pure |
| `ControlsFacade.enable_control` | controls_facade | Yes | L4:controls_handler | pure |
| `ControlsFacade.get_control` | controls_facade | Yes | L4:controls_handler | pure |
| `ControlsFacade.get_status` | controls_facade | Yes | L4:controls_handler | pure |
| `ControlsFacade.list_controls` | controls_facade | Yes | L4:controls_handler | pure |
| `ControlsFacade.update_control` | controls_facade | Yes | L4:controls_handler | pure |
| `CreatePolicyLimitRequest.validate_reset_period` | policy_limits | No (gap) | L2:policy_limits_crud | pure |
| `CreatePolicyLimitRequest.validate_window_seconds` | policy_limits | No (gap) | L2:policy_limits_crud | pure |
| `LLMRunEvaluator.evaluate_completed_run` | threshold_engine | Yes | L4:controls_handler | pure |
| `LLMRunEvaluator.evaluate_live_run` | threshold_engine | Yes | L4:controls_handler | pure |
| `LLMRunEvaluatorSync.evaluate_completed_run` | threshold_engine | Yes | L4:controls_handler | pure |
| `LLMRunThresholdResolver.resolve` | threshold_engine | Yes | L4:controls_handler | pure |
| `LLMRunThresholdResolverSync.resolve` | threshold_engine | Yes | L4:controls_handler | pure |
| `LimitOverrideRequest.validate_override_value` | overrides | No (gap) | L2:override | pure |
| `OverrideApprovalRequest.validate_rejection_reason` | overrides | No (gap) | L2:override | pure |
| `ThresholdDriverProtocol.get_active_threshold_limits` | threshold_engine | Yes | L4:controls_handler | pure |
| `ThresholdDriverSyncProtocol.get_active_threshold_limits` | threshold_engine | Yes | L4:controls_handler | pure |
| `ThresholdParams.coerce_decimal_to_float` | threshold_engine | Yes | L4:controls_handler | pure |
| `collect_signals_from_evaluation` | threshold_engine | Yes | L4:controls_handler | pure |
| `create_threshold_signal_record` | threshold_engine | Yes | L4:controls_handler | pure |
| `get_controls_facade` | controls_facade | Yes | L4:controls_handler | pure |

## 3. Internal Functions

### Decisions

| Function | File | Confidence |
|----------|------|------------|
| `AlertFatigueController.check_alert` | alert_fatigue | medium |
| `AlertFatigueController.should_send_alert` | alert_fatigue | medium |
| `CostSafetyRails.can_auto_apply_policy` | cost_safety_rails | ambiguous |
| `CostSafetyRails.can_auto_apply_recovery` | cost_safety_rails | ambiguous |
| `CostSafetyRails.can_auto_apply_routing` | cost_safety_rails | ambiguous |
| `allow` | decisions | medium |
| `validate_s2_envelope` | s2_cost_smoothing | medium |

### Helpers

_64 internal helper functions._

- **alert_fatigue:** `AlertCheckResult.to_dict`, `AlertFatigueController.__init__`, `AlertFatigueController._check_deduplication`, `AlertFatigueController._check_domain_cooldown`, `AlertFatigueController._check_tenant_rate_limit`, `AlertFatigueController._cleanup_old_records`, `AlertFatigueController._get_tenant_settings`, `AlertRecord.__post_init__`
- **budget_enforcement_driver:** `BudgetEnforcementDriver.__init__`, `BudgetEnforcementDriver._get_engine`
- **budget_enforcement_engine:** `BudgetEnforcementEngine.__init__`, `BudgetEnforcementEngine._parse_budget_from_error`
- **cb_sync_wrapper:** `_get_executor`, `_run_async_in_thread`
- **circuit_breaker:** `CircuitBreaker.__init__`, `CircuitBreaker._auto_recover`, `CircuitBreaker._get_or_create_state`, `CircuitBreaker._post_alertmanager`, `CircuitBreaker._resolve_incident_db`, `CircuitBreaker._save_incident_file`, `CircuitBreaker._send_alert_disable`, `CircuitBreaker._send_alert_enable`, `CircuitBreaker._trip`
- **circuit_breaker_async:** `AsyncCircuitBreaker.__init__`, `_auto_recover`, `_build_disable_alert_payload`, `_build_enable_alert_payload`, `_enqueue_alert`, `_get_or_create_state`, `_resolve_incident`, `_trip`, `_try_auto_recover`
- **controls_facade:** `ControlsFacade.__init__`, `ControlsFacade._ensure_default_controls`
- **cost_safety_rails:** `CostSafetyRails.__init__`, `CostSafetyRails._get_action_count`, `SafeCostLoopOrchestrator.__init__`
- **customer_killswitch_read_engine:** `CustomerKillswitchReadService.__init__`
- **decisions:** `AnomalySignal.to_signal_response`, `ProtectionResult.to_error_response`
- **killswitch:** `KillSwitch.__init__`
- **killswitch_read_driver:** `KillswitchReadDriver.__init__`, `KillswitchReadDriver._get_active_guardrails`, `KillswitchReadDriver._get_incident_stats`, `KillswitchReadDriver._get_killswitch_state`, `KillswitchReadDriver._get_session`
- **limits_read_driver:** `LimitsReadDriver.__init__`
- **override_driver:** `LimitOverrideService.__init__`, `LimitOverrideService._get_limit`, `LimitOverrideService._to_response`
- **policy_limits_driver:** `PolicyLimitsDriver.__init__`
- **scoped_execution:** `ScopeStore.__new__`, `ScopedExecutionContext.__init__`, `ScopedExecutionContext._compute_hash`, `ScopedExecutionContext._dry_run_validate`, `ScopedExecutionContext._elapsed_ms`, `ScopedExecutionContext._estimate_cost`, `ScopedExecutionContext._execute_scoped`
- **threshold_driver:** `ThresholdDriver.__init__`, `ThresholdDriverSync.__init__`
- **threshold_engine:** `LLMRunEvaluator.__init__`, `LLMRunEvaluatorSync.__init__`, `LLMRunThresholdResolver.__init__`, `LLMRunThresholdResolverSync.__init__`

### Persistence

| Function | File | Side Effects |
|----------|------|--------------|
| `AsyncCircuitBreaker.disable_v2` | circuit_breaker_async | pure |
| `AsyncCircuitBreaker.enable_v2` | circuit_breaker_async | pure |
| `AsyncCircuitBreaker.get_incidents` | circuit_breaker_async | pure |
| `AsyncCircuitBreaker.get_state` | circuit_breaker_async | pure |
| `AsyncCircuitBreaker.is_closed` | circuit_breaker_async | file_io |
| `AsyncCircuitBreaker.is_disabled` | circuit_breaker_async | pure |
| `AsyncCircuitBreaker.is_open` | circuit_breaker_async | file_io |
| `AsyncCircuitBreaker.report_drift` | circuit_breaker_async | pure |
| `AsyncCircuitBreaker.report_schema_error` | circuit_breaker_async | pure |
| `AsyncCircuitBreaker.reset` | circuit_breaker_async | pure |
| `AsyncCircuitBreaker.reset_v2` | circuit_breaker_async | pure |
| `BoundExecutionScope.can_execute` | scoped_execution | pure |
| `BoundExecutionScope.consume` | scoped_execution | pure |
| `BoundExecutionScope.is_valid` | scoped_execution | pure |
| `BoundExecutionScope.to_dict` | scoped_execution | pure |
| `BudgetEnforcementDriver.dispose` | budget_enforcement_driver | pure |
| `BudgetEnforcementDriver.fetch_pending_budget_halts` | budget_enforcement_driver | pure |
| `CircuitBreaker.disable_v2` | circuit_breaker | pure |
| `CircuitBreaker.enable_v2` | circuit_breaker | pure |
| `CircuitBreaker.get_incidents` | circuit_breaker | pure |
| `CircuitBreaker.get_state` | circuit_breaker | pure |
| `CircuitBreaker.is_closed` | circuit_breaker | file_io |
| `CircuitBreaker.is_disabled` | circuit_breaker | pure |
| `CircuitBreaker.is_open` | circuit_breaker | file_io |
| `CircuitBreaker.report_drift` | circuit_breaker | pure |
| `CircuitBreaker.report_schema_error` | circuit_breaker | pure |
| `CircuitBreaker.reset` | circuit_breaker | pure |
| `CircuitBreakerState.to_dict` | circuit_breaker | pure |
| `CircuitBreakerState.to_dict` | circuit_breaker_async | pure |
| `Incident.to_dict` | circuit_breaker | pure |
| `Incident.to_dict` | circuit_breaker_async | pure |
| `LimitOverrideService.cancel_override` | override_driver | pure |
| `LimitOverrideService.get_override` | override_driver | pure |
| `LimitOverrideService.list_overrides` | override_driver | pure |
| `LimitOverrideService.request_override` | override_driver | pure |
| `LimitsReadDriver.fetch_budget_limits` | limits_read_driver | db_write |
| `LimitsReadDriver.fetch_limit_by_id` | limits_read_driver | db_write |
| `LimitsReadDriver.fetch_limits` | limits_read_driver | db_write |
| `PolicyLimitsDriver.add_integrity` | policy_limits_driver | db_write |
| `PolicyLimitsDriver.add_limit` | policy_limits_driver | db_write |
| `PolicyLimitsDriver.fetch_limit_by_id` | policy_limits_driver | db_write |
| `PolicyLimitsDriver.flush` | policy_limits_driver | db_write |
| `ScopeStore.cleanup_expired` | scoped_execution | pure |
| `ScopeStore.create_scope` | scoped_execution | pure |
| `ScopeStore.get_scope` | scoped_execution | pure |
| `ScopeStore.get_scopes_for_incident` | scoped_execution | pure |
| `ScopeStore.revoke_scope` | scoped_execution | pure |
| `ScopedExecutionContext.execute` | scoped_execution | pure |
| `ThresholdDriver.get_active_threshold_limits` | threshold_driver | db_write |
| `ThresholdDriver.get_threshold_limit_by_scope` | threshold_driver | db_write |
| `ThresholdDriverSync.get_active_threshold_limits` | threshold_driver | db_write |
| `create_circuit_breaker` | circuit_breaker | pure |
| `create_recovery_scope` | scoped_execution | pure |
| `disable_v2` | circuit_breaker | pure |
| `disable_v2` | circuit_breaker_async | pure |
| `emit_and_persist_threshold_signal` | threshold_driver | pure |
| `emit_threshold_signal_sync` | threshold_driver | pure |
| `enable_v2` | circuit_breaker | pure |
| `enable_v2` | circuit_breaker_async | pure |
| `execute_with_scope` | scoped_execution | pure |
| `get_async_circuit_breaker` | circuit_breaker_async | pure |
| `get_budget_enforcement_driver` | budget_enforcement_driver | pure |
| `get_incidents` | circuit_breaker_async | db_write |
| `get_limits_read_driver` | limits_read_driver | pure |
| `get_policy_limits_driver` | policy_limits_driver | pure |
| `get_scope_store` | scoped_execution | pure |
| `get_state` | circuit_breaker_async | pure |
| `is_v2_disabled` | circuit_breaker | pure |
| `is_v2_disabled` | circuit_breaker_async | db_write |
| `report_drift` | circuit_breaker_async | pure |
| `report_schema_error` | circuit_breaker_async | pure |
| `requires_scoped_execution` | scoped_execution | pure |
| `test_recovery_scope` | scoped_execution | pure |
| `validate_scope_required` | scoped_execution | pure |

### Unclassified (needs review)

_43 functions need manual classification._

- `AlertFatigueController.get_tenant_stats` (alert_fatigue)
- `AlertFatigueController.record_alert_sent` (alert_fatigue)
- `AlertFatigueController.set_tenant_settings` (alert_fatigue)
- `AlertRecord.age` (alert_fatigue)
- `BudgetEnforcementEngine.emit_decision_for_halt` (budget_enforcement_engine)
- `BudgetEnforcementEngine.process_pending_halts` (budget_enforcement_engine)
- `CostSafetyRails.get_status` (cost_safety_rails)
- `CostSafetyRails.record_action` (cost_safety_rails)
- `CustomerKillswitchReadService.get_killswitch_status` (customer_killswitch_read_engine)
- `Decision.blocks_request` (decisions)
- `Decision.is_warning_only` (decisions)
- `KillSwitch.activate` (killswitch)
- `KillSwitch.get_events` (killswitch)
- `KillSwitch.get_last_event` (killswitch)
- `KillSwitch.is_disabled` (killswitch)
- `KillSwitch.is_enabled` (killswitch)
- `KillSwitch.mark_rollback_complete` (killswitch)
- `KillSwitch.on_activate` (killswitch)
- `KillSwitch.rearm` (killswitch)
- `KillSwitch.state` (killswitch)
- _...and 23 more_

## 4. Explicit Non-Features

_No explicit non-feature declarations found in CONTROLS_DOMAIN_LOCK_FINAL.md._
