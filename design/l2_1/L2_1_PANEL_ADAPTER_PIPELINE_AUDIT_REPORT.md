# L2.1 Panel Adapter Layer — HISAR/SDSR/AURORA Pipeline Audit Report

**Audit Date:** 2026-01-16
**Auditor:** Claude (Code-Verified Audit)
**Scope:** Panel Adapter Layer vs. actual pipeline implementations
**Method:** Code inspection, not documentation inference

---

## Executive Summary

**VERDICT: CRITICAL MISALIGNMENT**

The L2.1 Panel Adapter Layer creates a **parallel system** that does not integrate with the existing HISAR/SDSR/AURORA pipeline. This is a fundamental architectural gap that must be resolved before the Panel Adapter can be used in production.

| Category | Status | Severity |
|----------|--------|----------|
| HISAR Integration | ❌ NOT INTEGRATED | P0 |
| SDSR Observation Consumption | ❌ NOT IMPLEMENTED | P0 |
| AURORA Projection Alignment | ❌ CONFLICTING | P0 |
| Capability Registry Usage | ❌ NOT USED | P0 |
| UI Plan Authority | ❌ IGNORED | P0 |
| Intent YAML Integration | ❌ NOT IMPLEMENTED | P1 |
| State Model Alignment | ❌ DIFFERENT | P1 |
| Panel ID Alignment | ❌ MISMATCHED | P1 |
| Coherency Gate Alignment | ⚠️ DIFFERENT | P2 |

---

## GAP 1: Parallel Spec System (P0 — BLOCKING)

### Finding
The Panel Adapter creates its own specification files that duplicate/conflict with the canonical AURORA pipeline artifacts.

### Panel Adapter Creates:
```
design/l2_1/L2_1_PANEL_ADAPTER_SPEC.yaml      # Custom panel definitions
design/l2_1/L2_1_PANEL_DEPENDENCY_GRAPH.yaml  # Custom dependency graph
design/l2_1/L2_1_SLOT_DETERMINISM_MATRIX.csv  # Custom determinism rules
```

### Canonical Pipeline Uses (CODE-VERIFIED):
```
design/l2_1/intents/*.yaml                    # 200+ Intent YAMLs (L87-L199 of SDSR_UI_AURORA_compiler.py)
backend/AURORA_L2_CAPABILITY_REGISTRY/*.yaml  # 90+ Capability files (L105-L130)
design/l2_1/ui_plan.yaml                      # Canonical UI plan (L198-L218)
design/l2_1/ui_contract/ui_projection_lock.json  # Canonical output (L76-L79)
```

### Evidence
From `SDSR_UI_AURORA_compiler.py:L63-L79`:
```python
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
CAPABILITY_REGISTRY_DIR = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"
UI_PLAN_PATH = REPO_ROOT / "design/l2_1/ui_plan.yaml"
CANONICAL_PROJECTION_PATH = UI_CONTRACT_DIR / "ui_projection_lock.json"
```

### Impact
- Two separate sources of truth
- Panel definitions will diverge
- No automatic sync mechanism
- HISAR pipeline won't update Panel Adapter specs

### Resolution Required
Panel Adapter must consume existing AURORA artifacts, not define its own.

---

## GAP 2: No HISAR Pipeline Integration (P0 — BLOCKING)

### Finding
The Panel Adapter is not called anywhere in the HISAR execution chain.

### HISAR Phases (from `run_hisar.sh:L70-L91`):
```
Phase 0:   Snapshot Gate
Phase 0.1: Universe Validation (BLOCKING)
Phase 1:   Human Intent Validation
Phase 2:   Intent Specification
Phase 3:   Capability Declaration
Phase 3.5: Coherency Gate (BLOCKING)
Phase 4:   SDSR Verification
Phase 5:   Observation Application
Phase 5.5: Trust Evaluation
Phase 6:   Aurora Compilation         ← Produces ui_projection_lock.json
Phase 6.5: UI Plan Bind
Phase 7:   Projection Diff Guard (BLOCKING)
Phase 8:   Rendering                  ← Copies projection to public/
Phase 9:   Memory PIN Generation
```

### Panel Adapter Position
The Panel Adapter is not mentioned in any HISAR phase. It operates outside the governance chain.

