# hoc_cus_logs_L5_engines_evidence_report

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/logs/L5_engines/evidence_report.py` |
| Layer | L5 — Domain Engine |
| Domain | logs |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Evidence report generator - Legal-grade PDF export

## Intent

**Role:** Evidence report generator - Legal-grade PDF export
**Reference:** PIN-470, PIN-240
**Callers:** guard.py (incident export endpoint)

## Purpose

Evidence Report Generator - Legal-Grade PDF Export

---

## Functions

### `generate_evidence_report(incident_id: str, tenant_id: str, tenant_name: str, user_id: str, product_name: str, model_id: str, timestamp: str, user_input: str, context_data: Dict[str, Any], ai_output: str, policy_results: List[Dict[str, Any]], timeline_events: List[Dict[str, Any]], replay_result: Optional[Dict[str, Any]], prevention_result: Optional[Dict[str, Any]], root_cause: str, impact_assessment: Optional[List[str]], certificate: Optional[Dict[str, Any]], severity: str, status: str, is_demo: bool) -> bytes`
- **Async:** No
- **Docstring:** Convenience function to generate an evidence report.  Returns:
- **Calls:** CertificateEvidence, EvidenceReportGenerator, IncidentEvidence, generate, get

## Classes

### `CertificateEvidence`
- **Docstring:** M23: Certificate data for cryptographic proof.
- **Class Variables:** certificate_id: str, certificate_type: str, issued_at: str, valid_until: str, validation_passed: bool, signature: str, pem_format: str, determinism_level: str, match_achieved: str, policies_passed: int, policies_total: int

### `IncidentEvidence`
- **Docstring:** Evidence data for an incident.
- **Class Variables:** incident_id: str, tenant_id: str, tenant_name: str, user_id: str, product_name: str, model_id: str, timestamp: str, user_input: str, context_data: Dict[str, Any], ai_output: str, policy_results: List[Dict[str, Any]], timeline_events: List[Dict[str, Any]], replay_result: Optional[Dict[str, Any]], prevention_result: Optional[Dict[str, Any]], root_cause: str, impact_assessment: List[str], certificate: Optional[CertificateEvidence], severity: str, status: str

### `EvidenceReportGenerator`
- **Docstring:** Generates legal-grade PDF evidence reports.
- **Methods:** __init__, _setup_custom_styles, generate, _add_footer, _build_incident_snapshot, _build_cover_page, _build_executive_summary, _build_factual_reconstruction, _build_policy_evaluation, _build_decision_timeline, _build_replay_verification, _build_certificate_section, _build_prevention_proof, _build_remediation, _build_legal_attestation, _compute_hash, _compute_report_hash

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `reportlab.lib`, `reportlab.lib.enums`, `reportlab.lib.pagesizes`, `reportlab.lib.styles`, `reportlab.lib.units`, `reportlab.platypus` |

## Callers

guard.py (incident export endpoint)

## Export Contract

```yaml
exports:
  functions:
    - name: generate_evidence_report
      signature: "generate_evidence_report(incident_id: str, tenant_id: str, tenant_name: str, user_id: str, product_name: str, model_id: str, timestamp: str, user_input: str, context_data: Dict[str, Any], ai_output: str, policy_results: List[Dict[str, Any]], timeline_events: List[Dict[str, Any]], replay_result: Optional[Dict[str, Any]], prevention_result: Optional[Dict[str, Any]], root_cause: str, impact_assessment: Optional[List[str]], certificate: Optional[Dict[str, Any]], severity: str, status: str, is_demo: bool) -> bytes"
  classes:
    - name: CertificateEvidence
      methods: []
    - name: IncidentEvidence
      methods: []
    - name: EvidenceReportGenerator
      methods: [generate]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
