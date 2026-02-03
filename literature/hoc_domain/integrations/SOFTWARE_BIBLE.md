# Integrations — Software Bible

**Domain:** integrations  
**L2 Features:** 6  
**Scripts:** 46  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Script Registry

Each script's unique contribution and canonical function.

| Script | Layer | Canonical Function | Role | Decisions | Callers | Unique? |
|--------|-------|--------------------|------|-----------|---------|---------|
| audit_schemas | L5 | `PolicyActivationAudit.to_dict` | WRAPPER | 0 | L6:bridges_driver | L5s:__init__ | L5:bridges, bridges, connector_registry +4 | **OVERLAP** |
| bridges | L5 | `PatternToRecoveryBridge.process` | CANONICAL | 5 | ?:__init__, channel_engine, connector_registry +6 | YES |
| channel_engine | L5 | `NotifyChannelService.send` | CANONICAL | 8 | bridges, connector_registry, cost_bridges_engine +10 | **OVERLAP** |
| cloud_functions_adapter | L5 | `CloudFunctionsAdapter.invoke_batch` | CANONICAL | 2 | L3:__init__, channel_engine, connector_registry +8 | **OVERLAP** |
| connectors_facade | L5 | `ConnectorsFacade.update_connector` | CANONICAL | 5 | L4:integrations_handler, bridges, channel_engine +8 | YES |
| cost_bridges_engine | L5 | `CostLoopOrchestrator.process_anomaly` | CANONICAL | 3 | L5:__init__, bridges, channel_engine +7 | YES |
| cus_health_engine | L5 | `CusHealthService._perform_health_check` | SUPERSET | 14 | ?:cus_health_service, channel_engine, connector_registry +4 | YES |
| cus_integration_engine | L5 | `CusIntegrationEngine.create_integration` | CANONICAL | 8 | ?:cus_integration_service | L5:integrations_facade | ?:shim_guard | YES |
| cus_schemas | L5 | `CusIntegrationCreate.validate_not_raw_key` | LEAF | 1 | ?:cus_telemetry | ?:aos_cus_integrations | ?:cus_telemetry_engine | ?:cus_integration_engine | L2:aos_cus_integrations | L2:cus_telemetry | YES |
| customer_activity_adapter | L5 | `CustomerActivityAdapter.get_activity` | CANONICAL | 3 | ?:test_l2_l3_contracts, channel_engine, connector_registry +4 | YES |
| customer_incidents_adapter | L5 | `CustomerIncidentsAdapter.get_incident` | CANONICAL | 1 | ?:guard | L3:__init__ | L2:guard | ?:test_l2_l3_contracts, channel_engine, connector_registry +4 | YES |
| customer_keys_adapter | L5 | `CustomerKeysAdapter.freeze_key` | SUPERSET | 2 | ?:guard | L3:__init__ | L2:guard | ?:test_l2_l3_contracts, channel_engine, connector_registry +4 | YES |
| customer_logs_adapter | L5 | `CustomerLogsAdapter.get_log` | CANONICAL | 2 | ?:guard_logs | L3:__init__ | L2:guard_logs | ?:test_l2_l3_contracts, channel_engine, connector_registry +5 | YES |
| customer_policies_adapter | L5 | `CustomerPoliciesAdapter.get_guardrail_detail` | CANONICAL | 3 | ?:guard_policies | L3:__init__ | L2:guard_policies | ?:test_l2_l3_contracts, channel_engine, connector_registry +5 | YES |
| datasource_model | L5 | `DataSourceRegistry.update` | CANONICAL | 5 | ?:facade | ?:__init__ | L5:datasources_facade | ?:test_customer_datasource, bridges, channel_engine +29 | YES |
| datasources_facade | L5 | `DataSourcesFacade.register_source` | CANONICAL | 3 | L4:integrations_handler, bridges, channel_engine +8 | YES |
| dispatcher | L5 | `IntegrationDispatcher.dispatch` | CANONICAL | 8 | ?:bridges | ?:__init__ | L5:bridges | ?:test_m25_integration_loop, bridges, channel_engine +5 | YES |
| file_storage_base | L5 | `DownloadResult.success` | WRAPPER | 0 | bridges, connector_registry, cost_bridges_engine +12 | INTERFACE |
| founder_ops_adapter | L5 | `FounderOpsAdapter.to_summary_response` | ENTRY | 0 | ?:ops | YES |
| gcs_adapter | L5 | `GCSAdapter.list_files` | SUPERSET | 3 | L3:__init__, channel_engine, connector_registry +13 | YES |
| graduation_engine | L5 | `GraduationEngine.compute` | CANONICAL | 5 | ?:M25_integrations | ?:graduation_evaluator | L2:M25_integrations | ?:test_m25_graduation_downgrade, channel_engine, connector_registry +4 | YES |
| http_connector | L5 | `HttpConnectorService.execute` | CANONICAL | 9 | ?:__init__ | ?:test_connectors, bridges, channel_engine +7 | **OVERLAP** |
| iam_engine | L5 | `IAMService.resolve_identity` | SUPERSET | 3 | bridges, channel_engine, connector_registry +7 | YES |
| integrations_facade | L5 | `IntegrationsFacade.create_integration` | LEAF | 0 | ?:aos_cus_integrations | L4:integrations_handler, channel_engine, connector_registry +4 | YES |
| lambda_adapter | L5 | `LambdaAdapter.invoke_batch` | CANONICAL | 2 | L3:__init__, channel_engine, cloud_functions_adapter +8 | **OVERLAP** |
| loop_events | L5 | `ensure_json_serializable` | CANONICAL | 7 | L6:bridges_driver | L5s:__init__ | L5:bridges | L5:dispatcher | L5:cost_bridges_engine, bridges, connector_registry +3 | YES |
| mcp_connector | L5 | `McpConnectorService.execute` | CANONICAL | 6 | ?:__init__ | ?:test_connectors, bridges, channel_engine +7 | **OVERLAP** |
| pgvector_adapter | L5 | `PGVectorAdapter.query` | CANONICAL | 9 | L3:__init__, channel_engine, connector_registry +11 | **OVERLAP** |
| pinecone_adapter | L5 | `PineconeAdapter.delete` | CANONICAL | 4 | L3:__init__, channel_engine, connector_registry +11 | **OVERLAP** |
| prevention_contract | L5 | `validate_prevention_for_graduation` | SUPERSET | 5 | L5:__init__, channel_engine, connector_registry +3 | YES |
| protocol | L5 | `CredentialService.get` | WRAPPER | 0 | L5:http_connector | L5:mcp_connector | L5:sql_gateway | L5:__init__ | ?:credential_service, bridges, channel_engine +27 | YES |
| runtime_adapter | L5 | `RuntimeAdapter.query` | LEAF | 0 | ?:runtime | L3:__init__ | L2:runtime | L4:runtime_adapter, channel_engine, connector_registry +5 | **OVERLAP** |
| s3_adapter | L5 | `S3Adapter.upload` | CANONICAL | 4 | L3:__init__, channel_engine, connector_registry +12 | YES |
| serverless_base | L5 | `FunctionInfo.to_dict` | WRAPPER | 0 | bridges, cloud_functions_adapter, connector_registry +7 | INTERFACE |
| service | L5 | `CredentialService.get_rotatable_credentials` | CANONICAL | 2 | ?:rbac_engine | ?:role_mapping | ?:__init__ | ?:agent_spawn | ?:definitions | ?:failure_intelligence | ?:datasets | L5:datasets, channel_engine, connector_registry +5 | YES |
| slack_adapter | L5 | `SlackAdapter.send_batch` | CANONICAL | 2 | L3:__init__, channel_engine, connector_registry +7 | **OVERLAP** |
| smtp_adapter | L5 | `SMTPAdapter.send_batch` | CANONICAL | 1 | L3:__init__, channel_engine, connector_registry +7 | **OVERLAP** |
| sql_gateway | L5 | `SqlGatewayService.execute` | CANONICAL | 3 | ?:__init__ | ?:test_connectors, bridges, channel_engine +8 | **OVERLAP** |
| vault | L5 | `HashiCorpVault.update_credential` | CANONICAL | 5 | L7:cus_models | ?:cus_schemas | ?:__init__ | ?:service | L5s:cus_schemas, channel_engine, connector_registry +5 | YES |
| vector_stores_base | L5 | `DeleteResult.success` | WRAPPER | 0 | bridges, connector_registry, cost_bridges_engine +11 | INTERFACE |
| weaviate_adapter | L5 | `WeaviateAdapter.delete` | CANONICAL | 7 | L3:__init__, channel_engine, connector_registry +11 | **OVERLAP** |
| webhook_adapter | L5 | `WebhookAdapter.send` | CANONICAL | 3 | L3:__init__, bridges, channel_engine +11 | **OVERLAP** |
| workers_adapter | L5 | `get_workers_adapter` | LEAF | 1 | ?:workers | L3:__init__ | L2:workers | YES |
| connector_registry | L6 | `ConnectorRegistry.list` | CANONICAL | 3 | ?:retrieval_mediator | ?:facade | ?:__init__ | L5:connectors_facade | L4:retrieval_mediator | L4:execution | ?:test_connector_registry | ?:test_retrieval_mediator, bridges, channel_engine +31 | YES |
| external_response_driver | L6 | `ExternalResponseService.get_interpreted` | INTERNAL | 1 | channel_engine, connector_registry, datasource_model +3 | YES |
| worker_registry_driver | L6 | `WorkerRegistryService.get_worker_details` | CANONICAL | 4 | L6:__init__, channel_engine, connector_registry +4 | YES |

