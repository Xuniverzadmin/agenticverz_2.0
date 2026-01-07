# L2.1 Phase 2.1 Completion Report

**Status:** COMPLETE
**Created:** 2026-01-07
**Phase:** 2.1 — UI Intent Supertable Construction

---

## Objective

Construct the **L2.1 UI Intent Supertable** across all domains, exhaustively and explicitly, such that:
- L1 headless UI can be derived without ambiguity
- Customer intent is fully represented
- No capability or API assumptions leak in
- Any new concept introduced by Claude is **flagged, justified, and reviewable**

---

## Artifacts Produced

| Artifact | Location | Purpose |
|----------|----------|---------|
| **L2.1 UI Intent Supertable** | `L2_1_UI_INTENT_SUPERTABLE.csv` | 52-row master table |
| **Control Proposal Register** | `CONTROL_PROPOSAL_REGISTER.md` | 6 proposed new controls |
| **Column Proposal Register** | `COLUMN_PROPOSAL_REGISTER.md` | 2 recommended new columns |
| **Exploratory Analysis** | `PHASE_2_1_EXPLORATORY_ANALYSIS.md` | Patterns, risks, insights |
| **Completion Report** | `PHASE_2_1_COMPLETION_REPORT.md` | This document |

All artifacts in: `design/l2_1/supertable/`

---

## Supertable Statistics

### Coverage

| Metric | Value |
|--------|-------|
| Domains | 5 |
| Subdomains | 8 |
| Topics | 15 |
| Total Rows (Panel × Order) | 52 |

### By Domain

| Domain | Rows | Write Rows | Activate Rows |
|--------|------|-----------|---------------|
| Overview | 3 | 0 | 0 |
| Activity | 10 | 0 | 0 |
| Incidents | 11 | 1 | 3 |
| Policies | 15 | 3 | 3 |
| Logs | 13 | 0 | 0 |

### By Order

| Order | Rows | Purpose |
|-------|------|---------|
| O1 | 15 | Summary/Snapshot (entry points) |
| O2 | 14 | List (action hubs) |
| O3 | 12 | Detail (focused view) |
| O4 | 6 | Context/Impact |
| O5 | 7 | Proof (terminal) |

---

## Control Derivation Summary

### Controls Applied (From Catalog)

| Control | Occurrences | Derivation Rule |
|---------|-------------|-----------------|
| FILTER | 14 | Filtering = YES |
| SORT | 14 | Ranking Dimension != NONE |
| SELECT_SINGLE | 10 | Selection Mode = SINGLE |
| SELECT_MULTI | 8 | Selection Mode = MULTI |
| DOWNLOAD | 15 | Download = YES |
| NAVIGATE | 37 | Order ≥ O2 |
| ACKNOWLEDGE | 2 | Activate Action = ACKNOWLEDGE |
| RESOLVE | 1 | Activate Action includes RESOLVE |

### Controls NOT Applied

| Control | Reason |
|---------|--------|
| ADD_TO_POLICY | No Write Action starts with ADD_ |
| ACTIVATE_KILL_SWITCH | Policies use ACTIVATE/DEACTIVATE, not KILL_SWITCH |

---

## Proposals Summary

### New Controls Proposed (6)

| Control | Status | Recommendation |
|---------|--------|----------------|
| ACTIVATE_TOGGLE | PROPOSED | Add — distinct from KILL_SWITCH |
| ADD_NOTE | PROPOSED | Add — new write intent |
| EXPORT_PDF | PROPOSED | Review — may be column instead |
| SEARCH | PROPOSED | Add — complements FILTER |
| CANCEL | PROPOSED | Elicitation required |
| REOPEN | PROPOSED | Elicitation required |

### New Columns Proposed (2 Recommended)

| Column | Status | Recommendation |
|--------|--------|----------------|
| danger_level | PROPOSED | ACCEPT |
| requires_interpreter | PROPOSED | ACCEPT |
| export_format_hint | PROPOSED | DEFER |
| bulk_limit_hint | PROPOSED | REJECT |
| terminal_order | PROPOSED | REJECT |
| entry_point | PROPOSED | REJECT |

---

## Flags and Escalations

### STOP Conditions Encountered: NONE

No blocking conditions were encountered during supertable construction.

### Flags for Phase 2 Elicitation

| ID | Flag | Resolution Needed |
|----|------|-------------------|
| FLAG_A1 | Overview domain has NO Customer Console API | Option A: Create API, Option B: Remove from L2.1 |
| FLAG_I3 | Policies GC_L NOT IMPLEMENTED | Is GC_L in scope for v1? |
| FLAG_I4 | Ranking Dimension semantics unclear | Single vs list format? |
| FLAG_F1 | Incident acknowledge irreversibility | Add REOPEN or document? |
| FLAG_A3 | Activity has no actions | Is CANCEL in scope? |

---

## Phase 2 Elicitation Questions (Consolidated)

### From Phase 1 (PIN-348)

1. Should Overview surfaces be removed from L2.1 seed (Founder-only)?
2. Should incidents be reopenable after resolution?
3. What is idempotency contract for acknowledge/resolve?
4. Are GC_L policy mutations planned for v1?
5. Should `ACT-INCIDENT-ESCALATE` be implemented or removed?

### From Phase 2.1 (New)

6. Should Overview domain support DOWNLOAD for health metrics?
7. Should Activity support CANCEL for active runs?
8. What is the semantic format for Ranking Dimension?
9. Should SEARCH be added to control catalog?
10. Should danger_level column be added?
11. Should requires_interpreter column be added?

---

## Completion Attestation

```
✔ All 5 domains covered
✔ All 15 topics enumerated
✔ All 52 Panel × Order rows created
✔ All base columns populated
✔ Controls derived, not invented
✔ Proposals explicitly flagged (6 controls, 6 columns)
✔ Insights documented in Exploratory Analysis
✔ No capability binding
✔ No execution assumptions
✔ No silent mutations
```

---

## Next Steps

1. **Human Review:** Accept/reject proposals in Control and Column Registers
2. **Phase 2 Elicitation:** Resolve 11 open questions
3. **Phase 2.2:** Capability binding (map supertable rows to capabilities)
4. **Phase 3:** L2.1 surface binding (map to seed surfaces)
5. **Phase 4:** Database application (apply schemas to Neon)

---

## References

- PIN-348 — Phase 1 Capability Intelligence Extraction
- PIN-347 — L2.1 Epistemic Layer Table-First Design
- Customer Console v1 Constitution
- L2.1 Surface Registry Seed (`l2_1_surface_registry.seed.sql`)
