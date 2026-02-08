# Account — L5 Schemas (8 files)

**Domain:** account  
**Layer:** L5_schemas  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** Data contracts — Pydantic models, dataclasses, type references only

---

## crm_validator_types.py
**Path:** `backend/app/hoc/cus/account/L5_schemas/crm_validator_types.py`  
**Layer:** L5_schemas | **Domain:** account | **Lines:** 145

**Docstring:** CRM Validator Types (L5 Schemas)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IssueType` |  | Issue type classification. |
| `Severity` |  | Issue severity classification. |
| `RecommendedAction` |  | Recommended action from validator. |
| `IssueSource` |  | Issue source for confidence weighting. |
| `ValidatorInput` |  | Input to the validator. |
| `ValidatorVerdict` |  | Output from the validator. |
| `ValidatorErrorType` |  | Error types for validator failures. |
| `ValidatorError` |  | Error from validator with fallback verdict. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `decimal` | Decimal | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### __all__ Exports
`IssueType`, `Severity`, `RecommendedAction`, `IssueSource`, `ValidatorInput`, `ValidatorVerdict`, `ValidatorErrorType`, `ValidatorError`

---

## lifecycle_dtos.py
**Path:** `backend/app/hoc/cus/account/L5_schemas/lifecycle_dtos.py`  
**Layer:** L5_schemas | **Domain:** account | **Lines:** 84

**Docstring:** Lifecycle DTOs

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LifecycleActorType` |  | Who initiated the lifecycle action. |
| `LifecycleActorContext` |  | Context about who is performing the lifecycle action. |
| `LifecycleTransitionResult` |  | Result of a lifecycle transition attempt. |
| `LifecycleStateSnapshot` |  | Read-only snapshot of a tenant's lifecycle state. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### __all__ Exports
`LifecycleActorType`, `LifecycleActorContext`, `LifecycleTransitionResult`, `LifecycleStateSnapshot`

---

## onboarding_dtos.py
**Path:** `backend/app/hoc/cus/account/L5_schemas/onboarding_dtos.py`  
**Layer:** L5_schemas | **Domain:** account | **Lines:** 50

**Docstring:** Onboarding DTOs (L5 Schema)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `OnboardingTransitionResult` |  | Result of an onboarding state transition attempt. |
| `OnboardingStateSnapshot` |  | Current onboarding state for a tenant. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### __all__ Exports
`OnboardingTransitionResult`, `OnboardingStateSnapshot`

---

## onboarding_state.py
**Path:** `backend/app/hoc/cus/account/L5_schemas/onboarding_state.py`  
**Layer:** L5_schemas | **Domain:** account | **Lines:** 108

**Docstring:** Onboarding State Machine — Canonical (HOC)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `OnboardingState` | from_string, default | Monotonic onboarding state machine (forward-only). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `is_at_or_past` | `(current: int, target: int) -> bool` | no |  |
| `is_complete` | `(state: int) -> bool` | no |  |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `enum` | IntEnum | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### Constants
`STATE_TRANSITIONS`

### __all__ Exports
`OnboardingState`, `OnboardingStatus`, `ONBOARDING_STATUS_NAMES`, `STATE_TRANSITIONS`, `is_at_or_past`, `is_complete`

---

## plan_quotas.py
**Path:** `backend/app/hoc/cus/account/L5_schemas/plan_quotas.py`  
**Layer:** L5_schemas | **Domain:** account | **Lines:** 46

**Docstring:** Plan quota constants mirror.

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### Constants
`PLAN_QUOTAS`

---

## result_types.py
**Path:** `backend/app/hoc/cus/account/L5_schemas/result_types.py`  
**Layer:** L5_schemas | **Domain:** account | **Lines:** 25

**Docstring:** Account Result Types (L5 Schemas)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AccountsErrorResult` |  | Error result for accounts operations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

---

## tenant_lifecycle_enums.py
**Path:** `backend/app/hoc/cus/account/L5_schemas/tenant_lifecycle_enums.py`  
**Layer:** L5_schemas | **Domain:** account | **Lines:** 151

**Docstring:** Tenant Lifecycle Status Enums

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TenantLifecycleStatus` |  | Tenant lifecycle status values (matches DB VARCHAR). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `normalize_status` | `(raw: Optional[str]) -> TenantLifecycleStatus` | no | Normalize a raw DB status string to TenantLifecycleStatus. |
| `is_valid_transition` | `(from_status: TenantLifecycleStatus, to_status: TenantLifecycleStatus) -> bool` | no | Check if a lifecycle transition is valid. |
| `allows_sdk_execution` | `(status: TenantLifecycleStatus) -> bool` | no | Check if SDK execution is allowed in this status. |
| `allows_writes` | `(status: TenantLifecycleStatus) -> bool` | no | Check if data writes are allowed in this status. |
| `allows_reads` | `(status: TenantLifecycleStatus) -> bool` | no | Check if data reads are allowed in this status. |
| `allows_new_api_keys` | `(status: TenantLifecycleStatus) -> bool` | no | Check if new API keys can be created in this status. |
| `allows_token_refresh` | `(status: TenantLifecycleStatus) -> bool` | no | Check if auth token refresh is allowed in this status. |
| `is_terminal` | `(status: TenantLifecycleStatus) -> bool` | no | Check if this is a terminal status (no return to ACTIVE). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `enum` | Enum | no |
| `typing` | Dict, Optional, Set | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### __all__ Exports
`TenantLifecycleStatus`, `LEGACY_STATUS_MAP`, `VALID_TRANSITIONS`, `normalize_status`, `is_valid_transition`, `allows_sdk_execution`, `allows_writes`, `allows_reads`, `allows_new_api_keys`, `allows_token_refresh`, `is_terminal`

---

## tenant_lifecycle_state.py
**Path:** `backend/app/hoc/cus/account/L5_schemas/tenant_lifecycle_state.py`  
**Layer:** L5_schemas | **Domain:** account | **Lines:** 130

**Docstring:** Tenant Lifecycle State (IntEnum)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TenantLifecycleState` | allows_sdk_execution, allows_writes, allows_reads, allows_new_api_keys, allows_token_refresh, is_terminal, is_reversible |  |
| `LifecycleAction` |  |  |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `_to_status` | `(state: TenantLifecycleState) -> TenantLifecycleStatus` | no |  |
| `_to_state` | `(status: TenantLifecycleStatus) -> TenantLifecycleState` | no |  |
| `is_valid_transition` | `(from_state: TenantLifecycleState, to_state: TenantLifecycleState) -> bool` | no |  |
| `get_valid_transitions` | `(from_state: TenantLifecycleState) -> Set[TenantLifecycleState]` | no |  |
| `get_action_for_transition` | `(from_state: TenantLifecycleState, to_state: TenantLifecycleState) -> str | None` | no |  |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `enum` | IntEnum | no |
| `typing` | Set, Tuple | no |
| `app.hoc.cus.account.L5_schemas.tenant_lifecycle_enums` | TenantLifecycleStatus, VALID_TRANSITIONS, is_valid_transition | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### Constants
`_STATUS_TO_STATE`, `_STATE_TO_STATUS`

### __all__ Exports
`TenantLifecycleState`, `LifecycleAction`, `VALID_TRANSITIONS`, `ACTION_TRANSITIONS`, `is_valid_transition`, `get_valid_transitions`, `get_action_for_transition`

---
