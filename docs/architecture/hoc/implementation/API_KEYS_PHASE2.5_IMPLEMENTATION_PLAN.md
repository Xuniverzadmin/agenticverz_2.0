# API Keys Domain — Phase 2.5B Implementation Plan
# Status: COMPLETE → LOCKED
# Date: 2026-01-24
# Completed: 2026-01-24
# Reference: HOC_LAYER_TOPOLOGY_V1.md, API_KEYS_DOMAIN_ANALYSIS_REPORT.md

---

## Core Axiom (LOCKED)

> **API Keys is an ACCESS-PRIMITIVE domain, not an identity or governance domain.**

Consequences:
1. L4 may decide **key validity, expiry, freeze status, scope match**
2. L4 must NEVER decide **tenant status, account suspension, rate limits, kill-switches**
3. L6 may only **persist, query, or aggregate key data**
4. Call flow: **Facade → Engine → Driver** (mandatory)

---

## Violation Summary

| # | File | Violation | Severity | Phase |
|---|------|-----------|----------|-------|
| 1 | `facades/api_keys_facade.py` | L4 with sqlalchemy runtime imports | CRITICAL | I |
| 2 | `facades/api_keys_facade.py` | L4→L7 model import | CRITICAL | I |
| 3 | `engines/keys_service.py` | L4 with sqlalchemy runtime imports | CRITICAL | I |
| 4 | `engines/keys_service.py` | L4→L7 model imports | CRITICAL | I |
| 5 | `engines/keys_service.py` | BANNED_NAMING (`*_service.py`) | MEDIUM | I |
| 6 | `engines/email_verification.py` | Layer/location mismatch | LOW | II |

---

## Phase I — Hard Violations (Boundary Repair)

### I.1 — api_keys_facade.py Extraction

**Current State:**
- File declares L4
- Contains sqlalchemy imports at runtime (lines 33-34)
- Contains L7 model import (line 36)
- 2 methods with direct DB access

**Target State:**
- Facade becomes orchestration-only
- All DB access moves to driver
- Call flow: Facade → Driver

**Extraction Plan:**

```
BEFORE:
  api_keys_facade.py (L4) — contains DB queries

AFTER:
  api_keys_facade.py (L4) — orchestration only
      ↓ delegates to
  api_keys_facade_driver.py (L6) — pure DB access
```

**Files to Create:**
1. `drivers/api_keys_facade_driver.py` — L6 pure data access

**Functions to Extract:**

| Facade Function | Driver Function | Returns |
|-----------------|-----------------|---------|
| `list_api_keys()` | `fetch_api_keys()` | `list[APIKeySnapshot]` |
| `list_api_keys()` | `count_api_keys()` | `int` |
| `get_api_key_detail()` | `fetch_api_key_by_id()` | `Optional[APIKeyDetailSnapshot]` |

**Facade Transformation:**
- Remove sqlalchemy imports
- Add TYPE_CHECKING block for type hints
- Inject driver as dependency
- Delegate all DB operations to driver

---

### I.2 — keys_service.py Split (Engine + Driver)

**Current State:**
- File declares L4 (engines/)
- Contains sqlalchemy/sqlmodel imports (lines 42-43)
- Contains L7 model imports (lines 46-47)
- Contains both READ and WRITE operations
- BANNED naming (`*_service.py`)

**Target State:**
- Engine (L4): validation logic, freeze/unfreeze decisions, scope checks
- Driver (L6): all SQL/ORM operations, snapshot DTOs

**Split Plan:**

```
BEFORE:
  keys_service.py (L4) — mixed: DB queries + business logic

AFTER:
  keys_engine.py (L4) — validation, decisions
      ↓ delegates to
  keys_driver.py (L6) — pure DB access
```

**Files to Create:**
1. `drivers/keys_driver.py` — L6 pure data access
2. `engines/keys_engine.py` — L4 business logic (replaces keys_service.py)

**Files to Delete:**
1. `engines/keys_service.py` — removed after split

**Extraction Plan:**

