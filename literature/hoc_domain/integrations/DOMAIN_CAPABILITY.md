# Integrations — Domain Capability

**Domain:** integrations  
**Total functions:** 646  
**Generator:** `scripts/ops/hoc_capability_doc_generator.py`

---

## Reality Delta (2026-02-11)

- Integration onboarding write flows are session-corrected at L2:
- `backend/app/hoc/api/cus/integrations/aos_cus_integrations.py`
- `create/update/delete/enable/disable/test` now pass `sync_session` to L4 `integrations.query`.
- L4 integrations handlers strip transport params (`method`, `sync_session`) before facade dispatch.
- Activation authority boundary moved to persistent evidence:
- connector readiness is evaluated via DB (`cus_integrations.status = 'enabled'`) in onboarding handler.
- in-memory connector registry is explicitly cache-only and excluded from activation authority.
- CI check 35 blocks any activation-section import/use of connector registry cache APIs.

## Reality Delta (2026-02-07)

- L2 purity preserved: integrations L2 routes dispatch via L4 `OperationRegistry` (0 direct L2→L5).
- External connector I/O is isolated behind L6 (`backend/app/hoc/cus/integrations/L6_drivers/sql_gateway_driver.py`) with Protocol/DTO boundary in L5 schemas.
- L5/L6 purity: `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --domain integrations --json --advisory` reports 0 blocking, 0 advisory.
- Remaining coherence debt (execution boundary): `python3 scripts/ops/l5_spine_pairing_gap_detector.py --domain integrations --json` reports 5 orphaned L5 entry modules.
- Plan: `docs/architecture/hoc/DOMAIN_EXECUTION_BOUNDARY_REMEDIATION_PLAN.md`.

## 1. Domain Purpose

External system integrations — webhook management, third-party connectors, event routing, and integration health monitoring.

## 2. Customer-Facing Operations

