# PR2_INCIDENTS_LIST_FACADE_ISSUE_LEDGER_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-2 backend vertical slice (`GET /cus/incidents/list`)
- Contract Source: `backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- PR Summary: `backend/app/hoc/docs/architecture/usecases/PR2_INCIDENTS_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issue Register
| Issue ID | Severity | Category | Status |
|---|---|---|---|
| PR2-INC-001 | High | Missing public facade contract surface | Fixed |

## Detailed Finding
### PR2-INC-001 — `incidents_public.py` was scaffold-only (no enforceable list contract)
- Surface: `backend/app/hoc/api/cus/incidents/incidents_public.py`
- Symptom:
  - domain had no dedicated public list facade endpoint; file contained only TODO scaffold comments.
- Risk:
  - frontend cannot anchor on a stable, thin boundary contract; callers would need to bind to broader legacy endpoints with mixed semantics.
- Root cause:
  - PR-0 scaffold created domain shells, but no vertical-slice implementation existed for incidents read list.

## Fix Implementation
- Implemented read-only list facade endpoint:
  - `GET /cus/incidents/list`
  - file: `backend/app/hoc/api/cus/incidents/incidents_public.py`
- Enforced boundary rules:
  - required `topic`
  - unknown-param rejection
  - topic-specific allowlists
  - one registry dispatch to `incidents.query`
  - derived pagination determinism (`has_more` and `next_offset` from page math)
  - request/correlation id propagation via `meta`
  - `as_of` explicit unsupported in PR-2
- Added acceptance tests:
  - `backend/tests/api/test_incidents_public_facade_pr2.py`

## Verification Evidence
Executed on 2026-02-16:

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_incidents_public_facade_pr2.py
# Result: 17 passed, 0 failed

PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
# Result: CLEAN (no violations)
```

## Determinism Impact
- Facade now guarantees deterministic paging decisions independent of backend `has_more` payload.
- Sorting controls are fixed per topic and not caller-controlled in PR-2.

## Residual Risks (Tracked)
- Upstream data ordering tie-break guarantees remain an L5/L6 responsibility and should continue to be monitored in integration tests.
