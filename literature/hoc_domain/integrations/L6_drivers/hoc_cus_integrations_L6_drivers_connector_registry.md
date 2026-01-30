# hoc_cus_integrations_L6_drivers_connector_registry

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L6_drivers/connector_registry.py` |
| Layer | L6 — Domain Driver |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Connector management and registration

## Intent

**Role:** Connector management and registration
**Reference:** PIN-470, GAP-057 (ConnectorRegistry), GAP-061/062/064 (Connectors)
**Callers:** L5 engines

## Purpose

ConnectorRegistry - Connector management and registration.

---

## Functions

### `get_connector_registry() -> ConnectorRegistry`
- **Async:** No
- **Docstring:** Get the singleton registry instance.
- **Calls:** ConnectorRegistry

### `_reset_registry() -> None`
- **Async:** No
- **Docstring:** Reset the singleton (for testing).
- **Calls:** reset

### `register_connector(connector: BaseConnector) -> BaseConnector`
- **Async:** No
- **Docstring:** Register a connector using the singleton registry.
- **Calls:** get_connector_registry, register

### `get_connector(connector_id: str) -> Optional[BaseConnector]`
- **Async:** No
- **Docstring:** Get a connector by ID using the singleton registry.
- **Calls:** get, get_connector_registry

### `list_connectors(tenant_id: Optional[str], connector_type: Optional[ConnectorType]) -> list[BaseConnector]`
- **Async:** No
- **Docstring:** List connectors using the singleton registry.
- **Calls:** get_connector_registry, list

## Classes

### `ConnectorType(str, Enum)`
- **Docstring:** Types of connectors.

### `ConnectorStatus(str, Enum)`
- **Docstring:** Status of a connector.

### `ConnectorCapability(str, Enum)`
- **Docstring:** Capabilities a connector may have.

### `ConnectorConfig`
- **Docstring:** Base configuration for connectors.
- **Methods:** to_dict
- **Class Variables:** endpoint: Optional[str], timeout_seconds: int, max_retries: int, retry_delay_seconds: int, auth_type: Optional[str], credentials: dict[str, Any], rate_limit_enabled: bool, rate_limit_requests: int, rate_limit_window_seconds: int, options: dict[str, Any]

### `ConnectorError(Exception)`
- **Docstring:** Exception for connector errors.
- **Methods:** __init__, to_dict

### `BaseConnector(ABC)`
- **Docstring:** Abstract base class for all connectors.
- **Methods:** __init__, connect, disconnect, health_check, record_connection, record_error, to_dict

### `VectorConnector(BaseConnector)`
- **Docstring:** Connector for vector databases (GAP-061).
- **Methods:** __init__, connect, disconnect, health_check, upsert_vectors, search, delete_vectors, to_dict

### `FileConnector(BaseConnector)`
- **Docstring:** Connector for file storage (GAP-062).
- **Methods:** __init__, connect, disconnect, health_check, list_files, read_file, write_file, delete_file, to_dict

### `ServerlessConnector(BaseConnector)`
- **Docstring:** Connector for serverless functions (GAP-064).
- **Methods:** __init__, connect, disconnect, health_check, invoke, list_functions, get_result, to_dict

### `ConnectorStats`
- **Docstring:** Statistics for connectors.
- **Methods:** to_dict
- **Class Variables:** total_connectors: int, ready_connectors: int, connected_connectors: int, error_connectors: int, connectors_by_type: dict[str, int], total_connections: int, total_errors: int

### `ConnectorRegistry`
- **Docstring:** Registry for managing connectors (GAP-057).
- **Methods:** __init__, register, create_vector_connector, create_file_connector, create_serverless_connector, get, get_by_name, list, delete, get_statistics, clear_tenant, reset

## Attributes

- `_registry: Optional[ConnectorRegistry]` (line 800)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

L5 engines

## Export Contract

```yaml
exports:
  functions:
    - name: get_connector_registry
      signature: "get_connector_registry() -> ConnectorRegistry"
    - name: register_connector
      signature: "register_connector(connector: BaseConnector) -> BaseConnector"
    - name: get_connector
      signature: "get_connector(connector_id: str) -> Optional[BaseConnector]"
    - name: list_connectors
      signature: "list_connectors(tenant_id: Optional[str], connector_type: Optional[ConnectorType]) -> list[BaseConnector]"
  classes:
    - name: ConnectorType
      methods: []
    - name: ConnectorStatus
      methods: []
    - name: ConnectorCapability
      methods: []
    - name: ConnectorConfig
      methods: [to_dict]
    - name: ConnectorError
      methods: [to_dict]
    - name: BaseConnector
      methods: [connect, disconnect, health_check, record_connection, record_error, to_dict]
    - name: VectorConnector
      methods: [connect, disconnect, health_check, upsert_vectors, search, delete_vectors, to_dict]
    - name: FileConnector
      methods: [connect, disconnect, health_check, list_files, read_file, write_file, delete_file, to_dict]
    - name: ServerlessConnector
      methods: [connect, disconnect, health_check, invoke, list_functions, get_result, to_dict]
    - name: ConnectorStats
      methods: [to_dict]
    - name: ConnectorRegistry
      methods: [register, create_vector_connector, create_file_connector, create_serverless_connector, get, get_by_name, list, delete, get_statistics, clear_tenant, reset]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
