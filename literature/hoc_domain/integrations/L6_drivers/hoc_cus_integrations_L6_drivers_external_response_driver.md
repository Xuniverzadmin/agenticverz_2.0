# hoc_cus_integrations_L6_drivers_external_response_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L6_drivers/external_response_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

External response persistence and interpretation driver

## Intent

**Role:** External response persistence and interpretation driver
**Reference:** PIN-470, PIN-256 Phase E FIX-04
**Callers:** L3 adapters (record_raw), L4/L5 engines (interpret), L2 (read_interpreted)

## Purpose

External Response Driver (Phase E FIX-04)

---

## Functions

### `record_external_response(session: Session, source: str, raw_response: dict, interpretation_owner: str, interpretation_contract: Optional[str], request_id: Optional[str], run_id: Optional[str]) -> ExternalResponse`
- **Async:** No
- **Docstring:** Record a raw external response (L3 → L6).
- **Calls:** ExternalResponseService, record_raw_response

### `interpret_response(session: Session, response_id: UUID, interpreted_value: dict, interpreted_by: str) -> ExternalResponse`
- **Async:** No
- **Docstring:** Record L4 engine interpretation (L4 → L6).
- **Calls:** ExternalResponseService, interpret

### `get_interpreted_response(session: Session, response_id: UUID) -> Optional[InterpretedResponse]`
- **Async:** No
- **Docstring:** Get interpreted response for consumers (L5/L2 ← L6).
- **Calls:** ExternalResponseService, get_interpreted

## Classes

### `ExternalResponseService`
- **Docstring:** Service for external response operations.
- **Methods:** __init__, record_raw_response, interpret, get_raw_for_interpretation, get_interpreted, get_pending_interpretations

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.external_response` |
| External | `sqlalchemy`, `sqlalchemy.orm` |

## Callers

L3 adapters (record_raw), L4/L5 engines (interpret), L2 (read_interpreted)

## Export Contract

```yaml
exports:
  functions:
    - name: record_external_response
      signature: "record_external_response(session: Session, source: str, raw_response: dict, interpretation_owner: str, interpretation_contract: Optional[str], request_id: Optional[str], run_id: Optional[str]) -> ExternalResponse"
    - name: interpret_response
      signature: "interpret_response(session: Session, response_id: UUID, interpreted_value: dict, interpreted_by: str) -> ExternalResponse"
    - name: get_interpreted_response
      signature: "get_interpreted_response(session: Session, response_id: UUID) -> Optional[InterpretedResponse]"
  classes:
    - name: ExternalResponseService
      methods: [record_raw_response, interpret, get_raw_for_interpretation, get_interpreted, get_pending_interpretations]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
