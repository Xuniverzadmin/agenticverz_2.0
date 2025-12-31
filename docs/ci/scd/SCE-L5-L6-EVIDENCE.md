# SCE Evidence: L5 to L6 Boundary

**Generated:** 2025-12-31T20:24:08.469900+00:00
**Status:** EVIDENCE ONLY - No conclusions, no fixes
**Reference:** SCE_CONTRACT.yaml

---

## Boundary Crossings

| From File | To File | Type | Line |
|-----------|---------|------|------|
| backend/app/optimization/coordinator.py | backend/app/optimization/audit_persistence.py | import | 35 |
| backend/app/worker/recovery_evaluator.py | backend/app/metrics.py | import | 329 |
| backend/app/worker/outbox_processor.py | backend/app/metrics.py | import | 381 |
| backend/app/jobs/storage.py | backend/app/db.py | import | 462 |
| backend/app/jobs/storage.py | backend/app/secrets/vault_client.py | import | 67 |
| backend/app/jobs/storage.py | backend/app/utils/metrics_helpers.py | import | 50 |
| backend/app/jobs/graduation_evaluator.py | backend/app/db.py | import | 226 |
| backend/app/jobs/failure_aggregation.py | backend/app/db.py | import | 77 |
| backend/app/tasks/m10_metrics_collector.py | backend/app/db_async.py | import | 113 |
| backend/app/tasks/m10_metrics_collector.py | backend/app/metrics.py | import | 40 |
| backend/app/tasks/recovery_queue_stream.py | backend/app/metrics.py | import | 1158 |
| backend/app/runtime/failure_catalog.py | backend/app/db.py | import | 611 |
| backend/app/runtime/replay.py | backend/app/traces/store.py | import | 28 |
| backend/app/runtime/replay.py | backend/app/traces/pg_store.py | import | 28 |
| backend/app/runtime/replay.py | backend/app/traces/models.py | import | 21 |
| backend/app/worker/runtime/core.py | backend/app/workflow/metrics.py | import | 46 |
| backend/tests/runtime/test_runtime_determinism.py | backend/app/traces/models.py | import | 17 |
| backend/tests/runtime/test_runtime_determinism.py | backend/app/traces/store.py | import | 23 |
| backend/tests/runtime/test_invariants.py | backend/app/utils/canonical_json.py | import | 253 |

---

## Declared Signals (from metadata)

| File | Type | Signal Name | Source |
|------|------|-------------|--------|
| backend/app/worker/recovery_evaluator.py | consume | - on_evaluation_start: Called before evaluation begins | docstring: - on_evaluation_sta |

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
| backend/app/auth/rbac_middleware.py | dispatch_call | function dispatch matches signal pattern | MEDIUM |
| backend/app/auth/jwt_auth.py | object_construction | class TokenPayload looks like signal pay | MEDIUM |
| backend/app/auth/jwt_auth.py | object_construction | class MockRequest looks like signal payl | MEDIUM |
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
| backend/app/optimization/manager.py | event_subscribe | call to on_activate matches signal patte | MEDIUM |
| backend/app/optimization/manager.py | event_subscribe | function _on_killswitch_activated matche | MEDIUM |
| backend/app/stores/health.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/stores/health.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/workflow/logging_context.py | event_subscribe | function get_correlation_id matches sign | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | function set_correlation_id matches sign | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | call to get_correlation_id matches signa | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | call to removeHandler matches signal pat | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | call to StreamHandler matches signal pat | MEDIUM |
| backend/app/workflow/logging_context.py | event_subscribe | call to addHandler matches signal patter | MEDIUM |
| backend/app/workflow/health.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/workflow/health.py | object_construction | class MockResponse looks like signal pay | MEDIUM |
| backend/app/workflow/metrics.py | event_subscribe | function record_cost_simulation_drift ma | MEDIUM |
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
| backend/app/worker/pool.py | enqueue_call | call to _fetch_queued_runs matches signa | MEDIUM |
| backend/app/worker/pool.py | enqueue_call | call to submit matches signal pattern | MEDIUM |

---

## Drifts Detected

| Type | Description | Severity |
|------|-------------|----------|
| observed_not_declared | Pattern 'call to _emit_audit_record matches signal pattern'  | HIGH |
| observed_not_declared | Pattern 'call to _emit_audit_record matches signal pattern'  | HIGH |
| observed_not_declared | Pattern 'call to _emit_audit_record matches signal pattern'  | HIGH |
| observed_not_declared | Pattern 'call to _emit_audit_record matches signal pattern'  | HIGH |
| observed_not_declared | Pattern 'call to _emit_audit_record matches signal pattern'  | HIGH |
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
| observed_not_declared | Pattern 'call to emit_budget_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to emit_budget_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to emit_budget_decision matches signal pattern | HIGH |
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
| observed_not_declared | Pattern 'call to notify matches signal pattern' observed but | MEDIUM |
| observed_not_declared | Pattern 'call to notify matches signal pattern' observed but | MEDIUM |
| observed_not_declared | Pattern 'call to notify matches signal pattern' observed but | MEDIUM |

---

## Broken Circuits

| Type | Description | Severity |
|------|-------------|----------|
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L6 imports from L4 but allowed imports are set() | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
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

---

## Classification

This document is **EVIDENCE ONLY**.

- No conclusions have been drawn
- No fixes have been suggested
- Human SCD ratification is required for any action
