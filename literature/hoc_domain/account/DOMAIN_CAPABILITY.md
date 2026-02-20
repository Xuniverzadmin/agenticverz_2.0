# Account — Domain Capability

**Domain:** account  
**Total functions:** 186  
**Generator:** `scripts/ops/hoc_capability_doc_generator.py`

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

- Project-create onboarding path is active under canonical account domain:
- `backend/app/hoc/api/cus/account/aos_accounts.py` (`POST /accounts/projects`).
- SDK attestation evidence path is active:
- handshake route writes attestation through `account.sdk_attestation`.
- activation checks include `sdk_attested` from persistent table `sdk_attestations`.
- Onboarding activation authority is DB-only in `onboarding_handler.py`:
- `api_keys` (active key)
- `cus_integrations` (enabled integration evidence)
- `sdk_attestations` (attestation exists)
- Cache-only sources are excluded by CI check 35.

## Reality Delta (2026-02-08)

- L2 purity preserved: account L2 routes dispatch via L4 `OperationRegistry` (0 direct L2→L5).
- L5/L6 purity: `PYTHONPATH=. python3 backend/scripts/ops/hoc_l5_l6_purity_audit.py --domain account --json --advisory` reports 0 blocking, 0 advisory.
- Execution boundary (pairing): `PYTHONPATH=. python3 backend/scripts/ops/l5_spine_pairing_gap_detector.py --json` reports `total_l5_engines: 69`, `wired_via_l4: 69`, `direct_l2_to_l5: 0`, `orphaned: 0`.
- Plan: `docs/architecture/hoc/DOMAIN_EXECUTION_BOUNDARY_REMEDIATION_PLAN.md`.

**Tenant Lifecycle SSOT (Phase A1):** persisted lifecycle state is `Tenant.status` and is read/written via account-owned L5/L6 wrapped by L4 operations (`account.lifecycle.query`, `account.lifecycle.transition`).

**Note (Scope):** `backend/app/hoc/cus/account/logs/CRM/audit/audit_engine.py` is CRM governance-job audit (contract/job evidence → verdict), executed via L4 operation `governance.audit_job`.

## 1. Domain Purpose

Manages customer account settings, organization profiles, team members, and account-level configuration. Provides the identity boundary for all other domains.

## 2. Customer-Facing Operations

