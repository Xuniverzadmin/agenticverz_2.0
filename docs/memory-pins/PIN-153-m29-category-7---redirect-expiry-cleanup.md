# PIN-153: M29 Category 7 - Redirect Expiry & Cleanup

**Status:** COMPLETE
**Created:** 2025-12-24
**Category:** M29 Transition / Route Cleanup
**Milestone:** M29

---

## Summary

Eliminate legacy route paths, return 410 Gone for deprecated endpoints, and create CI guardrails to prevent regression.

---

## Overview

M29 Category 7 closes the loop on route transitions from legacy to new domain architecture. The goal is to lock the new mental model and prevent accidental regression to old patterns.

## Core Invariants

1. **No bare-path redirects** - Legacy paths return 410 Gone, not 301/302
2. **CI guardrails** - Tests fail on legacy route access
3. **Documentation cleaned** - Only reference new domains
4. **Delete, don't hide** - Remove old route files, don't comment them out

## Forbidden Paths

| Path | Original Purpose | Disposition |
|------|-----------------|-------------|
| `/dashboard` | Human admin dashboard | 410 Gone - Not for MVP customers |
| `/operator/*` | Old operator console | 410 Gone - Merged into `/ops/*` |
| `/demo/*` | Sales simulation tools | 410 Gone - Removed in M28 |
| `/simulation/*` | Pre-M29 testing tools | 410 Gone - Not for production |

## Valid Paths (NOT deprecated)

| Path | Purpose | Auth Domain |
|------|---------|-------------|
| `/metrics` | Prometheus metrics | Internal (no auth) |
| `/health`, `/healthz` | Health checks | Internal |
| `/ops/*` | Founder intelligence console | FOPS |
| `/guard/*` | Customer console | Console |
| `/api/v1/*` | SDK and machine APIs | API Key |
| `/v1/*` | OpenAI-compatible proxy | API Key |
| `/cost/*` | Cost intelligence | API Key |

## Implementation

### 1. Legacy Routes Handler

File: `backend/app/api/legacy_routes.py`

```python
# 410 Gone responses for deprecated endpoints
@router.get("/dashboard", status_code=410)
@router.get("/operator/{path:path}", status_code=410)
@router.get("/demo/{path:path}", status_code=410)
@router.get("/simulation/{path:path}", status_code=410)
```

### 2. CI Guardrail Tests

File: `backend/tests/test_category7_legacy_routes.py`

```python
# Tests that verify legacy paths return 410 Gone
# Tests that verify no redirects exist
```

## Files Created

| File | Purpose |
|------|---------|
| `backend/app/api/legacy_routes.py` | 410 Gone handlers |
| `backend/tests/test_category7_legacy_routes.py` | CI guardrail tests |

## Files Modified

| File | Changes |
|------|---------|
| `backend/app/main.py` | Register legacy_routes router |

## Test Results

```
tests/test_category7_legacy_routes.py: 40 passed in 5.95s
```

### Test Classes
- TestLegacyPathsReturn410 (22 tests)
- TestNoRedirects (5 tests)
- TestMigrationGuidance (4 tests)
- TestValidPathsStillWork (5 tests)
- TestCategoryInvariants (2 tests)
- TestLegacyRouterRegistration (2 tests)

## Exit Checklist

| Requirement | Status |
|-------------|--------|
| `/dashboard` returns 410 | ✅ COMPLETE |
| `/operator/*` returns 410 | ✅ COMPLETE |
| `/demo/*` returns 410 | ✅ COMPLETE |
| `/simulation/*` returns 410 | ✅ COMPLETE |
| CI tests for legacy paths | ✅ COMPLETE (40 tests) |
| No redirect responses (301/302) | ✅ VERIFIED |
| Valid paths unaffected | ✅ VERIFIED |

## Related PINs

- [PIN-152](PIN-152-m29-category-6---founder-action-paths-backend.md) - Category 6
- [PIN-145](PIN-145-m28-deprecated-route-removal.md) - M28 Route Removal (operator.py deleted)
