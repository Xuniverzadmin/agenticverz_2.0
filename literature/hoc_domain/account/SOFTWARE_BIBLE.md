# Account — Software Bible

**Domain:** account  
**L2 Features:** 5  
**Scripts:** 13  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

## Reality Delta (2026-02-16, PR-10 Account Users Facade Contract Hardening)

- Read-only account users list facade implemented at:
  - `backend/app/hoc/api/cus/account/account_public.py`
- Endpoint contract:
  - `GET /cus/account/users/list` (gateway: `/hoc/api/cus/account/users/list`)
- L4 dispatch path:
  - `account_public.py` -> `registry.execute("account.query", method="list_users", ...)`
- Boundary guarantees:
  - strict allowlist validation (`role`, `status`, `limit`, `offset`)
  - unknown-param rejection
  - `as_of` explicitly unsupported (PR-10)
  - request-id/correlation-id propagation in response meta
- Determinism hardening:
  - L6 users query ordering uses stable keys `email asc, id asc` in:
    - `backend/app/hoc/cus/account/L6_drivers/accounts_facade_driver.py`

## Reality Delta (2026-02-11)

- Account onboarding write capability includes project creation via canonical L2:
- `backend/app/hoc/api/cus/account/aos_accounts.py` (`POST /accounts/projects`)
- Path verified across layers:
- L2 `aos_accounts.py` -> L4 `account_handler.py` -> L5 `accounts_facade.py` -> L6 `accounts_facade_driver.py`.
- SDK attestation persistence is integrated:
- L2 handshake in `backend/app/hoc/api/int/general/sdk.py` dispatches `account.sdk_attestation` with real `sync_session`.
- L6 attestation persistence driver:
- `backend/app/hoc/cus/account/L6_drivers/sdk_attestation_driver.py`
- DB migration added:
- `backend/alembic/versions/127_create_sdk_attestations.py`
- Onboarding activation predicate is enforced at L4 for COMPLETE transitions in `onboarding_handler.py`.

## Reality Correction (2026-02-06)

This domain has been refactored under PIN-520 / strict HOC topology:
- L2 APIs dispatch via `OperationRegistry.execute(...)` into hoc_spine handlers.
- L5 engines do not accept `Session` parameters.
- L6 drivers are session-bound and never commit; L4 owns commit/rollback.

As a result, any generated call chains that show `L2 → L6` directly are stale.
The authoritative memory-pins feature chains are corrected below.

## Reality Delta (2026-02-08)

- Execution topology: account L2 routes dispatch via L4 `OperationRegistry` (0 direct L2→L5 gaps).
- L5/L6 purity: `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --domain account --json --advisory` reports 0 blocking, 0 advisory.
- Execution boundary (pairing): `PYTHONPATH=. python3 backend/scripts/ops/l5_spine_pairing_gap_detector.py --json` reports `total_l5_engines: 69`, `wired_via_l4: 69`, `direct_l2_to_l5: 0`, `orphaned: 0`.
- Plan: `docs/architecture/hoc/DOMAIN_EXECUTION_BOUNDARY_REMEDIATION_PLAN.md`.

**Tenant Lifecycle SSOT (Phase A1):** persisted lifecycle state is `Tenant.status` and is read/written via account-owned L5/L6 wrapped by L4 operations (`account.lifecycle.query`, `account.lifecycle.transition`).

**Onboarding SSOT (Phase A2):** persisted onboarding state is `Tenant.onboarding_state` and the canonical enum + transition metadata lives in `backend/app/hoc/cus/account/L5_schemas/onboarding_state.py` (legacy `backend/app/auth/onboarding_state.py` and the interim mirror `backend/app/hoc/cus/account/L5_schemas/onboarding_enums.py` were deleted after rewiring).

**Note (Scope):** `backend/app/hoc/cus/account/logs/CRM/audit/audit_engine.py` is CRM governance-job audit (contract/job evidence → verdict), executed via L4 operation `governance.audit_job`.

## Reality Delta (2026-02-12)

- Cross-domain validator correction completed for SDK attestation driver:
- `backend/app/hoc/cus/account/L6_drivers/sdk_attestation_driver.py` now imports `sql_text` from SQLAlchemy instead of `hoc_spine.orchestrator.operation_registry`.
- Post-fix validator state is clean (`HOC-CROSS-DOMAIN-001`: `count=0`).
- This closes the previously reported `E2 HIGH` L6 cross-domain import violation for account domain.

