# Overview Domain — Canonical Software Literature

**Domain:** overview
**Generated:** 2026-01-31
**Reference:** PIN-502
**Total Files:** 6 (2 L5_engines, 1 L5_schemas, 2 L6_drivers, 1 __init__.py)

---

## Reality Delta (2026-02-12, Wave-4 Script Coverage Audit)

- Wave-4 target scope for overview is fully classified: `5` scripts (`2 UC_LINKED`, `3 NON_UC_SUPPORT`, `0 UNLINKED`).
- `UC_LINKED` mapping is to `UC-001` in `HOC_USECASE_CODE_LINKAGE.md`.
- Architecture gates remain deterministic and clean in Wave-4 audit, with governance suite at `308` passing tests.

## Consolidation Actions (2026-01-31)

### Naming Violations — None

All files compliant. No renames needed.

### Header Correction (1)

| File | Old Header | New Header |
|------|-----------|------------|
| overview/__init__.py | `# Layer: L4 — Domain Services` | `# Layer: L5 — Domain (Overview)` |

### Legacy Connections — None

Zero active `app.services` imports. Clean.

### Cross-Domain Imports — None at L5 level

The L6 driver (`overview_facade_driver.py`) reads from multiple domain tables (Incident, PolicyProposal, Limit, LimitBreach, WorkerRun, AuditLedger) — this is by design. Overview is a **PROJECTION-ONLY** domain that synthesizes status from other domains but owns no state.

---

## Domain Contract (from __init__.py)

Overview is a **PROJECTION-ONLY** domain. It synthesizes status from other domains but owns no state and triggers no effects.

**Invariants (Non-Negotiable):**
- INV-OVW-001: Overview DOES NOT own any tables
- INV-OVW-002: Overview NEVER triggers side-effects
- INV-OVW-003: All mutations route to owning domains
- INV-OVW-004: No business rules — composition only

**Boundary with Analytics:**
- Overview: "What is the current status?"
- Analytics: "What patterns exist? What will happen?"

---

## L5_engines (2 files)

### __init__.py
- **Role:** Package init, re-exports OverviewFacade and all result types

### overview_facade.py
- **Role:** Overview engine — centralized access to overview operations (async, read-only)
- **Classes:** OverviewFacade, SystemPulse, DomainCount, HighlightsResult, DecisionItem, DecisionsResult, CostPeriod, LimitCostItem, CostsResult, DecisionsCountResult, RecoveryStatsResult
- **Factory:** `get_overview_facade()`
- **Callers:** L4 overview_handler (overview.query)

---

## L5_schemas (1 file)

### __init__.py
- **Role:** Schemas package init (placeholder)

---

## L6_drivers (2 files)

### __init__.py
- **Role:** Package init, exports OverviewFacadeDriver

### overview_facade_driver.py
- **Role:** Pure data access for overview aggregation (async, cross-domain reads)
- **Classes:** OverviewFacadeDriver
- **Reads:** Incident, PolicyProposal, Limit, LimitBreach, WorkerRun, AuditLedger

---

## L4 Handler

**File:** `hoc/cus/hoc_spine/orchestrator/handlers/overview_handler.py`
**Operations:** 1

| Operation | Handler Class | Target |
|-----------|--------------|--------|
| overview.query | OverviewQueryHandler | OverviewFacade |

No import updates required.

---

## Cleansing Cycle (2026-01-31) — PIN-503

### No Actions Required

Domain has zero `app.services` imports, zero `cus.general` imports, zero cross-domain violations.

### Tally

8/8 checks PASS (6 consolidation + 2 cleansing).

---

## PIN-507 Law 5 Remediation (2026-02-01)

**L4 Handler Update:** All `getattr()`-based reflection dispatch in this domain's L4 handler replaced with explicit `dispatch = {}` maps. All `asyncio.iscoroutinefunction()` eliminated via explicit sync/async split. Zero `__import__()` calls remain. See PIN-507 for full audit trail.

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`
