# hoc_cus_incidents_L5_engines_llm_failure_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/llm_failure_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

S4 failure truth model, fact persistence

## Intent

**Role:** S4 failure truth model, fact persistence
**Reference:** PIN-470, PIN-242 (Baseline Freeze), PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** L5 workers (on LLM failure)

## Purpose

LLMFailureService - S4 Failure Truth Implementation

---

## Classes

### `LLMFailureFact`
- **Docstring:** Authoritative LLM failure fact.
- **Methods:** __post_init__
- **Class Variables:** run_id: str, tenant_id: str, failure_type: str, model: str, error_code: str, error_message: str, request_id: Optional[str], duration_ms: Optional[int], metadata: Dict[str, Any], id: Optional[str], timestamp: Optional[datetime], persisted: bool

### `LLMFailureResult`
- **Docstring:** Result of failure persistence operation.
- **Class Variables:** failure_id: str, evidence_id: str, run_marked_failed: bool, timestamp: datetime

### `LLMFailureService`
- **Docstring:** Service for handling LLM failures with S4 truth guarantees.
- **Methods:** __init__, persist_failure_and_mark_run, _persist_failure, _capture_evidence, _mark_run_failed, _verify_no_contamination, get_failure_by_run_id

## Attributes

- `UuidFn` (line 69)
- `ClockFn` (line 70)
- `VERIFICATION_MODE` (line 87)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.incidents.L6_drivers.llm_failure_driver` |
| External | `app.utils.runtime`, `sqlalchemy.ext.asyncio` |

## Callers

L5 workers (on LLM failure)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: LLMFailureFact
      methods: []
    - name: LLMFailureResult
      methods: []
    - name: LLMFailureService
      methods: [persist_failure_and_mark_run, get_failure_by_run_id]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
