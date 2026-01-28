# General — L4 Runtime (6 files)

**Domain:** general  
**Layer:** L4_runtime  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Control plane — authority/execution/consequences, owns commit, all execution enters L4 once

---

## constraint_checker.py
**Path:** `backend/app/hoc/cus/general/L4_runtime/engines/constraint_checker.py`  
**Layer:** L4_runtime | **Domain:** general | **Lines:** 310

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

**Contract:** Control plane — authority/execution/consequences, owns commit, all execution enters L4 once

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters

---

## governance_orchestrator.py
**Path:** `backend/app/hoc/cus/general/L4_runtime/engines/governance_orchestrator.py`  
**Layer:** L4_runtime | **Domain:** general | **Lines:** 807

**Docstring:** Part-2 Governance Orchestrator (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `HealthLookup` | capture_health_snapshot | Protocol for capturing health state (read-only). |
| `JobState` |  | In-memory representation of job state. |
| `JobStateMachine` | can_transition, validate_transition, transition | State machine for Governance Job lifecycle. |
| `ExecutionOrchestrator` | create_job_plan, _parse_change_to_step | Translates contract → job plan. |
| `JobStateTracker` | record_step_result, calculate_completion_status | Observes job state - does NOT control execution. |
| `AuditEvidence` |  | Evidence package for audit layer. |
| `AuditTrigger` | prepare_evidence, should_trigger_audit | Prepares and hands evidence to audit layer. |
| `ContractActivationError` | __init__ | Raised when contract activation fails. |
| `ContractActivationService` | __init__, activate_contract | Activates approved contracts (APPROVED → ACTIVE). |
| `GovernanceOrchestrator` | __init__, version, activate_contract, start_job, record_step_result, complete_job, cancel_job, should_trigger_audit (+4 more) | Facade for all governance orchestration services. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Optional, Protocol | no |
| `uuid` | UUID, uuid4 | no |
| `app.models.contract` | ContractStatus | no |
| `app.models.governance_job` | JOB_TERMINAL_STATES, JOB_VALID_TRANSITIONS, HealthSnapshot, InvalidJobTransitionError, JobImmutableError (+5) | no |
| `app.hoc.cus.general.L5_workflow.contracts.engines.contract_engine` | ContractService, ContractState | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Control plane — authority/execution/consequences, owns commit, all execution enters L4 once

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters

### Constants
`ORCHESTRATOR_VERSION`

---

## phase_status_invariants.py
**Path:** `backend/app/hoc/cus/general/L4_runtime/engines/phase_status_invariants.py`  
**Layer:** L4_runtime | **Domain:** general | **Lines:** 361

**Docstring:** Module: phase_status_invariants

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `InvariantCheckResult` |  | Result of an invariant check. |
| `PhaseStatusInvariantEnforcementError` | __init__, to_dict | Raised when phase-status invariant enforcement fails. |
| `InvariantCheckResponse` | to_dict | Response from an invariant check. |
| `PhaseStatusInvariantChecker` | __init__, from_governance_config, enforcement_enabled, get_allowed_statuses, is_valid_combination, check, ensure_valid, should_allow_transition | Checks and enforces phase-status invariants. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_phase_status_invariant` | `(phase: str, status: str, enforcement_enabled: bool = True) -> InvariantCheckRes` | no | Quick helper to check a phase-status invariant. |
| `ensure_phase_status_invariant` | `(phase: str, status: str, enforcement_enabled: bool = True) -> None` | no | Quick helper to ensure phase-status invariant or raise error. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Any, FrozenSet, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Control plane — authority/execution/consequences, owns commit, all execution enters L4 once

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters

---

## plan_generation_engine.py
**Path:** `backend/app/hoc/cus/general/L4_runtime/engines/plan_generation_engine.py`  
**Layer:** L4_runtime | **Domain:** general | **Lines:** 264

**Docstring:** Domain engine for plan generation.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PlanGenerationContext` |  | Context for plan generation. |
| `PlanGenerationResult` |  | Result of plan generation. |
| `PlanGenerationEngine` | __init__, generate | L4 Domain Engine for plan generation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `generate_plan_for_run` | `(agent_id: str, goal: str, run_id: str) -> PlanGenerationResult` | no | Convenience function to generate a plan for a run. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.memory` | get_retriever | no |
| `app.planners` | get_planner | no |
| `app.skills` | get_skill_manifest | no |
| `app.utils.budget_tracker` | get_budget_tracker | no |
| `app.utils.plan_inspector` | validate_plan | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Control plane — authority/execution/consequences, owns commit, all execution enters L4 once

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters

### __all__ Exports
`PlanGenerationContext`, `PlanGenerationResult`, `PlanGenerationEngine`, `generate_plan_for_run`

---

## run_governance_facade.py
**Path:** `backend/app/hoc/cus/general/L4_runtime/facades/run_governance_facade.py`  
**Layer:** L4_runtime | **Domain:** general | **Lines:** 335

**Docstring:** Run Governance Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RunGovernanceFacade` | __init__, _lessons, create_policy_evaluation, _emit_ack, emit_near_threshold_lesson, emit_critical_success_lesson | Facade for run governance operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_run_governance_facade` | `() -> RunGovernanceFacade` | no | Get the run governance facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `typing` | Any, Dict, Optional | no |
| `uuid` | UUID | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Control plane — authority/execution/consequences, owns commit, all execution enters L4 once

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters

### Constants
`RAC_ENABLED`

---

## transaction_coordinator.py
**Path:** `backend/app/hoc/cus/general/L4_runtime/drivers/transaction_coordinator.py`  
**Layer:** L4_runtime | **Domain:** general | **Lines:** 841

**Docstring:** Transaction Coordinator for Cross-Domain Writes

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TransactionPhase` |  | Phases of transaction execution. |
| `TransactionFailed` | __init__ | Raised when cross-domain transaction fails. |
| `DomainResult` | to_dict | Result from a single domain operation. |
| `TransactionResult` | is_complete, all_domains_succeeded, to_dict | Result of a successful cross-domain transaction. |
| `RollbackAction` |  | Describes a rollback action for a domain operation. |
| `RunCompletionTransaction` | __init__, execute, _create_incident, _create_policy_evaluation, _complete_trace, _publish_events, _execute_rollback, _emit_rollback_ack (+2 more) | Atomic cross-domain transaction for run completion. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_transaction_coordinator` | `() -> RunCompletionTransaction` | no | Get the singleton transaction coordinator instance. |
| `create_transaction_coordinator` | `(publisher = None) -> RunCompletionTransaction` | no | Create a new transaction coordinator instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Callable, Dict, List, Optional | no |
| `uuid` | UUID | no |
| `sqlmodel` | Session | no |
| `app.db` | engine | no |
| `app.events` | get_publisher | no |
| `app.hoc.cus.general.L5_schemas.rac_models` | AckStatus, AuditAction, AuditDomain, DomainAck | no |
| `app.hoc.cus.general.L5_engines.audit_store` | get_audit_store | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Control plane — authority/execution/consequences, owns commit, all execution enters L4 once

**SHOULD call:** L5_engines, L6_drivers
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters

### Constants
`RAC_ROLLBACK_AUDIT_ENABLED`, `TRANSACTION_COORDINATOR_ENABLED`

---
