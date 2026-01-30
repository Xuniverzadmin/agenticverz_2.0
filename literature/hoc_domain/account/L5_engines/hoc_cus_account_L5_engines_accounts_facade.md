# hoc_cus_account_L5_engines_accounts_facade

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/account/L5_engines/accounts_facade.py` |
| Layer | L5 — Domain Engine |
| Domain | account |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Accounts domain facade - unified entry point for account management

## Intent

**Role:** Accounts domain facade - unified entry point for account management
**Reference:** PIN-470, Customer Console v1 Constitution, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
**Callers:** L2 accounts API (accounts.py)

## Purpose

Accounts Domain Facade (L5)

---

## Functions

### `get_accounts_facade() -> AccountsFacade`
- **Async:** No
- **Docstring:** Get the singleton AccountsFacade instance.
- **Calls:** AccountsFacade

## Classes

### `ProjectSummaryResult`
- **Docstring:** Project summary for list view.
- **Class Variables:** project_id: str, name: str, description: Optional[str], status: str, plan: str, created_at: datetime, updated_at: Optional[datetime]

### `ProjectsListResult`
- **Docstring:** Projects list response.
- **Class Variables:** items: list[ProjectSummaryResult], total: int, has_more: bool, filters_applied: dict[str, Any]

### `ProjectDetailResult`
- **Docstring:** Project detail response.
- **Class Variables:** project_id: str, name: str, slug: str, description: Optional[str], status: str, plan: str, max_workers: int, max_runs_per_day: int, max_concurrent_runs: int, max_tokens_per_month: int, max_api_keys: int, runs_today: int, runs_this_month: int, tokens_this_month: int, onboarding_state: int, onboarding_complete: bool, created_at: datetime, updated_at: Optional[datetime]

### `UserSummaryResult`
- **Docstring:** User summary for list view.
- **Class Variables:** user_id: str, email: str, name: Optional[str], role: str, status: str, created_at: datetime, last_login_at: Optional[datetime]

### `UsersListResult`
- **Docstring:** Users list response.
- **Class Variables:** items: list[UserSummaryResult], total: int, has_more: bool, filters_applied: dict[str, Any]

### `UserDetailResult`
- **Docstring:** User detail response.
- **Class Variables:** user_id: str, email: str, name: Optional[str], avatar_url: Optional[str], role: str, status: str, email_verified: bool, oauth_provider: Optional[str], membership_created_at: datetime, invited_by: Optional[str], can_manage_keys: bool, can_run_workers: bool, can_view_runs: bool, created_at: datetime, updated_at: Optional[datetime], last_login_at: Optional[datetime]

### `TenantUserResult`
- **Docstring:** User in tenant.
- **Class Variables:** user_id: str, email: str, name: Optional[str], role: str, joined_at: datetime

### `TenantUsersListResult`
- **Docstring:** List of tenant users.
- **Class Variables:** users: list[TenantUserResult], total: int

### `ProfileResult`
- **Docstring:** User profile response.
- **Class Variables:** user_id: str, email: str, name: Optional[str], avatar_url: Optional[str], tenant_id: str, tenant_name: Optional[str], role: str, created_at: datetime, preferences: Optional[dict[str, Any]]

### `ProfileUpdateResult`
- **Docstring:** Profile update response.
- **Class Variables:** user_id: str, email: str, display_name: Optional[str], timezone: Optional[str], preferences: dict[str, Any], updated_at: datetime

### `BillingSummaryResult`
- **Docstring:** Billing summary response.
- **Class Variables:** plan: str, status: str, billing_period: str, current_period_start: Optional[datetime], current_period_end: Optional[datetime], usage_this_period: dict[str, Any], next_invoice_date: Optional[datetime], max_runs_per_day: int, max_tokens_per_month: int, runs_this_month: int, tokens_this_month: int

### `InvoiceSummaryResult`
- **Docstring:** Invoice summary.
- **Class Variables:** invoice_id: str, period_start: datetime, period_end: datetime, amount_cents: int, status: str, description: str

### `InvoiceListResult`
- **Docstring:** Invoice list response.
- **Class Variables:** invoices: list[InvoiceSummaryResult], total: int, message: Optional[str]

### `SupportContactResult`
- **Docstring:** Support contact info.
- **Class Variables:** email: str, hours: str, response_time: str

### `SupportTicketResult`
- **Docstring:** Support ticket response.
- **Class Variables:** id: str, subject: str, description: str, category: str, priority: str, status: str, created_at: datetime, updated_at: datetime, resolution: Optional[str], resolved_at: Optional[datetime]

### `SupportTicketListResult`
- **Docstring:** Support ticket list response.
- **Class Variables:** tickets: list[SupportTicketResult], total: int

### `InvitationResult`
- **Docstring:** Invitation response.
- **Class Variables:** id: str, email: str, role: str, status: str, created_at: datetime, expires_at: datetime, invited_by: str

### `InvitationListResult`
- **Docstring:** Invitation list response.
- **Class Variables:** invitations: list[InvitationResult], total: int

### `AcceptInvitationResult`
- **Docstring:** Invitation acceptance result.
- **Class Variables:** success: bool, message: str, tenant_id: Optional[str], role: Optional[str]

### `AccountsErrorResult`
- **Docstring:** Error result for accounts operations.
- **Class Variables:** error: str, message: str, status_code: int

### `AccountsFacade`
- **Docstring:** Unified facade for all Accounts domain operations.
- **Methods:** __init__, list_projects, get_project_detail, list_users, get_user_detail, list_tenant_users, update_user_role, remove_user, get_profile, update_profile, get_billing_summary, get_billing_invoices, get_support_contact, create_support_ticket, list_support_tickets, invite_user, list_invitations, accept_invitation

## Attributes

- `_facade_instance: AccountsFacade | None` (line 1098)
- `__all__` (line 1109)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L6 Driver | `app.hoc.cus.account.L6_drivers.accounts_facade_driver` |
| External | `__future__`, `sqlalchemy.ext.asyncio` |

## Callers

L2 accounts API (accounts.py)

## Export Contract

```yaml
exports:
  functions:
    - name: get_accounts_facade
      signature: "get_accounts_facade() -> AccountsFacade"
  classes:
    - name: ProjectSummaryResult
      methods: []
    - name: ProjectsListResult
      methods: []
    - name: ProjectDetailResult
      methods: []
    - name: UserSummaryResult
      methods: []
    - name: UsersListResult
      methods: []
    - name: UserDetailResult
      methods: []
    - name: TenantUserResult
      methods: []
    - name: TenantUsersListResult
      methods: []
    - name: ProfileResult
      methods: []
    - name: ProfileUpdateResult
      methods: []
    - name: BillingSummaryResult
      methods: []
    - name: InvoiceSummaryResult
      methods: []
    - name: InvoiceListResult
      methods: []
    - name: SupportContactResult
      methods: []
    - name: SupportTicketResult
      methods: []
    - name: SupportTicketListResult
      methods: []
    - name: InvitationResult
      methods: []
    - name: InvitationListResult
      methods: []
    - name: AcceptInvitationResult
      methods: []
    - name: AccountsErrorResult
      methods: []
    - name: AccountsFacade
      methods: [list_projects, get_project_detail, list_users, get_user_detail, list_tenant_users, update_user_role, remove_user, get_profile, update_profile, get_billing_summary, get_billing_invoices, get_support_contact, create_support_ticket, list_support_tickets, invite_user, list_invitations, accept_invitation]
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