### Evidence
From `run_hisar.sh`, the only projection output is from Aurora Compiler:
```bash
python3 "$TOOLS_DIR/aurora_coherency_check.py" ...
python3 "$TOOLS_DIR/aurora_sdsr_runner.py" ...
python3 "$TOOLS_DIR/aurora_apply_observation.py" ...
python3 "$ROOT_DIR/backend/aurora_l2/SDSR_UI_AURORA_compiler.py" ...
```

No reference to `ai_console_panel_adapter` or `panel_engine`.

### Impact
- Panel Adapter runs outside governance
- No coherency checks apply
- No SDSR verification
- No projection diff guard

### Resolution Required
Either:
1. Panel Adapter becomes a HISAR phase (e.g., Phase 6.1)
2. Panel Adapter consumes HISAR output (ui_projection_lock.json)

---

## GAP 3: Different State Models (P1)

### Finding
Panel Adapter uses a different state model than AURORA.

### AURORA 4-State Capability Model (from `SDSR_UI_AURORA_compiler.py:L85-L96`):
```python
CAPABILITY_BINDING_MAP = {
    "DISCOVERED": "DRAFT",      # Auto-seeded, action name exists → disabled
    "DECLARED": "DRAFT",        # Backend claims it exists → still disabled
    "OBSERVED": "BOUND",        # UI + SDSR confirmed behavior → enabled
    "TRUSTED": "BOUND",         # Fully governed, CI-enforced → enabled
    "DEPRECATED": "UNBOUND",    # No longer valid → hidden
}
```

### AURORA 5-State Panel Model (from `ui_plan.yaml:L19-L24`):
```yaml
panel_states:
  EMPTY: Slot reserved, panel not implemented
  UNBOUND: Intent exists, capability missing
  DRAFT: Capability declared, SDSR not observed
  BOUND: Capability observed (or trusted)
  DEFERRED: Explicit governance decision
```

### Panel Adapter Model (from `panel_types.py`):
```python
class SlotState(str, Enum):
    AVAILABLE = "available"     # No equivalent
    PARTIAL = "partial"         # No equivalent
    MISSING = "missing"         # Similar to EMPTY but different

class Authority(str, Enum):
    AFFIRMATIVE = "affirmative"   # Similar to BOUND
    NEGATIVE = "negative"         # No equivalent in AURORA
    INDETERMINATE = "indeterminate"  # Similar to UNBOUND
```

### Impact
- State semantics don't align
- UI can't consume Panel Adapter states consistently with AURORA projections
- No mapping between systems

### Resolution Required
Panel Adapter must use AURORA's 5-state panel model (EMPTY/UNBOUND/DRAFT/BOUND/DEFERRED).

---

## GAP 4: SDSR Observation Not Consumed (P0 — BLOCKING)

### Finding
Panel Adapter doesn't consume SDSR observations that prove capability status.

### SDSR Output Location (from `SDSR_output_emit_AURORA_L2.py`):
```python
OUTPUT_DIR = REPO_ROOT / "sdsr/observations"
# Files: SDSR_OBSERVATION_{scenario_id}.json
```

### SDSR Observation Structure (CODE-VERIFIED):
```python
{
    "scenario_id": "...",
    "status": "PASSED",
    "observation_class": "INFRASTRUCTURE|EFFECT",
    "capabilities_observed": [...],
    "observed_effects": [...],
    "ac_v2_evidence": {...}  # Baseline certification
}
```

### How AURORA Uses It (from `aurora_apply_observation.py`):
- Reads observation JSON
- Updates capability status: DECLARED → OBSERVED
- Updates intent YAML with verification trace
- Updates PDG allowlist

### Panel Adapter Usage
**NONE.** The `panel_signal_collector.py` makes HTTP calls but:
- Doesn't read SDSR observations
- Doesn't verify capability status before collection
- Doesn't check if capability is OBSERVED

### Impact
- Panel Adapter may call APIs for DECLARED (unverified) capabilities
- No proof that data is real
- Violates "SDSR is the ONLY source of truth" doctrine

### Resolution Required
Panel Adapter must:
1. Check capability status before signal collection
2. Only collect from OBSERVED/TRUSTED capabilities
3. Reject DISCOVERED/DECLARED capabilities

---

## GAP 5: ui_projection_lock.json Not Consumed (P0 — BLOCKING)

### Finding
Panel Adapter produces its own response envelope instead of consuming the canonical projection.

### Canonical Projection (from `SDSR_UI_AURORA_compiler.py:L76-L79`):
```python
CANONICAL_PROJECTION_PATH = UI_CONTRACT_DIR / "ui_projection_lock.json"
# This is the ONLY projection file. No others should exist.
```

