# PIN-365: STEP 2A — UI Slot Population (Surface-Aligned)

**Status:** COMPLETE (CI validation pending)
**Created:** 2026-01-08
**Category:** Governance / UI Pipeline Evolution
**Scope:** Surface → UI Slot translation layer
**Prerequisites:** PIN-363 (STEP 1B-R frozen), PIN-359 (Wireframe Compliance)

---

## Status Context (Important)

The existing UI pipeline is **correct, governed, and production-grade**.
All memory PINs referenced (PIN-359, PIN-360, PIN-361, PIN-362, PIN-363, PIN-364) are **frozen facts**, not assumptions.

What has changed is **the semantic meaning of L2.1** after:

* STEP 1B — Capability ↔ L2.1 compatibility
* STEP 1B-R — L2.1 surface rebaselining (PIN-363, frozen)

This requires a **single controlled extension**, not a rewrite.

---

## Problem Statement (Why STEP 2A Exists)

### What worked before

* L2.1 Supertable directly encoded **UI panels**
* UI projection was deterministic and locked
* `/precus` was predictable and controllable

### What is now true (post-STEP 1B-R)

* L2.1 rows now represent **mechanical surfaces**, not UI panels
* Capabilities bind to **surfaces**, not UI
* UI panels are **product projections**, not system truth

### The mismatch

The current pipeline assumes:

```
L2.1 row = UI panel
```

But the system truth is now:

```
L2.1 row = Mechanical surface
UI panel = Projection of one or more surfaces
```

Without STEP 2A:

* STEP 3 scenarios can only be tested headless
* UI testing becomes misleading or impossible
* Product validation lags behind system validation

---

## STEP 2A — Definition

> **STEP 2A introduces an explicit Surface → UI Slot translation layer, without altering downstream stages or weakening governance.**

It allows:

* UI-level testing
* Product validation
* Continued determinism and CI enforcement

It does **not**:

* Modify capability binding
* Modify STEP 1 / STEP 1B artifacts
* Introduce a new pipeline
* Change frontend assumptions

---

## Conceptual Model (Authoritative)

```
Capability
   ↓
L2.1 Mechanical Surface   (SYSTEM truth, frozen)
   ↓
UI Slot                  (PRODUCT abstraction, STEP 2A)
   ↓
UI Projection (LOCKED)
   ↓
UI Renderer
```

UI **never** sees:

* capability IDs
* engines
* policies
* surface mechanics

UI sees **slots only**.

---

## What Changes, Stage by Stage

### [1] Human Intent

**NO CHANGE**

* Intent remains domain questions and product thinking
* Still referenced by PIN-359 wireframes
* No capability or surface leakage here

---

### [2] L2.1 Supertable — SEMANTIC CHANGE (not structural)

**Before**

* Rows = UI panels
* Columns include domain, subdomain, order, controls, visibility

**After (required)**

* Rows = **mechanical surfaces**
* Encodes only:
  * `surface_id`
  * `surface_type`
  * `authority_required`
  * `determinism_required`
  * `mutability_required`
  * `origin`

**Important**

* This is already true in `l2_supertable_v3_rebased_surfaces.xlsx`
* STEP 2A assumes this table is **frozen and correct**

No UI metadata belongs here anymore.

---

### [3] Raw Intent Parser

**NO CODE CHANGE**

* Continues to parse CSV → raw IR
* Now parses **surface intent**, not UI intent

---

### [4] Intent Normalizer

**NO CODE CHANGE**

* Applies defaults safely
* Normalizes surface metadata

---

### [4.5] NEW — Surface → UI Slot Resolver (STEP 2A)

This is the **only new stage**.

#### Purpose

Translate **mechanical surfaces** into **UI slots** that the existing compiler understands.

#### Inputs

| Input | Source | Purpose |
|-------|--------|---------|
| Normalized surface-aware IR | Stage 4 output | Surface definitions |
| `ui_slot_registry.xlsx` | STEP 2A | Product-level slot definitions |
| `surface_to_ui_slot_map.xlsx` | STEP 2A | Surface → Slot mapping |

#### Outputs

* Slot-aware IR that looks **identical in shape** to the previous panel-based IR

#### Responsibilities

* Map surface(s) → slot(s)
* Apply product visibility rules
* Enforce authority compatibility
* NO capability logic
* NO UI rendering logic

---

### [5] Intent Compiler

**NO CHANGE**

* Still hostile
* Still fails hard
* Still enforces explicitness

Now validates **slots**, not surfaces.

---

### [6] UI Projection Builder

**NO CHANGE**

* Builds explicit panels
* Explicit controls
* Explicit ordering