## Uncalled Functions

Functions with no internal or external callers detected.
May be: unused code, missing wiring, or entry points not yet traced.

- `channel_engine.NotifyChannelService.configure_channel`
- `channel_engine.NotifyChannelService.disable_channel`
- `channel_engine.NotifyChannelService.enable_channel`
- `channel_engine.NotifyChannelService.get_all_configs`
- `channel_engine.NotifyChannelService.get_delivery_history`
- `channel_engine.NotifyChannelService.set_event_filter`
- `channel_engine.check_channel_health`
- `channel_engine.send_notification`
- `external_response_driver.ExternalResponseService.get_pending_interpretations`
- `external_response_driver.ExternalResponseService.get_raw_for_interpretation`
- `external_response_driver.get_interpreted_response`
- `external_response_driver.interpret_response`
- `external_response_driver.record_external_response`
- `file_storage_base.DownloadResult.success`
- `file_storage_base.FileStorageAdapter.copy`
- `file_storage_base.FileStorageAdapter.delete_many`
- `file_storage_base.FileStorageAdapter.disconnect`
- `file_storage_base.FileStorageAdapter.download`
- `file_storage_base.FileStorageAdapter.download_stream`
- `file_storage_base.FileStorageAdapter.health_check`
- `file_storage_base.FileStorageAdapter.upload`
- `file_storage_base.UploadResult.success`
- `iam_engine.IAMService.check_access`
- `iam_engine.IAMService.define_resource_permissions`
- `iam_engine.IAMService.define_role`
- `iam_engine.IAMService.get_access_log`
- `iam_engine.IAMService.grant_role`
- `iam_engine.IAMService.list_resources`
- `iam_engine.IAMService.list_roles`
- `iam_engine.IAMService.resolve_identity`
- `iam_engine.IAMService.revoke_role`
- `iam_engine.Identity.has_all_roles`
- `iam_engine.Identity.has_any_role`
- `iam_engine.Identity.has_permission`
- `iam_engine.Identity.has_role`
- `serverless_base.InvocationResult.success`
- `serverless_base.ServerlessAdapter.disconnect`
- `serverless_base.ServerlessAdapter.function_exists`
- `serverless_base.ServerlessAdapter.health_check`
- `serverless_base.ServerlessAdapter.invoke_batch`
- `vector_stores_base.DeleteResult.success`
- `vector_stores_base.UpsertResult.success`
- `vector_stores_base.VectorStoreAdapter.create_namespace`
- `vector_stores_base.VectorStoreAdapter.delete_namespace`
- `vector_stores_base.VectorStoreAdapter.disconnect`
- `vector_stores_base.VectorStoreAdapter.health_check`
- `vector_stores_base.VectorStoreAdapter.list_namespaces`

