# Domain Linkage Plan v1 (HOC)

**Date:** 2026-02-09
**Scope:** LLM run monitoring linkages across Activity, Incidents, Policies, Logs.

## Evidence Sources (Observed)
- `backend/app/db.py`
- `backend/app/models/killswitch.py`
- `backend/app/models/logs_records.py`
- `backend/app/models/policy_control_plane.py`
- `backend/app/models/audit_ledger.py`
- `backend/app/hoc/cus/activity/L6_drivers/activity_read_driver.py`
- `backend/app/hoc/cus/activity/L6_drivers/run_signal_driver.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/run_evidence_coordinator.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/run_proof_coordinator.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/incidents_bridge.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/policies_bridge.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/logs_bridge.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py`
- `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/run_governance_handler.py`
- `backend/app/hoc/cus/incidents/L5_engines/incident_engine.py`
- `backend/app/hoc/cus/incidents/L5_engines/incident_write_engine.py`
- `backend/app/hoc/cus/incidents/L5_engines/policy_violation_engine.py`
- `backend/app/hoc/cus/incidents/L5_engines/incident_read_engine.py`
- `backend/app/hoc/cus/incidents/L6_drivers/policy_violation_driver.py`
- `backend/app/hoc/cus/incidents/L6_drivers/incident_write_driver.py`
- `backend/app/hoc/cus/activity/L6_drivers/run_signal_driver.py`
- `backend/app/hoc/cus/activity/L6_drivers/run_metrics_driver.py`
- `backend/app/hoc/cus/logs/L5_engines/logs_facade.py`
- `backend/app/hoc/cus/logs/L6_drivers/logs_domain_store.py`
- `backend/app/hoc/cus/logs/L6_drivers/pg_store.py`
- `backend/app/hoc/cus/logs/L6_drivers/export_bundle_store.py`
- `backend/app/hoc/cus/policies/L6_drivers/policy_enforcement_driver.py`
- `backend/alembic/versions/107_v_runs_o2_policy_context.py`

## Data Inventory (Run-Correlation Fields)

### runs (table: `runs`)
- Correlation keys: `id` (run ID), `tenant_id`.
- Lifecycle: `state`, `status`, `started_at`, `completed_at`, `duration_ms`.
- Signals: `risk_level` (string), `incident_count`, `policy_draft_count`, `policy_violation`.
- Cost: `input_tokens`, `output_tokens`, `estimated_cost_usd`.
- Evidence: `evidence_health`, `integrity_status`.
- Source: `source`, `provider_type`.
- Governance linkage: `policy_snapshot_id`, `termination_reason`, `stopped_at_step`, `violation_policy_id`.
- Observability: `observability_status`, `observability_error`.

### v_runs_o2 (view)
- Projects run data for Activity panels.
- Includes `run_id`, `risk_level`, `incident_count`, `policy_violation`, `policy_draft_count`.
- Adds policy context fields (`policy_id`, `policy_name`, `limit_type`, `evaluation_outcome`, `proximity_pct`).

### incidents (table: `incidents`)
- Run linkage: `source_run_id` (canonical), `llm_run_id` (tombstoned).
- Governance: `trigger_type`, `category`, `severity`, `status`, `created_at`.

### policy_enforcements (table: `policy_enforcements`)
- Run linkage: `run_id` (FK to `runs.id`).
- Incident linkage: `incident_id` (FK to `incidents.id`).
- Rule linkage: `rule_id`.
- Enforcement fields: `action_taken`, `details`, `triggered_at`.

### prevention_records (table: `prevention_records`)
- Observed columns in insert paths: `id`, `policy_id`, `pattern_id`, `original_incident_id`, `blocked_incident_id`,
  `run_id`, `tenant_id`, `outcome`, `signature_match_confidence`, `created_at`, `is_synthetic`, `synthetic_scenario_id`.
- Used for policy evaluation records and policy violation facts (based on L6 inserts).

### llm_run_records (table: `llm_run_records`)
- Run linkage: `run_id`, `tenant_id`, `trace_id`.
- Execution: `execution_status`, `started_at`, `completed_at`.
- Cost: `input_tokens`, `output_tokens`, `cost_cents`.
- Source: `provider`, `model`, `source`, `is_synthetic`, `synthetic_scenario_id`.

