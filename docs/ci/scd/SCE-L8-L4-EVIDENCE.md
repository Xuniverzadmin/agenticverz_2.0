# SCE Evidence: L8 to L4 Boundary

**Generated:** 2025-12-31T20:24:08.475991+00:00
**Status:** EVIDENCE ONLY - No conclusions, no fixes
**Reference:** SCE_CONTRACT.yaml

---

## Boundary Crossings

| From File | To File | Type | Line |
|-----------|---------|------|------|
| backend/tests/test_cost_simulator.py | backend/app/worker/simulate.py | import | 12 |
| backend/tests/test_m25_graduation_downgrade.py | backend/app/integrations/graduation_engine.py | import | 25 |
| backend/tests/test_category3_data_contracts.py | backend/app/contracts/ops.py | import | 202 |
| backend/tests/test_category3_data_contracts.py | backend/app/contracts/guard.py | import | 125 |
| backend/tests/test_m20_optimizer.py | backend/app/policy/compiler/grammar.py | import | 11 |
| backend/tests/test_m20_optimizer.py | backend/app/policy/compiler/parser.py | import | 12 |
| backend/tests/test_m20_optimizer.py | backend/app/policy/ir/ir_nodes.py | import | 14 |
| backend/tests/test_m20_optimizer.py | backend/app/policy/optimizer/dag_sorter.py | import | 26 |
| backend/tests/test_m20_optimizer.py | backend/app/policy/optimizer/folds.py | import | 27 |
| backend/tests/test_m20_optimizer.py | backend/app/policy/optimizer/conflict_resolver.py | import | 25 |
| backend/tests/test_category6_founder_actions.py | backend/app/contracts/ops.py | import | 22 |
| backend/tests/test_m10_recovery_enhanced.py | backend/app/services/recovery_rule_engine.py | import | 28 |
| backend/tests/test_m17_care.py | backend/app/routing/models.py | import | 11 |
| backend/tests/test_m17_care.py | backend/app/routing/care.py | import | 8 |
| backend/tests/test_m18_care_l.py | backend/app/agents/sba/evolution.py | import | 241 |
| backend/tests/test_m18_care_l.py | backend/app/routing/learning.py | import | 18 |
| backend/tests/test_m20_parser.py | backend/app/policy/compiler/grammar.py | import | 21 |
| backend/tests/test_m20_parser.py | backend/app/policy/compiler/parser.py | import | 22 |
| backend/tests/test_m20_parser.py | backend/app/policy/ast/visitors.py | import | 299 |
| backend/tests/test_m20_parser.py | backend/app/policy/compiler/tokenizer.py | import | 23 |
| backend/tests/test_m20_parser.py | backend/app/policy/ast/nodes.py | import | 13 |
| backend/tests/test_pb_s5_prediction.py | backend/app/services/__init__.py | import | 347 |
| backend/tests/test_m27_cost_loop.py | backend/app/integrations/cost_safety_rails.py | import | 298 |
| backend/tests/test_m27_cost_loop.py | backend/app/integrations/cost_bridges.py | import | 28 |
| backend/tests/test_m25_policy_overreach.py | backend/app/integrations/L3_adapters.py | import | 13 |
| backend/tests/test_m25_policy_overreach.py | backend/app/integrations/events.py | import | 16 |
| backend/tests/test_m26_prevention.py | backend/app/services/cost_anomaly_detector.py | import | 137 |
| backend/tests/test_m18_advanced.py | backend/app/agents/sba/evolution.py | import | 15 |
| backend/tests/test_m18_advanced.py | backend/app/routing/feedback.py | import | 21 |
| backend/tests/test_m18_advanced.py | backend/app/routing/governor.py | import | 25 |
| backend/tests/test_m18_advanced.py | backend/app/routing/learning.py | import | 32 |
| backend/tests/test_m12_load.py | backend/app/agents/services/job_service.py | import | 29 |
| backend/tests/test_m12_load.py | backend/app/agents/services/credit_service.py | import | 28 |
| backend/tests/test_m12_load.py | backend/app/agents/services/blackboard_service.py | import | 27 |
| backend/tests/test_m12_load.py | backend/app/agents/skills/agent_invoke.py | import | 326 |
| backend/tests/test_m12_load.py | backend/app/agents/services/worker_service.py | import | 30 |
| backend/tests/test_m20_runtime.py | backend/app/policy/compiler/grammar.py | import | 14 |
| backend/tests/test_m20_runtime.py | backend/app/policy/compiler/parser.py | import | 15 |
| backend/tests/test_m20_runtime.py | backend/app/policy/runtime/intent.py | import | 23 |
| backend/tests/test_m20_runtime.py | backend/app/policy/runtime/deterministic_engine.py | import | 18 |
| backend/tests/test_m19_policy.py | backend/app/policy/engine.py | import | 18 |
| backend/tests/test_m19_policy.py | backend/app/policy/models.py | import | 19 |
| backend/tests/test_pb_s3_feedback_loops.py | backend/app/services/__init__.py | import | 358 |
| backend/tests/test_pb_s2_crash_recovery.py | backend/app/services/__init__.py | import | 457 |
| backend/tests/test_m25_graduation_gates.py | backend/app/integrations/learning_proof.py | import | 19 |
| backend/tests/test_m24_prevention.py | backend/app/policy/validators/prevention_engine.py | import | 7 |
| backend/tests/test_pb_s4_policy_evolution.py | backend/app/services/__init__.py | import | 428 |
| backend/tests/test_m12_chaos.py | backend/app/agents/services/message_service.py | import | 278 |
| backend/tests/test_m12_chaos.py | backend/app/agents/services/job_service.py | import | 28 |
| backend/tests/test_m12_chaos.py | backend/app/agents/services/registry_service.py | import | 29 |

