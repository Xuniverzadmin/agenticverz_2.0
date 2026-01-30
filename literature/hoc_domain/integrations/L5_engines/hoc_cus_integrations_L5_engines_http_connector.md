# hoc_cus_integrations_L5_engines_http_connector

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/http_connector.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Machine-controlled HTTP connector (NOT LLM-controlled)

## Intent

**Role:** Machine-controlled HTTP connector (NOT LLM-controlled)
**Reference:** PIN-470, GAP-059
**Callers:** RetrievalMediator

## Purpose

Module: http_connector
Purpose: Machine-controlled HTTP connector (NOT LLM-controlled).

---

## Classes

### `HttpMethod(str, Enum)`
- **Docstring:** Allowed HTTP methods.

### `EndpointConfig`
- **Docstring:** Configuration for a single endpoint.
- **Class Variables:** method: HttpMethod, path: str, description: str, request_schema: Optional[Dict], requires_body: bool

### `HttpConnectorConfig`
- **Docstring:** Configuration for HTTP connector.
- **Class Variables:** id: str, name: str, base_url: str, auth_type: str, auth_header: str, credential_ref: str, timeout_seconds: int, max_response_bytes: int, rate_limit_per_minute: int, allowed_methods: List[str], endpoints: Dict[str, EndpointConfig], tenant_id: str

### `HttpConnectorError(Exception)`
- **Docstring:** Error from HTTP connector.
- **Methods:** __init__

### `RateLimitExceededError(HttpConnectorError)`
- **Docstring:** Rate limit exceeded.
- **Methods:** __init__

### `HttpConnectorService`
- **Docstring:** Governed HTTP connector.
- **Methods:** __init__, id, execute, _resolve_endpoint, _build_url, _get_auth_headers, _check_rate_limit, _record_request

## Attributes

- `logger` (line 68)
- `DEFAULT_MAX_RESPONSE_BYTES` (line 71)
- `DEFAULT_TIMEOUT_SECONDS` (line 72)
- `DEFAULT_RATE_LIMIT_PER_MINUTE` (line 73)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.integrations.L5_engines.credentials` |
| External | `httpx` |

## Callers

RetrievalMediator

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: HttpMethod
      methods: []
    - name: EndpointConfig
      methods: []
    - name: HttpConnectorConfig
      methods: []
    - name: HttpConnectorError
      methods: []
    - name: RateLimitExceededError
      methods: []
    - name: HttpConnectorService
      methods: [id, execute]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
