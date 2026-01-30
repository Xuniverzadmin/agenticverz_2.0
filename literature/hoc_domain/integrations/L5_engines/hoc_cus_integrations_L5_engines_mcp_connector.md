# hoc_cus_integrations_L5_engines_mcp_connector

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/mcp_connector.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Model Context Protocol (MCP) tool invocation with governance

## Intent

**Role:** Model Context Protocol (MCP) tool invocation with governance
**Reference:** PIN-470, GAP-063
**Callers:** RetrievalMediator

## Purpose

Module: mcp_connector
Purpose: Model Context Protocol (MCP) tool invocation with governance.

---

## Classes

### `McpToolDefinition`
- **Docstring:** Definition of an MCP tool.
- **Class Variables:** name: str, description: str, input_schema: Dict[str, Any], server_url: str, requires_approval: bool, max_response_bytes: int, timeout_seconds: int

### `McpConnectorConfig`
- **Docstring:** Configuration for MCP connector.
- **Class Variables:** id: str, name: str, server_url: str, api_key_ref: str, allowed_tools: List[str], timeout_seconds: int, max_response_bytes: int, max_retries: int, rate_limit_per_minute: int, tenant_id: str

### `McpConnectorError(Exception)`
- **Docstring:** Error from MCP connector.
- **Methods:** __init__

### `McpApprovalRequiredError(McpConnectorError)`
- **Docstring:** Tool requires manual approval.
- **Methods:** __init__

### `McpRateLimitExceededError(McpConnectorError)`
- **Docstring:** Rate limit exceeded.
- **Methods:** __init__

### `McpSchemaValidationError(McpConnectorError)`
- **Docstring:** Schema validation failed.
- **Methods:** __init__

### `McpConnectorService`
- **Docstring:** Governed MCP tool invocation.
- **Methods:** __init__, id, execute, _resolve_tool, _validate_against_schema, _build_mcp_request, _get_api_key, _check_rate_limit, _record_request, get_available_tools

## Attributes

- `logger` (line 67)
- `DEFAULT_MAX_RESPONSE_BYTES` (line 70)
- `DEFAULT_TIMEOUT_SECONDS` (line 71)
- `DEFAULT_RATE_LIMIT_PER_MINUTE` (line 72)
- `DEFAULT_MAX_RETRIES` (line 73)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.integrations.L5_engines.credentials` |
| External | `httpx`, `jsonschema` |

## Callers

RetrievalMediator

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: McpToolDefinition
      methods: []
    - name: McpConnectorConfig
      methods: []
    - name: McpConnectorError
      methods: []
    - name: McpApprovalRequiredError
      methods: []
    - name: McpRateLimitExceededError
      methods: []
    - name: McpSchemaValidationError
      methods: []
    - name: McpConnectorService
      methods: [id, execute, get_available_tools]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
