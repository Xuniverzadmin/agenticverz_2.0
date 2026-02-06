# integrations_bridge.py

**Path:** `backend/app/hoc/cus/hoc_spine/orchestrator/coordinators/bridges/integrations_bridge.py`
**Layer:** L4 — HOC Spine (Bridge)
**Component:** Orchestrator / Coordinator / Bridge
**Created:** 2026-02-03
**Reference:** PIN-520 (L4 Uniformity Initiative), PIN-504 (C4 Loop Model)

---

## Placement Card

```
File:            integrations_bridge.py
Lives in:        orchestrator/coordinators/bridges/
Role:            Integrations domain capability factory
Inbound:         hoc_spine/orchestrator/handlers/integrations_handler.py
Outbound:        integrations/L5_engines/* (lazy imports)
Transaction:     none (factory only)
Cross-domain:    no (single domain)
Purpose:         Bridge for integrations L5 engine access from L4
Violations:      none
```

## Purpose

Domain-specific capability factory for integrations L5 engines.
Implements the Switchboard Pattern (Law 4 - PIN-507):

- Never accepts session parameters
- Returns module references for lazy access
- Handler binds session (Law 4 responsibility)
- No retry logic, no decisions, no state

## Capabilities

| Method | Returns | L5 Module |
|--------|---------|-----------|
| `mcp_capability()` | `mcp_tool_invocation_engine` | `invoke_tool`, `list_tools` |
| `connector_capability()` | `connectors_facade` | `get_connector`, `list_connectors`, `register_connector` |
| `health_capability()` | `cus_health_engine` | `check_health`, `get_status` |
| `datasources_capability()` | `datasources_facade` | `get_datasource`, `list_datasources`, `create_datasource` |
| `credentials_capability()` | `cus_integration_engine` | `resolve_credential`, `store_credential` |

## Integrations Driver Bridge (L6 Capabilities)

| Method | Returns | L6 Module | Session |
|--------|---------|-----------|---------|
| `worker_registry_capability(session)` | `WorkerRegistryService` | `worker_registry_driver` | yes |
| `worker_registry_exceptions()` | `WorkerNotFoundError` | `worker_registry_driver` | no |

## IntegrationsEngineBridge (L4 → L5 engine access)

| Method | Returns | L5 Module | Session |
|--------|---------|-----------|---------|
| `incident_creator_capability()` | Incident creator factory | L5 CostBridgesEngine - PIN-520 Iter3.1 (2026-02-06) | no |

## Usage Pattern

```python
from app.hoc.cus.hoc_spine.orchestrator.coordinators.bridges.integrations_bridge import (
    get_integrations_bridge,
)

bridge = get_integrations_bridge()

# Get MCP capability
mcp = bridge.mcp_capability()
result = await mcp.invoke_tool(session, tool_name, params)

# Get connector capability
connectors = bridge.connector_capability()
connector = await connectors.get_connector(session, connector_id)

# Get health capability
health = bridge.health_capability()
status = await health.get_status(tenant_id)
```

## Bridge Contract

| Rule | Enforcement |
|------|-------------|
| Max 5 methods | CI check 19 |
| Returns modules (not sessions) | Code review |
| Lazy imports only | No top-level L5 imports |
| L4 handlers only | Forbidden import check |

## PIN-520 Phase 2

This bridge was created as part of PIN-520 Phase 2 (Bridge Completion).
Completes the bridge coverage for all 10 customer domains.

## PIN-L2-PURITY (L2 Bypass Removal)

Added `IntegrationsDriverBridge` to support L2 logs/tenants routes without
direct L6 imports.

**Caller:**
- `app/hoc/api/cus/logs/tenants.py`

## Singleton Access

```python
_bridge_instance: IntegrationsBridge | None = None

def get_integrations_bridge() -> IntegrationsBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = IntegrationsBridge()
    return _bridge_instance
```

---

*Generated: 2026-02-03*