| Function | File | L4 Wired | Entry Point | Side Effects |
|----------|------|----------|-------------|--------------|
| `AccountsFacade.accept_invitation` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.create_support_ticket` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.get_billing_invoices` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.get_billing_summary` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.get_profile` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.get_project_detail` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.get_support_contact` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.get_user_detail` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.invite_user` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.list_invitations` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.list_projects` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.list_support_tickets` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.list_tenant_users` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.list_users` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.remove_user` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.update_profile` | accounts_facade | Yes | L2:aos_accounts | pure |
| `AccountsFacade.update_user_role` | accounts_facade | Yes | L2:aos_accounts | pure |
| `ChannelInfo.to_dict` | notifications_facade | Yes | L4:account_handler | pure |
| `GovernanceConfig.to_dict` | profile | Yes | L2:aos_accounts | pure |
| `NotificationInfo.to_dict` | notifications_facade | Yes | L4:account_handler | pure |
| `NotificationPreferences.to_dict` | notifications_facade | Yes | L4:account_handler | pure |
| `NotificationsFacade.get_channel` | notifications_facade | Yes | L4:account_handler | pure |
| `NotificationsFacade.get_notification` | notifications_facade | Yes | L4:account_handler | pure |
| `NotificationsFacade.get_preferences` | notifications_facade | Yes | L4:account_handler | pure |
| `NotificationsFacade.list_channels` | notifications_facade | Yes | L4:account_handler | pure |
| `NotificationsFacade.list_notifications` | notifications_facade | Yes | L4:account_handler | pure |
| `NotificationsFacade.mark_as_read` | notifications_facade | Yes | L4:account_handler | pure |
| `NotificationsFacade.send_notification` | notifications_facade | Yes | L4:account_handler | pure |
| `NotificationsFacade.update_preferences` | notifications_facade | Yes | L4:account_handler | pure |
| `ValidatorService.validate` | crm_validator_engine | Yes | L4:contract_engine | pure |
| `get_accounts_facade` | accounts_facade | Yes | L2:aos_accounts | pure |
| `get_governance_config` | profile | Yes | L2:aos_accounts | pure |
| `get_governance_profile` | profile | Yes | L2:aos_accounts | pure |
| `get_notifications_facade` | notifications_facade | Yes | L4:account_handler | pure |
| `load_governance_config` | profile | Yes | L2:aos_accounts | pure |
| `reset_governance_config` | profile | Yes | L2:aos_accounts | pure |
| `validate_governance_at_startup` | profile | Yes | L2:aos_accounts | pure |
| `validate_governance_config` | profile | Yes | L2:aos_accounts | pure |

## 3. Internal Functions

### Decisions

| Function | File | Confidence |
|----------|------|------------|
| `EmailVerificationService.verify_otp` | email_verification | medium |
| `TenantEngine.check_run_quota` | tenant_engine | medium |
| `TenantEngine.check_token_quota` | tenant_engine | medium |
| `ValidatorService.validate` | validator_engine | medium |

### Coordinators

| Function | File | Confidence |
|----------|------|------------|
| `APIKeyIdentityResolver.resolve` | identity_resolver | medium |
| `ClerkIdentityResolver.resolve` | identity_resolver | medium |
| `IdentityChain.resolve` | identity_resolver | medium |
| `IdentityResolver.resolve` | identity_resolver | medium |
| `SystemIdentityResolver.resolve` | identity_resolver | medium |

### Helpers

_59 internal helper functions._

- **accounts_facade:** `AccountsFacade.__init__`
- **billing_provider:** `BillingProvider.get_billing_state`, `BillingProvider.get_limits`, `BillingProvider.get_plan`, `BillingProvider.is_limit_exceeded`, `MockBillingProvider.__init__`, `MockBillingProvider.get_billing_state`, `MockBillingProvider.get_limits`, `MockBillingProvider.get_plan`, `MockBillingProvider.is_limit_exceeded`, `MockBillingProvider.reset`
  _...and 4 more_
- **crm_validator_engine:** `ValidatorService.__init__`, `ValidatorService._build_reason`, `ValidatorService._calculate_confidence`, `ValidatorService._classify_issue_type`, `ValidatorService._classify_severity`, `ValidatorService._create_fallback_verdict`, `ValidatorService._determine_action`, `ValidatorService._do_validate`, `ValidatorService._extract_capabilities`, `ValidatorService._extract_text`
  _...and 3 more_
- **email_verification:** `EmailVerificationError.__init__`, `EmailVerificationService.__init__`, `EmailVerificationService._attempts_key`, `EmailVerificationService._cooldown_key`, `EmailVerificationService._generate_otp`, `EmailVerificationService._otp_key`, `EmailVerificationService._send_otp_email`
- **identity_resolver:** `ClerkIdentityResolver.__init__`
- **notifications_facade:** `NotificationsFacade.__init__`
- **profile:** `GovernanceConfigError.__init__`, `_get_bool_env`
- **tenant_driver:** `TenantDriver.__init__`
- **tenant_engine:** `QuotaExceededError.__init__`, `TenantEngine.__init__`, `TenantEngine._maybe_reset_daily_counter`
- **user_write_driver:** `UserWriteDriver.__init__`
- **user_write_engine:** `UserWriteService.__init__`, `UserWriteService.user_to_dict`
- **validator_engine:** `ValidatorService.__init__`, `ValidatorService._build_reason`, `ValidatorService._calculate_confidence`, `ValidatorService._classify_issue_type`, `ValidatorService._classify_severity`, `ValidatorService._create_fallback_verdict`, `ValidatorService._determine_action`, `ValidatorService._do_validate`, `ValidatorService._extract_capabilities`, `ValidatorService._extract_text`
  _...and 3 more_

### Persistence

| Function | File | Side Effects |
|----------|------|--------------|
| `AccountsFacadeDriver.count_tenants` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.count_users` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.delete_membership` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_invitation_by_email` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_invitation_by_id_and_token` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_invitations` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_membership` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_membership_with_user` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_profile` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_subscription` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_support_tickets` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_tenant` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_tenant_detail` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_tenant_memberships` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_tenants` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_user_by_email` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_user_by_id` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_user_detail` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.fetch_users` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.insert_invitation` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.insert_membership` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.insert_support_ticket` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.insert_user` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.update_invitation_accepted` | accounts_facade_driver | pure |
| `AccountsFacadeDriver.update_invitation_expired` | accounts_facade_driver | pure |
| `AccountsFacadeDriver.update_membership_role` | accounts_facade_driver | db_write |
| `AccountsFacadeDriver.update_user_profile` | accounts_facade_driver | pure |
| `TenantDriver.count_active_api_keys` | tenant_driver | pure |
| `TenantDriver.count_running_runs` | tenant_driver | pure |
| `TenantDriver.fetch_api_key_by_id` | tenant_driver | pure |
| `TenantDriver.fetch_api_keys` | tenant_driver | pure |
| `TenantDriver.fetch_run_by_id` | tenant_driver | pure |
| `TenantDriver.fetch_runs` | tenant_driver | pure |
| `TenantDriver.fetch_tenant_by_id` | tenant_driver | pure |
| `TenantDriver.fetch_tenant_by_slug` | tenant_driver | pure |
| `TenantDriver.fetch_tenant_snapshot` | tenant_driver | pure |
| `TenantDriver.fetch_usage_records` | tenant_driver | pure |
| `TenantDriver.increment_tenant_usage` | tenant_driver | db_write |
| `TenantDriver.insert_api_key` | tenant_driver | db_write |
| `TenantDriver.insert_audit_log` | tenant_driver | db_write |
| `TenantDriver.insert_membership` | tenant_driver | db_write |
| `TenantDriver.insert_run` | tenant_driver | db_write |
| `TenantDriver.insert_tenant` | tenant_driver | db_write |
| `TenantDriver.insert_usage_record` | tenant_driver | db_write |
| `TenantDriver.update_api_key_revoked` | tenant_driver | db_write |
| `TenantDriver.update_run_completed` | tenant_driver | db_write |
| `TenantDriver.update_tenant_plan` | tenant_driver | db_write |
| `TenantDriver.update_tenant_status` | tenant_driver | db_write |
| `TenantDriver.update_tenant_usage` | tenant_driver | db_write |
| `UserWriteDriver.create_user` | user_write_driver | db_write |
| `UserWriteDriver.update_user_login` | user_write_driver | db_write |
| `UserWriteDriver.user_to_dict` | user_write_driver | pure |
| `get_accounts_facade_driver` | accounts_facade_driver | pure |
| `get_tenant_driver` | tenant_driver | pure |
| `get_user_write_driver` | user_write_driver | pure |

