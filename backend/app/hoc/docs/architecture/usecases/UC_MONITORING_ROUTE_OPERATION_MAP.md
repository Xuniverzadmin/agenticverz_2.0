# UC-MON Route-to-Operation Map

## Canonical Root
- `backend/app/hoc/docs/architecture/usecases/`

## Scope
- Audience: `cust`
- Domains: `activity`, `incidents`, `controls`, `analytics`, `logs`, `policies`
- Architecture: L2 → L4 `hoc_spine` → L5 → L6 → L7

## Verifier
- `backend/scripts/verification/uc_mon_route_operation_map_check.py`

---

## Activity Domain

**L2 file:** `app/hoc/api/cus/activity/activity.py`
**L4 handler:** `ActivityQueryHandler` → operation key `activity.query`
**L5 entry:** `activity_facade.py` → `ActivityFacade`
**L6 drivers:** `activity_read_driver.py`, `run_signal_driver.py`, `run_metrics_driver.py`

| Method | Path | L2 Function | L4 Op | L5 Method | L6 Method | as_of | UC-MON |
|--------|------|-------------|-------|-----------|-----------|-------|--------|
| GET | `/activity/runs` | `list_runs` | `activity.query` | `get_runs` | `fetch_runs` | TODO | 01,04 |
| GET | `/activity/runs/{run_id}` | `get_run_detail` | `activity.query` | `get_run_detail` | `fetch_run_detail` | TODO | 01,04 |
| GET | `/activity/summary/by-status` | `get_summary_by_status` | `activity.query` | `get_status_summary` | `fetch_status_summary` | TODO | 03,04 |
| GET | `/activity/runs/live/by-dimension` | `get_live_runs_by_dimension` | `activity.query` | `get_dimension_breakdown` | `fetch_dimension_breakdown` | n/a | 04 |
| GET | `/activity/runs/completed/by-dimension` | `get_completed_runs_by_dimension` | `activity.query` | `get_dimension_breakdown` | `fetch_dimension_breakdown` | TODO | 04,06 |
| GET | `/activity/runs/by-dimension` | `get_runs_by_dimension` | `activity.query` | `get_dimension_breakdown` | `fetch_dimension_breakdown` | TODO | 04 |
| GET | `/activity/patterns` | `get_patterns` | `activity.query` | `get_patterns` | `PatternDetectionService` | TODO | 03,06 |
| GET | `/activity/cost-analysis` | `get_cost_analysis` | `activity.query` | `get_cost_analysis` | `CostAnalysisService` | TODO | 06 |
| GET | `/activity/attention-queue` | `get_attention_queue` | `activity.query` | `get_attention_queue` | `AttentionRankingService` | TODO | 04 |
| GET | `/activity/risk-signals` | `get_risk_signals` | `activity.query` | `get_risk_signals` | `fetch_metrics` | TODO | 03,04 |
| GET | `/activity/live` | `list_live_runs` | `activity.query` | `get_live_runs` | `fetch_runs_with_policy_context` | n/a | 01,04 |
| GET | `/activity/completed` | `list_completed_runs` | `activity.query` | `get_completed_runs` | `fetch_runs_with_policy_context` | TODO | 04,06 |
| GET | `/activity/signals` | `list_signals` | `activity.query` | `get_signals` | `fetch_at_risk_runs` | TODO | 03,04 |
| GET | `/activity/metrics` | `get_activity_metrics` | `activity.query` | `get_metrics` | `fetch_metrics` | TODO | 03,06 |
| GET | `/activity/threshold-signals` | `get_threshold_signals` | `activity.query` | `get_threshold_signals` | `fetch_threshold_signals` | TODO | 02,04 |
| POST | `/activity/signals/{fp}/ack` | `acknowledge_signal` | `activity.query` | `acknowledge_signal` | `SignalFeedbackService` | n/a | 04 |
| POST | `/activity/signals/{fp}/suppress` | `suppress_signal` | `activity.query` | `suppress_signal` | `SignalFeedbackService` | n/a | 04 |

