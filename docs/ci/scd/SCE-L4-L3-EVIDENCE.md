# SCE Evidence: L4 to L3 Boundary

**Generated:** 2025-12-31T20:24:08.466517+00:00
**Status:** EVIDENCE ONLY - No conclusions, no fixes
**Reference:** SCE_CONTRACT.yaml

---

## Boundary Crossings

| From File | To File | Type | Line |
|-----------|---------|------|------|
| backend/app/auth/rbac.py | backend/app/auth/clerk_provider.py | import | 127 |
| backend/tests/planner/test_interface.py | backend/app/planner/interface.py | import | 26 |
| backend/tests/planner/test_interface.py | backend/app/planner/stub_planner.py | import | 37 |
| backend/tests/planner/test_determinism_stress.py | backend/app/planner/interface.py | import | 31 |
| backend/tests/planner/test_determinism_stress.py | backend/app/planner/stub_planner.py | import | 36 |

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
| backend/app/skill_http.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/skill_http.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/skill_http.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/auth/shadow_audit.py | object_construction | class ShadowAuditEvent looks like signal | MEDIUM |
| backend/app/auth/shadow_audit.py | event_subscribe | function log_founder_isolation_check mat | MEDIUM |
| backend/app/auth/oauth_providers.py | event_subscribe | function get_authorization_url matches s | MEDIUM |
| backend/app/auth/oauth_providers.py | event_subscribe | function get_authorization_url matches s | MEDIUM |
| backend/app/auth/rbac_engine.py | event_subscribe | call to _db_session_factory matches sign | MEDIUM |
| backend/app/auth/rbac.py | enqueue_call | call to submit matches signal pattern | MEDIUM |
| backend/app/planners/test_planners.py | event_subscribe | function test_anthropic_planner_initiali | MEDIUM |
| backend/app/planners/test_planners.py | event_subscribe | function test_anthropic_planner_initiali | MEDIUM |
| backend/app/planners/anthropic_adapter.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/optimization/killswitch.py | object_construction | class KillSwitchEvent looks like signal  | MEDIUM |
| backend/app/optimization/killswitch.py | event_subscribe | function on_activate matches signal patt | MEDIUM |
| backend/app/policy/models.py | object_construction | class PolicyEvaluationRequest looks like | MEDIUM |
| backend/app/policy/models.py | object_construction | class EnhancedPolicyEvaluationRequest lo | MEDIUM |
| backend/app/policy/engine.py | event_publish | call to emit_policy_decision matches sig | HIGH |
| backend/app/policy/engine.py | event_subscribe | function get_version_provenance matches  | MEDIUM |
| backend/app/policy/engine.py | event_subscribe | function get_topological_evaluation_orde | MEDIUM |
| backend/app/workflow/checkpoint.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/workflow/checkpoint.py | event_subscribe | call to _async_session_factory matches s | MEDIUM |
| backend/app/workflow/checkpoint.py | event_subscribe | call to _async_session_factory matches s | MEDIUM |
| backend/app/workflow/checkpoint.py | event_subscribe | call to _async_session_factory matches s | MEDIUM |
| backend/app/workflow/checkpoint.py | event_subscribe | call to _async_session_factory matches s | MEDIUM |
| backend/app/workflow/checkpoint.py | event_subscribe | call to _async_session_factory matches s | MEDIUM |
| backend/app/workflow/policies.py | exception_signal | raises PolicyViolationError which looks  | MEDIUM |
| backend/app/workflow/policies.py | exception_signal | raises PolicyViolationError which looks  | MEDIUM |
| backend/app/workflow/golden.py | object_construction | class GoldenEvent looks like signal payl | MEDIUM |
| backend/app/workflow/golden.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/workflow/golden.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/workflow/external_guard.py | dispatch_call | call to _check_and_block_async_send matc | HIGH |
| backend/app/workflow/external_guard.py | dispatch_call | function _check_and_block_async_send mat | MEDIUM |
| backend/app/workflow/engine.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/worker/simulate.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/learning/suggestions.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/learning/suggestions.py | event_subscribe | function validate_suggestion_text matche | MEDIUM |
| backend/app/learning/s1_rollback.py | event_subscribe | call to _generate_suggestion_text matche | MEDIUM |
| backend/app/learning/s1_rollback.py | event_subscribe | call to validate_suggestion_text matches | MEDIUM |
| backend/app/learning/s1_rollback.py | event_subscribe | function _generate_suggestion_text match | MEDIUM |
| backend/app/routing/feedback.py | object_construction | class RoutingOutcomeSignal looks like si | MEDIUM |
| backend/app/routing/feedback.py | object_construction | class StrategyAdjustmentSignal looks lik | MEDIUM |
| backend/app/routing/feedback.py | event_subscribe | function get_reputation_updates_for_care | MEDIUM |
| backend/app/routing/care.py | event_subscribe | call to _build_decision_reason matches s | MEDIUM |
| backend/app/routing/care.py | event_publish | call to emit_routing_decision matches si | HIGH |
| backend/app/routing/care.py | event_subscribe | function _build_decision_reason matches  | MEDIUM |
| backend/app/routing/models.py | object_construction | class RoutingRequest looks like signal p | MEDIUM |
| backend/app/routing/learning.py | event_subscribe | function get_reputation_store matches si | MEDIUM |
| backend/app/services/policy_violation_service.py | event_subscribe | function persist_violation_fact matches  | MEDIUM |
| backend/app/services/policy_violation_service.py | event_subscribe | function check_violation_persisted match | MEDIUM |
| backend/app/services/policy_violation_service.py | event_subscribe | call to check_violation_persisted matche | MEDIUM |

---

## Drifts Detected

| Type | Description | Severity |
|------|-------------|----------|
| observed_not_declared | Pattern 'call to emit_policy_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to _check_and_block_async_send matches signal  | MEDIUM |
| observed_not_declared | Pattern 'call to emit_routing_decision matches signal patter | HIGH |
| observed_not_declared | Pattern 'call to emit_feedback matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to emit_feedback matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to _send_otp_email matches signal pattern' obs | MEDIUM |
| observed_not_declared | Pattern 'call to emit_prediction matches signal pattern' obs | HIGH |
| observed_not_declared | Pattern 'call to emit_prediction matches signal pattern' obs | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to RedisPublisher matches signal pattern' obse | HIGH |
| observed_not_declared | Pattern 'call to LoggingPublisher matches signal pattern' ob | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
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
| observed_not_declared | Pattern 'call to _emit_metrics matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to _emit matches signal pattern' observed but  | HIGH |
| observed_not_declared | Pattern 'call to IntentEmitter matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to emit_all matches signal pattern' observed b | HIGH |

---

## Broken Circuits

| Type | Description | Severity |
|------|-------------|----------|
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
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
| half_circuit | Signal 'function publish matches signal pattern 'publish'' h | MEDIUM |

---

## Classification

This document is **EVIDENCE ONLY**.

- No conclusions have been drawn
- No fixes have been suggested
- Human SCD ratification is required for any action
