# Account — Call Graph

**Domain:** account  
**Total functions:** 186  
**Generator:** `scripts/ops/hoc_call_chain_tracer.py`

---

## Role Summary

| Role | Count | Description |
|------|-------|-------------|
| CANONICAL | 6 | Owns the algorithm — most decisions, primary logic |
| SUPERSET | 15 | Calls other functions + adds its own decisions |
| WRAPPER | 58 | Thin delegation — ≤3 stmts, no branching |
| LEAF | 83 | Terminal — calls no other domain functions |
| ENTRY | 15 | Entry point — no domain-internal callers |
| INTERNAL | 9 | Called only by other domain functions |

## Canonical Algorithm Owners

### `accounts_facade.AccountsFacade.accept_invitation`
- **Layer:** L5
- **Decisions:** 4
- **Statements:** 12
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** accounts_facade.AccountsFacade.accept_invitation → accounts_facade_driver.AccountsFacadeDriver.fetch_invitation_by_id_and_token → accounts_facade_driver.AccountsFacadeDriver.fetch_membership → accounts_facade_driver.AccountsFacadeDriver.fetch_user_by_email → ...+5
- **Calls:** accounts_facade_driver:AccountsFacadeDriver.fetch_invitation_by_id_and_token, accounts_facade_driver:AccountsFacadeDriver.fetch_membership, accounts_facade_driver:AccountsFacadeDriver.fetch_user_by_email, accounts_facade_driver:AccountsFacadeDriver.insert_membership, accounts_facade_driver:AccountsFacadeDriver.insert_user, accounts_facade_driver:AccountsFacadeDriver.update_invitation_accepted, accounts_facade_driver:AccountsFacadeDriver.update_invitation_expired, tenant_driver:TenantDriver.insert_membership

### `billing_provider.MockBillingProvider.is_limit_exceeded`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 5
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** billing_provider.MockBillingProvider.is_limit_exceeded → billing_provider.BillingProvider.get_limits → billing_provider.BillingProvider.get_plan → billing_provider.MockBillingProvider.get_limits → ...+1
- **Calls:** billing_provider:BillingProvider.get_limits, billing_provider:BillingProvider.get_plan, billing_provider:MockBillingProvider.get_limits, billing_provider:MockBillingProvider.get_plan

### `email_verification.EmailVerificationService.send_otp`
- **Layer:** L5
- **Decisions:** 1
- **Statements:** 12
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** email_verification.EmailVerificationService.send_otp → email_verification.EmailVerificationService._attempts_key → email_verification.EmailVerificationService._cooldown_key → email_verification.EmailVerificationService._generate_otp → ...+2
- **Calls:** email_verification:EmailVerificationService._attempts_key, email_verification:EmailVerificationService._cooldown_key, email_verification:EmailVerificationService._generate_otp, email_verification:EmailVerificationService._otp_key, email_verification:EmailVerificationService._send_otp_email

### `identity_resolver.IdentityChain.resolve`
- **Layer:** L5
- **Decisions:** 4
- **Statements:** 3
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** identity_resolver.IdentityChain.resolve → identity_resolver.APIKeyIdentityResolver.resolve → identity_resolver.ClerkIdentityResolver.resolve → identity_resolver.IdentityResolver.resolve → ...+1
- **Calls:** identity_resolver:APIKeyIdentityResolver.resolve, identity_resolver:ClerkIdentityResolver.resolve, identity_resolver:IdentityResolver.resolve, identity_resolver:SystemIdentityResolver.resolve

### `profile.validate_governance_config`
- **Layer:** L5
- **Decisions:** 5
- **Statements:** 10
- **Delegation depth:** 2
- **Persistence:** no
- **Chain:** profile.validate_governance_config → profile.load_governance_config
- **Calls:** profile:load_governance_config

### `tenant_engine.TenantEngine.create_api_key`
- **Layer:** L5
- **Decisions:** 3
- **Statements:** 11
- **Delegation depth:** 1
- **Persistence:** no
- **Chain:** tenant_engine.TenantEngine.create_api_key → tenant_driver.TenantDriver.count_active_api_keys → tenant_driver.TenantDriver.fetch_tenant_by_id → tenant_driver.TenantDriver.insert_api_key → ...+1
- **Calls:** tenant_driver:TenantDriver.count_active_api_keys, tenant_driver:TenantDriver.fetch_tenant_by_id, tenant_driver:TenantDriver.insert_api_key, tenant_driver:TenantDriver.insert_audit_log

