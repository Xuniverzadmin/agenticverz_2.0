# PIN-496: Logs Domain Canonical Consolidation

**Status:** COMPLETE
**Date:** 2026-01-31
**Domain:** logs
**Scope:** 36 files (18 L5_engines, 13 L6_drivers, 1 L5_support, 1 adapter, 3 __init__.py)

---

## Actions Taken

### 1. Naming Violations Fixed (8 renames)

| Old Name | New Name | Layer |
|----------|----------|-------|
| audit_ledger_service.py | audit_ledger_engine.py | L5 |
| audit_ledger_service_async.py | audit_ledger_driver.py | L6 |
| capture.py | capture_driver.py | L6 |
| idempotency.py | idempotency_driver.py | L6 |
| integrity.py | integrity_driver.py | L6 |
| job_execution.py | job_execution_driver.py | L6 |
| panel_consistency_checker.py | panel_consistency_driver.py | L6 |
| replay.py | replay_driver.py | L6 |

### 2. Header Corrections (2)

- `logs/__init__.py`: L4 → L5
- `logs/L5_schemas/__init__.py`: "Domain Services" → "Domain Schemas"

### 3. Import Path Fix (1)

- `panel_response_assembler.py`: relative import `.panel_consistency_checker` → absolute `app.hoc.cus.logs.L6_drivers.panel_consistency_driver`

### 4. Legacy Connections

None — domain is clean. No HOC→legacy or legacy→HOC imports found.

### 5. Cross-Domain Imports

None — domain is clean.

### 6. Duplicates

None. `audit_ledger_engine.py` (L5, sync) and `audit_ledger_driver.py` (L6, async) are a legitimate sync/async layer split.

---

## Artifacts

| Artifact | Path |
|----------|------|
| Literature | `literature/hoc_domain/logs/LOGS_CANONICAL_SOFTWARE_LITERATURE.md` |
| Tally Script | `scripts/ops/hoc_logs_tally.py` |
| PIN | This file |

## Tally Result

34/34 checks PASS.

## L4 Handler

`logs_handler.py` — 6 operations registered. No import updates required (renamed files not referenced by handler).

---

## Key File Distinction: evidence_report.py vs pdf_renderer.py

These two L5 engines both use reportlab to generate PDFs but serve **different purposes**:

### evidence_report.py — Incident Investigation Report
- **Purpose:** Deep forensic document for a single AI incident
- **Input:** Raw incident data (strings, dicts) — builds its own `IncidentEvidence` dataclass
- **Output:** Single 10-section legal-grade report (incident snapshot, executive summary, factual reconstruction, policy evaluation, decision timeline, replay verification, M23 cryptographic certificate, prevention proof, remediation, legal attestation)
- **Called via:** L4 `logs.evidence_report` → `generate_evidence_report()`
- **Caller chain:** L2 incident export endpoint → L4 → function
- **Customer use case:** "Show me the evidence report for incident X"
- **Audience:** Legal review, audit, hostile questioning

### pdf_renderer.py — Compliance Export PDFs
- **Purpose:** Render pre-assembled structured bundles to PDF for compliance/export
- **Input:** Structured bundle objects from `app.models.export_bundles` (ORM-backed)
- **Output:** Three distinct report types:
  1. `render_evidence_pdf(EvidenceBundle)` — audit trail PDF (trace steps, policy context, integrity hash)
  2. `render_soc2_pdf(SOC2Bundle)` — SOC2 compliance export (control mappings, attestation, compliance period)
  3. `render_executive_debrief_pdf(ExecutiveDebriefBundle)` — executive briefing (risk level, business impact, recommendations)
- **Called via:** L4 `logs.pdf` → `PDFRenderer.render_*()`
- **Caller chain:** L2 incidents API → L4 → PDFRenderer singleton
- **Customer use case:** "Export SOC2 report", "Generate executive debrief", "Download evidence bundle as PDF"
- **Audience:** Compliance team, executives, auditors

### NOT interchangeable
`evidence_report` is the deep investigation document for one incident. `pdf_renderer` is the export pipeline for pre-packaged bundles used across SOC2 audits, executive briefings, and evidence exports.
