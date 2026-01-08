# PIN-353: Routing Authority Infrastructure Freeze

**Status:** FROZEN
**Created:** 2026-01-08
**Category:** Infrastructure / Routing
**Lock Level:** INFRASTRUCTURE
**Owner:** platform

---

## Summary

Established and froze the 4-console routing authority model for the AOS frontend. All routing infrastructure is now marked as low-churn, platform-owned code requiring deliberate review for any changes.

---

## Route Authority Model (FROZEN)

```
┌──────────────┬─────────────┬───────────┬─────────────────────────────┐
│ Console Kind │ Environment │ Root Path │ Layout/Entry                │
├──────────────┼─────────────┼───────────┼─────────────────────────────┤
│ customer     │ preflight   │ /precus   │ PreCusLayout (L2.1 UI)      │
├──────────────┼─────────────┼───────────┼─────────────────────────────┤
│ customer     │ production  │ /cus      │ AIConsoleApp                │
├──────────────┼─────────────┼───────────┼─────────────────────────────┤
│ founder      │ preflight   │ /prefops  │ FounderRoute (standalone)   │
├──────────────┼─────────────┼───────────┼─────────────────────────────┤
│ founder      │ production  │ /fops     │ FounderRoute (standalone)   │
└──────────────┴─────────────┴───────────┴─────────────────────────────┘
```

### Route Naming Rationale

| Route | Meaning |
|-------|---------|
| `/precus` | **Pre**flight **Cus**tomer Console |
| `/cus` | Production **Cus**tomer Console |
| `/prefops` | **Pre**flight **F**ounder **Ops** Console |
| `/fops` | Production **F**ounder **Ops** Console |

---

## Invariants (ENFORCED)

1. **4 distinct console namespaces** — NO mixing or leaking
2. Each console has its own route group
3. `FounderRoute` guard on ALL `/prefops/*` and `/fops/*` routes
4. `PreCusLayout` for `/precus/*` (L2.1 projection-driven UI)
5. `AIConsoleApp` for `/cus/*` (production customer)
6. All paths must start with one of the 4 valid console roots
7. Runtime assertion (`RouteGuardAssertion`) validates routes in dev/preflight

---

## Infrastructure-Owned Files (FROZEN)

All files marked with `INFRASTRUCTURE: FROZEN` header:

### Routing Module (`src/routing/`)

| File | Purpose | Change Frequency |
|------|---------|------------------|
| `consoleContext.ts` | Environment detection | NEVER |
| `consoleRoots.ts` | Root path mapping (4 roots) | NEVER |
| `routes.ts` | Route definitions | RARE |
| `index.ts` | Public API exports | NEVER |
| `RouteGuardAssertion.tsx` | Runtime validation | NEVER |
| `ROUTING_AUTHORITY_LOCK.md` | Freeze documentation | NEVER |

### Route Entry (`src/routes/`)

| File | Purpose | Change Frequency |
|------|---------|------------------|
| `index.tsx` | Route tree definition | RARE (new pages only) |
| `ProtectedRoute.tsx` | Auth guard | NEVER |
| `OnboardingRoute.tsx` | Onboarding guard | NEVER |
| `FounderRoute.tsx` | Founder auth guard | NEVER |

### Root Layout Components

| File | Purpose | Change Frequency |
|------|---------|------------------|
| `PreCusLayout.tsx` | Preflight customer layout | RARE |
| `AIConsoleApp.tsx` | Production customer entry | RARE |

---

## Changes Made in This PIN

### 1. Route Separation (4 Distinct Consoles)

- Moved founder routes outside customer layout
- Created separate route groups for each console
- Added `renderFounderRoutes(prefix)` helper for `/prefops` and `/fops`

### 2. Route Naming

- Renamed `/guard` → `/cus` (consumer-facing, no security associations)
- Renamed `GUARD_ROOT` → `CUS_ROOT`
- Updated all references in routing module

### 3. Infrastructure Freeze

- Added `INFRASTRUCTURE: FROZEN` header to all routing files
- Created `ROUTING_AUTHORITY_LOCK.md` documentation
- Defined change review process

### 4. Runtime Validation

- Updated `RouteGuardAssertion` for 4-console model
- Validates paths start with valid console roots
- Detects cross-console navigation
- Active in dev/preflight only

---

## Files Modified

| File | Changes |
|------|---------|
| `src/routing/consoleRoots.ts` | 4 console roots, `/guard` → `/cus` |
| `src/routing/routes.ts` | FOUNDER_ROUTES, `cusRoot` |
| `src/routing/index.ts` | Export `CUS_ROOT` |
| `src/routing/RouteGuardAssertion.tsx` | 4-console validation |
| `src/routes/index.tsx` | 4 route groups, `/cus/*` routes |
| `src/components/layout/PreCusLayout.tsx` | NEW - L2.1 layout |
| `src/components/layout/Sidebar.tsx` | Link to `/cus` |
| `src/products/ai-console/app/AIConsoleApp.tsx` | Comments updated |
| `src/components/navigation/CanonicalBreadcrumb.tsx` | Example comments |

---

## Remaining `/guard` References (NOT Changed)

These references are **intentionally not changed** as they refer to **backend API endpoints**, not frontend routes:

| Category | Location | Reason |
|----------|----------|--------|
| Backend API client | `src/api/guard.ts` | Calls backend `/guard/*` API endpoints |
| API module imports | `from '@/api/guard'` | Module name, not route path |
| Health checks | `src/lib/healthCheck.ts` | Backend API health endpoints |
| Guardrails feature | `src/api/operator.ts` | Different feature (guardrails) |

**Key distinction:**
- Frontend route paths (`/cus/*`) → Changed
- Backend API paths (`/guard/*`) → Not changed (separate concern)

---

## Validation

### Build Verification
```
✓ built in 12.17s
```

### RouteGuardAssertion Coverage

Validates at runtime (dev/preflight):
- `/precus/*` — preflight customer
- `/cus/*` — production customer
- `/prefops/*` — preflight founder
- `/fops/*` — production founder

Logs violations and cross-console navigation warnings.

---

## Change Review Process

Any change to infrastructure-owned files must follow:

1. **Document the change** — Why is this change needed?
2. **Impact analysis** — Which consoles are affected?
3. **PIN reference** — Link to relevant PIN
4. **Founder approval** — Explicit sign-off required
5. **Build verification** — Must pass all builds

---

## Related PINs

- **PIN-352:** L2.1 UI Projection Pipeline (Preflight Console)
- **PIN-318:** Phase 1.2 Authority Hardening (FounderRoute)

---

## Contact

Changes to routing infrastructure require review from:
- Architecture team
- PIN-352/353 owner

Do not bypass this lock without explicit authorization.
