# hoc_cus_incidents_L6_drivers_export_bundle_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L6_drivers/export_bundle_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Generate structured export bundles from incidents and traces

## Intent

**Role:** Generate structured export bundles from incidents and traces
**Reference:** PIN-470, BACKEND_REMEDIATION_PLAN.md GAP-004, GAP-005, GAP-008
**Callers:** api/incidents.py

## Purpose

Export Bundle Service

---

## Functions

### `get_export_bundle_service() -> ExportBundleService`
- **Async:** No
- **Docstring:** Get or create ExportBundleService singleton.
- **Calls:** ExportBundleService

## Classes

### `ExportBundleService`
- **Docstring:** Generate structured export bundles from incidents/traces.
- **Methods:** __init__, trace_store, create_evidence_bundle, create_soc2_bundle, create_executive_debrief, _compute_bundle_hash, _generate_attestation, _assess_risk_level, _generate_incident_summary, _assess_business_impact, _generate_recommendations

## Attributes

- `logger` (line 56)
- `_export_bundle_service: Optional[ExportBundleService]` (line 413)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.export_bundles` |
| External | `app.db`, `app.traces.store`, `sqlmodel` |

## Callers

api/incidents.py

## Export Contract

```yaml
exports:
  functions:
    - name: get_export_bundle_service
      signature: "get_export_bundle_service() -> ExportBundleService"
  classes:
    - name: ExportBundleService
      methods: [trace_store, create_evidence_bundle, create_soc2_bundle, create_executive_debrief]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
