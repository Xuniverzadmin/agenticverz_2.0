# PIN-359: Sidebar & Workspace Realignment - Wireframe Compliance

**Status:** ✅ COMPLETE (Phase 2 - Panel Surface Normalized)
**Created:** 2026-01-08
**Updated:** 2026-01-08
**Category:** Frontend / UI Governance
**Milestone:** Customer Console V1

---

## Summary

**Phase 1:** Restored strict wireframe alignment: sidebar shows only Domain→Subdomain, topics as horizontal tabs in workspace.

**Phase 2 (NEW):** Panel surface normalization - ALL panels under topic tabs render as full surfaces (not just O1). Panel inference KILLED. View mode toggle replaces console switching.

---

## Details

### Objective

Restore strict wireframe alignment by:
- Removing panels and topics from sidebar
- Rendering panels only under Topic tabs in main workspace
- Cleaning header hierarchy and chrome leaks
- Implementing Order-1 inline rendering (no button affordance)
- Adding temporary description injection for preflight validation

---

## Governance Rules (LOCKED)

### Sidebar Contract

> **Sidebar renders structure, not content.**

| Allowed | Forbidden |
|---------|-----------|
| Domain | Topics |
| Subdomain | Panels |
| | Entities |

### Header Hierarchy (Explicit Order)

1. **Domain** (e.g., `Overview`)
2. **Subdomain** (e.g., `SYSTEM HEALTH`)
3. **Short description** (human text only)
4. **Topic tabs** (horizontal)

### Order-1 Rendering Rule (SUPERSEDED by Phase 2)

~~| Order | Render Mode |~~
~~|-------|-------------|~~
~~| O1 | Inline content surface (no click, no CTA) |~~
~~| O2-O5 | Navigable card/link |~~

**PHASE 2 RULE:** ALL panels under topic tabs render as FULL_PANEL_SURFACE. No O1 vs O2-O5 distinction. Panel inference is KILLED.

### Topic Context Rendering Rule (Phase 2)

> Topic tabs are **content contexts**, not navigation.
> Once inside a topic tab, ALL panels render as FULL SURFACES.

| Rule | Enforcement |
|------|-------------|
| Panel render mode | FULL_PANEL_SURFACE (always) |
| Click-to-expand | FORBIDDEN |
| Card mode | FORBIDDEN |
| Inference | KILLED |

### View Mode Toggle Rule (Phase 2)

> Customer vs Developer view is a **render-mode toggle**, NOT a route change.

| Aspect | Requirement |
|--------|-------------|
| Route | Same (`/precus/*`) |
| Data | Same projection |
| Render | Different (DEVELOPER/CUSTOMER) |
| Console switch | FORBIDDEN for validation |

---

## Implementation

### Task Group 1: Sidebar Fix (`ProjectionSidebar.tsx`)

**Changes:**
- Removed `PanelNavItem` component
- Removed `SubdomainNavSection` with panel iteration
- Created `SubdomainNavItem` - simple nav link, no expansion
- Updated `DomainSection` to show only subdomains
- Sidebar footer now shows domain count only

**Result:** Sidebar shows Domain → Subdomain only. No topics. No panels.

### Task Group 2: DomainPage Restructure (`DomainPage.tsx`)

**Changes:**
- Added `TopicTabs` component (horizontal tabs)
- Added `Order1Panel` component (inline render, no CTA)
- Updated `PanelsGrid` to separate O1 from O2-O5 panels
- Implemented subdomain selection via URL param (`?subdomain=`)
- Auto-select first subdomain and first topic on load

**Result:** Topics as horizontal tabs, panels under selected topic.

### Task Group 3: Preflight Description Normalizer (`ui_projection_loader.ts`)

**New Functions:**
- `normalizePanel()` - Injects placeholder if `short_description` missing
- `normalizeDomain()` - Same for domains
- `getNormalizedPanelsForSubdomain()` - Returns normalized panels
- `getNormalizedDomain()` - Returns normalized domain

**Rules:**
- Only active when `VITE_PREFLIGHT_MODE=true`
- Marks auto-generated descriptions with `_normalization.auto_description`
- `AUTO` badge visible in Inspector mode only
- Never written back to L2.1

**Placeholder Format:**
```
Domain: "Provides an overview of {domain} across your system."
Panel: "Displays {panel name} data and controls."
```

### Task Group 4: Order-1 Inline Rendering (SUPERSEDED)

~~**`Order1Panel` Component:**~~
~~- No click handler~~
~~- No button/CTA styling~~

**See Phase 2 Task Groups below.**

---

## Phase 2 Implementation (Panel Surface Normalized)

### Task Group A: Kill Panel Inference (`DomainPage.tsx`)

**Root Cause:** Renderer had two panel modes active simultaneously (INLINE/SURFACE vs SELECTABLE/NAVIGABLE). Decision was made implicitly based on order level.

