# hoc_cus_policies_L5_engines_decorator

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/decorator.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Optional ergonomic decorator over ExecutionKernel

## Intent

**Role:** Optional ergonomic decorator over ExecutionKernel
**Reference:** PIN-470, PIN-337
**Callers:** HTTP route handlers, CLI commands

## Purpose

@governed Decorator - PIN-337 Optional Ergonomic Wrapper

---

## Functions

### `governed(capability: str, execution_vector: str, extract_tenant: Optional[Callable[..., str]], extract_subject: Optional[Callable[..., str]], reason: Optional[str]) -> Callable[[F], F]`
- **Async:** No
- **Docstring:** Decorator that routes execution through the ExecutionKernel.  Usage:
- **Calls:** InvocationContext, _extract_subject, _extract_tenant_id, func, invoke, invoke_async, iscoroutinefunction, wraps

### `_extract_tenant_id(args: tuple, kwargs: dict, extractor: Optional[Callable[..., str]]) -> str`
- **Async:** No
- **Docstring:** Extract tenant_id from function arguments.
- **Calls:** extractor, hasattr, str, values

### `_extract_subject(args: tuple, kwargs: dict, extractor: Optional[Callable[..., str]]) -> str`
- **Async:** No
- **Docstring:** Extract subject from function arguments.
- **Calls:** extractor, hasattr, str

## Attributes

- `logger` (line 44)
- `F` (line 46)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.governance.kernel` |

## Callers

HTTP route handlers, CLI commands

## Export Contract

```yaml
exports:
  functions:
    - name: governed
      signature: "governed(capability: str, execution_vector: str, extract_tenant: Optional[Callable[..., str]], extract_subject: Optional[Callable[..., str]], reason: Optional[str]) -> Callable[[F], F]"
  classes: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
