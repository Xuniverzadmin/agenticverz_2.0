# Integrations — L5 Engines (8 files)

**Domain:** integrations  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## connectors_facade.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/connectors_facade.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 439

**Docstring:** Connectors Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ConnectorInfo` | to_dict | Connector information. |
| `TestResult` | to_dict | Result of connector test. |
| `ConnectorsFacade` | __init__, registry, list_connectors, get_connector, register_connector, update_connector, delete_connector, test_connector (+1 more) | Facade for connector operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_connectors_facade` | `() -> ConnectorsFacade` | no | Get the connectors facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## cus_health_engine.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/cus_health_engine.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 542

**Docstring:** Customer Health Engine

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CusHealthService` | __init__, _get_driver, check_health, _perform_health_check, check_all_integrations, get_health_summary, _calculate_overall_health | Service for health checking customer LLM integrations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `logging` | logging | no |
| `contextlib` | contextmanager | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `httpx` | httpx | no |
| `app.hoc.cus.integrations.L5_schemas.cus_enums` | CusHealthState | no |
| `app.hoc.cus.hoc_spine.services.cus_credential_engine` | CusCredentialService | no |
| `app.hoc.cus.integrations.L6_drivers.cus_health_driver` | CusHealthDriver, HealthIntegrationRow, cus_health_driver_session | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## datasources_facade.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/datasources_facade.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 451

**Docstring:** DataSources Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TestConnectionResult` | to_dict | Result of testing a data source connection. |
| `DataSourcesFacade` | __init__, registry, register_source, list_sources, get_source, update_source, delete_source, test_connection (+3 more) | Facade for data source operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_datasources_facade` | `() -> DataSourcesFacade` | no | Get the data sources facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.hoc.cus.integrations.L5_schemas.datasource_model` | CustomerDataSource, DataSourceConfig, DataSourceRegistry, DataSourceStats, DataSourceStatus (+2) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## integrations_facade.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/integrations_facade.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 506

**Docstring:** Integrations Domain Facade (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IntegrationSummaryResult` |  | Integration summary for list view. |
| `IntegrationListResult` |  | Integration list response. |
| `IntegrationDetailResult` |  | Integration detail response. |
| `IntegrationLifecycleResult` |  | Result of enable/disable operation. |
| `IntegrationDeleteResult` |  | Result of delete operation. |
| `HealthCheckResult` |  | Health check result. |
| `HealthStatusResult` |  | Cached health status. |
| `LimitsStatusResult` |  | Usage vs limits status. |
| `IntegrationsFacade` | __init__, list_integrations, get_integration, create_integration, update_integration, delete_integration, enable_integration, disable_integration (+3 more) | Unified facade for LLM integration management. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_integrations_facade` | `(session) -> IntegrationsFacade` | no | Get an IntegrationsFacade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |
| `app.hoc.cus.integrations.L5_engines.cus_integration_engine` | CusIntegrationEngine, get_cus_integration_engine | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`IntegrationsFacade`, `get_integrations_facade`, `IntegrationSummaryResult`, `IntegrationListResult`, `IntegrationDetailResult`, `IntegrationLifecycleResult`, `IntegrationDeleteResult`, `HealthCheckResult`, `HealthStatusResult`, `LimitsStatusResult`

---

## prevention_contract.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/prevention_contract.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 206

**Docstring:** M25 Prevention Contract Enforcement

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PreventionContractViolation` | __init__ | Raised when a prevention record would violate the contract. |
| `PreventionCandidate` |  | Candidate for prevention record creation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `validate_prevention_candidate` | `(candidate: PreventionCandidate) -> None` | no | Validate that a prevention candidate satisfies the contract. |
| `assert_prevention_immutable` | `(record_id: str, existing_record: dict[str, Any]) -> None` | no | Assert that a prevention record has not been modified. |
| `assert_no_deletion` | `(record_id: str) -> None` | no | Assert that a prevention record cannot be deleted. |
| `validate_prevention_for_graduation` | `(prevention_record: dict[str, Any], policy_activated_at: datetime) -> bool` | no | Validate that a prevention record counts toward graduation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`PREVENTION_CONTRACT_VERSION`, `PREVENTION_CONTRACT_FROZEN_AT`

---

## protocol.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/credentials/protocol.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 63

**Docstring:** CredentialService Protocol — Canonical Definition

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CredentialService` | get | Protocol for credential service. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Protocol, runtime_checkable | no |
| `app.hoc.cus.integrations.L5_engines.types` | Credential | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## sql_gateway.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/sql_gateway.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 429

**Docstring:** Module: sql_gateway

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ParameterType` |  | Supported parameter types for validation. |
| `ParameterSpec` |  | Specification for a query parameter. |
| `QueryTemplate` |  | Definition of a SQL query template. |
| `SqlGatewayConfig` |  | Configuration for SQL gateway. |
| `SqlGatewayError` |  | Error from SQL gateway. |
| `SqlInjectionAttemptError` |  | Potential SQL injection detected. |
| `SqlGatewayService` | __init__, id, execute, _resolve_template, _validate_parameters, _coerce_parameter, _check_sql_injection, _get_connection_string | Governed SQL gateway. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional, TYPE_CHECKING | no |
| `datetime` | datetime | no |
| `enum` | Enum | no |
| `logging` | logging | no |
| `app.hoc.cus.integrations.L5_engines.credentials` | Credential, CredentialService | no |
| `app.hoc.cus.integrations.L5_schemas.sql_gateway_protocol` | SqlQueryRequest, SqlQueryResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`DEFAULT_MAX_ROWS`, `DEFAULT_MAX_RESULT_BYTES`, `DEFAULT_TIMEOUT_SECONDS`

---

## types.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/types.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 56

**Docstring:** Credential Type — Canonical Definition

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `Credential` |  | Credential from vault. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---