## Overlapping Scripts (same purpose, same layer)

These scripts may serve duplicate purposes within the domain.

- `audit_schemas` — canonical: `PolicyActivationAudit.to_dict` (WRAPPER)
- `channel_engine` — canonical: `NotifyChannelService.send` (CANONICAL)
- `cloud_functions_adapter` — canonical: `CloudFunctionsAdapter.invoke_batch` (CANONICAL)
- `file_storage_base` — canonical: `DownloadResult.success` (WRAPPER)
- `http_connector` — canonical: `HttpConnectorService.execute` (CANONICAL)
- `lambda_adapter` — canonical: `LambdaAdapter.invoke_batch` (CANONICAL)
- `mcp_connector` — canonical: `McpConnectorService.execute` (CANONICAL)
- `pgvector_adapter` — canonical: `PGVectorAdapter.query` (CANONICAL)
- `pinecone_adapter` — canonical: `PineconeAdapter.delete` (CANONICAL)
- `runtime_adapter` — canonical: `RuntimeAdapter.query` (LEAF)
- `serverless_base` — canonical: `FunctionInfo.to_dict` (WRAPPER)
- `slack_adapter` — canonical: `SlackAdapter.send_batch` (CANONICAL)
- `smtp_adapter` — canonical: `SMTPAdapter.send_batch` (CANONICAL)
- `sql_gateway` — canonical: `SqlGatewayService.execute` (CANONICAL)
- `vector_stores_base` — canonical: `DeleteResult.success` (WRAPPER)
- `weaviate_adapter` — canonical: `WeaviateAdapter.delete` (CANONICAL)
- `webhook_adapter` — canonical: `WebhookAdapter.send` (CANONICAL)

## L2 Feature Chains

| Status | Count |
|--------|-------|
| COMPLETE (L2→L4→L5→L6) | 6 |
| GAP (L2→L5 direct) | 0 |

### Wired Features (L2→L4→L5→L6)

#### GET /context
```
L2:session_context.get_session_context → L4:integrations_handler → L6:connector_registry.ConnectorRegistry.clear_tenant
```

#### GET /daily-aggregates
```
L2:cus_telemetry.get_daily_aggregates → L4:OperationContext | get_operation_registry → L6:connector_registry.ConnectorRegistry.clear_tenant
```

#### GET /usage-history
```
L2:cus_telemetry.get_usage_history → L4:OperationContext | get_operation_registry → L6:connector_registry.ConnectorRegistry.clear_tenant
```

#### GET /usage-summary
```
L2:cus_telemetry.get_usage_summary → L4:OperationContext | get_operation_registry → L6:connector_registry.ConnectorRegistry.clear_tenant
```

#### POST /llm-usage
```
L2:cus_telemetry.ingest_llm_usage → L4:OperationContext | get_operation_registry → L6:connector_registry.ConnectorRegistry.clear_tenant
```

#### POST /llm-usage/batch
```
L2:cus_telemetry.ingest_llm_usage_batch → L4:OperationContext | get_operation_registry → L6:connector_registry.ConnectorRegistry.clear_tenant
```

## Canonical Algorithm Inventory

