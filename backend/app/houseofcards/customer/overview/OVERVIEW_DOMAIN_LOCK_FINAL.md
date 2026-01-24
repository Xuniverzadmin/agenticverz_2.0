# Overview Domain Lock — FINAL
# Status: LOCKED
# Effective: 2026-01-24
# Reference: Phase-2.5B Overview Extraction (OVERVIEW_PHASE2.5_IMPLEMENTATION_PLAN.md)

---

## Domain Status

**LOCKED** — No modifications permitted without explicit unlock command.

| Attribute | Value |
|-----------|-------|
| Lock Date | 2026-01-24 |
| Lock Version | 1.0.0 |
| BLCA Baseline | 0 violations |
| Phase 2.5B Fixes | 1/1 COMPLETE |

---

## Domain Nature

> **Overview is a READ-ONLY aggregation domain — it queries, never writes.**

Overview domain:
- **Aggregates** — data from Activity, Incidents, Policies, Logs
- **Projects** — system pulse, domain counts, decisions queue
- **Reads** — never owns tables, never writes

Overview does NOT:
- Own any database tables
- Mutate any data
- Execute business decisions (only projects them)
- Contain direct DB access in facades (→ L6 drivers)

---

## Phase 2.5B Boundary Repairs

### Summary

| # | File | Original Layer | Violation | Fix Type | New Artifact |
|---|------|----------------|-----------|----------|--------------|
| 1 | `facades/overview_facade.py` | L4 | sqlalchemy runtime imports + L4→L7 model imports | Extraction | `drivers/overview_facade_driver.py` (L6) |

---

### Fix 1: overview_facade.py — L4 Sqlalchemy Extraction

**Violation:** L4 facade with sqlalchemy runtime imports (lines 46-47) and direct L7 model imports (lines 52-56)

**Before:**
```python
# overview_facade.py (L4)
from sqlalchemy import and_, case, func, select          # ❌ FORBIDDEN
from sqlalchemy.ext.asyncio import AsyncSession          # ❌ FORBIDDEN
from app.models.audit_ledger import AuditLedger          # ❌ L4→L7
from app.models.killswitch import Incident, ...          # ❌ L4→L7
from app.models.policy import PolicyProposal             # ❌ L4→L7
from app.models.policy_control_plane import Limit, ...   # ❌ L4→L7
from app.models.tenant import WorkerRun                  # ❌ L4→L7
```

**After:**
- Created `drivers/overview_facade_driver.py` (L6)
- Driver contains all sqlalchemy imports and DB queries
- Driver contains all model imports
- Driver returns snapshot dataclasses to facade
- Facade uses TYPE_CHECKING pattern for type hints
- Facade delegates all data access to driver
- Facade composes business results from driver snapshots

**New Artifact:**
```
drivers/overview_facade_driver.py (L6)
├── IncidentCountSnapshot (dataclass)
├── ProposalCountSnapshot (dataclass)
├── BreachCountSnapshot (dataclass)
├── RunCountSnapshot (dataclass)
├── AuditCountSnapshot (dataclass)
├── IncidentSnapshot (dataclass)
├── ProposalSnapshot (dataclass)
├── LimitSnapshot (dataclass)
├── RunCostSnapshot (dataclass)
├── BreachStatsSnapshot (dataclass)
├── IncidentDecisionCountSnapshot (dataclass)
├── RecoverySnapshot (dataclass)
└── OverviewFacadeDriver (class)
    ├── fetch_incident_counts()
    ├── fetch_proposal_counts()
    ├── fetch_breach_counts()
    ├── fetch_run_counts()
    ├── fetch_last_activity()
    ├── fetch_pending_incidents()
    ├── fetch_pending_proposals()
    ├── fetch_run_cost()
    ├── fetch_budget_limits()
    ├── fetch_breach_stats()
    ├── fetch_incident_decision_counts()
    ├── fetch_proposal_count()
    └── fetch_recovery_stats()
```

**Call Flow:**
```
BEFORE: Facade (L4) → DB directly  ❌
AFTER:  Facade (L4) → Driver (L6) → DB  ✅
```