### aos_traces (table: `aos_traces`)
- Run linkage: `run_id`, `tenant_id`, `trace_id`.
- Incident linkage: `incident_id`.
- Trace fields: `correlation_id`, `agent_id`, `root_hash`, `plan`, `trace`, `schema_version`, `status`,
  `started_at`, `created_at`, `completed_at` (updated later), `metadata` (updated later),
  `is_synthetic`, `synthetic_scenario_id`.

### aos_trace_steps (table: `aos_trace_steps`)
- Trace linkage: `trace_id`, `step_index`.
- Step fields: `timestamp`, `skill_name`, `status`, `outcome_category`, `outcome_code`, `outcome_data`,
  `cost_cents`, `duration_ms`, `retry_count`, `params`, `source`, `level`, `is_synthetic`, `synthetic_scenario_id`.

### audit_ledger (table: `audit_ledger`)
- Governance events: `event_type`, `entity_type`, `entity_id`, `actor_type`, `actor_id`, `before_state`, `after_state`, `created_at`.
- Run linkage: `after_state.run_id` (for incident audit events) when present.

## Observed Linkage Paths (Current)

1. **Run lifecycle → Activity**
- Activity reads from `v_runs_o2` (built from `runs` + policy context view).

2. **Run lifecycle → Incidents**
- Incident creation sets `incidents.source_run_id` and increments `runs.incident_count`.
- Incident creation propagates `incident_id` to `aos_traces` for trace correlation.

3. **Run lifecycle → Logs**
- Worker creates `llm_run_records` with `run_id` and (optional) `trace_id`.
- Logs facade reads `llm_run_records` and `aos_traces` using `run_id`.

4. **Run lifecycle → Policies**
- Policy enforcement records link `run_id` in `policy_enforcements`.
- Policy evaluation records are inserted into `prevention_records` with `blocked_incident_id = run_id`.

5. **Run evidence/proof (L4 cross-domain)**
- `RunEvidenceCoordinator` aggregates incidents (by `source_run_id`) + policy evaluations (from `prevention_records`) + limits for a `run_id`.
- `RunProofCoordinator` fetches traces via Logs bridge (Postgres in prod) and computes integrity proofs.

6. **Run lifecycle → Governance logs**
- `LogsFacade.get_llm_run_governance` filters audit ledger events by `run_id` when present in `after_state`.
- Incident write audit events embed `run_id` for correlation.

## Observed Gaps and Suggested Fixes

1. **Run-scoped governance logs are partial**
- `get_llm_run_governance()` now filters by `run_id` using `after_state`, but only entries that embed `run_id` are returned.
- Incident audit events embed `run_id`; policy rule/proposal/limit events still lack run-scoped fields.
- Suggested fix: include `run_id` in audit writes where available (e.g., limit breach, enforcement) or extend schema if allowed.

2. **Risk level type mismatch — RESOLVED (2026-02-09)**
- `RunSignalDriver` now maps signals to string risk levels (NORMAL, NEAR_THRESHOLD, AT_RISK, VIOLATED).

3. **Missing writers for `runs.policy_violation` and `runs.policy_draft_count` — RESOLVED (2026-02-09)**
- `RunGovernanceHandler.report_violation` now sets `runs.policy_violation = true`.
- `PoliciesLessonsHandler.convert_lesson_to_draft` increments `runs.policy_draft_count` when `source_run_id` is present.

4. **Audit Ledger run linkage is implicit only**
- `audit_ledger` lacks `run_id`; run correlation relies on optional `after_state` data.
- Suggested fix: enforce `run_id` embedding in `after_state` for run-scoped events, or extend the table with `run_id` if allowed.

## Implementation Notes (Non-Goals)
- This plan does not change layer authority or introduce new domains.
- Fixes should be implemented through L4 wiring, L5 business logic, and L6 persistence per HOC rules.

---

## Domain Inventory (Structural)

| Domain | L5 Engines | L6 Drivers | L5 Schemas | L2.1 Facade |
|--------|-----------|-----------|-----------|-------------|
| account | 8 | 7 | 9 | `facades/cus/account.py` |
| activity | 9 | 5 | 1 | `facades/cus/activity.py` |
| analytics | 19 | 14 | 6 | `facades/cus/analytics.py` |
| api_keys | 3 | 3 | 1 | `facades/cus/api_keys.py` |
| controls | 4 | 11 | 5 | `facades/cus/controls.py` |
| incidents | 15 | 14 | 3 | `facades/cus/incidents.py` |
| integrations | 13 | 9 | 7 | `facades/cus/integrations.py` |
| logs | 17 | 17 | 3 | `facades/cus/logs.py` |
| ops | 2 | 2 | 0 | (via handlers) |
| overview | 2 | 2 | 1 | `facades/cus/overview.py` |
| policies | 57 | (in L5) | 4 | `facades/cus/policies.py` |

