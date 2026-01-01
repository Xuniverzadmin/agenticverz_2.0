# Signal Circuit Discovery (SCD) Index

**Status:** PHASE 1 RATIFIED
**Date:** 2025-12-31
**Ownership Assigned:** 2025-12-31
**Ratified:** 2026-01-01
**Reference:** PRODUCT_DEVELOPMENT_CONTRACT_V3.md

---

## Purpose

This directory contains Signal Circuit Discovery (SCD) checklists for each layer boundary.
SCD is forensic topology mapping — observe and document, do NOT fix.

**Closed Signal Circuit:** INTENT → EMISSION → TRANSPORT → ADAPTER → CONSUMPTION → CONSEQUENCE

---

## Layer Model (L1-L8)

| Layer | Name | Description |
|-------|------|-------------|
| L1 | Product Experience | UI pages, components |
| L2 | Product APIs | REST endpoints |
| L3 | Boundary Adapters | Thin translation, < 200 LOC |
| L4 | Domain Engines | Business rules, system truth |
| L5 | Execution & Workers | Background jobs |
| L6 | Platform Substrate | DB, Redis, external services |
| L7 | Ops & Deployment | Systemd, Docker |
| L8 | Catalyst / Meta | CI, tests, validators |

---

## SCD Status

| Boundary | Status | Gaps Found | Blocking for Phase 2? |
|----------|--------|------------|----------------------|
| L4↔L5 | ✅ COMPLETE | 5 | NO |
| L8↔All | ✅ COMPLETE | 7 (2 P0 closed) | NO (ownership assigned) |
| L2↔L4 | ✅ COMPLETE | 5 | NO |
| L5↔L6 | ✅ COMPLETE | 5 | NO |
| L1↔L2 | ⏳ PENDING | - | TBD |
| L2↔L3 | N/A | - | - |
| L3↔L4 | N/A | - | - |

---

## Gap Summary

### P0 (Critical - Blocking) — CLOSED

| Gap ID | Boundary | Description | Status |
|--------|----------|-------------|--------|
| GAP-L8A-001 | L8↔All | 18/22 CI signals have no documented owner | ✅ CLOSED (2025-12-31) |
| GAP-L8A-002 | L8↔All | Main CI (SIG-001) is CRITICAL_UNOWNED | ✅ CLOSED (2025-12-31) |

**Closure:** All 22 signals assigned ownership. See `CI_SIGNAL_REGISTRY.md` for assignments.

### P1 (High)

| Gap ID | Boundary | Description | Resolution Required |
|--------|----------|-------------|---------------------|
| GAP-L2L4-001 | L2↔L4 | 30/33 API files have no L3 adapter | Code: Create adapters or accept |
| GAP-L2L4-002 | L2↔L4 | runtime.py imports directly from L5 | Code: Route through L3 adapter |
| GAP-L2L4-004 | L2↔L4 | No CI check for L2→L3→L4 import direction | CI: Add import checker |
| GAP-L4L5-001 | L4↔L5 | L5 RunRunner directly imports L4 planners/memory | Code: Add adapter or accept |
| GAP-L4L5-004 | L4↔L5 | No CI check for L5→L4 import direction | CI: Add import checker |
| GAP-L8A-003 | L8↔All | Some tests are environment-dependent | CI: Fix flaky tests |
| GAP-L8A-005 | L8↔All | No CI check for layer import direction | CI: Add import checker |
| GAP-L8A-007 | L8↔All | Manual overrides possible without ratification | Governance: Document |

### P2 (Medium)

| Gap ID | Boundary | Description | Resolution Required |
|--------|----------|-------------|---------------------|
| GAP-L2L4-003 | L2↔L4 | runtime.py imports directly from L4 commands | Code: Route through L3 adapter |
| GAP-L2L4-005 | L2↔L4 | No enforcement that L3 adapters stay thin | CI: Add LOC checker |
| GAP-L4L5-002 | L4↔L5 | Auto-execute confidence threshold hardcoded in L5 | Code: Move to L4 |
| GAP-L4L5-003 | L4↔L5 | Category/recovery heuristics in L5 instead of L4 | Code: Move to L4 |
| GAP-L5L6-001 | L5↔L6 | No L6 abstraction layer (workers use raw SQL) | Code: Add repository pattern |
| GAP-L5L6-003 | L5↔L6 | No circuit breaker for external HTTP calls | Code: Add circuit breaker |
| GAP-L5L6-004 | L5↔L6 | No retry logic for transient DB failures | Code: Add retry logic |
| GAP-L8A-004 | L8↔All | BLCA not run in all relevant workflows | CI: Add to workflows |
| GAP-L8A-006 | L8↔All | CI outcomes don't auto-update governance artifacts | CI/Governance |

