# USECASE Codebase Utilization Audit (UC-001..UC-017)

- Date: 2026-02-11
- Method: scripts/files explicitly referenced in `HANDOVER_BATCH_*_implemented.md` + current filesystem totals.
- Scope: `app/hoc/cus/{activity,incidents,policies,controls,analytics,logs}` (`L5_engines`, `L5_schemas`, `L6_drivers`, `adapters`) + L4 handlers.
- Important: `untouched` means not directly modified/referenced in the UC batch implementation evidence; it does not imply broken.

## Summary Counts

| Area | Total Scripts | Touched in UC Exercise | Untouched |
| --- | ---: | ---: | ---: |
| activity | 20 | 2 | 18 |
| incidents | 37 | 2 | 35 |
| policies | 97 | 0 | 97 |
| controls | 23 | 2 | 21 |
| analytics | 41 | 1 | 40 |
| logs | 42 | 3 | 39 |
| hoc_spine L4 handlers | 39 | 6 | 33 |
| verification scripts | 12 | 4 | 8 |

## Touched Script List (Resolved)

- `app/hoc/api/cus/policies/policy_proposals.py`
- `app/hoc/cus/activity/L5_engines/signal_feedback_engine.py`
- `app/hoc/cus/activity/L6_drivers/signal_feedback_driver.py`
- `app/hoc/cus/analytics/L6_drivers/analytics_artifacts_driver.py`
- `app/hoc/cus/controls/L6_drivers/evaluation_evidence_driver.py`
- `app/hoc/cus/controls/L6_drivers/override_driver.py`
- `app/hoc/cus/hoc_spine/orchestrator/handlers/activity_handler.py`
- `app/hoc/cus/hoc_spine/orchestrator/handlers/analytics_handler.py`
- `app/hoc/cus/hoc_spine/orchestrator/handlers/controls_handler.py`
- `app/hoc/cus/hoc_spine/orchestrator/handlers/incidents_handler.py`
- `app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py`
- `app/hoc/cus/hoc_spine/orchestrator/handlers/policy_approval_handler.py`
- `app/hoc/cus/incidents/L5_engines/incident_write_engine.py`
- `app/hoc/cus/incidents/L6_drivers/incident_write_driver.py`
- `app/hoc/cus/logs/L5_engines/trace_api_engine.py`
- `app/hoc/cus/logs/L5_schemas/traces_models.py`
- `app/hoc/cus/logs/L6_drivers/pg_store.py`
- `scripts/ci/check_init_hygiene.py`
- `scripts/verification/uc_mon_event_contract_check.py`
- `scripts/verification/uc_mon_route_operation_map_check.py`
- `scripts/verification/uc_mon_storage_contract_check.py`
- `scripts/verification/uc_mon_validation.py`

## Untouched in Exercise: activity

- `app/hoc/cus/activity/L5_engines/__init__.py`
- `app/hoc/cus/activity/L5_engines/activity_enums.py`
- `app/hoc/cus/activity/L5_engines/activity_facade.py`
- `app/hoc/cus/activity/L5_engines/attention_ranking.py`
- `app/hoc/cus/activity/L5_engines/cost_analysis.py`
- `app/hoc/cus/activity/L5_engines/cus_telemetry_engine.py`
- `app/hoc/cus/activity/L5_engines/pattern_detection.py`
- `app/hoc/cus/activity/L5_engines/signal_identity.py`
- `app/hoc/cus/activity/L5_schemas/__init__.py`
- `app/hoc/cus/activity/L6_drivers/__init__.py`
- `app/hoc/cus/activity/L6_drivers/activity_read_driver.py`
- `app/hoc/cus/activity/L6_drivers/cus_telemetry_driver.py`
- `app/hoc/cus/activity/L6_drivers/orphan_recovery_driver.py`
- `app/hoc/cus/activity/L6_drivers/run_metrics_driver.py`
- `app/hoc/cus/activity/L6_drivers/run_signal_driver.py`
- `app/hoc/cus/activity/adapters/__init__.py`
- `app/hoc/cus/activity/adapters/customer_activity_adapter.py`
- `app/hoc/cus/activity/adapters/workers_adapter.py`

## Untouched in Exercise: incidents

