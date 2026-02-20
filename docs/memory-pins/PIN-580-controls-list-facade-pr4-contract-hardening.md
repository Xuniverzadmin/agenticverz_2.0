# PIN-580: Controls List Facade PR-4 Contract Hardening

## Metadata
- Date: 2026-02-16
- Category: Architecture / API Contract / Frontend Enablement
- Status: ✅ COMPLETE
- Scope: Backend PR-4 vertical slice (`/cus/controls/list`)

## Context
After PR-1 (runs), PR-2 (incidents), and PR-3 (policies), controls domain still had scaffold-only public facade entry and no stable controls-list contract for frontend binding.

## Decision
Implement a read-only controls list public facade with strict boundary semantics:
- required `topic` (`all|enabled|disabled|auto`)
- strict allowlist + enum validation (`control_type`)
- unknown-param rejection
- single dispatch to `controls.query`
- deterministic pagination computed at facade boundary
- request/correlation id propagation in response meta
- explicit `as_of` unsupported in PR-4

Also patch controls list internals with explicit deterministic tie-break and a dedicated paged-result method that provides exact `total` in one call.

## Implementation
- Endpoint and boundary logic:
  - `backend/app/hoc/api/cus/controls/controls_public.py`
- L5/L4 paging support and ordering determinism:
  - `backend/app/hoc/cus/controls/L5_engines/controls_facade.py`
  - `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/controls_handler.py`
- Acceptance tests:
  - `backend/tests/api/test_controls_public_facade_pr4.py`
- Contract + issue ledger:
  - `backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
  - `backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`
- PR notes:
  - `backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Verification
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_controls_public_facade_pr4.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```

## Why This Matters
- Completes a fourth domain-aligned read facade slice needed for frontend scaffold planning.
- Reduces contract ambiguity by exposing a narrow, validated controls list surface.
- Preserves deterministic pagination behavior with explicit stable ordering and one-dispatch contract semantics.
