# Phase 2.1 Decision Ledger

**Status:** PHASE 2.1 OUTPUT
**Created:** 2026-01-07
**Purpose:** Customer-centric evaluation of all proposals for v1 thin UI

---

## Evaluation Criteria

| Criterion | Weight | Question |
|-----------|--------|----------|
| **Customer Problem Solved** | HIGH | Does this solve a real user pain point? |
| **User Risk If Absent** | HIGH | What bad thing happens to user without this? |
| **Cognitive Load Added** | MEDIUM | How much mental overhead does this add? |
| **Reversibility** | HIGH | Can user undo mistakes? |

### Decision Rules

- **ACCEPT** if: reduces friction, prevents irreversible mistakes, improves discoverability or trust
- **DEFER** if: value is real but not v1-critical, OR depends on unclear backend semantics
- **REJECT** if: duplicates existing intent, OR adds UI complexity without clear gain

---

## CONTROL PROPOSALS (6)

| proposal_type | proposal_name | affected_domains | customer_problem_solved | user_risk_if_absent | cognitive_load_added | reversibility | recommendation | rationale |
|---------------|---------------|------------------|------------------------|---------------------|---------------------|---------------|----------------|-----------|
| CONTROL | **ACTIVATE_TOGGLE** | Policies | "I want to quickly enable/disable a policy without emergency confirmation" | User must use KILL_SWITCH (designed for emergencies) for routine operations, causing friction and cognitive dissonance | LOW — familiar toggle pattern | HIGH — can toggle back | **ACCEPT** | Routine policy management needs lightweight control; KILL_SWITCH is semantically wrong for daily use |
| CONTROL | **ADD_NOTE** | Incidents | "I want to document why I acknowledged/resolved this incident" | No audit trail of human reasoning; compliance gap; team members lack context | LOW — simple text input | N/A — additive action | **ACCEPT** | Notes are essential for incident post-mortems and compliance; absence creates knowledge gaps |
| CONTROL | **EXPORT_PDF** | Incidents | "I need legal-grade evidence for audit/compliance" | User must manually assemble evidence; risk of incomplete audit trail | LOW — single button | N/A — export action | **DEFER** | Real value but depends on backend PDF generation capability (not confirmed); DOWNLOAD with JSON/CSV sufficient for v1 |
| CONTROL | **SEARCH** | All (O2 panels) | "I want to find a specific incident/log quickly by keyword" | User must manually filter columns one by one; slow discovery | LOW — familiar search box | N/A — read action | **ACCEPT** | Free-text search is fundamental UX; column filtering alone is insufficient for large datasets |
| CONTROL | **CANCEL** | Activity | "I want to stop a runaway execution before it causes damage" | User cannot intervene in active runs; must wait for timeout or failure | MEDIUM — needs confirmation UX | LOW — cannot undo cancelled work | **DEFER** | High value but backend CANCEL capability unclear (PIN-348 shows Activity has no actions); requires elicitation |
| CONTROL | **REOPEN** | Incidents | "I accidentally acknowledged/resolved the wrong incident" | Permanent mistake; user must create manual workaround or leave incorrect state | LOW — familiar undo pattern | HIGH — restores previous state | **DEFER** | High value for error recovery but backend reversibility not confirmed (PIN-348 Question #2); requires elicitation |

### Control Decisions Summary

| Control | Decision | v1 Status |
|---------|----------|-----------|
| ACTIVATE_TOGGLE | **ACCEPT** | Include in v1 |
| ADD_NOTE | **ACCEPT** | Include in v1 |
| EXPORT_PDF | **DEFER** | Post-v1 (backend dependency) |
| SEARCH | **ACCEPT** | Include in v1 |
| CANCEL | **DEFER** | Post-v1 (requires elicitation) |
| REOPEN | **DEFER** | Post-v1 (requires elicitation) |

---

## COLUMN PROPOSALS (6)

| proposal_type | proposal_name | affected_domains | customer_problem_solved | user_risk_if_absent | cognitive_load_added | reversibility | recommendation | rationale |
|---------------|---------------|------------------|------------------------|---------------------|---------------------|---------------|----------------|-----------|
| COLUMN | **danger_level** | Incidents, Policies | "I want to know how risky this action is before I click" | User may not realize some actions are more destructive than others; all confirmations look the same | NEGATIVE — reduces cognitive load by differentiating actions | N/A — metadata | **ACCEPT** | Graduated warnings prevent mistakes; "all confirmations equal" is bad UX; enables red/yellow/green visual cues |
| COLUMN | **requires_interpreter** | All (O3+) | "The UI knows when to render complex explanations" | None for user directly; affects L1 rendering decisions | NONE — invisible to user | N/A — structural | **ACCEPT** | Structural necessity for L1 derivation; no user-facing cost; directly from seed |
| COLUMN | **export_format_hint** | Logs, Incidents | "I want the right export format automatically suggested" | User must guess correct format; may export in wrong format | LOW — format selector | N/A — metadata | **DEFER** | Depends on EXPORT_PDF decision; DOWNLOAD button with format selector is v1-sufficient |
| COLUMN | **bulk_limit_hint** | All (O2 with SELECT_MULTI) | "I want guidance on how many items I can select" | User may try to select 1000 items and hit timeout/error | LOW — shows limit | N/A — advisory | **REJECT** | Implementation detail, not UI intent; backend should enforce limits and return clear errors |
| COLUMN | **terminal_order** | All (O5) | N/A — derivable | None | NONE | N/A | **REJECT** | Derivable from Order column (O5 = terminal, or max Order for topic); adds no value |
| COLUMN | **entry_point** | All | N/A — duplicates Nav Required | None | NONE | N/A | **REJECT** | Exact inverse of Nav Required; no new information |

### Column Decisions Summary

| Column | Decision | v1 Status |
|--------|----------|-----------|
| danger_level | **ACCEPT** | Include in v1 schema |
| requires_interpreter | **ACCEPT** | Include in v1 schema |
| export_format_hint | **DEFER** | Post-v1 |
| bulk_limit_hint | **REJECT** | Not adding |
| terminal_order | **REJECT** | Not adding |
| entry_point | **REJECT** | Not adding |

---

## DECISION SUMMARY

### ACCEPTED (5)

| Type | Name | Customer Value |
|------|------|----------------|
| CONTROL | ACTIVATE_TOGGLE | Routine policy management |
| CONTROL | ADD_NOTE | Incident documentation |
| CONTROL | SEARCH | Fast discovery |
| COLUMN | danger_level | Graduated risk awareness |
| COLUMN | requires_interpreter | L1 rendering support |

### DEFERRED (4)

| Type | Name | Reason |
|------|------|--------|
| CONTROL | EXPORT_PDF | Backend PDF generation unconfirmed |
| CONTROL | CANCEL | Backend CANCEL capability unclear |
| CONTROL | REOPEN | Backend reversibility unconfirmed |
| COLUMN | export_format_hint | Depends on EXPORT_PDF |

### REJECTED (3)

| Type | Name | Reason |
|------|------|--------|
| COLUMN | bulk_limit_hint | Implementation detail |
| COLUMN | terminal_order | Derivable |
| COLUMN | entry_point | Duplicates Nav Required |

---

## STOP CONDITIONS

No proposals required backend assumptions to be marked ACCEPT. All uncertain cases marked DEFER.

---

## ELICITATION DEPENDENCIES

These DEFERRED items will become ACCEPT if elicitation confirms:

| Proposal | Elicitation Question | If YES → |
|----------|---------------------|----------|
| CANCEL | "Should Activity support CANCEL for active runs?" | ACCEPT CANCEL |
| REOPEN | "Should incidents be reopenable after resolution?" | ACCEPT REOPEN |
| EXPORT_PDF | Backend PDF generation capability confirmed | ACCEPT EXPORT_PDF |
| export_format_hint | EXPORT_PDF accepted | ACCEPT export_format_hint |

---

## Attestation

```
✔ All 12 proposals evaluated
✔ Customer-centric criteria applied
✔ No backend assumptions in ACCEPT decisions
✔ Uncertain items marked DEFER, not ACCEPT
✔ Decision rationale documented
```
