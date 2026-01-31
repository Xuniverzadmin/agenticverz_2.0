# Customer Features

**Total features:** 225  
**Total operations:** 290  
**Health:** 192 healthy, 33 degraded, 0 orphaned  
**Generator:** `scripts/ops/hoc_feature_extractor.py`

---

## Feature Matrix

| Feature | Intents | Domains | Ops | Wired | Gaps | Health |
|---------|---------|---------|-----|-------|------|--------|
| integration | Create, Delete, Read, Update | integrations | 5 | 5 | 0 | OK |
| connector | Delete, Read, Update | integrations | 4 | 4 | 0 | OK |
| dataset | Evaluate, Read | analytics | 4 | 0 | 4 | GAP |
| limit | Evaluate, Read, Update | policies | 4 | 4 | 0 | OK |
| source | Delete, Read, Update | integrations | 4 | 4 | 0 | OK |
| statu | Read | analytics, controls, policies | 4 | 4 | 0 | OK |
| anomaly | Read, Resolve | analytics | 3 | 3 | 0 | OK |
| chain | Create, Read | logs | 3 | 3 | 0 | OK |
| completed_run | Evaluate, Read | activity, controls | 3 | 3 | 0 | OK |
| conflict | Read, Resolve | policies | 3 | 3 | 0 | OK |
| control | Read, Update | controls | 3 | 3 | 0 | OK |
| export | Create, Read | logs | 3 | 3 | 0 | OK |
| incident | Read, Resolve | integrations | 3 | 0 | 3 | GAP |
| log | Export, Read | integrations | 3 | 0 | 3 | GAP |
| metric | Read | activity, incidents, policies | 3 | 3 | 0 | OK |
| risk_ceiling | Read, Update | policies | 3 | 3 | 0 | OK |
| rule | Create, Delete, Evaluate | incidents | 3 | 0 | 3 | GAP |
| active_threshold_limit | Read | controls | 2 | 2 | 0 | OK |
| all | Detect, Evaluate | analytics | 2 | 0 | 2 | GAP |
| audit_entry | Read | logs | 2 | 2 | 0 | OK |
| capability | Read | integrations, policies | 2 | 2 | 0 | OK |
| channel | Read | account | 2 | 2 | 0 | OK |
| governance_config | Evaluate, Read | account | 2 | 2 | 0 | OK |
| incidents_for_run | Read | incidents | 2 | 2 | 0 | OK |
| intent | Create, Evaluate | policies | 2 | 2 | 0 | OK |
| key | Read | integrations | 2 | 0 | 2 | GAP |
| lesson | Read | policies | 2 | 2 | 0 | OK |
| live_run | Evaluate, Read | activity, controls | 2 | 2 | 0 | OK |
| not_raw_key | Evaluate | integrations | 2 | 0 | 2 | GAP |
| notification | Read | account | 2 | 2 | 0 | OK |
| pattern | Detect, Read | activity, incidents | 2 | 2 | 0 | OK |
| policy_version | Create, Read | policies | 2 | 2 | 0 | OK |
| preference | Read, Update | account | 2 | 2 | 0 | OK |
| profile | Read, Update | account | 2 | 2 | 0 | OK |
| resource_contract | Read | integrations, policies | 2 | 2 | 0 | OK |
| safety_rule | Read, Update | policies | 2 | 2 | 0 | OK |
| skill | Read | integrations, policies | 2 | 2 | 0 | OK |
| support_ticket | Create, Read | account | 2 | 2 | 0 | OK |
| temporal_policy | Create, Read | policies | 2 | 2 | 0 | OK |
| user | Delete, Read | account | 2 | 2 | 0 | OK |
| violation | Read | policies | 2 | 2 | 0 | OK |
| absolute_spike | Detect | analytics | 1 | 0 | 1 | GAP |
| accounts_facade | Read | account | 1 | 1 | 0 | OK |
| action_for_transition | Read | _models | 1 | 1 | 0 | OK |
| active_cooldown | Read | policies | 1 | 1 | 0 | OK |
| active_incident | Read | incidents | 1 | 1 | 0 | OK |
| activity_facade | Read | activity | 1 | 1 | 0 | OK |
| all_applicable_control | Read | logs | 1 | 1 | 0 | OK |
| all_dataset | Evaluate | analytics | 1 | 0 | 1 | GAP |
| all_skill_descriptor | Read | policies | 1 | 1 | 0 | OK |
| allowed_skill | Read | policies | 1 | 1 | 0 | OK |
| analytics_facade | Read | analytics | 1 | 1 | 0 | OK |
| and_create_incident | Evaluate | incidents | 1 | 1 | 0 | OK |
| api_key | Read | api_keys | 1 | 1 | 0 | OK |
| api_key_detail | Read | api_keys | 1 | 1 | 0 | OK |
| api_keys_facade | Read | api_keys | 1 | 1 | 0 | OK |
| attention_queue | Read | activity | 1 | 1 | 0 | OK |
| audit_access | Read | logs | 1 | 1 | 0 | OK |
| audit_authorization | Read | logs | 1 | 1 | 0 | OK |
| audit_export | Read | logs | 1 | 1 | 0 | OK |
| audit_identity | Read | logs | 1 | 1 | 0 | OK |
| audit_input_from_evidence | Create | logs | 1 | 1 | 0 | OK |
| audit_integrity | Read | logs | 1 | 1 | 0 | OK |
| billing_invoice | Read | account | 1 | 1 | 0 | OK |
| billing_summary | Read | account | 1 | 1 | 0 | OK |
| blocked_capability | Read | integrations | 1 | 0 | 1 | GAP |
| boot_statu | Read | policies | 1 | 1 | 0 | OK |
| breach_signal | Create | _models | 1 | 1 | 0 | OK |
| budget_issue | Detect | analytics | 1 | 0 | 1 | GAP |
| bulk_signal_feedback | Read | activity | 1 | 1 | 0 | OK |
| certificate | Export | logs | 1 | 1 | 0 | OK |
| connectors_facade | Read | integrations | 1 | 1 | 0 | OK |
| control_mappings_for_incident | Read | logs | 1 | 1 | 0 | OK |
| controls_facade | Read | controls | 1 | 1 | 0 | OK |
| cost | Read | overview | 1 | 1 | 0 | OK |
| cost_analysi | Read | activity | 1 | 1 | 0 | OK |
| cost_by_feature | Read | analytics | 1 | 1 | 0 | OK |
| cost_by_model | Read | analytics | 1 | 1 | 0 | OK |
| cost_cent | Analyze | integrations | 1 | 0 | 1 | GAP |
| cost_impact | Analyze | incidents | 1 | 1 | 0 | OK |
| cost_metric | Read | analytics | 1 | 1 | 0 | OK |
| cost_spend | Read | analytics | 1 | 1 | 0 | OK |
| cost_statistic | Read | analytics | 1 | 1 | 0 | OK |
| current_version | Read | policies | 1 | 1 | 0 | OK |
| cus_enforcement_service | Read | policies | 1 | 1 | 0 | OK |
| cus_telemetry_service | Read | activity | 1 | 1 | 0 | OK |
| customer_incidents_adapter | Read | integrations | 1 | 0 | 1 | GAP |
| customer_keys_adapter | Read | integrations | 1 | 0 | 1 | GAP |
| customer_logs_adapter | Read | integrations | 1 | 0 | 1 | GAP |
| customer_policies_adapter | Read | integrations | 1 | 0 | 1 | GAP |
| dataset_validator | Read | analytics | 1 | 0 | 1 | GAP |
| datasources_facade | Read | integrations | 1 | 1 | 0 | OK |
| decision | Read | overview | 1 | 1 | 0 | OK |
| decisions_count | Read | overview | 1 | 1 | 0 | OK |
| dependency_dag | Evaluate | policies | 1 | 1 | 0 | OK |
| dependency_graph | Read | policies | 1 | 1 | 0 | OK |
| dependency_with_dag_check | Create | policies | 1 | 1 | 0 | OK |
| detection_facade | Read | analytics | 1 | 1 | 0 | OK |
| detection_statu | Read | analytics | 1 | 1 | 0 | OK |
| divergence_report | Create | analytics | 1 | 0 | 1 | GAP |
| emitted | Read | policies | 1 | 1 | 0 | OK |
| error_category | Classify | incidents | 1 | 0 | 1 | GAP |
| ethical_constraint | Read | policies | 1 | 1 | 0 | OK |
| evidence | Create | logs | 1 | 1 | 0 | OK |
| evidence_facade | Read | logs | 1 | 1 | 0 | OK |
| evidence_report | Create | logs | 1 | 1 | 0 | OK |
| execution_fidelity | Evaluate | logs | 1 | 1 | 0 | OK |
| execution_history | Read | policies | 1 | 1 | 0 | OK |
| expired_deferred_lesson | Read | policies | 1 | 1 | 0 | OK |
| governance_at_startup | Evaluate | account | 1 | 1 | 0 | OK |
| governance_facade | Read | policies | 1 | 1 | 0 | OK |
| governance_profile | Read | account | 1 | 1 | 0 | OK |
| governance_state | Read | policies | 1 | 1 | 0 | OK |
| guardrail_detail | Read | integrations | 1 | 0 | 1 | GAP |
| health_preservation | Evaluate | logs | 1 | 1 | 0 | OK |
| health_statu | Read | integrations | 1 | 1 | 0 | OK |
| highlight | Read | overview | 1 | 1 | 0 | OK |
| historical_incident | Read | incidents | 1 | 1 | 0 | OK |
| incident_detail | Read | incidents | 1 | 1 | 0 | OK |
| incident_driver | Read | incidents | 1 | 1 | 0 | OK |
| incident_for_run | Create | incidents | 1 | 1 | 0 | OK |
| incident_learning | Read | incidents | 1 | 1 | 0 | OK |
| incidents_facade | Read | incidents | 1 | 1 | 0 | OK |
| integrations_facade | Read | integrations | 1 | 1 | 0 | OK |
| invitation | Read | account | 1 | 1 | 0 | OK |
| last_step_outcome | Read | policies | 1 | 1 | 0 | OK |
| lesson_from_critical_success | Detect | policies | 1 | 1 | 0 | OK |
| lesson_from_failure | Detect | policies | 1 | 1 | 0 | OK |
| lesson_from_near_threshold | Detect | policies | 1 | 1 | 0 | OK |
| lesson_stat | Read | policies | 1 | 1 | 0 | OK |
| lessons_learned_engine | Read | policies | 1 | 1 | 0 | OK |
| limits_facade | Read | policies | 1 | 1 | 0 | OK |
| limits_simulation_service | Read | policies | 1 | 1 | 0 | OK |
| limits_statu | Read | integrations | 1 | 1 | 0 | OK |
| llm_run_envelope | Read | logs | 1 | 1 | 0 | OK |
| llm_run_export | Read | logs | 1 | 1 | 0 | OK |
| llm_run_governance | Read | logs | 1 | 1 | 0 | OK |
| llm_run_record | Read | logs | 1 | 1 | 0 | OK |
| llm_run_replay | Read | logs | 1 | 1 | 0 | OK |
| llm_run_trace | Read | logs | 1 | 1 | 0 | OK |
| llm_usage | Read | analytics | 1 | 1 | 0 | OK |
| logs_facade | Read | logs | 1 | 1 | 0 | OK |
| near_signal | Create | _models | 1 | 1 | 0 | OK |
| next_offboarding_state | Read | _models | 1 | 1 | 0 | OK |
| next_onboarding_state | Read | _models | 1 | 1 | 0 | OK |
| no_unauthorized_mutation | Evaluate | logs | 1 | 1 | 0 | OK |
| notifications_facade | Read | account | 1 | 1 | 0 | OK |
| override_value | Evaluate | controls | 1 | 0 | 1 | GAP |
| overview_facade | Read | overview | 1 | 1 | 0 | OK |
| pdf_renderer | Read | logs | 1 | 1 | 0 | OK |
| pending | Read | policies | 1 | 1 | 0 | OK |
| policy_audit_certificate | Create | logs | 1 | 1 | 0 | OK |
| policy_conflict | Read | policies | 1 | 1 | 0 | OK |
| policy_constraint | Read | integrations | 1 | 0 | 1 | GAP |
| policy_driver | Read | policies | 1 | 1 | 0 | OK |
| prediction_summary | Read | analytics | 1 | 0 | 1 | GAP |
| project | Read | account | 1 | 1 | 0 | OK |
| project_detail | Read | account | 1 | 1 | 0 | OK |
| recovery_stat | Read | overview | 1 | 1 | 0 | OK |
| recurrence | Analyze | incidents | 1 | 1 | 0 | OK |
| redaction_pattern | Create | logs | 1 | 0 | 1 | GAP |
| rejection_reason | Evaluate | controls | 1 | 0 | 1 | GAP |
| remaining_budget | Read | policies | 1 | 1 | 0 | OK |
| replay | Evaluate | logs | 1 | 1 | 0 | OK |
| replay_certificate | Create | logs | 1 | 1 | 0 | OK |
| report | Create | analytics | 1 | 0 | 1 | GAP |
| reset_period | Evaluate | controls | 1 | 0 | 1 | GAP |
| resolved_incident | Read | incidents | 1 | 1 | 0 | OK |
| risk_signal | Read | activity | 1 | 1 | 0 | OK |
| rollback_availability | Evaluate | logs | 1 | 1 | 0 | OK |
| rollout_statu | Read | logs | 1 | 1 | 0 | OK |
| run | Read | activity | 1 | 1 | 0 | OK |
| run_detail | Read | activity | 1 | 1 | 0 | OK |
| run_evidence | Read | activity | 1 | 1 | 0 | OK |
| run_proof | Read | activity | 1 | 1 | 0 | OK |
| runtime_adapter | Read | integrations | 1 | 1 | 0 | OK |
| scope_compliance | Evaluate | logs | 1 | 1 | 0 | OK |
| sensitive_field | Create | logs | 1 | 0 | 1 | GAP |
| severity | Classify | analytics | 1 | 0 | 1 | GAP |
| signal | Read | activity | 1 | 1 | 0 | OK |
| signal_consistency | Evaluate | logs | 1 | 1 | 0 | OK |
| signal_feedback_statu | Read | activity | 1 | 1 | 0 | OK |
| signal_fingerprint | Analyze | activity | 1 | 1 | 0 | OK |
| signal_fingerprint_from_row | Analyze | activity | 1 | 1 | 0 | OK |
| skill_descriptor | Read | integrations | 1 | 1 | 0 | OK |
| skill_info | Read | policies | 1 | 1 | 0 | OK |
| skills_for_goal | Read | policies | 1 | 1 | 0 | OK |
| state | Read | policies | 1 | 1 | 0 | OK |
| statistic | Read | integrations | 1 | 1 | 0 | OK |
| status_summary | Read | activity | 1 | 1 | 0 | OK |
| step | Create | logs | 1 | 1 | 0 | OK |
| support_contact | Read | account | 1 | 1 | 0 | OK |
| supported_query | Read | integrations | 1 | 1 | 0 | OK |
| supported_query_type | Read | policies | 1 | 1 | 0 | OK |
| sustained_drift | Detect | analytics | 1 | 0 | 1 | GAP |
| system_audit | Read | logs | 1 | 1 | 0 | OK |
| system_event | Read | logs | 1 | 1 | 0 | OK |
| system_record | Read | logs | 1 | 1 | 0 | OK |
| system_replay | Read | logs | 1 | 1 | 0 | OK |
| system_snapshot | Read | logs | 1 | 1 | 0 | OK |
| system_telemetry | Read | logs | 1 | 1 | 0 | OK |
| temporal_storage_stat | Read | policies | 1 | 1 | 0 | OK |
| temporal_utilization | Read | policies | 1 | 1 | 0 | OK |
| tenant_user | Read | account | 1 | 1 | 0 | OK |
| threshold_band | Read | policies | 1 | 1 | 0 | OK |
| threshold_signal | Read | activity | 1 | 1 | 0 | OK |
| threshold_signal_record | Create | controls | 1 | 1 | 0 | OK |
| timing_compliance | Evaluate | logs | 1 | 1 | 0 | OK |
| topological_evaluation_order | Read | policies | 1 | 1 | 0 | OK |
| trace | Create | policies | 1 | 1 | 0 | OK |
| trace_facade | Read | logs | 1 | 1 | 0 | OK |
| transition | Evaluate | _models | 1 | 1 | 0 | OK |
| transition_for_action | Read | _models | 1 | 1 | 0 | OK |
| unlocked_capability | Read | integrations | 1 | 0 | 1 | GAP |
| usage | Read | policies | 1 | 1 | 0 | OK |
| usage_statistic | Read | analytics | 1 | 1 | 0 | OK |
| user_detail | Read | account | 1 | 1 | 0 | OK |
| user_role | Update | account | 1 | 1 | 0 | OK |
| valid_transition | Read | _models | 1 | 1 | 0 | OK |
| variable | Read | policies | 1 | 1 | 0 | OK |
| version_provenance | Read | policies | 1 | 1 | 0 | OK |
| window_second | Evaluate | controls | 1 | 0 | 1 | GAP |
| with_context | Evaluate | policies | 1 | 1 | 0 | OK |
| worker_execution | Read | analytics | 1 | 1 | 0 | OK |
| workers_adapter | Read | integrations | 1 | 0 | 1 | GAP |

