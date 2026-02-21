# HOC CUS API Ledger

- Generated (UTC): `2026-02-21T07:47:56.669825+00:00`
- Source: `/tmp/hoc-cus-stabilize-plan/docs/openapi.json`
- Prefix: `/hoc/api/cus/`
- Endpoints: `502`

| Domain | Method | Path | Operation ID | Auth | Schemes | Request | Response |
|---|---|---|---|---|---|---|---|
| account | GET | `/hoc/api/cus/account/users/list` | `list_account_users_public` | unknown | `` | `` | `AccountUsersListPublicResponse` |
| accounts | GET | `/hoc/api/cus/accounts/billing` | `get_billing_summary` | unknown | `` | `` | `BillingSummaryResponse` |
| accounts | GET | `/hoc/api/cus/accounts/billing/invoices` | `get_billing_invoices` | unknown | `` | `` | `InvoiceListResponse` |
| accounts | GET | `/hoc/api/cus/accounts/invitations` | `list_invitations` | unknown | `` | `` | `InvitationListResponse` |
| accounts | POST | `/hoc/api/cus/accounts/invitations/{invitation_id}/accept` | `accept_invitation` | unknown | `` | `` | `` |
| accounts | GET | `/hoc/api/cus/accounts/profile` | `get_profile` | unknown | `` | `` | `ProfileResponse` |
| accounts | PUT | `/hoc/api/cus/accounts/profile` | `update_profile` | unknown | `` | `` | `ProfileUpdateResponse` |
| accounts | GET | `/hoc/api/cus/accounts/projects` | `list_projects` | unknown | `` | `` | `ProjectsListResponse` |
| accounts | POST | `/hoc/api/cus/accounts/projects` | `create_project` | unknown | `` | `` | `ProjectDetailResponse` |
| accounts | GET | `/hoc/api/cus/accounts/projects/{project_id}` | `get_project_detail` | unknown | `` | `` | `ProjectDetailResponse` |
| accounts | GET | `/hoc/api/cus/accounts/support` | `get_support_contact` | unknown | `` | `` | `SupportContactResponse` |
| accounts | GET | `/hoc/api/cus/accounts/support/tickets` | `list_support_tickets` | unknown | `` | `` | `SupportTicketListResponse` |
| accounts | POST | `/hoc/api/cus/accounts/support/tickets` | `create_support_ticket` | unknown | `` | `` | `SupportTicketResponse` |
| accounts | GET | `/hoc/api/cus/accounts/tenant/users` | `list_tenant_users` | unknown | `` | `` | `TenantUserListResponse` |
| accounts | GET | `/hoc/api/cus/accounts/users` | `list_users` | unknown | `` | `` | `UsersListResponse` |
| accounts | POST | `/hoc/api/cus/accounts/users/invite` | `invite_user` | unknown | `` | `` | `InvitationResponse` |
| accounts | GET | `/hoc/api/cus/accounts/users/{user_id}` | `get_user_detail` | unknown | `` | `` | `UserDetailResponse` |
| accounts | DELETE | `/hoc/api/cus/accounts/users/{user_id}` | `remove_user` | unknown | `` | `` | `` |
| accounts | PUT | `/hoc/api/cus/accounts/users/{user_id}/role` | `update_user_role` | unknown | `` | `` | `TenantUserResponse` |
| activity | GET | `/hoc/api/cus/activity/attention-queue` | `get_attention_queue` | unknown | `` | `` | `AttentionQueueResponse` |
| activity | GET | `/hoc/api/cus/activity/completed` | `list_completed_runs` | unknown | `` | `` | `CompletedRunsResponse` |
| activity | GET | `/hoc/api/cus/activity/cost-analysis` | `get_cost_analysis` | unknown | `` | `` | `CostAnalysisResponse` |
| activity | GET | `/hoc/api/cus/activity/live` | `list_live_runs` | unknown | `` | `` | `LiveRunsResponse` |
| activity | GET | `/hoc/api/cus/activity/metrics` | `get_activity_metrics` | unknown | `` | `` | `MetricsResponse` |
| activity | GET | `/hoc/api/cus/activity/patterns` | `get_patterns` | unknown | `` | `` | `PatternDetectionResponse` |
| activity | GET | `/hoc/api/cus/activity/risk-signals` | `get_risk_signals` | unknown | `` | `` | `RiskSignalsResponse` |
| activity | GET | `/hoc/api/cus/activity/runs` | `list_runs` | unknown | `` | `` | `RunListResponse` |
| activity | GET | `/hoc/api/cus/activity/runs` | `list_runs_facade` | unknown | `` | `` | `RunsFacadeResponse` |
| activity | GET | `/hoc/api/cus/activity/runs/by-dimension` | `get_runs_by_dimension` | unknown | `` | `` | `DimensionBreakdownResponse` |
| activity | GET | `/hoc/api/cus/activity/runs/completed/by-dimension` | `get_completed_runs_by_dimension` | unknown | `` | `` | `DimensionBreakdownResponse` |
| activity | GET | `/hoc/api/cus/activity/runs/live/by-dimension` | `get_live_runs_by_dimension` | unknown | `` | `` | `DimensionBreakdownResponse` |
| activity | GET | `/hoc/api/cus/activity/runs/{run_id}` | `get_run_detail` | unknown | `` | `` | `RunDetailResponse` |
| activity | GET | `/hoc/api/cus/activity/runs/{run_id}/evidence` | `get_run_evidence` | unknown | `` | `` | `` |
| activity | GET | `/hoc/api/cus/activity/runs/{run_id}/proof` | `get_run_proof` | unknown | `` | `` | `` |
| activity | GET | `/hoc/api/cus/activity/signals` | `list_signals` | unknown | `` | `` | `SignalsResponse` |
| activity | POST | `/hoc/api/cus/activity/signals/{signal_fingerprint}/ack` | `acknowledge_signal` | unknown | `` | `` | `SignalAckResponse` |
| activity | POST | `/hoc/api/cus/activity/signals/{signal_fingerprint}/suppress` | `suppress_signal` | unknown | `` | `` | `SignalSuppressResponse` |
| activity | GET | `/hoc/api/cus/activity/summary/by-status` | `get_summary_by_status` | unknown | `` | `` | `StatusSummaryResponse` |
| activity | GET | `/hoc/api/cus/activity/threshold-signals` | `get_threshold_signals` | unknown | `` | `` | `ThresholdSignalsResponse` |
| alerts | GET | `/hoc/api/cus/alerts/history` | `list_history` | unknown | `` | `` | `Dict[str, Any]` |
| alerts | GET | `/hoc/api/cus/alerts/history/{event_id}` | `get_event` | unknown | `` | `` | `Dict[str, Any]` |
| alerts | POST | `/hoc/api/cus/alerts/history/{event_id}/acknowledge` | `acknowledge_event` | unknown | `` | `` | `Dict[str, Any]` |
| alerts | POST | `/hoc/api/cus/alerts/history/{event_id}/resolve` | `resolve_event` | unknown | `` | `` | `Dict[str, Any]` |
| alerts | GET | `/hoc/api/cus/alerts/routes` | `list_routes` | unknown | `` | `` | `Dict[str, Any]` |
| alerts | POST | `/hoc/api/cus/alerts/routes` | `create_route` | unknown | `` | `` | `Dict[str, Any]` |
| alerts | GET | `/hoc/api/cus/alerts/routes/{route_id}` | `get_route` | unknown | `` | `` | `Dict[str, Any]` |
| alerts | DELETE | `/hoc/api/cus/alerts/routes/{route_id}` | `delete_route` | unknown | `` | `` | `Dict[str, Any]` |
| alerts | GET | `/hoc/api/cus/alerts/rules` | `list_rules` | unknown | `` | `` | `Dict[str, Any]` |
| alerts | POST | `/hoc/api/cus/alerts/rules` | `create_rule` | unknown | `` | `` | `Dict[str, Any]` |
| alerts | GET | `/hoc/api/cus/alerts/rules/{rule_id}` | `get_rule` | unknown | `` | `` | `Dict[str, Any]` |
| alerts | PUT | `/hoc/api/cus/alerts/rules/{rule_id}` | `update_rule` | unknown | `` | `` | `Dict[str, Any]` |
| alerts | DELETE | `/hoc/api/cus/alerts/rules/{rule_id}` | `delete_rule` | unknown | `` | `` | `Dict[str, Any]` |
| analytics | GET | `/hoc/api/cus/analytics/_status` | `get_analytics_status` | unknown | `` | `` | `AnalyticsStatusResponse` |
| analytics | GET | `/hoc/api/cus/analytics/health` | `analytics_health` | unknown | `` | `` | `` |
| analytics | GET | `/hoc/api/cus/analytics/statistics/cost` | `get_cost_statistics` | unknown | `` | `` | `CostStatisticsResponse` |
| analytics | GET | `/hoc/api/cus/analytics/statistics/cost/export.csv` | `export_cost_csv` | unknown | `` | `` | `` |
| analytics | GET | `/hoc/api/cus/analytics/statistics/cost/export.json` | `export_cost_json` | unknown | `` | `` | `CostStatisticsResponse` |
| analytics | GET | `/hoc/api/cus/analytics/statistics/usage` | `get_usage_statistics` | unknown | `` | `` | `UsageStatisticsResponse` |
| analytics | GET | `/hoc/api/cus/analytics/statistics/usage` | `get_usage_statistics_public` | unknown | `` | `` | `AnalyticsUsagePublicResponse` |
| analytics | GET | `/hoc/api/cus/analytics/statistics/usage/export.csv` | `export_usage_csv` | unknown | `` | `` | `` |
| analytics | GET | `/hoc/api/cus/analytics/statistics/usage/export.json` | `export_usage_json` | unknown | `` | `` | `UsageStatisticsResponse` |
| api-keys | GET | `/hoc/api/cus/api-keys` | `list_api_keys` | unknown | `` | `` | `APIKeysListResponse` |
| api-keys | GET | `/hoc/api/cus/api-keys/{key_id}` | `get_api_key_detail` | unknown | `` | `` | `APIKeyDetailResponse` |
| api_keys | GET | `/hoc/api/cus/api_keys/list` | `list_api_keys_public` | unknown | `` | `` | `APIKeysListPublicResponse` |
| compliance | GET | `/hoc/api/cus/compliance/reports` | `list_reports` | unknown | `` | `` | `Dict[str, Any]` |
| compliance | GET | `/hoc/api/cus/compliance/reports/{report_id}` | `get_report` | unknown | `` | `` | `Dict[str, Any]` |
| compliance | GET | `/hoc/api/cus/compliance/rules` | `list_rules` | unknown | `` | `` | `Dict[str, Any]` |
| compliance | GET | `/hoc/api/cus/compliance/rules/{rule_id}` | `get_rule` | unknown | `` | `` | `Dict[str, Any]` |
| compliance | GET | `/hoc/api/cus/compliance/status` | `get_compliance_status` | unknown | `` | `` | `Dict[str, Any]` |
| compliance | POST | `/hoc/api/cus/compliance/verify` | `verify_compliance` | unknown | `` | `` | `Dict[str, Any]` |
| connectors | GET | `/hoc/api/cus/connectors` | `list_connectors` | unknown | `` | `` | `Dict[str, Any]` |
| connectors | POST | `/hoc/api/cus/connectors` | `register_connector` | unknown | `` | `` | `Dict[str, Any]` |
| connectors | GET | `/hoc/api/cus/connectors/{connector_id}` | `get_connector` | unknown | `` | `` | `Dict[str, Any]` |
| connectors | PUT | `/hoc/api/cus/connectors/{connector_id}` | `update_connector` | unknown | `` | `` | `Dict[str, Any]` |
| connectors | DELETE | `/hoc/api/cus/connectors/{connector_id}` | `delete_connector` | unknown | `` | `` | `Dict[str, Any]` |
| connectors | POST | `/hoc/api/cus/connectors/{connector_id}/test` | `test_connector` | unknown | `` | `` | `Dict[str, Any]` |
| controls | GET | `/hoc/api/cus/controls` | `list_controls` | unknown | `` | `` | `Dict[str, Any]` |
| controls | GET | `/hoc/api/cus/controls/list` | `list_controls_public` | unknown | `` | `` | `ControlsListResponse` |
| controls | GET | `/hoc/api/cus/controls/status` | `get_status` | unknown | `` | `` | `Dict[str, Any]` |
| controls | GET | `/hoc/api/cus/controls/{control_id}` | `get_control` | unknown | `` | `` | `Dict[str, Any]` |
| controls | PUT | `/hoc/api/cus/controls/{control_id}` | `update_control` | unknown | `` | `` | `Dict[str, Any]` |
| controls | POST | `/hoc/api/cus/controls/{control_id}/disable` | `disable_control` | unknown | `` | `` | `Dict[str, Any]` |
| controls | POST | `/hoc/api/cus/controls/{control_id}/enable` | `enable_control` | unknown | `` | `` | `Dict[str, Any]` |
| cost | GET | `/hoc/api/cus/cost/anomalies` | `get_anomalies` | unknown | `` | `` | `CostAnomaliesEnvelope` |
| cost | POST | `/hoc/api/cus/cost/anomalies/detect` | `trigger_anomaly_detection` | unknown | `` | `` | `AnomalyDetectionResponse` |
| cost | GET | `/hoc/api/cus/cost/budgets` | `list_budgets` | unknown | `` | `` | `List[BudgetResponse]` |
| cost | POST | `/hoc/api/cus/cost/budgets` | `create_or_update_budget` | unknown | `` | `` | `BudgetResponse` |
| cost | GET | `/hoc/api/cus/cost/by-feature` | `get_costs_by_feature` | unknown | `` | `` | `CostByFeatureEnvelope` |
| cost | GET | `/hoc/api/cus/cost/by-model` | `get_costs_by_model` | unknown | `` | `` | `CostByModelEnvelope` |
| cost | GET | `/hoc/api/cus/cost/by-user` | `get_costs_by_user` | unknown | `` | `` | `CostByUserEnvelope` |
| cost | GET | `/hoc/api/cus/cost/dashboard` | `get_cost_dashboard` | unknown | `` | `` | `CostDashboard` |
| cost | GET | `/hoc/api/cus/cost/features` | `list_feature_tags` | unknown | `` | `` | `List[FeatureTagResponse]` |
| cost | POST | `/hoc/api/cus/cost/features` | `create_feature_tag` | unknown | `` | `` | `FeatureTagResponse` |
| cost | PUT | `/hoc/api/cus/cost/features/{tag}` | `update_feature_tag` | unknown | `` | `` | `FeatureTagResponse` |
| cost | GET | `/hoc/api/cus/cost/projection` | `get_projection` | unknown | `` | `` | `CostProjection` |
| cost | POST | `/hoc/api/cus/cost/record` | `record_cost` | unknown | `` | `` | `` |
| cost | GET | `/hoc/api/cus/cost/summary` | `get_cost_summary` | unknown | `` | `` | `CostSummary` |
| costsim | GET | `/hoc/api/cus/costsim/canary/reports` | `get_canary_reports` | unknown | `` | `` | `` |
| costsim | POST | `/hoc/api/cus/costsim/canary/run` | `trigger_canary_run` | unknown | `` | `` | `CanaryRunResponse` |
| costsim | GET | `/hoc/api/cus/costsim/datasets` | `list_datasets` | unknown | `` | `` | `List[DatasetInfo]` |
| costsim | POST | `/hoc/api/cus/costsim/datasets/validate-all` | `validate_all` | unknown | `` | `` | `` |
| costsim | GET | `/hoc/api/cus/costsim/datasets/{dataset_id}` | `get_dataset_info` | unknown | `` | `` | `` |
| costsim | POST | `/hoc/api/cus/costsim/datasets/{dataset_id}/validate` | `validate_against_dataset` | unknown | `` | `` | `ValidationResultResponse` |
| costsim | GET | `/hoc/api/cus/costsim/divergence` | `get_divergence_report` | unknown | `` | `` | `DivergenceReportResponse` |
| costsim | GET | `/hoc/api/cus/costsim/v2/incidents` | `get_incidents` | unknown | `` | `` | `` |
| costsim | POST | `/hoc/api/cus/costsim/v2/reset` | `reset_circuit_breaker` | unknown | `` | `` | `` |
| costsim | POST | `/hoc/api/cus/costsim/v2/simulate` | `simulate_v2` | unknown | `` | `` | `SandboxSimulateResponse` |
| costsim | GET | `/hoc/api/cus/costsim/v2/status` | `get_sandbox_status` | unknown | `` | `` | `SandboxStatusResponse` |
| customer | POST | `/hoc/api/cus/customer/acknowledge` | `acknowledge_declaration` | unknown | `` | `` | `AcknowledgementResponse` |
| customer | GET | `/hoc/api/cus/customer/declaration/{declaration_id}` | `get_declaration` | unknown | `` | `` | `PreRunDeclaration` |
| customer | GET | `/hoc/api/cus/customer/outcome/{run_id}` | `get_outcome_reconciliation` | unknown | `` | `` | `OutcomeReconciliation` |
| customer | POST | `/hoc/api/cus/customer/pre-run` | `get_pre_run_declaration` | unknown | `` | `` | `PreRunDeclaration` |
| datasources | GET | `/hoc/api/cus/datasources` | `list_sources` | unknown | `` | `` | `Dict[str, Any]` |
| datasources | POST | `/hoc/api/cus/datasources` | `create_source` | unknown | `` | `` | `Dict[str, Any]` |
| datasources | GET | `/hoc/api/cus/datasources/stats` | `get_statistics` | unknown | `` | `` | `Dict[str, Any]` |
| datasources | GET | `/hoc/api/cus/datasources/{source_id}` | `get_source` | unknown | `` | `` | `Dict[str, Any]` |
| datasources | PUT | `/hoc/api/cus/datasources/{source_id}` | `update_source` | unknown | `` | `` | `Dict[str, Any]` |
| datasources | DELETE | `/hoc/api/cus/datasources/{source_id}` | `delete_source` | unknown | `` | `` | `Dict[str, Any]` |
| datasources | POST | `/hoc/api/cus/datasources/{source_id}/activate` | `activate_source` | unknown | `` | `` | `Dict[str, Any]` |
| datasources | POST | `/hoc/api/cus/datasources/{source_id}/deactivate` | `deactivate_source` | unknown | `` | `` | `Dict[str, Any]` |
| datasources | POST | `/hoc/api/cus/datasources/{source_id}/test` | `test_connection` | unknown | `` | `` | `Dict[str, Any]` |
| detection | GET | `/hoc/api/cus/detection/anomalies` | `list_anomalies` | unknown | `` | `` | `Dict[str, Any]` |
| detection | GET | `/hoc/api/cus/detection/anomalies/{anomaly_id}` | `get_anomaly` | unknown | `` | `` | `Dict[str, Any]` |
| detection | POST | `/hoc/api/cus/detection/anomalies/{anomaly_id}/acknowledge` | `acknowledge_anomaly` | unknown | `` | `` | `Dict[str, Any]` |
| detection | POST | `/hoc/api/cus/detection/anomalies/{anomaly_id}/resolve` | `resolve_anomaly` | unknown | `` | `` | `Dict[str, Any]` |
| detection | POST | `/hoc/api/cus/detection/run` | `run_detection` | unknown | `` | `` | `Dict[str, Any]` |
| detection | GET | `/hoc/api/cus/detection/status` | `get_detection_status` | unknown | `` | `` | `Dict[str, Any]` |
| embedding | DELETE | `/hoc/api/cus/embedding/cache` | `clear_embedding_cache` | unknown | `` | `` | `` |
| embedding | GET | `/hoc/api/cus/embedding/cache/stats` | `embedding_cache_stats` | unknown | `` | `` | `` |
| embedding | POST | `/hoc/api/cus/embedding/compose` | `compose_embedding` | unknown | `` | `` | `IAECComposeResponse` |
| embedding | GET | `/hoc/api/cus/embedding/config` | `get_embedding_config` | unknown | `` | `` | `EmbeddingConfigResponse` |
| embedding | POST | `/hoc/api/cus/embedding/decompose` | `decompose_embedding` | unknown | `` | `` | `IAECDecomposeResponse` |
| embedding | GET | `/hoc/api/cus/embedding/health` | `embedding_health` | unknown | `` | `` | `` |
| embedding | POST | `/hoc/api/cus/embedding/iaec/check-mismatch` | `check_mismatch` | unknown | `` | `` | `` |
| embedding | GET | `/hoc/api/cus/embedding/iaec/instructions` | `get_iaec_instructions` | unknown | `` | `` | `` |
| embedding | GET | `/hoc/api/cus/embedding/iaec/segment-info` | `get_iaec_segment_info` | unknown | `` | `` | `` |
| embedding | GET | `/hoc/api/cus/embedding/quota` | `get_embedding_quota` | unknown | `` | `` | `EmbeddingQuotaResponse` |
| enforcement | POST | `/hoc/api/cus/enforcement/batch` | `batch_enforcement_check` | unknown | `` | `` | `` |
| enforcement | POST | `/hoc/api/cus/enforcement/check` | `check_enforcement` | unknown | `` | `` | `` |
| enforcement | GET | `/hoc/api/cus/enforcement/status` | `get_enforcement_status` | unknown | `` | `` | `` |
| evidence | GET | `/hoc/api/cus/evidence/chains` | `list_chains` | unknown | `` | `` | `Dict[str, Any]` |
| evidence | POST | `/hoc/api/cus/evidence/chains` | `create_chain` | unknown | `` | `` | `Dict[str, Any]` |
| evidence | GET | `/hoc/api/cus/evidence/chains/{chain_id}` | `get_chain` | unknown | `` | `` | `Dict[str, Any]` |
| evidence | POST | `/hoc/api/cus/evidence/chains/{chain_id}/evidence` | `add_evidence` | unknown | `` | `` | `Dict[str, Any]` |
| evidence | GET | `/hoc/api/cus/evidence/chains/{chain_id}/verify` | `verify_chain` | unknown | `` | `` | `Dict[str, Any]` |
| evidence | POST | `/hoc/api/cus/evidence/export` | `create_export` | unknown | `` | `` | `Dict[str, Any]` |
| evidence | GET | `/hoc/api/cus/evidence/exports` | `list_exports` | unknown | `` | `` | `Dict[str, Any]` |
| evidence | GET | `/hoc/api/cus/evidence/exports/{export_id}` | `get_export` | unknown | `` | `` | `Dict[str, Any]` |
| feedback | GET | `/hoc/api/cus/feedback` | `list_feedback` | unknown | `` | `` | `FeedbackListResponse` |
| feedback | GET | `/hoc/api/cus/feedback/stats/summary` | `get_feedback_stats` | unknown | `` | `` | `` |
| feedback | GET | `/hoc/api/cus/feedback/{feedback_id}` | `get_feedback` | unknown | `` | `` | `FeedbackDetailResponse` |
| governance | GET | `/hoc/api/cus/governance/boot-status` | `get_boot_status` | unknown | `` | `` | `Dict[str, Any]` |
| governance | GET | `/hoc/api/cus/governance/conflicts` | `list_conflicts` | unknown | `` | `` | `Dict[str, Any]` |
| governance | POST | `/hoc/api/cus/governance/kill-switch` | `toggle_kill_switch` | unknown | `` | `` | `Dict[str, Any]` |
| governance | POST | `/hoc/api/cus/governance/mode` | `set_governance_mode` | unknown | `` | `` | `Dict[str, Any]` |
| governance | POST | `/hoc/api/cus/governance/resolve-conflict` | `resolve_conflict` | unknown | `` | `` | `Dict[str, Any]` |
| governance | GET | `/hoc/api/cus/governance/state` | `get_governance_state` | unknown | `` | `` | `Dict[str, Any]` |
| guard | GET | `/hoc/api/cus/guard/costs/explained` | `get_cost_explained` | unknown | `` | `` | `CustomerCostExplainedDTO` |
| guard | GET | `/hoc/api/cus/guard/costs/incidents` | `get_cost_incidents` | unknown | `` | `` | `CustomerCostIncidentListDTO` |
| guard | GET | `/hoc/api/cus/guard/costs/summary` | `get_cost_summary` | unknown | `` | `` | `CustomerCostSummaryDTO` |
| guard | GET | `/hoc/api/cus/guard/incidents` | `list_incidents` | unknown | `` | `` | `` |
| guard | POST | `/hoc/api/cus/guard/incidents/search` | `search_incidents` | unknown | `` | `` | `IncidentSearchResponse` |
| guard | GET | `/hoc/api/cus/guard/incidents/{incident_id}` | `get_incident_detail` | unknown | `` | `` | `IncidentDetailResponse` |
| guard | POST | `/hoc/api/cus/guard/incidents/{incident_id}/acknowledge` | `acknowledge_incident` | unknown | `` | `` | `` |
| guard | POST | `/hoc/api/cus/guard/incidents/{incident_id}/export` | `export_incident_evidence` | unknown | `` | `` | `` |
| guard | GET | `/hoc/api/cus/guard/incidents/{incident_id}/narrative` | `get_customer_incident_narrative` | unknown | `` | `` | `CustomerIncidentNarrativeDTO` |
| guard | POST | `/hoc/api/cus/guard/incidents/{incident_id}/resolve` | `resolve_incident` | unknown | `` | `` | `` |
| guard | GET | `/hoc/api/cus/guard/incidents/{incident_id}/timeline` | `get_decision_timeline` | unknown | `` | `` | `DecisionTimelineResponse` |
| guard | GET | `/hoc/api/cus/guard/keys` | `list_api_keys` | unknown | `` | `` | `` |
| guard | POST | `/hoc/api/cus/guard/keys/{key_id}/freeze` | `freeze_api_key` | unknown | `` | `` | `` |
| guard | POST | `/hoc/api/cus/guard/keys/{key_id}/unfreeze` | `unfreeze_api_key` | unknown | `` | `` | `` |
| guard | POST | `/hoc/api/cus/guard/killswitch/activate` | `activate_killswitch` | unknown | `` | `` | `` |
| guard | POST | `/hoc/api/cus/guard/killswitch/deactivate` | `deactivate_killswitch` | unknown | `` | `` | `` |
| guard | GET | `/hoc/api/cus/guard/logs` | `list_logs` | unknown | `` | `` | `CustomerLogListResponse` |
| guard | GET | `/hoc/api/cus/guard/logs/export` | `export_logs` | unknown | `` | `` | `` |
| guard | GET | `/hoc/api/cus/guard/logs/{log_id}` | `get_log` | unknown | `` | `` | `CustomerLogDetail` |
| guard | POST | `/hoc/api/cus/guard/onboarding/verify` | `onboarding_verify` | unknown | `` | `` | `OnboardingVerifyResponse` |
| guard | GET | `/hoc/api/cus/guard/policies` | `get_policy_constraints` | unknown | `` | `` | `CustomerPolicyConstraints` |
| guard | GET | `/hoc/api/cus/guard/policies/guardrails/{guardrail_id}` | `get_guardrail_detail` | unknown | `` | `` | `CustomerGuardrail` |
| guard | POST | `/hoc/api/cus/guard/replay/{call_id}` | `replay_call` | unknown | `` | `` | `ReplayResult` |
| guard | GET | `/hoc/api/cus/guard/settings` | `get_settings` | unknown | `` | `` | `TenantSettings` |
| guard | GET | `/hoc/api/cus/guard/snapshot/today` | `get_today_snapshot` | unknown | `` | `` | `TodaySnapshot` |
| guard | GET | `/hoc/api/cus/guard/status` | `get_guard_status` | unknown | `` | `` | `GuardStatus` |
| incidents | GET | `/hoc/api/cus/incidents` | `list_incidents` | unknown | `` | `` | `IncidentListResponse` |
| incidents | GET | `/hoc/api/cus/incidents/active` | `list_active_incidents` | unknown | `` | `` | `IncidentListResponse` |
| incidents | GET | `/hoc/api/cus/incidents/by-run/{run_id}` | `get_incidents_for_run` | unknown | `` | `` | `IncidentsByRunResponse` |
| incidents | GET | `/hoc/api/cus/incidents/cost-impact` | `analyze_cost_impact` | unknown | `` | `` | `CostImpactResponse` |
| incidents | GET | `/hoc/api/cus/incidents/historical` | `list_historical_incidents` | unknown | `` | `` | `IncidentListResponse` |
| incidents | GET | `/hoc/api/cus/incidents/historical/cost-trend` | `get_historical_cost_trend` | unknown | `` | `` | `CostTrendResponse` |
| incidents | GET | `/hoc/api/cus/incidents/historical/distribution` | `get_historical_distribution` | unknown | `` | `` | `HistoricalDistributionResponse` |
| incidents | GET | `/hoc/api/cus/incidents/historical/trend` | `get_historical_trend` | unknown | `` | `` | `HistoricalTrendResponse` |
| incidents | GET | `/hoc/api/cus/incidents/list` | `list_incidents_public` | unknown | `` | `` | `IncidentsListResponse` |
| incidents | GET | `/hoc/api/cus/incidents/metrics` | `get_incident_metrics` | unknown | `` | `` | `IncidentMetricsResponse` |
| incidents | GET | `/hoc/api/cus/incidents/patterns` | `detect_patterns` | unknown | `` | `` | `PatternDetectionResponse` |
| incidents | GET | `/hoc/api/cus/incidents/recurring` | `analyze_recurrence` | unknown | `` | `` | `RecurrenceAnalysisResponse` |
| incidents | GET | `/hoc/api/cus/incidents/resolved` | `list_resolved_incidents` | unknown | `` | `` | `IncidentListResponse` |
| incidents | GET | `/hoc/api/cus/incidents/{incident_id}` | `get_incident_detail` | unknown | `` | `` | `IncidentDetailResponse` |
| incidents | GET | `/hoc/api/cus/incidents/{incident_id}/evidence` | `get_incident_evidence` | unknown | `` | `` | `` |
| incidents | POST | `/hoc/api/cus/incidents/{incident_id}/export/evidence` | `export_evidence` | unknown | `` | `` | `` |
| incidents | POST | `/hoc/api/cus/incidents/{incident_id}/export/executive-debrief` | `export_executive_debrief` | unknown | `` | `` | `` |
| incidents | POST | `/hoc/api/cus/incidents/{incident_id}/export/soc2` | `export_soc2` | unknown | `` | `` | `` |
| incidents | GET | `/hoc/api/cus/incidents/{incident_id}/learnings` | `get_incident_learnings` | unknown | `` | `` | `LearningsResponse` |
| incidents | GET | `/hoc/api/cus/incidents/{incident_id}/proof` | `get_incident_proof` | unknown | `` | `` | `` |
| integration | GET | `/hoc/api/cus/integration/checkpoints` | `list_pending_checkpoints` | unknown | `` | `` | `list[CheckpointResponse]` |
| integration | GET | `/hoc/api/cus/integration/checkpoints/{checkpoint_id}` | `get_checkpoint` | unknown | `` | `` | `CheckpointResponse` |
| integration | POST | `/hoc/api/cus/integration/checkpoints/{checkpoint_id}/resolve` | `resolve_checkpoint` | unknown | `` | `` | `` |
| integration | GET | `/hoc/api/cus/integration/graduation` | `get_graduation_status` | unknown | `` | `` | `HardenedGraduationResponse` |
| integration | POST | `/hoc/api/cus/integration/graduation/re-evaluate` | `trigger_graduation_re_evaluation` | unknown | `` | `` | `` |
| integration | POST | `/hoc/api/cus/integration/graduation/record-view` | `record_timeline_view` | unknown | `` | `` | `` |
| integration | POST | `/hoc/api/cus/integration/graduation/simulate/prevention` | `simulate_prevention` | unknown | `` | `` | `` |
| integration | POST | `/hoc/api/cus/integration/graduation/simulate/regret` | `simulate_regret` | unknown | `` | `` | `` |
| integration | POST | `/hoc/api/cus/integration/graduation/simulate/timeline-view` | `simulate_timeline_view` | unknown | `` | `` | `` |
| integration | GET | `/hoc/api/cus/integration/loop/{incident_id}` | `get_loop_status` | unknown | `` | `` | `LoopStatusResponse` |
| integration | GET | `/hoc/api/cus/integration/loop/{incident_id}/narrative` | `get_loop_narrative` | unknown | `` | `` | `` |
| integration | POST | `/hoc/api/cus/integration/loop/{incident_id}/retry` | `retry_loop_stage` | unknown | `` | `` | `LoopStatusResponse` |
| integration | POST | `/hoc/api/cus/integration/loop/{incident_id}/revert` | `revert_loop` | unknown | `` | `` | `` |
| integration | GET | `/hoc/api/cus/integration/loop/{incident_id}/stages` | `get_loop_stages` | unknown | `` | `` | `list[StageDetail]` |
| integration | GET | `/hoc/api/cus/integration/loop/{incident_id}/stream` | `stream_loop_status` | unknown | `` | `` | `` |
| integration | GET | `/hoc/api/cus/integration/stats` | `get_integration_stats` | unknown | `` | `` | `IntegrationStatsResponse` |
| integration | GET | `/hoc/api/cus/integration/timeline/{incident_id}` | `get_prevention_timeline` | unknown | `` | `` | `PreventionTimelineResponse` |
| integrations | GET | `/hoc/api/cus/integrations` | `list_integrations` | unknown | `` | `` | `` |
| integrations | POST | `/hoc/api/cus/integrations` | `create_integration` | unknown | `` | `` | `` |
| integrations | GET | `/hoc/api/cus/integrations/list` | `list_integrations_public` | unknown | `` | `` | `IntegrationsListResponse` |
| integrations | GET | `/hoc/api/cus/integrations/mcp-servers` | `list_mcp_servers` | unknown | `` | `` | `McpServerListResponse` |
| integrations | POST | `/hoc/api/cus/integrations/mcp-servers` | `register_mcp_server` | unknown | `` | `` | `McpRegistrationResponse` |
| integrations | GET | `/hoc/api/cus/integrations/mcp-servers/{server_id}` | `get_mcp_server` | unknown | `` | `` | `McpServerResponse` |
| integrations | DELETE | `/hoc/api/cus/integrations/mcp-servers/{server_id}` | `delete_mcp_server` | unknown | `` | `` | `McpDeleteResponse` |
| integrations | POST | `/hoc/api/cus/integrations/mcp-servers/{server_id}/discover` | `discover_mcp_tools` | unknown | `` | `` | `McpDiscoveryResponse` |
| integrations | GET | `/hoc/api/cus/integrations/mcp-servers/{server_id}/health` | `check_mcp_health` | unknown | `` | `` | `McpHealthResponse` |
| integrations | GET | `/hoc/api/cus/integrations/mcp-servers/{server_id}/invocations` | `list_mcp_invocations` | unknown | `` | `` | `McpInvocationListResponse` |
| integrations | GET | `/hoc/api/cus/integrations/mcp-servers/{server_id}/tools` | `list_mcp_tools` | unknown | `` | `` | `McpToolListResponse` |
| integrations | POST | `/hoc/api/cus/integrations/mcp-servers/{server_id}/tools/{tool_id}/invoke` | `invoke_mcp_tool` | unknown | `` | `` | `McpInvokeResponse` |
| integrations | GET | `/hoc/api/cus/integrations/{integration_id}` | `get_integration` | unknown | `` | `` | `` |
| integrations | PUT | `/hoc/api/cus/integrations/{integration_id}` | `update_integration` | unknown | `` | `` | `` |
| integrations | DELETE | `/hoc/api/cus/integrations/{integration_id}` | `delete_integration` | unknown | `` | `` | `` |
| integrations | POST | `/hoc/api/cus/integrations/{integration_id}/disable` | `disable_integration` | unknown | `` | `` | `` |
| integrations | POST | `/hoc/api/cus/integrations/{integration_id}/enable` | `enable_integration` | unknown | `` | `` | `` |
| integrations | GET | `/hoc/api/cus/integrations/{integration_id}/health` | `get_integration_health` | unknown | `` | `` | `` |
| integrations | GET | `/hoc/api/cus/integrations/{integration_id}/limits` | `get_integration_limits` | unknown | `` | `` | `` |
| integrations | POST | `/hoc/api/cus/integrations/{integration_id}/test` | `test_integration_credentials` | unknown | `` | `` | `` |
| lifecycle | GET | `/hoc/api/cus/lifecycle/agents` | `list_agents` | unknown | `` | `` | `Dict[str, Any]` |
| lifecycle | POST | `/hoc/api/cus/lifecycle/agents` | `create_agent` | unknown | `` | `` | `Dict[str, Any]` |
| lifecycle | GET | `/hoc/api/cus/lifecycle/agents/{agent_id}` | `get_agent` | unknown | `` | `` | `Dict[str, Any]` |
| lifecycle | POST | `/hoc/api/cus/lifecycle/agents/{agent_id}/start` | `start_agent` | unknown | `` | `` | `Dict[str, Any]` |
| lifecycle | POST | `/hoc/api/cus/lifecycle/agents/{agent_id}/stop` | `stop_agent` | unknown | `` | `` | `Dict[str, Any]` |
| lifecycle | POST | `/hoc/api/cus/lifecycle/agents/{agent_id}/terminate` | `terminate_agent` | unknown | `` | `` | `Dict[str, Any]` |
| lifecycle | GET | `/hoc/api/cus/lifecycle/runs` | `list_runs` | unknown | `` | `` | `Dict[str, Any]` |
| lifecycle | POST | `/hoc/api/cus/lifecycle/runs` | `create_run` | unknown | `` | `` | `Dict[str, Any]` |
| lifecycle | GET | `/hoc/api/cus/lifecycle/runs/{run_id}` | `get_run` | unknown | `` | `` | `Dict[str, Any]` |
| lifecycle | POST | `/hoc/api/cus/lifecycle/runs/{run_id}/cancel` | `cancel_run` | unknown | `` | `` | `Dict[str, Any]` |
| lifecycle | POST | `/hoc/api/cus/lifecycle/runs/{run_id}/pause` | `pause_run` | unknown | `` | `` | `Dict[str, Any]` |
| lifecycle | POST | `/hoc/api/cus/lifecycle/runs/{run_id}/resume` | `resume_run` | unknown | `` | `` | `Dict[str, Any]` |
| lifecycle | GET | `/hoc/api/cus/lifecycle/summary` | `get_summary` | unknown | `` | `` | `Dict[str, Any]` |
| limits | GET | `/hoc/api/cus/limits/overrides` | `list_overrides` | unknown | `` | `` | `OverrideListResponse` |
| limits | POST | `/hoc/api/cus/limits/overrides` | `create_override` | unknown | `` | `` | `OverrideDetail` |
| limits | GET | `/hoc/api/cus/limits/overrides/{override_id}` | `get_override` | unknown | `` | `` | `OverrideDetail` |
| limits | DELETE | `/hoc/api/cus/limits/overrides/{override_id}` | `cancel_override` | unknown | `` | `` | `OverrideDetail` |
| limits | POST | `/hoc/api/cus/limits/simulate` | `simulate_execution` | unknown | `` | `` | `SimulateResponse` |
| logs | GET | `/hoc/api/cus/logs/audit` | `list_audit_entries` | unknown | `` | `` | `AuditLedgerResponse` |
| logs | GET | `/hoc/api/cus/logs/audit/access` | `get_audit_access` | unknown | `` | `` | `AuditAccess` |
| logs | GET | `/hoc/api/cus/logs/audit/authorization` | `get_audit_authorization` | unknown | `` | `` | `AuditAuthorization` |
| logs | GET | `/hoc/api/cus/logs/audit/exports` | `get_audit_exports` | unknown | `` | `` | `AuditExports` |
| logs | GET | `/hoc/api/cus/logs/audit/identity` | `get_audit_identity` | unknown | `` | `` | `AuditIdentity` |
| logs | GET | `/hoc/api/cus/logs/audit/integrity` | `get_audit_integrity` | unknown | `` | `` | `AuditIntegrity` |
| logs | GET | `/hoc/api/cus/logs/audit/{entry_id}` | `get_audit_entry` | unknown | `` | `` | `AuditLedgerDetailItem` |
| logs | GET | `/hoc/api/cus/logs/list` | `list_logs_public` | unknown | `` | `` | `LogsFeedResponse` |
| logs | GET | `/hoc/api/cus/logs/llm-runs` | `list_llm_run_records` | unknown | `` | `` | `LLMRunRecordsResponse` |
| logs | GET | `/hoc/api/cus/logs/llm-runs/{run_id}/envelope` | `get_llm_run_envelope` | unknown | `` | `` | `LLMRunEnvelope` |
| logs | GET | `/hoc/api/cus/logs/llm-runs/{run_id}/export` | `get_llm_run_export` | unknown | `` | `` | `LLMRunExport` |
| logs | GET | `/hoc/api/cus/logs/llm-runs/{run_id}/governance` | `get_llm_run_governance` | unknown | `` | `` | `LLMRunGovernance` |
| logs | GET | `/hoc/api/cus/logs/llm-runs/{run_id}/replay` | `get_llm_run_replay` | unknown | `` | `` | `LLMRunReplay` |
| logs | GET | `/hoc/api/cus/logs/llm-runs/{run_id}/trace` | `get_llm_run_trace` | unknown | `` | `` | `LLMRunTrace` |
| logs | GET | `/hoc/api/cus/logs/system` | `list_system_records` | unknown | `` | `` | `SystemRecordsResponse` |
| logs | GET | `/hoc/api/cus/logs/system/audit` | `get_system_audit` | unknown | `` | `` | `SystemAudit` |
| logs | GET | `/hoc/api/cus/logs/system/{run_id}/events` | `get_system_events` | unknown | `` | `` | `SystemEvents` |
| logs | GET | `/hoc/api/cus/logs/system/{run_id}/replay` | `get_system_replay` | unknown | `` | `` | `SystemReplay` |
| logs | GET | `/hoc/api/cus/logs/system/{run_id}/snapshot` | `get_system_snapshot` | unknown | `` | `` | `SystemSnapshot` |
| logs | GET | `/hoc/api/cus/logs/system/{run_id}/telemetry` | `get_system_telemetry` | unknown | `` | `` | `TelemetryStub` |
| memory | GET | `/hoc/api/cus/memory/pins` | `list_pins` | unknown | `` | `` | `MemoryPinListResponse` |
| memory | POST | `/hoc/api/cus/memory/pins` | `create_or_upsert_pin` | unknown | `` | `` | `MemoryPinResponse` |
| memory | POST | `/hoc/api/cus/memory/pins/cleanup` | `cleanup_expired_pins` | unknown | `` | `` | `` |
| memory | GET | `/hoc/api/cus/memory/pins/{key}` | `get_pin` | unknown | `` | `` | `MemoryPinResponse` |
| memory | DELETE | `/hoc/api/cus/memory/pins/{key}` | `delete_pin` | unknown | `` | `` | `MemoryPinDeleteResponse` |
| monitors | GET | `/hoc/api/cus/monitors` | `list_monitors` | unknown | `` | `` | `Dict[str, Any]` |
| monitors | POST | `/hoc/api/cus/monitors` | `create_monitor` | unknown | `` | `` | `Dict[str, Any]` |
| monitors | GET | `/hoc/api/cus/monitors/status` | `get_status` | unknown | `` | `` | `Dict[str, Any]` |
| monitors | GET | `/hoc/api/cus/monitors/{monitor_id}` | `get_monitor` | unknown | `` | `` | `Dict[str, Any]` |
| monitors | PUT | `/hoc/api/cus/monitors/{monitor_id}` | `update_monitor` | unknown | `` | `` | `Dict[str, Any]` |
| monitors | DELETE | `/hoc/api/cus/monitors/{monitor_id}` | `delete_monitor` | unknown | `` | `` | `Dict[str, Any]` |
| monitors | POST | `/hoc/api/cus/monitors/{monitor_id}/check` | `run_check` | unknown | `` | `` | `Dict[str, Any]` |
| monitors | GET | `/hoc/api/cus/monitors/{monitor_id}/history` | `get_history` | unknown | `` | `` | `Dict[str, Any]` |
| notifications | GET | `/hoc/api/cus/notifications` | `list_notifications` | unknown | `` | `` | `Dict[str, Any]` |
| notifications | POST | `/hoc/api/cus/notifications` | `send_notification` | unknown | `` | `` | `Dict[str, Any]` |
| notifications | GET | `/hoc/api/cus/notifications/channels` | `list_channels` | unknown | `` | `` | `Dict[str, Any]` |
| notifications | GET | `/hoc/api/cus/notifications/preferences` | `get_preferences` | unknown | `` | `` | `Dict[str, Any]` |
| notifications | PUT | `/hoc/api/cus/notifications/preferences` | `update_preferences` | unknown | `` | `` | `Dict[str, Any]` |
| notifications | GET | `/hoc/api/cus/notifications/{notification_id}` | `get_notification` | unknown | `` | `` | `Dict[str, Any]` |
| notifications | POST | `/hoc/api/cus/notifications/{notification_id}/read` | `mark_as_read` | unknown | `` | `` | `Dict[str, Any]` |
| overview | GET | `/hoc/api/cus/overview/costs` | `get_costs` | unknown | `` | `` | `CostsResponse` |
| overview | GET | `/hoc/api/cus/overview/decisions` | `get_decisions` | unknown | `` | `` | `DecisionsResponse` |
| overview | GET | `/hoc/api/cus/overview/decisions/count` | `get_decisions_count` | unknown | `` | `` | `DecisionsCountResponse` |
| overview | GET | `/hoc/api/cus/overview/highlights` | `get_highlights` | unknown | `` | `` | `HighlightsResponse` |
| overview | GET | `/hoc/api/cus/overview/highlights` | `get_overview_highlights_public` | unknown | `` | `` | `OverviewHighlightsPublicResponse` |
| overview | GET | `/hoc/api/cus/overview/recovery-stats` | `get_recovery_stats` | unknown | `` | `` | `RecoveryStatsResponse` |
| policies | GET | `/hoc/api/cus/policies/budgets` | `list_budget_definitions` | unknown | `` | `` | `BudgetsListResponse` |
| policies | GET | `/hoc/api/cus/policies/conflicts` | `list_policy_conflicts` | unknown | `` | `` | `ConflictsListResponse` |
| policies | GET | `/hoc/api/cus/policies/dependencies` | `get_policy_dependencies` | unknown | `` | `` | `DependencyGraphResponse` |
| policies | GET | `/hoc/api/cus/policies/lessons` | `list_lessons` | unknown | `` | `` | `LessonsListResponse` |
| policies | GET | `/hoc/api/cus/policies/lessons/stats` | `get_lesson_stats` | unknown | `` | `` | `LessonStatsResponse` |
| policies | GET | `/hoc/api/cus/policies/lessons/{lesson_id}` | `get_lesson_detail` | unknown | `` | `` | `LessonDetailResponse` |
| policies | GET | `/hoc/api/cus/policies/limits` | `list_limits` | unknown | `` | `` | `LimitsListResponse` |
| policies | POST | `/hoc/api/cus/policies/limits` | `create_limit` | unknown | `` | `` | `LimitDetail` |
| policies | GET | `/hoc/api/cus/policies/limits/{limit_id}` | `get_limit_detail` | unknown | `` | `` | `LimitDetailResponse` |
| policies | PUT | `/hoc/api/cus/policies/limits/{limit_id}` | `update_limit` | unknown | `` | `` | `LimitDetail` |
| policies | DELETE | `/hoc/api/cus/policies/limits/{limit_id}` | `delete_limit` | unknown | `` | `` | `` |
| policies | GET | `/hoc/api/cus/policies/limits/{limit_id}/evidence` | `get_limit_evidence` | unknown | `` | `` | `` |
| policies | GET | `/hoc/api/cus/policies/limits/{limit_id}/params` | `get_threshold_params` | unknown | `` | `` | `ThresholdParamsResponse` |
| policies | PUT | `/hoc/api/cus/policies/limits/{limit_id}/params` | `set_threshold_params` | unknown | `` | `` | `ThresholdParamsResponse` |
| policies | GET | `/hoc/api/cus/policies/list` | `list_policies_public` | unknown | `` | `` | `PoliciesListResponse` |
| policies | GET | `/hoc/api/cus/policies/metrics` | `get_policy_metrics` | unknown | `` | `` | `PolicyMetricsResponse` |
| policies | GET | `/hoc/api/cus/policies/requests` | `list_policy_requests` | unknown | `` | `` | `PolicyRequestsListResponse` |
| policies | GET | `/hoc/api/cus/policies/rules` | `list_policy_rules` | unknown | `` | `` | `RulesListResponse` |
| policies | POST | `/hoc/api/cus/policies/rules` | `create_rule` | unknown | `` | `` | `RuleDetail` |
| policies | GET | `/hoc/api/cus/policies/rules/{rule_id}` | `get_policy_rule_detail` | unknown | `` | `` | `PolicyRuleDetailResponse` |
| policies | PUT | `/hoc/api/cus/policies/rules/{rule_id}` | `update_rule` | unknown | `` | `` | `RuleDetail` |
| policies | GET | `/hoc/api/cus/policies/rules/{rule_id}/evidence` | `get_rule_evidence` | unknown | `` | `` | `` |
| policies | GET | `/hoc/api/cus/policies/state` | `get_policy_state` | unknown | `` | `` | `PolicyStateResponse` |
| policies | GET | `/hoc/api/cus/policies/violations` | `list_policy_violations` | unknown | `` | `` | `ViolationsListResponse` |
| policy | GET | `/hoc/api/cus/policy/active` | `get_active_policies` | unknown | `` | `` | `ActivePoliciesResponse` |
| policy | GET | `/hoc/api/cus/policy/active/{policy_id}` | `get_active_policy_detail` | unknown | `` | `` | `` |
| policy | POST | `/hoc/api/cus/policy/eval` | `evaluate_policy` | unknown | `` | `` | `PolicyEvalResponse` |
| policy | GET | `/hoc/api/cus/policy/lessons` | `get_policy_lessons` | unknown | `` | `` | `LessonsResponse` |
| policy | GET | `/hoc/api/cus/policy/lessons/{lesson_id}` | `get_policy_lesson_detail` | unknown | `` | `` | `` |
| policy | GET | `/hoc/api/cus/policy/library` | `get_policy_library` | unknown | `` | `` | `PolicyLibraryResponse` |
| policy | GET | `/hoc/api/cus/policy/requests` | `list_approval_requests` | unknown | `` | `` | `List[ApprovalStatusResponse]` |
| policy | POST | `/hoc/api/cus/policy/requests` | `create_approval_request` | unknown | `` | `` | `ApprovalRequestResponse` |
| policy | GET | `/hoc/api/cus/policy/requests/{request_id}` | `get_approval_request` | unknown | `` | `` | `ApprovalStatusResponse` |
| policy | POST | `/hoc/api/cus/policy/requests/{request_id}/approve` | `approve_request` | unknown | `` | `` | `ApprovalStatusResponse` |
| policy | POST | `/hoc/api/cus/policy/requests/{request_id}/reject` | `reject_request` | unknown | `` | `` | `ApprovalStatusResponse` |
| policy | GET | `/hoc/api/cus/policy/thresholds` | `get_policy_thresholds` | unknown | `` | `` | `ThresholdsResponse` |
| policy | GET | `/hoc/api/cus/policy/thresholds/{threshold_id}` | `get_policy_threshold_detail` | unknown | `` | `` | `` |
| policy | GET | `/hoc/api/cus/policy/violations` | `get_policy_violations_v2` | unknown | `` | `` | `ViolationsResponse` |
| policy | GET | `/hoc/api/cus/policy/violations/{violation_id}` | `get_policy_violation_detail` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/conflicts` | `list_conflicts` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/conflicts/{conflict_id}/resolve` | `resolve_conflict` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/cooldowns` | `list_active_cooldowns` | unknown | `` | `` | `List[CooldownInfo]` |
| policy-layer | DELETE | `/hoc/api/cus/policy-layer/cooldowns/{agent_id}` | `clear_cooldowns` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/dependencies` | `get_dependency_graph` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/dependencies/add` | `add_dependency_with_dag_check` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/dependencies/dag/validate` | `validate_dependency_dag` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/dependencies/evaluation-order` | `get_evaluation_order` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/ethical-constraints` | `list_ethical_constraints` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/evaluate` | `evaluate_action` | unknown | `` | `` | `PolicyEvaluationResult` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/evaluate/batch` | `evaluate_batch` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/evaluate/context-aware` | `evaluate_with_context` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/lessons` | `list_lessons` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/lessons/stats` | `get_lesson_stats` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/lessons/{lesson_id}` | `get_lesson` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/lessons/{lesson_id}/convert` | `convert_lesson_to_draft` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/lessons/{lesson_id}/defer` | `defer_lesson` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/lessons/{lesson_id}/dismiss` | `dismiss_lesson` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/metrics` | `get_policy_metrics` | unknown | `` | `` | `PolicyMetrics` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/reload` | `reload_policies` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/risk-ceilings` | `list_risk_ceilings` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/risk-ceilings/{ceiling_id}` | `get_risk_ceiling` | unknown | `` | `` | `` |
| policy-layer | PATCH | `/hoc/api/cus/policy-layer/risk-ceilings/{ceiling_id}` | `update_risk_ceiling` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/risk-ceilings/{ceiling_id}/reset` | `reset_risk_ceiling` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/safety-rules` | `list_safety_rules` | unknown | `` | `` | `` |
| policy-layer | PATCH | `/hoc/api/cus/policy-layer/safety-rules/{rule_id}` | `update_safety_rule` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/simulate` | `simulate_evaluation` | unknown | `` | `` | `PolicyEvaluationResult` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/state` | `get_policy_state` | unknown | `` | `` | `PolicyState` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/temporal-metrics/prune` | `prune_temporal_metrics` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/temporal-metrics/storage-stats` | `get_temporal_storage_stats` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/temporal-policies` | `list_temporal_policies` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/temporal-policies` | `create_temporal_policy` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/temporal-policies/{policy_id}/utilization` | `get_temporal_utilization` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/versions` | `list_policy_versions` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/versions` | `create_policy_version` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/versions/activate` | `activate_policy_version` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/versions/current` | `get_current_version` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/versions/rollback` | `rollback_to_version` | unknown | `` | `` | `` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/versions/{version_id}/check` | `check_version_integrity` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/versions/{version_id}/provenance` | `get_version_provenance` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/violations` | `list_violations` | unknown | `` | `` | `` |
| policy-layer | GET | `/hoc/api/cus/policy-layer/violations/{violation_id}` | `get_violation` | unknown | `` | `` | `PolicyViolation` |
| policy-layer | POST | `/hoc/api/cus/policy-layer/violations/{violation_id}/acknowledge` | `acknowledge_violation` | unknown | `` | `` | `` |
| policy-proposals | GET | `/hoc/api/cus/policy-proposals` | `list_proposals` | unknown | `` | `` | `ProposalListResponse` |
| policy-proposals | GET | `/hoc/api/cus/policy-proposals/stats/summary` | `get_proposal_stats` | unknown | `` | `` | `` |
| policy-proposals | GET | `/hoc/api/cus/policy-proposals/{proposal_id}` | `get_proposal` | unknown | `` | `` | `ProposalDetailResponse` |
| policy-proposals | POST | `/hoc/api/cus/policy-proposals/{proposal_id}/approve` | `approve_proposal` | unknown | `` | `` | `ApprovalResponse` |
| policy-proposals | POST | `/hoc/api/cus/policy-proposals/{proposal_id}/reject` | `reject_proposal` | unknown | `` | `` | `ApprovalResponse` |
| policy-proposals | GET | `/hoc/api/cus/policy-proposals/{proposal_id}/versions` | `list_proposal_versions` | unknown | `` | `` | `list[VersionResponse]` |
| predictions | GET | `/hoc/api/cus/predictions` | `list_predictions` | unknown | `` | `` | `PredictionListResponse` |
| predictions | GET | `/hoc/api/cus/predictions/stats/summary` | `get_prediction_stats` | unknown | `` | `` | `` |
| predictions | GET | `/hoc/api/cus/predictions/subject/{subject_type}/{subject_id}` | `get_predictions_for_subject` | unknown | `` | `` | `` |
| predictions | GET | `/hoc/api/cus/predictions/{prediction_id}` | `get_prediction` | unknown | `` | `` | `PredictionDetailResponse` |
| rate-limits | GET | `/hoc/api/cus/rate-limits` | `list_limits` | unknown | `` | `` | `Dict[str, Any]` |
| rate-limits | POST | `/hoc/api/cus/rate-limits/check` | `check_limit` | unknown | `` | `` | `Dict[str, Any]` |
| rate-limits | GET | `/hoc/api/cus/rate-limits/usage` | `get_usage` | unknown | `` | `` | `Dict[str, Any]` |
| rate-limits | GET | `/hoc/api/cus/rate-limits/{limit_id}` | `get_limit` | unknown | `` | `` | `Dict[str, Any]` |
| rate-limits | PUT | `/hoc/api/cus/rate-limits/{limit_id}` | `update_limit` | unknown | `` | `` | `Dict[str, Any]` |
| rate-limits | POST | `/hoc/api/cus/rate-limits/{limit_id}/reset` | `reset_limit` | unknown | `` | `` | `Dict[str, Any]` |
| rbac | GET | `/hoc/api/cus/rbac/audit` | `query_audit_logs` | unknown | `` | `` | `AuditResponse` |
| rbac | POST | `/hoc/api/cus/rbac/audit/cleanup` | `cleanup_audit_logs` | unknown | `` | `` | `` |
| rbac | GET | `/hoc/api/cus/rbac/info` | `get_policy_info` | unknown | `` | `` | `PolicyInfoResponse` |
| rbac | GET | `/hoc/api/cus/rbac/matrix` | `get_permission_matrix` | unknown | `` | `` | `` |
| rbac | POST | `/hoc/api/cus/rbac/reload` | `reload_policies` | unknown | `` | `` | `ReloadResponse` |
| replay | GET | `/hoc/api/cus/replay/{incident_id}/explain/{item_id}` | `explain_replay_item` | unknown | `` | `` | `` |
| replay | GET | `/hoc/api/cus/replay/{incident_id}/slice` | `get_replay_slice` | unknown | `` | `` | `ReplaySliceResponse` |
| replay | GET | `/hoc/api/cus/replay/{incident_id}/summary` | `get_incident_summary` | unknown | `` | `` | `IncidentSummaryResponse` |
| replay | GET | `/hoc/api/cus/replay/{incident_id}/timeline` | `get_replay_timeline` | unknown | `` | `` | `` |
| retrieval | POST | `/hoc/api/cus/retrieval/access` | `access_data` | unknown | `` | `` | `Dict[str, Any]` |
| runs | GET | `/hoc/api/cus/runs` | `list_runs` | unknown | `` | `` | `List[RunHistoryItem]` |
| runtime | GET | `/hoc/api/cus/runtime/capabilities` | `get_capabilities` | unknown | `` | `` | `CapabilitiesResponse` |
| runtime | POST | `/hoc/api/cus/runtime/query` | `query_runtime` | unknown | `` | `` | `QueryResponse` |
| runtime | POST | `/hoc/api/cus/runtime/replay/{run_id}` | `replay_run` | unknown | `` | `` | `ReplayResponse` |
| runtime | GET | `/hoc/api/cus/runtime/resource-contract/{resource_id}` | `get_resource_contract` | unknown | `` | `` | `` |
| runtime | POST | `/hoc/api/cus/runtime/simulate` | `simulate_plan` | unknown | `` | `` | `SimulateResponse` |
| runtime | GET | `/hoc/api/cus/runtime/skills` | `list_available_skills` | unknown | `` | `` | `SkillListResponse` |
| runtime | GET | `/hoc/api/cus/runtime/skills/{skill_id}` | `describe_skill` | unknown | `` | `` | `SkillDescriptorResponse` |
| runtime | GET | `/hoc/api/cus/runtime/traces` | `list_traces` | unknown | `` | `` | `` |
| runtime | GET | `/hoc/api/cus/runtime/traces/{run_id}` | `get_trace` | unknown | `` | `` | `` |
| scenarios | GET | `/hoc/api/cus/scenarios` | `list_scenarios` | unknown | `` | `` | `List[ScenarioResponse]` |
| scenarios | POST | `/hoc/api/cus/scenarios` | `create_scenario` | unknown | `` | `` | `ScenarioResponse` |
| scenarios | GET | `/hoc/api/cus/scenarios/info/immutability` | `get_immutability_info` | unknown | `` | `` | `` |
| scenarios | POST | `/hoc/api/cus/scenarios/simulate-adhoc` | `simulate_adhoc` | unknown | `` | `` | `SimulationResult` |
| scenarios | GET | `/hoc/api/cus/scenarios/{scenario_id}` | `get_scenario` | unknown | `` | `` | `ScenarioResponse` |
| scenarios | DELETE | `/hoc/api/cus/scenarios/{scenario_id}` | `delete_scenario` | unknown | `` | `` | `` |
| scenarios | POST | `/hoc/api/cus/scenarios/{scenario_id}/simulate` | `simulate_scenario` | unknown | `` | `` | `SimulationResult` |
| scheduler | GET | `/hoc/api/cus/scheduler/jobs` | `list_jobs` | unknown | `` | `` | `Dict[str, Any]` |
| scheduler | POST | `/hoc/api/cus/scheduler/jobs` | `create_job` | unknown | `` | `` | `Dict[str, Any]` |
| scheduler | GET | `/hoc/api/cus/scheduler/jobs/{job_id}` | `get_job` | unknown | `` | `` | `Dict[str, Any]` |
| scheduler | PUT | `/hoc/api/cus/scheduler/jobs/{job_id}` | `update_job` | unknown | `` | `` | `Dict[str, Any]` |
| scheduler | DELETE | `/hoc/api/cus/scheduler/jobs/{job_id}` | `delete_job` | unknown | `` | `` | `Dict[str, Any]` |
| scheduler | POST | `/hoc/api/cus/scheduler/jobs/{job_id}/pause` | `pause_job` | unknown | `` | `` | `Dict[str, Any]` |
| scheduler | POST | `/hoc/api/cus/scheduler/jobs/{job_id}/resume` | `resume_job` | unknown | `` | `` | `Dict[str, Any]` |
| scheduler | GET | `/hoc/api/cus/scheduler/jobs/{job_id}/runs` | `list_job_runs` | unknown | `` | `` | `Dict[str, Any]` |
| scheduler | POST | `/hoc/api/cus/scheduler/jobs/{job_id}/trigger` | `trigger_job` | unknown | `` | `` | `Dict[str, Any]` |
| scheduler | GET | `/hoc/api/cus/scheduler/runs/{run_id}` | `get_run` | unknown | `` | `` | `Dict[str, Any]` |
| session | GET | `/hoc/api/cus/session/context` | `get_session_context` | unknown | `` | `` | `` |
| status_history | GET | `/hoc/api/cus/status_history` | `query_status_history` | unknown | `` | `` | `StatusHistoryListResponse` |
| status_history | GET | `/hoc/api/cus/status_history/download/{export_id}` | `download_export` | unknown | `` | `` | `` |
| status_history | GET | `/hoc/api/cus/status_history/entity/{entity_type}/{entity_id}` | `get_entity_history` | unknown | `` | `` | `StatusHistoryListResponse` |
| status_history | POST | `/hoc/api/cus/status_history/export` | `create_export` | unknown | `` | `` | `ExportResponse` |
| status_history | GET | `/hoc/api/cus/status_history/stats` | `get_stats` | unknown | `` | `` | `StatsResponse` |
| telemetry | GET | `/hoc/api/cus/telemetry/daily-aggregates` | `get_daily_aggregates` | unknown | `` | `` | `` |
| telemetry | POST | `/hoc/api/cus/telemetry/llm-usage` | `ingest_llm_usage` | unknown | `` | `` | `` |
| telemetry | POST | `/hoc/api/cus/telemetry/llm-usage/batch` | `ingest_llm_usage_batch` | unknown | `` | `` | `` |
| telemetry | GET | `/hoc/api/cus/telemetry/usage-history` | `get_usage_history` | unknown | `` | `` | `` |
| telemetry | GET | `/hoc/api/cus/telemetry/usage-summary` | `get_usage_summary` | unknown | `` | `` | `` |
| tenant | GET | `/hoc/api/cus/tenant` | `get_current_tenant` | unknown | `` | `` | `TenantResponse` |
| tenant | GET | `/hoc/api/cus/tenant/api-keys` | `list_api_keys` | unknown | `` | `` | `List[APIKeyResponse]` |
| tenant | POST | `/hoc/api/cus/tenant/api-keys` | `create_api_key` | unknown | `` | `` | `APIKeyCreatedResponse` |
| tenant | DELETE | `/hoc/api/cus/tenant/api-keys/{key_id}` | `revoke_api_key` | unknown | `` | `` | `` |
| tenant | GET | `/hoc/api/cus/tenant/health` | `tenant_health` | unknown | `` | `` | `` |
| tenant | GET | `/hoc/api/cus/tenant/quota/runs` | `check_run_quota` | unknown | `` | `` | `QuotaCheckResponse` |
| tenant | GET | `/hoc/api/cus/tenant/quota/tokens` | `check_token_quota` | unknown | `` | `` | `QuotaCheckResponse` |
| tenant | GET | `/hoc/api/cus/tenant/usage` | `get_tenant_usage` | unknown | `` | `` | `UsageSummaryResponse` |
| traces | GET | `/hoc/api/cus/traces` | `list_traces` | unknown | `` | `` | `TraceListResponse` |
| traces | POST | `/hoc/api/cus/traces` | `store_trace` | unknown | `` | `` | `` |
| traces | GET | `/hoc/api/cus/traces/by-hash/{root_hash}` | `get_trace_by_hash` | unknown | `` | `` | `TraceDetailResponse` |
| traces | POST | `/hoc/api/cus/traces/cleanup` | `cleanup_old_traces` | unknown | `` | `` | `` |
| traces | GET | `/hoc/api/cus/traces/compare/{run_id1}/{run_id2}` | `compare_traces` | unknown | `` | `` | `TraceCompareResponse` |
| traces | GET | `/hoc/api/cus/traces/idempotency/{idempotency_key}` | `check_idempotency` | unknown | `` | `` | `` |
| traces | GET | `/hoc/api/cus/traces/mismatches` | `list_all_mismatches` | unknown | `` | `` | `` |
| traces | POST | `/hoc/api/cus/traces/mismatches/bulk-report` | `bulk_report_mismatches` | unknown | `` | `` | `` |
| traces | GET | `/hoc/api/cus/traces/{run_id}` | `get_trace` | unknown | `` | `` | `TraceDetailResponse` |
| traces | DELETE | `/hoc/api/cus/traces/{run_id}` | `delete_trace` | unknown | `` | `` | `` |
| traces | POST | `/hoc/api/cus/traces/{trace_id}/mismatch` | `report_mismatch` | unknown | `` | `` | `MismatchResponse` |
| traces | GET | `/hoc/api/cus/traces/{trace_id}/mismatches` | `list_trace_mismatches` | unknown | `` | `` | `` |
| traces | POST | `/hoc/api/cus/traces/{trace_id}/mismatches/{mismatch_id}/resolve` | `resolve_mismatch` | unknown | `` | `` | `` |
| v1 | GET | `/hoc/api/cus/v1/calls/{call_id}` | `get_call` | unknown | `` | `` | `ProxyCallDetail` |
| v1 | POST | `/hoc/api/cus/v1/chat/completions` | `chat_completions` | unknown | `` | `` | `ChatCompletionResponse` |
| v1 | POST | `/hoc/api/cus/v1/embeddings` | `embeddings` | unknown | `` | `` | `EmbeddingResponse` |
| v1 | GET | `/hoc/api/cus/v1/incidents` | `list_incidents` | unknown | `` | `` | `List[IncidentSummary]` |
| v1 | GET | `/hoc/api/cus/v1/incidents/{incident_id}` | `get_incident` | unknown | `` | `` | `IncidentDetail` |
| v1 | POST | `/hoc/api/cus/v1/killswitch/key` | `freeze_key` | unknown | `` | `` | `KillSwitchStatus` |
| v1 | DELETE | `/hoc/api/cus/v1/killswitch/key` | `unfreeze_key` | unknown | `` | `` | `KillSwitchStatus` |
| v1 | GET | `/hoc/api/cus/v1/killswitch/status` | `get_killswitch_status` | unknown | `` | `` | `Dict[str, Any]` |
| v1 | POST | `/hoc/api/cus/v1/killswitch/tenant` | `freeze_tenant` | unknown | `` | `` | `KillSwitchStatus` |
| v1 | DELETE | `/hoc/api/cus/v1/killswitch/tenant` | `unfreeze_tenant` | unknown | `` | `` | `KillSwitchStatus` |
| v1 | GET | `/hoc/api/cus/v1/policies/active` | `get_active_policies` | unknown | `` | `` | `List[GuardrailSummary]` |
| v1 | POST | `/hoc/api/cus/v1/replay/{call_id}` | `replay_call` | unknown | `` | `` | `ReplayResult` |
| v1 | GET | `/hoc/api/cus/v1/status` | `proxy_status` | unknown | `` | `` | `` |
| workers | GET | `/hoc/api/cus/workers` | `list_workers` | unknown | `` | `` | `List[WorkerSummaryResponse]` |
| workers | GET | `/hoc/api/cus/workers/available` | `list_available_workers_for_tenant` | unknown | `` | `` | `List[dict]` |
| workers | GET | `/hoc/api/cus/workers/business-builder/events/{run_id}` | `get_run_events` | unknown | `` | `` | `` |
| workers | GET | `/hoc/api/cus/workers/business-builder/health` | `worker_health` | unknown | `` | `` | `` |
| workers | POST | `/hoc/api/cus/workers/business-builder/replay` | `replay_execution_endpoint` | unknown | `` | `` | `WorkerRunResponse` |
| workers | POST | `/hoc/api/cus/workers/business-builder/run` | `run_worker` | unknown | `` | `` | `WorkerRunResponse` |
| workers | POST | `/hoc/api/cus/workers/business-builder/run-streaming` | `run_worker_streaming` | unknown | `` | `` | `WorkerRunResponse` |
| workers | GET | `/hoc/api/cus/workers/business-builder/runs` | `list_runs` | unknown | `` | `` | `RunListResponse` |
| workers | GET | `/hoc/api/cus/workers/business-builder/runs/{run_id}` | `get_run` | unknown | `` | `` | `WorkerRunResponse` |
| workers | DELETE | `/hoc/api/cus/workers/business-builder/runs/{run_id}` | `delete_run` | unknown | `` | `` | `` |
| workers | POST | `/hoc/api/cus/workers/business-builder/runs/{run_id}/retry` | `retry_run` | unknown | `` | `` | `RunRetryResponse` |
| workers | GET | `/hoc/api/cus/workers/business-builder/schema/brand` | `get_brand_schema` | unknown | `` | `` | `` |
| workers | GET | `/hoc/api/cus/workers/business-builder/schema/run` | `get_run_schema` | unknown | `` | `` | `` |
| workers | GET | `/hoc/api/cus/workers/business-builder/stream/{run_id}` | `stream_run_events` | unknown | `` | `` | `` |
| workers | POST | `/hoc/api/cus/workers/business-builder/validate-brand` | `validate_brand` | unknown | `` | `` | `BrandValidationResponse` |
| workers | GET | `/hoc/api/cus/workers/{worker_id}` | `get_worker_details` | unknown | `` | `` | `WorkerDetailResponse` |
| workers | GET | `/hoc/api/cus/workers/{worker_id}/config` | `get_worker_config` | unknown | `` | `` | `WorkerConfigResponse` |
| workers | PUT | `/hoc/api/cus/workers/{worker_id}/config` | `set_worker_config` | unknown | `` | `` | `WorkerConfigResponse` |
