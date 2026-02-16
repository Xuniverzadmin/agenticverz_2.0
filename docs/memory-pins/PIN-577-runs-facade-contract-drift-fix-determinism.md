# PIN-577: Runs Facade Contract Drift Fix (Deterministic Pagination)

## Metadata
- Date: 2026-02-16
- Category: Architecture / API Contract / Determinism
- Status: ✅ COMPLETE
- Scope: Backend PR-1 vertical slice (`/cus/activity/runs`)

## Context
PR-1 froze pagination semantics for runs facade at the boundary contract. During vertical-slice hardening, one drift was found between contract and implementation:
- facade trusted upstream `has_more` instead of deriving it from contract math.

## Decision
Enforce `has_more` deterministically in L2 boundary code:
- `has_more = (offset + len(runs) < total)`
- never trust backend-provided `has_more` in facade response.

## Implementation
- Fixed in `backend/app/hoc/api/cus/activity/runs_facade.py`.
- Added regression test in `backend/tests/api/test_runs_facade_pr1.py` to force mismatch and verify facade recomputation.
- Detailed record:
  - `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_ISSUE_LEDGER_2026-02-16.md`
- Contract anchor:
  - `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`

## Why It Matters
- Prevents frontend pagination drift (incorrect next-page affordance/state).
- Keeps API boundary deterministic even if upstream flags regress.
- Preserves replay/read stability for upcoming frontend scaffold work.

## Verification
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_runs_facade_pr1.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```
- Result snapshot: 14 tests passed; layer boundary check CLEAN.

## Follow-up Ritual (Locked)
For each future domain vertical slice:
1. Add contract addendum or reference an existing frozen contract.
2. Add issue ledger with root-cause + fix + evidence.
3. Add/refresh PR description links.
4. Add memory pin + index update.
5. Run deterministic record-quality check before commit.
