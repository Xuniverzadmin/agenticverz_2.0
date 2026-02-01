# Controls — Call Graph

**Domain:** controls  
**Total functions:** 211  
**Generator:** `scripts/ops/hoc_call_chain_tracer.py`

---

## Role Summary

| Role | Count | Description |
|------|-------|-------------|
| CANONICAL | 12 | Owns the algorithm — most decisions, primary logic |
| SUPERSET | 26 | Calls other functions + adds its own decisions |
| WRAPPER | 77 | Thin delegation — ≤3 stmts, no branching |
| LEAF | 62 | Terminal — calls no other domain functions |
| ENTRY | 14 | Entry point — no domain-internal callers |
| INTERNAL | 20 | Called only by other domain functions |

## Canonical Algorithm Owners

### `alert_fatigue.AlertFatigueController.check_alert`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 5
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** alert_fatigue.AlertFatigueController.check_alert → alert_fatigue.AlertFatigueController._check_deduplication → alert_fatigue.AlertFatigueController._check_domain_cooldown → alert_fatigue.AlertFatigueController._check_tenant_rate_limit → ...+1
- **Calls:** alert_fatigue:AlertFatigueController._check_deduplication, alert_fatigue:AlertFatigueController._check_domain_cooldown, alert_fatigue:AlertFatigueController._check_tenant_rate_limit, alert_fatigue:AlertFatigueController._get_tenant_settings

### `budget_enforcement_engine.BudgetEnforcementEngine.process_pending_halts`
- **Layer:** L5
- **Decisions:** 7
- **Statements:** 6
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** budget_enforcement_engine.BudgetEnforcementEngine.process_pending_halts → budget_enforcement_driver.BudgetEnforcementDriver.dispose → budget_enforcement_driver.BudgetEnforcementDriver.fetch_pending_budget_halts → budget_enforcement_driver.get_budget_enforcement_driver → ...+2
- **Calls:** budget_enforcement_driver:BudgetEnforcementDriver.dispose, budget_enforcement_driver:BudgetEnforcementDriver.fetch_pending_budget_halts, budget_enforcement_driver:get_budget_enforcement_driver, budget_enforcement_engine:BudgetEnforcementEngine._parse_budget_from_error, budget_enforcement_engine:BudgetEnforcementEngine.emit_decision_for_halt

### `circuit_breaker.CircuitBreaker.reset`
- **Layer:** L6
- **Decisions:** 2
- **Statements:** 17
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** circuit_breaker.CircuitBreaker.reset → circuit_breaker.CircuitBreaker._get_or_create_state → circuit_breaker.CircuitBreaker._resolve_incident_db → circuit_breaker.CircuitBreaker._send_alert_enable → ...+1
- **Calls:** circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker:CircuitBreaker._resolve_incident_db, circuit_breaker:CircuitBreaker._send_alert_enable, circuit_breaker_async:_get_or_create_state

### `circuit_breaker_async.is_v2_disabled`
- **Layer:** L6
- **Decisions:** 9
- **Statements:** 3
- **Delegation depth:** 3
- **Persistence:** yes
- **Chain:** circuit_breaker_async.is_v2_disabled → circuit_breaker_async._try_auto_recover → scoped_execution.ScopedExecutionContext.execute
- **Calls:** circuit_breaker_async:_try_auto_recover, scoped_execution:ScopedExecutionContext.execute

### `controls_facade.ControlsFacade.get_status`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 10
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** controls_facade.ControlsFacade.get_status → controls_facade.ControlsFacade._ensure_default_controls
- **Calls:** controls_facade:ControlsFacade._ensure_default_controls

### `cost_safety_rails.CostSafetyRails.can_auto_apply_policy`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 7
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** cost_safety_rails.CostSafetyRails.can_auto_apply_policy → cost_safety_rails.CostSafetyRails._get_action_count
- **Calls:** cost_safety_rails:CostSafetyRails._get_action_count

### `killswitch_read_driver.KillswitchReadDriver.get_killswitch_status`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 6
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** killswitch_read_driver.KillswitchReadDriver.get_killswitch_status → killswitch_read_driver.KillswitchReadDriver._get_active_guardrails → killswitch_read_driver.KillswitchReadDriver._get_incident_stats → killswitch_read_driver.KillswitchReadDriver._get_killswitch_state → ...+1
- **Calls:** killswitch_read_driver:KillswitchReadDriver._get_active_guardrails, killswitch_read_driver:KillswitchReadDriver._get_incident_stats, killswitch_read_driver:KillswitchReadDriver._get_killswitch_state, killswitch_read_driver:KillswitchReadDriver._get_session

### `limits_read_driver.LimitsReadDriver.fetch_limits`
- **Layer:** L6
- **Decisions:** 12
- **Statements:** 20
- **Delegation depth:** 3
- **Persistence:** yes
- **Chain:** limits_read_driver.LimitsReadDriver.fetch_limits → scoped_execution.ScopedExecutionContext.execute
- **Calls:** scoped_execution:ScopedExecutionContext.execute

### `override_driver.LimitOverrideService.request_override`
- **Layer:** L6
- **Decisions:** 3
- **Statements:** 13
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** override_driver.LimitOverrideService.request_override → override_driver.LimitOverrideService._get_limit → override_driver.LimitOverrideService._to_response
- **Calls:** override_driver:LimitOverrideService._get_limit, override_driver:LimitOverrideService._to_response

