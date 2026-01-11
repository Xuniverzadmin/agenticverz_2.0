# PIN-389: Projection Route Separation and Console Isolation

**Status:** ✅ COMPLETE
**Created:** 2026-01-11
**Category:** Architecture / Routing

---

## Summary

Fixed projection route validation to enforce relative-only routes. Added CI guard and runtime console isolation guard.

---

## Details

## Problem

Projection validation in `projection_assertions.ts` was enforcing **runtime route prefixes** (`/precus`, `/cus`) at **design time**, causing validation failures when the projection compiler correctly emitted relative routes (`/overview`, `/activity`).

This was a **boundary error** — the wrong invariant was being enforced at the wrong layer.

## Root Cause

Two incompatible truths in the same file:

1. **Old invariant (stale):** Routes must start with `/precus/` or `/cus/`
2. **New invariant (correct):** Routes are relative; console prefixes applied at runtime

The assertion layer was never updated when the architecture shifted to relative routes.

## Solution

### 1. Layer Separation (Core Fix)

Added `assertValidRelativeRoute()` to enforce projection routes are relative-only:

```typescript
// projection_assertions.ts
export function assertValidRelativeRoute(
  route: unknown,
  context: string
): asserts route is string {
  // Rejects: non-string, doesn't start with '/', has console prefix
  if (route.startsWith('/precus/') || route.startsWith('/cus/')) {
    throw new Error(`...route must be relative (no console prefix)...`);
  }
}
```

Updated `assertValidDomain()` and `assertValidPanel()` to use the new validator.

**Preserved:** `assertValidRoutePrefix()` for runtime validation only.

### 2. CI Guard (Compile-Time)

**File:** `scripts/projection-route-check.cjs`

- Validates `ui_projection_lock.json` before build
- Rejects routes with console prefixes
- Added to `npm run prebuild`
- Standalone: `npm run projection:routes`

### 3. Runtime Console Isolation Guard

**File:** `src/routing/ConsoleIsolationGuard.tsx`

- Wraps layouts (PreCusLayout, AIConsoleLayout)
- Blocks navigation escaping `CONSOLE_ROOT`
- Redirects violating paths to console root
- Logs detailed error for debugging

## Files Changed

| File | Change |
|------|--------|
| `src/contracts/projection_assertions.ts` | Added `assertValidRelativeRoute()`, updated validators |
| `scripts/projection-route-check.cjs` | **New** — CI guard |
| `package.json` | Added `projection:routes` script |
| `src/routing/ConsoleIsolationGuard.tsx` | **New** — Runtime guard |
| `src/routing/index.ts` | Export guard |
| `src/components/layout/PreCusLayout.tsx` | Wrapped with guard |
| `src/products/ai-console/app/AIConsoleLayout.tsx` | Wrapped with guard |

## Invariants (Now Enforced)

| Layer | Truth | Validator |
|-------|-------|-----------|
| Projection (design) | Relative routes only | `assertValidRelativeRoute()` |
| Build (CI) | No console prefixes | `projection-route-check.cjs` |
| Runtime (navigation) | Must match CONSOLE_ROOT | `ConsoleIsolationGuard` |

## FOPS Status

FOPS (`/prefops`, `/fops`) was **never affected** — it uses static routes from `consoleRoots.ts`, not projection-driven routing.

## Key Principle

> **Projection defines what exists**
> **Loader decides where it lives**
> **Router enforces where you're allowed to go**

Each layer enforces only its own truth. No duplication. No leaks.

---

## Related PINs

- [PIN-352](PIN-352-.md)
- [PIN-358](PIN-358-.md)
- [PIN-368](PIN-368-.md)
