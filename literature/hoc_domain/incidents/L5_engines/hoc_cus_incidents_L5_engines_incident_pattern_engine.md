# hoc_cus_incidents_L5_engines_incident_pattern_engine

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/incident_pattern_engine.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Detect structural patterns across incidents

## Intent

**Role:** Detect structural patterns across incidents
**Reference:** PIN-470, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** Incidents API (L2)

## Purpose

Incident Pattern Engine - L4 Domain Logic

---

## Classes

### `PatternMatch`
- **Docstring:** A detected incident pattern.
- **Class Variables:** pattern_type: str, dimension: str, count: int, incident_ids: list[str], confidence: float

### `PatternResult`
- **Docstring:** Result of pattern detection.
- **Class Variables:** patterns: list[PatternMatch], window_start: datetime, window_end: datetime, incidents_analyzed: int

### `IncidentPatternService`
- **Docstring:** Detect structural patterns across incidents.
- **Methods:** __init__, detect_patterns, _detect_category_clusters, _detect_severity_spikes, _detect_cascade_failures

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.incidents.L6_drivers.incident_pattern_driver` |
| External | `app.hoc.cus.hoc_spine.services.time`, `sqlalchemy.ext.asyncio` |

## Callers

Incidents API (L2)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: PatternMatch
      methods: []
    - name: PatternResult
      methods: []
    - name: IncidentPatternService
      methods: [detect_patterns]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
