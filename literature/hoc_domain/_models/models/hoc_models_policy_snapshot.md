# hoc_models_policy_snapshot

| Field | Value |
|-------|-------|
| Path | `backend/app/models/policy_snapshot.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Immutable policy snapshot for run-time governance

## Intent

**Role:** Immutable policy snapshot for run-time governance
**Reference:** BACKEND_REMEDIATION_PLAN.md GAP-006, GAP-022
**Callers:** worker/runner.py, policy/engine.py

## Purpose

Policy Snapshot Model

---

## Functions

### `utc_now() -> datetime`
- **Async:** No
- **Docstring:** Return timezone-aware UTC datetime.
- **Calls:** now

## Classes

### `PolicySnapshot(SQLModel)`
- **Docstring:** Immutable snapshot of policies at run start.
- **Methods:** create_snapshot, get_policies, get_thresholds, verify_integrity, verify_threshold_integrity, get_threshold_hash
- **Class Variables:** id: Optional[int], snapshot_id: str, tenant_id: str, policies_json: str, thresholds_json: str, content_hash: str, threshold_snapshot_hash: Optional[str], policy_count: int, policy_version: Optional[str], created_at: datetime

### `PolicySnapshotCreate(BaseModel)`
- **Docstring:** Input for creating a policy snapshot.
- **Class Variables:** tenant_id: str, policies: list[dict[str, Any]], thresholds: dict[str, Any], policy_version: Optional[str]

### `PolicySnapshotResponse(BaseModel)`
- **Docstring:** API response for policy snapshot.
- **Class Variables:** snapshot_id: str, tenant_id: str, policy_count: int, policy_version: Optional[str], content_hash: str, threshold_snapshot_hash: Optional[str], created_at: datetime, integrity_verified: bool, threshold_integrity_verified: bool

### `ThresholdSnapshot(BaseModel)`
- **Docstring:** Threshold values captured in snapshot.
- **Class Variables:** max_tokens_per_run: Optional[int], max_tokens_per_step: Optional[int], max_cost_cents_per_run: Optional[int], max_cost_cents_per_step: Optional[int], max_requests_per_minute: Optional[int], max_requests_per_hour: Optional[int], custom: dict[str, Any]

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic`, `sqlmodel` |

## Callers

worker/runner.py, policy/engine.py

## Export Contract

```yaml
exports:
  functions:
    - name: utc_now
      signature: "utc_now() -> datetime"
  classes:
    - name: PolicySnapshot
      methods: [create_snapshot, get_policies, get_thresholds, verify_integrity, verify_threshold_integrity, get_threshold_hash]
    - name: PolicySnapshotCreate
      methods: []
    - name: PolicySnapshotResponse
      methods: []
    - name: ThresholdSnapshot
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
