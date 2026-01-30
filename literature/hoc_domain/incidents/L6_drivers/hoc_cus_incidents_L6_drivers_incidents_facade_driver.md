# hoc_cus_incidents_L6_drivers_incidents_facade_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L6_drivers/incidents_facade_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Database operations for incidents facade - pure data access

## Intent

**Role:** Database operations for incidents facade - pure data access
**Reference:** PIN-470, INCIDENTS_PHASE2.5_IMPLEMENTATION_PLAN.md — Violation I.1
**Callers:** incidents_facade.py (L5)

## Purpose

Incidents Facade Driver (L6)

---

## Classes

### `IncidentSnapshot`
- **Docstring:** Raw incident data snapshot from database.
- **Class Variables:** id: str, tenant_id: str, lifecycle_state: Optional[str], severity: Optional[str], category: Optional[str], title: Optional[str], description: Optional[str], llm_run_id: Optional[str], source_run_id: Optional[str], cause_type: Optional[str], error_code: Optional[str], error_message: Optional[str], affected_agent_id: Optional[str], created_at: datetime, updated_at: Optional[datetime], resolved_at: Optional[datetime], is_synthetic: Optional[bool], synthetic_scenario_id: Optional[str]

### `IncidentListSnapshot`
- **Docstring:** Paginated list of incident snapshots.
- **Class Variables:** items: list[IncidentSnapshot], total: int

### `MetricsSnapshot`
- **Docstring:** Raw metrics aggregates from database.
- **Class Variables:** active_count: int, acked_count: int, resolved_count: int, total_count: int, avg_time_to_containment_ms: Optional[int], median_time_to_containment_ms: Optional[int], avg_time_to_resolution_ms: Optional[int], median_time_to_resolution_ms: Optional[int], sla_met_count: int, sla_breached_count: int, critical_count: int, high_count: int, medium_count: int, low_count: int

### `CostImpactRowSnapshot`
- **Docstring:** Single row from cost impact query.
- **Class Variables:** category: str, resolution_method: Optional[str], incident_count: int, total_cost_impact: float, avg_cost_impact: float

### `IncidentsFacadeDriver`
- **Docstring:** L6 Database driver for incidents facade.
- **Methods:** __init__, fetch_active_incidents, fetch_resolved_incidents, fetch_historical_incidents, fetch_incident_by_id, fetch_incidents_by_run, fetch_metrics_aggregates, fetch_cost_impact_data, _to_snapshot

## Attributes

- `__all__` (line 525)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.killswitch` |
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

incidents_facade.py (L5)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: IncidentSnapshot
      methods: []
    - name: IncidentListSnapshot
      methods: []
    - name: MetricsSnapshot
      methods: []
    - name: CostImpactRowSnapshot
      methods: []
    - name: IncidentsFacadeDriver
      methods: [fetch_active_incidents, fetch_resolved_incidents, fetch_historical_incidents, fetch_incident_by_id, fetch_incidents_by_run, fetch_metrics_aggregates, fetch_cost_impact_data]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
