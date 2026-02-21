# CUS Domain Ledger: analytics

**Generated:** 2026-02-21T07:54:56.667404+00:00
**Total endpoints:** 34
**Unique method+path:** 33

| Method | Path | Operation | Summary |
|--------|------|-----------|---------|
| GET | /hoc/api/cus/analytics/_status | get_analytics_status | Analytics capability probe. |
| GET | /hoc/api/cus/analytics/health | analytics_health | Internal health check for analytics facade. |
| GET | /hoc/api/cus/analytics/statistics/cost | get_cost_statistics | Get cost statistics for the specified time window. |
| GET | /hoc/api/cus/analytics/statistics/cost/export.csv | export_cost_csv | Export cost statistics as CSV. |
| GET | /hoc/api/cus/analytics/statistics/cost/export.json | export_cost_json | Export cost statistics as JSON. |
| GET | /hoc/api/cus/analytics/statistics/usage | get_usage_statistics | Get usage statistics for the specified time window. |
| GET | /hoc/api/cus/analytics/statistics/usage | get_usage_statistics_public |  |
| GET | /hoc/api/cus/analytics/statistics/usage/export.csv | export_usage_csv | Export usage statistics as CSV. |
| GET | /hoc/api/cus/analytics/statistics/usage/export.json | export_usage_json | Export usage statistics as JSON. |
| GET | /hoc/api/cus/costsim/canary/reports | get_canary_reports | Get recent canary run reports. |
| POST | /hoc/api/cus/costsim/canary/run | trigger_canary_run | Trigger a canary run on-demand. |
| GET | /hoc/api/cus/costsim/datasets | list_datasets | List all available reference datasets. |
| POST | /hoc/api/cus/costsim/datasets/validate-all | validate_all | Validate V2 against ALL reference datasets. |
| GET | /hoc/api/cus/costsim/datasets/{dataset_id} | get_dataset_info | Get information about a specific dataset. |
| POST | /hoc/api/cus/costsim/datasets/{dataset_id}/validate | validate_against_dataset | Validate V2 against a specific reference dataset. |
| GET | /hoc/api/cus/costsim/divergence | get_divergence_report | Get cost divergence report between V1 and V2. |
| GET | /hoc/api/cus/costsim/v2/incidents | get_incidents | Get circuit breaker incidents. |
| POST | /hoc/api/cus/costsim/v2/reset | reset_circuit_breaker | Reset the V2 circuit breaker. |
| POST | /hoc/api/cus/costsim/v2/simulate | simulate_v2 | Run simulation through V2 sandbox. |
| GET | /hoc/api/cus/costsim/v2/status | get_sandbox_status | Get current V2 sandbox status. |
| GET | /hoc/api/cus/feedback | list_feedback | List pattern feedback records (PB-S3). |
| GET | /hoc/api/cus/feedback/stats/summary | get_feedback_stats | Get feedback statistics summary (PB-S3). |
| GET | /hoc/api/cus/feedback/{feedback_id} | get_feedback | Get detailed feedback record by ID (PB-S3). |
| GET | /hoc/api/cus/predictions | list_predictions | List prediction events (PB-S5). |
| GET | /hoc/api/cus/predictions/stats/summary | get_prediction_stats | Get prediction statistics (PB-S5). |
| GET | /hoc/api/cus/predictions/subject/{subject_type}/{subject_id} | get_predictions_for_subject | Get all predictions for a specific subject (PB-S5). |
| GET | /hoc/api/cus/predictions/{prediction_id} | get_prediction | Get detailed prediction by ID (PB-S5). |
| GET | /hoc/api/cus/scenarios | list_scenarios | List all available scenarios. |
| POST | /hoc/api/cus/scenarios | create_scenario | Create a new scenario. |
| GET | /hoc/api/cus/scenarios/info/immutability | get_immutability_info | Get information about the immutability guarantees. |
| POST | /hoc/api/cus/scenarios/simulate-adhoc | simulate_adhoc | Run ad-hoc simulation without saving scenario. |
| DELETE | /hoc/api/cus/scenarios/{scenario_id} | delete_scenario | Delete a scenario. |
| GET | /hoc/api/cus/scenarios/{scenario_id} | get_scenario | Get a specific scenario by ID. |
| POST | /hoc/api/cus/scenarios/{scenario_id}/simulate | simulate_scenario | Run simulation for a saved scenario. |