| Function | File | L4 Wired | Entry Point | Side Effects |
|----------|------|----------|-------------|--------------|
| `CapabilityGates.can_auto_activate_policy` | graduation_engine | No (gap) | L2:M25_integrations | pure |
| `CapabilityGates.can_auto_apply_recovery` | graduation_engine | No (gap) | L2:M25_integrations | pure |
| `CapabilityGates.can_full_auto_routing` | graduation_engine | No (gap) | L2:M25_integrations | pure |
| `CapabilityGates.get_blocked_capabilities` | graduation_engine | No (gap) | L2:M25_integrations | pure |
| `CapabilityGates.get_unlocked_capabilities` | graduation_engine | No (gap) | L2:M25_integrations | pure |
| `ComputedGraduationStatus.is_degraded` | graduation_engine | No (gap) | L2:M25_integrations | pure |
| `ComputedGraduationStatus.is_graduated` | graduation_engine | No (gap) | L2:M25_integrations | pure |
| `ComputedGraduationStatus.status_label` | graduation_engine | No (gap) | L2:M25_integrations | pure |
| `ComputedGraduationStatus.to_api_response` | graduation_engine | No (gap) | L2:M25_integrations | pure |
| `ConnectorInfo.to_dict` | connectors_facade | Yes | L4:integrations_handler | pure |
| `ConnectorsFacade.delete_connector` | connectors_facade | Yes | L4:integrations_handler | pure |
| `ConnectorsFacade.get_connector` | connectors_facade | Yes | L4:integrations_handler | pure |
| `ConnectorsFacade.list_connectors` | connectors_facade | Yes | L4:integrations_handler | pure |
| `ConnectorsFacade.register_connector` | connectors_facade | Yes | L4:integrations_handler | pure |
| `ConnectorsFacade.registry` | connectors_facade | Yes | L4:integrations_handler | pure |
| `ConnectorsFacade.test_connector` | connectors_facade | Yes | L4:integrations_handler | pure |
| `ConnectorsFacade.update_connector` | connectors_facade | Yes | L4:integrations_handler | pure |
| `CusIntegrationCreate.validate_not_raw_key` | cus_schemas | No (gap) | L2:aos_cus_integrations | pure |
| `CusIntegrationUpdate.validate_not_raw_key` | cus_schemas | No (gap) | L2:aos_cus_integrations | pure |
| `CustomerIncidentsAdapter.acknowledge_incident` | customer_incidents_adapter | No (gap) | L2:guard | pure |
| `CustomerIncidentsAdapter.get_incident` | customer_incidents_adapter | No (gap) | L2:guard | pure |
| `CustomerIncidentsAdapter.list_incidents` | customer_incidents_adapter | No (gap) | L2:guard | pure |
| `CustomerIncidentsAdapter.resolve_incident` | customer_incidents_adapter | No (gap) | L2:guard | pure |
| `CustomerKeysAdapter.freeze_key` | customer_keys_adapter | No (gap) | L2:guard | pure |
| `CustomerKeysAdapter.get_key` | customer_keys_adapter | No (gap) | L2:guard | pure |
| `CustomerKeysAdapter.list_keys` | customer_keys_adapter | No (gap) | L2:guard | pure |
| `CustomerKeysAdapter.unfreeze_key` | customer_keys_adapter | No (gap) | L2:guard | pure |
| `CustomerLogsAdapter.export_logs` | customer_logs_adapter | No (gap) | L2:guard_logs | pure |
| `CustomerLogsAdapter.get_log` | customer_logs_adapter | No (gap) | L2:guard_logs | pure |
| `CustomerLogsAdapter.list_logs` | customer_logs_adapter | No (gap) | L2:guard_logs | pure |
| `CustomerPoliciesAdapter.get_guardrail_detail` | customer_policies_adapter | No (gap) | L2:guard_policies | pure |
| `CustomerPoliciesAdapter.get_policy_constraints` | customer_policies_adapter | No (gap) | L2:guard_policies | pure |
| `DataSourcesFacade.activate_source` | datasources_facade | Yes | L4:integrations_handler | pure |
| `DataSourcesFacade.deactivate_source` | datasources_facade | Yes | L4:integrations_handler | pure |
| `DataSourcesFacade.delete_source` | datasources_facade | Yes | L4:integrations_handler | db_write |
| `DataSourcesFacade.get_source` | datasources_facade | Yes | L4:integrations_handler | pure |
| `DataSourcesFacade.get_statistics` | datasources_facade | Yes | L4:integrations_handler | pure |
| `DataSourcesFacade.list_sources` | datasources_facade | Yes | L4:integrations_handler | pure |
| `DataSourcesFacade.register_source` | datasources_facade | Yes | L4:integrations_handler | pure |
| `DataSourcesFacade.registry` | datasources_facade | Yes | L4:integrations_handler | pure |
| `DataSourcesFacade.test_connection` | datasources_facade | Yes | L4:integrations_handler | pure |
| `DataSourcesFacade.update_source` | datasources_facade | Yes | L4:integrations_handler | pure |
| `GraduationEngine.compute` | graduation_engine | No (gap) | L2:M25_integrations | pure |
| `IntegrationsFacade.create_integration` | integrations_facade | Yes | L4:integrations_handler | pure |
| `IntegrationsFacade.delete_integration` | integrations_facade | Yes | L4:integrations_handler | pure |
| `IntegrationsFacade.disable_integration` | integrations_facade | Yes | L4:integrations_handler | pure |
| `IntegrationsFacade.enable_integration` | integrations_facade | Yes | L4:integrations_handler | pure |
| `IntegrationsFacade.get_health_status` | integrations_facade | Yes | L4:integrations_handler | pure |
| `IntegrationsFacade.get_integration` | integrations_facade | Yes | L4:integrations_handler | pure |
| `IntegrationsFacade.get_limits_status` | integrations_facade | Yes | L4:integrations_handler | pure |
| `IntegrationsFacade.list_integrations` | integrations_facade | Yes | L4:integrations_handler | pure |
| `IntegrationsFacade.test_credentials` | integrations_facade | Yes | L4:integrations_handler | pure |
| `IntegrationsFacade.update_integration` | integrations_facade | Yes | L4:integrations_handler | pure |
| `RuntimeAdapter.describe_skill` | runtime_adapter | Yes | L2:runtime | pure |
| `RuntimeAdapter.get_capabilities` | runtime_adapter | Yes | L2:runtime | pure |
| `RuntimeAdapter.get_resource_contract` | runtime_adapter | Yes | L2:runtime | pure |
| `RuntimeAdapter.get_skill_descriptors` | runtime_adapter | Yes | L2:runtime | pure |
| `RuntimeAdapter.get_supported_queries` | runtime_adapter | Yes | L2:runtime | pure |
| `RuntimeAdapter.list_skills` | runtime_adapter | Yes | L2:runtime | pure |
| `RuntimeAdapter.query` | runtime_adapter | Yes | L2:runtime | pure |
| `SimulationState.is_demo_mode` | graduation_engine | No (gap) | L2:M25_integrations | pure |
| `SimulationState.to_display` | graduation_engine | No (gap) | L2:M25_integrations | pure |
| `TestConnectionResult.to_dict` | datasources_facade | Yes | L4:integrations_handler | pure |
| `TestResult.to_dict` | connectors_facade | Yes | L4:integrations_handler | pure |
| `WorkersAdapter.calculate_cost_cents` | workers_adapter | No (gap) | L2:workers | pure |
| `WorkersAdapter.convert_brand_request` | workers_adapter | No (gap) | L2:workers | pure |
| `WorkersAdapter.execute_worker` | workers_adapter | No (gap) | L2:workers | pure |
| `WorkersAdapter.replay_execution` | workers_adapter | No (gap) | L2:workers | pure |
| `get_connectors_facade` | connectors_facade | Yes | L4:integrations_handler | pure |
| `get_customer_incidents_adapter` | customer_incidents_adapter | No (gap) | L2:guard | pure |
| `get_customer_keys_adapter` | customer_keys_adapter | No (gap) | L2:guard | pure |
| `get_customer_logs_adapter` | customer_logs_adapter | No (gap) | L2:guard_logs | pure |
| `get_customer_policies_adapter` | customer_policies_adapter | No (gap) | L2:guard_policies | pure |
| `get_datasources_facade` | datasources_facade | Yes | L4:integrations_handler | pure |
| `get_integrations_facade` | integrations_facade | Yes | L4:integrations_handler | pure |
| `get_runtime_adapter` | runtime_adapter | Yes | L2:runtime | pure |
| `get_workers_adapter` | workers_adapter | No (gap) | L2:workers | pure |

