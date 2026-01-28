# General — L5 Other (13 files)

**Domain:** general  
**Layer:** L5_other  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## contract_engine.py
**Path:** `backend/app/hoc/cus/general/L5_workflow/contracts/engines/contract_engine.py`  
**Layer:** L5_other | **Domain:** general | **Lines:** 718

**Docstring:** Part-2 Contract Service (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ContractState` |  | In-memory representation of contract state. |
| `ContractStateMachine` | can_transition, validate_transition, transition | State machine for System Contract lifecycle. |
| `ContractService` | __init__, version, create_contract, approve, reject, activate, complete, fail (+5 more) | Part-2 Contract Service (L4) |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta, timezone | no |
| `decimal` | Decimal | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID, uuid4 | no |
| `app.models.contract` | TERMINAL_STATES, VALID_TRANSITIONS, AuditVerdict, ContractApproval, ContractImmutableError (+8) | no |
| `app.hoc.cus.policies.L5_engines.eligibility_engine` | EligibilityDecision, EligibilityVerdict | no |
| `app.hoc.cus.account.L5_support.CRM.engines.crm_validator_engine` | ValidatorVerdict | no |

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.contract import TERMINAL_STATES, VALID_TRANSITIONS, AuditVerdict, ContractApproval, ContractImmutableError, ContractSource, ContractStatus, EligibilityVerdictData, InvalidTransitionError, MayNotVerdictError, RiskLevel, TransitionRecord, ValidatorVerdictData` | L5 MUST NOT import L7 models directly | Route through L6 driver | 82 |

### Constants
`CONTRACT_SERVICE_VERSION`

---

## degraded_mode_checker.py
**Path:** `backend/app/hoc/cus/general/L5_controls/engines/degraded_mode_checker.py`  
**Layer:** L5_other | **Domain:** general | **Lines:** 675

**Docstring:** Module: degraded_mode_checker

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DegradedModeCheckResult` |  | Result of a degraded mode check. |
| `DegradedModeState` |  | Possible degraded mode states. |
| `GovernanceDegradedModeError` | __init__, to_dict | Raised when governance degraded mode blocks an operation. |
| `DegradedModeStatus` | to_dict | Current degraded mode status. |
| `DegradedModeCheckResponse` | to_dict | Response from a degraded mode check. |
| `DegradedModeIncident` |  | Incident data for degraded mode transition. |
| `DegradedModeIncidentCreator` | __init__, create_degraded_incident, create_recovery_incident | Creates incidents for degraded mode transitions. |
| `GovernanceDegradedModeChecker` | __init__, from_governance_config, check_enabled, get_current_status, check, ensure_not_degraded, enter_degraded, exit_degraded (+2 more) | Checks and manages governance degraded mode. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_degraded_mode` | `(check_enabled: bool = True) -> DegradedModeCheckResponse` | no | Quick helper to check degraded mode. |
| `ensure_not_degraded` | `(operation: str, check_enabled: bool = True) -> None` | no | Quick helper to ensure not in degraded mode or raise error. |
| `enter_degraded_with_incident` | `(state: DegradedModeState, reason: str, entered_by: str, new_runs_action: str = ` | no | Quick helper to enter degraded mode with incident. |
| `_reset_degraded_mode_state` | `() -> None` | no | Reset global state (for testing only). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `threading` | Lock | no |
| `typing` | Any, Dict, FrozenSet, Optional | no |
| `logging` | logging | no |

---

## execution.py
**Path:** `backend/app/hoc/cus/general/L5_lifecycle/drivers/execution.py`  
**Layer:** L5_other | **Domain:** general | **Lines:** 1322

**Docstring:** Module: execution

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IngestionSourceType` |  | Types of data sources for ingestion. |
| `IngestionBatch` | __post_init__ | A batch of ingested records. |
| `IngestionResult` | to_dict | Result of data ingestion operation. |
| `DataIngestionExecutor` | __init__, execute, _get_connector, _ingest_from_http, _ingest_from_sql, _ingest_from_file, _ingest_from_vector, _simulate_ingestion | Real data ingestion executor (GAP-159). |
| `IndexingResult` | to_dict | Result of indexing operation. |
| `IndexingExecutor` | __init__, execute, _get_vector_connector, _extract_documents, _chunk_documents, _generate_embeddings, _simulate_embedding, _call_embedding_api | Real indexing executor (GAP-160). |
| `SensitivityLevel` |  | Data sensitivity levels. |
| `PIIType` |  | Types of PII detected. |
| `PIIDetection` |  | A detected PII instance. |
| `ClassificationResult` | to_dict | Result of classification operation. |
| `ClassificationExecutor` | __init__, execute, _sample_records, _detect_pii, _redact, _detect_categories, _determine_sensitivity | Real classification executor (GAP-161). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_ingestion_executor` | `() -> DataIngestionExecutor` | no | Get or create the singleton DataIngestionExecutor. |
| `get_indexing_executor` | `() -> IndexingExecutor` | no | Get or create the singleton IndexingExecutor. |
| `get_classification_executor` | `() -> ClassificationExecutor` | no | Get or create the singleton ClassificationExecutor. |
| `reset_executors` | `() -> None` | no | Reset all singletons (for testing). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `re` | re | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, Iterator, List, Optional (+1) | no |

---

## guard_write_driver.py
**Path:** `backend/app/hoc/cus/general/L5_controls/drivers/guard_write_driver.py`  
**Layer:** L5_other | **Domain:** general | **Lines:** 267

**Docstring:** Guard Write Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GuardWriteDriver` | __init__, get_or_create_killswitch_state, freeze_killswitch, unfreeze_killswitch, acknowledge_incident, resolve_incident, create_demo_incident | L6 driver for guard write operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_guard_write_driver` | `(session: Session) -> GuardWriteDriver` | no | Factory function to get GuardWriteDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `decimal` | Decimal | no |
| `typing` | List, Optional, Tuple | no |
| `sqlalchemy` | and_, select | no |
| `sqlmodel` | Session | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |
| `app.models.killswitch` | Incident, IncidentEvent, IncidentSeverity, IncidentStatus, KillSwitchState (+1) | no |

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from sqlalchemy import and_, select` | L5 MUST NOT import sqlalchemy | Move DB logic to L6 driver | 51 |
| `from sqlmodel import Session` | L5 MUST NOT import sqlmodel at runtime | Move DB logic to L6 driver | 52 |
| `from app.models.killswitch import Incident, IncidentEvent, IncidentSeverity, IncidentStatus, KillSwitchState, TriggerType` | L5 MUST NOT import L7 models directly | Route through L6 driver | 55 |

### __all__ Exports
`GuardWriteDriver`, `get_guard_write_driver`

---

## guard_write_engine.py
**Path:** `backend/app/hoc/cus/general/L5_controls/engines/guard_write_engine.py`  
**Layer:** L5_other | **Domain:** general | **Lines:** 154

**Docstring:** Guard Write Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GuardWriteService` | __init__, get_or_create_killswitch_state, freeze_killswitch, unfreeze_killswitch, acknowledge_incident, resolve_incident, create_demo_incident | DB write operations for Guard Console. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `decimal` | Decimal | no |
| `typing` | TYPE_CHECKING, List, Optional, Tuple | no |
| `app.hoc.cus.general.L5_controls.drivers.guard_write_driver` | GuardWriteDriver, get_guard_write_driver | no |

---

## job_executor.py
**Path:** `backend/app/hoc/cus/general/L5_support/CRM/engines/job_executor.py`  
**Layer:** L5_other | **Domain:** general | **Lines:** 520

**Docstring:** Part-2 Job Executor (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `HealthObserver` | observe_health | Protocol for observing health state (read-only). |
| `StepHandler` | execute | Protocol for step type handlers. |
| `StepOutput` |  | Output from executing a single step. |
| `ExecutionContext` |  | Context passed to step handlers during execution. |
| `ExecutionResult` |  | Result of executing a job. |
| `JobExecutor` | __init__, version, register_handler, execute_job, _execute_step | Part-2 Job Executor (L5) |
| `NoOpHandler` | execute | No-op handler for testing. |
| `FailingHandler` | __init__, execute | Failing handler for testing. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_default_executor` | `() -> JobExecutor` | no | Create a JobExecutor with default handlers. |
| `execution_result_to_evidence` | `(result: ExecutionResult) -> dict[str, Any]` | no | Convert ExecutionResult to audit evidence format. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Optional, Protocol | no |
| `uuid` | UUID | no |
| `app.models.governance_job` | JobStatus, JobStep, StepResult, StepStatus | no |

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.governance_job import JobStatus, JobStep, StepResult, StepStatus` | L5 MUST NOT import L7 models directly | Route through L6 driver | 63 |

### Constants
`EXECUTOR_VERSION`

---

## knowledge_plane.py
**Path:** `backend/app/hoc/cus/general/L5_lifecycle/drivers/knowledge_plane.py`  
**Layer:** L5_other | **Domain:** general | **Lines:** 482

**Docstring:** KnowledgePlane - Knowledge plane models and registry.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `KnowledgePlaneStatus` |  | Status of a knowledge plane. |
| `KnowledgeNodeType` |  | Types of knowledge nodes. |
| `KnowledgeNode` | add_child, add_related, to_dict | A node in the knowledge graph. |
| `KnowledgePlane` | add_node, get_node, remove_node, add_source, remove_source, activate, deactivate, start_indexing (+4 more) | Representation of a knowledge plane. |
| `KnowledgePlaneError` | __init__, to_dict | Exception for knowledge plane errors. |
| `KnowledgePlaneStats` | to_dict | Statistics for knowledge planes. |
| `KnowledgePlaneRegistry` | __init__, register, get, get_by_name, list, delete, get_statistics, clear_tenant (+1 more) | Registry for managing knowledge planes. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_knowledge_plane_registry` | `() -> KnowledgePlaneRegistry` | no | Get the singleton registry instance. |
| `_reset_registry` | `() -> None` | no | Reset the singleton (for testing). |
| `create_knowledge_plane` | `(tenant_id: str, name: str, description: Optional[str] = None) -> KnowledgePlane` | no | Create a new knowledge plane using the singleton registry. |
| `get_knowledge_plane` | `(plane_id: str) -> Optional[KnowledgePlane]` | no | Get a knowledge plane by ID using the singleton registry. |
| `list_knowledge_planes` | `(tenant_id: Optional[str] = None) -> list[KnowledgePlane]` | no | List knowledge planes using the singleton registry. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |
| `uuid` | uuid | no |

---

## offboarding.py
**Path:** `backend/app/hoc/cus/general/L5_lifecycle/engines/offboarding.py`  
**Layer:** L5_other | **Domain:** general | **Lines:** 532

**Docstring:** Offboarding Stage Handlers

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DeregisterHandler` | stage_name, handles_states, validate, execute, _check_active_references, _check_dependents | GAP-078: Start offboarding process. |
| `VerifyDeactivateHandler` | stage_name, handles_states, validate, execute, _check_active_usage | GAP-079: Verify deactivation is safe. |
| `DeactivateHandler` | stage_name, handles_states, validate, execute, _perform_deactivation | GAP-080: Deactivate knowledge plane (soft delete). |
| `ArchiveHandler` | stage_name, handles_states, validate, execute, _perform_archive | GAP-081: Archive knowledge plane to cold storage. |
| `PurgeHandler` | stage_name, handles_states, validate, execute, _perform_purge | GAP-082: Purge knowledge plane (permanent deletion). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.models.knowledge_lifecycle` | KnowledgePlaneLifecycleState | no |
| `base` | BaseStageHandler, StageContext, StageResult | yes |

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState` | L5 MUST NOT import L7 models directly | Route through L6 driver | 50 |

---

## onboarding.py
**Path:** `backend/app/hoc/cus/general/L5_lifecycle/engines/onboarding.py`  
**Layer:** L5_other | **Domain:** general | **Lines:** 703

**Docstring:** Onboarding Stage Handlers

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RegisterHandler` | stage_name, handles_states, validate, execute | GAP-071: Register knowledge plane. |
| `VerifyHandler` | stage_name, handles_states, validate, execute, _simulate_verification | GAP-072: Verify knowledge plane connectivity. |
| `IngestHandler` | stage_name, handles_states, validate, execute | GAP-073: Ingest data from knowledge source. |
| `IndexHandler` | stage_name, handles_states, validate, execute | GAP-074: Create indexes and embeddings. |
| `ClassifyHandler` | stage_name, handles_states, validate, execute | GAP-075: Classify data sensitivity and schema. |
| `ActivateHandler` | stage_name, handles_states, validate, execute, _simulate_activation | GAP-076: Activate knowledge plane. |
| `GovernHandler` | stage_name, handles_states, validate, execute | GAP-077: Runtime governance hooks. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, Optional | no |
| `app.models.knowledge_lifecycle` | KnowledgePlaneLifecycleState | no |
| `base` | BaseStageHandler, StageContext, StageResult, StageStatus | yes |

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState` | L5 MUST NOT import L7 models directly | Route through L6 driver | 45 |

---

## pool_manager.py
**Path:** `backend/app/hoc/cus/general/L5_lifecycle/engines/pool_manager.py`  
**Layer:** L5_other | **Domain:** general | **Lines:** 606

**Docstring:** Connection Pool Manager (GAP-172)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PoolType` |  | Types of connection pools. |
| `PoolStatus` |  | Pool health status. |
| `PoolConfig` |  | Configuration for a connection pool. |
| `PoolStats` | to_dict | Statistics for a connection pool. |
| `PoolHandle` |  | Handle to a managed connection pool. |
| `ConnectionPoolManager` | __init__, start, stop, create_database_pool, create_redis_pool, create_http_pool, get_pool, acquire_connection (+6 more) | Unified connection pool manager. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `asyncio` | asyncio | no |
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Callable, Dict, Optional | no |

---

## rollout_projection.py
**Path:** `backend/app/hoc/cus/general/L5_ui/engines/rollout_projection.py`  
**Layer:** L5_other | **Domain:** general | **Lines:** 724

**Docstring:** Part-2 Rollout Projection Service (L4 - Projection)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RolloutStage` |  | Rollout stages for controlled exposure. |
| `BlastRadius` |  | Blast radius projection attribute. |
| `StabilizationWindow` |  | Stabilization window for stage advancement. |
| `ContractSummary` |  | Summary of contract for rollout view. |
| `ExecutionSummary` |  | Summary of execution for rollout view. |
| `AuditSummary` |  | Summary of audit for rollout view. |
| `RolloutPlan` |  | Rollout plan showing progression. |
| `FounderRolloutView` |  | Complete rollout projection for founders. |
| `GovernanceCompletionReport` |  | Machine-generated governance completion artifact. |
| `CustomerRolloutView` |  | Customer-facing rollout view. |
| `RolloutProjectionService` | __init__, version, project_founder_view, _check_lineage_gaps, _derive_stage, _get_planned_stages, _default_blast_radius, _calculate_stabilization (+4 more) | Part-2 Rollout Projection Service (Read-Only) |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `founder_view_to_dict` | `(view: FounderRolloutView) -> dict[str, Any]` | no | Convert FounderRolloutView to dictionary for API response. |
| `completion_report_to_dict` | `(report: GovernanceCompletionReport) -> dict[str, Any]` | no | Convert GovernanceCompletionReport to dictionary for storage. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |

### Constants
`PROJECTION_VERSION`, `STAGE_ORDER`

---

## runtime_switch.py
**Path:** `backend/app/hoc/cus/general/L5_controls/drivers/runtime_switch.py`  
**Layer:** L5_other | **Domain:** general | **Lines:** 279

**Docstring:** Module: runtime_switch

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GovernanceState` |  | Current governance state. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `is_governance_active` | `() -> bool` | no | Check if governance is currently active. |
| `is_degraded_mode` | `() -> bool` | no | Check if system is in degraded mode (GAP-070). |
| `disable_governance_runtime` | `(reason: str, actor: str) -> None` | no | Emergency kill switch. Disables governance enforcement. |
| `enable_governance_runtime` | `(actor: str) -> None` | no | Re-enable governance after emergency. |
| `enter_degraded_mode` | `(reason: str, actor: str) -> None` | no | GAP-070: Enter degraded mode. |
| `exit_degraded_mode` | `(actor: str) -> None` | no | Exit degraded mode, return to normal operation. |
| `get_governance_state` | `() -> dict` | no | Get current governance state for health checks. |
| `reset_governance_state` | `() -> None` | no | Reset governance state to defaults (for testing). |
| `_emit_governance_event` | `(event_type: str, reason: str, actor: str) -> None` | no | Emit governance state change event. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `threading` | threading | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | Optional | no |
| `app.hoc.cus.general.L5_utils.time` | utc_now | no |

---

## time.py
**Path:** `backend/app/hoc/cus/general/L5_utils/time.py`  
**Layer:** L5_other | **Domain:** general | **Lines:** 25

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `utc_now` | `() -> datetime` | no | Get current UTC time. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |

---