---

## Feature Details

### integration

**Domains:** integrations  
**User intents:** Create, Delete, Read, Update  
**Health:** healthy  

**Operations:**
- `IntegrationsFacade.create_integration`
- `IntegrationsFacade.delete_integration`
- `IntegrationsFacade.get_integration`
- `IntegrationsFacade.list_integrations`
- `IntegrationsFacade.update_integration`

### connector

**Domains:** integrations  
**User intents:** Delete, Read, Update  
**Health:** healthy  

**Operations:**
- `ConnectorsFacade.delete_connector`
- `ConnectorsFacade.get_connector`
- `ConnectorsFacade.list_connectors`
- `ConnectorsFacade.update_connector`

### dataset

**Domains:** analytics  
**User intents:** Evaluate, Read  
**Health:** degraded  

**Operations:**
- `DatasetValidator.get_dataset`
- `DatasetValidator.list_datasets`
- `DatasetValidator.validate_dataset`
- `validate_dataset`

### limit

**Domains:** policies  
**User intents:** Evaluate, Read, Update  
**Health:** healthy  

**Operations:**
- `LimitsFacade.check_limit`
- `LimitsFacade.get_limit`
- `LimitsFacade.list_limits`
- `LimitsFacade.update_limit`

### source

**Domains:** integrations  
**User intents:** Delete, Read, Update  
**Health:** healthy  

