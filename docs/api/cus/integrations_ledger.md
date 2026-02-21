# CUS Domain Ledger: integrations

**Generated:** 2026-02-21T07:54:56.667404+00:00
**Total endpoints:** 54
**Unique method+path:** 54

| Method | Path | Operation | Summary |
|--------|------|-----------|---------|
| GET | /hoc/api/cus/connectors | list_connectors | List connectors for the tenant. |
| POST | /hoc/api/cus/connectors | register_connector | Register a new connector. |
| DELETE | /hoc/api/cus/connectors/{connector_id} | delete_connector | Delete a connector. |
| GET | /hoc/api/cus/connectors/{connector_id} | get_connector | Get a specific connector by ID. |
| PUT | /hoc/api/cus/connectors/{connector_id} | update_connector | Update a connector. |
| POST | /hoc/api/cus/connectors/{connector_id}/test | test_connector | Test a connector connection. |
| GET | /hoc/api/cus/datasources | list_sources | List data sources. |
| POST | /hoc/api/cus/datasources | create_source | Create a data source (GAP-113). |
| GET | /hoc/api/cus/datasources/stats | get_statistics | Get data source statistics. |
| DELETE | /hoc/api/cus/datasources/{source_id} | delete_source | Delete a data source. |
| GET | /hoc/api/cus/datasources/{source_id} | get_source | Get a specific data source. |
| PUT | /hoc/api/cus/datasources/{source_id} | update_source | Update a data source. |
| POST | /hoc/api/cus/datasources/{source_id}/activate | activate_source | Activate a data source. |
| POST | /hoc/api/cus/datasources/{source_id}/deactivate | deactivate_source | Deactivate a data source. |
| POST | /hoc/api/cus/datasources/{source_id}/test | test_connection | Test a data source connection. |
| GET | /hoc/api/cus/integrations | list_integrations | List all integrations for the tenant. |
| POST | /hoc/api/cus/integrations | create_integration | Create a new LLM integration. |
| GET | /hoc/api/cus/integrations/list | list_integrations_public |  |
| GET | /hoc/api/cus/integrations/mcp-servers | list_mcp_servers | List MCP servers. Tenant-scoped. |
| POST | /hoc/api/cus/integrations/mcp-servers | register_mcp_server | Register a new MCP server. Tenant-scoped. |
| DELETE | /hoc/api/cus/integrations/mcp-servers/{server_id} | delete_mcp_server | Delete MCP server. Tenant-scoped. |
| GET | /hoc/api/cus/integrations/mcp-servers/{server_id} | get_mcp_server | Get MCP server details. Tenant-scoped. |
| POST | /hoc/api/cus/integrations/mcp-servers/{server_id}/discover | discover_mcp_tools | Discover tools from MCP server. Tenant-scoped. |
| GET | /hoc/api/cus/integrations/mcp-servers/{server_id}/health | check_mcp_health | Health check MCP server. Tenant-scoped. |
| GET | /hoc/api/cus/integrations/mcp-servers/{server_id}/invocations | list_mcp_invocations | List invocations for MCP server. Tenant-scoped. |
| GET | /hoc/api/cus/integrations/mcp-servers/{server_id}/tools | list_mcp_tools | List tools for MCP server. Tenant-scoped. |
| POST | /hoc/api/cus/integrations/mcp-servers/{server_id}/tools/{tool_id}/invoke | invoke_mcp_tool | Invoke an MCP tool with governance. Tenant-scoped. |
| DELETE | /hoc/api/cus/integrations/{integration_id} | delete_integration | Delete an integration (soft delete). |
| GET | /hoc/api/cus/integrations/{integration_id} | get_integration | Get full details for a specific integration. |
| PUT | /hoc/api/cus/integrations/{integration_id} | update_integration | Update an existing integration. |
| POST | /hoc/api/cus/integrations/{integration_id}/disable | disable_integration | Disable an integration. |
| POST | /hoc/api/cus/integrations/{integration_id}/enable | enable_integration | Enable an integration. |
| GET | /hoc/api/cus/integrations/{integration_id}/health | get_integration_health | Get current health status without running a new check. |
| GET | /hoc/api/cus/integrations/{integration_id}/limits | get_integration_limits | Get current usage against configured limits. |
| POST | /hoc/api/cus/integrations/{integration_id}/test | test_integration_credentials | Test integration credentials and update health status. |
| GET | /hoc/api/cus/session/context | get_session_context | Get verified session context for the current authenticated u |
| GET | /hoc/api/cus/telemetry/daily-aggregates | get_daily_aggregates | Get daily aggregated usage for charts. |
| POST | /hoc/api/cus/telemetry/llm-usage | ingest_llm_usage | Ingest a single LLM usage telemetry record. |
| POST | /hoc/api/cus/telemetry/llm-usage/batch | ingest_llm_usage_batch | Ingest a batch of LLM usage telemetry records. |
| GET | /hoc/api/cus/telemetry/usage-history | get_usage_history | Get detailed usage history records. |
| GET | /hoc/api/cus/telemetry/usage-summary | get_usage_summary | Get aggregated usage summary for dashboard. |
| GET | /hoc/api/cus/v1/calls/{call_id} | get_call | Get single call truth. |
| POST | /hoc/api/cus/v1/chat/completions | chat_completions | OpenAI-compatible chat completions endpoint. |
| POST | /hoc/api/cus/v1/embeddings | embeddings | OpenAI-compatible embeddings endpoint. |
| GET | /hoc/api/cus/v1/incidents | list_incidents | List incidents (auto-grouped failures). |
| GET | /hoc/api/cus/v1/incidents/{incident_id} | get_incident | Get incident detail with timeline. |
| DELETE | /hoc/api/cus/v1/killswitch/key | unfreeze_key | Unfreeze an API key. |
| POST | /hoc/api/cus/v1/killswitch/key | freeze_key | Kill a single API key. |
| GET | /hoc/api/cus/v1/killswitch/status | get_killswitch_status | Get complete kill switch status for a tenant. |
| DELETE | /hoc/api/cus/v1/killswitch/tenant | unfreeze_tenant | Unfreeze a tenant. |
| POST | /hoc/api/cus/v1/killswitch/tenant | freeze_tenant | Hard stop everything for a tenant. |
| GET | /hoc/api/cus/v1/policies/active | get_active_policies | Get active guardrails - "What's protecting me right now?" |
| POST | /hoc/api/cus/v1/replay/{call_id} | replay_call | REPLAY PROVES ENFORCEMENT |
| GET | /hoc/api/cus/v1/status | proxy_status | Protection status endpoint - the pulse of your safety net. |
