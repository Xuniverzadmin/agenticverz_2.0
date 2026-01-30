# hoc_cus_incidents_L6_drivers_incident_pattern_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L6_drivers/incident_pattern_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Data access for incident pattern detection operations (async)

## Intent

**Role:** Data access for incident pattern detection operations (async)
**Reference:** PIN-470, PIN-468, PHASE2_EXTRACTION_PROTOCOL.md
**Callers:** IncidentPatternEngine (L5)

## Purpose

Incident Pattern Driver (L6)

---

## Functions

### `get_incident_pattern_driver(session: AsyncSession) -> IncidentPatternDriver`
- **Async:** No
- **Docstring:** Factory function to get IncidentPatternDriver instance.
- **Calls:** IncidentPatternDriver

## Classes

### `IncidentPatternDriver`
- **Docstring:** L6 driver for incident pattern detection operations (async).
- **Methods:** __init__, fetch_incidents_count, fetch_category_clusters, fetch_severity_spikes, fetch_cascade_failures

## Attributes

- `logger` (line 70)
- `__all__` (line 252)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

IncidentPatternEngine (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_incident_pattern_driver
      signature: "get_incident_pattern_driver(session: AsyncSession) -> IncidentPatternDriver"
  classes:
    - name: IncidentPatternDriver
      methods: [fetch_incidents_count, fetch_category_clusters, fetch_severity_spikes, fetch_cascade_failures]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
