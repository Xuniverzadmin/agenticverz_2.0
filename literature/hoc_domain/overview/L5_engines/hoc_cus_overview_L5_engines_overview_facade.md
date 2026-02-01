# hoc_cus_overview_L5_engines_overview_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/overview/L5_engines/overview_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | overview |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Overview Engine - Centralized access to overview domain operations

## Intent

**Role:** Overview Engine - Centralized access to overview domain operations
**Reference:** PIN-470
**Callers:** L2 API routes (/api/v1/overview/*)

## Purpose

Overview Engine (L5 Domain Logic)

---

## Functions

### `get_overview_facade() -> OverviewFacade`
- **Async:** No
- **Docstring:** Get the singleton OverviewFacade instance.
- **Calls:** OverviewFacade

## Classes

### `SystemPulse`
- **Docstring:** System health pulse summary.
- **Methods:** to_dict
- **Class Variables:** status: str, active_incidents: int, pending_decisions: int, recent_breaches: int, live_runs: int, queued_runs: int

### `DomainCount`
- **Docstring:** Count for a specific domain.
- **Methods:** to_dict
- **Class Variables:** domain: str, total: int, pending: int, critical: int

### `HighlightsResult`
- **Docstring:** Result from get_highlights.
- **Methods:** to_dict
- **Class Variables:** pulse: SystemPulse, domain_counts: List[DomainCount], last_activity_at: Optional[datetime]

### `DecisionItem`
- **Docstring:** A pending decision requiring human action.
- **Methods:** to_dict
- **Class Variables:** source_domain: str, entity_type: str, entity_id: str, decision_type: str, priority: str, summary: str, created_at: datetime

### `DecisionsResult`
- **Docstring:** Result from get_decisions.
- **Methods:** to_dict
- **Class Variables:** items: List[DecisionItem], total: int, has_more: bool, filters_applied: Dict[str, Any]

### `CostPeriod`
- **Docstring:** Time period for cost calculation.
- **Methods:** to_dict
- **Class Variables:** start: datetime, end: datetime

### `LimitCostItem`
- **Docstring:** Single limit with cost status.
- **Methods:** to_dict
- **Class Variables:** limit_id: str, name: str, category: str, max_value: float, used_value: float, remaining_value: float, status: str

### `CostsResult`
- **Docstring:** Result from get_costs.
- **Methods:** to_dict
- **Class Variables:** currency: str, period: CostPeriod, llm_run_cost: float, limits: List[LimitCostItem], breach_count: int, total_overage: float

### `DecisionsCountResult`
- **Docstring:** Result from get_decisions_count.
- **Methods:** to_dict
- **Class Variables:** total: int, by_domain: Dict[str, int], by_priority: Dict[str, int]

### `RecoveryStatsResult`
- **Docstring:** Result from get_recovery_stats.
- **Methods:** to_dict
- **Class Variables:** total_incidents: int, recovered: int, pending_recovery: int, failed_recovery: int, recovery_rate_pct: float, period: CostPeriod

### `OverviewFacade`
- **Docstring:** Overview Facade - Centralized access to overview domain operations.
- **Methods:** __init__, get_highlights, get_decisions, get_costs, get_decisions_count, get_recovery_stats

## Attributes

- `logger` (line 76)
- `_overview_facade: Optional[OverviewFacade]` (line 593)
- `__all__` (line 604)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.overview.L6_drivers.overview_facade_driver` |
| External | `__future__`, `app.hoc.cus.hoc_spine.services.time`, `sqlalchemy.ext.asyncio` |

## Callers

L2 API routes (/api/v1/overview/*)

## Export Contract

```yaml
exports:
  functions:
    - name: get_overview_facade
      signature: "get_overview_facade() -> OverviewFacade"
  classes:
    - name: SystemPulse
      methods: [to_dict]
    - name: DomainCount
      methods: [to_dict]
    - name: HighlightsResult
      methods: [to_dict]
    - name: DecisionItem
      methods: [to_dict]
    - name: DecisionsResult
      methods: [to_dict]
    - name: CostPeriod
      methods: [to_dict]
    - name: LimitCostItem
      methods: [to_dict]
    - name: CostsResult
      methods: [to_dict]
    - name: DecisionsCountResult
      methods: [to_dict]
    - name: RecoveryStatsResult
      methods: [to_dict]
    - name: OverviewFacade
      methods: [get_highlights, get_decisions, get_costs, get_decisions_count, get_recovery_stats]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