## 3. Internal Functions

### Decisions

| Function | File | Confidence |
|----------|------|------------|
| `CircuitBreaker.can_execute` | webhook_adapter | medium |
| `ConfidenceBand.allows_auto_apply` | loop_events | ambiguous |
| `ConfidenceCalculator.should_auto_apply` | loop_events | ambiguous |
| `CusHealthService.check_all_integrations` | cus_health_engine | medium |
| `CusHealthService.check_health` | cus_health_engine | medium |
| `FileStorageAdapter.health_check` | file_storage_base | ambiguous |
| `IAMService.check_access` | iam_engine | ambiguous |
| `IntegrationDispatcher.get_pending_checkpoints` | dispatcher | medium |
| `IntegrationDispatcher.resolve_checkpoint` | dispatcher | ambiguous |
| `NotifyChannelService.check_health` | channel_engine | ambiguous |
| `PatternMatchResult.should_auto_proceed` | loop_events | ambiguous |
| `RoutingAdjustment.check_kpi_regression` | loop_events | medium |
| `ServerlessAdapter.health_check` | serverless_base | ambiguous |
| `VectorStoreAdapter.health_check` | vector_stores_base | ambiguous |
| `assert_no_deletion` | prevention_contract | medium |
| `assert_prevention_immutable` | prevention_contract | medium |
| `check_channel_health` | channel_engine | ambiguous |
| `validate_prevention_candidate` | prevention_contract | medium |
| `validate_prevention_for_graduation` | prevention_contract | medium |

### Coordinators