- `app/hoc/cus/incidents/L5_engines/__init__.py`
- `app/hoc/cus/incidents/L5_engines/anomaly_bridge.py`
- `app/hoc/cus/incidents/L5_engines/export_engine.py`
- `app/hoc/cus/incidents/L5_engines/hallucination_detector.py`
- `app/hoc/cus/incidents/L5_engines/incident_engine.py`
- `app/hoc/cus/incidents/L5_engines/incident_pattern.py`
- `app/hoc/cus/incidents/L5_engines/incident_read_engine.py`
- `app/hoc/cus/incidents/L5_engines/incidents_facade.py`
- `app/hoc/cus/incidents/L5_engines/incidents_types.py`
- `app/hoc/cus/incidents/L5_engines/policy_violation_engine.py`
- `app/hoc/cus/incidents/L5_engines/postmortem.py`
- `app/hoc/cus/incidents/L5_engines/recovery_rule_engine.py`
- `app/hoc/cus/incidents/L5_engines/recurrence_analysis.py`
- `app/hoc/cus/incidents/L5_engines/semantic_failures.py`
- `app/hoc/cus/incidents/L5_schemas/__init__.py`
- `app/hoc/cus/incidents/L5_schemas/export_schemas.py`
- `app/hoc/cus/incidents/L5_schemas/incident_decision_port.py`
- `app/hoc/cus/incidents/L5_schemas/severity_policy.py`
- `app/hoc/cus/incidents/L6_drivers/__init__.py`
- `app/hoc/cus/incidents/L6_drivers/cost_guard_driver.py`
- `app/hoc/cus/incidents/L6_drivers/export_bundle_driver.py`
- `app/hoc/cus/incidents/L6_drivers/incident_aggregator.py`
- `app/hoc/cus/incidents/L6_drivers/incident_driver.py`
- `app/hoc/cus/incidents/L6_drivers/incident_pattern_driver.py`
- `app/hoc/cus/incidents/L6_drivers/incident_read_driver.py`
- `app/hoc/cus/incidents/L6_drivers/incident_run_read_driver.py`
- `app/hoc/cus/incidents/L6_drivers/incidents_facade_driver.py`
- `app/hoc/cus/incidents/L6_drivers/lessons_driver.py`
- `app/hoc/cus/incidents/L6_drivers/llm_failure_driver.py`
- `app/hoc/cus/incidents/L6_drivers/policy_violation_driver.py`
- `app/hoc/cus/incidents/L6_drivers/postmortem_driver.py`
- `app/hoc/cus/incidents/L6_drivers/recurrence_analysis_driver.py`
- `app/hoc/cus/incidents/adapters/__init__.py`
- `app/hoc/cus/incidents/adapters/customer_incidents_adapter.py`
- `app/hoc/cus/incidents/adapters/founder_ops_adapter.py`

## Untouched in Exercise: policies

