# hoc_cus_incidents_L6_drivers_llm_failure_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L6_drivers/llm_failure_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for LLM failure operations (async)

## Intent

**Role:** Data access for LLM failure operations (async)
**Reference:** PIN-470, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** LLMFailureEngine (L5)

## Purpose

LLM Failure Driver (L6)

---

## Functions

### `get_llm_failure_driver(session: AsyncSession) -> LLMFailureDriver`
- **Async:** No
- **Docstring:** Factory function to get LLMFailureDriver instance.
- **Calls:** LLMFailureDriver

## Classes

### `LLMFailureDriver`
- **Docstring:** L6 driver for LLM failure operations (async).
- **Methods:** __init__, insert_failure, insert_evidence, update_run_failed, fetch_failure_by_run_id, fetch_contamination_check

## Attributes

- `logger` (line 73)
- `__all__` (line 328)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

LLMFailureEngine (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_llm_failure_driver
      signature: "get_llm_failure_driver(session: AsyncSession) -> LLMFailureDriver"
  classes:
    - name: LLMFailureDriver
      methods: [insert_failure, insert_evidence, update_run_failed, fetch_failure_by_run_id, fetch_contamination_check]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