**Preflight-only (EXEMPT):**
| GET | `/activity/runs/{run_id}/evidence` | `get_run_evidence` | EXEMPT | stub | n/a | n/a | — |
| GET | `/activity/runs/{run_id}/proof` | `get_run_proof` | EXEMPT | stub | n/a | n/a | — |

---

## Incidents Domain

**L2 file:** `app/hoc/api/cus/incidents/incidents.py`
**L4 handler:** `IncidentsQueryHandler` → operation key `incidents.query`
**L5 entry:** `incidents_facade.py` → `IncidentsFacade`
**L6 drivers:** `incident_read_driver.py`, `incident_write_driver.py`, `incidents_facade_driver.py`

| Method | Path | L2 Function | L4 Op | L5 Method | L6 Method | as_of | UC-MON |
|--------|------|-------------|-------|-----------|-----------|-------|--------|
| GET | `/incidents` | `list_incidents` | `incidents.query` | `list_incidents` | `fetch_all_incidents` | TODO | 05 |
| GET | `/incidents/by-run/{run_id}` | `get_incidents_for_run` | `incidents.query` | `get_incidents_for_run` | `fetch_incidents_by_run` | TODO | 01,05 |
| GET | `/incidents/patterns` | `detect_patterns` | `incidents.query` | `detect_patterns` | `IncidentPatternService` | TODO | 05 |
| GET | `/incidents/recurring` | `analyze_recurrence` | `incidents.query` | `analyze_recurrence` | `RecurrenceAnalysisService` | TODO | 05 |
| GET | `/incidents/cost-impact` | `analyze_cost_impact` | `incidents.query` | `analyze_cost_impact` | `fetch_cost_impact_data` | TODO | 05,06 |
| GET | `/incidents/active` | `list_active_incidents` | `incidents.query` | `list_active_incidents` | `fetch_active_incidents` | TODO | 05 |
| GET | `/incidents/resolved` | `list_resolved_incidents` | `incidents.query` | `list_resolved_incidents` | `fetch_resolved_incidents` | TODO | 05 |
| GET | `/incidents/historical` | `list_historical_incidents` | `incidents.query` | `list_historical_incidents` | `fetch_historical_incidents` | TODO | 05 |
| GET | `/incidents/metrics` | `get_incident_metrics` | `incidents.query` | `get_metrics` | `fetch_metrics_aggregates` | TODO | 05 |
| GET | `/incidents/historical/trend` | `get_historical_trend` | `incidents.query` | `get_historical_trend` | `fetch_historical_trend` | TODO | 05,06 |
| GET | `/incidents/historical/distribution` | `get_historical_distribution` | `incidents.query` | `get_historical_distribution` | `fetch_historical_distribution` | TODO | 05,06 |
| GET | `/incidents/historical/cost-trend` | `get_historical_cost_trend` | `incidents.query` | `get_historical_cost_trend` | `fetch_historical_cost_trend` | TODO | 05,06 |
| GET | `/incidents/{incident_id}` | `get_incident_detail` | `incidents.query` | `get_incident_detail` | `fetch_incident_by_id` | TODO | 05 |
| GET | `/incidents/{incident_id}/learnings` | `get_incident_learnings` | `incidents.query` | `get_incident_learnings` | `PostMortemService` | TODO | 05 |
| POST | `/{incident_id}/export/evidence` | `export_evidence` | `incidents.export` | ExportEngine | ExportEngine | n/a | 05 |
| POST | `/{incident_id}/export/soc2` | `export_soc2` | `incidents.export` | ExportEngine | ExportEngine | n/a | 05 |
| POST | `/{incident_id}/export/executive-debrief` | `export_executive_debrief` | `incidents.export` | ExportEngine | ExportEngine | n/a | 05 |

**Preflight-only (EXEMPT):**
| GET | `/incidents/{incident_id}/evidence` | `get_incident_evidence` | EXEMPT | stub | n/a | n/a | — |
| GET | `/incidents/{incident_id}/proof` | `get_incident_proof` | EXEMPT | stub | n/a | n/a | — |

---

## Controls Domain

