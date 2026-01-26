# API Keys Domain — Phase 2.5B Analysis Report
# Status: ANALYSIS COMPLETE
# Date: 2026-01-24
# Scanner: layer_validator.py (HOC Layer Topology V1)
# Reference: HOC_LAYER_TOPOLOGY_V1.md, HOC_CUSTOMER_DOMAIN_AUDIT_2026-01-24.md

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Files** | 8 |
| **Files with Violations** | 2 |
| **Total Violations** | 8 |
| **Complexity** | MEDIUM-LOW |
| **Recommendation** | PROCEED with Phase 2.5B extraction |

### Violation Breakdown

| Category | Count | Severity | Files Affected |
|----------|-------|----------|----------------|
| SQLALCHEMY_RUNTIME | 4 | CRITICAL | api_keys_facade.py (2), keys_service.py (2) |
| LAYER_BOUNDARY | 3 | HIGH | api_keys_facade.py (1), keys_service.py (2) |
| BANNED_NAMING | 1 | MEDIUM | keys_service.py |
| **TOTAL** | **8** | — | — |

---

## File Inventory

```
api_keys/
├── __init__.py                          ✅ NO VIOLATIONS
├── drivers/
│   └── __init__.py                      ✅ NO VIOLATIONS (empty)
├── engines/
│   ├── __init__.py                      ✅ NO VIOLATIONS
│   ├── email_verification.py            ✅ NO VIOLATIONS (L3 Redis-only)
│   └── keys_service.py                  ❌ 5 VIOLATIONS
├── facades/
│   ├── __init__.py                      ✅ NO VIOLATIONS
│   └── api_keys_facade.py               ❌ 3 VIOLATIONS
└── schemas/
    └── __init__.py                      ✅ NO VIOLATIONS (empty)
```

---

## File-by-File Analysis

### 1. facades/api_keys_facade.py

**Declared Layer:** L4 — Domain Engine (line 1)
**Location:** `facades/` (correct for L4)
**AUDIENCE:** CUSTOMER
**Lines:** 238

#### Violations (3 total)

| # | Line | Category | Violation | Import |
|---|------|----------|-----------|--------|
| 1 | 33 | SQLALCHEMY_RUNTIME | L4 cannot import sqlalchemy at runtime | `from sqlalchemy import func, select` |
| 2 | 34 | SQLALCHEMY_RUNTIME | L4 cannot import sqlalchemy at runtime | `from sqlalchemy.ext.asyncio import AsyncSession` |
| 3 | 36 | LAYER_BOUNDARY | L4→L7 direct model import | `from app.models.tenant import APIKey` |

#### Evidence — Lines 33-36

```python
from sqlalchemy import func, select                    # ❌ SQLALCHEMY_RUNTIME
from sqlalchemy.ext.asyncio import AsyncSession        # ❌ SQLALCHEMY_RUNTIME

from app.models.tenant import APIKey                   # ❌ LAYER_BOUNDARY (L4→L7)
```

#### Functions with Direct DB Access

| Function | Lines | DB Pattern | Queries |
|----------|-------|------------|---------|
| `list_api_keys()` | 108-168 | `select(APIKey)`, `func.count()` | 2 queries |
| `get_api_key_detail()` | 170-211 | `select(APIKey)` | 1 query |

#### Analysis

- **Facade Role:** Read-only projection of API keys for customer console
- **Caller:** L2 API routes (`aos_api_key.py`)
- **Pattern Match:** Same as `overview_facade.py` — L4 with direct DB access
- **Fix Pattern:** Extract DB operations to `api_keys_facade_driver.py` (L6)

---

### 2. engines/keys_service.py

**Declared Layer:** L4 — Domain Engine (line 1)
**Location:** `engines/` (correct for L4)
**AUDIENCE:** Not declared (system-wide product scope)
**Lines:** 218

#### Violations (5 total)

| # | Line | Category | Violation | Import/Issue |
|---|------|----------|-----------|--------------|
| 1 | 1 | BANNED_NAMING | Filename `keys_service.py` banned | Must be `*_engine.py` or `*_driver.py` |
| 2 | 42 | SQLALCHEMY_RUNTIME | L4 cannot import sqlalchemy at runtime | `from sqlalchemy import and_, desc, func, select` |
| 3 | 43 | SQLALCHEMY_RUNTIME | L4 cannot import sqlmodel at runtime | `from sqlmodel import Session` |
| 4 | 46 | LAYER_BOUNDARY | L4→L7 direct model import | `from app.models.killswitch import ProxyCall` |
| 5 | 47 | LAYER_BOUNDARY | L4→L7 direct model import | `from app.models.tenant import APIKey` |

#### Evidence — Lines 42-47