- `app/hoc/cus/policies/L5_engines/__init__.py`
- `app/hoc/cus/policies/L5_engines/ast.py`
- `app/hoc/cus/policies/L5_engines/authority_checker.py`
- `app/hoc/cus/policies/L5_engines/binding_moment_enforcer.py`
- `app/hoc/cus/policies/L5_engines/compiler_parser.py`
- `app/hoc/cus/policies/L5_engines/content_accuracy.py`
- `app/hoc/cus/policies/L5_engines/cus_enforcement_engine.py`
- `app/hoc/cus/policies/L5_engines/customer_policy_read_engine.py`
- `app/hoc/cus/policies/L5_engines/dag_executor.py`
- `app/hoc/cus/policies/L5_engines/decorator.py`
- `app/hoc/cus/policies/L5_engines/degraded_mode.py`
- `app/hoc/cus/policies/L5_engines/deterministic_engine.py`
- `app/hoc/cus/policies/L5_engines/dsl_parser.py`
- `app/hoc/cus/policies/L5_engines/engine.py`
- `app/hoc/cus/policies/L5_engines/failure_mode_handler.py`
- `app/hoc/cus/policies/L5_engines/folds.py`
- `app/hoc/cus/policies/L5_engines/governance_facade.py`
- `app/hoc/cus/policies/L5_engines/grammar.py`
- `app/hoc/cus/policies/L5_engines/intent.py`
- `app/hoc/cus/policies/L5_engines/interpreter.py`
- `app/hoc/cus/policies/L5_engines/ir_builder.py`
- `app/hoc/cus/policies/L5_engines/ir_compiler.py`
- `app/hoc/cus/policies/L5_engines/ir_nodes.py`
- `app/hoc/cus/policies/L5_engines/kernel.py`
- `app/hoc/cus/policies/L5_engines/kill_switch.py`
- `app/hoc/cus/policies/L5_engines/lessons_engine.py`
- `app/hoc/cus/policies/L5_engines/limits.py`
- `app/hoc/cus/policies/L5_engines/limits_facade.py`
- `app/hoc/cus/policies/L5_engines/limits_simulation_engine.py`
- `app/hoc/cus/policies/L5_engines/llm_policy.py`
- `app/hoc/cus/policies/L5_engines/nodes.py`
- `app/hoc/cus/policies/L5_engines/phase_status_invariants.py`
- `app/hoc/cus/policies/L5_engines/plan.py`
- `app/hoc/cus/policies/L5_engines/plan_generation.py`
- `app/hoc/cus/policies/L5_engines/policies_facade.py`
- `app/hoc/cus/policies/L5_engines/policies_limits_query_engine.py`
- `app/hoc/cus/policies/L5_engines/policies_proposals_query_engine.py`
- `app/hoc/cus/policies/L5_engines/policies_rules_query_engine.py`
- `app/hoc/cus/policies/L5_engines/policy_command.py`
- `app/hoc/cus/policies/L5_engines/policy_conflict_resolver.py`
- `app/hoc/cus/policies/L5_engines/policy_driver.py`
- `app/hoc/cus/policies/L5_engines/policy_graph.py`
- `app/hoc/cus/policies/L5_engines/policy_limits_engine.py`
- `app/hoc/cus/policies/L5_engines/policy_mapper.py`
- `app/hoc/cus/policies/L5_engines/policy_models.py`
- `app/hoc/cus/policies/L5_engines/policy_proposal_engine.py`
- `app/hoc/cus/policies/L5_engines/policy_rules_engine.py`
- `app/hoc/cus/policies/L5_engines/prevention_hook.py`
- `app/hoc/cus/policies/L5_engines/protection_provider.py`
- `app/hoc/cus/policies/L5_engines/recovery_evaluation_engine.py`
- `app/hoc/cus/policies/L5_engines/runtime_command.py`
- `app/hoc/cus/policies/L5_engines/sandbox_engine.py`
- `app/hoc/cus/policies/L5_engines/sandbox_executor.py`
- `app/hoc/cus/policies/L5_engines/snapshot_engine.py`
- `app/hoc/cus/policies/L5_engines/state.py`
- `app/hoc/cus/policies/L5_engines/tokenizer.py`
- `app/hoc/cus/policies/L5_engines/validator.py`
- `app/hoc/cus/policies/L5_engines/visitors.py`
- `app/hoc/cus/policies/L5_engines/worker_execution_command.py`
- `app/hoc/cus/policies/L5_schemas/__init__.py`
- `app/hoc/cus/policies/L5_schemas/domain_bridge_capabilities.py`
- `app/hoc/cus/policies/L5_schemas/intent_validation.py`
- `app/hoc/cus/policies/L5_schemas/policy_check.py`
- `app/hoc/cus/policies/L5_schemas/policy_rules.py`
- `app/hoc/cus/policies/L6_drivers/__init__.py`
- `app/hoc/cus/policies/L6_drivers/arbitrator.py`
- `app/hoc/cus/policies/L6_drivers/cus_enforcement_driver.py`
- `app/hoc/cus/policies/L6_drivers/guard_read_driver.py`
- `app/hoc/cus/policies/L6_drivers/limits_simulation_driver.py`
- `app/hoc/cus/policies/L6_drivers/m25_integration_read_driver.py`
- `app/hoc/cus/policies/L6_drivers/m25_integration_write_driver.py`
- `app/hoc/cus/policies/L6_drivers/optimizer_conflict_resolver.py`
- `app/hoc/cus/policies/L6_drivers/policies_facade_driver.py`
- `app/hoc/cus/policies/L6_drivers/policy_approval_driver.py`
- `app/hoc/cus/policies/L6_drivers/policy_enforcement_driver.py`
- `app/hoc/cus/policies/L6_drivers/policy_enforcement_write_driver.py`
- `app/hoc/cus/policies/L6_drivers/policy_engine_driver.py`
- `app/hoc/cus/policies/L6_drivers/policy_graph_driver.py`
- `app/hoc/cus/policies/L6_drivers/policy_proposal_read_driver.py`
- `app/hoc/cus/policies/L6_drivers/policy_proposal_write_driver.py`
- `app/hoc/cus/policies/L6_drivers/policy_read_driver.py`
- `app/hoc/cus/policies/L6_drivers/policy_rules_driver.py`
- `app/hoc/cus/policies/L6_drivers/policy_rules_read_driver.py`
- `app/hoc/cus/policies/L6_drivers/prevention_records_read_driver.py`
- `app/hoc/cus/policies/L6_drivers/proposals_read_driver.py`
- `app/hoc/cus/policies/L6_drivers/rbac_audit_driver.py`
- `app/hoc/cus/policies/L6_drivers/recovery_matcher.py`
- `app/hoc/cus/policies/L6_drivers/recovery_read_driver.py`
- `app/hoc/cus/policies/L6_drivers/recovery_write_driver.py`
- `app/hoc/cus/policies/L6_drivers/replay_read_driver.py`
- `app/hoc/cus/policies/L6_drivers/scope_resolver.py`
- `app/hoc/cus/policies/L6_drivers/symbol_table.py`
- `app/hoc/cus/policies/L6_drivers/workers_read_driver.py`
- `app/hoc/cus/policies/adapters/__init__.py`
- `app/hoc/cus/policies/adapters/customer_policies_adapter.py`
- `app/hoc/cus/policies/adapters/founder_contract_review_adapter.py`
- `app/hoc/cus/policies/adapters/policy_adapter.py`

