# PIN-464: HOC Customer Domain Comprehensive Audit

**Status:** ✅ COMPLETE
**Created:** 2026-01-23
**Category:** Architecture / HOC Audit

---

## Summary

Deep audit of all 10 hoc/cus/* domains for duplicates, imports, semantics, and deprecated API usage

---

## Details

## Purpose

Comprehensive audit of the House of Cards (HOC) customer domain structure to identify:
- Duplicate files and functions
- Import/export issues
- Semantic violations
- Deprecated API usage (datetime.utcnow())

## Scope

All 10 domains under `app/hoc/cus/`:
1. account
2. activity
3. analytics
4. api_keys
5. general
6. incidents
7. integrations
8. logs
9. overview
10. policies

## Key Findings

### 1. datetime.utcnow() Deprecation (FIXED)

Found 42 occurrences of deprecated `datetime.utcnow()` across 12 files.

**Resolution:**
- Created shared utility: `app/hoc/cus/general/L5_utils/time.py`
- Replaced all occurrences with `utc_now()` which returns timezone-aware `datetime.now(timezone.utc)`

**Files Fixed:**
| File | Occurrences |
|------|-------------|
| overview/facades/overview_facade.py | 3 |
| incidents/engines/incident_pattern_service.py | 2 |
| incidents/engines/recurrence_analysis_service.py | 1 |
| activity/engines/attention_ranking_service.py | 1 |
| policies/facades/policies_facade.py | 7 |
| policies/controls/engines/runtime_switch.py | 9 |
| activity/engines/signal_feedback_service.py | 3 |
| activity/engines/pattern_detection_service.py | 1 |
| activity/engines/cost_analysis_service.py | 1 |
| analytics/engines/pattern_detection.py | 3 |
| policies/engines/policy_proposal.py | 5 |
| analytics/engines/prediction.py | 6 |

### 2. Misplaced Audit Reports (FIXED)

5 audit reports were in wrong location (`app/hoc/` instead of their domain folders).

**Relocated:**
- `HOC_policies_detailed_audit_report.md` → `customer/policies/`
- `HOC_policies_deep_audit_report.md` → `customer/policies/`
- `HOC_logs_detailed_audit_report.md` → `customer/logs/`
- `HOC_analytics_detailed_audit_report.md` → `customer/analytics/`
- `HOC_integrations_detailed_audit_report.md` → `customer/integrations/`

### 3. Legacy Duplicates (INTENTIONAL)

Files in `app/services/` that duplicate HOC files are intentional for backward compatibility.

### 4. Import Fix (account domain)

Fixed broken import in `identity_resolver.py` - changed relative import to absolute import from `app.hoc.int.platform.iam.engines.iam_service`.

### 5. Removed Triple Duplicate

Deleted `app/hoc/cus/policies/L5_engines/validator_service.py` (existed in 3 locations).

## Audit Reports

All 10 domains now have co-located audit reports:

| Domain | Report |
|--------|--------|
| account | HOC_account_detailed_audit_report.md |
| activity | HOC_activity_deep_audit_report.md |
| analytics | HOC_analytics_detailed_audit_report.md |
| api_keys | HOC_api_keys_detailed_audit_report.md |
| general | HOC_general_deep_audit_report.md |
| incidents | HOC_incidents_deep_audit_report.md |
| integrations | HOC_integrations_detailed_audit_report.md |
| logs | HOC_logs_detailed_audit_report.md |
| overview | HOC_overview_detailed_audit_report.md |
| policies | HOC_policies_detailed_audit_report.md |

## Shared Utility Created

```python
# app/hoc/cus/general/L5_utils/time.py
from datetime import datetime, timezone

def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)
```

## Status

- [x] All 10 domains audited
- [x] 42 datetime.utcnow() occurrences fixed
- [x] Shared time utility created
- [x] Audit reports relocated to correct folders
- [x] Overview audit report updated to reflect fixes
- [x] 100% audit coverage confirmed
