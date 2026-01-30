# hoc_models_log_exports

| Field | Value |
|-------|-------|
| Path | `backend/app/models/log_exports.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Log Exports model for LOGS Domain V2 (O5 evidence bundles)

## Intent

**Role:** Log Exports model for LOGS Domain V2 (O5 evidence bundles)
**Reference:** LOGS_DOMAIN_V2_CONTRACT.md
**Callers:** logs API, LogExportService

## Purpose

Log Exports Model (LOGS Domain V2)

---

## Functions

### `utc_now() -> datetime`
- **Async:** No
- **Docstring:** Return current UTC time.
- **Calls:** now

### `generate_uuid() -> str`
- **Async:** No
- **Docstring:** Generate a UUID string.
- **Calls:** str, uuid4

## Classes

### `ExportScope(str, Enum)`
- **Docstring:** Scope of the export.

### `ExportFormat(str, Enum)`
- **Docstring:** Export file format.

### `ExportOrigin(str, Enum)`
- **Docstring:** Who/what initiated the export.

### `ExportStatus(str, Enum)`
- **Docstring:** Export completion status.

### `LogExport(SQLModel)`
- **Docstring:** Immutable record for log/evidence exports (LOGS domain O5).
- **Class Variables:** id: str, tenant_id: str, scope: str, run_id: Optional[str], requested_by: str, format: str, origin: str, source_component: str, correlation_id: Optional[str], checksum: Optional[str], status: str, delivered_at: Optional[datetime], created_at: datetime

## Attributes

- `__all__` (line 130)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlmodel` |

## Callers

logs API, LogExportService

## Export Contract

```yaml
exports:
  functions:
    - name: utc_now
      signature: "utc_now() -> datetime"
    - name: generate_uuid
      signature: "generate_uuid() -> str"
  classes:
    - name: ExportScope
      methods: []
    - name: ExportFormat
      methods: []
    - name: ExportOrigin
      methods: []
    - name: ExportStatus
      methods: []
    - name: LogExport
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