**L2 file:** `app/hoc/api/cus/controls/controls.py`
**L4 handler:** `ControlsQueryHandler` → operation key `controls.query`
**L5 entry:** `controls_facade.py` → `ControlsFacade`
**L6 drivers:** in-memory (no persistent L6 for core controls)

| Method | Path | L2 Function | L4 Op | L5 Method | L6 Method | as_of | UC-MON |
|--------|------|-------------|-------|-----------|-----------|-------|--------|
| GET | `/controls` | `list_controls` | `controls.query` | `list_controls` | in-memory | TODO | 02,03 |
| GET | `/controls/status` | `get_status` | `controls.query` | `get_status` | in-memory | returned | 02,03 |
| GET | `/controls/{control_id}` | `get_control` | `controls.query` | `get_control` | in-memory | TODO | 02 |
| PUT | `/controls/{control_id}` | `update_control` | `controls.query` | `update_control` | in-memory | n/a | 02,07 |
| POST | `/controls/{control_id}/enable` | `enable_control` | `controls.query` | `enable_control` | in-memory | n/a | 02 |
| POST | `/controls/{control_id}/disable` | `disable_control` | `controls.query` | `disable_control` | in-memory | n/a | 02 |

---

## Analytics Domain

### Feedback (`analytics.feedback`)

**L2 file:** `app/hoc/api/cus/analytics/feedback.py`
**L4 handler:** `FeedbackReadHandler` → operation key `analytics.feedback`
**L5 entry:** `feedback_read_engine.py`
**L6 driver:** `feedback_read_driver.py`

| Method | Path | L2 Function | L4 Op | L5 Method | L6 Method | as_of | UC-MON |
|--------|------|-------------|-------|-----------|-----------|-------|--------|
| GET | `/feedback` | `list_feedback` | `analytics.feedback` | `list_feedback` | `fetch_feedback_list` | TODO | 04,06 |
| GET | `/feedback/{feedback_id}` | `get_feedback` | `analytics.feedback` | `get_feedback` | `fetch_feedback_by_id` | TODO | 04 |
| GET | `/feedback/stats/summary` | `get_feedback_stats` | `analytics.feedback` | `get_feedback_stats` | `fetch_feedback_stats` | TODO | 06 |

### Predictions (`analytics.prediction_read`)

**L2 file:** `app/hoc/api/cus/analytics/predictions.py`
**L4 handler:** `AnalyticsPredictionHandler` → operation key `analytics.prediction_read`
**L5 entry:** `prediction_read_engine.py`
**L6 driver:** `prediction_read_driver.py`

| Method | Path | L2 Function | L4 Op | L5 Method | L6 Method | as_of | UC-MON |
|--------|------|-------------|-------|-----------|-----------|-------|--------|
| GET | `/predictions` | `list_predictions` | `analytics.prediction_read` | `list_predictions` | `fetch_prediction_list` | TODO | 06 |
| GET | `/predictions/{prediction_id}` | `get_prediction` | `analytics.prediction_read` | `get_prediction` | `fetch_prediction_by_id` | TODO | 06 |
| GET | `/predictions/subject/{st}/{sid}` | `get_predictions_for_subject` | `analytics.prediction_read` | `get_predictions_for_subject` | `fetch_predictions_for_subject` | TODO | 06 |
| GET | `/predictions/stats/summary` | `get_prediction_stats` | `analytics.prediction_read` | `get_prediction_stats` | `fetch_prediction_stats` | TODO | 06 |

### Cost Simulation (`analytics.costsim.*`)

**L2 file:** `app/hoc/api/cus/analytics/costsim.py`
**L4 handlers:** multiple costsim handlers
**L5 entry:** various costsim engines
**L6 drivers:** costsim drivers