Because slots produce panel-shaped IR, this stage is untouched.

---

### [7] Projection Lock

**NO CHANGE**

* Remains immutable
* CI checksum enforcement stays
* UI consumes only this file

---

### [8] Loader

**NO CHANGE**

---

### [9] Renderer

**NO CHANGE**

Frontend remains completely ignorant of:

* capabilities
* surfaces
* binding logic

---

## New Artifacts Introduced by STEP 2A

### 1. `ui_slot_registry.xlsx`

Defines **product-level slots**.

| Column | Description |
|--------|-------------|
| `slot_id` | Unique slot identifier (e.g., `SLOT-ACT-001`) |
| `domain` | Target domain (ACTIVITY, INCIDENTS, POLICIES, LOGS) |
| `slot_name` | Human-readable name |
| `surface_type` | Compatible surface type(s) |
| `authority` | Required authority level |
| `intent` | What question this slot answers |
| `default_visibility` | VISIBLE / COLLAPSIBLE / HIDDEN |
| `order` | Display order within domain |

This replaces the **UI meaning** previously embedded in L2.1.

---

### 2. `surface_to_ui_slot_map.xlsx`

Defines how surfaces are projected to slots.

| Column | Description |
|--------|-------------|
| `surface_id` | Source surface (from rebased L2.1) |
| `slot_id` | Target slot |
| `binding_type` | PRIMARY / SECONDARY / FALLBACK |
| `conditions` | Optional conditions for binding |

This is **pure mapping**, no logic.

---

## Pipeline Flow (Updated)

```
L2_1_UI_INTENT_SUPERTABLE.csv (surfaces)
                    ↓
        [Step 1: l2_raw_intent_parser.py]
                    ↓
         ui_intent_ir_raw.json
                    ↓
        [Step 2: intent_normalizer.py]
                    ↓
    ui_intent_ir_normalized.json
                    ↓
  ┌─────────────────────────────────────────┐
  │  [Step 2A: surface_to_slot_resolver.py] │  ← NEW
  │                                          │
  │  Inputs:                                 │
  │    - ui_intent_ir_normalized.json        │
  │    - ui_slot_registry.xlsx               │
  │    - surface_to_ui_slot_map.xlsx         │
  │                                          │
  │  Output:                                 │
  │    - ui_intent_ir_slotted.json           │
  └─────────────────────────────────────────┘
                    ↓
        [Step 3: intent_compiler.py]
                    ↓
   ui_intent_ir_compiled.json
                    ↓
       [Step 4: ui_projection_builder.py]
                    ↓
    ui_projection_lock.json (LOCKED)
                    ↓
          [UI Renderer Consumes]
```

---

## Governance & Safety Guarantees

STEP 2A preserves:

| Guarantee | Status |
|-----------|--------|
| Single source of truth | PRESERVED |
| CI enforcement | PRESERVED |
| Deterministic UI builds | PRESERVED |
| Locked projection contract | PRESERVED |
| Human-reviewable inputs | PRESERVED |

It introduces **zero runtime ambiguity**.

---

## Why This Is One-Time, Long-Term, and Safe

| Aspect | Explanation |
|--------|-------------|
| Capabilities can grow | → surfaces remain stable |
| Surfaces can remain stable | → slots evolve slowly |
| UI stays predictable | slots are explicit |
| `/precus` remains valid | no pipeline disruption |
| No second pipeline | single flow with new stage |
| No duplication | slot registry replaces embedded UI metadata |

---

## Summary

> We are not replacing the UI pipeline.
> We are redefining L2.1 as **mechanical surfaces** and inserting a **Surface → UI Slot resolver** (STEP 2A) before intent compilation.
>
> Downstream stages remain unchanged.
> UI renders slots, not surfaces or capabilities.
>
> This enables UI-level testing while preserving all existing governance and determinism.

---

## Implementation Checklist

| Task | Status | Notes |
|------|--------|-------|
| Create PIN-365 | COMPLETE | This document |
| Lock design decisions | COMPLETE | 2026-01-08 |
| Draft `ui_slot_registry.xlsx` | COMPLETE | 52 slots, 1:1 with panels |
| Draft `surface_to_ui_slot_map.xlsx` | COMPLETE | 109 mappings |
| Implement `surface_to_slot_resolver.py` | COMPLETE | Stage 2A script implemented |
| Update `run_l2_pipeline.sh` | COMPLETE | Stage 2A integrated |
| Validate end-to-end | COMPLETE | Full pipeline test passed |
| Update CI validation | PENDING | Add slot validation |

---

## References

