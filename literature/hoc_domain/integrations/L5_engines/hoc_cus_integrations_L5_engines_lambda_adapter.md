# hoc_cus_integrations_L5_engines_lambda_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/lambda_adapter.py` |
| Layer | L3 — Boundary Adapters |
| Domain | integrations |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

AWS Lambda serverless adapter

## Intent

**Role:** AWS Lambda serverless adapter
**Reference:** GAP-149 (AWS Lambda Serverless Adapter)
**Callers:** SkillExecutor, WorkflowEngine

## Purpose

AWS Lambda Serverless Adapter (GAP-149)

---

## Classes

### `LambdaAdapter(ServerlessAdapter)`
- **Docstring:** AWS Lambda serverless adapter.
- **Methods:** __init__, connect, disconnect, invoke, invoke_batch, get_function_info, list_functions, function_exists

## Attributes

- `logger` (line 39)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `aioboto3`, `base` |

## Callers

SkillExecutor, WorkflowEngine

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: LambdaAdapter
      methods: [connect, disconnect, invoke, invoke_batch, get_function_info, list_functions, function_exists]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
