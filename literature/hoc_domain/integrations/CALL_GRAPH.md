# Integrations — Call Graph

**Domain:** integrations  
**Total functions:** 646  
**Generator:** `scripts/ops/hoc_call_chain_tracer.py`

---

## Role Summary

| Role | Count | Description |
|------|-------|-------------|
| CANONICAL | 29 | Owns the algorithm — most decisions, primary logic |
| SUPERSET | 76 | Calls other functions + adds its own decisions |
| WRAPPER | 251 | Thin delegation — ≤3 stmts, no branching |
| LEAF | 163 | Terminal — calls no other domain functions |
| ENTRY | 49 | Entry point — no domain-internal callers |
| INTERNAL | 78 | Called only by other domain functions |

## Canonical Algorithm Owners

### `bridges.PatternToRecoveryBridge.process`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 1
- **Delegation depth:** 10
- **Persistence:** no
- **Chain:** bridges.PatternToRecoveryBridge.process → audit_schemas.PolicyActivationAudit.to_dict → bridges.PatternToRecoveryBridge._apply_recovery → bridges.PatternToRecoveryBridge._generate_recovery → ...+43
- **Calls:** audit_schemas:PolicyActivationAudit.to_dict, bridges:PatternToRecoveryBridge._apply_recovery, bridges:PatternToRecoveryBridge._generate_recovery, bridges:PatternToRecoveryBridge._instantiate_template, bridges:PatternToRecoveryBridge._load_pattern, bridges:PatternToRecoveryBridge._queue_for_review, bridges:RecoveryToPolicyBridge._load_pattern, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, connector_registry:BaseConnector.to_dict, connector_registry:ConnectorConfig.to_dict, connector_registry:ConnectorError.to_dict, connector_registry:ConnectorRegistry.get, connector_registry:ConnectorStats.to_dict, connector_registry:FileConnector.to_dict, connector_registry:ServerlessConnector.to_dict, connector_registry:VectorConnector.to_dict, connectors_facade:ConnectorInfo.to_dict, connectors_facade:TestResult.to_dict, cost_bridges_engine:CostAnomaly.to_dict, datasource_model:CustomerDataSource.to_dict, datasource_model:DataSourceConfig.to_dict, datasource_model:DataSourceError.to_dict, datasource_model:DataSourceRegistry.get, datasource_model:DataSourceStats.to_dict, datasources_facade:TestConnectionResult.to_dict, file_storage_base:FileMetadata.to_dict, iam_engine:AccessDecision.to_dict, iam_engine:Identity.to_dict, loop_events:ConfidenceBand.from_confidence, loop_events:LoopEvent.to_dict, loop_events:LoopStatus.to_dict, loop_events:PatternMatchResult.to_dict, loop_events:PolicyRule.to_dict, loop_events:RecoverySuggestion.to_dict, loop_events:RoutingAdjustment.to_dict, protocol:CredentialService.get, serverless_base:FunctionInfo.to_dict, serverless_base:InvocationRequest.to_dict, serverless_base:InvocationResult.to_dict, vector_stores_base:IndexStats.to_dict, vector_stores_base:QueryResult.to_dict, vector_stores_base:VectorRecord.to_dict, webhook_adapter:WebhookDelivery.to_dict

### `channel_engine.NotifyChannelService.send`
- **Layer:** L5
- **Decisions:** 8
- **Statements:** 8
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** channel_engine.NotifyChannelService.send → channel_engine.NotifyChannelConfig.is_event_enabled → channel_engine.NotifyChannelConfig.record_failure → channel_engine.NotifyChannelConfig.record_success → ...+7
- **Calls:** channel_engine:NotifyChannelConfig.is_event_enabled, channel_engine:NotifyChannelConfig.record_failure, channel_engine:NotifyChannelConfig.record_success, channel_engine:NotifyChannelService._send_ui_notification, channel_engine:NotifyChannelService._send_via_channel, channel_engine:NotifyChannelService.get_channel_config, channel_engine:NotifyChannelService.get_enabled_channels, channel_engine:get_channel_config, webhook_adapter:CircuitBreaker.record_failure, webhook_adapter:CircuitBreaker.record_success

### `cloud_functions_adapter.CloudFunctionsAdapter.invoke_batch`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 8
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** cloud_functions_adapter.CloudFunctionsAdapter.invoke_batch → cloud_functions_adapter.CloudFunctionsAdapter.invoke → connector_registry.ServerlessConnector.invoke → lambda_adapter.LambdaAdapter.invoke → ...+1
- **Calls:** cloud_functions_adapter:CloudFunctionsAdapter.invoke, connector_registry:ServerlessConnector.invoke, lambda_adapter:LambdaAdapter.invoke, serverless_base:ServerlessAdapter.invoke

### `connector_registry.ConnectorRegistry.list`
- **Layer:** L6
- **Decisions:** 3
- **Statements:** 6
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** connector_registry.ConnectorRegistry.list → datasource_model.DataSourceRegistry.list
- **Calls:** datasource_model:DataSourceRegistry.list

### `connectors_facade.ConnectorsFacade.update_connector`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 8
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** connectors_facade.ConnectorsFacade.update_connector → connector_registry.ConnectorRegistry.get → datasource_model.DataSourceRegistry.get → protocol.CredentialService.get
- **Calls:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `cost_bridges_engine.CostLoopOrchestrator.process_anomaly`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 14
- **Delegation depth:** 10
- **Persistence:** no
- **Chain:** cost_bridges_engine.CostLoopOrchestrator.process_anomaly → audit_schemas.PolicyActivationAudit.to_dict → channel_engine.NotifyChannelConfig.to_dict → channel_engine.NotifyChannelConfigResponse.to_dict → ...+38
- **Calls:** audit_schemas:PolicyActivationAudit.to_dict, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, connector_registry:BaseConnector.to_dict, connector_registry:ConnectorConfig.to_dict, connector_registry:ConnectorError.to_dict, connector_registry:ConnectorStats.to_dict, connector_registry:FileConnector.to_dict, connector_registry:ServerlessConnector.to_dict, connector_registry:VectorConnector.to_dict, connectors_facade:ConnectorInfo.to_dict, connectors_facade:TestResult.to_dict, cost_bridges_engine:CostAnomaly.to_dict, cost_bridges_engine:CostLoopBridge.on_anomaly_detected, cost_bridges_engine:CostPatternMatcher.match_cost_pattern, cost_bridges_engine:CostPolicyGenerator.generate_policy, cost_bridges_engine:CostRecoveryGenerator.generate_recovery, cost_bridges_engine:CostRoutingAdjuster.on_cost_policy_created, datasource_model:CustomerDataSource.to_dict, datasource_model:DataSourceConfig.to_dict, datasource_model:DataSourceError.to_dict, datasource_model:DataSourceStats.to_dict, datasources_facade:TestConnectionResult.to_dict, file_storage_base:FileMetadata.to_dict, iam_engine:AccessDecision.to_dict, iam_engine:Identity.to_dict, loop_events:LoopEvent.to_dict, loop_events:LoopStatus.to_dict, loop_events:PatternMatchResult.to_dict, loop_events:PolicyRule.to_dict, loop_events:RecoverySuggestion.to_dict, loop_events:RoutingAdjustment.to_dict, serverless_base:FunctionInfo.to_dict, serverless_base:InvocationRequest.to_dict, serverless_base:InvocationResult.to_dict, vector_stores_base:IndexStats.to_dict, vector_stores_base:QueryResult.to_dict, vector_stores_base:VectorRecord.to_dict, webhook_adapter:WebhookDelivery.to_dict

### `customer_activity_adapter.CustomerActivityAdapter.get_activity`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 5
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** customer_activity_adapter.CustomerActivityAdapter.get_activity → customer_activity_adapter.CustomerActivityAdapter._get_facade → customer_activity_adapter.CustomerActivityAdapter._to_customer_detail
- **Calls:** customer_activity_adapter:CustomerActivityAdapter._get_facade, customer_activity_adapter:CustomerActivityAdapter._to_customer_detail

### `customer_incidents_adapter.CustomerIncidentsAdapter.get_incident`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 7
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** customer_incidents_adapter.CustomerIncidentsAdapter.get_incident → customer_incidents_adapter._translate_severity → customer_incidents_adapter._translate_status
- **Calls:** customer_incidents_adapter:_translate_severity, customer_incidents_adapter:_translate_status

### `customer_logs_adapter.CustomerLogsAdapter.get_log`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 10
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** customer_logs_adapter.CustomerLogsAdapter.get_log → customer_logs_adapter.CustomerLogsAdapter._get_service → customer_policies_adapter.CustomerPoliciesAdapter._get_service
- **Calls:** customer_logs_adapter:CustomerLogsAdapter._get_service, customer_policies_adapter:CustomerPoliciesAdapter._get_service

### `customer_policies_adapter.CustomerPoliciesAdapter.get_guardrail_detail`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 5
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** customer_policies_adapter.CustomerPoliciesAdapter.get_guardrail_detail → customer_logs_adapter.CustomerLogsAdapter._get_service → customer_policies_adapter.CustomerPoliciesAdapter._get_service → customer_policies_adapter.CustomerPoliciesAdapter._to_customer_guardrail
- **Calls:** customer_logs_adapter:CustomerLogsAdapter._get_service, customer_policies_adapter:CustomerPoliciesAdapter._get_service, customer_policies_adapter:CustomerPoliciesAdapter._to_customer_guardrail

### `datasource_model.DataSourceRegistry.update`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 8
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** datasource_model.DataSourceRegistry.update → connector_registry.ConnectorRegistry.get → datasource_model.CustomerDataSource.update_config → datasource_model.DataSourceRegistry.get → ...+1
- **Calls:** connector_registry:ConnectorRegistry.get, datasource_model:CustomerDataSource.update_config, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `datasources_facade.DataSourcesFacade.register_source`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 7
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** datasources_facade.DataSourcesFacade.register_source → bridges.BaseBridge.register → connector_registry.ConnectorRegistry.get → connector_registry.ConnectorRegistry.register → ...+3
- **Calls:** bridges:BaseBridge.register, connector_registry:ConnectorRegistry.get, connector_registry:ConnectorRegistry.register, datasource_model:DataSourceRegistry.get, datasource_model:DataSourceRegistry.register, protocol:CredentialService.get

### `dispatcher.IntegrationDispatcher.dispatch`
- **Layer:** L5
- **Decisions:** 8
- **Statements:** 6
- **Delegation depth:** 11
- **Persistence:** yes
- **Chain:** dispatcher.IntegrationDispatcher.dispatch → dispatcher.IntegrationDispatcher._check_db_idempotency → dispatcher.IntegrationDispatcher._check_human_checkpoint_needed → dispatcher.IntegrationDispatcher._execute_handlers → ...+9
- **Calls:** dispatcher:IntegrationDispatcher._check_db_idempotency, dispatcher:IntegrationDispatcher._check_human_checkpoint_needed, dispatcher:IntegrationDispatcher._execute_handlers, dispatcher:IntegrationDispatcher._get_or_create_loop_status, dispatcher:IntegrationDispatcher._load_loop_status, dispatcher:IntegrationDispatcher._persist_checkpoint, dispatcher:IntegrationDispatcher._persist_event, dispatcher:IntegrationDispatcher._publish_checkpoint_needed, dispatcher:IntegrationDispatcher._publish_event, dispatcher:IntegrationDispatcher._trigger_next_stage, dispatcher:IntegrationDispatcher._update_loop_status, dispatcher:IntegrationDispatcher.is_bridge_enabled

### `graduation_engine.GraduationEngine.compute`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 14
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** graduation_engine.GraduationEngine.compute → graduation_engine.GraduationEngine._check_degradation → graduation_engine.GraduationEngine._evaluate_gate1 → graduation_engine.GraduationEngine._evaluate_gate2 → ...+1
- **Calls:** graduation_engine:GraduationEngine._check_degradation, graduation_engine:GraduationEngine._evaluate_gate1, graduation_engine:GraduationEngine._evaluate_gate2, graduation_engine:GraduationEngine._evaluate_gate3

### `http_connector.HttpConnectorService.execute`
- **Layer:** L5
- **Decisions:** 9
- **Statements:** 6
- **Delegation depth:** 9
- **Persistence:** yes
- **Chain:** http_connector.HttpConnectorService.execute → connector_registry.ConnectorRegistry.delete → connector_registry.ConnectorRegistry.get → datasource_model.DataSourceRegistry.delete → ...+16
- **Calls:** connector_registry:ConnectorRegistry.delete, connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.delete, datasource_model:DataSourceRegistry.get, file_storage_base:FileStorageAdapter.delete, gcs_adapter:GCSAdapter.delete, http_connector:HttpConnectorService._build_url, http_connector:HttpConnectorService._check_rate_limit, http_connector:HttpConnectorService._get_auth_headers, http_connector:HttpConnectorService._record_request, http_connector:HttpConnectorService._resolve_endpoint, mcp_connector:McpConnectorService._check_rate_limit, mcp_connector:McpConnectorService._record_request, pgvector_adapter:PGVectorAdapter.delete, pinecone_adapter:PineconeAdapter.delete, protocol:CredentialService.get, s3_adapter:S3Adapter.delete, vector_stores_base:VectorStoreAdapter.delete, weaviate_adapter:WeaviateAdapter.delete

### `lambda_adapter.LambdaAdapter.invoke_batch`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 8
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** lambda_adapter.LambdaAdapter.invoke_batch → cloud_functions_adapter.CloudFunctionsAdapter.invoke → connector_registry.ServerlessConnector.invoke → lambda_adapter.LambdaAdapter.invoke → ...+1
- **Calls:** cloud_functions_adapter:CloudFunctionsAdapter.invoke, connector_registry:ServerlessConnector.invoke, lambda_adapter:LambdaAdapter.invoke, serverless_base:ServerlessAdapter.invoke

### `loop_events.ensure_json_serializable`
- **Layer:** L5
- **Decisions:** 7
- **Statements:** 8
- **Delegation depth:** 10
- **Persistence:** no
- **Chain:** loop_events.ensure_json_serializable → audit_schemas.PolicyActivationAudit.to_dict → channel_engine.NotifyChannelConfig.to_dict → channel_engine.NotifyChannelConfigResponse.to_dict → ...+33
- **Calls:** audit_schemas:PolicyActivationAudit.to_dict, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, connector_registry:BaseConnector.to_dict, connector_registry:ConnectorConfig.to_dict, connector_registry:ConnectorError.to_dict, connector_registry:ConnectorStats.to_dict, connector_registry:FileConnector.to_dict, connector_registry:ServerlessConnector.to_dict, connector_registry:VectorConnector.to_dict, connectors_facade:ConnectorInfo.to_dict, connectors_facade:TestResult.to_dict, cost_bridges_engine:CostAnomaly.to_dict, datasource_model:CustomerDataSource.to_dict, datasource_model:DataSourceConfig.to_dict, datasource_model:DataSourceError.to_dict, datasource_model:DataSourceStats.to_dict, datasources_facade:TestConnectionResult.to_dict, file_storage_base:FileMetadata.to_dict, iam_engine:AccessDecision.to_dict, iam_engine:Identity.to_dict, loop_events:LoopEvent.to_dict, loop_events:LoopStatus.to_dict, loop_events:PatternMatchResult.to_dict, loop_events:PolicyRule.to_dict, loop_events:RecoverySuggestion.to_dict, loop_events:RoutingAdjustment.to_dict, serverless_base:FunctionInfo.to_dict, serverless_base:InvocationRequest.to_dict, serverless_base:InvocationResult.to_dict, vector_stores_base:IndexStats.to_dict, vector_stores_base:QueryResult.to_dict, vector_stores_base:VectorRecord.to_dict, webhook_adapter:WebhookDelivery.to_dict

### `mcp_connector.McpConnectorService.execute`
- **Layer:** L5
- **Decisions:** 6
- **Statements:** 9
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** mcp_connector.McpConnectorService.execute → connector_registry.ConnectorRegistry.get → datasource_model.DataSourceRegistry.get → http_connector.HttpConnectorService._check_rate_limit → ...+8
- **Calls:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, http_connector:HttpConnectorService._check_rate_limit, http_connector:HttpConnectorService._record_request, mcp_connector:McpConnectorService._build_mcp_request, mcp_connector:McpConnectorService._check_rate_limit, mcp_connector:McpConnectorService._get_api_key, mcp_connector:McpConnectorService._record_request, mcp_connector:McpConnectorService._resolve_tool, mcp_connector:McpConnectorService._validate_against_schema, protocol:CredentialService.get

### `pgvector_adapter.PGVectorAdapter.query`
- **Layer:** L5
- **Decisions:** 9
- **Statements:** 2
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** pgvector_adapter.PGVectorAdapter.query → connector_registry.ConnectorRegistry.get → datasource_model.DataSourceRegistry.get → protocol.CredentialService.get
- **Calls:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `pinecone_adapter.PineconeAdapter.delete`
- **Layer:** L5
- **Decisions:** 4
- **Statements:** 2
- **Delegation depth:** 8
- **Persistence:** no
- **Chain:** pinecone_adapter.PineconeAdapter.delete → connector_registry.ConnectorRegistry.delete → datasource_model.DataSourceRegistry.delete → file_storage_base.FileStorageAdapter.delete → ...+5
- **Calls:** connector_registry:ConnectorRegistry.delete, datasource_model:DataSourceRegistry.delete, file_storage_base:FileStorageAdapter.delete, gcs_adapter:GCSAdapter.delete, pgvector_adapter:PGVectorAdapter.delete, s3_adapter:S3Adapter.delete, vector_stores_base:VectorStoreAdapter.delete, weaviate_adapter:WeaviateAdapter.delete