```python
from sqlalchemy import and_, desc, func, select        # ❌ SQLALCHEMY_RUNTIME
from sqlmodel import Session                           # ❌ SQLALCHEMY_RUNTIME

# L6 imports (allowed)  <-- COMMENT IS INCORRECT, these are L7
from app.models.killswitch import ProxyCall            # ❌ LAYER_BOUNDARY (L4→L7)
from app.models.tenant import APIKey                   # ❌ LAYER_BOUNDARY (L4→L7)
```

#### Classes and Functions with DB Access

**Class: KeysReadService (L4 READ operations)**

| Method | Lines | DB Pattern | Queries |
|--------|-------|------------|---------|
| `list_keys()` | 61-94 | `select(APIKey)`, `func.count()` | 2 queries |
| `get_key()` | 96-118 | `select(APIKey)` | 1 query |
| `get_key_usage_today()` | 120-147 | `select(func.count(ProxyCall))` | 1 query |

**Class: KeysWriteService (L4 WRITE operations)**

| Method | Lines | DB Pattern | Mutations |
|--------|-------|------------|-----------|
| `freeze_key()` | 161-179 | `session.add()`, `session.commit()` | UPDATE |
| `unfreeze_key()` | 181-199 | `session.add()`, `session.commit()` | UPDATE |

#### Analysis

- **Dual Role:** Contains both READ and WRITE services
- **Caller:** L3 adapters, runtime, gateway (NOT L2 — documented)
- **Sync Session:** Uses `sqlmodel.Session` (sync, not async)
- **Naming Violation:** Must rename to `keys_engine.py`
- **Fix Pattern:**
  - Rename to `keys_engine.py`
  - Extract DB operations to `keys_driver.py` (L6)
  - Engine retains business logic (if any)

---

### 3. engines/email_verification.py

**Declared Layer:** L3 — Boundary Adapter (line 1)
**Location:** `engines/` (MISMATCH — should be in adapters/)
**AUDIENCE:** Not declared
**Lines:** 286

#### Violations (0 total)

No BLCA violations because:
- Uses Redis only (not PostgreSQL)
- No sqlalchemy/sqlmodel imports
- No L7 model imports

#### Evidence — Lines 1-5

```python
# Layer: L3 — Boundary Adapter (Console → Platform)
# Product: AI Console
# Callers: onboarding.py (auth flow)
# Reference: PIN-240
# NOTE: Redis-only state (not PostgreSQL). M24 onboarding.
```

#### Analysis

- **Actual Role:** Email OTP verification for onboarding
- **State Storage:** Redis (not PostgreSQL)
- **Layer Mismatch:** Declared L3 but located in `engines/` directory
- **No Phase 2.5B Work:** This file has no DB violations
- **Recommendation:** Relocate to `adapters/` or reclassify header to L4
  - If it's truly L3 (adapter), move to `api_keys/adapters/email_verification.py`
  - If it's L4 (engine), update header

---

### 4. __init__.py Files

All `__init__.py` files have no violations:

| File | Layer | Notes |
|------|-------|-------|
| `api_keys/__init__.py` | L4 | Domain contract documentation |
| `drivers/__init__.py` | L4 | Empty, awaiting drivers |
| `engines/__init__.py` | L4 | Empty exports |
| `facades/__init__.py` | L4 | Empty exports |
| `schemas/__init__.py` | L4 | Empty |

**Note:** `drivers/__init__.py` declares L4 but should declare L6 when drivers are added.

---

## Required Fixes

### Phase I — Critical Violations (SQLALCHEMY_RUNTIME + LAYER_BOUNDARY)

#### I.1 — api_keys_facade.py Extraction

**Current State:**
- L4 facade with sqlalchemy runtime imports (lines 33-34)
- L4 facade with direct L7 model import (line 36)
- 2 methods with direct DB access

**Target State:**
- Facade (L4): orchestration only, TYPE_CHECKING for type hints
- Driver (L6): all DB queries

**Files to Create:**
1. `drivers/api_keys_facade_driver.py` — L6 pure data access

**Extraction Plan:**

| Facade Function | Driver Function | Returns |
|-----------------|-----------------|---------|
| `list_api_keys()` | `fetch_api_keys()` | `list[APIKeySnapshot]` |
| `list_api_keys()` | `fetch_api_keys_count()` | `int` |
| `get_api_key_detail()` | `fetch_api_key_by_id()` | `Optional[APIKeyDetailSnapshot]` |

---

#### I.2 — keys_service.py Extraction

**Current State:**
- L4 engine with sqlalchemy/sqlmodel runtime imports (lines 42-43)
- L4 engine with direct L7 model imports (lines 46-47)
- 2 read classes + write class with direct DB access

**Target State:**
- Engine (L4): business logic only (if any), TYPE_CHECKING for type hints
- Driver (L6): all DB queries and mutations

