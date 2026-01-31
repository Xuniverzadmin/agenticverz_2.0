# monitors_facade.py

**Path:** `backend/app/hoc/hoc_spine/services/monitors_facade.py`  
**Layer:** L4 — HOC Spine (Facade)  
**Component:** Services

---

## Placement Card

```
File:            monitors_facade.py
Lives in:        services/
Role:            Services
Inbound:         L2 monitors.py API, SDK, Scheduler
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Monitors Facade (L4 Domain Logic)
Violations:      none
```

## Purpose

Monitors Facade (L4 Domain Logic)

This facade provides the external interface for monitoring operations.
All monitor APIs MUST use this facade instead of directly importing
internal monitor modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes health monitoring logic
- Provides unified access to monitor configuration
- Single point for audit emission

L2 API Routes (GAP-120, GAP-121):
- POST /api/v1/monitors (create monitor)
- GET /api/v1/monitors (list monitors)
- GET /api/v1/monitors/{id} (get monitor)
- PUT /api/v1/monitors/{id} (update monitor)
- DELETE /api/v1/monitors/{id} (delete monitor)
- POST /api/v1/monitors/{id}/check (run health check)
- GET /api/v1/monitors/{id}/history (check history)
- GET /api/v1/monitors/status (overall status)

Usage:
    from app.services.monitors.facade import get_monitors_facade

    facade = get_monitors_facade()

    # Create monitor
    monitor = await facade.create_monitor(
        tenant_id="...",
        name="API Health",
        target={"url": "https://api.example.com/health"},
    )

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_monitors_facade() -> MonitorsFacade`

Get the monitors facade instance.

This is the recommended way to access monitor operations
from L2 APIs and the SDK.

Returns:
    MonitorsFacade instance

## Classes

### `MonitorType(str, Enum)`

Types of monitors.

### `MonitorStatus(str, Enum)`

Monitor status.

### `CheckStatus(str, Enum)`

Health check result status.

### `MonitorConfig`

Monitor configuration.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `HealthCheckResult`

Health check result.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `MonitorStatusSummary`

Overall monitoring status summary.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `MonitorsFacade`

Facade for monitor operations.

This is the ONLY entry point for L2 APIs and SDK to interact with
monitoring services.

Layer: L4 (Domain Logic)
Callers: monitors.py (L2), aos_sdk, Scheduler

#### Methods

- `__init__()` — Initialize facade.
- `async create_monitor(tenant_id: str, name: str, monitor_type: str, target: Dict[str, Any], interval_seconds: int, timeout_seconds: int, retries: int, enabled: bool, metadata: Optional[Dict[str, Any]]) -> MonitorConfig` — Create a monitor.
- `async list_monitors(tenant_id: str, monitor_type: Optional[str], status: Optional[str], enabled_only: bool, limit: int, offset: int) -> List[MonitorConfig]` — List monitors.
- `async get_monitor(monitor_id: str, tenant_id: str) -> Optional[MonitorConfig]` — Get a specific monitor.
- `async update_monitor(monitor_id: str, tenant_id: str, name: Optional[str], target: Optional[Dict[str, Any]], interval_seconds: Optional[int], timeout_seconds: Optional[int], retries: Optional[int], enabled: Optional[bool], metadata: Optional[Dict[str, Any]]) -> Optional[MonitorConfig]` — Update a monitor.
- `async delete_monitor(monitor_id: str, tenant_id: str) -> bool` — Delete a monitor.
- `async run_check(monitor_id: str, tenant_id: str) -> Optional[HealthCheckResult]` — Run a health check.
- `async get_check_history(monitor_id: str, tenant_id: str, limit: int, offset: int) -> List[HealthCheckResult]` — Get health check history for a monitor.
- `async get_status_summary(tenant_id: str) -> MonitorStatusSummary` — Get overall monitoring status summary.

## Domain Usage

**Callers:** L2 monitors.py API, SDK, Scheduler

## Export Contract

```yaml
exports:
  functions:
    - name: get_monitors_facade
      signature: "get_monitors_facade() -> MonitorsFacade"
      consumers: ["orchestrator"]
  classes:
    - name: MonitorType
      methods: []
      consumers: ["orchestrator"]
    - name: MonitorStatus
      methods: []
      consumers: ["orchestrator"]
    - name: CheckStatus
      methods: []
      consumers: ["orchestrator"]
    - name: MonitorConfig
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: HealthCheckResult
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: MonitorStatusSummary
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: MonitorsFacade
      methods:
        - create_monitor
        - list_monitors
        - get_monitor
        - update_monitor
        - delete_monitor
        - run_check
        - get_check_history
        - get_status_summary
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

