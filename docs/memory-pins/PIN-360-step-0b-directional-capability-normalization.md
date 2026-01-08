# PIN-360: STEP 0B — Directional Capability Normalization

**Status:** ✅ COMPLETE
**Created:** 2026-01-08
**Completed:** 2026-01-08
**Category:** Governance / Capability Intelligence
**Scope:** All 21 FIRST_CLASS + 20 SUBSTRATE Capabilities
**Prerequisites:** PIN-329 (Capability Promotion & Merge Report)

---

## Objective

STEP 0B exists to answer one question only:

> "Given everything we claim about a capability, what do we tentatively believe about its nature — without binding, exposing, or rejecting it?"

It produces **directional truth**, not operational truth.

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| FIRST_CLASS capabilities | 21 | PROCESSED |
| SUBSTRATE capabilities | 20 | PROCESSED |
| Total capabilities | 41 | COMPLETE |
| Script implemented | YES | COMPLETE |
| Directional metadata generated | YES | COMPLETE |

### Trust Weight Distribution

| Level | Count | Percentage |
|-------|-------|------------|
| HIGH | 7 | 17% |
| MEDIUM | 27 | 66% |
| LOW | 7 | 17% |

### Console Scope Distribution

| Scope | Count |
|-------|-------|
| CUSTOMER | 7 |
| FOUNDER | 3 |
| SDK | 3 |
| NONE | 28 |

### Exposure Type Distribution

| Type | Count |
|------|-------|
| UI | 9 |
| API | 11 |
| SDK | 3 |
| CLI | 1 |
| INTERNAL | 17 |

### PIN-329 Coverage

**34/41 capabilities** (82%) have explicit governance mentions in PIN-329.

---

## Authoritative Inputs

| Input | Authority Level | Used For |
|-------|-----------------|----------|
| `CAPABILITY_REGISTRY_UNIFIED.yaml` | HIGH | Capability identity, lifecycle state |
| `PIN-329-capability-promotion-merge-report.md` | MEDIUM | Intent, promotion rationale |
| Claude capability summary | LOW | Semantic hints only |

**No other inputs allowed in 0B.**

---

## Directional Attributes (Schema)

These are not bindings, only claims.

| Column | Description | Source |
|--------|-------------|--------|
| `capability_id` | CAP-XXX or SUB-XXX | Registry |
| `canonical_name` | Final agreed name | Registry |
| `lifecycle_state` | active / planned / deprecated | Registry |
| `promotion_origin` | pre-PIN-329 / promoted / new | PIN-329 |
| `claimed_console_scope` | CUSTOMER / FOUNDER / SDK / NONE | Registry + PIN-329 |
| `claimed_exposure_type` | UI / API / SDK / INTERNAL | PIN-329 inference |
| `claimed_role` | engine / middleware / advisory / control | PIN-329 |
| `determinism_claim` | deterministic / probabilistic / mixed | PIN-329 + description |
| `mutability_claim` | read / write / control | PIN-329 |
| `replay_claim` | yes / no / unknown | PIN-329 |
| `export_claim` | yes / no / unknown | PIN-329 |
| `trust_weight` | LOW / MEDIUM / HIGH | Computed |
| `normalization_notes` | Free text | Script |

---

## Trust Weight Computation Rules (LOCKED)

### Trust Weight Levels

- **HIGH** — Multiple independent artifacts agree with execution semantics
- **MEDIUM** — Registry + code alignment OR registry + governance rationale
- **LOW** — Default, or only Claude summary presence

### Elevation Rules

| Rule | Condition | Result |
|------|-----------|--------|
| T1 | Registry + Code Alignment (API routes, imports) | MEDIUM |
| T2 | Registry + Governance Rationale (PIN-329 discussion) | MEDIUM |
| T3 | Execution + Governance + Code (all three) | HIGH |

### Degradation Rules

| Rule | Condition | Result |
|------|-----------|--------|
| D1 | Lifecycle = PLANNED | Always LOW |
| D2 | Claude-only presence | Always LOW |
| D3 | Middleware / Internal-only (no routes, no exports) | max MEDIUM |

**Trust weight NEVER implies bindability.** It only affects confidence and review priority.

---

## Outputs (MANDATORY)

