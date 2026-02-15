# UC Expansion Context (UC-018..UC-032)

- Date: 2026-02-12
- Scope: `app/hoc/cus/{activity,incidents,policies,controls,analytics,logs}` and related L4 handlers
- Intent: provide concrete domain context so new usecases can be generated from existing scripts, validated in code, and promoted `RED -> YELLOW -> GREEN`.

## 1) Baseline Reality

From `USECASE_CODEBASE_UTILIZATION_AUDIT.md`:

| Domain | Scripts in Audit Scope | Touched | Untouched | Coverage |
|---|---:|---:|---:|---:|
| activity | 20 | 2 | 18 | 10.0% |
| incidents | 37 | 2 | 35 | 5.4% |
| policies | 97 | 0 | 97 | 0.0% |
| controls | 23 | 2 | 21 | 8.7% |
| analytics | 41 | 1 | 40 | 2.4% |
| logs | 42 | 3 | 39 | 7.1% |
| **Total** | **260** | **10** | **250** | **3.8%** |

Interpretation:
- Current `UC-001..UC-017` closure is narrow and valid for those slices.
- Domain-wide utilization is still low, especially `policies` and `analytics`.

## 2) Domain Context Anchors

Context source files:
- `literature/hoc_domain/<domain>/SOFTWARE_BIBLE.md`
- `literature/hoc_domain/<domain>/DOMAIN_CAPABILITY.md`

High-signal context by domain:
- `activity`: feed, ranking, pattern/cost analysis, signal feedback lifecycle, orphan recovery.
- `incidents`: incident detection/classification/resolution/recurrence/postmortem, plus recovery-rule decisioning surfaces.
- `policies`: DSL/runtime governance, proposals/rules/limits query surfaces, sandbox execution, snapshot/version integrity.
- `controls`: thresholds, overrides, policy-limit validation, scoped execution and circuit-breaker controls.
- `analytics`: anomaly detection, dataset validation, prediction cycle, snapshot baselines, cost write/read paths.
- `logs`: trace store/search/replay/integrity, evidence chain and certificates, redaction policy and deterministic replay checks.

Gap intensity observed from `DOMAIN_CAPABILITY.md`:
- analytics: 24 `No (gap)` rows
- incidents: 18 `No (gap)` rows
- logs: 7 `No (gap)` rows
- controls: 4 `No (gap)` rows
- activity: 0 `No (gap)` rows
- policies: 0 `No (gap)` rows (but still 0.0% touched in utilization audit slice)

## 3) Proposed Usecase Backlog (UC-018..UC-032)

Status for all below: `RED` (proposed, not yet registered in canonical index table).

