# PIN-352: L2.1 UI Projection Pipeline & Preflight Console

**Status:** ACTIVE
**Created:** 2026-01-07
**Category:** UI Pipeline / Governance
**Milestone:** L2.1 UI Contract System

---

## Summary

Complete implementation of the L2.1 UI Projection Pipeline with a governance-gated
preflight console for testing before production promotion.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     L2.1 UI PROJECTION PIPELINE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   L2.1 Excel (l2_supertable_v3_cap_expanded.xlsx)                          │
│       │                                                                     │
│       ▼                                                                     │
│   [A] l2_raw_intent_parser.py ──────────► ui_intent_ir_raw.json            │
│       │   • NO validation                                                   │
│       │   • NO defaults                                                     │
│       │   • Preserves empty cells                                           │
│       ▼                                                                     │
│   [B] intent_normalizer.py ─────────────► ui_intent_ir_normalized.json     │
│       │   • Gap-fills missing values                                        │
│       │   • order → 999                                                     │
│       │   • enabled → false                                                 │
│       │   • render_mode → FLAT                                              │
│       │   • visibility → ALWAYS                                             │
│       ▼                                                                     │
│   [C] intent_compiler.py (HOSTILE) ─────► ui_intent_ir_compiled.json       │
│       │   • FAIL HARD on errors                                             │
│       │   • Unknown render_mode → ABORT                                     │
│       │   • Unknown control type → ABORT                                    │
│       │   • Disabled without reason → ABORT                                 │
│       ▼                                                                     │
│   [D] ui_projection_builder.py ─────────► ui_projection_lock.json (LOCKED) │
│       │   • Expand domains → panels → controls                              │
│       │   • Explicit ordering everywhere                                    │
│       │   • No optional fields                                              │
│       │   • editable: false                                                 │
│       ▼                                                                     │
│   [E] TypeScript Types ─────────────────► website/app-shell/src/contracts/ │
│       │   • UIProjectionLock                                                │
│       │   • Domain, Panel, Control types                                    │
│       │   • Runtime validation                                              │
│       ▼                                                                     │
│   [F] CI Validation ────────────────────► scripts/ci/validate_projection_lock.py
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Statistics

| Stage | Output | Count |
|-------|--------|-------|
| Raw | ui_intent_ir_raw.json | 303 rows |
| Normalized | ui_intent_ir_normalized.json | 303 rows, 793 fields filled |
| Compiled | ui_intent_ir_compiled.json | 303 rows, validation PASSED |
| Locked | ui_projection_lock.json | 5 domains, 52 panels, 95 controls |

---

## Preflight Console

### Purpose

Test L2.1 UI changes before promotion to production.

### URLs

| Environment | URL | Header |
|-------------|-----|--------|
| Preflight | https://preflight-console.agenticverz.com | `X-AOS-Environment: preflight` |
| Production | https://console.agenticverz.com | (none) |

### Shared Resources

- Same backend API (port 8000)
- Same Clerk authentication
- Same RBAC rules
- Different frontend builds (`dist-preflight` vs `dist`)

---

## Governance Gates

### Preflight Build Gates (build_preflight_console.sh)

| Step | Name | Validation |
|------|------|------------|
| 1 | Pipeline Integrity | Projection lock schema valid |
| 2 | UI Consumes Projection | ProjectionSidebar, DomainPage, routes configured |
| 3 | Dependencies | npm install |
| 4 | Projection Copy | Copy ui_projection_lock.json to public/ |
| 5 | Build | Build with preflight environment |

### Production Promotion Gates (promote_to_production.sh)

| Gate | Name | Validation |
|------|------|------------|
| 1 | Pipeline Integrity | Projection lock schema valid |
| 2 | Preflight Build | dist-preflight exists |
| 3 | Preflight Accessibility | HTTP 200 |
| 4 | Domain/Panel Integrity | 5 domains, panels > 0 |
| 5 | Auth Configuration | Auth env vars present |
| 6 | UI Consumes Projection | ProjectionSidebar, DomainPage, routes configured |
| 7 | Human Approval | Interactive confirmation |

### UI Consumption Gate Checks

Both scripts verify:
- `ProjectionSidebar.tsx` exists
- `DomainPage.tsx` exists
- Routes configured for L2.1 domains (Overview, Activity, Incidents, Policies, Logs)
- `AppLayout.tsx` uses ProjectionSidebar
- ProjectionSidebar uses projection loader (`loadProjection`, `getEnabledPanels`)

---

## Scripts

| Script | Purpose | Location |
|--------|---------|----------|
| Full Pipeline | Run A→D stages | `scripts/tools/run_l2_pipeline.sh` |
| Raw Parser | Stage A | `scripts/tools/l2_raw_intent_parser.py` |
| Normalizer | Stage B | `scripts/tools/intent_normalizer.py` |
| Compiler | Stage C | `scripts/tools/intent_compiler.py` |
| Builder | Stage D | `scripts/tools/ui_projection_builder.py` |
| CI Validation | Stage F | `scripts/ci/validate_projection_lock.py` |
| Preflight Build | Build preflight | `scripts/ops/build_preflight_console.sh` |
| Promotion | Promote with gates | `scripts/ops/promote_to_production.sh` |

---

## Commands

