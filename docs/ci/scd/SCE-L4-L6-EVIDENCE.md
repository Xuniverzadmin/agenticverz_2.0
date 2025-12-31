# SCE Evidence: L4 to L6 Boundary

**Generated:** 2025-12-31T20:24:08.468098+00:00
**Status:** EVIDENCE ONLY - No conclusions, no fixes
**Reference:** SCE_CONTRACT.yaml

---

## Boundary Crossings

| From File | To File | Type | Line |
|-----------|---------|------|------|
| backend/app/services/policy_violation_service.py | backend/app/utils/runtime.py | import | 39 |
| backend/app/services/policy_violation_service.py | backend/app/db.py | import | 289 |
| backend/app/services/cost_anomaly_detector.py | backend/app/db.py | import | 36 |
| backend/app/services/recovery_matcher.py | backend/app/security/sanitize.py | import | 32 |
| backend/app/services/orphan_recovery.py | backend/app/models/tenant.py | import | 34 |
| backend/app/services/orphan_recovery.py | backend/app/db.py | import | 33 |
| backend/app/services/user_write_service.py | backend/app/models/tenant.py | import | 29 |
| backend/app/services/cost_write_service.py | backend/app/db.py | import | 29 |
| backend/app/services/incident_aggregator.py | backend/app/utils/runtime.py | import | 41 |
| backend/app/services/incident_aggregator.py | backend/app/models/killswitch.py | import | 40 |
| backend/app/services/llm_failure_service.py | backend/app/utils/runtime.py | import | 37 |
| backend/app/services/pattern_detection.py | backend/app/models/tenant.py | import | 34 |
| backend/app/services/pattern_detection.py | backend/app/db.py | import | 32 |
| backend/app/services/pattern_detection.py | backend/app/models/feedback.py | import | 32 |
| backend/app/services/founder_action_write_service.py | backend/app/models/tenant.py | import | 30 |
| backend/app/services/worker_write_service_async.py | backend/app/models/tenant.py | import | 33 |
| backend/app/services/worker_write_service_async.py | backend/app/db.py | import | 32 |
| backend/app/services/guard_write_service.py | backend/app/models/killswitch.py | import | 42 |
| backend/app/integrations/__init__.py | backend/app/db.py | import | 141 |
| backend/app/discovery/ledger.py | backend/app/db.py | import | 98 |
| backend/app/predictions/api.py | backend/app/models/prediction.py | import | 54 |
| backend/app/predictions/api.py | backend/app/db.py | import | 53 |
| backend/app/commands/policy_command.py | backend/app/workflow/metrics.py | import | 322 |
| backend/app/policy/validators/prevention_engine.py | backend/app/db_async.py | import | 811 |
| backend/app/agents/skills/llm_invoke_governed.py | backend/app/db.py | import | 384 |

---

## Declared Signals (from metadata)

