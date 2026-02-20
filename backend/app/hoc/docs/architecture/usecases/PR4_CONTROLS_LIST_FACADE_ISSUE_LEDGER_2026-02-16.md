# PR4_CONTROLS_LIST_FACADE_ISSUE_LEDGER_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-4 backend vertical slice (`GET /cus/controls/list`)
- Contract Source: `backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- PR Summary: `backend/app/hoc/docs/architecture/usecases/PR4_CONTROLS_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issue Register
| Issue ID | Severity | Category | Status |
|---|---|---|---|
| PR4-CTRL-001 | High | Missing public facade list contract | Fixed |
| PR4-CTRL-002 | Medium | No exact total contract from existing list method | Fixed |
| PR4-CTRL-003 | Medium | Deterministic tie-break not explicit for controls ordering | Fixed |

## Detailed Finding
### PR4-CTRL-001 — `controls_public.py` was scaffold-only (no enforceable list contract)
- Surface: `backend/app/hoc/api/cus/controls/controls_public.py`
- Symptom:
  - domain had no dedicated public list facade endpoint; file contained only scaffold TODO comments.
- Risk:
  - frontend cannot anchor to a stable controls list contract and must bind to broader legacy routes with mixed semantics.
- Root cause:
  - PR-0 scaffolding created domain shell files, but no read vertical-slice behavior was implemented for controls.

### PR4-CTRL-002 — existing `list_controls` call shape could not provide exact total for paging
- Surface: `backend/app/hoc/cus/controls/L5_engines/controls_facade.py`
- Symptom:
  - existing `list_controls` returns sliced list only.
- Risk:
  - facade paging contract cannot reliably expose exact `total` and deterministic `has_more` using one dispatch.
- Root cause:
  - legacy method focused on list retrieval, not explicit page metadata contract.

### PR4-CTRL-003 — controls ordering tie-break not explicit in list logic
- Surface: `backend/app/hoc/cus/controls/L5_engines/controls_facade.py`
- Symptom:
  - list ordering used `name` only.
- Risk:
  - equal names could produce unstable order in pagination boundaries.
- Root cause:
  - sorting did not include a stable unique secondary key.

## Fix Implementation
- Implemented read-only list facade endpoint:
  - `GET /cus/controls/list`
  - file: `backend/app/hoc/api/cus/controls/controls_public.py`
- Enforced boundary rules:
  - required `topic`
  - unknown-param rejection
  - strict enum parsing for `control_type`
  - one registry dispatch to `controls.query`
  - derived pagination determinism (`has_more` and `next_offset` from page math)
  - request/correlation id propagation via `meta`
  - `as_of` explicit unsupported in PR-4
- Added L5 page result contract and deterministic sort tie-break:
  - new `list_controls_page(...)` method returning `items`, `total`, `generated_at`
  - explicit sort tuple `(name, id)`
  - file: `backend/app/hoc/cus/controls/L5_engines/controls_facade.py`
- Added L4 dispatch map support for the new method:
  - `list_controls_page` in `ControlsQueryHandler`
  - file: `backend/app/hoc/cus/hoc_spine/orchestrator/handlers/controls_handler.py`
- Added acceptance tests:
  - `backend/tests/api/test_controls_public_facade_pr4.py`

## Verification Evidence
Executed on 2026-02-16:

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_controls_public_facade_pr4.py
# Result: PASS

PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
# Result: CLEAN (no violations)
```

## Determinism Impact
- Facade now guarantees deterministic paging decisions via exact total and page-math derivation.
- Controls list ordering now has an explicit stable tie-break (`id`) after primary key (`name`).
- Facade preserves backend ordering exactly and does not re-sort in application layer.

## Residual Risks (Tracked)
- Controls domain still includes legacy `/controls` routes for broad compatibility; PR-4 intentionally scopes only the public list facade surface.
