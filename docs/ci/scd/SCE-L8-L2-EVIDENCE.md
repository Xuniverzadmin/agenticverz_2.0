# SCE Evidence: L8 to L2 Boundary

**Generated:** 2025-12-31T20:24:08.474206+00:00
**Status:** EVIDENCE ONLY - No conclusions, no fixes
**Reference:** SCE_CONTRACT.yaml

---

## Boundary Crossings

| From File | To File | Type | Line |
|-----------|---------|------|------|
| backend/scripts/run_escalation.py | backend/app/api/policy.py | import | 38 |
| backend/tests/test_m10_metrics.py | backend/app/main.py | import | 128 |
| backend/tests/test_category7_legacy_routes.py | backend/app/api/legacy_routes.py | import | 233 |
| backend/tests/test_category7_legacy_routes.py | backend/app/main.py | import | 20 |
| backend/tests/test_category6_founder_actions.py | backend/app/api/founder_actions.py | import | 236 |
| backend/tests/test_m10_recovery_enhanced.py | backend/app/api/recovery_ingest.py | import | 410 |
| backend/tests/test_m10_recovery_enhanced.py | backend/app/api/recovery.py | import | 410 |
| backend/tests/test_m26_prevention.py | backend/app/api/cost_intelligence.py | import | 53 |
| backend/tests/test_m26_prevention.py | backend/app/main.py | import | 39 |
| backend/tests/test_m24_ops_console.py | backend/app/main.py | import | 346 |
| backend/tests/test_m19_policy.py | backend/app/api/policy.py | import | 692 |
| backend/tests/test_m13_iterations_cost.py | backend/app/api/runtime.py | import | 211 |
| backend/tests/test_category4_cost_intelligence.py | backend/app/api/cost_ops.py | import | 30 |
| backend/tests/test_category4_cost_intelligence.py | backend/app/api/cost_guard.py | import | 21 |
| backend/tests/test_m10_recovery_chaos.py | backend/app/api/recovery_ingest.py | import | 332 |
| backend/tests/test_route_contracts.py | backend/app/main.py | import | 28 |
| backend/tests/test_route_contracts.py | backend/app/api/ops.py | import | 343 |
| backend/tests/test_category5_incident_contrast.py | backend/app/api/guard.py | import | 22 |
| backend/tests/test_category5_incident_contrast.py | backend/app/api/ops.py | import | 30 |
| backend/tests/test_m22_killswitch.py | backend/app/api/v1_proxy.py | import | 339 |
| backend/tests/test_recovery.py | backend/app/main.py | import | 168 |
| backend/tests/integration/test_memory_integration.py | backend/app/api/costsim.py | import | 19 |
| backend/tests/integration/test_memory_integration.py | backend/app/main.py | import | 42 |
| backend/tests/lit/conftest.py | backend/app/main.py | import | 19 |
| tools/webhook_receiver/tests/test_rate_limiter_chaos.py | backend/app/main.py | import | 268 |
| tools/webhook_receiver/tests/test_readiness_probe.py | backend/app/main.py | import | 62 |
| tools/webhook_receiver/tests/test_log_correlation.py | backend/app/main.py | import | 251 |
| tools/webhook_receiver/tests/test_metric_fuzzer.py | backend/app/main.py | import | 255 |

---

## Declared Signals (from metadata)