### `s3_adapter.S3Adapter.upload`
- **Layer:** L5
- **Decisions:** 4
- **Statements:** 2
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** s3_adapter.S3Adapter.upload → connector_registry.ConnectorRegistry.get → datasource_model.DataSourceRegistry.get → protocol.CredentialService.get
- **Calls:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `service.CredentialService.get_rotatable_credentials`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 6
- **Delegation depth:** 5
- **Persistence:** no
- **Chain:** service.CredentialService.get_rotatable_credentials → service.CredentialService.list_credentials → vault.CredentialVault.list_credentials → vault.EnvCredentialVault.list_credentials → ...+1
- **Calls:** service:CredentialService.list_credentials, vault:CredentialVault.list_credentials, vault:EnvCredentialVault.list_credentials, vault:HashiCorpVault.list_credentials

### `slack_adapter.SlackAdapter.send_batch`
- **Layer:** L5
- **Decisions:** 2
- **Statements:** 8
- **Delegation depth:** 8
- **Persistence:** no
- **Chain:** slack_adapter.SlackAdapter.send_batch → channel_engine.NotificationSender.send → channel_engine.NotifyChannelService.send → slack_adapter.SlackAdapter.send → ...+2
- **Calls:** channel_engine:NotificationSender.send, channel_engine:NotifyChannelService.send, slack_adapter:SlackAdapter.send, smtp_adapter:SMTPAdapter.send, webhook_adapter:WebhookAdapter.send

### `smtp_adapter.SMTPAdapter.send_batch`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 7
- **Delegation depth:** 8
- **Persistence:** no
- **Chain:** smtp_adapter.SMTPAdapter.send_batch → channel_engine.NotificationSender.send → channel_engine.NotifyChannelService.send → slack_adapter.SlackAdapter.send → ...+2
- **Calls:** channel_engine:NotificationSender.send, channel_engine:NotifyChannelService.send, slack_adapter:SlackAdapter.send, smtp_adapter:SMTPAdapter.send, webhook_adapter:WebhookAdapter.send

### `sql_gateway.SqlGatewayService.execute`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 5
- **Delegation depth:** 7
- **Persistence:** no
- **Chain:** sql_gateway.SqlGatewayService.execute → cloud_functions_adapter.CloudFunctionsAdapter.connect → connector_registry.BaseConnector.connect → connector_registry.ConnectorRegistry.get → ...+20
- **Calls:** cloud_functions_adapter:CloudFunctionsAdapter.connect, connector_registry:BaseConnector.connect, connector_registry:ConnectorRegistry.get, connector_registry:FileConnector.connect, connector_registry:ServerlessConnector.connect, connector_registry:VectorConnector.connect, datasource_model:DataSourceRegistry.get, file_storage_base:FileStorageAdapter.connect, gcs_adapter:GCSAdapter.connect, lambda_adapter:LambdaAdapter.connect, pgvector_adapter:PGVectorAdapter.connect, pinecone_adapter:PineconeAdapter.connect, protocol:CredentialService.get, s3_adapter:S3Adapter.connect, serverless_base:ServerlessAdapter.connect, slack_adapter:SlackAdapter.connect, smtp_adapter:SMTPAdapter.connect, sql_gateway:SqlGatewayService._get_connection_string, sql_gateway:SqlGatewayService._resolve_template, sql_gateway:SqlGatewayService._validate_parameters, vector_stores_base:VectorStoreAdapter.connect, weaviate_adapter:WeaviateAdapter.connect, webhook_adapter:WebhookAdapter.connect

### `vault.HashiCorpVault.update_credential`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 14
- **Delegation depth:** 4
- **Persistence:** no
- **Chain:** vault.HashiCorpVault.update_credential → service.CredentialService.get_credential → vault.CredentialVault.get_credential → vault.EnvCredentialVault.get_credential → ...+1
- **Calls:** service:CredentialService.get_credential, vault:CredentialVault.get_credential, vault:EnvCredentialVault.get_credential, vault:HashiCorpVault.get_credential

### `weaviate_adapter.WeaviateAdapter.delete`
- **Layer:** L5
- **Decisions:** 7
- **Statements:** 2
- **Delegation depth:** 8
- **Persistence:** no
- **Chain:** weaviate_adapter.WeaviateAdapter.delete → connector_registry.ConnectorRegistry.delete → connector_registry.ConnectorRegistry.get → datasource_model.DataSourceRegistry.delete → ...+10
- **Calls:** connector_registry:ConnectorRegistry.delete, connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.delete, datasource_model:DataSourceRegistry.get, file_storage_base:FileStorageAdapter.delete, gcs_adapter:GCSAdapter.delete, pgvector_adapter:PGVectorAdapter.delete, pinecone_adapter:PineconeAdapter.delete, protocol:CredentialService.get, s3_adapter:S3Adapter.delete, vector_stores_base:VectorStoreAdapter.delete, weaviate_adapter:WeaviateAdapter._build_filter, weaviate_adapter:WeaviateAdapter._create_collection

### `webhook_adapter.WebhookAdapter.send`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 8
- **Delegation depth:** 3
- **Persistence:** no
- **Chain:** webhook_adapter.WebhookAdapter.send → webhook_adapter.WebhookAdapter._deliver_with_retry
- **Calls:** webhook_adapter:WebhookAdapter._deliver_with_retry

### `worker_registry_driver.WorkerRegistryService.get_worker_details`
- **Layer:** L6
- **Decisions:** 4
- **Statements:** 10
- **Delegation depth:** 5
- **Persistence:** no
- **Chain:** worker_registry_driver.WorkerRegistryService.get_worker_details → worker_registry_driver.WorkerRegistryService.get_worker_or_raise
- **Calls:** worker_registry_driver:WorkerRegistryService.get_worker_or_raise

## Supersets (orchestrating functions)

### `bridges.IncidentToCatalogBridge._calculate_fuzzy_confidence`
- **Decisions:** 5, **Statements:** 5
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `bridges.IncidentToCatalogBridge._find_matching_pattern`
- **Decisions:** 4, **Statements:** 1
- **Subsumes:** bridges:IncidentToCatalogBridge._calculate_fuzzy_confidence, bridges:IncidentToCatalogBridge._create_pattern, bridges:IncidentToCatalogBridge._increment_pattern_count, connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, http_connector:HttpConnectorService.execute, loop_events:PatternMatchResult.from_match, loop_events:PatternMatchResult.no_match, mcp_connector:McpConnectorService.execute, protocol:CredentialService.get, sql_gateway:SqlGatewayService.execute

### `bridges.IncidentToCatalogBridge.process`
- **Decisions:** 2, **Statements:** 1
- **Subsumes:** audit_schemas:PolicyActivationAudit.to_dict, bridges:IncidentToCatalogBridge._extract_signature, bridges:IncidentToCatalogBridge._find_matching_pattern, bridges:IncidentToCatalogBridge._hash_signature, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, connector_registry:BaseConnector.to_dict, connector_registry:ConnectorConfig.to_dict, connector_registry:ConnectorError.to_dict, connector_registry:ConnectorRegistry.get, connector_registry:ConnectorStats.to_dict, connector_registry:FileConnector.to_dict, connector_registry:ServerlessConnector.to_dict, connector_registry:VectorConnector.to_dict, connectors_facade:ConnectorInfo.to_dict, connectors_facade:TestResult.to_dict, cost_bridges_engine:CostAnomaly.to_dict, cost_bridges_engine:CostPatternMatcher._hash_signature, datasource_model:CustomerDataSource.to_dict, datasource_model:DataSourceConfig.to_dict, datasource_model:DataSourceError.to_dict, datasource_model:DataSourceRegistry.get, datasource_model:DataSourceStats.to_dict, datasources_facade:TestConnectionResult.to_dict, file_storage_base:FileMetadata.to_dict, iam_engine:AccessDecision.to_dict, iam_engine:Identity.to_dict, loop_events:LoopEvent.to_dict, loop_events:LoopStatus.to_dict, loop_events:PatternMatchResult.to_dict, loop_events:PolicyRule.to_dict, loop_events:RecoverySuggestion.to_dict, loop_events:RoutingAdjustment.to_dict, protocol:CredentialService.get, serverless_base:FunctionInfo.to_dict, serverless_base:InvocationRequest.to_dict, serverless_base:InvocationResult.to_dict, vector_stores_base:IndexStats.to_dict, vector_stores_base:QueryResult.to_dict, vector_stores_base:VectorRecord.to_dict, webhook_adapter:WebhookDelivery.to_dict

### `bridges.PatternToRecoveryBridge._generate_recovery`
- **Decisions:** 2, **Statements:** 12
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, loop_events:ConfidenceCalculator.calculate_recovery_confidence, loop_events:ConfidenceCalculator.get_confirmation_level, loop_events:ConfidenceCalculator.should_auto_apply, loop_events:RecoverySuggestion.create, protocol:CredentialService.get

### `bridges.PolicyToRoutingBridge.process`
- **Decisions:** 5, **Statements:** 1
- **Subsumes:** audit_schemas:PolicyActivationAudit.to_dict, bridges:PolicyToRoutingBridge._create_adjustment, bridges:PolicyToRoutingBridge._identify_affected_agents, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, connector_registry:BaseConnector.to_dict, connector_registry:ConnectorConfig.to_dict, connector_registry:ConnectorError.to_dict, connector_registry:ConnectorRegistry.get, connector_registry:ConnectorStats.to_dict, connector_registry:FileConnector.to_dict, connector_registry:ServerlessConnector.to_dict, connector_registry:VectorConnector.to_dict, connectors_facade:ConnectorInfo.to_dict, connectors_facade:TestResult.to_dict, cost_bridges_engine:CostAnomaly.to_dict, datasource_model:CustomerDataSource.to_dict, datasource_model:DataSourceConfig.to_dict, datasource_model:DataSourceError.to_dict, datasource_model:DataSourceRegistry.get, datasource_model:DataSourceStats.to_dict, datasources_facade:TestConnectionResult.to_dict, file_storage_base:FileMetadata.to_dict, iam_engine:AccessDecision.to_dict, iam_engine:Identity.to_dict, loop_events:ConfidenceBand.from_confidence, loop_events:LoopEvent.to_dict, loop_events:LoopStatus.to_dict, loop_events:PatternMatchResult.to_dict, loop_events:PolicyRule.to_dict, loop_events:RecoverySuggestion.to_dict, loop_events:RoutingAdjustment.to_dict, protocol:CredentialService.get, serverless_base:FunctionInfo.to_dict, serverless_base:InvocationRequest.to_dict, serverless_base:InvocationResult.to_dict, vector_stores_base:IndexStats.to_dict, vector_stores_base:QueryResult.to_dict, vector_stores_base:VectorRecord.to_dict, webhook_adapter:WebhookDelivery.to_dict

### `bridges.RecoveryToPolicyBridge._generate_policy`
- **Decisions:** 2, **Statements:** 8
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, loop_events:PolicyRule.create, protocol:CredentialService.get

### `bridges.RecoveryToPolicyBridge.process`
- **Decisions:** 4, **Statements:** 1
- **Subsumes:** audit_schemas:PolicyActivationAudit.to_dict, bridges:PatternToRecoveryBridge._load_pattern, bridges:RecoveryToPolicyBridge._generate_policy, bridges:RecoveryToPolicyBridge._load_pattern, bridges:RecoveryToPolicyBridge._persist_policy, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, connector_registry:BaseConnector.to_dict, connector_registry:ConnectorConfig.to_dict, connector_registry:ConnectorError.to_dict, connector_registry:ConnectorRegistry.get, connector_registry:ConnectorStats.to_dict, connector_registry:FileConnector.to_dict, connector_registry:ServerlessConnector.to_dict, connector_registry:VectorConnector.to_dict, connectors_facade:ConnectorInfo.to_dict, connectors_facade:TestResult.to_dict, cost_bridges_engine:CostAnomaly.to_dict, datasource_model:CustomerDataSource.to_dict, datasource_model:DataSourceConfig.to_dict, datasource_model:DataSourceError.to_dict, datasource_model:DataSourceRegistry.get, datasource_model:DataSourceStats.to_dict, datasources_facade:TestConnectionResult.to_dict, file_storage_base:FileMetadata.to_dict, iam_engine:AccessDecision.to_dict, iam_engine:Identity.to_dict, loop_events:ConfidenceBand.from_confidence, loop_events:LoopEvent.to_dict, loop_events:LoopStatus.to_dict, loop_events:PatternMatchResult.to_dict, loop_events:PolicyRule.to_dict, loop_events:RecoverySuggestion.to_dict, loop_events:RoutingAdjustment.to_dict, protocol:CredentialService.get, serverless_base:FunctionInfo.to_dict, serverless_base:InvocationRequest.to_dict, serverless_base:InvocationResult.to_dict, vector_stores_base:IndexStats.to_dict, vector_stores_base:QueryResult.to_dict, vector_stores_base:VectorRecord.to_dict, webhook_adapter:WebhookDelivery.to_dict

### `channel_engine.NotifyChannelService._send_via_channel`
- **Decisions:** 6, **Statements:** 3
- **Subsumes:** channel_engine:NotifyChannelService._send_email_notification, channel_engine:NotifyChannelService._send_pagerduty_notification, channel_engine:NotifyChannelService._send_slack_notification, channel_engine:NotifyChannelService._send_teams_notification, channel_engine:NotifyChannelService._send_ui_notification, channel_engine:NotifyChannelService._send_webhook_notification

### `channel_engine.NotifyChannelService.configure_channel`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** channel_engine:NotifyChannelConfig.is_configured

### `channel_engine.NotifyChannelService.enable_channel`
- **Decisions:** 2, **Statements:** 7
- **Subsumes:** channel_engine:NotifyChannelConfig.is_configured, channel_engine:NotifyChannelService.get_channel_config, channel_engine:get_channel_config, connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list

### `channel_engine.NotifyChannelService.get_enabled_channels`
- **Decisions:** 4, **Statements:** 4
- **Subsumes:** channel_engine:NotifyChannelConfig.is_configured, channel_engine:NotifyChannelConfig.is_event_enabled, connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list

### `cloud_functions_adapter.CloudFunctionsAdapter.invoke`
- **Decisions:** 6, **Statements:** 2
- **Subsumes:** cloud_functions_adapter:CloudFunctionsAdapter.get_function_info, connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, lambda_adapter:LambdaAdapter.get_function_info, protocol:CredentialService.get, serverless_base:ServerlessAdapter.get_function_info

### `cloud_functions_adapter.CloudFunctionsAdapter.list_functions`
- **Decisions:** 3, **Statements:** 2
- **Subsumes:** connector_registry:ConnectorRegistry.list, connector_registry:ServerlessConnector.list_functions, datasource_model:DataSourceRegistry.list, lambda_adapter:LambdaAdapter.list_functions, serverless_base:ServerlessAdapter.list_functions

### `connector_registry.ConnectorRegistry.delete`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `connector_registry.ConnectorRegistry.get_statistics`
- **Decisions:** 4, **Statements:** 3
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `connectors_facade.ConnectorsFacade.test_connector`
- **Decisions:** 4, **Statements:** 5
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `cost_bridges_engine.CostAnomaly.create`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `cost_bridges_engine.CostEstimationProbe._find_cheaper_model`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** cost_bridges_engine:CostEstimationProbe._calculate_cost

### `cost_bridges_engine.CostEstimationProbe.probe`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** cost_bridges_engine:CostEstimationProbe._calculate_cost, cost_bridges_engine:CostEstimationProbe._find_cheaper_model

### `cost_bridges_engine.CostPatternMatcher._calculate_confidence`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `cost_bridges_engine.CostRecoveryGenerator.generate_recovery`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, loop_events:RecoverySuggestion.create, protocol:CredentialService.get

### `cost_bridges_engine.CostRoutingAdjuster.on_cost_policy_created`
- **Decisions:** 8, **Statements:** 4
- **Subsumes:** cost_bridges_engine:CostRoutingAdjuster._create_budget_block_adjustment, cost_bridges_engine:CostRoutingAdjuster._create_escalation_adjustment, cost_bridges_engine:CostRoutingAdjuster._create_model_routing_adjustment, cost_bridges_engine:CostRoutingAdjuster._create_notify_adjustment, cost_bridges_engine:CostRoutingAdjuster._create_rate_limit_adjustment, cost_bridges_engine:CostRoutingAdjuster._create_review_adjustment, cost_bridges_engine:CostRoutingAdjuster._create_throttle_adjustment, cost_bridges_engine:CostRoutingAdjuster._create_token_limit_adjustment

### `cus_health_engine.CusHealthService._perform_health_check`
- **Decisions:** 14, **Statements:** 16
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, datasource_model:DataSourceRegistry.update, protocol:CredentialService.get

### `cus_health_engine.CusHealthService.check_health`
- **Decisions:** 3, **Statements:** 2
- **Subsumes:** cus_health_engine:CusHealthService._perform_health_check

