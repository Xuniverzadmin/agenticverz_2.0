# hoc_cus_integrations_L5_engines_customer_incidents_adapter

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/integrations/L5_engines/external_adapters/customer_incidents_adapter.py` |
| Layer | L3 — Boundary Adapter |
| Domain | integrations |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Customer incidents boundary adapter (L2 → L3 → L4)

## Intent

**Role:** Customer incidents boundary adapter (L2 → L3 → L4)
**Reference:** PIN-280, PIN-281 (L2 Promotion Governance - PHASE 1 L3 Closure)
**Callers:** guard.py (L2) — to be wired

## Purpose

Customer Incidents Boundary Adapter (L3)

---

## Functions

### `_translate_severity(internal_severity: str) -> str`
- **Async:** No
- **Docstring:** Translate internal severity to calm customer vocabulary.
- **Calls:** get, lower

### `_translate_status(internal_status: str) -> str`
- **Async:** No
- **Docstring:** Translate internal status to customer vocabulary.
- **Calls:** get, lower

### `get_customer_incidents_adapter(session: Session) -> CustomerIncidentsAdapter`
- **Async:** No
- **Docstring:** Get a CustomerIncidentsAdapter instance.  Args:
- **Calls:** CustomerIncidentsAdapter

## Classes

### `CustomerIncidentSummary(BaseModel)`
- **Docstring:** Customer-safe incident summary for list view.
- **Class Variables:** id: str, title: str, severity: str, status: str, trigger_type: str, action_taken: Optional[str], cost_avoided_cents: int, calls_affected: int, started_at: str, ended_at: Optional[str]

### `CustomerIncidentEvent(BaseModel)`
- **Docstring:** Customer-safe timeline event.
- **Class Variables:** id: str, event_type: str, description: str, timestamp: str

### `CustomerIncidentDetail(BaseModel)`
- **Docstring:** Customer-safe incident detail.
- **Class Variables:** incident: CustomerIncidentSummary, timeline: List[CustomerIncidentEvent]

### `CustomerIncidentListResponse(BaseModel)`
- **Docstring:** Paginated customer incident list.
- **Class Variables:** items: List[CustomerIncidentSummary], total: int, page: int, page_size: int

### `CustomerIncidentsAdapter`
- **Docstring:** Boundary adapter for customer incident operations.
- **Methods:** __init__, list_incidents, get_incident, acknowledge_incident, resolve_incident

## Attributes

- `__all__` (line 390)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L5 Engine | `app.hoc.cus.incidents.L5_engines.incident_read_engine`, `app.hoc.cus.incidents.L5_engines.incident_write_engine` |
| Cross-Domain | `app.hoc.cus.incidents.L5_engines.incident_read_engine`, `app.hoc.cus.incidents.L5_engines.incident_write_engine` |
| External | `pydantic`, `sqlmodel` |

## Callers

guard.py (L2) — to be wired

## Export Contract

```yaml
exports:
  functions:
    - name: get_customer_incidents_adapter
      signature: "get_customer_incidents_adapter(session: Session) -> CustomerIncidentsAdapter"
  classes:
    - name: CustomerIncidentSummary
      methods: []
    - name: CustomerIncidentEvent
      methods: []
    - name: CustomerIncidentDetail
      methods: []
    - name: CustomerIncidentListResponse
      methods: []
    - name: CustomerIncidentsAdapter
      methods: [list_incidents, get_incident, acknowledge_incident, resolve_incident]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
