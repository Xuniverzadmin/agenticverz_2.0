# L2.1 Phase 2.1 Exploratory Analysis

**Status:** PHASE 2.1 OUTPUT
**Created:** 2026-01-07
**Purpose:** Document patterns, inconsistencies, and insights from supertable construction

---

## Pattern Analysis

### Pattern P1: O1 Panels Are Always Entry Points

**Observation:** Every O1 panel has:
- Nav Required = NO
- Visible by Default = YES
- Selection Mode = NONE
- Filtering = NO
- Control Set = []

**Implication:** O1 is the "dashboard view" — no user interaction except navigation deeper.

**L1 Derivation Rule:** O1 panels render as read-only summary cards.

---

### Pattern P2: O2 Panels Are Action Hubs

**Observation:** O2 panels consistently have:
- Filtering = YES
- Selection Mode = SINGLE or MULTI
- Control Set includes [FILTER, SORT, SELECT_*, NAVIGATE]
- Download often enabled for bulk export

**Implication:** O2 is where users "work" — filter, sort, select, act.

**L1 Derivation Rule:** O2 panels render as interactive tables/lists.

---

### Pattern P3: O3 Panels Require Navigation

**Observation:** All O3 panels have Nav Required = YES.

**Implication:** You cannot deep-link directly to O3 without context.

**UX Consideration:** Shareable URLs for O3 must encode parent context.

---

### Pattern P4: O5 Is Always Terminal

**Observation:** No O5 panel has navigation to deeper levels.

**Implication:** O5 is the "proof layer" — immutable, exportable, final.

**L1 Derivation Rule:** O5 panels render as raw data viewers with prominent DOWNLOAD.

---

### Pattern P5: Write Actions Cluster in O3

**Observation:** Write = YES appears only in:
- INC-AI-ID-O3 (Incident Detail)
- POL-AP-BP-O3 (Budget Policy Detail)
- POL-AP-RL-O3 (Rate Limit Detail)
- POL-AP-AR-O3 (Approval Rule Detail)

**Implication:** Modifications happen at detail level, not list level.

**Exception:** Bulk ACKNOWLEDGE at O2 is activation, not write.

---

### Pattern P6: Activate Actions Appear at O2 and O3

**Observation:**
- O2: Bulk acknowledge (Incidents)
- O3: Single-item activate/deactivate (Policies), acknowledge/resolve (Incidents)

**Implication:** Activation can be bulk (O2) or targeted (O3).

---

## Inconsistencies Identified

### Inconsistency I1: Overview Domain Has No Actions

**Finding:** Overview domain (3 rows) has:
- Write = NO (all rows)
- Activate = NO (all rows)
- Download = NO (all rows)

**Question:** Is Overview purely observational? Or should DOWNLOAD be enabled for health metrics export?

**Recommendation:** Phase 2 elicitation needed.

---

### Inconsistency I2: Logs O4 Skipped

**Finding:** LOGS.AUDIT_LOGS surfaces skip O4:
- O1, O2, O3 enabled
- O4 disabled
- O5 enabled

**Question:** Why no context layer for audit logs?

**Possible Reason:** Audit logs are atomic — no "related context" makes sense.

**Status:** Flagged but likely intentional per seed design.

---

### Inconsistency I3: Policies GC_L Not Implemented

**Finding:** 6 Policies rows have:
- Activate = YES
- Activate Action = ACTIVATE|DEACTIVATE
- Action Layer = GC_L

But PIN-348 says GC_L is NOT IMPLEMENTED.

**Implication:** UI intent is documented but backend cannot fulfill it.

**Recommendation:** Phase 2 elicitation: Are GC_L mutations planned for v1?

---

### Inconsistency I4: Ranking Dimension Inconsistency

**Finding:** O2 panels have Ranking Dimension, but some are unclear:
- `severity|created_at` (Incidents) — pipe-separated, implies multiple
- `metric_type` (Overview Health Metrics) — categorical, not ordinal

**Question:** Should Ranking Dimension be:
- Single value only?
- List of values?
- Include sort direction?

**Recommendation:** Clarify Ranking Dimension semantics.

---

## UX Friction Risks

### Friction F1: Incident Acknowledge Irreversibility

