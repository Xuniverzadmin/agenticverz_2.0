# SCE Evidence: L5 to L4 Boundary

**Generated:** 2025-12-31T20:24:08.469045+00:00
**Status:** EVIDENCE ONLY - No conclusions, no fixes
**Reference:** SCE_CONTRACT.yaml

---

## Boundary Crossings

| From File | To File | Type | Line |
|-----------|---------|------|------|
| backend/app/optimization/coordinator.py | backend/app/optimization/envelope.py | import | 36 |
| backend/app/optimization/manager.py | backend/app/optimization/envelope.py | import | 23 |
| backend/app/optimization/manager.py | backend/app/optimization/killswitch.py | import | 33 |
| backend/app/worker/recovery_evaluator.py | backend/app/contracts/decisions.py | import | 54 |
| backend/app/worker/recovery_evaluator.py | backend/app/services/recovery_rule_engine.py | import | 215 |
| backend/app/worker/recovery_evaluator.py | backend/app/services/recovery_matcher.py | import | 234 |
| backend/app/worker/recovery_claim_worker.py | backend/app/services/claim_decision_engine.py | import | 147 |
| backend/app/jobs/graduation_evaluator.py | backend/app/integrations/graduation_engine.py | import | 62 |
| backend/app/jobs/failure_aggregation.py | backend/app/jobs/failure_classification_engine.py | import | 43 |
| backend/app/policy/runtime/__init__.py | backend/app/policy/runtime/intent.py | import | 20 |
| backend/app/policy/runtime/__init__.py | backend/app/policy/runtime/deterministic_engine.py | import | 15 |
| backend/app/policy/runtime/dag_executor.py | backend/app/policy/compiler/grammar.py | import | 28 |
| backend/app/policy/runtime/dag_executor.py | backend/app/policy/runtime/intent.py | import | 36 |
| backend/app/policy/runtime/dag_executor.py | backend/app/policy/ir/ir_nodes.py | import | 29 |
| backend/app/policy/runtime/dag_executor.py | backend/app/policy/optimizer/dag_sorter.py | import | 30 |
| backend/app/policy/runtime/dag_executor.py | backend/app/policy/runtime/deterministic_engine.py | import | 31 |

---

## Declared Signals (from metadata)

