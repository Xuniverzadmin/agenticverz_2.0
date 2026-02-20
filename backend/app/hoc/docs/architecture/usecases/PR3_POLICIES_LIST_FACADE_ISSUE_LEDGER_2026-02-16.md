# PR3_POLICIES_LIST_FACADE_ISSUE_LEDGER_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-3 backend vertical slice (`GET /cus/policies/list`)
- Contract Source: `backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- PR Summary: `backend/app/hoc/docs/architecture/usecases/PR3_POLICIES_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issue Register
| Issue ID | Severity | Category | Status |
|---|---|---|---|
| PR3-POL-001 | High | Missing public facade list contract | Fixed |
| PR3-POL-002 | Medium | Deterministic tie-break missing in rules query order | Fixed |

## Detailed Finding
### PR3-POL-001 — `policies_public.py` was scaffold-only (no enforceable list contract)
- Surface: `backend/app/hoc/api/cus/policies/policies_public.py`
- Symptom:
  - domain had no dedicated public list facade endpoint; file contained only scaffold TODO comments.
- Risk:
  - frontend cannot anchor to a stable policies list contract and must bind to broader legacy routes with mixed semantics.
- Root cause:
  - PR-0 scaffolding created domain shell files, but no read vertical-slice behavior was implemented for policies.

### PR3-POL-002 — rules ordering lacked stable unique tie-break
- Surface: `backend/app/hoc/cus/policies/L6_drivers/policies_facade_driver.py`
- Symptom:
  - rules query ordered by `last_triggered_at desc nulls last, created_at desc` only.
- Risk:
  - equal timestamps can produce unstable ordering under offset pagination, causing nondeterministic page boundaries.
- Root cause:
  - ORDER BY clause did not include a unique, stable final sort key.

## Fix Implementation
- Implemented read-only list facade endpoint:
  - `GET /cus/policies/list`
  - file: `backend/app/hoc/api/cus/policies/policies_public.py`
- Enforced boundary rules:
  - required `topic`
  - unknown-param rejection
  - topic-specific allowlists
  - one registry dispatch to `policies.query`
  - derived pagination determinism (`has_more` and `next_offset` from page math)
  - request/correlation id propagation via `meta`
  - `as_of` explicit unsupported in PR-3
- Added deterministic ordering tie-break in L6 rules read path:
  - `ORDER BY ... PolicyRule.id.desc()`
  - file: `backend/app/hoc/cus/policies/L6_drivers/policies_facade_driver.py`
- Added acceptance tests:
  - `backend/tests/api/test_policies_public_facade_pr3.py`

## Verification Evidence
Executed on 2026-02-16:

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_policies_public_facade_pr3.py
# Result: PASS

PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
# Result: CLEAN (no violations)
```

## Determinism Impact
- Facade now guarantees deterministic paging decisions independent of backend `has_more` payload.
- Rules query now includes a stable unique tie-break (`rule_id`) at L6 ordering boundary.
- Facade preserves backend ordering exactly and does not re-sort in application layer.

## Residual Risks (Tracked)
- Cross-topic aggregation for policies remains out of scope for PR-3 and will require a separate discriminated response contract if introduced.