### `cus_health_engine.CusHealthService.get_health_summary`
- **Decisions:** 2, **Statements:** 2
- **Subsumes:** connector_registry:ConnectorRegistry.list, cus_health_engine:CusHealthService._calculate_overall_health, datasource_model:DataSourceRegistry.list

### `customer_keys_adapter.CustomerKeysAdapter.freeze_key`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** customer_keys_adapter:CustomerKeysAdapter.get_key

### `customer_keys_adapter.CustomerKeysAdapter.unfreeze_key`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** customer_keys_adapter:CustomerKeysAdapter.get_key

### `datasource_model.DataSourceRegistry.delete`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `datasource_model.DataSourceRegistry.get_statistics`
- **Decisions:** 5, **Statements:** 3
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `datasource_model.DataSourceRegistry.list`
- **Decisions:** 4, **Statements:** 7
- **Subsumes:** connector_registry:ConnectorRegistry.list

### `datasources_facade.DataSourcesFacade.list_sources`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list

### `datasources_facade.DataSourcesFacade.update_source`
- **Decisions:** 3, **Statements:** 5
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, datasource_model:DataSourceRegistry.update, protocol:CredentialService.get

### `dispatcher.IntegrationDispatcher._check_human_checkpoint_needed`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, loop_events:HumanCheckpoint.create, protocol:CredentialService.get

### `dispatcher.IntegrationDispatcher._execute_handlers`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `dispatcher.IntegrationDispatcher._get_or_create_loop_status`
- **Decisions:** 2, **Statements:** 7
- **Subsumes:** dispatcher:IntegrationDispatcher._load_loop_status, dispatcher:IntegrationDispatcher._persist_loop_status

### `dispatcher.IntegrationDispatcher._trigger_next_stage`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** loop_events:LoopEvent.create

### `dispatcher.IntegrationDispatcher._update_loop_status`
- **Decisions:** 8, **Statements:** 6
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, dispatcher:IntegrationDispatcher._persist_loop_status, protocol:CredentialService.get

### `dispatcher.IntegrationDispatcher.resolve_checkpoint`
- **Decisions:** 4, **Statements:** 9
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, dispatcher:IntegrationDispatcher._load_checkpoint, dispatcher:IntegrationDispatcher._persist_checkpoint, dispatcher:IntegrationDispatcher.dispatch, loop_events:HumanCheckpoint.resolve, loop_events:LoopEvent.create, protocol:CredentialService.get

### `dispatcher.IntegrationDispatcher.retry_failed_stage`
- **Decisions:** 2, **Statements:** 8
- **Subsumes:** dispatcher:IntegrationDispatcher.dispatch, dispatcher:IntegrationDispatcher.get_loop_status, loop_events:LoopEvent.create

### `dispatcher.IntegrationDispatcher.revert_loop`
- **Decisions:** 3, **Statements:** 9
- **Subsumes:** dispatcher:IntegrationDispatcher._persist_loop_status, dispatcher:IntegrationDispatcher.get_loop_status, loop_events:RoutingAdjustment.rollback

### `gcs_adapter.GCSAdapter.list_files`
- **Decisions:** 3, **Statements:** 2
- **Subsumes:** connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list

### `graduation_engine.CapabilityGates.get_blocked_capabilities`
- **Decisions:** 3, **Statements:** 5
- **Subsumes:** graduation_engine:CapabilityGates.can_auto_activate_policy, graduation_engine:CapabilityGates.can_auto_apply_recovery, graduation_engine:CapabilityGates.can_full_auto_routing

### `graduation_engine.CapabilityGates.get_unlocked_capabilities`
- **Decisions:** 3, **Statements:** 5
- **Subsumes:** graduation_engine:CapabilityGates.can_auto_activate_policy, graduation_engine:CapabilityGates.can_auto_apply_recovery, graduation_engine:CapabilityGates.can_full_auto_routing

### `http_connector.HttpConnectorService._get_auth_headers`
- **Decisions:** 5, **Statements:** 4
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `iam_engine.IAMService.resolve_identity`
- **Decisions:** 3, **Statements:** 1
- **Subsumes:** iam_engine:IAMService._create_system_identity, iam_engine:IAMService._resolve_api_key_identity, iam_engine:IAMService._resolve_clerk_identity

### `lambda_adapter.LambdaAdapter.invoke`
- **Decisions:** 6, **Statements:** 2
- **Subsumes:** cloud_functions_adapter:CloudFunctionsAdapter.invoke, connector_registry:ConnectorRegistry.get, connector_registry:ServerlessConnector.invoke, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get, serverless_base:ServerlessAdapter.invoke

### `lambda_adapter.LambdaAdapter.list_functions`
- **Decisions:** 4, **Statements:** 2
- **Subsumes:** cloud_functions_adapter:CloudFunctionsAdapter.list_functions, connector_registry:ConnectorRegistry.get, connector_registry:ServerlessConnector.list_functions, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get, serverless_base:ServerlessAdapter.list_functions

### `loop_events.LoopStatus.to_console_display`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** loop_events:LoopStatus._generate_narrative

### `loop_events.RoutingAdjustment.check_kpi_regression`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** loop_events:RoutingAdjustment.rollback

### `mcp_connector.McpConnectorService._resolve_tool`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list

### `pgvector_adapter.PGVectorAdapter.delete`
- **Decisions:** 9, **Statements:** 2
- **Subsumes:** http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute

### `pinecone_adapter.PineconeAdapter.upsert`
- **Decisions:** 2, **Statements:** 2
- **Subsumes:** pgvector_adapter:PGVectorAdapter.upsert, vector_stores_base:VectorStoreAdapter.upsert, weaviate_adapter:WeaviateAdapter.upsert

### `prevention_contract.validate_prevention_for_graduation`
- **Decisions:** 5, **Statements:** 5
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `s3_adapter.S3Adapter.delete_many`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `s3_adapter.S3Adapter.list_files`
- **Decisions:** 3, **Statements:** 2
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `service.CredentialService.get_credential`
- **Decisions:** 2, **Statements:** 1
- **Subsumes:** service:CredentialService._audit, vault:CredentialVault.get_credential, vault:EnvCredentialVault.get_credential, vault:HashiCorpVault.get_credential

### `slack_adapter.SlackAdapter._build_blocks`
- **Decisions:** 3, **Statements:** 10
- **Subsumes:** slack_adapter:SlackAdapter._get_priority_emoji

### `slack_adapter.SlackAdapter.send`
- **Decisions:** 2, **Statements:** 7
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get, slack_adapter:SlackAdapter._build_blocks

### `slack_adapter.SlackAdapter.send_thread_reply`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `smtp_adapter.SMTPAdapter._build_email`
- **Decisions:** 4, **Statements:** 11
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `sql_gateway.SqlGatewayService._coerce_parameter`
- **Decisions:** 23, **Statements:** 2
- **Subsumes:** sql_gateway:SqlGatewayService._check_sql_injection

### `sql_gateway.SqlGatewayService._resolve_template`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list

### `sql_gateway.SqlGatewayService._validate_parameters`
- **Decisions:** 4, **Statements:** 5
- **Subsumes:** connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list, sql_gateway:SqlGatewayService._coerce_parameter

### `vault.EnvCredentialVault.get_credential`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `vault.HashiCorpVault.get_credential`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `vault.HashiCorpVault.get_metadata`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** service:CredentialService.get_credential, vault:CredentialVault.get_credential, vault:EnvCredentialVault.get_credential, vault:HashiCorpVault.get_credential

### `vault.HashiCorpVault.list_credentials`
- **Decisions:** 5, **Statements:** 3
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, file_storage_base:FileStorageAdapter.get_metadata, gcs_adapter:GCSAdapter.get_metadata, protocol:CredentialService.get, s3_adapter:S3Adapter.get_metadata, vault:CredentialVault.get_metadata, vault:EnvCredentialVault.get_metadata, vault:HashiCorpVault.get_metadata

### `weaviate_adapter.WeaviateAdapter.get_stats`
- **Decisions:** 3, **Statements:** 2
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `weaviate_adapter.WeaviateAdapter.list_namespaces`
- **Decisions:** 3, **Statements:** 2
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get

### `weaviate_adapter.WeaviateAdapter.query`
- **Decisions:** 6, **Statements:** 2
- **Subsumes:** connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get, weaviate_adapter:WeaviateAdapter._build_filter

### `webhook_adapter.WebhookAdapter._attempt_delivery`
- **Decisions:** 2, **Statements:** 3
- **Subsumes:** webhook_adapter:WebhookAdapter._sign_payload

### `webhook_adapter.WebhookAdapter._deliver_with_retry`
- **Decisions:** 3, **Statements:** 4
- **Subsumes:** channel_engine:NotifyChannelConfig.record_failure, channel_engine:NotifyChannelConfig.record_success, webhook_adapter:CircuitBreaker.can_execute, webhook_adapter:CircuitBreaker.record_failure, webhook_adapter:CircuitBreaker.record_success, webhook_adapter:WebhookAdapter._attempt_delivery, webhook_adapter:WebhookAdapter._get_circuit_breaker

### `webhook_adapter.WebhookAdapter.send_batch`
- **Decisions:** 2, **Statements:** 8
- **Subsumes:** channel_engine:NotificationSender.send, channel_engine:NotifyChannelService.send, slack_adapter:SlackAdapter.send, smtp_adapter:SMTPAdapter.send, webhook_adapter:WebhookAdapter.send

### `worker_registry_driver.WorkerRegistryService.get_effective_worker_config`
- **Decisions:** 4, **Statements:** 7
- **Subsumes:** datasource_model:DataSourceRegistry.update, worker_registry_driver:WorkerRegistryService.get_tenant_worker_config, worker_registry_driver:WorkerRegistryService.get_worker_or_raise

### `worker_registry_driver.WorkerRegistryService.get_workers_for_tenant`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** worker_registry_driver:WorkerRegistryService.get_effective_worker_config, worker_registry_driver:WorkerRegistryService.list_available_workers

### `worker_registry_driver.WorkerRegistryService.list_workers`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list

## Wrappers (thin delegation)

