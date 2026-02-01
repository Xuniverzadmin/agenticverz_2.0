# export_bundle_adapter.py

**Path:** `backend/app/hoc/cus/hoc_spine/consequences/adapters/export_bundle_adapter.py`  
**Layer:** L4 — HOC Spine (Adapter)  
**Component:** Consequences

---

## Placement Card

```
File:            export_bundle_adapter.py
Lives in:        consequences/
Role:            Consequences
Inbound:         L2 API routes
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Export Bundle Adapter (L2)
Violations:      none
```

## Purpose

Export Bundle Adapter (L2)

Generates structured export bundles from incidents, runs, and traces
for evidence export, SOC2 compliance, and executive debriefs.

ADAPTER CONTRACT:
- NO sqlalchemy imports
- NO direct database queries
- Delegates all data access to L6 ExportBundleStore

## Import Analysis

**L7 Models:**
- `app.models.export_bundles`

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `get_export_bundle_adapter() -> ExportBundleAdapter`

Get or create ExportBundleAdapter singleton.

## Classes

### `ExportBundleAdapter`

Adapter for generating export bundles.

Translates between API requests and L6 store,
composing bundle structures from raw data.

#### Methods

- `__init__(store: Optional[ExportBundleStore])` — Initialize with optional store (for testing).
- `async create_evidence_bundle(incident_id: str, exported_by: str, export_reason: Optional[str], include_raw_steps: bool) -> EvidenceBundle` — Create evidence bundle from incident.
- `async create_soc2_bundle(incident_id: str, exported_by: str, compliance_period_start: Optional[datetime], compliance_period_end: Optional[datetime], auditor_notes: Optional[str]) -> SOC2Bundle` — Create SOC2-compliant bundle.
- `async create_executive_debrief(incident_id: str, prepared_for: Optional[str], prepared_by: str) -> ExecutiveDebriefBundle` — Create executive summary (non-technical).
- `_compute_bundle_hash(bundle: EvidenceBundle) -> str` — Compute SHA256 hash of bundle for integrity verification.
- `_generate_attestation(bundle: EvidenceBundle) -> str` — Generate SOC2 attestation statement.
- `_assess_risk_level(incident: IncidentSnapshot) -> str` — Assess risk level for executive summary.
- `_generate_incident_summary(incident: IncidentSnapshot, run: Optional[RunSnapshot]) -> str` — Generate non-technical incident summary.
- `_assess_business_impact(incident: IncidentSnapshot, run: Optional[RunSnapshot]) -> str` — Assess business impact for executive summary.
- `_generate_recommendations(incident: IncidentSnapshot, run: Optional[RunSnapshot]) -> list[str]` — Generate recommended actions.

## Domain Usage

**Callers:** L2 API routes

## Export Contract

```yaml
exports:
  functions:
    - name: get_export_bundle_adapter
      signature: "get_export_bundle_adapter() -> ExportBundleAdapter"
      consumers: ["orchestrator"]
  classes:
    - name: ExportBundleAdapter
      methods:
        - create_evidence_bundle
        - create_soc2_bundle
        - create_executive_debrief
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: ['app.models.export_bundles']
    external: []
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