| PIN | Topic | Status |
|-----|-------|--------|
| PIN-359 | Sidebar Workspace Realignment — Wireframe Compliance | REFERENCE |
| PIN-360 | STEP 0B Directional Capability Normalization | COMPLETE |
| PIN-361 | STEP 1 Domain Applicability Matrix | COMPLETE |
| PIN-362 | STEP 1B L2.1 Compatibility Scan | COMPLETE |
| PIN-363 | STEP 1B-R L2.1 Surface Rebaselining | FROZEN |
| PIN-364 | STEP X Capability Opportunity Mapping | ARCHIVED |

---

## Related Files

| File | Purpose | Layer |
|------|---------|-------|
| `design/l2_1/supertable/L2_1_UI_INTENT_SUPERTABLE.csv` | Original supertable (303 panels) | L4 |
| `docs/capabilities/l21_bounded/l2_supertable_v3_rebased_surfaces.xlsx` | Rebased surfaces (8 rows) | L4 |
| `scripts/tools/l2_raw_intent_parser.py` | Stage 1 | L8 |
| `scripts/tools/intent_normalizer.py` | Stage 2 | L8 |
| `scripts/tools/surface_to_slot_resolver.py` | Stage 2A (NEW) | L8 |
| `scripts/tools/intent_compiler.py` | Stage 3 | L8 |
| `scripts/tools/ui_projection_builder.py` | Stage 4 | L8 |
| `design/l2_1/ui_contract/ui_intent_ir_slotted.json` | Stage 2A output (NEW) | L4 |
| `design/l2_1/ui_contract/ui_projection_lock.json` | Final output | L4 |
| `design/l2_1/step_2a/ui_slot_registry.xlsx` | Slot registry | L4 |
| `design/l2_1/step_2a/surface_to_ui_slot_map.xlsx` | Surface-to-slot mappings | L4 |

---

## Updates

### 2026-01-08: PIN Created

- Problem statement defined
- Conceptual model established
- Stage-by-stage analysis complete
- New artifacts specified
- Ready for implementation

### 2026-01-08: Design Decisions Locked

- Slot granularity: 52 slots, 1:1 with panels
- Cardinality: Many-to-many with compatibility enforcement
- Visibility: Slot owns visibility
- Backward compat: Keep old supertable as legacy

### 2026-01-08: Artifacts Generated

**Generator Script:** `scripts/ops/generate_step2a_artifacts.py`

**Slot Registry Generated:**
| Metric | Value |
|--------|-------|
| Total slots | 52 |
| Overview | 3 slots |
| Activity | 10 slots |
| Incidents | 11 slots |
| Policies | 15 slots |
| Logs | 13 slots |

**Surface Mappings Generated:**
| Metric | Value |
|--------|-------|
| Total mappings | 109 |
| L21-EVD-R bindings | 52 |
| L21-SUB-ER bindings | 47 |
| L21-CTL-G bindings | 5 |
| L21-SUB-EG bindings | 5 |

**Output Artifacts:**
| Artifact | Path |
|----------|------|
| Slot Registry | `design/l2_1/step_2a/ui_slot_registry.xlsx` |
| Surface-Slot Map | `design/l2_1/step_2a/surface_to_ui_slot_map.xlsx` |

### 2026-01-08: Stage 2A Implemented

**Resolver Script:** `scripts/tools/surface_to_slot_resolver.py`

**Pipeline Updated:** `scripts/tools/run_l2_pipeline.sh`

**End-to-End Validation Results:**

| Stage | Status | Details |
|-------|--------|---------|
| Step 1: Parse | PASS | 303 intents from supertable |
| Step 2: Normalize | PASS | 793 fields filled |
| Step 2A: Resolve | PASS | 303 resolved, 0 unmapped, 0 warnings |
| Step 3: Compile | PASS | Validation passed |
| Step 4: Build | PASS | 5 domains, 52 panels, 95 controls |

**New Artifact Generated:**

| Artifact | Path |
|----------|------|
| Slotted IR | `design/l2_1/ui_contract/ui_intent_ir_slotted.json` |

**Pipeline Flow (Updated):**

```
L2.1 Supertable
      ↓
[Stage 1] l2_raw_intent_parser.py → ui_intent_ir_raw.json
      ↓
[Stage 2] intent_normalizer.py → ui_intent_ir_normalized.json
      ↓
[Stage 2A] surface_to_slot_resolver.py → ui_intent_ir_slotted.json (NEW)
      ↓
[Stage 3] intent_compiler.py → ui_intent_ir_compiled.json
      ↓
[Stage 4] ui_projection_builder.py → ui_projection_lock.json
```