## Execution Boundary Baseline

**Source:** `scripts/ops/l5_spine_pairing_gap_detector.py`
**Baseline:** `docs/architecture/hoc/L2_L4_L5_BASELINE.json` (2026-02-08)

| Metric | Value |
|--------|-------|
| total_l5_engines | 66 |
| wired_via_l4 | 66 |
| direct_l2_to_l5 | 0 |
| orphaned | 0 |

## L4 Handler Wiring (40 Handlers)

All domain operations route through `hoc_spine/orchestrator/operation_registry.py`.

| Handler | Domain |
|---------|--------|
| account_handler | account |
| activity_handler | activity |
| analytics_handler | analytics |
| analytics_config_handler | analytics |
| analytics_metrics_handler | analytics |
| analytics_prediction_handler | analytics |
| analytics_sandbox_handler | analytics |
| analytics_snapshot_handler | analytics |
| analytics_validation_handler | analytics |
| api_keys_handler | api_keys |
| circuit_breaker_handler | controls |
| controls_handler | controls |
| governance_audit_handler | cross-domain |
| idempotency_handler | cross-domain |
| incidents_handler | incidents |
| integration_bootstrap_handler | integrations |
| integrations_handler | integrations |
| killswitch_handler | controls |
| knowledge_planes_handler | integrations |
| lifecycle_handler | account |
| logs_handler | logs |
| mcp_handler | integrations |
| m25_integration_handler | integrations |
| onboarding_handler | account |
| ops_handler | ops |
| overview_handler | overview |
| orphan_recovery_handler | cross-domain |
| platform_handler | cross-domain |
| policies_handler | policies |
| policies_sandbox_handler | policies |
| policy_approval_handler | policies |
| policy_governance_handler | policies |
| proxy_handler | integrations |
| run_governance_handler | cross-domain |
| system_handler | cross-domain |
| traces_handler | logs |

## Bridge Linkage Map (L4 Cross-Domain Coordination)

| Bridge | Domain(s) | Capabilities |
|--------|-----------|-------------|
| account_bridge | account | Account capability factory |
| activity_bridge | activity | Activity signals |
| analytics_bridge | analytics | config, sandbox, canary, divergence, datasets, detection |
| api_keys_bridge | api_keys | Key management |
| incidents_bridge | incidents | recovery_rule_engine |
| integrations_bridge | integrations | mcp_tool, connectors, health, datasources, cus_integration |
| logs_bridge | logs | Log retrieval |
| overview_bridge | overview | overview_facade |
| policies_bridge | policies | prevention_hook, sandbox_engine |

**Bridge rules:** Max 5 capabilities, lazy imports, returns modules not instances.

## Non-Bridge Coordinators

| Coordinator | Cross-Domain Scope |
|-------------|-------------------|
| anomaly_incident_coordinator | analytics → incidents |
| canary_coordinator | analytics canary validation |
| evidence_coordinator | cross-domain evidence capture |
| execution_coordinator | run orchestration |
| lessons_coordinator | incident → lessons learned |
| provenance_coordinator | cost provenance |
| signal_coordinator | cross-domain signals |
| transaction_coordinator | distributed transactions |

## CI Guards Protecting Linkage

| Check | Rule | Enforcement |
|-------|------|-------------|
| 25 | L5 no DB module imports | BLOCKING |
| 27 | L2 no direct L5/L6 imports | BLOCKING (8-file allowlist) |
| 28 | L5 no cross-domain L5 imports | BLOCKING (2-file allowlist) |
| 29 | Driver no L5 engine imports | BLOCKING (3-file allowlist) |
| 30 | Facade logic minimum | Advisory |

## Transaction Boundary Ownership

| Layer | Ownership | Allowed |
|-------|----------|---------|
| L4 Handler | OWNS begin/commit/rollback | Calls L5/L6 |
| L5 Engine | Passes to L4 | session.add(), session.flush() |
| L6 Driver | Passes to L4 | session.add(), session.execute() |

Purity status: 0 blocking, 0 advisory, 0 exemptions (PIN-520).