**Operations:**
- `DataSourcesFacade.delete_source`
- `DataSourcesFacade.get_source`
- `DataSourcesFacade.list_sources`
- `DataSourcesFacade.update_source`

### statu

**Domains:** analytics, controls, policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `AnalyticsFacade.get_status`
- `ControlsFacade.get_status`
- `DefaultSystemHealthLookup.get_status`
- `SystemHealthLookup.get_status`

### anomaly

**Domains:** analytics  
**User intents:** Read, Resolve  
**Health:** healthy  

**Operations:**
- `DetectionFacade.get_anomaly`
- `DetectionFacade.list_anomalies`
- `DetectionFacade.resolve_anomaly`

### chain

**Domains:** logs  
**User intents:** Create, Read  
**Health:** healthy  

**Operations:**
- `EvidenceFacade.create_chain`
- `EvidenceFacade.get_chain`
- `EvidenceFacade.list_chains`

### completed_run

**Domains:** activity, controls  
**User intents:** Evaluate, Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_completed_runs`
- `LLMRunEvaluator.evaluate_completed_run`
- `LLMRunEvaluatorSync.evaluate_completed_run`

### conflict

**Domains:** policies  
**User intents:** Read, Resolve  
**Health:** healthy  

**Operations:**
- `GovernanceFacade.list_conflicts`
- `GovernanceFacade.resolve_conflict`
- `PolicyDriver.resolve_conflict`

### control

**Domains:** controls  
**User intents:** Read, Update  
**Health:** healthy  

**Operations:**
- `ControlsFacade.get_control`
- `ControlsFacade.list_controls`
- `ControlsFacade.update_control`

### export

**Domains:** logs  
**User intents:** Create, Read  
**Health:** healthy  

**Operations:**
- `EvidenceFacade.create_export`
- `EvidenceFacade.get_export`
- `EvidenceFacade.list_exports`

### incident

**Domains:** integrations  
**User intents:** Read, Resolve  
**Health:** degraded  

**Operations:**
- `CustomerIncidentsAdapter.get_incident`
- `CustomerIncidentsAdapter.list_incidents`
- `CustomerIncidentsAdapter.resolve_incident`

### log

**Domains:** integrations  
**User intents:** Export, Read  
**Health:** degraded  

**Operations:**
- `CustomerLogsAdapter.export_logs`
- `CustomerLogsAdapter.get_log`
- `CustomerLogsAdapter.list_logs`

### metric

**Domains:** activity, incidents, policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_metrics`
- `IncidentsFacade.get_metrics`
- `PolicyDriver.get_metrics`

