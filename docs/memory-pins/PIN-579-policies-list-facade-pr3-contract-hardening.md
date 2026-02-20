# PIN-579: Policies List Facade PR-3 Contract Hardening

## Metadata
- Date: 2026-02-16
- Category: Architecture / API Contract / Frontend Enablement
- Status: ✅ COMPLETE
- Scope: Backend PR-3 vertical slice (`/cus/policies/list`)

## Context
After PR-1 (runs) and PR-2 (incidents), policies domain still had scaffold-only public facade entry and no stable rules-list contract for frontend binding.

## Decision
Implement a read-only policies list public facade with strict boundary semantics:
- required `topic` (`active|retired`)
- strict topic-specific filter allowlists
- unknown-param rejection
- single dispatch to `policies.query`
- deterministic pagination computed at facade boundary
- request/correlation id propagation in response meta
- explicit `as_of` unsupported in PR-3

Also patch deterministic ordering at L6 by adding a unique tie-break key to rules list query ordering.

## Implementation
- Endpoint and boundary logic:
  - `backend/app/hoc/api/cus/policies/policies_public.py`
- Deterministic L6 ordering tie-break:
  - `backend/app/hoc/cus/policies/L6_drivers/policies_facade_driver.py`
- Acceptance tests:
  - `backend/tests/api/test_policies_public_facade_pr3.py`
- Contract + issue ledger:
  - `backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
  - `backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`
- PR notes:
  - `backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Verification
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_policies_public_facade_pr3.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```

## Why This Matters
- Completes a third domain-aligned read facade slice needed for frontend scaffold planning.
- Reduces contract ambiguity by exposing a narrow, validated list surface.
- Improves pagination determinism by hardening sort tie-break behavior in the backend read path.