| Function | File | Confidence |
|----------|------|------------|
| `CloudFunctionsAdapter.invoke_batch` | cloud_functions_adapter | medium |
| `HumanCheckpoint.resolve` | loop_events | medium |
| `IAMService.resolve_identity` | iam_engine | ambiguous |
| `IntegrationDispatcher.dispatch` | dispatcher | medium |
| `LambdaAdapter.invoke_batch` | lambda_adapter | medium |
| `SMTPAdapter.send_batch` | smtp_adapter | medium |
| `ServerlessAdapter.invoke_batch` | serverless_base | ambiguous |
| `SlackAdapter.send_batch` | slack_adapter | medium |
| `WebhookAdapter.send_batch` | webhook_adapter | medium |

### Helpers

_265 internal helper functions._

- **audit_schemas:** `PolicyActivationAudit.to_dict`
- **bridges:** `IncidentToCatalogBridge.__init__`, `IncidentToCatalogBridge._calculate_fuzzy_confidence`, `IncidentToCatalogBridge._create_pattern`, `IncidentToCatalogBridge._extract_signature`, `IncidentToCatalogBridge._find_matching_pattern`, `IncidentToCatalogBridge._hash_signature`, `IncidentToCatalogBridge._increment_pattern_count`, `LoopStatusBridge.__init__`, `LoopStatusBridge._build_loop_status`, `LoopStatusBridge._push_sse_update`
  _...and 18 more_
- **channel_engine:** `NotificationSender.send`, `NotifyChannelConfig.is_configured`, `NotifyChannelConfig.is_event_enabled`, `NotifyChannelConfig.record_failure`, `NotifyChannelConfig.record_success`, `NotifyChannelConfig.to_dict`, `NotifyChannelConfigResponse.to_dict`, `NotifyChannelError.__init__`, `NotifyChannelError.to_dict`, `NotifyChannelService.__init__`
  _...and 21 more_
- **cloud_functions_adapter:** `CloudFunctionsAdapter.__init__`
- **connector_registry:** `BaseConnector.__init__`, `ConnectorError.__init__`, `ConnectorRegistry.__init__`, `FileConnector.__init__`, `ServerlessConnector.__init__`, `VectorConnector.__init__`, `_reset_registry`
- **connectors_facade:** `ConnectorsFacade.__init__`, `ConnectorsFacade._get_capabilities_for_type`
- **cost_bridges_engine:** `CostAnomaly.to_dict`, `CostEstimationProbe.__init__`, `CostEstimationProbe._calculate_cost`, `CostEstimationProbe._find_cheaper_model`, `CostLoopBridge.__init__`, `CostLoopBridge._map_severity_to_incident_severity`, `CostLoopOrchestrator.__init__`, `CostPatternMatcher.__init__`, `CostPatternMatcher._build_signature`, `CostPatternMatcher._calculate_confidence`
  _...and 14 more_
- **cus_health_engine:** `CusHealthService.__init__`, `CusHealthService._calculate_overall_health`, `CusHealthService._perform_health_check`
- **customer_activity_adapter:** `CustomerActivityAdapter.__init__`, `CustomerActivityAdapter._get_facade`, `CustomerActivityAdapter._to_customer_detail`, `CustomerActivityAdapter._to_customer_summary`
- **customer_incidents_adapter:** `CustomerIncidentsAdapter.__init__`, `_translate_severity`, `_translate_status`
- **customer_keys_adapter:** `CustomerKeysAdapter.__init__`
- **customer_logs_adapter:** `CustomerLogsAdapter.__init__`, `CustomerLogsAdapter._get_service`
- **customer_policies_adapter:** `CustomerPoliciesAdapter.__init__`, `CustomerPoliciesAdapter._get_service`, `CustomerPoliciesAdapter._to_customer_guardrail`, `CustomerPoliciesAdapter._to_customer_policy_constraints`
- **datasource_model:** `CustomerDataSource.to_dict`, `DataSourceConfig.to_dict`, `DataSourceError.__init__`, `DataSourceError.to_dict`, `DataSourceRegistry.__init__`, `DataSourceStats.to_dict`, `_reset_registry`
- **datasources_facade:** `DataSourcesFacade.__init__`
- **dispatcher:** `DispatcherConfig.from_env`, `IntegrationDispatcher.__init__`, `IntegrationDispatcher._check_db_idempotency`, `IntegrationDispatcher._check_human_checkpoint_needed`, `IntegrationDispatcher._execute_handlers`, `IntegrationDispatcher._get_or_create_loop_status`, `IntegrationDispatcher._load_checkpoint`, `IntegrationDispatcher._load_loop_status`, `IntegrationDispatcher._persist_checkpoint`, `IntegrationDispatcher._persist_event`
  _...and 5 more_
