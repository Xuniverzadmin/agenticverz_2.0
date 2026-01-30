# hoc_cus_analytics_L5_engines_provenance

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/provenance.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

CostSim V2 provenance logging (full audit trail)

## Intent

**Role:** CostSim V2 provenance logging (full audit trail)
**Reference:** PIN-470
**Callers:** sandbox engine

## Purpose

Full provenance logging for CostSim V2 sandbox.

---

## Functions

### `compute_hash(data: Any) -> str`
- **Async:** No
- **Docstring:** Compute SHA256 hash of data.
- **Calls:** dumps, encode, hexdigest, isinstance, sha256, str

### `compress_json(data: Any) -> str`
- **Async:** No
- **Docstring:** Compress JSON data to base64-encoded gzip.
- **Calls:** b64encode, compress, decode, dumps, encode

### `get_provenance_logger() -> ProvenanceLogger`
- **Async:** No
- **Docstring:** Get the global provenance logger.
- **Calls:** ProvenanceLogger

## Classes

### `ProvenanceLog`
- **Docstring:** Single provenance log entry.
- **Methods:** to_dict, from_dict, get_decompressed_input, get_decompressed_output
- **Class Variables:** id: str, timestamp: datetime, input_hash: str, output_hash: str, input_json: str, output_json: str, compressed: bool, model_version: str, adapter_version: str, commit_sha: str, runtime_ms: int, status: str, tenant_id: Optional[str], run_id: Optional[str], plan_hash: Optional[str]

### `ProvenanceLogger`
- **Docstring:** Logger for CostSim V2 provenance.
- **Methods:** __init__, log, _store, _flush, _write_to_file, _write_to_db, close, query

## Attributes

- `logger` (line 51)
- `_provenance_logger: Optional[ProvenanceLogger]` (line 377)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `__future__`, `app.costsim.config`, `gzip` |

## Callers

sandbox engine

## Export Contract

```yaml
exports:
  functions:
    - name: compute_hash
      signature: "compute_hash(data: Any) -> str"
    - name: compress_json
      signature: "compress_json(data: Any) -> str"
    - name: get_provenance_logger
      signature: "get_provenance_logger() -> ProvenanceLogger"
  classes:
    - name: ProvenanceLog
      methods: [to_dict, from_dict, get_decompressed_input, get_decompressed_output]
    - name: ProvenanceLogger
      methods: [log, close, query]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
