# HOC CUS Script-vs-Usecase Matching - Iteration 3 Decision Table (2026-02-15)

## Scope
- Input set: 30 unresolved scripts from Iteration 1.
- Evidence sources:
  - handler operation registrations (`registry.register(...)`)
  - governance/verification tests under `backend/tests` and `backend/scripts/verification`
  - `UC_MONITORING_ROUTE_OPERATION_MAP.md` route-operation evidence
  - canonical basename anchors in `HOC_USECASE_CODE_LINKAGE.md`

## Decision Summary
- Generated at (UTC): `2026-02-15T06:53:26Z`
- `ASSIGN`: `7`
- `HOLD`: `15`
- `SPLIT`: `8`

## Decision Table
| Script | Linkage UC Hits | Handler Ops (key) | Route Ops | Decision | Assigned UC(s) |
| --- | --- | --- | --- | --- | --- |
| `app/hoc/cus/activity/L5_engines/activity_facade.py` | `-` | `activity.discovery;activity.orphan_recovery;activity.query;activity.signal_feedback;...` | `activity.query` | `HOLD` | `-` |
| `app/hoc/cus/activity/L5_engines/cus_telemetry_engine.py` | `-` | `activity.discovery;activity.orphan_recovery;activity.query;activity.signal_feedback;...` | `-` | `HOLD` | `-` |
| `app/hoc/cus/activity/L5_engines/signal_feedback_engine.py` | `UC-006` | `activity.discovery;activity.orphan_recovery;activity.query;activity.signal_feedback;...` | `-` | `ASSIGN` | `UC-006` |
| `app/hoc/cus/activity/L6_drivers/activity_read_driver.py` | `-` | `-` | `activity.query` | `HOLD` | `-` |
| `app/hoc/cus/activity/L6_drivers/cus_telemetry_driver.py` | `-` | `-` | `-` | `HOLD` | `-` |
| `app/hoc/cus/activity/L6_drivers/signal_feedback_driver.py` | `UC-006` | `-` | `-` | `ASSIGN` | `UC-006` |
| `app/hoc/cus/activity/adapters/customer_activity_adapter.py` | `-` | `-` | `-` | `HOLD` | `-` |
| `app/hoc/cus/analytics/L5_engines/feedback_read_engine.py` | `-` | `analytics.artifacts;analytics.canary;analytics.canary_reports;analytics.costsim.datasets;...` | `analytics.feedback;analytics.prediction_read` | `HOLD` | `-` |
| `app/hoc/cus/analytics/L6_drivers/analytics_artifacts_driver.py` | `UC-008` | `analytics.artifacts;analytics.canary;analytics.canary_reports;analytics.costsim.datasets;...` | `-` | `ASSIGN` | `UC-008` |
| `app/hoc/cus/analytics/L6_drivers/feedback_read_driver.py` | `-` | `-` | `analytics.feedback;analytics.prediction_read` | `HOLD` | `-` |
| `app/hoc/cus/controls/L6_drivers/evaluation_evidence_driver.py` | `UC-004` | `controls.circuit_breaker;controls.evaluation_evidence;controls.killswitch.read;controls.killswitch.write;...` | `-` | `ASSIGN` | `UC-004` |
| `app/hoc/cus/hoc_spine/authority/event_schema_contract.py` | `-` | `account.onboarding.advance;account.onboarding.query;activity.discovery;activity.orphan_recovery;...` | `-` | `SPLIT` | `UC-001|UC-002` |
| `app/hoc/cus/hoc_spine/authority/onboarding_policy.py` | `UC-002` | `account.onboarding.advance;account.onboarding.query` | `-` | `ASSIGN` | `UC-002` |
| `app/hoc/cus/hoc_spine/orchestrator/coordinators/signal_feedback_coordinator.py` | `-` | `-` | `-` | `HOLD` | `-` |
| `app/hoc/cus/hoc_spine/orchestrator/handlers/activity_handler.py` | `UC-006` | `activity.discovery;activity.orphan_recovery;activity.query;activity.signal_feedback;...` | `-` | `SPLIT` | `UC-001|UC-006|UC-010` |
| `app/hoc/cus/hoc_spine/orchestrator/handlers/controls_handler.py` | `-` | `controls.circuit_breaker;controls.evaluation_evidence;controls.killswitch.read;controls.killswitch.write;...` | `-` | `SPLIT` | `UC-004|UC-021` |
| `app/hoc/cus/hoc_spine/orchestrator/handlers/incidents_handler.py` | `-` | `-` | `-` | `SPLIT` | `UC-007|UC-011|UC-031` |
| `app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py` | `UC-002` | `account.onboarding.advance;account.onboarding.query` | `-` | `ASSIGN` | `UC-002` |
| `app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py` | `UC-018` | `-` | `-` | `SPLIT` | `UC-018|UC-019|UC-020|UC-021|UC-022|UC-023` |
| `app/hoc/cus/incidents/L5_engines/anomaly_bridge.py` | `-` | `-` | `-` | `HOLD` | `-` |
| `app/hoc/cus/incidents/L5_engines/incident_engine.py` | `-` | `-` | `-` | `HOLD` | `-` |
| `app/hoc/cus/incidents/L5_engines/incidents_facade.py` | `-` | `incidents.cost_guard;incidents.export;incidents.query;incidents.recovery_rules;...` | `incidents.query` | `HOLD` | `-` |
| `app/hoc/cus/incidents/L6_drivers/cost_guard_driver.py` | `-` | `incidents.cost_guard;incidents.export;incidents.query;incidents.recovery_rules;...` | `-` | `HOLD` | `-` |
| `app/hoc/cus/incidents/L6_drivers/incident_aggregator.py` | `-` | `-` | `-` | `HOLD` | `-` |
| `app/hoc/cus/incidents/L6_drivers/incidents_facade_driver.py` | `-` | `-` | `incidents.query` | `HOLD` | `-` |
| `app/hoc/cus/incidents/adapters/customer_incidents_adapter.py` | `-` | `-` | `-` | `HOLD` | `-` |
| `app/hoc/cus/integrations/L6_drivers/connector_registry_driver.py` | `UC-002` | `account.onboarding.advance;account.onboarding.query` | `-` | `ASSIGN` | `UC-002` |
| `app/hoc/cus/logs/L5_engines/trace_api_engine.py` | `UC-003;UC-017` | `logs.capture;logs.certificate;logs.evidence;logs.evidence_report;...` | `logs.traces_api` | `SPLIT` | `UC-003|UC-017` |
| `app/hoc/cus/logs/L6_drivers/pg_store.py` | `UC-003;UC-017` | `-` | `logs.traces_api;traces.bulk_report_mismatches;traces.list_mismatches;traces.list_trace_mismatches;traces.report_mismatch;traces.resolve_mismatch` | `SPLIT` | `UC-003|UC-017` |
| `app/hoc/cus/logs/L6_drivers/trace_store.py` | `UC-032` | `logs.capture;logs.certificate;logs.evidence;logs.evidence_report;...` | `logs.traces_api` | `SPLIT` | `UC-017|UC-032` |

