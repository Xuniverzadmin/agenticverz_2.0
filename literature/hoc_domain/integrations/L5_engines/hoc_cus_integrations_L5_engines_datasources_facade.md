# hoc_cus_integrations_L5_engines_datasources_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/datasources_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

DataSources Facade - Centralized access to data source operations

## Intent

**Role:** DataSources Facade - Centralized access to data source operations
**Reference:** PIN-470, GAP-113 (Data Sources API)
**Callers:** L2 datasources.py API, SDK

## Purpose

DataSources Facade (L4 Domain Logic)

---

## Functions

### `get_datasources_facade() -> DataSourcesFacade`
- **Async:** No
- **Docstring:** Get the data sources facade instance.  This is the recommended way to access data source operations
- **Calls:** DataSourcesFacade

## Classes

### `TestConnectionResult`
- **Docstring:** Result of testing a data source connection.
- **Methods:** to_dict
- **Class Variables:** success: bool, message: str, latency_ms: Optional[int], details: Optional[Dict[str, Any]]

### `DataSourcesFacade`
- **Docstring:** Facade for data source operations.
- **Methods:** __init__, registry, register_source, list_sources, get_source, update_source, delete_source, test_connection, activate_source, deactivate_source, get_statistics

## Attributes

- `logger` (line 71)
- `_facade_instance: Optional[DataSourcesFacade]` (line 435)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Schema | `app.hoc.cus.integrations.L5_schemas.datasource_model` |

## Callers

L2 datasources.py API, SDK

## Export Contract

```yaml
exports:
  functions:
    - name: get_datasources_facade
      signature: "get_datasources_facade() -> DataSourcesFacade"
  classes:
    - name: TestConnectionResult
      methods: [to_dict]
    - name: DataSourcesFacade
      methods: [registry, register_source, list_sources, get_source, update_source, delete_source, test_connection, activate_source, deactivate_source, get_statistics]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
