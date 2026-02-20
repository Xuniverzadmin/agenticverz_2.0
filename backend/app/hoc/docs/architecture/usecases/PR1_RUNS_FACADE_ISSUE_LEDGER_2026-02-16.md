# PR1_RUNS_FACADE_ISSUE_LEDGER_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-1 backend vertical slice (`GET /cus/activity/runs`)
- Contract Source: `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- PR Summary: `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issue Register
| Issue ID | Severity | Category | Status |
|---|---|---|---|
| PR1-RUNS-001 | High | Pagination contract drift | Fixed |

## Detailed Finding
### PR1-RUNS-001 — `has_more` contract drift at facade boundary
- Surface: `backend/app/hoc/api/cus/activity/runs_facade.py`
- Symptom:
  - Facade returned `has_more` from backend payload (`result.has_more`) instead of deriving from frozen PR-1 math.
- Violated contract clause:
  - Addendum Section 7 (`has_more = (offset + len(runs) < total)`).
- Root cause:
  - Boundary layer trusted upstream flag instead of enforcing deterministic contract at facade edge.
- Frontend risk if unresolved:
  - Paging controls can desync (`Next` disabled/enabled incorrectly), causing inconsistent list navigation and cache invalidation behavior.

## Fix Implementation
- Code fix:
  - `backend/app/hoc/api/cus/activity/runs_facade.py:336`
  - Changed `has_more` computation to:
    - `has_more = (offset + len(runs)) < total`
  - `next_offset` remains derived from computed `has_more`.
- Proof test added:
  - `backend/tests/api/test_runs_facade_pr1.py:275`
  - `test_has_more_derived_from_total_and_page_math` injects contradictory backend value (`has_more=False` with `total=2`, one returned row) and verifies facade returns `has_more=True` + `next_offset=1`.

## Verification Evidence
Executed on 2026-02-16:

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_runs_facade_pr1.py
# Result: 14 passed, 0 failed

PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
# Result: CLEAN (no violations)
```

## Determinism Impact
- Pagination determinism is now enforced at contract boundary and is independent of backend flag drift.
- Replay/read stability improves for frontend list consumers because page progression now depends only on `(offset, returned_rows_count, total)`.

## Residual Risks (Tracked)
- Exactness of `total` remains a backend/L4-L6 responsibility and should continue to be validated in integration/stagetest runs.
- Sorting guarantees (`started_at/completed_at + run_id tie-break`) rely on upstream query implementation and are validated by existing PR-1 test matrix.