- **external_response_driver:** `ExternalResponseService.__init__`
- **file_storage_base:** `DownloadResult.success`, `FileMetadata.to_dict`, `FileStorageAdapter.connect`, `FileStorageAdapter.copy`, `FileStorageAdapter.delete`, `FileStorageAdapter.delete_many`, `FileStorageAdapter.disconnect`, `FileStorageAdapter.download`, `FileStorageAdapter.download_stream`, `FileStorageAdapter.exists`
  _...and 5 more_
- **founder_ops_adapter:** `FounderOpsAdapter.to_summary_response`, `FounderOpsAdapter.to_summary_view`
- **gcs_adapter:** `GCSAdapter.__init__`
- **graduation_engine:** `GraduationEngine.__init__`, `GraduationEngine._check_degradation`, `GraduationEngine._evaluate_gate1`, `GraduationEngine._evaluate_gate2`, `GraduationEngine._evaluate_gate3`
- **http_connector:** `HttpConnectorError.__init__`, `HttpConnectorService.__init__`, `HttpConnectorService._build_url`, `HttpConnectorService._check_rate_limit`, `HttpConnectorService._get_auth_headers`, `HttpConnectorService._record_request`, `HttpConnectorService._resolve_endpoint`, `RateLimitExceededError.__init__`
- **iam_engine:** `AccessDecision.to_dict`, `IAMService.__init__`, `IAMService._create_system_identity`, `IAMService._expand_role_permissions`, `IAMService._resolve_api_key_identity`, `IAMService._resolve_clerk_identity`, `IAMService._setup_default_roles`, `IAMService.define_resource_permissions`, `IAMService.define_role`, `IAMService.get_access_log`
  _...and 9 more_
- **integrations_facade:** `IntegrationsFacade.__init__`
- **lambda_adapter:** `LambdaAdapter.__init__`
- **loop_events:** `ConfidenceBand.from_confidence`, `LoopEvent.to_dict`, `LoopStatus._generate_narrative`, `LoopStatus.to_console_display`, `LoopStatus.to_dict`, `PatternMatchResult.from_match`, `PatternMatchResult.to_dict`, `PolicyRule.to_dict`, `RecoverySuggestion.to_dict`, `RoutingAdjustment.to_dict`
- **mcp_connector:** `McpApprovalRequiredError.__init__`, `McpConnectorError.__init__`, `McpConnectorService.__init__`, `McpConnectorService._build_mcp_request`, `McpConnectorService._check_rate_limit`, `McpConnectorService._get_api_key`, `McpConnectorService._record_request`, `McpConnectorService._resolve_tool`, `McpConnectorService._validate_against_schema`, `McpRateLimitExceededError.__init__`
  _...and 1 more_
- **pgvector_adapter:** `PGVectorAdapter.__init__`
- **pinecone_adapter:** `PineconeAdapter.__init__`
- **prevention_contract:** `PreventionContractViolation.__init__`
- **runtime_adapter:** `RuntimeAdapter.__init__`
- **s3_adapter:** `S3Adapter.__init__`
- **serverless_base:** `FunctionInfo.to_dict`, `InvocationRequest.to_dict`, `InvocationResult.success`, `InvocationResult.to_dict`, `ServerlessAdapter.connect`, `ServerlessAdapter.disconnect`, `ServerlessAdapter.function_exists`, `ServerlessAdapter.get_function_info`, `ServerlessAdapter.invoke`, `ServerlessAdapter.list_functions`
- **service:** `CredentialService.__init__`, `CredentialService._audit`, `CredentialService._validate_name`, `CredentialService._validate_secret_data`, `CredentialService._validate_tenant_id`
- **slack_adapter:** `SlackAdapter.__init__`, `SlackAdapter._build_blocks`, `SlackAdapter._get_priority_emoji`
- **smtp_adapter:** `SMTPAdapter.__init__`, `SMTPAdapter._build_email`
- **sql_gateway:** `SqlGatewayService.__init__`, `SqlGatewayService._check_sql_injection`, `SqlGatewayService._coerce_parameter`, `SqlGatewayService._get_connection_string`, `SqlGatewayService._resolve_template`, `SqlGatewayService._validate_parameters`
- **vault:** `EnvCredentialVault.__init__`, `HashiCorpVault.__init__`
- **vector_stores_base:** `DeleteResult.success`, `IndexStats.to_dict`, `QueryResult.to_dict`, `UpsertResult.success`, `VectorRecord.to_dict`, `VectorStoreAdapter.connect`, `VectorStoreAdapter.create_namespace`, `VectorStoreAdapter.delete`, `VectorStoreAdapter.delete_namespace`, `VectorStoreAdapter.disconnect`
  _...and 4 more_
