# AgenticVerz 2.0 Repository Structure

**Generated:** 2025-12-30 UTC
**Commit:** $(git rev-parse --short HEAD)

---

## Overview

This document provides a comprehensive view of the AgenticVerz 2.0 codebase structure.

### Directory Legend

| Directory | Purpose | Layer |
|-----------|---------|-------|
| `backend/` | FastAPI backend, API routes, services | L2-L6 |
| `sdk/` | Python & JS SDKs | L3 |
| `website/` | Console UI & Landing page | L1 |
| `docs/` | Documentation, PINs, contracts | L7 |
| `scripts/` | Operations, CI, testing | L8 |
| `monitoring/` | Prometheus, Grafana configs | L7 |

---

## Full Structure (Level 4)

```
.
├── agentiverz_mn
│   ├── README.md
│   ├── auth_blocker_notes.md
│   ├── auth_integration_checklist.md
│   ├── demo_checklist.md
│   ├── m9_blueprint.md
│   ├── m9_checklist.md
│   ├── m9_postmortem.md
│   ├── milestone_plan.md
│   ├── repo_snapshot.md
│   └── sdk_packaging_checklist.md
├── artifacts
├── backend
│   ├── alembic
│   │   ├── versions
│   │   │   ├── 001_create_workflow_checkpoints.py
│   │   │   ├── 002_fix_status_enum.py
│   │   │   ├── 003_add_workflow_id_index.py
│   │   │   ├── 004_add_feature_flags_and_policy_approval.py
│   │   │   ├── 005_add_approval_requests.py
│   │   │   ├── 006_add_archival_partitioning.py
│   │   │   ├── 007_add_costsim_cb_state.py
│   │   │   ├── 008_add_provenance_and_alert_queue.py
│   │   │   ├── 009_create_memory_pins.py
│   │   │   ├── 010_create_rbac_audit.py
│   │   │   ├── 011_create_memory_audit.py
│   │   │   ├── 012_add_aos_traces_table.py
│   │   │   ├── 013_add_trace_retention_lifecycle.py
│   │   │   ├── 014_create_trace_mismatches.py
│   │   │   ├── 015_create_failure_matches.py
│   │   │   ├── 015b_harden_failure_matches.py
│   │   │   ├── 016_create_failure_pattern_exports.py
│   │   │   ├── 017_create_recovery_candidates.py
│   │   │   ├── 018_add_m10_recovery_enhancements.py
│   │   │   ├── 019_m10_recovery_enhancements.py
│   │   │   ├── 020_m10_concurrent_indexes.py
│   │   │   ├── 021_m10_durable_queue_fallback.py
│   │   │   ├── 022_m10_production_hardening.py
│   │   │   ├── 023_m10_archive_partitioning.py
│   │   │   ├── 024_m11_skill_audit.py
│   │   │   ├── 025_m12_agents_schema.py
│   │   │   ├── 026_m12_credit_tables_fix.py
│   │   │   ├── 027_m15_llm_governance.py
│   │   │   ├── 028_m15_1_sba_schema.py
│   │   │   ├── 029_m15_sba_validator.py
│   │   │   ├── 030_m17_care_routing.py
│   │   │   ├── 031_m18_care_l_sba_evolution.py
│   │   │   ├── 032_m19_policy_layer.py
│   │   │   ├── 033_m19_1_policy_gaps.py
│   │   │   ├── 034_fix_outbox_constraint.py
│   │   │   ├── 035_m10_schema_repair.py
│   │   │   ├── 036_m21_tenant_auth_billing.py
│   │   │   ├── 037_m22_killswitch.py
│   │   │   ├── 038_m24_ops_events.py
│   │   │   ├── 039_m23_user_tracking.py
│   │   │   ├── 040_m24_onboarding.py
│   │   │   ├── 041_fix_enqueue_work_constraint.py
│   │   │   ├── 042_m25_integration_loop.py
│   │   │   ├── 043_m25_learning_proof.py
│   │   │   ├── 044_m25_graduation_hardening.py
│   │   │   ├── 045_m25_policy_activation_audit.py
│   │   │   ├── 046_m26_cost_intelligence.py
│   │   │   ├── 047_m27_cost_snapshots.py
│   │   │   ├── 048_m29_anomaly_rules_alignment.py
│   │   │   ├── 049_decision_records.py
│   │   │   ├── 050_causal_binding.py
│   │   │   ├── 051_s4_run_failures.py
│   │   │   ├── 052_s6_trace_immutability.py
│   │   │   ├── 053_pb_s1_retry_immutability.py
│   │   │   ├── 054_merge_heads.py
│   │   │   ├── 055_pb_s2_crashed_status.py
│   │   │   ├── 056_pb_s3_pattern_feedback.py
│   │   │   ├── 057_pb_s4_policy_proposals.py
│   │   │   ├── 058_pb_s5_prediction_events.py
│   │   │   ├── 059_pc_discovery_ledger.py
│   │   │   ├── 060_c1_telemetry_plane.py
│   │   │   ├── 061_c2_prediction_hardening.py
│   │   │   ├── 062_c5_learning_suggestions.py
│   │   │   └── 063_c4_coordination_audit.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── app
│   │   ├── agents
│   │   │   ├── sba
│   │   │   ├── services
│   │   │   ├── skills
│   │   │   └── __init__.py
│   │   ├── api
│   │   │   ├── agents.py
│   │   │   ├── auth_helpers.py
│   │   │   ├── cost_guard.py
│   │   │   ├── cost_intelligence.py
│   │   │   ├── cost_ops.py
│   │   │   ├── costsim.py
│   │   │   ├── customer_visibility.py
│   │   │   ├── discovery.py
│   │   │   ├── embedding.py
│   │   │   ├── failures.py.m28_deleted
│   │   │   ├── feedback.py
│   │   │   ├── founder_actions.py
│   │   │   ├── founder_timeline.py
│   │   │   ├── guard.py
│   │   │   ├── health.py
│   │   │   ├── integration.py
│   │   │   ├── legacy_routes.py
│   │   │   ├── memory_pins.py
│   │   │   ├── onboarding.py
│   │   │   ├── operator.py.m28_deleted
│   │   │   ├── ops.py
│   │   │   ├── policy.py
│   │   │   ├── policy_layer.py
│   │   │   ├── policy_proposals.py
│   │   │   ├── predictions.py
│   │   │   ├── rbac_api.py
│   │   │   ├── recovery.py
│   │   │   ├── recovery_ingest.py
│   │   │   ├── runtime.py
│   │   │   ├── status_history.py
│   │   │   ├── tenants.py
│   │   │   ├── traces.py
│   │   │   ├── v1_killswitch.py
│   │   │   ├── v1_proxy.py
│   │   │   └── workers.py
│   │   ├── auth
│   │   │   ├── __init__.py
│   │   │   ├── clerk_provider.py
│   │   │   ├── console_auth.py
│   │   │   ├── jwt_auth.py
│   │   │   ├── oauth_providers.py
│   │   │   ├── oidc_provider.py
│   │   │   ├── rbac.py
│   │   │   ├── rbac_engine.py
│   │   │   ├── rbac_middleware.py
│   │   │   ├── role_mapping.py
│   │   │   ├── shadow_audit.py
│   │   │   ├── tenant_auth.py
│   │   │   └── tier_gating.py
│   │   ├── config
│   │   │   ├── __init__.py
│   │   │   ├── feature_flags.json
│   │   │   ├── flag_sync.py
│   │   │   ├── rbac_policies.json
│   │   │   └── secrets.py
│   │   ├── contracts
│   │   │   ├── __init__.py
│   │   │   ├── common.py
│   │   │   ├── decisions.py
│   │   │   ├── guard.py
│   │   │   └── ops.py
│   │   ├── costsim
│   │   │   ├── __init__.py
│   │   │   ├── alert_worker.py
│   │   │   ├── canary.py
│   │   │   ├── cb_sync_wrapper.py
│   │   │   ├── circuit_breaker.py
│   │   │   ├── circuit_breaker_async.py
│   │   │   ├── config.py
│   │   │   ├── datasets.py
│   │   │   ├── divergence.py
│   │   │   ├── leader.py
│   │   │   ├── metrics.py
│   │   │   ├── models.py
│   │   │   ├── provenance.py
│   │   │   ├── provenance_async.py
│   │   │   ├── sandbox.py
│   │   │   └── v2_adapter.py
│   │   ├── data
│   │   │   └── failure_catalog.json
│   │   ├── discovery
│   │   │   ├── __init__.py
│   │   │   └── ledger.py
│   │   ├── events
│   │   │   ├── __init__.py
│   │   │   ├── nats_adapter.py
│   │   │   ├── publisher.py
│   │   │   └── redis_publisher.py
│   │   ├── integrations
│   │   │   ├── __init__.py
│   │   │   ├── bridges.py
│   │   │   ├── cost_bridges.py
│   │   │   ├── cost_safety_rails.py
│   │   │   ├── cost_snapshots.py
│   │   │   ├── dispatcher.py
│   │   │   ├── events.py
│   │   │   ├── graduation_engine.py
│   │   │   ├── learning_proof.py
│   │   │   └── prevention_contract.py
│   │   ├── jobs
│   │   │   ├── __init__.py
│   │   │   ├── failure_aggregation.py
│   │   │   ├── graduation_evaluator.py
│   │   │   └── storage.py
│   │   ├── learning
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── s1_rollback.py
│   │   │   ├── suggestions.py
│   │   │   └── tables.py
│   │   ├── memory
│   │   │   ├── __init__.py
│   │   │   ├── drift_detector.py
│   │   │   ├── embedding_cache.py
│   │   │   ├── embedding_metrics.py
│   │   │   ├── iaec.py
│   │   │   ├── memory_service.py
│   │   │   ├── retriever.py
│   │   │   ├── store.py
│   │   │   ├── update_rules.py
│   │   │   └── vector_store.py
│   │   ├── middleware
│   │   │   ├── __init__.py
│   │   │   ├── rate_limit.py
│   │   │   ├── tenancy.py
│   │   │   └── tenant.py
│   │   ├── models
│   │   │   ├── __init__.py
│   │   │   ├── costsim_cb.py
│   │   │   ├── feedback.py
│   │   │   ├── killswitch.py
│   │   │   ├── m10_recovery.py
│   │   │   ├── policy.py
│   │   │   ├── prediction.py
│   │   │   └── tenant.py
│   │   ├── observability
│   │   │   └── cost_tracker.py
│   │   ├── optimization
│   │   │   ├── envelopes
│   │   │   ├── __init__.py
│   │   │   ├── audit_persistence.py
│   │   │   ├── coordinator.py
│   │   │   ├── envelope.py
│   │   │   ├── killswitch.py
│   │   │   └── manager.py
│   │   ├── planner
│   │   │   ├── __init__.py
│   │   │   ├── interface.py
│   │   │   └── stub_planner.py
│   │   ├── planners
│   │   │   ├── __init__.py
│   │   │   ├── anthropic_adapter.py
│   │   │   ├── stub_adapter.py
│   │   │   └── test_planners.py
│   │   ├── policy
│   │   │   ├── ast
│   │   │   ├── compiler
│   │   │   ├── ir
│   │   │   ├── optimizer
│   │   │   ├── runtime
│   │   │   ├── validators
│   │   │   ├── __init__.py
│   │   │   ├── engine.py
│   │   │   └── models.py
│   │   ├── predictions
│   │   │   ├── __init__.py
│   │   │   └── api.py
│   │   ├── routing
│   │   │   ├── __init__.py
│   │   │   ├── care.py
│   │   │   ├── feedback.py
│   │   │   ├── governor.py
│   │   │   ├── learning.py
│   │   │   ├── models.py
│   │   │   └── probes.py
│   │   ├── runtime
│   │   │   ├── failure_catalog.py
│   │   │   └── replay.py
│   │   ├── schemas
│   │   │   ├── examples
│   │   │   ├── __init__.py
│   │   │   ├── agent.py
│   │   │   ├── agent_profile.schema.json
│   │   │   ├── artifact.py
│   │   │   ├── failure_catalog.schema.json
│   │   │   ├── plan.py
│   │   │   ├── resource_contract.schema.json
│   │   │   ├── retry.py
│   │   │   ├── skill.py
│   │   │   ├── skill_metadata.schema.json
│   │   │   └── structured_outcome.schema.json
│   │   ├── secrets
│   │   │   ├── __init__.py
│   │   │   └── vault_client.py
│   │   ├── security
│   │   │   ├── __init__.py
│   │   │   └── sanitize.py
│   │   ├── services
│   │   │   ├── __init__.py
│   │   │   ├── certificate.py
│   │   │   ├── cost_anomaly_detector.py
│   │   │   ├── email_verification.py
│   │   │   ├── event_emitter.py
│   │   │   ├── evidence_report.py
│   │   │   ├── incident_aggregator.py
│   │   │   ├── llm_failure_service.py
│   │   │   ├── orphan_recovery.py
│   │   │   ├── pattern_detection.py
│   │   │   ├── policy_proposal.py
│   │   │   ├── policy_violation_service.py
│   │   │   ├── prediction.py
│   │   │   ├── recovery_matcher.py
│   │   │   ├── recovery_rule_engine.py
│   │   │   ├── replay_determinism.py
│   │   │   ├── scoped_execution.py
│   │   │   ├── tenant_service.py
│   │   │   └── worker_registry_service.py
│   │   ├── skills
│   │   │   ├── adapters
│   │   │   ├── contracts
│   │   │   ├── stubs
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── calendar_write.py
│   │   │   ├── email_send.py
│   │   │   ├── executor.py
│   │   │   ├── http_call.py
│   │   │   ├── http_call_v2.py
│   │   │   ├── json_transform.py
│   │   │   ├── json_transform_v2.py
│   │   │   ├── kv_store.py
│   │   │   ├── llm_invoke.py
│   │   │   ├── llm_invoke_v2.py
│   │   │   ├── postgres_query.py
│   │   │   ├── registry.py
│   │   │   ├── registry_v2.py
│   │   │   ├── slack_send.py
│   │   │   ├── voyage_embed.py
│   │   │   └── webhook_send.py
│   │   ├── specs
│   │   │   ├── canonical_json.md
│   │   │   ├── contract_compatibility.md
│   │   │   ├── determinism_and_replay.md
│   │   │   ├── error_contract.md
│   │   │   ├── error_taxonomy.md
│   │   │   ├── planner_determinism.md
│   │   │   └── recovery_modes.md
│   │   ├── storage
│   │   │   ├── __init__.py
│   │   │   └── artifact.py
│   │   ├── stores
│   │   │   ├── __init__.py
│   │   │   ├── checkpoint_offload.py
│   │   │   └── health.py
│   │   ├── tasks
│   │   │   ├── __init__.py
│   │   │   ├── m10_metrics_collector.py
│   │   │   ├── memory_update.py
│   │   │   ├── recovery_queue.py
│   │   │   └── recovery_queue_stream.py
│   │   ├── traces
│   │   │   ├── __init__.py
│   │   │   ├── idempotency.lua
│   │   │   ├── idempotency.py
│   │   │   ├── models.py
│   │   │   ├── pg_store.py
│   │   │   ├── redact.py
│   │   │   ├── replay.py
│   │   │   ├── store.py
│   │   │   └── traces_metrics.py
│   │   ├── utils
│   │   │   ├── __init__.py
│   │   │   ├── budget_tracker.py
│   │   │   ├── canonical_json.py
│   │   │   ├── concurrent_runs.py
│   │   │   ├── db_helpers.py
│   │   │   ├── deterministic.py
│   │   │   ├── guard_cache.py
│   │   │   ├── idempotency.py
│   │   │   ├── input_sanitizer.py
│   │   │   ├── metrics_helpers.py
│   │   │   ├── plan_inspector.py
│   │   │   ├── rate_limiter.py
│   │   │   ├── runtime.py
│   │   │   ├── schema_parity.py
│   │   │   └── webhook_verify.py
│   │   ├── worker
│   │   │   ├── runtime
│   │   │   ├── __init__.py
│   │   │   ├── outbox_processor.py
│   │   │   ├── pool.py
│   │   │   ├── recovery_claim_worker.py
│   │   │   ├── recovery_evaluator.py
│   │   │   ├── runner.py
│   │   │   └── simulate.py
│   │   ├── workers
│   │   │   └── business_builder
│   │   ├── workflow
│   │   │   ├── __init__.py
│   │   │   ├── canonicalize.py
│   │   │   ├── checkpoint.py
│   │   │   ├── engine.py
│   │   │   ├── errors.py
│   │   │   ├── external_guard.py
│   │   │   ├── golden.py
│   │   │   ├── health.py
│   │   │   ├── logging_context.py
│   │   │   ├── metrics.py
│   │   │   ├── planner_sandbox.py
│   │   │   └── policies.py
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── cli.py
│   │   ├── db.py
│   │   ├── db_async.py
│   │   ├── db_helpers.py
│   │   ├── logging_config.py
│   │   ├── main.py
│   │   ├── metrics.py
│   │   └── skill_http.py
│   ├── cli
│   │   ├── aos.py
│   │   └── aos_workflow.py
│   ├── data
│   │   └── reference_datasets
│   ├── examples
│   │   └── m12_parallel_scrape.py
│   ├── migrations
│   │   └── versions
│   │       └── 001_contracts_decision_records.py
│   ├── scripts
│   │   ├── ops
│   │   │   ├── check_redis_config.py
│   │   │   ├── m10_retention_cleanup.py
│   │   │   ├── reconcile_dl.py
│   │   │   └── refresh_matview.py
│   │   ├── verification
│   │   │   ├── s3_policy_violation_verification.py
│   │   │   ├── s4_llm_failure_truth_verification.py
│   │   │   ├── s4_llm_failure_verification.py
│   │   │   ├── s5_memory_injection_verification.py
│   │   │   └── s6_trace_integrity_verification.py
│   │   ├── backfill_memory_embeddings.py
│   │   ├── backfill_provenance.py
│   │   ├── benchmark_registry.py
│   │   ├── check_no_datetime_now.sh
│   │   ├── check_pydantic_config.sh
│   │   ├── deploy_migrations.sh
│   │   ├── golden_archival.py
│   │   ├── load_test_approvals.py
│   │   ├── mypy_zones.py
│   │   └── run_escalation.py
│   ├── static
│   │   └── openapi.json
│   ├── tests
│   │   ├── api
│   │   │   ├── __init__.py
│   │   │   └── test_policy_api.py
│   │   ├── auth
│   │   │   ├── __init__.py
│   │   │   ├── test_rbac_engine.py
│   │   │   ├── test_rbac_middleware.py
│   │   │   ├── test_rbac_path_mapping.py
│   │   │   └── test_role_mapping.py
│   │   ├── chaos
│   │   │   ├── __init__.py
│   │   │   ├── test_http_call_chaos.py
│   │   │   ├── test_llm_invoke_chaos.py
│   │   │   └── test_resource_stress.py
│   │   ├── ci
│   │   │   ├── __init__.py
│   │   │   └── test_no_external_calls.py
│   │   ├── contracts
│   │   │   ├── __init__.py
│   │   │   ├── test_g5b_policy_precheck.py
│   │   │   ├── test_g5c_recovery_automation.py
│   │   │   └── test_g5d_care_optimization.py
│   │   ├── costsim
│   │   │   ├── __init__.py
│   │   │   ├── test_alert_worker.py
│   │   │   ├── test_canary.py
│   │   │   ├── test_circuit_breaker.py
│   │   │   ├── test_circuit_breaker_async.py
│   │   │   ├── test_integration_real_db.py
│   │   │   └── test_leader.py
│   │   ├── e2e
│   │   │   └── test_m11_workflow.py
│   │   ├── fixtures
│   │   │   └── golden_trace.json
│   │   ├── golden
│   │   │   ├── execute_skill_echo.json
│   │   │   ├── execute_skill_not_found.json
│   │   │   ├── execute_timeout.json
│   │   │   ├── planner_error.json
│   │   │   ├── planner_multi_step.json
│   │   │   ├── planner_simple.json
│   │   │   ├── stub_http_call.json
│   │   │   ├── stub_json_transform.json
│   │   │   ├── stub_llm_invoke.json
│   │   │   └── workflow_multi_skill.json
│   │   ├── integration
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py
│   │   │   ├── test_circuit_breaker.py
│   │   │   ├── test_m7_rbac_memory.py
│   │   │   ├── test_memory_integration.py
│   │   │   ├── test_metrics_wiring.py
│   │   │   ├── test_rate_limit.py
│   │   │   ├── test_redis_budget_multiworker.py
│   │   │   ├── test_registry_snapshot.py
│   │   │   ├── test_replay_parity.py
│   │   │   └── test_vector_search.py
│   │   ├── learning
│   │   │   ├── __init__.py
│   │   │   └── test_s1_rollback.py
│   │   ├── legacy
│   │   │   ├── __init__.py
│   │   │   └── test_skills_legacy.py
│   │   ├── lit
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py
│   │   │   ├── test_l2_l3_api_adapter.py
│   │   │   └── test_l2_l6_api_platform.py
│   │   ├── live
│   │   │   ├── __init__.py
│   │   │   └── test_claude_live.py
│   │   ├── memory
│   │   │   ├── __init__.py
│   │   │   ├── test_drift_detector.py
│   │   │   └── test_memory_service.py
│   │   ├── observability
│   │   │   ├── __init__.py
│   │   │   └── test_cost_tracker.py
│   │   ├── optimization
│   │   │   ├── __init__.py
│   │   │   ├── test_c3_failure_scenarios.py
│   │   │   ├── test_c3_s2_cost_smoothing.py
│   │   │   ├── test_c3_s3_failure_matrix.py
│   │   │   └── test_c4_s1_coordination.py
│   │   ├── planner
│   │   │   ├── __init__.py
│   │   │   ├── test_determinism_stress.py
│   │   │   └── test_interface.py
│   │   ├── quota
│   │   │   ├── __init__.py
│   │   │   └── test_quota_exhaustion.py
│   │   ├── replay
│   │   │   └── test_replay_end_to_end.py
│   │   ├── runtime
│   │   │   ├── __init__.py
│   │   │   ├── test_invariants.py
│   │   │   ├── test_m1_runtime.py
│   │   │   ├── test_runtime_determinism.py
│   │   │   └── test_runtime_interfaces.py
│   │   ├── schemas
│   │   │   ├── __init__.py
│   │   │   └── test_m0_schemas.py
│   │   ├── skills
│   │   │   ├── __init__.py
│   │   │   ├── test_claude_adapter.py
│   │   │   ├── test_email_send.py
│   │   │   ├── test_executor.py
│   │   │   ├── test_http_call_v2.py
│   │   │   ├── test_json_transform_v2.py
│   │   │   ├── test_llm_invoke_v2.py
│   │   │   ├── test_m11_skills.py
│   │   │   ├── test_m3_integration.py
│   │   │   ├── test_registry_load.py
│   │   │   ├── test_registry_v2.py
│   │   │   ├── test_stub_replay.py
│   │   │   └── test_stubs.py
│   │   ├── snapshots
│   │   │   └── ops_api_contracts.json
│   │   ├── workflow
│   │   │   ├── __init__.py
│   │   │   ├── test_checkpoint_store.py
│   │   │   ├── test_engine_smoke.py
│   │   │   ├── test_golden_lifecycle.py
│   │   │   ├── test_lifecycle_kill_resume.py
│   │   │   ├── test_m4_hardening.py
│   │   │   ├── test_multi_skill_workflow.py
│   │   │   ├── test_nightly_golden_stress.py
│   │   │   ├── test_observability.py
│   │   │   ├── test_p0_fixes.py
│   │   │   ├── test_replay_certification.py
│   │   │   └── test_workflow_golden_pipeline.py
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── acceptance_runtime.md
│   │   ├── conftest.py
│   │   ├── registry_snapshot.json
│   │   ├── test_business_builder_worker.py
│   │   ├── test_category2_auth_boundary.py
│   │   ├── test_category3_data_contracts.py
│   │   ├── test_category4_cost_intelligence.py
│   │   ├── test_category5_absence.py
│   │   ├── test_category5_incident_contrast.py
│   │   ├── test_category6_founder_actions.py
│   │   ├── test_category7_legacy_routes.py
│   │   ├── test_cost_simulator.py
│   │   ├── test_determinism_invariant.py
│   │   ├── test_failure_catalog.py
│   │   ├── test_failure_catalog_m9.py
│   │   ├── test_integration.py
│   │   ├── test_m10_leader_election.py
│   │   ├── test_m10_metrics.py
│   │   ├── test_m10_outbox_e2e.py
│   │   ├── test_m10_production_hardening.py
│   │   ├── test_m10_recovery_chaos.py
│   │   ├── test_m10_recovery_enhanced.py
│   │   ├── test_m12_agents.py
│   │   ├── test_m12_chaos.py
│   │   ├── test_m12_integration.py
│   │   ├── test_m12_load.py
│   │   ├── test_m13_iterations_cost.py
│   │   ├── test_m13_prompt_cache.py
│   │   ├── test_m17_care.py
│   │   ├── test_m18_advanced.py
│   │   ├── test_m18_care_l.py
│   │   ├── test_m19_policy.py
│   │   ├── test_m20_ir.py
│   │   ├── test_m20_optimizer.py
│   │   ├── test_m20_parser.py
│   │   ├── test_m20_runtime.py
│   │   ├── test_m22_killswitch.py
│   │   ├── test_m24_ops_console.py
│   │   ├── test_m24_prevention.py
│   │   ├── test_m25_graduation_downgrade.py
│   │   ├── test_m25_graduation_gates.py
│   │   ├── test_m25_integration_loop.py
│   │   ├── test_m25_policy_overreach.py
│   │   ├── test_m26_prevention.py
│   │   ├── test_m27_cost_loop.py
│   │   ├── test_pb_s1_behavioral_invariants.py
│   │   ├── test_pb_s1_bypass_detection.py
│   │   ├── test_pb_s1_invariants.py
│   │   ├── test_pb_s2_crash_recovery.py
│   │   ├── test_pb_s3_feedback_loops.py
│   │   ├── test_pb_s4_policy_evolution.py
│   │   ├── test_pb_s5_prediction.py
│   │   ├── test_phase4_e2e.py
│   │   ├── test_phase5_security.py
│   │   ├── test_phase5a_governance.py
│   │   ├── test_recovery.py
│   │   ├── test_route_contracts.py
│   │   ├── test_tier_gating.py
│   │   └── test_worker_pool.py
│   ├── tools
│   │   ├── mypy_autofix
│   │   │   ├── README.md
│   │   │   ├── __init__.py
│   │   │   ├── apply.py
│   │   │   ├── macros.py
│   │   │   └── rules.yaml
│   │   └── replay
│   │       ├── __init__.py
│   │       ├── audit.py
│   │       ├── runner.py
│   │       └── verifier.py
│   ├── Dockerfile
│   ├── Dockerfile.test
│   ├── Makefile
│   ├── PYTHON_EXECUTION_CONTRACT.md
│   ├── alembic.ini
│   ├── docker-compose.test.yml
│   ├── pyproject.toml
│   └── requirements.txt
├── backups
│   ├── m7_pre_enable_20251205T044346Z.dump
│   ├── m7_pre_enable_20251205T052016Z.dump
│   ├── nova_aos_20251204_045856.dump
│   └── nova_aos_pre_neon.dump
├── budgetllm
│   ├── core
│   │   ├── backends
│   │   │   ├── __init__.py
│   │   │   ├── memory.py
│   │   │   └── redis.py
│   │   ├── __init__.py
│   │   ├── budget.py
│   │   ├── cache.py
│   │   ├── client.py
│   │   ├── output_analysis.py
│   │   ├── prompt_classifier.py
│   │   ├── risk_formula.py
│   │   └── safety.py
│   ├── tests
│   │   ├── __init__.py
│   │   ├── test_budgetllm.py
│   │   ├── test_openai_compat.py
│   │   └── test_safety_governance.py
│   ├── LICENSE
│   ├── README.md
│   ├── __init__.py
│   ├── py.typed
│   └── pyproject.toml
├── config
│   └── pgbouncer
│       ├── pgbouncer.ini
│       └── userlist.txt
├── deploy
│   ├── nginx
│   │   └── aos-console.conf
│   └── systemd
│       ├── agenticverz-failure-aggregation.service
│       ├── agenticverz-failure-aggregation.timer
│       ├── agenticverz-r2-retry.service
│       ├── agenticverz-r2-retry.timer
│       ├── aos-cost-snapshot-daily.service
│       ├── aos-cost-snapshot-daily.timer
│       ├── aos-cost-snapshot-hourly.service
│       └── aos-cost-snapshot-hourly.timer
├── deployment
│   ├── redis
│   │   └── redis-m10-durable.conf
│   └── systemd
│       ├── m10-daily-stats.service
│       ├── m10-daily-stats.timer
│       ├── m10-maintenance.service
│       ├── m10-maintenance.timer
│       ├── m10-metrics-collector.service
│       ├── m10-synthetic-traffic.service
│       └── m10-synthetic-traffic.timer
├── docs
│   ├── architecture
│   │   ├── ARCHITECTURE_INCIDENT_TAXONOMY.md
│   │   └── console-slice-mapping.md
│   ├── behavior
│   │   ├── behavior_library.json
│   │   └── behavior_library.yaml
│   ├── certification
│   │   ├── C1_CERTIFICATION_STATEMENT.md
│   │   └── C1_HUMAN_UI_VERIFICATION.md
│   ├── certifications
│   │   ├── C2_CERTIFICATION_STATEMENT.md
│   │   ├── C3_CERTIFICATION_STATEMENT.md
│   │   ├── C4_CERTIFICATION_STATEMENT.md
│   │   ├── C5_S1_CERTIFICATION_STATEMENT.md
│   │   └── INDEX.md
│   ├── checklists
│   │   └── M12-PRODUCTION-ENABLEMENT.md
│   ├── codebase-registry
│   │   ├── artifacts
│   │   │   ├── AOS-BE-API-COP-001.yaml
│   │   │   ├── AOS-BE-API-CSM-001.yaml
│   │   │   ├── AOS-BE-API-CST-001.yaml
│   │   │   ├── AOS-BE-API-CVS-001.yaml
│   │   │   ├── AOS-BE-API-DSC-001.yaml
│   │   │   ├── AOS-BE-API-EMB-001.yaml
│   │   │   ├── AOS-BE-API-FBK-001.yaml
│   │   │   ├── AOS-BE-API-FND-001.yaml
│   │   │   ├── AOS-BE-API-FTL-001.yaml
│   │   │   ├── AOS-BE-API-GRD-001.yaml
│   │   │   ├── AOS-BE-API-HLT-001.yaml
│   │   │   ├── AOS-BE-API-INT-001.yaml
│   │   │   ├── AOS-BE-API-KSW-001.yaml
│   │   │   ├── AOS-BE-API-LGC-001.yaml
│   │   │   ├── AOS-BE-API-MEM-001.yaml
│   │   │   ├── AOS-BE-API-ONB-001.yaml
│   │   │   ├── AOS-BE-API-OPS-001.yaml
│   │   │   ├── AOS-BE-API-PLY-001.yaml
│   │   │   ├── AOS-BE-API-POL-001.yaml
│   │   │   ├── AOS-BE-API-PPR-001.yaml
│   │   │   ├── AOS-BE-API-PRD-001.yaml
│   │   │   ├── AOS-BE-API-RBC-001.yaml
│   │   │   ├── AOS-BE-API-RCV-001.yaml
│   │   │   ├── AOS-BE-API-RTM-001.yaml
│   │   │   ├── AOS-BE-API-STH-001.yaml
│   │   │   ├── AOS-BE-API-TNT-001.yaml
│   │   │   ├── AOS-BE-API-TRC-001.yaml
│   │   │   ├── AOS-BE-API-WRK-001.yaml
│   │   │   ├── AOS-BE-MEM-VEC-001.yaml
│   │   │   ├── AOS-BE-SVC-BBD-001.yaml
│   │   │   ├── AOS-BE-SVC-CAD-001.yaml
│   │   │   ├── AOS-BE-SVC-CRD-001.yaml
│   │   │   ├── AOS-BE-SVC-CRT-001.yaml
│   │   │   ├── AOS-BE-SVC-EML-001.yaml
│   │   │   ├── AOS-BE-SVC-EMT-001.yaml
│   │   │   ├── AOS-BE-SVC-EVD-001.yaml
│   │   │   ├── AOS-BE-SVC-EVT-001.yaml
│   │   │   ├── AOS-BE-SVC-GOV-001.yaml
│   │   │   ├── AOS-BE-SVC-IAD-001.yaml
│   │   │   ├── AOS-BE-SVC-INC-001.yaml
│   │   │   ├── AOS-BE-SVC-JOB-001.yaml
│   │   │   ├── AOS-BE-SVC-LLF-001.yaml
│   │   │   ├── AOS-BE-SVC-MEM-001.yaml
│   │   │   ├── AOS-BE-SVC-MSG-001.yaml
│   │   │   ├── AOS-BE-SVC-ORP-001.yaml
│   │   │   ├── AOS-BE-SVC-PPL-001.yaml
│   │   │   ├── AOS-BE-SVC-PRD-001.yaml
│   │   │   ├── AOS-BE-SVC-PTN-001.yaml
│   │   │   ├── AOS-BE-SVC-PVS-001.yaml
│   │   │   ├── AOS-BE-SVC-REG-001.yaml
│   │   │   ├── AOS-BE-SVC-RMT-001.yaml
│   │   │   ├── AOS-BE-SVC-RPD-001.yaml
│   │   │   ├── AOS-BE-SVC-RRE-001.yaml
│   │   │   ├── AOS-BE-SVC-SCE-001.yaml
│   │   │   ├── AOS-BE-SVC-SEC-001.yaml
│   │   │   ├── AOS-BE-SVC-TNT-001.yaml
│   │   │   ├── AOS-BE-SVC-WKS-001.yaml
│   │   │   ├── AOS-BE-SVC-WRG-001.yaml
│   │   │   ├── AOS-BE-TST-QTA-001.yaml
│   │   │   ├── AOS-BE-WKR-OBX-001.yaml
│   │   │   ├── AOS-BE-WKR-POL-001.yaml
│   │   │   ├── AOS-BE-WKR-RCC-001.yaml
│   │   │   ├── AOS-BE-WKR-RCE-001.yaml
│   │   │   ├── AOS-BE-WKR-RUN-001.yaml
│   │   │   ├── AOS-CLI-AOS-001.yaml
│   │   │   ├── AOS-FE-AIC-ACC-001.yaml
│   │   │   ├── AOS-FE-AIC-ACC-002.yaml
│   │   │   ├── AOS-FE-AIC-ACC-003.yaml
│   │   │   ├── AOS-FE-AIC-ACT-001.yaml
│   │   │   ├── AOS-FE-AIC-INC-001.yaml
│   │   │   ├── AOS-FE-AIC-INC-002.yaml
│   │   │   ├── AOS-FE-AIC-INC-003.yaml
│   │   │   ├── AOS-FE-AIC-INC-004.yaml
│   │   │   ├── AOS-FE-AIC-INC-005.yaml
│   │   │   ├── AOS-FE-AIC-INT-001.yaml
│   │   │   ├── AOS-FE-AIC-INT-002.yaml
│   │   │   ├── AOS-FE-AIC-LOG-001.yaml
│   │   │   ├── AOS-FE-AIC-OVR-001.yaml
│   │   │   ├── AOS-FE-AIC-POL-001.yaml
│   │   │   ├── AOS-FE-AIC-SYS-001.yaml
│   │   │   ├── AOS-FE-AIC-SYS-002.yaml
│   │   │   ├── AOS-FE-AIC-SYS-003.yaml
│   │   │   ├── AOS-IF-MON-DSH-001.yaml
│   │   │   ├── AOS-LIB-BLL-BGT-001.yaml
│   │   │   ├── AOS-LIB-BLL-BMM-001.yaml
│   │   │   ├── AOS-LIB-BLL-BRD-001.yaml
│   │   │   ├── AOS-LIB-BLL-CCH-001.yaml
│   │   │   ├── AOS-LIB-BLL-CLT-001.yaml
│   │   │   ├── AOS-LIB-BLL-OAN-001.yaml
│   │   │   ├── AOS-LIB-BLL-PCL-001.yaml
│   │   │   ├── AOS-LIB-BLL-RSK-001.yaml
│   │   │   ├── AOS-LIB-BLL-SFT-001.yaml
│   │   │   ├── AOS-OP-CHS-CPU-001.yaml
│   │   │   ├── AOS-OP-CHS-MEM-001.yaml
│   │   │   ├── AOS-OP-CHS-RDS-001.yaml
│   │   │   ├── AOS-OP-CI-SYN-001.yaml
│   │   │   ├── AOS-OP-DOC-CFG-001.yaml
│   │   │   ├── AOS-OP-DOC-RNB-001.yaml
│   │   │   ├── AOS-OP-DOC-RNB-002.yaml
│   │   │   ├── AOS-OP-DPL-CON-001.yaml
│   │   │   ├── AOS-OP-INT-E2E-001.yaml
│   │   │   ├── AOS-OP-OPS-ALK-001.yaml
│   │   │   ├── AOS-OP-OPS-CHR-001.yaml
│   │   │   ├── AOS-OP-OPS-CRV-001.yaml
│   │   │   ├── AOS-OP-OPS-HYG-001.yaml
│   │   │   ├── AOS-OP-OPS-M10-001.yaml
│   │   │   ├── AOS-OP-OPS-MTL-001.yaml
│   │   │   ├── AOS-OP-OPS-PFL-001.yaml
│   │   │   ├── AOS-OP-OPS-PST-001.yaml
│   │   │   ├── AOS-OP-OPS-RBC-001.yaml
│   │   │   ├── AOS-OP-OPS-SST-001.yaml
│   │   │   ├── AOS-OP-SMK-RBC-001.yaml
│   │   │   ├── AOS-OP-STR-FLT-001.yaml
│   │   │   ├── AOS-OP-STR-GLD-001.yaml
│   │   │   ├── AOS-OP-TLS-PDR-001.yaml
│   │   │   ├── AOS-OP-VRF-TIS-001.yaml
│   │   │   ├── AOS-OP-VRF-TPF-001.yaml
│   │   │   ├── AOS-SDK-JS-AOS-001.yaml
│   │   │   ├── AOS-SDK-JS-NVA-001.yaml
│   │   │   ├── AOS-SDK-PY-AOS-001.yaml
│   │   │   └── AOS-SDK-PY-NVA-001.yaml
│   │   ├── changes
│   │   │   ├── CHANGE-2025-0001.yaml
│   │   │   └── CHANGE-2025-0002.yaml
│   │   ├── CODEBASE_INVENTORY.md
│   │   ├── README.md
│   │   ├── SURVEY_BACKLOG.md
│   │   ├── SURVEY_REPORT.md
│   │   ├── UNKNOWN_TRIAGE.md
│   │   ├── artifact-intent-schema.yaml
│   │   ├── change-schema-v1.yaml
│   │   └── schema-v1.yaml
│   ├── console
│   │   ├── CONSOLE_MAPPING_TABLE_V1.md
│   │   ├── KNOWN_GAPS_CUSTOMER_CONSOLE_V1.md
│   │   ├── TERMINOLOGY_IMPLEMENTATION_SYNTHESIS_V1.md
│   │   ├── TERMINOLOGY_NORMALIZATION_MAP_V1.md
│   │   └── TOPOLOGY_AUDIT_CUSTOMER_CONSOLE_V1.md
│   ├── contracts
│   │   ├── C3_ENVELOPE_ABSTRACTION.md
│   │   ├── C3_KILLSWITCH_ROLLBACK_MODEL.md
│   │   ├── C3_OPTIMIZATION_SAFETY_CONTRACT.md
│   │   ├── C4_CI_GUARDRAILS_DESIGN.md
│   │   ├── C4_COORDINATION_AUDIT_SCHEMA.md
│   │   ├── C4_ENVELOPE_COORDINATION_CONTRACT.md
│   │   ├── C4_FOUNDER_STABILITY_CRITERIA.md
│   │   ├── C4_OPERATIONAL_STABILITY_CRITERIA.md
│   │   ├── C4_PAPER_SIMULATION_RECORD.md
│   │   ├── C4_RECERTIFICATION_RULES.md
│   │   ├── C4_S1_COORDINATION_SCENARIO.md
│   │   ├── C4_STABILITY_EVIDENCE_PACK.md
│   │   ├── C4_STABILITY_EVIDENCE_PACK_20251228.md
│   │   ├── C4_SYNTHETIC_STABILITY_RUNBOOK.md
│   │   ├── C4_SYSTEM_LEARNINGS.md
│   │   ├── C5_CI_GUARDRAILS_DESIGN.md
│   │   ├── C5_S1_ACCEPTANCE_CRITERIA.md
│   │   ├── C5_S1_CI_ENFORCEMENT.md
│   │   ├── C5_S1_LEARNING_SCENARIO.md
│   │   ├── C5_S2_ACCEPTANCE_CRITERIA.md
│   │   ├── C5_S2_LEARNING_SCENARIO.md
│   │   ├── C5_S3_ACCEPTANCE_CRITERIA.md
│   │   ├── C5_S3_LEARNING_SCENARIO.md
│   │   ├── CODE_EVOLUTION_CONTRACT.md
│   │   ├── CONSOLE_TRUTH_MODEL.md
│   │   ├── CONSTRAINT_DECLARATION_CONTRACT.md
│   │   ├── COVERAGE_MATRIX.md
│   │   ├── CUSTOMER_CONSOLE_V1_CONSTITUTION.md
│   │   ├── DECISION_RECORD_CONTRACT.md
│   │   ├── INDEX.md
│   │   ├── INTEGRATION_INTEGRITY_CONTRACT.md
│   │   ├── M0_M27_CLASSIFICATION.md
│   │   ├── O4_ADVISORY_UI_CONTRACT.md
│   │   ├── O4_RECERTIFICATION_CHECKS.md
│   │   ├── O4_UI_ACCEPTANCE_CRITERIA.md
│   │   ├── O4_UI_COPY_BLOCKS.md
│   │   ├── O4_UI_WIREFRAMES.md
│   │   ├── OBLIGATION_DELTAS.md
│   │   ├── OUTCOME_RECONCILIATION_CONTRACT.md
│   │   ├── PHASE_5_PLAN.md
│   │   ├── PRE_RUN_CONTRACT.md
│   │   ├── PRODUCT_BOUNDARY_CONTRACT.md
│   │   ├── PROTECTIVE_GOVERNANCE_CONTRACT.md
│   │   ├── TEMPORAL_INTEGRITY_CONTRACT.md
│   │   ├── database_contract.yaml
│   │   ├── discovery_ledger.yaml
│   │   ├── visibility_contract.yaml
│   │   └── visibility_lifecycle.yaml
│   ├── demo
│   │   ├── DEMO_TALK_TRACK.md
│   │   ├── LOCKED_NARRATIVE.md
│   │   └── PDF_EVIDENCE_REPORT_SPEC.md
│   ├── deployment
│   │   └── EMAIL_PROVIDER_CONFIGURATION.md
│   ├── execution
│   │   └── API_CALL_TEMPLATE.md
│   ├── incidents
│   │   └── CI_FAILURE_ANALYSIS_20251207.md
│   ├── internal
│   │   └── HOW_M25_WORKS.md
│   ├── legal
│   │   └── DATA_HANDLING_TOS_SECTION.md
│   ├── memory-pins
│   │   ├── INDEX.md
│   │   ├── PB-S1-FROZEN.md
│   │   ├── PENDING-TODO-INDEX.md
│   │   ├── PIN-001-aos-roadmap-status.md
│   │   ├── PIN-002-critical-review.md
│   │   ├── PIN-003-phase3-completion.md
│   │   ├── PIN-004-phase4-phase5-completion.md
│   │   ├── PIN-005-machine-native-architecture.md
│   │   ├── PIN-006-execution-plan-review.md
│   │   ├── PIN-007-v1-milestone-plan.md
│   │   ├── PIN-008-v1-milestone-plan-full.md
│   │   ├── PIN-009-m0-finalization-report.md
│   │   ├── PIN-010-m2-completion-report.md
│   │   ├── PIN-011-m2.5-hardening-report.md
│   │   ├── PIN-012-m3-m35-completion-m4-prep.md
│   │   ├── PIN-013-m4-workflow-engine-completion.md
│   │   ├── PIN-014-m4-technical-review.md
│   │   ├── PIN-015-completion-template.md
│   │   ├── PIN-015-m4-validation-maturity-gates.md
│   │   ├── PIN-016-m4-ops-tooling-runbook.md
│   │   ├── PIN-017-m4-monitoring-infrastructure.md
│   │   ├── PIN-018-m4-incident-ops-readiness.md
│   │   ├── PIN-019-aos-brainstorm-revised-milestones.md
│   │   ├── PIN-020-m4-final-signoff.md
│   │   ├── PIN-021-m5-policy-api-completion.md
│   │   ├── PIN-022-m5-ops-deployment-session.md
│   │   ├── PIN-023-comprehensive-feedback-analysis.md
│   │   ├── PIN-024-m6-specification.md
│   │   ├── PIN-025-m6-implementation-plan.md
│   │   ├── PIN-026-m6-implementation-complete.md
│   │   ├── PIN-027-m6-critical-fixes.md
│   │   ├── PIN-028-m6-critical-gaps-fixes.md
│   │   ├── PIN-029-infra-hardening-ci-fixes.md
│   │   ├── PIN-030-m6.5-webhook-externalization.md
│   │   ├── PIN-031-m7-memory-integration.md
│   │   ├── PIN-032-m7-rbac-enablement.md
│   │   ├── PIN-033-m8-m14-machine-native-realignment.md
│   │   ├── PIN-034-vault-secrets-management.md
│   │   ├── PIN-035-sdk-package-registry.md
│   │   ├── PIN-036-EXTERNAL-SERVICES.md
│   │   ├── PIN-036-infrastructure-pending.md
│   │   ├── PIN-037-grafana-cloud-integration.md
│   │   ├── PIN-038-upstash-redis-integration.md
│   │   ├── PIN-039-m8-implementation-progress.md
│   │   ├── PIN-040-rate-limit-middleware.md
│   │   ├── PIN-041-mismatch-tracking-system.md
│   │   ├── PIN-042-alert-observability-tooling.md
│   │   ├── PIN-043-m8-infrastructure-session.md
│   │   ├── PIN-044-e2e-test-harness-run.md
│   │   ├── PIN-045-ci-infrastructure-fixes.md
│   │   ├── PIN-046-stub-replacement-pgvector.md
│   │   ├── PIN-047-pending-polishing-tasks.md
│   │   ├── PIN-048-m9-failure-catalog-completion.md
│   │   ├── PIN-049-r2-durable-storage.md
│   │   ├── PIN-050-m10-recovery-suggestion-engine-complete.md
│   │   ├── PIN-051-vision-mission-assessment.md
│   │   ├── PIN-052-data-ownership-embedding-risks.md
│   │   ├── PIN-053-mock-inventory-real-world-plugins.md
│   │   ├── PIN-054-engineering-audit-finops.md
│   │   ├── PIN-055-m11-store-factories-implementation.md
│   │   ├── PIN-056-m11-production-hardening.md
│   │   ├── PIN-057-m10-recovery-enhancement.md
│   │   ├── PIN-058-m10-simplification-analysis.md
│   │   ├── PIN-059-m11-skill-expansion-blueprint.md
│   │   ├── PIN-060-m11-implementation-report.md
│   │   ├── PIN-061-m10-test-verification.md
│   │   ├── PIN-062-m12-multi-agent-system.md
│   │   ├── PIN-063-m12.1-stabilization.md
│   │   ├── PIN-064-m13-boundary-checklist.md
│   │   ├── PIN-065-aos-system-reference.md
│   │   ├── PIN-066-external-api-keys-integrations.md
│   │   ├── PIN-067-m13-iterations-cost-fix.md
│   │   ├── PIN-068-m13-prompt-caching.md
│   │   ├── PIN-069-budgetllm-go-to-market-plan.md
│   │   ├── PIN-070-budgetllm-safety-governance.md
│   │   ├── PIN-071-m15-budgetllm-a2a-integration.md
│   │   ├── PIN-072-m15-1-sba-foundations.md
│   │   ├── PIN-073-m15-1-1-sba-inspector-ui.md
│   │   ├── PIN-074-m16-strategybound-governance-console.md
│   │   ├── PIN-075-m17-care-routing-engine.md
│   │   ├── PIN-076-m18-care-l-sba-evolution.md
│   │   ├── PIN-077-m18-3-metrics-dashboard.md
│   │   ├── PIN-078-m19-policy-layer.md
│   │   ├── PIN-079-ci-ephemeral-neon-fixes.md
│   │   ├── PIN-080-ci-consistency-checker-v41.md
│   │   ├── PIN-081-mn-os-naming-evolution.md
│   │   ├── PIN-082-iaec-v2-embedding-composer.md
│   │   ├── PIN-083-iaec-v4-frontier-challenges.md
│   │   ├── PIN-084-m20-policy-compiler-runtime.md
│   │   ├── PIN-085-worker-brainstorm-moat-audit.md
│   │   ├── PIN-086-business-builder-worker-v02.md
│   │   ├── PIN-087-business-builder-api-hosting.md
│   │   ├── PIN-088-worker-execution-console.md
│   │   ├── PIN-089-m21-tenant-auth-billing.md
│   │   ├── PIN-090-worker-console-llm-integration.md
│   │   ├── PIN-091-artifact-identity-placement.md
│   │   ├── PIN-092-sse-lifecycle-hardening.md
│   │   ├── PIN-093-worker-v03-real-moat-integration.md
│   │   ├── PIN-094-build-your-app-landing-page.md
│   │   ├── PIN-095-ai-incident-console-strategy.md
│   │   ├── PIN-096-m22-killswitch-mvp.md
│   │   ├── PIN-097-prevention-system-v1.md
│   │   ├── PIN-098-m22.1-ui-console-implementation.md
│   │   ├── PIN-099-sqlmodel-row-extraction-patterns.md
│   │   ├── PIN-100-m23-ai-incident-console-production.md
│   │   ├── PIN-101-website-cluster-restructure.md
│   │   ├── PIN-102-m23-production-infrastructure.md
│   │   ├── PIN-103-m23-survival-stack.md
│   │   ├── PIN-104-organic-traction-strategy.md
│   │   ├── PIN-105-ops-console-founder-intelligence.md
│   │   ├── PIN-106-sqlmodel-linter-fixes.md
│   │   ├── PIN-107-m24-phase2-friction-intel.md
│   │   ├── PIN-108-developer-tooling-preflight-postflight.md
│   │   ├── PIN-109-preflight-postflight-v2.md
│   │   ├── PIN-110-enhanced-compute-stickiness-job.md
│   │   ├── PIN-111-founder-ops-console-ui.md
│   │   ├── PIN-112-compute-stickiness-scheduler.md
│   │   ├── PIN-113-memory-trail-automation-system.md
│   │   ├── PIN-114-m23-guard-console-health-prevention.md
│   │   ├── PIN-115-guard-console-8-phase-implementation.md
│   │   ├── PIN-116-guard-console-latency-optimization.md
│   │   ├── PIN-117-evidence-report-enhancements.md
│   │   ├── PIN-118-m24-customer-onboarding.md
│   │   ├── PIN-119-sqlmodel-session-safety.md
│   │   ├── PIN-120-test-suite-stabilization-prevention.md
│   │   ├── PIN-121-mypy-technical-debt.md
│   │   ├── PIN-122-master-milestone-compendium-m0-m21.md
│   │   ├── PIN-123-strategic-product-plan-2025.md
│   │   ├── PIN-124-unified-identity-hybrid-architecture.md
│   │   ├── PIN-125-sdk-parity-ci-fix-prevention.md
│   │   ├── PIN-126-test-infrastructure-prevention-blueprint.md
│   │   ├── PIN-127-replay-determinism-proof.md
│   │   ├── PIN-128-master-plan-m25-m32.md
│   │   ├── PIN-129-m25-pillar-integration-blueprint.md
│   │   ├── PIN-130-m25-code-freeze-declaration.md
│   │   ├── PIN-130-m26-cost-intelligence-blueprint.md
│   │   ├── PIN-131-m25-evidence-trail-protocol.md
│   │   ├── PIN-131-m27-cost-loop-integration-blueprint.md
│   │   ├── PIN-132-m26-hygiene-gate-checklist.md
│   │   ├── PIN-132-m28-unified-console-blueprint.md
│   │   ├── PIN-133-m29-quality-score-blueprint.md
│   │   ├── PIN-134-m30-trust-badge-blueprint.md
│   │   ├── PIN-135-m25-integration-loop-wiring.md
│   │   ├── PIN-136-m25-prevention-contract.md
│   │   ├── PIN-137-m25-stabilization-freeze.md
│   │   ├── PIN-138-m28-console-structure-audit.md
│   │   ├── PIN-139-m27-cost-loop-integration.md
│   │   ├── PIN-140-m25-complete-rollback-safe.md
│   │   ├── PIN-141-m26-cost-intelligence.md
│   │   ├── PIN-142-secrets-env-contract.md
│   │   ├── PIN-143-m27-real-cost-enforcement-proof.md
│   │   ├── PIN-144-m271-cost-snapshot-barrier.md
│   │   ├── PIN-145-m28-deletion-execution-report.md
│   │   ├── PIN-146-m28-unified-console-ui.md
│   │   ├── PIN-147-m28-route-migration-plan.md
│   │   ├── PIN-148-m29-categorical-next-steps.md
│   │   ├── PIN-149-category2-auth-boundary-full-spec.md
│   │   ├── PIN-150-category3-data-contract-freeze-full-spec.md
│   │   ├── PIN-151-m29-category-4---cost-intelligence-completion.md
│   │   ├── PIN-152-m29-category-6---founder-action-paths-backend.md
│   │   ├── PIN-153-m29-category-7---redirect-expiry-cleanup.md
│   │   ├── PIN-154-m31-key-safety-contract-blueprint.md
│   │   ├── PIN-155-m32-tier-infrastructure-blueprint.md
│   │   ├── PIN-156-landing-page-identity-guidelines.md
│   │   ├── PIN-157-numeric-pricing-anchors.md
│   │   ├── PIN-158-m32-tier-gating-implementation.md
│   │   ├── PIN-159-m32-numeric-pricing-anchors-currency-model.md
│   │   ├── PIN-160-m0-m27-utilization-audit-disposition.md
│   │   ├── PIN-161-p2fc-partial-to-full-consume.md
│   │   ├── PIN-162-p2fc-4-scoped-execution-gate.md
│   │   ├── PIN-163-m0-m28-utilization-report.md
│   │   ├── PIN-164-system-mental-model-pillar-interactions.md
│   │   ├── PIN-165-pillar-definition-reconciliation.md
│   │   ├── PIN-166-m10-validation-auth-fix.md
│   │   ├── PIN-167-final-review-tasks-1.md
│   │   ├── PIN-168-m0-m28-human-test-scenarios.md
│   │   ├── PIN-169-m7-m28-rbac-integration-plan.md
│   │   ├── PIN-170-system-contract-governance-framework.md
│   │   ├── PIN-171-phase-4b-4c-causal-binding-customer-visibility.md
│   │   ├── PIN-172-phase-5a-budget-enforcement.md
│   │   ├── PIN-173-phase-5b-policy-pre-check-matrix.md
│   │   ├── PIN-174-phase-5c-recovery-automation-matrix.md
│   │   ├── PIN-175-session-phase5b-phase5c-complete.md
│   │   ├── PIN-176-phase-5d-care-optimization-matrix.md
│   │   ├── PIN-177-phase-5e-visibility-surfacing-matrix.md
│   │   ├── PIN-178-phase-5e-h-human-test-eligibility.md
│   │   ├── PIN-179-phase-5e-1-founder-timeline-ui.md
│   │   ├── PIN-180-phase-5e-2-killswitch-ui.md
│   │   ├── PIN-181-phase-5e-3-navigation-linking.md
│   │   ├── PIN-182-phase-5e-4-customer-essentials.md
│   │   ├── PIN-183-runtime-v1-feature-freeze.md
│   │   ├── PIN-184-founder-led-beta-criteria.md
│   │   ├── PIN-185-phase-5e-5-contract-surfacing-fixes.md
│   │   ├── PIN-186-page-order-drill-down-invariants.md
│   │   ├── PIN-187-pin186-compliance-audit.md
│   │   ├── PIN-188-beta-scorecard.md
│   │   ├── PIN-188-founder-beta-signals-framework.md
│   │   ├── PIN-189-phase-a-closure-beta-launch.md
│   │   ├── PIN-189-weekly-synthesis.md
│   │   ├── PIN-190-phase-b-subdomain-rollout-plan.md
│   │   ├── PIN-191-claude-system-test-script.md
│   │   ├── PIN-192-phase-a5-founder-verification.md
│   │   ├── PIN-193-acceptance-gate-truth-propagation.md
│   │   ├── PIN-194-acceptance-gate-cost-signal-truth.md
│   │   ├── PIN-195-acceptance-gate-policy-violation-truth.md
│   │   ├── PIN-196-acceptance-gate-llm-failure-truth.md
│   │   ├── PIN-196-s2-hardening-preventive-fixes.md
│   │   ├── PIN-197-acceptance-gate-memory-injection-truth.md
│   │   ├── PIN-198-acceptance-gate-trace-integrity-truth.md
│   │   ├── PIN-199-pb-s1-retry-creates-new-execution---implementation.md
│   │   ├── PIN-200-claude-behavior-enforcement-system.md
│   │   ├── PIN-201-enhanced-behavior-library.md
│   │   ├── PIN-202-pb-s2-crash-recovery-frozen.md
│   │   ├── PIN-203-pb-s3-controlled-feedback-loops.md
│   │   ├── PIN-204-pb-s4-policy-evolution-provenance.md
│   │   ├── PIN-205-pb-s5-prediction-without-determinism-loss.md
│   │   ├── PIN-206-session-playbook-bootstrap.md
│   │   ├── PIN-207-phase-ab-vcl-rerun-verification.md
│   │   ├── PIN-208-phase-c-discovery-ledger.md
│   │   ├── PIN-209-claude-assumption-elimination.md
│   │   ├── PIN-210-c1-telemetry-plane.md
│   │   ├── PIN-211-pillar-complement-gap-analysis.md
│   │   ├── PIN-212-c1-ci-enforcement.md
│   │   ├── PIN-220-c2-entry-conditions.md
│   │   ├── PIN-221-c2-semantic-contract-failure-modes.md
│   │   ├── PIN-222-c2-implementation-specification.md
│   │   ├── PIN-223-c2-t3-policy-drift-implementation-complete.md
│   │   ├── PIN-224-c2-o4-governance-complete.md
│   │   ├── PIN-225-c3-entry-conditions.md
│   │   ├── PIN-226-c3-closure-c4-bridge.md
│   │   ├── PIN-230-c4-entry-conditions.md
│   │   ├── PIN-231-c4-certification-complete.md
│   │   ├── PIN-232-c5-entry-conditions.md
│   │   ├── PIN-233-file-utilization-customer-console.md
│   │   ├── PIN-234-customer-console-v1-constitution-and-governance-framework.md
│   │   ├── PIN-235-products-first-architecture-migration.md
│   │   ├── PIN-236-code-purpose-authority-registry.md
│   │   ├── PIN-237-codebase-registry-survey.md
│   │   ├── PIN-238-code-registration-evolution-governance.md
│   │   ├── PIN-239-product-boundary-enforcement.md
│   │   ├── PIN-240-seven-layer-codebase-mental-model.md
│   │   ├── PIN-241-layer-violation-triage-strategy.md
│   │   ├── PIN-242-layer-map-baseline-freeze.md
│   │   ├── PIN-243-l6-platform-subdivision.md
│   │   ├── PIN-244-l3-adapter-contract.md
│   │   ├── PIN-245-integration-integrity-system.md
│   │   ├── PIN-246-architecture-governance-implementation.md
│   │   ├── PIN-247-governance-closeout.md
│   │   ├── PIN-248-codebase-inventory-layer-system.md
│   │   └── PIN-249-protective-governance-housekeeping-normalization.md
│   ├── milestones
│   │   ├── M4-SPEC.md
│   │   └── M5-SPEC.md
│   ├── mn-os
│   │   ├── architecture_overview.md
│   │   ├── subsystem_mapping.md
│   │   └── transition_guide.md
│   ├── ops
│   │   └── ops-suite-overview.md
│   ├── playbooks
│   │   └── SESSION_PLAYBOOK.yaml
│   ├── release-notes
│   │   ├── M12-M12.1-RELEASE-NOTES.md
│   │   └── M4-summary.md
│   ├── reports
│   ├── runbooks
│   │   ├── tabletop-results
│   │   │   └── 2025-12-01.md
│   │   ├── DEPLOY_OWNERSHIP.md
│   │   ├── M10_MIGRATION_022_RUNBOOK.md
│   │   ├── M10_PROD_HANDBOOK.md
│   │   ├── M10_RECOVERY_OPERATIONS.md
│   │   ├── M5_POLICY_RUNBOOK.md
│   │   ├── MEMORY_PIN_CLEANUP.md
│   │   ├── MIGRATION_022_PRODUCTION_RUNBOOK.md
│   │   ├── NoRunsProcessed.md
│   │   ├── ONCALL_QUICK_REFERENCE.md
│   │   ├── QueueDepthCritical.md
│   │   ├── RBAC_ENABLEMENT_RUNBOOK.md
│   │   ├── RBAC_INCIDENTS.md
│   │   ├── SECRETS_ROTATION.md
│   │   ├── WEBHOOK_SECRET_ROTATION.md
│   │   ├── WORKER_POOL_PRODUCTION_RUNBOOK.md
│   │   ├── WorkerPoolDown.md
│   │   ├── m4-incident-playbook.md
│   │   ├── m4-safety-failure-catalog.md
│   │   ├── m4-workflow-engine.md
│   │   ├── operations.md
│   │   ├── tabletop-drill.md
│   │   ├── webhook-ops.md
│   │   └── workflow-recovery.md
│   ├── security
│   │   └── TENANT_AUDIT_REPORT.md
│   ├── specs
│   │   └── COSTSIM-V2-SPEC.md
│   ├── system
│   │   └── SESSION_SUMMARY_REQUIREMENTS.md
│   ├── technical-debt
│   │   └── QUARANTINE_LEDGER.md
│   ├── templates
│   │   ├── ARTIFACT_INTENT.yaml
│   │   └── FILE_HEADER_TEMPLATE.md
│   ├── test_reports
│   │   ├── M26_REAL_TEST_PROOF_20251223_095145.md
│   │   ├── M26_REAL_TEST_PROOF_20251223_095527.md
│   │   ├── REGISTER.md
│   │   ├── TR-001_CLI_DEMO_HAPPY_PATH_2025-12-16.md
│   │   ├── TR-002_CLI_ADVERSARIAL_TEST_2025-12-16.md
│   │   ├── TR-003_CLI_ADVERSARIAL_TEST_PASS_2025-12-16.md
│   │   ├── TR-004_SCENARIO_TEST_MATRIX_2025-12-16.md
│   │   └── TR-005_SQLMODEL_LINTER_FIXES_2025-12-20.md
│   ├── testing
│   │   └── WORKER_CONSOLE_VALIDATION.md
│   ├── wireframes
│   │   └── SCENARIO_VALUE_WIREFRAMES.md
│   ├── workflow
│   │   └── seed-determinism.md
│   ├── AOS_TEST_HANDBOOK.md
│   ├── API_WORKFLOW_GUIDE.md
│   ├── ARCHITECTURE_OPERATING_MANUAL.md
│   ├── ARCHITECTURE_OVERVIEW.md
│   ├── AUTH_FLOW.md
│   ├── AUTH_SERVICE_REQUIREMENTS.md
│   ├── AUTH_SETUP.md
│   ├── BETA_INSTRUCTIONS.md
│   ├── CI_PREVENTION_GUIDE.md
│   ├── CI_SESSION_REPORT_2025-12-15.md
│   ├── CODE_HEALTH_POLICY.md
│   ├── DATA_CONTRACT_FREEZE.md
│   ├── DEMOS.md
│   ├── DEPLOYMENT_GATE_POLICY.md
│   ├── DETERMINISM.md
│   ├── ERROR_PLAYBOOK.md
│   ├── GOVERNANCE_FREEZE.md
│   ├── HOUSEKEEPING_BASELINE.md
│   ├── HOUSEKEEPING_CLASSIFICATION.md
│   ├── IMPLEMENTATION_REPORT.md
│   ├── LESSONS_ENFORCED.md
│   ├── M26_M27_HANDOVER.md
│   ├── M28_ROUTE_OWNERSHIP.md
│   ├── ONBOARDING.md
│   ├── ONCALL_RUNBOOK.md
│   ├── OPERATING_RULES.md
│   ├── PHASE_A5_CLOSURE.md
│   ├── PREVENTION_PLAYBOOK.md
│   ├── QUICKSTART.md
│   ├── RCA-CI-FIXES-2025-12-07.md
│   ├── REPO_STRUCTURE.md
│   ├── RETURN_TO_DEVELOPMENT.md
│   ├── SCENARIO_OBSERVATION_CONTRACT.md
│   ├── SCHEMA_NAMING_CONVENTIONS.md
│   ├── SESSION_BOOTSTRAP.md
│   ├── STAGING_READINESS.md
│   ├── SYSTEM_TRUTH_LEDGER.md
│   ├── USER_JOURNEY.md
│   ├── openapi.json
│   ├── openapi.yaml
│   ├── replay_scope.md
│   └── v1_feature_freeze.md
├── evidence
│   └── m25
│       ├── README.md
│       ├── graduation_delta_2025-12-23.json
│       ├── policy_activation_pol_eff9bcd477874df3.json
│       └── prevention_prev_ee322953b7764bac.json
├── examples
│   ├── btc_price_slack
│   │   ├── README.md
│   │   ├── demo.py
│   │   └── run.sh
│   ├── http_retry
│   │   ├── README.md
│   │   ├── demo.py
│   │   └── run.sh
│   ├── json_transform
│   │   ├── README.md
│   │   ├── demo.py
│   │   └── run.sh
│   └── README.md
├── helm
│   └── aos
│       ├── templates
│       │   ├── costsim-sandbox
│       │   ├── _helpers.tpl
│       │   ├── canary-cronjob.yaml
│       │   ├── configmap.yaml
│       │   ├── deployment.yaml
│       │   ├── pdb.yaml
│       │   ├── pvc.yaml
│       │   ├── service.yaml
│       │   ├── serviceaccount.yaml
│       │   └── servicemonitor.yaml
│       ├── Chart.yaml
│       └── values.yaml
├── k8s
│   ├── costsim-v2-namespace.yaml
│   ├── escalation-cronjob.yaml
│   └── pgbouncer-deployment.yaml
├── load-tests
│   ├── results
│   │   └── simulate_summary.json
│   └── simulate_k6.js
├── logs
│   ├── architecture_incidents.log
│   ├── mypy_baseline.txt
│   ├── precommit_baseline.txt
│   └── test_baseline.txt
├── memory-pins
│   ├── CLAUDE.md
│   ├── INDEX.md
│   ├── M0_FINALIZATION.md
│   └── PIN-009-EXTERNAL-ROLLOUT-PENDING.md
├── migrations
│   ├── 20251130_add_llm_costs.sql
│   └── 20251224_add_founder_actions.sql
├── monitoring
│   ├── alertmanager
│   │   ├── config.yml
│   │   ├── config.yml.tmpl
│   │   └── entrypoint.sh
│   ├── alerts
│   │   ├── m45_failure_catalog_alerts.yml
│   │   ├── m5_policy_alerts.yml
│   │   └── workflow-alerts.yml
│   ├── dashboards
│   │   ├── embedding-cost-dashboard.json
│   │   ├── m12_m18_multi_agent_self_optimization.json
│   │   ├── m7_rbac_memory_dashboard.json
│   │   ├── m9_failure_catalog_v2.json
│   │   └── workflow-engine.json
│   ├── grafana
│   │   ├── provisioning
│   │   │   ├── dashboards
│   │   │   └── datasources
│   │   ├── aos_traces_dashboard.json
│   │   ├── aos_traces_dashboard_v2.json
│   │   ├── m45_failure_catalog_dashboard.json
│   │   ├── nova_basic_dashboard.json
│   │   └── nova_workflow_m4_dashboard.json
│   ├── rules
│   │   ├── costsim_v2_alerts.yml
│   │   ├── embedding_alerts.yml
│   │   ├── m10_recovery_alerts.yml
│   │   ├── m5_policy_alerts.yml
│   │   ├── m7_rbac_memory_alerts.yml
│   │   ├── m9_failure_catalog_alerts.yml
│   │   ├── nova_alerts.yml
│   │   └── workflow-alerts.yml
│   ├── README.md
│   └── prometheus.yml
├── observability
│   ├── grafana
│   │   └── dashboards
│   │       └── m7_memory_rbac.json
│   └── prometheus
│       └── alert_fuzzer.py
├── openapi
│   └── traces.yaml
├── ops
│   ├── commands
│   │   └── disable-workflows.sh
│   ├── grafana
│   │   ├── README.md
│   │   ├── aos_overview.json
│   │   ├── determinism_replay.json
│   │   └── llm_spend.json
│   ├── prometheus_rules
│   │   ├── alerts.yml
│   │   └── workflow_alerts.yml
│   ├── KNOWN_WARNINGS.md
│   ├── M7_RUNBOOK.md
│   ├── check_pgbouncer.sh
│   ├── memory_pins_seed.json
│   └── seed_memory_pins.py
├── scripts
│   ├── chaos
│   │   ├── cpu_spike.sh
│   │   ├── memory_pressure.sh
│   │   └── redis_stall.sh
│   ├── ci
│   │   ├── c2_guardrails
│   │   │   ├── gr1_import_isolation.sh
│   │   │   ├── gr2_advisory_enforcement.sh
│   │   │   ├── gr3_replay_blindness.sh
│   │   │   ├── gr4_semantic_lint.sh
│   │   │   ├── gr5_redis_authority.sh
│   │   │   └── run_all.sh
│   │   ├── c3_guardrails
│   │   │   └── run_all.sh
│   │   ├── c4_guardrails
│   │   │   ├── check_audit.sh
│   │   │   ├── check_audit_immutability.sh
│   │   │   ├── check_audit_isolation.sh
│   │   │   ├── check_audit_replay_safety.sh
│   │   │   ├── check_coordination_required.sh
│   │   │   ├── check_envelope_class.sh
│   │   │   ├── check_killswitch.sh
│   │   │   ├── check_priority_immutable.sh
│   │   │   ├── check_same_parameter.sh
│   │   │   └── run_all.sh
│   │   ├── c5_guardrails
│   │   │   ├── check_advisory_only.sh
│   │   │   ├── check_approval_gate.sh
│   │   │   ├── check_disable_flag.sh
│   │   │   ├── check_killswitch_isolation.sh
│   │   │   ├── check_metadata_boundary.sh
│   │   │   ├── check_versioning.sh
│   │   │   └── run_all.sh
│   │   ├── o4_checks
│   │   │   ├── rc1_language.sh
│   │   │   ├── rc2_routes.sh
│   │   │   ├── rc3_imports.sh
│   │   │   ├── rc4_api.sh
│   │   │   ├── rc5_banner.sh
│   │   │   ├── rc6_colors.sh
│   │   │   └── run_all.sh
│   │   ├── check_catalog_metrics.py
│   │   ├── check_env_misuse.sh
│   │   ├── check_sqlmodel_exec.sh
│   │   ├── lint_regression_guard.sh
│   │   └── synthetic_alert.sh
│   ├── deploy
│   │   ├── apache
│   │   │   └── agenticverz.com.conf
│   │   ├── backend
│   │   ├── aos-console-deploy.sh
│   │   ├── aos-smoke-test.sh
│   │   ├── cloudflare-checklist.md
│   │   └── verify_config.py
│   ├── hooks
│   │   └── pre-push
│   ├── inventory
│   │   ├── find_unknown_files_v2.py
│   │   └── full_inventory.py
│   ├── ops
│   │   ├── archival
│   │   │   └── run_archival.sh
│   │   ├── canary
│   │   │   ├── configs
│   │   │   ├── reports
│   │   │   ├── CANARY_PLAYBOOK.md
│   │   │   ├── README.md
│   │   │   ├── canary_runner.py
│   │   │   └── generate_signoff.sh
│   │   ├── chaos
│   │   │   ├── cpu_spike.sh
│   │   │   ├── kill_child.sh
│   │   │   └── redis_stall.sh
│   │   ├── cron
│   │   │   └── aos-maintenance.cron
│   │   ├── diagnostics
│   │   │   └── db_diagnostics.sh
│   │   ├── vault
│   │   │   ├── README.md
│   │   │   ├── rotate_secret.sh
│   │   │   ├── unseal_vault.sh
│   │   │   └── vault_env.sh
│   │   ├── webhook
│   │   │   └── rotate_webhook_key.sh
│   │   ├── add_lint_pattern.py
│   │   ├── aos_console_health_test.sh
│   │   ├── architecture_incident_logger.py
│   │   ├── artifact_lookup.py
│   │   ├── c2_prediction_expiry_cleanup.py
│   │   ├── canary_smoke_test.sh
│   │   ├── change_record.py
│   │   ├── check_api_wiring.py
│   │   ├── check_migration_heads.sh
│   │   ├── check_migrations.sh
│   │   ├── ci_consistency_check.sh
│   │   ├── claude_response_validator.py
│   │   ├── claude_session_boot.sh
│   │   ├── cli_demo_test.sh
│   │   ├── compute_stickiness_cron.sh
│   │   ├── cost_snapshot_job.py
│   │   ├── deploy_website.sh
│   │   ├── dev_sync.sh
│   │   ├── disable-workflows.sh
│   │   ├── expire_memory_pins.sh
│   │   ├── golden_retention.sh
│   │   ├── golden_test.py
│   │   ├── guard_health_test.sh
│   │   ├── hygiene_check.sh
│   │   ├── incident_classifier.py
│   │   ├── intent_validator.py
│   │   ├── job_wrapper.sh
│   │   ├── layer_validator.py
│   │   ├── lint_frontend_api_calls.py
│   │   ├── lint_schema_naming.py
│   │   ├── lint_sqlmodel_patterns.py
│   │   ├── m10_48h_health_check.sh
│   │   ├── m10_daily_stats_export.py
│   │   ├── m10_dl_inspector.py
│   │   ├── m10_load_chaos_test.py
│   │   ├── m10_observability_validation.py
│   │   ├── m10_orchestrator.py
│   │   ├── m10_prod_deploy_checklist.sh
│   │   ├── m10_retention_archive.py
│   │   ├── m10_staging_verify.sh
│   │   ├── m10_synthetic_traffic.py
│   │   ├── m10_synthetic_validation.py
│   │   ├── m25_activate_policy.py
│   │   ├── m25_capture_evidence_trail.py
│   │   ├── m25_gate_passage_demo.py
│   │   ├── m25_graduation_delta.py
│   │   ├── m25_trigger_prevention.py
│   │   ├── m25_trigger_real_incident.py
│   │   ├── m26_real_cost_test.py
│   │   ├── m27_real_cost_test.py
│   │   ├── m5_ga_deploy.sh
│   │   ├── m7_monitoring_check.sh
│   │   ├── m9_monitoring_deploy.sh
│   │   ├── memory_pins_seed.json
│   │   ├── memory_trail.py
│   │   ├── metrics_validation.py
│   │   ├── postflight.py
│   │   ├── preflight.py
│   │   ├── prom_reload.sh
│   │   ├── r2_cleanup.sh
│   │   ├── r2_lifecycle.sh
│   │   ├── r2_verify.sh
│   │   ├── rbac_enable.sh
│   │   ├── rbac_enable_smoke.sh
│   │   ├── rbac_oneclick_enable.sh
│   │   ├── retry_r2_fallbacks.sh
│   │   ├── runtime_smoke.py
│   │   ├── scenario_test_matrix.py
│   │   ├── schema_audit.py
│   │   ├── seed_demo_events.py
│   │   ├── seed_memory_pins.py
│   │   ├── session_bootstrap_validator.py
│   │   ├── session_start.sh
│   │   ├── setup_ci_hooks.sh
│   │   ├── temporal_detector.py
│   │   ├── test_cost_snapshots.py
│   │   ├── test_customer_console.py
│   │   ├── test_worker_events.py
│   │   ├── trace_retention_cron.sh
│   │   ├── verify_console_routes.sh
│   │   └── visibility_validator.py
│   ├── preflight
│   │   └── check_auth_context.sh
│   ├── smoke
│   │   ├── rbac_smoke.sh
│   │   └── test_rbac_keycloak.sh
│   ├── stress
│   │   ├── check_shadow_status.sh
│   │   ├── golden_diff_debug.py
│   │   ├── run_checkpoint_stress.sh
│   │   ├── run_cpu_stress_replay.sh
│   │   ├── run_fault_injection.sh
│   │   ├── run_golden_stress.sh
│   │   ├── run_multi_worker_determinism.sh
│   │   ├── run_shadow_simulation.sh
│   │   ├── shadow_cron_check.sh
│   │   ├── shadow_debug.sh
│   │   ├── shadow_monitor_daemon.sh
│   │   ├── shadow_sanity_check.sh
│   │   └── shadow_wrapper_notify.sh
│   ├── tools
│   │   └── pin_drift_detector.sh
│   ├── verification
│   │   ├── evidence
│   │   │   ├── c1_baseline_20251227_202107.json
│   │   │   ├── c1_failure_injection_20251227_203917.json
│   │   │   └── c1_neon_20251227_205438.json
│   │   ├── c1_claude_test_pack.md
│   │   ├── c1_failure_injection_matrix.md
│   │   ├── c1_telemetry_probes.py
│   │   ├── c2_regression.py
│   │   ├── c4_synthetic_stability.py
│   │   ├── tenant_isolation_test.py
│   │   └── truth_preflight.sh
│   ├── bootstrap-dev.sh
│   ├── e2e_integration.sh
│   ├── list-failed.sh
│   ├── nova-tunnel.sh
│   ├── pg_backup.sh
│   ├── preflight_m4_signoff.sh
│   ├── rerun.sh
│   ├── rollback_failure_catalog.sh
│   ├── run_worker_local.sh
│   ├── smoke_release.sh
│   ├── test-alerts.sh
│   └── test_webhook_receiver.sh
├── sdk
│   ├── js
│   │   ├── aos-sdk
│   │   │   ├── scripts
│   │   │   ├── src
│   │   │   ├── test
│   │   │   ├── README.md
│   │   │   ├── package-lock.json
│   │   │   ├── package.json
│   │   │   └── tsconfig.json
│   │   ├── nova-sdk
│   │   │   └── index.js
│   │   ├── tests
│   │   │   └── test_js_sdk.js
│   │   └── README.md
│   ├── python
│   │   ├── aos_sdk
│   │   │   ├── __init__.py
│   │   │   ├── cli.py
│   │   │   ├── client.py
│   │   │   ├── py.typed
│   │   │   ├── runtime.py
│   │   │   └── trace.py
│   │   ├── nova_sdk
│   │   │   ├── __init__.py
│   │   │   └── client.py
│   │   ├── tests
│   │   │   ├── __init__.py
│   │   │   ├── test_python_sdk.py
│   │   │   ├── test_runtime.py
│   │   │   └── test_trace.py
│   │   ├── README.md
│   │   ├── pyproject.toml
│   │   └── setup.py
│   └── tests
│       └── test_sdk_flow.sh
├── secrets
│   ├── cloudflare
│   │   ├── auth-dev.xuniverz.com.crt
│   │   └── auth-dev.xuniverz.com.key
│   ├── README.md
│   ├── clerk.env
│   ├── clerk_public_key.pem
│   ├── cloudflare.env
│   ├── google_oauth.env
│   ├── google_oauth.json
│   ├── keycloak_oidc.env
│   ├── load_all.sh
│   ├── microsoft_oauth.env
│   ├── neon.env
│   ├── openai.env
│   ├── posthog.env
│   ├── resend.env
│   ├── trigger.env
│   └── voyage.env
├── tests
│   ├── aos-test-suite
│   │   ├── agent_simulation_test.py
│   │   ├── load_test.py
│   │   ├── skill_evaluation.py
│   │   └── smoke_test.py
│   └── golden
│       ├── m14_budget_decision.json
│       ├── m17_routing_decision.json
│       ├── m18_governor_adjustment.json
│       ├── m19_policy_evaluation.json
│       ├── m4_execution_plan.json
│       └── m6_costsim_pricing.json
├── tools
│   ├── webhook_dev
│   │   ├── Dockerfile.dev
│   │   ├── README.md
│   │   ├── app.py
│   │   └── docker-compose.yml
│   ├── webhook_receiver
│   │   ├── app
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   └── rate_limiter.py
│   │   ├── grafana
│   │   │   └── webhook-receiver-dashboard.json
│   │   ├── k8s
│   │   │   ├── base
│   │   │   └── overlay-staging
│   │   ├── prometheus
│   │   │   └── scrape-config.yaml
│   │   ├── tests
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py
│   │   │   ├── test_log_correlation.py
│   │   │   ├── test_metric_fuzzer.py
│   │   │   ├── test_rate_limiter.py
│   │   │   ├── test_rate_limiter_chaos.py
│   │   │   └── test_readiness_probe.py
│   │   ├── DEPLOYMENT.md
│   │   ├── Dockerfile
│   │   ├── README.md
│   │   ├── deploy-staging.sh
│   │   └── requirements.txt
│   ├── wiremock
│   │   ├── __files
│   │   ├── mappings
│   │   │   ├── alertmanager-get.json
│   │   │   ├── alertmanager-health.json
│   │   │   ├── alertmanager-post.json
│   │   │   ├── alertmanager-ready.json
│   │   │   └── webhook-catchall.json
│   │   ├── README.md
│   │   └── docker-compose.yml
│   ├── e2e_results_parser.py
│   ├── generate_synthetic_failures.py
│   ├── inject_synthetic_alert.py
│   ├── k6_slo_mapper.py
│   └── test_idempotency_atomicity.py
├── website
│   ├── aos-console
│   │   ├── components
│   │   │   ├── API-UI-MAPPING.md
│   │   │   ├── EVENT-MODEL-DEFINITIONS.md
│   │   │   └── REACT-COMPONENT-TREE.md
│   │   ├── console
│   │   │   ├── public
│   │   │   ├── scripts
│   │   │   ├── src
│   │   │   ├── tests
│   │   │   ├── DOMAIN_MAPPING_ANALYSIS.md
│   │   │   ├── RUNTIME_V1_FREEZE_NOTES.md
│   │   │   ├── WIREFRAME_GAP_ANALYSIS.md
│   │   │   ├── index.html
│   │   │   ├── package-lock.json
│   │   │   ├── package.json
│   │   │   ├── postcss.config.js
│   │   │   ├── tailwind.config.js
│   │   │   ├── tsconfig.json
│   │   │   ├── tsconfig.node.json
│   │   │   └── vite.config.ts
│   │   ├── design-system
│   │   │   └── UI-DESIGN-SYSTEM.md
│   │   ├── landing
│   │   │   └── WEBSITE-LANDING-STRUCTURE.md
│   │   ├── wireframes
│   │   │   └── AOS-CONSOLE-WIREFRAMES.md
│   │   ├── BOILERPLATE-CODE.md
│   │   └── DEPLOYMENT-RUNBOOK.md
│   └── landing
│       ├── public
│       │   └── logo.svg
│       ├── src
│       │   ├── pages
│       │   ├── App.jsx
│       │   ├── index.css
│       │   └── main.jsx
│       ├── index.html
│       ├── package-lock.json
│       ├── package.json
│       ├── postcss.config.js
│       ├── tailwind.config.js
│       └── vite.config.js
├── CLAUDE.md
├── CLAUDE_BEHAVIOR_LIBRARY.md
├── CLAUDE_BOOT_CONTRACT.md
├── CLAUDE_PRE_CODE_DISCIPLINE.md
├── GPT.md
├── Makefile
├── PROJECT_NOTES.md
├── README.md
├── SESSION_BOOTSTRAP_REQUIRED.md
├── docker-compose.staging.yml
├── docker-compose.yml
├── mypy.ini
└── test_api.sh

256 directories, 1535 files
```