## Supersets (orchestrating functions)

### `accounts_facade.AccountsFacade.get_billing_invoices`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** accounts_facade_driver:AccountsFacadeDriver.fetch_tenant_detail

### `accounts_facade.AccountsFacade.get_billing_summary`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** accounts_facade_driver:AccountsFacadeDriver.fetch_subscription, accounts_facade_driver:AccountsFacadeDriver.fetch_tenant_detail

### `accounts_facade.AccountsFacade.get_project_detail`
- **Decisions:** 2, **Statements:** 4
- **Subsumes:** accounts_facade_driver:AccountsFacadeDriver.fetch_tenant_detail

### `accounts_facade.AccountsFacade.invite_user`
- **Decisions:** 2, **Statements:** 10
- **Subsumes:** accounts_facade_driver:AccountsFacadeDriver.fetch_invitation_by_email, accounts_facade_driver:AccountsFacadeDriver.fetch_membership, accounts_facade_driver:AccountsFacadeDriver.insert_invitation

### `accounts_facade.AccountsFacade.list_users`
- **Decisions:** 2, **Statements:** 7
- **Subsumes:** accounts_facade_driver:AccountsFacadeDriver.count_users, accounts_facade_driver:AccountsFacadeDriver.fetch_users

### `accounts_facade.AccountsFacade.remove_user`
- **Decisions:** 4, **Statements:** 8
- **Subsumes:** accounts_facade_driver:AccountsFacadeDriver.delete_membership, accounts_facade_driver:AccountsFacadeDriver.fetch_membership

### `accounts_facade.AccountsFacade.update_user_role`
- **Decisions:** 4, **Statements:** 10
- **Subsumes:** accounts_facade_driver:AccountsFacadeDriver.fetch_membership, accounts_facade_driver:AccountsFacadeDriver.fetch_membership_with_user, accounts_facade_driver:AccountsFacadeDriver.update_membership_role

### `accounts_facade_driver.AccountsFacadeDriver.update_user_profile`
- **Decisions:** 3, **Statements:** 6
- **Subsumes:** notifications_facade:NotificationsFacade.get_preferences

### `email_verification.EmailVerificationService.verify_otp`
- **Decisions:** 3, **Statements:** 10
- **Subsumes:** email_verification:EmailVerificationService._attempts_key, email_verification:EmailVerificationService._otp_key

### `notifications_facade.NotificationsFacade.update_preferences`
- **Decisions:** 2, **Statements:** 6
- **Subsumes:** notifications_facade:NotificationsFacade.get_preferences

### `tenant_engine.TenantEngine._maybe_reset_daily_counter`
- **Decisions:** 2, **Statements:** 2
- **Subsumes:** tenant_driver:TenantDriver.update_tenant_usage

### `tenant_engine.TenantEngine.check_run_quota`
- **Decisions:** 4, **Statements:** 8
- **Subsumes:** tenant_driver:TenantDriver.count_running_runs, tenant_driver:TenantDriver.fetch_tenant_by_id, tenant_engine:TenantEngine._maybe_reset_daily_counter

### `tenant_engine.TenantEngine.check_token_quota`
- **Decisions:** 2, **Statements:** 5
- **Subsumes:** tenant_driver:TenantDriver.fetch_tenant_by_id

### `tenant_engine.TenantEngine.complete_run`
- **Decisions:** 3, **Statements:** 6
- **Subsumes:** tenant_driver:TenantDriver.fetch_run_by_id, tenant_driver:TenantDriver.fetch_tenant_by_id, tenant_driver:TenantDriver.update_run_completed, tenant_driver:TenantDriver.update_tenant_usage, tenant_engine:TenantEngine.record_usage

### `tenant_engine.TenantEngine.get_usage_summary`
- **Decisions:** 3, **Statements:** 7
- **Subsumes:** tenant_driver:TenantDriver.fetch_usage_records

## Wrappers (thin delegation)

