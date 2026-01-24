# Account Domain — LOCK FINAL
# Status: LOCKED
# Date: 2026-01-24
# BLCA Status: CLEAN (0 violations)
# Reference: ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md

---

## Domain Certification

| Check | Status | Evidence |
|-------|--------|----------|
| BLCA Scan | ✅ CLEAN | 0 violations in account domain |
| Facade Extraction | ✅ COMPLETE | `accounts_facade.py` → `accounts_facade_driver.py` |
| Tenant Service Split | ✅ COMPLETE | `tenant_service.py` → `tenant_engine.py` + `tenant_driver.py` |
| Email Verification | ✅ COMPLETE | Reclassified from L3 to L4 |
| Service Naming | ✅ FIXED | 4 files renamed from `*_service.py` |
| Init Exports | ✅ COMPLETE | `drivers/__init__.py` and `engines/__init__.py` updated |

---

## Final File Structure

```
backend/app/hoc/cus/account/
├── __init__.py
├── adapters/
│   └── __init__.py
├── drivers/
│   ├── __init__.py                      # L6 — Platform Substrate
│   ├── accounts_facade_driver.py        # L6 — Async driver for facade
│   ├── tenant_driver.py                 # L6 — Tenant data access (new)
│   ├── user_write_driver.py             # L6 — User write operations
│   └── worker_registry_driver.py        # L6 — Worker registry (renamed)
├── engines/
│   ├── __init__.py                      # L4 — Domain Engines
│   ├── email_verification.py            # L4 — Email OTP engine (reclassified)
│   ├── tenant_engine.py                 # L4 — Tenant business logic (new)
│   └── user_write_engine.py             # L4 — User write engine (renamed)
├── facades/
│   ├── __init__.py
│   └── accounts_facade.py               # L4 — Domain Facade (delegates to driver)
├── notifications/
│   └── engines/
│       └── channel_engine.py            # L4 — Notification channels (renamed)
├── support/
│   └── CRM/
│       └── engines/
│           └── validator_engine.py      # L4 — CRM validation (renamed)
└── schemas/
    └── __init__.py
```

---

## Layer Distribution

| Layer | Files | Role |
|-------|-------|------|
| L4 (Domain Engine) | `accounts_facade.py`, `tenant_engine.py`, `email_verification.py`, `user_write_engine.py`, `channel_engine.py`, `validator_engine.py` | Business logic, orchestration |
| L6 (Platform Substrate) | `accounts_facade_driver.py`, `tenant_driver.py`, `user_write_driver.py`, `worker_registry_driver.py` | Pure data access |

---

## Violations Remediated

| # | File | Violation | Resolution |
|---|------|-----------|------------|
| 1 | `accounts_facade.py` | L4 with sqlalchemy runtime imports | ✅ Extracted to `accounts_facade_driver.py` |
| 2 | `accounts_facade.py` | L4→L7 model imports | ✅ Moved to driver |
| 3 | `tenant_service.py` | L6 contains business logic | ✅ Split into `tenant_engine.py` (L4) + `tenant_driver.py` (L6) |
| 4 | `tenant_service.py` | BANNED_NAMING (`*_service.py`) | ✅ Deleted, replaced with engine + driver |
| 5 | `email_verification.py` | Layer/location mismatch (L3 in engines/) | ✅ Reclassified to L4 with note |
| 6 | `user_write_service.py` | BANNED_NAMING (`*_service.py`) | ✅ Renamed to `user_write_engine.py` |
| 7 | `worker_registry_service.py` | BANNED_NAMING (`*_service.py`) | ✅ Renamed to `worker_registry_driver.py` |
| 8 | `channel_service.py` | BANNED_NAMING (`*_service.py`) | ✅ Renamed to `channel_engine.py` |
| 9 | `validator_service.py` | BANNED_NAMING (`*_service.py`) | ✅ Renamed to `validator_engine.py` |

---

## Governance Invariants (Enforced)

