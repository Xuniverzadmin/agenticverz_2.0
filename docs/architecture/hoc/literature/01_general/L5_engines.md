# General — L5 Engines (36 files)

**Domain:** general  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## alert_log_linker.py
**Path:** `backend/app/hoc/cus/general/L5_engines/alert_log_linker.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 759

**Docstring:** Module: alert_log_linker

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AlertLogLinkType` |  | Type of alert-to-log link. |
| `AlertLogLinkStatus` |  | Status of an alert-log link. |
| `AlertLogLinkError` | __init__, to_dict | Raised when alert-log linking operation fails. |
| `AlertLogLink` | is_valid, record_access, expire, archive, to_dict | Represents a link between an alert and log records. |
| `AlertLogLinkResponse` | to_dict | Response from link operations. |
| `AlertLogLinker` | __init__, _generate_link_id, create_link, get_link, get_links_for_alert, get_links_for_run, get_links_for_tenant, get_links_by_step (+6 more) | Service for managing alert-to-log links. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_alert_log_linker` | `() -> AlertLogLinker` | no | Get or create the alert log linker singleton. |
| `_reset_alert_log_linker` | `() -> None` | no | Reset the alert log linker (for testing). |
| `create_alert_log_link` | `(alert_id: str, run_id: str, tenant_id: str, link_type: AlertLogLinkType, step_i` | no | Quick helper to create an alert-log link. |
| `get_alerts_for_run` | `(run_id: str, link_type: Optional[AlertLogLinkType] = None) -> List[AlertLogLink` | no | Quick helper to get alerts for a run. |
| `get_logs_for_alert` | `(alert_id: str) -> List[AlertLogLink]` | no | Quick helper to get log links for an alert. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional, Set | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## alert_worker.py
**Path:** `backend/app/hoc/cus/general/L5_engines/alert_worker.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 430

**Docstring:** CostSim Alert Worker - Reliable Alert Delivery (L4 Engine)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AlertWorker` | __init__, close, process_batch, run_continuous, get_queue_stats | Background worker for processing alert queue. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `enqueue_alert` | `(payload: List[Dict[str, Any]], alert_type: str, circuit_breaker_name: Optional[` | yes | Enqueue an alert for delivery. |
| `retry_failed_alerts` | `(max_retries: int = 3) -> int` | yes | Retry failed alerts (reset to pending). |
| `purge_old_alerts` | `(days: int = 30, statuses: Optional[List[str]] = None) -> int` | yes | Purge old alerts from queue. |
| `run_alert_worker` | `(use_leader_election: bool = True, process_interval: float = 5.0) -> None` | yes | Run alert worker continuously. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `app.infra` | FeatureIntent, RetryPolicy | no |
| `asyncio` | asyncio | no |
| `logging` | logging | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | TYPE_CHECKING, Any, Dict, List, Optional | no |
| `app.costsim.config` | get_config | no |
| `app.costsim.leader` | LOCK_ALERT_WORKER, leader_election | no |
| `app.costsim.metrics` | get_metrics | no |
| `app.db_async` | AsyncSessionLocal, async_session_context | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.db_async import AsyncSessionLocal, async_session_context` | L5 MUST NOT access DB directly | Use L6 driver for DB access | 99 |

### Constants
`FEATURE_INTENT`, `RETRY_POLICY`

---

## alerts_facade.py
**Path:** `backend/app/hoc/cus/general/L5_engines/alerts_facade.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 679

**Docstring:** Alerts Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AlertSeverity` |  | Alert severity levels. |
| `AlertStatus` |  | Alert status. |
| `AlertRule` | to_dict | Alert rule definition. |
| `AlertEvent` | to_dict | Alert event (history entry). |
| `AlertRoute` | to_dict | Alert routing rule. |
| `AlertsFacade` | __init__, create_rule, list_rules, get_rule, update_rule, delete_rule, list_history, get_event (+7 more) | Facade for alert operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_alerts_facade` | `() -> AlertsFacade` | no | Get the alerts facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## audit_durability.py
**Path:** `backend/app/hoc/cus/general/L5_engines/audit_durability.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 325

**Docstring:** Module: durability

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DurabilityCheckResult` |  | Result of a durability check. |
| `RACDurabilityEnforcementError` | __init__, to_dict | Raised when RAC durability enforcement fails. |
| `DurabilityCheckResponse` | to_dict | Response from a durability check. |
| `RACDurabilityChecker` | __init__, from_governance_config, from_audit_store, is_durable, enforcement_enabled, check, ensure_durable, should_allow_operation | Checks and enforces RAC durability constraints. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_rac_durability` | `(enforcement_enabled: bool = True, durability_mode: str = 'MEMORY') -> Durabilit` | no | Quick helper to check RAC durability. |
| `ensure_rac_durability` | `(operation: str, enforcement_enabled: bool = True, durability_mode: str = 'MEMOR` | no | Quick helper to ensure RAC durability or raise error. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## audit_store.py
**Path:** `backend/app/hoc/cus/general/L5_engines/audit_store.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 448

**Docstring:** Audit Store

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `StoreDurabilityMode` |  | Durability mode for the audit store. |
| `RACDurabilityError` |  | Raised when RAC requires durable storage but none is available. |
| `AuditStore` | __init__, durability_mode, is_durable, add_expectations, get_expectations, update_expectation_status, add_ack, get_acks (+5 more) | Storage for audit expectations and acknowledgments. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_determine_durability_mode` | `(redis_client) -> StoreDurabilityMode` | no | Determine the durability mode based on environment and Redis availability. |
| `get_audit_store` | `(redis_client = None) -> AuditStore` | no | Get the audit store singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `threading` | Lock | no |
| `typing` | Dict, List, Optional | no |
| `uuid` | UUID | no |
| `app.hoc.cus.general.L5_schemas.rac_models` | AuditExpectation, AuditStatus, DomainAck | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`REDIS_TTL_SECONDS`, `AUDIT_REDIS_ENABLED`, `RAC_ENABLED`, `AOS_MODE`

---

## canonical_json.py
**Path:** `backend/app/hoc/cus/general/L5_engines/canonical_json.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 294

**Docstring:** Canonical JSON serialization for AOS.

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `canonical_json` | `(obj: Any, exclude_fields: Optional[Set[str]] = None) -> str` | no | Serialize object to canonical JSON format. |
| `canonical_json_bytes` | `(obj: Any, exclude_fields: Optional[Set[str]] = None) -> bytes` | no | Serialize object to canonical JSON bytes (UTF-8). |
| `content_hash` | `(obj: Any, exclude_fields: Optional[Set[str]] = None, length: int = 16) -> str` | no | Compute deterministic content hash. |
| `content_hash_full` | `(obj: Any, exclude_fields: Optional[Set[str]] = None) -> str` | no | Compute full SHA-256 content hash. |
| `deterministic_hash` | `(obj: Any, length: int = 16) -> str` | no | Compute hash excluding allowed variance fields. |
| `_json_serializer` | `(obj: Any) -> Any` | no | Custom JSON serializer for non-standard types. |
| `_filter_fields` | `(obj: Any, exclude: Set[str]) -> Any` | no | Recursively filter out excluded fields from an object. |
| `is_canonical` | `(json_str: str) -> bool` | no | Check if a JSON string is in canonical format. |
| `canonicalize_file` | `(filepath: str) -> None` | no | Rewrite a JSON file in canonical format. |
| `assert_canonical` | `(filepath: str) -> None` | no | Assert that a JSON file is in canonical format. |
| `compare_deterministic` | `(actual: Dict[str, Any], expected: Dict[str, Any], deterministic_fields: Optiona` | no | Compare two outputs, checking only deterministic fields. |
| `_get_nested` | `(obj: Dict[str, Any], path: str) -> Any` | no | Get nested value using dot notation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `json` | json | no |
| `datetime` | date, datetime | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional, Set | no |
| `uuid` | UUID | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`ALLOWED_VARIANCE_FIELDS`

---

## compliance_facade.py
**Path:** `backend/app/hoc/cus/general/L5_engines/compliance_facade.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 518

**Docstring:** Compliance Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ComplianceScope` |  | Compliance verification scope. |
| `ComplianceStatus` |  | Compliance status. |
| `ComplianceRule` | to_dict | Compliance rule definition. |
| `ComplianceViolation` | to_dict | A compliance violation. |
| `ComplianceReport` | to_dict | Compliance verification report. |
| `ComplianceStatusInfo` | to_dict | Overall compliance status. |
| `ComplianceFacade` | __init__, _init_default_rules, verify_compliance, _check_rule_compliance, list_reports, get_report, list_rules, get_rule (+1 more) | Facade for compliance verification operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_compliance_facade` | `() -> ComplianceFacade` | no | Get the compliance facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## concurrent_runs.py
**Path:** `backend/app/hoc/cus/general/L5_engines/concurrent_runs.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 247

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ConcurrentRunsLimiter` | __init__, _get_client, acquire, release, get_count, slot | Limits concurrent runs using Redis-based semaphore. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_concurrent_limiter` | `() -> ConcurrentRunsLimiter` | no | Get the singleton concurrent runs limiter. |
| `acquire_slot` | `(key: str, max_slots: int)` | no | Convenience context manager for acquiring a slot. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `uuid` | uuid | no |
| `contextlib` | contextmanager | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`REDIS_URL`, `DEFAULT_SLOT_TIMEOUT`

---

## constraint_checker.py
**Path:** `backend/app/hoc/cus/general/L5_engines/constraint_checker.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 309

**Docstring:** Module: constraint_checker

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `InspectionOperation` |  | Operations that require inspection constraint checks. |
| `InspectionConstraintViolation` | to_dict | Record of an inspection constraint violation. |
| `InspectionConstraintChecker` | __init__, from_monitor_config, from_snapshot, is_allowed, check, check_all, get_allowed_operations, get_denied_operations (+1 more) | Enforces inspection constraints from MonitorConfig. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_inspection_allowed` | `(operation: InspectionOperation, allow_prompt_logging: bool = False, allow_respo` | no | Quick helper to check if an operation is allowed. |
| `get_constraint_violations` | `(operations: list[InspectionOperation], allow_prompt_logging: bool = False, allo` | no | Get all constraint violations for a set of operations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## control_registry.py
**Path:** `backend/app/hoc/cus/general/L5_engines/control_registry.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 455

**Docstring:** Module: control_registry

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SOC2Category` |  | SOC2 Trust Service Categories. |
| `SOC2ComplianceStatus` |  | Compliance status for a control mapping. |
| `SOC2Control` | __post_init__ | SOC2 Trust Service Criteria control definition. |
| `SOC2ControlMapping` | to_dict | Mapping of incident/evidence to a SOC2 control. |
| `SOC2ControlRegistry` | __init__, _register_all_controls, _register_incident_response_controls, _register_access_controls, _register_change_management_controls, _register_processing_integrity_controls, _register_availability_controls, _register_communication_controls (+6 more) | Registry of SOC2 Trust Service Criteria controls. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_control_registry` | `() -> SOC2ControlRegistry` | no | Get or create the singleton control registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## cus_credential_service.py
**Path:** `backend/app/hoc/cus/general/L5_engines/cus_credential_service.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 477

**Docstring:** Customer Credential Service

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `CusCredentialService` | __init__, _derive_dev_key, _derive_tenant_key, encrypt_credential, decrypt_credential, resolve_credential, _resolve_vault_credential, _resolve_env_credential (+4 more) | Service for managing customer LLM credentials. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `base64` | base64 | no |
| `hashlib` | hashlib | no |
| `hmac` | hmac | no |
| `logging` | logging | no |
| `os` | os | no |
| `secrets` | secrets | no |
| `typing` | Dict, Optional, Tuple | no |
| `cryptography.hazmat.primitives.ciphers.aead` | AESGCM | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## cus_health_shim.py
**Path:** `backend/app/hoc/cus/general/L5_engines/cus_health_shim.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 66

**Docstring:** DEPRECATED: Customer Health Service

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `warnings` | warnings | no |
| `app.hoc.cus.general.L6_drivers.cus_health_driver` | CusHealthDriver, CusHealthService | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`CusHealthService`, `CusHealthDriver`

---

## dag_sorter.py
**Path:** `backend/app/hoc/cus/general/L5_engines/dag_sorter.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 318

**Docstring:** DAG-based execution ordering for PLang v2.0.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ExecutionPhase` |  | Execution phases in deterministic order. |
| `ExecutionNode` | __hash__, __eq__ | A node in the execution DAG. |
| `ExecutionDAG` | add_node, add_edge, get_roots, get_leaves | Directed Acyclic Graph of policy execution. |
| `ExecutionPlan` | to_dict | A deterministic execution plan. |
| `DAGSorter` | __init__, build_dag, _get_phase, _add_category_dependencies, _add_routing_dependencies, sort, get_execution_order, visualize | Sorts policies into deterministic execution order. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `enum` | Enum, auto | no |
| `typing` | Any, Dict, List, Optional, Set (+1) | no |
| `app.policy.compiler.grammar` | PolicyCategory | no |
| `app.policy.ir.ir_nodes` | IRFunction, IRGovernance, IRModule | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## db_helpers.py
**Path:** `backend/app/hoc/cus/general/L5_engines/db_helpers.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 437

**Docstring:** Database helper functions for SQLModel row extraction.

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `scalar_or_default` | `(row: Optional[Any], default: Any = 0) -> Any` | no | Extract scalar value from Row or return default. |
| `scalar_or_none` | `(row: Optional[Any]) -> Optional[Any]` | no | Extract scalar value from Row, returning None if unavailable. |
| `extract_model` | `(row: Any, model_attr: str = 'id') -> Any` | no | Extract model instance from Row or return as-is. |
| `extract_models` | `(results: List[Any], model_attr: str = 'id') -> List[Any]` | no | Extract model instances from a list of results. |
| `count_or_zero` | `(row: Optional[Any]) -> int` | no | Extract count value, guaranteed to return int. |
| `sum_or_zero` | `(row: Optional[Any]) -> float` | no | Extract sum value, guaranteed to return numeric. |
| `query_one` | `(session: Any, statement: Any, model_class: Optional[type] = None) -> Optional[A` | no | Safe single-row query with automatic Row/Model detection. |
| `query_all` | `(session: Any, statement: Any, model_class: Optional[type] = None) -> list` | no | Safe multi-row query with automatic Row/Model detection. |
| `model_to_dict` | `(model: Any, include: Optional[list] = None, exclude: Optional[list] = None) -> ` | no | Convert ORM model to dict to prevent DetachedInstanceError. |
| `models_to_dicts` | `(models: list, include: Optional[list] = None, exclude: Optional[list] = None) -` | no | Convert list of ORM models to list of dicts. |
| `safe_get` | `(session: Any, model_class: type, id: Any, to_dict: bool = False, include: Optio` | no | Safe session.get() wrapper with optional dict conversion. |
| `get_or_create` | `(session: Any, model_class: type, defaults: Optional[dict] = None, **kwargs) -> ` | no | Get existing model or create new one. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, List, Optional, TypeVar | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`T`

---

## deterministic.py
**Path:** `backend/app/hoc/cus/general/L5_engines/deterministic.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 143

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `seeded_jitter` | `(workflow_run_id: str, attempt: int) -> float` | no | Generate deterministic jitter value from workflow ID and attempt number. |
| `deterministic_backoff_ms` | `(workflow_run_id: str, attempt: int, initial_ms: int = 200, multiplier: float = ` | no | Calculate exponential backoff with deterministic jitter. |
| `deterministic_timestamp` | `(workflow_run_id: str, step_index: int, base_time: Optional[float] = None) -> in` | no | Generate a deterministic timestamp for replay scenarios. |
| `generate_idempotency_key` | `(workflow_run_id: str, skill_name: str, step_index: int) -> str` | no | Generate a deterministic idempotency key for a skill execution. |
| `hash_params` | `(params: dict) -> str` | no | Generate a hash of skill parameters for idempotency comparison. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `hmac` | hmac | no |
| `struct` | struct | no |
| `time` | time | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## fatigue_controller.py
**Path:** `backend/app/hoc/cus/general/L5_engines/fatigue_controller.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 749

**Docstring:** AlertFatigueController - Alert fatigue management service.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AlertFatigueMode` |  | Operating modes for fatigue control. |
| `AlertFatigueAction` |  | Actions taken by the fatigue controller. |
| `AlertFatigueConfig` | to_dict | Configuration for alert fatigue thresholds. |
| `AlertFatigueState` | record_alert, reset_window, start_suppression, end_suppression, start_cooldown, end_cooldown, add_to_aggregation, flush_aggregation (+4 more) | State tracking for an alert source. |
| `AlertFatigueStats` | update_rates, to_dict | Statistics from fatigue controller. |
| `AlertFatigueError` | __init__, to_dict | Exception for fatigue controller errors. |
| `FatigueCheckResult` | to_dict | Result of a fatigue check. |
| `AlertFatigueController` | __init__, _get_state_key, _generate_source_id, configure_tenant, get_config, get_or_create_state, get_state, check_alert (+6 more) | Controller for managing alert fatigue. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_alert_fatigue_controller` | `() -> AlertFatigueController` | no | Get the singleton controller instance. |
| `_reset_controller` | `() -> None` | no | Reset the singleton (for testing). |
| `check_alert_fatigue` | `(tenant_id: str, alert_type: str, source_id: Optional[str] = None, source_data: ` | no | Check if an alert should be allowed or suppressed. |
| `suppress_alert` | `(tenant_id: str, source_id: str, alert_type: str, duration_seconds: Optional[int` | no | Manually suppress an alert source. |
| `get_fatigue_stats` | `(tenant_id: Optional[str] = None) -> AlertFatigueStats` | no | Get fatigue statistics. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |
| `hashlib` | hashlib | no |
| `json` | json | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## guard.py
**Path:** `backend/app/hoc/cus/general/L5_engines/guard.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 622

**Docstring:** Guard Console Data Contracts - Customer-Facing API

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GuardStatusDTO` |  | GET /guard/status response. |
| `TodaySnapshotDTO` |  | GET /guard/snapshot/today response. |
| `IncidentSummaryDTO` |  | Incident list item. |
| `IncidentEventDTO` |  | Timeline event within an incident. |
| `IncidentDetailDTO` |  | GET /guard/incidents/{id} response. |
| `IncidentListDTO` |  | GET /guard/incidents response (paginated). |
| `CustomerIncidentImpactDTO` |  | Impact assessment for customers - calm, explicit. |
| `CustomerIncidentResolutionDTO` |  | Resolution status for customers - reassuring. |
| `CustomerIncidentActionDTO` |  | Customer action item - only if necessary. |
| `CustomerIncidentNarrativeDTO` |  | GET /guard/incidents/{id} enhanced response. |
| `ApiKeyDTO` |  | API key response (masked). |
| `ApiKeyListDTO` |  | GET /guard/keys response. |
| `GuardrailConfigDTO` |  | Individual guardrail configuration. |
| `TenantSettingsDTO` |  | GET /guard/settings response. |
| `ReplayCallSnapshotDTO` |  | Original call context for replay. |
| `ReplayCertificateDTO` |  | Cryptographic proof of replay (M23). |
| `ReplayResultDTO` |  | POST /guard/replay/{call_id} response. |
| `KillSwitchActionDTO` |  | POST /guard/killswitch/activate and /deactivate response. |
| `OnboardingVerifyResponseDTO` |  | POST /guard/onboarding/verify response. |
| `CustomerCostSummaryDTO` |  | GET /guard/costs/summary response. |
| `CostBreakdownItemDTO` |  | Individual cost breakdown item. |
| `CustomerCostExplainedDTO` |  | GET /guard/costs/explained response. |
| `CustomerCostIncidentDTO` |  | Cost-related incident visible to customer. |
| `CustomerCostIncidentListDTO` |  | GET /guard/costs/incidents response. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List, Literal, Optional | no |
| `pydantic` | BaseModel, Field | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## input_sanitizer.py
**Path:** `backend/app/hoc/cus/general/L5_engines/input_sanitizer.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 260

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SanitizationResult` | __post_init__ | Result of input sanitization. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `detect_injection_patterns` | `(text: str) -> List[tuple]` | no | Detect prompt injection patterns in text. |
| `extract_urls` | `(text: str) -> List[str]` | no | Extract all URLs from text. |
| `is_url_safe` | `(url: str) -> tuple[bool, Optional[str]]` | no | Check if a URL is safe (not targeting internal resources). |
| `sanitize_goal` | `(goal: str) -> SanitizationResult` | no | Sanitize a goal string before processing. |
| `validate_goal` | `(goal: str) -> tuple[bool, Optional[str], List[str]]` | no | Convenience function to validate a goal. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `re` | re | no |
| `dataclasses` | dataclass | no |
| `typing` | List, Optional, Set | no |
| `urllib.parse` | urlparse | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`MAX_GOAL_LENGTH`, `ENABLE_INJECTION_DETECTION`, `ENABLE_URL_SANITIZATION`, `INJECTION_PATTERNS`

---

## knowledge_lifecycle_manager.py
**Path:** `backend/app/hoc/cus/general/L5_engines/knowledge_lifecycle_manager.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 921

**Docstring:** GAP-086: Knowledge Lifecycle Manager

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GateDecision` |  | Policy gate decision. |
| `GateResult` | __bool__, allowed, blocked, pending | Result of a policy gate check. |
| `LifecycleAuditEventType` |  | Types of lifecycle audit events. |
| `LifecycleAuditEvent` | to_dict | Audit event for lifecycle transitions (GAP-088). |
| `KnowledgePlaneLifecycle` | record_state_change | In-memory representation of a knowledge plane lifecycle. |
| `TransitionRequest` |  | Request to transition a knowledge plane to a new state. |
| `TransitionResponse` | to_dict | Response from a transition attempt. |
| `KnowledgeLifecycleManager` | __init__, handle_transition, _handle_register, get_state, get_plane, get_history, get_audit_log, get_next_action (+14 more) | GAP-086: Knowledge Lifecycle Manager — THE ORCHESTRATOR. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `generate_id` | `(prefix: str = 'kp') -> str` | no | Generate a unique ID with prefix. |
| `get_knowledge_lifecycle_manager` | `() -> KnowledgeLifecycleManager` | no | Get the singleton KnowledgeLifecycleManager instance. |
| `reset_manager` | `() -> None` | no | Reset the singleton instance (for testing). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Callable, Dict, List, Optional | no |
| `uuid` | uuid4 | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |
| `app.models.knowledge_lifecycle` | KnowledgePlaneLifecycleState, LifecycleAction, TransitionResult, is_valid_transition, validate_transition (+4) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState, LifecycleAction, TransitionResult, is_valid_transition, validate_transition, get_action_for_transition, get_transition_for_action, get_next_onboarding_state, get_next_offboarding_state` | L5 MUST NOT import L7 models directly | Route through L6 driver | 54 |

### __all__ Exports
`KnowledgeLifecycleManager`, `KnowledgePlaneLifecycle`, `TransitionRequest`, `TransitionResponse`, `GateDecision`, `GateResult`, `LifecycleAuditEventType`, `LifecycleAuditEvent`, `get_knowledge_lifecycle_manager`, `reset_manager`

---

## knowledge_sdk.py
**Path:** `backend/app/hoc/cus/general/L5_engines/knowledge_sdk.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 983

**Docstring:** GAP-083-085: Knowledge SDK Façade

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `KnowledgePlaneConfig` |  | Configuration for creating a knowledge plane. |
| `WaitOptions` |  | Options for wait operations. |
| `SDKResult` | from_transition_response, error, to_dict | Structured result from SDK operations. |
| `PlaneInfo` | from_plane, to_dict | Information about a knowledge plane for SDK consumers. |
| `KnowledgeSDK` | __init__, register, verify, ingest, index, classify, request_activation, activate (+16 more) | GAP-083-085: Knowledge SDK Façade. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_knowledge_sdk` | `(tenant_id: str, actor_id: Optional[str] = None) -> KnowledgeSDK` | no | Create a KnowledgeSDK instance for a tenant. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `time` | time | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.models.knowledge_lifecycle` | KnowledgePlaneLifecycleState, LifecycleAction | no |
| `app.hoc.cus.general.L5_engines.knowledge_lifecycle_manager` | KnowledgeLifecycleManager, KnowledgePlaneLifecycle, TransitionRequest, TransitionResponse, GateDecision (+1) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState, LifecycleAction` | L5 MUST NOT import L7 models directly | Route through L6 driver | 58 |

### __all__ Exports
`KnowledgeSDK`, `KnowledgePlaneConfig`, `WaitOptions`, `SDKResult`, `PlaneInfo`, `create_knowledge_sdk`

---

## lifecycle_facade.py
**Path:** `backend/app/hoc/cus/general/L5_engines/lifecycle_facade.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 709

**Docstring:** Lifecycle Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AgentState` |  | Agent lifecycle states. |
| `RunState` |  | Run lifecycle states. |
| `AgentLifecycle` | to_dict | Agent lifecycle information. |
| `RunLifecycle` | to_dict | Run lifecycle information. |
| `LifecycleSummary` | to_dict | Summary of lifecycle entities. |
| `LifecycleFacade` | __init__, create_agent, list_agents, get_agent, start_agent, stop_agent, terminate_agent, create_run (+6 more) | Facade for lifecycle operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_lifecycle_facade` | `() -> LifecycleFacade` | no | Get the lifecycle facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## lifecycle_stages_base.py
**Path:** `backend/app/hoc/cus/general/L5_engines/lifecycle_stages_base.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 317

**Docstring:** Stage Handler Protocol and Base Types

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `StageStatus` |  | Result status from stage execution. |
| `StageContext` |  | Context passed to stage handlers. |
| `StageResult` | success, is_async, ok, fail, pending, skipped | Result returned by stage handlers. |
| `StageHandler` | stage_name, handles_states, execute, validate | Protocol for stage handlers. |
| `BaseStageHandler` | stage_name, handles_states, validate, execute | Base class for stage handlers. |
| `StageRegistry` | __init__, register, get_handler, has_handler, create_default | Registry of stage handlers. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `abc` | ABC, abstractmethod | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, Optional, Protocol, Type (+1) | no |
| `app.models.knowledge_lifecycle` | KnowledgePlaneLifecycleState | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState` | L5 MUST NOT import L7 models directly | Route through L6 driver | 44 |

---

## manager.py
**Path:** `backend/app/hoc/cus/general/L5_engines/manager.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 394

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `EnvelopeApplication` |  | Record of an active envelope application. |
| `EnvelopeManager` | __init__, active_envelope_count, can_apply, apply, revert, revert_all, _on_killswitch_activated, get_active_envelopes (+2 more) | Manages the lifecycle of optimization envelopes. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_envelope_manager` | `() -> EnvelopeManager` | no | Get the global envelope manager instance. |
| `reset_manager_for_testing` | `() -> None` | no | Reset envelope manager. FOR TESTING ONLY. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `threading` | threading | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Callable, Dict, List, Optional | no |
| `app.optimization.envelope` | Envelope, EnvelopeAuditRecord, EnvelopeLifecycle, EnvelopeValidationError, RevertReason (+3) | no |
| `app.optimization.killswitch` | KillSwitch, KillSwitchEvent, RollbackStatus, get_killswitch | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## metrics_helpers.py
**Path:** `backend/app/hoc/cus/general/L5_engines/metrics_helpers.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 210

**Docstring:** Prometheus Metrics Helpers - Idempotent Registration

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_find_existing_metric` | `(name: str)` | no | Find an existing metric in the registry by name. |
| `get_or_create_counter` | `(name: str, documentation: str, labelnames: Optional[List[str]] = None) -> Count` | no | Get existing counter or create new one - idempotent. |
| `get_or_create_gauge` | `(name: str, documentation: str, labelnames: Optional[List[str]] = None) -> Gauge` | no | Get existing gauge or create new one - idempotent. |
| `get_or_create_histogram` | `(name: str, documentation: str, labelnames: Optional[List[str]] = None, buckets:` | no | Get existing histogram or create new one - idempotent. |
| `validate_metric_name` | `(name: str) -> bool` | no | Validate metric name follows conventions. |
| `reset_metrics_registry` | `()` | no | Reset the Prometheus registry for test isolation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | List, Optional | no |
| `prometheus_client` | REGISTRY, Counter, Gauge, Histogram | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`VALID_SUFFIXES`

---

## monitors_facade.py
**Path:** `backend/app/hoc/cus/general/L5_engines/monitors_facade.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 541

**Docstring:** Monitors Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `MonitorType` |  | Types of monitors. |
| `MonitorStatus` |  | Monitor status. |
| `CheckStatus` |  | Health check result status. |
| `MonitorConfig` | to_dict | Monitor configuration. |
| `HealthCheckResult` | to_dict | Health check result. |
| `MonitorStatusSummary` | to_dict | Overall monitoring status summary. |
| `MonitorsFacade` | __init__, create_monitor, list_monitors, get_monitor, update_monitor, delete_monitor, run_check, get_check_history (+1 more) | Facade for monitor operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_monitors_facade` | `() -> MonitorsFacade` | no | Get the monitors facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## panel_invariant_monitor.py
**Path:** `backend/app/hoc/cus/general/L5_engines/panel_invariant_monitor.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 456

**Docstring:** Panel Invariant Monitor

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AlertType` |  | Panel invariant alert types. |
| `AlertSeverity` |  | Alert severity levels. |
| `PanelInvariant` |  | A panel's invariant definition. |
| `PanelStatus` |  | Current status of a panel. |
| `PanelAlert` | to_dict | An alert for a panel invariant violation. |
| `PanelInvariantRegistry` | __init__, _default_registry_path, _load_registry, get_invariant, get_all_invariants, get_alertable_invariants | Registry of panel invariants. |
| `PanelInvariantMonitor` | __init__, check_panel, report_filter_break, _create_empty_panel_alert, get_panel_status, get_all_statuses, get_unhealthy_panels, get_recent_alerts (+1 more) | Monitors panel invariants and detects silent governance failures. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_panel_monitor` | `() -> PanelInvariantMonitor` | no | Get the singleton panel invariant monitor. |
| `reset_panel_monitor` | `() -> None` | no | Reset the monitor (for testing). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `enum` | Enum | no |
| `pathlib` | Path | no |
| `typing` | Any, Optional | no |
| `yaml` | yaml | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## panel_slot_evaluator.py
**Path:** `backend/app/hoc/cus/general/L5_engines/panel_slot_evaluator.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 248

**Docstring:** Panel Slot Evaluator — Execute slot evaluation logic

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PanelSlotEvaluator` | __init__, evaluate, evaluate_missing, _compute_outputs, _map_signal, _get_nested, _compute_system_state, _compute_attention_required (+2 more) | Evaluates individual panel slots. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Callable, Dict, Optional | no |
| `panel_types` | Authority, NegativeAuthorityValue, PanelSlotResult, SlotProvenance, SlotSpec (+4) | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## panel_verification_engine.py
**Path:** `backend/app/hoc/cus/general/L5_engines/panel_verification_engine.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 220

**Docstring:** Panel Verification Engine — Determinism enforcement

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PanelVerificationEngine` | verify_inputs, check_contradictions, determine_state, determine_authority, _check_negative_authority, enforce_determinism, check_determinism_rule | Verifies inputs and enforces determinism rules. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `typing` | Any, Dict, List, Optional, Tuple | no |
| `panel_types` | Authority, DeterminismRule, NegativeAuthorityValue, SlotState, VerificationSignals | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## plan_inspector.py
**Path:** `backend/app/hoc/cus/general/L5_engines/plan_inspector.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 312

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PlanValidationError` |  | A single validation error. |
| `PlanValidationResult` | add_error, add_warning | Result of plan validation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `extract_urls_from_params` | `(params: Dict[str, Any]) -> List[str]` | no | Extract all URLs from skill parameters. |
| `is_domain_forbidden` | `(url: str) -> tuple[bool, str]` | no | Check if a URL targets a forbidden domain. |
| `validate_step` | `(step: Dict[str, Any], result: PlanValidationResult)` | no | Validate a single plan step. |
| `validate_plan` | `(plan: Dict[str, Any], agent_budget_cents: int = 0) -> PlanValidationResult` | no | Validate a complete plan before execution. |
| `inspect_plan` | `(plan: Dict[str, Any], agent_budget_cents: int = 0) -> Dict[str, Any]` | no | Inspect a plan and return validation results. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass, field | no |
| `typing` | Any, Dict, List, Optional, Set | no |
| `urllib.parse` | urlparse | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`MAX_PLAN_STEPS`, `MAX_LOOP_ITERATIONS`, `MAX_ESTIMATED_COST_CENTS`

---

## profile_policy_mode.py
**Path:** `backend/app/hoc/cus/general/L5_engines/profile_policy_mode.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 459

**Docstring:** Governance Profile Configuration

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GovernanceProfile` |  | Pre-defined governance profiles. |
| `GovernanceConfig` | to_dict | Complete governance configuration derived from profile + overrides. |
| `GovernanceConfigError` | __init__ | Raised when governance configuration is invalid. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_get_bool_env` | `(name: str, default: bool) -> bool` | no | Get boolean from environment variable. |
| `get_governance_profile` | `() -> GovernanceProfile` | no | Get the current governance profile from environment. |
| `load_governance_config` | `() -> GovernanceConfig` | no | Load complete governance configuration. |
| `validate_governance_config` | `(config: Optional[GovernanceConfig] = None) -> List[str]` | no | Validate governance configuration for invalid combinations. |
| `get_governance_config` | `() -> GovernanceConfig` | no | Get the validated governance configuration singleton. |
| `reset_governance_config` | `() -> None` | no | Reset the singleton (for testing). |
| `validate_governance_at_startup` | `() -> None` | no | Validate governance configuration at application startup. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Dict, FrozenSet, List, Optional, Tuple | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## rate_limiter.py
**Path:** `backend/app/hoc/cus/general/L5_engines/rate_limiter.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 184

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RateLimiter` | __init__, _get_client, allow, get_remaining | Token bucket rate limiter using Redis. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_rate_limiter` | `() -> RateLimiter` | no | Get the singleton rate limiter instance. |
| `allow_request` | `(key: str, rate_per_min: int) -> bool` | no | Convenience function to check rate limit. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `time` | time | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`REDIS_URL`, `TOKEN_BUCKET_LUA`

---

## retrieval_facade.py
**Path:** `backend/app/hoc/cus/general/L5_engines/retrieval_facade.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 518

**Docstring:** Retrieval Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AccessResult` | to_dict | Result of a mediated data access. |
| `PlaneInfo` | to_dict | Information about a knowledge plane. |
| `EvidenceInfo` | to_dict | Evidence record information. |
| `RetrievalFacade` | __init__, mediator, access_data, list_planes, register_plane, get_plane, list_evidence, get_evidence (+1 more) | Facade for mediated data retrieval operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_retrieval_facade` | `() -> RetrievalFacade` | no | Get the retrieval facade instance. |

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

## retrieval_mediator.py
**Path:** `backend/app/hoc/cus/general/L5_engines/retrieval_mediator.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 471

**Docstring:** Module: retrieval_mediator

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `MediationAction` |  | Allowed mediation actions. |
| `MediatedResult` |  | Result of a mediated data access. |
| `PolicyCheckResult` |  | Result of policy check. |
| `EvidenceRecord` |  | Evidence record for a mediated access. |
| `MediationDeniedError` | __init__ | Raised when mediation denies access. |
| `Connector` | execute | Protocol for connectors. |
| `ConnectorRegistry` | resolve | Protocol for connector registry. |
| `PolicyChecker` | check_access | Protocol for policy checking. |
| `EvidenceService` | record | Protocol for evidence recording. |
| `RetrievalMediator` | __init__, access, _check_policy, _resolve_connector, _record_evidence, _hash_payload | Unified mediation layer for all external data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_retrieval_mediator` | `() -> RetrievalMediator` | no | Get or create the singleton RetrievalMediator. |
| `configure_retrieval_mediator` | `(policy_checker: Optional[PolicyChecker] = None, connector_registry: Optional[Co` | no | Configure the singleton RetrievalMediator with dependencies. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional, Protocol (+1) | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## runtime.py
**Path:** `backend/app/hoc/cus/general/L5_engines/runtime.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 68

**Docstring:** Runtime Utilities - Centralized Shared Helpers

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `generate_uuid` | `() -> str` | no | Generate a UUID string. |
| `utc_now` | `() -> datetime` | no | Return timezone-aware UTC datetime. |
| `utc_now_naive` | `() -> datetime` | no | Return timezone-naive UTC datetime (for asyncpg raw SQL compatibility). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `uuid` | uuid4 | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## scheduler_facade.py
**Path:** `backend/app/hoc/cus/general/L5_engines/scheduler_facade.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 552

**Docstring:** Scheduler Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `JobStatus` |  | Job status. |
| `JobRunStatus` |  | Job run status. |
| `ScheduledJob` | to_dict | Scheduled job definition. |
| `JobRun` | to_dict | Job run history entry. |
| `SchedulerFacade` | __init__, create_job, list_jobs, get_job, update_job, delete_job, trigger_job, pause_job (+4 more) | Facade for scheduled job operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_scheduler_facade` | `() -> SchedulerFacade` | no | Get the scheduler facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## webhook_verify.py
**Path:** `backend/app/hoc/cus/general/L5_engines/webhook_verify.py`  
**Layer:** L5_engines | **Domain:** general | **Lines:** 294

**Docstring:** Webhook Signature Verification Utility

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `WebhookVerifier` | __init__, _parse_grace_env, _get_key, _compute_signature, verify, sign | Webhook signature verifier with key version support. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_file_key_loader` | `(keys_path: str) -> Callable[[str], Optional[str]]` | no | Create a key loader that reads from files. |
| `create_vault_key_loader` | `(mount_path: str = 'secret', secret_path: str = 'webhook/keys') -> Callable[[str` | no | Create a key loader that reads from Vault. |
| `verify_webhook` | `(body: bytes, signature: str, key_version: Optional[str], keys: Dict[str, str], ` | no | Quick verification without creating a WebhookVerifier instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `hmac` | hmac | no |
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Callable, Dict, List, Optional, Union | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---
