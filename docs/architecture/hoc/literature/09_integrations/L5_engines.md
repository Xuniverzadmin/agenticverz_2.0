# Integrations — L5 Engines (16 files)

**Domain:** integrations  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## bridges.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/bridges.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 1229

**Docstring:** M25 Integration Bridges

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `BaseBridge` | stage, process, register | Base class for all integration bridges. |
| `IncidentToCatalogBridge` | __init__, stage, process, _extract_signature, _hash_signature, _find_matching_pattern, _calculate_fuzzy_confidence, _increment_pattern_count (+1 more) | Bridge 1: Route incidents to failure catalog. |
| `PatternToRecoveryBridge` | __init__, stage, process, _load_pattern, _instantiate_template, _generate_recovery, _apply_recovery, _queue_for_review (+1 more) | Bridge 2: Generate recovery suggestions from patterns. |
| `RecoveryToPolicyBridge` | __init__, stage, process, _load_pattern, _generate_policy, _persist_policy | Bridge 3: Convert applied recovery into prevention policy. |
| `PolicyToRoutingBridge` | __init__, stage, process, _identify_affected_agents, _create_adjustment, _get_active_adjustments, _get_agent_kpi, _persist_adjustment | Bridge 4: Update CARE routing based on new policy. |
| `LoopStatusBridge` | __init__, stage, process, _build_loop_status, _push_sse_update | Bridge 5: Aggregate loop status for console display. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_check_frozen` | `() -> None` | no | Log that frozen mechanics are in use. |
| `create_bridges` | `(db_session_factory, redis_client, config = None) -> list[BaseBridge]` | no | Create all bridges with shared configuration. |
| `register_all_bridges` | `(dispatcher: 'IntegrationDispatcher', db_session_factory, redis_client, config =` | no | Register all bridges with the dispatcher. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `abc` | ABC, abstractmethod | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | TYPE_CHECKING, Optional | no |
| `schemas.audit_schemas` | PolicyActivationAudit | yes |
| `schemas.loop_events` | LOOP_MECHANICS_FROZEN_AT, LOOP_MECHANICS_VERSION, ConfidenceBand, ConfidenceCalculator, LoopEvent (+8) | yes |
| `bridges_driver` | record_policy_activation | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

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

## cost_bridges_engine.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/cost_bridges_engine.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 1147

**Docstring:** M27 Cost Loop Integration Bridges

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AnomalyType` |  | Types of cost anomalies. |
| `AnomalySeverity` |  | Severity levels for cost anomalies. |
| `CostAnomaly` | create, to_dict | Detected cost anomaly from M26 Cost Intelligence. |
| `CostLoopBridge` | __init__, on_anomaly_detected, _map_severity_to_incident_severity | Bridge C1: Cost Anomaly → Incident (MANDATORY GOVERNANCE). |
| `CostPatternMatcher` | __init__, match_cost_pattern, _build_signature, _hash_signature, _deviation_bucket, _find_predefined_match, _calculate_confidence | Bridge C2: Match cost anomalies to failure patterns. |
| `CostRecoveryGenerator` | __init__, generate_recovery | Bridge C3: Generate recovery suggestions for cost anomalies. |
| `CostPolicyGenerator` | __init__, generate_policy | Bridge C4: Generate policies from cost recoveries. |
| `CostRoutingAdjuster` | __init__, on_cost_policy_created, _create_model_routing_adjustment, _create_rate_limit_adjustment, _create_budget_block_adjustment, _create_token_limit_adjustment, _create_throttle_adjustment, _create_notify_adjustment (+2 more) | Bridge C5: Adjust CARE routing based on cost policies. |
| `CostEstimationProbe` | __init__, probe, _calculate_cost, _find_cheaper_model | CARE probe that estimates request cost before execution. |
| `CostLoopOrchestrator` | __init__, process_anomaly | Orchestrates the full M27 cost loop: |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `uuid` | uuid | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |
| `schemas.loop_events` | LoopEvent, LoopStage, PatternMatchResult, PolicyRule, RecoverySuggestion (+2) | yes |
| `app.hoc.cus.general.L4_runtime.engines` | create_incident_from_cost_anomaly_sync | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## cus_health_engine.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/cus_health_engine.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 534

**Docstring:** Customer Health Engine

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CusHealthService` | __init__, check_health, _perform_health_check, check_all_integrations, get_health_summary, _calculate_overall_health | Service for health checking customer LLM integrations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `logging` | logging | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | UUID | no |
| `httpx` | httpx | no |
| `sqlmodel` | Session, select | no |
| `app.db` | get_engine | no |
| `app.models.cus_models` | CusHealthState, CusIntegration | no |
| `app.hoc.cus.general.L5_engines.cus_credential_service` | CusCredentialService | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from sqlmodel import Session, select` | L5 MUST NOT import sqlmodel at runtime | Move DB logic to L6 driver | 60 |
| `from app.db import get_engine` | L5 MUST NOT access DB directly | Use L6 driver for DB access | 62 |
| `from app.models.cus_models import CusHealthState, CusIntegration` | L5 MUST NOT import L7 models directly | Route through L6 driver | 63 |

---

## cus_integration_service.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/cus_integration_service.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 68

**Docstring:** CusIntegrationService (SWEEP-03 Batch 3)

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_cus_integration_service` | `() -> CusIntegrationService` | no | Get the CusIntegrationService instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | TYPE_CHECKING | no |
| `app.services.cus_integration_engine` | CusIntegrationEngine, CusIntegrationService, DeleteResult, EnableResult, HealthCheckResult (+1) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`CusIntegrationService`, `CusIntegrationEngine`, `EnableResult`, `DeleteResult`, `HealthCheckResult`, `get_cus_integration_service`, `get_cus_integration_engine`

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

## dispatcher.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/dispatcher.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 806

**Docstring:** M25 Integration Dispatcher

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DispatcherConfig` | from_env | Configuration for the integration dispatcher. |
| `IntegrationDispatcher` | __init__, register_handler, is_bridge_enabled, dispatch, _check_db_idempotency, _execute_handlers, _check_human_checkpoint_needed, resolve_checkpoint (+14 more) | Central dispatcher for the M25 integration loop. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `asyncio` | asyncio | no |
| `json` | json | no |
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Callable, Coroutine, Optional | no |
| `uuid` | uuid4 | no |
| `schemas.loop_events` | LOOP_MECHANICS_FROZEN_AT, LOOP_MECHANICS_VERSION, ConfidenceBand, HumanCheckpoint, HumanCheckpointType (+5) | yes |
| `schemas.loop_events` | PolicyMode | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## graduation_engine.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/graduation_engine.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 594

**Docstring:** M25 Graduation Engine

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GraduationThresholds` |  | Configurable thresholds for graduation gates. |
| `GateEvidence` |  | Evidence for a single gate - computed from database. |
| `GraduationEvidence` |  | All evidence needed to compute graduation status. |
| `GraduationLevel` |  | Graduation levels - derived from evidence. |
| `ComputedGraduationStatus` | is_graduated, is_degraded, status_label, to_api_response | Graduation status computed from evidence. |
| `GraduationEngine` | __init__, compute, _evaluate_gate1, _evaluate_gate2, _evaluate_gate3, _check_degradation | Computes graduation status from evidence. |
| `CapabilityGates` | can_auto_apply_recovery, can_auto_activate_policy, can_full_auto_routing, get_blocked_capabilities, get_unlocked_capabilities | Capabilities that are LOCKED until graduation passes specific gates. |
| `SimulationState` | is_demo_mode, to_display | Simulation state - SEPARATE from real graduation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | NamedTuple, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## http_connector.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/http_connector.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 367

**Docstring:** Module: http_connector

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `HttpMethod` |  | Allowed HTTP methods. |
| `EndpointConfig` |  | Configuration for a single endpoint. |
| `HttpConnectorConfig` |  | Configuration for HTTP connector. |
| `HttpConnectorError` | __init__ | Error from HTTP connector. |
| `RateLimitExceededError` | __init__ | Rate limit exceeded. |
| `HttpConnectorService` | __init__, id, execute, _resolve_endpoint, _build_url, _get_auth_headers, _check_rate_limit, _record_request | Governed HTTP connector. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `typing` | Any, Dict, List, Optional | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `logging` | logging | no |
| `app.hoc.cus.integrations.L5_engines.credentials` | Credential, CredentialService | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`DEFAULT_MAX_RESPONSE_BYTES`, `DEFAULT_TIMEOUT_SECONDS`, `DEFAULT_RATE_LIMIT_PER_MINUTE`

---

## iam_engine.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/iam_engine.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 440

**Docstring:** IAM Engine (GAP-173)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IdentityProvider` |  | Supported identity providers. |
| `ActorType` |  | Types of actors in the system. |
| `Identity` | has_role, has_permission, has_any_role, has_all_roles, to_dict | Resolved identity from any provider. |
| `AccessDecision` | to_dict | Result of an access control decision. |
| `IAMService` | __init__, _setup_default_roles, resolve_identity, _resolve_clerk_identity, _resolve_api_key_identity, _create_system_identity, _expand_role_permissions, check_access (+7 more) | IAM Service for identity and access management. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional, Set | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## integrations_facade.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/integrations_facade.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 491

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
| `get_integrations_facade` | `() -> IntegrationsFacade` | no | Get the singleton IntegrationsFacade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |
| `app.hoc.cus.integrations.L5_engines.cus_integration_service` | CusIntegrationService | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`IntegrationsFacade`, `get_integrations_facade`, `IntegrationSummaryResult`, `IntegrationListResult`, `IntegrationDetailResult`, `IntegrationLifecycleResult`, `IntegrationDeleteResult`, `HealthCheckResult`, `HealthStatusResult`, `LimitsStatusResult`

---

## mcp_connector.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/mcp_connector.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 423

**Docstring:** Module: mcp_connector

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `McpToolDefinition` |  | Definition of an MCP tool. |
| `McpConnectorConfig` |  | Configuration for MCP connector. |
| `McpConnectorError` | __init__ | Error from MCP connector. |
| `McpApprovalRequiredError` | __init__ | Tool requires manual approval. |
| `McpRateLimitExceededError` | __init__ | Rate limit exceeded. |
| `McpSchemaValidationError` | __init__ | Schema validation failed. |
| `McpConnectorService` | __init__, id, execute, _resolve_tool, _validate_against_schema, _build_mcp_request, _get_api_key, _check_rate_limit (+2 more) | Governed MCP tool invocation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional | no |
| `datetime` | datetime, timezone | no |
| `logging` | logging | no |
| `app.hoc.cus.integrations.L5_engines.credentials` | Credential, CredentialService | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`DEFAULT_MAX_RESPONSE_BYTES`, `DEFAULT_TIMEOUT_SECONDS`, `DEFAULT_RATE_LIMIT_PER_MINUTE`, `DEFAULT_MAX_RETRIES`

---

## prevention_contract.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/prevention_contract.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 201

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
| `types` | Credential | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## sql_gateway.py
**Path:** `backend/app/hoc/cus/integrations/L5_engines/sql_gateway.py`  
**Layer:** L5_engines | **Domain:** integrations | **Lines:** 464

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
| `typing` | Any, Dict, List, Optional | no |
| `datetime` | datetime | no |
| `enum` | Enum | no |
| `logging` | logging | no |
| `app.hoc.cus.integrations.L5_engines.credentials` | Credential, CredentialService | no |
| `asyncio` | asyncio | no |

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
