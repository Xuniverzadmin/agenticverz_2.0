# hoc_cus_integrations_L5_engines_gcs_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/gcs_adapter.py` |
| Layer | L3 — Boundary Adapters |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Google Cloud Storage file storage adapter

## Intent

**Role:** Google Cloud Storage file storage adapter
**Reference:** GAP-148 (GCS File Storage Adapter)
**Callers:** DataIngestionExecutor, ExportService

## Purpose

Google Cloud Storage File Storage Adapter (GAP-148)

---

## Classes

### `GCSAdapter(FileStorageAdapter)`
- **Docstring:** Google Cloud Storage file storage adapter.
- **Methods:** __init__, connect, disconnect, upload, download, download_stream, delete, delete_many, exists, get_metadata, list_files, generate_presigned_url, copy

## Attributes

- `logger` (line 35)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `base`, `google.cloud` |

## Callers

DataIngestionExecutor, ExportService

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: GCSAdapter
      methods: [connect, disconnect, upload, download, download_stream, delete, delete_many, exists, get_metadata, list_files, generate_presigned_url, copy]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
