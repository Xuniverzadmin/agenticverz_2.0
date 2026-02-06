# HOC Audit Report (Static Import Scan)

## Scope

- Directory: `backend/app/hoc`

- Method: static AST scan for missing imports and unreferenced modules

- Note: dynamic imports, runtime registration, and tests may make some items false positives


## Missing / Broken Imports (Internal Only)

- Parse errors: 7 (first 5 listed)

  - `/root/agenticverz2.0/backend/app/hoc/int/platform/drivers/stub_planner.py`: unexpected indent (<unknown>, line 41)

  - `/root/agenticverz2.0/backend/app/hoc/int/agent/drivers/json_transform_stub.py`: unexpected indent (<unknown>, line 28)

  - `/root/agenticverz2.0/backend/app/hoc/int/agent/drivers/registry_v2.py`: unexpected indent (<unknown>, line 36)

  - `/root/agenticverz2.0/backend/app/hoc/int/agent/drivers/llm_invoke_governed.py`: unexpected indent (<unknown>, line 37)

  - `/root/agenticverz2.0/backend/app/hoc/int/agent/engines/http_call_stub.py`: unexpected indent (<unknown>, line 29)

- Missing module targets: 305

  - `hoc.api.cus.schemas.response` — 13 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/cus/policies/M25_integrations.py`)

  - `hoc.api.cus.db` — 13 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/cus/policies/policy_proposals.py`)

  - `hoc.cus.integrations.adapters.base` — 10 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/cus/integrations/adapters/smtp_adapter.py`)

  - `hoc.int.agent.engines.panel_types` — 9 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/agent/engines/panel_verification_engine.py`)

  - `hoc.int.agent.schemas.skill` — 7 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/agent/drivers/kv_store.py`)

  - `hoc.api.cus.auth.onboarding_transitions` — 6 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/cus/agent/onboarding.py`)

  - `hoc.cus.controls.L6_drivers.scoped_execution` — 5 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/cus/recovery/recovery.py`)

  - `hoc.api.cus.memory.iaec` — 5 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/cus/api_keys/embedding.py`)

  - `hoc.int.agent.engines.semantic_types` — 4 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/agent/engines/semantic_validator.py`)

  - `hoc.int.general.models.tenant` — 4 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/general/engines/role_guard.py`)

  - `hoc.api.cus.auth.gateway_middleware` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/cus/policies/policy_proposals.py`)

  - `hoc.api.fdr.auth.console_auth` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/fdr/account/founder_explorer.py`)

  - `hoc.api.fdr.schemas.response` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/fdr/account/founder_explorer.py`)

  - `hoc.api.int.agent.db` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/int/agent/main.py`)

  - `hoc.int.platform.agents.sba` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/platform/drivers/care.py`)

  - `models.run` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/policies/engines/policy_checker.py`)

  - `core.idempotency` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/policies/engines/job_queue_worker.py`)

  - `hoc.int.agent.services.credit_service` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/agent/drivers/blackboard_ops.py`)

  - `hoc.int.agent.drivers.registry` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/agent/drivers/kv_store.py`)

  - `hoc.int.agent.engines.panel_consistency_checker` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/agent/engines/panel_metrics_emitter.py`)

  - `hoc.int.account.drivers.tier_gating` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/account/drivers/tenant_auth.py`)

  - `hoc.int.api_keys.db` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/api_keys/engines/onboarding_transitions.py`)

  - `hoc.int.api_keys.models.tenant` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/api_keys/engines/onboarding_transitions.py`)

  - `hoc.int.general.engines.contexts` — 3 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/general/engines/route_planes.py`)

  - `hoc.int.platform.facades` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/cus/hoc_spine/orchestrator/plan_generation_engine.py`)

  - `hoc.cus.logs.L6_drivers.audit_ledger_service_async` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py`)

  - `hoc.cus.hoc_spine.orchestrator.lifecycle.engines.base` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/engines/onboarding.py`)

  - `hoc.api.cus.auth.console_auth` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/cus/policies/M25_integrations.py`)

  - `hoc.api.cus.auth.authority` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/cus/policies/replay.py`)

  - `hoc.api.cus.auth` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/cus/analytics/feedback.py`)

  - `hoc.api.cus.memory.embedding_cache` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/cus/api_keys/embedding.py`)

  - `hoc.api.cus.agents.sba` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/cus/general/agents.py`)

  - `hoc.api.cus.routing` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/cus/general/agents.py`)

  - `hoc.api.fdr.auth.onboarding_transitions` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/fdr/incidents/founder_onboarding.py`)

  - `hoc.api.int.agent.auth.gateway_config` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/int/agent/main.py`)

  - `hoc.api.int.agent.events.reactor_initializer` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/api/int/agent/main.py`)

  - `hoc.int.platform.drivers.engine` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/platform/drivers/policies.py`)

  - `hoc.int.platform.drivers.models` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/platform/drivers/care.py`)

  - `hoc.int.platform.engines.policies` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/platform/engines/errors.py`)

  - `models.policy_rule` — 2 occurrences (e.g. `/root/agenticverz2.0/backend/app/hoc/int/policies/engines/policy_checker.py`)


## Dead/Unused Code Candidates (Not Imported via app.* or relative)

- Total candidates: 458

- By area (top 10):

  - `int`: 208

  - `cus`: 156

  - `api`: 85

  - `fdr`: 9


- Sample candidates (first 40):

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

  - `hoc.cus.hoc_spine.schemas.skill`

  - `hoc.cus.hoc_spine.schemas.agent`

  - `hoc.cus.hoc_spine.schemas.common`

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
