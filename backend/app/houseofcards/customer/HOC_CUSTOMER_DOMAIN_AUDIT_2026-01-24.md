# HOC Customer Domain Audit Report
# Status: COMPLETE
# Date: 2026-01-24
# Scanner: layer_validator.py (HOC Layer Topology V1)
# Purpose: Identify next Phase 2.5B domain candidate

---

## Executive Summary

| Domain | Files | Violations | Complexity | Status | Recommendation |
|--------|-------|------------|------------|--------|----------------|
| analytics | 22 | 0 | - | LOCKED | - |
| policies | 41 | 0 | - | LOCKED | - |
| activity | 29 | 0 | - | LOCKED | - |
| logs | 56 | 0 | - | LOCKED | - |
| incidents | 48 | 37 | - | LOCKED | - |
| **overview** | **6** | **7** | **LOW** | PENDING | **NEXT CANDIDATE** |
| api_keys | 8 | 8 | MEDIUM-LOW | PENDING | Second priority |
| account | 18 | 15 | MEDIUM | PENDING | Third priority |
| integrations | 63 | 55 | HIGH | PENDING | Defer |
| general | 66 | 63 | HIGHEST | PENDING | Defer |

---

## Recommendation: overview Domain

**Rationale:**
1. Smallest file count (6 files)
2. Lowest violation count (7)
3. Single point of failure (`overview_facade.py`)
4. Clear extraction pattern (identical to incidents_facade.py)
5. Domain is READ-ONLY (no writes) — simplest to extract

---

## Domain 1: overview

### File Inventory (6 files)

```
overview/
├── __init__.py
├── drivers/
│   └── __init__.py
├── engines/
│   └── __init__.py
├── facades/
│   ├── __init__.py
│   └── overview_facade.py    ❌ 7 VIOLATIONS
└── schemas/
    └── __init__.py
```

### Violations (7 total)

| Category | Count | Files Affected |
|----------|-------|----------------|
| SQLALCHEMY_RUNTIME | 2 | overview_facade.py |
| LAYER_BOUNDARY | 5 | overview_facade.py |

### Evidence — overview_facade.py

**File:** `facades/overview_facade.py`
**Declared Layer:** L4 — Domain Services (line 1)
**Location:** `facades/` (correct for L4)

**Violation 1-2: SQLALCHEMY_RUNTIME (lines 46-47)**
```python
from sqlalchemy import and_, case, func, select          # ❌ FORBIDDEN in L4
from sqlalchemy.ext.asyncio import AsyncSession          # ❌ FORBIDDEN in L4
```

**Violation 3-7: LAYER_BOUNDARY (lines 52-56)**
```python
from app.models.audit_ledger import AuditLedger                              # L4→L7 ❌
from app.models.killswitch import Incident, IncidentLifecycleState           # L4→L7 ❌
from app.models.policy import PolicyProposal                                 # L4→L7 ❌
from app.models.policy_control_plane import Limit, LimitBreach, LimitCategory # L4→L7 ❌
from app.models.tenant import WorkerRun                                      # L4→L7 ❌
```

**Functions with Direct DB Access:**

| Function | Lines | DB Pattern |
|----------|-------|------------|
| `get_highlights()` | 270-389 | `select(Incident)`, `select(PolicyProposal)`, `select(LimitBreach)`, `select(WorkerRun)` |
| `get_decisions()` | 390-496 | `select(PolicyProposal)`, `select(Incident)` |
| `get_costs()` | 497-584 | `select(Limit)`, `select(LimitBreach)` |
| `get_decisions_count()` | 585-638 | `select(PolicyProposal)`, `select(Incident)` |
| `get_recovery_stats()` | 639-693 | `select(Incident)` |

### Required Fix Pattern

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

**Extraction Plan:**

