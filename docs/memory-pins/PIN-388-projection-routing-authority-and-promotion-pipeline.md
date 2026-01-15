# PIN-388: Projection Routing Authority & Promotion Pipeline

**Status:** COMPLETE
**Category:** Architecture / UI Pipeline / Routing
**Created:** 2026-01-10
**Related:** PIN-387 (Canonical Projection Design), PIN-352 (L2.1 UI Projection Pipeline)

## Summary

Establishes proper separation between environment concerns and projection data, implementing a contractual promotion pipeline from preflight to production. Routes are now environment-agnostic in the projection, with frontend resolving the console root at runtime.

## Problem Statement

The original implementation had environment concerns leaking into the projection layer:

```
BEFORE (BROKEN):
┌─────────────────────────────────────────────────────────────┐
│ AURORA_L2 Compiler hardcoded "/cus/*" routes               │
│   → Projection stored absolute routes                       │
│   → preflight-console navigated to /cus/* (wrong)          │
│   → Cross-console navigation warnings                       │
└─────────────────────────────────────────────────────────────┘
```

## Solution: 3-Layer Routing Authority Model

```
AURORA_L2 (compiler)  →  semantic routes (NO environment)
Frontend runtime      →  environment root resolution
Deployment            →  which root is active
```

### Core Principle

> **Projection must be environment-agnostic.**
> **Environment decides the root, not the compiler.**

---

## Implementation

### 1. Compiler Changes (`backend/aurora_l2/SDSR_UI_AURORA_compiler.py`)

**Routes now relative (no `/cus` prefix):**

```python
# Line 356 - Domain routes
"route": f"/{domain.lower()}"  # Was: f"/cus/{domain.lower()}"

# Line 403 - Panel routes
"route": f"/{domain.lower()}/{intent['panel_id'].lower()}"  # Was: f"/cus/..."
```

**New `_meta` fields for promotion pipeline:**

```python
"_meta": {
    # ... existing fields ...
    "environment": "preflight",        # preflight or production
    "approval_status": "EXPERIMENTAL", # EXPERIMENTAL or APPROVED
    "sdsr_verified": True,             # SDSR scenarios passed
    "routes_relative": True,           # Routes resolved by frontend
}
```

### 2. Frontend Loader (`ui_projection_loader.ts`)

**Single point of route resolution:**

```typescript
import { CONSOLE_ROOT } from "@/routing/consoleRoots";

function resolveRoute(relativeRoute: string): string {
  // Handle legacy absolute routes
  if (relativeRoute.startsWith('/cus/') || relativeRoute.startsWith('/precus/')) {
    const stripped = relativeRoute.replace(/^\/(cus|precus)/, '');
    return `${CONSOLE_ROOT}${stripped}`;
  }
  return `${CONSOLE_ROOT}${relativeRoute}`;
}

function resolveProjectionRoutes(projection: UIProjectionLock): UIProjectionLock {
  return {
    ...projection,
    domains: projection.domains.map(domain => ({
      ...domain,
      route: resolveRoute(domain.route),
      panels: domain.panels.map(panel => ({
        ...panel,
        route: resolveRoute(panel.route),
      })),
    })),
  };
}
```

**Applied once at load time:**

```typescript
const rawData = await response.json();
validateProjection(rawData);
const data = resolveProjectionRoutes(rawData);  // Routes resolved HERE
cachedProjection = data;
```

### 3. TypeScript Types (`ui_projection_types.ts`)

```typescript
export interface ProjectionMeta {
  // ... existing fields ...
  environment: "preflight" | "production";
  approval_status: "EXPERIMENTAL" | "APPROVED";
  sdsr_verified: boolean;
  routes_relative: boolean;
}
```

### 4. Promotion Script (`scripts/tools/promote_projection.sh`)

```bash
# Check eligibility
./scripts/tools/promote_projection.sh --check

# Promote (only changes _meta, no recompilation)
./scripts/tools/promote_projection.sh --from preflight --to production

# Rollback if needed
./scripts/tools/promote_projection.sh --rollback

# Show status
./scripts/tools/promote_projection.sh --status
```

**Promotion requirements:**
- `sdsr_verified: true`
- No UNBOUND panels
- `routes_relative: true`

