# Account — Software Bible

**Domain:** account  
**L2 Features:** 5  
**Scripts:** 13  
**Generator:** `scripts/ops/hoc_software_bible_generator.py`

---

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
L2:memory_pins.delete_pin → L4:account_handler → L6:accounts_facade_driver.AccountsFacadeDriver.count_tenants
```

#### GET /pins
```
L2:memory_pins.list_pins → L4:account_handler → L6:accounts_facade_driver.AccountsFacadeDriver.count_tenants
```

#### GET /pins/{key}
```
L2:memory_pins.get_pin → L4:account_handler → L6:accounts_facade_driver.AccountsFacadeDriver.count_tenants
```

#### POST /pins
```
L2:memory_pins.create_or_upsert_pin → L4:account_handler → L6:accounts_facade_driver.AccountsFacadeDriver.count_tenants
```

#### POST /pins/cleanup
```
L2:memory_pins.cleanup_expired_pins → L4:account_handler → L6:accounts_facade_driver.AccountsFacadeDriver.count_tenants
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