- **weaviate_adapter:** `WeaviateAdapter.__init__`, `WeaviateAdapter._build_filter`, `WeaviateAdapter._create_collection`
- **webhook_adapter:** `WebhookAdapter.__init__`, `WebhookAdapter._attempt_delivery`, `WebhookAdapter._deliver_with_retry`, `WebhookAdapter._get_circuit_breaker`, `WebhookAdapter._sign_payload`, `WebhookDelivery.to_dict`
- **worker_registry_driver:** `WorkerRegistryService.__init__`

### Persistence

| Function | File | Side Effects |
|----------|------|--------------|
| `BaseConnector.connect` | connector_registry | pure |
| `BaseConnector.disconnect` | connector_registry | pure |
| `BaseConnector.health_check` | connector_registry | pure |
| `BaseConnector.record_connection` | connector_registry | pure |
| `BaseConnector.record_error` | connector_registry | pure |
| `BaseConnector.to_dict` | connector_registry | pure |
| `ConnectorConfig.to_dict` | connector_registry | pure |
| `ConnectorError.to_dict` | connector_registry | pure |
| `ConnectorRegistry.clear_tenant` | connector_registry | db_write |
| `ConnectorRegistry.create_file_connector` | connector_registry | pure |
| `ConnectorRegistry.create_serverless_connector` | connector_registry | pure |
| `ConnectorRegistry.create_vector_connector` | connector_registry | pure |
| `ConnectorRegistry.delete` | connector_registry | pure |
| `ConnectorRegistry.get` | connector_registry | pure |
| `ConnectorRegistry.get_by_name` | connector_registry | pure |
| `ConnectorRegistry.get_statistics` | connector_registry | pure |
| `ConnectorRegistry.list` | connector_registry | pure |
| `ConnectorRegistry.register` | connector_registry | db_write |
| `ConnectorRegistry.reset` | connector_registry | pure |
| `ConnectorStats.to_dict` | connector_registry | pure |
| `ExternalResponseService.get_interpreted` | external_response_driver | db_write |
| `ExternalResponseService.get_pending_interpretations` | external_response_driver | db_write |
| `ExternalResponseService.get_raw_for_interpretation` | external_response_driver | db_write |
| `ExternalResponseService.interpret` | external_response_driver | db_write |
| `ExternalResponseService.record_raw_response` | external_response_driver | db_write |
| `FileConnector.connect` | connector_registry | pure |
| `FileConnector.delete_file` | connector_registry | pure |
| `FileConnector.disconnect` | connector_registry | pure |
| `FileConnector.health_check` | connector_registry | pure |
| `FileConnector.list_files` | connector_registry | pure |
| `FileConnector.read_file` | connector_registry | pure |
| `FileConnector.to_dict` | connector_registry | pure |
| `FileConnector.write_file` | connector_registry | pure |
| `ServerlessConnector.connect` | connector_registry | pure |
| `ServerlessConnector.disconnect` | connector_registry | pure |
| `ServerlessConnector.get_result` | connector_registry | pure |
| `ServerlessConnector.health_check` | connector_registry | pure |
| `ServerlessConnector.invoke` | connector_registry | pure |
| `ServerlessConnector.list_functions` | connector_registry | pure |
| `ServerlessConnector.to_dict` | connector_registry | pure |
| `VectorConnector.connect` | connector_registry | pure |
| `VectorConnector.delete_vectors` | connector_registry | pure |
| `VectorConnector.disconnect` | connector_registry | pure |
| `VectorConnector.health_check` | connector_registry | pure |
| `VectorConnector.search` | connector_registry | pure |
| `VectorConnector.to_dict` | connector_registry | pure |
| `VectorConnector.upsert_vectors` | connector_registry | pure |
| `WorkerRegistryService.deprecate_worker` | worker_registry_driver | pure |
| `WorkerRegistryService.get_effective_worker_config` | worker_registry_driver | pure |
| `WorkerRegistryService.get_tenant_worker_config` | worker_registry_driver | pure |
| `WorkerRegistryService.get_worker` | worker_registry_driver | pure |
| `WorkerRegistryService.get_worker_details` | worker_registry_driver | pure |
| `WorkerRegistryService.get_worker_or_raise` | worker_registry_driver | pure |
| `WorkerRegistryService.get_worker_summary` | worker_registry_driver | pure |
| `WorkerRegistryService.get_workers_for_tenant` | worker_registry_driver | pure |
| `WorkerRegistryService.is_worker_available` | worker_registry_driver | pure |
| `WorkerRegistryService.is_worker_enabled_for_tenant` | worker_registry_driver | pure |
| `WorkerRegistryService.list_available_workers` | worker_registry_driver | pure |
| `WorkerRegistryService.list_tenant_worker_configs` | worker_registry_driver | pure |
| `WorkerRegistryService.list_worker_summaries` | worker_registry_driver | pure |
| `WorkerRegistryService.list_workers` | worker_registry_driver | pure |
| `WorkerRegistryService.register_worker` | worker_registry_driver | db_write |
| `WorkerRegistryService.set_tenant_worker_config` | worker_registry_driver | db_write |
| `WorkerRegistryService.update_worker_status` | worker_registry_driver | db_write |
| `get_connector` | connector_registry | pure |
| `get_connector_registry` | connector_registry | pure |
| `get_interpreted_response` | external_response_driver | pure |
| `get_worker_registry_service` | worker_registry_driver | pure |
| `interpret_response` | external_response_driver | pure |
| `list_connectors` | connector_registry | pure |
| `record_external_response` | external_response_driver | pure |
| `register_connector` | connector_registry | pure |

