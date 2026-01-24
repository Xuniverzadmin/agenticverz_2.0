# Overview Domain — Phase 2.5B Implementation Plan
# Status: COMPLETE → LOCKED
# Date: 2026-01-24
# Lock Date: 2026-01-24
# Lock Document: OVERVIEW_DOMAIN_LOCK_FINAL.md
# Reference: HOC_LAYER_TOPOLOGY_V1.md, HOC_CUSTOMER_DOMAIN_AUDIT_2026-01-24.md

---

## Core Axiom

> **Overview is a READ-ONLY aggregation domain — it queries, never writes.**

Consequences:
1. L4 may **compose** results from multiple queries
2. L6 may only **fetch and aggregate** data
3. Facades must never touch persistence directly
4. Call flow: **Facade → Driver** (no engine needed for pure reads)

---

## Violation Summary

| # | File | Violation | Severity | Category |
|---|------|-----------|----------|----------|
| 1 | `facades/overview_facade.py` | `from sqlalchemy import and_, case, func, select` | CRITICAL | SQLALCHEMY_RUNTIME |
| 2 | `facades/overview_facade.py` | `from sqlalchemy.ext.asyncio import AsyncSession` | CRITICAL | SQLALCHEMY_RUNTIME |
| 3 | `facades/overview_facade.py` | `from app.models.audit_ledger import AuditLedger` | HIGH | LAYER_BOUNDARY (L4→L7) |
| 4 | `facades/overview_facade.py` | `from app.models.killswitch import Incident, IncidentLifecycleState` | HIGH | LAYER_BOUNDARY (L4→L7) |
| 5 | `facades/overview_facade.py` | `from app.models.policy import PolicyProposal` | HIGH | LAYER_BOUNDARY (L4→L7) |
| 6 | `facades/overview_facade.py` | `from app.models.policy_control_plane import Limit, LimitBreach, LimitCategory` | HIGH | LAYER_BOUNDARY (L4→L7) |
| 7 | `facades/overview_facade.py` | `from app.models.tenant import WorkerRun` | HIGH | LAYER_BOUNDARY (L4→L7) |

**Total:** 7 violations (2 SQLALCHEMY_RUNTIME + 5 LAYER_BOUNDARY)

---

## Phase I — Boundary Repair (Single Phase)

### I.1 — overview_facade.py Extraction

**Current State:**
- File declares L4 (facades/)
- Contains direct sqlalchemy imports at runtime (lines 46-47)
- Contains direct model imports (lines 52-56)
- 5 methods with direct DB access

**Target State:**
- Facade becomes orchestration-only
- All DB access moves to driver
- Call flow: Facade → Driver

**Extraction Plan:**

```
BEFORE:
  overview_facade.py (L4) — contains DB queries

AFTER:
  overview_facade.py (L4) — orchestration only
      ↓ delegates to
  overview_facade_driver.py (L6) — pure DB access
```

**Files to Create:**
1. `drivers/overview_facade_driver.py` — L6 pure data access

---

## Function Extraction Matrix

| Facade Function | Lines | Driver Function | Return Type |
|-----------------|-------|-----------------|-------------|
| `get_highlights()` | 270-389 | `fetch_incident_counts()` | `IncidentCountSnapshot` |
| `get_highlights()` | 270-389 | `fetch_proposal_counts()` | `ProposalCountSnapshot` |
| `get_highlights()` | 270-389 | `fetch_breach_counts()` | `BreachCountSnapshot` |
| `get_highlights()` | 270-389 | `fetch_run_counts()` | `RunCountSnapshot` |
| `get_highlights()` | 270-389 | `fetch_audit_counts()` | `AuditCountSnapshot` |
| `get_decisions()` | 390-496 | `fetch_pending_proposals()` | `list[ProposalSnapshot]` |
| `get_decisions()` | 390-496 | `fetch_pending_incidents()` | `list[IncidentSnapshot]` |
| `get_costs()` | 497-584 | `fetch_limits_with_breaches()` | `list[LimitSnapshot]` |
| `get_costs()` | 497-584 | `fetch_run_costs()` | `RunCostSnapshot` |
| `get_decisions_count()` | 585-638 | `fetch_decisions_count()` | `DecisionsCountSnapshot` |
| `get_recovery_stats()` | 639-693 | `fetch_recovery_incidents()` | `RecoverySnapshot` |

---

## Snapshot Dataclasses (Driver Output)

