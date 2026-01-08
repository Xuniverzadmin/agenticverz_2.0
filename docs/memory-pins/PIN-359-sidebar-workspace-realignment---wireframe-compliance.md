# PIN-359: Sidebar & Workspace Realignment - Wireframe Compliance

**Status:** ✅ COMPLETE
**Created:** 2026-01-08
**Category:** Frontend / UI Governance
**Milestone:** Customer Console V1

---

## Summary

Restored strict wireframe alignment: sidebar shows only Domain→Subdomain, topics as horizontal tabs in workspace, Order-1 panels render inline (not as buttons), temporary description injection for preflight validation.

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

### Order-1 Rendering Rule

| Order | Render Mode |
|-------|-------------|
| O1 | Inline content surface (no click, no CTA) |
| O2-O5 | Navigable card/link |

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

### Task Group 4: Order-1 Inline Rendering

**`Order1Panel` Component:**
- No click handler
- No button/CTA styling
- Panel header as heading (not link)
- Content placeholder inline
- Inspector-only metadata (O1 badge, render mode, control count)

---

## Files Modified

| File | Changes |
|------|---------|
| `src/components/layout/ProjectionSidebar.tsx` | Removed panel iteration, simplified to Domain→Subdomain |
| `src/pages/domains/DomainPage.tsx` | Added TopicTabs, Order1Panel, normalized data usage |
| `src/contracts/ui_projection_loader.ts` | Added preflight normalizer functions |

---

## Acceptance Criteria

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
| O1 panels render inline (no button) | ✅ |
| O1 panels have no click-to-expand | ✅ |
| No kebab menu anywhere | ✅ |

---

## Final Lock-In Rules

> **Sidebar = structure**
> **Workspace = slices + content**
> **Panels = content, never navigation**
> **O1 = inline, O2-O5 = navigable**

---

## Related PINs

- [PIN-358](PIN-358-precus-gap-closure-task-tracker.md) - PreCus Gap Closure Task Tracker
- [PIN-357](PIN-357-view-mode-layer-architecture-renderercontext.md) - View Mode Layer Architecture
- [PIN-355](PIN-355-.md) - ONE-PASS RE-RENDER PLAN
