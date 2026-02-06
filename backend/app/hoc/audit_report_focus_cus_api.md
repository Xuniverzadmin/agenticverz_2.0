# HOC Audit Focus: hoc/cus and hoc/api

## Summary

- HOC routers (hoc/api) found: 74

- Wired in `app/main.py`: 1

- Unwired routers: 73

- Dead/unused candidates in hoc/cus + hoc/api: 249


## Wired HOC Routers in app/main.py

- `hoc.api.cus.integrations.mcp_servers`


## Missing `hoc.api.int.agent.api.*` Modules (imported but absent)

- `hoc.api.int.agent.api.M25_integrations`

- `hoc.api.int.agent.api.activity`

- `hoc.api.int.agent.api.agents`

- `hoc.api.int.agent.api.alerts`

- `hoc.api.int.agent.api.analytics`

- `hoc.api.int.agent.api.aos_accounts`

- `hoc.api.int.agent.api.aos_api_key`

- `hoc.api.int.agent.api.aos_cus_integrations`

- `hoc.api.int.agent.api.authz_status`

- `hoc.api.int.agent.api.compliance`

- `hoc.api.int.agent.api.controls`

- `hoc.api.int.agent.api.cost_guard`

- `hoc.api.int.agent.api.cost_intelligence`

- `hoc.api.int.agent.api.cost_ops`

- `hoc.api.int.agent.api.costsim`

- `hoc.api.int.agent.api.cus_enforcement`

- `hoc.api.int.agent.api.cus_telemetry`

- `hoc.api.int.agent.api.customer_visibility`

- `hoc.api.int.agent.api.datasources`

- `hoc.api.int.agent.api.debug_auth`

- `hoc.api.int.agent.api.detection`

- `hoc.api.int.agent.api.discovery`

- `hoc.api.int.agent.api.embedding`

- `hoc.api.int.agent.api.evidence`

- `hoc.api.int.agent.api.feedback`

- `hoc.api.int.agent.api.founder_actions`

- `hoc.api.int.agent.api.founder_contract_review`

- `hoc.api.int.agent.api.founder_explorer`

- `hoc.api.int.agent.api.founder_onboarding`

- `hoc.api.int.agent.api.founder_review`

- `hoc.api.int.agent.api.founder_timeline`

- `hoc.api.int.agent.api.guard`

- `hoc.api.int.agent.api.guard_logs`

- `hoc.api.int.agent.api.guard_policies`

- `hoc.api.int.agent.api.health`

- `hoc.api.int.agent.api.incidents`

- `hoc.api.int.agent.api.legacy_routes`

- `hoc.api.int.agent.api.lifecycle`

- `hoc.api.int.agent.api.limits.override`

- `hoc.api.int.agent.api.limits.simulate`

- `hoc.api.int.agent.api.logs`

- `hoc.api.int.agent.api.memory_pins`

- `hoc.api.int.agent.api.monitors`

- `hoc.api.int.agent.api.notifications`

- `hoc.api.int.agent.api.onboarding`

- `hoc.api.int.agent.api.ops`

- `hoc.api.int.agent.api.overview`

- `hoc.api.int.agent.api.platform`

- `hoc.api.int.agent.api.policies`

- `hoc.api.int.agent.api.policy`

- `hoc.api.int.agent.api.policy_layer`

- `hoc.api.int.agent.api.policy_limits_crud`

- `hoc.api.int.agent.api.policy_proposals`

- `hoc.api.int.agent.api.policy_rules_crud`

- `hoc.api.int.agent.api.predictions`

- `hoc.api.int.agent.api.rate_limits`

- `hoc.api.int.agent.api.rbac_api`

- `hoc.api.int.agent.api.recovery`

- `hoc.api.int.agent.api.recovery_ingest`

- `hoc.api.int.agent.api.replay`

- `hoc.api.int.agent.api.retrieval`

- `hoc.api.int.agent.api.runtime`

- `hoc.api.int.agent.api.scenarios`

- `hoc.api.int.agent.api.scheduler`

- `hoc.api.int.agent.api.sdk`

- `hoc.api.int.agent.api.session_context`

- `hoc.api.int.agent.api.status_history`

- `hoc.api.int.agent.api.tenants`

- `hoc.api.int.agent.api.traces`

- `hoc.api.int.agent.api.v1_killswitch`

- `hoc.api.int.agent.api.v1_proxy`

