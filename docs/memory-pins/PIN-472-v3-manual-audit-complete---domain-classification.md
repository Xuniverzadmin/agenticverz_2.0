# PIN-472: V3 Manual Audit Complete - Domain Classification

**Status:** ✅ COMPLETE
**Created:** 2026-01-26
**Category:** HOC / Domain Classification

---

## Summary

Manual audit of 187 AMBIGUOUS files using Decision Ownership lens. 100 confirmed (53%), 87 misplaced (47%). Updated DOMAIN_CRITERIA.yaml to v1.1 with lessons learned.

---

## Details

## Overview

Completed V3 Manual Audit of all 187 AMBIGUOUS files in `hoc/cus/` using the Decision Ownership lens.

## Audit Results

| Metric | Value |
|--------|-------|
| **Total Files** | 187 |
| **Confirmed** | 100 (53%) |
| **Misplaced** | 87 (47%) |

### Domain Performance

| Domain | Confirmation Rate |
|--------|------------------|
| general | 100% (30/30) |
| activity | 80% (4/5) |
| logs | 51% (18/35) |
| incidents | 50% (12/24) |
| analytics | 47% (7/15) |
| policies | 44% (24/55) |
| account | 33% (2/6) |
| integrations | 21% (3/14) |

## Key Findings

1. **general domain is gold standard** - 100% confirmation. Cross-domain and system-wide items correctly centralized.

2. **policies domain overloaded** - 31 misplaced files (controls, general, logs items landed here)

3. **integrations domain misused as catch-all** - Only 21% confirmation rate

4. **controls domain underutilized** - Many limit/threshold/killswitch items scattered

5. **Adapters should follow their domain** - L3 adapters were placed in wrong domains

## DOMAIN_CRITERIA.yaml v1.1 Updates

Based on audit findings, updated criteria with:

- **controls**: +16 qualifier_phrases (limit drivers, budget enforcement, alert rules)
- **policies**: +19 veto_phrases (prevent overloading with controls/general/logs items)
- **integrations**: +12 veto_phrases (prevent catch-all misuse)
- **general**: +16 qualifier_phrases (cross-domain, lifecycle, scheduler patterns)
- **logs**: +12 qualifier_phrases (verdict, certificate, SOC2, compliance)
- **account**: +5 qualifier_phrases (identity resolution per user correction)

## Artifacts

| File | Purpose |
|------|---------|
| `backend/app/hoc/cus/_domain_map/V3_MANUAL_AUDIT_WORKBOOK.md` | Full detailed audit |
| `docs/architecture/console_domains/DOMAIN_CRITERIA.yaml` | Updated v1.1 criteria |

## Next Steps (Optional)

- Create migration plan for 87 misplaced files
- Execute file moves with git history preservation
- Re-run domain classifier with v1.1 criteria to measure improvement

---

## Related PINs

- [PIN-470](PIN-470-.md)
