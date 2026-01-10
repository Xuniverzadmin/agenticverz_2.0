# PIN-385: SDSR UI Pipeline Integration Status

**Status:** 🔄 IN PROGRESS (Paused for Context Switch)
**Created:** 2026-01-10
**Category:** SDSR / UI Pipeline
**Milestone:** SDSR-UI-Integration

---

## Summary

SDSR → UI projection binding and validation spec created. Gap exposure complete. Fixes pending user decision.

---

## What Was Done

### Tasks Completed

| Task | Status | Output |
|------|--------|--------|
| Load L2.1 UI governance artifacts | ✅ DONE | ui_projection_lock.json, PanelContentRegistry.tsx |
| Map SDSR-E2E-001/003/004 to UI projections | ✅ DONE | Coverage matrix in spec |
| Produce UI Validation Spec per Scenario | ✅ DONE | `docs/governance/SDSR_UI_VALIDATION_SPEC.md` |
| Document explicit gaps | ✅ DONE | 5 gaps identified |

### Artifacts Created

| File | Purpose |
|------|---------|
| `docs/governance/SDSR_UI_VALIDATION_SPEC.md` | Full validation spec with binary criteria |
| PIN-381 update | Added UI validation section |

---

## Current Status

### Scenario UI Readiness

| Scenario | UI Validatable | Blocking Issue |
|----------|----------------|----------------|
| SDSR-E2E-001 | ✅ YES | None |
| SDSR-E2E-003 | ✅ YES | None |
| SDSR-E2E-004 | ⚠️ PARTIAL | POL-RU-O2 missing from projection |

### Gaps Identified (Not Fixed)

| Gap ID | Severity | Description | Fix Required |
|--------|----------|-------------|--------------|
| GAP-003 | **HIGH** | POL-RU-O2 not in ui_projection_lock.json | Add intent row → run pipeline |
| GAP-001 | **HIGH** | POL-RU-O2 not bound in PanelContentRegistry | Add renderer (after GAP-003) |
| GAP-002 | INFO | prevention_records panel missing | Optional |
| Control | LOW | ACKNOWLEDGE action not implemented | Add mutation to OpenIncidentsList |
| Control | LOW | Proposal SDSR badge not rendered | Add is_synthetic check to ProposalListItem |

---

## What Needs To Be Done (When Resuming)

### To Fix GAP-003 + GAP-001 (Policy Rules Panel)

```bash
# 1. Add intent row to CSV (for POLICIES.RULES.ACTIVE_RULES topic)
# Edit: design/l2_1/supertable/L2_1_UI_INTENT_SUPERTABLE.csv

# 2. Run L2.1 pipeline
python3 scripts/tools/l2_pipeline.py generate vN
python3 scripts/tools/l2_raw_intent_parser.py --input design/l2_1/supertable/l2_supertable_vN_cap_expanded.xlsx
./scripts/tools/run_l2_pipeline.sh

# 3. Copy to public
cp design/l2_1/ui_contract/ui_projection_lock.json website/app-shell/public/projection/

# 4. Add renderer to PanelContentRegistry.tsx
# Function: PolicyRulesList (fetches from /api/v1/policy-rules)
```

### To Fix Control Gaps

1. **ACKNOWLEDGE action** - Add mutation to `OpenIncidentsList` in PanelContentRegistry.tsx
2. **Proposal SDSR badge** - Add `is_synthetic` check to `ProposalListItem` component

---

## Key Files Reference

| File | Role |
|------|------|
| `docs/governance/SDSR_UI_VALIDATION_SPEC.md` | Full spec (read this first) |
| `design/l2_1/ui_contract/ui_projection_lock.json` | Projection (source of truth) |
| `website/app-shell/src/components/panels/PanelContentRegistry.tsx` | Panel renderers |
| `backend/scripts/sdsr/scenarios/SDSR-E2E-004.yaml` | Scenario referencing POL-RU-O2 |

---

## Governance Compliance

- ✅ Did NOT invent UI - only validated existing
- ✅ Did NOT fix gaps - only exposed them
- ✅ Used binary criteria (exists/visible/matches_backend)
- ✅ Referenced projection lock as source of truth
- ✅ Followed SDSR-UI-001 through SDSR-UI-004

---

## Decision Points (For User)

1. **Should we add POL-RU-O2 to the projection?**
   - Requires L2.1 pipeline update
   - E2E-004 cannot be fully UI-validated without it

2. **Should we fix the control gaps?**
   - ACKNOWLEDGE action for incidents
   - SDSR badge for proposals

3. **Should we create prevention_records panel?**
   - Currently informational gap only
   - Useful for debugging suppression

---

## Related PINs

- PIN-381: SDSR E2E Testing Protocol Implementation
- PIN-384: E2E-004 Certification
- PIN-370: SDSR Architecture
- PIN-352: L2.1 UI Projection Pipeline