| Function | File | Role | Decisions | Stmts | Persistence | Delegates To |
|----------|------|------|-----------|-------|-------------|--------------|
| `CapabilityGates.get_blocked_capabilities` | graduation_engine | SUPERSET | 3 | 5 | no | graduation_engine:CapabilityGates.can_auto_activate_policy | |
| `CapabilityGates.get_unlocked_capabilities` | graduation_engine | SUPERSET | 3 | 5 | no | graduation_engine:CapabilityGates.can_auto_activate_policy | |
| `CloudFunctionsAdapter.invoke` | cloud_functions_adapter | SUPERSET | 6 | 2 | no | cloud_functions_adapter:CloudFunctionsAdapter.get_function_i |
| `CloudFunctionsAdapter.invoke_batch` | cloud_functions_adapter | CANONICAL | 2 | 8 | no | cloud_functions_adapter:CloudFunctionsAdapter.invoke | conne |
| `CloudFunctionsAdapter.list_functions` | cloud_functions_adapter | SUPERSET | 3 | 2 | no | connector_registry:ConnectorRegistry.list | connector_regist |
| `ConnectorRegistry.delete` | connector_registry | SUPERSET | 2 | 5 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `ConnectorRegistry.get_statistics` | connector_registry | SUPERSET | 4 | 3 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `ConnectorRegistry.list` | connector_registry | CANONICAL | 3 | 6 | no | datasource_model:DataSourceRegistry.list |
| `ConnectorsFacade.test_connector` | connectors_facade | SUPERSET | 4 | 5 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `ConnectorsFacade.update_connector` | connectors_facade | CANONICAL | 5 | 8 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `CostAnomaly.create` | cost_bridges_engine | SUPERSET | 3 | 4 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `CostEstimationProbe._find_cheaper_model` | cost_bridges_engine | SUPERSET | 2 | 4 | no | cost_bridges_engine:CostEstimationProbe._calculate_cost |
| `CostEstimationProbe.probe` | cost_bridges_engine | SUPERSET | 3 | 4 | no | cost_bridges_engine:CostEstimationProbe._calculate_cost | co |
| `CostLoopOrchestrator.process_anomaly` | cost_bridges_engine | CANONICAL | 3 | 14 | no | audit_schemas:PolicyActivationAudit.to_dict | channel_engine |
| `CostPatternMatcher._calculate_confidence` | cost_bridges_engine | SUPERSET | 3 | 4 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `CostRecoveryGenerator.generate_recovery` | cost_bridges_engine | SUPERSET | 2 | 4 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `CostRoutingAdjuster.on_cost_policy_created` | cost_bridges_engine | SUPERSET | 8 | 4 | no | cost_bridges_engine:CostRoutingAdjuster._create_budget_block |
| `CredentialService.get_credential` | service | SUPERSET | 2 | 1 | no | service:CredentialService._audit | vault:CredentialVault.get |
| `CredentialService.get_rotatable_credentials` | service | CANONICAL | 2 | 6 | no | service:CredentialService.list_credentials | vault:Credentia |
| `CusHealthService._perform_health_check` | cus_health_engine | SUPERSET | 14 | 16 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `CusHealthService.check_health` | cus_health_engine | SUPERSET | 3 | 2 | yes | cus_health_engine:CusHealthService._perform_health_check |
| `CusHealthService.get_health_summary` | cus_health_engine | SUPERSET | 2 | 2 | no | connector_registry:ConnectorRegistry.list | cus_health_engin |
| `CustomerActivityAdapter.get_activity` | customer_activity_adapter | CANONICAL | 3 | 5 | no | customer_activity_adapter:CustomerActivityAdapter._get_facad |
| `CustomerIncidentsAdapter.get_incident` | customer_incidents_adapter | CANONICAL | 1 | 7 | no | customer_incidents_adapter:_translate_severity | customer_in |
| `CustomerKeysAdapter.freeze_key` | customer_keys_adapter | SUPERSET | 2 | 5 | no | customer_keys_adapter:CustomerKeysAdapter.get_key |
| `CustomerKeysAdapter.unfreeze_key` | customer_keys_adapter | SUPERSET | 2 | 5 | no | customer_keys_adapter:CustomerKeysAdapter.get_key |
| `CustomerLogsAdapter.get_log` | customer_logs_adapter | CANONICAL | 2 | 10 | no | customer_logs_adapter:CustomerLogsAdapter._get_service | cus |
| `CustomerPoliciesAdapter.get_guardrail_detail` | customer_policies_adapter | CANONICAL | 3 | 5 | no | customer_logs_adapter:CustomerLogsAdapter._get_service | cus |
| `DataSourceRegistry.delete` | datasource_model | SUPERSET | 2 | 5 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `DataSourceRegistry.get_statistics` | datasource_model | SUPERSET | 5 | 3 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `DataSourceRegistry.list` | datasource_model | SUPERSET | 4 | 7 | no | connector_registry:ConnectorRegistry.list |
| `DataSourceRegistry.update` | datasource_model | CANONICAL | 5 | 8 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `DataSourcesFacade.list_sources` | datasources_facade | SUPERSET | 2 | 5 | no | connector_registry:ConnectorRegistry.list | datasource_model |
| `DataSourcesFacade.register_source` | datasources_facade | CANONICAL | 3 | 7 | no | bridges:BaseBridge.register | connector_registry:ConnectorRe |
| `DataSourcesFacade.update_source` | datasources_facade | SUPERSET | 3 | 5 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `EnvCredentialVault.get_credential` | vault | SUPERSET | 2 | 6 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `GCSAdapter.list_files` | gcs_adapter | SUPERSET | 3 | 2 | no | connector_registry:ConnectorRegistry.list | datasource_model |
| `GraduationEngine.compute` | graduation_engine | CANONICAL | 5 | 14 | no | graduation_engine:GraduationEngine._check_degradation | grad |
| `HashiCorpVault.get_credential` | vault | SUPERSET | 2 | 3 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `HashiCorpVault.get_metadata` | vault | SUPERSET | 2 | 5 | no | service:CredentialService.get_credential | vault:CredentialV |
| `HashiCorpVault.list_credentials` | vault | SUPERSET | 5 | 3 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `HashiCorpVault.update_credential` | vault | CANONICAL | 5 | 14 | no | service:CredentialService.get_credential | vault:CredentialV |
| `HttpConnectorService._get_auth_headers` | http_connector | SUPERSET | 5 | 4 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `HttpConnectorService.execute` | http_connector | CANONICAL | 9 | 6 | yes | connector_registry:ConnectorRegistry.delete | connector_regi |
| `IAMService.resolve_identity` | iam_engine | SUPERSET | 3 | 1 | no | iam_engine:IAMService._create_system_identity | iam_engine:I |
| `IncidentToCatalogBridge._calculate_fuzzy_confidence` | bridges | SUPERSET | 5 | 5 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `IncidentToCatalogBridge._find_matching_pattern` | bridges | SUPERSET | 4 | 1 | yes | bridges:IncidentToCatalogBridge._calculate_fuzzy_confidence  |
| `IncidentToCatalogBridge.process` | bridges | SUPERSET | 2 | 1 | no | audit_schemas:PolicyActivationAudit.to_dict | bridges:Incide |
| `IntegrationDispatcher._check_human_checkpoint_needed` | dispatcher | SUPERSET | 3 | 4 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `IntegrationDispatcher._execute_handlers` | dispatcher | SUPERSET | 2 | 5 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `IntegrationDispatcher._get_or_create_loop_status` | dispatcher | SUPERSET | 2 | 7 | no | dispatcher:IntegrationDispatcher._load_loop_status | dispatc |
| `IntegrationDispatcher._trigger_next_stage` | dispatcher | SUPERSET | 2 | 3 | no | loop_events:LoopEvent.create |
| `IntegrationDispatcher._update_loop_status` | dispatcher | SUPERSET | 8 | 6 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `IntegrationDispatcher.dispatch` | dispatcher | CANONICAL | 8 | 6 | yes | dispatcher:IntegrationDispatcher._check_db_idempotency | dis |
| `IntegrationDispatcher.resolve_checkpoint` | dispatcher | SUPERSET | 4 | 9 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `IntegrationDispatcher.retry_failed_stage` | dispatcher | SUPERSET | 2 | 8 | no | dispatcher:IntegrationDispatcher.dispatch | dispatcher:Integ |
| `IntegrationDispatcher.revert_loop` | dispatcher | SUPERSET | 3 | 9 | no | dispatcher:IntegrationDispatcher._persist_loop_status | disp |
| `LambdaAdapter.invoke` | lambda_adapter | SUPERSET | 6 | 2 | no | cloud_functions_adapter:CloudFunctionsAdapter.invoke | conne |
| `LambdaAdapter.invoke_batch` | lambda_adapter | CANONICAL | 2 | 8 | no | cloud_functions_adapter:CloudFunctionsAdapter.invoke | conne |
| `LambdaAdapter.list_functions` | lambda_adapter | SUPERSET | 4 | 2 | no | cloud_functions_adapter:CloudFunctionsAdapter.list_functions |
| `LoopStatus.to_console_display` | loop_events | SUPERSET | 3 | 4 | no | loop_events:LoopStatus._generate_narrative |
| `McpConnectorService._resolve_tool` | mcp_connector | SUPERSET | 2 | 3 | no | connector_registry:ConnectorRegistry.list | datasource_model |
| `McpConnectorService.execute` | mcp_connector | CANONICAL | 6 | 9 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `NotifyChannelService._send_via_channel` | channel_engine | SUPERSET | 6 | 3 | no | channel_engine:NotifyChannelService._send_email_notification |
| `NotifyChannelService.configure_channel` | channel_engine | SUPERSET | 2 | 6 | no | channel_engine:NotifyChannelConfig.is_configured |
| `NotifyChannelService.enable_channel` | channel_engine | SUPERSET | 2 | 7 | no | channel_engine:NotifyChannelConfig.is_configured | channel_e |
| `NotifyChannelService.get_enabled_channels` | channel_engine | SUPERSET | 4 | 4 | no | channel_engine:NotifyChannelConfig.is_configured | channel_e |
| `NotifyChannelService.send` | channel_engine | CANONICAL | 8 | 8 | no | channel_engine:NotifyChannelConfig.is_event_enabled | channe |
| `PGVectorAdapter.delete` | pgvector_adapter | SUPERSET | 9 | 2 | yes | http_connector:HttpConnectorService.execute | mcp_connector: |
| `PGVectorAdapter.query` | pgvector_adapter | CANONICAL | 9 | 2 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `PatternToRecoveryBridge._generate_recovery` | bridges | SUPERSET | 2 | 12 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `PatternToRecoveryBridge.process` | bridges | CANONICAL | 5 | 1 | no | audit_schemas:PolicyActivationAudit.to_dict | bridges:Patter |
| `PineconeAdapter.delete` | pinecone_adapter | CANONICAL | 4 | 2 | no | connector_registry:ConnectorRegistry.delete | datasource_mod |
| `PineconeAdapter.upsert` | pinecone_adapter | SUPERSET | 2 | 2 | no | pgvector_adapter:PGVectorAdapter.upsert | vector_stores_base |
| `PolicyToRoutingBridge.process` | bridges | SUPERSET | 5 | 1 | no | audit_schemas:PolicyActivationAudit.to_dict | bridges:Policy |
| `RecoveryToPolicyBridge._generate_policy` | bridges | SUPERSET | 2 | 8 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `RecoveryToPolicyBridge.process` | bridges | SUPERSET | 4 | 1 | no | audit_schemas:PolicyActivationAudit.to_dict | bridges:Patter |
| `RoutingAdjustment.check_kpi_regression` | loop_events | SUPERSET | 2 | 5 | no | loop_events:RoutingAdjustment.rollback |
| `S3Adapter.delete_many` | s3_adapter | SUPERSET | 2 | 3 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `S3Adapter.list_files` | s3_adapter | SUPERSET | 3 | 2 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `S3Adapter.upload` | s3_adapter | CANONICAL | 4 | 2 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `SMTPAdapter._build_email` | smtp_adapter | SUPERSET | 4 | 11 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `SMTPAdapter.send_batch` | smtp_adapter | CANONICAL | 1 | 7 | no | channel_engine:NotificationSender.send | channel_engine:Noti |
| `SlackAdapter._build_blocks` | slack_adapter | SUPERSET | 3 | 10 | no | slack_adapter:SlackAdapter._get_priority_emoji |
| `SlackAdapter.send` | slack_adapter | SUPERSET | 2 | 7 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `SlackAdapter.send_batch` | slack_adapter | CANONICAL | 2 | 8 | no | channel_engine:NotificationSender.send | channel_engine:Noti |
| `SlackAdapter.send_thread_reply` | slack_adapter | SUPERSET | 2 | 3 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `SqlGatewayService._coerce_parameter` | sql_gateway | SUPERSET | 23 | 2 | no | sql_gateway:SqlGatewayService._check_sql_injection |
| `SqlGatewayService._resolve_template` | sql_gateway | SUPERSET | 2 | 4 | no | connector_registry:ConnectorRegistry.list | datasource_model |
| `SqlGatewayService._validate_parameters` | sql_gateway | SUPERSET | 4 | 5 | no | connector_registry:ConnectorRegistry.list | datasource_model |
| `SqlGatewayService.execute` | sql_gateway | CANONICAL | 3 | 5 | no | cloud_functions_adapter:CloudFunctionsAdapter.connect | conn |
| `WeaviateAdapter.delete` | weaviate_adapter | CANONICAL | 7 | 2 | no | connector_registry:ConnectorRegistry.delete | connector_regi |
| `WeaviateAdapter.get_stats` | weaviate_adapter | SUPERSET | 3 | 2 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `WeaviateAdapter.list_namespaces` | weaviate_adapter | SUPERSET | 3 | 2 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `WeaviateAdapter.query` | weaviate_adapter | SUPERSET | 6 | 2 | no | connector_registry:ConnectorRegistry.get | datasource_model: |
| `WebhookAdapter._attempt_delivery` | webhook_adapter | SUPERSET | 2 | 3 | no | webhook_adapter:WebhookAdapter._sign_payload |
| `WebhookAdapter._deliver_with_retry` | webhook_adapter | SUPERSET | 3 | 4 | no | channel_engine:NotifyChannelConfig.record_failure | channel_ |
| `WebhookAdapter.send` | webhook_adapter | CANONICAL | 3 | 8 | no | webhook_adapter:WebhookAdapter._deliver_with_retry |
| `WebhookAdapter.send_batch` | webhook_adapter | SUPERSET | 2 | 8 | no | channel_engine:NotificationSender.send | channel_engine:Noti |
| `WorkerRegistryService.get_effective_worker_config` | worker_registry_driver | SUPERSET | 4 | 7 | no | datasource_model:DataSourceRegistry.update | worker_registry |
| `WorkerRegistryService.get_worker_details` | worker_registry_driver | CANONICAL | 4 | 10 | no | worker_registry_driver:WorkerRegistryService.get_worker_or_r |
| `WorkerRegistryService.get_workers_for_tenant` | worker_registry_driver | SUPERSET | 2 | 4 | no | worker_registry_driver:WorkerRegistryService.get_effective_w |
| `WorkerRegistryService.list_workers` | worker_registry_driver | SUPERSET | 2 | 5 | no | connector_registry:ConnectorRegistry.list | datasource_model |
| `ensure_json_serializable` | loop_events | CANONICAL | 7 | 8 | no | audit_schemas:PolicyActivationAudit.to_dict | channel_engine |
| `validate_prevention_for_graduation` | prevention_contract | SUPERSET | 5 | 5 | no | connector_registry:ConnectorRegistry.get | datasource_model: |

