# hoc_cus_logs_L5_engines_pdf_renderer

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/pdf_renderer.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Render export bundles to PDF format

## Intent

**Role:** Render export bundles to PDF format
**Reference:** PIN-470, BACKEND_REMEDIATION_PLAN.md GAP-004, GAP-005
**Callers:** api/incidents.py

## Purpose

PDF Renderer Service

---

## Functions

### `get_pdf_renderer() -> PDFRenderer`
- **Async:** No
- **Docstring:** Get or create PDFRenderer singleton.
- **Calls:** PDFRenderer

## Classes

### `PDFRenderer`
- **Docstring:** Render export bundles to PDF format.
- **Methods:** __init__, _setup_styles, render_evidence_pdf, render_soc2_pdf, render_executive_debrief_pdf, _build_evidence_cover, _build_evidence_summary, _build_trace_timeline, _build_policy_section, _build_integrity_section, _build_soc2_cover, _build_control_mappings, _build_attestation, _build_exec_cover, _build_exec_summary, _build_recommendations, _build_exec_metrics

## Attributes

- `logger` (line 60)
- `_pdf_renderer: Optional[PDFRenderer]` (line 679)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.export_bundles` |
| External | `reportlab.lib`, `reportlab.lib.enums`, `reportlab.lib.pagesizes`, `reportlab.lib.styles`, `reportlab.lib.units`, `reportlab.platypus` |

## Callers

api/incidents.py

## Export Contract

```yaml
exports:
  functions:
    - name: get_pdf_renderer
      signature: "get_pdf_renderer() -> PDFRenderer"
  classes:
    - name: PDFRenderer
      methods: [render_evidence_pdf, render_soc2_pdf, render_executive_debrief_pdf]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