---

## Locked Artifacts

### L4 Facades (facades/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `overview_facade.py` | LOCKED | 2026-01-24 | Main facade (DB extracted, TYPE_CHECKING) |
| `__init__.py` | LOCKED | 2026-01-24 | Facade exports |

### L6 Drivers (drivers/)

| File | Status | Lock Date | Notes |
|------|--------|-----------|-------|
| `overview_facade_driver.py` | LOCKED | 2026-01-24 | **NEW** — Extracted from facade |
| `__init__.py` | LOCKED | 2026-01-24 | Driver exports |

### Other Directories

| Directory | Status | Lock Date | Notes |
|-----------|--------|-----------|-------|
| `engines/` | LOCKED | 2026-01-24 | Empty (overview has no engines) |
| `schemas/` | LOCKED | 2026-01-24 | Empty (overview uses facade dataclasses) |

---

## Governance Invariants

| ID | Rule | Status | Enforcement |
|----|------|--------|-------------|
| **INV-OVW-001** | L4 cannot import sqlalchemy at runtime | COMPLIANT | BLCA |
| **INV-OVW-002** | L4 cannot import from L7 models directly | COMPLIANT | BLCA |
| **INV-OVW-003** | Facades delegate, never query directly | COMPLIANT | BLCA |
| **INV-OVW-004** | Call flow: Facade → Driver | COMPLIANT | Architecture |
| **INV-OVW-005** | Driver returns snapshots, not ORM models | COMPLIANT | Code review |

---

## Known Technical Debt (Non-Blocking)

**None** — Overview domain achieved zero violations.

| Category | Count | Severity | Phase |
|----------|-------|----------|-------|
| SQLALCHEMY_RUNTIME | 0 | — | — |
| LAYER_BOUNDARY | 0 | — | — |
| BANNED_NAMING | 0 | — | — |
| LEGACY_IMPORT | 0 | — | — |

**Total:** 0 violations

---

## Lock Rules

### What Is Locked

1. **Layer assignments** — No file may change its declared layer
2. **File locations** — No file may move between directories
3. **New extractions** — No new L4/L6 splits without unlock
4. **Business logic placement** — L6 drivers remain pure data access
5. **Import boundaries** — L4 facade cannot add sqlalchemy imports

### What Is Allowed (Without Unlock)

1. **Bug fixes** — Within existing file boundaries
2. **Documentation** — Comments, docstrings
3. **Type hints** — Adding TYPE_CHECKING imports
4. **Test coverage** — New tests for existing code

### Unlock Procedure

To modify locked artifacts:

1. Create unlock request with justification
2. Specify which invariant(s) will be affected
3. Provide migration plan if boundaries change
4. Run BLCA after changes
5. Update this lock document
6. Re-lock domain

---

## Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| HOC Layer Topology | `docs/architecture/HOC_LAYER_TOPOLOGY_V1.md` | Canonical layer rules |
| Implementation Plan | `docs/architecture/hoc/implementation/OVERVIEW_PHASE2.5_IMPLEMENTATION_PLAN.md` | Phase 2.5B execution |
| Customer Domain Audit | `backend/app/houseofcards/customer/HOC_CUSTOMER_DOMAIN_AUDIT_2026-01-24.md` | Domain selection rationale |
| HOC Index | `docs/architecture/hoc/INDEX.md` | Master documentation index |

---

## Audit Trail

| Date | Version | Action | Author |
|------|---------|--------|--------|
| 2026-01-24 | 0.1.0 | Domain selected as next Phase 2.5B candidate | Claude |
| 2026-01-24 | 0.2.0 | Implementation plan created | Claude |
| 2026-01-24 | 1.0.0 | **DOMAIN LOCKED** — Extraction complete, 0 violations | Claude |

---

**DOMAIN STATUS: LOCKED**

**Lock Signature:** `OVERVIEW-LOCK-2026-01-24-V1.0.0`

**END OF LOCK DOCUMENT**
