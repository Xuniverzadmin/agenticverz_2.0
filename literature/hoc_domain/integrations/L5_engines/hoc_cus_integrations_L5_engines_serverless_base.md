# hoc_cus_integrations_L5_engines_serverless_base

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/serverless_base.py` |
| Layer | L3 — Boundary Adapters |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Base class for serverless adapters

## Intent

**Role:** Base class for serverless adapters
**Reference:** GAP-149, GAP-150
**Callers:** Serverless adapter implementations

## Purpose

Serverless Base Adapter

---

## Classes

### `InvocationType(str, Enum)`
- **Docstring:** Type of function invocation.

### `InvocationRequest`
- **Docstring:** Request to invoke a serverless function.
- **Methods:** to_dict
- **Class Variables:** function_name: str, payload: Dict[str, Any], invocation_type: InvocationType, timeout_seconds: int, metadata: Dict[str, Any]

### `InvocationResult`
- **Docstring:** Result of a serverless function invocation.
- **Methods:** success, to_dict
- **Class Variables:** request_id: str, status_code: int, payload: Optional[Dict[str, Any]], error: Optional[str], logs: Optional[str], duration_ms: Optional[int], billed_duration_ms: Optional[int], memory_used_mb: Optional[int], invoked_at: datetime

### `FunctionInfo`
- **Docstring:** Information about a serverless function.
- **Methods:** to_dict
- **Class Variables:** name: str, arn_or_uri: str, runtime: Optional[str], memory_mb: Optional[int], timeout_seconds: Optional[int], last_modified: Optional[datetime], description: Optional[str], tags: Dict[str, str]

### `ServerlessAdapter(ABC)`
- **Docstring:** Abstract base class for serverless adapters.
- **Methods:** connect, disconnect, invoke, invoke_batch, get_function_info, list_functions, function_exists, health_check

## Attributes

- `logger` (line 26)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

Serverless adapter implementations

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: InvocationType
      methods: []
    - name: InvocationRequest
      methods: [to_dict]
    - name: InvocationResult
      methods: [success, to_dict]
    - name: FunctionInfo
      methods: [to_dict]
    - name: ServerlessAdapter
      methods: [connect, disconnect, invoke, invoke_batch, get_function_info, list_functions, function_exists, health_check]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
