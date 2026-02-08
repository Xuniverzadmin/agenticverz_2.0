# Controls — L5 Schemas (5 files)

**Domain:** controls  
**Layer:** L5_schemas  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** Data contracts — Pydantic models, dataclasses, type references only

---

## override_types.py
**Path:** `backend/app/hoc/cus/controls/L5_schemas/override_types.py`  
**Layer:** L5_schemas | **Domain:** controls | **Lines:** 47

**Docstring:** Override Types

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LimitOverrideServiceError` |  | Base exception for limit override service. |
| `LimitNotFoundError` |  | Raised when the target limit does not exist. |
| `OverrideNotFoundError` |  | Raised when the override does not exist. |
| `OverrideValidationError` |  | Raised when override request validation fails. |
| `StackingAbuseError` |  | Raised when attempting to stack overrides on same limit. |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### __all__ Exports
`LimitOverrideServiceError`, `LimitNotFoundError`, `OverrideNotFoundError`, `OverrideValidationError`, `StackingAbuseError`

---

## overrides.py
**Path:** `backend/app/hoc/cus/controls/L5_schemas/overrides.py`  
**Layer:** L5_schemas | **Domain:** controls | **Lines:** 188

**Docstring:** Limit Override Schemas (PIN-LIM-05)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `OverrideStatus` |  | Override lifecycle status. |
| `LimitOverrideRequest` | validate_override_value | Request model for requesting a temporary limit override. |
| `LimitOverrideResponse` |  | Response model for limit override operations. |
| `OverrideApprovalRequest` | validate_rejection_reason | Request model for approving/rejecting an override. |
| `OverrideListResponse` |  | Response model for listing overrides. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `decimal` | Decimal | no |
| `enum` | Enum | no |
| `typing` | Optional | no |
| `pydantic` | BaseModel, Field, field_validator | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

---

## policy_limits.py
**Path:** `backend/app/hoc/cus/controls/L5_schemas/policy_limits.py`  
**Layer:** L5_schemas | **Domain:** controls | **Lines:** 190

**Docstring:** Policy Limits Schemas (PIN-LIM-01)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LimitCategoryEnum` |  | Limit categories. |
| `LimitScopeEnum` |  | Limit scope levels. |
| `LimitEnforcementEnum` |  | Limit enforcement behaviors. |
| `ResetPeriodEnum` |  | Budget limit reset periods. |
| `CreatePolicyLimitRequest` | validate_reset_period, validate_window_seconds | Request model for creating a policy limit. |
| `UpdatePolicyLimitRequest` |  | Request model for updating a policy limit. |
| `PolicyLimitResponse` |  | Response model for policy limit operations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `decimal` | Decimal | no |
| `enum` | Enum | no |
| `typing` | Optional | no |
| `pydantic` | BaseModel, Field, field_validator | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

---

## simulation.py
**Path:** `backend/app/hoc/cus/controls/L5_schemas/simulation.py`  
**Layer:** L5_schemas | **Domain:** controls | **Lines:** 217

**Docstring:** Limit Simulation Schemas (PIN-LIM-04)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SimulationDecision` |  | Simulation outcome decision. |
| `MessageCode` |  | Standardized message codes (no free-text messages). |
| `LimitSimulationRequest` |  | Request model for limit simulation (pre-execution check). |
| `LimitCheckResult` |  | Result of a single limit check. |
| `HeadroomInfo` |  | Remaining headroom before hitting limits. |
| `LimitWarning` |  | Warning for soft limit approaching. |
| `LimitSimulationResponse` |  | Response model for limit simulation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `decimal` | Decimal | no |
| `enum` | Enum | no |
| `typing` | Optional | no |
| `pydantic` | BaseModel, Field | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

---

## threshold_signals.py
**Path:** `backend/app/hoc/cus/controls/L5_schemas/threshold_signals.py`  
**Layer:** L5_schemas | **Domain:** controls | **Lines:** 49

**Docstring:** Threshold Signal Types (L5 Schema)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ThresholdSignal` |  | Signals emitted when runs breach thresholds. |
| `ThresholdEvaluationResult` |  | Result of threshold evaluation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `enum` | Enum | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### __all__ Exports
`ThresholdSignal`, `ThresholdEvaluationResult`

---