### risk_ceiling

**Domains:** policies  
**User intents:** Read, Update  
**Health:** healthy  

**Operations:**
- `PolicyDriver.get_risk_ceiling`
- `PolicyDriver.get_risk_ceilings`
- `PolicyDriver.update_risk_ceiling`

### rule

**Domains:** incidents  
**User intents:** Create, Delete, Evaluate  
**Health:** degraded  

**Operations:**
- `RecoveryRuleEngine.add_rule`
- `RecoveryRuleEngine.remove_rule`
- `evaluate_rules`

### active_threshold_limit

**Domains:** controls  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `ThresholdDriverProtocol.get_active_threshold_limits`
- `ThresholdDriverSyncProtocol.get_active_threshold_limits`

### all

**Domains:** analytics  
**User intents:** Detect, Evaluate  
**Health:** degraded  

**Operations:**
- `CostAnomalyDetector.detect_all`
- `DatasetValidator.validate_all`

### audit_entry

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_audit_entry`
- `LogsFacade.list_audit_entries`

### capability

**Domains:** integrations, policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `RuntimeAdapter.get_capabilities`
- `get_capabilities`

### channel

**Domains:** account  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `NotificationsFacade.get_channel`
- `NotificationsFacade.list_channels`

### governance_config

**Domains:** account  
**User intents:** Evaluate, Read  
**Health:** healthy  

**Operations:**
- `get_governance_config`
- `validate_governance_config`

### incidents_for_run

**Domains:** incidents  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `IncidentDriver.get_incidents_for_run`
- `IncidentsFacade.get_incidents_for_run`

### intent

**Domains:** policies  
**User intents:** Create, Evaluate  
**Health:** healthy  

**Operations:**
- `IntentEmitter.create_intent`
- `IntentEmitter.validate_intent`

### key

**Domains:** integrations  
**User intents:** Read  
**Health:** degraded  

**Operations:**
- `CustomerKeysAdapter.get_key`
- `CustomerKeysAdapter.list_keys`

### lesson

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LessonsLearnedEngine.get_lesson`
- `LessonsLearnedEngine.list_lessons`

