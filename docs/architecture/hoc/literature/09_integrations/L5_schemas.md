# Integrations — L5 Schemas (4 files)

**Domain:** integrations  
**Layer:** L5_schemas  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Data contracts — Pydantic models, dataclasses, type references only

---

## audit_schemas.py
**Path:** `backend/app/hoc/cus/integrations/L5_schemas/audit_schemas.py`  
**Layer:** L5_schemas | **Domain:** integrations | **Lines:** 59

**Docstring:** M25 Audit Schemas

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyActivationAudit` | to_dict | Audit record for policy activation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

---

## cus_schemas.py
**Path:** `backend/app/hoc/cus/integrations/L5_schemas/cus_schemas.py`  
**Layer:** L5_schemas | **Domain:** integrations | **Lines:** 498

**Docstring:** Customer Integrations API Schemas

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CusIntegrationCreate` | validate_not_raw_key | Request schema for creating a new integration. |
| `CusIntegrationUpdate` | validate_not_raw_key | Request schema for updating an integration. |
| `CusLLMUsageIngest` |  | Request schema for SDK telemetry ingestion. |
| `CusLLMUsageBatchIngest` |  | Request schema for batch telemetry ingestion. |
| `CusIntegrationResponse` |  | Full integration details response. |
| `CusIntegrationSummary` |  | Integration summary for list views. |
| `CusLimitsStatus` |  | Current usage vs configured limits. |
| `CusUsageSummary` |  | Aggregated usage statistics. |
| `CusIntegrationUsage` |  | Usage for a single integration within a period. |
| `CusLLMUsageResponse` |  | Individual usage record response. |
| `CusHealthCheckResponse` |  | Response from integration health check. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | date, datetime | no |
| `typing` | Any, Dict, List, Optional | no |
| `pydantic` | BaseModel, Field, field_validator | no |
| `app.models.cus_models` | CusHealthState, CusIntegrationStatus, CusPolicyResult, CusProviderType | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

---

## datasource_model.py
**Path:** `backend/app/hoc/cus/integrations/L5_schemas/datasource_model.py`  
**Layer:** L5_schemas | **Domain:** integrations | **Lines:** 582

**Docstring:** CustomerDataSource - Customer data source models and registry.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DataSourceType` |  | Types of data sources. |
| `DataSourceStatus` |  | Status of a data source. |
| `DataSourceConfig` | to_dict, get_connection_url | Configuration for a data source. |
| `CustomerDataSource` | record_connection, record_error, activate, deactivate, deprecate, update_config, add_tag, remove_tag (+4 more) | Representation of a customer data source. |
| `DataSourceError` | __init__, to_dict | Exception for data source errors. |
| `DataSourceStats` | to_dict | Statistics for data sources. |
| `DataSourceRegistry` | __init__, register, get, get_by_name, list, update, activate, deactivate (+4 more) | Registry for managing customer data sources. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_datasource_registry` | `() -> DataSourceRegistry` | no | Get the singleton registry instance. |
| `_reset_registry` | `() -> None` | no | Reset the singleton (for testing). |
| `create_datasource` | `(tenant_id: str, name: str, source_type: DataSourceType, config: Optional[DataSo` | no | Create a new data source using the singleton registry. |
| `get_datasource` | `(source_id: str) -> Optional[CustomerDataSource]` | no | Get a data source by ID using the singleton registry. |
| `list_datasources` | `(tenant_id: Optional[str] = None, source_type: Optional[DataSourceType] = None) ` | no | List data sources using the singleton registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

---

## loop_events.py
**Path:** `backend/app/hoc/cus/integrations/L5_schemas/loop_events.py`  
**Layer:** L5_schemas | **Domain:** integrations | **Lines:** 968

**Docstring:** M25 Integration Loop Events

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ConfidenceCalculator` | calculate_recovery_confidence, should_auto_apply, get_confirmation_level | Centralized confidence calculation. |
| `ConfidenceBand` | from_confidence, allows_auto_apply, requires_human_review | Confidence classification for pattern matching. |
| `LoopStage` |  | Stages in the integration feedback loop. |
| `LoopFailureState` |  | Explicit failure states for when the loop doesn't complete. |
| `PolicyMode` |  | Policy activation modes for safety. |
| `HumanCheckpointType` |  | Types of human intervention points. |
| `LoopEvent` | create, is_success, is_blocked, to_dict | Base event for integration loop. |
| `PatternMatchResult` | from_match, no_match, should_auto_proceed, to_dict | Result of Bridge 1: Incident → Failure Catalog. |
| `RecoverySuggestion` | create, none_available, add_confirmation, to_dict | Result of Bridge 2: Pattern → Recovery. |
| `PolicyRule` | create, record_shadow_evaluation, add_confirmation, record_regret, shadow_block_rate, to_dict | Result of Bridge 3: Recovery → Policy. |
| `RoutingAdjustment` | create, check_kpi_regression, rollback, effective_magnitude, to_dict | Result of Bridge 4: Policy → CARE Routing. |
| `HumanCheckpoint` | create, resolve, is_pending | Human intervention point in the loop. |
| `LoopStatus` | completion_pct, to_console_display, _generate_narrative, to_dict | Complete status of an integration loop instance. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `ensure_json_serializable` | `(obj: Any, path: str = 'root') -> Any` | no | Guard function to ensure all objects stored in details are JSON-serializable. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `uuid` | uuid | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Literal, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

### Constants
`LOOP_MECHANICS_VERSION`, `LOOP_MECHANICS_FROZEN_AT`

---
