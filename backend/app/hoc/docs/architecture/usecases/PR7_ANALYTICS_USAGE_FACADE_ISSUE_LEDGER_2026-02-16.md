# PR7_ANALYTICS_USAGE_FACADE_ISSUE_LEDGER_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-7 backend vertical slice (`GET /cus/analytics/statistics/usage`)
- Contract Source: `backend/app/hoc/docs/architecture/usecases/PR7_ANALYTICS_USAGE_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- PR Summary: `backend/app/hoc/docs/architecture/usecases/PR7_ANALYTICS_USAGE_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issue Register
| Issue ID | Severity | Category | Status |
|---|---|---|---|
| PR7-AN-001 | High | Missing analytics usage public facade contract | Fixed |

## Detailed Finding
### PR7-AN-001 — `analytics_public.py` was scaffold-only (no enforceable usage contract)
- Surface: `backend/app/hoc/api/cus/analytics/analytics_public.py`
- Symptom:
  - domain had no dedicated public usage facade endpoint; file contained scaffold TODO comments only.
- Risk:
  - frontend analytics widgets cannot rely on a stable CUS analytics usage boundary and must bind to broader legacy route surfaces.
- Root cause:
  - PR-0 scaffolding created domain shell files, but no read vertical-slice behavior was implemented for analytics.

## Fix Implementation
- Implemented read-only analytics usage facade endpoint:
  - `GET /cus/analytics/statistics/usage`
  - file: `backend/app/hoc/api/cus/analytics/analytics_public.py`
- Enforced boundary rules:
  - strict allowlist (`from`, `to`, `resolution`, `scope`)
  - required timezone-aware timestamps for `from`/`to`
  - strict 90-day maximum window
  - one registry dispatch to `analytics.query`
  - `as_of` explicit unsupported in PR-7
  - request/correlation id propagation via `meta`
- Added acceptance tests:
  - `backend/tests/api/test_analytics_public_facade_pr7.py`

## Verification Evidence
Executed on 2026-02-16:

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_analytics_public_facade_pr7.py
# Result: PASS

PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
# Result: CLEAN (no violations)
```

## Determinism Impact
- Facade preserves backend usage `series` ordering and does not mutate ordering.
- Repeated calls with identical backend payload retain stable ordering and shape.

## Residual Risks (Tracked)
- Cost statistics and export surfaces remain on legacy analytics routes; PR-7 intentionally scopes only usage statistics public slice.
