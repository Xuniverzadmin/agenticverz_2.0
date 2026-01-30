# hoc_models_tenant

| Field | Value |
|-------|-------|
| Path | `backend/app/models/tenant.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Tenant data models

## Intent

**Role:** Tenant data models
**Reference:** Tenant System
**Callers:** tenant services

## Purpose

Tenant, User, and Multi-Tenancy Models (M21)

---

## Functions

### `utc_now() -> datetime`
- **Async:** No
- **Docstring:** Return current UTC time as a naive datetime (no timezone info).  PostgreSQL TIMESTAMP WITHOUT TIME ZONE columns require naive datetimes.
- **Calls:** utcnow

### `generate_uuid() -> str`
- **Async:** No
- **Docstring:** _None_
- **Calls:** str, uuid4

## Classes

### `Tenant(SQLModel)`
- **Docstring:** Organization/Tenant model for multi-tenancy.
- **Methods:** can_create_run, can_use_tokens, increment_usage, tier, tier_marketing_name, retention_days, has_feature, get_available_features, onboarding, has_completed_onboarding, can_access_endpoint
- **Class Variables:** id: str, name: str, slug: str, clerk_org_id: Optional[str], plan: str, billing_email: Optional[str], stripe_customer_id: Optional[str], max_workers: int, max_runs_per_day: int, max_concurrent_runs: int, max_tokens_per_month: int, max_api_keys: int, runs_today: int, runs_this_month: int, tokens_this_month: int, last_run_reset_at: Optional[datetime], status: str, suspended_reason: Optional[str], onboarding_state: int, created_at: datetime, updated_at: datetime, is_synthetic: bool, synthetic_scenario_id: Optional[str]

### `User(SQLModel)`
- **Docstring:** User account - supports OAuth (Google/Azure) and email signup.
- **Methods:** get_preferences, set_preferences
- **Class Variables:** id: str, clerk_user_id: str, email: str, name: Optional[str], avatar_url: Optional[str], oauth_provider: Optional[str], oauth_provider_id: Optional[str], email_verified: bool, email_verified_at: Optional[datetime], default_tenant_id: Optional[str], status: str, preferences_json: Optional[str], created_at: datetime, updated_at: datetime, last_login_at: Optional[datetime]

### `TenantMembership(SQLModel)`
- **Docstring:** User membership in a tenant with role.
- **Methods:** can_manage_keys, can_run_workers, can_view_runs, can_manage_users, can_change_roles
- **Class Variables:** id: str, tenant_id: str, user_id: str, role: str, created_at: datetime, invited_by: Optional[str]

### `Invitation(SQLModel)`
- **Docstring:** User invitation to join a tenant.
- **Methods:** generate_token, is_valid
- **Class Variables:** id: str, tenant_id: str, email: str, role: str, status: str, token_hash: str, invited_by: str, created_at: datetime, expires_at: datetime, accepted_at: Optional[datetime]

### `APIKey(SQLModel)`
- **Docstring:** API key for programmatic access.
- **Methods:** generate_key, hash_key, is_valid, record_usage
- **Class Variables:** id: str, tenant_id: str, user_id: Optional[str], name: str, key_prefix: str, key_hash: str, permissions_json: Optional[str], allowed_workers_json: Optional[str], rate_limit_rpm: Optional[int], max_concurrent_runs: Optional[int], status: str, expires_at: Optional[datetime], revoked_at: Optional[datetime], revoked_reason: Optional[str], is_frozen: bool, frozen_at: Optional[datetime], last_used_at: Optional[datetime], total_requests: int, created_at: datetime, is_synthetic: bool, synthetic_scenario_id: Optional[str]

### `Subscription(SQLModel)`
- **Docstring:** Billing subscription for a tenant.
- **Class Variables:** id: str, tenant_id: str, plan: str, status: str, stripe_subscription_id: Optional[str], stripe_price_id: Optional[str], billing_period: str, current_period_start: Optional[datetime], current_period_end: Optional[datetime], trial_ends_at: Optional[datetime], canceled_at: Optional[datetime], cancel_at_period_end: bool, created_at: datetime, updated_at: datetime

### `UsageRecord(SQLModel)`
- **Docstring:** Usage metering for billing.
- **Class Variables:** id: str, tenant_id: str, meter_name: str, amount: int, unit: str, period_start: datetime, period_end: datetime, worker_id: Optional[str], api_key_id: Optional[str], metadata_json: Optional[str], recorded_at: datetime

### `WorkerRegistry(SQLModel)`
- **Docstring:** Registry of available workers.
- **Class Variables:** id: str, name: str, description: Optional[str], version: str, status: str, is_public: bool, moats_json: Optional[str], default_config_json: Optional[str], input_schema_json: Optional[str], output_schema_json: Optional[str], tokens_per_run_estimate: Optional[int], cost_per_run_cents: Optional[int], created_at: datetime, updated_at: datetime

### `WorkerConfig(SQLModel)`
- **Docstring:** Per-tenant worker configuration.
- **Class Variables:** id: str, tenant_id: str, worker_id: str, enabled: bool, config_json: Optional[str], brand_json: Optional[str], max_runs_per_day: Optional[int], max_tokens_per_run: Optional[int], created_at: datetime, updated_at: datetime

### `WorkerRun(SQLModel)`
- **Docstring:** Worker execution run with tenant isolation.
- **Class Variables:** id: str, tenant_id: str, worker_id: str, api_key_id: Optional[str], user_id: Optional[str], task: str, input_json: Optional[str], status: str, success: Optional[bool], error: Optional[str], output_json: Optional[str], replay_token_json: Optional[str], total_tokens: Optional[int], total_latency_ms: Optional[int], stages_completed: Optional[int], recoveries: int, policy_violations: int, cost_cents: Optional[int], parent_run_id: Optional[str], attempt: int, is_retry: bool, created_at: datetime, started_at: Optional[datetime], completed_at: Optional[datetime], is_synthetic: bool, synthetic_scenario_id: Optional[str]

### `SupportTicket(SQLModel)`
- **Docstring:** Support ticket for customer issues - feeds into CRM workflow.
- **Class Variables:** id: str, tenant_id: str, user_id: str, subject: str, description: str, category: str, priority: str, status: str, resolution: Optional[str], issue_event_id: Optional[str], created_at: datetime, updated_at: datetime, resolved_at: Optional[datetime]

### `AuditLog(SQLModel)`
- **Docstring:** Comprehensive audit log for compliance.
- **Class Variables:** id: str, tenant_id: Optional[str], user_id: Optional[str], api_key_id: Optional[str], action: str, resource_type: str, resource_id: Optional[str], ip_address: Optional[str], user_agent: Optional[str], request_id: Optional[str], old_value_json: Optional[str], new_value_json: Optional[str], created_at: datetime

### `FounderAction(SQLModel)`
- **Docstring:** Immutable record of founder actions on tenants/keys/incidents.
- **Methods:** is_reversal
- **Class Variables:** id: str, action_type: str, target_type: str, target_id: str, target_name: Optional[str], reason_code: str, reason_note: Optional[str], source_incident_id: Optional[str], founder_id: str, founder_email: str, mfa_verified: bool, applied_at: datetime, reversed_at: Optional[datetime], reversed_by_action_id: Optional[str], is_active: bool, is_reversible: bool

## Attributes

- `PLAN_QUOTAS` (line 188)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `auth.onboarding_state`, `auth.tier_gating`, `sqlmodel` |

## Callers

tenant services

## Export Contract

```yaml
exports:
  functions:
    - name: utc_now
      signature: "utc_now() -> datetime"
    - name: generate_uuid
      signature: "generate_uuid() -> str"
  classes:
    - name: Tenant
      methods: [can_create_run, can_use_tokens, increment_usage, tier, tier_marketing_name, retention_days, has_feature, get_available_features, onboarding, has_completed_onboarding, can_access_endpoint]
    - name: User
      methods: [get_preferences, set_preferences]
    - name: TenantMembership
      methods: [can_manage_keys, can_run_workers, can_view_runs, can_manage_users, can_change_roles]
    - name: Invitation
      methods: [generate_token, is_valid]
    - name: APIKey
      methods: [generate_key, hash_key, is_valid, record_usage]
    - name: Subscription
      methods: []
    - name: UsageRecord
      methods: []
    - name: WorkerRegistry
      methods: []
    - name: WorkerConfig
      methods: []
    - name: WorkerRun
      methods: []
    - name: SupportTicket
      methods: []
    - name: AuditLog
      methods: []
    - name: FounderAction
      methods: [is_reversal]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
