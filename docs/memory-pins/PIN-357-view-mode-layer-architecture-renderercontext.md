# PIN-357: View Mode Layer Architecture (RendererContext)

**Status:** ✅ COMPLETE
**Created:** 2026-01-08
**Category:** Frontend / Architecture
**Milestone:** PIN-356 Implementation

---

## Summary

Implemented View Mode Layer with INSPECTOR/CUSTOMER modes. One Projection, One Renderer, Two View Modes, Zero Divergence.

---

## Details

## Overview

The **View Mode Layer** provides a single renderer with two faces, controlled by context — not environment hacks.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  One Projection → One Renderer → Two View Modes             │
├─────────────────────────────────────────────────────────────┤
│  /precus/*  │  INSPECTOR_MODE  │  Full metadata visible     │
│  /cus/*     │  CUSTOMER_MODE   │  Clean UX, no internals    │
└─────────────────────────────────────────────────────────────┘
```

## Core Abstraction

```typescript
type RendererMode = "INSPECTOR" | "CUSTOMER";

interface RendererContextValue {
  mode: RendererMode;
  showMetadata: boolean;        // Panel info, topic info blocks
  showPermissions: boolean;     // Permissions matrix
  showControlTypes: boolean;    // Control type labels
  showInternalIDs: boolean;     // Topic IDs, panel IDs
  showRenderMode: boolean;      // Render mode indicator
  showDisabledReasons: boolean; // Why controls are disabled
  showDebugBanner: boolean;     // Development banners
  showRouteInfo: boolean;       // Route path display
  showOrderInfo: boolean;       // Order (O1-O5) indicators
}
```

## Mode Presets

### INSPECTOR_MODE (PreCus)
- Full developer triage capability
- Shows all internal metadata
- Used for projection validation before promotion

### CUSTOMER_MODE (Customer Console)
- Clean UX, suppressed internals
- Same navigation, panels, controls
- Different visibility rules only

## Visibility Matrix

| Element | INSPECTOR | CUSTOMER |
|---------|-----------|----------|
| Panel ID | Yes | No |
| Topic ID | Yes | No |
| Route | Yes | No |
| Permissions matrix | Yes | No |
| Control types/categories | Yes | No |
| Order (O1-O5) | Yes | No |
| PREFLIGHT badge | Yes | No |
| Mode badge | Yes | No |
| "Coming soon" placeholder | No | Yes |
| Disabled reason | Full | User-friendly |

## Files

| File | Purpose |
|------|---------|
| `src/contexts/RendererContext.tsx` | Context provider with mode presets |
| `src/pages/panels/PanelView.tsx` | Uses `useRenderer()` for conditional display |
| `src/components/layout/PreCusLayout.tsx` | Wrapped with INSPECTOR_MODE |
| `src/products/ai-console/app/AIConsoleApp.tsx` | Wrapped with CUSTOMER_MODE |

## Helper Components

```typescript
// Conditional rendering helpers
<InspectorOnly>...</InspectorOnly>  // Only in INSPECTOR mode
<CustomerOnly>...</CustomerOnly>    // Only in CUSTOMER mode

// Hooks
const renderer = useRenderer();      // Full context access
const isInspector = useIsInspectorMode(); // Boolean check
```

## Promotion Rule

> A panel can be promoted to customer console only if it renders correctly in INSPECTOR mode without manual overrides.

This ensures:
- Confidence in customer-facing output
- Traceability from spec to production
- Zero surprises in prod

## What This Achieves

- **No fork** — Same codebase, same components
- **No divergence** — Projection stays single source of truth
- **No drift** — Changes propagate to both modes automatically
- **Developer triage** — Full visibility in /precus
- **Customer UX** — Clean experience in /cus

---

## Related PINs

- [PIN-356](PIN-356-.md)
- [PIN-355](PIN-355-.md)
- [PIN-352](PIN-352-.md)