**Status:** STEP 2A implementation COMPLETE. CI validation pending.

---

### Update (2026-01-08)

### 2026-01-08: Frontend Rebuilt & Deployed

**Deployment Steps Completed:**
1. Frontend built: `npm run build` (15.57s)
2. Copied to preflight: `cp -r dist dist-preflight`
3. Apache reloaded: `systemctl reload apache2`

**Live URL:** https://preflight-console.agenticverz.com/precus/

**Verification Results:**

| Check | Status |
|-------|--------|
| Projection lock served | HTTP 200, application/json |
| File size | 62,254 bytes |
| Main JS bundle | index-DT2yuvPj.js loading |
| SPA routing | /precus/overview → HTTP 200 |

**Projection Lock Contents:**

| Domain | Panels |
|--------|--------|
| Overview | 3 |
| Activity | 10 |
| Incidents | 11 |
| Policies | 15 |
| Logs | 13 |
| **Total** | **52 panels, 95 controls** |

**STEP 2A Pipeline Fully Operational.**

### Update (2026-01-08)

### 2026-01-08: Surface-Slot Coverage Guard Added

**Script:** `scripts/ci/surface_slot_coverage_guard.py`

**Rule:** Every surface bound in STEP 1B must map to ≥1 UI slot or be explicitly marked non-UI.

**Purpose:** Prevent "silent invisibility" bugs where a surface exists but has no UI representation.

**Coverage Results:**

| Surface | Status |
|---------|--------|
| L21-EVD-R | MAPPED |
| L21-SUB-ER | MAPPED |
| L21-SUB-EG | MAPPED |
| L21-CTL-G | MAPPED |
| L21-ACT-W | NON-UI (no write UI yet) |
| L21-ACT-R | NON-UI (no action UI yet) |
| L21-ACT-WS | NON-UI (no strict write UI yet) |
| L21-ACT-RS | NON-UI (no strict action UI yet) |

**Note:** ACTION surfaces marked non-UI because customer console is currently read-only. When write/action capabilities are added, these should be mapped to slots.


## Design Decisions (LOCKED — 2026-01-08)

### Guiding Principle

> STEP 2A's job is **UI continuity + architectural correction**, not product redesign.
> The default bias is: preserve UI behavior, preserve user muscle memory, preserve CI determinism, shift semantics *under the hood*.

---

### Decision 1: Slot Granularity — **52 slots, 1:1 with panels**

**Choice:** Create **52 UI slots**, 1:1 aligned with existing panels.

**Rationale:**
- UI is already wired, validated, predictable, and preflight-tested
- STEP 2A is *not* a redesign phase
- Changing slot count would invalidate STEP 3 product testing and PIN-359 wireframes

**Key Principle:**
> STEP 2A must be *lossless* at the UI level.

**Future Evolution:**
- Slots may be merged, split, or added **later** — but NOT in STEP 2A

---

### Decision 2: Surface ↔ Slot Cardinality — **Many-to-Many Allowed**

**Choice:** Allow both:
- One surface → many slots
- One slot → many surfaces

**With strict semantics:**

| Case | Rule |
|------|------|
| 1 surface → N slots | Allowed. Same mechanical capability, different user context. |
| N surfaces → 1 slot | Allowed, but surfaces must have compatible authority, mutability, and determinism. |

**Enforcement:**
> Resolver must reject incompatible surface combinations at build time.

---

### Decision 3: Visibility Rules — **Slot Owns Visibility**

**Choice:** Visibility is specified **per slot** in the slot registry.

**Surface authority is a *constraint*, not visibility logic.**

**Rationale:**
- Surface authority is mechanical
- Visibility is product & policy
- Same surface may be visible in one domain, hidden in another

**Example:**
| Surface | Policies | Activity | Logs |
|---------|----------|----------|------|
| `L21-CTL-G` (CONTROL) | VISIBLE | HIDDEN | DISABLED |

---

### Decision 4: Backward Compatibility — **Keep as Legacy Reference**

**Choice:**
- **Keep** `L2_1_UI_INTENT_SUPERTABLE.csv` (303 rows)
- Mark it **READ-ONLY / LEGACY**
- Use it as reference, audit trail, and migration source

**Do NOT use it as source of truth anymore.**

**New product source of truth:** `ui_slot_registry.xlsx`

---

## Design Decisions Summary

| Question | Decision |
|----------|----------|
| Slot granularity | 52 slots, 1:1 with existing panels |
| Cardinality | Many-to-many, with compatibility enforcement |
| Visibility | Slot owns visibility; surface authority constrains only |
| Backward compat | Keep old supertable as legacy reference only |
