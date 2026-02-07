# alerts_facade.py

**Path:** `backend/app/hoc/cus/hoc_spine/services/alerts_facade.py`  
**Layer:** L4 — HOC Spine (Facade)  
**Component:** Services

---

## Placement Card

```
File:            alerts_facade.py
Lives in:        services/
Role:            Services
Inbound:         L2 alerts.py API, SDK, Worker
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Alerts Facade (L4 Domain Logic)
Violations:      none
```

## Purpose

Alerts Facade (L4 Domain Logic)

This facade provides the external interface for alert operations.
All alert APIs MUST use this facade instead of directly importing
internal alert modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes alert configuration and routing
- Provides unified access to alert history
- Single point for audit emission

L2 API Routes (GAP-110, GAP-111, GAP-124):
- POST /alerts/rules (create alert rule)
- GET /alerts/rules (list alert rules)
- GET /alerts/rules/{id} (get alert rule)
- PUT /alerts/rules/{id} (update alert rule)
- DELETE /alerts/rules/{id} (delete alert rule)
- GET /alerts/history (alert history)
- GET /alerts/routes (alert routes)
- POST /alerts/routes (create route)

Usage:
    from app.services.alerts.facade import get_alerts_facade

    facade = get_alerts_facade()

    # Create alert rule
    rule = await facade.create_rule(
        tenant_id="...",
        name="High Cost Alert",
        condition={"metric": "cost", "threshold": 1000},
    )

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_alerts_facade() -> AlertsFacade`

Get the alerts facade instance.

This is the recommended way to access alert operations
from L2 APIs and the SDK.

Returns:
    AlertsFacade instance

## Classes

### `AlertSeverity(str, Enum)`

Alert severity levels.

### `AlertStatus(str, Enum)`

Alert status.

### `AlertRule`

Alert rule definition.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `AlertEvent`

Alert event (history entry).

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `AlertRoute`

Alert routing rule.

#### Methods

- `to_dict() -> Dict[str, Any]` — Convert to dictionary.

### `AlertsFacade`

Facade for alert operations.

This is the ONLY entry point for L2 APIs and SDK to interact with
alert services.

Layer: L4 (Domain Logic)
Callers: alerts.py (L2), aos_sdk, Worker

#### Methods

- `__init__()` — Initialize facade.
- `async create_rule(tenant_id: str, name: str, condition: Dict[str, Any], severity: str, description: Optional[str], channels: Optional[List[str]], enabled: bool, metadata: Optional[Dict[str, Any]]) -> AlertRule` — Create an alert rule.
- `async list_rules(tenant_id: str, severity: Optional[str], enabled_only: bool, limit: int, offset: int) -> List[AlertRule]` — List alert rules.
- `async get_rule(rule_id: str, tenant_id: str) -> Optional[AlertRule]` — Get a specific alert rule.
- `async update_rule(rule_id: str, tenant_id: str, name: Optional[str], condition: Optional[Dict[str, Any]], severity: Optional[str], description: Optional[str], channels: Optional[List[str]], enabled: Optional[bool]) -> Optional[AlertRule]` — Update an alert rule.
- `async delete_rule(rule_id: str, tenant_id: str) -> bool` — Delete an alert rule.
- `async list_history(tenant_id: str, rule_id: Optional[str], severity: Optional[str], status: Optional[str], limit: int, offset: int) -> List[AlertEvent]` — List alert history.
- `async get_event(event_id: str, tenant_id: str) -> Optional[AlertEvent]` — Get a specific alert event.
- `async acknowledge_event(event_id: str, tenant_id: str, actor: str) -> Optional[AlertEvent]` — Acknowledge an alert event.
- `async resolve_event(event_id: str, tenant_id: str, actor: str) -> Optional[AlertEvent]` — Resolve an alert event.
- `async trigger_alert(tenant_id: str, rule_id: str, message: str, context: Optional[Dict[str, Any]]) -> AlertEvent` — Trigger an alert (internal use by detection).
- `async create_route(tenant_id: str, name: str, match_labels: Dict[str, str], channel: str, priority_override: Optional[str], enabled: bool) -> AlertRoute` — Create an alert route.
- `async list_routes(tenant_id: str, enabled_only: bool, limit: int, offset: int) -> List[AlertRoute]` — List alert routes.
- `async get_route(route_id: str, tenant_id: str) -> Optional[AlertRoute]` — Get a specific alert route.
- `async delete_route(route_id: str, tenant_id: str) -> bool` — Delete an alert route.

## Domain Usage

**Callers:** L2 alerts.py API, SDK, Worker

## Export Contract

```yaml
exports:
  functions:
    - name: get_alerts_facade
      signature: "get_alerts_facade() -> AlertsFacade"
      consumers: ["orchestrator"]
  classes:
    - name: AlertSeverity
      methods: []
      consumers: ["orchestrator"]
    - name: AlertStatus
      methods: []
      consumers: ["orchestrator"]
    - name: AlertRule
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: AlertEvent
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: AlertRoute
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: AlertsFacade
      methods:
        - create_rule
        - list_rules
        - get_rule
        - update_rule
        - delete_rule
        - list_history
        - get_event
        - acknowledge_event
        - resolve_event
        - trigger_alert
        - create_route
        - list_routes
        - get_route
        - delete_route
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
