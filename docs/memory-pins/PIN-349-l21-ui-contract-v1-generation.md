# PIN-349: L2.1 UI Contract v1 Generation

**Status:** ✅ COMPLETE
**Created:** 2026-01-07
**Category:** Customer Console / L2.1 Orchestration

---

## Summary

Generated versioned UI contract JSON from L2 supertable v3 with full traceability

---

## Details

## Purpose

Transform `l2_supertable_v3_cap_expanded.xlsx` into a **versioned UI contract JSON** that can be rendered by the TSX frontend without code mutation.

## Artifacts Generated

| Artifact | Path |
|----------|------|
| UI Contract JSON | `website/app-shell/src/contracts/ui_contract.v1.json` |
| Summary Report | `design/l2_1/ui_contract/ui_contract_v1_summary.md` |
| Generator Script | `scripts/tools/ui_contract_generator.py` |

## Contract Statistics

| Metric | Value |
|--------|-------|
| Total Panels | 52 |
| SAFE Panels | 38 |
| QUESTIONABLE Panels | 14 |
| Total Controls | 145 |
| Enabled Controls | 136 |
| Disabled Controls | 9 |

## Domain Breakdown

| Domain | Panels |
|--------|--------|
| Overview | 3 |
| Activity | 10 |
| Incidents | 11 |
| Policies | 15 |
| Logs | 13 |

## Traceability

Each contract panel includes `_source` field for bidirectional lookup:

```json
"_source": {
  "row_uids": ["81ff29d26153"],
  "capabilities": ["CAP-INC-LIST", "CAP-INC-GET", ...],
  "intents": ["READ", "ACTIVATE:ACKNOWLEDGE"]
}
```

| Direction | Key | Lookup Method |
|-----------|-----|---------------|
| Contract → Supertable | `_source.row_uids` | `df[df["row_uid"] == uid]` |
| Supertable → Contract | `Panel ID` | `contract["domains"][*]["panels"][*]["panel_id"]` |

## QUESTIONABLE Actions Gated (Not Hidden)

| Panel | Disabled Controls |
|-------|-------------------|
| Incidents / Open Incidents List | ACKNOWLEDGE |
| Incidents / Incident Detail | ADD_NOTE, ACTIVATE |
| Policies / Budget Policy Detail | UPDATE_THRESHOLD, ACTIVATE |
| Policies / Rate Limit Detail | UPDATE_LIMIT, ACTIVATE |
| Policies / Approval Rule Detail | UPDATE_RULE, ACTIVATE |

## Hard Rules Applied

- Never generate or edit TSX
- Never infer business logic
- Never hide QUESTIONABLE actions
- Never change the XLSX
- Only transform → never decide

## Integrity Statement

> **No semantics resolved. UI reflects system uncertainty.**

The contract:
- Does NOT decide whether ACK/RESOLVE is reversible
- Does NOT decide whether policy mutations are allowed
- Does NOT infer missing capabilities
- Does NOT hide QUESTIONABLE actions from the user

## Related PINs

- PIN-348: L2.1 UI Intent Supertable (source)
- PIN-347: L2.2 Capability Binding (bindings)

## Attestation

```
✔ ui_contract.v1.json generated
✔ No TSX touched
✔ QUESTIONABLE actions gated, not hidden
✔ Overview read-only and navigational
✔ Full traceability via _source field
✘ No business decisions made
✘ No semantics resolved
```
