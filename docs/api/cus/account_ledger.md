# CUS Domain Ledger: account

**Generated:** 2026-02-21T07:54:56.667404+00:00
**Total endpoints:** 32
**Unique method+path:** 32

| Method | Path | Operation | Summary |
|--------|------|-----------|---------|
| GET | /hoc/api/cus/account/users/list | list_account_users_public |  |
| GET | /hoc/api/cus/accounts/billing | get_billing_summary | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| GET | /hoc/api/cus/accounts/billing/invoices | get_billing_invoices | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| GET | /hoc/api/cus/accounts/invitations | list_invitations | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| POST | /hoc/api/cus/accounts/invitations/{invitation_id}/accept | accept_invitation | Accept an invitation to join a tenant. |
| GET | /hoc/api/cus/accounts/profile | get_profile | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| PUT | /hoc/api/cus/accounts/profile | update_profile | WRITE customer facade - delegates to L4 AccountsFacade. |
| GET | /hoc/api/cus/accounts/projects | list_projects | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| POST | /hoc/api/cus/accounts/projects | create_project | Create a new project. Delegates to L4 AccountsFacade. |
| GET | /hoc/api/cus/accounts/projects/{project_id} | get_project_detail | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| GET | /hoc/api/cus/accounts/support | get_support_contact | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| GET | /hoc/api/cus/accounts/support/tickets | list_support_tickets | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| POST | /hoc/api/cus/accounts/support/tickets | create_support_ticket | WRITE customer facade - delegates to L4 AccountsFacade. |
| GET | /hoc/api/cus/accounts/tenant/users | list_tenant_users | List users in the current tenant. |
| GET | /hoc/api/cus/accounts/users | list_users | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| POST | /hoc/api/cus/accounts/users/invite | invite_user | WRITE customer facade - delegates to L4 AccountsFacade. |
| DELETE | /hoc/api/cus/accounts/users/{user_id} | remove_user | Remove a user from the tenant. |
| GET | /hoc/api/cus/accounts/users/{user_id} | get_user_detail | READ-ONLY customer facade - delegates to L4 AccountsFacade. |
| PUT | /hoc/api/cus/accounts/users/{user_id}/role | update_user_role | Update a user's role in the tenant. |
| GET | /hoc/api/cus/memory/pins | list_pins | List memory pins for a tenant. |
| POST | /hoc/api/cus/memory/pins | create_or_upsert_pin | Create or upsert a memory pin. |
| POST | /hoc/api/cus/memory/pins/cleanup | cleanup_expired_pins | Clean up expired memory pins. |
| DELETE | /hoc/api/cus/memory/pins/{key} | delete_pin | Delete a memory pin by key. |
| GET | /hoc/api/cus/memory/pins/{key} | get_pin | Get a memory pin by key. |
| GET | /hoc/api/cus/tenant | get_current_tenant | Get information about the current tenant (from API key). |
| GET | /hoc/api/cus/tenant/api-keys | list_api_keys | List all API keys for the current tenant. |
| POST | /hoc/api/cus/tenant/api-keys | create_api_key | Create a new API key for the current tenant. |
| DELETE | /hoc/api/cus/tenant/api-keys/{key_id} | revoke_api_key | Revoke an API key. |
| GET | /hoc/api/cus/tenant/health | tenant_health | Health check for tenant system. |
| GET | /hoc/api/cus/tenant/quota/runs | check_run_quota | Check if the tenant can create a new run. |
| GET | /hoc/api/cus/tenant/quota/tokens | check_token_quota | Check if the tenant has token budget for an operation. |
| GET | /hoc/api/cus/tenant/usage | get_tenant_usage | Get usage summary for the current tenant. |
