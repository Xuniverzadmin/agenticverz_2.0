# L2.1 Control Proposal Register

**Status:** PHASE 2.1 OUTPUT
**Created:** 2026-01-07
**Purpose:** Track proposed new controls not in the initial catalog

---

## Initial Control Catalog (FROZEN)

```
FILTER
SORT
SELECT_SINGLE
SELECT_MULTI
DOWNLOAD
ADD_TO_POLICY
ACTIVATE_KILL_SWITCH
ACKNOWLEDGE
RESOLVE
NAVIGATE
```

---

## Proposed Controls

| proposed_control | reason | affected_rows | customer_value | overlaps_existing |
|------------------|--------|---------------|----------------|-------------------|
| ACTIVATE_TOGGLE | Policies O2/O3 need toggle to enable/disable policy without full activation flow | POL-AP-BP-O2, POL-AP-BP-O3, POL-AP-RL-O2, POL-AP-RL-O3, POL-AP-AR-O2, POL-AP-AR-O3 | High — instant policy control without modal confirmation | Partial overlap with ACTIVATE_KILL_SWITCH but semantically different (toggle vs kill) |
| ADD_NOTE | Incident O3 allows adding resolution notes | INC-AI-ID-O3 | Medium — contextual annotation during incident handling | No overlap — new write intent |
| EXPORT_PDF | Evidence export for legal-grade incidents | INC-HI-RI-O5 | High — compliance/audit requirement | Extends DOWNLOAD with format specification |
| BULK_ACKNOWLEDGE | Open Incidents O2 bulk action | INC-AI-OI-O2 | High — operational efficiency for many incidents | Extends ACKNOWLEDGE to multi-select context |

---

## Derivation Notes

### ACTIVATE_TOGGLE vs ACTIVATE_KILL_SWITCH

**Problem:** The initial catalog has `ACTIVATE_KILL_SWITCH` which implies emergency/destructive action. But Policies domain needs a simple enable/disable toggle that is:
- Reversible
- Non-emergency
- Used for routine policy management

**Proposal:** Add `ACTIVATE_TOGGLE` as a distinct control for non-destructive enable/disable patterns.

**Affected Rows (6):**
- POL-AP-BP-O2, POL-AP-BP-O3 (Budget Policies)
- POL-AP-RL-O2, POL-AP-RL-O3 (Rate Limits)
- POL-AP-AR-O2, POL-AP-AR-O3 (Approval Rules)

---

### ADD_NOTE

**Problem:** Incident Detail (O3) has Write=YES with Write Action=ADD_NOTE, but `ADD_NOTE` is not in the control catalog.

**Proposal:** Add `ADD_NOTE` as a write control for contextual annotation.

**Affected Rows (1):**
- INC-AI-ID-O3

---

### EXPORT_PDF

**Problem:** Resolved Incident Proof (O5) needs legal-grade evidence export. DOWNLOAD covers the action, but the format (PDF vs JSON vs CSV) is semantically important for compliance.

**Proposal:** Add `EXPORT_PDF` as a specialized download control for legal/compliance contexts.

**Affected Rows (1):**
- INC-HI-RI-O5

**Alternative:** Could be represented as DOWNLOAD with a `format_hint` column.

---

### BULK_ACKNOWLEDGE

**Problem:** Open Incidents List (O2) has Selection Mode=MULTI and Activate=YES with Action=ACKNOWLEDGE. The control derivation rules give ACKNOWLEDGE, but bulk semantics differ from single-item acknowledge.

**Proposal:** Either:
- A) Add `BULK_ACKNOWLEDGE` as distinct control
- B) Treat ACKNOWLEDGE as inherently bulk-capable when Selection Mode=MULTI

**Recommendation:** Option B — ACKNOWLEDGE inherits bulk semantics from Selection Mode. No new control needed.

**Status:** WITHDRAWN — covered by existing control + selection mode combination.

---

## Summary

| Control | Status | Recommendation |
|---------|--------|----------------|
| ACTIVATE_TOGGLE | PROPOSED | Add to catalog — distinct from KILL_SWITCH |
| ADD_NOTE | PROPOSED | Add to catalog — new write intent |
| EXPORT_PDF | PROPOSED | Review — may be column (format_hint) instead |
| BULK_ACKNOWLEDGE | WITHDRAWN | Covered by ACKNOWLEDGE + SELECT_MULTI |

---

---

## Additional Proposals (From Exploratory Analysis)

| proposed_control | reason | affected_rows | customer_value | overlaps_existing |
|------------------|--------|---------------|----------------|-------------------|
| SEARCH | Free-text search across records, distinct from column-based FILTER | All O2 panels (14 rows) | High — faster discovery than column filtering | Low — complements FILTER |
| CANCEL | Cancel active execution run | ACT-EX-AR-O2, ACT-EX-AR-O3 | Medium — operational control | No overlap |
| REOPEN | Reopen acknowledged/resolved incident | INC-AI-ID-O3, INC-HI-RI-O3 | Medium — error recovery | No overlap |

### SEARCH

**Problem:** FILTER operates on structured columns. Users may want free-text search.

**Proposal:** Add SEARCH as a distinct control for O2 panels.

**Status:** PROPOSED — requires human decision.

---

### CANCEL

**Problem:** Activity domain has no actions. Active runs cannot be cancelled from UI.

**Proposal:** Add CANCEL for active runs.

**Affected Rows (2):**
- ACT-EX-AR-O2 (Active Runs List)
- ACT-EX-AR-O3 (Active Run Detail) — if O3 existed

**Note:** Current seed has ACTIVE_RUNS at O1+O2 only. CANCEL may require O3.

**Status:** PROPOSED — requires Phase 2 elicitation.

---

### REOPEN

**Problem:** ACKNOWLEDGE and RESOLVE are currently irreversible.

**Proposal:** Add REOPEN to allow error recovery.

**Affected Rows (2):**
- INC-AI-ID-O3 (Incident Detail)
- INC-HI-RI-O3 (Resolved Incident Detail)

**Status:** PROPOSED — requires Phase 2 elicitation.

---

## Summary (Updated)

| Control | Status | Recommendation |
|---------|--------|----------------|
| ACTIVATE_TOGGLE | PROPOSED | Add to catalog — distinct from KILL_SWITCH |
| ADD_NOTE | PROPOSED | Add to catalog — new write intent |
| EXPORT_PDF | PROPOSED | Review — may be column (format_hint) instead |
| BULK_ACKNOWLEDGE | WITHDRAWN | Covered by ACKNOWLEDGE + SELECT_MULTI |
| SEARCH | PROPOSED | Add to catalog — complements FILTER |
| CANCEL | PROPOSED | Phase 2 elicitation required |
| REOPEN | PROPOSED | Phase 2 elicitation required |

---

## Review Required

Before Phase 2.2 (capability binding), human must:
1. Accept or reject ACTIVATE_TOGGLE
2. Accept or reject ADD_NOTE
3. Decide EXPORT_PDF: new control or new column?
4. Accept or reject SEARCH
5. Elicit: Is CANCEL for active runs in scope?
6. Elicit: Is REOPEN for incidents in scope?