### `scoped_execution.execute_with_scope`
- **Layer:** L6
- **Decisions:** 6
- **Statements:** 9
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** scoped_execution.execute_with_scope → scoped_execution.BoundExecutionScope.can_execute → scoped_execution.BoundExecutionScope.consume → scoped_execution.ScopeStore.get_scope → ...+1
- **Calls:** scoped_execution:BoundExecutionScope.can_execute, scoped_execution:BoundExecutionScope.consume, scoped_execution:ScopeStore.get_scope, scoped_execution:get_scope_store

### `threshold_driver.ThresholdDriver.get_threshold_limit_by_scope`
- **Layer:** L6
- **Decisions:** 2
- **Statements:** 6
- **Delegation depth:** 3
- **Persistence:** yes
- **Chain:** threshold_driver.ThresholdDriver.get_threshold_limit_by_scope → scoped_execution.ScopedExecutionContext.execute
- **Calls:** scoped_execution:ScopedExecutionContext.execute

### `threshold_engine.LLMRunThresholdResolver.resolve`
- **Layer:** L5
- **Decisions:** 8
- **Statements:** 5
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** threshold_engine.LLMRunThresholdResolver.resolve → threshold_driver.ThresholdDriver.get_active_threshold_limits → threshold_driver.ThresholdDriverSync.get_active_threshold_limits → threshold_engine.ThresholdDriverProtocol.get_active_threshold_limits → ...+1
- **Calls:** threshold_driver:ThresholdDriver.get_active_threshold_limits, threshold_driver:ThresholdDriverSync.get_active_threshold_limits, threshold_engine:ThresholdDriverProtocol.get_active_threshold_limits, threshold_engine:ThresholdDriverSyncProtocol.get_active_threshold_limits

## Supersets (orchestrating functions)

### `alert_fatigue.AlertFatigueController._check_domain_cooldown`
- **Decisions:** 2, **Statements:** 8
- **Subsumes:** alert_fatigue:TenantFatigueSettings.get_domain_cooldown

### `alert_fatigue.AlertFatigueController.record_alert_sent`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** alert_fatigue:AlertFatigueController._cleanup_old_records

### `circuit_breaker.CircuitBreaker._auto_recover`
- **Decisions:** 2, **Statements:** 14
- **Subsumes:** circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker:CircuitBreaker._resolve_incident_db, circuit_breaker:CircuitBreaker._send_alert_enable, circuit_breaker_async:_get_or_create_state

### `circuit_breaker.CircuitBreaker._get_or_create_state`
- **Decisions:** 3, **Statements:** 5
- **Subsumes:** policy_limits_driver:PolicyLimitsDriver.flush

### `circuit_breaker.CircuitBreaker._trip`
- **Decisions:** 2, **Statements:** 19
- **Subsumes:** circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker:CircuitBreaker._save_incident_file, circuit_breaker:CircuitBreaker._send_alert_disable, circuit_breaker_async:_get_or_create_state

### `circuit_breaker.CircuitBreaker.is_disabled`
- **Decisions:** 5, **Statements:** 5
- **Subsumes:** circuit_breaker:CircuitBreaker._auto_recover, circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker_async:_auto_recover, circuit_breaker_async:_get_or_create_state

### `circuit_breaker.CircuitBreaker.report_drift`
- **Decisions:** 3, **Statements:** 5
- **Subsumes:** circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker:CircuitBreaker._trip, circuit_breaker_async:_get_or_create_state, circuit_breaker_async:_trip

### `circuit_breaker_async._auto_recover`
- **Decisions:** 2, **Statements:** 12
- **Subsumes:** circuit_breaker_async:_build_enable_alert_payload, circuit_breaker_async:_enqueue_alert, circuit_breaker_async:_resolve_incident

### `circuit_breaker_async._get_or_create_state`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** policy_limits_driver:PolicyLimitsDriver.flush, scoped_execution:ScopedExecutionContext.execute

### `circuit_breaker_async._try_auto_recover`
- **Decisions:** 6, **Statements:** 3
- **Subsumes:** circuit_breaker_async:_build_enable_alert_payload, circuit_breaker_async:_enqueue_alert, circuit_breaker_async:_resolve_incident, policy_limits_driver:PolicyLimitsDriver.flush, scoped_execution:ScopedExecutionContext.execute

### `circuit_breaker_async.enable_v2`
- **Decisions:** 2, **Statements:** 1
- **Subsumes:** circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker_async:_build_enable_alert_payload, circuit_breaker_async:_enqueue_alert, circuit_breaker_async:_get_or_create_state, circuit_breaker_async:_resolve_incident

### `circuit_breaker_async.report_drift`
- **Decisions:** 3, **Statements:** 3
- **Subsumes:** circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker:CircuitBreaker._trip, circuit_breaker_async:_get_or_create_state, circuit_breaker_async:_trip

### `controls_facade.ControlsFacade.disable_control`
- **Decisions:** 2, **Statements:** 11
- **Subsumes:** controls_facade:ControlsFacade._ensure_default_controls

### `controls_facade.ControlsFacade.enable_control`
- **Decisions:** 2, **Statements:** 11
- **Subsumes:** controls_facade:ControlsFacade._ensure_default_controls

### `controls_facade.ControlsFacade.list_controls`
- **Decisions:** 3, **Statements:** 5
- **Subsumes:** controls_facade:ControlsFacade._ensure_default_controls

### `controls_facade.ControlsFacade.update_control`
- **Decisions:** 4, **Statements:** 9
- **Subsumes:** controls_facade:ControlsFacade._ensure_default_controls

### `cost_safety_rails.CostSafetyRails.can_auto_apply_recovery`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** cost_safety_rails:CostSafetyRails._get_action_count

### `cost_safety_rails.CostSafetyRails.can_auto_apply_routing`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** cost_safety_rails:CostSafetyRails._get_action_count

