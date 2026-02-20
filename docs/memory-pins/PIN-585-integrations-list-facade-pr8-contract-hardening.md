# PIN-585: Integrations List Facade PR-8 Contract Hardening

## Metadata
- Date: 2026-02-16
- Category: Architecture / API Contract / Frontend Enablement
- Status: ✅ COMPLETE
- Scope: Backend PR-8 vertical slice (`/cus/integrations/list`)

## Context
After PR-1 through PR-7, integrations domain still had scaffold-only public facade entry and no stable list summary contract for frontend integrations surfaces.

## Decision
Implement a read-only integrations list public facade with strict boundary semantics:
- strict allowlist: `status`, `provider_type`, `limit`, `offset`
- unknown-param rejection
- enum + pagination bounds validation
- single dispatch to `integrations.query` (`method=list_integrations`)
- request/correlation id propagation in response meta
- explicit `as_of` unsupported in PR-8
- deterministic L6 ordering hardening (`created_at desc, id desc`)

## Implementation
- Endpoint and boundary logic:
  - `backend/app/hoc/api/cus/integrations/integrations_public.py`
- L6 deterministic ordering hardening:
  - `backend/app/hoc/cus/integrations/L6_drivers/cus_integration_driver.py`
- Acceptance tests:
  - `backend/tests/api/test_integrations_public_facade_pr8.py`
- Contract + issue ledger:
  - `backend/app/hoc/docs/architecture/usecases/PR8_INTEGRATIONS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
  - `backend/app/hoc/docs/architecture/usecases/PR8_INTEGRATIONS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`
- PR notes:
  - `backend/app/hoc/docs/architecture/usecases/PR8_INTEGRATIONS_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Verification
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_integrations_public_facade_pr8.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```

## Why This Matters
- Adds integrations list as a stable frontend-consumable CUS facade slice.
- Keeps frontend scaffold contracts narrow, explicit, and auditable.
- Preserves strict facade boundary discipline with one-dispatch runtime flow.
