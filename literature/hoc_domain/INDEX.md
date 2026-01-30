# HOC Domain Literature — Master Index

**Total files:** 292  
**Domains:** 12  
**Generator:** `scripts/ops/hoc_domain_literature_generator.py`

---

## Navigation

| Domain | L5 | L6 | L7 | Total |
|--------|----|----|----|-------|
| [_models (L7)](_models/_summary.md) | 0 | 0 | 29 | 29 |
| [account](account/_summary.md) | 10 | 3 | 0 | 13 |
| [activity](activity/_summary.md) | 8 | 3 | 0 | 11 |
| [analytics](analytics/_summary.md) | 21 | 8 | 0 | 29 |
| [api_keys](api_keys/_summary.md) | 2 | 2 | 0 | 4 |
| [apis](apis/_summary.md) | 0 | 1 | 0 | 1 |
| [controls](controls/_summary.md) | 14 | 8 | 0 | 22 |
| [incidents](incidents/_summary.md) | 17 | 11 | 0 | 28 |
| [integrations](integrations/_summary.md) | 44 | 3 | 0 | 47 |
| [logs](logs/_summary.md) | 18 | 12 | 0 | 30 |
| [overview](overview/_summary.md) | 1 | 1 | 0 | 2 |
| [policies](policies/_summary.md) | 62 | 14 | 0 | 76 |

## Models (L7)

[Domain Summary](_models/_summary.md)

### models

- [alert_config.py](_models/models/hoc_models_alert_config.md) — Configure alerting behavior for near-threshold events
- [audit_ledger.py](_models/models/hoc_models_audit_ledger.md) — Audit Ledger model for Logs domain (PIN-413)
- [contract.py](_models/models/hoc_models_contract.md) — System Contract database models
- [costsim_cb.py](_models/models/hoc_models_costsim_cb.md) — CostSim circuit breaker models
- [cus_models.py](_models/models/hoc_models_cus_models.md) — Customer integration data models
- [execution_envelope.py](_models/models/hoc_models_execution_envelope.md) — Execution envelope models for implicit authority hardening
- [export_bundles.py](_models/models/hoc_models_export_bundles.md) — Structured export bundle models for SOC2, evidence, and executive debr
- [external_response.py](_models/models/hoc_models_external_response.md) — External response data models (DB tables)
- [feedback.py](_models/models/hoc_models_feedback.md) — Feedback data models
- [governance.py](_models/models/hoc_models_governance.md) — Governance signal data models (DB tables)
- [governance_job.py](_models/models/hoc_models_governance_job.md) — Governance Job database models
- [killswitch.py](_models/models/hoc_models_killswitch.md) — Killswitch data models
- [knowledge_lifecycle.py](_models/models/hoc_models_knowledge_lifecycle.md) — GAP-089 Knowledge Plane Lifecycle State Machine
- [lessons_learned.py](_models/models/hoc_models_lessons_learned.md) — Lessons learned data model for policy domain intelligence
- [log_exports.py](_models/models/hoc_models_log_exports.md) — Log Exports model for LOGS Domain V2 (O5 evidence bundles)
- [logs_records.py](_models/models/hoc_models_logs_records.md) — LLM Run Records and System Records models for Logs domain (PIN-413)
- [m10_recovery.py](_models/models/hoc_models_m10_recovery.md) — M10 recovery data models
- [monitor_config.py](_models/models/hoc_models_monitor_config.md) — Define what signals to monitor during run execution
- [override_authority.py](_models/models/hoc_models_override_authority.md) — Define emergency override rules for policies
- [policy.py](_models/models/hoc_models_policy.md) — Policy data models (DB tables)
- [policy_control_plane.py](_models/models/hoc_models_policy_control_plane.md) — Policy control-plane models (PIN-412)
- [policy_precedence.py](_models/models/hoc_models_policy_precedence.md) — Define policy precedence and conflict resolution strategies
- [policy_scope.py](_models/models/hoc_models_policy_scope.md) — Define policy scope selectors for targeting runs by agent, API key, or
- [policy_snapshot.py](_models/models/hoc_models_policy_snapshot.md) — Immutable policy snapshot for run-time governance
- [prediction.py](_models/models/hoc_models_prediction.md) — Prediction data models
- [retrieval_evidence.py](_models/models/hoc_models_retrieval_evidence.md) — Audit log model for mediated data access
- [run_lifecycle.py](_models/models/hoc_models_run_lifecycle.md) — Run lifecycle enums and models for governance
- [tenant.py](_models/models/hoc_models_tenant.md) — Tenant data models
- [threshold_signal.py](_models/models/hoc_models_threshold_signal.md) — Record near-threshold and breach events for alerting and audit

## Account

[Domain Summary](account/_summary.md)

### L5_engines

