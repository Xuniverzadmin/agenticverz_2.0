# App-Shell TypeScript Debt Inventory

**Date:** 2026-02-15
**Total Errors:** 293
**Scope:** `npm run typecheck` (global `tsc --noEmit`)
**Status:** Non-blocking — separated from UAT release criteria
**Reference:** `UC_UAT_FINDINGS_CLEARANCE_DETOUR_PLAN_2026-02-15.md` (E5)

---

## Error Distribution by Directory

| Bucket | Count | % | Notes |
|--------|-------|---|-------|
| `../fops/` (cross-app) | 232 | 79% | Founder ops pages — missing type declarations for react/react-router-dom/axios in fops workspace |
| `src/` (app-shell core) | 42 | 14% | Quarantine hooks/API (23), domain pages (8), components (4), contracts (3), panels (4) |
| `../onboarding/` (cross-app) | 19 | 7% | Onboarding pages — same missing type declarations issue as fops |

## Detailed Breakdown by Sub-Directory

### `../fops/` — 232 errors
| Sub-path | Count | Root Cause |
|----------|-------|------------|
| `pages/workers/components/` | 69 | Missing type fields on interfaces (RoutingDecisionEvent, DriftEvent) |
| `pages/workers/` | 44 | Worker console — event type mismatches |
| `pages/founder/` | 41 | Founder pages — missing module declarations |
| `pages/ops/` | 11 | Ops console — same pattern |
| `pages/traces/` | 10 | Trace pages — missing modules |
| `pages/sba/` | 26 | SBA inspector components — type mismatches |
| `pages/integration/` | 9 | Integration dashboard — missing modules |
| `pages/recovery/` | 4 | Recovery page — missing modules |
| Other | 18 | Scattered component-level issues |

### `src/` — 42 errors
| Sub-path | Count | Root Cause |
|----------|-------|------------|
| `quarantine/hooks/` | 15 | Quarantined hooks — stale interfaces |
| `quarantine/api/` | 8 | Quarantined API clients — stale types |
| `pages/domains/DomainPage.tsx` | 8 | Binding status comparisons (`EMPTY`, `DEFERRED` not in BindingStatus type) |
| `quarantine/pages/credits/` | 4 | Credits page — stale interfaces |
| `components/controls/` | 2 | `disabled_reason` not on Control type |
| `components/HealthIndicator.tsx` | 2 | Function signature mismatch |
| `contracts/ui_projection_loader.ts` | 1 | `unknown` to `string` argument |
| `pages/panels/PanelView.tsx` | 1 | Missing `Analytics` in domain icon map |
| `components/layout/Header.tsx` | 1 | `formatCredits` not defined |

### `../onboarding/` — 19 errors
| Sub-path | Count | Root Cause |
|----------|-------|------------|
| All pages | 19 | Missing type declarations for `react`, `react-router-dom`, `axios` in onboarding workspace (no local `node_modules` or tsconfig reference) |

## Remediation Waves (Proposed)

| Wave | Scope | Effort | Impact |
|------|-------|--------|--------|
| Wave 1 | `../fops/` + `../onboarding/` workspace tsconfig | Low | -251 errors (86%) — add `compilerOptions.paths` or workspace `node_modules` symlink |
| Wave 2 | `src/quarantine/` cleanup | Medium | -27 errors — remove or fix quarantined modules |
| Wave 3 | `src/` core type fixes | Low | -15 errors — DomainPage binding status, Control type, PanelView icon map |

## Separation from UAT Gate

The UAT gate (`hoc_uc_validation_uat_gate.sh`) uses:
- `npm run typecheck:uat` — **BLOCKING** (scoped to `src/features/uat/`, 0 errors)
- `npm run typecheck` — **NON-BLOCKING** (informational debt report, 293 errors)

This debt is tracked separately and does not affect UAT release criteria.