### `cost_safety_rails.SafeCostLoopOrchestrator.process_anomaly_safe`
- **Decisions:** 5, **Statements:** 6
- **Subsumes:** controls_facade:ControlsFacade.get_status, cost_safety_rails:CostSafetyRails.can_auto_apply_policy, cost_safety_rails:CostSafetyRails.can_auto_apply_routing, cost_safety_rails:CostSafetyRails.get_status

### `override_driver.LimitOverrideService.cancel_override`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** override_driver:LimitOverrideService._to_response

### `scoped_execution.BoundExecutionScope.can_execute`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** scoped_execution:BoundExecutionScope.is_valid

### `scoped_execution.ScopedExecutionContext._dry_run_validate`
- **Decisions:** 3, **Statements:** 5
- **Subsumes:** scoped_execution:ScopedExecutionContext._compute_hash, scoped_execution:ScopedExecutionContext._elapsed_ms, scoped_execution:ScopedExecutionContext._estimate_cost

### `threshold_engine.LLMRunEvaluator.evaluate_completed_run`
- **Decisions:** 4, **Statements:** 7
- **Subsumes:** threshold_engine:LLMRunThresholdResolver.resolve, threshold_engine:LLMRunThresholdResolverSync.resolve

### `threshold_engine.LLMRunEvaluator.evaluate_live_run`
- **Decisions:** 2, **Statements:** 7
- **Subsumes:** threshold_engine:LLMRunThresholdResolver.resolve, threshold_engine:LLMRunThresholdResolverSync.resolve

### `threshold_engine.LLMRunEvaluatorSync.evaluate_completed_run`
- **Decisions:** 4, **Statements:** 7
- **Subsumes:** threshold_engine:LLMRunThresholdResolver.resolve, threshold_engine:LLMRunThresholdResolverSync.resolve

### `threshold_engine.LLMRunThresholdResolverSync.resolve`
- **Decisions:** 8, **Statements:** 2
- **Subsumes:** threshold_driver:ThresholdDriver.get_active_threshold_limits, threshold_driver:ThresholdDriverSync.get_active_threshold_limits, threshold_engine:ThresholdDriverProtocol.get_active_threshold_limits, threshold_engine:ThresholdDriverSyncProtocol.get_active_threshold_limits

## Wrappers (thin delegation)

- `alert_fatigue.AlertCheckResult.to_dict` → ?
- `alert_fatigue.AlertFatigueController.set_tenant_settings` → ?
- `alert_fatigue.AlertFatigueController.should_send_alert` → alert_fatigue:AlertFatigueController.check_alert
- `alert_fatigue.AlertRecord.age` → ?
- `alert_fatigue.reset_alert_fatigue_controller` → ?
- `budget_enforcement_driver.BudgetEnforcementDriver.__init__` → ?
- `budget_enforcement_driver.get_budget_enforcement_driver` → ?
- `budget_enforcement_engine.BudgetEnforcementEngine.__init__` → ?
- `budget_enforcement_engine.emit_budget_halt_decision` → budget_enforcement_engine:BudgetEnforcementEngine.emit_decision_for_halt
- `budget_enforcement_engine.process_pending_budget_decisions` → budget_enforcement_engine:BudgetEnforcementEngine.process_pending_halts
- `circuit_breaker.CircuitBreaker.enable_v2` → circuit_breaker:CircuitBreaker.reset
- `circuit_breaker.CircuitBreaker.get_state` → circuit_breaker:CircuitBreaker._get_or_create_state
- `circuit_breaker.CircuitBreaker.is_closed` → circuit_breaker:CircuitBreaker.is_open
- `circuit_breaker.CircuitBreaker.is_open` → circuit_breaker:CircuitBreaker._get_or_create_state
- `circuit_breaker.create_circuit_breaker` → ?
- `circuit_breaker.disable_v2` → circuit_breaker:CircuitBreaker.disable_v2
- `circuit_breaker.enable_v2` → circuit_breaker:CircuitBreaker.enable_v2
- `circuit_breaker.is_v2_disabled` → circuit_breaker:CircuitBreaker.is_disabled
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
- `controls_facade.ControlConfig.to_dict` → ?
- `controls_facade.ControlStatusSummary.to_dict` → ?
- `controls_facade.ControlsFacade.__init__` → ?
- `cost_safety_rails.SafetyConfig.production` → ?
- `cost_safety_rails.SafetyConfig.testing` → ?
- `customer_killswitch_read_engine.CustomerKillswitchReadService.__init__` → killswitch_read_driver:get_killswitch_read_driver
- `decisions.AnomalySignal.to_signal_response` → ?
- `decisions.Decision.blocks_request` → ?
- `decisions.Decision.is_warning_only` → ?
- `decisions.allow` → ?
- `decisions.reject_cost_limit` → ?
- `decisions.reject_rate_limit` → ?
- `decisions.throttle` → ?
- `decisions.warn` → ?
- `killswitch.KillSwitch.get_events` → ?
- `killswitch.KillSwitch.get_last_event` → ?
- `killswitch.KillSwitch.is_disabled` → ?
- `killswitch.KillSwitch.is_enabled` → ?
- `killswitch.KillSwitch.on_activate` → ?
- `killswitch.KillSwitch.rearm` → ?
- `killswitch.KillSwitch.state` → ?
- `killswitch.get_killswitch` → ?
- `killswitch.reset_killswitch_for_testing` → ?
- `killswitch_read_driver.KillswitchReadDriver.__init__` → ?
- `killswitch_read_driver.get_killswitch_read_driver` → ?
- `limits_read_driver.LimitsReadDriver.__init__` → ?
- `limits_read_driver.get_limits_read_driver` → ?
- `override_driver.LimitOverrideService.__init__` → ?
- `overrides.OverrideApprovalRequest.validate_rejection_reason` → ?
- `policy_limits.CreatePolicyLimitRequest.validate_reset_period` → ?
- `policy_limits.CreatePolicyLimitRequest.validate_window_seconds` → ?
- `policy_limits_driver.PolicyLimitsDriver.__init__` → ?
- `policy_limits_driver.PolicyLimitsDriver.add_integrity` → ?
- `policy_limits_driver.PolicyLimitsDriver.add_limit` → ?
- `policy_limits_driver.PolicyLimitsDriver.flush` → ?
- `policy_limits_driver.get_policy_limits_driver` → ?
- `scoped_execution.ScopeStore.get_scope` → ?
- `scoped_execution.ScopeStore.get_scopes_for_incident` → ?
- `scoped_execution.ScopedExecutionContext._estimate_cost` → ?
- `scoped_execution.get_scope_store` → ?
- `scoped_execution.validate_scope_required` → ?
- `threshold_driver.ThresholdDriver.__init__` → ?
- `threshold_driver.ThresholdDriverSync.__init__` → ?
- `threshold_engine.LLMRunEvaluator.__init__` → ?
- `threshold_engine.LLMRunEvaluatorSync.__init__` → ?
- `threshold_engine.LLMRunThresholdResolver.__init__` → ?
- `threshold_engine.LLMRunThresholdResolverSync.__init__` → ?
- `threshold_engine.ThresholdDriverProtocol.get_active_threshold_limits` → ?
- `threshold_engine.ThresholdDriverSyncProtocol.get_active_threshold_limits` → ?

