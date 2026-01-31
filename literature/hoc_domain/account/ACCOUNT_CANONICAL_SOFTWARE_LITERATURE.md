# Account Domain — Canonical Software Literature

**Domain:** account
**Generated:** 2026-01-31
**Reference:** PIN-500
**Total Files:** 16 (10 L5_engines, 1 L5_schemas, 4 L6_drivers, 1 __init__.py)

---

## Consolidation Actions (2026-01-31)

### Naming Violations Fixed (4 renames)

**L5 (4):**

| # | Old Name | New Name |
|---|----------|----------|
| N1 | billing_provider.py | billing_provider_engine.py |
| N2 | email_verification.py | email_verification_engine.py |
| N3 | identity_resolver.py | identity_resolver_engine.py |
| N4 | profile.py | profile_engine.py |

**L6:** All compliant. No renames needed.

### Header Correction (1)

| File | Old Header | New Header |
|------|-----------|------------|
| account/__init__.py | `# Layer: L4 — Domain Services` | `# Layer: L5 — Domain (Account)` |

### Import Path Fix (1)

| File | Old Import | New Import |
|------|-----------|------------|
| L5_engines/__init__.py | `...email_verification import` | `...email_verification_engine import` |

### Duplicate Resolved (1)

`L5_support/CRM/engines/` contained two files with identical code bodies, header-only diff:
- `validator_engine.py` (L4 header, stale metadata) — **DELETED**
- `crm_validator_engine.py` (L5 header, correct metadata) — **KEPT, relocated to L5_engines/**

`L5_support/` directory deleted after relocation.

### Legacy Connections — None

Zero active `app.services` imports. Clean.

### Cross-Domain Import (1 — Documented, Deferred to Rewiring)

| File | Target Domain | Import Path |
|------|--------------|-------------|
| L6_drivers/__init__.py | integrations | `app.hoc.cus.integrations.L6_drivers.worker_registry_driver` — re-exports WorkerRegistryService |

L6→L6 cross-domain. Should go through L4 spine. Deferred to rewiring phase.

### Empty Directory (Documented)

`L5_notifications/` exists but contains no .py files. Reserved for future notification engine implementation.

### L4 Handler — None

No `account_handler.py` exists in `hoc_spine/orchestrator/handlers/`. Account domain has no L4 orchestrator wiring. Candidate for construction during L2-L4-L5 wiring phase.

---

## Domain Purpose (from __init__.py)

Account domain handles identity and billing:
- Projects, users, profile
- Billing, support
- Email verification, tenant management

---

## L5_engines (10 files)

### __init__.py
- **Role:** Package init, re-exports EmailVerificationService, TenantEngine, UserWriteService, AccountsFacade, NotificationsFacade

### accounts_facade.py
- **Role:** Unified entry point for account management
- **Classes:** AccountsFacade
- **Factory:** `get_accounts_facade()`

### billing_provider_engine.py *(renamed from billing_provider.py)*
- **Role:** Phase-6 BillingProvider protocol and MockBillingProvider
- **Callers:** billing middleware, billing APIs, runtime enforcement

### crm_validator_engine.py *(relocated from L5_support/CRM/engines/)*
- **Role:** Issue Validator — pure analysis, advisory verdicts
- **Note:** Duplicate `validator_engine.py` deleted (header-only diff)

### email_verification_engine.py *(renamed from email_verification.py)*
- **Role:** Email OTP verification engine for customer onboarding
- **Classes:** EmailVerificationService
- **Callers:** onboarding.py (auth flow)

### identity_resolver_engine.py *(renamed from identity_resolver.py)*
- **Role:** Identity resolution from various providers
- **Callers:** IAMService, Auth middleware

### notifications_facade.py
- **Role:** Centralized access to notification operations
- **Classes:** NotificationsFacade
- **Factory:** `get_notifications_facade()`

### profile_engine.py *(renamed from profile.py)*
- **Role:** Governance Profile configuration and validation
- **Callers:** main.py (L2), workers (L5)

### tenant_engine.py
- **Role:** Tenant domain engine — business logic for tenant operations
- **Classes:** TenantEngine
- **Factory:** `get_tenant_engine()`

### user_write_engine.py
- **Role:** User write operations (L5 engine over L6 driver)
- **Classes:** UserWriteService (class name not yet renamed to UserWriteEngine)

---

## L5_schemas (1 file)

### __init__.py
- **Role:** Schemas package init (empty, awaiting schema files)

---

## L6_drivers (4 files)

### __init__.py
- **Role:** Package init, re-exports AccountsFacadeDriver, TenantDriver, UserWriteDriver, WorkerRegistryService (cross-domain)

### accounts_facade_driver.py
- **Role:** Accounts domain facade driver — pure data access
- **Classes:** AccountsFacadeDriver
- **Factory:** `get_accounts_facade_driver()`

### tenant_driver.py
- **Role:** Tenant domain driver — pure data access for tenant operations
- **Classes:** TenantDriver
- **Factory:** `get_tenant_driver()`

### user_write_driver.py
- **Role:** Data access for user write operations
- **Classes:** UserWriteDriver
- **Factory:** `get_user_write_driver()`

---

## Cleansing Cycle (2026-01-31) — PIN-503

### Cat A/B: No Actions Required

Domain has zero `app.services` imports (active or docstring) and zero `cus.general` imports.

### Cat D: L2→L5 Bypass Violations (7 — DOCUMENT ONLY)

| L2 File | Import Target |
|---------|--------------|
| `policies/aos_accounts.py` | `account.L5_engines.*` (7 imports) |

**Deferred:** Requires Loop Model infrastructure (PIN-487 Part 2).

### Tally

28/28 checks PASS (25 consolidation + 3 cleansing).
