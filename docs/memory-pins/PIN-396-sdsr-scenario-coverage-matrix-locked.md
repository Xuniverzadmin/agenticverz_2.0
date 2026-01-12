# PIN-396: SDSR Scenario Coverage Matrix — LOCKED

**Status:** 🔒 LOCKED
**Created:** 2026-01-11
**Category:** SDSR / Governance / System Contract
**Milestone:** Phase G Steady State

---

## Summary

Locked the authoritative SDSR–Aurora Scenario Coverage Matrix. This contract answers one question: *Which real-world system behaviors must exist before a capability is allowed to become OBSERVED?*

---

## Contract Location

```
docs/governance/SDSR_SCENARIO_COVERAGE_MATRIX.md
```

---

## Core Invariants (Constitutional)

| ID | Invariant |
|----|-----------|
| INV-SCM-001 | No button can appear without forensic evidence |
| INV-SCM-002 | Near-misses (SC-TH-N) must never unlock capabilities |
| INV-SCM-003 | Human vs Agent proof exists in SDSR, not UI |
| INV-SCM-004 | Missing observability is a first-class failure |
| INV-SCM-005 | Scenario class determines maximum yield |
| INV-SCM-006 | Panel binding is derived from capability status |

---

## 12 Canonical Scenario Classes

| Code    | Scenario Class          | Purpose                           |
|---------|-------------------------|-----------------------------------|
| SC-EX-S | Execution — Success     | Prove system can run work cleanly |
| SC-EX-F | Execution — Failure     | Prove failure produces artifacts  |
| SC-EX-D | Execution — Degraded    | Prove partial failure handling    |
| SC-TH-N | Near Threshold          | Prove detection without action    |
| SC-TH-B | Threshold Breach        | Prove incident creation           |
| SC-VI-A | Violation — Auto Action | Prove policy auto-enforcement     |
| SC-PO-H | Policy — HITL           | Prove human governance            |
| SC-PO-L | Policy — Lifecycle      | Prove activate/deactivate         |
| SC-TR-F | Trace — Full            | Prove end-to-end traceability     |
| SC-TR-G | Trace — Gap             | Prove blind-spot detection        |
| SC-ID-H | Identity — Human        | Prove human action path           |
| SC-ID-A | Identity — Agent        | Prove agent action path           |

**These do not change.** New scenarios are instances, not new classes.

---

## Scenario → Capability Yield Matrix (Prevents Overclaiming)

| Scenario Class | May Produce OBSERVED                 |
|----------------|--------------------------------------|
| SC-EX-S        | EXECUTE, TRACE                       |
| SC-EX-F        | ACKNOWLEDGE, ADD_NOTE                |
| SC-EX-D        | RESOLVE                              |
| SC-TH-N        | ❌ NONE (must remain INFRASTRUCTURE) |
| SC-TH-B        | ACKNOWLEDGE                          |
| SC-VI-A        | ACTIVATE, DEACTIVATE, RESOLVE        |
| SC-PO-H        | APPROVE, REJECT                      |
| SC-PO-L        | ACTIVATE, UPDATE_*                   |
| SC-TR-F        | TRACE, VIEW_EXECUTION_GRAPH          |
| SC-TR-G        | TRACE_GAP_DETECTED                   |
| SC-ID-H        | (identity evidence only)             |
| SC-ID-A        | (identity evidence only)             |

---

## Execution Order (Enforced)

| Order | Scenario Class    | Unlocks                       |
|-------|-------------------|-------------------------------|
| 1     | SC-TH-B           | ACKNOWLEDGE                   |
| 2     | SC-EX-D           | RESOLVE                       |
| 3     | SC-EX-S + SC-TR-F | EXECUTE, TRACE                |
| 4     | SC-PO-L           | ACTIVATE, UPDATE_*            |
| 5     | SC-TH-N           | ❌ (verify no unlock happens) |
| 6     | SC-TR-G           | verify blind-spot detection   |

---

## Implementation Scope (Minimal)

**Aurora:** No changes.

**SDSR only:**
1. Add `scenario_class` to scenario metadata
2. Add capability inference guard: validate yields against matrix

---

## What This Gives Us

After this matrix is enforced:

- No button can ever appear without **forensic evidence**
- Near-misses stop polluting capability truth
- Human vs Agent proof exists without UI hacks
- Missing observability becomes a *first-class failure*

---

## Related PINs

- [PIN-395](PIN-395-sdsr-scenario-taxonomy-and-capability-court-of-law.md) — Scenario Taxonomy (superseded by this lock)
- [PIN-393](PIN-393-sdsr-observation-class-mechanical-discriminator.md) — Observation Class Discriminator
- [PIN-394](PIN-394-sdsr-aurora-one-way-causality-pipeline.md) — One-Way Causality Pipeline
- [PIN-370](PIN-370-sdsr-activity-incident-lifecycle.md) — SDSR Activity/Incident Lifecycle

---

## Contract Artifact

`docs/governance/SDSR_SCENARIO_COVERAGE_MATRIX.md`

---

*This PIN locks a system contract. Modification requires founder approval.*
