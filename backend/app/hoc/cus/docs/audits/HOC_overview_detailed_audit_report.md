# HOC Overview Domain Audit Report

**Date:** 2026-01-23
**Domain:** `app/houseofcards/customer/overview/`
**Scope:** Internal domain audit (duplicates, imports, semantics)
**Reference:** INT-OVERVIEW-AUDIT-001

---

## Executive Summary

| Metric | Count | Severity |
|--------|-------|----------|
| Files Audited | 6 | - |
| **Near-Duplicate** | 1 | LOW (intentional) |
| **Deprecated API Usage** | 0 | ~~RESOLVED~~ |
| Import Issues | 0 | - |
| Structural Issues | 0 | - |

**Overall Health:** EXCELLENT - All issues resolved

---

## 1. File Inventory

### 1.1 Overview Domain Structure

```
app/houseofcards/customer/overview/
├── __init__.py (47 lines - domain contract)
├── facades/
│   ├── __init__.py (placeholder)
│   └── overview_facade.py (715 lines) ← MAIN IMPLEMENTATION
├── drivers/
│   └── __init__.py (placeholder)
├── engines/
│   └── __init__.py (placeholder)
└── schemas/
    └── __init__.py (placeholder)
```

**Total LOC:** ~715 lines (single facade)

### 1.2 Domain Contract (INV-OVW-001 to INV-OVW-004)

The domain has a well-defined constitutional contract in `__init__.py`:

| Invariant | Description |
|-----------|-------------|
| INV-OVW-001 | Overview DOES NOT own any tables |
| INV-OVW-002 | Overview NEVER triggers side-effects |
| INV-OVW-003 | All mutations route to owning domains |
| INV-OVW-004 | No business rules — composition only |

**Status:** Compliant - domain is projection-only

---

## 2. Duplicate Analysis

### 2.1 overview_facade.py - Near-Duplicate

| Location | Lines | Status |
|----------|-------|--------|
| `app/services/overview_facade.py` | 721 | LEGACY |
| `app/houseofcards/customer/overview/facades/overview_facade.py` | 715 | HOC |

**Difference:** Header metadata only (6 lines)

| Attribute | Legacy | HOC |
|-----------|--------|-----|
| Layer | L4 — Domain Engine | L4 — Domain Services |
| Product | ai-console (Customer Console) | (not specified) |
| Temporal | api/async | (not specified) |
| Reference | PIN-413 | DIRECTORY_REORGANIZATION_PLAN.md |
| Import path | `app.services.overview_facade` | `app.houseofcards.customer.overview.facades.overview_facade` |
| Logger | `nova.services.overview_facade` | `nova.houseofcards.customer.overview.facades` |

**Verdict:** INTENTIONAL duplicate (acknowledged per account audit pattern)

---

## 3. ~~RESOLVED~~: datetime.utcnow() Usage Fixed

### 3.1 Resolution Applied (2026-01-23)

**Status:** FIXED

All 3 occurrences of deprecated `datetime.utcnow()` have been replaced with the shared utility:

| File | Line | Old | New |
|------|------|-----|-----|
| `overview_facade.py` | ~278 | `datetime.utcnow()` | `utc_now()` |
| `overview_facade.py` | ~506 | `datetime.utcnow()` | `utc_now()` |
| `overview_facade.py` | ~648 | `datetime.utcnow()` | `utc_now()` |

**Fix Applied:**
```python
from app.houseofcards.customer.general.utils.time import utc_now
now = utc_now()  # Returns timezone-aware datetime.now(timezone.utc)
```

---

## 4. Import Analysis

### 4.1 Current Imports (overview_facade.py)

```python
# Standard library
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# SQLAlchemy
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# L6 model imports (allowed for L4)
from app.models.audit_ledger import AuditLedger
from app.models.killswitch import Incident, IncidentLifecycleState
from app.models.policy import PolicyProposal
from app.models.policy_control_plane import Limit, LimitBreach, LimitCategory
from app.models.tenant import WorkerRun
```