### live_run

**Domains:** activity, controls  
**User intents:** Evaluate, Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_live_runs`
- `LLMRunEvaluator.evaluate_live_run`

### not_raw_key

**Domains:** integrations  
**User intents:** Evaluate  
**Health:** degraded  

**Operations:**
- `CusIntegrationCreate.validate_not_raw_key`
- `CusIntegrationUpdate.validate_not_raw_key`

### notification

**Domains:** account  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `NotificationsFacade.get_notification`
- `NotificationsFacade.list_notifications`

### pattern

**Domains:** activity, incidents  
**User intents:** Detect, Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_patterns`
- `IncidentsFacade.detect_patterns`

### policy_version

**Domains:** policies  
**User intents:** Create, Read  
**Health:** healthy  

**Operations:**
- `PolicyDriver.create_policy_version`
- `PolicyDriver.get_policy_versions`

### preference

**Domains:** account  
**User intents:** Read, Update  
**Health:** healthy  

**Operations:**
- `NotificationsFacade.get_preferences`
- `NotificationsFacade.update_preferences`

### profile

**Domains:** account  
**User intents:** Read, Update  
**Health:** healthy  

**Operations:**
- `AccountsFacade.get_profile`
- `AccountsFacade.update_profile`

### resource_contract

**Domains:** integrations, policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `RuntimeAdapter.get_resource_contract`
- `get_resource_contract`

### safety_rule

**Domains:** policies  
**User intents:** Read, Update  
**Health:** healthy  

**Operations:**
- `PolicyDriver.get_safety_rules`
- `PolicyDriver.update_safety_rule`

### skill

**Domains:** integrations, policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `RuntimeAdapter.list_skills`
- `list_skills`

### support_ticket

**Domains:** account  
**User intents:** Create, Read  
**Health:** healthy  

**Operations:**
- `AccountsFacade.create_support_ticket`
- `AccountsFacade.list_support_tickets`

### temporal_policy

**Domains:** policies  
**User intents:** Create, Read  
**Health:** healthy  

**Operations:**
- `PolicyDriver.create_temporal_policy`
- `PolicyDriver.get_temporal_policies`

### user

**Domains:** account  
**User intents:** Delete, Read  
**Health:** healthy  

**Operations:**
- `AccountsFacade.list_users`
- `AccountsFacade.remove_user`

### violation

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `PolicyDriver.get_violation`
- `PolicyDriver.get_violations`

### absolute_spike

**Domains:** analytics  
**User intents:** Detect  
**Health:** degraded  

**Operations:**
- `CostAnomalyDetector.detect_absolute_spikes`

### accounts_facade

**Domains:** account  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_accounts_facade`

### action_for_transition

**Domains:** _models  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_action_for_transition`

### active_cooldown

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `PolicyDriver.get_active_cooldowns`

### active_incident

**Domains:** incidents  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `IncidentsFacade.list_active_incidents`

### activity_facade

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_activity_facade`

### all_applicable_control

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `SOC2ControlMapper.get_all_applicable_controls`

### all_dataset

**Domains:** analytics  
**User intents:** Evaluate  
**Health:** degraded  

**Operations:**
- `validate_all_datasets`

### all_skill_descriptor

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_all_skill_descriptors`

### allowed_skill

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `query_allowed_skills`

### analytics_facade

**Domains:** analytics  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_analytics_facade`

### and_create_incident

**Domains:** incidents  
**User intents:** Evaluate  
**Health:** healthy  

**Operations:**
- `IncidentDriver.check_and_create_incident`

### api_key

**Domains:** api_keys  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `APIKeysFacade.list_api_keys`

### api_key_detail

**Domains:** api_keys  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `APIKeysFacade.get_api_key_detail`

### api_keys_facade

**Domains:** api_keys  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_api_keys_facade`

### attention_queue

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_attention_queue`

### audit_access

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_audit_access`

### audit_authorization

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_audit_authorization`

### audit_export

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_audit_exports`

### audit_identity

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_audit_identity`

### audit_input_from_evidence

**Domains:** logs  
**User intents:** Create  
**Health:** healthy  

**Operations:**
- `create_audit_input_from_evidence`

### audit_integrity

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_audit_integrity`

### billing_invoice

**Domains:** account  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `AccountsFacade.get_billing_invoices`

### billing_summary

**Domains:** account  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `AccountsFacade.get_billing_summary`

### blocked_capability

**Domains:** integrations  
**User intents:** Read  
**Health:** degraded  

**Operations:**
- `CapabilityGates.get_blocked_capabilities`

### boot_statu

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `GovernanceFacade.get_boot_status`

### breach_signal

**Domains:** _models  
**User intents:** Create  
**Health:** healthy  

**Operations:**
- `ThresholdSignal.create_breach_signal`

### budget_issue

**Domains:** analytics  
**User intents:** Detect  
**Health:** degraded  

**Operations:**
- `CostAnomalyDetector.detect_budget_issues`