```bash
# Run full L2.1 pipeline
./scripts/tools/run_l2_pipeline.sh

# Build preflight console
./scripts/ops/build_preflight_console.sh

# Validate CI gates
python3 scripts/ci/validate_projection_lock.py

# Validate promotion readiness
./scripts/ops/promote_to_production.sh --validate

# Promote to production (interactive)
./scripts/ops/promote_to_production.sh

# Rollback production
./scripts/ops/promote_to_production.sh --rollback
```

---

## Files

### Pipeline Artifacts

| File | Location |
|------|----------|
| Source Excel | `design/l2_1/supertable/l2_supertable_v3_cap_expanded.xlsx` |
| Raw IR | `design/l2_1/ui_contract/ui_intent_ir_raw.json` |
| Normalized IR | `design/l2_1/ui_contract/ui_intent_ir_normalized.json` |
| Compiled IR | `design/l2_1/ui_contract/ui_intent_ir_compiled.json` |
| Projection Lock | `design/l2_1/ui_contract/ui_projection_lock.json` |

### TypeScript Contracts

| File | Purpose |
|------|---------|
| `src/contracts/index.ts` | Module exports |
| `src/contracts/ui_projection_types.ts` | Type definitions |
| `src/contracts/ui_projection_loader.ts` | Runtime loader with validation |

### Projection-Driven UI Components

| File | Purpose |
|------|---------|
| `src/components/layout/ProjectionSidebar.tsx` | Sidebar that renders domains from projection |
| `src/pages/domains/DomainPage.tsx` | Domain page that renders panels from projection |
| `src/components/layout/AppLayout.tsx` | Uses ProjectionSidebar in preflight mode |
| `src/routes/index.tsx` | Routes for /overview, /activity, /incidents, /policies, /logs |

### Apache Configs

| File | Purpose |
|------|---------|
| `console.agenticverz.com.conf` | Production console |
| `preflight-console.agenticverz.com.conf` | Preflight console |

### Governance

| File | Purpose |
|------|---------|
| `docs/governance/PREFLIGHT_PROMOTION_CHECKPOINT.md` | Promotion rules |

---

## Valid Control Types

```
FILTER, SORT, SELECT_SINGLE, SELECT_MULTI, NAVIGATE,
BULK_SELECT, DETAIL_VIEW, ACTION, DOWNLOAD, EXPAND,
REFRESH, SEARCH, PAGINATION, TOGGLE, EDIT, DELETE,
CREATE, APPROVE, REJECT, ARCHIVE, EXPORT, IMPORT,
ACKNOWLEDGE, RESOLVE
```

---

## Valid Render Modes

```
FLAT, TREE, GRID, TABLE, CARD, LIST
```

---

## Valid Domains (Frozen v1)

```
Overview, Activity, Incidents, Policies, Logs
```

---

## Anti-Patterns (Forbidden)

| Action | Reason |
|--------|--------|
| Manual edit of ui_projection_lock.json | Bypasses validation |
| Direct copy to production | Skips preflight testing |
| Hardcoded domain/panel names in UI | Use projection loader |
| Import JSON directly | Use TypeScript contracts |
| Promotion without human approval | Governance violation |

---


---

## Updates

### Update (2026-01-07)

### Update (2026-01-07)

## 2026-01-07: Onboarding Completion Redirect Fix

Fixed post-onboarding redirects to be environment-aware.

### Issue
Onboarding CompletePage.tsx had hardcoded redirects:
- 'View Incidents' → /guard (wrong)
- 'Manage Policies' → /guard/policies (wrong)

### Fix
Added environment detection in CompletePage.tsx:
```typescript
const isPreflight = import.meta.env.VITE_PREFLIGHT_MODE === 'true';
const CONSOLE_ROOT = isPreflight ? '/overview' : '/guard';
const POLICIES_PATH = isPreflight ? '/policies' : '/guard/policies';
```

Now redirects correctly:
- Preflight: /overview, /policies
- Production: /guard, /guard/policies

Build timestamp: 20:56 CET



## 2026-01-07: Preflight Debug Logger Implementation

Added browser debug logger for L2.1 projection debugging.

### New Files
- `src/lib/preflightLogger.ts` — Core logger with styled console output

### Logger Features
- Conditional activation (only when VITE_PREFLIGHT_MODE=true)
- Styled console output with timestamps
- Log history (max 500 entries) with JSON export
- Category-specific logging: projection, nav, sidebar, domain, api

### Integration Points
- `ui_projection_loader.ts` — logs projection load/cache events
- `ProjectionSidebar.tsx` — logs sidebar render, domain expand/collapse, navigation
- `DomainPage.tsx` — logs domain render, subdomain/topic expand

### Browser API
```javascript
// Available in browser console when VITE_PREFLIGHT_MODE=true
window.preflightLogger.getHistory()  // Get log history
window.exportPreflightLogs()         // Download logs as JSON
```

### Routing Fix
- Root redirect now correctly routes to /overview in preflight mode
- Rebuilt preflight console with all changes at 20:48 CET


## Related PINs

- PIN-349: L2.1 UI Contract v1 Generation
- PIN-350: L2 Governed Pipeline with Approval Gate

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-07 | Initial pipeline implementation |
| 2026-01-07 | Added ACKNOWLEDGE, RESOLVE control types |
| 2026-01-07 | Preflight console deployed |
| 2026-01-07 | Governance checkpoint documented |
| 2026-01-07 | Added ProjectionSidebar and DomainPage components |
| 2026-01-07 | Added Gate 6: UI Consumes Projection Lock |
| 2026-01-07 | All 7 governance gates passing |
