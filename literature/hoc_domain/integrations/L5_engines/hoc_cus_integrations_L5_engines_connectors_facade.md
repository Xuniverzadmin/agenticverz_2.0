# hoc_cus_integrations_L5_engines_connectors_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/connectors_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Connectors Facade - Centralized access to connector operations

## Intent

**Role:** Connectors Facade - Centralized access to connector operations
**Reference:** PIN-470, GAP-093 (Connector Registry API)
**Callers:** L2 connectors.py API, SDK

## Purpose

Connectors Facade (L4 Domain Logic)

---

## Functions

### `get_connectors_facade() -> ConnectorsFacade`
- **Async:** No
- **Docstring:** Get the connectors facade instance.  This is the recommended way to access connector operations
- **Calls:** ConnectorsFacade

## Classes

### `ConnectorInfo`
- **Docstring:** Connector information.
- **Methods:** to_dict
- **Class Variables:** id: str, name: str, connector_type: str, status: str, capabilities: List[str], endpoint: Optional[str], tenant_id: str, created_at: datetime, updated_at: Optional[datetime], last_used_at: Optional[datetime], config: Dict[str, Any], metadata: Dict[str, Any]

### `TestResult`
- **Docstring:** Result of connector test.
- **Methods:** to_dict
- **Class Variables:** success: bool, connector_id: str, latency_ms: Optional[int], error: Optional[str], details: Dict[str, Any]

### `ConnectorsFacade`
- **Docstring:** Facade for connector operations.
- **Methods:** __init__, registry, list_connectors, get_connector, register_connector, update_connector, delete_connector, test_connector, _get_capabilities_for_type

## Attributes

- `logger` (line 69)
- `_facade_instance: Optional[ConnectorsFacade]` (line 423)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.integrations.L6_drivers.connector_registry` |

## Callers

L2 connectors.py API, SDK

## Export Contract

```yaml
exports:
  functions:
    - name: get_connectors_facade
      signature: "get_connectors_facade() -> ConnectorsFacade"
  classes:
    - name: ConnectorInfo
      methods: [to_dict]
    - name: TestResult
      methods: [to_dict]
    - name: ConnectorsFacade
      methods: [registry, list_connectors, get_connector, register_connector, update_connector, delete_connector, test_connector]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
