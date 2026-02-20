# PR6_OVERVIEW_HIGHLIGHTS_FACADE_ISSUE_LEDGER_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-6 backend vertical slice (`GET /cus/overview/highlights`)
- Contract Source: `backend/app/hoc/docs/architecture/usecases/PR6_OVERVIEW_HIGHLIGHTS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- PR Summary: `backend/app/hoc/docs/architecture/usecases/PR6_OVERVIEW_HIGHLIGHTS_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issue Register
| Issue ID | Severity | Category | Status |
|---|---|---|---|
| PR6-OV-001 | High | Missing public highlights facade contract | Fixed |

## Detailed Finding
### PR6-OV-001 — `overview_public.py` was scaffold-only (no enforceable highlights contract)
- Surface: `backend/app/hoc/api/cus/overview/overview_public.py`
- Symptom:
  - domain had no dedicated public highlights facade endpoint; file contained only scaffold TODO comments.
- Risk:
  - frontend overview/dashboard cannot anchor on a stable summary boundary and must bind to broader legacy route surfaces.
- Root cause:
  - PR-0 scaffolding created domain shell files, but no read vertical-slice behavior was implemented for overview.

## Fix Implementation
- Implemented read-only highlights facade endpoint:
  - `GET /cus/overview/highlights`
  - file: `backend/app/hoc/api/cus/overview/overview_public.py`
- Enforced boundary rules:
  - no query params supported
  - unknown-param rejection
  - one registry dispatch to `overview.query`
  - `as_of` explicit unsupported in PR-6
  - request/correlation id propagation via `meta`
- Added acceptance tests:
  - `backend/tests/api/test_overview_public_facade_pr6.py`

## Verification Evidence
Executed on 2026-02-16:

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_overview_public_facade_pr6.py
# Result: PASS

PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
# Result: CLEAN (no violations)
```

## Determinism Impact
- Facade preserves backend `domain_counts` order and does not mutate ordering.
- Repeated calls with identical backend payload retain stable ordering and shape.

## Residual Risks (Tracked)
- Other overview projections (`decisions`, `costs`, `recovery-stats`) remain on legacy routes; PR-6 intentionally scopes only the highlights public slice.
