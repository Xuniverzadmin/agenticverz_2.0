# hoc_cus_account_L6_drivers_accounts_facade_driver

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/account/L6_drivers/accounts_facade_driver.py` |
| Layer | L6 — Domain Driver |
| Domain | account |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Accounts domain facade driver - pure data access — L6 DOES NOT COMMIT

## Intent

**Role:** Accounts domain facade driver - pure data access — L6 DOES NOT COMMIT
**Reference:** PIN-470, ACCOUNT_PHASE2.5_IMPLEMENTATION_PLAN.md
**Callers:** accounts_facade.py (L5), must own transaction boundary

## Purpose

Accounts Facade Driver (L6)

---

## Functions

### `get_accounts_facade_driver() -> AccountsFacadeDriver`
- **Async:** No
- **Docstring:** Get the singleton AccountsFacadeDriver instance.
- **Calls:** AccountsFacadeDriver

## Classes

### `TenantSnapshot`
- **Docstring:** Tenant data from DB for list view.
- **Class Variables:** id: str, name: str, slug: str, status: str, plan: str, created_at: datetime, updated_at: Optional[datetime]

### `TenantDetailSnapshot`
- **Docstring:** Detailed tenant data from DB.
- **Class Variables:** id: str, name: str, slug: str, status: str, plan: str, max_workers: int, max_runs_per_day: int, max_concurrent_runs: int, max_tokens_per_month: int, max_api_keys: int, runs_today: int, runs_this_month: int, tokens_this_month: int, onboarding_state: int, onboarding_complete: bool, created_at: datetime, updated_at: Optional[datetime]

### `UserSnapshot`
- **Docstring:** User data from DB for list view.
- **Class Variables:** id: str, email: str, name: Optional[str], status: str, role: str, created_at: datetime, last_login_at: Optional[datetime]

### `UserDetailSnapshot`
- **Docstring:** Detailed user data from DB.
- **Class Variables:** id: str, email: str, name: Optional[str], avatar_url: Optional[str], status: str, role: str, email_verified: bool, oauth_provider: Optional[str], membership_created_at: datetime, invited_by: Optional[str], can_manage_keys: bool, can_run_workers: bool, can_view_runs: bool, created_at: datetime, updated_at: Optional[datetime], last_login_at: Optional[datetime]

### `MembershipSnapshot`
- **Docstring:** Tenant membership data from DB.
- **Class Variables:** user_id: str, email: str, name: Optional[str], role: str, created_at: datetime

### `ProfileSnapshot`
- **Docstring:** User profile data from DB.
- **Class Variables:** user_id: str, email: str, name: Optional[str], avatar_url: Optional[str], tenant_id: str, tenant_name: Optional[str], role: str, created_at: datetime, preferences: Optional[dict[str, Any]]

### `SubscriptionSnapshot`
- **Docstring:** Subscription data from DB.
- **Class Variables:** plan: str, status: str, billing_period: str, current_period_start: Optional[datetime], current_period_end: Optional[datetime]

### `InvitationSnapshot`
- **Docstring:** Invitation data from DB.
- **Class Variables:** id: str, email: str, role: str, status: str, token_hash: str, invited_by: str, created_at: datetime, expires_at: datetime, accepted_at: Optional[datetime]

### `TicketSnapshot`
- **Docstring:** Support ticket data from DB.
- **Class Variables:** id: str, subject: str, description: str, category: str, priority: str, status: str, resolution: Optional[str], created_at: datetime, updated_at: datetime, resolved_at: Optional[datetime]

### `AccountsFacadeDriver`
- **Docstring:** L6 Driver for accounts domain data access.
- **Methods:** fetch_tenant, fetch_tenants, count_tenants, fetch_tenant_detail, fetch_users, count_users, fetch_user_detail, fetch_tenant_memberships, fetch_membership, fetch_membership_with_user, update_membership_role, delete_membership, fetch_profile, fetch_user_by_id, update_user_profile, fetch_subscription, insert_support_ticket, fetch_support_tickets, fetch_invitation_by_email, insert_invitation, fetch_invitations, fetch_invitation_by_id_and_token, fetch_user_by_email, insert_user, insert_membership, update_invitation_accepted, update_invitation_expired

## Attributes

- `_driver_instance: AccountsFacadeDriver | None` (line 929)
- `__all__` (line 940)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.tenant` |
| External | `__future__`, `sqlalchemy`, `sqlalchemy.ext.asyncio` |

## Callers

accounts_facade.py (L5), must own transaction boundary

## Export Contract

```yaml
exports:
  functions:
    - name: get_accounts_facade_driver
      signature: "get_accounts_facade_driver() -> AccountsFacadeDriver"
  classes:
    - name: TenantSnapshot
      methods: []
    - name: TenantDetailSnapshot
      methods: []
    - name: UserSnapshot
      methods: []
    - name: UserDetailSnapshot
      methods: []
    - name: MembershipSnapshot
      methods: []
    - name: ProfileSnapshot
      methods: []
    - name: SubscriptionSnapshot
      methods: []
    - name: InvitationSnapshot
      methods: []
    - name: TicketSnapshot
      methods: []
    - name: AccountsFacadeDriver
      methods: [fetch_tenant, fetch_tenants, count_tenants, fetch_tenant_detail, fetch_users, count_users, fetch_user_detail, fetch_tenant_memberships, fetch_membership, fetch_membership_with_user, update_membership_role, delete_membership, fetch_profile, fetch_user_by_id, update_user_profile, fetch_subscription, insert_support_ticket, fetch_support_tickets, fetch_invitation_by_email, insert_invitation, fetch_invitations, fetch_invitation_by_id_and_token, fetch_user_by_email, insert_user, insert_membership, update_invitation_accepted, update_invitation_expired]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
