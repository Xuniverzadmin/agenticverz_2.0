# Runtime v1 Freeze Notes

**Date:** 2025-12-26
**Status:** FROZEN

---

## Cleanup Executed

### Deleted Files (5)
- `guard/KillSwitchPage.tsx` - Customer authority leak
- `guard/LiveActivityPage.tsx` - Replaced by CustomerRunsPage
- `guard/LogsPage.tsx` - Raw logs are founder-only
- `guard/GuardDashboard.tsx` - Replaced by CustomerHomePage
- `guard/GuardOverview.tsx` - Replaced by CustomerHomePage

### Moved Files (1)
- `DecisionTimeline.tsx` → copied to `founder/components/`
  - **Note:** Original kept in `guard/incidents/` for incident investigation
  - **Architectural Question:** Should customers see decision timelines during incident investigation?
  - **Current State:** Both planes have access (customer = incidents, founder = full timeline)
  - **Recommendation:** Review if customer timeline should be simplified "outcome view" vs full decision details

---

## Build Verification

```
✓ built in 13.43s
✓ No blocking errors
✓ 6 warnings remaining (budget: 35)
```

---

## Domain Architecture Confirmed

| Domain | Pages | Status |
|--------|-------|--------|
| console.agenticverz.com | 10 customer pages | FROZEN |
| fops.agenticverz.com | 8+ founder pages | FROZEN |
| preflight-fops | DTO schema only | READY |
| preflight-console | DTO schema only | READY |

---

## Next Steps

1. Commit these changes
2. Tag as `runtime-v1.0.0-freeze`
3. Define beta success/failure criteria
4. Begin founder-led beta (3-7 users)

---

## Files Added This Phase

### Analysis Docs
- `DOMAIN_MAPPING_ANALYSIS.md` - Page inventory and domain mapping
- `WIREFRAME_GAP_ANALYSIS.md` - Contract/test scenario gap analysis

### New Customer Pages (Phase 5E-4)
- `CustomerRunsPage.tsx` - Run history & outcomes
- `CustomerLimitsPage.tsx` - Budget & rate limits
- `CustomerKeysPage.tsx` - API key management

### Preflight API
- `api/preflight/index.ts` - Domain constants, promotion rules
- `api/preflight/founder.ts` - FounderPreflightDTO
- `api/preflight/customer.ts` - CustomerPreflightDTO

---

## Governance Lock

From this point forward:
- No new pages without domain + plane justification
- Any new UI must answer: "Which contract does it exercise?"
- Feature freeze per PIN-183
