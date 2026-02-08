# Account Domain — Canonical Software Literature

**Domain:** account
**Generated:** 2026-01-31
**Reference:** PIN-500
**Total Files:** 21 (13 L5_engines, 1 L5_schemas, 4 L6_drivers, 3 __init__.py)

---

## Reality Delta (2026-02-08)

- Execution topology: account L2 routes dispatch via L4 `OperationRegistry` (0 direct L2→L5 gaps).
- L5/L6 purity: `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --domain account --json --advisory` reports 0 blocking, 0 advisory.
- Execution boundary (pairing): `PYTHONPATH=. python3 backend/scripts/ops/l5_spine_pairing_gap_detector.py --json` reports `total_l5_engines: 69`, `wired_via_l4: 69`, `direct_l2_to_l5: 0`, `orphaned: 0`.

**Tenant Lifecycle SSOT (Phase A1):** persisted lifecycle state is `Tenant.status` and is read/written via account-owned L5/L6 wrapped by L4 operations (`account.lifecycle.query`, `account.lifecycle.transition`).

**Note (Scope):** `backend/app/hoc/cus/account/logs/CRM/audit/audit_engine.py` is CRM governance-job audit (contract/job evidence → verdict), executed via L4 operation `governance.audit_job`.

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

### Cross-Domain Import (1 → 0 — RESOLVED)

| File | Target Domain | Resolution |
|------|--------------|-----------|
| ~~L6_drivers/__init__.py~~ | ~~integrations~~ | **RESOLVED** (PIN-504 Phase 6): Deleted re-export block (`WorkerRegistryService` etc.). Zero callers used this path. |

### Empty Directory (Documented)

`L5_notifications/` exists but contains no .py files. Reserved for future notification engine implementation.

### L4 Handler — None

**Reality update (2026-02-06):** Account domain IS wired into hoc_spine via `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/account_handler.py` (L4).
Registered operations include:
- `account.query`
- `account.notifications`
- `account.billing.provider`
- `account.memory_pins`
- `account.tenant`

---

## Domain Purpose (from __init__.py)

Account domain handles identity and billing:
- Projects, users, profile
- Billing, support
- Email verification, tenant management

---

## L5_engines (9 files)

### __init__.py
- **Role:** Package init, re-exports `EmailVerificationService`, `TenantEngine`, `UserWriteService`, `AccountsFacade`, `NotificationsFacade`

### accounts_facade.py
- **Role:** Unified entry point for account management
- **Classes:** AccountsFacade
- **Factory:** `get_accounts_facade()`

### billing_provider_engine.py *(renamed from billing_provider.py)*
- **Role:** Phase-6 BillingProvider protocol and MockBillingProvider
- **Callers:** billing middleware, billing APIs, runtime enforcement

### crm_validator_engine.py *(relocated from L5_support/CRM/engines/)*
- **Role:** Issue Validator — pure analysis, advisory verdicts
- **Schema split:** Validator enums/dataclasses live in `account/L5_schemas/crm_validator_types.py` to avoid cross-domain L5 engine imports.

### email_verification_engine.py *(renamed from email_verification.py)*
- **Role:** Email OTP verification engine for customer onboarding
- **Classes:** EmailVerificationService
- **Callers:** onboarding.py (auth flow)

### memory_pins_engine.py
- **Role:** Memory pins business logic (feature flag, metrics, audit) — consumes an injected L6 driver port (no Session in L5).
- **Wiring:** L4 `AccountMemoryPinsHandler` owns commit/rollback and injects a session-bound L6 driver.

### notifications_facade.py
- **Role:** Centralized access to notification operations
- **Classes:** NotificationsFacade
- **Factory:** `get_notifications_facade()`

### tenant_engine.py
- **Role:** Tenant domain engine — business logic for tenant operations
- **Classes:** TenantEngine
- **Factory:** `get_tenant_engine()`

### user_write_engine.py
- **Role:** User write operations (L5 engine over L6 driver)
- **Classes:** UserWriteService (class name not yet renamed to UserWriteEngine)

---

## L5_schemas (3 files)

### __init__.py
- **Role:** Schemas package init

### result_types.py
- **Role:** Shared result types safe for L2 import

### crm_validator_types.py
- **Role:** CRM validator schema types shared across domains (enums + dataclasses)

---

## L6_drivers (5 files)

### __init__.py
- **Role:** Package init, re-exports `AccountsFacadeDriver`, `TenantDriver`, `UserWriteDriver`

### accounts_facade_driver.py
- **Role:** Accounts domain facade driver — pure data access
- **Classes:** AccountsFacadeDriver
- **Factory:** `get_accounts_facade_driver()`

### memory_pins_driver.py
- **Role:** Memory pins data access (raw SQL). Driver is session-bound; never commits.

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

---

## PIN-271 Auth Subdomain Migration (2026-02-04)

### New Subdomain: `auth/`

Created `hoc/cus/account/auth/` subdomain to consolidate authentication and authorization components per PIN-271 (RBAC Authority Separation).

**Structure:**
```
account/auth/
├── __init__.py              # Subdomain package, re-exports all auth components
├── L5_engines/
│   ├── __init__.py          # L5 engines package
│   ├── rbac_engine.py       # RBAC authorization engine (M7 Legacy)
│   └── identity_adapter.py  # Identity extraction adapters
└── L6_drivers/
    └── __init__.py          # Placeholder for future auth drivers
```

### L5_engines/rbac_engine.py
- **Role:** RBAC authorization engine with policy evaluation (M7 Legacy)
- **Classes:** `RBACEngine`, `PolicyObject`, `Decision`, `PolicyConfig`
- **Functions:** `get_rbac_engine()`, `init_rbac_engine()`, `check_permission()`, `require_permission()`, `get_policy_for_path()`
- **Role Mapping:** `map_external_role_to_aos()`, `map_external_roles_to_aos()`, `get_role_approval_level()`, `get_max_approval_level()`
- **Note:** M7 LEGACY — new code should use M28 `authorization.py`

### L5_engines/identity_adapter.py
- **Role:** Extract identity from requests, produce ActorContext
- **Classes:** `IdentityAdapter` (ABC), `ClerkAdapter`, `SystemIdentityAdapter`, `DevIdentityAdapter`
- **Exception:** `AuthenticationError`
- **Callers:** `IdentityChain`, API middleware

### Import Path Migration (Clean Cut)

Old paths **DELETED** (no shims, no backward compat):

| Component | Canonical Path | Old Path (DELETED) |
|-----------|----------------|-------------------|
| RBAC Engine | `app.hoc.cus.account.auth` | ~~`app.auth.rbac_engine`~~ |
| Identity Adapters | `app.hoc.cus.account.auth` | ~~`app.auth.identity_adapter`~~ |

### Files Deleted (Orphans)
- `hoc/int/policies/engines/rbac_engine.py` (orphan duplicate)
- `hoc/int/general/facades/identity_adapter.py` (moved to auth subdomain)

### Updated Total
- **Total Files:** 21 (13 L5_engines, 1 L5_schemas, 4 L6_drivers, 3 __init__.py)