### bulk_signal_feedback

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `SignalFeedbackService.get_bulk_signal_feedback`

### certificate

**Domains:** logs  
**User intents:** Export  
**Health:** healthy  

**Operations:**
- `CertificateService.export_certificate`

### connectors_facade

**Domains:** integrations  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_connectors_facade`

### control_mappings_for_incident

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_control_mappings_for_incident`

### controls_facade

**Domains:** controls  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_controls_facade`

### cost

**Domains:** overview  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `OverviewFacade.get_costs`

### cost_analysi

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_cost_analysis`

### cost_by_feature

**Domains:** analytics  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `SignalAdapter.fetch_cost_by_feature`

### cost_by_model

**Domains:** analytics  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `SignalAdapter.fetch_cost_by_model`

### cost_cent

**Domains:** integrations  
**User intents:** Analyze  
**Health:** degraded  

**Operations:**
- `WorkersAdapter.calculate_cost_cents`

### cost_impact

**Domains:** incidents  
**User intents:** Analyze  
**Health:** healthy  

**Operations:**
- `IncidentsFacade.analyze_cost_impact`

### cost_metric

**Domains:** analytics  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `SignalAdapter.fetch_cost_metrics`

### cost_spend

**Domains:** analytics  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `SignalAdapter.fetch_cost_spend`

### cost_statistic

**Domains:** analytics  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `AnalyticsFacade.get_cost_statistics`

### current_version

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `PolicyDriver.get_current_version`

### cus_enforcement_service

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_cus_enforcement_service`

### cus_telemetry_service

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_cus_telemetry_service`

### customer_incidents_adapter

**Domains:** integrations  
**User intents:** Read  
**Health:** degraded  

**Operations:**
- `get_customer_incidents_adapter`

### customer_keys_adapter

**Domains:** integrations  
**User intents:** Read  
**Health:** degraded  

**Operations:**
- `get_customer_keys_adapter`

### customer_logs_adapter

**Domains:** integrations  
**User intents:** Read  
**Health:** degraded  

**Operations:**
- `get_customer_logs_adapter`

### customer_policies_adapter

**Domains:** integrations  
**User intents:** Read  
**Health:** degraded  

**Operations:**
- `get_customer_policies_adapter`

### dataset_validator

**Domains:** analytics  
**User intents:** Read  
**Health:** degraded  

**Operations:**
- `get_dataset_validator`

### datasources_facade

**Domains:** integrations  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_datasources_facade`

### decision

**Domains:** overview  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `OverviewFacade.get_decisions`

### decisions_count

**Domains:** overview  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `OverviewFacade.get_decisions_count`

### dependency_dag

**Domains:** policies  
**User intents:** Evaluate  
**Health:** healthy  

**Operations:**
- `PolicyDriver.validate_dependency_dag`

### dependency_graph

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `PolicyDriver.get_dependency_graph`

### dependency_with_dag_check

**Domains:** policies  
**User intents:** Create  
**Health:** healthy  

**Operations:**
- `PolicyDriver.add_dependency_with_dag_check`

### detection_facade

**Domains:** analytics  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_detection_facade`

### detection_statu

**Domains:** analytics  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `DetectionFacade.get_detection_status`

### divergence_report

**Domains:** analytics  
**User intents:** Create  
**Health:** degraded  

**Operations:**
- `generate_divergence_report`

### emitted

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `IntentEmitter.get_emitted`

### error_category

**Domains:** incidents  
**User intents:** Classify  
**Health:** degraded  

**Operations:**
- `classify_error_category`

### ethical_constraint

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `PolicyDriver.get_ethical_constraints`

### evidence

**Domains:** logs  
**User intents:** Create  
**Health:** healthy  

**Operations:**
- `EvidenceFacade.add_evidence`

### evidence_facade

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_evidence_facade`

### evidence_report

**Domains:** logs  
**User intents:** Create  
**Health:** healthy  

**Operations:**
- `generate_evidence_report`

### execution_fidelity

**Domains:** logs  
**User intents:** Evaluate  
**Health:** healthy  

**Operations:**
- `AuditChecks.check_execution_fidelity`

### execution_history

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `query_execution_history`

### expired_deferred_lesson

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LessonsLearnedEngine.get_expired_deferred_lessons`

### governance_at_startup

**Domains:** account  
**User intents:** Evaluate  
**Health:** healthy  

**Operations:**
- `validate_governance_at_startup`

### governance_facade

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_governance_facade`

### governance_profile

**Domains:** account  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_governance_profile`

### governance_state

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `GovernanceFacade.get_governance_state`

### guardrail_detail

**Domains:** integrations  
**User intents:** Read  
**Health:** degraded  

**Operations:**
- `CustomerPoliciesAdapter.get_guardrail_detail`

### health_preservation

**Domains:** logs  
**User intents:** Evaluate  
**Health:** healthy  

**Operations:**
- `AuditChecks.check_health_preservation`

### health_statu

**Domains:** integrations  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `IntegrationsFacade.get_health_status`

### highlight

**Domains:** overview  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `OverviewFacade.get_highlights`

### historical_incident

**Domains:** incidents  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `IncidentsFacade.list_historical_incidents`

### incident_detail

**Domains:** incidents  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `IncidentsFacade.get_incident_detail`

### incident_driver

**Domains:** incidents  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_incident_driver`

### incident_for_run

**Domains:** incidents  
**User intents:** Create  
**Health:** healthy  

**Operations:**
- `IncidentDriver.create_incident_for_run`

### incident_learning

**Domains:** incidents  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `IncidentsFacade.get_incident_learnings`

### incidents_facade

**Domains:** incidents  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_incidents_facade`

### integrations_facade