- `hoc.api.int.agent.api.workers`


## Unwired HOC Routers (APIRouter defined, no wiring found)

- `hoc.api.cus.account.memory_pins`

- `hoc.api.cus.activity.activity`

- `hoc.api.cus.agent.authz_status`

- `hoc.api.cus.agent.discovery`

- `hoc.api.cus.agent.onboarding`

- `hoc.api.cus.agent.platform`

- `hoc.api.cus.analytics.costsim`

- `hoc.api.cus.analytics.feedback`

- `hoc.api.cus.analytics.predictions`

- `hoc.api.cus.analytics.scenarios`

- `hoc.api.cus.api_keys.auth_helpers`

- `hoc.api.cus.api_keys.embedding`

- `hoc.api.cus.general.agents`

- `hoc.api.cus.general.debug_auth`

- `hoc.api.cus.general.health`

- `hoc.api.cus.general.sdk`

- `hoc.api.cus.incidents.cost_guard`

- `hoc.api.cus.incidents.incidents`

- `hoc.api.cus.integrations.cus_telemetry`

- `hoc.api.cus.integrations.session_context`

- `hoc.api.cus.logs.cost_intelligence`

- `hoc.api.cus.logs.guard_logs`

- `hoc.api.cus.logs.tenants`

- `hoc.api.cus.logs.traces`

- `hoc.api.cus.ops.cost_ops`

- `hoc.api.cus.overview.overview`

- `hoc.api.cus.policies.M25_integrations`

- `hoc.api.cus.policies.alerts`

- `hoc.api.cus.policies.analytics`

- `hoc.api.cus.policies.aos_accounts`

- `hoc.api.cus.policies.aos_api_key`

- `hoc.api.cus.policies.aos_cus_integrations`

- `hoc.api.cus.policies.compliance`

- `hoc.api.cus.policies.connectors`

- `hoc.api.cus.policies.controls`

- `hoc.api.cus.policies.cus_enforcement`

- `hoc.api.cus.policies.customer_visibility`

- `hoc.api.cus.policies.datasources`

- `hoc.api.cus.policies.detection`

- `hoc.api.cus.policies.evidence`

- `hoc.api.cus.policies.governance`

- `hoc.api.cus.policies.guard`

- `hoc.api.cus.policies.guard_policies`

- `hoc.api.cus.policies.lifecycle`

- `hoc.api.cus.policies.logs`

- `hoc.api.cus.policies.monitors`

- `hoc.api.cus.policies.notifications`

- `hoc.api.cus.policies.override`

- `hoc.api.cus.policies.policies`

- `hoc.api.cus.policies.policy`

- `hoc.api.cus.policies.policy_layer`

- `hoc.api.cus.policies.policy_limits_crud`

- `hoc.api.cus.policies.policy_proposals`

- `hoc.api.cus.policies.policy_rules_crud`

- `hoc.api.cus.policies.rate_limits`

- `hoc.api.cus.policies.rbac_api`

- `hoc.api.cus.policies.replay`

- `hoc.api.cus.policies.retrieval`

- `hoc.api.cus.policies.runtime`

- `hoc.api.cus.policies.scheduler`

- `hoc.api.cus.policies.simulate`

- `hoc.api.cus.policies.status_history`

- `hoc.api.cus.policies.workers`

- `hoc.api.cus.recovery.recovery`

- `hoc.api.cus.recovery.recovery_ingest`

- `hoc.api.fdr.account.founder_explorer`

- `hoc.api.fdr.account.founder_lifecycle`

- `hoc.api.fdr.agent.founder_contract_review`

- `hoc.api.fdr.incidents.founder_onboarding`

- `hoc.api.fdr.incidents.ops`

- `hoc.api.fdr.logs.founder_review`

- `hoc.api.fdr.logs.founder_timeline`

- `hoc.api.fdr.ops.founder_actions`


## Dead/Unused Candidates (hoc/cus + hoc/api only)

- Total: 249

- By area (top 10):

  - `cus`: 165

  - `api`: 84


