# hoc_cus_incidents_L5_engines_hallucination_detector

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/incidents/L5_engines/hallucination_detector.py` |
| Layer | L5 — Domain Engine |
| Domain | incidents |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Detect potential hallucinations in LLM outputs (non-blocking)

## Intent

**Role:** Detect potential hallucinations in LLM outputs (non-blocking)
**Reference:** PIN-470, GAP-023, INV-002 (HALLU-INV-001)
**Callers:** worker/runner.py, services/incident_engine.py

## Purpose

Module: hallucination_detector
Purpose: Detect potential hallucinations in LLM outputs.

---

## Functions

### `create_detector_for_tenant(tenant_config: Optional[dict[str, Any]]) -> HallucinationDetector`
- **Async:** No
- **Docstring:** Create a detector configured for a specific tenant.  Args:
- **Calls:** HallucinationConfig, HallucinationDetector, get

## Classes

### `HallucinationType(str, Enum)`
- **Docstring:** Types of hallucination indicators.

### `HallucinationSeverity(str, Enum)`
- **Docstring:** Severity levels for hallucination detections.

### `HallucinationIndicator`
- **Docstring:** Individual hallucination indicator.
- **Methods:** to_dict
- **Class Variables:** indicator_type: HallucinationType, description: str, confidence: float, evidence: str, severity: HallucinationSeverity, context: Optional[dict[str, Any]]

### `HallucinationResult`
- **Docstring:** Result of hallucination detection.
- **Methods:** to_incident_data, _derive_severity
- **Class Variables:** detected: bool, overall_confidence: float, indicators: list[HallucinationIndicator], blocking_recommended: bool, blocking_customer_opted_in: bool, content_hash: str, checked_at: datetime

### `HallucinationConfig`
- **Docstring:** Configuration for hallucination detection.
- **Class Variables:** minimum_confidence: float, high_confidence_threshold: float, blocking_enabled: bool, blocking_threshold: float, detect_url_validity: bool, detect_citation_validity: bool, detect_contradictions: bool, detect_temporal_issues: bool, max_content_length: int, timeout_seconds: float

### `HallucinationDetector`
- **Docstring:** Hallucination detection service.
- **Methods:** __init__, detect, _detect_suspicious_urls, _detect_suspicious_citations, _detect_contradictions, _detect_temporal_issues, _hash_content

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

worker/runner.py, services/incident_engine.py

## Export Contract

```yaml
exports:
  functions:
    - name: create_detector_for_tenant
      signature: "create_detector_for_tenant(tenant_config: Optional[dict[str, Any]]) -> HallucinationDetector"
  classes:
    - name: HallucinationType
      methods: []
    - name: HallucinationSeverity
      methods: []
    - name: HallucinationIndicator
      methods: [to_dict]
    - name: HallucinationResult
      methods: [to_incident_data]
    - name: HallucinationConfig
      methods: []
    - name: HallucinationDetector
      methods: [detect]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