```python
@dataclass
class IncidentCountSnapshot:
    total: int
    active: int
    resolved_today: int
    by_severity: dict[str, int]

@dataclass
class ProposalCountSnapshot:
    total: int
    pending: int
    approved_today: int
    rejected_today: int

@dataclass
class BreachCountSnapshot:
    total: int
    active: int
    resolved_today: int

@dataclass
class RunCountSnapshot:
    total: int
    running: int
    completed_today: int
    failed_today: int

@dataclass
class AuditCountSnapshot:
    total_today: int
    by_action: dict[str, int]

@dataclass
class ProposalSnapshot:
    id: str
    name: str
    status: str
    created_at: datetime
    policy_type: str

@dataclass
class IncidentSnapshot:
    id: str
    title: str
    severity: str
    status: str
    created_at: datetime

@dataclass
class LimitSnapshot:
    id: str
    name: str
    category: str
    current_value: float
    limit_value: float
    breach_count: int

@dataclass
class RunCostSnapshot:
    total_cost: float
    cost_today: float
    runs_today: int

@dataclass
class DecisionsCountSnapshot:
    pending_proposals: int
    pending_incidents: int
    total_pending: int

@dataclass
class RecoverySnapshot:
    total_recovered: int
    avg_recovery_time_hours: float
    recovered_today: int
```

---

## Facade Transformation

### Before (overview_facade.py):

```python
# Layer: L4 — Domain Services
from sqlalchemy import and_, case, func, select          # ❌ FORBIDDEN
from sqlalchemy.ext.asyncio import AsyncSession          # ❌ FORBIDDEN
from app.models.audit_ledger import AuditLedger          # ❌ LAYER_BOUNDARY
from app.models.killswitch import Incident, ...          # ❌ LAYER_BOUNDARY
...

class OverviewFacade:
    async def get_highlights(self, session: AsyncSession, tenant_id: str):
        # Direct DB queries here
        result = await session.execute(select(Incident).where(...))
```

### After (overview_facade.py):

```python
# Layer: L4 — Domain Services
# Role: Overview aggregation facade - orchestration only
#
# PHASE 2.5B EXTRACTION (2026-01-24):
# All DB operations extracted to overview_facade_driver.py (L6)
# This facade now delegates to driver for data access

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.hoc.cus.overview.L6_drivers.overview_facade_driver import (
    OverviewFacadeDriver,
)

class OverviewFacade:
    def __init__(self):
        self._driver = OverviewFacadeDriver()

    async def get_highlights(self, session: AsyncSession, tenant_id: str):
        # Delegate to driver, compose results
        incidents = await self._driver.fetch_incident_counts(session, tenant_id)
        proposals = await self._driver.fetch_proposal_counts(session, tenant_id)
        breaches = await self._driver.fetch_breach_counts(session, tenant_id)
        runs = await self._driver.fetch_run_counts(session, tenant_id)
        audits = await self._driver.fetch_audit_counts(session, tenant_id)

        return self._compose_highlights(incidents, proposals, breaches, runs, audits)
```

---

## Execution Checklist

### Phase I Execution

- [x] **I.1.1** Create `drivers/overview_facade_driver.py` with snapshot dataclasses ✅ 2026-01-24
- [x] **I.1.2** Implement driver fetch methods (DB queries) ✅ 2026-01-24
- [x] **I.1.3** Update facade to use TYPE_CHECKING pattern ✅ 2026-01-24
- [x] **I.1.4** Update facade to delegate to driver ✅ 2026-01-24
- [x] **I.1.5** Run BLCA verification — 0 violations ✅ 2026-01-24
- [x] **I.1.6** Create OVERVIEW_DOMAIN_LOCK_FINAL.md ✅ 2026-01-24

---

## Transitional Debt Policy

**Decision:** ❌ NO transitional debt approved

Rationale:
- Overview is smallest domain (6 files, 1 with violations)
- Prior domains achieved zero debt
- Clean extraction is achievable in single phase

---

## Governance Invariants

| ID | Rule | Enforcement |
|----|------|-------------|
| **INV-OVW-001** | L4 cannot import sqlalchemy at runtime | BLOCKING |
| **INV-OVW-002** | L4 cannot import from L7 models directly | BLOCKING |
| **INV-OVW-003** | Facades delegate, never query directly | BLOCKING |
| **INV-OVW-004** | Call flow: Facade → Driver | BLOCKING |
| **INV-OVW-005** | Driver returns snapshots, not ORM models | BLOCKING |

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-24 | 1.0.0 | Initial plan created |
| 2026-01-24 | 2.0.0 | **DOMAIN LOCKED** — See OVERVIEW_DOMAIN_LOCK_FINAL.md |

---

**STATUS: COMPLETE → LOCKED**

**Lock Signature:** `OVERVIEW-LOCK-2026-01-24-V1.0.0`

**END OF IMPLEMENTATION PLAN**