**Files to Create:**
1. `drivers/keys_driver.py` — L6 pure data access

**Extraction Plan:**

| Engine Method | Driver Function | Returns |
|---------------|-----------------|---------|
| `KeysReadService.list_keys()` | `fetch_keys()` | `list[APIKeySnapshot]` |
| `KeysReadService.list_keys()` | `count_keys()` | `int` |
| `KeysReadService.get_key()` | `fetch_key_by_id()` | `Optional[APIKeySnapshot]` |
| `KeysReadService.get_key_usage_today()` | `fetch_key_usage()` | `KeyUsageSnapshot` |
| `KeysWriteService.freeze_key()` | `update_key_frozen()` | `APIKeySnapshot` |
| `KeysWriteService.unfreeze_key()` | `update_key_unfrozen()` | `APIKeySnapshot` |

---

### Phase II — Naming Violation

#### II.1 — keys_service.py Rename

**Current Name:** `engines/keys_service.py`
**Target Name:** `engines/keys_engine.py`

**Risk:** HIGH — requires updating all callers

**Callers to Update:**
- L3 adapters (customer_keys_adapter.py)
- Runtime/gateway imports
- Domain `__init__.py` exports

**Decision Required:**
- Option A: Rename now (requires caller graph analysis)
- Option B: Defer to Phase 3.0 (naming normalization phase)

**Recommendation:** Option B — Defer. Focus on critical violations first.

---

### Phase III — Intent Resolution

#### III.1 — email_verification.py Classification

**Current State:**
- Declared L3 (Boundary Adapter)
- Located in `engines/` directory
- Redis-only (no PostgreSQL)

**Decision Required:**
> Is this file truly an adapter (L3), or should it be reclassified as an engine (L4)?

**Options:**

| Option | Classification | Action |
|--------|---------------|--------|
| A | L3 Adapter | Move to `adapters/email_verification.py` |
| B | L4 Engine | Update header to L4, keep in `engines/` |

**Analysis:**
- The file translates between console auth flow and external email service (Resend)
- This is adapter behavior (boundary translation)
- However, it contains business logic (OTP generation, cooldown, rate limiting)

**Recommendation:** Option B — Reclassify as L4 engine. The OTP logic is business logic, not pure translation.

---

## Snapshot Dataclasses (Proposed)

### For api_keys_facade_driver.py

```python
@dataclass
class APIKeySnapshot:
    """Raw API key data from DB."""
    id: str
    name: str
    key_prefix: str
    status: str
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    total_requests: int
    is_synthetic: bool

@dataclass
class APIKeyDetailSnapshot:
    """Detailed API key data from DB."""
    id: str
    name: str
    key_prefix: str
    status: str
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    total_requests: int
    permissions_json: Optional[str]
    allowed_workers_json: Optional[str]
    rate_limit_rpm: Optional[int]
    max_concurrent_runs: Optional[int]
    revoked_at: Optional[datetime]
    revoked_reason: Optional[str]
```

### For keys_driver.py

```python
@dataclass
class KeyUsageSnapshot:
    """Key usage statistics from DB."""
    request_count: int
    spend_cents: int
```

---

## Governance Invariants

| ID | Rule | Enforcement |
|----|------|-------------|
| **INV-KEY-001** | L4 cannot import sqlalchemy at runtime | BLOCKING |
| **INV-KEY-002** | L4 cannot import from L7 models directly | BLOCKING |
| **INV-KEY-003** | Facades delegate, never query directly | BLOCKING |
| **INV-KEY-004** | `*_service.py` naming is BANNED | MEDIUM (defer to Phase 3) |
| **INV-KEY-005** | Driver returns snapshots, not ORM models | BLOCKING |

---

## Implementation Order

| Priority | Task | Files | Violations Fixed |
|----------|------|-------|------------------|
| 1 | Extract api_keys_facade.py | Create driver, update facade | 3 |
| 2 | Extract keys_service.py | Create driver, update engine | 4 |
| 3 | Reclassify email_verification.py | Update header | 0 (layer mismatch) |
| 4 | Rename keys_service.py | Rename + update callers | 1 |

**Recommended Approach:**
- Priority 1-2: Phase 2.5B (critical violations)
- Priority 3-4: Phase 3.0 (naming/classification)

---

## Audit Trail

| Date | Action | Result |
|------|--------|--------|
| 2026-01-24 | BLCA scan | 8 violations found |
| 2026-01-24 | File inventory | 8 files catalogued |
| 2026-01-24 | Evidence collection | All violations documented |
| 2026-01-24 | Analysis complete | Ready for Phase 2.5B |

---

**ANALYSIS COMPLETE**

**Recommendation:** Proceed with Phase 2.5B extraction for `api_keys_facade.py` and `keys_service.py`.

**END OF ANALYSIS REPORT**