| File | Type | Signal Name | Source |
|------|------|-------------|--------|
| backend/app/workflow/canonicalize.py | consume | List of event dictionaries | docstring: List of event dicti |
| backend/app/worker/recovery_evaluator.py | consume | - on_evaluation_start: Called before evaluation begins | docstring: - on_evaluation_sta |
| backend/app/services/guard_write_service.py | consume | List of (event_type, description) tuples | docstring: List of (event_type |

---

## Observed Patterns (from code)

| File | Pattern Type | Evidence | Confidence |
|------|--------------|----------|------------|
| backend/app/auth/shadow_audit.py | object_construction | class ShadowAuditEvent looks like signal | MEDIUM |
| backend/app/auth/shadow_audit.py | event_subscribe | function log_founder_isolation_check mat | MEDIUM |
| backend/app/auth/rbac_engine.py | event_subscribe | call to _db_session_factory matches sign | MEDIUM |
| backend/app/auth/rbac.py | enqueue_call | call to submit matches signal pattern | MEDIUM |
| backend/app/planners/test_planners.py | event_subscribe | function test_anthropic_planner_initiali | MEDIUM |
| backend/app/planners/test_planners.py | event_subscribe | function test_anthropic_planner_initiali | MEDIUM |
| backend/app/optimization/coordinator.py | event_publish | function _emit_audit_record matches sign | MEDIUM |
| backend/app/optimization/coordinator.py | event_publish | call to _emit_audit_record matches signa | HIGH |
| backend/app/optimization/coordinator.py | event_publish | call to _emit_audit_record matches signa | HIGH |
| backend/app/optimization/coordinator.py | event_publish | call to _emit_audit_record matches signa | HIGH |
| backend/app/optimization/coordinator.py | event_subscribe | call to _find_preemption_targets matches | MEDIUM |
| backend/app/optimization/coordinator.py | event_subscribe | function _find_preemption_targets matche | MEDIUM |
| backend/app/optimization/coordinator.py | event_subscribe | call to _find_preemption_targets matches | MEDIUM |
| backend/app/optimization/coordinator.py | event_publish | call to _emit_audit_record matches signa | HIGH |
| backend/app/optimization/coordinator.py | event_publish | call to _emit_audit_record matches signa | HIGH |
| backend/app/optimization/coordinator.py | event_subscribe | function get_coordination_stats matches  | MEDIUM |
| backend/app/optimization/killswitch.py | object_construction | class KillSwitchEvent looks like signal  | MEDIUM |
| backend/app/optimization/killswitch.py | event_subscribe | function on_activate matches signal patt | MEDIUM |
| backend/app/optimization/manager.py | event_subscribe | call to on_activate matches signal patte | MEDIUM |
| backend/app/optimization/manager.py | event_subscribe | function _on_killswitch_activated matche | MEDIUM |
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
| backend/app/worker/recovery_evaluator.py | object_construction | class FailureEvent looks like signal pay | MEDIUM |
| backend/app/worker/recovery_evaluator.py | event_publish | call to emit_recovery_decision matches s | HIGH |
| backend/app/worker/recovery_evaluator.py | event_publish | call to emit_recovery_decision matches s | HIGH |
| backend/app/worker/recovery_evaluator.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/worker/recovery_evaluator.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/worker/recovery_evaluator.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/worker/recovery_evaluator.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/worker/recovery_evaluator.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/worker/pool.py | event_publish | call to get_publisher matches signal pat | HIGH |
| backend/app/worker/pool.py | dispatch_call | function poll_and_dispatch matches signa | MEDIUM |
| backend/app/worker/pool.py | event_publish | call to publish matches signal pattern | HIGH |

---

## Drifts Detected

| Type | Description | Severity |
|------|-------------|----------|
| observed_not_declared | Pattern 'call to _emit_audit_record matches signal pattern'  | HIGH |
| observed_not_declared | Pattern 'call to _emit_audit_record matches signal pattern'  | HIGH |
| observed_not_declared | Pattern 'call to _emit_audit_record matches signal pattern'  | HIGH |
| observed_not_declared | Pattern 'call to _emit_audit_record matches signal pattern'  | HIGH |
| observed_not_declared | Pattern 'call to _emit_audit_record matches signal pattern'  | HIGH |
| observed_not_declared | Pattern 'call to emit_policy_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to _check_and_block_async_send matches signal  | MEDIUM |
| observed_not_declared | Pattern 'call to emit_recovery_decision matches signal patte | HIGH |
| observed_not_declared | Pattern 'call to emit_recovery_decision matches signal patte | HIGH |
| observed_not_declared | Pattern 'call to get_publisher matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to poll_and_dispatch matches signal pattern' o | MEDIUM |
| observed_not_declared | Pattern 'call to get_publisher matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to emit_budget_enforcement_decision matches si | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
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
| observed_not_declared | Pattern 'call to notify matches signal pattern' observed but | MEDIUM |
| observed_not_declared | Pattern 'call to notify matches signal pattern' observed but | MEDIUM |
| observed_not_declared | Pattern 'call to notify matches signal pattern' observed but | MEDIUM |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to IntegrationDispatcher matches signal patter | MEDIUM |
| observed_not_declared | Pattern 'call to get_dispatcher matches signal pattern' obse | MEDIUM |
| observed_not_declared | Pattern 'call to dispatch matches signal pattern' observed b | MEDIUM |
| observed_not_declared | Pattern 'call to _publish_checkpoint_needed matches signal p | HIGH |
| observed_not_declared | Pattern 'call to _publish_event matches signal pattern' obse | HIGH |
| observed_not_declared | Pattern 'call to dispatch matches signal pattern' observed b | MEDIUM |
| observed_not_declared | Pattern 'call to dispatch matches signal pattern' observed b | MEDIUM |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |

---

## Broken Circuits

| Type | Description | Severity |
|------|-------------|----------|
| boundary_bypass | L4 imports from L3 but allowed imports are {'L5', 'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
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

---

## Classification

This document is **EVIDENCE ONLY**.

- No conclusions have been drawn
- No fixes have been suggested
- Human SCD ratification is required for any action
