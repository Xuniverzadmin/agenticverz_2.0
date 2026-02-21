# CUS Domain Ledger: logs

**Generated:** 2026-02-21T07:54:56.667404+00:00
**Total endpoints:** 47
**Unique method+path:** 47

| Method | Path | Operation | Summary |
|--------|------|-----------|---------|
| GET | /hoc/api/cus/cost/anomalies | get_anomalies | Get detected cost anomalies. |
| POST | /hoc/api/cus/cost/anomalies/detect | trigger_anomaly_detection | Trigger anomaly detection for this tenant. |
| GET | /hoc/api/cus/cost/budgets | list_budgets | List all budgets for the tenant. |
| POST | /hoc/api/cus/cost/budgets | create_or_update_budget | Create or update a budget. |
| GET | /hoc/api/cus/cost/by-feature | get_costs_by_feature | Get cost breakdown by feature tag. |
| GET | /hoc/api/cus/cost/by-model | get_costs_by_model | Get cost breakdown by model. |
| GET | /hoc/api/cus/cost/by-user | get_costs_by_user | Get cost breakdown by user with anomaly detection. |
| GET | /hoc/api/cus/cost/dashboard | get_cost_dashboard | Get complete cost dashboard. |
| GET | /hoc/api/cus/cost/features | list_feature_tags | List all feature tags for the tenant. |
| POST | /hoc/api/cus/cost/features | create_feature_tag | Register a new feature tag. |
| PUT | /hoc/api/cus/cost/features/{tag} | update_feature_tag | Update a feature tag. |
| GET | /hoc/api/cus/cost/projection | get_projection | Get cost projection based on historical data. |
| POST | /hoc/api/cus/cost/record | record_cost | Record a cost entry. |
| GET | /hoc/api/cus/cost/summary | get_cost_summary | Get cost summary for the period. |
| GET | /hoc/api/cus/logs/audit | list_audit_entries | List audit entries. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/audit/access | get_audit_access | O3: Log access audit. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/audit/authorization | get_audit_authorization | O2: Authorization decisions. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/audit/exports | get_audit_exports | O5: Compliance exports. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/audit/identity | get_audit_identity | O1: Identity lifecycle. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/audit/integrity | get_audit_integrity | O4: Tamper detection. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/audit/{entry_id} | get_audit_entry | Get audit entry detail. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/list | list_logs_public |  |
| GET | /hoc/api/cus/logs/llm-runs | list_llm_run_records | List LLM run records. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/llm-runs/{run_id}/envelope | get_llm_run_envelope | O1: Canonical immutable run record. READ-ONLY customer facad |
| GET | /hoc/api/cus/logs/llm-runs/{run_id}/export | get_llm_run_export | O5: Export information. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/llm-runs/{run_id}/governance | get_llm_run_governance | O3: Policy interaction trace. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/llm-runs/{run_id}/replay | get_llm_run_replay | O4: 60-second replay window. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/llm-runs/{run_id}/trace | get_llm_run_trace | O2: Step-by-step execution trace. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/system | list_system_records | List system records. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/system/audit | get_system_audit | O5: Infra attribution. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/system/{run_id}/events | get_system_events | O3: Infra events affecting run. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/system/{run_id}/replay | get_system_replay | O4: Infra replay window. READ-ONLY customer facade. |
| GET | /hoc/api/cus/logs/system/{run_id}/snapshot | get_system_snapshot | O1: Environment baseline snapshot. READ-ONLY customer facade |
| GET | /hoc/api/cus/logs/system/{run_id}/telemetry | get_system_telemetry | O2: Telemetry stub - producer not implemented. READ-ONLY cus |
| GET | /hoc/api/cus/traces | list_traces | List and search traces with optional filters. |
| POST | /hoc/api/cus/traces | store_trace | Store a client-provided trace. |
| GET | /hoc/api/cus/traces/by-hash/{root_hash} | get_trace_by_hash | Get a trace by its deterministic root hash. |
| POST | /hoc/api/cus/traces/cleanup | cleanup_old_traces | Delete traces older than specified number of days. |
| GET | /hoc/api/cus/traces/compare/{run_id1}/{run_id2} | compare_traces | Compare two traces for deterministic equality. |
| GET | /hoc/api/cus/traces/idempotency/{idempotency_key} | check_idempotency | Check if an idempotency key has been executed. |
| GET | /hoc/api/cus/traces/mismatches | list_all_mismatches | List all trace mismatches across the system. |
| POST | /hoc/api/cus/traces/mismatches/bulk-report | bulk_report_mismatches | Create a single GitHub issue for multiple mismatches. |
| DELETE | /hoc/api/cus/traces/{run_id} | delete_trace | Delete a trace by run ID. |
| GET | /hoc/api/cus/traces/{run_id} | get_trace | Get a complete trace by run ID. |
| POST | /hoc/api/cus/traces/{trace_id}/mismatch | report_mismatch | Report a replay mismatch for operator review. |
| GET | /hoc/api/cus/traces/{trace_id}/mismatches | list_trace_mismatches | List all mismatches reported for a trace. |
| POST | /hoc/api/cus/traces/{trace_id}/mismatches/{mismatch_id}/resolve | resolve_mismatch | Mark a mismatch as resolved. |
