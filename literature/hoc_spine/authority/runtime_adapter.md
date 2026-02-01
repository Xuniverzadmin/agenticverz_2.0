# runtime_adapter.py

**Path:** `backend/app/hoc/cus/hoc_spine/authority/runtime_adapter.py`  
**Layer:** L4 — HOC Spine (Authority)  
**Component:** Authority

---

## Placement Card

```
File:            runtime_adapter.py
Lives in:        authority/
Role:            Authority
Inbound:         runtime.py (L2)
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Runtime Adapter (L2)
Violations:      none
```

## Purpose

Runtime Adapter (L2)

Adapter for runtime API operations. This is the boundary between:
- L2 (API routes) - callers
- L4 (Domain commands) - domain decisions

This adapter:
1. Receives API requests from L2
2. Translates them into L4 domain facts
3. Calls L4 command functions
4. Returns domain results to L2

It does NOT:
- Import from L5 (workers)
- Execute skills directly
- Make domain decisions (that's L4's job)

Reference: PIN-258 Phase F-3 Runtime Cluster

## Import Analysis

**External:**
- `app.commands.runtime_command`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_runtime_adapter() -> RuntimeAdapter`

Factory function to get RuntimeAdapter instance.

This is the entry point for L2 to get the adapter.

Returns:
    RuntimeAdapter instance

Reference: PIN-258 Phase F-3

## Classes

### `RuntimeAdapter`

Adapter for runtime operations.

Translates API requests into L4 domain commands.
This is the ONLY runtime interface L2 may call.

Reference: PIN-258 Phase F-3 Runtime Cluster

#### Methods

- `__init__()` — Initialize the adapter.
- `query(query_type: str, params: Optional[Dict[str, Any]]) -> QueryResult` — Execute a runtime query.
- `get_supported_queries() -> List[str]` — Get list of supported query types.
- `describe_skill(skill_id: str) -> Optional[SkillInfo]` — Get skill description.
- `list_skills() -> List[str]` — List all available skills.
- `get_skill_descriptors() -> Dict[str, Dict[str, Any]]` — Get descriptors for all skills.
- `get_resource_contract(resource_id: str) -> ResourceContractInfo` — Get resource contract.
- `get_capabilities(agent_id: Optional[str], tenant_id: Optional[str]) -> CapabilitiesInfo` — Get capabilities for an agent/tenant.

## Domain Usage

**Callers:** runtime.py (L2)

## Export Contract

```yaml
exports:
  functions:
    - name: get_runtime_adapter
      signature: "get_runtime_adapter() -> RuntimeAdapter"
      consumers: ["orchestrator"]
  classes:
    - name: RuntimeAdapter
      methods:
        - query
        - get_supported_queries
        - describe_skill
        - list_skills
        - get_skill_descriptors
        - get_resource_contract
        - get_capabilities
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: ['app.commands.runtime_command']
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

