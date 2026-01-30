# hoc_cus_policies_L5_engines_policies_rules_query_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/policies_rules_query_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Policy rules query engine - read-only operations for policy rules

## Intent

**Role:** Policy rules query engine - read-only operations for policy rules
**Reference:** PIN-470, Phase 3B P3 Design-First
**Callers:** L2 policies API

## Purpose

Policy Rules Query Engine (L5)

---

## Functions

### `get_policy_rules_query_engine(session: 'AsyncSession') -> PolicyRulesQueryEngine`
- **Async:** No
- **Docstring:** Get a PolicyRulesQueryEngine instance.
- **Calls:** PolicyRulesQueryEngine, get_policy_rules_read_driver

## Classes

### `PolicyRuleSummaryResult`
- **Docstring:** Policy rule summary for list view (O2).
- **Class Variables:** rule_id: str, name: str, enforcement_mode: str, scope: str, source: str, status: str, created_at: datetime, created_by: Optional[str], integrity_status: str, integrity_score: Decimal, trigger_count_30d: int, last_triggered_at: Optional[datetime]

### `PolicyRulesListResult`
- **Docstring:** Policy rules list response.
- **Class Variables:** items: list[PolicyRuleSummaryResult], total: int, has_more: bool, filters_applied: dict[str, Any]

### `PolicyRuleDetailResult`
- **Docstring:** Policy rule detail response (O3).
- **Class Variables:** rule_id: str, name: str, description: Optional[str], enforcement_mode: str, scope: str, source: str, status: str, created_at: datetime, created_by: Optional[str], updated_at: Optional[datetime], integrity_status: str, integrity_score: Decimal, trigger_count_30d: int, last_triggered_at: Optional[datetime], rule_definition: Optional[dict], violation_count_total: int

### `PolicyRulesQueryEngine`
- **Docstring:** L5 Query Engine for policy rules.
- **Methods:** __init__, list_policy_rules, get_policy_rule_detail, count_rules

## Attributes

- `__all__` (line 238)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.policies.L6_drivers.policy_rules_read_driver` |
| External | `sqlalchemy.ext.asyncio` |

## Callers

L2 policies API

## Export Contract

```yaml
exports:
  functions:
    - name: get_policy_rules_query_engine
      signature: "get_policy_rules_query_engine(session: 'AsyncSession') -> PolicyRulesQueryEngine"
  classes:
    - name: PolicyRuleSummaryResult
      methods: []
    - name: PolicyRulesListResult
      methods: []
    - name: PolicyRuleDetailResult
      methods: []
    - name: PolicyRulesQueryEngine
      methods: [list_policy_rules, get_policy_rule_detail, count_rules]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
