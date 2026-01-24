# Account Domain — HOC Layer Analysis Report
# Status: ANALYSIS COMPLETE
# Date: 2026-01-24
# BLCA Reference: HOC_LAYER_TOPOLOGY_V1.md
# Prior Art: API_KEYS_DOMAIN_ANALYSIS_REPORT.md, OVERVIEW_DOMAIN_ANALYSIS_REPORT.md

---

## Executive Summary

The Account domain (`backend/app/houseofcards/customer/account/`) contains **18 Python files** with **9 violations** identified:
- **3 CRITICAL** violations (blocking)
- **6 MEDIUM** violations (naming)

The primary issues are:
1. L4 facades with direct sqlalchemy/ORM imports (bypassing L6 drivers)
2. L6 drivers containing business logic (quota enforcement, decisions)
3. `*_service.py` naming banned under HOC Layer Topology V1
4. Layer/location mismatches (L3 code in engines/)

---

## Domain Core Axiom

> **Account is a MANAGEMENT domain, not an operations domain.**
> It manages who, what, and billing — not what happened.

Consequences:
1. Account pages MUST NOT display executions, incidents, policies, or logs
2. L4 may decide **user roles, membership, profile updates, billing status**
3. L4 must NEVER decide **run quotas, token limits, tenant suspension** (those are platform concerns)
4. L6 may only **persist, query, or aggregate account data**
5. Call flow: **Facade → Engine → Driver** (mandatory)

---

## File Inventory (18 files)

| # | File | Declared Layer | Status |
|---|------|----------------|--------|
| 1 | `facades/accounts_facade.py` | L4 | **CRITICAL** |
| 2 | `facades/notifications_facade.py` | L4 | CLEAN |
| 3 | `facades/__init__.py` | - | CLEAN |
| 4 | `engines/user_write_service.py` | L4 | **MEDIUM** |
| 5 | `engines/email_verification.py` | L3 | **CRITICAL** |
| 6 | `engines/__init__.py` | L4 | CLEAN |
| 7 | `drivers/tenant_service.py` | L6 | **CRITICAL** |
| 8 | `drivers/worker_registry_service.py` | L6 | **MEDIUM** |
| 9 | `drivers/user_write_driver.py` | L6 | CLEAN |
| 10 | `drivers/profile.py` | L6 | CLEAN |
| 11 | `drivers/identity_resolver.py` | L6 | CLEAN |
| 12 | `drivers/__init__.py` | L6 | CLEAN |
| 13 | `notifications/engines/channel_service.py` | L4 | **MEDIUM** |
| 14 | `support/CRM/engines/audit_service.py` | L8 | CLEAN |
| 15 | `support/CRM/engines/validator_service.py` | L4 | **MEDIUM** |
| 16 | `support/CRM/engines/job_executor.py` | L5 | CLEAN |
| 17 | `schemas/__init__.py` | - | CLEAN |
| 18 | `__init__.py` | - | CLEAN |

---

## Violation Details

### CRITICAL-1: accounts_facade.py — L4 with runtime sqlalchemy imports

**File:** `facades/accounts_facade.py`
**Declared Layer:** L4 — Domain Engine
**Violation Type:** L4→sqlalchemy runtime import, L4→L7 direct import

**Evidence (Lines 34-46):**
```python
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import (
    Invitation,
    Subscription,
    SupportTicket,
    Tenant,
    TenantMembership,
    User,
    generate_uuid,
    utc_now,
)
```

**Rule Violated:**
- INV-KEY-001: L4 cannot import sqlalchemy at runtime
- INV-KEY-002: L4 cannot import from L7 models directly

**Impact:** This 1300+ line facade performs all DB operations directly instead of delegating to L6 drivers. Every async method in the class contains direct SQL queries.

**Required Fix:** Extract all DB operations to `drivers/accounts_facade_driver.py` (L6). Facade must delegate to driver and compose business results only.

---

### CRITICAL-2: tenant_service.py — L6 with business logic + BANNED naming

**File:** `drivers/tenant_service.py`
**Declared Layer:** L6 — Driver
**Violation Type:** L6 contains business logic, BANNED naming

**Evidence (Header, Lines 1-5):**
```python
# Layer: L6 — Driver
# Product: system-wide
# Role: Tenant CRUD, API key management, quota enforcement  # <-- BUSINESS LOGIC
# Callers: L2 APIs, L4 engines, L5 workers
```