---

## Declared Signals (from metadata)

| File | Type | Signal Name | Source |
|------|------|-------------|--------|
| backend/app/workflow/canonicalize.py | consume | List of event dictionaries | docstring: List of event dicti |
| backend/app/services/guard_write_service.py | consume | List of (event_type, description) tuples | docstring: List of (event_type |
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
| backend/tests/test_category6_founder_actions.py | event_subscribe | function test_action_request_has_require | MEDIUM |
| backend/tests/test_category6_founder_actions.py | event_subscribe | function test_action_has_exactly_4_types | MEDIUM |
| backend/tests/test_category6_founder_actions.py | event_subscribe | function test_reason_has_required_fields | MEDIUM |
| backend/tests/test_category6_founder_actions.py | event_subscribe | function test_reason_code_has_6_values m | MEDIUM |
| backend/tests/test_category6_founder_actions.py | event_subscribe | function test_audit_action_type_includes | MEDIUM |
| backend/tests/test_category6_founder_actions.py | event_subscribe | function test_action_endpoints_exist mat | MEDIUM |
| backend/tests/test_category6_founder_actions.py | event_subscribe | function test_mutual_exclusion_configure | MEDIUM |
| backend/tests/test_category6_founder_actions.py | event_subscribe | function test_action_request_instantiati | MEDIUM |
| backend/tests/test_category6_founder_actions.py | event_subscribe | function test_action_response_instantiat | MEDIUM |
| backend/tests/test_pb_s1_invariants.py | event_subscribe | function test_mutation_of_failed_run_is_ | MEDIUM |
| backend/tests/test_pb_s1_invariants.py | event_subscribe | function test_mutation_of_completed_run_ | MEDIUM |
| backend/tests/test_pb_s1_invariants.py | event_subscribe | function test_retry_run_has_independent_ | MEDIUM |
| backend/tests/test_m10_recovery_enhanced.py | event_subscribe | function test_action_response_model matc | MEDIUM |
| backend/tests/test_m10_recovery_enhanced.py | event_subscribe | function test_suggestion_action_model ma | MEDIUM |
| backend/tests/test_m10_recovery_enhanced.py | event_subscribe | function test_suggestion_action_matches_ | MEDIUM |
| backend/tests/test_m10_recovery_enhanced.py | event_subscribe | function test_suggestion_input_to_dict m | MEDIUM |
| backend/tests/test_m10_recovery_enhanced.py | event_subscribe | function test_suggestion_provenance_to_d | MEDIUM |

---

## Drifts Detected

| Type | Description | Severity |
|------|-------------|----------|
| declared_not_observed | Signal '- SEMANTIC_DRIFT' is declared but no mechanical patt | MEDIUM |
| declared_not_observed | Signal ')' is declared but no mechanical pattern was observe | MEDIUM |
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
| observed_not_declared | Pattern 'call to emit_policy_decision matches signal pattern | HIGH |
| observed_not_declared | Pattern 'call to _check_and_block_async_send matches signal  | MEDIUM |
| observed_not_declared | Pattern 'call to emit_routing_decision matches signal patter | HIGH |
| observed_not_declared | Pattern 'call to emit_feedback matches signal pattern' obser | HIGH |
| observed_not_declared | Pattern 'call to emit_feedback matches signal pattern' obser | HIGH |

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