**Domains:** integrations  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_integrations_facade`

### invitation

**Domains:** account  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `AccountsFacade.list_invitations`

### last_step_outcome

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `query_last_step_outcome`

### lesson_from_critical_success

**Domains:** policies  
**User intents:** Detect  
**Health:** healthy  

**Operations:**
- `LessonsLearnedEngine.detect_lesson_from_critical_success`

### lesson_from_failure

**Domains:** policies  
**User intents:** Detect  
**Health:** healthy  

**Operations:**
- `LessonsLearnedEngine.detect_lesson_from_failure`

### lesson_from_near_threshold

**Domains:** policies  
**User intents:** Detect  
**Health:** healthy  

**Operations:**
- `LessonsLearnedEngine.detect_lesson_from_near_threshold`

### lesson_stat

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LessonsLearnedEngine.get_lesson_stats`

### lessons_learned_engine

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_lessons_learned_engine`

### limits_facade

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_limits_facade`

### limits_simulation_service

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_limits_simulation_service`

### limits_statu

**Domains:** integrations  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `IntegrationsFacade.get_limits_status`

### llm_run_envelope

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_llm_run_envelope`

### llm_run_export

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_llm_run_export`

### llm_run_governance

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_llm_run_governance`

### llm_run_record

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.list_llm_run_records`

### llm_run_replay

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_llm_run_replay`

### llm_run_trace

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_llm_run_trace`

### llm_usage

**Domains:** analytics  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `SignalAdapter.fetch_llm_usage`

### logs_facade

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_logs_facade`

### near_signal

**Domains:** _models  
**User intents:** Create  
**Health:** healthy  

**Operations:**
- `ThresholdSignal.create_near_signal`

### next_offboarding_state

**Domains:** _models  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_next_offboarding_state`

### next_onboarding_state

**Domains:** _models  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_next_onboarding_state`

### no_unauthorized_mutation

**Domains:** logs  
**User intents:** Evaluate  
**Health:** healthy  

**Operations:**
- `AuditChecks.check_no_unauthorized_mutations`

### notifications_facade

**Domains:** account  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_notifications_facade`

### override_value

**Domains:** controls  
**User intents:** Evaluate  
**Health:** degraded  

**Operations:**
- `LimitOverrideRequest.validate_override_value`

### overview_facade

**Domains:** overview  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_overview_facade`

### pdf_renderer

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_pdf_renderer`

### pending

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `IntentEmitter.get_pending`

### policy_audit_certificate

**Domains:** logs  
**User intents:** Create  
**Health:** healthy  

**Operations:**
- `CertificateService.create_policy_audit_certificate`

### policy_conflict

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `PolicyDriver.get_policy_conflicts`

### policy_constraint

**Domains:** integrations  
**User intents:** Read  
**Health:** degraded  

**Operations:**
- `CustomerPoliciesAdapter.get_policy_constraints`

### policy_driver

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_policy_driver`

### prediction_summary

**Domains:** analytics  
**User intents:** Read  
**Health:** degraded  

**Operations:**
- `get_prediction_summary`

### project

**Domains:** account  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `AccountsFacade.list_projects`

### project_detail

**Domains:** account  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `AccountsFacade.get_project_detail`

### recovery_stat

**Domains:** overview  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `OverviewFacade.get_recovery_stats`

### recurrence

**Domains:** incidents  
**User intents:** Analyze  
**Health:** healthy  

**Operations:**
- `IncidentsFacade.analyze_recurrence`

### redaction_pattern

**Domains:** logs  
**User intents:** Create  
**Health:** degraded  

**Operations:**
- `add_redaction_pattern`

### rejection_reason

**Domains:** controls  
**User intents:** Evaluate  
**Health:** degraded  

**Operations:**
- `OverrideApprovalRequest.validate_rejection_reason`

### remaining_budget

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `query_remaining_budget`

### replay

**Domains:** logs  
**User intents:** Evaluate  
**Health:** healthy  

**Operations:**
- `ReplayValidator.validate_replay`

### replay_certificate

**Domains:** logs  
**User intents:** Create  
**Health:** healthy  

**Operations:**
- `CertificateService.create_replay_certificate`

### report

**Domains:** analytics  
**User intents:** Create  
**Health:** degraded  

**Operations:**
- `DivergenceAnalyzer.generate_report`

### reset_period

**Domains:** controls  
**User intents:** Evaluate  
**Health:** degraded  

**Operations:**
- `CreatePolicyLimitRequest.validate_reset_period`

### resolved_incident

**Domains:** incidents  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `IncidentsFacade.list_resolved_incidents`

### risk_signal

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_risk_signals`

### rollback_availability

**Domains:** logs  
**User intents:** Evaluate  
**Health:** healthy  

**Operations:**
- `AuditChecks.check_rollback_availability`

### rollout_statu

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `RolloutGate.get_rollout_status`

### run

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_runs`

### run_detail

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_run_detail`

### run_evidence

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_run_evidence`

### run_proof

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_run_proof`

### runtime_adapter

**Domains:** integrations  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_runtime_adapter`

### scope_compliance

**Domains:** logs  
**User intents:** Evaluate  
**Health:** healthy  

**Operations:**
- `AuditChecks.check_scope_compliance`

### sensitive_field

**Domains:** logs  
**User intents:** Create  
**Health:** degraded  

**Operations:**
- `add_sensitive_field`

### severity

**Domains:** analytics  
**User intents:** Classify  
**Health:** degraded  

**Operations:**
- `classify_severity`

