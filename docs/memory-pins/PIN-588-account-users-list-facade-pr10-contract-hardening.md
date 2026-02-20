# PIN-588: Account Users List Facade PR-10 Contract Hardening

## Metadata
- Date: 2026-02-16
- Category: Architecture / API Contract / Frontend Enablement
- Status: ✅ COMPLETE
- Scope: Backend PR-10 vertical slice (`/cus/account/users/list`)

## Context
After PR-1 through PR-9, account domain still had scaffold-only public facade entry and no stable users-list contract for frontend member-management surfaces.

## Decision
Implement a read-only account users list public facade with strict boundary semantics:
- strict allowlist: `role`, `status`, `limit`, `offset`
- unknown-param rejection
- enum + pagination bounds validation
- single dispatch to `account.query` (`method=list_users`)
- request/correlation id propagation in response meta
- explicit `as_of` unsupported in PR-10
- deterministic L6 ordering hardening (`email asc, id asc`)

## Implementation
- Endpoint and boundary logic:
  - `backend/app/hoc/api/cus/account/account_public.py`
- L6 deterministic ordering hardening:
  - `backend/app/hoc/cus/account/L6_drivers/accounts_facade_driver.py`
- Acceptance tests:
  - `backend/tests/api/test_account_public_facade_pr10.py`
- Contract + issue ledger:
  - `backend/app/hoc/docs/architecture/usecases/PR10_ACCOUNT_USERS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
  - `backend/app/hoc/docs/architecture/usecases/PR10_ACCOUNT_USERS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`
- PR notes:
  - `backend/app/hoc/docs/architecture/usecases/PR10_ACCOUNT_USERS_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Verification
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_account_public_facade_pr10.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```

## Why This Matters
- Adds account users list as a stable frontend-consumable CUS facade slice.
- Keeps frontend scaffold contracts narrow, explicit, and auditable.
- Preserves strict facade boundary discipline with one-dispatch runtime flow.