### Unclassified (needs review)

_25 functions need manual classification._

- `APIKeyIdentityResolver.provider` (identity_resolver)
- `ClerkIdentityResolver.provider` (identity_resolver)
- `EmailVerificationService.send_otp` (email_verification)
- `IdentityResolver.provider` (identity_resolver)
- `SystemIdentityResolver.provider` (identity_resolver)
- `TenantEngine.complete_run` (tenant_engine)
- `TenantEngine.create_api_key` (tenant_engine)
- `TenantEngine.create_membership_with_default` (tenant_engine)
- `TenantEngine.create_run` (tenant_engine)
- `TenantEngine.create_tenant` (tenant_engine)
- `TenantEngine.get_tenant` (tenant_engine)
- `TenantEngine.get_tenant_by_slug` (tenant_engine)
- `TenantEngine.get_usage_summary` (tenant_engine)
- `TenantEngine.increment_usage` (tenant_engine)
- `TenantEngine.list_api_keys` (tenant_engine)
- `TenantEngine.list_runs` (tenant_engine)
- `TenantEngine.record_usage` (tenant_engine)
- `TenantEngine.revoke_api_key` (tenant_engine)
- `TenantEngine.suspend` (tenant_engine)
- `TenantEngine.update_plan` (tenant_engine)
- _...and 5 more_

## 4. Explicit Non-Features

_No explicit non-feature declarations found in ACCOUNT_DOMAIN_LOCK_FINAL.md._
