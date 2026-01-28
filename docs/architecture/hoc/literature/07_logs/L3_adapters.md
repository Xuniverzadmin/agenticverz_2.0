# Logs — L3 Adapters (1 files)

**Domain:** logs  
**Layer:** L3_adapters  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

---

## export_bundle_adapter.py
**Path:** `backend/app/hoc/cus/logs/L3_adapters/export_bundle_adapter.py`  
**Layer:** L3_adapters | **Domain:** logs | **Lines:** 422

**Docstring:** Export Bundle Adapter (L3)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ExportBundleAdapter` | __init__, create_evidence_bundle, create_soc2_bundle, create_executive_debrief, _compute_bundle_hash, _generate_attestation, _assess_risk_level, _generate_incident_summary (+2 more) | L3 Adapter for generating export bundles. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_export_bundle_adapter` | `() -> ExportBundleAdapter` | no | Get or create ExportBundleAdapter singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `datetime` | datetime, timezone | no |
| `typing` | Optional | no |
| `app.hoc.cus.logs.L6_drivers.export_bundle_store` | ExportBundleStore, IncidentSnapshot, RunSnapshot, TraceSummarySnapshot, TraceStepSnapshot (+1) | no |
| `app.models.export_bundles` | DEFAULT_SOC2_CONTROLS, EvidenceBundle, ExecutiveDebriefBundle, PolicyContext, SOC2Bundle (+1) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Translation + aggregation ONLY — no state mutation, no retries, no policy decisions

**SHOULD call:** L4_runtime, L5_engines
**MUST NOT call:** L2_api, L6_drivers, L7_models
**Called by:** L2_api

### Violations
| Import | Rule Broken | Required Fix | Line |
|--------|-------------|-------------|------|
| `from app.models.export_bundles import DEFAULT_SOC2_CONTROLS, EvidenceBundle, ExecutiveDebriefBundle, PolicyContext, SOC2Bundle, TraceStepEvidence` | L3 MUST NOT import L7 models | Use L5 schemas for data contracts | 49 |

### __all__ Exports
`ExportBundleAdapter`, `get_export_bundle_adapter`

---
