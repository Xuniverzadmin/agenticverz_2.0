# hoc_models_external_response

| Field | Value |
|-------|-------|
| Path | `backend/app/models/external_response.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

External response data models (DB tables)

## Intent

**Role:** External response data models (DB tables)
**Reference:** PIN-256 Phase E FIX-04
**Callers:** L3 adapters (write raw), L4 engines (read/interpret)

## Purpose

External Response Models (Phase E FIX-04)

---

## Classes

### `ExternalResponse(Base)`
- **Docstring:** External response record - raw data with interpretation ownership.

### `ExternalResponseCreate(BaseModel)`
- **Docstring:** Input model for recording external responses (L3 → L6 write).
- **Class Variables:** source: str, raw_response: dict, interpretation_owner: str, interpretation_contract: Optional[str], request_id: Optional[str], run_id: Optional[str]

### `InterpretationUpdate(BaseModel)`
- **Docstring:** Input model for L4 engine interpretation (L4 → L6 write).
- **Class Variables:** interpreted_value: dict, interpreted_by: str

### `ExternalResponseRead(BaseModel)`
- **Docstring:** Output model for external responses.
- **Class Variables:** id: UUID, source: str, request_id: Optional[str], run_id: Optional[str], raw_response: dict, interpretation_owner: str, interpretation_contract: Optional[str], interpreted_value: Optional[dict], interpreted_at: Optional[datetime], interpreted_by: Optional[str], received_at: datetime

### `InterpretedResponse(BaseModel)`
- **Docstring:** Output model for consumers (L5/L2) - only the interpreted value.
- **Class Variables:** id: UUID, source: str, interpretation_owner: str, interpreted_value: dict, interpreted_at: datetime, interpreted_by: str

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.costsim_cb` |
| External | `pydantic`, `sqlalchemy`, `sqlalchemy.dialects.postgresql`, `sqlalchemy.sql` |

## Callers

L3 adapters (write raw), L4 engines (read/interpret)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: ExternalResponse
      methods: []
    - name: ExternalResponseCreate
      methods: []
    - name: InterpretationUpdate
      methods: []
    - name: ExternalResponseRead
      methods: []
    - name: InterpretedResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
