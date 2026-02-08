# Policies — L5 Schemas (4 files)

**Domain:** policies  
**Layer:** L5_schemas  
**Reference:** HOC_LAYER_TOPOLOGY_V2.0.0.md (RATIFIED)

**Layer Contract:** Data contracts — Pydantic models, dataclasses, type references only

---

## domain_bridge_capabilities.py
**Path:** `backend/app/hoc/cus/policies/L5_schemas/domain_bridge_capabilities.py`  
**Layer:** L5_schemas | **Domain:** policies | **Lines:** 199

**Docstring:** Domain Bridge Capability Protocols (PIN-508 Phase 2)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LessonsQueryCapability` | insert_lesson, fetch_lessons_list, fetch_lesson_by_id, fetch_lesson_stats, fetch_debounce_count, insert_policy_proposal_from_lesson, update_lesson_converted, update_lesson_deferred (+3 more) | Capability Protocol for lessons data access. |
| `LimitsQueryCapability` | fetch_limits, fetch_limit_by_id, fetch_budget_limits | Capability Protocol for limits read access. |
| `PolicyLimitsCapability` | add_limit, add_integrity, fetch_limit_by_id, flush | Capability Protocol for policy limits CRUD. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional, Protocol (+1) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

### __all__ Exports
`LessonsQueryCapability`, `LimitsQueryCapability`, `PolicyLimitsCapability`

---

## intent_validation.py
**Path:** `backend/app/hoc/cus/policies/L5_schemas/intent_validation.py`  
**Layer:** L5_schemas | **Domain:** policies | **Lines:** 43

**Docstring:** M19 Intent Validation Protocol.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyIntentValidationResult` |  | Result of M19 intent validation. |
| `PolicyIntentValidator` | validate_intent | Protocol for M19 intent validators. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Protocol, runtime_checkable | no |
| `typing_extensions` | TypedDict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

---

## policy_check.py
**Path:** `backend/app/hoc/cus/policies/L5_schemas/policy_check.py`  
**Layer:** L5_schemas | **Domain:** policies | **Lines:** 42

**Docstring:** IRCheckPolicy Validation Protocol.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyCheckResult` |  | Result of an IR policy check. |
| `PolicyCheckValidator` | validate_policy | Protocol for IR policy check validators. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Protocol, runtime_checkable | no |
| `typing_extensions` | TypedDict | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

---

## policy_rules.py
**Path:** `backend/app/hoc/cus/policies/L5_schemas/policy_rules.py`  
**Layer:** L5_schemas | **Domain:** policies | **Lines:** 161

**Docstring:** Policy Rules Schemas (PIN-LIM-02)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `EnforcementModeEnum` |  | Policy rule enforcement modes. |
| `PolicyScopeEnum` |  | Policy rule scope levels. |
| `PolicySourceEnum` |  | Policy rule creation source. |
| `CreatePolicyRuleRequest` |  | Request model for creating a policy rule. |
| `UpdatePolicyRuleRequest` |  | Request model for updating a policy rule. |
| `PolicyRuleResponse` |  | Response model for policy rule operations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | Any, Optional | no |
| `pydantic` | BaseModel, Field | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V2.0.0)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L4_spine, L5_engines, L6_drivers
**Called by:** L5_engines, L4_spine

---
