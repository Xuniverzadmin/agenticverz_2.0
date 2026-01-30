# hoc_cus_integrations_L5_schemas_datasource_model

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_schemas/datasource_model.py` |
| Layer | L5 — Domain Engines |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

CustomerDataSource - Customer data source models and registry.

## Intent

**Reference:** GAP-055 (CustomerDataSource model)

## Purpose

CustomerDataSource - Customer data source models and registry.

---

## Functions

### `get_datasource_registry() -> DataSourceRegistry`
- **Async:** No
- **Docstring:** Get the singleton registry instance.
- **Calls:** DataSourceRegistry

### `_reset_registry() -> None`
- **Async:** No
- **Docstring:** Reset the singleton (for testing).
- **Calls:** reset

### `create_datasource(tenant_id: str, name: str, source_type: DataSourceType, config: Optional[DataSourceConfig]) -> CustomerDataSource`
- **Async:** No
- **Docstring:** Create a new data source using the singleton registry.
- **Calls:** get_datasource_registry, register

### `get_datasource(source_id: str) -> Optional[CustomerDataSource]`
- **Async:** No
- **Docstring:** Get a data source by ID using the singleton registry.
- **Calls:** get, get_datasource_registry

### `list_datasources(tenant_id: Optional[str], source_type: Optional[DataSourceType]) -> list[CustomerDataSource]`
- **Async:** No
- **Docstring:** List data sources using the singleton registry.
- **Calls:** get_datasource_registry, list

## Classes

### `DataSourceType(str, Enum)`
- **Docstring:** Types of data sources.

### `DataSourceStatus(str, Enum)`
- **Docstring:** Status of a data source.

### `DataSourceConfig`
- **Docstring:** Configuration for a data source.
- **Methods:** to_dict, get_connection_url
- **Class Variables:** connection_string: Optional[str], host: Optional[str], port: Optional[int], username: Optional[str], password: Optional[str], database: Optional[str], auth_type: Optional[str], api_key: Optional[str], oauth_config: Optional[dict[str, Any]], pool_size: int, pool_timeout: int, max_retries: int, ssl_enabled: bool, ssl_verify: bool, ssl_cert_path: Optional[str], options: dict[str, Any]

### `CustomerDataSource`
- **Docstring:** Representation of a customer data source.
- **Methods:** record_connection, record_error, activate, deactivate, deprecate, update_config, add_tag, remove_tag, grant_access, revoke_access, has_access, to_dict
- **Class Variables:** source_id: str, tenant_id: str, name: str, source_type: DataSourceType, config: DataSourceConfig, status: DataSourceStatus, description: Optional[str], tags: list[str], metadata: dict[str, Any], access_roles: list[str], owner_id: Optional[str], last_connected: Optional[datetime], last_error: Optional[str], connection_count: int, error_count: int, created_at: datetime, updated_at: datetime

### `DataSourceError(Exception)`
- **Docstring:** Exception for data source errors.
- **Methods:** __init__, to_dict

### `DataSourceStats`
- **Docstring:** Statistics for data sources.
- **Methods:** to_dict
- **Class Variables:** total_sources: int, active_sources: int, inactive_sources: int, error_sources: int, pending_sources: int, sources_by_type: dict[str, int], total_connections: int, total_errors: int

### `DataSourceRegistry`
- **Docstring:** Registry for managing customer data sources.
- **Methods:** __init__, register, get, get_by_name, list, update, activate, deactivate, delete, get_statistics, clear_tenant, reset

## Attributes

- `_registry: Optional[DataSourceRegistry]` (line 534)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

_Not declared in file header._

## Export Contract

```yaml
exports:
  functions:
    - name: get_datasource_registry
      signature: "get_datasource_registry() -> DataSourceRegistry"
    - name: create_datasource
      signature: "create_datasource(tenant_id: str, name: str, source_type: DataSourceType, config: Optional[DataSourceConfig]) -> CustomerDataSource"
    - name: get_datasource
      signature: "get_datasource(source_id: str) -> Optional[CustomerDataSource]"
    - name: list_datasources
      signature: "list_datasources(tenant_id: Optional[str], source_type: Optional[DataSourceType]) -> list[CustomerDataSource]"
  classes:
    - name: DataSourceType
      methods: []
    - name: DataSourceStatus
      methods: []
    - name: DataSourceConfig
      methods: [to_dict, get_connection_url]
    - name: CustomerDataSource
      methods: [record_connection, record_error, activate, deactivate, deprecate, update_config, add_tag, remove_tag, grant_access, revoke_access, has_access, to_dict]
    - name: DataSourceError
      methods: [to_dict]
    - name: DataSourceStats
      methods: [to_dict]
    - name: DataSourceRegistry
      methods: [register, get, get_by_name, list, update, activate, deactivate, delete, get_statistics, clear_tenant, reset]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