### signal

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_signals`

### signal_consistency

**Domains:** logs  
**User intents:** Evaluate  
**Health:** healthy  

**Operations:**
- `AuditChecks.check_signal_consistency`

### signal_feedback_statu

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `SignalFeedbackService.get_signal_feedback_status`

### signal_fingerprint

**Domains:** activity  
**User intents:** Analyze  
**Health:** healthy  

**Operations:**
- `compute_signal_fingerprint`

### signal_fingerprint_from_row

**Domains:** activity  
**User intents:** Analyze  
**Health:** healthy  

**Operations:**
- `compute_signal_fingerprint_from_row`

### skill_descriptor

**Domains:** integrations  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `RuntimeAdapter.get_skill_descriptors`

### skill_info

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_skill_info`

### skills_for_goal

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `query_skills_for_goal`

### state

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `PolicyDriver.get_state`

### statistic

**Domains:** integrations  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `DataSourcesFacade.get_statistics`

### status_summary

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_status_summary`

### step

**Domains:** logs  
**User intents:** Create  
**Health:** healthy  

**Operations:**
- `TraceFacade.add_step`

### support_contact

**Domains:** account  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `AccountsFacade.get_support_contact`

### supported_query

**Domains:** integrations  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `RuntimeAdapter.get_supported_queries`

### supported_query_type

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_supported_query_types`

### sustained_drift

**Domains:** analytics  
**User intents:** Detect  
**Health:** degraded  

**Operations:**
- `CostAnomalyDetector.detect_sustained_drift`

### system_audit

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_system_audit`

### system_event

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_system_events`

### system_record

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.list_system_records`

### system_replay

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_system_replay`

### system_snapshot

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_system_snapshot`

### system_telemetry

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LogsFacade.get_system_telemetry`

### temporal_storage_stat

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `PolicyDriver.get_temporal_storage_stats`

### temporal_utilization

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `PolicyDriver.get_temporal_utilization`

### tenant_user

**Domains:** account  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `AccountsFacade.list_tenant_users`

### threshold_band

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_threshold_band`

### threshold_signal

**Domains:** activity  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `ActivityFacade.get_threshold_signals`

### threshold_signal_record

**Domains:** controls  
**User intents:** Create  
**Health:** healthy  

**Operations:**
- `create_threshold_signal_record`

### timing_compliance

**Domains:** logs  
**User intents:** Evaluate  
**Health:** healthy  

**Operations:**
- `AuditChecks.check_timing_compliance`

### topological_evaluation_order

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `PolicyDriver.get_topological_evaluation_order`

### trace

**Domains:** policies  
**User intents:** Create  
**Health:** healthy  

**Operations:**
- `ExecutionContext.add_trace`

### trace_facade

**Domains:** logs  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_trace_facade`

### transition

**Domains:** _models  
**User intents:** Evaluate  
**Health:** healthy  

**Operations:**
- `validate_transition`

### transition_for_action

**Domains:** _models  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_transition_for_action`

### unlocked_capability

**Domains:** integrations  
**User intents:** Read  
**Health:** degraded  

**Operations:**
- `CapabilityGates.get_unlocked_capabilities`

### usage

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `LimitsFacade.get_usage`

### usage_statistic

**Domains:** analytics  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `AnalyticsFacade.get_usage_statistics`

### user_detail

**Domains:** account  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `AccountsFacade.get_user_detail`

### user_role

**Domains:** account  
**User intents:** Update  
**Health:** healthy  

**Operations:**
- `AccountsFacade.update_user_role`

### valid_transition

**Domains:** _models  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `get_valid_transitions`

### variable

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `ExecutionContext.get_variable`

### version_provenance

**Domains:** policies  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `PolicyDriver.get_version_provenance`

### window_second

**Domains:** controls  
**User intents:** Evaluate  
**Health:** degraded  

**Operations:**
- `CreatePolicyLimitRequest.validate_window_seconds`

### with_context

**Domains:** policies  
**User intents:** Evaluate  
**Health:** healthy  

**Operations:**
- `PolicyDriver.evaluate_with_context`

### worker_execution

**Domains:** analytics  
**User intents:** Read  
**Health:** healthy  

**Operations:**
- `SignalAdapter.fetch_worker_execution`

### workers_adapter

**Domains:** integrations  
**User intents:** Read  
**Health:** degraded  

**Operations:**
- `get_workers_adapter`

---

## Wiring Health Summary

### Features with L2→L5 Gaps

- **dataset** (4 gaps across analytics)
- **incident** (3 gaps across integrations)
- **log** (3 gaps across integrations)
- **rule** (3 gaps across incidents)
- **all** (2 gaps across analytics)
- **key** (2 gaps across integrations)
- **not_raw_key** (2 gaps across integrations)
- **absolute_spike** (1 gaps across analytics)
- **all_dataset** (1 gaps across analytics)
- **blocked_capability** (1 gaps across integrations)
- **budget_issue** (1 gaps across analytics)
- **cost_cent** (1 gaps across integrations)
- **customer_incidents_adapter** (1 gaps across integrations)
- **customer_keys_adapter** (1 gaps across integrations)
- **customer_logs_adapter** (1 gaps across integrations)
- **customer_policies_adapter** (1 gaps across integrations)
- **dataset_validator** (1 gaps across analytics)
- **divergence_report** (1 gaps across analytics)
- **error_category** (1 gaps across incidents)
- **guardrail_detail** (1 gaps across integrations)
- **override_value** (1 gaps across controls)
- **policy_constraint** (1 gaps across integrations)
- **prediction_summary** (1 gaps across analytics)
- **redaction_pattern** (1 gaps across logs)
- **rejection_reason** (1 gaps across controls)
- **report** (1 gaps across analytics)
- **reset_period** (1 gaps across controls)
- **sensitive_field** (1 gaps across logs)
- **severity** (1 gaps across analytics)
- **sustained_drift** (1 gaps across analytics)
- **unlocked_capability** (1 gaps across integrations)
- **window_second** (1 gaps across controls)
- **workers_adapter** (1 gaps across integrations)