| File | Type | Signal Name | Source |
|------|------|-------------|--------|
| backend/app/workflow/canonicalize.py | consume | List of event dictionaries | docstring: List of event dicti |
| backend/app/services/guard_write_service.py | consume | List of (event_type, description) tuples | docstring: List of (event_type |

---

## Observed Patterns (from code)

| File | Pattern Type | Evidence | Confidence |
|------|--------------|----------|------------|
| backend/app/db.py | event_subscribe | function get_async_session_factory match | MEDIUM |
| backend/app/db.py | event_subscribe | call to get_async_session_factory matche | MEDIUM |
| backend/app/db.py | event_subscribe | call to session_factory matches signal p | MEDIUM |
| backend/app/db.py | object_construction | class ApprovalRequest looks like signal  | MEDIUM |
| backend/app/db.py | event_subscribe | function transition_status matches signa | MEDIUM |
| backend/app/db.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/db_async.py | event_subscribe | function async_session_context matches s | MEDIUM |
| backend/app/logging_config.py | event_subscribe | call to StreamHandler matches signal pat | MEDIUM |
| backend/app/logging_config.py | event_subscribe | call to addHandler matches signal patter | MEDIUM |
| backend/app/auth/console_auth.py | object_construction | class AuthAuditEvent looks like signal p | MEDIUM |
| backend/app/auth/console_auth.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/auth/shadow_audit.py | object_construction | class ShadowAuditEvent looks like signal | MEDIUM |
| backend/app/auth/shadow_audit.py | event_subscribe | function log_founder_isolation_check mat | MEDIUM |
| backend/app/auth/rbac_middleware.py | dispatch_call | function dispatch matches signal pattern | MEDIUM |
| backend/app/auth/jwt_auth.py | object_construction | class TokenPayload looks like signal pay | MEDIUM |
| backend/app/auth/jwt_auth.py | object_construction | class MockRequest looks like signal payl | MEDIUM |
| backend/app/auth/rbac_engine.py | event_subscribe | call to _db_session_factory matches sign | MEDIUM |
| backend/app/auth/rbac.py | enqueue_call | call to submit matches signal pattern | MEDIUM |
| backend/app/planners/test_planners.py | event_subscribe | function test_anthropic_planner_initiali | MEDIUM |
| backend/app/planners/test_planners.py | event_subscribe | function test_anthropic_planner_initiali | MEDIUM |
| backend/app/optimization/killswitch.py | object_construction | class KillSwitchEvent looks like signal  | MEDIUM |
| backend/app/optimization/killswitch.py | event_subscribe | function on_activate matches signal patt | MEDIUM |
| backend/app/stores/health.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/stores/health.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/policy/models.py | object_construction | class PolicyEvaluationRequest looks like | MEDIUM |
| backend/app/policy/models.py | object_construction | class EnhancedPolicyEvaluationRequest lo | MEDIUM |
| backend/app/policy/engine.py | event_publish | call to emit_policy_decision matches sig | HIGH |
| backend/app/policy/engine.py | event_subscribe | function get_version_provenance matches  | MEDIUM |
| backend/app/policy/engine.py | event_subscribe | function get_topological_evaluation_orde | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | function get_correlation_id matches sign | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | function set_correlation_id matches sign | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | call to get_correlation_id matches signa | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | call to removeHandler matches signal pat | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | call to StreamHandler matches signal pat | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | call to addHandler matches signal patter | MEDIUM |
| backend/app/workflow/checkpoint.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/workflow/checkpoint.py | event_subscribe | call to _async_session_factory matches s | MEDIUM |
| backend/app/workflow/checkpoint.py | event_subscribe | call to _async_session_factory matches s | MEDIUM |
| backend/app/workflow/checkpoint.py | event_subscribe | call to _async_session_factory matches s | MEDIUM |
| backend/app/workflow/checkpoint.py | event_subscribe | call to _async_session_factory matches s | MEDIUM |
| backend/app/workflow/checkpoint.py | event_subscribe | call to _async_session_factory matches s | MEDIUM |
| backend/app/workflow/health.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/workflow/health.py | object_construction | class MockResponse looks like signal pay | MEDIUM |
| backend/app/workflow/policies.py | exception_signal | raises PolicyViolationError which looks  | MEDIUM |
| backend/app/workflow/policies.py | exception_signal | raises PolicyViolationError which looks  | MEDIUM |
| backend/app/workflow/golden.py | object_construction | class GoldenEvent looks like signal payl | MEDIUM |
| backend/app/workflow/golden.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/workflow/golden.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/workflow/external_guard.py | dispatch_call | call to _check_and_block_async_send matc | HIGH |
| backend/app/workflow/external_guard.py | dispatch_call | function _check_and_block_async_send mat | MEDIUM |

---

## Drifts Detected

| Type | Description | Severity |
|------|-------------|----------|
| observed_not_declared | Pattern 'call to emit_policy_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to _check_and_block_async_send matches signal  | MEDIUM |
| observed_not_declared | Pattern 'call to emit_routing_decision matches signal patter | HIGH |
| observed_not_declared | Pattern 'call to emit_budget_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to emit_budget_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to emit_budget_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to emit_feedback matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to emit_feedback matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to emit_batch matches signal pattern' observed | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to EventEmitter matches signal pattern' observ | HIGH |
| observed_not_declared | Pattern 'call to _emit_sync_impl matches signal pattern' obs | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to _emit_sync_impl matches signal pattern' obs | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to emit_sync matches signal pattern' observed  | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to IntegrationDispatcher matches signal patter | MEDIUM |
| observed_not_declared | Pattern 'call to get_dispatcher matches signal pattern' obse | MEDIUM |
| observed_not_declared | Pattern 'call to dispatch matches signal pattern' observed b | MEDIUM |
| observed_not_declared | Pattern 'call to dispatch matches signal pattern' observed b | MEDIUM |
| observed_not_declared | Pattern 'call to _create_notify_adjustment matches signal pa | MEDIUM |

---

## Broken Circuits

| Type | Description | Severity |
|------|-------------|----------|
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L6 imports from L4 but allowed imports are set() | MEDIUM |
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| half_circuit | Signal 'call to emit_budget_enforcement_decision matches sig | MEDIUM |
| half_circuit | Signal 'function emit_session_idle_timeout matches signal pa | MEDIUM |
| half_circuit | Signal 'function send_alert matches signal pattern 'send'' h | MEDIUM |
| half_circuit | Signal 'function send_one matches signal pattern 'send'' has | MEDIUM |
| half_circuit | Signal 'function emit_batch matches signal pattern 'emit'' h | MEDIUM |
| half_circuit | Signal 'call to integrationdispatcher matches signal pattern | MEDIUM |
| half_circuit | Signal 'call to _send_alert_disable matches signal pattern'  | MEDIUM |
| half_circuit | Signal 'call to eventemitter matches signal pattern' has emi | MEDIUM |
| half_circuit | Signal 'call to emailsendinput matches signal pattern' has e | MEDIUM |
| half_circuit | Signal 'function emit_session_ended matches signal pattern ' | MEDIUM |
| half_circuit | Signal 'function test_r2_emits_recovery_suggested matches si | MEDIUM |
| half_circuit | Signal 'function test_emit_single_event matches signal patte | MEDIUM |
| half_circuit | Signal 'function emit_freeze matches signal pattern 'emit''  | MEDIUM |
| half_circuit | Signal 'function test_get_publisher_returns_logging_by_defau | MEDIUM |
| half_circuit | Signal 'function send_otp matches signal pattern 'send'' has | MEDIUM |
| half_circuit | Signal 'function reset_publisher matches signal pattern 'pub | MEDIUM |
| half_circuit | Signal 'call to emit_llm_call matches signal pattern' has em | MEDIUM |
| half_circuit | Signal 'function emit_llm_call matches signal pattern 'emit' | MEDIUM |
| half_circuit | Signal 'call to helper_emit_care_decision matches signal pat | MEDIUM |
| half_circuit | Signal 'function emit_feedback matches signal pattern 'emit' | MEDIUM |
| half_circuit | Signal 'call to webhooksendskill matches signal pattern' has | MEDIUM |
| half_circuit | Signal 'function _emit matches signal pattern 'emit'' has em | MEDIUM |
| half_circuit | Signal 'call to record_alert_send_failure matches signal pat | MEDIUM |
| half_circuit | Signal ' boundary_crossing_observed' has emitter but no cons | MEDIUM |
| half_circuit | Signal 'call to emit_recovery_decision matches signal patter | MEDIUM |
| half_circuit | Signal 'call to dispatch matches signal pattern' has emitter | MEDIUM |
| half_circuit | Signal 'function emit_incident_viewed matches signal pattern | MEDIUM |
| half_circuit | Signal 'function emit_all matches signal pattern 'emit'' has | MEDIUM |
| half_circuit | Signal 'function emit_care_optimization_decision matches sig | MEDIUM |
| half_circuit | Signal 'function test_emission_rule_strict_failure_emits mat | MEDIUM |
| half_circuit | Signal 'function emit_export_started matches signal pattern  | MEDIUM |
| half_circuit | Signal 'function has_resend matches signal pattern 'send'' h | MEDIUM |
| half_circuit | Signal 'function dispatcher_config matches signal pattern 'd | MEDIUM |
| half_circuit | Signal 'function emit_replay_started matches signal pattern  | MEDIUM |
| half_circuit | Signal 'function _send_alert matches signal pattern 'send''  | MEDIUM |
| half_circuit | Signal 'call to emit_recovery_evaluation_decision matches si | MEDIUM |
| half_circuit | Signal 'function emit_routing_decision matches signal patter | MEDIUM |
| half_circuit | Signal 'function test_invariant_every_failure_emits_decision | MEDIUM |
| half_circuit | Signal 'call to loggingpublisher matches signal pattern' has | MEDIUM |
| half_circuit | Signal 'function test_emit_api_call matches signal pattern ' | MEDIUM |
| half_circuit | Signal 'boundary_crossing_observed' has emitter but no consu | MEDIUM |
| half_circuit | Signal 'function _create_notify_adjustment matches signal pa | MEDIUM |
| half_circuit | Signal 'function test_send_message matches signal pattern 's | MEDIUM |
| half_circuit | Signal 'call to poll_and_dispatch matches signal pattern' ha | MEDIUM |

---

## Classification

This document is **EVIDENCE ONLY**.

- No conclusions have been drawn
- No fixes have been suggested
- Human SCD ratification is required for any action
