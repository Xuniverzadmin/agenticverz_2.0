# PIN-350: L2 Governed Pipeline with Approval Gate

**Status:** ✅ COMPLETE
**Created:** 2026-01-07
**Category:** Customer Console / L2.1 Orchestration

---

## Summary

Governed pipeline for supertable generation with human approval gate before UI contract consumption

---

## Details

## Purpose

Provide a governed workflow for L2.1 supertable → UI contract generation with:
- Fast distillation (generate many versions)
- Human approval gate (only promoted version feeds UI contract)
- Version tracking and sync status

## Problem Solved

Previously, `l2_cap_expander.py` and `ui_contract_generator.py` were independent scripts with no linkage. If a new supertable was generated, the UI contract would become stale without warning.

## Solution

Single pipeline script with approval gate:

```
┌──────────────┐     ┌──────────────┐
│ Intent CSV   │ ──▶ │ v4.xlsx      │ ──┐
└──────────────┘     └──────────────┘   │
       │             ┌──────────────┐   │    ┌─────────────────┐
       ├───────────▶ │ v5.xlsx      │ ──┼──▶ │ HUMAN REVIEW    │
       │             └──────────────┘   │    │ "promote v5"    │
       │             ┌──────────────┐   │    └────────┬────────┘
       └───────────▶ │ v6.xlsx      │ ──┘             │
                     └──────────────┘           APPROVAL GATE
                                                      │
                                                      ▼
                                          ┌──────────────────┐
                                          │ ui_contract.json │
                                          │ (from v5 only)   │
                                          └──────────────────┘
```

## Commands

| Command | Action | Approval Required |
|---------|--------|-------------------|
| `generate v4` | Create new supertable version | No |
| `list` | Show all versions + status | No |
| `promote v4` | Approve version → regenerate contract | **Yes** |
| `status` | Check approved version + sync status | No |
| `demote` | Remove approval | Yes |

## Usage

```bash
# Generate multiple versions (fast, no approval)
python3 scripts/tools/l2_pipeline.py generate v4
python3 scripts/tools/l2_pipeline.py generate v5

# Review XLSXs, pick the best

# Promote approved version (requires confirmation)
python3 scripts/tools/l2_pipeline.py promote v5
# → Prompts: "Proceed? [y/N]"

# Check status
python3 scripts/tools/l2_pipeline.py status
```

## Artifacts

| Artifact | Path |
|----------|------|
| Pipeline Script | `scripts/tools/l2_pipeline.py` |
| Version Manifest | `design/l2_1/supertable/l2_supertable_manifest.json` |

## Governance Rules

- Multiple XLSX can be generated (distillation phase)
- Only ONE version approved at a time
- UI contract ONLY regenerated on explicit `promote`
- Promotion requires human confirmation (`[y/N]`)
- Manifest tracks all versions + approval history
- Status shows if contract is IN SYNC or STALE

## Traceability Chain

```
L2_1_UI_INTENT_SUPERTABLE.csv
        ↓ [l2_pipeline.py generate]
l2_supertable_vN_cap_expanded.xlsx (CANDIDATE)
        ↓ [l2_pipeline.py promote] ← HUMAN APPROVAL
l2_supertable_vN_cap_expanded.xlsx (APPROVED)
        ↓ [auto-triggered]
ui_contract.v1.json
```

## Attestation

```
✔ Pipeline script implemented
✔ Version manifest tracking
✔ Approval gate with confirmation
✔ Sync status detection
✔ Demote capability for rollback
```

---

## Related PINs

- [PIN-349](PIN-349-.md)
- [PIN-348](PIN-348-.md)
