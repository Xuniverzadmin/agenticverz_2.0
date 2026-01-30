# hoc_cus_activity_L5_engines_signal_identity

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/activity/L5_engines/signal_identity.py` |
| Layer | L5 — Domain Engine |
| Domain | activity |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Signal identity computation for deduplication

## Intent

**Role:** Signal identity computation for deduplication
**Reference:** PIN-470, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
**Callers:** activity_facade.py, signal engines

## Purpose

Signal identity utilities for fingerprinting and deduplication.

---

## Functions

### `compute_signal_fingerprint_from_row(row: dict[str, Any]) -> str`
- **Async:** No
- **Docstring:** Compute a stable fingerprint for a signal row.  Used for:
- **Calls:** dumps, encode, get, hexdigest, sha256

### `compute_signal_fingerprint(signal_type: str, dimension: str, source: str, tenant_id: str) -> str`
- **Async:** No
- **Docstring:** Compute a stable fingerprint for signal identity fields.  Args:
- **Calls:** compute_signal_fingerprint_from_row

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

activity_facade.py, signal engines

## Export Contract

```yaml
exports:
  functions:
    - name: compute_signal_fingerprint_from_row
      signature: "compute_signal_fingerprint_from_row(row: dict[str, Any]) -> str"
    - name: compute_signal_fingerprint
      signature: "compute_signal_fingerprint(signal_type: str, dimension: str, source: str, tenant_id: str) -> str"
  classes: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