- `audit_schemas.PolicyActivationAudit.to_dict` → ?
- `bridges.BaseBridge.process` → ?
- `bridges.BaseBridge.register` → dispatcher:IntegrationDispatcher.register_handler
- `bridges.BaseBridge.stage` → ?
- `bridges.IncidentToCatalogBridge.__init__` → ?
- `bridges.IncidentToCatalogBridge._increment_pattern_count` → http_connector:HttpConnectorService.execute
- `bridges.IncidentToCatalogBridge.stage` → ?
- `bridges.LoopStatusBridge.__init__` → ?
- `bridges.LoopStatusBridge._push_sse_update` → ?
- `bridges.LoopStatusBridge.stage` → ?
- `bridges.PatternToRecoveryBridge.__init__` → ?
- `bridges.PatternToRecoveryBridge.stage` → ?
- `bridges.PolicyToRoutingBridge.__init__` → ?
- `bridges.PolicyToRoutingBridge.stage` → ?
- `bridges.RecoveryToPolicyBridge.__init__` → ?
- `bridges.RecoveryToPolicyBridge.stage` → ?
- `bridges._check_frozen` → ?
- `channel_engine.NotificationSender.send` → ?
- `channel_engine.NotifyChannelConfig.is_event_enabled` → ?
- `channel_engine.NotifyChannelConfig.record_failure` → ?
- `channel_engine.NotifyChannelConfig.record_success` → ?
- `channel_engine.NotifyChannelConfigResponse.to_dict` → ?
- `channel_engine.NotifyChannelError.to_dict` → ?
- `channel_engine.NotifyChannelService.__init__` → ?
- `channel_engine.NotifyChannelService.get_all_configs` → connector_registry:ConnectorRegistry.get
- `channel_engine.NotifyDeliveryResult.to_dict` → ?
- `channel_engine._reset_notify_service` → ?
- `channel_engine.check_channel_health` → channel_engine:NotifyChannelService.check_health
- `channel_engine.get_channel_config` → channel_engine:NotifyChannelService.get_channel_config
- `channel_engine.send_notification` → channel_engine:NotificationSender.send
- `cloud_functions_adapter.CloudFunctionsAdapter.function_exists` → cloud_functions_adapter:CloudFunctionsAdapter.get_function_info
- `connector_registry.BaseConnector.connect` → ?
- `connector_registry.BaseConnector.disconnect` → ?
- `connector_registry.BaseConnector.health_check` → ?
- `connector_registry.ConnectorConfig.to_dict` → ?
- `connector_registry.ConnectorError.to_dict` → ?
- `connector_registry.ConnectorRegistry.__init__` → ?
- `connector_registry.ConnectorRegistry.get` → datasource_model:DataSourceRegistry.get
- `connector_registry.ConnectorRegistry.reset` → ?
- `connector_registry.ConnectorStats.to_dict` → ?
- `connector_registry.FileConnector.health_check` → ?
- `connector_registry.ServerlessConnector.health_check` → ?
- `connector_registry.VectorConnector.health_check` → ?
- `connector_registry.get_connector` → connector_registry:ConnectorRegistry.get
- `connector_registry.list_connectors` → connector_registry:ConnectorRegistry.list
- `connector_registry.register_connector` → bridges:BaseBridge.register
- `connectors_facade.ConnectorsFacade._get_capabilities_for_type` → connector_registry:ConnectorRegistry.get
- `connectors_facade.TestResult.to_dict` → ?
- `cost_bridges_engine.CostAnomaly.to_dict` → ?
- `cost_bridges_engine.CostEstimationProbe.__init__` → ?
- `cost_bridges_engine.CostEstimationProbe._calculate_cost` → connector_registry:ConnectorRegistry.get
- `cost_bridges_engine.CostLoopBridge._map_severity_to_incident_severity` → connector_registry:ConnectorRegistry.get
- `cost_bridges_engine.CostPatternMatcher.__init__` → ?
- `cost_bridges_engine.CostPatternMatcher._build_signature` → cost_bridges_engine:CostPatternMatcher._deviation_bucket
- `cost_bridges_engine.CostPolicyGenerator.__init__` → ?
- `cost_bridges_engine.CostRecoveryGenerator.__init__` → ?
- `cost_bridges_engine.CostRoutingAdjuster.__init__` → ?
- `cost_bridges_engine.CostRoutingAdjuster._create_budget_block_adjustment` → loop_events:RoutingAdjustment.create
- `cost_bridges_engine.CostRoutingAdjuster._create_escalation_adjustment` → loop_events:RoutingAdjustment.create
- `cost_bridges_engine.CostRoutingAdjuster._create_model_routing_adjustment` → loop_events:RoutingAdjustment.create
- `cost_bridges_engine.CostRoutingAdjuster._create_notify_adjustment` → loop_events:RoutingAdjustment.create
- `cost_bridges_engine.CostRoutingAdjuster._create_rate_limit_adjustment` → loop_events:RoutingAdjustment.create
- `cost_bridges_engine.CostRoutingAdjuster._create_review_adjustment` → loop_events:RoutingAdjustment.create
- `cost_bridges_engine.CostRoutingAdjuster._create_throttle_adjustment` → loop_events:RoutingAdjustment.create
- `cost_bridges_engine.CostRoutingAdjuster._create_token_limit_adjustment` → loop_events:RoutingAdjustment.create
- `cus_health_engine.CusHealthService.__init__` → ?
- `cus_integration_service.get_cus_integration_service` → ?
- `customer_activity_adapter.CustomerActivityAdapter.__init__` → ?
- `customer_incidents_adapter.CustomerIncidentsAdapter.__init__` → ?
- `customer_incidents_adapter._translate_severity` → connector_registry:ConnectorRegistry.get
- `customer_incidents_adapter._translate_status` → connector_registry:ConnectorRegistry.get
- `customer_incidents_adapter.get_customer_incidents_adapter` → ?
- `customer_keys_adapter.CustomerKeysAdapter.__init__` → ?
- `customer_keys_adapter.get_customer_keys_adapter` → ?
- `customer_logs_adapter.CustomerLogsAdapter.__init__` → ?
- `customer_policies_adapter.CustomerPoliciesAdapter.__init__` → ?
- `customer_policies_adapter.CustomerPoliciesAdapter._to_customer_guardrail` → ?
- `datasource_model.CustomerDataSource.deactivate` → ?
- `datasource_model.CustomerDataSource.deprecate` → ?
- `datasource_model.CustomerDataSource.has_access` → ?
- `datasource_model.DataSourceConfig.to_dict` → ?
- `datasource_model.DataSourceError.to_dict` → ?
- `datasource_model.DataSourceRegistry.__init__` → ?
- `datasource_model.DataSourceRegistry.get` → connector_registry:ConnectorRegistry.get
- `datasource_model.DataSourceRegistry.reset` → ?
- `datasource_model.DataSourceStats.to_dict` → ?
- `datasource_model.create_datasource` → bridges:BaseBridge.register
- `datasource_model.get_datasource` → connector_registry:ConnectorRegistry.get
- `datasource_model.list_datasources` → connector_registry:ConnectorRegistry.list
- `datasources_facade.DataSourcesFacade.__init__` → ?
- `datasources_facade.DataSourcesFacade.get_statistics` → connector_registry:ConnectorRegistry.get_statistics
- `datasources_facade.TestConnectionResult.to_dict` → ?
- `dispatcher.IntegrationDispatcher.get_pending_checkpoints` → ?
- `dispatcher.IntegrationDispatcher.is_bridge_enabled` → connector_registry:ConnectorRegistry.get
- `dispatcher.IntegrationDispatcher.register_handler` → ?
- `external_response_driver.ExternalResponseService.__init__` → ?
- `external_response_driver.get_interpreted_response` → external_response_driver:ExternalResponseService.get_interpreted
- `external_response_driver.interpret_response` → external_response_driver:ExternalResponseService.interpret
- `external_response_driver.record_external_response` → external_response_driver:ExternalResponseService.record_raw_response
- `file_storage_base.DownloadResult.success` → ?
- `file_storage_base.FileMetadata.to_dict` → ?
- `file_storage_base.FileStorageAdapter.connect` → ?
- `file_storage_base.FileStorageAdapter.copy` → ?
- `file_storage_base.FileStorageAdapter.delete` → ?
- `file_storage_base.FileStorageAdapter.delete_many` → ?
- `file_storage_base.FileStorageAdapter.disconnect` → ?
- `file_storage_base.FileStorageAdapter.download` → ?
- `file_storage_base.FileStorageAdapter.download_stream` → ?
- `file_storage_base.FileStorageAdapter.exists` → ?
- `file_storage_base.FileStorageAdapter.generate_presigned_url` → ?
- `file_storage_base.FileStorageAdapter.get_metadata` → ?
- `file_storage_base.FileStorageAdapter.health_check` → connector_registry:FileConnector.list_files
- `file_storage_base.FileStorageAdapter.list_files` → ?
- `file_storage_base.FileStorageAdapter.upload` → ?
- `file_storage_base.UploadResult.success` → ?
- `gcs_adapter.GCSAdapter.disconnect` → ?
- `graduation_engine.CapabilityGates.can_auto_activate_policy` → connector_registry:ConnectorRegistry.get
- `graduation_engine.CapabilityGates.can_auto_apply_recovery` → connector_registry:ConnectorRegistry.get
- `graduation_engine.CapabilityGates.can_full_auto_routing` → ?
- `graduation_engine.ComputedGraduationStatus.is_degraded` → ?
- `graduation_engine.ComputedGraduationStatus.is_graduated` → ?
- `graduation_engine.GraduationEngine.__init__` → ?
- `graduation_engine.SimulationState.is_demo_mode` → ?
- `graduation_engine.SimulationState.to_display` → ?
- `http_connector.HttpConnectorError.__init__` → bridges:IncidentToCatalogBridge.__init__
- `http_connector.HttpConnectorService.__init__` → ?
- `http_connector.HttpConnectorService.id` → ?
- `http_connector.RateLimitExceededError.__init__` → bridges:IncidentToCatalogBridge.__init__
- `iam_engine.AccessDecision.to_dict` → ?
- `iam_engine.IAMService._create_system_identity` → iam_engine:IAMService._expand_role_permissions
- `iam_engine.IAMService._resolve_api_key_identity` → iam_engine:IAMService._expand_role_permissions
- `iam_engine.IAMService._setup_default_roles` → ?
- `iam_engine.IAMService.define_resource_permissions` → ?
- `iam_engine.IAMService.define_role` → ?
- `iam_engine.IAMService.grant_role` → ?
- `iam_engine.IAMService.list_resources` → ?
- `iam_engine.IAMService.list_roles` → ?
- `iam_engine.IAMService.revoke_role` → ?
- `iam_engine.Identity.has_all_roles` → ?
- `iam_engine.Identity.has_any_role` → ?
- `iam_engine.Identity.has_permission` → ?
- `iam_engine.Identity.has_role` → ?
- `integrations_facade.IntegrationsFacade.__init__` → ?
- `integrations_facade.IntegrationsFacade.delete_integration` → ?
- `lambda_adapter.LambdaAdapter.disconnect` → ?
- `lambda_adapter.LambdaAdapter.function_exists` → cloud_functions_adapter:CloudFunctionsAdapter.get_function_info
- `loop_events.ConfidenceBand.allows_auto_apply` → ?
- `loop_events.ConfidenceBand.requires_human_review` → ?
- `loop_events.ConfidenceCalculator.should_auto_apply` → ?
- `loop_events.HumanCheckpoint.is_pending` → ?
- `loop_events.HumanCheckpoint.resolve` → ?
- `loop_events.LoopEvent.is_blocked` → ?
- `loop_events.LoopEvent.is_success` → ?
- `loop_events.LoopEvent.to_dict` → ?
- `loop_events.LoopStatus.completion_pct` → ?
- `loop_events.PatternMatchResult.from_match` → loop_events:ConfidenceBand.from_confidence
- `loop_events.PatternMatchResult.no_match` → ?
- `loop_events.PatternMatchResult.should_auto_proceed` → ?
- `loop_events.PatternMatchResult.to_dict` → ?
- `loop_events.PolicyRule.to_dict` → ?
- `loop_events.RecoverySuggestion.none_available` → ?
- `loop_events.RecoverySuggestion.to_dict` → ?
- `loop_events.RoutingAdjustment.rollback` → ?
- `loop_events.RoutingAdjustment.to_dict` → ?
- `mcp_connector.McpApprovalRequiredError.__init__` → bridges:IncidentToCatalogBridge.__init__
- `mcp_connector.McpConnectorError.__init__` → bridges:IncidentToCatalogBridge.__init__
- `mcp_connector.McpConnectorService._build_mcp_request` → ?
- `mcp_connector.McpConnectorService.id` → ?
- `mcp_connector.McpRateLimitExceededError.__init__` → bridges:IncidentToCatalogBridge.__init__
- `mcp_connector.McpSchemaValidationError.__init__` → bridges:IncidentToCatalogBridge.__init__
- `pgvector_adapter.PGVectorAdapter.create_namespace` → ?
- `pgvector_adapter.PGVectorAdapter.delete_namespace` → connector_registry:ConnectorRegistry.delete
- `pinecone_adapter.PineconeAdapter.create_namespace` → ?
- `pinecone_adapter.PineconeAdapter.disconnect` → ?
- `prevention_contract.PreventionContractViolation.__init__` → bridges:IncidentToCatalogBridge.__init__
- `prevention_contract.assert_no_deletion` → ?
- `prevention_contract.assert_prevention_immutable` → ?
- `protocol.CredentialService.get` → ?
- `runtime_adapter.RuntimeAdapter.__init__` → ?
- `runtime_adapter.RuntimeAdapter.describe_skill` → ?
- `runtime_adapter.RuntimeAdapter.get_capabilities` → ?
- `runtime_adapter.RuntimeAdapter.get_resource_contract` → ?
- `runtime_adapter.RuntimeAdapter.get_skill_descriptors` → ?
- `runtime_adapter.RuntimeAdapter.get_supported_queries` → ?
- `runtime_adapter.RuntimeAdapter.list_skills` → ?
- `runtime_adapter.get_runtime_adapter` → ?
- `s3_adapter.S3Adapter.disconnect` → ?
- `serverless_base.FunctionInfo.to_dict` → ?
- `serverless_base.InvocationRequest.to_dict` → ?
- `serverless_base.InvocationResult.success` → ?
- `serverless_base.InvocationResult.to_dict` → ?
- `serverless_base.ServerlessAdapter.connect` → ?
- `serverless_base.ServerlessAdapter.disconnect` → ?
- `serverless_base.ServerlessAdapter.function_exists` → ?
- `serverless_base.ServerlessAdapter.get_function_info` → ?
- `serverless_base.ServerlessAdapter.health_check` → cloud_functions_adapter:CloudFunctionsAdapter.list_functions
- `serverless_base.ServerlessAdapter.invoke` → ?
- `serverless_base.ServerlessAdapter.invoke_batch` → ?
- `serverless_base.ServerlessAdapter.list_functions` → ?
- `service.CredentialService.__init__` → ?
- `slack_adapter.SlackAdapter._get_priority_emoji` → connector_registry:ConnectorRegistry.get
- `slack_adapter.SlackAdapter.disconnect` → ?
- `slack_adapter.SlackAdapter.get_status` → connector_registry:ConnectorRegistry.get
- `smtp_adapter.SMTPAdapter.disconnect` → ?
- `smtp_adapter.SMTPAdapter.get_status` → connector_registry:ConnectorRegistry.get
- `sql_gateway.SqlGatewayService.__init__` → ?
- `sql_gateway.SqlGatewayService.id` → ?
- `vault.CredentialData.credential_id` → ?
- `vault.CredentialData.tenant_id` → ?
- `vault.CredentialVault.delete_credential` → ?
- `vault.CredentialVault.get_credential` → ?
- `vault.CredentialVault.get_metadata` → ?
- `vault.CredentialVault.list_credentials` → ?
- `vault.CredentialVault.rotate_credential` → ?
- `vault.CredentialVault.store_credential` → ?
- `vault.CredentialVault.update_credential` → ?
- `vault.EnvCredentialVault.__init__` → ?
- `vault.EnvCredentialVault.get_metadata` → connector_registry:ConnectorRegistry.get
- `vault.EnvCredentialVault.rotate_credential` → service:CredentialService.update_credential
- `vault.HashiCorpVault.rotate_credential` → service:CredentialService.update_credential
- `vector_stores_base.DeleteResult.success` → ?
- `vector_stores_base.IndexStats.to_dict` → ?
- `vector_stores_base.QueryResult.to_dict` → ?
- `vector_stores_base.UpsertResult.success` → ?
- `vector_stores_base.VectorRecord.to_dict` → ?
- `vector_stores_base.VectorStoreAdapter.connect` → ?
- `vector_stores_base.VectorStoreAdapter.create_namespace` → ?
- `vector_stores_base.VectorStoreAdapter.delete` → ?
- `vector_stores_base.VectorStoreAdapter.delete_namespace` → ?
- `vector_stores_base.VectorStoreAdapter.disconnect` → ?
- `vector_stores_base.VectorStoreAdapter.get_stats` → ?
- `vector_stores_base.VectorStoreAdapter.health_check` → pgvector_adapter:PGVectorAdapter.get_stats
- `vector_stores_base.VectorStoreAdapter.list_namespaces` → ?
- `vector_stores_base.VectorStoreAdapter.query` → ?
- `vector_stores_base.VectorStoreAdapter.upsert` → ?
- `weaviate_adapter.WeaviateAdapter._create_collection` → ?
- `weaviate_adapter.WeaviateAdapter.create_namespace` → ?
- `weaviate_adapter.WeaviateAdapter.delete_namespace` → connector_registry:ConnectorRegistry.delete
- `weaviate_adapter.WeaviateAdapter.disconnect` → ?
- `webhook_adapter.WebhookAdapter.get_delivery_details` → connector_registry:ConnectorRegistry.get
- `webhook_adapter.WebhookDelivery.to_dict` → ?
- `worker_registry_driver.WorkerRegistryService.__init__` → ?
- `worker_registry_driver.WorkerRegistryService.deprecate_worker` → worker_registry_driver:WorkerRegistryService.update_worker_status
- `worker_registry_driver.WorkerRegistryService.get_worker` → connector_registry:ConnectorRegistry.get
- `worker_registry_driver.WorkerRegistryService.list_available_workers` → worker_registry_driver:WorkerRegistryService.list_workers
- `worker_registry_driver.WorkerRegistryService.list_worker_summaries` → worker_registry_driver:WorkerRegistryService.get_worker_summary
- `worker_registry_driver.get_worker_registry_service` → ?
- `workers_adapter.WorkersAdapter.calculate_cost_cents` → ?
- `workers_adapter.WorkersAdapter.convert_brand_request` → ?
- `workers_adapter.WorkersAdapter.execute_worker` → ?
- `workers_adapter.WorkersAdapter.replay_execution` → ?

## Full Call Graph

