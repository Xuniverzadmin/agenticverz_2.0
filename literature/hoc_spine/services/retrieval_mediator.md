# retrieval_mediator.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/retrieval_mediator.py`  
**Layer:** L4 — HOC Spine (Service)  
**Component:** Services

---

## Placement Card

```
File:            retrieval_mediator.py
Lives in:        services/
Role:            Services
Inbound:         L2 API routes, skill execution
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Module: retrieval_mediator
Violations:      none
```

## Purpose

Module: retrieval_mediator
Purpose: All external data access must route through this layer.

This is the CENTRAL CHOKE POINT for data retrieval.
Any data access from LLM-controlled code MUST go through here.

Imports (Dependencies):
    - None (interfaces defined here, implementations injected)

Exports (Provides):
    - RetrievalMediator: Main mediation class
    - MediatedResult: Result of a mediated access
    - MediationDeniedError: Raised when access denied
    - get_retrieval_mediator(): Factory to get singleton

Wiring Points:
    - Called from: L2 API route /api/v1/mediation/access
    - Calls: PolicyEngine (injected), ConnectorRegistry (injected)

Invariant: Deny-by-default. All access blocked unless explicitly allowed.

Acceptance Criteria:
    - [x] AC-065-01: All data access routes through mediator
    - [x] AC-065-02: Deny-by-default enforced
    - [x] AC-065-03: Evidence emitted for every access
    - [x] AC-065-04: Policy check before connector
    - [x] AC-065-05: Tenant isolation enforced

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_retrieval_mediator() -> RetrievalMediator`

Get or create the singleton RetrievalMediator.

In production, this should be configured with real implementations
of PolicyChecker, ConnectorRegistry, and EvidenceService.

### `configure_retrieval_mediator(policy_checker: Optional[PolicyChecker], connector_registry: Optional[ConnectorRegistry], evidence_service: Optional[EvidenceService]) -> RetrievalMediator`

Configure the singleton RetrievalMediator with dependencies.

Call this at startup to inject real implementations.

## Classes

### `MediationAction(str, Enum)`

Allowed mediation actions.

### `MediatedResult`

Result of a mediated data access.

### `PolicyCheckResult`

Result of policy check.

### `EvidenceRecord`

Evidence record for a mediated access.

### `MediationDeniedError(Exception)`

Raised when mediation denies access.

#### Methods

- `__init__(reason: str, policy_id: Optional[str], tenant_id: Optional[str], run_id: Optional[str])` — _No docstring._

### `Connector(Protocol)`

Protocol for connectors.

#### Methods

- `async execute(action: str, payload: Dict[str, Any]) -> Dict[str, Any]` — Execute connector action.

### `ConnectorRegistry(Protocol)`

Protocol for connector registry.

#### Methods

- `async resolve(tenant_id: str, plane_id: str) -> Optional[Connector]` — Resolve connector for plane.

### `PolicyChecker(Protocol)`

Protocol for policy checking.

#### Methods

- `async check_access(tenant_id: str, run_id: str, plane_id: str, action: str) -> PolicyCheckResult` — Check if access is allowed.

### `EvidenceService(Protocol)`

Protocol for evidence recording.

#### Methods

- `async record(tenant_id: str, run_id: str, plane_id: str, connector_id: str, query_hash: str, doc_ids: List[str], token_count: int, policy_snapshot_id: Optional[str], timestamp: datetime) -> EvidenceRecord` — Record evidence of data access.

### `RetrievalMediator`

Unified mediation layer for all external data access.

Flow:
1. Receive access request (plane_id, action, payload)
2. Tenant isolation check
3. Policy check (deny-by-default)
4. Connector resolution (plane -> data source)
5. Execute access through connector
6. Emit retrieval evidence
7. Return result

All data access from LLM-controlled code MUST go through this layer.

#### Methods

- `__init__(policy_checker: Optional[PolicyChecker], connector_registry: Optional[ConnectorRegistry], evidence_service: Optional[EvidenceService])` — _No docstring._
- `async access(tenant_id: str, run_id: str, plane_id: str, action: str, payload: Dict[str, Any], requesting_tenant_id: Optional[str]) -> MediatedResult` — Mediated access to external data.
- `async _check_policy(tenant_id: str, run_id: str, plane_id: str, action: str) -> PolicyCheckResult` — Check if access is allowed by policy.
- `async _resolve_connector(tenant_id: str, plane_id: str) -> Optional[Connector]` — Resolve connector for the given plane.
- `async _record_evidence(tenant_id: str, run_id: str, plane_id: str, connector_id: str, query_hash: str, doc_ids: List[str], token_count: int, policy_snapshot_id: Optional[str], timestamp: datetime) -> Optional[EvidenceRecord]` — Record evidence of data access.
- `_hash_payload(payload: Dict[str, Any]) -> str` — Create deterministic hash of payload for audit.

## Domain Usage

**Callers:** L2 API routes, skill execution

## Export Contract

```yaml
exports:
  functions:
    - name: get_retrieval_mediator
      signature: "get_retrieval_mediator() -> RetrievalMediator"
      consumers: ["orchestrator"]
    - name: configure_retrieval_mediator
      signature: "configure_retrieval_mediator(policy_checker: Optional[PolicyChecker], connector_registry: Optional[ConnectorRegistry], evidence_service: Optional[EvidenceService]) -> RetrievalMediator"
      consumers: ["orchestrator"]
  classes:
    - name: MediationAction
      methods: []
      consumers: ["orchestrator"]
    - name: MediatedResult
      methods: []
      consumers: ["orchestrator"]
    - name: PolicyCheckResult
      methods: []
      consumers: ["orchestrator"]
    - name: EvidenceRecord
      methods: []
      consumers: ["orchestrator"]
    - name: MediationDeniedError
      methods:
      consumers: ["orchestrator"]
    - name: Connector
      methods:
        - execute
      consumers: ["orchestrator"]
    - name: ConnectorRegistry
      methods:
        - resolve
      consumers: ["orchestrator"]
    - name: PolicyChecker
      methods:
        - check_access
      consumers: ["orchestrator"]
    - name: EvidenceService
      methods:
        - record
      consumers: ["orchestrator"]
    - name: RetrievalMediator
      methods:
        - access
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