| Facade Function | Driver Function | Returns |
|-----------------|-----------------|---------|
| `get_highlights()` | `fetch_incident_counts()` | IncidentCountSnapshot |
| `get_highlights()` | `fetch_proposal_counts()` | ProposalCountSnapshot |
| `get_highlights()` | `fetch_breach_counts()` | BreachCountSnapshot |
| `get_highlights()` | `fetch_run_counts()` | RunCountSnapshot |
| `get_decisions()` | `fetch_pending_proposals()` | list[ProposalSnapshot] |
| `get_decisions()` | `fetch_pending_incidents()` | list[IncidentSnapshot] |
| `get_costs()` | `fetch_limits()` | list[LimitSnapshot] |
| `get_costs()` | `fetch_breaches()` | list[BreachSnapshot] |
| `get_decisions_count()` | (reuse above) | — |
| `get_recovery_stats()` | `fetch_recovery_incidents()` | RecoverySnapshot |

---

## Domain 2: api_keys

### File Inventory (8 files)

```
api_keys/
├── __init__.py
├── drivers/
│   └── __init__.py
├── engines/
│   ├── __init__.py
│   ├── email_verification.py
│   └── keys_service.py       ❌ 4 VIOLATIONS + BANNED_NAMING
├── facades/
│   ├── __init__.py
│   └── api_keys_facade.py    ❌ 4 VIOLATIONS
└── schemas/
    └── __init__.py
```

### Violations (8 total)

| Category | Count | Files Affected |
|----------|-------|----------------|
| BANNED_NAMING | 1 | keys_service.py |
| SQLALCHEMY_RUNTIME | 4 | api_keys_facade.py (2), keys_service.py (2) |
| LAYER_BOUNDARY | 3 | api_keys_facade.py (1), keys_service.py (2) |

### Evidence — api_keys_facade.py

**File:** `facades/api_keys_facade.py`
**Declared Layer:** L4 — Domain Engine (line 1)

**SQLALCHEMY_RUNTIME (lines 33-34):**
```python
from sqlalchemy import func, select                      # ❌ FORBIDDEN in L4
from sqlalchemy.ext.asyncio import AsyncSession          # ❌ FORBIDDEN in L4
```

**LAYER_BOUNDARY (line 36):**
```python
from app.models.tenant import APIKey                     # L4→L7 ❌
```

**Functions with DB Access:**

| Function | Lines | DB Pattern |
|----------|-------|------------|
| `list_api_keys()` | 108-169 | `select(APIKey)` |
| `get_api_key_detail()` | 170-220 | `select(APIKey)` |

### Evidence — keys_service.py

**File:** `engines/keys_service.py`
**Declared Layer:** L4 — Domain Engine (line 1)
**Naming Violation:** `*_service.py` pattern is BANNED

**SQLALCHEMY_RUNTIME (lines 42-43):**
```python
from sqlalchemy import and_, desc, func, select          # ❌ FORBIDDEN in L4
from sqlmodel import Session                             # ❌ FORBIDDEN in L4
```

**LAYER_BOUNDARY (lines 46-47):**
```python
from app.models.killswitch import ProxyCall              # L4→L7 ❌
from app.models.tenant import APIKey                     # L4→L7 ❌
```

**Functions with DB Access:**

| Function | Lines | DB Pattern |
|----------|-------|------------|
| `list_keys()` | 61-95 | `select(APIKey)` |
| `get_key()` | 96-119 | `select(APIKey)` |
| `get_key_usage_today()` | 120-155 | `select(ProxyCall)` |
| `freeze_key()` | 161-180 | `session.add()` |
| `unfreeze_key()` | 181-201 | `session.add()` |

### Required Fix Pattern

1. Rename `keys_service.py` → `keys_engine.py`
2. Extract DB operations to `drivers/keys_driver.py`
3. Update facade to delegate to driver

---

## Domain 3: account

### File Inventory (18 files)