### Projection Contract (from `ui_projection_lock.json:L37-L53`):
```json
"_contract": {
    "renderer_must_consume_only_this_file": true,
    "no_optional_fields": true,
    "ui_must_not_infer": true
}
```

### Panel Adapter Response (from `panel_response_assembler.py`):
Creates its own envelope with:
- `response_metadata`
- `panel`
- `verification`
- `request_context`

This is a **different format** than `ui_projection_lock.json`.

### Impact
- Two different response formats
- Frontend must handle both
- No single source of truth

### Resolution Required
Options:
1. Panel Adapter reads and enriches `ui_projection_lock.json`
2. Panel Adapter becomes a phase that modifies projection before copy to public/
3. Panel Adapter is deprecated in favor of projection-based rendering

---

## GAP 6: Capability Registry Not Used (P0 — BLOCKING)

### Finding
Panel Adapter doesn't read the AURORA capability registry.

### Capability Registry Location (CODE-VERIFIED):
```
backend/AURORA_L2_CAPABILITY_REGISTRY/AURORA_L2_CAPABILITY_*.yaml
```

### Example Capability (from `AURORA_L2_CAPABILITY_activity.summary.yaml`):
```yaml
capability_id: activity.summary
status: OBSERVED                    # 4-state model
endpoint: /api/v1/activity/summary
method: GET
coherency:
  last_checked: '2026-01-15T06:41:08Z'
  status: PASSED
observation:
  scenario_id: SDSR-ACT-LLM-COMP-O2-001
  invariants_passed: 3
```

### Panel Adapter Capability Definition (from `L2_1_PANEL_ADAPTER_SPEC.yaml`):
```yaml
slots:
  activity-snapshot:
    consumed_apis:
      - path: /api/v1/activity/summary
        method: GET
```

### Impact
- Panel Adapter doesn't know if capability is OBSERVED or just DECLARED
- May call unverified endpoints
- No coherency status check

### Resolution Required
Panel Adapter must read capability registry and respect status.

---

## GAP 7: UI Plan Not Used as Authority (P0 — BLOCKING)

### Finding
Panel Adapter ignores `ui_plan.yaml` which is the canonical authority.

### UI-as-Constraint Doctrine (from `SDSR_UI_AURORA_compiler.py:L71-L74`):
```python
# UI Plan Authority (CANONICAL SOURCE OF TRUTH)
# ui_plan.yaml is the HIGHEST authority per UI-as-Constraint doctrine
# Compiler reads this FIRST, then derives state mechanically
UI_PLAN_PATH = REPO_ROOT / "design/l2_1/ui_plan.yaml"
```

### UI Plan Structure (CODE-VERIFIED):
```yaml
status: LOCKED_UNTIL_TERMINAL_STATE
authority: design/l2_1/INTENT_LEDGER.md
domains:
- id: OVERVIEW
  subdomains:
  - id: SUMMARY
    topics:
    - id: HIGHLIGHTS
      panels:
      - panel_id: OVR-SUM-HL-O1
        state: BOUND
        intent_spec: design/l2_1/intents/AURORA_L2_INTENT_OVR-SUM-HL-O1.yaml
        expected_capability: overview.activity_snapshot
```

### Panel Adapter Approach
Defines its own panels in `L2_1_PANEL_ADAPTER_SPEC.yaml`, ignoring ui_plan.yaml.

### Impact
- Panel definitions may conflict
- Panel states not synchronized
- Authority hierarchy violated

### Resolution Required
Panel Adapter must read and respect ui_plan.yaml.

---

## GAP 8: Panel IDs Don't Match (P1)

### Finding
Panel Adapter uses different panel ID format than the actual system.

### Panel Adapter IDs (from `L2_1_PANEL_ADAPTER_SPEC.yaml`):
```yaml
panels:
  OVR-SUM-HL:    # No order suffix
    slots: ...
```

### Actual System IDs (from `ui_plan.yaml`):
```yaml
panels:
  - panel_id: OVR-SUM-HL-O1   # O1 = Order Level 1
  - panel_id: OVR-SUM-HL-O2   # O2 = Order Level 2
  - panel_id: OVR-SUM-HL-O3
  - panel_id: OVR-SUM-HL-O4
```

### Impact
- Panel lookup will fail
- IDs don't map between systems
- 82 actual panels vs. unknown Panel Adapter panels

### Resolution Required
Panel Adapter must use exact panel IDs from ui_plan.yaml.

---