**Evidence (Lines 313-345) — Business Logic in L6:**
```python
def check_run_quota(self, tenant_id: str) -> Tuple[bool, str]:
    """Check if tenant can create a new run."""
    tenant = self.get_tenant(tenant_id)
    if not tenant:
        return False, "Tenant not found"

    # Check status  <-- DECISION LOGIC
    if tenant.status != "active":
        return False, f"Tenant is {tenant.status}"

    # Reset daily counter if needed  <-- BUSINESS LOGIC
    self._maybe_reset_daily_counter(tenant)

    # Check daily limit  <-- DECISION LOGIC
    if tenant.runs_today >= tenant.max_runs_per_day:
        return False, f"Daily run limit ({tenant.max_runs_per_day}) exceeded"

    # Check concurrent runs  <-- DECISION LOGIC
    running_count = self.session.exec(...)
    if running_count >= tenant.max_concurrent_runs:
        return False, f"Concurrent run limit ({tenant.max_concurrent_runs}) exceeded"

    return True, ""
```

**Rule Violated:**
- INV-KEY-006: `*_service.py` naming banned
- L6 drivers are pure data access — NO business logic (`if status !=`, `if quota >=`)

**Impact:** This 630-line file is a hybrid engine+driver that violates HOC topology. Contains:
- Quota enforcement decisions (L4 responsibility)
- Plan management logic (L4 responsibility)
- Daily counter reset logic (L4 responsibility)
- Tenant status checks (L4 responsibility)

**Required Fix:** Split into:
- `engines/tenant_engine.py` (L4) — quota decisions, plan logic, status checks
- `drivers/tenant_driver.py` (L6) — pure CRUD operations, returns snapshots

---

### CRITICAL-3: email_verification.py — Layer/location mismatch

**File:** `engines/email_verification.py`
**Declared Layer:** L3 — Boundary Adapter
**Actual Location:** `engines/` (L4 directory)
**Violation Type:** Layer/location mismatch

**Evidence (Lines 1-5):**
```python
# Layer: L3 — Boundary Adapter (Console → Platform)
# Product: AI Console
# Callers: onboarding.py (auth flow)
# Reference: PIN-240
# NOTE: Redis-only state (not PostgreSQL). M24 onboarding.
```

**Analysis:**
- Declares L3 (Boundary Adapter) but located in `engines/` which is for L4
- Contains domain-specific verification logic: OTP generation, cooldown, rate limiting
- These are NOT protocol adaptation (L3) — they are business rules (L4)

**Rule Violated:**
- File location must match declared layer
- L3 adapters are thin translation layers (<200 LOC) with no business logic

**Required Fix:** Reclassify as L4. Update header to:
```python
# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: Email OTP verification engine for customer onboarding
# RECLASSIFICATION NOTE (2026-01-24):
# This file was previously declared as L3 (Boundary Adapter).
# Reclassified to L4 because it contains domain-specific verification
# logic (OTP generation, cooldown, rate limiting). Redis-only state.
```

---

### MEDIUM-1: user_write_service.py — BANNED naming

**File:** `engines/user_write_service.py`
**Declared Layer:** L4 — Domain Engine
**Violation Type:** BANNED naming pattern

**Evidence:** File named `*_service.py` instead of `*_engine.py`

**Rule Violated:** INV-KEY-006: `*_service.py` naming banned

**Analysis:** The file is otherwise correctly structured:
- Uses TYPE_CHECKING pattern for sqlalchemy imports
- Delegates all DB operations to `UserWriteDriver`
- Contains no direct DB access

**Required Fix:** Rename to `user_write_engine.py`

---

### MEDIUM-2: worker_registry_service.py — BANNED naming

**File:** `drivers/worker_registry_service.py`
**Declared Layer:** L6 — Platform Substrate
**Violation Type:** BANNED naming pattern

**Evidence:** File named `*_service.py` instead of `*_driver.py`

**Rule Violated:** INV-KEY-006: `*_service.py` naming banned

**Analysis:** Contains some business logic (configuration merging in `get_effective_worker_config`) but primarily L6 data access patterns.

**Required Fix:** Rename to `worker_registry_driver.py`. Consider extracting configuration merging logic to L4.

---

### MEDIUM-3: channel_service.py — BANNED naming

**File:** `notifications/engines/channel_service.py`
**Declared Layer:** L4 — Domain Engine
**Violation Type:** BANNED naming pattern

**Evidence:** File named `*_service.py` instead of `*_engine.py`

**Rule Violated:** INV-KEY-006: `*_service.py` naming banned

**Analysis:** Uses in-memory stores (no DB). Properly structured otherwise.

**Required Fix:** Rename to `channel_engine.py`

---

### MEDIUM-4: validator_service.py — BANNED naming