- [accounts_facade.py](account/L5_engines/hoc_cus_account_L5_engines_accounts_facade.md) — Accounts domain facade - unified entry point for account management
- [billing_provider.py](account/L5_engines/hoc_cus_account_L5_engines_billing_provider.md) — Phase-6 BillingProvider protocol and MockBillingProvider
- [email_verification.py](account/L5_engines/hoc_cus_account_L5_engines_email_verification.md) — Email OTP verification engine for customer onboarding
- [identity_resolver.py](account/L5_engines/hoc_cus_account_L5_engines_identity_resolver.md) — Identity resolution from various providers
- [notifications_facade.py](account/L5_engines/hoc_cus_account_L5_engines_notifications_facade.md) — Notifications Facade - Centralized access to notification operations
- [profile.py](account/L5_engines/hoc_cus_account_L5_engines_profile.md) — Governance Profile configuration and validation
- [tenant_engine.py](account/L5_engines/hoc_cus_account_L5_engines_tenant_engine.md) — Tenant domain engine - business logic for tenant operations
- [user_write_engine.py](account/L5_engines/hoc_cus_account_L5_engines_user_write_engine.md) — User write operations (L5 engine over L6 driver)

### L5_support

- [crm_validator_engine.py](account/L5_support/hoc_cus_account_L5_support_crm_validator_engine.md) — Issue Validator - pure analysis, advisory verdicts (pure business logi
- [validator_engine.py](account/L5_support/hoc_cus_account_L5_support_validator_engine.md) — Issue Validator engine - pure analysis, advisory verdicts

### L6_drivers

- [accounts_facade_driver.py](account/L6_drivers/hoc_cus_account_L6_drivers_accounts_facade_driver.md) — Accounts domain facade driver - pure data access — L6 DOES NOT COMMIT
- [tenant_driver.py](account/L6_drivers/hoc_cus_account_L6_drivers_tenant_driver.md) — Tenant domain driver - pure data access for tenant operations — L6 DOE
- [user_write_driver.py](account/L6_drivers/hoc_cus_account_L6_drivers_user_write_driver.md) — Data access for user write operations

## Activity

[Domain Summary](activity/_summary.md)

### L5_engines

- [activity_enums.py](activity/L5_engines/hoc_cus_activity_L5_engines_activity_enums.md) — Canonical enums for activity domain - owned by engines
- [activity_facade.py](activity/L5_engines/hoc_cus_activity_L5_engines_activity_facade.md) — Activity Facade - Centralized access to activity domain operations
- [attention_ranking_engine.py](activity/L5_engines/hoc_cus_activity_L5_engines_attention_ranking_engine.md) — Attention ranking engine for activity signals
- [cost_analysis_engine.py](activity/L5_engines/hoc_cus_activity_L5_engines_cost_analysis_engine.md) — Cost analysis engine for activity signals
- [cus_telemetry_service.py](activity/L5_engines/hoc_cus_activity_L5_engines_cus_telemetry_service.md) — Customer telemetry service - LLM usage ingestion and reporting
- [pattern_detection_engine.py](activity/L5_engines/hoc_cus_activity_L5_engines_pattern_detection_engine.md) — Pattern detection engine for activity signals
- [signal_feedback_engine.py](activity/L5_engines/hoc_cus_activity_L5_engines_signal_feedback_engine.md) — Signal feedback engine for acknowledging/suppressing signals
- [signal_identity.py](activity/L5_engines/hoc_cus_activity_L5_engines_signal_identity.md) — Signal identity computation for deduplication

### L6_drivers

- [activity_read_driver.py](activity/L6_drivers/hoc_cus_activity_L6_drivers_activity_read_driver.md) — Activity read data access operations
- [orphan_recovery.py](activity/L6_drivers/hoc_cus_activity_L6_drivers_orphan_recovery.md) — Orphan detection logic, PB-S2 truth guarantee
- [run_signal_service.py](activity/L6_drivers/hoc_cus_activity_L6_drivers_run_signal_service.md) — RunSignalService - updates run risk levels based on threshold signals

## Analytics

[Domain Summary](analytics/_summary.md)

### L5_engines

- [ai_console_panel_engine.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_ai_console_panel_engine.md) — Main orchestration engine for panel evaluation
- [analytics_facade.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_analytics_facade.md) — Analytics Facade - Centralized access to analytics domain operations
- [canary.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_canary.md) — CostSim V2 canary runner (daily validation, drift detection)
- [config.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_config.md) — CostSim V2 configuration and feature flags
- [coordinator.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_coordinator.md) — Optimization envelope coordination
- [cost_anomaly_detector.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_cost_anomaly_detector.md) — Cost anomaly detection business logic (System Truth)
- [cost_model_engine.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_cost_model_engine.md) — Cost modeling and risk estimation domain authority (System Truth)
- [cost_snapshots.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_cost_snapshots.md) — Cost snapshot computation with embedded DB operations
- [cost_write_engine.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_cost_write_engine.md) — Cost write operations (L5 facade over L6 driver)
- [costsim_models.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_costsim_models.md) — CostSim V2 data models (simulation status, results)
- [datasets.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_datasets.md) — CostSim V2 reference datasets (validation samples)
- [detection_facade.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_detection_facade.md) — Detection Facade - Centralized access to anomaly detection operations
- [divergence.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_divergence.md) — CostSim V2 divergence reporting (delta metrics, KL divergence)
- [envelope.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_envelope.md) — Base optimization envelope definition
- [metrics.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_metrics.md) — CostSim V2 Prometheus metrics (drift detection, circuit breaker)
- [pattern_detection.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_pattern_detection.md) — Pattern detection (PB-S3) - observe → feedback → no mutation (System T
- [prediction.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_prediction.md) — Prediction generation and orchestration (advisory only)
- [provenance.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_provenance.md) — CostSim V2 provenance logging (full audit trail)
- [s1_retry_backoff.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_s1_retry_backoff.md) — S1 Retry backoff envelope implementation
- [sandbox.py](analytics/L5_engines/hoc_cus_analytics_L5_engines_sandbox.md) — CostSim V2 sandbox routing (V1/V2 comparison, shadow mode)

### L5_schemas

- [cost_snapshot_schemas.py](analytics/L5_schemas/hoc_cus_analytics_L5_schemas_cost_snapshot_schemas.md) — Cost snapshot dataclasses and enums

### L6_drivers

- [analytics_read_driver.py](analytics/L6_drivers/hoc_cus_analytics_L6_drivers_analytics_read_driver.md) — Analytics read data access operations
- [audit_persistence.py](analytics/L6_drivers/hoc_cus_analytics_L6_drivers_audit_persistence.md) — Optimization audit trail persistence
- [cost_anomaly_driver.py](analytics/L6_drivers/hoc_cus_analytics_L6_drivers_cost_anomaly_driver.md) — Data access for cost anomaly detection operations
- [cost_write_driver.py](analytics/L6_drivers/hoc_cus_analytics_L6_drivers_cost_write_driver.md) — Data access for cost write operations
- [leader.py](analytics/L6_drivers/hoc_cus_analytics_L6_drivers_leader.md) — CostSim Leader Election via PostgreSQL Advisory Locks
- [pattern_detection_driver.py](analytics/L6_drivers/hoc_cus_analytics_L6_drivers_pattern_detection_driver.md) — Pattern detection data access operations
- [prediction_driver.py](analytics/L6_drivers/hoc_cus_analytics_L6_drivers_prediction_driver.md) — Data access for prediction operations
- [provenance_async.py](analytics/L6_drivers/hoc_cus_analytics_L6_drivers_provenance_async.md) — CostSim V2 Provenance Logger - Async Implementation

## Api_Keys

[Domain Summary](api_keys/_summary.md)

### L5_engines

- [api_keys_facade.py](api_keys/L5_engines/hoc_cus_api_keys_L5_engines_api_keys_facade.md) — API Keys domain engine - unified entry point for API key operations
- [keys_engine.py](api_keys/L5_engines/hoc_cus_api_keys_L5_engines_keys_engine.md) — API Keys domain engine - business logic for key operations

### L6_drivers

- [api_keys_facade_driver.py](api_keys/L6_drivers/hoc_cus_api_keys_L6_drivers_api_keys_facade_driver.md) — API Keys Facade Driver - Pure data access for API key queries
- [keys_driver.py](api_keys/L6_drivers/hoc_cus_api_keys_L6_drivers_keys_driver.md) — Keys Driver - Pure data access for API key engine operations

## Apis

[Domain Summary](apis/_summary.md)

### L6_drivers

- [keys_driver.py](apis/L6_drivers/hoc_cus_apis_L6_drivers_keys_driver.md) — API Keys data access operations

## Controls

[Domain Summary](controls/_summary.md)

### L5_controls

- [customer_killswitch_read_engine.py](controls/L5_controls/hoc_cus_controls_L5_controls_customer_killswitch_read_engine.md) — Customer killswitch read operations (L5 engine over L6 driver)
- [killswitch_read_driver.py](controls/L5_controls/hoc_cus_controls_L5_controls_killswitch_read_driver.md) — Data access for killswitch read operations

### L5_engines

- [alert_fatigue.py](controls/L5_engines/hoc_cus_controls_L5_engines_alert_fatigue.md) — Alert deduplication and fatigue control (Redis-backed)
- [budget_enforcement_engine.py](controls/L5_engines/hoc_cus_controls_L5_engines_budget_enforcement_engine.md) — Budget enforcement decision-making (domain logic)
- [cb_sync_wrapper.py](controls/L5_engines/hoc_cus_controls_L5_engines_cb_sync_wrapper.md) — Circuit breaker sync wrapper (thread-safe async bridge)
- [controls_facade.py](controls/L5_engines/hoc_cus_controls_L5_engines_controls_facade.md) — Controls Facade - Centralized access to control operations
- [cost_safety_rails.py](controls/L5_engines/hoc_cus_controls_L5_engines_cost_safety_rails.md) — Cost safety rail enforcement (business rules)
- [decisions.py](controls/L5_engines/hoc_cus_controls_L5_engines_decisions.md) — Phase-7 Decision enum and result types
- [killswitch.py](controls/L5_engines/hoc_cus_controls_L5_engines_killswitch.md) — Optimization killswitch for emergency stops (pure state logic)
- [s2_cost_smoothing.py](controls/L5_engines/hoc_cus_controls_L5_engines_s2_cost_smoothing.md) — S2 Cost smoothing envelope implementation
- [threshold_engine.py](controls/L5_engines/hoc_cus_controls_L5_engines_threshold_engine.md) — Threshold resolution and evaluation logic (decision engine)

### L5_schemas

- [overrides.py](controls/L5_schemas/hoc_cus_controls_L5_schemas_overrides.md) — Limit override request/response schemas
- [policy_limits.py](controls/L5_schemas/hoc_cus_controls_L5_schemas_policy_limits.md) — Policy limits request/response schemas
- [simulation.py](controls/L5_schemas/hoc_cus_controls_L5_schemas_simulation.md) — Limit simulation request/response schemas

### L6_drivers

- [budget_enforcement_driver.py](controls/L6_drivers/hoc_cus_controls_L6_drivers_budget_enforcement_driver.md) — Budget enforcement data access operations
- [circuit_breaker.py](controls/L6_drivers/hoc_cus_controls_L6_drivers_circuit_breaker.md) — DB-backed circuit breaker state tracking (sync) — L6 DOES NOT COMMIT
- [circuit_breaker_async.py](controls/L6_drivers/hoc_cus_controls_L6_drivers_circuit_breaker_async.md) — Async DB-backed circuit breaker state tracking
- [limits_read_driver.py](controls/L6_drivers/hoc_cus_controls_L6_drivers_limits_read_driver.md) — Read operations for limits
- [override_driver.py](controls/L6_drivers/hoc_cus_controls_L6_drivers_override_driver.md) — Limit override driver (PIN-LIM-05) - DB boundary crossing
- [policy_limits_driver.py](controls/L6_drivers/hoc_cus_controls_L6_drivers_policy_limits_driver.md) — Data access for policy limits CRUD operations
- [scoped_execution.py](controls/L6_drivers/hoc_cus_controls_L6_drivers_scoped_execution.md) — Pre-execution gate, scope enforcement
- [threshold_driver.py](controls/L6_drivers/hoc_cus_controls_L6_drivers_threshold_driver.md) — Database operations for threshold limits

## Incidents

[Domain Summary](incidents/_summary.md)

### L5_engines

- [anomaly_bridge.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_anomaly_bridge.md) — Anomaly-to-Incident bridge (incidents-owned, not analytics)
- [hallucination_detector.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_hallucination_detector.md) — Detect potential hallucinations in LLM outputs (non-blocking)
- [incident_driver.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_incident_driver.md) — Incident Domain Engine - Internal orchestration for incident operation
- [incident_engine.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_incident_engine.md) — Incident creation decision-making (domain logic)
- [incident_pattern_engine.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_incident_pattern_engine.md) — Detect structural patterns across incidents
- [incident_read_engine.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_incident_read_engine.md) — Incident domain read operations (L5 facade over L6 driver)
- [incident_severity_engine.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_incident_severity_engine.md) — Severity calculation and escalation decisions for incidents
- [incident_write_engine.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_incident_write_engine.md) — Incident domain write operations with audit (L5 facade over L6 driver)
- [incidents_facade.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_incidents_facade.md) — Incidents domain facade - unified entry point for incident management 
- [incidents_types.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_incidents_types.md) — Shared type aliases for incidents domain engines
- [llm_failure_engine.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_llm_failure_engine.md) — S4 failure truth model, fact persistence
- [policy_violation_engine.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_policy_violation_engine.md) — S3 violation truth model, fact persistence, evidence linking
- [postmortem_engine.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_postmortem_engine.md) — Extract learnings and post-mortem insights from resolved incidents
- [prevention_engine.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_prevention_engine.md) — Prevention-based policy validation
- [recovery_rule_engine.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_recovery_rule_engine.md) — Rule-based evaluation engine for recovery suggestions
- [recurrence_analysis_engine.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_recurrence_analysis_engine.md) — Analyze recurring incident patterns (business logic)
- [semantic_failures.py](incidents/L5_engines/hoc_cus_incidents_L5_engines_semantic_failures.md) — Semantic failure taxonomy and fix guidance for incidents domain

### L6_drivers

- [export_bundle_driver.py](incidents/L6_drivers/hoc_cus_incidents_L6_drivers_export_bundle_driver.md) — Generate structured export bundles from incidents and traces
- [incident_aggregator.py](incidents/L6_drivers/hoc_cus_incidents_L6_drivers_incident_aggregator.md) — Incident aggregation persistence - pure data access
- [incident_pattern_driver.py](incidents/L6_drivers/hoc_cus_incidents_L6_drivers_incident_pattern_driver.md) — Data access for incident pattern detection operations (async)
- [incident_read_driver.py](incidents/L6_drivers/hoc_cus_incidents_L6_drivers_incident_read_driver.md) — Data access for incident read operations
- [incident_write_driver.py](incidents/L6_drivers/hoc_cus_incidents_L6_drivers_incident_write_driver.md) — Data access for incident write operations
- [incidents_facade_driver.py](incidents/L6_drivers/hoc_cus_incidents_L6_drivers_incidents_facade_driver.md) — Database operations for incidents facade - pure data access
- [lessons_driver.py](incidents/L6_drivers/hoc_cus_incidents_L6_drivers_lessons_driver.md) — Data access for lessons_learned operations
- [llm_failure_driver.py](incidents/L6_drivers/hoc_cus_incidents_L6_drivers_llm_failure_driver.md) — Data access for LLM failure operations (async)
- [policy_violation_driver.py](incidents/L6_drivers/hoc_cus_incidents_L6_drivers_policy_violation_driver.md) — Data access for policy violation operations (async + sync)
- [postmortem_driver.py](incidents/L6_drivers/hoc_cus_incidents_L6_drivers_postmortem_driver.md) — Data access for post-mortem analytics operations (async)
- [recurrence_analysis_driver.py](incidents/L6_drivers/hoc_cus_incidents_L6_drivers_recurrence_analysis_driver.md) — Database operations for recurrence analysis - pure data access

## Integrations

[Domain Summary](integrations/_summary.md)

### L5_engines

- [bridges.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_bridges.md) — Integration bridge abstractions with embedded DB operations
- [cloud_functions_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_cloud_functions_adapter.md) — Google Cloud Functions serverless adapter
- [connectors_facade.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_connectors_facade.md) — Connectors Facade - Centralized access to connector operations
- [cost_bridges_engine.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_cost_bridges_engine.md) — Cost-related integration bridges (cost loop business logic)
- [cus_health_engine.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_cus_health_engine.md) — Health checking engine for customer LLM integrations
- [cus_integration_service.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_cus_integration_service.md) — Customer integration service - LLM BYOK, SDK, RAG management
- [customer_activity_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_customer_activity_adapter.md) — Customer activity boundary adapter (L2 → L3 → L5)
- [customer_incidents_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_customer_incidents_adapter.md) — Customer incidents boundary adapter (L2 → L3 → L4)
- [customer_keys_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_customer_keys_adapter.md) — Customer API keys boundary adapter (L2 → L3 → L4)
- [customer_logs_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_customer_logs_adapter.md) — Customer logs boundary adapter (L2 → L3 → L4)
- [customer_policies_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_customer_policies_adapter.md) — Customer policies boundary adapter (L2 → L3 → L4)
- [datasources_facade.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_datasources_facade.md) — DataSources Facade - Centralized access to data source operations
- [dispatcher.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_dispatcher.md) — Integration event dispatcher with embedded DB persistence
- [file_storage_base.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_file_storage_base.md) — Base class for file storage adapters
- [founder_ops_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_founder_ops_adapter.md) — Translate OpsIncident domain models to Founder-facing views
- [gcs_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_gcs_adapter.md) — Google Cloud Storage file storage adapter
- [graduation_engine.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_graduation_engine.md) — Agent graduation evaluation domain logic (pure computation)
- [http_connector.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_http_connector.md) — Machine-controlled HTTP connector (NOT LLM-controlled)
- [iam_engine.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_iam_engine.md) — IAM engine for identity and access management
- [integrations_facade.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_integrations_facade.md) — Integrations domain facade - unified entry point for integration manag
- [lambda_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_lambda_adapter.md) — AWS Lambda serverless adapter
- [mcp_connector.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_mcp_connector.md) — Model Context Protocol (MCP) tool invocation with governance
- [pgvector_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_pgvector_adapter.md) — PGVector production adapter
- [pinecone_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_pinecone_adapter.md) — Pinecone vector store adapter
- [prevention_contract.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_prevention_contract.md) — Prevention contract enforcement (validation logic)
- [protocol.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_protocol.md) — Canonical CredentialService protocol for connector services
- [runtime_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_runtime_adapter.md) — Translate API requests into runtime domain commands
- [s3_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_s3_adapter.md) — AWS S3 file storage adapter
- [serverless_base.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_serverless_base.md) — Base class for serverless adapters
- [slack_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_slack_adapter.md) — Slack notification adapter
- [smtp_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_smtp_adapter.md) — SMTP email notification adapter
- [sql_gateway.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_sql_gateway.md) — Template-based SQL queries (NO raw SQL from LLM)
- [types.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_types.md) — Canonical Credential dataclass for connector services
- [vector_stores_base.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_vector_stores_base.md) — Base class for vector store adapters
- [weaviate_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_weaviate_adapter.md) — Weaviate vector store adapter
- [webhook_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_webhook_adapter.md) — Webhook notification adapter with retry logic
- [workers_adapter.py](integrations/L5_engines/hoc_cus_integrations_L5_engines_workers_adapter.md) — Worker execution boundary adapter (L2 → L3 → L4)

### L5_notifications

- [channel_engine.py](integrations/L5_notifications/hoc_cus_integrations_L5_notifications_channel_engine.md) — Configurable notification channel management engine

### L5_schemas

- [audit_schemas.py](integrations/L5_schemas/hoc_cus_integrations_L5_schemas_audit_schemas.md) — Audit trail dataclasses for integration bridges
- [cus_schemas.py](integrations/L5_schemas/hoc_cus_integrations_L5_schemas_cus_schemas.md) — Pydantic schemas for Customer Integration domain (LLM BYOK, SDK, RAG)
- [datasource_model.py](integrations/L5_schemas/hoc_cus_integrations_L5_schemas_datasource_model.md) — _no role declared_
- [loop_events.py](integrations/L5_schemas/hoc_cus_integrations_L5_schemas_loop_events.md) — Integration loop event definitions (dataclasses, enums)

### L5_vault

- [service.py](integrations/L5_vault/hoc_cus_integrations_L5_vault_service.md) — High-level credential service with validation and auditing
- [vault.py](integrations/L5_vault/hoc_cus_integrations_L5_vault_vault.md) — Credential vault abstraction with multiple provider support

### L6_drivers

- [connector_registry.py](integrations/L6_drivers/hoc_cus_integrations_L6_drivers_connector_registry.md) — Connector management and registration
- [external_response_driver.py](integrations/L6_drivers/hoc_cus_integrations_L6_drivers_external_response_driver.md) — External response persistence and interpretation driver
- [worker_registry_driver.py](integrations/L6_drivers/hoc_cus_integrations_L6_drivers_worker_registry_driver.md) — Worker discovery, status queries, capability registry driver

## Logs

[Domain Summary](logs/_summary.md)

### L5_engines

- [audit_evidence.py](logs/L5_engines/hoc_cus_logs_L5_engines_audit_evidence.md) — Emit compliance-grade audit for MCP tool calls
- [audit_ledger_service.py](logs/L5_engines/hoc_cus_logs_L5_engines_audit_ledger_service.md) — Sync audit ledger writer for governance events (incidents)
- [audit_reconciler.py](logs/L5_engines/hoc_cus_logs_L5_engines_audit_reconciler.md) — Reconcile audit expectations against acknowledgments
- [certificate.py](logs/L5_engines/hoc_cus_logs_L5_engines_certificate.md) — Cryptographic certificate generation for deterministic replay
- [completeness_checker.py](logs/L5_engines/hoc_cus_logs_L5_engines_completeness_checker.md) — Evidence PDF completeness validation for SOC2 compliance
- [evidence_facade.py](logs/L5_engines/hoc_cus_logs_L5_engines_evidence_facade.md) — Evidence Facade - Centralized access to evidence and export operations
- [evidence_report.py](logs/L5_engines/hoc_cus_logs_L5_engines_evidence_report.md) — Evidence report generator - Legal-grade PDF export
- [logs_facade.py](logs/L5_engines/hoc_cus_logs_L5_engines_logs_facade.md) — Logs domain facade - unified entry point for all logs operations
- [logs_read_engine.py](logs/L5_engines/hoc_cus_logs_L5_engines_logs_read_engine.md) — Logs/Traces domain read operations (L5)
- [mapper.py](logs/L5_engines/hoc_cus_logs_L5_engines_mapper.md) — Map incidents to relevant SOC2 controls
- [panel_response_assembler.py](logs/L5_engines/hoc_cus_logs_L5_engines_panel_response_assembler.md) — Assemble final panel response envelope
- [pdf_renderer.py](logs/L5_engines/hoc_cus_logs_L5_engines_pdf_renderer.md) — Render export bundles to PDF format
- [redact.py](logs/L5_engines/hoc_cus_logs_L5_engines_redact.md) — Trace data redaction for security
- [replay_determinism.py](logs/L5_engines/hoc_cus_logs_L5_engines_replay_determinism.md) — Replay determinism validation for LLM calls — CANONICAL DEFINITIONS
- [trace_facade.py](logs/L5_engines/hoc_cus_logs_L5_engines_trace_facade.md) — Trace Domain Facade - Centralized access to trace operations with RAC 
- [traces_metrics.py](logs/L5_engines/hoc_cus_logs_L5_engines_traces_metrics.md) — Trace metrics collection (Prometheus)
- [traces_models.py](logs/L5_engines/hoc_cus_logs_L5_engines_traces_models.md) — Trace data models (dataclasses)

### L5_support

- [audit_engine.py](logs/L5_support/hoc_cus_logs_L5_support_audit_engine.md) — Audit Engine - verifies job execution against contract intent

### L6_drivers

- [audit_ledger_service_async.py](logs/L6_drivers/hoc_cus_logs_L6_drivers_audit_ledger_service_async.md) — Async audit ledger writer for governance events
- [bridges_driver.py](logs/L6_drivers/hoc_cus_logs_L6_drivers_bridges_driver.md) — Database operations for integration bridges
- [capture.py](logs/L6_drivers/hoc_cus_logs_L6_drivers_capture.md) — Taxonomy evidence capture service (ctx-aware) — L6 DOES NOT COMMIT
- [export_bundle_store.py](logs/L6_drivers/hoc_cus_logs_L6_drivers_export_bundle_store.md) — Database operations for export bundle data (incidents, runs, traces)
- [idempotency.py](logs/L6_drivers/hoc_cus_logs_L6_drivers_idempotency.md) — Trace idempotency enforcement (Redis + Lua scripts)
- [integrity.py](logs/L6_drivers/hoc_cus_logs_L6_drivers_integrity.md) — Integrity computation with separated concerns
- [job_execution.py](logs/L6_drivers/hoc_cus_logs_L6_drivers_job_execution.md) — Job execution support services (retry, progress, audit)
- [logs_domain_store.py](logs/L6_drivers/hoc_cus_logs_L6_drivers_logs_domain_store.md) — Database operations for Logs domain (LLM runs, system records, audit l
- [panel_consistency_checker.py](logs/L6_drivers/hoc_cus_logs_L6_drivers_panel_consistency_checker.md) — Cross-slot consistency enforcement
- [pg_store.py](logs/L6_drivers/hoc_cus_logs_L6_drivers_pg_store.md) — PostgreSQL trace storage
- [replay.py](logs/L6_drivers/hoc_cus_logs_L6_drivers_replay.md) — Trace replay execution
- [traces_store.py](logs/L6_drivers/hoc_cus_logs_L6_drivers_traces_store.md) — Trace store abstraction

## Overview

[Domain Summary](overview/_summary.md)

### L5_engines

- [overview_facade.py](overview/L5_engines/hoc_cus_overview_L5_engines_overview_facade.md) — Overview Engine - Centralized access to overview domain operations

### L6_drivers

- [overview_facade_driver.py](overview/L6_drivers/hoc_cus_overview_L6_drivers_overview_facade_driver.md) — Overview Facade Driver - Pure data access for overview aggregation

## Policies

[Domain Summary](policies/_summary.md)

### L5_engines

- [ast.py](policies/L5_engines/hoc_cus_policies_L5_engines_ast.md) — Policy DSL AST node definitions (immutable, typed)
- [authority_checker.py](policies/L5_engines/hoc_cus_policies_L5_engines_authority_checker.md) — Check override authority before policy enforcement
- [binding_moment_enforcer.py](policies/L5_engines/hoc_cus_policies_L5_engines_binding_moment_enforcer.md) — Enforce binding moments - when policies are evaluated
- [claim_decision_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_claim_decision_engine.md) — _no role declared_
- [compiler_parser.py](policies/L5_engines/hoc_cus_policies_L5_engines_compiler_parser.md) — Policy language parser
- [content_accuracy.py](policies/L5_engines/hoc_cus_policies_L5_engines_content_accuracy.md) — Policy content accuracy validation (pure logic)
- [cus_enforcement_service.py](policies/L5_engines/hoc_cus_policies_L5_engines_cus_enforcement_service.md) — Customer enforcement service - LLM integration policy enforcement
- [customer_policy_read_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_customer_policy_read_engine.md) — Customer policy domain read operations with business logic (pure logic
- [decorator.py](policies/L5_engines/hoc_cus_policies_L5_engines_decorator.md) — Optional ergonomic decorator over ExecutionKernel
- [degraded_mode.py](policies/L5_engines/hoc_cus_policies_L5_engines_degraded_mode.md) — Degraded mode for governance system (pure state logic)
- [deterministic_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_deterministic_engine.md) — Deterministic policy execution engine
- [dsl_parser.py](policies/L5_engines/hoc_cus_policies_L5_engines_dsl_parser.md) — Policy DSL text parser (DSL → AST) - pure parsing
- [eligibility_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_eligibility_engine.md) — Eligibility Engine - pure rules, deterministic gating
- [engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_engine.md) — Policy rule evaluation engine
- [failure_mode_handler.py](policies/L5_engines/hoc_cus_policies_L5_engines_failure_mode_handler.md) — Handle failure modes - default to fail-closed
- [folds.py](policies/L5_engines/hoc_cus_policies_L5_engines_folds.md) — Policy constant folding optimizations (pure logic)
- [governance_facade.py](policies/L5_engines/hoc_cus_policies_L5_engines_governance_facade.md) — Governance Facade - Centralized access to governance control operation
- [grammar.py](policies/L5_engines/hoc_cus_policies_L5_engines_grammar.md) — Policy language grammar definitions (pure definitions)
- [intent.py](policies/L5_engines/hoc_cus_policies_L5_engines_intent.md) — Policy intent model and declaration
- [interpreter.py](policies/L5_engines/hoc_cus_policies_L5_engines_interpreter.md) — Policy DSL Interpreter (pure IR evaluation)
- [ir_builder.py](policies/L5_engines/hoc_cus_policies_L5_engines_ir_builder.md) — Policy intermediate representation builder
- [ir_compiler.py](policies/L5_engines/hoc_cus_policies_L5_engines_ir_compiler.md) — Policy DSL IR Compiler (AST → bytecode) - pure compilation logic
- [ir_nodes.py](policies/L5_engines/hoc_cus_policies_L5_engines_ir_nodes.md) — Policy IR node definitions (pure data structures)
- [kernel.py](policies/L5_engines/hoc_cus_policies_L5_engines_kernel.md) — Mandatory execution kernel - single choke point for all EXECUTE power
- [keys_shim.py](policies/L5_engines/hoc_cus_policies_L5_engines_keys_shim.md) — API Keys domain operations — delegates to L6 driver
- [kill_switch.py](policies/L5_engines/hoc_cus_policies_L5_engines_kill_switch.md) — Runtime kill switch for governance bypass (pure state logic)
- [learning_proof_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_learning_proof_engine.md) — Learning proof generation (graduation gates, regret tracking)
- [lessons_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_lessons_engine.md) — Lessons learned creation and management (domain logic)
- [limits.py](policies/L5_engines/hoc_cus_policies_L5_engines_limits.md) — Phase-6 Limits derivation (code only, not stored)
- [limits_facade.py](policies/L5_engines/hoc_cus_policies_L5_engines_limits_facade.md) — Limits Facade - Centralized access to rate limits and quotas
- [limits_simulation_service.py](policies/L5_engines/hoc_cus_policies_L5_engines_limits_simulation_service.md) — Limits simulation service - pre-execution limit checks
- [llm_policy_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_llm_policy_engine.md) — LLM policy and safety limits enforcement (pure logic)
- [nodes.py](policies/L5_engines/hoc_cus_policies_L5_engines_nodes.md) — Policy AST node definitions (pure data structures)
- [phase_status_invariants.py](policies/L5_engines/hoc_cus_policies_L5_engines_phase_status_invariants.md) — Phase-status invariant enforcement from GovernanceConfig
- [plan.py](policies/L5_engines/hoc_cus_policies_L5_engines_plan.md) — Phase-6 Plan model (abstract, no DB persistence)
- [plan_generation_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_plan_generation_engine.md) — Plan generation (domain logic)
- [policies_facade.py](policies/L5_engines/hoc_cus_policies_L5_engines_policies_facade.md) — Policies facade - unified entry point for policy management
- [policies_limits_query_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_policies_limits_query_engine.md) — Limits query engine - read-only operations for limits
- [policies_proposals_query_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_policies_proposals_query_engine.md) — Proposals query engine - read-only operations for policy proposals lis
- [policies_rules_query_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_policies_rules_query_engine.md) — Policy rules query engine - read-only operations for policy rules
- [policy_command.py](policies/L5_engines/hoc_cus_policies_L5_engines_policy_command.md) — Policy evaluation and decision authority
- [policy_conflict_resolver.py](policies/L5_engines/hoc_cus_policies_L5_engines_policy_conflict_resolver.md) — Resolve conflicts when multiple policies trigger different actions (pu
- [policy_driver.py](policies/L5_engines/hoc_cus_policies_L5_engines_policy_driver.md) — Policy Domain Driver - Internal orchestration for policy operations
- [policy_graph_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_policy_graph_engine.md) — Policy conflict detection and dependency graph computation
- [policy_limits_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_policy_limits_engine.md) — Policy limits CRUD engine (PIN-LIM-01) - pure business logic
- [policy_mapper.py](policies/L5_engines/hoc_cus_policies_L5_engines_policy_mapper.md) — Map MCP tool invocations to policy gates
- [policy_models.py](policies/L5_engines/hoc_cus_policies_L5_engines_policy_models.md) — Policy domain models and types
- [policy_proposal_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_policy_proposal_engine.md) — Policy proposal lifecycle engine - manages proposal state machine
- [policy_rules_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_policy_rules_engine.md) — Policy rules CRUD engine (PIN-LIM-02) - pure business logic
- [prevention_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_prevention_engine.md) — Policy prevention engine for runtime enforcement
- [prevention_hook.py](policies/L5_engines/hoc_cus_policies_L5_engines_prevention_hook.md) — Prevention hook for policy enforcement
- [protection_provider.py](policies/L5_engines/hoc_cus_policies_L5_engines_protection_provider.md) — Phase-7 AbuseProtectionProvider protocol and MockAbuseProtectionProvid
- [recovery_evaluation_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_recovery_evaluation_engine.md) — Recovery evaluation decision-making (domain logic)
- [runtime_command.py](policies/L5_engines/hoc_cus_policies_L5_engines_runtime_command.md) — Runtime domain commands and query logic (pure logic)
- [sandbox_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_sandbox_engine.md) — High-level sandbox engine with policy enforcement (pure business logic
- [snapshot_engine.py](policies/L5_engines/hoc_cus_policies_L5_engines_snapshot_engine.md) — Policy snapshot immutability engine (pure business logic)
- [state.py](policies/L5_engines/hoc_cus_policies_L5_engines_state.md) — Phase-6 Billing State enum (pure enum definitions)
- [tokenizer.py](policies/L5_engines/hoc_cus_policies_L5_engines_tokenizer.md) — Policy language tokenizer (pure lexical analysis)
- [validator.py](policies/L5_engines/hoc_cus_policies_L5_engines_validator.md) — Policy DSL semantic validator (pure validation logic)
- [visitors.py](policies/L5_engines/hoc_cus_policies_L5_engines_visitors.md) — Policy AST visitor pattern implementations
- [worker_execution_command.py](policies/L5_engines/hoc_cus_policies_L5_engines_worker_execution_command.md) — Worker execution authorization and delegation

### L5_schemas

- [policy_rules.py](policies/L5_schemas/hoc_cus_policies_L5_schemas_policy_rules.md) — Policy rules request/response schemas

### L6_drivers

- [arbitrator.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_arbitrator.md) — Resolve conflicts between multiple applicable policies
- [optimizer_conflict_resolver.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_optimizer_conflict_resolver.md) — Policy conflict resolution
- [policy_engine_driver.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_policy_engine_driver.md) — Policy Engine data access operations
- [policy_graph_driver.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_policy_graph_driver.md) — Policy graph data access operations
- [policy_proposal_read_driver.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_policy_proposal_read_driver.md) — Read operations for policy proposal engine
- [policy_proposal_write_driver.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_policy_proposal_write_driver.md) — Write operations for policy proposal engine
- [policy_read_driver.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_policy_read_driver.md) — Data access for customer policy read operations
- [policy_rules_driver.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_policy_rules_driver.md) — Data access for policy rules CRUD operations
- [policy_rules_read_driver.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_policy_rules_read_driver.md) — Read operations for policy rules
- [proposals_read_driver.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_proposals_read_driver.md) — Read operations for policy proposals (list view)
- [recovery_matcher.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_recovery_matcher.md) — Match failure patterns and generate recovery suggestions — L6 DOES NOT
- [recovery_write_driver.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_recovery_write_driver.md) — DB write driver for Recovery APIs (DB boundary crossing)
- [scope_resolver.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_scope_resolver.md) — Resolve which policies apply to a given run context
- [symbol_table.py](policies/L6_drivers/hoc_cus_policies_L6_drivers_symbol_table.md) — Policy symbol table management