## GAP 9: No Intent YAML Integration (P1)

### Finding
Panel Adapter doesn't read intent YAMLs that define panel behavior.

### Intent YAML Location:
```
design/l2_1/intents/AURORA_L2_INTENT_*.yaml
```

### Intent YAML Content (defines panel completely):
- Panel metadata (domain, subdomain, topic)
- Display properties (visible_by_default, expansion_mode)
- Data properties (read/write/download)
- Control properties (filtering, selection_mode, actions)
- SDSR observation trace

### Panel Adapter Approach
Defines its own slot specs in `L2_1_PANEL_ADAPTER_SPEC.yaml`.

### Impact
- Duplicate definitions
- Potential conflicts
- Manual sync required

---

## GAP 10: Coherency Gate Mismatch (P2)

### Finding
Panel Adapter has consistency rules but they don't align with HISAR coherency gates.

### HISAR Coherency Gates (from `aurora_coherency_check.py`):
```
COH-001: Panel ID exists in intent registry
COH-002: Intent YAML file exists
COH-003: Capability is declared
COH-004: Endpoint matches intent
COH-005: Domain alignment
...
COH-010: Reality check (endpoint actually exists)
```

### Panel Adapter Consistency Rules (from `panel_consistency_checker.py`):
```
CONS-001: active_incidents > 0 → attention_required = true
CONS-002: at_risk_runs > 0 → system_state = STRESSED
CONS-003: active_runs matches running counts
CONS-004: active_incidents > 0 → highest_severity ≠ NONE
```

### Impact
- Different things being checked
- Panel Adapter doesn't verify structural coherency
- HISAR gates not enforced

---

## Summary of Required Changes

### P0 — Must Fix Before Use

| Gap | Resolution |
|-----|------------|
| GAP 1 | Read existing artifacts, don't create parallel specs |
| GAP 2 | Integrate into HISAR as Phase 6.1 or consume projection |
| GAP 4 | Check capability status before signal collection |
| GAP 5 | Consume or enrich ui_projection_lock.json |
| GAP 6 | Read capability registry, respect status |
| GAP 7 | Use ui_plan.yaml as authority |

### P1 — Must Fix for Correctness

| Gap | Resolution |
|-----|------------|
| GAP 3 | Adopt AURORA's 5-state panel model |
| GAP 8 | Use exact panel IDs from ui_plan.yaml |
| GAP 9 | Read intent YAMLs for panel definitions |

### P2 — Should Fix for Alignment

| Gap | Resolution |
|-----|------------|
| GAP 10 | Align consistency rules with coherency gates |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HISAR PIPELINE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Phase 0-3.5: Intent → Capability → Coherency                       │
│       ↓                                                              │
│  Phase 4-5.5: SDSR Verification → Observation → Trust                │
│       ↓                                                              │
│  Phase 6: AURORA Compiler → ui_projection_lock.json                  │
│       ↓                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Phase 6.1: PANEL ADAPTER (NEW)                                  ││
│  │  • Reads ui_projection_lock.json                                ││
│  │  • Reads capability registry for status                         ││
│  │  • Enriches with verification signals                           ││
│  │  • Adds truth metadata (using AURORA state model)               ││
│  │  • Enforces determinism rules                                   ││
│  │  • Outputs enriched_projection.json                             ││
│  └─────────────────────────────────────────────────────────────────┘│
│       ↓                                                              │
│  Phase 7: Projection Diff Guard                                      │
│       ↓                                                              │
│  Phase 8: Rendering → public/projection/                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Conclusion

The L2.1 Panel Adapter Layer is a well-designed component in isolation, but it was built without awareness of the existing HISAR/SDSR/AURORA pipeline. The fundamental issue is that it creates a **parallel system** rather than integrating with the canonical pipeline.

**Before the Panel Adapter can be used:**
1. It must consume AURORA artifacts (ui_plan.yaml, capability registry, ui_projection_lock.json)
2. It must respect the 4-state capability model (DISCOVERED → DECLARED → OBSERVED → TRUSTED)
3. It must use the 5-state panel model (EMPTY/UNBOUND/DRAFT/BOUND/DEFERRED)
4. It must integrate into HISAR as a new phase

**The Panel Adapter concepts are valuable:**
- Truth metadata
- Verification signals
- Negative authority
- Determinism rules
- Time semantics

These should be integrated into the existing pipeline, not run as a parallel system.

---

*Report generated by code inspection. All findings verified against actual source files.*
