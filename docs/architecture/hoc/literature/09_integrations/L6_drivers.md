# Integrations — L6 Drivers (3 files)

**Domain:** integrations  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## connector_registry.py
**Path:** `backend/app/hoc/cus/integrations/L6_drivers/connector_registry.py`  
**Layer:** L6_drivers | **Domain:** integrations | **Lines:** 838

**Docstring:** ConnectorRegistry - Connector management and registration.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ConnectorType` |  | Types of connectors. |
| `ConnectorStatus` |  | Status of a connector. |
| `ConnectorCapability` |  | Capabilities a connector may have. |
| `ConnectorConfig` | to_dict | Base configuration for connectors. |
| `ConnectorError` | __init__, to_dict | Exception for connector errors. |
| `BaseConnector` | __init__, connect, disconnect, health_check, record_connection, record_error, to_dict | Abstract base class for all connectors. |
| `VectorConnector` | __init__, connect, disconnect, health_check, upsert_vectors, search, delete_vectors, to_dict | Connector for vector databases (GAP-061). |
| `FileConnector` | __init__, connect, disconnect, health_check, list_files, read_file, write_file, delete_file (+1 more) | Connector for file storage (GAP-062). |
| `ServerlessConnector` | __init__, connect, disconnect, health_check, invoke, list_functions, get_result, to_dict | Connector for serverless functions (GAP-064). |
| `ConnectorStats` | to_dict | Statistics for connectors. |
| `ConnectorRegistry` | __init__, register, create_vector_connector, create_file_connector, create_serverless_connector, get, get_by_name, list (+4 more) | Registry for managing connectors (GAP-057). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_connector_registry` | `() -> ConnectorRegistry` | no | Get the singleton registry instance. |
| `_reset_registry` | `() -> None` | no | Reset the singleton (for testing). |
| `register_connector` | `(connector: BaseConnector) -> BaseConnector` | no | Register a connector using the singleton registry. |
| `get_connector` | `(connector_id: str) -> Optional[BaseConnector]` | no | Get a connector by ID using the singleton registry. |
| `list_connectors` | `(tenant_id: Optional[str] = None, connector_type: Optional[ConnectorType] = None` | no | List connectors using the singleton registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `abc` | ABC, abstractmethod | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## external_response_driver.py
**Path:** `backend/app/hoc/cus/integrations/L6_drivers/external_response_driver.py`  
**Layer:** L6_drivers | **Domain:** integrations | **Lines:** 289

**Docstring:** External Response Driver (Phase E FIX-04)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ExternalResponseService` | __init__, record_raw_response, interpret, get_raw_for_interpretation, get_interpreted, get_pending_interpretations | Service for external response operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `record_external_response` | `(session: Session, source: str, raw_response: dict, interpretation_owner: str, i` | no | Record a raw external response (L3 → L6). |
| `interpret_response` | `(session: Session, response_id: UUID, interpreted_value: dict, interpreted_by: s` | no | Record L4 engine interpretation (L4 → L6). |
| `get_interpreted_response` | `(session: Session, response_id: UUID) -> Optional[InterpretedResponse]` | no | Get interpreted response for consumers (L5/L2 ← L6). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `typing` | Optional | no |
| `uuid` | UUID | no |
| `sqlalchemy` | and_, select, update | no |
| `sqlalchemy.orm` | Session | no |
| `app.models.external_response` | ExternalResponse, InterpretedResponse | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## worker_registry_driver.py
**Path:** `backend/app/hoc/cus/integrations/L6_drivers/worker_registry_driver.py`  
**Layer:** L6_drivers | **Domain:** integrations | **Lines:** 424

**Docstring:** Worker Registry Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `WorkerRegistryError` |  | Base exception for worker registry errors. |
| `WorkerNotFoundError` |  | Raised when a worker is not found. |
| `WorkerUnavailableError` |  | Raised when a worker is not available. |
| `WorkerRegistryService` | __init__, get_worker, get_worker_or_raise, list_workers, list_available_workers, is_worker_available, get_worker_details, get_worker_summary (+10 more) | Service for worker registry operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_worker_registry_service` | `(session: Session) -> WorkerRegistryService` | no | Get a WorkerRegistryService instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `typing` | Any, Dict, List, Optional | no |
| `sqlmodel` | Session, select | no |
| `app.models.tenant` | WorkerConfig, WorkerRegistry | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`WorkerRegistryService`, `WorkerRegistryError`, `WorkerNotFoundError`, `WorkerUnavailableError`, `get_worker_registry_service`

---
