# hoc_cus_policies_L5_engines_snapshot_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/snapshot_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy snapshot immutability engine (pure business logic)

## Intent

**Role:** Policy snapshot immutability engine (pure business logic)
**Reference:** PIN-470, GAP-029 (Policy snapshot immutability)
**Callers:** L4 orchestrators, policy engines

## Purpose

Policy Snapshot Immutability Engine (GAP-029).

---

## Functions

### `get_snapshot_registry() -> PolicySnapshotRegistry`
- **Async:** No
- **Docstring:** Get the singleton registry instance.
- **Calls:** PolicySnapshotRegistry

### `_reset_snapshot_registry() -> None`
- **Async:** No
- **Docstring:** Reset the singleton (for testing).
- **Calls:** reset

### `create_policy_snapshot(tenant_id: str, policies: list[dict[str, Any]], thresholds: dict[str, Any], policy_version: Optional[str], description: Optional[str]) -> PolicySnapshotData`
- **Async:** No
- **Docstring:** Create a new immutable policy snapshot.
- **Calls:** create, get_snapshot_registry

### `get_policy_snapshot(snapshot_id: str) -> Optional[PolicySnapshotData]`
- **Async:** No
- **Docstring:** Get a policy snapshot by ID.
- **Calls:** get, get_snapshot_registry

### `get_active_snapshot(tenant_id: str) -> Optional[PolicySnapshotData]`
- **Async:** No
- **Docstring:** Get the active policy snapshot for a tenant.
- **Calls:** get_active, get_snapshot_registry

### `get_snapshot_history(tenant_id: str, limit: int) -> List[PolicySnapshotData]`
- **Async:** No
- **Docstring:** Get snapshot version history for a tenant.
- **Calls:** get_history, get_snapshot_registry

### `verify_snapshot(snapshot_id: str) -> dict[str, Any]`
- **Async:** No
- **Docstring:** Verify snapshot integrity.
- **Calls:** get_snapshot_registry, verify

## Classes

### `SnapshotStatus(str, Enum)`
- **Docstring:** Status of a policy snapshot.

### `ImmutabilityViolation(str, Enum)`
- **Docstring:** Types of immutability violations.

### `PolicySnapshotData`
- **Docstring:** Immutable policy snapshot data.
- **Methods:** compute_hash, verify_integrity, verify_threshold_integrity, get_policies, get_thresholds, to_dict
- **Class Variables:** snapshot_id: str, tenant_id: str, version: int, policies_json: str, thresholds_json: str, content_hash: str, threshold_hash: str, policy_count: int, policy_version: Optional[str], description: Optional[str], status: SnapshotStatus, created_at: datetime, superseded_at: Optional[datetime], superseded_by: Optional[str], is_sealed: bool

### `PolicySnapshotError(Exception)`
- **Docstring:** Exception for policy snapshot errors.
- **Methods:** __init__, to_dict

### `SnapshotRegistryStats`
- **Docstring:** Statistics for snapshot registry.
- **Methods:** to_dict
- **Class Variables:** total_snapshots: int, active_snapshots: int, superseded_snapshots: int, archived_snapshots: int, invalid_snapshots: int, tenants_with_snapshots: int, snapshots_with_valid_integrity: int

### `PolicySnapshotRegistry`
- **Docstring:** Registry for managing immutable policy snapshots.
- **Methods:** __init__, create, get, get_active, get_by_version, list, get_history, archive, verify, attempt_modify, delete, get_statistics, clear_tenant, reset, _get_next_version, _supersede_active
- **Class Variables:** ALLOWED_TRANSITIONS: dict[SnapshotStatus, set[SnapshotStatus]]

## Attributes

- `_registry: Optional[PolicySnapshotRegistry]` (line 532)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

L4 orchestrators, policy engines

## Export Contract

```yaml
exports:
  functions:
    - name: get_snapshot_registry
      signature: "get_snapshot_registry() -> PolicySnapshotRegistry"
    - name: create_policy_snapshot
      signature: "create_policy_snapshot(tenant_id: str, policies: list[dict[str, Any]], thresholds: dict[str, Any], policy_version: Optional[str], description: Optional[str]) -> PolicySnapshotData"
    - name: get_policy_snapshot
      signature: "get_policy_snapshot(snapshot_id: str) -> Optional[PolicySnapshotData]"
    - name: get_active_snapshot
      signature: "get_active_snapshot(tenant_id: str) -> Optional[PolicySnapshotData]"
    - name: get_snapshot_history
      signature: "get_snapshot_history(tenant_id: str, limit: int) -> List[PolicySnapshotData]"
    - name: verify_snapshot
      signature: "verify_snapshot(snapshot_id: str) -> dict[str, Any]"
  classes:
    - name: SnapshotStatus
      methods: []
    - name: ImmutabilityViolation
      methods: []
    - name: PolicySnapshotData
      methods: [compute_hash, verify_integrity, verify_threshold_integrity, get_policies, get_thresholds, to_dict]
    - name: PolicySnapshotError
      methods: [to_dict]
    - name: SnapshotRegistryStats
      methods: [to_dict]
    - name: PolicySnapshotRegistry
      methods: [create, get, get_active, get_by_version, list, get_history, archive, verify, attempt_modify, delete, get_statistics, clear_tenant, reset]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