## Untouched in Exercise: controls

- `app/hoc/cus/controls/L5_engines/__init__.py`
- `app/hoc/cus/controls/L5_engines/cb_sync_wrapper_engine.py`
- `app/hoc/cus/controls/L5_engines/controls_facade.py`
- `app/hoc/cus/controls/L5_engines/threshold_engine.py`
- `app/hoc/cus/controls/L5_schemas/__init__.py`
- `app/hoc/cus/controls/L5_schemas/override_types.py`
- `app/hoc/cus/controls/L5_schemas/overrides.py`
- `app/hoc/cus/controls/L5_schemas/policy_limits.py`
- `app/hoc/cus/controls/L5_schemas/simulation.py`
- `app/hoc/cus/controls/L5_schemas/threshold_signals.py`
- `app/hoc/cus/controls/L6_drivers/__init__.py`
- `app/hoc/cus/controls/L6_drivers/budget_enforcement_driver.py`
- `app/hoc/cus/controls/L6_drivers/circuit_breaker_async_driver.py`
- `app/hoc/cus/controls/L6_drivers/circuit_breaker_driver.py`
- `app/hoc/cus/controls/L6_drivers/killswitch_ops_driver.py`
- `app/hoc/cus/controls/L6_drivers/killswitch_read_driver.py`
- `app/hoc/cus/controls/L6_drivers/limits_read_driver.py`
- `app/hoc/cus/controls/L6_drivers/policy_limits_driver.py`
- `app/hoc/cus/controls/L6_drivers/scoped_execution_driver.py`
- `app/hoc/cus/controls/L6_drivers/threshold_driver.py`
- `app/hoc/cus/controls/adapters/__init__.py`

## Untouched in Exercise: analytics

- `app/hoc/cus/analytics/L5_engines/__init__.py`
- `app/hoc/cus/analytics/L5_engines/analytics_facade.py`
- `app/hoc/cus/analytics/L5_engines/canary_engine.py`
- `app/hoc/cus/analytics/L5_engines/config_engine.py`
- `app/hoc/cus/analytics/L5_engines/cost_anomaly_detector_engine.py`
- `app/hoc/cus/analytics/L5_engines/cost_model.py`
- `app/hoc/cus/analytics/L5_engines/cost_snapshots_engine.py`
- `app/hoc/cus/analytics/L5_engines/cost_write.py`
- `app/hoc/cus/analytics/L5_engines/costsim_models.py`
- `app/hoc/cus/analytics/L5_engines/datasets_engine.py`
- `app/hoc/cus/analytics/L5_engines/detection_facade.py`
- `app/hoc/cus/analytics/L5_engines/divergence_engine.py`
- `app/hoc/cus/analytics/L5_engines/feedback_read_engine.py`
- `app/hoc/cus/analytics/L5_engines/metrics_engine.py`
- `app/hoc/cus/analytics/L5_engines/prediction_engine.py`
- `app/hoc/cus/analytics/L5_engines/prediction_read_engine.py`
- `app/hoc/cus/analytics/L5_engines/provenance.py`
- `app/hoc/cus/analytics/L5_engines/sandbox_engine.py`
- `app/hoc/cus/analytics/L5_engines/v2_adapter.py`
- `app/hoc/cus/analytics/L5_schemas/__init__.py`
- `app/hoc/cus/analytics/L5_schemas/cost_anomaly_dtos.py`
- `app/hoc/cus/analytics/L5_schemas/cost_anomaly_schemas.py`
- `app/hoc/cus/analytics/L5_schemas/cost_snapshot_schemas.py`
- `app/hoc/cus/analytics/L5_schemas/feedback_schemas.py`
- `app/hoc/cus/analytics/L5_schemas/query_types.py`
- `app/hoc/cus/analytics/L6_drivers/__init__.py`
- `app/hoc/cus/analytics/L6_drivers/analytics_read_driver.py`
- `app/hoc/cus/analytics/L6_drivers/canary_report_driver.py`
- `app/hoc/cus/analytics/L6_drivers/coordination_audit_driver.py`
- `app/hoc/cus/analytics/L6_drivers/cost_anomaly_driver.py`
- `app/hoc/cus/analytics/L6_drivers/cost_anomaly_read_driver.py`
- `app/hoc/cus/analytics/L6_drivers/cost_snapshots_driver.py`
- `app/hoc/cus/analytics/L6_drivers/cost_write_driver.py`
- `app/hoc/cus/analytics/L6_drivers/feedback_read_driver.py`
- `app/hoc/cus/analytics/L6_drivers/leader_driver.py`
- `app/hoc/cus/analytics/L6_drivers/pattern_detection_driver.py`
- `app/hoc/cus/analytics/L6_drivers/prediction_driver.py`
- `app/hoc/cus/analytics/L6_drivers/prediction_read_driver.py`
- `app/hoc/cus/analytics/L6_drivers/provenance_driver.py`
- `app/hoc/cus/analytics/adapters/__init__.py`