---

## Key Directories Detail

### Backend (`backend/app/`)

| Directory | Purpose | Layer |
|-----------|---------|-------|
| `api/` | REST API routes | L2 |
| `services/` | Business logic services | L4 |
| `models/` | SQLModel database models | L6 |
| `auth/` | Authentication & RBAC | L4 |
| `policy/` | Policy engine (AST, compiler, runtime) | L4 |
| `integrations/` | M25 Pillar Integration (Domain) | L4 |
| `workflow/` | Workflow execution engine | L5 |
| `workers/` | Background workers | L5 |
| `routing/` | CARE routing engine | L4 |
| `learning/` | Learning subsystem | L4 |
| `traces/` | Trace storage & replay | L4 |
| `skills/` | Skill registry & implementations | L4 |
| `contracts/` | Data contracts | L4 |

### Documentation (`docs/`)

| Directory | Purpose |
|-----------|---------|
| `memory-pins/` | 247+ PINs (project memory) |
| `contracts/` | System contracts (governance) |
| `technical-debt/` | Quarantine ledger |
| `playbooks/` | SESSION_PLAYBOOK.yaml |
| `templates/` | File header templates |
| `codebase-registry/` | Artifact registry |

### Scripts (`scripts/`)

| Directory | Purpose |
|-----------|---------|
| `ops/` | Operations scripts |
| `ci/` | CI/CD scripts |
| `verification/` | Truth verification |
| `preflight/` | Pre-execution checks |
| `stress/` | Load testing |

---

## Statistics

```
Total Python files: 683
Total TypeScript files: 149
Total Markdown files: 479
Memory PINs: 247
Alembic migrations: 64
Test files: 144
```

---

*Generated by ARCH-GOV-007 audit process*
