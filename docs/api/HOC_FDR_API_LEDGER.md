# HOC CUS API Ledger

- Generated (UTC): `2026-02-21T07:19:42.623185+00:00`
- Source: `/tmp/hoc-wave2-fdr-ledger/docs/openapi.json`
- Prefix: `/hoc/api/fdr/`
- Endpoints: `66`

| Domain | Method | Path | Operation ID | Auth | Schemes | Request | Response |
|---|---|---|---|---|---|---|---|
| explorer | GET | `/hoc/api/fdr/explorer/info` | `get_explorer_info` | unknown | `` | `` | `` |
| explorer | GET | `/hoc/api/fdr/explorer/patterns` | `get_usage_patterns` | unknown | `` | `` | `PatternsResponse` |
| explorer | GET | `/hoc/api/fdr/explorer/summary` | `get_system_summary` | unknown | `` | `` | `SystemSummary` |
| explorer | GET | `/hoc/api/fdr/explorer/system/health` | `get_system_health` | unknown | `` | `` | `SystemHealthResponse` |
| explorer | GET | `/hoc/api/fdr/explorer/tenant/{tenant_id}/diagnostics` | `get_tenant_diagnostics` | unknown | `` | `` | `TenantDiagnostics` |
| explorer | GET | `/hoc/api/fdr/explorer/tenants` | `list_tenants` | unknown | `` | `` | `List[TenantSummary]` |
| fdr | GET | `/hoc/api/fdr/fdr/contracts/review-queue` | `get_review_queue` | unknown | `` | `` | `None` |
| fdr | GET | `/hoc/api/fdr/fdr/contracts/{contract_id}` | `get_contract_detail` | unknown | `` | `` | `None` |
| fdr | POST | `/hoc/api/fdr/fdr/contracts/{contract_id}/review` | `submit_review` | unknown | `` | `` | `None` |
| fdr | POST | `/hoc/api/fdr/fdr/lifecycle/archive` | `archive_tenant` | unknown | `` | `` | `LifecycleTransitionResponse` |
| fdr | POST | `/hoc/api/fdr/fdr/lifecycle/resume` | `resume_tenant` | unknown | `` | `` | `LifecycleTransitionResponse` |
| fdr | POST | `/hoc/api/fdr/fdr/lifecycle/suspend` | `suspend_tenant` | unknown | `` | `` | `LifecycleTransitionResponse` |
| fdr | POST | `/hoc/api/fdr/fdr/lifecycle/terminate` | `terminate_tenant` | unknown | `` | `` | `LifecycleTransitionResponse` |
| fdr | GET | `/hoc/api/fdr/fdr/lifecycle/{tenant_id}` | `get_lifecycle_state` | unknown | `` | `` | `LifecycleStateResponse` |
| fdr | GET | `/hoc/api/fdr/fdr/lifecycle/{tenant_id}/history` | `get_lifecycle_history` | unknown | `` | `` | `LifecycleHistoryResponse` |
| fdr | POST | `/hoc/api/fdr/fdr/onboarding/force-complete` | `force_complete_onboarding` | unknown | `` | `` | `ForceCompleteResponse` |
| fdr | GET | `/hoc/api/fdr/fdr/onboarding/stalled` | `get_stalled_tenants` | unknown | `` | `` | `` |
| fdr | GET | `/hoc/api/fdr/fdr/review/auto-execute` | `list_auto_execute_decisions` | unknown | `` | `` | `AutoExecuteReviewListDTO` |
| fdr | GET | `/hoc/api/fdr/fdr/review/auto-execute/stats` | `get_auto_execute_stats` | unknown | `` | `` | `AutoExecuteReviewStatsDTO` |
| fdr | GET | `/hoc/api/fdr/fdr/review/auto-execute/{invocation_id}` | `get_auto_execute_decision` | unknown | `` | `` | `AutoExecuteReviewItemDTO` |
| fdr | GET | `/hoc/api/fdr/fdr/timeline/count` | `count_decision_records` | unknown | `` | `` | `` |
| fdr | GET | `/hoc/api/fdr/fdr/timeline/decisions` | `list_decision_records` | unknown | `` | `` | `List[DecisionRecordView]` |
| fdr | GET | `/hoc/api/fdr/fdr/timeline/decisions/{decision_id}` | `get_decision_record` | unknown | `` | `` | `DecisionRecordView` |
| fdr | GET | `/hoc/api/fdr/fdr/timeline/run/{run_id}` | `get_run_timeline` | unknown | `` | `` | `RunTimeline` |
| hoc | GET | `/hoc/api/fdr/hoc/api/stagetest/apis` | `stagetest_list_apis` | unknown | `` | `` | `ApisSnapshotResponse` |
| hoc | GET | `/hoc/api/fdr/hoc/api/stagetest/apis/ledger` | `stagetest_list_apis_ledger` | unknown | `` | `` | `ApisSnapshotResponse` |
| hoc | GET | `/hoc/api/fdr/hoc/api/stagetest/runs` | `stagetest_list_runs` | unknown | `` | `` | `RunListResponse` |
| hoc | GET | `/hoc/api/fdr/hoc/api/stagetest/runs/{run_id}` | `stagetest_get_run` | unknown | `` | `` | `RunSummary` |
| hoc | GET | `/hoc/api/fdr/hoc/api/stagetest/runs/{run_id}/cases` | `stagetest_list_cases` | unknown | `` | `` | `CaseListResponse` |
| hoc | GET | `/hoc/api/fdr/hoc/api/stagetest/runs/{run_id}/cases/{case_id}` | `stagetest_get_case` | unknown | `` | `` | `CaseDetail` |
| ops | GET | `/hoc/api/fdr/ops/actions/audit` | `get_audit_trail` | unknown | `` | `` | `FounderActionListDTO` |
| ops | GET | `/hoc/api/fdr/ops/actions/audit/{action_id}` | `get_audit_record` | unknown | `` | `` | `FounderAuditRecordDTO` |
| ops | POST | `/hoc/api/fdr/ops/actions/freeze-api-key` | `freeze_api_key` | unknown | `` | `` | `FounderActionResponseDTO` |
| ops | POST | `/hoc/api/fdr/ops/actions/freeze-tenant` | `freeze_tenant` | unknown | `` | `` | `FounderActionResponseDTO` |
| ops | POST | `/hoc/api/fdr/ops/actions/override-incident` | `override_incident` | unknown | `` | `` | `FounderActionResponseDTO` |
| ops | POST | `/hoc/api/fdr/ops/actions/throttle-tenant` | `throttle_tenant` | unknown | `` | `` | `FounderActionResponseDTO` |
| ops | POST | `/hoc/api/fdr/ops/actions/unfreeze-api-key` | `unfreeze_api_key` | unknown | `` | `` | `FounderActionResponseDTO` |
| ops | POST | `/hoc/api/fdr/ops/actions/unfreeze-tenant` | `unfreeze_tenant` | unknown | `` | `` | `FounderActionResponseDTO` |
| ops | POST | `/hoc/api/fdr/ops/actions/unthrottle-tenant` | `unthrottle_tenant` | unknown | `` | `` | `FounderActionResponseDTO` |
| ops | GET | `/hoc/api/fdr/ops/cost/anomalies` | `get_cost_anomalies` | unknown | `` | `` | `FounderCostAnomalyListDTO` |
| ops | GET | `/hoc/api/fdr/ops/cost/customers/{tenant_id}` | `get_customer_cost_drilldown` | unknown | `` | `` | `FounderCustomerCostDrilldownDTO` |
| ops | GET | `/hoc/api/fdr/ops/cost/overview` | `get_cost_overview` | unknown | `` | `` | `FounderCostOverviewDTO` |
| ops | GET | `/hoc/api/fdr/ops/cost/tenants` | `get_cost_tenants` | unknown | `` | `` | `FounderCostTenantListDTO` |
| ops | GET | `/hoc/api/fdr/ops/customers` | `get_customer_segments` | unknown | `` | `` | `List[CustomerSegment]` |
| ops | GET | `/hoc/api/fdr/ops/customers/at-risk` | `get_customers_at_risk` | unknown | `` | `` | `List[CustomerAtRisk]` |
| ops | GET | `/hoc/api/fdr/ops/customers/{tenant_id}` | `get_customer_detail` | unknown | `` | `` | `CustomerSegment` |
| ops | GET | `/hoc/api/fdr/ops/events` | `get_event_stream` | unknown | `` | `` | `OpsEventListResponse` |
| ops | GET | `/hoc/api/fdr/ops/incidents` | `get_founder_incidents` | unknown | `` | `` | `FounderIncidentListDTO` |
| ops | GET | `/hoc/api/fdr/ops/incidents/infra-summary` | `get_infra_incident_summary` | unknown | `` | `` | `` |
| ops | GET | `/hoc/api/fdr/ops/incidents/patterns` | `get_incident_patterns` | unknown | `` | `` | `List[IncidentPattern]` |
| ops | GET | `/hoc/api/fdr/ops/incidents/{incident_id}` | `get_founder_incident_detail` | unknown | `` | `` | `FounderIncidentDetailDTO` |
| ops | GET | `/hoc/api/fdr/ops/infra` | `get_infra_limits` | unknown | `` | `` | `InfraLimits` |
| ops | GET | `/hoc/api/fdr/ops/playbooks` | `get_founder_playbooks` | unknown | `` | `` | `List[PlaybookDetail]` |
| ops | GET | `/hoc/api/fdr/ops/playbooks/{playbook_id}` | `get_playbook_detail` | unknown | `` | `` | `PlaybookDetail` |
| ops | GET | `/hoc/api/fdr/ops/pulse` | `get_system_pulse` | unknown | `` | `` | `SystemPulse` |
| ops | GET | `/hoc/api/fdr/ops/revenue` | `get_revenue_risk` | unknown | `` | `` | `RevenueRisk` |
| ops | GET | `/hoc/api/fdr/ops/stickiness` | `get_stickiness_by_feature` | unknown | `` | `` | `List[StickinessByFeature]` |
| retrieval | GET | `/hoc/api/fdr/retrieval/evidence` | `list_evidence` | unknown | `` | `` | `Dict[str, Any]` |
| retrieval | GET | `/hoc/api/fdr/retrieval/evidence/{evidence_id}` | `get_evidence` | unknown | `` | `` | `Dict[str, Any]` |
| retrieval | GET | `/hoc/api/fdr/retrieval/planes` | `list_planes` | unknown | `` | `` | `Dict[str, Any]` |
| retrieval | POST | `/hoc/api/fdr/retrieval/planes` | `register_plane` | unknown | `` | `` | `Dict[str, Any]` |
| retrieval | GET | `/hoc/api/fdr/retrieval/planes/{plane_id}` | `get_plane` | unknown | `` | `` | `Dict[str, Any]` |
| retrieval | POST | `/hoc/api/fdr/retrieval/planes/{plane_id}/approve_purge` | `approve_purge` | unknown | `` | `` | `Dict[str, Any]` |
| retrieval | POST | `/hoc/api/fdr/retrieval/planes/{plane_id}/bind_policy` | `bind_policy` | unknown | `` | `` | `Dict[str, Any]` |
| retrieval | POST | `/hoc/api/fdr/retrieval/planes/{plane_id}/transition` | `transition_plane` | unknown | `` | `` | `Dict[str, Any]` |
| retrieval | POST | `/hoc/api/fdr/retrieval/planes/{plane_id}/unbind_policy` | `unbind_policy` | unknown | `` | `` | `Dict[str, Any]` |