- `accounts_facade.AccountsFacade.__init__` → accounts_facade_driver:get_accounts_facade_driver
- `accounts_facade.AccountsFacade.create_support_ticket` → accounts_facade_driver:AccountsFacadeDriver.insert_support_ticket
- `accounts_facade.AccountsFacade.get_support_contact` → ?
- `accounts_facade_driver.AccountsFacadeDriver.delete_membership` → ?
- `accounts_facade_driver.AccountsFacadeDriver.update_invitation_expired` → ?
- `billing_provider.BillingProvider.get_billing_state` → ?
- `billing_provider.BillingProvider.get_limits` → ?
- `billing_provider.BillingProvider.get_plan` → ?
- `billing_provider.BillingProvider.is_limit_exceeded` → ?
- `billing_provider.MockBillingProvider.__init__` → ?
- `billing_provider.MockBillingProvider.get_billing_state` → ?
- `billing_provider.MockBillingProvider.get_limits` → ?
- `billing_provider.MockBillingProvider.get_plan` → ?
- `billing_provider.MockBillingProvider.reset` → ?
- `billing_provider.MockBillingProvider.set_billing_state` → ?
- `billing_provider.MockBillingProvider.set_plan` → ?
- `billing_provider.set_billing_provider` → ?
- `crm_validator_engine.ValidatorService.__init__` → ?
- `crm_validator_engine.ValidatorService._find_severity_indicators` → ?
- `email_verification.EmailVerificationError.__init__` → accounts_facade:AccountsFacade.__init__
- `identity_resolver.APIKeyIdentityResolver.provider` → ?
- `identity_resolver.ClerkIdentityResolver.__init__` → ?
- `identity_resolver.ClerkIdentityResolver.provider` → ?
- `identity_resolver.IdentityResolver.provider` → ?
- `identity_resolver.IdentityResolver.resolve` → ?
- `identity_resolver.SystemIdentityResolver.provider` → ?
- `identity_resolver.SystemIdentityResolver.resolve` → ?
- `notifications_facade.ChannelInfo.to_dict` → ?
- `notifications_facade.NotificationInfo.to_dict` → ?
- `notifications_facade.NotificationPreferences.to_dict` → ?
- `notifications_facade.NotificationsFacade.get_channel` → ?
- `notifications_facade.NotificationsFacade.list_channels` → ?
- `profile.GovernanceConfig.to_dict` → ?
- `profile.reset_governance_config` → ?
- `profile.validate_governance_at_startup` → profile:get_governance_config
- `tenant_driver.TenantDriver.__init__` → ?
- `tenant_driver.TenantDriver.fetch_api_key_by_id` → ?
- `tenant_driver.TenantDriver.fetch_run_by_id` → ?
- `tenant_driver.TenantDriver.fetch_tenant_by_id` → ?
- `tenant_driver.TenantDriver.increment_tenant_usage` → tenant_engine:TenantEngine.increment_usage
- `tenant_driver.get_tenant_driver` → ?
- `tenant_engine.TenantEngine.__init__` → tenant_driver:get_tenant_driver
- `tenant_engine.TenantEngine.create_membership_with_default` → accounts_facade_driver:AccountsFacadeDriver.insert_membership
- `tenant_engine.TenantEngine.get_tenant` → tenant_driver:TenantDriver.fetch_tenant_by_id
- `tenant_engine.TenantEngine.get_tenant_by_slug` → tenant_driver:TenantDriver.fetch_tenant_by_slug
- `tenant_engine.TenantEngine.list_api_keys` → tenant_driver:TenantDriver.fetch_api_keys
- `tenant_engine.TenantEngine.list_runs` → tenant_driver:TenantDriver.fetch_runs
- `tenant_engine.TenantEngine.record_usage` → tenant_driver:TenantDriver.insert_usage_record
- `tenant_engine.get_tenant_engine` → ?
- `user_write_driver.UserWriteDriver.__init__` → ?
- `user_write_driver.UserWriteDriver.user_to_dict` → ?
- `user_write_driver.get_user_write_driver` → ?
- `user_write_engine.UserWriteService.__init__` → user_write_driver:get_user_write_driver
- `user_write_engine.UserWriteService.create_user` → user_write_driver:UserWriteDriver.create_user
- `user_write_engine.UserWriteService.update_user_login` → user_write_driver:UserWriteDriver.update_user_login
- `user_write_engine.UserWriteService.user_to_dict` → user_write_driver:UserWriteDriver.user_to_dict
- `validator_engine.ValidatorService.__init__` → ?
- `validator_engine.ValidatorService._find_severity_indicators` → ?

