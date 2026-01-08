# PIN-364: STEP X — Capability Opportunity Mapping (Read-Only)

**Status:** COMPLETE (ARCHIVED)
**Created:** 2026-01-08
**Category:** Governance / Roadmap Intelligence
**Scope:** Read-only analysis, parallel to main pipeline
**Prerequisites:** PIN-363 (STEP 1B-R frozen)

---

## Purpose (tight and non-negotiable)

> Identify **latent product surfaces and customer questions** implied by existing capabilities **without affecting** STEP 1 / 1B / STEP 3.

**This is roadmap intelligence, not architecture.**

---

## Positioning

| Aspect | Rule |
|--------|------|
| Execution | Runs **in parallel** to STEP 3 |
| Data flow | **Consumes frozen artifacts** only |
| Output | **Produces new artifacts only** |
| Feedback | **Never feeds back** into capability binding, L2.1, or scenarios |

Once executed and recorded → **closed**.

---

## Inputs (Read-Only, Frozen)

| Input | Source | Purpose |
|-------|--------|---------|
| `capability_directional_metadata.xlsx` | STEP 0B | Capability truth |
| `capability_applicability_matrix.xlsx` | STEP 1 | Domain admissibility |
| `l2_supertable_v3_rebased_surfaces.xlsx` | STEP 1B-R | Mechanical surfaces |
| `domain_intent_spec.yaml` | STEP 1 | Existing questions |

**No codebase scans. No UI context.**

---

## Outputs (New Only)

| Output | Purpose |
|--------|---------|
| `capability_opportunity_map.xlsx` | Surface gaps per capability |
| `unasked_questions.xlsx` | Candidate customer questions |

---

## STEP X.A — Capability × Surface Opportunity Scan

### What this answers

> "Which L2.1 surfaces *could* this capability support but currently does not?"

### Method

For each capability:
1. Compare **allowed surfaces** (by authority, determinism, mutability)
2. Compare **currently bound surfaces**
3. Compute **surface gaps**

### Output Schema

| Column | Description |
|--------|-------------|
| `capability_id` | CAP-XXX or SUB-XXX |
| `authority` | Capability's authority level |
| `current_surfaces` | Surfaces capability is bound to |
| `potential_surfaces` | Surfaces capability could bind to |
| `gap_type` | Product / UX / Productization / Ignore |

### Gap Type Enum

| Type | Meaning |
|------|---------|
| `Product` | New customer-facing surface |
| `UX` | Better visibility of existing value |
| `Productization` | Platform feature → product |
| `Ignore` | Internal-only, no surface value |

**No binding. No decisions.**

---

## STEP X.B — "Unasked Question" Derivation

### What this answers

> "What customer questions could exist that we are not asking today?"

### Method

For each capability with gaps:
1. Generate **candidate questions** based on authority, role, data produced
2. Verify question **does not exist** in `domain_intent_spec.yaml`

### Output Schema

| Column | Description |
|--------|-------------|
| `capability_id` | Source capability |
| `proposed_question` | Candidate question text |
| `domain_candidate` | Potential domain fit |
| `rationale` | Why this question might matter |

**These are hypotheses, not requirements.**

---

## STEP X.C — Customer Value Classification

| Field | Values |
|-------|--------|
| `customer_value` | HIGH / MEDIUM / LOW |
| `audience` | DEV / OPS / FOUNDER / ENTERPRISE |
| `time_horizon` | NOW / NEXT / LATER |

---

## Hard Stop Rules (Drift Prevention)

STEP X **must NOT**:
- Modify any existing YAML/XLSX used by STEP 1–3
- Introduce new L2.1 surfaces
- Add domains or subdomains
- Influence scenario design
- Influence UI binding

**If someone asks "can we just use this now?" → the answer is NO.**

---

## Completion Criteria

STEP X is **done** when:
1. `capability_opportunity_map.xlsx` exists
2. `unasked_questions.xlsx` exists
3. Findings reviewed once
4. Artifacts archived

**No iteration loop. No optimization.**

---

## Implementation

**Script:** `scripts/ops/capability_opportunity_mapping.py`

**Design Constraints:**
- No writes to STEP 1–3 artifacts
- No L2.1 mutation
- No UI logic
- Deterministic
- Record-only outputs

---

## Progress Tracker

| Task | Status | Notes |
|------|--------|-------|
| Create PIN-364 | COMPLETE | This document |
| Implement script | COMPLETE | `scripts/ops/capability_opportunity_mapping.py` |
| Run STEP X | COMPLETE | 2026-01-08 |
| Archive outputs | COMPLETE | `docs/capabilities/step_x/` | |

---

## References

- PIN-363: STEP 1B-R L2.1 Surface Rebaselining (FROZEN)
- PIN-362: STEP 1B L2.1 Compatibility Scan
- PIN-361: STEP 1 Domain Applicability Matrix
- PIN-360: STEP 0B Directional Capability Normalization

---

## Updates

### 2026-01-08: PIN Created

- Purpose defined
- Hard stop rules locked
- Ready for implementation

### 2026-01-08: STEP X Executed and Archived

**Script:** `scripts/ops/capability_opportunity_mapping.py`

**Inputs consumed (frozen):**
- 41 capabilities from `capability_directional_metadata.xlsx`
- 164 applicability evaluations from `capability_applicability_matrix.xlsx`
- 8 rebased surfaces from `l2_supertable_v3_rebased_surfaces.xlsx`
- 33 current bindings from `l21_rerun_results.xlsx`
- 18 existing questions from `domain_intent_spec.yaml`

**STEP X.A Results — Surface Opportunity Scan:**

| Metric | Value |
|--------|-------|
| Total surface gaps | 38 |
| Gap Type: UX | 20 |
| Gap Type: Ignore | 15 |
| Gap Type: Productization | 3 |

**Top 5 Capabilities by Gap Count:**

| Capability | Name | Gap Count |
|------------|------|-----------|
| CAP-005 | Founder Console | 5 |
| CAP-002 | Cost Simulation V2 | 3 |
| CAP-009 | M19 Policy Engine | 3 |
| CAP-011 | M28 Governance Orchestration | 3 |
| CAP-016 | Skill System (M2/M3) | 3 |

**STEP X.B Results — Unasked Question Derivation:**

| Metric | Value |
|--------|-------|
| Candidate questions generated | 8 |
| Domain: POLICIES | 7 |
| Domain: ACTIVITY | 1 |

**Sample Unasked Questions:**

1. "How do I access Cost Simulation V2 features?" (POLICIES)
2. "What predictions are available from Policy Proposals?" (POLICIES)
3. "Can I trigger M12 Multi-Agent Orchestration from the UI?" (POLICIES)
4. "How do I access Founder Console features?" (POLICIES)

**Output Artifacts:**

| Artifact | Path |
|----------|------|
| Opportunity Map | `docs/capabilities/step_x/capability_opportunity_map.xlsx` |
| Unasked Questions | `docs/capabilities/step_x/unasked_questions.xlsx` |

**Hard Stop Verification:**
- ✅ No writes to STEP 1-3 artifacts
- ✅ No L2.1 mutation
- ✅ Read-only analysis only

**Status:** ARCHIVED — No iteration. No optimization.