| File | Type | Signal Name | Source |
|------|------|-------------|--------|
| backend/app/api/legacy_routes.py | consume | 1. Confusion when legacy paths silently fail | docstring: 1. Confusion when l |
| scripts/ops/sce/passes/pass_4_diff.py | emit | - SEMANTIC_DRIFT | docstring: - SEMANTIC_DRIFT |
| scripts/ops/sce/passes/pass_2_metadata.py | emit | - DECLARED_SIGNAL_EMIT | docstring: - DECLARED_SIGNAL_E |
| scripts/ops/sce/passes/pass_2_metadata.py | emit | signal_name | docstring: signal_name |
| scripts/ops/sce/passes/pass_2_metadata.py | consume | signal_name | docstring: signal_name |
| scripts/ops/sce/passes/pass_2_metadata.py | emit | , Consumes:) | docstring: , Consumes:) |
| scripts/ops/sce/passes/pass_2_metadata.py | consume | ) | docstring: ) |
| scripts/ops/sce/passes/pass_2_metadata.py | emit | signal_name | decorator: @emit('signal_name' |
| scripts/ops/sce/passes/pass_2_metadata.py | consume | signal_name | decorator: @consume('signal_na |
| scripts/ops/sce/passes/pass_2_metadata.py | consume | signal_name | decorator: @consume('signal_na |
| scripts/ops/sce/passes/pass_2_metadata.py | emit | signal_name | decorator: @emit('signal_name' |
| scripts/ops/sce/passes/pass_2_metadata.py | consume | signal_name | decorator: @consume('signal_na |
| scripts/ops/sce/passes/pass_2_metadata.py | emit | signal_name | comment: signal_name |
| scripts/ops/sce/passes/pass_2_metadata.py | consume | signal_name | comment: signal_name |
| scripts/ops/sce/passes/pass_3_mechanics.py | emit | - OBSERVED_SIGNAL_EMIT | docstring: - OBSERVED_SIGNAL_E |
| scripts/ops/sce/passes/pass_1_layers.py | emit | - BOUNDARY_CROSSING_OBSERVED | docstring: - BOUNDARY_CROSSING |
| scripts/ops/sce/passes/pass_1_layers.py | emit | BOUNDARY_CROSSING_OBSERVED | docstring: BOUNDARY_CROSSING_O |
| scripts/semantic_auditor/correlation/delta_engine.py | consume | Dict of file paths to their signals | docstring: Dict of file paths  |
| scripts/semantic_auditor/signals/layering.py | consume | - Import graph violations (e.g., L3 importing L5) | docstring: - Import graph viol |
| scripts/semantic_auditor/signals/authority.py | consume | - DB writes (session.commit(), session.add()) outside *_write_service*.py files | docstring: - DB writes (sessio |
| scripts/semantic_auditor/signals/execution.py | consume | - Async functions calling blocking I/O (open(), requests.get(), time.sleep()) | docstring: - Async functions c |

---

## Observed Patterns (from code)

| File | Pattern Type | Evidence | Confidence |
|------|--------------|----------|------------|
| backend/app/main.py | object_construction | class CreateAgentRequest looks like sign | MEDIUM |
| backend/app/main.py | object_construction | class CreateAgentResponse looks like sig | MEDIUM |
| backend/app/main.py | object_construction | class GoalRequest looks like signal payl | MEDIUM |
| backend/app/main.py | object_construction | class GoalResponse looks like signal pay | MEDIUM |
| backend/app/main.py | object_construction | class RunResponse looks like signal payl | MEDIUM |
| backend/app/main.py | object_construction | class MemoryResponse looks like signal p | MEDIUM |
| backend/app/main.py | object_construction | class ProvenanceResponse looks like sign | MEDIUM |
| backend/app/main.py | enqueue_call | function update_queue_depth matches sign | MEDIUM |
| backend/app/main.py | event_publish | call to get_publisher matches signal pat | HIGH |
| backend/app/main.py | enqueue_call | call to update_queue_depth matches signa | MEDIUM |
| backend/app/main.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/main.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/main.py | return_signal | function returns dict with signal-like k | LOW |
| backend/app/main.py | object_construction | class RetryRequest looks like signal pay | MEDIUM |
| backend/app/main.py | object_construction | class RetryResponse looks like signal pa | MEDIUM |
| backend/app/main.py | object_construction | class RerunRequest looks like signal pay | MEDIUM |
| backend/app/main.py | object_construction | class RerunResponse looks like signal pa | MEDIUM |
| backend/scripts/run_escalation.py | event_subscribe | call to run_escalation_task matches sign | MEDIUM |
| backend/scripts/backfill_provenance.py | return_signal | function returns dict with signal-like k | LOW |
| backend/scripts/backfill_provenance.py | return_signal | function returns dict with signal-like k | LOW |
| backend/scripts/backfill_memory_embeddings.py | event_subscribe | function signal_handler matches signal p | MEDIUM |
| backend/scripts/backfill_memory_embeddings.py | event_subscribe | call to async_session_context matches si | MEDIUM |
| backend/tests/test_m10_outbox_e2e.py | dispatch_call | call to send_response matches signal pat | HIGH |
| backend/tests/test_m10_outbox_e2e.py | dispatch_call | call to send_response matches signal pat | HIGH |
| backend/tests/test_m10_outbox_e2e.py | dispatch_call | call to send_response matches signal pat | HIGH |
| backend/tests/test_m10_outbox_e2e.py | dispatch_call | call to send_response matches signal pat | HIGH |
| backend/tests/test_m10_outbox_e2e.py | dispatch_call | call to send_header matches signal patte | HIGH |
| backend/tests/test_m10_outbox_e2e.py | event_subscribe | function test_retry_on_500_error matches | MEDIUM |
| backend/tests/test_m10_outbox_e2e.py | event_subscribe | function test_metrics_incremented_on_suc | MEDIUM |
| backend/tests/conftest.py | return_signal | function returns dict with signal-like k | LOW |
| backend/tests/test_worker_pool.py | event_publish | function test_logging_publisher_works ma | MEDIUM |
| backend/tests/test_worker_pool.py | event_publish | call to LoggingPublisher matches signal  | HIGH |
| backend/tests/test_worker_pool.py | event_publish | call to publish matches signal pattern | HIGH |
| backend/tests/test_worker_pool.py | event_publish | function test_get_publisher_returns_logg | MEDIUM |
| backend/tests/test_worker_pool.py | event_publish | call to get_publisher matches signal pat | HIGH |
| backend/tests/test_cost_simulator.py | event_subscribe | function test_json_transform_fast matche | MEDIUM |
| backend/tests/test_pb_s1_bypass_detection.py | event_subscribe | function test_no_direct_status_mutation_ | MEDIUM |
| backend/tests/test_pb_s1_bypass_detection.py | event_subscribe | function test_no_cross_table_confusion_i | MEDIUM |
| backend/tests/test_m25_graduation_downgrade.py | event_subscribe | function test_prevention_rate_collapse_t | MEDIUM |
| backend/tests/test_m25_graduation_downgrade.py | event_subscribe | function test_healthy_prevention_rate_no | MEDIUM |
| backend/tests/test_m25_graduation_downgrade.py | event_subscribe | function test_capability_lockouts_reenga | MEDIUM |
| backend/tests/test_category3_data_contracts.py | event_subscribe | function test_common_has_no_domain_types | MEDIUM |
| backend/tests/test_category3_data_contracts.py | event_subscribe | function test_contract_version_exists ma | MEDIUM |
| backend/tests/test_category3_data_contracts.py | event_subscribe | function test_contract_version_is_semver | MEDIUM |
| backend/tests/test_category7_legacy_routes.py | event_subscribe | function test_no_redirect_on_legacy_path | MEDIUM |
| backend/tests/test_category7_legacy_routes.py | event_subscribe | function test_operator_410_has_migration | MEDIUM |
| backend/tests/test_m20_optimizer.py | event_subscribe | function test_no_fold_non_constant match | MEDIUM |
| backend/tests/test_m20_optimizer.py | event_subscribe | function test_detect_action_conflict mat | MEDIUM |
| backend/tests/test_m20_optimizer.py | event_subscribe | call to get_execution_order matches sign | MEDIUM |
| backend/tests/test_m20_optimizer.py | event_subscribe | function test_execution_plan_stages matc | MEDIUM |

---

## Drifts Detected

| Type | Description | Severity |
|------|-------------|----------|
| declared_not_observed | Signal '- SEMANTIC_DRIFT' is declared but no mechanical patt | MEDIUM |
| declared_not_observed | Signal ')' is declared but no mechanical pattern was observe | MEDIUM |
| observed_not_declared | Pattern 'call to get_publisher matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to send_response matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to send_response matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to send_response matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to send_response matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to send_header matches signal pattern' observe | MEDIUM |
| observed_not_declared | Pattern 'call to LoggingPublisher matches signal pattern' ob | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to get_publisher matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to EventEmitter matches signal pattern' observ | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to EventEmitter matches signal pattern' observ | HIGH |
| observed_not_declared | Pattern 'call to emit_api_call matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to EventEmitter matches signal pattern' observ | HIGH |
| observed_not_declared | Pattern 'call to emit_llm_call matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to EventEmitter matches signal pattern' observ | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to EventEmitter matches signal pattern' observ | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to EventEmitter matches signal pattern' observ | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to IntentEmitter matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to IntentEmitter matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to IntentEmitter matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to IntentEmitter matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to emit matches signal pattern' observed but n | HIGH |
| observed_not_declared | Pattern 'call to get_emitted matches signal pattern' observe | HIGH |
| observed_not_declared | Pattern 'call to send matches signal pattern' observed but n | MEDIUM |
| observed_not_declared | Pattern 'call to DispatcherConfig matches signal pattern' ob | MEDIUM |
| observed_not_declared | Pattern 'call to IntegrationDispatcher matches signal patter | MEDIUM |
| observed_not_declared | Pattern 'call to IntegrationDispatcher matches signal patter | MEDIUM |
| observed_not_declared | Pattern 'call to send matches signal pattern' observed but n | MEDIUM |
| observed_not_declared | Pattern 'call to send matches signal pattern' observed but n | MEDIUM |
| observed_not_declared | Pattern 'call to send matches signal pattern' observed but n | MEDIUM |
| observed_not_declared | Pattern 'call to send matches signal pattern' observed but n | MEDIUM |
| observed_not_declared | Pattern 'call to send matches signal pattern' observed but n | MEDIUM |
| observed_not_declared | Pattern 'call to send matches signal pattern' observed but n | MEDIUM |
| observed_not_declared | Pattern 'call to emit_budget_enforcement_decision matches si | HIGH |
| observed_not_declared | Pattern 'call to emit_budget_enforcement_decision matches si | HIGH |
| observed_not_declared | Pattern 'call to MockPublisher matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to publish matches signal pattern' observed bu | HIGH |
| observed_not_declared | Pattern 'call to send_otp matches signal pattern' observed b | MEDIUM |
| observed_not_declared | Pattern 'call to get_dispatcher matches signal pattern' obse | MEDIUM |
| observed_not_declared | Pattern 'call to _send_webhook matches signal pattern' obser | MEDIUM |
| observed_not_declared | Pattern 'call to _send_webhook matches signal pattern' obser | MEDIUM |

---

## Broken Circuits

| Type | Description | Severity |
|------|-------------|----------|
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L8 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
| boundary_bypass | L2 imports from L5 but allowed imports are {'L6', 'L3', 'L4' | HIGH |
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

---

## Classification

This document is **EVIDENCE ONLY**.

- No conclusions have been drawn
- No fixes have been suggested
- Human SCD ratification is required for any action
