# hoc_cus_incidents_L5_engines_postmortem_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/postmortem_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Extract learnings and post-mortem insights from resolved incidents

## Intent

**Role:** Extract learnings and post-mortem insights from resolved incidents
**Reference:** PIN-470, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** Incidents API (L2)

## Purpose

Post-Mortem Engine - L4 Domain Logic

---

## Classes

### `ResolutionSummary`
- **Docstring:** Summary of how an incident was resolved.
- **Class Variables:** incident_id: str, title: str, category: Optional[str], severity: str, resolution_method: Optional[str], time_to_resolution_ms: Optional[int], evidence_count: int, recovery_attempted: bool

### `LearningInsight`
- **Docstring:** A learning extracted from incident analysis.
- **Class Variables:** insight_type: str, description: str, confidence: float, supporting_incident_ids: list[str]

### `PostMortemResult`
- **Docstring:** Result of post-mortem analysis for an incident.
- **Class Variables:** incident_id: str, resolution_summary: ResolutionSummary, similar_incidents: list[ResolutionSummary], insights: list[LearningInsight], generated_at: datetime

### `CategoryLearnings`
- **Docstring:** Aggregated learnings for a category.
- **Class Variables:** category: str, total_incidents: int, resolved_count: int, avg_resolution_time_ms: Optional[float], common_resolution_methods: list[tuple[str, int]], recurrence_rate: float, insights: list[LearningInsight]

### `PostMortemService`
- **Docstring:** Extract learnings and post-mortem insights from incidents.
- **Methods:** __init__, get_incident_learnings, get_category_learnings, _get_resolution_summary, _find_similar_incidents, _extract_insights, _generate_category_insights

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.incidents.L6_drivers.postmortem_driver` |
| External | `sqlalchemy.ext.asyncio` |

## Callers

Incidents API (L2)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: ResolutionSummary
      methods: []
    - name: LearningInsight
      methods: []
    - name: PostMortemResult
      methods: []
    - name: CategoryLearnings
      methods: []
    - name: PostMortemService
      methods: [get_incident_learnings, get_category_learnings]
```

## PIN-520 Dead Code Rewiring Updates

- **Change Date:** 2026-02-03
- **Change Type:** Documentation — Dead Code Rewiring
- **Details:** Wired `avg_resolution_time_ms` parameter during PIN-520 phase 3 dead code rewiring
- **Impact:** No code changes; enhanced documentation of existing parameter

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
