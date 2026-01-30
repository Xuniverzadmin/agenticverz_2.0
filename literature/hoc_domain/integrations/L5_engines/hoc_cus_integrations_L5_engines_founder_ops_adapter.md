# hoc_cus_integrations_L5_engines_founder_ops_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/founder_ops_adapter.py` |
| Layer | L3 — Boundary Adapter |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Translate OpsIncident domain models to Founder-facing views

## Intent

**Role:** Translate OpsIncident domain models to Founder-facing views
**Reference:** PIN-264 (Phase-S L3 Adapter)
**Callers:** ops.py (L2)

## Purpose

Founder Ops Adapter (L3)

---

## Classes

### `FounderIncidentSummaryView`
- **Docstring:** Founder-facing incident summary.
- **Class Variables:** incident_id: str, title: str, severity: str, component: str, occurrence_count: int, first_seen: str, last_seen: str, affected_runs: int, affected_agents: int, is_resolved: bool

### `FounderIncidentsSummaryResponse`
- **Docstring:** Response for GET /ops/incidents/summary.
- **Class Variables:** total_incidents: int, by_severity: dict, recent_incidents: List[FounderIncidentSummaryView], window_start: str, window_end: str

### `FounderOpsAdapter`
- **Docstring:** Boundary adapter for Founder Ops incident views.
- **Methods:** to_summary_view, to_summary_response

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.hoc.fdr.ops.schemas.ops_domain_models` |

## Callers

ops.py (L2)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: FounderIncidentSummaryView
      methods: []
    - name: FounderIncidentsSummaryResponse
      methods: []
    - name: FounderOpsAdapter
      methods: [to_summary_view, to_summary_response]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
