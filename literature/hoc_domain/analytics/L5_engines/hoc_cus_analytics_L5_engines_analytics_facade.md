# hoc_cus_analytics_L5_engines_analytics_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/analytics/L5_engines/analytics_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | analytics |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Analytics Facade - Centralized access to analytics domain operations

## Intent

**Role:** Analytics Facade - Centralized access to analytics domain operations
**Reference:** PIN-470, Analytics Domain Declaration v1, PIN-411, W4 Pattern
**Callers:** app.api.analytics (L2)

## Purpose

Analytics Facade (L5)

---

## Functions

### `get_analytics_facade() -> AnalyticsFacade`
- **Async:** No
- **Docstring:** Get the singleton AnalyticsFacade instance.
- **Calls:** AnalyticsFacade

## Classes

### `ResolutionType(str, Enum)`
- **Docstring:** Time resolution for analytics data.

### `ScopeType(str, Enum)`
- **Docstring:** Scope of analytics aggregation.

### `TimeWindowResult`
- **Docstring:** Time window specification.
- **Class Variables:** from_ts: datetime, to_ts: datetime, resolution: str

### `UsageTotalsResult`
- **Docstring:** Aggregate usage totals.
- **Class Variables:** requests: int, compute_units: int, tokens: int

### `UsageDataPointResult`
- **Docstring:** Single data point in usage time series.
- **Class Variables:** ts: str, requests: int, compute_units: int, tokens: int

### `SignalSourceResult`
- **Docstring:** Signal source metadata.
- **Class Variables:** sources: list[str], freshness_sec: int

### `UsageStatisticsResult`
- **Docstring:** Usage statistics result.
- **Class Variables:** window: TimeWindowResult, totals: UsageTotalsResult, series: list[UsageDataPointResult], signals: SignalSourceResult

### `CostTotalsResult`
- **Docstring:** Aggregate cost totals.
- **Class Variables:** spend_cents: float, spend_usd: float, requests: int, input_tokens: int, output_tokens: int

### `CostDataPointResult`
- **Docstring:** Single data point in cost time series.
- **Class Variables:** ts: str, spend_cents: float, requests: int, input_tokens: int, output_tokens: int

### `CostByModelResult`
- **Docstring:** Cost breakdown by model.
- **Class Variables:** model: str, spend_cents: float, requests: int, input_tokens: int, output_tokens: int, pct_of_total: float

### `CostByFeatureResult`
- **Docstring:** Cost breakdown by feature tag.
- **Class Variables:** feature_tag: str, spend_cents: float, requests: int, pct_of_total: float

### `CostStatisticsResult`
- **Docstring:** Cost statistics result.
- **Class Variables:** window: TimeWindowResult, totals: CostTotalsResult, series: list[CostDataPointResult], by_model: list[CostByModelResult], by_feature: list[CostByFeatureResult], signals: SignalSourceResult

### `TopicStatusResult`
- **Docstring:** Status of a topic within a subdomain.
- **Class Variables:** read: bool, write: bool, signals_bound: int

### `AnalyticsStatusResult`
- **Docstring:** Analytics domain status.
- **Class Variables:** domain: str, subdomains: list[str], topics: dict[str, TopicStatusResult]

### `SignalAdapter`
- **Docstring:** Signal adapters for fetching data from various sources.
- **Methods:** fetch_cost_metrics, fetch_llm_usage, fetch_worker_execution, fetch_cost_spend, fetch_cost_by_model, fetch_cost_by_feature

### `AnalyticsFacade`
- **Docstring:** Unified facade for Analytics domain operations.
- **Methods:** __init__, get_usage_statistics, get_cost_statistics, get_status, _calculate_freshness, _calculate_freshness_from_cost

## Attributes

- `logger` (line 55)
- `_facade_instance: AnalyticsFacade | None` (line 631)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.analytics.L6_drivers.analytics_read_driver` |
| External | `__future__`, `sqlalchemy.ext.asyncio` |

## Callers

app.api.analytics (L2)

## Export Contract

```yaml
exports:
  functions:
    - name: get_analytics_facade
      signature: "get_analytics_facade() -> AnalyticsFacade"
  classes:
    - name: ResolutionType
      methods: []
    - name: ScopeType
      methods: []
    - name: TimeWindowResult
      methods: []
    - name: UsageTotalsResult
      methods: []
    - name: UsageDataPointResult
      methods: []
    - name: SignalSourceResult
      methods: []
    - name: UsageStatisticsResult
      methods: []
    - name: CostTotalsResult
      methods: []
    - name: CostDataPointResult
      methods: []
    - name: CostByModelResult
      methods: []
    - name: CostByFeatureResult
      methods: []
    - name: CostStatisticsResult
      methods: []
    - name: TopicStatusResult
      methods: []
    - name: AnalyticsStatusResult
      methods: []
    - name: SignalAdapter
      methods: [fetch_cost_metrics, fetch_llm_usage, fetch_worker_execution, fetch_cost_spend, fetch_cost_by_model, fetch_cost_by_feature]
    - name: AnalyticsFacade
      methods: [get_usage_statistics, get_cost_statistics, get_status]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
