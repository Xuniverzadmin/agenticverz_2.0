# Smoke Test R3-2: Onboarding → App-Shell Handoff

**Status:** PENDING MANUAL EXECUTION
**Created:** 2026-01-06
**Reference:** PIN-319 (Frontend Realignment), R3-2

---

## Prerequisites

- [ ] Backend running on localhost:8000
- [ ] Frontend dev server running (npm run dev)
- [ ] Test user account available
- [ ] Test user has `onboardingComplete: false`

---

## Test Execution

### T1: New User Redirect to Onboarding

1. [ ] Login as test user (onboardingComplete: false)
2. [ ] Expected: Redirect to `/onboarding/connect`
3. [ ] Verify: Customer console (`/guard`) is NOT accessible

**Result:** [ ] PASS / [ ] FAIL

---

### T2: Complete Onboarding Flow

1. [ ] Navigate through: connect → safety → alerts → verify → complete
2. [ ] Verify each step validates before proceeding
3. [ ] On `/onboarding/complete`, click "Get Started"

**Result:** [ ] PASS / [ ] FAIL

---

### T3: Handoff to Customer Console

1. [ ] Expected: Redirect to `/guard`
2. [ ] Verify: Customer console loads correctly
3. [ ] Verify: `onboardingComplete` is now `true` in auth state

**Result:** [ ] PASS / [ ] FAIL

---

### T4: Cannot Re-Enter Onboarding

1. [ ] Navigate to `/onboarding/connect`
2. [ ] Expected: Redirect to `/guard`
3. [ ] Verify: No access to onboarding pages

**Result:** [ ] PASS / [ ] FAIL

---

### T5: Founder Console Blocked for Customer

1. [ ] Navigate to `/fops/ops`
2. [ ] Expected: Redirect to `/guard` (customer console)
3. [ ] Verify: No access to founder pages

**Result:** [ ] PASS / [ ] FAIL

---

## Build Verification

```bash
# Run all checks
cd website/app-shell
npm run build

# Expected output:
# ✓ UI Hygiene Check passes
# ✓ Import Boundary Check passes
# ✓ Build completes successfully
```

**Build Verification:**
- [x] UI Hygiene Check: PASS (0 errors, 5 warnings within budget)
- [x] Import Boundary Check: PASS (0 violations)
- [x] Build: SUCCESS (13.19s)

---

## Summary

| Test | Status |
|------|--------|
| T1: New User Redirect | PENDING |
| T2: Complete Onboarding | PENDING |
| T3: Handoff to Console | PENDING |
| T4: Cannot Re-Enter | PENDING |
| T5: Founder Blocked | PENDING |
| Build Checks | PASS |

---

## Sign-Off

- [ ] Manual tests executed
- [ ] All tests pass
- [ ] Tester: _______________
- [ ] Date: _______________
