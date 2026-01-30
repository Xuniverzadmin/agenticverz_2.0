# hoc_cus_policies_L6_drivers_recovery_write_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L6_drivers/recovery_write_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

DB write driver for Recovery APIs (DB boundary crossing)

## Intent

**Role:** DB write driver for Recovery APIs (DB boundary crossing)
**Reference:** PIN-470, PIN-250 Phase 2B Batch 4
**Callers:** L5 engines, api/recovery_ingest.py, api/recovery.py

## Purpose

_No module docstring._

---

## Classes

### `RecoveryWriteService`
- **Docstring:** Sync DB write operations for Recovery APIs.
- **Methods:** __init__, upsert_recovery_candidate, get_candidate_by_idempotency_key, enqueue_evaluation_db_fallback, update_recovery_candidate, insert_suggestion_provenance

## Attributes

- `FEATURE_INTENT` (line 30)
- `RETRY_POLICY` (line 31)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.infra`, `sqlalchemy`, `sqlmodel` |

## Callers

L5 engines, api/recovery_ingest.py, api/recovery.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: RecoveryWriteService
      methods: [upsert_recovery_candidate, get_candidate_by_idempotency_key, enqueue_evaluation_db_fallback, update_recovery_candidate, insert_suggestion_provenance]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
