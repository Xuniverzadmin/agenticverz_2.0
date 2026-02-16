# PIN-578: Incidents List Facade PR-2 Contract Hardening

## Metadata
- Date: 2026-02-16
- Category: Architecture / API Contract / Frontend Enablement
- Status: ✅ COMPLETE
- Scope: Backend PR-2 vertical slice (`/cus/incidents/list`)

## Context
After PR-1 runs facade hardening, incidents domain still had only scaffold-level public facade entry and no stable list contract dedicated for frontend consumption.

## Decision
Implement a read-only incidents list public facade with strict boundary semantics:
- required `topic` (`active|resolved|historical`)
- strict topic-specific filter allowlists
- unknown-param rejection
- single dispatch to `incidents.query`
- deterministic pagination computed at facade boundary
- request/correlation id propagation in response meta

## Implementation
- Endpoint and boundary logic:
  - `backend/app/hoc/api/cus/incidents/incidents_public.py`
- Acceptance tests:
  - `backend/tests/api/test_incidents_public_facade_pr2.py`
- Contract + issue ledger:
  - `backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
  - `backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_ISSUE_LEDGER_2026-02-16.md`
- PR notes:
  - `backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`
- Frontend scaffold links:
  - `docs/architecture/frontend/FRONTEND_SCAFFOLD_CONTRACT_LINKS_PR1_PR2_2026-02-16.md`

## Verification
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_incidents_public_facade_pr2.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```
- Result snapshot: 17 tests passed; layer boundary check CLEAN.

## Why This Matters
- Gives frontend a stable incidents list contract without binding to larger legacy route surface.
- Preserves small, auditable PR increments and domain-by-domain rollout discipline.
