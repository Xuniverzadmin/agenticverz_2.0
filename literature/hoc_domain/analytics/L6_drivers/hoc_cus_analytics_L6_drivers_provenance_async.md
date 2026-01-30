# hoc_cus_analytics_L6_drivers_provenance_async

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L6_drivers/provenance_async.py` |
| Layer | L6 — Domain Driver |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

CostSim V2 Provenance Logger - Async Implementation

## Intent

**Role:** CostSim V2 Provenance Logger - Async Implementation
**Reference:** PIN-470, M6 CostSim
**Callers:** sandbox.py (L5 engine)

## Purpose

Async provenance logging for CostSim V2.

---

## Functions

### `async write_provenance(run_id: Optional[str], tenant_id: Optional[str], variant_slug: str, source: str, model_version: Optional[str], adapter_version: Optional[str], commit_sha: Optional[str], input_hash: Optional[str], output_hash: Optional[str], v1_cost: Optional[float], v2_cost: Optional[float], payload: Optional[Dict[str, Any]], runtime_ms: Optional[int], session: Optional[AsyncSession]) -> int`
- **Async:** Yes
- **Docstring:** Write a single provenance record.  Args:
- **Calls:** AsyncSessionLocal, CostSimProvenanceModel, add, close, debug, error, flush, refresh

### `async write_provenance_batch(records: List[Dict[str, Any]], session: Optional[AsyncSession]) -> List[int]`
- **Async:** Yes
- **Docstring:** Write multiple provenance records in a single transaction.  More efficient than individual writes for high-throughput scenarios.
- **Calls:** AsyncSessionLocal, CostSimProvenanceModel, add, close, error, get, info, len, list, range

### `async query_provenance(tenant_id: Optional[str], variant_slug: Optional[str], source: Optional[str], input_hash: Optional[str], start_date: Optional[datetime], end_date: Optional[datetime], limit: int, offset: int) -> List[Dict[str, Any]]`
- **Async:** Yes
- **Docstring:** Query provenance records.  Args:
- **Calls:** and_, append, async_session_context, desc, execute, limit, offset, order_by, scalars, select, to_dict, where

### `async count_provenance(tenant_id: Optional[str], variant_slug: Optional[str], start_date: Optional[datetime], end_date: Optional[datetime]) -> int`
- **Async:** Yes
- **Docstring:** Count provenance records matching filters.  Args:
- **Calls:** and_, append, async_session_context, count, execute, scalar, select, select_from, where

### `async get_drift_stats(start_date: Optional[datetime], end_date: Optional[datetime]) -> Dict[str, Any]`
- **Async:** Yes
- **Docstring:** Get drift statistics between V1 and V2 costs.  Args:
- **Calls:** and_, append, async_session_context, avg, count, execute, fetchone, float, isnot, label, max, min, select, stddev, where

### `async check_duplicate(input_hash: str) -> bool`
- **Async:** Yes
- **Docstring:** Check if a record with this input hash already exists.  Args:
- **Calls:** async_session_context, execute, first, limit, scalars, select, where

### `compute_input_hash(payload: Dict[str, Any]) -> str`
- **Async:** No
- **Docstring:** Compute deterministic hash of input payload.  Args:
- **Calls:** dumps, encode, hexdigest, sha256

### `async backfill_v1_baseline(records: List[Dict[str, Any]], batch_size: int) -> Dict[str, int]`
- **Async:** Yes
- **Docstring:** Backfill V1 baseline records from historical data.  Args:
- **Calls:** check_duplicate, error, get, info, len, range, write_provenance

## Attributes

- `logger` (line 76)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.costsim_cb` |
| External | `__future__`, `app.db_async`, `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

sandbox.py (L5 engine)

## Export Contract

```yaml
exports:
  functions:
    - name: write_provenance
      signature: "async write_provenance(run_id: Optional[str], tenant_id: Optional[str], variant_slug: str, source: str, model_version: Optional[str], adapter_version: Optional[str], commit_sha: Optional[str], input_hash: Optional[str], output_hash: Optional[str], v1_cost: Optional[float], v2_cost: Optional[float], payload: Optional[Dict[str, Any]], runtime_ms: Optional[int], session: Optional[AsyncSession]) -> int"
    - name: write_provenance_batch
      signature: "async write_provenance_batch(records: List[Dict[str, Any]], session: Optional[AsyncSession]) -> List[int]"
    - name: query_provenance
      signature: "async query_provenance(tenant_id: Optional[str], variant_slug: Optional[str], source: Optional[str], input_hash: Optional[str], start_date: Optional[datetime], end_date: Optional[datetime], limit: int, offset: int) -> List[Dict[str, Any]]"
    - name: count_provenance
      signature: "async count_provenance(tenant_id: Optional[str], variant_slug: Optional[str], start_date: Optional[datetime], end_date: Optional[datetime]) -> int"
    - name: get_drift_stats
      signature: "async get_drift_stats(start_date: Optional[datetime], end_date: Optional[datetime]) -> Dict[str, Any]"
    - name: check_duplicate
      signature: "async check_duplicate(input_hash: str) -> bool"
    - name: compute_input_hash
      signature: "compute_input_hash(payload: Dict[str, Any]) -> str"
    - name: backfill_v1_baseline
      signature: "async backfill_v1_baseline(records: List[Dict[str, Any]], batch_size: int) -> Dict[str, int]"
  classes: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
