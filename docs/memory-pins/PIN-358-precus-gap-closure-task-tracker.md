# PIN-358: PreCus Gap Closure Task Tracker

**Status:** COMPLETE
**Created:** 2026-01-08
**Updated:** 2026-01-08
**Category:** Frontend / Implementation
**Milestone:** Projection to Customer-Ready

---

## Summary

Execution checklist for closing remaining gaps in /precus to achieve wireframe-accurate Order-1 and depth navigation.

---

## Details

## Objective

Bring `/precus` to **wireframe-accurate Order-1 and depth navigation**, while preserving:

- L2.1 as intent authority
- Projection as structural truth
- Renderer as the only place for layout & visibility
- Zero UI guessing
- Clean path to CUSTOMER vs DEVELOPER modes

## Ownership Rule (DO NOT VIOLATE)

| Concern | Owner |
|---------|-------|
| Human labels, descriptions | L2.1 Supertable |
| Safe defaults | Normalizer |
| Completeness & consistency | Compiler |
| Structure & navigation shape | Projection Builder |
| Layout & visibility | Renderer |
| Breadcrumb & depth state | UI Navigation State |

---

## TASK GROUP A — GLOBAL CONTEXT (PROJECT SELECTOR)

| Task | Description | Status |
|------|-------------|--------|
| A1 | Create `design/global_context_intent.json` with project_selector spec | ✅ COMPLETE |
| A2 | Load Global Context in PreCusLayout, render project dropdown in Header | ✅ COMPLETE |

**Outcome:** Project selector visible without polluting L2.1

**Files Created:**
- `src/contexts/ProjectContext.tsx`
- `src/components/layout/ProjectSelector.tsx`
- `design/global_context_intent.json`

---

## TASK GROUP B — BREADCRUMB (DERIVED, NOT DECLARED)

| Task | Description | Status |
|------|-------------|--------|
| B1 | Create `src/navigation/useBreadcrumb.ts` - derive from route + projection | ✅ COMPLETE |
| B2 | Wire Breadcrumb into Header | ✅ COMPLETE |

**Outcome:** Breadcrumb appears and updates correctly with depth

**Files Created:**
- `src/navigation/useBreadcrumb.ts`
- `src/navigation/ProjectionBreadcrumb.tsx`

---

## TASK GROUP C — DOMAIN & SUBDOMAIN CONTEXT IN MAIN WORKSPACE

| Task | Description | Status |
|------|-------------|--------|
| C1 | Extend ui_projection_loader with context accessor functions | ✅ COMPLETE |
| C2 | Renderer uses context header for Domain + Subdomain display | ✅ COMPLETE |

**Outcome:** Domain/Subdomain visible per wireframe

**Files Created:**
- `src/navigation/useDomainContext.ts`
- `src/navigation/DomainContextHeader.tsx`

---

## TASK GROUP D — SHORT DESCRIPTION (HUMAN INTENT)

| Task | Description | Status |
|------|-------------|--------|
| D1 | Add `short_description` to projection types | ✅ COMPLETE |
| D2 | Update projection JSON with descriptions | ✅ COMPLETE |
| D3 | Renderer shows description (Customer: prominent, Inspector: metadata) | ✅ COMPLETE |

**Outcome:** One-line domain/subdomain description appears correctly

**Files Modified:**
- `src/contracts/ui_projection_types.ts`
- `public/projection/ui_projection_lock.json`
- `src/pages/panels/PanelView.tsx`
- `src/pages/domains/DomainPage.tsx`

---

## TASK GROUP E — TOPIC-LEVEL NAVIGATION (ORDER-1 PEERS)

| Task | Description | Status |
|------|-------------|--------|
| E1 | Sidebar shows Domain → Subdomain → Panels hierarchy | ✅ COMPLETE |
| E2 | Topics removed from sidebar (Fix 2) | ✅ COMPLETE |

**Note:** Per wireframe review, topics should be horizontal tabs in main workspace, NOT nested in sidebar. Sidebar now shows: Domain → Subdomain → Panels (flat).

**Outcome:** Clean sidebar hierarchy, topics in workspace

---

## TASK GROUP F — ORDER-1 LAYOUT ZONING (UI RESPONSIBILITY)

