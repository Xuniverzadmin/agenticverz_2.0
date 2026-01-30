# hoc_models_export_bundles

| Field | Value |
|-------|-------|
| Path | `backend/app/models/export_bundles.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Structured export bundle models for SOC2, evidence, and executive debrief

## Intent

**Role:** Structured export bundle models for SOC2, evidence, and executive debrief
**Reference:** BACKEND_REMEDIATION_PLAN.md GAP-008
**Callers:** services/export_bundle_service.py, services/pdf_renderer.py

## Purpose

Export Bundle Models

---

## Functions

### `utc_now() -> datetime`
- **Async:** No
- **Docstring:** Return timezone-aware UTC datetime.
- **Calls:** now

### `generate_bundle_id(prefix: str) -> str`
- **Async:** No
- **Docstring:** Generate unique bundle ID.
- **Calls:** uuid4

## Classes

### `TraceStepEvidence(BaseModel)`
- **Docstring:** Single step in trace with evidence markers.
- **Class Variables:** step_index: int, timestamp: datetime, step_type: str, tokens: int, cost_cents: float, duration_ms: float, status: str, is_inflection: bool, content_hash: Optional[str]

### `PolicyContext(BaseModel)`
- **Docstring:** Policy information captured in evidence bundle.
- **Class Variables:** policy_snapshot_id: str, active_policies: list[dict[str, Any]], violated_policy_id: Optional[str], violated_policy_name: Optional[str], violation_type: Optional[str], threshold_value: Optional[str], actual_value: Optional[str]

### `EvidenceBundle(BaseModel)`
- **Docstring:** Generic evidence bundle for any export.
- **Class Variables:** bundle_id: str, bundle_type: str, created_at: datetime, run_id: str, incident_id: Optional[str], trace_id: str, tenant_id: str, agent_id: Optional[str], policy_context: PolicyContext, violation_step_index: Optional[int], violation_timestamp: Optional[datetime], steps: list[TraceStepEvidence], total_steps: int, total_duration_ms: float, total_tokens: int, total_cost_cents: float, run_goal: Optional[str], run_started_at: Optional[datetime], run_completed_at: Optional[datetime], termination_reason: Optional[str], exported_by: str, export_reason: Optional[str], content_hash: Optional[str]

### `SOC2ControlMapping(BaseModel)`
- **Docstring:** SOC2 control objective mapping for compliance.
- **Class Variables:** control_id: str, control_name: str, control_description: str, evidence_provided: str, compliance_status: str

### `SOC2Bundle(EvidenceBundle)`
- **Docstring:** SOC2-specific export bundle.
- **Class Variables:** bundle_type: str, bundle_id: str, control_mappings: list[SOC2ControlMapping], attestation_statement: str, compliance_period_start: Optional[datetime], compliance_period_end: Optional[datetime], auditor_notes: Optional[str], review_status: str, reviewed_by: Optional[str], reviewed_at: Optional[datetime], criteria_covered: list[str]

### `ExecutiveDebriefBundle(BaseModel)`
- **Docstring:** Executive summary bundle (non-technical).
- **Class Variables:** bundle_id: str, bundle_type: str, created_at: datetime, incident_summary: str, business_impact: str, risk_level: str, run_id: str, incident_id: str, tenant_id: str, policy_violated: str, violation_time: datetime, detection_time: datetime, recommended_actions: list[str], remediation_status: str, remediation_notes: Optional[str], time_to_detect_seconds: int, time_to_contain_seconds: Optional[int], cost_incurred_cents: int, cost_prevented_cents: Optional[int], prepared_for: Optional[str], prepared_by: str, classification: str

### `ExportBundleRequest(BaseModel)`
- **Docstring:** Request to create an export bundle.
- **Class Variables:** incident_id: str, bundle_type: str, export_reason: Optional[str], include_raw_steps: bool, prepared_for: Optional[str]

### `ExportBundleResponse(BaseModel)`
- **Docstring:** Response containing export bundle metadata.
- **Class Variables:** bundle_id: str, bundle_type: str, created_at: datetime, incident_id: Optional[str], run_id: str, download_url: Optional[str], status: str

## Attributes

- `DEFAULT_SOC2_CONTROLS` (line 242)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `pydantic` |

## Callers

services/export_bundle_service.py, services/pdf_renderer.py

## Export Contract

```yaml
exports:
  functions:
    - name: utc_now
      signature: "utc_now() -> datetime"
    - name: generate_bundle_id
      signature: "generate_bundle_id(prefix: str) -> str"
  classes:
    - name: TraceStepEvidence
      methods: []
    - name: PolicyContext
      methods: []
    - name: EvidenceBundle
      methods: []
    - name: SOC2ControlMapping
      methods: []
    - name: SOC2Bundle
      methods: []
    - name: ExecutiveDebriefBundle
      methods: []
    - name: ExportBundleRequest
      methods: []
    - name: ExportBundleResponse
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
