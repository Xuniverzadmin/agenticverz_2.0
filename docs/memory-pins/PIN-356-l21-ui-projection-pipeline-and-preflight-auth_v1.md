# PIN-356: L2.1 UI Projection Pipeline and Preflight Auth

**Status:** ✅ COMPLETE
**Created:** 2026-01-08
**Category:** Frontend / Architecture
**Milestone:** PIN-355 Implementation

---

## Summary

Implemented projection-driven navigation, panel execution surface, cross-console switcher, and dev password login for preflight convenience.

---

## Details

## Overview

This PIN documents the implementation of the L2.1 UI Projection Pipeline and preflight authentication improvements completed on 2026-01-08.

## 1. UI Projection Pipeline (L2.1)

### Projection Types (`src/types/projection.ts`)
Defined TypeScript interfaces for the projection data model:
- `ProjectionPanel` - Panel definition with route, controls, permissions
- `ProjectionDomain` - Domain grouping panels
- `UIProjection` - Root projection with metadata

### Projection Builder (`scripts/ui_projection_builder.py`)
Python script that generates `ui_projection_lock.json`:
- Emits routes for each domain and panel
- Routes are relative to console root (e.g., `/precus`)
- Command: `python3 scripts/ui_projection_builder.py --console-root /precus`

### Route Structure
```
/precus                    → PreCusLayout (sidebar + outlet)
/precus/:domain            → DomainPage (domain home)
/precus/:domain/:panelSlug → PanelView (panel execution)
```

## 2. Panel Execution Surface (`src/pages/panels/PanelView.tsx`)

Generic panel renderer that:
- Reads panel slug from route params
- Looks up panel definition from projection
- Displays panel metadata: header, controls, permissions, disabled reasons
- Placeholder for future data execution

Key functions:
- `findPanelByRoute()` - Locate panel by matching route
- `findDomainByPanelRoute()` - Find parent domain

## 3. Cross-Console Switcher (`src/components/layout/Header.tsx`)

Added `ConsoleSwitcher` component with navigation between:
- `/precus` - Preflight Customer Console
- `/cus` - Customer Console
- `/prefops` - Preflight Founder Ops
- `/fops` - Founder Ops

Dropdown in header allows switching consoles while preserving navigation context.

## 4. Domain Page Panel Links (`src/pages/domains/DomainPage.tsx`)

Converted `PanelCard` from static `<div>` to `<Link>` using `panel.route` from projection.
Panels are now clickable and navigate to their execution surface.

## 5. Preflight Password Login

### Problem
OTP login required email verification on every frontend rebuild, slowing development iteration.

### Solution
Added dev-only password login that browsers can cache/autofill.

### Backend Changes (`backend/app/api/onboarding.py`)
- Added `PasswordLoginRequest` schema
- Added `/api/v1/auth/login/password` endpoint
- Reads `DEV_LOGIN_PASSWORD` from environment
- Returns 403 if password login not enabled

### Frontend Changes (`src/pages/auth/LoginPage.tsx`)
- Added `password` state and `usePassword` toggle (defaults to true)
- Added `handlePasswordLogin()` function
- Password form with `autoComplete="email"` and `autoComplete="current-password"`
- Toggle to switch between password and OTP modes

### Configuration
```bash
# .env
DEV_LOGIN_PASSWORD=preflight2026

# docker-compose.yml (backend service)
DEV_LOGIN_PASSWORD: ${DEV_LOGIN_PASSWORD:-}
```

### Usage
1. Go to preflight-console.agenticverz.com/login
2. Click "Continue with Email"
3. Enter email: admin1@agenticverz.com
4. Enter password: preflight2026
5. Browser saves credentials for future autofill

## Files Modified

| File | Change |
|------|--------|
| `src/types/projection.ts` | New - Projection TypeScript types |
| `src/pages/panels/PanelView.tsx` | New - Panel execution surface |
| `src/routes/index.tsx` | Added PanelView route |
| `src/pages/domains/DomainPage.tsx` | Panel cards now Link components |
| `src/components/layout/Header.tsx` | Added ConsoleSwitcher |
| `src/pages/auth/LoginPage.tsx` | Added password login form |
| `backend/app/api/onboarding.py` | Added password login endpoint |
| `docker-compose.yml` | Added DEV_LOGIN_PASSWORD env |
| `.env` | Added DEV_LOGIN_PASSWORD value |

## Deployment

```bash
# Rebuild projection
python3 scripts/ui_projection_builder.py --console-root /precus
cp design/l2_1/ui_contract/ui_projection_lock.json website/app-shell/public/projection/

# Build frontend
cd website/app-shell && npm run build
cp -r dist dist-preflight

# Restart backend (picks up DEV_LOGIN_PASSWORD)
docker compose up -d --build backend

# Reload Apache
sudo systemctl reload apache2
```

## Security Note

Password login is **dev-only** and requires `DEV_LOGIN_PASSWORD` to be set.
Production deployments should NOT set this variable, forcing OAuth/OTP authentication.

---


---

## Updates

### Update (2026-01-08)

## 2026-01-08: View Mode Layer Implementation (RendererContext)

### Core Architecture

Implemented the **View Mode Layer** abstraction per architectural guidance:

- **One Projection, One Renderer, Two View Modes, Zero Divergence**

### New File: `src/contexts/RendererContext.tsx`

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

### Mode Presets

**INSPECTOR_MODE** (PreCus - all metadata visible):
- Used in `/precus/*` routes
- Full developer triage capability
- Shows panel IDs, topic IDs, permissions, control types

**CUSTOMER_MODE** (Customer Console - clean UX):
- Used in `/cus/*` routes
- Suppresses internal metadata
- Same navigation, panels, controls - different visibility

### Files Modified

| File | Change |
|------|--------|
| `src/contexts/RendererContext.tsx` | New - Context provider with mode presets |
| `src/pages/panels/PanelView.tsx` | Uses `useRenderer()` for conditional metadata |
| `src/components/layout/PreCusLayout.tsx` | Wrapped with `INSPECTOR_MODE` |
| `src/products/ai-console/app/AIConsoleApp.tsx` | Wrapped with `CUSTOMER_MODE` |

### Helper Components

- `InspectorOnly` - Renders children only in INSPECTOR mode
- `CustomerOnly` - Renders children only in CUSTOMER mode
- `useRenderer()` - Hook to access visibility flags
- `useIsInspectorMode()` - Quick boolean check

### Promotion Semantics

A panel can be promoted to customer console only if it renders correctly in INSPECTOR mode without manual overrides.

This ensures:
- Confidence in customer-facing output
- Traceability from spec to production
- Zero surprises in prod

## Related PINs

- [PIN-355](PIN-355-.md)
- [PIN-352](PIN-352-.md)