| Method | Path | L2 Function | L4 Op | as_of | UC-MON |
|--------|------|-------------|-------|-------|--------|
| GET | `/costsim/v2/status` | `get_sandbox_status` | `analytics.costsim.status` | TODO | 06 |
| POST | `/costsim/v2/simulate` | `simulate_v2` | `analytics.costsim.simulate` | n/a | 06 |
| GET | `/costsim/divergence` | `get_divergence_report` | `analytics.costsim.divergence` | TODO | 06 |
| GET | `/costsim/canary/reports` | `get_canary_reports` | `analytics.canary_reports` | TODO | 06 |
| GET | `/costsim/datasets` | `list_datasets` | `analytics.costsim.datasets` | TODO | 06 |
| GET | `/costsim/datasets/{dataset_id}` | `get_dataset_info` | `analytics.costsim.datasets` | TODO | 06 |

---

## Logs Domain

### Traces (`logs.traces_api`)

**L2 file:** `app/hoc/api/cus/logs/traces.py`
**L4 handler:** `LogsQueryHandler` (traces dispatch)
**L5 entry:** `trace_api_engine.py`
**L6 driver:** `pg_store.py` (PostgreSQL), `trace_store.py` (SQLite hybrid)

| Method | Path | L2 Function | L4 Op | L5 Method | L6 Method | as_of | UC-MON |
|--------|------|-------------|-------|-----------|-----------|-------|--------|
| GET | `/traces` | `list_traces` | `logs.traces_api` | `list_traces` | `pg_store.list` | TODO | 01 |
| POST | `/traces` | `store_trace` | `logs.traces_api` | `store_trace` | `pg_store.store` | n/a | 01 |
| GET | `/traces/{run_id}` | `get_trace` | `logs.traces_api` | `get_trace` | `pg_store.get` | TODO | 01 |
| GET | `/traces/by-hash/{root_hash}` | `get_trace_by_hash` | `logs.traces_api` | `get_trace_by_root_hash` | `pg_store` | TODO | 01 |
| GET | `/traces/compare/{r1}/{r2}` | `compare_traces` | `logs.traces_api` | `compare_traces` | `pg_store` | TODO | 01 |
| DELETE | `/traces/{run_id}` | `delete_trace` | `logs.traces_api` | `delete_trace` | `pg_store.delete` | n/a | 01 |
| POST | `/traces/cleanup` | `cleanup_old_traces` | `logs.traces_api` | `cleanup_old_traces` | `pg_store` | n/a | 01 |
| GET | `/traces/idempotency/{key}` | `check_idempotency` | `logs.traces_api` | idempotency engine | `idempotency_driver` | n/a | 01 |
| GET | `/traces/mismatches` | `list_all_mismatches` | `traces.list_mismatches` | `trace_mismatch_engine` | `trace_mismatch_driver` | TODO | 01 |
| POST | `/traces/mismatches/bulk-report` | `bulk_report_mismatches` | `traces.bulk_report_mismatches` | `trace_mismatch_engine` | `trace_mismatch_driver` | n/a | 01 |
| POST | `/traces/{tid}/mismatch` | `report_mismatch` | `traces.report_mismatch` | `trace_mismatch_engine` | `trace_mismatch_driver` | n/a | 01 |
| GET | `/traces/{tid}/mismatches` | `list_trace_mismatches` | `traces.list_trace_mismatches` | `trace_mismatch_engine` | `trace_mismatch_driver` | TODO | 01 |
| POST | `/traces/{tid}/mismatches/{mid}/resolve` | `resolve_mismatch` | `traces.resolve_mismatch` | `trace_mismatch_engine` | `trace_mismatch_driver` | n/a | 01 |

### Cost Intelligence (bridge-based)

**L2 file:** `app/hoc/api/cus/logs/cost_intelligence.py`
**L4 dispatch:** via bridge (not L4 registry)
**L5 entry:** `cost_intelligence_engine`
**L6 driver:** `cost_intelligence_driver.py`

| Method | Path | L2 Function | L4 Op | as_of | UC-MON |
|--------|------|-------------|-------|-------|--------|
| GET | `/cost/dashboard` | `get_cost_dashboard` | bridge | TODO | 06 |
| GET | `/cost/summary` | `get_cost_summary` | bridge | TODO | 06 |
| GET | `/cost/by-feature` | `get_costs_by_feature` | bridge | TODO | 06 |
| GET | `/cost/by-model` | `get_costs_by_model` | bridge | TODO | 06 |
| GET | `/cost/anomalies` | `get_anomalies` | bridge | TODO | 05,06 |
| GET | `/cost/projection` | `get_projection` | bridge | TODO | 06 |