| ID | Rule | Status |
|----|------|--------|
| INV-ACCT-001 | L4 cannot import sqlalchemy at runtime | ✅ ENFORCED |
| INV-ACCT-002 | L4 cannot import from L7 models directly | ✅ ENFORCED |
| INV-ACCT-003 | Facades delegate, never query directly | ✅ ENFORCED |
| INV-ACCT-004 | Call flow: Facade → Engine → Driver | ✅ ENFORCED |
| INV-ACCT-005 | Driver returns snapshots, not ORM models | ✅ ENFORCED |
| INV-ACCT-006 | `*_service.py` naming banned | ✅ ENFORCED |
| INV-ACCT-007 | L6 contains no business logic | ✅ ENFORCED |

---

## Call Flow Verification

### Facade Path (Async, Customer Console)
```
L2 API (account endpoints)
    ↓
L4 Facade (accounts_facade.py)
    ↓
L6 Driver (accounts_facade_driver.py)
    ↓
L7 Models (app.models.tenant.*)
```

### Tenant Engine Path (Sync, Quota/Run Management)
```
L2 API or L5 Worker
    ↓
L4 Engine (tenant_engine.py)
    ↓
L6 Driver (tenant_driver.py)
    ↓
L7 Models (app.models.tenant.*)
```

### User Write Path
```
L2 API (onboarding)
    ↓
L4 Engine (user_write_engine.py)
    ↓
L6 Driver (user_write_driver.py)
    ↓
L7 Models (app.models.tenant.User)
```

---

## Files Created

| File | Layer | Purpose |
|------|-------|---------|
| `accounts_facade_driver.py` | L6 | Pure async data access for facade |
| `tenant_driver.py` | L6 | Tenant/API key/usage data access |
| `tenant_engine.py` | L4 | Quota decisions, plan logic, run lifecycle |

---

## Files Deleted

| File | Reason |
|------|--------|
| `drivers/tenant_service.py` | BANNED_NAMING + L6 with business logic, split into engine + driver |

---

## Files Renamed

| Old Name | New Name | Layer |
|----------|----------|-------|
| `engines/user_write_service.py` | `engines/user_write_engine.py` | L4 |
| `drivers/worker_registry_service.py` | `drivers/worker_registry_driver.py` | L6 |
| `notifications/engines/channel_service.py` | `notifications/engines/channel_engine.py` | L4 |
| `support/CRM/engines/validator_service.py` | `support/CRM/engines/validator_engine.py` | L4 |

---

## Domain Axiom (LOCKED)

> **Account is a MANAGEMENT domain, not an operations domain.**
> It manages who, what, and billing — not what happened.

Consequences:
1. Account pages MUST NOT display executions, incidents, policies, or logs
2. L4 may decide **user roles, membership, profile updates, billing status**
3. L4 must NEVER decide **run quotas, token limits, tenant suspension** (platform concerns)
4. L6 may only **persist, query, or aggregate account data**
5. Call flow: **Facade → Engine → Driver** (mandatory)

---

## Post-Lock Constraints

Any future changes to the account domain MUST:

1. Maintain 0 BLCA violations
2. Follow the established call flow patterns
3. Place all DB operations in L6 drivers
4. Keep business logic in L4 engines/facades
5. Use snapshot dataclasses for driver return types
6. Never use `*_service.py` naming
7. Never import sqlalchemy/sqlmodel at runtime in L4

---

## Certification

```
DOMAIN: account
STATUS: LOCKED
DATE: 2026-01-24
BLCA: CLEAN (0 violations)
PHASE: 2.5B COMPLETE
VIOLATIONS_REMEDIATED: 9
FILES_CREATED: 3
FILES_DELETED: 1
FILES_RENAMED: 4
```

---

## Changelog

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-24 | 1.0.0 | Initial lock | Claude |
| 2026-01-24 | 1.1.0 | Phase 2.5E BLCA verification: 0 errors, 0 warnings across all 6 check types | Claude |

---

**END OF LOCK DOCUMENT**
