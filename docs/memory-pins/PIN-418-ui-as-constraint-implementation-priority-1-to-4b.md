# PIN-418: UI-as-Constraint Implementation (Priority-1 to 4B)

| Field | Value |
|-------|-------|
| **Status** | COMPLETE |
| **Category** | Architecture / UI Governance |
| **Milestone** | UI-as-Constraint Doctrine |
| **Created** | 2026-01-14 |
| **Author** | Claude (pair) |

## Summary

Implementation of the UI-as-Constraint doctrine across Priority-1 through Priority-4B. This work establishes the canonical authority model where `ui_plan.yaml` is the highest authority, and the compiler/projection mechanically derive state from it. All 87 panels now render with proper state UX.

## Priority-1: Domain Visibility (COMPLETE)

**Goal:** Wire Account and Connectivity domains to sidebar navigation.

### Files Modified

| File | Changes |
|------|---------|
| `website/app-shell/src/contracts/ui_projection_types.ts` | Extended `DomainName` type to include "Account" and "Connectivity" |
| `website/app-shell/src/routing/consoleRoots.ts` | Added `account` and `connectivity` to `DOMAIN_ROOTS` |
| `website/app-shell/src/components/layout/ProjectionSidebar.tsx` | Added User/Plug icons to `DOMAIN_ICONS` |
| `website/app-shell/src/pages/domains/DomainPage.tsx` | Added User/Plug icons, exported `AccountPage` and `ConnectivityPage` |
| `website/app-shell/src/pages/panels/PanelView.tsx` | Added User/Plug icons to `DOMAIN_ICONS` |
| `website/app-shell/src/routes/index.tsx` | Added routes for Account and Connectivity pages |
| `website/app-shell/src/routing/routes.ts` | Updated `CUSTOMER_ROUTES` to include account/connectivity |

### Result
- All 7 domains now visible in sidebar: Overview, Activity, Incidents, Policies, Logs, Account, Connectivity
- Routes properly configured for `/precus/account` and `/precus/connectivity`

---

## Priority-2: UI Scaffolding Adapter (COMPLETE)

**Goal:** Wire subdomains/topics from ui_plan.yaml as navigable UI scaffolding WITHOUT touching projection/backend/SDSR.

### Key Insight
> "UI expresses human intent. Backend earns the right to fill it."

The UI plan is authoritative. EMPTY/UNBOUND states must render visibly. Projection is NOT required for navigation structure.

### Files Created

| File | Purpose |
|------|---------|
| `website/app-shell/src/contracts/ui_plan_scaffolding.ts` | Static TypeScript scaffolding data derived from ui_plan.yaml |

### Files Modified

| File | Changes |
|------|---------|
| `website/app-shell/src/contracts/ui_projection_loader.ts` | Added scaffolding fallback for `getDomain`, `getDomains`, `getSubdomainsForDomain`, `getTopicsForSubdomain` |
| `website/app-shell/src/pages/domains/DomainPage.tsx` | Updated topics useMemo to fall back to scaffolding when panels empty |

### Key Functions Added

```typescript
// ui_projection_loader.ts
function scaffoldingToDomain(scaffolding: ScaffoldingDomain): Domain
export function getTopicsForSubdomain(domainName: DomainName, subdomainId: string)
export function domainHasScaffolding(domainName: DomainName): boolean
export function isDomainFromProjection(domainName: DomainName): boolean
```

### Result
- UI renders structural scaffolding from ui_plan.yaml when projection is incomplete
- Account and Connectivity domains visible with proper subdomain/topic structure
- No backend changes required

---

## Priority-3A: Compiler Alignment (COMPLETE)

**Goal:** Make projection structurally complete with all 87 panels from ui_plan.yaml using mechanical state derivation.

### Compiler Changes (`backend/aurora_l2/SDSR_UI_AURORA_compiler.py`)

| Change | Location | Description |
|--------|----------|-------------|
| UI Plan path constant | Lines 71-74 | `UI_PLAN_PATH` points to canonical authority |
| Domain display order | Lines 331-341 | All 7 domains now in `DOMAIN_DISPLAY_ORDER` |
| `load_ui_plan()` | Lines 198-218 | Loads ui_plan.yaml as canonical authority |
| `derive_panel_state()` | Lines 221-281 | Mechanically derives EMPTY/UNBOUND/DRAFT/BOUND/DEFERRED |
| `generate_canonical_projection()` | Lines 430-657 | Rewritten to iterate over ui_plan (not just compiled intents) |
| `_build_panel_from_intent()` | Lines 660-743 | Builds panel from compiled intent with derived state |
| `_build_empty_panel()` | Lines 746-794 | Builds EMPTY panel when no intent exists |
| `_get_disabled_reason()` | Lines 797-807 | Returns disabled reason based on state |
| `_build_empty_content_blocks()` | Lines 810-836 | Minimal content blocks for EMPTY panels |
| Statistics update | Lines 613-634 | Includes `empty_panels`, `deferred_panels`, `ui_plan_source` |
| `main()` update | Lines 1040-1153 | Loads ui_plan first, uses new projection signature |

### State Derivation Rules

| State | Condition |
|-------|-----------|
| EMPTY | intent_spec is null OR intent YAML doesn't exist on disk |
| UNBOUND | Intent exists but capability missing or not registered |
| DRAFT | Capability DECLARED but SDSR not observed |
| BOUND | Capability OBSERVED or TRUSTED |
| DEFERRED | Explicit governance decision in ui_plan.yaml |

### Projection Output

```
Domains: 7
Panels: 87
States:
  EMPTY: 32
  UNBOUND: 54
  DRAFT: 0
  BOUND: 1
  DEFERRED: 0
```

