# hoc_models_policy_control_plane

| Field | Value |
|-------|-------|
| Path | `backend/app/models/policy_control_plane.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Policy control-plane models (PIN-412)

## Intent

**Role:** Policy control-plane models (PIN-412)
**Reference:** PIN-412 Domain Design
**Callers:** policy/*, api/policies/*

## Purpose

Policy Control-Plane Models (PIN-412)

---

## Functions

### `utc_now() -> datetime`
- **Async:** No
- **Docstring:** Return current UTC time (PIN-412).
- **Calls:** now

### `generate_uuid() -> str`
- **Async:** No
- **Docstring:** Generate a UUID string (PIN-412).
- **Calls:** str, uuid4

## Classes

### `EnforcementMode(str, Enum)`
- **Docstring:** Policy rule enforcement modes.

### `PolicyScope(str, Enum)`
- **Docstring:** Policy rule scope levels.

### `LimitScope(str, Enum)`
- **Docstring:** Limit scope levels (extends PolicyScope with PROVIDER).

### `PolicyRuleStatus(str, Enum)`
- **Docstring:** Policy rule lifecycle status.

### `PolicySource(str, Enum)`
- **Docstring:** Policy rule creation source.

### `RuleType(str, Enum)`
- **Docstring:** Policy rule semantic type (PIN-411 Gap Closure).

### `EnforcementAction(str, Enum)`
- **Docstring:** Actions taken when a rule triggers.

### `LimitCategory(str, Enum)`
- **Docstring:** Limit categories.

### `LimitEnforcement(str, Enum)`
- **Docstring:** Limit enforcement behaviors.

### `LimitConsequence(str, Enum)`
- **Docstring:** Threshold limit consequences.

### `ResetPeriod(str, Enum)`
- **Docstring:** Budget limit reset periods.

### `LimitStatus(str, Enum)`
- **Docstring:** Limit status.

### `BreachType(str, Enum)`
- **Docstring:** Types of limit breaches.

### `PolicyRule(SQLModel)`
- **Docstring:** Policy rule record - governance rule definition.
- **Methods:** retire
- **Class Variables:** id: str, tenant_id: str, name: str, description: Optional[str], enforcement_mode: str, scope: str, scope_id: Optional[str], conditions: Optional[dict], status: str, created_by: Optional[str], source: str, rule_type: str, source_proposal_id: Optional[str], parent_rule_id: Optional[str], legacy_rule_id: Optional[str], retired_at: Optional[datetime], retired_by: Optional[str], retirement_reason: Optional[str], superseded_by: Optional[str], created_at: datetime, updated_at: datetime, enforcements: list['PolicyEnforcement']

### `PolicyEnforcement(SQLModel)`
- **Docstring:** Policy enforcement record - when a rule triggered.
- **Class Variables:** id: str, tenant_id: str, rule_id: str, run_id: Optional[str], incident_id: Optional[str], action_taken: str, details: Optional[dict], triggered_at: datetime, rule: Optional[PolicyRule]

### `Limit(SQLModel)`
- **Docstring:** Limit record - quantitative constraint definition.
- **Class Variables:** id: str, tenant_id: str, name: str, description: Optional[str], limit_category: str, limit_type: str, scope: str, scope_id: Optional[str], max_value: Decimal, reset_period: Optional[str], next_reset_at: Optional[datetime], window_seconds: Optional[int], measurement_window_seconds: Optional[int], params: Optional[dict], enforcement: str, consequence: Optional[str], status: str, created_at: datetime, updated_at: datetime, breaches: list['LimitBreach']

### `LimitBreach(SQLModel)`
- **Docstring:** Limit breach record - when a limit was exceeded.
- **Class Variables:** id: str, tenant_id: str, limit_id: str, run_id: Optional[str], incident_id: Optional[str], breach_type: str, value_at_breach: Optional[Decimal], limit_value: Decimal, details: Optional[dict], breached_at: datetime, recovered_at: Optional[datetime], limit: Optional[Limit]

### `IntegrityStatus(str, Enum)`
- **Docstring:** Policy rule integrity status values.

### `PolicyRuleIntegrity(SQLModel)`
- **Docstring:** Policy rule integrity record - current integrity state per rule.
- **Class Variables:** id: str, rule_id: str, integrity_status: str, integrity_score: Decimal, hash_root: str, details: Optional[dict], computed_at: datetime

### `LimitIntegrity(SQLModel)`
- **Docstring:** Limit integrity record - current integrity state per limit.
- **Class Variables:** id: str, limit_id: str, integrity_status: str, integrity_score: Decimal, computed_at: datetime

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.dialects.postgresql`, `sqlmodel` |

## Callers

policy/*, api/policies/*

## Export Contract

```yaml
exports:
  functions:
    - name: utc_now
      signature: "utc_now() -> datetime"
    - name: generate_uuid
      signature: "generate_uuid() -> str"
  classes:
    - name: EnforcementMode
      methods: []
    - name: PolicyScope
      methods: []
    - name: LimitScope
      methods: []
    - name: PolicyRuleStatus
      methods: []
    - name: PolicySource
      methods: []
    - name: RuleType
      methods: []
    - name: EnforcementAction
      methods: []
    - name: LimitCategory
      methods: []
    - name: LimitEnforcement
      methods: []
    - name: LimitConsequence
      methods: []
    - name: ResetPeriod
      methods: []
    - name: LimitStatus
      methods: []
    - name: BreachType
      methods: []
    - name: PolicyRule
      methods: [retire]
    - name: PolicyEnforcement
      methods: []
    - name: Limit
      methods: []
    - name: LimitBreach
      methods: []
    - name: IntegrityStatus
      methods: []
    - name: PolicyRuleIntegrity
      methods: []
    - name: LimitIntegrity
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
