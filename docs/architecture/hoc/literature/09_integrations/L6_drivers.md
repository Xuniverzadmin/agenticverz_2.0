# Integrations — L6 Drivers (8 files)

**Domain:** integrations  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## bridges_driver.py
**Path:** `backend/app/hoc/cus/integrations/L6_drivers/bridges_driver.py`  
**Layer:** L6_drivers | **Domain:** integrations | **Lines:** 114

**Docstring:** M25 Bridges Driver

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `record_policy_activation` | `(session: AsyncSession, policy_id: str, source_pattern_id: str, source_recovery_` | yes | Record policy activation for audit trail. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.hoc.cus.integrations.L5_schemas.audit_schemas` | PolicyActivationAudit | no |
| `app.hoc.cus.integrations.L5_schemas.loop_events` | ConfidenceCalculator | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## connector_registry_driver.py
**Path:** `backend/app/hoc/cus/integrations/L6_drivers/connector_registry_driver.py`  
**Layer:** L6_drivers | **Domain:** integrations | **Lines:** 839

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## cus_health_driver.py
**Path:** `backend/app/hoc/cus/integrations/L6_drivers/cus_health_driver.py`  
**Layer:** L6_drivers | **Domain:** integrations | **Lines:** 258

**Docstring:** Customer Health Driver

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `HealthIntegrationRow` |  | Immutable data transfer object for health-relevant integration data. |
| `CusHealthDriver` | __init__, fetch_integration_for_health_check, fetch_stale_enabled_integrations, fetch_all_integrations_for_tenant, update_health_state | L6 driver for health-check data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_to_row` | `(integration: CusIntegration) -> HealthIntegrationRow` | no | Convert ORM model to frozen DTO. |
| `get_cus_health_driver` | `(session: Session) -> CusHealthDriver` | no | Get driver instance. |
| `cus_health_driver_session` | `() -> Generator[CusHealthDriver, None, None]` | no | Context manager that creates a Session-bound CusHealthDriver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `contextlib` | contextmanager | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Generator, List, Optional | no |
| `uuid` | UUID | no |
| `sqlmodel` | Session, select | no |
| `app.models.cus_models` | CusHealthState, CusIntegration | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## cus_integration_driver.py
**Path:** `backend/app/hoc/cus/integrations/L6_drivers/cus_integration_driver.py`  
**Layer:** L6_drivers | **Domain:** integrations | **Lines:** 466

**Docstring:** Customer Integration Driver

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IntegrationRow` |  | Immutable data transfer object. |
| `UsageAggregate` |  | Immutable usage aggregate row. |
| `CusIntegrationDriver` | __init__, fetch_by_id, fetch_by_name, fetch_list, fetch_monthly_usage, fetch_current_rpm, create, update_fields (+3 more) | L6 driver for customer integration data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_cus_integration_driver` | `(session: Session) -> CusIntegrationDriver` | no | Get driver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | date, datetime, timezone | no |
| `typing` | Any, Dict, List, Optional, Tuple | no |
| `uuid` | UUID, uuid4 | no |
| `sqlmodel` | Session, col, func, select | no |
| `app.models.cus_models` | CusHealthState, CusIntegration, CusIntegrationStatus, CusLLMUsage, CusUsageDaily | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## mcp_driver.py
**Path:** `backend/app/hoc/cus/integrations/L6_drivers/mcp_driver.py`  
**Layer:** L6_drivers | **Domain:** integrations | **Lines:** 754

**Docstring:** MCP Driver - Pure persistence layer for MCP servers and tools.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `McpServerRow` |  | Immutable DTO for MCP server database row. |
| `McpToolRow` |  | Immutable DTO for MCP tool database row. |
| `McpInvocationRow` |  | Immutable DTO for MCP tool invocation database row. |
| `McpDriver` | __init__, create_server, get_server, get_server_by_url, list_servers, update_server, soft_delete_server, upsert_tools (+11 more) | L6 driver for MCP persistence. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `compute_input_hash` | `(params: Dict[str, Any]) -> str` | no | Compute SHA256 hash of input parameters. |
| `compute_output_hash` | `(output: Any) -> str` | no | Compute SHA256 hash of output. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid4 | no |
| `sqlalchemy` | and_, select, update | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.mcp_models` | McpServer, McpTool, McpToolInvocation | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## proxy_driver.py
**Path:** `backend/app/hoc/cus/integrations/L6_drivers/proxy_driver.py`  
**Layer:** L6_drivers | **Domain:** integrations | **Lines:** 526

**Docstring:** Proxy Driver - Pure persistence layer for OpenAI proxy operations.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ApiKeyRow` |  | Immutable DTO for API key database row. |
| `TenantRow` |  | Immutable DTO for tenant database row. |
| `KillSwitchStateRow` |  | Immutable DTO for killswitch state database row. |
| `GuardrailRow` |  | Immutable DTO for default guardrail database row. |
| `LatencyStats` |  | Immutable DTO for latency statistics. |
| `IncidentRow` |  | Immutable DTO for incident database row. |
| `ProxyDriver` | __init__, get_api_key_by_hash, get_api_key_id_and_tenant, record_api_key_usage, get_tenant_by_id, get_killswitch_state, get_enabled_guardrails, log_proxy_call (+3 more) | L6 driver for OpenAI proxy persistence. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_proxy_driver` | `(session: Session) -> ProxyDriver` | no | Get ProxyDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta, timezone | no |
| `decimal` | Decimal | no |
| `typing` | Any, Dict, List, Optional | no |
| `sqlalchemy` | text | no |
| `sqlmodel` | Session | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

---

## sql_gateway_driver.py
**Path:** `backend/app/hoc/cus/integrations/L6_drivers/sql_gateway_driver.py`  
**Layer:** L6_drivers | **Domain:** integrations | **Lines:** 108

**Docstring:** SQL Gateway Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SqlGatewayDriver` | execute_query | L6 driver: executes parameterized SQL against external databases. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_sql_gateway_driver` | `() -> SqlGatewayDriver` | no | Factory for L4/L5 callers. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `logging` | logging | no |
| `typing` | Any, Dict, List | no |
| `asyncpg` | asyncpg | no |
| `app.hoc.cus.integrations.L5_schemas.sql_gateway_protocol` | SqlQueryRequest, SqlQueryResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L4_spine, L5_engines
**Called by:** L5_engines, L4_spine

### __all__ Exports
`WorkerRegistryService`, `WorkerRegistryError`, `WorkerNotFoundError`, `WorkerUnavailableError`, `get_worker_registry_service`

---