```
account/
├── __init__.py
├── drivers/
│   ├── __init__.py
│   ├── identity_resolver.py
│   ├── profile.py               ❌ LEGACY_IMPORT + LAYER_BOUNDARY
│   ├── tenant_service.py        ❌ BANNED_NAMING
│   ├── user_write_driver.py
│   └── worker_registry_service.py ❌ BANNED_NAMING
├── engines/
│   ├── __init__.py
│   ├── email_verification.py
│   └── user_write_service.py    ❌ BANNED_NAMING + LAYER_BOUNDARY
├── facades/
│   ├── __init__.py
│   ├── accounts_facade.py       ❌ SQLALCHEMY_RUNTIME + LAYER_BOUNDARY
│   └── notifications_facade.py  ❌ LEGACY_IMPORT
├── notifications/
│   └── engines/
│       └── channel_service.py   ❌ BANNED_NAMING
├── schemas/
│   └── __init__.py
└── support/
    └── CRM/
        └── engines/
            ├── audit_service.py     ❌ BANNED_NAMING
            ├── job_executor.py      ❌ LAYER_BOUNDARY
            └── validator_service.py ❌ BANNED_NAMING
```

### Violations (15 total)

| Category | Count | Files Affected |
|----------|-------|----------------|
| BANNED_NAMING | 6 | tenant_service, worker_registry_service, user_write_service, channel_service, audit_service, validator_service |
| LAYER_BOUNDARY | 5 | profile.py (1), identity_resolver.py (1), accounts_facade.py (1), user_write_service.py (1), job_executor.py (1) |
| LEGACY_IMPORT | 2 | profile.py (1), notifications_facade.py (1) |
| SQLALCHEMY_RUNTIME | 2 | accounts_facade.py |

### Key Violations

**accounts_facade.py (lines 34-37):**
```python
from sqlalchemy import func, select                      # ❌ SQLALCHEMY_RUNTIME
from sqlalchemy.ext.asyncio import AsyncSession          # ❌ SQLALCHEMY_RUNTIME
from app.models.tenant import (...)                      # ❌ LAYER_BOUNDARY
```

**profile.py (line 23):**
```python
from app.services.governance.profile import (...)        # ❌ LEGACY_IMPORT + L6→L4
```

### Complexity Assessment

- **Multiple subdirectories:** notifications/, support/CRM/
- **Mixed layer violations:** L6→L4, L6→L5, L4→L7
- **6 files need renaming**
- **Requires significant refactoring**

---

## Domain 4: integrations

### File Inventory (63 files)

```
integrations/
├── drivers/ (17 files)
│   ├── bridges.py               ❌ 21 SQLALCHEMY_RUNTIME violations
│   ├── cost_bridges.py          ❌ LEGACY_IMPORT
│   ├── execution.py             ❌ LAYER_BOUNDARY + LEGACY_IMPORT
│   └── ...
├── engines/ (10 files)
│   ├── cus_health_service.py    ❌ BANNED_NAMING + LAYER_BOUNDARY
│   ├── iam_service.py           ❌ BANNED_NAMING
│   └── ...
├── facades/ (25 files)
│   ├── customer_incidents_adapter.py  ❌ LEGACY_IMPORT
│   ├── customer_killswitch_adapter.py ❌ LAYER_BOUNDARY + LEGACY_IMPORT
│   ├── integrations_facade.py         ❌ LAYER_BOUNDARY + LEGACY_IMPORT
│   ├── retrieval_facade.py            ❌ LAYER_BOUNDARY + LEGACY_IMPORT
│   ├── connectors_facade.py           ❌ LAYER_BOUNDARY + LEGACY_IMPORT
│   └── ...
├── vault/
│   └── engines/
│       └── cus_credential_service.py  ❌ BANNED_NAMING
└── schemas/ (3 files)
```

### Violations (55 total)

| Category | Count | Notes |
|----------|-------|-------|
| BANNED_NAMING | 4 | Multiple *_service.py files |
| LAYER_BOUNDARY | 9 | Complex: L6→L4, L3→L7 |
| LEGACY_IMPORT | 21 | Heavy app.services dependency |
| SQLALCHEMY_RUNTIME | 21 | Mostly in bridges.py |

### Key Issue: bridges.py

This file has **21 sqlalchemy violations** — runtime imports throughout:
- Lines 139, 307, 417, 443, 563, 673, 819, 870, 1021, 1088, ...

**Assessment:** This domain requires extensive refactoring of legacy dependencies before L4/L6 extraction is feasible.

---

## Domain 5: general

### File Inventory (66 files)