## Reality Delta (2026-02-12, Wave-3 Script Coverage Audit)

- Wave-3 script coverage (`controls + account`) has been independently audited and reconciled.
- Account target-scope classification is complete:
- `13` scripts marked `UC_LINKED`
- `18` scripts marked `NON_UC_SUPPORT`
- `0` target-scope residual scripts in Wave-3 account target list.
- Deterministic gates remain clean post-wave and governance suite now runs `250` passing tests in `test_uc018_uc032_expansion.py`.
- Canonical audit artifacts:
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_3_implemented.md`
- `backend/app/hoc/docs/architecture/usecases/UC_SCRIPT_COVERAGE_WAVE_3_AUDIT_2026-02-12.md`

## Script Registry

Each script's unique contribution and canonical function.

| Script | Layer | Canonical Function | Role | Decisions | Callers | Unique? |
|--------|-------|--------------------|------|-----------|---------|---------|
| accounts_facade | L5 | `AccountsFacade.accept_invitation` | CANONICAL | 4 | ?:aos_accounts | L5:__init__ | L2:aos_accounts | L4:account_handler, email_verification, profile +1 | YES |
| billing_provider | L5 | `MockBillingProvider.is_limit_exceeded` | CANONICAL | 1 | email_verification, profile, tenant_engine | YES |
| crm_validator_engine | L5 | `ValidatorService._build_reason` | LEAF | 3 | L4:contract_engine | L4:__init__, email_verification, profile +2 | **OVERLAP** |
| email_verification | L5 | `EmailVerificationService.send_otp` | CANONICAL | 1 | L5:__init__, profile, tenant_engine | YES |
| identity_resolver | L5 | `IdentityChain.resolve` | CANONICAL | 4 | ?:__init__, email_verification, profile +1 | YES |
| notifications_facade | L5 | `NotificationsFacade.update_preferences` | SUPERSET | 2 | L5:__init__ | L4:account_handler, accounts_facade, accounts_facade_driver +3 | YES |
| profile | L5 | `validate_governance_config` | CANONICAL | 5 | ?:aos_accounts | ?:failure_mode_handler | ?:boot_guard | ?:profile | ?:reactor_initializer | ?:main | L2:aos_accounts | L4:profile_policy_mode | ?:test_stubs, email_verification, tenant_engine | YES |
| tenant_engine | L5 | `TenantEngine.create_api_key` | CANONICAL | 3 | L5:__init__, email_verification, profile +1 | YES |
| user_write_engine | L5 | `UserWriteService.__init__` | WRAPPER | 0 | L5:__init__, email_verification, profile +1 | INTERFACE |
| validator_engine | L5 | `ValidatorService._build_reason` | LEAF | 3 | ?:__init__ | ?:aurora_semantic_validator, crm_validator_engine, email_verification +2 | **OVERLAP** |
| accounts_facade_driver | L6 | `AccountsFacadeDriver.update_user_profile` | SUPERSET | 3 | L6:__init__ | L5:accounts_facade, accounts_facade, tenant_engine | YES |
| tenant_driver | L6 | `TenantDriver.count_active_api_keys` | LEAF | 0 | L6:__init__ | L5:tenant_engine, accounts_facade, email_verification +2 | YES |
| user_write_driver | L6 | `UserWriteDriver.create_user` | LEAF | 0 | L6:__init__ | L5:user_write_engine, email_verification, profile +2 | YES |

## Uncalled Functions

Functions with no internal or external callers detected.
May be: unused code, missing wiring, or entry points not yet traced.

- `billing_provider.BillingProvider.get_billing_state`
- `billing_provider.BillingProvider.is_limit_exceeded`
- `billing_provider.MockBillingProvider.get_billing_state`
- `billing_provider.MockBillingProvider.is_limit_exceeded`
- `billing_provider.MockBillingProvider.reset`
- `billing_provider.MockBillingProvider.set_billing_state`
- `billing_provider.MockBillingProvider.set_plan`
- `billing_provider.get_billing_provider`
- `billing_provider.set_billing_provider`

## Overlapping Scripts (same purpose, same layer)

These scripts may serve duplicate purposes within the domain.

- `crm_validator_engine` — canonical: `ValidatorService._build_reason` (LEAF)
- `validator_engine` — canonical: `ValidatorService._build_reason` (LEAF)

## L2 Feature Chains

| Status | Count |
|--------|-------|
| COMPLETE (L2→L4→L5→L6) | 5 |
| GAP (L2→L5 direct) | 0 |

### Wired Features (L2→L4→L5→L6)

#### DELETE /pins/{key}
```
L2:account/memory_pins.delete_pin → L4:account.memory_pins (AccountMemoryPinsHandler) → L5:MemoryPinsEngine.delete_pin → L6:MemoryPinsDriver.delete_pin
```

#### GET /pins
```
L2:account/memory_pins.list_pins → L4:account.memory_pins (AccountMemoryPinsHandler) → L5:MemoryPinsEngine.list_pins → L6:MemoryPinsDriver.list_pins
```

#### GET /pins/{key}
```
L2:account/memory_pins.get_pin → L4:account.memory_pins (AccountMemoryPinsHandler) → L5:MemoryPinsEngine.get_pin → L6:MemoryPinsDriver.get_pin
```

#### POST /pins
```
L2:account/memory_pins.create_or_upsert_pin → L4:account.memory_pins (AccountMemoryPinsHandler) → L5:MemoryPinsEngine.upsert_pin → L6:MemoryPinsDriver.upsert_pin
```

#### POST /pins/cleanup
```
L2:account/memory_pins.cleanup_expired_pins → L4:account.memory_pins (AccountMemoryPinsHandler) → L5:MemoryPinsEngine.cleanup_expired → L6:MemoryPinsDriver.cleanup_expired
```

## Canonical Algorithm Inventory

| Function | File | Role | Decisions | Stmts | Persistence | Delegates To |
|----------|------|------|-----------|-------|-------------|--------------|
| `AccountsFacade.accept_invitation` | accounts_facade | CANONICAL | 4 | 12 | no | accounts_facade_driver:AccountsFacadeDriver.fetch_invitation |
| `AccountsFacade.get_billing_invoices` | accounts_facade | SUPERSET | 2 | 4 | no | accounts_facade_driver:AccountsFacadeDriver.fetch_tenant_det |
| `AccountsFacade.get_billing_summary` | accounts_facade | SUPERSET | 2 | 4 | no | accounts_facade_driver:AccountsFacadeDriver.fetch_subscripti |
| `AccountsFacade.get_project_detail` | accounts_facade | SUPERSET | 2 | 4 | no | accounts_facade_driver:AccountsFacadeDriver.fetch_tenant_det |
| `AccountsFacade.invite_user` | accounts_facade | SUPERSET | 2 | 10 | no | accounts_facade_driver:AccountsFacadeDriver.fetch_invitation |
| `AccountsFacade.list_users` | accounts_facade | SUPERSET | 2 | 7 | no | accounts_facade_driver:AccountsFacadeDriver.count_users | ac |
| `AccountsFacade.remove_user` | accounts_facade | SUPERSET | 4 | 8 | no | accounts_facade_driver:AccountsFacadeDriver.delete_membershi |
| `AccountsFacade.update_user_role` | accounts_facade | SUPERSET | 4 | 10 | no | accounts_facade_driver:AccountsFacadeDriver.fetch_membership |
| `AccountsFacadeDriver.update_user_profile` | accounts_facade_driver | SUPERSET | 3 | 6 | no | notifications_facade:NotificationsFacade.get_preferences |
| `EmailVerificationService.send_otp` | email_verification | CANONICAL | 1 | 12 | no | email_verification:EmailVerificationService._attempts_key |  |
| `EmailVerificationService.verify_otp` | email_verification | SUPERSET | 3 | 10 | no | email_verification:EmailVerificationService._attempts_key |  |
| `IdentityChain.resolve` | identity_resolver | CANONICAL | 4 | 3 | no | identity_resolver:APIKeyIdentityResolver.resolve | identity_ |
| `MockBillingProvider.is_limit_exceeded` | billing_provider | CANONICAL | 1 | 5 | no | billing_provider:BillingProvider.get_limits | billing_provid |
| `NotificationsFacade.update_preferences` | notifications_facade | SUPERSET | 2 | 6 | no | notifications_facade:NotificationsFacade.get_preferences |
| `TenantEngine._maybe_reset_daily_counter` | tenant_engine | SUPERSET | 2 | 2 | no | tenant_driver:TenantDriver.update_tenant_usage |
| `TenantEngine.check_run_quota` | tenant_engine | SUPERSET | 4 | 8 | no | tenant_driver:TenantDriver.count_running_runs | tenant_drive |
| `TenantEngine.check_token_quota` | tenant_engine | SUPERSET | 2 | 5 | no | tenant_driver:TenantDriver.fetch_tenant_by_id |
| `TenantEngine.complete_run` | tenant_engine | SUPERSET | 3 | 6 | no | tenant_driver:TenantDriver.fetch_run_by_id | tenant_driver:T |
| `TenantEngine.create_api_key` | tenant_engine | CANONICAL | 3 | 11 | no | tenant_driver:TenantDriver.count_active_api_keys | tenant_dr |
| `TenantEngine.get_usage_summary` | tenant_engine | SUPERSET | 3 | 7 | no | tenant_driver:TenantDriver.fetch_usage_records |
| `validate_governance_config` | profile | CANONICAL | 5 | 10 | no | profile:load_governance_config |

## Wrapper Inventory

_58 thin delegation functions._

- `identity_resolver.APIKeyIdentityResolver.provider` → ?
- `accounts_facade.AccountsFacade.__init__` → accounts_facade_driver:get_accounts_facade_driver
- `accounts_facade.AccountsFacade.create_support_ticket` → accounts_facade_driver:AccountsFacadeDriver.insert_support_ticket
- `accounts_facade.AccountsFacade.get_support_contact` → ?
- `accounts_facade_driver.AccountsFacadeDriver.delete_membership` → ?
- `accounts_facade_driver.AccountsFacadeDriver.update_invitation_expired` → ?
- `billing_provider.BillingProvider.get_billing_state` → ?
- `billing_provider.BillingProvider.get_limits` → ?
- `billing_provider.BillingProvider.get_plan` → ?
- `billing_provider.BillingProvider.is_limit_exceeded` → ?
- `notifications_facade.ChannelInfo.to_dict` → ?
- `identity_resolver.ClerkIdentityResolver.__init__` → ?
- `identity_resolver.ClerkIdentityResolver.provider` → ?
- `email_verification.EmailVerificationError.__init__` → accounts_facade:AccountsFacade.__init__
- `profile.GovernanceConfig.to_dict` → ?
- `identity_resolver.IdentityResolver.provider` → ?
- `identity_resolver.IdentityResolver.resolve` → ?
- `billing_provider.MockBillingProvider.__init__` → ?
- `billing_provider.MockBillingProvider.get_billing_state` → ?
- `billing_provider.MockBillingProvider.get_limits` → ?
- `billing_provider.MockBillingProvider.get_plan` → ?
- `billing_provider.MockBillingProvider.reset` → ?
- `billing_provider.MockBillingProvider.set_billing_state` → ?
- `billing_provider.MockBillingProvider.set_plan` → ?
- `notifications_facade.NotificationInfo.to_dict` → ?
- `notifications_facade.NotificationPreferences.to_dict` → ?
- `notifications_facade.NotificationsFacade.get_channel` → ?
- `notifications_facade.NotificationsFacade.list_channels` → ?
- `identity_resolver.SystemIdentityResolver.provider` → ?
- `identity_resolver.SystemIdentityResolver.resolve` → ?
- _...and 28 more_

---

## PIN-504 Amendments (2026-01-31)

| Script | Change | Reference |
|--------|--------|-----------|
| `L5_schemas/result_types.py` | **NEW** — Extracted `AccountsErrorResult` dataclass from `accounts_facade.py` so L2 can import without pulling L5 engine. | PIN-504 Phase 1 |
| `accounts_facade` | `AccountsErrorResult` re-exported from `L5_schemas.result_types` (backward compatible). | PIN-504 Phase 1 |

## PIN-507 Law 5 Remediation (2026-02-01)

| Script | Change | Reference |
|--------|--------|-----------|
| L4 `account_handler.py` | `AccountQueryHandler`: Replaced `getattr()` dispatch with explicit map (6 methods). `AccountNotificationsHandler`: Replaced `getattr()` dispatch with explicit map (4 methods). Zero reflection in dispatch paths. | PIN-507 Law 5 |

## PIN-509 Tooling Hardening (2026-02-01)

- CI checks 16–18 added to `scripts/ci/check_init_hygiene.py`:
  - Check 16: Frozen import ban (no imports from `_frozen/` paths)
  - Check 17: L5 Session symbol import ban (type erasure enforcement)
  - Check 18: Protocol surface baseline (capability creep prevention, max 12 methods)
- New scripts: `collapse_tombstones.py`, `new_l5_engine.py`, `new_l6_driver.py`
- `app/services/__init__.py` now emits DeprecationWarning
- Reference: `docs/memory-pins/PIN-509-tooling-hardening.md`

## PIN-513 Topology Completion & Hygiene (2026-02-01)

### Phase 2 — Account Bridge Creation

Account was the only domain without a bridge in `hoc_spine/orchestrator/coordinators/bridges/`. Bridge created to complete the "every domain has a bridge" invariant.

| File | Change | Reference |
|------|--------|-----------|
| **NEW** `hoc_spine/orchestrator/coordinators/bridges/account_bridge.py` | `AccountBridge` with 3 capabilities: `account_query_capability(session)` → `AccountsFacade`, `notifications_capability(session)` → `NotificationsFacade`, `tenant_capability(session)` → `TenantEngine(session)`. Singleton pattern + `get_account_bridge()` factory. | PIN-513 Phase 2 |
| `bridges/__init__.py` | Added `AccountBridge`, `get_account_bridge` to exports and `__all__` | PIN-513 Phase 2 |

## PIN-513 Phase C — Account Domain Changes (2026-02-01)

- billing_provider_engine.py: Now canonical source for `get_billing_provider`. 4 callers rewired from `app.billing.provider` to HOC path.
- profile_engine.py: Confirmed 100% duplicate of hoc_spine/authority/profile_policy_mode.py. hoc_spine version is canonical (governance is cross-domain). profile_engine.py should be MARKED_FOR_DELETION during cutover.
- Governance config callers rewired: events/reactor_initializer.py, startup/boot_guard.py (×2), policy/failure_mode_handler.py → hoc_spine/authority/profile_policy_mode.py

## PIN-513 Phase 9 — Batch 1C Wiring (2026-02-01)

**First-principles decision:** Identity resolution and governance profile are authority-level, not domain-level.

- Tombstoned `identity_resolver_engine.py` as TOPOLOGY_DEAD — canonical: hoc_spine/authority/
- Tombstoned `profile_engine.py` (6 symbols) as TOPOLOGY_DEAD — canonical: hoc_spine/authority/profile_policy_mode.py
- Reclassified `billing_provider_engine.py` (2 symbols) as already WIRED — called by BillingGate middleware + tests
- All 9 CSV entries resolved: 2 WIRED (stale), 7 TOPOLOGY_DEAD

---

### PIN-513 Phase 9 Batch 4 Amendment (2026-02-01)

**Deletions:**
- `account/L5_engines/identity_resolver_engine.py` — DELETED (was TOPOLOGY_DEAD, canonical: hoc_spine/authority/)
- `account/L5_engines/profile_engine.py` — DELETED (was TOPOLOGY_DEAD, canonical: hoc_spine/authority/profile_policy_mode.py)

**Final status:** Zero UNWIRED account symbols remain. Zero TOPOLOGY_DEAD files remain.

---

## PIN-271 Auth Subdomain Migration (2026-02-04)

### New Subdomain: `account/auth/`

Consolidated authentication and authorization components into dedicated `auth/` subdomain under account domain per PIN-271 (RBAC Authority Separation).

| File | Layer | Role | Status |
|------|-------|------|--------|
| `auth/__init__.py` | L5 | Subdomain package, re-exports all auth components | NEW |
| `auth/L5_engines/__init__.py` | L5 | L5 engines package | NEW |
| `auth/L5_engines/rbac_engine.py` | L5 | RBAC authorization engine (M7 Legacy) | MIGRATED |
| `auth/L5_engines/identity_adapter.py` | L5 | Identity extraction adapters | MIGRATED |
| `auth/L6_drivers/__init__.py` | L6 | Placeholder for future auth drivers | NEW |

### Script Registry Additions

| Script | Layer | Canonical Function | Role | Callers |
|--------|-------|--------------------|------|---------|
| rbac_engine | L5 | `RBACEngine.check` | CANONICAL | API middleware, auth choke |
| identity_adapter | L5 | `IdentityAdapter.extract_actor` | CANONICAL | IdentityChain |

### Files Deleted (Clean Cut - No Shims)

| Deleted File | Reason |
|--------------|--------|
| `hoc/int/policies/engines/rbac_engine.py` | Orphan duplicate |
| `hoc/int/general/facades/identity_adapter.py` | Moved to auth subdomain |
| `app/auth/rbac_engine.py` | Old path severed (no shim) |
| `app/auth/identity_adapter.py` | Old path severed (no shim) |

**Import path:** `from app.hoc.cus.account.auth import RBACEngine, ClerkAdapter, ...`