- Sample (first 80):

  - `hoc.cus.hoc_spine.drivers.alert_emitter`

  - `hoc.cus.hoc_spine.drivers.idempotency`

  - `hoc.cus.hoc_spine.drivers.guard_cache`

  - `hoc.cus.hoc_spine.drivers.governance_signal_driver`

  - `hoc.cus.hoc_spine.drivers.dag_executor`

  - `hoc.cus.hoc_spine.drivers.decisions`

  - `hoc.cus.hoc_spine.drivers.schema_parity`

  - `hoc.cus.hoc_spine.utilities.s1_retry_backoff`

  - `hoc.cus.hoc_spine.schemas.plan`

  - `hoc.cus.hoc_spine.schemas.response`

  - `hoc.cus.hoc_spine.schemas.artifact`

  - `hoc.cus.hoc_spine.schemas.retry`

  - `hoc.cus.hoc_spine.schemas.skill`

  - `hoc.cus.hoc_spine.schemas.agent`

  - `hoc.cus.hoc_spine.schemas.common`

  - `hoc.cus.hoc_spine.schemas.authority_decision`

  - `hoc.cus.hoc_spine.services.db_helpers`

  - `hoc.cus.hoc_spine.services.fatigue_controller`

  - `hoc.cus.hoc_spine.services.canonical_json`

  - `hoc.cus.hoc_spine.services.deterministic`

  - `hoc.cus.hoc_spine.services.guard`

  - `hoc.cus.hoc_spine.services.webhook_verify`

  - `hoc.cus.hoc_spine.services.input_sanitizer`

  - `hoc.cus.hoc_spine.services.metrics_helpers`

  - `hoc.cus.hoc_spine.services.dag_sorter`

  - `hoc.cus.hoc_spine.services.audit_durability`

  - `hoc.cus.hoc_spine.authority.guard_write_engine`

  - `hoc.cus.hoc_spine.authority.degraded_mode_checker`

  - `hoc.cus.hoc_spine.authority.concurrent_runs`

  - `hoc.cus.hoc_spine.authority.runtime`

  - `hoc.cus.hoc_spine.authority.runtime_adapter`

  - `hoc.cus.hoc_spine.orchestrator.phase_status_invariants`

  - `hoc.cus.hoc_spine.orchestrator.constraint_checker`

  - `hoc.cus.hoc_spine.tests.conftest`

  - `hoc.cus.hoc_spine.tests.test_operation_registry`

  - `hoc.cus.hoc_spine.consequences.adapters.export_bundle_adapter`

  - `hoc.cus.hoc_spine.orchestrator.handlers.controls_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.integrity_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.analytics_sandbox_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.activity_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.account_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.analytics_validation_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.mcp_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.analytics_config_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.integration_bootstrap_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.analytics_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.logs_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.analytics_prediction_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.api_keys_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.integrations_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.analytics_snapshot_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.policy_governance_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.incidents_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.analytics_metrics_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.run_governance_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.overview_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.idempotency_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.circuit_breaker_handler`

  - `hoc.cus.hoc_spine.orchestrator.handlers.policies_handler`

  - `hoc.cus.hoc_spine.orchestrator.coordinators.snapshot_scheduler`

  - `hoc.cus.hoc_spine.orchestrator.coordinators.leadership_coordinator`

  - `hoc.cus.hoc_spine.orchestrator.coordinators.evidence_coordinator`

  - `hoc.cus.hoc_spine.orchestrator.coordinators.provenance_coordinator`

  - `hoc.cus.hoc_spine.orchestrator.lifecycle.drivers.knowledge_plane`

  - `hoc.cus.hoc_spine.orchestrator.lifecycle.engines.pool_manager`

  - `hoc.cus.hoc_spine.orchestrator.coordinators.bridges.overview_bridge`

  - `hoc.cus.hoc_spine.orchestrator.coordinators.bridges.integrations_bridge`

  - `hoc.cus.policies.adapters.policy_adapter`

  - `hoc.cus.policies.adapters.customer_policies_adapter`

  - `hoc.cus.policies.adapters.founder_contract_review_adapter`

  - `hoc.cus.policies.L5_schemas.domain_bridge_capabilities`

  - `hoc.cus.policies.L6_drivers.arbitrator`

  - `hoc.cus.policies.L6_drivers.symbol_table`

  - `hoc.cus.policies.L6_drivers.optimizer_conflict_resolver`

  - `hoc.cus.policies.L6_drivers.scope_resolver`

  - `hoc.cus.policies.L5_engines.ir_compiler`

  - `hoc.cus.policies.L5_engines.kernel`

  - `hoc.cus.policies.L5_engines.grammar`

  - `hoc.cus.policies.L5_engines.plan`

  - `hoc.cus.policies.L5_engines.eligibility_engine`