**Fix:**
- Removed `PanelCard` component entirely
- Renamed `Order1Panel` → `FullPanelSurface`
- Updated `PanelsGrid` to render ALL panels as `FullPanelSurface`
- Removed `isOrder1Panel` helper function
- Removed `Link` import (no navigable cards)

**Result:** Topic context = surface mode. Panel inference KILLED.

```typescript
// PanelsGrid now renders ALL panels as surfaces
return (
  <div className="space-y-4">
    {panels.map((panel) => (
      <FullPanelSurface key={panel.panel_id} panel={panel} />
    ))}
  </div>
);
```

### Task Group B: Remove Panel Menu

**Status:** Already done by governance. "NO kebab menus" rule was locked.

### Task Group C: View Mode Toggle (`uiStore.ts`, `PreCusLayout.tsx`, `Header.tsx`)

**Problem:** Console switching to `/cus` was wrong mechanism for validation. Different route = different auth, session, data surface.

**Fix:**
- Added `viewMode: 'DEVELOPER' | 'CUSTOMER'` to `uiStore`
- Added `toggleViewMode()` and `setViewMode()` actions
- `PreCusLayout` maps `viewMode` to renderer mode:
  - DEVELOPER → INSPECTOR_MODE
  - CUSTOMER → CUSTOMER_MODE
- Added `ViewModeToggle` component in Header

**Result:** Same route (`/precus/*`), same data, different render mode.

```typescript
// PreCusLayout.tsx
const rendererMode = viewMode === 'DEVELOPER' ? INSPECTOR_MODE : CUSTOMER_MODE;
```

---

## Files Modified (Phase 2)

| File | Changes |
|------|---------|
| `src/stores/uiStore.ts` | Added `viewMode`, `setViewMode()`, `toggleViewMode()` |
| `src/pages/domains/DomainPage.tsx` | Removed PanelCard, renamed Order1Panel → FullPanelSurface, all panels as surfaces |
| `src/components/layout/PreCusLayout.tsx` | Maps viewMode to INSPECTOR_MODE/CUSTOMER_MODE |
| `src/components/layout/Header.tsx` | Added ViewModeToggle component |

---

## Files Modified (Phase 1)

| File | Changes |
|------|---------|
| `src/components/layout/ProjectionSidebar.tsx` | Removed panel iteration, simplified to Domain→Subdomain |
| `src/pages/domains/DomainPage.tsx` | Added TopicTabs, Order1Panel, normalized data usage |
| `src/contracts/ui_projection_loader.ts` | Added preflight normalizer functions |

---

## Acceptance Criteria (Phase 1)

| Check | Status |
|-------|--------|
| Sidebar shows only Domain → Subdomain | ✅ |
| No topics in sidebar | ✅ |
| No panels in sidebar | ✅ |
| Topics render as horizontal tabs | ✅ |
| Panels render only under selected topic | ✅ |
| Domain + Subdomain visible in header | ✅ |
| Short description shown if provided | ✅ |
| Auto-description marked with `AUTO` (Inspector only) | ✅ |
| No internal IDs in customer header | ✅ |

---

## Acceptance Criteria (Phase 2 - Panel Surface Normalized)

| Check | Status |
|-------|--------|
| All panels under topic tabs render identically as full surfaces | ✅ |
| No panel appears as a button/card | ✅ |
| No three-dot menu exists anywhere | ✅ |
| "Awaiting backend binding" appears consistently | ✅ |
| Switching to Customer View keeps URL `/precus/...` | ✅ |
| Customer View shows zero developer metadata | ✅ |
| Developer View remains unchanged | ✅ |
| View mode toggle visible in Header (PreCus only) | ✅ |

---

## Final Lock-In Rules

> **Sidebar = structure**
> **Workspace = slices + content**
> **Panels = content surfaces, never navigation**
> **Topic context = ALL panels as FULL_PANEL_SURFACE**
> **View mode = render toggle, NOT route change**

---

## Governance Rules Added (Phase 2)

| Rule ID | Name | Enforcement |
|---------|------|-------------|
| BL-DEPLOY-001 | Deploy After Rebuild | BLOCKING |
| DEPLOY-001 | Deploy After Frontend Build | BLOCKING |
| DEPLOY-002 | Reload Apache After Deploy | BLOCKING |
| DEPLOY-003 | Backend Build Includes Deploy | BY_CONSTRUCTION |
| DEPLOY-004 | Verify Deployment | MANDATORY |

**Principle:** Build without deploy = invisible work = wasted time.

**Files Updated:**
- `docs/playbooks/SESSION_PLAYBOOK.yaml` (Section 37, v2.36)
- `docs/behavior/behavior_library.yaml` (BL-DEPLOY-001)

---

## Related PINs

- [PIN-358](PIN-358-precus-gap-closure-task-tracker.md) - PreCus Gap Closure Task Tracker
- [PIN-357](PIN-357-view-mode-layer-architecture-renderercontext.md) - View Mode Layer Architecture
- [PIN-355](PIN-355-.md) - ONE-PASS RE-RENDER PLAN
