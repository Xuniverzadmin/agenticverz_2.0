# HOC Audit Report (Refined Wiring Scan)

## Summary

- HOC router modules found: 74

- HOC routers wired in `app/main.py`: 1

- HOC routers unwired (no include_router wiring found): 73

- HOC dead/unused candidates after wiring refinement: 483


## Entry Points Detected

- `backend/app/main.py` includes HOC router imports:

  - `hoc.api.cus.integrations.mcp_servers`


- `backend/app/hoc/api/int/agent/main.py` imports (expected routers):

  - `hoc.api.int.agent.api.M25_integrations` (MISSING)

  - `hoc.api.int.agent.api.activity` (MISSING)

  - `hoc.api.int.agent.api.agents` (MISSING)

  - `hoc.api.int.agent.api.alerts` (MISSING)

  - `hoc.api.int.agent.api.analytics` (MISSING)

  - `hoc.api.int.agent.api.aos_accounts` (MISSING)

  - `hoc.api.int.agent.api.aos_api_key` (MISSING)

  - `hoc.api.int.agent.api.aos_cus_integrations` (MISSING)

  - `hoc.api.int.agent.api.authz_status` (MISSING)

  - `hoc.api.int.agent.api.compliance` (MISSING)

  - `hoc.api.int.agent.api.controls` (MISSING)

  - `hoc.api.int.agent.api.cost_guard` (MISSING)

  - `hoc.api.int.agent.api.cost_intelligence` (MISSING)

  - `hoc.api.int.agent.api.cost_ops` (MISSING)

  - `hoc.api.int.agent.api.costsim` (MISSING)

  - `hoc.api.int.agent.api.cus_enforcement` (MISSING)

  - `hoc.api.int.agent.api.cus_telemetry` (MISSING)

  - `hoc.api.int.agent.api.customer_visibility` (MISSING)

  - `hoc.api.int.agent.api.datasources` (MISSING)

  - `hoc.api.int.agent.api.debug_auth` (MISSING)

  - `hoc.api.int.agent.api.detection` (MISSING)

  - `hoc.api.int.agent.api.discovery` (MISSING)

  - `hoc.api.int.agent.api.embedding` (MISSING)

  - `hoc.api.int.agent.api.evidence` (MISSING)

  - `hoc.api.int.agent.api.feedback` (MISSING)

  - `hoc.api.int.agent.api.founder_actions` (MISSING)

  - `hoc.api.int.agent.api.founder_contract_review` (MISSING)

  - `hoc.api.int.agent.api.founder_explorer` (MISSING)

  - `hoc.api.int.agent.api.founder_onboarding` (MISSING)

  - `hoc.api.int.agent.api.founder_review` (MISSING)

  - `hoc.api.int.agent.api.founder_timeline` (MISSING)

  - `hoc.api.int.agent.api.guard` (MISSING)

  - `hoc.api.int.agent.api.guard_logs` (MISSING)

  - `hoc.api.int.agent.api.guard_policies` (MISSING)

  - `hoc.api.int.agent.api.health` (MISSING)

  - `hoc.api.int.agent.api.incidents` (MISSING)

  - `hoc.api.int.agent.api.legacy_routes` (MISSING)

  - `hoc.api.int.agent.api.lifecycle` (MISSING)

  - `hoc.api.int.agent.api.limits.override` (MISSING)

  - `hoc.api.int.agent.api.limits.simulate` (MISSING)

  - `hoc.api.int.agent.api.logs` (MISSING)

  - `hoc.api.int.agent.api.memory_pins` (MISSING)

  - `hoc.api.int.agent.api.monitors` (MISSING)

  - `hoc.api.int.agent.api.notifications` (MISSING)

  - `hoc.api.int.agent.api.onboarding` (MISSING)

  - `hoc.api.int.agent.api.ops` (MISSING)

  - `hoc.api.int.agent.api.overview` (MISSING)

  - `hoc.api.int.agent.api.platform` (MISSING)

  - `hoc.api.int.agent.api.policies` (MISSING)

  - `hoc.api.int.agent.api.policy` (MISSING)

  - `hoc.api.int.agent.api.policy_layer` (MISSING)

  - `hoc.api.int.agent.api.policy_limits_crud` (MISSING)

  - `hoc.api.int.agent.api.policy_proposals` (MISSING)

  - `hoc.api.int.agent.api.policy_rules_crud` (MISSING)

  - `hoc.api.int.agent.api.predictions` (MISSING)

  - `hoc.api.int.agent.api.rate_limits` (MISSING)

  - `hoc.api.int.agent.api.rbac_api` (MISSING)

  - `hoc.api.int.agent.api.recovery` (MISSING)

  - `hoc.api.int.agent.api.recovery_ingest` (MISSING)

  - `hoc.api.int.agent.api.replay` (MISSING)

  - `hoc.api.int.agent.api.retrieval` (MISSING)

  - `hoc.api.int.agent.api.runtime` (MISSING)

  - `hoc.api.int.agent.api.scenarios` (MISSING)

  - `hoc.api.int.agent.api.scheduler` (MISSING)

  - `hoc.api.int.agent.api.sdk` (MISSING)

  - `hoc.api.int.agent.api.session_context` (MISSING)

  - `hoc.api.int.agent.api.status_history` (MISSING)

  - `hoc.api.int.agent.api.tenants` (MISSING)

  - `hoc.api.int.agent.api.traces` (MISSING)

  - `hoc.api.int.agent.api.v1_killswitch` (MISSING)

  - `hoc.api.int.agent.api.v1_proxy` (MISSING)

  - `hoc.api.int.agent.api.workers` (MISSING)


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


## Orchestrator Handlers Wiring

- Handlers defined: 24

- Handlers package imported by: 2 files (example `/root/agenticverz2.0/backend/app/main.py`)


## Dead/Unused Candidates (Refined)

- Total: 483

- By area (top 10):

  - `int`: 225

  - `cus`: 165

  - `api`: 84

  - `fdr`: 9


- Sample (first 60):

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