## Rationale Notes
- `app/hoc/cus/activity/L5_engines/activity_facade.py` -> `HOLD`: No canonical UC anchor; route-map points to broad activity.query surface only.
- `app/hoc/cus/activity/L5_engines/cus_telemetry_engine.py` -> `HOLD`: Only legacy UC-MON evidence; no canonical UC anchor.
- `app/hoc/cus/activity/L5_engines/signal_feedback_engine.py` -> `ASSIGN`: Explicit linkage basename hit under UC-006 and activity signal-feedback handler path.
- `app/hoc/cus/activity/L6_drivers/activity_read_driver.py` -> `HOLD`: Broad read driver used by activity.query; no unique canonical UC anchor.
- `app/hoc/cus/activity/L6_drivers/cus_telemetry_driver.py` -> `HOLD`: Only legacy UC-MON evidence; no canonical UC anchor.
- `app/hoc/cus/activity/L6_drivers/signal_feedback_driver.py` -> `ASSIGN`: Explicit linkage basename hit under UC-006 (signal feedback lifecycle).
- `app/hoc/cus/activity/adapters/customer_activity_adapter.py` -> `HOLD`: Adapter-level references only; no canonical UC anchor in current linkage.
- `app/hoc/cus/analytics/L5_engines/feedback_read_engine.py` -> `HOLD`: Route-map analytics.feedback present, but canonical UC mapping not explicit.
- `app/hoc/cus/analytics/L6_drivers/analytics_artifacts_driver.py` -> `ASSIGN`: Explicit linkage basename hit under UC-008 reproducible analytics artifacts.
- `app/hoc/cus/analytics/L6_drivers/feedback_read_driver.py` -> `HOLD`: Route-map evidence exists but no explicit canonical UC anchor.
- `app/hoc/cus/controls/L6_drivers/evaluation_evidence_driver.py` -> `ASSIGN`: Explicit linkage hit under UC-004 plus dedicated controls.evaluation_evidence operation path.
- `app/hoc/cus/hoc_spine/authority/event_schema_contract.py` -> `SPLIT`: Shared contract used by multiple handlers and UC-001/UC-002 validators; cross-UC authority component.
- `app/hoc/cus/hoc_spine/authority/onboarding_policy.py` -> `ASSIGN`: Explicit linkage hit under UC-002 and dedicated onboarding governance tests.
- `app/hoc/cus/hoc_spine/orchestrator/coordinators/signal_feedback_coordinator.py` -> `HOLD`: Coordinator evidence is legacy UC-MON only; no canonical UC anchor.
- `app/hoc/cus/hoc_spine/orchestrator/handlers/activity_handler.py` -> `SPLIT`: Registers multiple activity operations spanning query/discovery/feedback surfaces.
- `app/hoc/cus/hoc_spine/orchestrator/handlers/controls_handler.py` -> `SPLIT`: Registers multiple controls operations including evaluation evidence and limits-related paths.
- `app/hoc/cus/hoc_spine/orchestrator/handlers/incidents_handler.py` -> `SPLIT`: Registers multiple incidents operations (query/write/recurrence/export) across lifecycle concerns.
- `app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py` -> `ASSIGN`: Explicit linkage hit under UC-002 and onboarding-only operation registrations.
- `app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py` -> `SPLIT`: Single handler registers many policy lifecycle/query operations across multiple UCs.
- `app/hoc/cus/incidents/L5_engines/anomaly_bridge.py` -> `HOLD`: No canonical UC anchor; evidence remains legacy UC-MON oriented.
- `app/hoc/cus/incidents/L5_engines/incident_engine.py` -> `HOLD`: No canonical UC anchor; broad incident engine usage.
- `app/hoc/cus/incidents/L5_engines/incidents_facade.py` -> `HOLD`: Route-map incidents.query evidence exists but canonical UC split not explicit.
- `app/hoc/cus/incidents/L6_drivers/cost_guard_driver.py` -> `HOLD`: Legacy UC-MON evidence only; no canonical linkage anchor.
- `app/hoc/cus/incidents/L6_drivers/incident_aggregator.py` -> `HOLD`: Legacy UC-MON evidence only; no canonical linkage anchor.
- `app/hoc/cus/incidents/L6_drivers/incidents_facade_driver.py` -> `HOLD`: Route-map incidents.query exists, but canonical UC assignment remains non-unique.
- `app/hoc/cus/incidents/adapters/customer_incidents_adapter.py` -> `HOLD`: Adapter-level tests exist but no canonical UC anchor in linkage.
- `app/hoc/cus/integrations/L6_drivers/connector_registry_driver.py` -> `ASSIGN`: Explicit linkage hit under UC-002 and onboarding authority boundary tests.
- `app/hoc/cus/logs/L5_engines/trace_api_engine.py` -> `SPLIT`: Explicit linkage hits in both UC-003 and UC-017; trace ingest + replay integrity concerns.
- `app/hoc/cus/logs/L6_drivers/pg_store.py` -> `SPLIT`: Explicit linkage hits in both UC-003 and UC-017; persistence covers trace ingest and replay metadata.
- `app/hoc/cus/logs/L6_drivers/trace_store.py` -> `SPLIT`: Explicit linkage hit under UC-032 plus trace-store replay/determinism evidence; cross-cutting logs concerns.

## Artifact
- Detailed evidence CSV: `backend/app/hoc/docs/architecture/usecases/HOC_CUS_UC_MATCH_ITERATION3_DECISION_TABLE_2026-02-15.csv`
