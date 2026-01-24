# P1-1.4 Dead/Suspicious Backend Code Inventory

**Generated:** 2026-01-06
**Phase:** Phase 1 - Repository Reality Alignment
**Reference:** PIN-316

---

## Summary

| Category | Count |
|----------|-------|
| API files not imported | 2 |
| API files disabled | 1 |
| Legacy routes | 1 file (23 routes) |

## API Files Not Imported (Dead Code)

| File | Status | Recommendation |
|------|--------|----------------|
| `app/api/auth_helpers.py` | NOT IMPORTED | Review and either mount or delete |
| `app/api/founder_review.py` | NOT IMPORTED | **BUG: Recently added but not mounted** |

### Action Required: founder_review.py

This file was added as part of CAP-005/CAP-006 work but the router was never mounted in `main.py`. This is a gap that needs to be fixed.

```python
# Add to main.py imports:
from .api.founder_review import router as founder_review_router

# Add to router mounting:
app.include_router(founder_review_router)  # /fdr/contracts/* - Founder Review Gate
```

## Explicitly Disabled API Files

| File | Status | Reason |
|------|--------|--------|
| `app/api/tenants.py` | DISABLED | M21 - Premature for beta stage |

## Legacy Routes (Quarantine Candidate)

**File:** `app/api/legacy_routes.py`

This file contains 23 legacy routes that return 410 Gone for deprecated paths:
- `/dashboard/*`
- `/operator/*`
- `/demo/*`
- `/simulation/*`

**Recommendation:** Keep for backwards compatibility during transition, then remove.

## Classification Summary

| Classification | Files | Action |
|----------------|-------|--------|
| Legacy | 1 | Keep (provides 410 responses) |
| Orphaned | 1 | Fix (mount founder_review.py) |
| Speculative | 0 | - |
| Disabled | 1 | Keep disabled per M21 decision |

## Acceptance Criteria

- [x] Dead/suspicious code identified
- [x] Classification complete (legacy/orphaned/speculative)
- [x] No deletions performed (facts only)

## Immediate Action Items

1. **CRITICAL:** Mount `founder_review_router` in main.py
2. Review `auth_helpers.py` for removal or integration
