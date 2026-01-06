# Phase Status

**Current Phase:** Phase 2 PENDING
**Last Updated:** 2026-01-06
**Reference:** PIN-319 (Frontend Realignment)

---

## Current Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | COMPLETE | Frontend Realignment (PIN-319) |
| Phase 2 | PENDING | L2.1 Headless Layer (Synthetic Journeys) |
| Phase 3 | NOT STARTED | TBD |

---

## Phase 1: Frontend Realignment (COMPLETE)

### Completed Work

- [x] Renamed `aos-console/console` → `app-shell`
- [x] Extracted founder UI to `website/fops/`
- [x] Extracted onboarding to `website/onboarding/`
- [x] All founder routes under `/fops/*` with FounderRoute
- [x] API clients classified by audience
- [x] Import boundary checks (CI blocking)
- [x] Directory ownership checks (CI blocking)
- [x] Route namespace guards (CI blocking)
- [x] Onboarding handoff contract documented

### Hardening Complete

- [x] R1-1: App-Shell Scope Contract (`APP_SHELL_SCOPE.md`)
- [x] R1-2: Page Budget Enforcement (soft guard)
- [x] R2-1: API Client Audience Classification
- [x] R2-2: Import Boundary Check (hard guard)
- [x] R3-1: Onboarding Handoff Contract
- [x] R3-2: Manual Smoke Validation (checklist ready)
- [x] G-1: Directory Ownership Rules
- [x] G-2: Route Namespace Guard
- [x] G-3: Phase Marker Lock (this document)

---

## Phase 2: L2.1 Headless Layer (PENDING)

### Entry Criteria

Before starting Phase 2:

- [x] All Phase 1 hardening complete
- [x] Build passes all guards
- [x] No structural regressions
- [ ] Phase 2 TODO list approved

### Scope (TBD)

- Synthetic journey framework
- Headless API testing
- L2.1 implementation

---

## UI Change Protocol

**Any UI changes require:**

1. Phase bump justification
2. PIN documentation
3. Update to this document
4. Review of affected contracts

**Forbidden without Phase bump:**

- New pages in app-shell
- New routes
- New API clients
- Structural changes to fops/onboarding

---

## Guards Summary

| Guard | Type | Script |
|-------|------|--------|
| UI Hygiene | Soft (warnings) | `npm run hygiene` |
| Page Budget | Soft (warning) | `npm run hygiene` |
| Import Boundary | Hard (blocks) | `npm run boundary` |
| Directory Ownership | Hard (blocks) | `npm run ownership` |
| Route Namespace | Hard (blocks) | `npm run routes` |
| All Guards | Combined | `npm run guards` |

---

## References

- PIN-319: Frontend Realignment - App Shell Architecture
- `website/app-shell/APP_SHELL_SCOPE.md`
- `docs/inventories/FRONTEND_API_AUDIENCE_MAP.md`
- `docs/contracts/ONBOARDING_TO_APP_SHELL.md`
