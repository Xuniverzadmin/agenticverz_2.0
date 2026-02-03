# hoc_cus_policies_L5_engines_policy_graph_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/policy_graph_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy conflict detection and dependency graph computation

## Intent

**Role:** Policy conflict detection and dependency graph computation
**Reference:** PIN-470, PIN-411 (Gap Closure), DFT-O4, DFT-O5
**Callers:** policies.py, policy_layer.py

## Purpose

Policy Graph Engine — Conflict Detection & Dependency Analysis

---

## Functions

### `get_conflict_engine(tenant_id: str) -> PolicyConflictEngine`
- **Async:** No
- **Docstring:** Get a PolicyConflictEngine instance for a tenant.
- **Calls:** PolicyConflictEngine

### `get_dependency_engine(tenant_id: str) -> PolicyDependencyEngine`
- **Async:** No
- **Docstring:** Get a PolicyDependencyEngine instance for a tenant.
- **Calls:** PolicyDependencyEngine

## Classes

### `ConflictType(str, Enum)`
- **Docstring:** Conflict taxonomy (LOCKED).

### `ConflictSeverity(str, Enum)`
- **Docstring:** Conflict severity levels.

### `DependencyType(str, Enum)`
- **Docstring:** Dependency types (LOCKED).

### `PolicyConflict`
- **Docstring:** A detected conflict between two policies.
- **Methods:** to_dict
- **Class Variables:** policy_a_id: str, policy_b_id: str, policy_a_name: str, policy_b_name: str, conflict_type: ConflictType, severity: ConflictSeverity, explanation: str, recommended_action: str, detected_at: datetime

### `PolicyDependency`
- **Docstring:** A dependency relationship between policies.
- **Methods:** to_dict
- **Class Variables:** policy_id: str, depends_on_id: str, policy_name: str, depends_on_name: str, dependency_type: DependencyType, reason: str, is_active: bool

### `PolicyNode`
- **Docstring:** A node in the dependency graph.
- **Methods:** to_dict
- **Class Variables:** id: str, name: str, rule_type: str, scope: str, status: str, enforcement_mode: str, depends_on: list[dict], required_by: list[dict]

### `DependencyGraphResult`
- **Docstring:** Result of dependency graph computation.
- **Methods:** to_dict
- **Class Variables:** nodes: list[PolicyNode], edges: list[PolicyDependency], computed_at: datetime

### `ConflictDetectionResult`
- **Docstring:** Result of conflict detection.
- **Methods:** to_dict
- **Class Variables:** conflicts: list[PolicyConflict], unresolved_count: int, computed_at: datetime

### `PolicyConflictEngine`
- **Docstring:** Detects logical contradictions, overlaps, or unsafe coexistence between policies.
- **Methods:** __init__, detect_conflicts, _detect_scope_overlaps, _detect_threshold_contradictions, _detect_temporal_conflicts, _detect_priority_overrides, _has_contradicting_conditions, _time_windows_overlap, _involves_policy

### `PolicyDependencyEngine`
- **Docstring:** Computes structural relationships between policies.
- **Methods:** __init__, compute_dependency_graph, _detect_explicit_dependencies, _detect_implicit_scope_dependencies, _detect_implicit_limit_dependencies, check_can_delete, check_can_activate

## Attributes

- `logger` (line 45)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.policies.L6_drivers.policy_graph_driver` |
| External | `__future__` |

## Driver Dependency Pattern

This engine uses **dependency injection** for L6 driver access:

```python
# Engine receives driver as parameter (not session)
async def detect_conflicts(self, driver: PolicyGraphDriver, ...) -> ConflictDetectionResult
async def compute_dependency_graph(self, driver: PolicyGraphDriver, ...) -> DependencyGraphResult
```

**Callers must:**
1. Import `get_policy_graph_driver` from L6
2. Create driver: `driver = get_policy_graph_driver(session)`
3. Pass driver to engine methods

**L5 Engine Contract:** Engines never import or create sessions. They receive drivers from callers.

## Callers

- `policies_facade.py` (L5) — creates driver, passes to engine
- `policy_layer.py` (deprecated)

## Export Contract

```yaml
exports:
  functions:
    - name: get_conflict_engine
      signature: "get_conflict_engine(tenant_id: str) -> PolicyConflictEngine"
    - name: get_dependency_engine
      signature: "get_dependency_engine(tenant_id: str) -> PolicyDependencyEngine"
  classes:
    - name: ConflictType
      methods: []
    - name: ConflictSeverity
      methods: []
    - name: DependencyType
      methods: []
    - name: PolicyConflict
      methods: [to_dict]
    - name: PolicyDependency
      methods: [to_dict]
    - name: PolicyNode
      methods: [to_dict]
    - name: DependencyGraphResult
      methods: [to_dict]
    - name: ConflictDetectionResult
      methods: [to_dict]
    - name: PolicyConflictEngine
      methods: [detect_conflicts]
    - name: PolicyDependencyEngine
      methods: [compute_dependency_graph, check_can_delete, check_can_activate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
