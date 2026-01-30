# hoc_cus_policies_L5_engines_policies_limits_query_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/policies/L5_engines/policies_limits_query_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | policies |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Limits query engine - read-only operations for limits

## Intent

**Role:** Limits query engine - read-only operations for limits
**Reference:** PIN-470, Phase 3B P3 Design-First
**Callers:** L2 policies API

## Purpose

Limits Query Engine (L5)

---

## Functions

### `get_limits_query_engine(session: 'AsyncSession') -> LimitsQueryEngine`
- **Async:** No
- **Docstring:** Get a LimitsQueryEngine instance.
- **Calls:** LimitsQueryEngine, get_limits_read_driver

## Classes

### `LimitSummaryResult`
- **Docstring:** Limit summary for list view (O2).
- **Class Variables:** limit_id: str, name: str, limit_category: str, limit_type: str, scope: str, enforcement: str, status: str, max_value: Decimal, window_seconds: Optional[int], reset_period: Optional[str], integrity_status: str, integrity_score: Decimal, breach_count_30d: int, last_breached_at: Optional[datetime], created_at: datetime

### `LimitsListResult`
- **Docstring:** Limits list response.
- **Class Variables:** items: list[LimitSummaryResult], total: int, has_more: bool, filters_applied: dict[str, Any]

### `LimitDetailResult`
- **Docstring:** Limit detail response (O3).
- **Class Variables:** limit_id: str, name: str, description: Optional[str], limit_category: str, limit_type: str, scope: str, enforcement: str, status: str, max_value: Decimal, window_seconds: Optional[int], reset_period: Optional[str], integrity_status: str, integrity_score: Decimal, breach_count_30d: int, last_breached_at: Optional[datetime], created_at: datetime, updated_at: Optional[datetime], current_value: Optional[Decimal], utilization_percent: Optional[float]

### `BudgetDefinitionResult`
- **Docstring:** Budget definition summary (THR-O2).
- **Class Variables:** id: str, name: str, scope: str, max_value: Decimal, reset_period: Optional[str], enforcement: str, status: str, current_usage: Optional[Decimal], utilization_percent: Optional[float]

### `BudgetsListResult`
- **Docstring:** Budget definitions list response.
- **Class Variables:** items: list[BudgetDefinitionResult], total: int, filters_applied: dict[str, Any]

### `LimitsQueryEngine`
- **Docstring:** L5 Query Engine for limits.
- **Methods:** __init__, list_limits, get_limit_detail, list_budgets

## Attributes

- `__all__` (line 308)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.controls.L6_drivers.limits_read_driver` |
| Cross-Domain | `app.hoc.cus.controls.L6_drivers.limits_read_driver` |
| External | `sqlalchemy.ext.asyncio` |

## Callers

L2 policies API

## Export Contract

```yaml
exports:
  functions:
    - name: get_limits_query_engine
      signature: "get_limits_query_engine(session: 'AsyncSession') -> LimitsQueryEngine"
  classes:
    - name: LimitSummaryResult
      methods: []
    - name: LimitsListResult
      methods: []
    - name: LimitDetailResult
      methods: []
    - name: BudgetDefinitionResult
      methods: []
    - name: BudgetsListResult
      methods: []
    - name: LimitsQueryEngine
      methods: [list_limits, get_limit_detail, list_budgets]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
