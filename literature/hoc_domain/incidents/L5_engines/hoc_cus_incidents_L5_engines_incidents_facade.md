# hoc_cus_incidents_L5_engines_incidents_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/incidents_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Incidents domain facade - unified entry point for incident management operations

## Intent

**Role:** Incidents domain facade - unified entry point for incident management operations
**Reference:** PIN-470, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
**Callers:** L2 incidents API (incidents.py)

## Purpose

Incidents Domain Facade (L5)

---

## Functions

### `get_incidents_facade() -> IncidentsFacade`
- **Async:** No
- **Docstring:** Get the singleton IncidentsFacade instance.
- **Calls:** IncidentsFacade

## Classes

### `IncidentSummaryResult`
- **Docstring:** Incident summary for list view (O2).
- **Class Variables:** incident_id: str, tenant_id: str, lifecycle_state: str, severity: str, category: str, title: str, description: Optional[str], llm_run_id: Optional[str], cause_type: str, error_code: Optional[str], error_message: Optional[str], created_at: datetime, resolved_at: Optional[datetime], is_synthetic: bool, policy_ref: Optional[str], violation_ref: Optional[str]

### `PaginationResult`
- **Docstring:** Pagination metadata.
- **Class Variables:** limit: int, offset: int, next_offset: Optional[int]

### `IncidentListResult`
- **Docstring:** Incidents list response.
- **Class Variables:** items: list[IncidentSummaryResult], total: int, has_more: bool, filters_applied: dict[str, Any], pagination: PaginationResult

### `IncidentDetailResult`
- **Docstring:** Incident detail response (O3).
- **Class Variables:** incident_id: str, tenant_id: str, lifecycle_state: str, severity: str, category: str, title: str, description: Optional[str], llm_run_id: Optional[str], source_run_id: Optional[str], cause_type: str, error_code: Optional[str], error_message: Optional[str], affected_agent_id: Optional[str], created_at: datetime, updated_at: Optional[datetime], resolved_at: Optional[datetime], is_synthetic: bool, synthetic_scenario_id: Optional[str], policy_id: Optional[str], policy_ref: Optional[str], violation_id: Optional[str], violation_ref: Optional[str], lesson_ref: Optional[str]

### `IncidentsByRunResult`
- **Docstring:** Incidents by run response.
- **Class Variables:** run_id: str, incidents: list[IncidentSummaryResult], total: int

### `PatternMatchResult`
- **Docstring:** A detected incident pattern.
- **Class Variables:** pattern_type: str, dimension: str, count: int, incident_ids: list[str], confidence: float

### `PatternDetectionResult`
- **Docstring:** Pattern detection response.
- **Class Variables:** patterns: list[PatternMatchResult], window_hours: int, window_start: datetime, window_end: datetime, incidents_analyzed: int

### `RecurrenceGroupResult`
- **Docstring:** A group of recurring incidents.
- **Class Variables:** category: str, resolution_method: Optional[str], total_occurrences: int, distinct_days: int, occurrences_per_day: float, first_occurrence: datetime, last_occurrence: datetime, recent_incident_ids: list[str]

### `RecurrenceAnalysisResult`
- **Docstring:** Recurrence analysis response.
- **Class Variables:** groups: list[RecurrenceGroupResult], baseline_days: int, total_recurring: int, generated_at: datetime

### `CostImpactSummaryResult`
- **Docstring:** Cost impact summary for an incident category.
- **Class Variables:** category: str, incident_count: int, total_cost_impact: float, avg_cost_impact: float, resolution_method: Optional[str]

### `CostImpactResult`
- **Docstring:** Cost impact analysis response.
- **Class Variables:** summaries: list[CostImpactSummaryResult], total_cost_impact: float, baseline_days: int, generated_at: datetime

### `IncidentMetricsResult`
- **Docstring:** Incident metrics response.
- **Class Variables:** active_count: int, acked_count: int, resolved_count: int, total_count: int, avg_time_to_containment_ms: Optional[int], median_time_to_containment_ms: Optional[int], avg_time_to_resolution_ms: Optional[int], median_time_to_resolution_ms: Optional[int], sla_met_count: int, sla_breached_count: int, sla_compliance_rate: Optional[float], critical_count: int, high_count: int, medium_count: int, low_count: int, window_days: int, generated_at: datetime

