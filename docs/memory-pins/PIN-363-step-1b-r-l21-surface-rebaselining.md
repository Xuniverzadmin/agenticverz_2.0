# PIN-363: STEP 1B-R — L2.1 Surface Rebaselining

**Status:** IN_PROGRESS
**Created:** 2026-01-08
**Category:** Governance / Capability Intelligence
**Scope:** Mechanical taxonomy repair
**Prerequisites:** PIN-362 (STEP 1B L2.1 Compatibility Scan)

---

## Purpose (single sentence)

> Given that STEP 1B generated 100% of rows (none matched baseline), STEP 1B-R introduces a **minimal, canonical set of mechanical surface primitives** into L2.1 so that STEP 1B becomes a "row selector" instead of a "row generator".

**This is mechanical taxonomy repair, not UI work.**

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Generated rows to analyze | 33 | FROM STEP 1B |
| Expected surface primitives | 6-8 | TARGET |
| Baseline dominance target | ≥60% | GATE G1 |
| Authority violations allowed | 0 | GATE G3 |

---

## Problem Statement

STEP 1B revealed a structural issue:

> *Capabilities are structurally valid, but L2.1 has no mechanical surfaces for them to land on.*

Original L2.1 rows were implicitly:
- Panel-oriented
- UI-action-centric
- Authority-blind
- Determinism-agnostic

Generated rows exposed **true mechanical dimensions**:
- Authority
- Determinism
- Mutability
- Intent surface (observe vs act vs govern)

**STEP 1B-R redefines L2.1 rows as mechanical surfaces, not panels.**

---

## Inputs (Locked)

| Input | Source | Purpose |
|-------|--------|---------|
| `l21_generated_rows.xlsx` | STEP 1B | Rows to cluster |
| `capability_directional_metadata.xlsx` | STEP 0B | Capability truth |
| `capability_applicability_matrix.xlsx` | STEP 1 | Domain admissibility |
| `l2_supertable_v3_cap_expanded.xlsx` | L2.1 baseline | Original (panel-centric) |

---

## Outputs (Authoritative)

| Output | Purpose |
|--------|---------|
| `l2_supertable_v3_rebased_surfaces.xlsx` | New mechanical baseline |
| `l21_surface_derivation_audit.xlsx` | Clustering audit trail |

---

## Algorithm

### Step 1: Cluster Generated Rows

From `l21_generated_rows.xlsx`, cluster by tuple:

```
(authority_required,
 determinism_required,
 mutability_required,
 surface_type)
```

**Ignore:** domain, capability_id, UI visibility

### Step 2: Collapse Clusters into Primitives

Each cluster becomes **one baseline surface**.

### Step 3: Define Canonical Surface Set

Target: **6-8 surfaces**, no more.

| Surface ID | Surface Type | Authority | Mutability | Determinism | Purpose |
|------------|--------------|-----------|------------|-------------|---------|
| L21-OBS-R | OBSERVE | OBSERVE | READ | STRICT | Pure read-only state |
| L21-EVD-R | EVIDENCE | OBSERVE | READ | STRICT | Replay, logs, proofs |
| L21-EXP-R | EXPLAIN | OBSERVE | READ | BOUNDED | Derived insight |
| L21-ACT-W | ACTUATE | ACT | WRITE | BOUNDED | User-triggered action |
| L21-RUN-X | SUBSTRATE | ACT | EXECUTE | BOUNDED | Execution substrate |
| L21-CTL-G | GOVERN | CONTROL | GOVERN | STRICT | Policy / governance |
| L21-ADM-A | ADMIN | ADMIN | GOVERN | STRICT | Founder-only irreversible |

**Rule:** If a surface does not appear in clustering → do NOT invent it.

### Step 4: Create Rebased Supertable

Each row must include:
- `surface_id`
- `surface_type`
- `authority_required`
- `determinism_required`
- `mutability_required`
- `ui_visibility = COLLAPSIBLE`
- `origin = REBASED`

**No domain yet.** These are global mechanical surfaces.

### Step 5: Re-run STEP 1B

Run `l21_capability_bind_scan.py` unchanged with:
- Rebased L2.1 as input
- Row generation still enabled (as fallback)

---

## Acceptance Gates (Non-Negotiable)

### Gate G1 — Baseline Dominance

| Metric | Requirement |
|--------|-------------|
| Bindings on rebased surfaces | ≥ 60% |
| Bindings requiring generation | ≤ 40% |

If not met → surface set incomplete.

### Gate G2 — CAP-001 Sanity

CAP-001 **must** bind to:
- `L21-EVD-R` (EVIDENCE)
- Optionally `L21-OBS-R`

CAP-001 **must NOT** bind to:
- ACTUATE
- SUBSTRATE
- GOVERN

If violated → surfaces are wrong.

### Gate G3 — Zero Authority Violations

- No capability binds upward in authority
- No fallback-generated row exceeds capability truth

Any violation = **HARD STOP**.

### Gate G4 — Generated Rows Become Rare

