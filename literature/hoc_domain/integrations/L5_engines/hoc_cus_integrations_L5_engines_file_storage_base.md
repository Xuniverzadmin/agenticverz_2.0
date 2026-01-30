# hoc_cus_integrations_L5_engines_file_storage_base

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/file_storage_base.py` |
| Layer | L3 — Boundary Adapters |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Base class for file storage adapters

## Intent

**Role:** Base class for file storage adapters
**Reference:** GAP-147, GAP-148
**Callers:** File storage adapter implementations

## Purpose

File Storage Base Adapter

---

## Classes

### `FileMetadata`
- **Docstring:** Metadata for a stored file.
- **Methods:** to_dict
- **Class Variables:** key: str, size: int, content_type: Optional[str], last_modified: Optional[datetime], etag: Optional[str], metadata: Dict[str, str]

### `UploadResult`
- **Docstring:** Result of an upload operation.
- **Methods:** success
- **Class Variables:** key: str, size: int, etag: Optional[str], version_id: Optional[str], location: Optional[str]

### `DownloadResult`
- **Docstring:** Result of a download operation.
- **Methods:** success
- **Class Variables:** content: bytes, metadata: FileMetadata

### `ListResult`
- **Docstring:** Result of a list operation.
- **Class Variables:** files: List[FileMetadata], continuation_token: Optional[str], is_truncated: bool

### `FileStorageAdapter(ABC)`
- **Docstring:** Abstract base class for file storage adapters.
- **Methods:** connect, disconnect, upload, download, download_stream, delete, delete_many, exists, get_metadata, list_files, generate_presigned_url, copy, health_check

## Attributes

- `logger` (line 25)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

File storage adapter implementations

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: FileMetadata
      methods: [to_dict]
    - name: UploadResult
      methods: [success]
    - name: DownloadResult
      methods: [success]
    - name: ListResult
      methods: []
    - name: FileStorageAdapter
      methods: [connect, disconnect, upload, download, download_stream, delete, delete_many, exists, get_metadata, list_files, generate_presigned_url, copy, health_check]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