### `HistoricalTrendDataPointResult`
- **Docstring:** A single data point in a historical trend.
- **Class Variables:** period: str, incident_count: int, resolved_count: int, avg_resolution_time_ms: Optional[int]

### `HistoricalTrendResult`
- **Docstring:** Historical trend response.
- **Class Variables:** data_points: list[HistoricalTrendDataPointResult], granularity: str, window_days: int, total_incidents: int, generated_at: datetime

### `HistoricalDistributionEntryResult`
- **Docstring:** A single entry in the distribution.
- **Class Variables:** dimension: str, value: str, count: int, percentage: float

### `HistoricalDistributionResult`
- **Docstring:** Historical distribution response.
- **Class Variables:** by_category: list[HistoricalDistributionEntryResult], by_severity: list[HistoricalDistributionEntryResult], by_cause_type: list[HistoricalDistributionEntryResult], window_days: int, total_incidents: int, generated_at: datetime

### `CostTrendDataPointResult`
- **Docstring:** A single data point in the cost trend.
- **Class Variables:** period: str, total_cost: float, incident_count: int, avg_cost_per_incident: float

### `CostTrendResult`
- **Docstring:** Cost trend response.
- **Class Variables:** data_points: list[CostTrendDataPointResult], granularity: str, window_days: int, total_cost: float, total_incidents: int, generated_at: datetime

### `LearningInsightResult`
- **Docstring:** A learning insight from incident analysis.
- **Class Variables:** insight_type: str, description: str, confidence: float, supporting_incident_ids: list[str]

### `ResolutionSummaryResult`
- **Docstring:** Summary of incident resolution.
- **Class Variables:** incident_id: str, title: str, category: Optional[str], severity: str, resolution_method: Optional[str], time_to_resolution_ms: Optional[int], evidence_count: int, recovery_attempted: bool

### `LearningsResult`
- **Docstring:** Incident learnings response.
- **Class Variables:** incident_id: str, resolution_summary: ResolutionSummaryResult, similar_incidents: list[ResolutionSummaryResult], insights: list[LearningInsightResult], generated_at: datetime

### `IncidentsFacade`
- **Docstring:** Unified facade for incident management.
- **Methods:** list_active_incidents, list_resolved_incidents, list_historical_incidents, get_incident_detail, get_incidents_for_run, get_metrics, analyze_cost_impact, _snapshot_to_summary, detect_patterns, analyze_recurrence, get_incident_learnings

## Attributes

- `_facade_instance: IncidentsFacade | None` (line 939)
- `__all__` (line 950)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.incidents.L5_engines.incident_pattern_engine`, `app.hoc.cus.incidents.L5_engines.postmortem_engine`, `app.hoc.cus.incidents.L5_engines.recurrence_analysis_engine` |
| L6 Driver | `app.hoc.cus.incidents.L6_drivers.incidents_facade_driver` |
| External | `sqlalchemy.ext.asyncio` |

## Callers

L2 incidents API (incidents.py)

## Export Contract

```yaml
exports:
  functions:
    - name: get_incidents_facade
      signature: "get_incidents_facade() -> IncidentsFacade"
  classes:
    - name: IncidentSummaryResult
      methods: []
    - name: PaginationResult
      methods: []
    - name: IncidentListResult
      methods: []
    - name: IncidentDetailResult
      methods: []
    - name: IncidentsByRunResult
      methods: []
    - name: PatternMatchResult
      methods: []
    - name: PatternDetectionResult
      methods: []
    - name: RecurrenceGroupResult
      methods: []
    - name: RecurrenceAnalysisResult
      methods: []
    - name: CostImpactSummaryResult
      methods: []
    - name: CostImpactResult
      methods: []
    - name: IncidentMetricsResult
      methods: []
    - name: HistoricalTrendDataPointResult
      methods: []
    - name: HistoricalTrendResult
      methods: []
    - name: HistoricalDistributionEntryResult
      methods: []
    - name: HistoricalDistributionResult
      methods: []
    - name: CostTrendDataPointResult
      methods: []
    - name: CostTrendResult
      methods: []
    - name: LearningInsightResult
      methods: []
    - name: ResolutionSummaryResult
      methods: []
    - name: LearningsResult
      methods: []
    - name: IncidentsFacade
      methods: [list_active_incidents, list_resolved_incidents, list_historical_incidents, get_incident_detail, get_incidents_for_run, get_metrics, analyze_cost_impact, detect_patterns, analyze_recurrence, get_incident_learnings]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
