# knowledge_plane.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/lifecycle/drivers/knowledge_plane.py`  
**Layer:** L4 — HOC Spine (Orchestrator)  
**Component:** Orchestrator

---

## Placement Card

```
File:            knowledge_plane.py
Lives in:        orchestrator/
Role:            Orchestrator
Inbound:         lifecycle engines, drivers
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         KnowledgePlane - Knowledge plane models and registry.
Violations:      none
```

## Purpose

KnowledgePlane - Knowledge plane models and registry.

Provides knowledge graph abstraction for:
- Knowledge organization
- Semantic relationships
- Multi-source integration

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_knowledge_plane_registry() -> KnowledgePlaneRegistry`

Get the singleton registry instance.

### `_reset_registry() -> None`

Reset the singleton (for testing).

### `create_knowledge_plane(tenant_id: str, name: str, description: Optional[str]) -> KnowledgePlane`

Create a new knowledge plane using the singleton registry.

### `get_knowledge_plane(plane_id: str) -> Optional[KnowledgePlane]`

Get a knowledge plane by ID using the singleton registry.

### `list_knowledge_planes(tenant_id: Optional[str]) -> list[KnowledgePlane]`

List knowledge planes using the singleton registry.

## Classes

### `KnowledgePlaneStatus(str, Enum)`

Status of a knowledge plane.

### `KnowledgeNodeType(str, Enum)`

Types of knowledge nodes.

### `KnowledgeNode`

A node in the knowledge graph.

#### Methods

- `add_child(child_id: str) -> None` — Add a child node reference.
- `add_related(node_id: str) -> None` — Add a related node reference.
- `to_dict() -> dict[str, Any]` — Convert to dictionary.

### `KnowledgePlane`

Representation of a knowledge plane.

A knowledge plane is a tenant-specific knowledge graph
that organizes and indexes content from multiple sources.

#### Methods

- `add_node(node: KnowledgeNode) -> None` — Add a node to the plane.
- `get_node(node_id: str) -> Optional[KnowledgeNode]` — Get a node by ID.
- `remove_node(node_id: str) -> bool` — Remove a node from the plane.
- `add_source(source_id: str) -> None` — Add a source to the plane.
- `remove_source(source_id: str) -> bool` — Remove a source from the plane.
- `activate(now: Optional[datetime]) -> None` — Activate the plane.
- `deactivate(now: Optional[datetime]) -> None` — Deactivate the plane.
- `start_indexing(now: Optional[datetime]) -> None` — Start indexing the plane.
- `finish_indexing(success: bool, error: Optional[str], now: Optional[datetime]) -> None` — Finish indexing the plane.
- `archive(now: Optional[datetime]) -> None` — Archive the plane.
- `record_error(error: str, now: Optional[datetime]) -> None` — Record an error.
- `to_dict() -> dict[str, Any]` — Convert to dictionary.

### `KnowledgePlaneError(Exception)`

Exception for knowledge plane errors.

#### Methods

- `__init__(message: str, plane_id: Optional[str])` — _No docstring._
- `to_dict() -> dict[str, Any]` — Convert to dictionary.

### `KnowledgePlaneStats`

Statistics for knowledge planes.

#### Methods

- `to_dict() -> dict[str, Any]` — Convert to dictionary.

### `KnowledgePlaneRegistry`

Registry for managing knowledge planes.

Features:
- Plane registration and lookup
- Node management
- Status tracking
- Tenant isolation

#### Methods

- `__init__()` — Initialize the registry.
- `register(tenant_id: str, name: str, description: Optional[str], embedding_model: str, plane_id: Optional[str], tags: Optional[list[str]]) -> KnowledgePlane` — Register a new knowledge plane.
- `get(plane_id: str) -> Optional[KnowledgePlane]` — Get a plane by ID.
- `get_by_name(tenant_id: str, name: str) -> Optional[KnowledgePlane]` — Get a plane by name within a tenant.
- `list(tenant_id: Optional[str], status: Optional[KnowledgePlaneStatus], limit: int, offset: int) -> list[KnowledgePlane]` — List planes with optional filters.
- `delete(plane_id: str) -> bool` — Delete a plane.
- `get_statistics(tenant_id: Optional[str]) -> KnowledgePlaneStats` — Get registry statistics.
- `clear_tenant(tenant_id: str) -> int` — Clear all planes for a tenant.
- `reset() -> None` — Reset all state (for testing).

## Domain Usage

**Callers:** lifecycle engines, drivers

## Export Contract

```yaml
exports:
  functions:
    - name: get_knowledge_plane_registry
      signature: "get_knowledge_plane_registry() -> KnowledgePlaneRegistry"
      consumers: ["orchestrator"]
    - name: _reset_registry
      signature: "_reset_registry() -> None"
      consumers: ["orchestrator"]
    - name: create_knowledge_plane
      signature: "create_knowledge_plane(tenant_id: str, name: str, description: Optional[str]) -> KnowledgePlane"
      consumers: ["orchestrator"]
    - name: get_knowledge_plane
      signature: "get_knowledge_plane(plane_id: str) -> Optional[KnowledgePlane]"
      consumers: ["orchestrator"]
    - name: list_knowledge_planes
      signature: "list_knowledge_planes(tenant_id: Optional[str]) -> list[KnowledgePlane]"
      consumers: ["orchestrator"]
  classes:
    - name: KnowledgePlaneStatus
      methods: []
      consumers: ["orchestrator"]
    - name: KnowledgeNodeType
      methods: []
      consumers: ["orchestrator"]
    - name: KnowledgeNode
      methods:
        - add_child
        - add_related
        - to_dict
      consumers: ["orchestrator"]
    - name: KnowledgePlane
      methods:
        - add_node
        - get_node
        - remove_node
        - add_source
        - remove_source
        - activate
        - deactivate
        - start_indexing
        - finish_indexing
        - archive
        - record_error
        - to_dict
      consumers: ["orchestrator"]
    - name: KnowledgePlaneError
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: KnowledgePlaneStats
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: KnowledgePlaneRegistry
      methods:
        - register
        - get
        - get_by_name
        - list
        - delete
        - get_statistics
        - clear_tenant
        - reset
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc.api.*"
    - "hoc_spine.adapters.*"
  forbidden_inbound:
  actual_imports:
    spine_internal: []
    l7_model: []
    external: []
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