**Promotion changes ONLY:**
- `environment: "preflight"` → `"production"`
- `approval_status: "EXPERIMENTAL"` → `"APPROVED"`
- Adds `promoted_at` timestamp

---

## Architecture Result

```
┌─────────────────────────────────────────────────────────────┐
│ AURORA_L2 Compiler                                          │
│   Routes: /activity, /policies, /incidents, etc.            │
│   (Environment-agnostic)                                    │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ ui_projection_lock.json                                     │
│   _meta.routes_relative: true                               │
│   _meta.environment: "preflight"                            │
│   domains[].route: "/activity" (relative)                   │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend Loader (resolveProjectionRoutes)                   │
│   CONSOLE_ROOT = IS_PREFLIGHT ? "/precus" : "/cus"         │
│   Resolved: "/precus/activity" or "/cus/activity"          │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ UI Components (ProjectionSidebar, etc.)                     │
│   Use domain.route verbatim (already resolved)              │
│   No environment checks, no string replacements             │
└─────────────────────────────────────────────────────────────┘
```

---

## Projection Data (After Fix)

```json
{
  "_meta": {
    "environment": "preflight",
    "approval_status": "EXPERIMENTAL",
    "sdsr_verified": true,
    "routes_relative": true
  },
  "domains": [
    {"domain": "Overview", "route": "/overview"},
    {"domain": "Activity", "route": "/activity"},
    {"domain": "Incidents", "route": "/incidents"},
    {"domain": "Policies", "route": "/policies"},
    {"domain": "Logs", "route": "/logs"}
  ]
}
```

---

## What Was Removed

| Anti-Pattern | Status |
|--------------|--------|
| `/cus/*` hardcoded in compiler | REMOVED |
| Environment checks in sidebar | NOT NEEDED |
| String replacements like `.replace('/cus', '/precus')` | NOT NEEDED |
| Logic inferring environment from hostname | NOT NEEDED |
| Re-running compiler for promotion | NOT NEEDED |

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/aurora_l2/SDSR_UI_AURORA_compiler.py` | Emits relative routes, adds env metadata |
| `website/app-shell/src/contracts/ui_projection_loader.ts` | Resolves routes at load time |
| `website/app-shell/src/contracts/ui_projection_types.ts` | TypeScript types with env fields |
| `website/app-shell/src/routing/consoleRoots.ts` | CONSOLE_ROOT definition |
| `scripts/tools/promote_projection.sh` | Promotion pipeline |

---

## Promotion Pipeline Flow

```
1. PREFLIGHT VALIDATION
   - SDSR scenarios PASS
   - No UNBOUND panels
   - routes_relative = true

2. PROMOTION COMMAND
   ./scripts/tools/promote_projection.sh --from preflight --to production

3. WHAT PROMOTION DOES (mechanically)
   - Copies projection verbatim
   - Changes ONLY _meta fields:
     - environment: preflight → production
     - approval_status: EXPERIMENTAL → APPROVED
     - promoted_at: <timestamp>
   - NO recompilation
   - NO route changes

4. RESULT
   - Production projection in ui_projection_lock_production.json
   - Copied to public/ for deployment
```

---

## Verification

```bash
# Check projection routes
curl -s https://preflight-console.agenticverz.com/projection/ui_projection_lock.json | \
  jq '.domains[] | {domain, route}'

# Expected output (relative routes):
# {"domain": "Activity", "route": "/activity"}
# {"domain": "Policies", "route": "/policies"}

# Check meta
curl -s https://preflight-console.agenticverz.com/projection/ui_projection_lock.json | \
  jq '._meta | {environment, approval_status, routes_relative}'

# Expected:
# {"environment": "preflight", "approval_status": "EXPERIMENTAL", "routes_relative": true}
```

---

## Invariants (LOCKED)

1. **Projection routes are ALWAYS relative** - No environment prefix in projection
2. **Route resolution happens ONCE** - In ui_projection_loader.ts at load time
3. **Promotion is artifact movement** - No recompilation, only _meta changes
4. **Environment is declared, never inferred** - `_meta.environment` is authoritative

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-10 | Initial implementation |
| 2026-01-10 | Compiler: relative routes |
| 2026-01-10 | Loader: route resolution |
| 2026-01-10 | Types: environment metadata |
| 2026-01-10 | Script: promote_projection.sh |
| 2026-01-10 | Deployed to preflight-console |
