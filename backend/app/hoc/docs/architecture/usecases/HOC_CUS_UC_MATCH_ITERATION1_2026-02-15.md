# HOC CUS Script-vs-Usecase Matching - Iteration 1 (2026-02-15)

## Method (No Force-Fit)
1. Keep canonical `UC-###` from classification when present.
2. Recover non-canonical/blank rows only via strict explicit path anchors in canonical UC sections.
3. Leave rows unresolved when no unique canonical anchor exists.

## Snapshot
- Generated at (UTC): `2026-02-15T06:26:46Z`
- Input UC-linked scripts: `264`
- `MATCHED_CANONICAL_FROM_CSV`: `206`
- `MATCHED_FROM_EXPLICIT_ANCHOR`: `28`
- `AMBIGUOUS_MULTIPLE_EXPLICIT`: `0`
- `UNRESOLVED_NO_CANONICAL_EVIDENCE`: `30`
- Final assigned to canonical UC: `234`
- Unresolved: `30`

## Evidence Quality
- `CSV_PLUS_EXPLICIT`: `72`
- `CSV_CANONICAL_ONLY`: `134`
- `EXPLICIT_ONLY`: `28`
- `NO_EVIDENCE`: `30`

## Canonical UC Distribution (Final Assignment)
| UC | Status | Script Count |
| --- | --- | ---: |
| UC-001 | `GREEN` | 17 |
| UC-002 | `GREEN` | 31 |
| UC-003 | `GREEN` | 6 |
| UC-004 | `GREEN` | 0 |
| UC-005 | `GREEN` | 0 |
| UC-006 | `GREEN` | 0 |
| UC-007 | `GREEN` | 0 |
| UC-008 | `GREEN` | 0 |
| UC-009 | `GREEN` | 8 |
| UC-010 | `GREEN` | 0 |
| UC-011 | `GREEN` | 0 |
| UC-012 | `GREEN` | 0 |
| UC-013 | `GREEN` | 0 |
| UC-014 | `GREEN` | 0 |
| UC-015 | `GREEN` | 0 |
| UC-016 | `GREEN` | 0 |
| UC-017 | `GREEN` | 11 |
| UC-018 | `GREEN` | 2 |
| UC-019 | `GREEN` | 4 |
| UC-020 | `GREEN` | 2 |
| UC-021 | `GREEN` | 5 |
| UC-022 | `GREEN` | 2 |
| UC-023 | `GREEN` | 3 |
| UC-024 | `GREEN` | 12 |
| UC-025 | `GREEN` | 5 |
| UC-026 | `GREEN` | 2 |
| UC-027 | `GREEN` | 10 |
| UC-028 | `GREEN` | 2 |
| UC-029 | `GREEN` | 6 |
| UC-030 | `GREEN` | 3 |
| UC-031 | `GREEN` | 13 |
| UC-032 | `GREEN` | 2 |
| UC-033 | `GREEN` | 26 |
| UC-034 | `GREEN` | 6 |
| UC-035 | `GREEN` | 17 |
| UC-036 | `GREEN` | 33 |
| UC-037 | `GREEN` | 3 |
| UC-038 | `GREEN` | 1 |
| UC-039 | `GREEN` | 1 |
| UC-040 | `GREEN` | 1 |

## Unresolved Scripts
- `app/hoc/cus/activity/L5_engines/activity_facade.py` (csv_uc=`UC-MON-01', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/activity/L5_engines/cus_telemetry_engine.py` (csv_uc=`UC-MON-05', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/activity/L5_engines/signal_feedback_engine.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/activity/L6_drivers/activity_read_driver.py` (csv_uc=`UC-MON-01', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/activity/L6_drivers/cus_telemetry_driver.py` (csv_uc=`UC-MON-05', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/activity/L6_drivers/signal_feedback_driver.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/activity/adapters/customer_activity_adapter.py` (csv_uc=`UC-MON-01', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/analytics/L5_engines/feedback_read_engine.py` (csv_uc=`UC-MON-04', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/analytics/L6_drivers/analytics_artifacts_driver.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/analytics/L6_drivers/feedback_read_driver.py` (csv_uc=`UC-MON-04', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/controls/L6_drivers/evaluation_evidence_driver.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/hoc_spine/authority/event_schema_contract.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/hoc_spine/authority/onboarding_policy.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/hoc_spine/orchestrator/coordinators/signal_feedback_coordinator.py` (csv_uc=`UC-MON-04', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/hoc_spine/orchestrator/handlers/activity_handler.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/hoc_spine/orchestrator/handlers/controls_handler.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/hoc_spine/orchestrator/handlers/incidents_handler.py` (csv_uc=`UC-MON-07', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/hoc_spine/orchestrator/handlers/policies_handler.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/incidents/L5_engines/anomaly_bridge.py` (csv_uc=`UC-MON-07', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/incidents/L5_engines/incident_engine.py` (csv_uc=`UC-MON-07', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/incidents/L5_engines/incidents_facade.py` (csv_uc=`UC-MON-07', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/incidents/L6_drivers/cost_guard_driver.py` (csv_uc=`UC-MON-07', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/incidents/L6_drivers/incident_aggregator.py` (csv_uc=`UC-MON-07', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/incidents/L6_drivers/incidents_facade_driver.py` (csv_uc=`UC-MON-07', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/incidents/adapters/customer_incidents_adapter.py` (csv_uc=`UC-MON-07', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/integrations/L6_drivers/connector_registry_driver.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/logs/L5_engines/trace_api_engine.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/logs/L6_drivers/pg_store.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)
- `app/hoc/cus/logs/L6_drivers/trace_store.py` (csv_uc=`-', evidence=`NO_EVIDENCE`)

## Artifact
- Detail CSV: `backend/app/hoc/docs/architecture/usecases/HOC_CUS_UC_MATCH_ITERATION1_2026-02-15.csv`