| Task | Description | Status |
|------|-------------|--------|
| F1 | O1 Summary Zone with distinct cards | ✅ COMPLETE |
| F2 | O1/O2-O5 separation in DomainPage | ✅ COMPLETE |

**Outcome:** Order-1 content looks intentional, not stacked

**Components Added:**
- `O1SummaryCard` in DomainPage
- `separatePanelsByOrder()` helper

---

## TASK GROUP G — RENDERER MODE (CUSTOMER vs DEVELOPER)

| Task | Description | Status |
|------|-------------|--------|
| G1 | Create RendererMode Context (CUSTOMER/DEVELOPER) | ✅ COMPLETE (PIN-357) |
| G2 | Define Mode Presets with visibility flags | ✅ COMPLETE (PIN-357) |
| G3 | Wire /precus→DEVELOPER, /cus→CUSTOMER | ✅ COMPLETE (PIN-357) |

**Outcome:** Same UI, two faces. Zero drift.

---

## TASK GROUP H — COMPILER SAFETY (FINAL GUARD)

| Task | Description | Status |
|------|-------------|--------|
| H1 | Add compiler assertions: route prefix, domain, panel validation | ✅ COMPLETE |

**Outcome:** Broken intent cannot reach UI

**Files Created:**
- `src/contracts/projection_assertions.ts`

---

## POST-IMPLEMENTATION FIXES (2026-01-08)

### Fix 1: Console Hygiene (Boundary Violation)

**Problem:** PreCus switcher showed Founder consoles, violating pipeline boundary.

**Solution:** Filter consoles by audience - Customer pipeline only sees Customer consoles.

**File:** `src/components/layout/Header.tsx`

```typescript
const availableConsoles = CONSOLES.filter(
  (c) => c.audience === activeConsole.audience
);
```

---

### Fix 2: Topics in Workspace, Not Sidebar

**Problem:** Topics were nested under subdomains in sidebar, violating wireframe.

**Wireframe says:**
- Sidebar: Domain + Subdomain only
- Topics: Horizontal tabs in Main Workspace

**Solution:** Removed TopicNavSection from sidebar. Sidebar now shows Domain → Subdomain → Panels (flat).

**File:** `src/components/layout/ProjectionSidebar.tsx`

---

### Fix 3: Console Switch = Hard Reload

**Problem:** SPA navigation for console switch conflicted with route guards.

**Solution:** Console switch uses `window.location.href` for full page reload.

**File:** `src/components/layout/Header.tsx`

```typescript
const handleConsoleSwitch = (consolePath: string) => {
  window.location.href = consolePath;
};
```

---

## Acceptance Checklist

| Check | Status |
|-------|--------|
| Project dropdown visible | ✅ |
| Breadcrumb updates with depth | ✅ |
| Domain + Subdomain visible | ✅ |
| Short description renders if present | ✅ |
| Sidebar shows Domain → Subdomain → Panels | ✅ |
| Order-1 layout is zoned | ✅ |
| Console switcher respects pipeline boundary | ✅ |
| Console switch uses hard reload | ✅ |
| CUSTOMER mode hides metadata | ✅ |
| DEVELOPER mode shows metadata | ✅ |
| No UI guessing anywhere | ✅ |

---

## Final Rule (LOCKED)

> **L2.1 defines meaning.**
> **Projection defines structure.**
> **Renderer defines experience.**
> **Nothing else decides.**

---

## Progress Log

### 2026-01-08: Initial Creation
- Created task tracker
- Task Group G (Renderer Mode) marked COMPLETE via PIN-357

### 2026-01-08: Task Groups A-F, H Complete
- Implemented all task groups
- Build successful

### 2026-01-08: Post-Implementation Fixes
- Fix 1: Console hygiene - no cross-pipeline entries
- Fix 2: Topics in workspace, not sidebar
- Fix 3: Console switch = hard reload
- All fixes deployed to preflight

---

## Related PINs

- [PIN-357](PIN-357-view-mode-layer-architecture-renderercontext.md) - View Mode Layer Architecture
- [PIN-356](PIN-356-.md)
- [PIN-355](PIN-355-.md)
- [PIN-352](PIN-352-.md)
- [PIN-234](PIN-234-.md) - Customer Console Wireframe
