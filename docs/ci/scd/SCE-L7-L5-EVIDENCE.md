# SCE Evidence: L7 to L5 Boundary

**Generated:** 2025-12-31T20:24:08.472820+00:00
**Status:** EVIDENCE ONLY - No conclusions, no fixes
**Reference:** SCE_CONTRACT.yaml

---

## Boundary Crossings

| From File | To File | Type | Line |
|-----------|---------|------|------|
| scripts/ops/m10_orchestrator.py | backend/app/worker/outbox_processor.py | import | 141 |
| scripts/ops/m10_load_chaos_test.py | backend/app/worker/outbox_processor.py | import | 280 |

---

## Declared Signals (from metadata)

| File | Type | Signal Name | Source |
|------|------|-------------|--------|
| backend/app/worker/recovery_evaluator.py | consume | - on_evaluation_start: Called before evaluation begins | docstring: - on_evaluation_sta |
| scripts/ops/canary/canary_runner.py | consume | - Partial writes (atomic rename) | docstring: - Partial writes (a |

---

## Observed Patterns (from code)

| File | Pattern Type | Evidence | Confidence |
|------|--------------|----------|------------|
| backend/app/cli.py | return_signal | function returns dict with signal-like k | LOW |
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
| backend/app/worker/pool.py | event_subscribe | call to _on_run_complete matches signal  | MEDIUM |
| backend/app/worker/pool.py | enqueue_call | function _fetch_queued_runs matches sign | MEDIUM |
| backend/app/worker/pool.py | event_subscribe | function _on_run_complete matches signal | MEDIUM |
| backend/app/worker/pool.py | event_publish | call to publish matches signal pattern | HIGH |
| backend/app/worker/pool.py | event_subscribe | function _signal_handler matches signal  | MEDIUM |
| backend/app/worker/pool.py | dispatch_call | call to poll_and_dispatch matches signal | HIGH |
| backend/app/worker/outbox_processor.py | event_subscribe | call to _handle_notification_event match | MEDIUM |
| backend/app/worker/outbox_processor.py | event_subscribe | function _handle_notification_event matc | MEDIUM |
| backend/app/worker/outbox_processor.py | event_subscribe | function shutdown_handler matches signal | MEDIUM |
| backend/app/worker/runner.py | event_publish | call to get_publisher matches signal pat | HIGH |
| backend/app/worker/runner.py | event_publish | call to publish matches signal pattern | HIGH |
| backend/app/worker/runner.py | event_publish | call to publish matches signal pattern | HIGH |
| backend/app/worker/runner.py | event_publish | call to publish matches signal pattern | HIGH |
| backend/app/worker/runner.py | event_publish | call to emit_budget_enforcement_decision | HIGH |
| backend/app/worker/runner.py | event_publish | call to publish matches signal pattern | HIGH |
| backend/app/worker/runner.py | event_publish | call to publish matches signal pattern | HIGH |
| backend/app/worker/runner.py | event_publish | call to publish matches signal pattern | HIGH |
| backend/app/worker/runner.py | event_publish | call to publish matches signal pattern | HIGH |
| backend/app/worker/recovery_claim_worker.py | event_subscribe | function signal_handler matches signal p | MEDIUM |
| backend/app/jobs/storage.py | event_subscribe | call to retry_if_exception_type matches  | MEDIUM |
| backend/app/jobs/storage.py | event_subscribe | function write_candidate_json_and_upload | MEDIUM |
| backend/app/jobs/storage.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/jobs/storage.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/jobs/storage.py | return_signal | function returns dict with signal-like k | LOW |

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
| observed_not_declared | Pattern 'call to notify matches signal pattern' observed but | MEDIUM |
| observed_not_declared | Pattern 'call to notify matches signal pattern' observed but | MEDIUM |
| observed_not_declared | Pattern 'call to notify matches signal pattern' observed but | MEDIUM |
| observed_not_declared | Pattern 'call to _publish_checkpoint_needed matches signal p | HIGH |
| observed_not_declared | Pattern 'call to _publish_event matches signal pattern' obse | HIGH |
| observed_not_declared | Pattern 'call to dispatch matches signal pattern' observed b | MEDIUM |
| observed_not_declared | Pattern 'call to dispatch matches signal pattern' observed b | MEDIUM |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to dispatch matches signal pattern' observed b | MEDIUM |
| observed_not_declared | Pattern 'call to WebhookSendSkill matches signal pattern' ob | MEDIUM |
| observed_not_declared | Pattern 'call to send_response matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to send_response matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to ResendEmailer matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to send_alert matches signal pattern' observed | MEDIUM |
| observed_not_declared | Pattern 'call to send_alert matches signal pattern' observed | MEDIUM |
| observed_not_declared | Pattern 'call to send_alert_with_retry matches signal patter | MEDIUM |

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
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
| boundary_bypass | L5 imports from L4 but allowed imports are {'L6'} | MEDIUM |
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

---

## Classification

This document is **EVIDENCE ONLY**.

- No conclusions have been drawn
- No fixes have been suggested
- Human SCD ratification is required for any action