## Full Call Graph

```
[WRAPPER] alert_fatigue.AlertCheckResult.to_dict
[LEAF] alert_fatigue.AlertFatigueController.__init__
[LEAF] alert_fatigue.AlertFatigueController._check_deduplication
[SUPERSET] alert_fatigue.AlertFatigueController._check_domain_cooldown → alert_fatigue:TenantFatigueSettings.get_domain_cooldown
[LEAF] alert_fatigue.AlertFatigueController._check_tenant_rate_limit
[LEAF] alert_fatigue.AlertFatigueController._cleanup_old_records
[LEAF] alert_fatigue.AlertFatigueController._get_tenant_settings
[CANONICAL] alert_fatigue.AlertFatigueController.check_alert → alert_fatigue:AlertFatigueController._check_deduplication, alert_fatigue:AlertFatigueController._check_domain_cooldown, alert_fatigue:AlertFatigueController._check_tenant_rate_limit, alert_fatigue:AlertFatigueController._get_tenant_settings
[ENTRY] alert_fatigue.AlertFatigueController.get_tenant_stats → alert_fatigue:AlertFatigueController._get_tenant_settings
[SUPERSET] alert_fatigue.AlertFatigueController.record_alert_sent → alert_fatigue:AlertFatigueController._cleanup_old_records
[WRAPPER] alert_fatigue.AlertFatigueController.set_tenant_settings
[WRAPPER] alert_fatigue.AlertFatigueController.should_send_alert → alert_fatigue:AlertFatigueController.check_alert
[LEAF] alert_fatigue.AlertRecord.__post_init__
[WRAPPER] alert_fatigue.AlertRecord.age
[LEAF] alert_fatigue.TenantFatigueSettings.get_domain_cooldown
[LEAF] alert_fatigue.get_alert_fatigue_controller
[WRAPPER] alert_fatigue.reset_alert_fatigue_controller
[WRAPPER] budget_enforcement_driver.BudgetEnforcementDriver.__init__
[LEAF] budget_enforcement_driver.BudgetEnforcementDriver._get_engine
[LEAF] budget_enforcement_driver.BudgetEnforcementDriver.dispose
[INTERNAL] budget_enforcement_driver.BudgetEnforcementDriver.fetch_pending_budget_halts → budget_enforcement_driver:BudgetEnforcementDriver._get_engine, scoped_execution:ScopedExecutionContext.execute
[WRAPPER] budget_enforcement_driver.get_budget_enforcement_driver
[WRAPPER] budget_enforcement_engine.BudgetEnforcementEngine.__init__
[LEAF] budget_enforcement_engine.BudgetEnforcementEngine._parse_budget_from_error
[LEAF] budget_enforcement_engine.BudgetEnforcementEngine.emit_decision_for_halt
[CANONICAL] budget_enforcement_engine.BudgetEnforcementEngine.process_pending_halts → budget_enforcement_driver:BudgetEnforcementDriver.dispose, budget_enforcement_driver:BudgetEnforcementDriver.fetch_pending_budget_halts, budget_enforcement_driver:get_budget_enforcement_driver, budget_enforcement_engine:BudgetEnforcementEngine._parse_budget_from_error, budget_enforcement_engine:BudgetEnforcementEngine.emit_decision_for_halt
[WRAPPER] budget_enforcement_engine.emit_budget_halt_decision → budget_enforcement_engine:BudgetEnforcementEngine.emit_decision_for_halt
[WRAPPER] budget_enforcement_engine.process_pending_budget_decisions → budget_enforcement_engine:BudgetEnforcementEngine.process_pending_halts
[LEAF] cb_sync_wrapper._get_executor
[INTERNAL] cb_sync_wrapper._run_async_in_thread → cb_sync_wrapper:_get_executor
[ENTRY] cb_sync_wrapper.get_state_sync → cb_sync_wrapper:_run_async_in_thread, circuit_breaker:CircuitBreaker.get_state, circuit_breaker_async:AsyncCircuitBreaker.get_state, circuit_breaker_async:get_state
[INTERNAL] cb_sync_wrapper.is_v2_disabled_sync → cb_sync_wrapper:_run_async_in_thread, circuit_breaker:is_v2_disabled, circuit_breaker_async:is_v2_disabled
[LEAF] cb_sync_wrapper.shutdown_executor
[LEAF] circuit_breaker.CircuitBreaker.__init__
[SUPERSET] circuit_breaker.CircuitBreaker._auto_recover → circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker:CircuitBreaker._resolve_incident_db, circuit_breaker:CircuitBreaker._send_alert_enable, circuit_breaker_async:_get_or_create_state
[SUPERSET] circuit_breaker.CircuitBreaker._get_or_create_state → policy_limits_driver:PolicyLimitsDriver.flush
[LEAF] circuit_breaker.CircuitBreaker._post_alertmanager
[LEAF] circuit_breaker.CircuitBreaker._resolve_incident_db
[INTERNAL] circuit_breaker.CircuitBreaker._save_incident_file → alert_fatigue:AlertCheckResult.to_dict, circuit_breaker:CircuitBreakerState.to_dict, circuit_breaker:Incident.to_dict, circuit_breaker_async:CircuitBreakerState.to_dict, circuit_breaker_async:Incident.to_dict, ...+3
[INTERNAL] circuit_breaker.CircuitBreaker._send_alert_disable → circuit_breaker:CircuitBreaker._post_alertmanager
[INTERNAL] circuit_breaker.CircuitBreaker._send_alert_enable → circuit_breaker:CircuitBreaker._post_alertmanager
[SUPERSET] circuit_breaker.CircuitBreaker._trip → circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker:CircuitBreaker._save_incident_file, circuit_breaker:CircuitBreaker._send_alert_disable, circuit_breaker_async:_get_or_create_state
[INTERNAL] circuit_breaker.CircuitBreaker.disable_v2 → circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker:CircuitBreaker._trip, circuit_breaker_async:_get_or_create_state, circuit_breaker_async:_trip
[WRAPPER] circuit_breaker.CircuitBreaker.enable_v2 → circuit_breaker:CircuitBreaker.reset, circuit_breaker_async:AsyncCircuitBreaker.reset
[LEAF] circuit_breaker.CircuitBreaker.get_incidents
[WRAPPER] circuit_breaker.CircuitBreaker.get_state → circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker_async:_get_or_create_state
[WRAPPER] circuit_breaker.CircuitBreaker.is_closed → circuit_breaker:CircuitBreaker.is_open, circuit_breaker_async:AsyncCircuitBreaker.is_open
[SUPERSET] circuit_breaker.CircuitBreaker.is_disabled → circuit_breaker:CircuitBreaker._auto_recover, circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker_async:_auto_recover, circuit_breaker_async:_get_or_create_state
[WRAPPER] circuit_breaker.CircuitBreaker.is_open → circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker_async:_get_or_create_state
[SUPERSET] circuit_breaker.CircuitBreaker.report_drift → circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker:CircuitBreaker._trip, circuit_breaker_async:_get_or_create_state, circuit_breaker_async:_trip
[INTERNAL] circuit_breaker.CircuitBreaker.report_schema_error → circuit_breaker:CircuitBreaker._trip, circuit_breaker_async:_trip
[CANONICAL] circuit_breaker.CircuitBreaker.reset → circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker:CircuitBreaker._resolve_incident_db, circuit_breaker:CircuitBreaker._send_alert_enable, circuit_breaker_async:_get_or_create_state
[LEAF] circuit_breaker.CircuitBreakerState.to_dict
[LEAF] circuit_breaker.Incident.to_dict
[WRAPPER] circuit_breaker.create_circuit_breaker
[WRAPPER] circuit_breaker.disable_v2 → circuit_breaker:CircuitBreaker.disable_v2, circuit_breaker:create_circuit_breaker, circuit_breaker_async:AsyncCircuitBreaker.disable_v2, circuit_breaker_async:disable_v2
[WRAPPER] circuit_breaker.enable_v2 → circuit_breaker:CircuitBreaker.enable_v2, circuit_breaker:create_circuit_breaker, circuit_breaker_async:AsyncCircuitBreaker.enable_v2, circuit_breaker_async:enable_v2
[WRAPPER] circuit_breaker.is_v2_disabled → circuit_breaker:CircuitBreaker.is_disabled, circuit_breaker:create_circuit_breaker, circuit_breaker_async:AsyncCircuitBreaker.is_disabled, killswitch:KillSwitch.is_disabled
[LEAF] circuit_breaker_async.AsyncCircuitBreaker.__init__
[WRAPPER] circuit_breaker_async.AsyncCircuitBreaker.disable_v2 → circuit_breaker:CircuitBreaker.disable_v2, circuit_breaker:disable_v2, circuit_breaker_async:disable_v2
[WRAPPER] circuit_breaker_async.AsyncCircuitBreaker.enable_v2 → circuit_breaker:CircuitBreaker.enable_v2, circuit_breaker:enable_v2, circuit_breaker_async:enable_v2
[ENTRY] circuit_breaker_async.AsyncCircuitBreaker.get_incidents → circuit_breaker:CircuitBreaker.get_incidents, circuit_breaker_async:get_incidents
[WRAPPER] circuit_breaker_async.AsyncCircuitBreaker.get_state → circuit_breaker:CircuitBreaker.get_state, circuit_breaker_async:get_state
[WRAPPER] circuit_breaker_async.AsyncCircuitBreaker.is_closed → circuit_breaker:CircuitBreaker.is_open, circuit_breaker_async:AsyncCircuitBreaker.is_open
[WRAPPER] circuit_breaker_async.AsyncCircuitBreaker.is_disabled → circuit_breaker:is_v2_disabled, circuit_breaker_async:is_v2_disabled
[WRAPPER] circuit_breaker_async.AsyncCircuitBreaker.is_open → cb_sync_wrapper:is_v2_disabled_sync
[WRAPPER] circuit_breaker_async.AsyncCircuitBreaker.report_drift → circuit_breaker:CircuitBreaker.report_drift, circuit_breaker_async:report_drift
[WRAPPER] circuit_breaker_async.AsyncCircuitBreaker.report_schema_error → circuit_breaker:CircuitBreaker.report_schema_error, circuit_breaker_async:report_schema_error
[WRAPPER] circuit_breaker_async.AsyncCircuitBreaker.reset → circuit_breaker:CircuitBreaker.enable_v2, circuit_breaker:enable_v2, circuit_breaker_async:AsyncCircuitBreaker.enable_v2, circuit_breaker_async:enable_v2
[WRAPPER] circuit_breaker_async.AsyncCircuitBreaker.reset_v2 → circuit_breaker:CircuitBreaker.reset, circuit_breaker_async:AsyncCircuitBreaker.reset
[LEAF] circuit_breaker_async.CircuitBreakerState.to_dict
[LEAF] circuit_breaker_async.Incident.to_dict
[SUPERSET] circuit_breaker_async._auto_recover → circuit_breaker_async:_build_enable_alert_payload, circuit_breaker_async:_enqueue_alert, circuit_breaker_async:_resolve_incident
[LEAF] circuit_breaker_async._build_disable_alert_payload
[LEAF] circuit_breaker_async._build_enable_alert_payload
[INTERNAL] circuit_breaker_async._enqueue_alert → policy_limits_driver:PolicyLimitsDriver.flush
[SUPERSET] circuit_breaker_async._get_or_create_state → policy_limits_driver:PolicyLimitsDriver.flush, scoped_execution:ScopedExecutionContext.execute
[INTERNAL] circuit_breaker_async._resolve_incident → scoped_execution:ScopedExecutionContext.execute
[INTERNAL] circuit_breaker_async._trip → circuit_breaker_async:_build_disable_alert_payload, circuit_breaker_async:_enqueue_alert, policy_limits_driver:PolicyLimitsDriver.flush
[SUPERSET] circuit_breaker_async._try_auto_recover → circuit_breaker_async:_build_enable_alert_payload, circuit_breaker_async:_enqueue_alert, circuit_breaker_async:_resolve_incident, policy_limits_driver:PolicyLimitsDriver.flush, scoped_execution:ScopedExecutionContext.execute
[INTERNAL] circuit_breaker_async.disable_v2 → circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker:CircuitBreaker._trip, circuit_breaker_async:_get_or_create_state, circuit_breaker_async:_trip
[SUPERSET] circuit_breaker_async.enable_v2 → circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker_async:_build_enable_alert_payload, circuit_breaker_async:_enqueue_alert, circuit_breaker_async:_get_or_create_state, circuit_breaker_async:_resolve_incident
[LEAF] circuit_breaker_async.get_async_circuit_breaker
[INTERNAL] circuit_breaker_async.get_incidents → scoped_execution:ScopedExecutionContext.execute
[INTERNAL] circuit_breaker_async.get_state → circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker_async:_get_or_create_state
[CANONICAL] circuit_breaker_async.is_v2_disabled → circuit_breaker_async:_try_auto_recover, scoped_execution:ScopedExecutionContext.execute
[SUPERSET] circuit_breaker_async.report_drift → circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker:CircuitBreaker._trip, circuit_breaker_async:_get_or_create_state, circuit_breaker_async:_trip
[INTERNAL] circuit_breaker_async.report_schema_error → circuit_breaker:CircuitBreaker._get_or_create_state, circuit_breaker:CircuitBreaker._trip, circuit_breaker_async:_get_or_create_state, circuit_breaker_async:_trip
[WRAPPER] controls_facade.ControlConfig.to_dict
[WRAPPER] controls_facade.ControlStatusSummary.to_dict
[WRAPPER] controls_facade.ControlsFacade.__init__
[LEAF] controls_facade.ControlsFacade._ensure_default_controls
[SUPERSET] controls_facade.ControlsFacade.disable_control → controls_facade:ControlsFacade._ensure_default_controls
[SUPERSET] controls_facade.ControlsFacade.enable_control → controls_facade:ControlsFacade._ensure_default_controls
[ENTRY] controls_facade.ControlsFacade.get_control → controls_facade:ControlsFacade._ensure_default_controls
[CANONICAL] controls_facade.ControlsFacade.get_status → controls_facade:ControlsFacade._ensure_default_controls
[SUPERSET] controls_facade.ControlsFacade.list_controls → controls_facade:ControlsFacade._ensure_default_controls
[SUPERSET] controls_facade.ControlsFacade.update_control → controls_facade:ControlsFacade._ensure_default_controls
[LEAF] controls_facade.get_controls_facade
[LEAF] cost_safety_rails.CostSafetyRails.__init__
[LEAF] cost_safety_rails.CostSafetyRails._get_action_count
[CANONICAL] cost_safety_rails.CostSafetyRails.can_auto_apply_policy → cost_safety_rails:CostSafetyRails._get_action_count
[SUPERSET] cost_safety_rails.CostSafetyRails.can_auto_apply_recovery → cost_safety_rails:CostSafetyRails._get_action_count
[SUPERSET] cost_safety_rails.CostSafetyRails.can_auto_apply_routing → cost_safety_rails:CostSafetyRails._get_action_count
[LEAF] cost_safety_rails.CostSafetyRails.get_status
[LEAF] cost_safety_rails.CostSafetyRails.record_action
[LEAF] cost_safety_rails.SafeCostLoopOrchestrator.__init__
[SUPERSET] cost_safety_rails.SafeCostLoopOrchestrator.process_anomaly_safe → controls_facade:ControlsFacade.get_status, cost_safety_rails:CostSafetyRails.can_auto_apply_policy, cost_safety_rails:CostSafetyRails.can_auto_apply_routing, cost_safety_rails:CostSafetyRails.get_status
[WRAPPER] cost_safety_rails.SafetyConfig.production
[WRAPPER] cost_safety_rails.SafetyConfig.testing
[LEAF] cost_safety_rails.get_safety_rails
[WRAPPER] customer_killswitch_read_engine.CustomerKillswitchReadService.__init__ → killswitch_read_driver:get_killswitch_read_driver
[ENTRY] customer_killswitch_read_engine.CustomerKillswitchReadService.get_killswitch_status → killswitch_read_driver:KillswitchReadDriver.get_killswitch_status
[LEAF] customer_killswitch_read_engine.get_customer_killswitch_read_service
[WRAPPER] decisions.AnomalySignal.to_signal_response
[WRAPPER] decisions.Decision.blocks_request
[WRAPPER] decisions.Decision.is_warning_only
[LEAF] decisions.ProtectionResult.to_error_response
[WRAPPER] decisions.allow
[WRAPPER] decisions.reject_cost_limit
[WRAPPER] decisions.reject_rate_limit
[WRAPPER] decisions.throttle
[WRAPPER] decisions.warn
[LEAF] killswitch.KillSwitch.__init__
[LEAF] killswitch.KillSwitch.activate
[WRAPPER] killswitch.KillSwitch.get_events
[WRAPPER] killswitch.KillSwitch.get_last_event
[WRAPPER] killswitch.KillSwitch.is_disabled
[WRAPPER] killswitch.KillSwitch.is_enabled
[LEAF] killswitch.KillSwitch.mark_rollback_complete
[WRAPPER] killswitch.KillSwitch.on_activate
[WRAPPER] killswitch.KillSwitch.rearm
[WRAPPER] killswitch.KillSwitch.state
[WRAPPER] killswitch.get_killswitch
[WRAPPER] killswitch.reset_killswitch_for_testing
[WRAPPER] killswitch_read_driver.KillswitchReadDriver.__init__
[LEAF] killswitch_read_driver.KillswitchReadDriver._get_active_guardrails
[LEAF] killswitch_read_driver.KillswitchReadDriver._get_incident_stats
[LEAF] killswitch_read_driver.KillswitchReadDriver._get_killswitch_state
[LEAF] killswitch_read_driver.KillswitchReadDriver._get_session
[CANONICAL] killswitch_read_driver.KillswitchReadDriver.get_killswitch_status → killswitch_read_driver:KillswitchReadDriver._get_active_guardrails, killswitch_read_driver:KillswitchReadDriver._get_incident_stats, killswitch_read_driver:KillswitchReadDriver._get_killswitch_state, killswitch_read_driver:KillswitchReadDriver._get_session
[WRAPPER] killswitch_read_driver.get_killswitch_read_driver
[WRAPPER] limits_read_driver.LimitsReadDriver.__init__
[ENTRY] limits_read_driver.LimitsReadDriver.fetch_budget_limits → scoped_execution:ScopedExecutionContext.execute
[ENTRY] limits_read_driver.LimitsReadDriver.fetch_limit_by_id → scoped_execution:ScopedExecutionContext.execute
[CANONICAL] limits_read_driver.LimitsReadDriver.fetch_limits → scoped_execution:ScopedExecutionContext.execute
[WRAPPER] limits_read_driver.get_limits_read_driver
[WRAPPER] override_driver.LimitOverrideService.__init__
[INTERNAL] override_driver.LimitOverrideService._get_limit → scoped_execution:ScopedExecutionContext.execute
[LEAF] override_driver.LimitOverrideService._to_response
[SUPERSET] override_driver.LimitOverrideService.cancel_override → override_driver:LimitOverrideService._to_response
[ENTRY] override_driver.LimitOverrideService.get_override → override_driver:LimitOverrideService._to_response
[ENTRY] override_driver.LimitOverrideService.list_overrides → override_driver:LimitOverrideService._to_response
[CANONICAL] override_driver.LimitOverrideService.request_override → override_driver:LimitOverrideService._get_limit, override_driver:LimitOverrideService._to_response
[LEAF] overrides.LimitOverrideRequest.validate_override_value
[WRAPPER] overrides.OverrideApprovalRequest.validate_rejection_reason
[WRAPPER] policy_limits.CreatePolicyLimitRequest.validate_reset_period
[WRAPPER] policy_limits.CreatePolicyLimitRequest.validate_window_seconds
[WRAPPER] policy_limits_driver.PolicyLimitsDriver.__init__
[WRAPPER] policy_limits_driver.PolicyLimitsDriver.add_integrity
[WRAPPER] policy_limits_driver.PolicyLimitsDriver.add_limit
[ENTRY] policy_limits_driver.PolicyLimitsDriver.fetch_limit_by_id → scoped_execution:ScopedExecutionContext.execute
[WRAPPER] policy_limits_driver.PolicyLimitsDriver.flush
[WRAPPER] policy_limits_driver.get_policy_limits_driver
[LEAF] s2_cost_smoothing.calculate_s2_bounded_value
[LEAF] s2_cost_smoothing.create_s2_envelope
[LEAF] s2_cost_smoothing.validate_s2_envelope
[SUPERSET] scoped_execution.BoundExecutionScope.can_execute → scoped_execution:BoundExecutionScope.is_valid
[LEAF] scoped_execution.BoundExecutionScope.consume
[LEAF] scoped_execution.BoundExecutionScope.is_valid
[LEAF] scoped_execution.BoundExecutionScope.to_dict
[LEAF] scoped_execution.ScopeStore.__new__
[LEAF] scoped_execution.ScopeStore.cleanup_expired
[LEAF] scoped_execution.ScopeStore.create_scope
[WRAPPER] scoped_execution.ScopeStore.get_scope
[WRAPPER] scoped_execution.ScopeStore.get_scopes_for_incident
[LEAF] scoped_execution.ScopeStore.revoke_scope
[LEAF] scoped_execution.ScopedExecutionContext.__init__
[LEAF] scoped_execution.ScopedExecutionContext._compute_hash
[SUPERSET] scoped_execution.ScopedExecutionContext._dry_run_validate → scoped_execution:ScopedExecutionContext._compute_hash, scoped_execution:ScopedExecutionContext._elapsed_ms, scoped_execution:ScopedExecutionContext._estimate_cost
[LEAF] scoped_execution.ScopedExecutionContext._elapsed_ms
[WRAPPER] scoped_execution.ScopedExecutionContext._estimate_cost
[INTERNAL] scoped_execution.ScopedExecutionContext._execute_scoped → scoped_execution:ScopedExecutionContext._compute_hash, scoped_execution:ScopedExecutionContext._elapsed_ms
[INTERNAL] scoped_execution.ScopedExecutionContext.execute → scoped_execution:ScopedExecutionContext._compute_hash, scoped_execution:ScopedExecutionContext._dry_run_validate, scoped_execution:ScopedExecutionContext._elapsed_ms, scoped_execution:ScopedExecutionContext._execute_scoped
[ENTRY] scoped_execution.create_recovery_scope → alert_fatigue:AlertCheckResult.to_dict, circuit_breaker:CircuitBreakerState.to_dict, circuit_breaker:Incident.to_dict, circuit_breaker_async:CircuitBreakerState.to_dict, circuit_breaker_async:Incident.to_dict, ...+5
[CANONICAL] scoped_execution.execute_with_scope → scoped_execution:BoundExecutionScope.can_execute, scoped_execution:BoundExecutionScope.consume, scoped_execution:ScopeStore.get_scope, scoped_execution:get_scope_store
[WRAPPER] scoped_execution.get_scope_store
[LEAF] scoped_execution.requires_scoped_execution
[ENTRY] scoped_execution.test_recovery_scope → scoped_execution:ScopedExecutionContext.execute
[WRAPPER] scoped_execution.validate_scope_required
[WRAPPER] threshold_driver.ThresholdDriver.__init__
[INTERNAL] threshold_driver.ThresholdDriver.get_active_threshold_limits → scoped_execution:ScopedExecutionContext.execute
[CANONICAL] threshold_driver.ThresholdDriver.get_threshold_limit_by_scope → scoped_execution:ScopedExecutionContext.execute
[WRAPPER] threshold_driver.ThresholdDriverSync.__init__
[INTERNAL] threshold_driver.ThresholdDriverSync.get_active_threshold_limits → scoped_execution:ScopedExecutionContext.execute
# [DELETED] threshold_driver.emit_and_persist_threshold_signal — moved to L4 signal_coordinator (PIN-507 Law 4)
[LEAF] threshold_driver.emit_threshold_signal_sync
[WRAPPER] threshold_engine.LLMRunEvaluator.__init__
[SUPERSET] threshold_engine.LLMRunEvaluator.evaluate_completed_run → threshold_engine:LLMRunThresholdResolver.resolve, threshold_engine:LLMRunThresholdResolverSync.resolve
[SUPERSET] threshold_engine.LLMRunEvaluator.evaluate_live_run → threshold_engine:LLMRunThresholdResolver.resolve, threshold_engine:LLMRunThresholdResolverSync.resolve
[WRAPPER] threshold_engine.LLMRunEvaluatorSync.__init__
[SUPERSET] threshold_engine.LLMRunEvaluatorSync.evaluate_completed_run → threshold_engine:LLMRunThresholdResolver.resolve, threshold_engine:LLMRunThresholdResolverSync.resolve
[WRAPPER] threshold_engine.LLMRunThresholdResolver.__init__
[CANONICAL] threshold_engine.LLMRunThresholdResolver.resolve → threshold_driver:ThresholdDriver.get_active_threshold_limits, threshold_driver:ThresholdDriverSync.get_active_threshold_limits, threshold_engine:ThresholdDriverProtocol.get_active_threshold_limits, threshold_engine:ThresholdDriverSyncProtocol.get_active_threshold_limits
[WRAPPER] threshold_engine.LLMRunThresholdResolverSync.__init__
[SUPERSET] threshold_engine.LLMRunThresholdResolverSync.resolve → threshold_driver:ThresholdDriver.get_active_threshold_limits, threshold_driver:ThresholdDriverSync.get_active_threshold_limits, threshold_engine:ThresholdDriverProtocol.get_active_threshold_limits, threshold_engine:ThresholdDriverSyncProtocol.get_active_threshold_limits
[WRAPPER] threshold_engine.ThresholdDriverProtocol.get_active_threshold_limits
[WRAPPER] threshold_engine.ThresholdDriverSyncProtocol.get_active_threshold_limits
[LEAF] threshold_engine.ThresholdParams.coerce_decimal_to_float
[ENTRY] threshold_engine.collect_signals_from_evaluation → threshold_engine:create_threshold_signal_record
[LEAF] threshold_engine.create_threshold_signal_record
```