---

## Policies Domain

**L2 files:** `app/hoc/api/cus/policies/policies.py` (primary CRUD)
**L4 handler:** `PoliciesQueryHandler` → various policy operations
**L5 entry:** `policy_rules_engine.py`, `policy_proposal_engine.py`
**L6 drivers:** `policy_read_driver.py`, `policy_write_driver.py`

| Method | Path | L2 Function | L4 Op | as_of | UC-MON |
|--------|------|-------------|-------|-------|--------|
| GET | `/policies` | `list_policies` | `policies.query` | TODO | 02,07 |
| POST | `/policies` | `create_policy` | `policies.query` | n/a | 07 |
| GET | `/policies/{id}` | `get_policy` | `policies.query` | TODO | 02 |
| PUT | `/policies/{id}` | `update_policy` | `policies.query` | n/a | 07 |
| DELETE | `/policies/{id}` | `delete_policy` | `policies.query` | n/a | 07 |
| POST | `/policies/{id}/enable` | `enable_policy` | `policies.query` | n/a | 02 |
| POST | `/policies/{id}/disable` | `disable_policy` | `policies.query` | n/a | 02 |

---

## Summary

| Domain | Routes | L4 Op Keys | Primary UC-MON |
|--------|--------|------------|----------------|
| activity | 17+2E | `activity.query` | 01, 03, 04, 06 |
| incidents | 17+2E | `incidents.query`, `incidents.export` | 01, 05, 06 |
| controls | 6 | `controls.query` | 02, 03, 07 |
| analytics | 13 | `analytics.feedback`, `.prediction_read`, `.costsim.*`, `.canary*` | 04, 06 |
| logs | 19 | `logs.traces_api`, `traces.*`, bridge | 01, 05, 06 |
| policies | 7 | `policies.query`, `policies.query` | 02, 07 |
| **Total** | **83** | | |

E = EXEMPT (preflight-only stubs)

## Deterministic Read Candidates (as_of required)

Priority endpoints where `as_of` contract should be formalized:

1. **Activity reads:** `/activity/runs`, `/activity/completed`, `/activity/signals`, `/activity/metrics`, `/activity/attention-queue`, `/activity/patterns`
2. **Incident reads:** `/incidents`, `/incidents/active`, `/incidents/resolved`, `/incidents/historical`, `/incidents/metrics`, `/incidents/patterns`
3. **Analytics reads:** `/feedback`, `/feedback/stats/summary`, `/predictions`, `/predictions/stats/summary`
4. **Logs reads:** `/traces`, `/traces/{run_id}`, `/traces/mismatches`

## Event Emissions Required (per UC-MON)

| UC-MON | Key Events | Domains |
|--------|------------|---------|
| 01 | `RunIngested`, `TraceCanonicalized`, `TracePersisted`, `EvidenceChainComputed` | logs, analytics, activity |
| 02 | `ControlsEvaluated`, `ControlDecisionApplied`, `ThresholdSignalEmitted`, `OverrideApplied` | controls, logs, activity |
| 03 | `BaselineLoaded`, `BaselineSignalsComputed`, `ControlProposalGenerated`, `AttentionQueueUpdated` | controls, analytics, activity |
| 04 | `SignalAcknowledged`, `SignalSuppressed` | activity, logs |
| 05 | `IncidentCreated`, `IncidentRunLinked`, `IncidentSeverityUpdated`, `IncidentResolved` | incidents, logs |
| 06 | `AnalyticsDatasetBuilt`, `AnomalyDetected`, `AnomalyAcknowledged`, `AnomalyResolved` | analytics, logs |
| 07 | `ControlProposalCreated`, `PolicyProposalCreated`, `ProposalAccepted`, `ProposalRejected` | controls, policies |
