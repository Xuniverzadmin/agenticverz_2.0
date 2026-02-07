# retrieval_facade.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/retrieval_facade.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            retrieval_facade.py
Lives in:        services/
Role:            Services
Inbound:         L2 retrieval.py API, SDK
Outbound:        app.hoc.cus.hoc_spine.services.retrieval_mediator
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Retrieval Facade (L4 Domain Logic)
Violations:      none
```

## Purpose

Retrieval Facade (L4 Domain Logic)

This facade provides the external interface for mediated data retrieval operations.
All retrieval APIs MUST use this facade instead of directly importing
the RetrievalMediator.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes retrieval mediation logic
- Provides unified access to data retrieval with policy enforcement
- Single point for audit emission

Wrapped Services:
- RetrievalMediator: Central choke point for data access (GAP-065)

L2 API Routes (GAP-094):
- POST /retrieval/access (mediated data access)
- GET /retrieval/planes (list available planes)
- GET /retrieval/evidence (retrieve evidence records)

Usage:
    from app.services.retrieval.facade import get_retrieval_facade

    facade = get_retrieval_facade()

    # Mediated data access
    result = await facade.access_data(
        tenant_id="...",
        run_id="...",
        plane_id="documents",
        action="query",
        payload={"query": "..."},
    )

    # List available planes
    planes = await facade.list_planes(tenant_id="...")

## Import Analysis

**Spine-internal:**
- `app.hoc.cus.hoc_spine.services.retrieval_mediator`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_retrieval_facade() -> RetrievalFacade`

Get the retrieval facade instance.

This is the recommended way to access retrieval operations
from L2 APIs and the SDK.

Returns:
    RetrievalFacade instance

## Classes

### `AccessResult`

Result of a mediated data access.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `PlaneInfo`

Information about a knowledge plane.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `EvidenceInfo`

Evidence record information.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `RetrievalFacade`

Facade for mediated data retrieval operations.

This is the ONLY entry point for L2 APIs and SDK to interact with
the retrieval mediator.

Layer: L4 (Domain Logic)
Callers: retrieval.py (L2), aos_sdk

#### Methods

- `__init__()` — Initialize facade with lazy-loaded services.
- `mediator()` — Lazy-load RetrievalMediator.
- `async access_data(tenant_id: str, run_id: str, plane_id: str, action: str, payload: Dict[str, Any]) -> AccessResult` — Mediated access to external data.
- `async list_planes(tenant_id: str, connector_type: Optional[str], status: Optional[str]) -> List[PlaneInfo]` — List available knowledge planes for a tenant.
- `async register_plane(tenant_id: str, name: str, connector_type: str, connector_id: str, capabilities: Optional[List[str]]) -> PlaneInfo` — Register a knowledge plane for a tenant.
- `async get_plane(plane_id: str, tenant_id: str) -> Optional[PlaneInfo]` — Get a specific plane.
- `async list_evidence(tenant_id: str, run_id: Optional[str], plane_id: Optional[str], limit: int, offset: int) -> List[EvidenceInfo]` — List evidence records for a tenant.
- `async get_evidence(evidence_id: str, tenant_id: str) -> Optional[EvidenceInfo]` — Get a specific evidence record.
- `async record_evidence(tenant_id: str, run_id: str, plane_id: str, connector_id: str, query_hash: str, doc_ids: List[str], token_count: int, policy_snapshot_id: Optional[str]) -> EvidenceInfo` — Record evidence of a data access (internal use).

## Domain Usage

**Callers:** L2 retrieval.py API, SDK

## Export Contract

```yaml
exports:
  functions:
    - name: get_retrieval_facade
      signature: "get_retrieval_facade() -> RetrievalFacade"
      consumers: ["orchestrator"]
  classes:
    - name: AccessResult
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: PlaneInfo
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: EvidenceInfo
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: RetrievalFacade
      methods:
        - mediator
        - access_data
        - list_planes
        - register_plane
        - get_plane
        - list_evidence
        - get_evidence
        - record_evidence
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
    - "hoc_spine.authority.*"
    - "hoc_spine.consequences.*"
    - "hoc_spine.drivers.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: ['app.hoc.cus.hoc_spine.services.retrieval_mediator']
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