**File:** `support/CRM/engines/validator_service.py`
**Declared Layer:** L4 — Domain Engine
**Violation Type:** BANNED naming pattern

**Evidence:** File named `*_service.py` instead of `*_engine.py`

**Rule Violated:** INV-KEY-006: `*_service.py` naming banned

**Analysis:** Properly stateless and deterministic validation logic.

**Required Fix:** Rename to `validator_engine.py`

---

## Violation Summary Table

| # | File | Violation | Severity | Phase |
|---|------|-----------|----------|-------|
| 1 | `facades/accounts_facade.py` | L4 with sqlalchemy runtime imports | CRITICAL | I |
| 2 | `facades/accounts_facade.py` | L4→L7 model imports | CRITICAL | I |
| 3 | `drivers/tenant_service.py` | L6 contains business logic | CRITICAL | I |
| 4 | `drivers/tenant_service.py` | BANNED naming (`*_service.py`) | MEDIUM | I |
| 5 | `engines/email_verification.py` | Layer/location mismatch (L3 in engines/) | CRITICAL | II |
| 6 | `engines/user_write_service.py` | BANNED naming (`*_service.py`) | MEDIUM | II |
| 7 | `drivers/worker_registry_service.py` | BANNED naming (`*_service.py`) | MEDIUM | II |
| 8 | `notifications/engines/channel_service.py` | BANNED naming (`*_service.py`) | MEDIUM | II |
| 9 | `support/CRM/engines/validator_service.py` | BANNED naming (`*_service.py`) | MEDIUM | II |

---

## Clean Files

The following files have no violations:

| File | Layer | Notes |
|------|-------|-------|
| `facades/notifications_facade.py` | L4 | In-memory stores, no DB |
| `drivers/user_write_driver.py` | L6 | Properly structured driver |
| `drivers/profile.py` | L6 | Environment-based config |
| `drivers/identity_resolver.py` | L6 | Identity abstraction |
| `support/CRM/engines/audit_service.py` | L8 | Catalyst layer |
| `support/CRM/engines/job_executor.py` | L5 | Worker layer |
| All `__init__.py` files | Various | Package exports |

---

## Recommended Phase Plan

### Phase I — Hard Violations (Boundary Repair)

**I.1 — accounts_facade.py Extraction**
1. Create `drivers/accounts_facade_driver.py` with snapshot dataclasses
2. Implement driver fetch/mutation methods
3. Update facade to delegate to driver
4. Remove runtime sqlalchemy imports from facade
5. Run BLCA verification

**I.2 — tenant_service.py Split**
1. Create `engines/tenant_engine.py` (L4) for quota/plan logic
2. Create `drivers/tenant_driver.py` (L6) for pure CRUD
3. Delete `drivers/tenant_service.py`
4. Update callers to use engine→driver pattern
5. Run BLCA verification

### Phase II — Intent Resolution

**II.1 — Reclassifications**
1. `email_verification.py`: L3 → L4 (header only)

**II.2 — Renaming**
1. `user_write_service.py` → `user_write_engine.py`
2. `worker_registry_service.py` → `worker_registry_driver.py`
3. `channel_service.py` → `channel_engine.py`
4. `validator_service.py` → `validator_engine.py`

---

## Governance Invariants (Proposed)

| ID | Rule | Enforcement |
|----|------|-------------|
| **INV-ACCT-001** | L4 cannot import sqlalchemy at runtime | BLOCKING |
| **INV-ACCT-002** | L4 cannot import from L7 models directly | BLOCKING |
| **INV-ACCT-003** | Facades delegate, never query directly | BLOCKING |
| **INV-ACCT-004** | Call flow: Facade → Engine → Driver | BLOCKING |
| **INV-ACCT-005** | Driver returns snapshots, not ORM models | BLOCKING |
| **INV-ACCT-006** | `*_service.py` naming banned | BLOCKING |
| **INV-ACCT-007** | L6 contains no business logic | BLOCKING |

---

## Complexity Assessment

| Factor | Assessment |
|--------|------------|
| File Count | 18 files |
| Critical Violations | 3 |
| Total Violations | 9 |
| Estimated Effort | HIGH (accounts_facade.py is 1300+ lines) |
| Risk Level | MEDIUM (tenant_service.py is used by many callers) |
| Dependencies | Onboarding flow, API endpoints, workers |

---

## Next Steps

1. Create `ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md`
2. Execute Phase I extractions
3. Execute Phase II renames/reclassifications
4. Run BLCA verification
5. Create `ACCOUNT_DOMAIN_LOCK_FINAL.md`
6. Update HOC INDEX.md

---

**END OF ANALYSIS REPORT**
