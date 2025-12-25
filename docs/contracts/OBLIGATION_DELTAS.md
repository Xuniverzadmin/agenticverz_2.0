# Obligation Deltas

**Created:** 2025-12-25
**Source:** M0-M27 Classification (Phase 3)
**Status:** ACCEPTED - Deltas incorporated into DECISION contract v0.2

---

## Purpose

This document captures obligations that emerged from milestone classification
but are not fully covered by the skeletal contracts. These are Phase-4 inputs.

---

## Delta Entry Format

```
Milestone: Mx
Contract: [PRE-RUN | CONSTRAINT | DECISION | OUTCOME]
New Obligation:
  - [description]
Reason:
  - [why existing obligations are insufficient]
Status:
  - Proposed | Accepted | Rejected
```

---

## Delta 1: Decision Source

```
Milestone: M10 (Recovery Suggestion Engine)
Contract: DECISION
New Obligation:
  - decision_source: human | system | hybrid
Reason:
  - Current DECISION contract requires recording "who decided" but does not
    distinguish between human-approved decisions, system-autonomous decisions,
    and hybrid decisions requiring human confirmation.
  - Recovery engine introduces human-in-loop approval workflow where the
    source of the decision (human vs system) affects trust interpretation.
Status:
  - ACCEPTED (incorporated in DECISION contract v0.2)
```

---

## Delta 2: Decision Trigger

```
Milestone: M14 (Self-Improving Loop)
Contract: DECISION
New Obligation:
  - decision_trigger: explicit | autonomous | reactive
Reason:
  - Current DECISION contract requires recording decisions but does not
    distinguish what triggered the decision.
  - Self-improving loop makes decisions without explicit trigger (drift
    detected → learning triggered automatically).
  - Without trigger classification, observers cannot determine if a decision
    was requested or self-initiated.
Status:
  - ACCEPTED (incorporated in DECISION contract v0.2)
```

---

## Summary

| Delta | Contract | Field | Values | Status |
|-------|----------|-------|--------|--------|
| 1 | DECISION | decision_source | human \| system \| hybrid | ACCEPTED |
| 2 | DECISION | decision_trigger | explicit \| autonomous \| reactive | ACCEPTED |

---

## Stabilization Proof

After M10 and M14, no new obligations were identified:

| Milestone Range | New Obligations |
|-----------------|-----------------|
| M0 - M9 | 0 |
| M10 | 1 (Delta 1) |
| M11 - M13 | 0 |
| M14 | 1 (Delta 2) |
| M15 - M27 | 0 |

**Consecutive milestones without new obligation:** 13 (M15 → M27)

This meets the stabilization criterion (≥ 3-4 consecutive milestones without new obligations).

---

## Next Steps (Phase 4 Preview)

When implementation begins:

1. Evolve DECISION contract to include `decision_source` and `decision_trigger`
2. Update COVERAGE_MATRIX.md to reflect contract evolution
3. No other contracts require evolution from M0-M27 analysis

---

## Rules

- No implementation until contracts are evolved
- No prioritization yet
- Just truth capture