### P3 (Low)

| Gap ID | Boundary | Description | Resolution Required |
|--------|----------|-------------|---------------------|
| GAP-L4L5-005 | L4↔L5 | Redundant budget check in L5 vs L4 | Accept or consolidate |
| GAP-L5L6-002 | L5↔L6 | Multiple raw SQL text queries in L5 | Accept or convert to ORM |
| GAP-L5L6-005 | L5↔L6 | Event publisher coupling not explicit | Accept or make explicit |

---

## Documents

| File | Description |
|------|-------------|
| `SIGNAL_CIRCUIT_DISCOVERY_TEMPLATE.md` | Blank template for new boundaries |
| `SCD-L4-L5-BOUNDARY.md` | L4↔L5 (Domain↔Workers) discovery |
| `SCD-L8-ALL-BOUNDARY.md` | L8↔All (CI↔All layers) discovery |
| `SCD-L2-L4-BOUNDARY.md` | L2↔L4 (APIs↔Domain via Adapters) discovery |
| `SCD-L5-L6-BOUNDARY.md` | L5↔L6 (Workers↔Platform) discovery |
| `PHASE_1_EXIT_DECLARATION.md` | Phase-1 exit ratification (RATIFIED) |
| `PHASE_1_5_TRANSITION_PLAN_DRAFT.md` | Phase-1.5 transition planning |
| `FUTURE_DELEGATION_CHECKLIST_DRAFT.md` | Ownership redistribution planning |
| `WAVE_1_IMPORT_DIRECTION_PLAN.md` | Wave-1 CI enforcement planning |
| `IMPORT_VIOLATION_BASELINE.md` | Violation baseline observation |

---

## Phase 1 Completion Criteria Status

From PRODUCT_DEVELOPMENT_CONTRACT_V3.md:

- [x] All existing CI checks inventoried (24 workflows)
- [x] Each signal classified by type (Structural/Semantic/Behavioral/Product)
- [x] Each signal has enforcement level (BLOCKING/ADVISORY/INFORMATIONAL)
- [x] **Every signal has a named owner** (22/22 assigned — 2025-12-31)
- [x] Every signal has failure meaning
- [x] Flaky signals identified (m7-nightly-smoke.yml)
- [x] Same commit = same CI result (verified for blocking signals)
- [x] CI trusted enough to block releases (ownership assigned)
- [ ] No manual overrides except via governance ratification (P1 — NOT ENFORCED)
- [ ] CI outcomes feed governance artifacts (P2 — NOT IMPLEMENTED)

**Phase 1 Status: COMPLETE** — Structural closure achieved (2025-12-31)

> **Note:** Two P1/P2 items remain open but are NOT blocking for Phase 2.
> They are documented in GAP-L8A-006 and GAP-L8A-007.

---

## Next Steps (Phase 2)

1. ~~**Human Required:** Assign owners to 18 unowned CI signals~~ ✅ DONE
2. ~~**Human Required:** Assign owner to SIG-001 (main CI)~~ ✅ DONE
3. Continue SCD for remaining boundaries (L1↔L2)
4. Add import direction checker to CI (GAP-L8A-005, GAP-L4L5-004, GAP-L2L4-004)
5. Document manual override ratification process (GAP-L8A-007)
6. Implement CI→governance artifact pipeline (GAP-L8A-006)

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-01 | Phase-1.5: Wave-1 planning docs and violation baseline added |
| 2026-01-01 | **PHASE 1 RATIFIED:** Exit declaration signed by Maheshwar VM |
| 2025-12-31 | **PHASE 1 COMPLETE:** All ownership assigned, P0 gaps closed |
| 2025-12-31 | Added L5↔L6 boundary discovery (5 gaps found) |
| 2025-12-31 | Added L2↔L4 boundary discovery (5 gaps found) |
| 2025-12-31 | Index created with L4↔L5 and L8↔All complete |