## Wrapper Inventory

_251 thin delegation functions._

- `iam_engine.AccessDecision.to_dict` → ?
- `bridges.BaseBridge.process` → ?
- `bridges.BaseBridge.register` → dispatcher:IntegrationDispatcher.register_handler
- `bridges.BaseBridge.stage` → ?
- `connector_registry.BaseConnector.connect` → ?
- `connector_registry.BaseConnector.disconnect` → ?
- `connector_registry.BaseConnector.health_check` → ?
- `graduation_engine.CapabilityGates.can_auto_activate_policy` → connector_registry:ConnectorRegistry.get
- `graduation_engine.CapabilityGates.can_auto_apply_recovery` → connector_registry:ConnectorRegistry.get
- `graduation_engine.CapabilityGates.can_full_auto_routing` → ?
- `cloud_functions_adapter.CloudFunctionsAdapter.function_exists` → cloud_functions_adapter:CloudFunctionsAdapter.get_function_info
- `graduation_engine.ComputedGraduationStatus.is_degraded` → ?
- `graduation_engine.ComputedGraduationStatus.is_graduated` → ?
- `loop_events.ConfidenceBand.allows_auto_apply` → ?
- `loop_events.ConfidenceBand.requires_human_review` → ?
- `loop_events.ConfidenceCalculator.should_auto_apply` → ?
- `connector_registry.ConnectorConfig.to_dict` → ?
- `connector_registry.ConnectorError.to_dict` → ?
- `connector_registry.ConnectorRegistry.__init__` → ?
- `connector_registry.ConnectorRegistry.get` → datasource_model:DataSourceRegistry.get
- `connector_registry.ConnectorRegistry.reset` → ?
- `connector_registry.ConnectorStats.to_dict` → ?
- `connectors_facade.ConnectorsFacade._get_capabilities_for_type` → connector_registry:ConnectorRegistry.get
- `cost_bridges_engine.CostAnomaly.to_dict` → ?
- `cost_bridges_engine.CostEstimationProbe.__init__` → ?
- `cost_bridges_engine.CostEstimationProbe._calculate_cost` → connector_registry:ConnectorRegistry.get
- `cost_bridges_engine.CostLoopBridge._map_severity_to_incident_severity` → connector_registry:ConnectorRegistry.get
- `cost_bridges_engine.CostPatternMatcher.__init__` → ?
- `cost_bridges_engine.CostPatternMatcher._build_signature` → cost_bridges_engine:CostPatternMatcher._deviation_bucket
- `cost_bridges_engine.CostPolicyGenerator.__init__` → ?
- _...and 221 more_

