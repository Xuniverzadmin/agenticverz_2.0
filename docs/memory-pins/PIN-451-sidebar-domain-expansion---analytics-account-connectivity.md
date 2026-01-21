# PIN-451: Sidebar Domain Expansion - Analytics, Account, Connectivity

**Status:** ✅ COMPLETE
**Created:** 2026-01-19
**Category:** Frontend / UI

---

## Summary

Added Analytics, Account, and Connectivity domains to the Customer Console sidebar via scaffolding integration and INTENT_LEDGER topology update.

---

## Details

## Overview

Extended the Customer Console sidebar from 5 core domains to 8 domains by adding Analytics, Account, and Connectivity.

## Problem

The sidebar was only showing 5 domains (Overview, Activity, Incidents, Policies, Logs) from the projection. Analytics, Account, and Connectivity were missing despite having panel definitions in INTENT_LEDGER.md.

## Root Cause

1. **Analytics** - Missing from the Topology section in INTENT_LEDGER.md (panels existed but domain wasn't declared)
2. **Account/Connectivity** - Panels have `State: EMPTY` so no intent YAMLs were generated, meaning they don't appear in projection
3. **Scaffolding gap** - Analytics wasn't in ui_plan_scaffolding.ts fallback

## Solution

### 1. Added ANALYTICS to INTENT_LEDGER Topology

```markdown
### ANALYTICS

#### COST
- USAGE (5 slots)
```

Location: `design/l2_1/INTENT_LEDGER.md:58-61`

### 2. Added Analytics to Scaffolding

Added Analytics domain to `ui_plan_scaffolding.ts` with:
- order: 6
- route: /precus/analytics
- subdomain: COST with topic USAGE

Updated domain ordering:
- Analytics: 6
- Account: 7 (was 6)
- Connectivity: 8 (was 7)

Location: `website/app-shell/src/contracts/ui_plan_scaffolding.ts:184-198`

### 3. Ran Pipeline

```bash
python3 scripts/tools/sync_from_intent_ledger.py
DB_AUTHORITY=neon ./scripts/tools/run_aurora_l2_pipeline.sh
```

## Final Sidebar Structure

| Order | Domain | Source | Status |
|-------|--------|--------|--------|
| 0 | OVERVIEW | Projection | BOUND |
| 1 | ACTIVITY | Projection | BOUND |
| 2 | INCIDENTS | Projection | BOUND |
| 3 | POLICIES | Projection | BOUND |
| 4 | LOGS | Projection | BOUND |
| 6 | Analytics | Scaffolding | EMPTY |
| 7 | Account | Scaffolding | EMPTY |
| 8 | Connectivity | Scaffolding | EMPTY |

## Files Modified

- `design/l2_1/INTENT_LEDGER.md` - Added ANALYTICS to Topology
- `website/app-shell/src/contracts/ui_plan_scaffolding.ts` - Added Analytics, reordered Account/Connectivity
- `design/l2_1/AURORA_L2_SEMANTIC_REGISTRY.yaml` - Updated to 8 domains (auto-generated)

## Next Steps (Future Work)

To move these domains from scaffolding to projection:

1. **Create capabilities** for Account, Connectivity, Analytics panels
2. **Write SDSR scenarios** to observe the capabilities
3. **Run E2E validation** to generate observation evidence
4. **Apply observations** to promote DECLARED → OBSERVED

## Related

- PIN-450: SDSR System Hardening (fixed duplicate domains bug)
- Customer Console Constitution: Defines domain structure

---

## Related PINs

- [PIN-450](PIN-450-.md)
