# PIN-235: Products-First Architecture Migration

**Status:** COMPLETE (Phase 3)
**Created:** 2025-12-29
**Updated:** 2025-12-29
**Category:** Architecture / Console / Migration

---

## Summary

Restructured AI Console codebase from feature-first to products-first architecture, enabling multiple products (AI Console, Agents, Product Builder) to coexist without future structural refactors.

---

## Problem Statement

The previous folder structure silently decided product boundaries:

```
src/pages/aiconsole/     # "console" is the product
src/pages/guard/         # "guard" is the primary concept
```

This created three accidental assumptions:
1. "console" is the product (it's actually the website)
2. "guard" is the primary concept (it's the AI Console)
3. There will only be one product surface (we have 3 planned)

---

## Solution: 4-Layer Model

```
Brand → Product → App → Feature
  │         │        │       │
  └─console └─ai-console     └─OverviewPage
             └─agents        └─ActivityPage
             └─product-builder
```

---

## Target Structure (Implemented)

```
src/products/ai-console/
├── main.tsx                    # Browser entry (standalone deployment)
├── app/
│   ├── AIConsoleApp.tsx        # Product root (providers, routing, layout)
│   └── AIConsoleLayout.tsx     # Layout shell
├── pages/
│   ├── overview/OverviewPage.tsx
│   ├── activity/ActivityPage.tsx
│   ├── incidents/
│   │   ├── IncidentsPage.tsx
│   │   ├── IncidentDetailPage.tsx
│   │   ├── DecisionTimeline.tsx
│   │   ├── IncidentFilters.tsx
│   │   └── IncidentSearchBar.tsx
│   ├── policies/PoliciesPage.tsx
│   └── logs/LogsPage.tsx
├── integrations/               # Renamed from connectivity/
│   ├── IntegrationsPage.tsx
│   └── KeysPage.tsx
└── account/
    ├── SettingsPage.tsx
    ├── AccountPage.tsx
    └── SupportPage.tsx
```

---

## Implementation Details

### Phase 1: Guard → AI Console Rename (COMPLETE)
- Renamed `GuardConsoleEntry.tsx` → `AIConsoleEntry.tsx`
- Renamed `GuardLayout.tsx` → `AIConsoleLayout.tsx`
- Renamed `GuardSettingsPage.tsx` → `AIConsoleSettingsPage.tsx`
- Updated display labels from "Guard" to "AI Console"

### Phase 2: Products-First Structure (COMPLETE)
- Created directory structure under `src/products/ai-console/`
- Added TypeScript path aliases:
  ```json
  "@ai-console/*": ["./src/products/ai-console/*"]
  ```
- Added Vite alias for build resolution
- Moved all pages to domain-first folders
- Renamed components (removed "Customer" prefix)
- Updated all imports to absolute paths
- Updated routes in AIConsoleApp.tsx
- Updated routes/index.tsx to import from new location
- Cleaned up old `src/pages/aiconsole/` folder (17 files removed)

### Phase 3: Entry Point Separation (COMPLETE)
- Created `main.tsx` as standalone browser entry point
- Separated runtime concerns from product logic
- Added named export to AIConsoleApp for direct imports
- Preserved default export for lazy loading compatibility

**3-Layer Architecture:**

| Layer | File | Responsibility |
|-------|------|----------------|
| Runtime entry | `main.tsx` | DOM mounting, BrowserRouter (standalone) |
| Product root | `AIConsoleApp.tsx` | Providers, routing, layout |
| Features | `pages/*` | UI, business logic |

**Why This Matters:**
- `main.tsx` handles browser/environment concerns only
- `AIConsoleApp` can be lazy-loaded (current) OR mounted standalone (future)
- Enables SSR, micro-frontends, and multi-product shell later
- No business logic in entry point

### Files Modified

| File | Changes |
|------|---------|
| `tsconfig.json` | Added `@ai-console/*` path alias |
| `vite.config.ts` | Added `@ai-console` resolve alias |
| `routes/index.tsx` | Updated import to `@ai-console/app/AIConsoleApp` |

### Files Created/Moved

| New Location | Original |
|--------------|----------|
| `products/ai-console/app/AIConsoleApp.tsx` | `pages/aiconsole/AIConsoleEntry.tsx` |
| `products/ai-console/app/AIConsoleLayout.tsx` | `pages/aiconsole/AIConsoleLayout.tsx` |
| `products/ai-console/pages/overview/OverviewPage.tsx` | `pages/aiconsole/CustomerOverviewPage.tsx` |
| `products/ai-console/pages/activity/ActivityPage.tsx` | `pages/aiconsole/CustomerActivityPage.tsx` |
| `products/ai-console/pages/policies/PoliciesPage.tsx` | `pages/aiconsole/CustomerPoliciesPage.tsx` |
| `products/ai-console/pages/logs/LogsPage.tsx` | `pages/aiconsole/CustomerLogsPage.tsx` |
| `products/ai-console/pages/incidents/IncidentsPage.tsx` | `pages/aiconsole/IncidentsPage.tsx` |
| `products/ai-console/pages/incidents/IncidentDetailPage.tsx` | `pages/aiconsole/IncidentDetailPage.tsx` |
| `products/ai-console/pages/incidents/DecisionTimeline.tsx` | `pages/aiconsole/DecisionTimeline.tsx` |
| `products/ai-console/pages/incidents/IncidentFilters.tsx` | `pages/aiconsole/IncidentFilters.tsx` |
| `products/ai-console/pages/incidents/IncidentSearchBar.tsx` | `pages/aiconsole/IncidentSearchBar.tsx` |
| `products/ai-console/connectivity/IntegrationsPage.tsx` | `pages/aiconsole/CustomerIntegrationsPage.tsx` |
| `products/ai-console/connectivity/KeysPage.tsx` | `pages/aiconsole/CustomerKeysPage.tsx` |
| `products/ai-console/account/SettingsPage.tsx` | `pages/aiconsole/AIConsoleSettingsPage.tsx` |
| `products/ai-console/account/AccountPage.tsx` | `pages/aiconsole/AccountPage.tsx` |
| `products/ai-console/account/SupportPage.tsx` | `pages/aiconsole/SupportPage.tsx` |

---

## Component Renames

| Old Name | New Name |
|----------|----------|
| `CustomerOverviewPage` | `OverviewPage` |
| `CustomerActivityPage` | `ActivityPage` |
| `CustomerPoliciesPage` | `PoliciesPage` |
| `CustomerLogsPage` | `LogsPage` |
| `CustomerIntegrationsPage` | `IntegrationsPage` |
| `CustomerKeysPage` | `KeysPage` |
| `AIConsoleSettingsPage` | `SettingsPage` |

---

## Import Pattern

**Old Pattern (relative):**
```typescript
import { guardApi } from '../../api/guard';
```

**New Pattern (absolute):**
```typescript
import { guardApi } from '@/api/guard';
import { OverviewPage } from '@ai-console/pages/overview/OverviewPage';
```

---

## Verification

- Build verified successful at each step
- All routes functional
- No broken imports
- TypeScript compilation passes

---

## Benefits

1. **Product Isolation:** Each product has its own folder with clear boundaries
2. **Scalability:** Easy to add new products (agents, product-builder)
3. **Clean Imports:** Path aliases make imports readable and refactor-safe
4. **Domain Organization:** Pages organized by domain (overview, activity, incidents, etc.)
5. **Future-Proof:** Structure supports multiple console surfaces

---

## Freeze Points (LOCKED)

These decisions are now frozen. No future debate needed.

### Freeze #1 — Product Entry Pattern

```
main.tsx        = runtime entry (DOM, browser)
AIConsoleApp.tsx = product root (providers, routing)
```

**Rule:** No business logic in `main.tsx`. No DOM mounting in product code.

### Freeze #2 — Product Folder Layout

All Agenticverz products must follow:

```
products/{product-name}/
  main.tsx
  app/
  pages/
  account/
  integrations/
```

### Freeze #3 — Domain → Folder Mapping

```
Overview   → pages/overview
Activity   → pages/activity
Incidents  → pages/incidents
Policies   → pages/policies
Logs       → pages/logs
```

No aliases. No exceptions.

---

## Anti-Patterns (Avoid)

- ❌ Don't reorganize Orders (O2-O5) into folders
- ❌ Don't merge account + pages
- ❌ Don't move providers into `main.tsx`
- ❌ Don't add a global "Admin" folder
- ❌ Don't rename AIConsoleApp again

---

## Next Steps (Optional)

1. ~~**Clean up old folder:** Remove `src/pages/aiconsole/`~~ ✅ DONE
2. **Add agents product:** Create `src/products/agents/` structure
3. **Add product-builder:** Create `src/products/product-builder/` structure
4. **Standalone deployment:** Configure Vite to use `main.tsx` for `console.agenticverz.com`

---

## Related PINs

- PIN-234: Customer Console v1 Constitution (governance framework)
- PIN-005: Machine-Native Architecture (strategic vision)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-29 | **FROZEN:** Added 3 freeze points and anti-patterns section |
| 2025-12-29 | Renamed `connectivity/` → `integrations/` (user-recognized term) |
| 2025-12-29 | Phase 3 complete: Entry point separation (main.tsx + AIConsoleApp) |
| 2025-12-29 | Cleaned up old `src/pages/aiconsole/` folder (17 files removed) |
| 2025-12-29 | Phase 2 complete: products-first structure with path aliases |
| 2025-12-29 | Phase 1 complete: Guard → AI Console rename |
| 2025-12-29 | Created PIN-235 documenting architecture migration |
