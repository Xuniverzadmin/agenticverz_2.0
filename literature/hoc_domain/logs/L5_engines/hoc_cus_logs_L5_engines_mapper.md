# hoc_cus_logs_L5_engines_mapper

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/mapper.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Map incidents to relevant SOC2 controls

## Intent

**Role:** Map incidents to relevant SOC2 controls
**Reference:** PIN-470, GAP-025 (SOC2 Control Mapping)
**Callers:** services/export_bundle_service.py, api/incidents.py

## Purpose

Module: mapper
Purpose: Map incidents and evidence to SOC2 controls.

---

## Functions

### `get_control_mappings_for_incident(incident_category: str, incident_data: dict[str, Any]) -> list[dict[str, Any]]`
- **Async:** No
- **Docstring:** Get SOC2 control mappings for an incident (GAP-025 main entry point).  This is the primary function for obtaining SOC2 control mappings
- **Calls:** SOC2ControlMapper, map_incident_to_controls, to_dict

## Classes

### `SOC2ControlMapper`
- **Docstring:** Maps incidents to relevant SOC2 controls.
- **Methods:** __init__, map_incident_to_controls, _create_mapping, _determine_compliance_status, get_all_applicable_controls

## Attributes

- `CATEGORY_CONTROL_MAP: dict[str, list[str]]` (line 45)
- `EVIDENCE_TEMPLATES: dict[str, str]` (line 67)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `app.hoc.cus.hoc_spine.services.control_registry`, `app.hoc.cus.hoc_spine.services.time` |

## Callers

services/export_bundle_service.py, api/incidents.py

## Export Contract

```yaml
exports:
  functions:
    - name: get_control_mappings_for_incident
      signature: "get_control_mappings_for_incident(incident_category: str, incident_data: dict[str, Any]) -> list[dict[str, Any]]"
  classes:
    - name: SOC2ControlMapper
      methods: [map_incident_to_controls, get_all_applicable_controls]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
