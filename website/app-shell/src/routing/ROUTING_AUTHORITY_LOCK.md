# ROUTING AUTHORITY LOCK

**Status:** FROZEN
**Lock Date:** 2026-01-08
**Reference:** PIN-352
**Lock Level:** INFRASTRUCTURE
**Owner:** platform

---

## Lock Declaration

This module (`src/routing/`) and associated layout components are **FROZEN** as infrastructure code.

### What This Means

1. **No Feature Work Allowed**
   - Do not add new routes directly to this module
   - Do not modify existing route patterns without review
   - Changes require explicit founder approval

2. **Changes Must Be Rare and Intentional**
   - New console kinds → Requires architecture review
   - New domain roots → Requires PIN documentation
   - Environment changes → Requires CI validation

3. **Low Churn Expectation**
   - Infrastructure code should be stable
   - Any change here affects ALL console surfaces
   - Deliberate review process required

---

## Route Authority Model (4 DISTINCT CONSOLES)

```
┌──────────────┬─────────────┬───────────┬─────────────────────────────┐
│ Console Kind │ Environment │ Root Path │ Layout/Entry                │
├──────────────┼─────────────┼───────────┼─────────────────────────────┤
│ customer     │ preflight   │ /precus   │ PreCusLayout (L2.1 UI)      │
├──────────────┼─────────────┼───────────┼─────────────────────────────┤
│ customer     │ production  │ /cus    │ AIConsoleApp                │
├──────────────┼─────────────┼───────────┼─────────────────────────────┤
│ founder      │ preflight   │ /prefops  │ FounderRoute (standalone)   │
├──────────────┼─────────────┼───────────┼─────────────────────────────┤
│ founder      │ production  │ /fops     │ FounderRoute (standalone)   │
└──────────────┴─────────────┴───────────┴─────────────────────────────┘
```

### Invariants

- **4 distinct console namespaces** — NO mixing or leaking
- Each console has its own route group
- `FounderRoute` guard on ALL `/prefops/*` and `/fops/*` routes
- `PreCusLayout` for `/precus/*` (L2.1 projection-driven UI)
- `AIConsoleApp` for `/cus/*` (production customer)

---

## Infrastructure-Owned Files (FROZEN)

The following files are marked as infrastructure-owned with low churn expectation:

### Routing Module (`src/routing/`)

| File | Purpose | Change Frequency |
|------|---------|------------------|
| `consoleContext.ts` | Environment detection | NEVER (unless new console kind) |
| `consoleRoots.ts` | Root path mapping (4 roots) | NEVER (frozen) |
| `routes.ts` | Route definitions | RARE (new routes added here) |
| `index.ts` | Public API exports | NEVER (exports only) |
| `RouteGuardAssertion.tsx` | Runtime validation | NEVER (enforcement logic) |
| `ROUTING_AUTHORITY_LOCK.md` | This file | NEVER |

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
| `PreCusLayout.tsx` | Preflight customer layout | RARE (L2.1 projections) |
| `AIConsoleApp.tsx` | Production customer entry | RARE |

---

## Allowed vs Forbidden Changes

### ALLOWED (with review)

- Adding new routes to `CUSTOMER_ROUTES` or `FOUNDER_ROUTES`
- Adding new dynamic route helpers (e.g., `incidentDetail(id)`)
- Bug fixes to existing routing logic
- Adding new founder pages (via `renderFounderRoutes`)

### FORBIDDEN (requires architecture review)

- Changing `IS_PREFLIGHT` / `IS_PRODUCTION` logic
- Modifying any of the 4 console roots (`PRECUS_ROOT`, `CUS_ROOT`, `PREFOPS_ROOT`, `FOPS_ROOT`)
- Adding new console kinds
- Removing existing exports
- Adding side effects to this module
- Mixing console namespaces
- Adding routes outside the 4 console roots

---

## Validation

The routing module is validated by:

1. **Runtime Assertion:** `RouteGuardAssertion` component (dev/preflight only)
   - Validates all paths start with valid console roots
   - Logs violations to console
   - Detects cross-console navigation

2. **Build-time:** TypeScript compilation
   - Type-safe route definitions
   - Import validation

3. **CI Script:** `scripts/ops/check_hardcoded_routes.sh` (planned)
   - Detect hardcoded paths in components
   - Enforce `@/routing` imports

---

## Integration with UI Projection Pipeline

The routing module is the **authority layer** for the UI projection pipeline:

```
ui_projection_lock.json
        ↓
   Domain Pages (NO routing logic)
        ↓
   CUSTOMER_ROUTES / FOUNDER_ROUTES (this module)
        ↓
   Console Root (/precus, /cus, /prefops, /fops)
        ↓
   Browser URL
```

Pages receive their routes FROM this module. They do NOT decide routes.

---

## Change Review Process

Any change to infrastructure-owned files must follow:

1. **Document the change** — Why is this change needed?
2. **Impact analysis** — Which consoles are affected?
3. **PIN reference** — Link to relevant PIN
4. **Founder approval** — Explicit sign-off required
5. **Build verification** — Must pass all builds

---

## Contact

Changes to this module require review from:
- Architecture team
- PIN-352 owner

Do not bypass this lock without explicit authorization.