| Service Method | Layer | Destination |
|----------------|-------|-------------|
| `KeysReadService.list_keys()` | L6 | Driver: `fetch_keys()` |
| `KeysReadService.get_key()` | L6 | Driver: `fetch_key_by_id()` |
| `KeysReadService.get_key_usage_today()` | L6 | Driver: `fetch_key_usage()` |
| `KeysWriteService.freeze_key()` | L4+L6 | Engine: `freeze_key()` → Driver: `update_key_frozen()` |
| `KeysWriteService.unfreeze_key()` | L4+L6 | Engine: `unfreeze_key()` → Driver: `update_key_unfrozen()` |

**Business Logic in Engine (L4):**
- `freeze_key()`: Validate key state, then delegate persistence
- `unfreeze_key()`: Validate key state, then delegate persistence
- Future: Expiry checks, scope validation

---

## Phase II — Intent Resolution

### II.1 — email_verification.py Reclassification

**Current State:**
- Declares L3 (Boundary Adapter)
- Located in `engines/`
- Redis-only (no PostgreSQL)

**Analysis:**
- Contains domain-local verification logic
- OTP generation, cooldown, rate limiting = business logic
- NOT protocol adaptation (not L3)

**Decision:** Reclassify as L4

**After:**
```python
# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: Email OTP verification engine for customer onboarding
#
# RECLASSIFICATION NOTE (2026-01-24):
# This file was previously declared as L3 (Boundary Adapter).
# Reclassified to L4 because it contains domain-specific verification
# logic (OTP generation, cooldown, rate limiting). Redis-only state.
```

---

## Snapshot Dataclasses

### api_keys_facade_driver.py

```python
@dataclass
class APIKeySnapshot:
    """Raw API key data from DB for list view."""
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

### keys_driver.py

```python
@dataclass
class KeySnapshot:
    """API key snapshot for engine operations."""
    id: str
    tenant_id: str
    name: str
    key_prefix: str
    status: str
    is_frozen: bool
    frozen_at: Optional[datetime]
    created_at: datetime

@dataclass
class KeyUsageSnapshot:
    """Key usage statistics from DB."""
    request_count: int
    spend_cents: int
```

---

## Execution Checklist

### Phase I Execution

- [x] **I.1.1** Create `drivers/api_keys_facade_driver.py` with snapshot dataclasses
- [x] **I.1.2** Implement driver fetch methods (DB queries)
- [x] **I.1.3** Update facade to use TYPE_CHECKING pattern
- [x] **I.1.4** Update facade to delegate to driver
- [x] **I.1.5** Run BLCA verification — target: 0 violations for facade
- [x] **I.2.1** Create `drivers/keys_driver.py` with snapshot dataclasses
- [x] **I.2.2** Implement driver fetch/update methods (DB queries + mutations)
- [x] **I.2.3** Create `engines/keys_engine.py` with business logic
- [x] **I.2.4** Update engine to delegate to driver
- [x] **I.2.5** Delete `engines/keys_service.py`
- [x] **I.2.6** Run BLCA verification — target: 0 violations for engine

### Phase II Execution

- [x] **II.1.1** Reclassify email_verification.py header to L4
- [x] **II.1.2** Add reclassification note

### Post-Remediation

- [x] Run full BLCA scan — target: 0 violations ✅ CLEAN
- [x] Update drivers/__init__.py header to L6
- [x] Create API_KEYS_DOMAIN_LOCK_FINAL.md
- [x] Update HOC INDEX.md

---

## Transitional Debt Policy

**Decision:** ❌ NO transitional debt approved

Rationale:
- API Keys gates access — security-critical domain
- Any "temporary" shortcut becomes a security liability
- Prior domains achieved zero debt
- Zero-debt is achievable here

---

## Governance Invariants

| ID | Rule | Enforcement |
|----|------|-------------|
| **INV-KEY-001** | L4 cannot import sqlalchemy at runtime | BLOCKING |
| **INV-KEY-002** | L4 cannot import from L7 models directly | BLOCKING |
| **INV-KEY-003** | Facades delegate, never query directly | BLOCKING |
| **INV-KEY-004** | Call flow: Facade → Engine → Driver | BLOCKING |
| **INV-KEY-005** | Driver returns snapshots, not ORM models | BLOCKING |
| **INV-KEY-006** | `*_service.py` naming banned | BLOCKING |

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-24 | 1.0.0 | Initial plan created |

---

**STATUS: COMPLETE → LOCKED**

**END OF IMPLEMENTATION PLAN**
