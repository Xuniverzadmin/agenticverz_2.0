# SCE Evidence: L7 to L4 Boundary

**Generated:** 2025-12-31T20:24:08.472050+00:00
**Status:** EVIDENCE ONLY - No conclusions, no fixes
**Reference:** SCE_CONTRACT.yaml

---

## Boundary Crossings

| From File | To File | Type | Line |
|-----------|---------|------|------|
| scripts/ops/cost_snapshot_job.py | backend/app/integrations/cost_snapshots.py | import | 14 |
| scripts/ops/runtime_smoke.py | backend/app/workflow/checkpoint.py | import | 241 |
| scripts/ops/runtime_smoke.py | backend/app/agents/sba/schema.py | import | 311 |
| scripts/ops/runtime_smoke.py | backend/app/agents/services/__init__.py | import | 311 |
| scripts/ops/m25_trigger_real_incident.py | backend/app/integrations/__init__.py | import | 141 |
| scripts/ops/test_cost_snapshots.py | backend/app/integrations/cost_snapshots.py | import | 7 |
| scripts/ops/m25_gate_passage_demo.py | backend/app/integrations/graduation_engine.py | import | 343 |
| scripts/ops/m27_real_cost_test.py | backend/app/integrations/cost_safety_rails.py | import | 25 |
| scripts/ops/m27_real_cost_test.py | backend/app/integrations/cost_bridges.py | import | 25 |

---

## Declared Signals (from metadata)

| File | Type | Signal Name | Source |
|------|------|-------------|--------|
| backend/app/workflow/canonicalize.py | consume | List of event dictionaries | docstring: List of event dicti |
| backend/app/services/guard_write_service.py | consume | List of (event_type, description) tuples | docstring: List of (event_type |
| scripts/ops/canary/canary_runner.py | consume | - Partial writes (atomic rename) | docstring: - Partial writes (a |

---

## Observed Patterns (from code)

| File | Pattern Type | Evidence | Confidence |
|------|--------------|----------|------------|
| backend/app/cli.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/auth/shadow_audit.py | object_construction | class ShadowAuditEvent looks like signal | MEDIUM |
| backend/app/auth/shadow_audit.py | event_subscribe | function log_founder_isolation_check mat | MEDIUM |
| backend/app/auth/rbac_engine.py | event_subscribe | call to _db_session_factory matches sign | MEDIUM |
| backend/app/auth/rbac.py | enqueue_call | call to submit matches signal pattern | MEDIUM |
| backend/app/planners/test_planners.py | event_subscribe | function test_anthropic_planner_initiali | MEDIUM |
| backend/app/planners/test_planners.py | event_subscribe | function test_anthropic_planner_initiali | MEDIUM |
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
| backend/app/services/policy_violation_service.py | event_subscribe | function persist_violation_and_create_in | MEDIUM |
| backend/app/services/policy_violation_service.py | event_subscribe | call to persist_violation_fact matches s | MEDIUM |
| backend/app/services/policy_violation_service.py | event_subscribe | function verify_violation_truth matches  | MEDIUM |
| backend/app/services/policy_violation_service.py | event_subscribe | call to persist_violation_and_create_inc | MEDIUM |
| backend/app/services/cost_anomaly_detector.py | event_subscribe | function run_anomaly_detection_with_m25  | MEDIUM |

---

## Drifts Detected

| Type | Description | Severity |
|------|-------------|----------|
| observed_not_declared | Pattern 'call to emit_policy_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to _check_and_block_async_send matches signal  | MEDIUM |
| observed_not_declared | Pattern 'call to emit_routing_decision matches signal patter | HIGH |
| observed_not_declared | Pattern 'call to emit_feedback matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to emit_feedback matches signal pattern' obser | HIGH |
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
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to SendResult matches signal pattern' observed | MEDIUM |
| observed_not_declared | Pattern 'call to SendResult matches signal pattern' observed | MEDIUM |
| observed_not_declared | Pattern 'call to send matches signal pattern' observed but n | MEDIUM |
| observed_not_declared | Pattern 'call to WebhookSendSkill matches signal pattern' ob | MEDIUM |
| observed_not_declared | Pattern 'call to send_response matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to send_response matches signal pattern' obser | MEDIUM |

---

## Broken Circuits

| Type | Description | Severity |
|------|-------------|----------|
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L3 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L3 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L5 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L5 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L7 imports from L4 but allowed imports are {'L6'} | MEDIUM |
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

---

## Classification

This document is **EVIDENCE ONLY**.

- No conclusions have been drawn
- No fixes have been suggested
- Human SCD ratification is required for any action
