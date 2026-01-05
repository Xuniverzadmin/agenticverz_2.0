# PIN-300: Semantic Promotion Gate - L2 Intent Declaration Requirement

**Status:** 📋 CONSTITUTIONAL
**Created:** 2026-01-05
**Category:** Governance / Promotion
**Milestone:** Tech Debt Clearance

---

## Summary

Establishes the Semantic Promotion Gate: No L2 surface may be promoted or consumed by L1 without an explicit intent declaration. Structural classification produces zero eligibility for promotion. Intent must declare question answered, domain placement, authority semantics, source of truth, RBAC visibility, and L1 consumption contract.

---

## Details

## Problem Statement

Structural classification (UNIQUE/DUPLICATE/LEGACY/etc.) is necessary but NOT sufficient for promotion.

**The Gap:**
- Structural analysis tells us a file EXISTS
- It does NOT tell us what it MEANS
- L1 cannot safely consume L2 without knowing semantic intent
- Inference by L1 is a governance violation

---

## Solution: Semantic Promotion Gate

### Core Invariant (Constitutional)

> **Nothing is "promoted" unless its intent is declared, reviewable, and consumable by L1 without inference.**

### Gate Requirements

For every L2 surface to be promotable:

1. **Intent Declaration Required** — Stored in `/docs/intents/L2_<surface>_INTENT.yaml`
2. **Intent Completeness Check** — All 8 sections must be filled
3. **Semantic Consistency Check** — L2 intent aligns with L4 service authority

---

## Intent Declaration Template

Location: `docs/intents/L2_INTENT_TEMPLATE.yaml`

### Required Sections

| Section | Purpose |
|---------|---------|
| 1. Semantic Purpose | What question does this answer? What are non-goals? |
| 2. Domain Placement | Which frozen domain? Why? |
| 3. Authority Semantics | Projection or control? Mutates state? |
| 4. Source of Truth | L4 service? Derived? Rules? |
| 5. RBAC & Visibility | Who can see? Cross-tenant? |
| 6. L1 Consumption Contract | What UI allowed? What forbidden? |
| 7. Invariants | Forbidden assumptions |
| 8. Promotion Decision | Founder approval record |

---

## Promotion Flow

```
STRUCTURAL CLASSIFICATION
    ↓
    (produces: "Structurally valid, semantically undefined")
    ↓
INTENT DECLARATION
    ↓
    (produces: docs/intents/L2_<surface>_INTENT.yaml)
    ↓
INTENT COMPLETENESS CHECK
    ↓
    (validates: all 8 sections filled)
    ↓
SEMANTIC CONSISTENCY CHECK
    ↓
    (validates: L2 intent aligns with L4 authority)
    ↓
FOUNDER REVIEW
    ↓
    (produces: APPROVED | REJECTED | REQUEST_CHANGE)
    ↓
GOVERNED PROMOTION
    ↓
    (produces: Structural + Semantic + Approved)
```

---

## Blocking Rules

| Rule | Condition | Response |
|------|-----------|----------|
| SEM-001 | Missing intent file | BLOCK promotion |
| SEM-002 | Incomplete intent | BLOCK promotion |
| SEM-003 | L2/L4 authority mismatch | BLOCK promotion |
| SEM-004 | L1 would require inference | BLOCK promotion |
| SEM-005 | Cross-domain leakage | BLOCK promotion |

---

## What Claude Cannot Do

- Treat structural classification as promotion
- Allow L1 to bind to L2 without semantic declaration
- Infer UI meaning from code shape
- Auto-approve intent declarations
- Override founder decisions

---

## What Claude Must Do

- Halt if intent is unclear
- Halt if L1 meaning would require inference
- Halt if semantic ownership is disputed
- Present intent files for founder review
- Record all decisions explicitly

---

## Files

- `docs/intents/L2_INTENT_TEMPLATE.yaml` — Canonical template
- `docs/intents/L2_<surface>_INTENT.yaml` — Per-surface declarations

---

## References

- PIN-299 (Tech Debt Clearance)
- PIN-298 (Frontend Constitution Survey)
- docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md (frozen domains)


---

## Related PINs

- [PIN-299](PIN-299-.md)
- [PIN-298](PIN-298-.md)
- [PIN-290](PIN-290-.md)