| UC ID | Domain | Context to Validate | File/Function Anchors | Why It Matters |
|---|---|---|---|---|
| UC-018 | policies | Policy snapshot lifecycle + integrity verification | `app/hoc/cus/policies/L5_engines/snapshot_engine.py` (`create_policy_snapshot`, `get_snapshot_history`, `verify_snapshot`) | Snapshot/version integrity is core governance evidence but currently underused. |
| UC-019 | policies | Proposal query lifecycle (list/detail/drafts) | `app/hoc/cus/policies/L5_engines/policies_proposals_query_engine.py`, `app/hoc/cus/policies/L6_drivers/proposals_read_driver.py` | Turns proposal workflow into query-verifiable, deterministic surface. |
| UC-020 | policies | Policy rules query lifecycle (list/detail/count) | `app/hoc/cus/policies/L5_engines/policies_rules_query_engine.py`, `app/hoc/cus/policies/L6_drivers/policy_rules_read_driver.py` | Gives explicit contract for runtime policy visibility and auditability. |
| UC-021 | policies | Policy limits query lifecycle (limits/budgets/detail) | `app/hoc/cus/policies/L5_engines/policies_limits_query_engine.py`, `app/hoc/cus/controls/L6_drivers/limits_read_driver.py` | Links policy-governance limits to concrete retrieval semantics. |
| UC-022 | policies | Sandbox definition + execution telemetry lifecycle | `app/hoc/cus/policies/L5_engines/sandbox_engine.py` (`define_policy`, `list_policies`, `get_execution_records`, `get_execution_stats`), `app/hoc/cus/hoc_spine/orchestrator/handlers/policies_sandbox_handler.py` | Closes loop between sandbox API and governance runtime evidence. |
| UC-023 | policies | Conflict-resolution explainability | `app/hoc/cus/policies/L5_engines/policy_conflict_resolver.py`, `app/hoc/cus/policies/L6_drivers/optimizer_conflict_resolver.py` | Ensures deterministic, explainable conflict outcomes for policy DAG/precedence. |
| UC-024 | analytics | Cost anomaly detection lifecycle | `app/hoc/cus/analytics/L5_engines/cost_anomaly_detector_engine.py`, `app/hoc/cus/analytics/L6_drivers/cost_anomaly_driver.py` | Largest analytics gap cluster (`L2:cost_intelligence` marked `No (gap)`). |
| UC-025 | analytics | Prediction cycle lifecycle | `app/hoc/cus/analytics/L5_engines/prediction_engine.py`, `app/hoc/cus/analytics/L6_drivers/prediction_driver.py` | Closes `L2:predictions` gap rows (`predict_*`, `run_prediction_cycle`). |
| UC-026 | analytics | Dataset validation lifecycle | `app/hoc/cus/analytics/L5_engines/datasets_engine.py` (`validate_dataset`, `validate_all`) | Addresses `L2:costsim` gap rows and makes validation contract auditable. |
| UC-027 | analytics | Snapshot + baseline scheduled jobs | `app/hoc/cus/analytics/L5_engines/cost_snapshots_engine.py` (`run_hourly_snapshot_job`, `run_daily_snapshot_and_baseline_job`) | Uncalled job paths block confidence in trend/anomaly baselines. |
| UC-028 | analytics | Cost write lifecycle (record/tag/budget) | `app/hoc/cus/analytics/L5_engines/cost_write.py`, `app/hoc/cus/analytics/L6_drivers/cost_write_driver.py` | Uncalled write path means missing testable provenance for write-side analytics. |
| UC-029 | incidents | Recovery-rule evaluation lifecycle | `app/hoc/cus/incidents/L5_engines/recovery_rule_engine.py` (`evaluate_rules`, `suggest_recovery_mode`, `should_auto_execute`) | Incidents `No (gap)` rows are concentrated here (`L2:recovery`). |
| UC-030 | incidents | Policy-violation truth pipeline | `app/hoc/cus/incidents/L5_engines/policy_violation_engine.py` (`persist_violation_and_create_incident`, `verify_violation_truth`, `handle_policy_violation`), `app/hoc/cus/incidents/L6_drivers/policy_violation_driver.py` | Converts currently pending design-ahead functions into verified production path. |
| UC-031 | incidents | Pattern + postmortem learnings lifecycle | `app/hoc/cus/incidents/L5_engines/incident_pattern.py`, `app/hoc/cus/incidents/L5_engines/postmortem.py`, `app/hoc/cus/incidents/L6_drivers/incident_pattern_driver.py`, `app/hoc/cus/incidents/L6_drivers/postmortem_driver.py` | Validates root-cause and learnings pipeline, not just incident CRUD. |
| UC-032 | logs | Redaction governance and trace-safe export | `app/hoc/cus/logs/L5_engines/redact.py`, `app/hoc/cus/logs/L6_drivers/redact.py` (`redact_*`, `add_sensitive_field`, `add_redaction_pattern`) | `DOMAIN_CAPABILITY` shows explicit `No (gap)` rows at L2 traces redaction surfaces. |

## 4) Execution Order (Recommended)

Wave 1 (highest leverage):
1. UC-024 analytics anomaly detection
2. UC-025 analytics prediction cycle
3. UC-029 incidents recovery-rule evaluation
4. UC-018 policies snapshot lifecycle
5. UC-032 logs redaction governance

Wave 2:
1. UC-026 dataset validation
2. UC-027 snapshot jobs
3. UC-030 policy-violation truth pipeline
4. UC-019 proposals query lifecycle
5. UC-020 rules query lifecycle

Wave 3:
1. UC-021 limits query lifecycle
2. UC-022 sandbox lifecycle
3. UC-023 conflict explainability
4. UC-028 cost write lifecycle
5. UC-031 incidents pattern/postmortem lifecycle

## 5) Promotion Contract Per Candidate

For each UC candidate:
1. Add UC section to `HOC_USECASE_CODE_LINKAGE.md` with initial `RED`.
2. Add row to `INDEX.md` registry (same UC ID/status).
3. Provide L2 -> L4 -> L5 -> L6 file-level evidence.
4. Add/execute verifier(s): route-operation map, event contract, storage contract, determinism where applicable.
5. Promote `RED -> YELLOW -> GREEN` only with passing command output evidence.

## 6) Guardrails (Must Hold)

- Preserve `L2.1 -> L2 -> L4 -> L5 -> L6 -> L7`.
- No direct `L2 -> L5/L6`.
- Engines decide; drivers perform effects.
- No new `*_service.py` in HOC.
- Keep changes minimal and reversible; no file moves/deletes without explicit approval.