Remaining generated rows should represent:
- Genuinely novel interaction modes
- NOT missing primitives

---

## What NOT to Do

| Forbidden | Reason |
|-----------|--------|
| Add UI panels | Not UI work |
| Rename domains | Out of scope |
| Tweak STEP 1 logic | Separate concern |
| Special-case capabilities | Breaks universality |
| Fix numbers manually | Destroys auditability |

---

## Why This Step is Crucial

**If STEP 1B-R is skipped:**
- STEP 3 scenarios bind to fake surfaces
- UI ends up driving system shape
- L2.1 loses authority permanently

**If STEP 1B-R is done correctly:**
- L2.1 becomes a real contract
- Scenarios test real mechanics
- UI becomes a projection, not a driver

> This is the difference between a **platform** and a **dashboard**.

---

## Progress Tracker

| Task | Status | Notes |
|------|--------|-------|
| Create PIN-363 | COMPLETE | This document |
| Derive surface clusters | COMPLETE | 8 unique clusters identified |
| Define rebased schema | COMPLETE | 8 canonical surfaces |
| Create rebased supertable | COMPLETE | `l2_supertable_v3_rebased_surfaces.xlsx` |
| Re-run STEP 1B | COMPLETE | See results below |
| Validate gates G1-G4 | PARTIAL | G2 FAIL — data quality issue |

---

## STEP 1B-R Results (2026-01-08)

### Cluster Analysis

8 unique mechanical clusters identified from 33 generated rows:

| # | Authority | Determinism | Mutability | Surface Type | Count |
|---|-----------|-------------|------------|--------------|-------|
| 1 | ACT | BOUNDED | WRITE | ACTION | 11 |
| 2 | ACT | BOUNDED | READ | ACTION | 8 |
| 3 | ACT | STRICT | WRITE | ACTION | 4 |
| 4 | ACT | STRICT | READ | ACTION | 2 |
| 5 | EXPLAIN | BOUNDED | GOVERN | SUBSTRATE | 2 |
| 6 | EXPLAIN | BOUNDED | READ | SUBSTRATE | 2 |
| 7 | OBSERVE | BOUNDED | READ | EVIDENCE | 2 |
| 8 | CONTROL | BOUNDED | GOVERN | ACTION | 2 |

### Rebased Surfaces

| Surface ID | Type | Authority | Determinism | Mutability | Purpose |
|------------|------|-----------|-------------|------------|---------|
| L21-ACT-W | ACTION | ACT | BOUNDED | WRITE | User-triggered write action |
| L21-ACT-R | ACTION | ACT | BOUNDED | READ | User-triggered read action |
| L21-ACT-WS | ACTION | ACT | STRICT | WRITE | Strict write action |
| L21-ACT-RS | ACTION | ACT | STRICT | READ | Strict read action |
| L21-SUB-EG | SUBSTRATE | EXPLAIN | BOUNDED | GOVERN | Governance substrate |
| L21-SUB-ER | SUBSTRATE | EXPLAIN | BOUNDED | READ | Read-only substrate |
| L21-EVD-R | EVIDENCE | OBSERVE | BOUNDED | READ | Evidence and replay |
| L21-CTL-G | ACTION | CONTROL | BOUNDED | GOVERN | Policy control action |

### Gate Validation Results

| Gate | Requirement | Result | Status |
|------|-------------|--------|--------|
| G1 | Baseline dominance ≥60% | 100% | **PASS** |
| G2 | CAP-001 → EVIDENCE | CAP-001 → ACTION | **FAIL** |
| G3 | Zero authority violations | 0 violations | **PASS** |
| G4 | Generated ≤40% | 0% | **PASS** |

### Gate G2 Failure Analysis

**Problem:** CAP-001 (Execution Replay & Activity) binds to L21-ACT-W in all 4 domains.

**Root Cause:** STEP 0B metadata is incorrect:
- Current: `claimed_role=control`, `mutability_claim=write`
- Expected: `claimed_role=observe`, `mutability_claim=read`

**Impact:** Mechanical binding is correct per input data, but input data is wrong.

**Corrective Action Required:**
1. Fix CAP-001's directional metadata in STEP 0B
2. Re-run STEP 0B → STEP 1 → STEP 1B → STEP 1B-R
3. Validate Gate G2 passes

---

## Generated Artifacts

| Artifact | Path |
|----------|------|
| Rebased Surfaces | `docs/capabilities/l21_bounded/l2_supertable_v3_rebased_surfaces.xlsx` |
| Re-run Results | `docs/capabilities/l21_bounded/l21_rerun_results.xlsx` |

---

## References

- PIN-362: STEP 1B L2.1 Compatibility Scan
- PIN-361: STEP 1 Domain Applicability Matrix
- PIN-360: STEP 0B Directional Capability Normalization

---

## Updates

### 2026-01-08: PIN Created

- Purpose defined
- Algorithm specified
- Acceptance gates locked
- Starting with Option 1 (cluster derivation)