**Risk:** ACKNOWLEDGE at O2/O3 has Confirmation Required = YES, but:
- No UNDO control in catalog
- No REOPEN semantic defined

**Customer Impact:** Accidental acknowledge cannot be undone.

**Mitigation:** Either add REOPEN control or document irreversibility clearly.

---

### Friction F2: Policy Activation Without Preview

**Risk:** ACTIVATE/DEACTIVATE at O3 immediately changes enforcement.

**Customer Impact:** User might not understand impact before activating.

**Mitigation:** O4 (Impact Context) exists for Approval Rules — should it exist for Budget/Rate policies too?

---

### Friction F3: Bulk Download Without Progress

**Risk:** O2 bulk download (Completed Runs, Logs) may export large datasets.

**Customer Impact:** No progress indicator defined in UI intent.

**Recommendation:** Phase 2.2 should consider async download patterns.

---

### Friction F4: No Search Control

**Risk:** Control catalog has FILTER but no SEARCH.

**Observation:** FILTER implies column-based filtering. Free-text search is different.

**Question:** Should SEARCH be added to catalog for O2 panels?

**Recommendation:** Add to Control Proposal Register.

---

## Intent Asymmetries

### Asymmetry A1: Incidents vs Policies Action Depth

| Domain | O2 Actions | O3 Actions |
|--------|-----------|-----------|
| Incidents | ACKNOWLEDGE (bulk) | ACKNOWLEDGE, RESOLVE, ADD_NOTE |
| Policies | None | ACTIVATE, DEACTIVATE, UPDATE_* |

**Observation:** Incidents allow bulk action at O2; Policies require detail view.

**Implication:** Incidents prioritize speed; Policies prioritize deliberation.

---

### Asymmetry A2: Logs Have No Write Actions

**Observation:** All 13 Logs rows have Write = NO.

**Implication:** Logs are append-only, immutable.

**Correctness:** This is intentional — logs are truth.

---

### Asymmetry A3: Activity Has No Actions

**Observation:** All 10 Activity rows have:
- Write = NO
- Activate = NO

**Question:** Should Activity support CANCEL for active runs?

**Recommendation:** Phase 2 elicitation if CANCEL is customer intent.

---

## Summary of Findings

### Patterns (Intentional, Leverage for L1)

| ID | Pattern | L1 Implication |
|----|---------|----------------|
| P1 | O1 always entry point | Render as dashboard cards |
| P2 | O2 is action hub | Render as interactive tables |
| P3 | O3 requires navigation | Deep-link needs context |
| P4 | O5 is terminal | Render as raw data viewer |
| P5 | Write clusters at O3 | Modifications are deliberate |
| P6 | Activate at O2 and O3 | Bulk and targeted patterns |

### Inconsistencies (Require Clarification)

| ID | Issue | Action |
|----|-------|--------|
| I1 | Overview no actions | Elicitation: Download? |
| I2 | Logs O4 skipped | Likely intentional |
| I3 | Policies GC_L not implemented | Elicitation: v1 scope? |
| I4 | Ranking Dimension semantics | Clarify format |

### Friction Risks (UX Debt)

| ID | Risk | Mitigation |
|----|------|------------|
| F1 | Acknowledge irreversibility | REOPEN control or warning |
| F2 | Policy activation impact | Show impact preview |
| F3 | Bulk download no progress | Async pattern |
| F4 | No SEARCH control | Add to catalog? |

### Asymmetries (Intentional Differences)

| ID | Observation | Status |
|----|-------------|--------|
| A1 | Incidents bulk, Policies deliberate | Intentional |
| A2 | Logs no write | Correct (immutable) |
| A3 | Activity no actions | Elicitation: CANCEL? |

---

## New Control Proposal (From Analysis)

Added to Control Proposal Register:

| Control | Reason |
|---------|--------|
| SEARCH | Free-text search distinct from column FILTER |
| CANCEL | Activity domain may need run cancellation |
| REOPEN | Incidents may need to reopen after acknowledge |

---

## Phase 2 Elicitation Questions (From Analysis)

1. Should Overview domain support DOWNLOAD for health metrics?
2. Are GC_L policy mutations planned for Customer Console v1?
3. Should Activity support CANCEL for active runs?
4. Should Incidents support REOPEN after acknowledge?
5. What is the semantic format for Ranking Dimension (single vs list)?
