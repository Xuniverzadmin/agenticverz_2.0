# PIN-319: Frontend Realignment - App Shell Architecture

**Status:** ✅ COMPLETE
**Created:** 2026-01-06
**Category:** Frontend / Architecture

---

## Summary

Restructured frontend into app-shell + fops + onboarding with proper audience separation

---

## Details

## Overview

Completed a full frontend realignment to enforce proper audience separation and minimize app-shell scope.

## Changes Made

### Phase A: Rename (Completed in Prior Session)
- Renamed `aos-console/console` → `app-shell`
- Updated all imports and references

### Phase B: Extract Founder UI
- Moved 40 founder pages to `website/fops/src/pages/`
- All founder routes moved under `/fops/*` namespace
- All founder routes wrapped with `FounderRoute` guard
- Fixed imports to use `@fops/` alias

### Phase C: Extract Onboarding
- Moved 6 onboarding pages to `website/onboarding/src/pages/`
- Routes: `/onboarding/connect`, `/onboarding/safety`, `/onboarding/alerts`, `/onboarding/verify`, `/onboarding/complete`
- Documented redirect contract

### Phase D: Validation
- Build passes (2453 modules, 12.30s)
- Hygiene check: 0 errors, 5 warnings (within budget)
- No forbidden imports in shared code

## Final Architecture

```
website/
├── app-shell/            # Shared shell + Customer console
│   └── src/
│       ├── pages/        # 2 files (LoginPage, CreditsPage)
│       ├── products/ai-console/pages/  # 9 files (customer UI)
│       ├── components/   # Shared UI components
│       ├── api/          # Shared API clients
│       ├── lib/          # Shared utilities
│       └── routes/       # Central router
├── fops/                 # Founder Operations
│   └── src/pages/        # 40 files (founder UI)
└── onboarding/           # Pre-console setup
    └── src/pages/        # 6 files (onboarding flow)
```

## Route Architecture

| Route | Audience | Guard |
|-------|----------|-------|
| `/guard/*` | Customer | ProtectedRoute |
| `/fops/*` | Founder | FounderRoute |
| `/onboarding/*` | Pre-setup | OnboardingRoute |
| `/login` | Public | None |

## Key Configuration Changes

### vite.config.ts
- Added `@fops` and `@onboarding` aliases
- Added explicit node_modules aliases for external directory resolution
- Added `dedupe` and `optimizeDeps` for shared dependencies

### tsconfig.json
- Added `@fops/*` and `@onboarding/*` paths
- External directories extend app-shell's tsconfig

## Invariants

1. **No @fops imports in shared code** (except routes/index.tsx)
2. **No @onboarding imports in shared code** (except routes/index.tsx)
3. **All founder routes under /fops/***
4. **All founder routes wrapped with FounderRoute**
5. **Build must pass before merge**

## File Counts

| Location | Count |
|----------|-------|
| app-shell/src/pages | 2 |
| fops/src/pages | 40 |
| onboarding/src/pages | 6 |
| ai-console/pages | 9 |
---

## Hardening

### Update (2026-01-06)

## Post-Realignment Hardening (2026-01-06)

### RISK-1: App-Shell Scope Creep Prevention
- **R1-1:** Created `APP_SHELL_SCOPE.md` - defines allowed/forbidden responsibilities
- **R1-2:** Added page budget check to hygiene script (soft guard)

### RISK-2: Shared API Client Leakage
- **R2-1:** Classified all 28 API clients with `@audience` annotations
  - 13 founder-only APIs
  - 6 customer APIs
  - 9 shared APIs
- **R2-2:** Added import boundary check (hard guard, blocks build)

### RISK-3: Onboarding Handoff Untested
- **R3-1:** Created `ONBOARDING_TO_APP_SHELL.md` contract
- **R3-2:** Created smoke test checklist, build verification passed

### Regression Guardrails
- **G-1:** Directory ownership check (hard guard)
- **G-2:** Route namespace guard (hard guard)
- **G-3:** Phase marker lock (`PHASE_STATUS.md`)

### Guard Scripts
- `npm run boundary` - Import boundary check
- `npm run ownership` - Directory ownership check
- `npm run routes` - Route namespace guard
- `npm run guards` - Run all guards

### Exit Criteria Met
- [x] App-shell scope documented and bounded
- [x] API clients audience-classified
- [x] CI blocks cross-surface imports
- [x] Onboarding → shell contract explicit
- [x] Build verification passed
- [x] No new routes/pages can appear silently

**Status:** Ready for Phase 2 (L2.1 Headless Layer)
