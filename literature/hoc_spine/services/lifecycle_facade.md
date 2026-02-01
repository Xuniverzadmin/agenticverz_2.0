# lifecycle_facade.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/lifecycle_facade.py`  
**Layer:** L4 — HOC Spine (Facade)  
**Component:** Services

---

## Placement Card

```
File:            lifecycle_facade.py
Lives in:        services/
Role:            Services
Inbound:         L2 lifecycle.py API, SDK
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Lifecycle Facade (L4 Domain Logic)
Violations:      none
```

## Purpose

Lifecycle Facade (L4 Domain Logic)

This facade provides the external interface for lifecycle operations.
All lifecycle APIs MUST use this facade instead of directly importing
internal lifecycle modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes agent and run lifecycle logic
- Provides unified access to state transitions
- Single point for audit emission

L2 API Routes (GAP-131 to GAP-136):
- POST /api/v1/lifecycle/agents (create agent)
- GET /api/v1/lifecycle/agents (list agents)
- GET /api/v1/lifecycle/agents/{id} (get agent)
- POST /api/v1/lifecycle/agents/{id}/start (start agent)
- POST /api/v1/lifecycle/agents/{id}/stop (stop agent)
- POST /api/v1/lifecycle/agents/{id}/terminate (terminate agent)
- POST /api/v1/lifecycle/runs (create run)
- GET /api/v1/lifecycle/runs (list runs)
- GET /api/v1/lifecycle/runs/{id} (get run)
- POST /api/v1/lifecycle/runs/{id}/pause (pause run)
- POST /api/v1/lifecycle/runs/{id}/resume (resume run)
- POST /api/v1/lifecycle/runs/{id}/cancel (cancel run)

Usage:
    # L5 engine import (V2.0.0 - hoc_spine)
    from app.hoc.cus.hoc_spine.services.lifecycle_facade import get_lifecycle_facade

    facade = get_lifecycle_facade()

    # Start an agent
    agent = await facade.start_agent(agent_id="...", tenant_id="...")

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_lifecycle_facade() -> LifecycleFacade`

Get the lifecycle facade instance.

This is the recommended way to access lifecycle operations
from L2 APIs and the SDK.

Returns:
    LifecycleFacade instance

## Classes

### `AgentState(str, Enum)`

Agent lifecycle states.

### `RunState(str, Enum)`

Run lifecycle states.

### `AgentLifecycle`

Agent lifecycle information.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `RunLifecycle`

Run lifecycle information.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `LifecycleSummary`

Summary of lifecycle entities.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `LifecycleFacade`

Facade for lifecycle operations.

This is the ONLY entry point for L2 APIs and SDK to interact with
lifecycle services.

Layer: L4 (Domain Logic)
Callers: lifecycle.py (L2), aos_sdk

#### Methods

- `__init__()` — Initialize facade.
- `async create_agent(tenant_id: str, name: str, config: Optional[Dict[str, Any]], metadata: Optional[Dict[str, Any]]) -> AgentLifecycle` — Create a new agent.
- `async list_agents(tenant_id: str, state: Optional[str], limit: int, offset: int) -> List[AgentLifecycle]` — List agents for a tenant.
- `async get_agent(agent_id: str, tenant_id: str) -> Optional[AgentLifecycle]` — Get a specific agent.
- `async start_agent(agent_id: str, tenant_id: str) -> Optional[AgentLifecycle]` — Start an agent.
- `async stop_agent(agent_id: str, tenant_id: str) -> Optional[AgentLifecycle]` — Stop an agent.
- `async terminate_agent(agent_id: str, tenant_id: str) -> Optional[AgentLifecycle]` — Terminate an agent.
- `async create_run(tenant_id: str, agent_id: str, input_data: Optional[Dict[str, Any]], metadata: Optional[Dict[str, Any]]) -> Optional[RunLifecycle]` — Create a new run.
- `async list_runs(tenant_id: str, agent_id: Optional[str], state: Optional[str], limit: int, offset: int) -> List[RunLifecycle]` — List runs for a tenant.
- `async get_run(run_id: str, tenant_id: str) -> Optional[RunLifecycle]` — Get a specific run.
- `async pause_run(run_id: str, tenant_id: str) -> Optional[RunLifecycle]` — Pause a run.
- `async resume_run(run_id: str, tenant_id: str) -> Optional[RunLifecycle]` — Resume a paused run.
- `async cancel_run(run_id: str, tenant_id: str) -> Optional[RunLifecycle]` — Cancel a run.
- `async get_summary(tenant_id: str) -> LifecycleSummary` — Get lifecycle summary for a tenant.

## Domain Usage

**Callers:** L2 lifecycle.py API, SDK

## Export Contract

```yaml
exports:
  functions:
    - name: get_lifecycle_facade
      signature: "get_lifecycle_facade() -> LifecycleFacade"
      consumers: ["orchestrator"]
  classes:
    - name: AgentState
      methods: []
      consumers: ["orchestrator"]
    - name: RunState
      methods: []
      consumers: ["orchestrator"]
    - name: AgentLifecycle
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: RunLifecycle
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: LifecycleSummary
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: LifecycleFacade
      methods:
        - create_agent
        - list_agents
        - get_agent
        - start_agent
        - stop_agent
        - terminate_agent
        - create_run
        - list_runs
        - get_run
        - pause_run
        - resume_run
        - cancel_run
        - get_summary
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