### Also Fixed
- `design/l2_1/ui_plan.yaml` summary corrected from 86 to 87 panels (count was wrong)

---

## Authority Model (LOCKED)

```
┌─────────────────────────────────────────────────────────────┐
│ ui_plan.yaml (human constraint) — HIGHEST AUTHORITY        │
│      ↓                                                      │
│ ui_projection_lock.json (machine mirror, complete)          │
│      ↓                                                      │
│ Frontend renderer (dumb consumer)                           │
└─────────────────────────────────────────────────────────────┘
```

## Invariants Established

1. **UI plan declares surface** — All 87 panels exist because ui_plan says so
2. **Compiler derives state mechanically** — No interpretation, just inputs → state
3. **EMPTY panels are signals, not failures** — They render as empty state UX
4. **Scaffolding provides navigation** — Structure comes from ui_plan, data from projection
5. **Backend earns binding** — SDSR observation promotes UNBOUND → DRAFT → BOUND

## Priority-3B: PDG Verification (COMPLETE)

**Goal:** Prove the new projection is valid and intentional via Projection Diff Guard.

### PDG Report: PASS WITH EXPECTED STRUCTURAL DELTA

| Violation Type | Count | Verdict |
|----------------|-------|---------|
| PDG-001 (new panels) | 33 | **EXPECTED** - New panels from ui_plan.yaml additions |
| PDG-002 (subdomain rename) | 10 | **CORRECT** - Fixed outdated LLM_RUNS → EXECUTIONS |
| PDG-003 (binding regression) | 0 | **FIXED** - Bug in derive_panel_state() corrected |

### Bug Fixed
- `derive_panel_state()` was not checking `activate_actions` from compiled intent against capability registry
- This caused BOUND panels (like POL-PR-PP-O2) to regress to UNBOUND
- Fixed by adding `compiled_intent` parameter to derive_panel_state()

### Result
- 43 violations all explained (structural changes, not regressions)
- Projection accepted as canonical mirror of UI plan

---

## Priority-4A: Sorting Lock (COMPLETE)

**Goal:** Ensure panels appear in the same order every run.

### Sorting Order (LOCKED)

1. **Domain** → by DOMAIN_DISPLAY_ORDER (0-6)
2. **Subdomain** → by position in ui_plan.yaml
3. **Topic** → by position in ui_plan.yaml
4. **Panel** → by position in ui_plan.yaml (within topic)

### Changes Made

| File | Change |
|------|--------|
| `backend/aurora_l2/SDSR_UI_AURORA_compiler.py` | Removed runtime sort that collapsed topic structure |

### Before (Wrong)
```
ACT-EX-AR-O1, ACT-EX-CR-O1, ACT-EX-RD-O1 (all O1 together)
ACT-EX-AR-O2, ACT-EX-CR-O2, ACT-EX-RD-O2 (all O2 together)
```

### After (Correct)
```
ACT-EX-AR-O1, ACT-EX-AR-O2 (ACTIVE_RUNS together)
ACT-EX-CR-O1, ACT-EX-CR-O2, ACT-EX-CR-O3 (COMPLETED_RUNS together)
ACT-EX-RD-O1, ACT-EX-RD-O2, ACT-EX-RD-O3, ACT-EX-RD-O4, ACT-EX-RD-O5 (RUN_DETAILS together)
```

---

## Priority-4B: State UX Audit (COMPLETE)

**Goal:** Every panel state renders honestly. UI says "nothing here" instead of lying/hiding.

### State → UX Contract (LOCKED)

| State | Label | Dim Header? | Show Controls? | Message |
|-------|-------|-------------|----------------|---------|
| EMPTY | Empty | yes | no | "This panel is planned but not yet defined" |
| UNBOUND | Awaiting Backend | yes | no | "Backend capability not connected" |
| DRAFT | Preview | no | yes (disabled) | "Data not yet observed" |
| BOUND | (none) | no | yes | (normal) |
| DEFERRED | On Hold | yes | no | "This feature is deferred by governance" |

### Compiler Changes

| File | Change |
|------|--------|
| `backend/aurora_l2/SDSR_UI_AURORA_compiler.py` | All panels now `enabled: True` (MUST render) |
| `backend/aurora_l2/SDSR_UI_AURORA_compiler.py` | `_get_disabled_reason()` returns state-specific messages |
| `backend/aurora_l2/SDSR_UI_AURORA_compiler.py` | Content blocks visible for all states (not HIDDEN) |

### Frontend Changes

| File | Change |
|------|--------|
| `website/app-shell/src/pages/domains/DomainPage.tsx` | State label badges (Empty, Awaiting Backend, Preview, On Hold) |
| `website/app-shell/src/pages/domains/DomainPage.tsx` | Dim header styling for EMPTY/UNBOUND/DEFERRED |
| `website/app-shell/src/pages/domains/DomainPage.tsx` | State-specific empty state message display |
| `website/app-shell/src/pages/domains/DomainPage.tsx` | Updated comment block with State → UX contract |

### Projection Statistics (Final)

```
Panels: 87
  Enabled: 87 (all panels render)
  Disabled: 0

By State:
  BOUND: 2
  DRAFT: 5
  EMPTY: 32
  UNBOUND: 48
```

---

## Reference

- UI-as-Constraint Doctrine: `docs/contracts/UI_AS_CONSTRAINT_V1.md`
- Architecture Constraints: `docs/contracts/ARCHITECTURE_CONSTRAINTS_V1.yaml`
- UI Plan Authority: `design/l2_1/ui_plan.yaml`