### Unclassified (needs review)

_204 functions need manual classification._

- `BaseBridge.process` (bridges)
- `BaseBridge.register` (bridges)
- `BaseBridge.stage` (bridges)
- `CircuitBreaker.record_failure` (webhook_adapter)
- `CircuitBreaker.record_success` (webhook_adapter)
- `CloudFunctionsAdapter.connect` (cloud_functions_adapter)
- `CloudFunctionsAdapter.disconnect` (cloud_functions_adapter)
- `CloudFunctionsAdapter.function_exists` (cloud_functions_adapter)
- `CloudFunctionsAdapter.get_function_info` (cloud_functions_adapter)
- `CloudFunctionsAdapter.invoke` (cloud_functions_adapter)
- `CloudFunctionsAdapter.list_functions` (cloud_functions_adapter)
- `ConfidenceBand.requires_human_review` (loop_events)
- `ConfidenceCalculator.calculate_recovery_confidence` (loop_events)
- `ConfidenceCalculator.get_confirmation_level` (loop_events)
- `CostAnomaly.create` (cost_bridges_engine)
- `CostEstimationProbe.probe` (cost_bridges_engine)
- `CostLoopBridge.on_anomaly_detected` (cost_bridges_engine)
- `CostLoopOrchestrator.process_anomaly` (cost_bridges_engine)
- `CostPatternMatcher.match_cost_pattern` (cost_bridges_engine)
- `CostPolicyGenerator.generate_policy` (cost_bridges_engine)
- _...and 184 more_

## 4. Explicit Non-Features

_No explicit non-feature declarations found in INTEGRATIONS_DOMAIN_LOCK_FINAL.md._
