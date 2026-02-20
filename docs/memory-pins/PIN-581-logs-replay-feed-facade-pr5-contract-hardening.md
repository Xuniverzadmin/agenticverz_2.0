# PIN-581: Logs Replay Feed Facade PR-5 Contract Hardening

## Metadata
- Date: 2026-02-16
- Category: Architecture / API Contract / Frontend Enablement
- Status: ✅ COMPLETE
- Scope: Backend PR-5 vertical slice (`/cus/logs/list`)

## Context
After PR-1 (runs), PR-2 (incidents), PR-3 (policies), and PR-4 (controls), logs domain still had scaffold-only public facade entry and no stable replay-feed list contract for frontend binding.

## Decision
Implement a read-only logs replay-feed public facade with strict boundary semantics:
- required `topic` (`llm_runs|system_records`)
- strict allowlist + unknown-param rejection
- single dispatch to `logs.query`
- deterministic pagination computed at facade boundary
- request/correlation id propagation in response meta
- explicit `as_of` unsupported in PR-5

Also patch deterministic ordering in L6 logs lists by adding unique tie-break keys.

## Implementation
- Endpoint and boundary logic:
  - `backend/app/hoc/api/cus/logs/logs_public.py`
- Deterministic L6 ordering tie-break:
  - `backend/app/hoc/cus/logs/L6_drivers/logs_domain_store.py`
- Acceptance tests:
  - `backend/tests/api/test_logs_public_facade_pr5.py`
- Contract + issue ledger:
  - `backend/app/hoc/docs/architecture/usecases/PR5_LOGS_REPLAY_FEED_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
  - `backend/app/hoc/docs/architecture/usecases/PR5_LOGS_REPLAY_FEED_FACADE_ISSUE_LEDGER_2026-02-16.md`
- PR notes:
  - `backend/app/hoc/docs/architecture/usecases/PR5_LOGS_REPLAY_FEED_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Verification
```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_logs_public_facade_pr5.py
PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
```

## Why This Matters
- Complements prior read slices with a logs replay feed needed for Replay-oriented frontend routes.
- Provides narrow, validated HTTP boundary over existing logs query operations.
- Hardens ordering determinism for stable server-side pagination behavior.