## Full Call Graph

```
[WRAPPER] accounts_facade.AccountsFacade.__init__ → accounts_facade_driver:get_accounts_facade_driver
[CANONICAL] accounts_facade.AccountsFacade.accept_invitation → accounts_facade_driver:AccountsFacadeDriver.fetch_invitation_by_id_and_token, accounts_facade_driver:AccountsFacadeDriver.fetch_membership, accounts_facade_driver:AccountsFacadeDriver.fetch_user_by_email, accounts_facade_driver:AccountsFacadeDriver.insert_membership, accounts_facade_driver:AccountsFacadeDriver.insert_user, ...+3
[WRAPPER] accounts_facade.AccountsFacade.create_support_ticket → accounts_facade_driver:AccountsFacadeDriver.insert_support_ticket
[SUPERSET] accounts_facade.AccountsFacade.get_billing_invoices → accounts_facade_driver:AccountsFacadeDriver.fetch_tenant_detail
[SUPERSET] accounts_facade.AccountsFacade.get_billing_summary → accounts_facade_driver:AccountsFacadeDriver.fetch_subscription, accounts_facade_driver:AccountsFacadeDriver.fetch_tenant_detail
[ENTRY] accounts_facade.AccountsFacade.get_profile → accounts_facade_driver:AccountsFacadeDriver.fetch_profile
[SUPERSET] accounts_facade.AccountsFacade.get_project_detail → accounts_facade_driver:AccountsFacadeDriver.fetch_tenant_detail
[WRAPPER] accounts_facade.AccountsFacade.get_support_contact
[ENTRY] accounts_facade.AccountsFacade.get_user_detail → accounts_facade_driver:AccountsFacadeDriver.fetch_user_detail
[SUPERSET] accounts_facade.AccountsFacade.invite_user → accounts_facade_driver:AccountsFacadeDriver.fetch_invitation_by_email, accounts_facade_driver:AccountsFacadeDriver.fetch_membership, accounts_facade_driver:AccountsFacadeDriver.insert_invitation
[ENTRY] accounts_facade.AccountsFacade.list_invitations → accounts_facade_driver:AccountsFacadeDriver.fetch_invitations, accounts_facade_driver:AccountsFacadeDriver.fetch_membership
[ENTRY] accounts_facade.AccountsFacade.list_projects → accounts_facade_driver:AccountsFacadeDriver.count_tenants, accounts_facade_driver:AccountsFacadeDriver.fetch_tenants
[ENTRY] accounts_facade.AccountsFacade.list_support_tickets → accounts_facade_driver:AccountsFacadeDriver.fetch_support_tickets
[ENTRY] accounts_facade.AccountsFacade.list_tenant_users → accounts_facade_driver:AccountsFacadeDriver.fetch_tenant_memberships
[SUPERSET] accounts_facade.AccountsFacade.list_users → accounts_facade_driver:AccountsFacadeDriver.count_users, accounts_facade_driver:AccountsFacadeDriver.fetch_users
[SUPERSET] accounts_facade.AccountsFacade.remove_user → accounts_facade_driver:AccountsFacadeDriver.delete_membership, accounts_facade_driver:AccountsFacadeDriver.fetch_membership
[ENTRY] accounts_facade.AccountsFacade.update_profile → accounts_facade_driver:AccountsFacadeDriver.fetch_user_by_id, accounts_facade_driver:AccountsFacadeDriver.update_user_profile, notifications_facade:NotificationsFacade.get_preferences
[SUPERSET] accounts_facade.AccountsFacade.update_user_role → accounts_facade_driver:AccountsFacadeDriver.fetch_membership, accounts_facade_driver:AccountsFacadeDriver.fetch_membership_with_user, accounts_facade_driver:AccountsFacadeDriver.update_membership_role
[LEAF] accounts_facade.get_accounts_facade
[LEAF] accounts_facade_driver.AccountsFacadeDriver.count_tenants
[LEAF] accounts_facade_driver.AccountsFacadeDriver.count_users
[WRAPPER] accounts_facade_driver.AccountsFacadeDriver.delete_membership
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_invitation_by_email
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_invitation_by_id_and_token
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_invitations
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_membership
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_membership_with_user
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_profile
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_subscription
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_support_tickets
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_tenant
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_tenant_detail
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_tenant_memberships
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_tenants
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_user_by_email
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_user_by_id
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_user_detail
[LEAF] accounts_facade_driver.AccountsFacadeDriver.fetch_users
[LEAF] accounts_facade_driver.AccountsFacadeDriver.insert_invitation
[LEAF] accounts_facade_driver.AccountsFacadeDriver.insert_membership
[LEAF] accounts_facade_driver.AccountsFacadeDriver.insert_support_ticket
[LEAF] accounts_facade_driver.AccountsFacadeDriver.insert_user
[LEAF] accounts_facade_driver.AccountsFacadeDriver.update_invitation_accepted
[WRAPPER] accounts_facade_driver.AccountsFacadeDriver.update_invitation_expired
[LEAF] accounts_facade_driver.AccountsFacadeDriver.update_membership_role
[SUPERSET] accounts_facade_driver.AccountsFacadeDriver.update_user_profile → notifications_facade:NotificationsFacade.get_preferences
[LEAF] accounts_facade_driver.get_accounts_facade_driver
[WRAPPER] billing_provider.BillingProvider.get_billing_state
[WRAPPER] billing_provider.BillingProvider.get_limits
[WRAPPER] billing_provider.BillingProvider.get_plan
[WRAPPER] billing_provider.BillingProvider.is_limit_exceeded
[WRAPPER] billing_provider.MockBillingProvider.__init__
[WRAPPER] billing_provider.MockBillingProvider.get_billing_state
[WRAPPER] billing_provider.MockBillingProvider.get_limits
[WRAPPER] billing_provider.MockBillingProvider.get_plan
[CANONICAL] billing_provider.MockBillingProvider.is_limit_exceeded → billing_provider:BillingProvider.get_limits, billing_provider:BillingProvider.get_plan, billing_provider:MockBillingProvider.get_limits, billing_provider:MockBillingProvider.get_plan
[WRAPPER] billing_provider.MockBillingProvider.reset
[WRAPPER] billing_provider.MockBillingProvider.set_billing_state
[WRAPPER] billing_provider.MockBillingProvider.set_plan
[LEAF] billing_provider.get_billing_provider
[WRAPPER] billing_provider.set_billing_provider
[WRAPPER] crm_validator_engine.ValidatorService.__init__
[LEAF] crm_validator_engine.ValidatorService._build_reason
[INTERNAL] crm_validator_engine.ValidatorService._calculate_confidence → crm_validator_engine:ValidatorService._get_capability_confidence, crm_validator_engine:ValidatorService._get_source_weight, validator_engine:ValidatorService._get_capability_confidence, validator_engine:ValidatorService._get_source_weight
[LEAF] crm_validator_engine.ValidatorService._classify_issue_type
[LEAF] crm_validator_engine.ValidatorService._classify_severity
[LEAF] crm_validator_engine.ValidatorService._create_fallback_verdict
[LEAF] crm_validator_engine.ValidatorService._determine_action
[INTERNAL] crm_validator_engine.ValidatorService._do_validate → crm_validator_engine:ValidatorService._build_reason, crm_validator_engine:ValidatorService._calculate_confidence, crm_validator_engine:ValidatorService._classify_issue_type, crm_validator_engine:ValidatorService._classify_severity, crm_validator_engine:ValidatorService._determine_action, ...+15
[LEAF] crm_validator_engine.ValidatorService._extract_capabilities
[LEAF] crm_validator_engine.ValidatorService._extract_text
[WRAPPER] crm_validator_engine.ValidatorService._find_severity_indicators
[LEAF] crm_validator_engine.ValidatorService._get_capability_confidence
[LEAF] crm_validator_engine.ValidatorService._get_source_weight
[ENTRY] crm_validator_engine.ValidatorService.validate → crm_validator_engine:ValidatorService._create_fallback_verdict, crm_validator_engine:ValidatorService._do_validate, validator_engine:ValidatorService._create_fallback_verdict, validator_engine:ValidatorService._do_validate
[WRAPPER] email_verification.EmailVerificationError.__init__ → accounts_facade:AccountsFacade.__init__, billing_provider:MockBillingProvider.__init__, crm_validator_engine:ValidatorService.__init__, email_verification:EmailVerificationService.__init__, identity_resolver:ClerkIdentityResolver.__init__, ...+8
[LEAF] email_verification.EmailVerificationService.__init__
[LEAF] email_verification.EmailVerificationService._attempts_key
[LEAF] email_verification.EmailVerificationService._cooldown_key
[LEAF] email_verification.EmailVerificationService._generate_otp
[LEAF] email_verification.EmailVerificationService._otp_key
[LEAF] email_verification.EmailVerificationService._send_otp_email
[CANONICAL] email_verification.EmailVerificationService.send_otp → email_verification:EmailVerificationService._attempts_key, email_verification:EmailVerificationService._cooldown_key, email_verification:EmailVerificationService._generate_otp, email_verification:EmailVerificationService._otp_key, email_verification:EmailVerificationService._send_otp_email
[SUPERSET] email_verification.EmailVerificationService.verify_otp → email_verification:EmailVerificationService._attempts_key, email_verification:EmailVerificationService._otp_key
[LEAF] email_verification.get_email_verification_service
[WRAPPER] identity_resolver.APIKeyIdentityResolver.provider
[LEAF] identity_resolver.APIKeyIdentityResolver.resolve
[WRAPPER] identity_resolver.ClerkIdentityResolver.__init__
[WRAPPER] identity_resolver.ClerkIdentityResolver.provider
[LEAF] identity_resolver.ClerkIdentityResolver.resolve
[CANONICAL] identity_resolver.IdentityChain.resolve → identity_resolver:APIKeyIdentityResolver.resolve, identity_resolver:ClerkIdentityResolver.resolve, identity_resolver:IdentityResolver.resolve, identity_resolver:SystemIdentityResolver.resolve
[WRAPPER] identity_resolver.IdentityResolver.provider
[WRAPPER] identity_resolver.IdentityResolver.resolve
[WRAPPER] identity_resolver.SystemIdentityResolver.provider
[WRAPPER] identity_resolver.SystemIdentityResolver.resolve
[LEAF] identity_resolver.create_default_identity_chain
[WRAPPER] notifications_facade.ChannelInfo.to_dict
[WRAPPER] notifications_facade.NotificationInfo.to_dict
[WRAPPER] notifications_facade.NotificationPreferences.to_dict
[LEAF] notifications_facade.NotificationsFacade.__init__
[WRAPPER] notifications_facade.NotificationsFacade.get_channel
[LEAF] notifications_facade.NotificationsFacade.get_notification
[LEAF] notifications_facade.NotificationsFacade.get_preferences
[WRAPPER] notifications_facade.NotificationsFacade.list_channels
[LEAF] notifications_facade.NotificationsFacade.list_notifications
[LEAF] notifications_facade.NotificationsFacade.mark_as_read
[LEAF] notifications_facade.NotificationsFacade.send_notification
[SUPERSET] notifications_facade.NotificationsFacade.update_preferences → notifications_facade:NotificationsFacade.get_preferences
[LEAF] notifications_facade.get_notifications_facade
[WRAPPER] profile.GovernanceConfig.to_dict
[INTERNAL] profile.GovernanceConfigError.__init__ → accounts_facade:AccountsFacade.__init__, billing_provider:MockBillingProvider.__init__, crm_validator_engine:ValidatorService.__init__, email_verification:EmailVerificationError.__init__, email_verification:EmailVerificationService.__init__, ...+8
[LEAF] profile._get_bool_env
[INTERNAL] profile.get_governance_config → profile:load_governance_config, profile:validate_governance_config
[LEAF] profile.get_governance_profile
[INTERNAL] profile.load_governance_config → notifications_facade:ChannelInfo.to_dict, notifications_facade:NotificationInfo.to_dict, notifications_facade:NotificationPreferences.to_dict, profile:GovernanceConfig.to_dict, profile:_get_bool_env, ...+1
[WRAPPER] profile.reset_governance_config
[WRAPPER] profile.validate_governance_at_startup → profile:get_governance_config
[CANONICAL] profile.validate_governance_config → profile:load_governance_config
[WRAPPER] tenant_driver.TenantDriver.__init__
[LEAF] tenant_driver.TenantDriver.count_active_api_keys
[LEAF] tenant_driver.TenantDriver.count_running_runs
[WRAPPER] tenant_driver.TenantDriver.fetch_api_key_by_id
[LEAF] tenant_driver.TenantDriver.fetch_api_keys
[WRAPPER] tenant_driver.TenantDriver.fetch_run_by_id
[LEAF] tenant_driver.TenantDriver.fetch_runs
[WRAPPER] tenant_driver.TenantDriver.fetch_tenant_by_id
[LEAF] tenant_driver.TenantDriver.fetch_tenant_by_slug
[ENTRY] tenant_driver.TenantDriver.fetch_tenant_snapshot → tenant_driver:TenantDriver.fetch_tenant_by_id
[LEAF] tenant_driver.TenantDriver.fetch_usage_records
[WRAPPER] tenant_driver.TenantDriver.increment_tenant_usage → tenant_engine:TenantEngine.increment_usage
[LEAF] tenant_driver.TenantDriver.insert_api_key
[LEAF] tenant_driver.TenantDriver.insert_audit_log
[LEAF] tenant_driver.TenantDriver.insert_membership
[LEAF] tenant_driver.TenantDriver.insert_run
[LEAF] tenant_driver.TenantDriver.insert_tenant
[LEAF] tenant_driver.TenantDriver.insert_usage_record
[LEAF] tenant_driver.TenantDriver.update_api_key_revoked
[LEAF] tenant_driver.TenantDriver.update_run_completed
[LEAF] tenant_driver.TenantDriver.update_tenant_plan
[LEAF] tenant_driver.TenantDriver.update_tenant_status
[LEAF] tenant_driver.TenantDriver.update_tenant_usage
[WRAPPER] tenant_driver.get_tenant_driver
[INTERNAL] tenant_engine.QuotaExceededError.__init__ → accounts_facade:AccountsFacade.__init__, billing_provider:MockBillingProvider.__init__, crm_validator_engine:ValidatorService.__init__, email_verification:EmailVerificationError.__init__, email_verification:EmailVerificationService.__init__, ...+8
[WRAPPER] tenant_engine.TenantEngine.__init__ → tenant_driver:get_tenant_driver
[SUPERSET] tenant_engine.TenantEngine._maybe_reset_daily_counter → tenant_driver:TenantDriver.update_tenant_usage
[SUPERSET] tenant_engine.TenantEngine.check_run_quota → tenant_driver:TenantDriver.count_running_runs, tenant_driver:TenantDriver.fetch_tenant_by_id, tenant_engine:TenantEngine._maybe_reset_daily_counter
[SUPERSET] tenant_engine.TenantEngine.check_token_quota → tenant_driver:TenantDriver.fetch_tenant_by_id
[SUPERSET] tenant_engine.TenantEngine.complete_run → tenant_driver:TenantDriver.fetch_run_by_id, tenant_driver:TenantDriver.fetch_tenant_by_id, tenant_driver:TenantDriver.update_run_completed, tenant_driver:TenantDriver.update_tenant_usage, tenant_engine:TenantEngine.record_usage
[CANONICAL] tenant_engine.TenantEngine.create_api_key → tenant_driver:TenantDriver.count_active_api_keys, tenant_driver:TenantDriver.fetch_tenant_by_id, tenant_driver:TenantDriver.insert_api_key, tenant_driver:TenantDriver.insert_audit_log
[WRAPPER] tenant_engine.TenantEngine.create_membership_with_default → accounts_facade_driver:AccountsFacadeDriver.insert_membership, tenant_driver:TenantDriver.insert_membership
[ENTRY] tenant_engine.TenantEngine.create_run → tenant_driver:TenantDriver.insert_run, tenant_engine:TenantEngine.check_run_quota, tenant_engine:TenantEngine.increment_usage
[ENTRY] tenant_engine.TenantEngine.create_tenant → tenant_driver:TenantDriver.fetch_tenant_by_slug, tenant_driver:TenantDriver.insert_tenant
[WRAPPER] tenant_engine.TenantEngine.get_tenant → tenant_driver:TenantDriver.fetch_tenant_by_id
[WRAPPER] tenant_engine.TenantEngine.get_tenant_by_slug → tenant_driver:TenantDriver.fetch_tenant_by_slug
[SUPERSET] tenant_engine.TenantEngine.get_usage_summary → tenant_driver:TenantDriver.fetch_usage_records
[INTERNAL] tenant_engine.TenantEngine.increment_usage → tenant_driver:TenantDriver.fetch_tenant_by_id, tenant_driver:TenantDriver.increment_tenant_usage, tenant_engine:TenantEngine._maybe_reset_daily_counter
[WRAPPER] tenant_engine.TenantEngine.list_api_keys → tenant_driver:TenantDriver.fetch_api_keys
[WRAPPER] tenant_engine.TenantEngine.list_runs → tenant_driver:TenantDriver.fetch_runs
[WRAPPER] tenant_engine.TenantEngine.record_usage → tenant_driver:TenantDriver.insert_usage_record
[ENTRY] tenant_engine.TenantEngine.revoke_api_key → tenant_driver:TenantDriver.fetch_api_key_by_id, tenant_driver:TenantDriver.insert_audit_log, tenant_driver:TenantDriver.update_api_key_revoked
[ENTRY] tenant_engine.TenantEngine.suspend → tenant_driver:TenantDriver.fetch_tenant_by_id, tenant_driver:TenantDriver.update_tenant_status
[ENTRY] tenant_engine.TenantEngine.update_plan → tenant_driver:TenantDriver.fetch_tenant_by_id, tenant_driver:TenantDriver.update_tenant_plan
[WRAPPER] tenant_engine.get_tenant_engine
[WRAPPER] user_write_driver.UserWriteDriver.__init__
[LEAF] user_write_driver.UserWriteDriver.create_user
[LEAF] user_write_driver.UserWriteDriver.update_user_login
[WRAPPER] user_write_driver.UserWriteDriver.user_to_dict
[WRAPPER] user_write_driver.get_user_write_driver
[WRAPPER] user_write_engine.UserWriteService.__init__ → user_write_driver:get_user_write_driver
[WRAPPER] user_write_engine.UserWriteService.create_user → user_write_driver:UserWriteDriver.create_user
[WRAPPER] user_write_engine.UserWriteService.update_user_login → user_write_driver:UserWriteDriver.update_user_login
[WRAPPER] user_write_engine.UserWriteService.user_to_dict → user_write_driver:UserWriteDriver.user_to_dict
[WRAPPER] validator_engine.ValidatorService.__init__
[LEAF] validator_engine.ValidatorService._build_reason
[INTERNAL] validator_engine.ValidatorService._calculate_confidence → crm_validator_engine:ValidatorService._get_capability_confidence, crm_validator_engine:ValidatorService._get_source_weight, validator_engine:ValidatorService._get_capability_confidence, validator_engine:ValidatorService._get_source_weight
[LEAF] validator_engine.ValidatorService._classify_issue_type
[LEAF] validator_engine.ValidatorService._classify_severity
[LEAF] validator_engine.ValidatorService._create_fallback_verdict
[LEAF] validator_engine.ValidatorService._determine_action
[INTERNAL] validator_engine.ValidatorService._do_validate → crm_validator_engine:ValidatorService._build_reason, crm_validator_engine:ValidatorService._calculate_confidence, crm_validator_engine:ValidatorService._classify_issue_type, crm_validator_engine:ValidatorService._classify_severity, crm_validator_engine:ValidatorService._determine_action, ...+15
[LEAF] validator_engine.ValidatorService._extract_capabilities
[LEAF] validator_engine.ValidatorService._extract_text
[WRAPPER] validator_engine.ValidatorService._find_severity_indicators
[LEAF] validator_engine.ValidatorService._get_capability_confidence
[LEAF] validator_engine.ValidatorService._get_source_weight
[ENTRY] validator_engine.ValidatorService.validate → crm_validator_engine:ValidatorService._create_fallback_verdict, crm_validator_engine:ValidatorService._do_validate, validator_engine:ValidatorService._create_fallback_verdict, validator_engine:ValidatorService._do_validate
```