---

## PIN-504 Amendments (2026-01-31)

| Script | Change | Reference |
|--------|--------|-----------|
| `customer_logs_adapter` | Routes through `LogsCoordinator` (`hoc.cus.hoc_spine.orchestrator.coordinators.logs_coordinator`) instead of direct logs L5 import. | PIN-504 Phase 4 |

## PIN-507 Law 5 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| L4 `integrations_handler.py` | `IntegrationsQueryHandler`: Replaced `getattr()` dispatch with explicit map (10 methods). `IntegrationsConnectorsHandler`: Replaced `getattr()` dispatch with explicit map (6 methods). `IntegrationsDataSourcesHandler`: Replaced `getattr()` dispatch with explicit map (9 methods). Zero reflection in dispatch paths. | PIN-507 Law 5 |

## PIN-507 Law 0 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| `tests/test_m25_integration_loop.py` | Import of `IncidentToCatalogBridge`, `PatternToRecoveryBridge`, `RecoveryToPolicyBridge` rewired from abolished `app.integrations.L3_adapters` → `app.integrations.bridges`. L3 abolished per PIN-485. | PIN-507 Law 0 |
| `tests/test_m25_policy_overreach.py` | Import of `ConfidenceCalculator` rewired from abolished `app.integrations.L3_adapters` → `app.integrations.events`. L3 abolished per PIN-485. | PIN-507 Law 0 |
| `L5_engines/__init__.py` | Removed stale re-export of `learning_proof_engine` (16 symbols). Module moved to `policies/L5_engines/` during PIN-498 domain consolidation. | PIN-507 Law 0 |
| `L5_schemas/__init__.py` | Removed stale re-export of `cost_snapshot_schemas` (8 symbols). Module lives in `analytics/L5_schemas/`, wrong domain. | PIN-507 Law 0 |
| `L5_engines/cost_bridges_engine.py` | Fixed relative import `..schemas.loop_events` → absolute `app.hoc.cus.integrations.L5_schemas.loop_events`. | PIN-507 Law 0 |
| `L5_engines/credentials/__init__.py` | Stale relative import `.types` → absolute `app.hoc.cus.integrations.L5_engines.types`. `Credential` class lives in parent package `L5_engines/types.py`, not `credentials/types.py`. Detected by `check_init_hygiene.py` STALE_REEXPORT check. | PIN-507 Law 0 |