```
general/
├── controls/
│   ├── drivers/
│   │   └── guard_write_driver.py
│   └── engines/
│       └── guard_write_service.py    ❌ BANNED_NAMING
├── cross-domain/
│   └── drivers/
│       └── cross_domain.py
├── drivers/ (23 files)
├── engines/ (7 files)
│   ├── cus_health_service.py         ❌ BANNED_NAMING + SQLALCHEMY + LEGACY
│   ├── knowledge_sdk.py              ❌ LAYER_BOUNDARY + LEGACY
│   └── ...
├── facades/ (5 files)
│   ├── alerts_facade.py              ❌ LAYER_BOUNDARY + LEGACY
│   ├── compliance_facade.py          ❌ LAYER_BOUNDARY + LEGACY
│   ├── lifecycle_facade.py           ❌ LAYER_BOUNDARY + LEGACY
│   ├── monitors_facade.py            ❌ LEGACY
│   └── scheduler_facade.py           ❌ LEGACY
├── lifecycle/
│   ├── drivers/
│   └── engines/
├── runtime/
│   ├── drivers/
│   ├── engines/
│   └── facades/
├── workflow/
│   └── contracts/
│       └── engines/
│           └── contract_service.py   ❌ BANNED_NAMING + LEGACY
├── ui/
│   └── engines/
├── utils/
└── schemas/ (6 files)
```

### Violations (63 total)

| Category | Count | Notes |
|----------|-------|-------|
| BANNED_NAMING | 3 | *_service.py files |
| LAYER_BOUNDARY | 22 | Complex multi-directional |
| LEGACY_IMPORT | 35 | Most in codebase |
| MISSING_HEADER | 2 (warnings) | __init__.py files |
| SQLALCHEMY_RUNTIME | 1 | cus_health_service.py |

### Complexity Assessment

- **Largest domain:** 66 files
- **Most legacy imports:** 35
- **Complex subdomain structure:** controls/, cross-domain/, lifecycle/, runtime/, workflow/, ui/
- **Requires major refactoring before L4/L6 work**

---

## Next Steps

### Recommended Action: Lock overview Domain

1. Create `OVERVIEW_DOMAIN_ANALYSIS_REPORT.md`
2. Create `OVERVIEW_PHASE2.5_IMPLEMENTATION_PLAN.md`
3. Extract DB operations from `overview_facade.py` to `overview_facade_driver.py`
4. Update facade to use TYPE_CHECKING pattern
5. Run BLCA verification
6. Create `OVERVIEW_DOMAIN_LOCK_FINAL.md`

### Estimated Effort

| Domain | Effort | Files to Create | Files to Modify |
|--------|--------|-----------------|-----------------|
| overview | LOW | 1 driver | 1 facade |
| api_keys | MEDIUM | 2 drivers | 2 files + rename |
| account | HIGH | 3+ drivers | 6+ files + renames |
| integrations | VERY HIGH | 5+ drivers | 20+ files |
| general | VERY HIGH | 10+ drivers | 30+ files |

---

## Governance Invariants Check

| Invariant | overview | api_keys | account | integrations | general |
|-----------|----------|----------|---------|--------------|---------|
| L4 no sqlalchemy runtime | ❌ 2 | ❌ 4 | ❌ 2 | ❌ 21 | ❌ 1 |
| L6 no business logic | ✅ | ✅ | ✅ | ✅ | ✅ |
| No banned naming | ✅ | ❌ 1 | ❌ 6 | ❌ 4 | ❌ 3 |
| No legacy imports | ✅ | ✅ | ❌ 2 | ❌ 21 | ❌ 35 |

---

## Audit Trail

| Date | Action | Result |
|------|--------|--------|
| 2026-01-24 | BLCA scan all remaining domains | 5 domains scanned |
| 2026-01-24 | File inventory complete | 161 files total |
| 2026-01-24 | Evidence-based violation analysis | 148 violations total |
| 2026-01-24 | Domain ranking complete | overview recommended |

---

**AUDIT COMPLETE**

**Recommendation:** Proceed with **overview** domain Phase 2.5B extraction.
