# Policies — L5 Schemas (1 files)

**Domain:** policies  
**Layer:** L5_schemas  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Data contracts — Pydantic models, dataclasses, type references only

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

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Data contracts — Pydantic models, dataclasses, type references only

**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines, L6_drivers
**Called by:** L5_engines, L3_adapters

---