```
[WRAPPER] audit_schemas.PolicyActivationAudit.to_dict
[WRAPPER] bridges.BaseBridge.process
[WRAPPER] bridges.BaseBridge.register → dispatcher:IntegrationDispatcher.register_handler
[WRAPPER] bridges.BaseBridge.stage
[WRAPPER] bridges.IncidentToCatalogBridge.__init__
[SUPERSET] bridges.IncidentToCatalogBridge._calculate_fuzzy_confidence → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[INTERNAL] bridges.IncidentToCatalogBridge._create_pattern → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, protocol:CredentialService.get, ...+1
[INTERNAL] bridges.IncidentToCatalogBridge._extract_signature → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[SUPERSET] bridges.IncidentToCatalogBridge._find_matching_pattern → bridges:IncidentToCatalogBridge._calculate_fuzzy_confidence, bridges:IncidentToCatalogBridge._create_pattern, bridges:IncidentToCatalogBridge._increment_pattern_count, connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, ...+6
[LEAF] bridges.IncidentToCatalogBridge._hash_signature
[WRAPPER] bridges.IncidentToCatalogBridge._increment_pattern_count → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[SUPERSET] bridges.IncidentToCatalogBridge.process → audit_schemas:PolicyActivationAudit.to_dict, bridges:IncidentToCatalogBridge._extract_signature, bridges:IncidentToCatalogBridge._find_matching_pattern, bridges:IncidentToCatalogBridge._hash_signature, channel_engine:NotifyChannelConfig.to_dict, ...+38
[WRAPPER] bridges.IncidentToCatalogBridge.stage
[WRAPPER] bridges.LoopStatusBridge.__init__
[INTERNAL] bridges.LoopStatusBridge._build_loop_status → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, protocol:CredentialService.get, ...+1
[WRAPPER] bridges.LoopStatusBridge._push_sse_update
[ENTRY] bridges.LoopStatusBridge.process → audit_schemas:PolicyActivationAudit.to_dict, bridges:LoopStatusBridge._build_loop_status, bridges:LoopStatusBridge._push_sse_update, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, ...+34
[WRAPPER] bridges.LoopStatusBridge.stage
[WRAPPER] bridges.PatternToRecoveryBridge.__init__
[INTERNAL] bridges.PatternToRecoveryBridge._apply_recovery → bridges:PatternToRecoveryBridge._persist_recovery
[SUPERSET] bridges.PatternToRecoveryBridge._generate_recovery → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, loop_events:ConfidenceCalculator.calculate_recovery_confidence, loop_events:ConfidenceCalculator.get_confirmation_level, loop_events:ConfidenceCalculator.should_auto_apply, ...+2
[INTERNAL] bridges.PatternToRecoveryBridge._instantiate_template → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, loop_events:RecoverySuggestion.create, protocol:CredentialService.get
[INTERNAL] bridges.PatternToRecoveryBridge._load_pattern → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[INTERNAL] bridges.PatternToRecoveryBridge._persist_recovery → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[INTERNAL] bridges.PatternToRecoveryBridge._queue_for_review → bridges:PatternToRecoveryBridge._persist_recovery
[CANONICAL] bridges.PatternToRecoveryBridge.process → audit_schemas:PolicyActivationAudit.to_dict, bridges:PatternToRecoveryBridge._apply_recovery, bridges:PatternToRecoveryBridge._generate_recovery, bridges:PatternToRecoveryBridge._instantiate_template, bridges:PatternToRecoveryBridge._load_pattern, ...+41
[WRAPPER] bridges.PatternToRecoveryBridge.stage
[WRAPPER] bridges.PolicyToRoutingBridge.__init__
[INTERNAL] bridges.PolicyToRoutingBridge._create_adjustment → bridges:PolicyToRoutingBridge._get_active_adjustments, bridges:PolicyToRoutingBridge._get_agent_kpi, bridges:PolicyToRoutingBridge._persist_adjustment, connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, ...+2
[INTERNAL] bridges.PolicyToRoutingBridge._get_active_adjustments → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[INTERNAL] bridges.PolicyToRoutingBridge._get_agent_kpi → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[INTERNAL] bridges.PolicyToRoutingBridge._identify_affected_agents → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[INTERNAL] bridges.PolicyToRoutingBridge._persist_adjustment → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[SUPERSET] bridges.PolicyToRoutingBridge.process → audit_schemas:PolicyActivationAudit.to_dict, bridges:PolicyToRoutingBridge._create_adjustment, bridges:PolicyToRoutingBridge._identify_affected_agents, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, ...+37
[WRAPPER] bridges.PolicyToRoutingBridge.stage
[WRAPPER] bridges.RecoveryToPolicyBridge.__init__
[SUPERSET] bridges.RecoveryToPolicyBridge._generate_policy → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, loop_events:PolicyRule.create, protocol:CredentialService.get
[INTERNAL] bridges.RecoveryToPolicyBridge._load_pattern → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[INTERNAL] bridges.RecoveryToPolicyBridge._persist_policy → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[SUPERSET] bridges.RecoveryToPolicyBridge.process → audit_schemas:PolicyActivationAudit.to_dict, bridges:PatternToRecoveryBridge._load_pattern, bridges:RecoveryToPolicyBridge._generate_policy, bridges:RecoveryToPolicyBridge._load_pattern, bridges:RecoveryToPolicyBridge._persist_policy, ...+39
[WRAPPER] bridges.RecoveryToPolicyBridge.stage
[WRAPPER] bridges._check_frozen
[LEAF] bridges.create_bridges
[ENTRY] bridges.register_all_bridges → bridges:BaseBridge.register, bridges:create_bridges, connector_registry:ConnectorRegistry.register, datasource_model:DataSourceRegistry.register
[WRAPPER] channel_engine.NotificationSender.send
[LEAF] channel_engine.NotifyChannelConfig.is_configured
[WRAPPER] channel_engine.NotifyChannelConfig.is_event_enabled
[WRAPPER] channel_engine.NotifyChannelConfig.record_failure
[WRAPPER] channel_engine.NotifyChannelConfig.record_success
[INTERNAL] channel_engine.NotifyChannelConfig.to_dict → channel_engine:NotifyChannelConfig.is_configured
[WRAPPER] channel_engine.NotifyChannelConfigResponse.to_dict
[INTERNAL] channel_engine.NotifyChannelError.__init__ → bridges:IncidentToCatalogBridge.__init__, bridges:LoopStatusBridge.__init__, bridges:PatternToRecoveryBridge.__init__, bridges:PolicyToRoutingBridge.__init__, bridges:RecoveryToPolicyBridge.__init__, ...+54
[WRAPPER] channel_engine.NotifyChannelError.to_dict
[WRAPPER] channel_engine.NotifyChannelService.__init__
[LEAF] channel_engine.NotifyChannelService._send_email_notification
[LEAF] channel_engine.NotifyChannelService._send_pagerduty_notification
[LEAF] channel_engine.NotifyChannelService._send_slack_notification
[LEAF] channel_engine.NotifyChannelService._send_teams_notification
[LEAF] channel_engine.NotifyChannelService._send_ui_notification
[SUPERSET] channel_engine.NotifyChannelService._send_via_channel → channel_engine:NotifyChannelService._send_email_notification, channel_engine:NotifyChannelService._send_pagerduty_notification, channel_engine:NotifyChannelService._send_slack_notification, channel_engine:NotifyChannelService._send_teams_notification, channel_engine:NotifyChannelService._send_ui_notification, ...+1
[LEAF] channel_engine.NotifyChannelService._send_webhook_notification
[INTERNAL] channel_engine.NotifyChannelService.check_health → channel_engine:NotifyChannelConfig.is_configured, channel_engine:NotifyChannelService.get_channel_config, channel_engine:get_channel_config
[SUPERSET] channel_engine.NotifyChannelService.configure_channel → channel_engine:NotifyChannelConfig.is_configured
[ENTRY] channel_engine.NotifyChannelService.disable_channel → channel_engine:NotifyChannelConfig.is_configured, channel_engine:NotifyChannelService.get_channel_config, channel_engine:get_channel_config, connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list
[SUPERSET] channel_engine.NotifyChannelService.enable_channel → channel_engine:NotifyChannelConfig.is_configured, channel_engine:NotifyChannelService.get_channel_config, channel_engine:get_channel_config, connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list
[WRAPPER] channel_engine.NotifyChannelService.get_all_configs → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[INTERNAL] channel_engine.NotifyChannelService.get_channel_config → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[LEAF] channel_engine.NotifyChannelService.get_delivery_history
[SUPERSET] channel_engine.NotifyChannelService.get_enabled_channels → channel_engine:NotifyChannelConfig.is_configured, channel_engine:NotifyChannelConfig.is_event_enabled, connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list
[CANONICAL] channel_engine.NotifyChannelService.send → channel_engine:NotifyChannelConfig.is_event_enabled, channel_engine:NotifyChannelConfig.record_failure, channel_engine:NotifyChannelConfig.record_success, channel_engine:NotifyChannelService._send_ui_notification, channel_engine:NotifyChannelService._send_via_channel, ...+5
[ENTRY] channel_engine.NotifyChannelService.set_event_filter → channel_engine:NotifyChannelConfig.is_configured, channel_engine:NotifyChannelService.get_channel_config, channel_engine:get_channel_config, connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list
[WRAPPER] channel_engine.NotifyDeliveryResult.to_dict
[WRAPPER] channel_engine._reset_notify_service
[WRAPPER] channel_engine.check_channel_health → channel_engine:NotifyChannelService.check_health, channel_engine:get_notify_service, cus_health_engine:CusHealthService.check_health
[WRAPPER] channel_engine.get_channel_config → channel_engine:NotifyChannelService.get_channel_config, channel_engine:get_notify_service
[LEAF] channel_engine.get_notify_service
[WRAPPER] channel_engine.send_notification → channel_engine:NotificationSender.send, channel_engine:NotifyChannelService.send, channel_engine:get_notify_service, slack_adapter:SlackAdapter.send, smtp_adapter:SMTPAdapter.send, ...+1
[LEAF] cloud_functions_adapter.CloudFunctionsAdapter.__init__
[LEAF] cloud_functions_adapter.CloudFunctionsAdapter.connect
[LEAF] cloud_functions_adapter.CloudFunctionsAdapter.disconnect
[WRAPPER] cloud_functions_adapter.CloudFunctionsAdapter.function_exists → cloud_functions_adapter:CloudFunctionsAdapter.get_function_info, lambda_adapter:LambdaAdapter.get_function_info, serverless_base:ServerlessAdapter.get_function_info
[LEAF] cloud_functions_adapter.CloudFunctionsAdapter.get_function_info
[SUPERSET] cloud_functions_adapter.CloudFunctionsAdapter.invoke → cloud_functions_adapter:CloudFunctionsAdapter.get_function_info, connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, lambda_adapter:LambdaAdapter.get_function_info, protocol:CredentialService.get, ...+1
[CANONICAL] cloud_functions_adapter.CloudFunctionsAdapter.invoke_batch → cloud_functions_adapter:CloudFunctionsAdapter.invoke, connector_registry:ServerlessConnector.invoke, lambda_adapter:LambdaAdapter.invoke, serverless_base:ServerlessAdapter.invoke
[SUPERSET] cloud_functions_adapter.CloudFunctionsAdapter.list_functions → connector_registry:ConnectorRegistry.list, connector_registry:ServerlessConnector.list_functions, datasource_model:DataSourceRegistry.list, lambda_adapter:LambdaAdapter.list_functions, serverless_base:ServerlessAdapter.list_functions
[LEAF] connector_registry.BaseConnector.__init__
[WRAPPER] connector_registry.BaseConnector.connect
[WRAPPER] connector_registry.BaseConnector.disconnect
[WRAPPER] connector_registry.BaseConnector.health_check
[LEAF] connector_registry.BaseConnector.record_connection
[LEAF] connector_registry.BaseConnector.record_error
[INTERNAL] connector_registry.BaseConnector.to_dict → audit_schemas:PolicyActivationAudit.to_dict, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, ...+30
[WRAPPER] connector_registry.ConnectorConfig.to_dict
[INTERNAL] connector_registry.ConnectorError.__init__ → bridges:IncidentToCatalogBridge.__init__, bridges:LoopStatusBridge.__init__, bridges:PatternToRecoveryBridge.__init__, bridges:PolicyToRoutingBridge.__init__, bridges:RecoveryToPolicyBridge.__init__, ...+54
[WRAPPER] connector_registry.ConnectorError.to_dict
[WRAPPER] connector_registry.ConnectorRegistry.__init__
[ENTRY] connector_registry.ConnectorRegistry.clear_tenant → connector_registry:ConnectorRegistry.delete, connector_registry:ConnectorRegistry.get, connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.delete, datasource_model:DataSourceRegistry.get, ...+9
[ENTRY] connector_registry.ConnectorRegistry.create_file_connector → bridges:BaseBridge.register, connector_registry:ConnectorRegistry.register, datasource_model:DataSourceRegistry.register
[ENTRY] connector_registry.ConnectorRegistry.create_serverless_connector → bridges:BaseBridge.register, connector_registry:ConnectorRegistry.register, datasource_model:DataSourceRegistry.register
[ENTRY] connector_registry.ConnectorRegistry.create_vector_connector → bridges:BaseBridge.register, connector_registry:ConnectorRegistry.register, datasource_model:DataSourceRegistry.register
[SUPERSET] connector_registry.ConnectorRegistry.delete → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] connector_registry.ConnectorRegistry.get → datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[LEAF] connector_registry.ConnectorRegistry.get_by_name
[SUPERSET] connector_registry.ConnectorRegistry.get_statistics → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[CANONICAL] connector_registry.ConnectorRegistry.list → datasource_model:DataSourceRegistry.list
[LEAF] connector_registry.ConnectorRegistry.register
[WRAPPER] connector_registry.ConnectorRegistry.reset
[WRAPPER] connector_registry.ConnectorStats.to_dict
[INTERNAL] connector_registry.FileConnector.__init__ → bridges:IncidentToCatalogBridge.__init__, bridges:LoopStatusBridge.__init__, bridges:PatternToRecoveryBridge.__init__, bridges:PolicyToRoutingBridge.__init__, bridges:RecoveryToPolicyBridge.__init__, ...+54
[INTERNAL] connector_registry.FileConnector.connect → connector_registry:BaseConnector.record_connection, connector_registry:BaseConnector.record_error, datasource_model:CustomerDataSource.record_connection, datasource_model:CustomerDataSource.record_error
[LEAF] connector_registry.FileConnector.delete_file
[LEAF] connector_registry.FileConnector.disconnect
[WRAPPER] connector_registry.FileConnector.health_check
[LEAF] connector_registry.FileConnector.list_files
[LEAF] connector_registry.FileConnector.read_file
[INTERNAL] connector_registry.FileConnector.to_dict → audit_schemas:PolicyActivationAudit.to_dict, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, ...+30
[LEAF] connector_registry.FileConnector.write_file
[INTERNAL] connector_registry.ServerlessConnector.__init__ → bridges:IncidentToCatalogBridge.__init__, bridges:LoopStatusBridge.__init__, bridges:PatternToRecoveryBridge.__init__, bridges:PolicyToRoutingBridge.__init__, bridges:RecoveryToPolicyBridge.__init__, ...+54
[INTERNAL] connector_registry.ServerlessConnector.connect → connector_registry:BaseConnector.record_connection, connector_registry:BaseConnector.record_error, datasource_model:CustomerDataSource.record_connection, datasource_model:CustomerDataSource.record_error
[LEAF] connector_registry.ServerlessConnector.disconnect
[LEAF] connector_registry.ServerlessConnector.get_result
[WRAPPER] connector_registry.ServerlessConnector.health_check
[LEAF] connector_registry.ServerlessConnector.invoke
[LEAF] connector_registry.ServerlessConnector.list_functions
[INTERNAL] connector_registry.ServerlessConnector.to_dict → audit_schemas:PolicyActivationAudit.to_dict, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, ...+30
[INTERNAL] connector_registry.VectorConnector.__init__ → bridges:IncidentToCatalogBridge.__init__, bridges:LoopStatusBridge.__init__, bridges:PatternToRecoveryBridge.__init__, bridges:PolicyToRoutingBridge.__init__, bridges:RecoveryToPolicyBridge.__init__, ...+54
[INTERNAL] connector_registry.VectorConnector.connect → connector_registry:BaseConnector.record_connection, connector_registry:BaseConnector.record_error, datasource_model:CustomerDataSource.record_connection, datasource_model:CustomerDataSource.record_error
[LEAF] connector_registry.VectorConnector.delete_vectors
[LEAF] connector_registry.VectorConnector.disconnect
[WRAPPER] connector_registry.VectorConnector.health_check
[LEAF] connector_registry.VectorConnector.search
[INTERNAL] connector_registry.VectorConnector.to_dict → audit_schemas:PolicyActivationAudit.to_dict, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, ...+30
[LEAF] connector_registry.VectorConnector.upsert_vectors
[ENTRY] connector_registry._reset_registry → connector_registry:ConnectorRegistry.reset, datasource_model:DataSourceRegistry.reset
[WRAPPER] connector_registry.get_connector → connector_registry:ConnectorRegistry.get, connector_registry:get_connector_registry, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[LEAF] connector_registry.get_connector_registry
[WRAPPER] connector_registry.list_connectors → connector_registry:ConnectorRegistry.list, connector_registry:get_connector_registry, datasource_model:DataSourceRegistry.list
[WRAPPER] connector_registry.register_connector → bridges:BaseBridge.register, connector_registry:ConnectorRegistry.register, connector_registry:get_connector_registry, datasource_model:DataSourceRegistry.register
[LEAF] connectors_facade.ConnectorInfo.to_dict
[LEAF] connectors_facade.ConnectorsFacade.__init__
[WRAPPER] connectors_facade.ConnectorsFacade._get_capabilities_for_type → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[ENTRY] connectors_facade.ConnectorsFacade.delete_connector → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[ENTRY] connectors_facade.ConnectorsFacade.get_connector → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[LEAF] connectors_facade.ConnectorsFacade.list_connectors
[ENTRY] connectors_facade.ConnectorsFacade.register_connector → connectors_facade:ConnectorsFacade._get_capabilities_for_type
[LEAF] connectors_facade.ConnectorsFacade.registry
[SUPERSET] connectors_facade.ConnectorsFacade.test_connector → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[CANONICAL] connectors_facade.ConnectorsFacade.update_connector → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] connectors_facade.TestResult.to_dict
[LEAF] connectors_facade.get_connectors_facade
[SUPERSET] cost_bridges_engine.CostAnomaly.create → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] cost_bridges_engine.CostAnomaly.to_dict
[WRAPPER] cost_bridges_engine.CostEstimationProbe.__init__
[WRAPPER] cost_bridges_engine.CostEstimationProbe._calculate_cost → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[SUPERSET] cost_bridges_engine.CostEstimationProbe._find_cheaper_model → cost_bridges_engine:CostEstimationProbe._calculate_cost
[SUPERSET] cost_bridges_engine.CostEstimationProbe.probe → cost_bridges_engine:CostEstimationProbe._calculate_cost, cost_bridges_engine:CostEstimationProbe._find_cheaper_model
[LEAF] cost_bridges_engine.CostLoopBridge.__init__
[WRAPPER] cost_bridges_engine.CostLoopBridge._map_severity_to_incident_severity → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[LEAF] cost_bridges_engine.CostLoopBridge.on_anomaly_detected
[LEAF] cost_bridges_engine.CostLoopOrchestrator.__init__
[CANONICAL] cost_bridges_engine.CostLoopOrchestrator.process_anomaly → audit_schemas:PolicyActivationAudit.to_dict, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, ...+36
[WRAPPER] cost_bridges_engine.CostPatternMatcher.__init__
[WRAPPER] cost_bridges_engine.CostPatternMatcher._build_signature → cost_bridges_engine:CostPatternMatcher._deviation_bucket
[SUPERSET] cost_bridges_engine.CostPatternMatcher._calculate_confidence → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[LEAF] cost_bridges_engine.CostPatternMatcher._deviation_bucket
[LEAF] cost_bridges_engine.CostPatternMatcher._find_predefined_match
[LEAF] cost_bridges_engine.CostPatternMatcher._hash_signature
[INTERNAL] cost_bridges_engine.CostPatternMatcher.match_cost_pattern → bridges:IncidentToCatalogBridge._hash_signature, cost_bridges_engine:CostPatternMatcher._build_signature, cost_bridges_engine:CostPatternMatcher._calculate_confidence, cost_bridges_engine:CostPatternMatcher._find_predefined_match, cost_bridges_engine:CostPatternMatcher._hash_signature, ...+1
[WRAPPER] cost_bridges_engine.CostPolicyGenerator.__init__
[INTERNAL] cost_bridges_engine.CostPolicyGenerator.generate_policy → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, loop_events:PolicyRule.create, protocol:CredentialService.get
[WRAPPER] cost_bridges_engine.CostRecoveryGenerator.__init__
[SUPERSET] cost_bridges_engine.CostRecoveryGenerator.generate_recovery → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, loop_events:RecoverySuggestion.create, protocol:CredentialService.get
[WRAPPER] cost_bridges_engine.CostRoutingAdjuster.__init__
[WRAPPER] cost_bridges_engine.CostRoutingAdjuster._create_budget_block_adjustment → loop_events:RoutingAdjustment.create
[WRAPPER] cost_bridges_engine.CostRoutingAdjuster._create_escalation_adjustment → loop_events:RoutingAdjustment.create
[WRAPPER] cost_bridges_engine.CostRoutingAdjuster._create_model_routing_adjustment → loop_events:RoutingAdjustment.create
[WRAPPER] cost_bridges_engine.CostRoutingAdjuster._create_notify_adjustment → loop_events:RoutingAdjustment.create
[WRAPPER] cost_bridges_engine.CostRoutingAdjuster._create_rate_limit_adjustment → loop_events:RoutingAdjustment.create
[WRAPPER] cost_bridges_engine.CostRoutingAdjuster._create_review_adjustment → loop_events:RoutingAdjustment.create
[WRAPPER] cost_bridges_engine.CostRoutingAdjuster._create_throttle_adjustment → loop_events:RoutingAdjustment.create
[WRAPPER] cost_bridges_engine.CostRoutingAdjuster._create_token_limit_adjustment → loop_events:RoutingAdjustment.create
[SUPERSET] cost_bridges_engine.CostRoutingAdjuster.on_cost_policy_created → cost_bridges_engine:CostRoutingAdjuster._create_budget_block_adjustment, cost_bridges_engine:CostRoutingAdjuster._create_escalation_adjustment, cost_bridges_engine:CostRoutingAdjuster._create_model_routing_adjustment, cost_bridges_engine:CostRoutingAdjuster._create_notify_adjustment, cost_bridges_engine:CostRoutingAdjuster._create_rate_limit_adjustment, ...+3
[WRAPPER] cus_health_engine.CusHealthService.__init__
[LEAF] cus_health_engine.CusHealthService._calculate_overall_health
[SUPERSET] cus_health_engine.CusHealthService._perform_health_check → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, datasource_model:DataSourceRegistry.update, protocol:CredentialService.get
[ENTRY] cus_health_engine.CusHealthService.check_all_integrations → channel_engine:NotifyChannelService.check_health, connector_registry:ConnectorRegistry.list, cus_health_engine:CusHealthService.check_health, datasource_model:DataSourceRegistry.list
[SUPERSET] cus_health_engine.CusHealthService.check_health → cus_health_engine:CusHealthService._perform_health_check
[SUPERSET] cus_health_engine.CusHealthService.get_health_summary → connector_registry:ConnectorRegistry.list, cus_health_engine:CusHealthService._calculate_overall_health, datasource_model:DataSourceRegistry.list
[WRAPPER] cus_integration_service.get_cus_integration_service
[LEAF] cus_schemas.CusIntegrationCreate.validate_not_raw_key
[LEAF] cus_schemas.CusIntegrationUpdate.validate_not_raw_key
[WRAPPER] customer_activity_adapter.CustomerActivityAdapter.__init__
[LEAF] customer_activity_adapter.CustomerActivityAdapter._get_facade
[LEAF] customer_activity_adapter.CustomerActivityAdapter._to_customer_detail
[LEAF] customer_activity_adapter.CustomerActivityAdapter._to_customer_summary
[CANONICAL] customer_activity_adapter.CustomerActivityAdapter.get_activity → customer_activity_adapter:CustomerActivityAdapter._get_facade, customer_activity_adapter:CustomerActivityAdapter._to_customer_detail
[ENTRY] customer_activity_adapter.CustomerActivityAdapter.list_activities → customer_activity_adapter:CustomerActivityAdapter._get_facade, customer_activity_adapter:CustomerActivityAdapter._to_customer_summary
[LEAF] customer_activity_adapter.get_customer_activity_adapter
[WRAPPER] customer_incidents_adapter.CustomerIncidentsAdapter.__init__
[ENTRY] customer_incidents_adapter.CustomerIncidentsAdapter.acknowledge_incident → customer_incidents_adapter:CustomerIncidentsAdapter.get_incident, customer_incidents_adapter:_translate_severity
[CANONICAL] customer_incidents_adapter.CustomerIncidentsAdapter.get_incident → customer_incidents_adapter:_translate_severity, customer_incidents_adapter:_translate_status
[ENTRY] customer_incidents_adapter.CustomerIncidentsAdapter.list_incidents → customer_incidents_adapter:_translate_severity, customer_incidents_adapter:_translate_status
[ENTRY] customer_incidents_adapter.CustomerIncidentsAdapter.resolve_incident → customer_incidents_adapter:CustomerIncidentsAdapter.get_incident, customer_incidents_adapter:_translate_severity
[WRAPPER] customer_incidents_adapter._translate_severity → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] customer_incidents_adapter._translate_status → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] customer_incidents_adapter.get_customer_incidents_adapter
[WRAPPER] customer_keys_adapter.CustomerKeysAdapter.__init__
[SUPERSET] customer_keys_adapter.CustomerKeysAdapter.freeze_key → customer_keys_adapter:CustomerKeysAdapter.get_key
[LEAF] customer_keys_adapter.CustomerKeysAdapter.get_key
[LEAF] customer_keys_adapter.CustomerKeysAdapter.list_keys
[SUPERSET] customer_keys_adapter.CustomerKeysAdapter.unfreeze_key → customer_keys_adapter:CustomerKeysAdapter.get_key
[WRAPPER] customer_keys_adapter.get_customer_keys_adapter
[WRAPPER] customer_logs_adapter.CustomerLogsAdapter.__init__
[LEAF] customer_logs_adapter.CustomerLogsAdapter._get_service
[ENTRY] customer_logs_adapter.CustomerLogsAdapter.export_logs → customer_logs_adapter:CustomerLogsAdapter.list_logs
[CANONICAL] customer_logs_adapter.CustomerLogsAdapter.get_log → customer_logs_adapter:CustomerLogsAdapter._get_service, customer_policies_adapter:CustomerPoliciesAdapter._get_service
[INTERNAL] customer_logs_adapter.CustomerLogsAdapter.list_logs → customer_logs_adapter:CustomerLogsAdapter._get_service, customer_policies_adapter:CustomerPoliciesAdapter._get_service
[LEAF] customer_logs_adapter.get_customer_logs_adapter
[WRAPPER] customer_policies_adapter.CustomerPoliciesAdapter.__init__
[LEAF] customer_policies_adapter.CustomerPoliciesAdapter._get_service
[WRAPPER] customer_policies_adapter.CustomerPoliciesAdapter._to_customer_guardrail
[INTERNAL] customer_policies_adapter.CustomerPoliciesAdapter._to_customer_policy_constraints → customer_policies_adapter:CustomerPoliciesAdapter._to_customer_guardrail
[CANONICAL] customer_policies_adapter.CustomerPoliciesAdapter.get_guardrail_detail → customer_logs_adapter:CustomerLogsAdapter._get_service, customer_policies_adapter:CustomerPoliciesAdapter._get_service, customer_policies_adapter:CustomerPoliciesAdapter._to_customer_guardrail
[ENTRY] customer_policies_adapter.CustomerPoliciesAdapter.get_policy_constraints → customer_logs_adapter:CustomerLogsAdapter._get_service, customer_policies_adapter:CustomerPoliciesAdapter._get_service, customer_policies_adapter:CustomerPoliciesAdapter._to_customer_policy_constraints
[LEAF] customer_policies_adapter.get_customer_policies_adapter
[LEAF] datasource_model.CustomerDataSource.activate
[LEAF] datasource_model.CustomerDataSource.add_tag
[WRAPPER] datasource_model.CustomerDataSource.deactivate
[WRAPPER] datasource_model.CustomerDataSource.deprecate
[LEAF] datasource_model.CustomerDataSource.grant_access
[WRAPPER] datasource_model.CustomerDataSource.has_access
[LEAF] datasource_model.CustomerDataSource.record_connection
[LEAF] datasource_model.CustomerDataSource.record_error
[LEAF] datasource_model.CustomerDataSource.remove_tag
[LEAF] datasource_model.CustomerDataSource.revoke_access
[INTERNAL] datasource_model.CustomerDataSource.to_dict → audit_schemas:PolicyActivationAudit.to_dict, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, ...+30
[LEAF] datasource_model.CustomerDataSource.update_config
[LEAF] datasource_model.DataSourceConfig.get_connection_url
[WRAPPER] datasource_model.DataSourceConfig.to_dict
[INTERNAL] datasource_model.DataSourceError.__init__ → bridges:IncidentToCatalogBridge.__init__, bridges:LoopStatusBridge.__init__, bridges:PatternToRecoveryBridge.__init__, bridges:PolicyToRoutingBridge.__init__, bridges:RecoveryToPolicyBridge.__init__, ...+54
[WRAPPER] datasource_model.DataSourceError.to_dict
[WRAPPER] datasource_model.DataSourceRegistry.__init__
[INTERNAL] datasource_model.DataSourceRegistry.activate → connector_registry:ConnectorRegistry.get, datasource_model:CustomerDataSource.activate, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[ENTRY] datasource_model.DataSourceRegistry.clear_tenant → connector_registry:ConnectorRegistry.delete, connector_registry:ConnectorRegistry.get, connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.delete, datasource_model:DataSourceRegistry.get, ...+9
[INTERNAL] datasource_model.DataSourceRegistry.deactivate → connector_registry:ConnectorRegistry.get, datasource_model:CustomerDataSource.deactivate, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[SUPERSET] datasource_model.DataSourceRegistry.delete → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] datasource_model.DataSourceRegistry.get → connector_registry:ConnectorRegistry.get, protocol:CredentialService.get
[LEAF] datasource_model.DataSourceRegistry.get_by_name
[SUPERSET] datasource_model.DataSourceRegistry.get_statistics → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[SUPERSET] datasource_model.DataSourceRegistry.list → connector_registry:ConnectorRegistry.list
[LEAF] datasource_model.DataSourceRegistry.register
[WRAPPER] datasource_model.DataSourceRegistry.reset
[CANONICAL] datasource_model.DataSourceRegistry.update → connector_registry:ConnectorRegistry.get, datasource_model:CustomerDataSource.update_config, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] datasource_model.DataSourceStats.to_dict
[ENTRY] datasource_model._reset_registry → connector_registry:ConnectorRegistry.reset, datasource_model:DataSourceRegistry.reset
[WRAPPER] datasource_model.create_datasource → bridges:BaseBridge.register, connector_registry:ConnectorRegistry.register, datasource_model:DataSourceRegistry.register, datasource_model:get_datasource_registry
[WRAPPER] datasource_model.get_datasource → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, datasource_model:get_datasource_registry, protocol:CredentialService.get
[LEAF] datasource_model.get_datasource_registry
[WRAPPER] datasource_model.list_datasources → connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list, datasource_model:get_datasource_registry
[WRAPPER] datasources_facade.DataSourcesFacade.__init__
[ENTRY] datasources_facade.DataSourcesFacade.activate_source → connector_registry:ConnectorRegistry.get, datasource_model:CustomerDataSource.activate, datasource_model:DataSourceRegistry.activate, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[ENTRY] datasources_facade.DataSourcesFacade.deactivate_source → connector_registry:ConnectorRegistry.get, datasource_model:CustomerDataSource.deactivate, datasource_model:DataSourceRegistry.deactivate, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[ENTRY] datasources_facade.DataSourcesFacade.delete_source → connector_registry:ConnectorRegistry.delete, connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.delete, datasource_model:DataSourceRegistry.get, file_storage_base:FileStorageAdapter.delete, ...+7
[ENTRY] datasources_facade.DataSourcesFacade.get_source → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] datasources_facade.DataSourcesFacade.get_statistics → connector_registry:ConnectorRegistry.get_statistics, datasource_model:DataSourceRegistry.get_statistics
[SUPERSET] datasources_facade.DataSourcesFacade.list_sources → connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list
[CANONICAL] datasources_facade.DataSourcesFacade.register_source → bridges:BaseBridge.register, connector_registry:ConnectorRegistry.get, connector_registry:ConnectorRegistry.register, datasource_model:DataSourceRegistry.get, datasource_model:DataSourceRegistry.register, ...+1
[ENTRY] datasources_facade.DataSourcesFacade.registry → datasource_model:get_datasource_registry
[ENTRY] datasources_facade.DataSourcesFacade.test_connection → connector_registry:BaseConnector.record_connection, connector_registry:ConnectorRegistry.get, datasource_model:CustomerDataSource.record_connection, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[SUPERSET] datasources_facade.DataSourcesFacade.update_source → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, datasource_model:DataSourceRegistry.update, protocol:CredentialService.get
[WRAPPER] datasources_facade.TestConnectionResult.to_dict
[LEAF] datasources_facade.get_datasources_facade
[LEAF] dispatcher.DispatcherConfig.from_env
[INTERNAL] dispatcher.IntegrationDispatcher.__init__ → dispatcher:DispatcherConfig.from_env
[INTERNAL] dispatcher.IntegrationDispatcher._check_db_idempotency → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[SUPERSET] dispatcher.IntegrationDispatcher._check_human_checkpoint_needed → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, loop_events:HumanCheckpoint.create, protocol:CredentialService.get
[SUPERSET] dispatcher.IntegrationDispatcher._execute_handlers → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[SUPERSET] dispatcher.IntegrationDispatcher._get_or_create_loop_status → dispatcher:IntegrationDispatcher._load_loop_status, dispatcher:IntegrationDispatcher._persist_loop_status
[INTERNAL] dispatcher.IntegrationDispatcher._load_checkpoint → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[INTERNAL] dispatcher.IntegrationDispatcher._load_loop_status → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, protocol:CredentialService.get, ...+1
[INTERNAL] dispatcher.IntegrationDispatcher._persist_checkpoint → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[INTERNAL] dispatcher.IntegrationDispatcher._persist_event → audit_schemas:PolicyActivationAudit.to_dict, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, ...+35
[INTERNAL] dispatcher.IntegrationDispatcher._persist_loop_status → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[LEAF] dispatcher.IntegrationDispatcher._publish_checkpoint_needed
[INTERNAL] dispatcher.IntegrationDispatcher._publish_event → audit_schemas:PolicyActivationAudit.to_dict, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, ...+31
[SUPERSET] dispatcher.IntegrationDispatcher._trigger_next_stage → loop_events:LoopEvent.create
[SUPERSET] dispatcher.IntegrationDispatcher._update_loop_status → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, dispatcher:IntegrationDispatcher._persist_loop_status, protocol:CredentialService.get
[CANONICAL] dispatcher.IntegrationDispatcher.dispatch → dispatcher:IntegrationDispatcher._check_db_idempotency, dispatcher:IntegrationDispatcher._check_human_checkpoint_needed, dispatcher:IntegrationDispatcher._execute_handlers, dispatcher:IntegrationDispatcher._get_or_create_loop_status, dispatcher:IntegrationDispatcher._load_loop_status, ...+7
[INTERNAL] dispatcher.IntegrationDispatcher.get_loop_status → dispatcher:IntegrationDispatcher._load_loop_status
[WRAPPER] dispatcher.IntegrationDispatcher.get_pending_checkpoints
[WRAPPER] dispatcher.IntegrationDispatcher.is_bridge_enabled → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] dispatcher.IntegrationDispatcher.register_handler
[SUPERSET] dispatcher.IntegrationDispatcher.resolve_checkpoint → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, dispatcher:IntegrationDispatcher._load_checkpoint, dispatcher:IntegrationDispatcher._persist_checkpoint, dispatcher:IntegrationDispatcher.dispatch, ...+3
[SUPERSET] dispatcher.IntegrationDispatcher.retry_failed_stage → dispatcher:IntegrationDispatcher.dispatch, dispatcher:IntegrationDispatcher.get_loop_status, loop_events:LoopEvent.create
[SUPERSET] dispatcher.IntegrationDispatcher.revert_loop → dispatcher:IntegrationDispatcher._persist_loop_status, dispatcher:IntegrationDispatcher.get_loop_status, loop_events:RoutingAdjustment.rollback
[WRAPPER] external_response_driver.ExternalResponseService.__init__
[INTERNAL] external_response_driver.ExternalResponseService.get_interpreted → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[ENTRY] external_response_driver.ExternalResponseService.get_pending_interpretations → connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list, http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[ENTRY] external_response_driver.ExternalResponseService.get_raw_for_interpretation → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[INTERNAL] external_response_driver.ExternalResponseService.interpret → datasource_model:DataSourceRegistry.update, http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[LEAF] external_response_driver.ExternalResponseService.record_raw_response
[WRAPPER] external_response_driver.get_interpreted_response → external_response_driver:ExternalResponseService.get_interpreted
[WRAPPER] external_response_driver.interpret_response → external_response_driver:ExternalResponseService.interpret
[WRAPPER] external_response_driver.record_external_response → external_response_driver:ExternalResponseService.record_raw_response
[WRAPPER] file_storage_base.DownloadResult.success
[WRAPPER] file_storage_base.FileMetadata.to_dict
[WRAPPER] file_storage_base.FileStorageAdapter.connect
[WRAPPER] file_storage_base.FileStorageAdapter.copy
[WRAPPER] file_storage_base.FileStorageAdapter.delete
[WRAPPER] file_storage_base.FileStorageAdapter.delete_many
[WRAPPER] file_storage_base.FileStorageAdapter.disconnect
[WRAPPER] file_storage_base.FileStorageAdapter.download
[WRAPPER] file_storage_base.FileStorageAdapter.download_stream
[WRAPPER] file_storage_base.FileStorageAdapter.exists
[WRAPPER] file_storage_base.FileStorageAdapter.generate_presigned_url
[WRAPPER] file_storage_base.FileStorageAdapter.get_metadata
[WRAPPER] file_storage_base.FileStorageAdapter.health_check → connector_registry:FileConnector.list_files, file_storage_base:FileStorageAdapter.list_files, gcs_adapter:GCSAdapter.list_files, s3_adapter:S3Adapter.list_files
[WRAPPER] file_storage_base.FileStorageAdapter.list_files
[WRAPPER] file_storage_base.FileStorageAdapter.upload
[WRAPPER] file_storage_base.UploadResult.success
[ENTRY] founder_ops_adapter.FounderOpsAdapter.to_summary_response → founder_ops_adapter:FounderOpsAdapter.to_summary_view
[LEAF] founder_ops_adapter.FounderOpsAdapter.to_summary_view
[LEAF] gcs_adapter.GCSAdapter.__init__
[LEAF] gcs_adapter.GCSAdapter.connect
[LEAF] gcs_adapter.GCSAdapter.copy
[LEAF] gcs_adapter.GCSAdapter.delete
[LEAF] gcs_adapter.GCSAdapter.delete_many
[WRAPPER] gcs_adapter.GCSAdapter.disconnect
[LEAF] gcs_adapter.GCSAdapter.download
[LEAF] gcs_adapter.GCSAdapter.download_stream
[LEAF] gcs_adapter.GCSAdapter.exists
[LEAF] gcs_adapter.GCSAdapter.generate_presigned_url
[LEAF] gcs_adapter.GCSAdapter.get_metadata
[SUPERSET] gcs_adapter.GCSAdapter.list_files → connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list
[LEAF] gcs_adapter.GCSAdapter.upload
[WRAPPER] graduation_engine.CapabilityGates.can_auto_activate_policy → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] graduation_engine.CapabilityGates.can_auto_apply_recovery → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] graduation_engine.CapabilityGates.can_full_auto_routing
[SUPERSET] graduation_engine.CapabilityGates.get_blocked_capabilities → graduation_engine:CapabilityGates.can_auto_activate_policy, graduation_engine:CapabilityGates.can_auto_apply_recovery, graduation_engine:CapabilityGates.can_full_auto_routing
[SUPERSET] graduation_engine.CapabilityGates.get_unlocked_capabilities → graduation_engine:CapabilityGates.can_auto_activate_policy, graduation_engine:CapabilityGates.can_auto_apply_recovery, graduation_engine:CapabilityGates.can_full_auto_routing
[WRAPPER] graduation_engine.ComputedGraduationStatus.is_degraded
[WRAPPER] graduation_engine.ComputedGraduationStatus.is_graduated
[LEAF] graduation_engine.ComputedGraduationStatus.status_label
[LEAF] graduation_engine.ComputedGraduationStatus.to_api_response
[WRAPPER] graduation_engine.GraduationEngine.__init__
[LEAF] graduation_engine.GraduationEngine._check_degradation
[INTERNAL] graduation_engine.GraduationEngine._evaluate_gate1 → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[INTERNAL] graduation_engine.GraduationEngine._evaluate_gate2 → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[INTERNAL] graduation_engine.GraduationEngine._evaluate_gate3 → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[CANONICAL] graduation_engine.GraduationEngine.compute → graduation_engine:GraduationEngine._check_degradation, graduation_engine:GraduationEngine._evaluate_gate1, graduation_engine:GraduationEngine._evaluate_gate2, graduation_engine:GraduationEngine._evaluate_gate3
[WRAPPER] graduation_engine.SimulationState.is_demo_mode
[WRAPPER] graduation_engine.SimulationState.to_display
[WRAPPER] http_connector.HttpConnectorError.__init__ → bridges:IncidentToCatalogBridge.__init__, bridges:LoopStatusBridge.__init__, bridges:PatternToRecoveryBridge.__init__, bridges:PolicyToRoutingBridge.__init__, bridges:RecoveryToPolicyBridge.__init__, ...+54
[WRAPPER] http_connector.HttpConnectorService.__init__
[LEAF] http_connector.HttpConnectorService._build_url
[LEAF] http_connector.HttpConnectorService._check_rate_limit
[SUPERSET] http_connector.HttpConnectorService._get_auth_headers → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[LEAF] http_connector.HttpConnectorService._record_request
[INTERNAL] http_connector.HttpConnectorService._resolve_endpoint → connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list
[CANONICAL] http_connector.HttpConnectorService.execute → connector_registry:ConnectorRegistry.delete, connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.delete, datasource_model:DataSourceRegistry.get, file_storage_base:FileStorageAdapter.delete, ...+14
[WRAPPER] http_connector.HttpConnectorService.id
[WRAPPER] http_connector.RateLimitExceededError.__init__ → bridges:IncidentToCatalogBridge.__init__, bridges:LoopStatusBridge.__init__, bridges:PatternToRecoveryBridge.__init__, bridges:PolicyToRoutingBridge.__init__, bridges:RecoveryToPolicyBridge.__init__, ...+54
[WRAPPER] iam_engine.AccessDecision.to_dict
[INTERNAL] iam_engine.IAMService.__init__ → iam_engine:IAMService._setup_default_roles
[WRAPPER] iam_engine.IAMService._create_system_identity → iam_engine:IAMService._expand_role_permissions
[INTERNAL] iam_engine.IAMService._expand_role_permissions → datasource_model:DataSourceRegistry.update
[WRAPPER] iam_engine.IAMService._resolve_api_key_identity → iam_engine:IAMService._expand_role_permissions
[INTERNAL] iam_engine.IAMService._resolve_clerk_identity → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, iam_engine:IAMService._expand_role_permissions, protocol:CredentialService.get
[WRAPPER] iam_engine.IAMService._setup_default_roles
[LEAF] iam_engine.IAMService.check_access
[WRAPPER] iam_engine.IAMService.define_resource_permissions
[WRAPPER] iam_engine.IAMService.define_role
[LEAF] iam_engine.IAMService.get_access_log
[WRAPPER] iam_engine.IAMService.grant_role
[WRAPPER] iam_engine.IAMService.list_resources
[WRAPPER] iam_engine.IAMService.list_roles
[SUPERSET] iam_engine.IAMService.resolve_identity → iam_engine:IAMService._create_system_identity, iam_engine:IAMService._resolve_api_key_identity, iam_engine:IAMService._resolve_clerk_identity
[WRAPPER] iam_engine.IAMService.revoke_role
[WRAPPER] iam_engine.Identity.has_all_roles
[WRAPPER] iam_engine.Identity.has_any_role
[WRAPPER] iam_engine.Identity.has_permission
[WRAPPER] iam_engine.Identity.has_role
[INTERNAL] iam_engine.Identity.to_dict → connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list
[WRAPPER] integrations_facade.IntegrationsFacade.__init__
[LEAF] integrations_facade.IntegrationsFacade.create_integration
[WRAPPER] integrations_facade.IntegrationsFacade.delete_integration
[LEAF] integrations_facade.IntegrationsFacade.disable_integration
[LEAF] integrations_facade.IntegrationsFacade.enable_integration
[ENTRY] integrations_facade.IntegrationsFacade.get_health_status → integrations_facade:IntegrationsFacade.get_integration
[LEAF] integrations_facade.IntegrationsFacade.get_integration
[LEAF] integrations_facade.IntegrationsFacade.get_limits_status
[LEAF] integrations_facade.IntegrationsFacade.list_integrations
[ENTRY] integrations_facade.IntegrationsFacade.test_credentials → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[LEAF] integrations_facade.IntegrationsFacade.update_integration
[LEAF] integrations_facade.get_integrations_facade
[LEAF] lambda_adapter.LambdaAdapter.__init__
[INTERNAL] lambda_adapter.LambdaAdapter.connect → cloud_functions_adapter:CloudFunctionsAdapter.list_functions, connector_registry:ServerlessConnector.list_functions, lambda_adapter:LambdaAdapter.list_functions, serverless_base:ServerlessAdapter.list_functions
[WRAPPER] lambda_adapter.LambdaAdapter.disconnect
[WRAPPER] lambda_adapter.LambdaAdapter.function_exists → cloud_functions_adapter:CloudFunctionsAdapter.get_function_info, lambda_adapter:LambdaAdapter.get_function_info, serverless_base:ServerlessAdapter.get_function_info
[INTERNAL] lambda_adapter.LambdaAdapter.get_function_info → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[SUPERSET] lambda_adapter.LambdaAdapter.invoke → cloud_functions_adapter:CloudFunctionsAdapter.invoke, connector_registry:ConnectorRegistry.get, connector_registry:ServerlessConnector.invoke, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get, ...+1
[CANONICAL] lambda_adapter.LambdaAdapter.invoke_batch → cloud_functions_adapter:CloudFunctionsAdapter.invoke, connector_registry:ServerlessConnector.invoke, lambda_adapter:LambdaAdapter.invoke, serverless_base:ServerlessAdapter.invoke
[SUPERSET] lambda_adapter.LambdaAdapter.list_functions → cloud_functions_adapter:CloudFunctionsAdapter.list_functions, connector_registry:ConnectorRegistry.get, connector_registry:ServerlessConnector.list_functions, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get, ...+1
[WRAPPER] loop_events.ConfidenceBand.allows_auto_apply
[LEAF] loop_events.ConfidenceBand.from_confidence
[WRAPPER] loop_events.ConfidenceBand.requires_human_review
[LEAF] loop_events.ConfidenceCalculator.calculate_recovery_confidence
[LEAF] loop_events.ConfidenceCalculator.get_confirmation_level
[WRAPPER] loop_events.ConfidenceCalculator.should_auto_apply
[INTERNAL] loop_events.HumanCheckpoint.create → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] loop_events.HumanCheckpoint.is_pending
[WRAPPER] loop_events.HumanCheckpoint.resolve
[LEAF] loop_events.LoopEvent.create
[WRAPPER] loop_events.LoopEvent.is_blocked
[WRAPPER] loop_events.LoopEvent.is_success
[WRAPPER] loop_events.LoopEvent.to_dict
[LEAF] loop_events.LoopStatus._generate_narrative
[WRAPPER] loop_events.LoopStatus.completion_pct
[SUPERSET] loop_events.LoopStatus.to_console_display → loop_events:LoopStatus._generate_narrative
[INTERNAL] loop_events.LoopStatus.to_dict → audit_schemas:PolicyActivationAudit.to_dict, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, ...+30
[WRAPPER] loop_events.PatternMatchResult.from_match → loop_events:ConfidenceBand.from_confidence
[WRAPPER] loop_events.PatternMatchResult.no_match
[WRAPPER] loop_events.PatternMatchResult.should_auto_proceed
[WRAPPER] loop_events.PatternMatchResult.to_dict
[LEAF] loop_events.PolicyRule.add_confirmation
[INTERNAL] loop_events.PolicyRule.create → loop_events:ConfidenceBand.from_confidence
[LEAF] loop_events.PolicyRule.record_regret
[LEAF] loop_events.PolicyRule.record_shadow_evaluation
[LEAF] loop_events.PolicyRule.shadow_block_rate
[WRAPPER] loop_events.PolicyRule.to_dict
[LEAF] loop_events.RecoverySuggestion.add_confirmation
[INTERNAL] loop_events.RecoverySuggestion.create → loop_events:ConfidenceBand.from_confidence
[WRAPPER] loop_events.RecoverySuggestion.none_available
[WRAPPER] loop_events.RecoverySuggestion.to_dict
[SUPERSET] loop_events.RoutingAdjustment.check_kpi_regression → loop_events:RoutingAdjustment.rollback
[LEAF] loop_events.RoutingAdjustment.create
[LEAF] loop_events.RoutingAdjustment.effective_magnitude
[WRAPPER] loop_events.RoutingAdjustment.rollback
[WRAPPER] loop_events.RoutingAdjustment.to_dict
[CANONICAL] loop_events.ensure_json_serializable → audit_schemas:PolicyActivationAudit.to_dict, channel_engine:NotifyChannelConfig.to_dict, channel_engine:NotifyChannelConfigResponse.to_dict, channel_engine:NotifyChannelError.to_dict, channel_engine:NotifyDeliveryResult.to_dict, ...+31
[WRAPPER] mcp_connector.McpApprovalRequiredError.__init__ → bridges:IncidentToCatalogBridge.__init__, bridges:LoopStatusBridge.__init__, bridges:PatternToRecoveryBridge.__init__, bridges:PolicyToRoutingBridge.__init__, bridges:RecoveryToPolicyBridge.__init__, ...+54
[WRAPPER] mcp_connector.McpConnectorError.__init__ → bridges:IncidentToCatalogBridge.__init__, bridges:LoopStatusBridge.__init__, bridges:PatternToRecoveryBridge.__init__, bridges:PolicyToRoutingBridge.__init__, bridges:RecoveryToPolicyBridge.__init__, ...+54
[LEAF] mcp_connector.McpConnectorService.__init__
[WRAPPER] mcp_connector.McpConnectorService._build_mcp_request
[LEAF] mcp_connector.McpConnectorService._check_rate_limit
[INTERNAL] mcp_connector.McpConnectorService._get_api_key → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[LEAF] mcp_connector.McpConnectorService._record_request
[SUPERSET] mcp_connector.McpConnectorService._resolve_tool → connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list
[LEAF] mcp_connector.McpConnectorService._validate_against_schema
[CANONICAL] mcp_connector.McpConnectorService.execute → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, http_connector:HttpConnectorService._check_rate_limit, http_connector:HttpConnectorService._record_request, mcp_connector:McpConnectorService._build_mcp_request, ...+6
[LEAF] mcp_connector.McpConnectorService.get_available_tools
[WRAPPER] mcp_connector.McpConnectorService.id
[WRAPPER] mcp_connector.McpRateLimitExceededError.__init__ → bridges:IncidentToCatalogBridge.__init__, bridges:LoopStatusBridge.__init__, bridges:PatternToRecoveryBridge.__init__, bridges:PolicyToRoutingBridge.__init__, bridges:RecoveryToPolicyBridge.__init__, ...+54
[WRAPPER] mcp_connector.McpSchemaValidationError.__init__ → bridges:IncidentToCatalogBridge.__init__, bridges:LoopStatusBridge.__init__, bridges:PatternToRecoveryBridge.__init__, bridges:PolicyToRoutingBridge.__init__, bridges:RecoveryToPolicyBridge.__init__, ...+54
[LEAF] pgvector_adapter.PGVectorAdapter.__init__
[INTERNAL] pgvector_adapter.PGVectorAdapter.connect → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[WRAPPER] pgvector_adapter.PGVectorAdapter.create_namespace
[SUPERSET] pgvector_adapter.PGVectorAdapter.delete → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[WRAPPER] pgvector_adapter.PGVectorAdapter.delete_namespace → connector_registry:ConnectorRegistry.delete, datasource_model:DataSourceRegistry.delete, file_storage_base:FileStorageAdapter.delete, gcs_adapter:GCSAdapter.delete, pgvector_adapter:PGVectorAdapter.delete, ...+4
[LEAF] pgvector_adapter.PGVectorAdapter.disconnect
[LEAF] pgvector_adapter.PGVectorAdapter.get_stats
[LEAF] pgvector_adapter.PGVectorAdapter.list_namespaces
[CANONICAL] pgvector_adapter.PGVectorAdapter.query → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[INTERNAL] pgvector_adapter.PGVectorAdapter.upsert → http_connector:HttpConnectorService.execute, mcp_connector:McpConnectorService.execute, sql_gateway:SqlGatewayService.execute
[LEAF] pinecone_adapter.PineconeAdapter.__init__
[LEAF] pinecone_adapter.PineconeAdapter.connect
[WRAPPER] pinecone_adapter.PineconeAdapter.create_namespace
[CANONICAL] pinecone_adapter.PineconeAdapter.delete → connector_registry:ConnectorRegistry.delete, datasource_model:DataSourceRegistry.delete, file_storage_base:FileStorageAdapter.delete, gcs_adapter:GCSAdapter.delete, pgvector_adapter:PGVectorAdapter.delete, ...+3
[ENTRY] pinecone_adapter.PineconeAdapter.delete_namespace → connector_registry:ConnectorRegistry.delete, datasource_model:DataSourceRegistry.delete, file_storage_base:FileStorageAdapter.delete, gcs_adapter:GCSAdapter.delete, pgvector_adapter:PGVectorAdapter.delete, ...+4
[WRAPPER] pinecone_adapter.PineconeAdapter.disconnect
[LEAF] pinecone_adapter.PineconeAdapter.get_stats
[ENTRY] pinecone_adapter.PineconeAdapter.list_namespaces → connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list
[ENTRY] pinecone_adapter.PineconeAdapter.query → pgvector_adapter:PGVectorAdapter.query, runtime_adapter:RuntimeAdapter.query, vector_stores_base:VectorStoreAdapter.query, weaviate_adapter:WeaviateAdapter.query
[SUPERSET] pinecone_adapter.PineconeAdapter.upsert → pgvector_adapter:PGVectorAdapter.upsert, vector_stores_base:VectorStoreAdapter.upsert, weaviate_adapter:WeaviateAdapter.upsert
[WRAPPER] prevention_contract.PreventionContractViolation.__init__ → bridges:IncidentToCatalogBridge.__init__, bridges:LoopStatusBridge.__init__, bridges:PatternToRecoveryBridge.__init__, bridges:PolicyToRoutingBridge.__init__, bridges:RecoveryToPolicyBridge.__init__, ...+54
[WRAPPER] prevention_contract.assert_no_deletion
[WRAPPER] prevention_contract.assert_prevention_immutable
[LEAF] prevention_contract.validate_prevention_candidate
[SUPERSET] prevention_contract.validate_prevention_for_graduation → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] protocol.CredentialService.get
[WRAPPER] runtime_adapter.RuntimeAdapter.__init__
[WRAPPER] runtime_adapter.RuntimeAdapter.describe_skill
[WRAPPER] runtime_adapter.RuntimeAdapter.get_capabilities
[WRAPPER] runtime_adapter.RuntimeAdapter.get_resource_contract
[WRAPPER] runtime_adapter.RuntimeAdapter.get_skill_descriptors
[WRAPPER] runtime_adapter.RuntimeAdapter.get_supported_queries
[WRAPPER] runtime_adapter.RuntimeAdapter.list_skills
[LEAF] runtime_adapter.RuntimeAdapter.query
[WRAPPER] runtime_adapter.get_runtime_adapter
[LEAF] s3_adapter.S3Adapter.__init__
[LEAF] s3_adapter.S3Adapter.connect
[LEAF] s3_adapter.S3Adapter.copy
[LEAF] s3_adapter.S3Adapter.delete
[SUPERSET] s3_adapter.S3Adapter.delete_many → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] s3_adapter.S3Adapter.disconnect
[ENTRY] s3_adapter.S3Adapter.download → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[LEAF] s3_adapter.S3Adapter.download_stream
[LEAF] s3_adapter.S3Adapter.exists
[ENTRY] s3_adapter.S3Adapter.generate_presigned_url → file_storage_base:FileStorageAdapter.generate_presigned_url, gcs_adapter:GCSAdapter.generate_presigned_url
[INTERNAL] s3_adapter.S3Adapter.get_metadata → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[SUPERSET] s3_adapter.S3Adapter.list_files → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[CANONICAL] s3_adapter.S3Adapter.upload → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] serverless_base.FunctionInfo.to_dict
[WRAPPER] serverless_base.InvocationRequest.to_dict
[WRAPPER] serverless_base.InvocationResult.success
[WRAPPER] serverless_base.InvocationResult.to_dict
[WRAPPER] serverless_base.ServerlessAdapter.connect
[WRAPPER] serverless_base.ServerlessAdapter.disconnect
[WRAPPER] serverless_base.ServerlessAdapter.function_exists
[WRAPPER] serverless_base.ServerlessAdapter.get_function_info
[WRAPPER] serverless_base.ServerlessAdapter.health_check → cloud_functions_adapter:CloudFunctionsAdapter.list_functions, connector_registry:ServerlessConnector.list_functions, lambda_adapter:LambdaAdapter.list_functions, serverless_base:ServerlessAdapter.list_functions
[WRAPPER] serverless_base.ServerlessAdapter.invoke
[WRAPPER] serverless_base.ServerlessAdapter.invoke_batch
[WRAPPER] serverless_base.ServerlessAdapter.list_functions
[WRAPPER] service.CredentialService.__init__
[LEAF] service.CredentialService._audit
[LEAF] service.CredentialService._validate_name
[LEAF] service.CredentialService._validate_secret_data
[LEAF] service.CredentialService._validate_tenant_id
[ENTRY] service.CredentialService.delete_credential → service:CredentialService._audit, vault:CredentialVault.delete_credential, vault:EnvCredentialVault.delete_credential, vault:HashiCorpVault.delete_credential
[LEAF] service.CredentialService.get_access_log
[SUPERSET] service.CredentialService.get_credential → service:CredentialService._audit, vault:CredentialVault.get_credential, vault:EnvCredentialVault.get_credential, vault:HashiCorpVault.get_credential
[ENTRY] service.CredentialService.get_expiring_credentials → service:CredentialService.list_credentials, vault:CredentialVault.list_credentials, vault:EnvCredentialVault.list_credentials, vault:HashiCorpVault.list_credentials
[CANONICAL] service.CredentialService.get_rotatable_credentials → service:CredentialService.list_credentials, vault:CredentialVault.list_credentials, vault:EnvCredentialVault.list_credentials, vault:HashiCorpVault.list_credentials
[ENTRY] service.CredentialService.get_secret_value → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get, service:CredentialService.get_credential, vault:CredentialVault.get_credential, ...+2
[INTERNAL] service.CredentialService.list_credentials → vault:CredentialVault.list_credentials, vault:EnvCredentialVault.list_credentials, vault:HashiCorpVault.list_credentials
[ENTRY] service.CredentialService.rotate_credential → service:CredentialService._audit, vault:CredentialVault.rotate_credential, vault:EnvCredentialVault.rotate_credential, vault:HashiCorpVault.rotate_credential
[ENTRY] service.CredentialService.store_credential → service:CredentialService._audit, service:CredentialService._validate_name, service:CredentialService._validate_secret_data, service:CredentialService._validate_tenant_id, vault:CredentialVault.store_credential, ...+2
[INTERNAL] service.CredentialService.update_credential → service:CredentialService._audit, vault:CredentialVault.update_credential, vault:EnvCredentialVault.update_credential, vault:HashiCorpVault.update_credential
[LEAF] slack_adapter.SlackAdapter.__init__
[SUPERSET] slack_adapter.SlackAdapter._build_blocks → slack_adapter:SlackAdapter._get_priority_emoji
[WRAPPER] slack_adapter.SlackAdapter._get_priority_emoji → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[INTERNAL] slack_adapter.SlackAdapter.connect → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] slack_adapter.SlackAdapter.disconnect
[WRAPPER] slack_adapter.SlackAdapter.get_status → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[SUPERSET] slack_adapter.SlackAdapter.send → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get, slack_adapter:SlackAdapter._build_blocks
[CANONICAL] slack_adapter.SlackAdapter.send_batch → channel_engine:NotificationSender.send, channel_engine:NotifyChannelService.send, slack_adapter:SlackAdapter.send, smtp_adapter:SMTPAdapter.send, webhook_adapter:WebhookAdapter.send
[SUPERSET] slack_adapter.SlackAdapter.send_thread_reply → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[LEAF] smtp_adapter.SMTPAdapter.__init__
[SUPERSET] smtp_adapter.SMTPAdapter._build_email → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[INTERNAL] smtp_adapter.SMTPAdapter.connect → cloud_functions_adapter:CloudFunctionsAdapter.connect, connector_registry:BaseConnector.connect, connector_registry:FileConnector.connect, connector_registry:ServerlessConnector.connect, connector_registry:VectorConnector.connect, ...+11
[WRAPPER] smtp_adapter.SMTPAdapter.disconnect
[WRAPPER] smtp_adapter.SMTPAdapter.get_status → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[INTERNAL] smtp_adapter.SMTPAdapter.send → cloud_functions_adapter:CloudFunctionsAdapter.connect, connector_registry:BaseConnector.connect, connector_registry:ConnectorRegistry.list, connector_registry:FileConnector.connect, connector_registry:ServerlessConnector.connect, ...+15
[CANONICAL] smtp_adapter.SMTPAdapter.send_batch → channel_engine:NotificationSender.send, channel_engine:NotifyChannelService.send, slack_adapter:SlackAdapter.send, smtp_adapter:SMTPAdapter.send, webhook_adapter:WebhookAdapter.send
[WRAPPER] sql_gateway.SqlGatewayService.__init__
[LEAF] sql_gateway.SqlGatewayService._check_sql_injection
[SUPERSET] sql_gateway.SqlGatewayService._coerce_parameter → sql_gateway:SqlGatewayService._check_sql_injection
[INTERNAL] sql_gateway.SqlGatewayService._get_connection_string → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[SUPERSET] sql_gateway.SqlGatewayService._resolve_template → connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list
[SUPERSET] sql_gateway.SqlGatewayService._validate_parameters → connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list, sql_gateway:SqlGatewayService._coerce_parameter
[CANONICAL] sql_gateway.SqlGatewayService.execute → cloud_functions_adapter:CloudFunctionsAdapter.connect, connector_registry:BaseConnector.connect, connector_registry:ConnectorRegistry.get, connector_registry:FileConnector.connect, connector_registry:ServerlessConnector.connect, ...+18
[WRAPPER] sql_gateway.SqlGatewayService.id
[WRAPPER] vault.CredentialData.credential_id
[WRAPPER] vault.CredentialData.tenant_id
[WRAPPER] vault.CredentialVault.delete_credential
[WRAPPER] vault.CredentialVault.get_credential
[WRAPPER] vault.CredentialVault.get_metadata
[WRAPPER] vault.CredentialVault.list_credentials
[WRAPPER] vault.CredentialVault.rotate_credential
[WRAPPER] vault.CredentialVault.store_credential
[WRAPPER] vault.CredentialVault.update_credential
[WRAPPER] vault.EnvCredentialVault.__init__
[LEAF] vault.EnvCredentialVault.delete_credential
[SUPERSET] vault.EnvCredentialVault.get_credential → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] vault.EnvCredentialVault.get_metadata → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[LEAF] vault.EnvCredentialVault.list_credentials
[WRAPPER] vault.EnvCredentialVault.rotate_credential → service:CredentialService.update_credential, vault:CredentialVault.update_credential, vault:EnvCredentialVault.update_credential, vault:HashiCorpVault.update_credential
[LEAF] vault.EnvCredentialVault.store_credential
[LEAF] vault.EnvCredentialVault.update_credential
[LEAF] vault.HashiCorpVault.__init__
[INTERNAL] vault.HashiCorpVault.delete_credential → connector_registry:ConnectorRegistry.delete, datasource_model:DataSourceRegistry.delete, file_storage_base:FileStorageAdapter.delete, gcs_adapter:GCSAdapter.delete, pgvector_adapter:PGVectorAdapter.delete, ...+4
[SUPERSET] vault.HashiCorpVault.get_credential → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[SUPERSET] vault.HashiCorpVault.get_metadata → service:CredentialService.get_credential, vault:CredentialVault.get_credential, vault:EnvCredentialVault.get_credential, vault:HashiCorpVault.get_credential
[SUPERSET] vault.HashiCorpVault.list_credentials → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, file_storage_base:FileStorageAdapter.get_metadata, gcs_adapter:GCSAdapter.get_metadata, protocol:CredentialService.get, ...+4
[WRAPPER] vault.HashiCorpVault.rotate_credential → service:CredentialService.update_credential, vault:CredentialVault.update_credential, vault:EnvCredentialVault.update_credential, vault:HashiCorpVault.update_credential
[LEAF] vault.HashiCorpVault.store_credential
[CANONICAL] vault.HashiCorpVault.update_credential → service:CredentialService.get_credential, vault:CredentialVault.get_credential, vault:EnvCredentialVault.get_credential, vault:HashiCorpVault.get_credential
[LEAF] vault.create_credential_vault
[WRAPPER] vector_stores_base.DeleteResult.success
[WRAPPER] vector_stores_base.IndexStats.to_dict
[WRAPPER] vector_stores_base.QueryResult.to_dict
[WRAPPER] vector_stores_base.UpsertResult.success
[WRAPPER] vector_stores_base.VectorRecord.to_dict
[WRAPPER] vector_stores_base.VectorStoreAdapter.connect
[WRAPPER] vector_stores_base.VectorStoreAdapter.create_namespace
[WRAPPER] vector_stores_base.VectorStoreAdapter.delete
[WRAPPER] vector_stores_base.VectorStoreAdapter.delete_namespace
[WRAPPER] vector_stores_base.VectorStoreAdapter.disconnect
[WRAPPER] vector_stores_base.VectorStoreAdapter.get_stats
[WRAPPER] vector_stores_base.VectorStoreAdapter.health_check → pgvector_adapter:PGVectorAdapter.get_stats, pinecone_adapter:PineconeAdapter.get_stats, vector_stores_base:VectorStoreAdapter.get_stats, weaviate_adapter:WeaviateAdapter.get_stats
[WRAPPER] vector_stores_base.VectorStoreAdapter.list_namespaces
[WRAPPER] vector_stores_base.VectorStoreAdapter.query
[WRAPPER] vector_stores_base.VectorStoreAdapter.upsert
[LEAF] weaviate_adapter.WeaviateAdapter.__init__
[LEAF] weaviate_adapter.WeaviateAdapter._build_filter
[WRAPPER] weaviate_adapter.WeaviateAdapter._create_collection
[INTERNAL] weaviate_adapter.WeaviateAdapter.connect → file_storage_base:FileStorageAdapter.exists, gcs_adapter:GCSAdapter.exists, s3_adapter:S3Adapter.exists, weaviate_adapter:WeaviateAdapter._create_collection
[WRAPPER] weaviate_adapter.WeaviateAdapter.create_namespace
[CANONICAL] weaviate_adapter.WeaviateAdapter.delete → connector_registry:ConnectorRegistry.delete, connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.delete, datasource_model:DataSourceRegistry.get, file_storage_base:FileStorageAdapter.delete, ...+8
[WRAPPER] weaviate_adapter.WeaviateAdapter.delete_namespace → connector_registry:ConnectorRegistry.delete, datasource_model:DataSourceRegistry.delete, file_storage_base:FileStorageAdapter.delete, gcs_adapter:GCSAdapter.delete, pgvector_adapter:PGVectorAdapter.delete, ...+4
[WRAPPER] weaviate_adapter.WeaviateAdapter.disconnect
[SUPERSET] weaviate_adapter.WeaviateAdapter.get_stats → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[SUPERSET] weaviate_adapter.WeaviateAdapter.list_namespaces → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[SUPERSET] weaviate_adapter.WeaviateAdapter.query → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get, weaviate_adapter:WeaviateAdapter._build_filter
[LEAF] weaviate_adapter.WeaviateAdapter.upsert
[LEAF] webhook_adapter.CircuitBreaker.can_execute
[LEAF] webhook_adapter.CircuitBreaker.record_failure
[LEAF] webhook_adapter.CircuitBreaker.record_success
[LEAF] webhook_adapter.WebhookAdapter.__init__
[SUPERSET] webhook_adapter.WebhookAdapter._attempt_delivery → webhook_adapter:WebhookAdapter._sign_payload
[SUPERSET] webhook_adapter.WebhookAdapter._deliver_with_retry → channel_engine:NotifyChannelConfig.record_failure, channel_engine:NotifyChannelConfig.record_success, webhook_adapter:CircuitBreaker.can_execute, webhook_adapter:CircuitBreaker.record_failure, webhook_adapter:CircuitBreaker.record_success, ...+2
[LEAF] webhook_adapter.WebhookAdapter._get_circuit_breaker
[LEAF] webhook_adapter.WebhookAdapter._sign_payload
[LEAF] webhook_adapter.WebhookAdapter.connect
[LEAF] webhook_adapter.WebhookAdapter.disconnect
[ENTRY] webhook_adapter.WebhookAdapter.get_circuit_breaker_status → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[WRAPPER] webhook_adapter.WebhookAdapter.get_delivery_details → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[ENTRY] webhook_adapter.WebhookAdapter.get_status → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[CANONICAL] webhook_adapter.WebhookAdapter.send → webhook_adapter:WebhookAdapter._deliver_with_retry
[SUPERSET] webhook_adapter.WebhookAdapter.send_batch → channel_engine:NotificationSender.send, channel_engine:NotifyChannelService.send, slack_adapter:SlackAdapter.send, smtp_adapter:SMTPAdapter.send, webhook_adapter:WebhookAdapter.send
[WRAPPER] webhook_adapter.WebhookDelivery.to_dict
[WRAPPER] worker_registry_driver.WorkerRegistryService.__init__
[WRAPPER] worker_registry_driver.WorkerRegistryService.deprecate_worker → worker_registry_driver:WorkerRegistryService.update_worker_status
[SUPERSET] worker_registry_driver.WorkerRegistryService.get_effective_worker_config → datasource_model:DataSourceRegistry.update, worker_registry_driver:WorkerRegistryService.get_tenant_worker_config, worker_registry_driver:WorkerRegistryService.get_worker_or_raise
[LEAF] worker_registry_driver.WorkerRegistryService.get_tenant_worker_config
[WRAPPER] worker_registry_driver.WorkerRegistryService.get_worker → connector_registry:ConnectorRegistry.get, datasource_model:DataSourceRegistry.get, protocol:CredentialService.get
[CANONICAL] worker_registry_driver.WorkerRegistryService.get_worker_details → worker_registry_driver:WorkerRegistryService.get_worker_or_raise
[INTERNAL] worker_registry_driver.WorkerRegistryService.get_worker_or_raise → worker_registry_driver:WorkerRegistryService.get_worker
[INTERNAL] worker_registry_driver.WorkerRegistryService.get_worker_summary → worker_registry_driver:WorkerRegistryService.get_worker_or_raise
[SUPERSET] worker_registry_driver.WorkerRegistryService.get_workers_for_tenant → worker_registry_driver:WorkerRegistryService.get_effective_worker_config, worker_registry_driver:WorkerRegistryService.list_available_workers
[ENTRY] worker_registry_driver.WorkerRegistryService.is_worker_available → worker_registry_driver:WorkerRegistryService.get_worker
[ENTRY] worker_registry_driver.WorkerRegistryService.is_worker_enabled_for_tenant → worker_registry_driver:WorkerRegistryService.get_tenant_worker_config
[WRAPPER] worker_registry_driver.WorkerRegistryService.list_available_workers → worker_registry_driver:WorkerRegistryService.list_workers
[ENTRY] worker_registry_driver.WorkerRegistryService.list_tenant_worker_configs → connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list
[WRAPPER] worker_registry_driver.WorkerRegistryService.list_worker_summaries → worker_registry_driver:WorkerRegistryService.get_worker_summary, worker_registry_driver:WorkerRegistryService.list_workers
[SUPERSET] worker_registry_driver.WorkerRegistryService.list_workers → connector_registry:ConnectorRegistry.list, datasource_model:DataSourceRegistry.list
[ENTRY] worker_registry_driver.WorkerRegistryService.register_worker → worker_registry_driver:WorkerRegistryService.get_worker
[ENTRY] worker_registry_driver.WorkerRegistryService.set_tenant_worker_config → worker_registry_driver:WorkerRegistryService.get_tenant_worker_config, worker_registry_driver:WorkerRegistryService.get_worker_or_raise
[INTERNAL] worker_registry_driver.WorkerRegistryService.update_worker_status → worker_registry_driver:WorkerRegistryService.get_worker_or_raise
[WRAPPER] worker_registry_driver.get_worker_registry_service
[WRAPPER] workers_adapter.WorkersAdapter.calculate_cost_cents
[WRAPPER] workers_adapter.WorkersAdapter.convert_brand_request
[WRAPPER] workers_adapter.WorkersAdapter.execute_worker
[WRAPPER] workers_adapter.WorkersAdapter.replay_execution
[LEAF] workers_adapter.get_workers_adapter
```