## Untouched in Exercise: logs

- `app/hoc/cus/logs/L5_engines/__init__.py`
- `app/hoc/cus/logs/L5_engines/audit_evidence.py`
- `app/hoc/cus/logs/L5_engines/audit_ledger_engine.py`
- `app/hoc/cus/logs/L5_engines/audit_reconciler.py`
- `app/hoc/cus/logs/L5_engines/certificate.py`
- `app/hoc/cus/logs/L5_engines/completeness_checker.py`
- `app/hoc/cus/logs/L5_engines/cost_intelligence_engine.py`
- `app/hoc/cus/logs/L5_engines/evidence_facade.py`
- `app/hoc/cus/logs/L5_engines/evidence_report.py`
- `app/hoc/cus/logs/L5_engines/logs_facade.py`
- `app/hoc/cus/logs/L5_engines/logs_read_engine.py`
- `app/hoc/cus/logs/L5_engines/mapper.py`
- `app/hoc/cus/logs/L5_engines/pdf_renderer.py`
- `app/hoc/cus/logs/L5_engines/redact.py`
- `app/hoc/cus/logs/L5_engines/replay_determinism.py`
- `app/hoc/cus/logs/L5_engines/trace_mismatch_engine.py`
- `app/hoc/cus/logs/L5_engines/traces_models.py`
- `app/hoc/cus/logs/L5_schemas/__init__.py`
- `app/hoc/cus/logs/L5_schemas/determinism_types.py`
- `app/hoc/cus/logs/L6_drivers/__init__.py`
- `app/hoc/cus/logs/L6_drivers/audit_ledger_driver.py`
- `app/hoc/cus/logs/L6_drivers/audit_ledger_read_driver.py`
- `app/hoc/cus/logs/L6_drivers/audit_ledger_write_driver_sync.py`
- `app/hoc/cus/logs/L6_drivers/bridges_driver.py`
- `app/hoc/cus/logs/L6_drivers/capture_driver.py`
- `app/hoc/cus/logs/L6_drivers/cost_intelligence_driver.py`
- `app/hoc/cus/logs/L6_drivers/cost_intelligence_sync_driver.py`
- `app/hoc/cus/logs/L6_drivers/export_bundle_store.py`
- `app/hoc/cus/logs/L6_drivers/idempotency_driver.py`
- `app/hoc/cus/logs/L6_drivers/integrity_driver.py`
- `app/hoc/cus/logs/L6_drivers/job_execution_driver.py`
- `app/hoc/cus/logs/L6_drivers/logs_domain_store.py`
- `app/hoc/cus/logs/L6_drivers/panel_consistency_driver.py`
- `app/hoc/cus/logs/L6_drivers/redact.py`
- `app/hoc/cus/logs/L6_drivers/replay_driver.py`
- `app/hoc/cus/logs/L6_drivers/trace_mismatch_driver.py`
- `app/hoc/cus/logs/L6_drivers/trace_store.py`
- `app/hoc/cus/logs/adapters/__init__.py`
- `app/hoc/cus/logs/adapters/customer_logs_adapter.py`