## PIN-508 Quarantine & Stub Actions (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| `L5_engines/_frozen/bridges_engine.py` | MOVED to `_frozen/` subdirectory from `L5_engines/` — M25_FROZEN quarantine (Phase 7). L5/L6 HYBRID removed from active production wiring. No exports from L5_engines __init__. | PIN-508 Phase 7 |
| `L5_engines/_frozen/dispatcher_engine.py` | MOVED to `_frozen/` subdirectory from `L5_engines/` — M25_FROZEN quarantine (Phase 7). L5/L6 HYBRID removed from active production wiring. No exports from L5_engines __init__. | PIN-508 Phase 7 |
| `L5_engines/_frozen/__init__.py` | NEW MARKER FILE — quarantine directory marker, no exports. Indicates M25_FROZEN hybrid engines removed from active wiring. | PIN-508 Phase 7 |
| `cus_integration_engine.py` | STUB_ENGINE marker added to indicate legacy stub (disconnected during PIN-498, now explicitly classified). | PIN-508 Phase 5 |

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`

## PIN-513 Topology Completion & Hygiene (2026-02-01)

### Phase 1C — Cross-Domain Duplicate Adapter Deletion

Three adapter files in `integrations/adapters/` were duplicates of files already living in their home domains. Zero HOC callers confirmed via grep before deletion.

| File | Change | Reference |
|------|--------|-----------|
| `adapters/customer_incidents_adapter.py` | **DELETED** — duplicate of `incidents/adapters/`. Zero HOC callers. | PIN-513 Phase 1C |
| `adapters/customer_logs_adapter.py` | **DELETED** — duplicate of `logs/adapters/`. Zero HOC callers. | PIN-513 Phase 1C |
| `adapters/customer_policies_adapter.py` | **DELETED** — duplicate of `policies/adapters/`. Zero HOC callers. | PIN-513 Phase 1C |

**Note:** The canonical adapters at `integrations/L5_engines/customer_*_adapter.py` remain intact — those are the active production copies. The deleted files were in the `adapters/` subdirectory (stale L3 remnants).

## PIN-510 Phase 0 — Per-Domain Bridges (2026-02-01)

### L4 hoc_spine Bridge Infrastructure (NEW)

**Location:** `hoc/cus/hoc_spine/orchestrator/coordinators/bridges/`

Phase 0A establishes per-domain bridge layer to eliminate monolithic DomainBridge god object. All adapters in integrations domain will rewire to these bridges during Phase 1A.

**Files Created:**

| File | Purpose | Capabilities | Reference |
|------|---------|--------------|-----------|
| `__init__.py` | Per-domain bridge package exports | — | PIN-510 Phase 0A |
| `incidents_bridge.py` | IncidentsBridge — incidents L5 capabilities | 3 (read, write, lessons) | PIN-510 Phase 0A |
| `controls_bridge.py` | ControlsBridge — controls L5 capabilities | 3 (limits_query, policy_limits, killswitch) | PIN-510 Phase 0A |
| `activity_bridge.py` | ActivityBridge — activity L5 capabilities | 1 (query) | PIN-510 Phase 0A |
| `policies_bridge.py` | PoliciesBridge — policies L5 capabilities | 1 (customer_policy_read) | PIN-510 Phase 0A |
| `api_keys_bridge.py` | ApiKeysBridge — api_keys L5 capabilities | 2 (keys_read, keys_write) | PIN-510 Phase 0A |
| `logs_bridge.py` | LogsBridge — logs L5 capabilities | 1 (read_service) | PIN-510 Phase 0A |

**Domain Coordinator Integration:** `domain_bridge.py` (L4 spine) modified to delegate per-domain bridge resolution.

**CI Hardening (2 new checks added to `scripts/ci/check_init_hygiene.py`):**

- Check 19: `check_bridge_method_count` — per-domain bridge max 5 capabilities
- Check 20: `check_schema_admission` — hoc/cus/hoc_spine/schemas/ files must have Consumers header

**Architecture Rules (L4 Spine Bridges):**

- Max 5 capability methods per bridge (enforced by CI check 19)
- Bridge never accepts session in constructor — returns session-bound capability
- Lazy imports only (no circular dependencies)
- Only L4 handlers and coordinators may use bridges
- All bridges serve ALL domains (spine layer, not domain-specific)

**Adoption Path (Phase 1A):**

Integrations adapters will rewire cross-domain L5 reads through these bridges:
- `customer_incidents_adapter` → incidents_bridge.incident_read_capability()
- `customer_logs_adapter` → logs_bridge.read_service_capability()
- `customer_policies_adapter` → policies_bridge.customer_policy_read_capability()
- `customer_activity_adapter` → activity_bridge.query_capability()
- `customer_keys_adapter` → api_keys_bridge.keys_read_capability() / keys_write_capability()

## PIN-513 Phase A — Integrations Domain Changes (2026-02-01)

- external_response_driver.py (L6): DELETED — zero callers, canonical replacement exists at app/services/external_response_service.py and app/hoc/int/platform/drivers/external_response_service.py
- bridges_engine.py (_frozen/L5): DELETED — helper functions unused, bridge classes wired elsewhere via app/integrations/bridges.py

## PIN-513 Phase 8 — Zero-Caller Wiring (2026-02-01)

| Component | L4 Owner | Action |
|-----------|----------|--------|
| `worker_registry_driver` (L6) | `hoc_spine/orchestrator/handlers/integrations_handler.py` | Added `IntegrationsWorkersHandler` class — dispatches 7 methods (`list_workers`, `get_worker`, `get_workers_for_tenant`, `is_available`, `get_effective_config`, `register_worker`, `update_status`) via `WorkerRegistryService(session)`. Registered as `integrations.workers` operation. |

## PIN-513 Phase 9 — Batch 1D Wiring (2026-02-01)

- Created `hoc_spine/orchestrator/handlers/integration_bootstrap_handler.py` (L4 handler)
- Wired 4 channel_engine symbols: `get_notify_service`, `send_notification`, `check_channel_health`, `get_channel_config`
- Reclassified `worker_registry_driver` as already WIRED via Phase 8 `IntegrationsWorkersHandler`
- Reclassified `bridges_engine` (2 symbols) as OUT_OF_SCOPE — lives in legacy `app/integrations/bridges.py`, not HOC
- Reclassified `external_response_driver` (3 symbols) as OUT_OF_SCOPE — lives in `hoc/int/`, not `hoc/cus/`
- All 10 CSV entries resolved: 5 WIRED, 2 OUT_OF_SCOPE (legacy), 3 OUT_OF_SCOPE (hoc/int/)

## PIN-517 cus_vault Authority Refactor (2026-02-03)

Establishes trust zone architecture for credential management with rule-based access control.

### Trust Zones

| Zone | Scope | Provider Source | env:// | Default Rule |
|------|-------|-----------------|--------|--------------|
| System | `scope="system"` | From env var | Allowed | Permissive |
| Customer | `scope="customer"` | Explicit in ref | **FORBIDDEN** | Fail-closed |

### Credential Reference Scheme (LOCKED)

```
cus-vault://<tenant_id>/<credential_id>
```

Valid providers (via env): `hashicorp`, `aws_secrets`

### Gap Fixes Applied

| Gap | Issue | Fix |
|-----|-------|-----|
| GAP-1 | Async boundary violation | Vault resolution async; rule check at L4 |
| GAP-2 | Ambiguous credential refs | Provider from env, tenant/cred explicit in ref |
| GAP-3 | Mutable accessor state | Accessor per-call, no instance state |
| GAP-4 | Permissive default | Fail-closed for customer scope |
| GAP-5 | AWS namespace collision | Include `{env}` in secret path |
| GAP-6 | No SDK contract test | SDK contract tests lock invariants |

### L5_vault Subsystem Files

| Layer | File | Canonical Function | Role |
|-------|------|-------------------|------|
| L5 | `L5_vault/engines/vault_rule_check.py` | `CredentialAccessRuleChecker.check_credential_access` | CANONICAL |
| L5 | `L5_vault/engines/service.py` | `CredentialService.get_credential` | CANONICAL |
| L6 | `L5_vault/drivers/vault.py` | `create_credential_vault` | CANONICAL |

### Security Invariants (Binding)

1. Customer scope NEVER falls back to env vault — explicit provider required
2. Rule check ALWAYS before vault access — at L4 orchestrator
3. Accessor context ALWAYS per-call — no mutable state
4. AWS secrets ALWAYS namespaced by environment — no staging/prod collision
5. Missing rule checker = access denied — fail-closed default

### CI Hardening

SDK contract tests: `tests/test_cus_vault_sdk_contract.py` (10 tests)

| Test Class | Coverage |
|------------|----------|
| `TestCusCredentialServiceContract` | SDK-level behavior |
| `TestVaultFactoryContract` | Factory behavior |
| `TestCredentialAccessRuleContract` | Rule enforcement |
| `TestCredentialReferenceFormat` | Format validation |

## PIN-518 Analytics Storage Follow-ups (2026-02-03)

Analytics storage wiring for canary reports and provenance logging.

### Completed

| Fix | Description | Files |
|-----|-------------|-------|
| Gap 1 | L2→L4 routing for `/canary/reports` | `analytics_handler.py`, `costsim.py` |
| Gap 2 | Split provenance/canary L6 drivers | `canary_report_driver.py` (NEW) |
| Gap 3 | Artifact-before-DB invariant | `canary_engine.py` |

### New Files

| Layer | File | Purpose |
|-------|------|---------|
| L6 | `analytics/L6_drivers/canary_report_driver.py` | Canary report persistence |
| L4 | `analytics_handler.py:CanaryReportHandler` | Route canary report queries |
| DB | `alembic/versions/121_add_costsim_canary_reports.py` | Migration for canary reports table |

### Deferred

- Index performance audit (low priority)
- Golden comparison implementation (needs design decision)