| Artifact | Path | Role |
|----------|------|------|
| Authoritative table | `capability_directional_metadata.xlsx` | Consumed by STEP 1 and STEP 1B |
| CSV format | `capability_directional_metadata.csv` | Derived, never edited manually |
| YAML format | `capability_directional_metadata.yaml` | Derived, never edited manually |

---

## Explicit NON-GOALS

STEP 0B must NOT:

- Decide domain applicability
- Bind to L2.1 rows
- Expose anything to UI
- Reject capabilities
- Merge or split capabilities

If any of that happens here, the step is invalid.

---

## Design Principles

### A. Truth Hierarchy (Hard-coded)

From highest to lowest authority:

1. **Code truth** — API routes, imports, module ownership
2. **Registry truth** — CAPABILITY_REGISTRY_UNIFIED.yaml
3. **Governance truth** — PIN-329-capability-promotion-merge-report.md
4. **Semantic hints** — Claude summary

If two sources conflict → higher authority always wins.

### B. Expansion Rule

The script may:
- Add new inferred columns
- Add derived flags
- Add confidence modifiers

But it may not:
- Remove a capability
- Rename a capability
- Change lifecycle state
- Assert UI eligibility

### C. Determinism Rule

- No LLM calls
- Same inputs → same outputs. Always.

---

## Implementation

### Script

**File:** `scripts/ops/capability_directional_ingest.py`

**Behavior:**
1. Load `CAPABILITY_REGISTRY_UNIFIED.yaml`
2. Load `PIN-329-capability-promotion-merge-report.md`
3. Normalize each capability into directional profile
4. Compute trust weight per formalized rules
5. Output to xlsx, csv, yaml formats

---

## Progress Tracker

| Task | Status | Notes |
|------|--------|-------|
| Create PIN-360 | COMPLETE | This document |
| Implement script | COMPLETE | `scripts/ops/capability_directional_ingest.py` |
| Run script | COMPLETE | All 41 capabilities processed |
| Generate outputs | COMPLETE | xlsx, csv, yaml generated |
| Verify trust weights | COMPLETE | 7 HIGH, 27 MEDIUM, 7 LOW |
| Update PIN with results | COMPLETE | Results documented above |

## Generated Artifacts

| Artifact | Path | Size |
|----------|------|------|
| Authoritative Excel | `docs/capabilities/directional/capability_directional_metadata.xlsx` | 10.7 KB |
| CSV (derived) | `docs/capabilities/directional/capability_directional_metadata.csv` | 11.3 KB |
| YAML (derived) | `docs/capabilities/directional/capability_directional_metadata.yaml` | 30.1 KB |
| Ingest Script | `scripts/ops/capability_directional_ingest.py` | Deterministic |

---

## References

- PIN-329: Capability Promotion & Merge Report
- PIN-327: Capability Registration Finalization
- PIN-326: Dormant Capability Elicitation
- CAPABILITY_REGISTRY_UNIFIED.yaml

---

## Updates

### 2026-01-08: STEP 0B Complete

- **Script implemented:** `scripts/ops/capability_directional_ingest.py`
- **All 41 capabilities processed:** 21 FIRST_CLASS + 20 SUBSTRATE
- **Trust weight computed per formal rules:**
  - HIGH: 7 (capabilities with execution + governance + code)
  - MEDIUM: 27 (registry + code or governance)
  - LOW: 7 (planned or internal-only)
- **Outputs generated:**
  - `capability_directional_metadata.xlsx` (authoritative)
  - `capability_directional_metadata.csv` (derived)
  - `capability_directional_metadata.yaml` (derived)
- **PIN-329 coverage:** 82% (34/41 capabilities)

### 2026-01-08: PIN Created

- Objective defined
- Trust weight rules formalized
- Directional attributes schema locked

### Update (2026-01-08)

STEP 0B COMPLETE - All 41 capabilities processed, directional metadata generated


## HIGH Trust Capabilities

The following 7 capabilities have HIGH trust weight (execution + governance + code):

| ID | Name | Console Scope |
|----|------|---------------|
| CAP-001 | Execution Replay & Activity | CUSTOMER |
| CAP-002 | Cost Simulation V2 | CUSTOMER |
| CAP-005 | Founder Console | FOUNDER |
| CAP-009 | M19 Policy Engine | CUSTOMER |
| CAP-016 | Skill System (M2/M3) | SDK |
| CAP-018 | M25 Integration Platform | CUSTOMER |
| CAP-019 | Run Management | SDK |