**Status:** CORRECT - All imports are from L6 (models), compliant with L4 rules

### 4.2 No Cross-Domain HOC Imports

The overview facade correctly imports from `app.models.*` (L6) and does NOT import from other HOC domains, maintaining proper isolation.

---

## 5. Semantic Analysis

### 5.1 Layer Compliance

| File | Declared Layer | Actual | Status |
|------|----------------|--------|--------|
| `__init__.py` | L4 Domain Services | Domain contract | Correct |
| `facades/__init__.py` | L4 Domain Services | Placeholder | Correct |
| `facades/overview_facade.py` | L4 Domain Services | Aggregation logic | Correct |
| `drivers/__init__.py` | L4 Domain Services | Placeholder | Correct |
| `engines/__init__.py` | L4 Domain Services | Placeholder | Correct |
| `schemas/__init__.py` | L4 Domain Services | Placeholder | Correct |

### 5.2 Architectural Compliance

| Rule | Status |
|------|--------|
| No table ownership | ✅ Compliant |
| No side-effects | ✅ Compliant |
| Read-only operations | ✅ Compliant |
| Projection-only | ✅ Compliant |

### 5.3 Dataclasses Defined

| Class | Purpose | Lines |
|-------|---------|-------|
| `SystemPulse` | System health pulse summary | 64-82 |
| `DomainCount` | Count for a specific domain | 85-99 |
| `HighlightsResult` | Result from get_highlights | 102-114 |
| `DecisionItem` | A pending decision item | 117-137 |
| `DecisionsResult` | Result from get_decisions | 140-154 |
| `CostPeriod` | Time period for cost calculation | 157-167 |
| `LimitCostItem` | Single limit with cost status | 170-190 |
| `CostsResult` | Result from get_costs | 193-213 |
| `DecisionsCountResult` | Result from get_decisions_count | 216-228 |
| `RecoveryStatsResult` | Result from get_recovery_stats | 231-249 |

### 5.4 Facade Methods

| Method | Purpose | API Route |
|--------|---------|-----------|
| `get_highlights()` | O1 system pulse & domain counts | GET /api/v1/overview/highlights |
| `get_decisions()` | O2 pending decisions queue | GET /api/v1/overview/decisions |
| `get_costs()` | O2 cost intelligence summary | GET /api/v1/overview/costs |
| `get_decisions_count()` | O2 decisions count summary | GET /api/v1/overview/decisions/count |
| `get_recovery_stats()` | O3 recovery statistics | GET /api/v1/overview/recovery-stats |

---

## 6. Recommendations

### 6.1 ~~Replace datetime.utcnow()~~ (COMPLETED)

**Status:** FIXED (2026-01-23)

All occurrences replaced with shared utility `app.houseofcards.customer.general.utils.time.utc_now`

### 6.2 Legacy Duplicate (LOW - Optional)

**Status:** INTENTIONAL - No action required

The legacy `app/services/overview_facade.py` is maintained for backward compatibility.

---

## 7. Audit Summary

| Category | Issues Found | Severity | Action |
|----------|--------------|----------|--------|
| File Duplicates | 1 | LOW | INTENTIONAL |
| Deprecated API | ~~3~~ 0 | ~~MEDIUM~~ | ~~FIXED~~ |
| Import Issues | 0 | - | None |
| Layer Violations | 0 | - | None |
| Semantic Issues | 0 | - | None |

**Domain Health:** EXCELLENT - Well-structured projection-only domain, all issues resolved

---

## 8. Domain Architecture Notes

The Overview domain is exemplary in its design:

1. **Clear Contract:** INV-OVW-001 to INV-OVW-004 define boundaries
2. **Single Facade:** One file handles all aggregation logic
3. **No State Ownership:** Correctly projects from other domains
4. **Clean Separation:** Reads from Activity, Incidents, Policies via models
5. **Proper Layer Compliance:** L4 facade importing only from L6 models

---

**Report Generated:** 2026-01-23
**Auditor:** Claude (Automated HOC Audit)
**Status:** COMPLETE
