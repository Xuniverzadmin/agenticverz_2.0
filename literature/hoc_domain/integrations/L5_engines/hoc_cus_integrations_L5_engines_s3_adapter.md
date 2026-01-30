# hoc_cus_integrations_L5_engines_s3_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/s3_adapter.py` |
| Layer | L3 — Boundary Adapters |
| Domain | integrations |
| Audience | INTERNAL |
| Artifact Class | CODE |

## Description

AWS S3 file storage adapter

## Intent

**Role:** AWS S3 file storage adapter
**Reference:** GAP-147 (S3 File Storage Adapter)
**Callers:** DataIngestionExecutor, ExportService

## Purpose

AWS S3 File Storage Adapter (GAP-147)

---

## Classes

### `S3Adapter(FileStorageAdapter)`
- **Docstring:** AWS S3 file storage adapter.
- **Methods:** __init__, connect, disconnect, upload, download, download_stream, delete, delete_many, exists, get_metadata, list_files, generate_presigned_url, copy

## Attributes

- `logger` (line 36)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `aioboto3`, `base` |

## Callers

DataIngestionExecutor, ExportService

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: S3Adapter
      methods: [connect, disconnect, upload, download, download_stream, delete, delete_many, exists, get_metadata, list_files, generate_presigned_url, copy]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
