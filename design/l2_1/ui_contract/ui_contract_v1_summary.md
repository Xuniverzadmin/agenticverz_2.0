# UI Contract v1 Summary Report

**Generated:** 2026-01-07T16:12:16.688181+00:00
**Source:** l2_supertable_v3_cap_expanded.xlsx
**Status:** DRAFT_UI_DRIVING

---

## Domain Summary

| Domain | Panels |
|--------|--------|
| Overview | 3 |
| Activity | 10 |
| Incidents | 11 |
| Policies | 15 |
| Logs | 13 |

**Total Panels:** 52

---

## Control Statistics

| Metric | Count |
|--------|-------|
| Total Controls | 145 |
| Enabled Controls | 136 |
| Disabled Controls | 9 |

---

## Binding Status Breakdown

| Status | Panels |
|--------|--------|
| SAFE | 38 |
| QUESTIONABLE | 14 |

---

## QUESTIONABLE Actions Surfaced to UI

The following panels have QUESTIONABLE binding status, meaning their WRITE/ACTIVATE
controls are **disabled** in the UI with a visible reason:

- **Incidents / Open Incidents List**: ACKNOWLEDGE
- **Incidents / Incident Detail**: ADD_NOTE, ACTIVATE
- **Policies / Budget Policy Detail**: UPDATE_THRESHOLD, ACTIVATE
- **Policies / Rate Limit Detail**: UPDATE_LIMIT, ACTIVATE
- **Policies / Approval Rule Detail**: UPDATE_RULE, ACTIVATE

---

## Integrity Statement

> **No semantics resolved. UI reflects system uncertainty.**

This contract:
- Does NOT decide whether ACK/RESOLVE is reversible
- Does NOT decide whether policy mutations are allowed
- Does NOT infer missing capabilities
- Does NOT hide QUESTIONABLE actions from the user

The UI will display disabled controls with visible reasons, allowing operators
to understand system constraints without false confidence.

---

## Attestation

```
✔ 52 panels transformed
✔ 136 controls enabled
✔ 9 controls disabled (with reasons)
✔ 14 QUESTIONABLE panels surfaced
✔ Overview domain: READ + NAVIGATE only
✘ No business decisions made
✘ No semantics resolved
```
