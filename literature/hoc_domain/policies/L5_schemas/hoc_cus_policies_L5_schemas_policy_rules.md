# hoc_cus_policies_L5_schemas_policy_rules

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_schemas/policy_rules.py` |
| Layer | L5 — Domain Schema |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy rules request/response schemas

## Intent

**Role:** Policy rules request/response schemas
**Reference:** PIN-LIM-02
**Callers:** api/policies.py, services/limits/policy_rules_service.py

## Purpose

Policy Rules Schemas (PIN-LIM-02)

---

## Classes

### `EnforcementModeEnum(str)`
- **Docstring:** Policy rule enforcement modes.

### `PolicyScopeEnum(str)`
- **Docstring:** Policy rule scope levels.

### `PolicySourceEnum(str)`
- **Docstring:** Policy rule creation source.

### `CreatePolicyRuleRequest(BaseModel)`
- **Docstring:** Request model for creating a policy rule.
- **Class Variables:** name: str, description: Optional[str], enforcement_mode: str, scope: str, scope_id: Optional[str], conditions: Optional[dict[str, Any]], source: str, source_proposal_id: Optional[str], parent_rule_id: Optional[str]

### `UpdatePolicyRuleRequest(BaseModel)`
- **Docstring:** Request model for updating a policy rule.
- **Class Variables:** name: Optional[str], description: Optional[str], enforcement_mode: Optional[str], conditions: Optional[dict[str, Any]], status: Optional[str], retirement_reason: Optional[str], superseded_by: Optional[str]

### `PolicyRuleResponse(BaseModel)`
- **Docstring:** Response model for policy rule operations.
- **Class Variables:** rule_id: str, tenant_id: str, name: str, description: Optional[str], enforcement_mode: str, scope: str, scope_id: Optional[str], conditions: Optional[dict[str, Any]], status: str, source: str, source_proposal_id: Optional[str], parent_rule_id: Optional[str], created_at: datetime, created_by: Optional[str], updated_at: datetime, retired_at: Optional[datetime], retired_by: Optional[str], retirement_reason: Optional[str], superseded_by: Optional[str]

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic` |

## Callers

api/policies.py, services/limits/policy_rules_service.py

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: EnforcementModeEnum
      methods: []
    - name: PolicyScopeEnum
      methods: []
    - name: PolicySourceEnum
      methods: []
    - name: CreatePolicyRuleRequest
      methods: []
    - name: UpdatePolicyRuleRequest
      methods: []
    - name: PolicyRuleResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
