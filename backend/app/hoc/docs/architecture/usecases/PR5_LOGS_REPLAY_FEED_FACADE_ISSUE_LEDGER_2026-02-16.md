# PR5_LOGS_REPLAY_FEED_FACADE_ISSUE_LEDGER_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-5 backend vertical slice (`GET /cus/logs/list`)
- Contract Source: `backend/app/hoc/docs/architecture/usecases/PR5_LOGS_REPLAY_FEED_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- PR Summary: `backend/app/hoc/docs/architecture/usecases/PR5_LOGS_REPLAY_FEED_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issue Register
| Issue ID | Severity | Category | Status |
|---|---|---|---|
| PR5-LOG-001 | High | Missing public facade replay-feed contract | Fixed |
| PR5-LOG-002 | Medium | Deterministic tie-break missing in L6 list queries | Fixed |

## Detailed Finding
### PR5-LOG-001 — `logs_public.py` was scaffold-only (no enforceable replay-feed contract)
- Surface: `backend/app/hoc/api/cus/logs/logs_public.py`
- Symptom:
  - domain had no dedicated public list facade endpoint; file contained only scaffold TODO comments.
- Risk:
  - replay-oriented frontend surfaces cannot anchor on a stable logs feed contract and must bind to broader legacy routes with mixed semantics.
- Root cause:
  - PR-0 scaffolding created domain shell files, but no read vertical-slice behavior was implemented for logs.

### PR5-LOG-002 — list query ordering lacked explicit stable unique tie-break
- Surface: `backend/app/hoc/cus/logs/L6_drivers/logs_domain_store.py`
- Symptom:
  - list queries sorted by `created_at desc` only.
- Risk:
  - equal timestamps can produce unstable ordering under offset pagination.
- Root cause:
  - ORDER BY clauses did not include a unique stable final key.

## Fix Implementation
- Implemented read-only replay-feed list facade endpoint:
  - `GET /cus/logs/list`
  - file: `backend/app/hoc/api/cus/logs/logs_public.py`
- Enforced boundary rules:
  - required `topic`
  - unknown-param rejection
  - one registry dispatch to `logs.query`
  - derived pagination determinism (`has_more` and `next_offset` from page math)
  - request/correlation id propagation via `meta`
  - `as_of` explicit unsupported in PR-5
- Added deterministic ordering tie-breaks in L6:
  - `LLMRunRecord.created_at desc, LLMRunRecord.id desc`
  - `SystemRecord.created_at desc, SystemRecord.id desc`
  - file: `backend/app/hoc/cus/logs/L6_drivers/logs_domain_store.py`
- Added acceptance tests:
  - `backend/tests/api/test_logs_public_facade_pr5.py`

## Verification Evidence
Executed on 2026-02-16:

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_logs_public_facade_pr5.py
# Result: PASS

PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
# Result: CLEAN (no violations)
```

## Determinism Impact
- Facade now guarantees deterministic paging decisions at boundary level.
- Logs list queries now include stable tie-break (`id`) after `created_at` sort.
- Facade preserves backend order exactly and does not re-sort in application layer.

## Residual Risks (Tracked)
- Broader logs endpoints (`traces`, `guard_logs`, `tenants`) remain active; PR-5 intentionally scopes only the public replay-feed list surface.
