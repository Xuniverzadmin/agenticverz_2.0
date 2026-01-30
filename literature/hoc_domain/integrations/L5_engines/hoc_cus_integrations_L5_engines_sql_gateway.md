# hoc_cus_integrations_L5_engines_sql_gateway

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/sql_gateway.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Template-based SQL queries (NO raw SQL from LLM)

## Intent

**Role:** Template-based SQL queries (NO raw SQL from LLM)
**Reference:** PIN-470, GAP-060
**Callers:** RetrievalMediator

## Purpose

Module: sql_gateway
Purpose: Template-based SQL queries (NO raw SQL from LLM).

---

## Classes

### `ParameterType(str, Enum)`
- **Docstring:** Supported parameter types for validation.

### `ParameterSpec`
- **Docstring:** Specification for a query parameter.
- **Class Variables:** name: str, param_type: ParameterType, required: bool, default: Any, description: str, max_length: Optional[int], min_value: Optional[float], max_value: Optional[float]

### `QueryTemplate`
- **Docstring:** Definition of a SQL query template.
- **Class Variables:** id: str, name: str, description: str, sql: str, parameters: List[ParameterSpec], read_only: bool, max_rows: int, timeout_seconds: int

### `SqlGatewayConfig`
- **Docstring:** Configuration for SQL gateway.
- **Class Variables:** id: str, name: str, connection_string_ref: str, allowed_templates: List[str], max_rows: int, max_result_bytes: int, timeout_seconds: int, read_only: bool, tenant_id: str

### `SqlGatewayError(Exception)`
- **Docstring:** Error from SQL gateway.

### `SqlInjectionAttemptError(SqlGatewayError)`
- **Docstring:** Potential SQL injection detected.

### `SqlGatewayService`
- **Docstring:** Governed SQL gateway.
- **Methods:** __init__, id, execute, _resolve_template, _validate_parameters, _coerce_parameter, _check_sql_injection, _get_connection_string

## Attributes

- `logger` (line 66)
- `DEFAULT_MAX_ROWS` (line 69)
- `DEFAULT_MAX_RESULT_BYTES` (line 70)
- `DEFAULT_TIMEOUT_SECONDS` (line 71)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.integrations.L5_engines.credentials` |
| External | `asyncpg` |

## Callers

RetrievalMediator

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: ParameterType
      methods: []
    - name: ParameterSpec
      methods: []
    - name: QueryTemplate
      methods: []
    - name: SqlGatewayConfig
      methods: []
    - name: SqlGatewayError
      methods: []
    - name: SqlInjectionAttemptError
      methods: []
    - name: SqlGatewayService
      methods: [id, execute]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
