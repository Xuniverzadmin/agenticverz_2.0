# PR10_ACCOUNT_USERS_LIST_FACADE_ISSUE_LEDGER_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-10 backend vertical slice (`GET /cus/account/users/list`)
- Contract Source: `backend/app/hoc/docs/architecture/usecases/PR10_ACCOUNT_USERS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- PR Summary: `backend/app/hoc/docs/architecture/usecases/PR10_ACCOUNT_USERS_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issue Register
| Issue ID | Severity | Category | Status |
|---|---|---|---|
| PR10-AC-001 | High | Missing account users public list facade contract | Fixed |
| PR10-AC-002 | Medium | L6 users list ordering lacked explicit stable tie-break | Fixed |

## Detailed Finding
### PR10-AC-001 — `account_public.py` was scaffold-only (no enforceable users-list contract)
- Surface: `backend/app/hoc/api/cus/account/account_public.py`
- Symptom:
  - account domain had no concrete public users list facade endpoint; file contained scaffold TODO comments only.
- Risk:
  - frontend account/member pages cannot rely on a stable CUS users boundary and must bind to broader legacy route surfaces.
- Root cause:
  - PR-0 scaffolding created domain shell files, but no read vertical-slice behavior was implemented for account.

### PR10-AC-002 — L6 account users list ordering had no unique tie-break
- Surface: `backend/app/hoc/cus/account/L6_drivers/accounts_facade_driver.py`
- Symptom:
  - list query ordered by `email` only.
- Risk:
  - pagination order can drift when duplicate/similar sort keys are present.
- Root cause:
  - prior implementation did not append a unique deterministic final sort key.

## Fix Implementation
- Implemented read-only account users list facade endpoint:
  - `GET /cus/account/users/list`
  - file: `backend/app/hoc/api/cus/account/account_public.py`
- Enforced boundary rules:
  - strict allowlist (`role`, `status`, `limit`, `offset`)
  - enum and bounds validation
  - one registry dispatch to `account.query`
  - `as_of` explicit unsupported in PR-10
  - request/correlation id propagation via `meta`
- Determinism hardening in L6 list query:
  - updated ordering to `email asc, id asc`
  - file: `backend/app/hoc/cus/account/L6_drivers/accounts_facade_driver.py`
- Added acceptance tests:
  - `backend/tests/api/test_account_public_facade_pr10.py`

## Verification Evidence
Executed on 2026-02-16:

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_account_public_facade_pr10.py
# Result: PASS

PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
# Result: CLEAN (no violations)
```

## Determinism Impact
- Facade preserves backend list ordering and does not mutate ordering.
- L6 ordering now includes stable unique tie-break (`id asc`) after `email asc`.

## Residual Risks (Tracked)
- Account project/profile/billing facade slices remain on legacy routes; PR-10 intentionally scopes only users list summary surface.
