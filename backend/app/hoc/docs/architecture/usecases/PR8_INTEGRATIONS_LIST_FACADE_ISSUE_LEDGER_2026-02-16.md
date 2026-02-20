# PR8_INTEGRATIONS_LIST_FACADE_ISSUE_LEDGER_2026-02-16

## Status
- Date: 2026-02-16
- Scope: PR-8 backend vertical slice (`GET /cus/integrations/list`)
- Contract Source: `backend/app/hoc/docs/architecture/usecases/PR8_INTEGRATIONS_LIST_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`
- PR Summary: `backend/app/hoc/docs/architecture/usecases/PR8_INTEGRATIONS_LIST_FACADE_PR_DESCRIPTION_2026-02-16.md`

## Issue Register
| Issue ID | Severity | Category | Status |
|---|---|---|---|
| PR8-INT-001 | High | Missing integrations public list facade contract | Fixed |
| PR8-INT-002 | Medium | L6 list ordering lacked explicit stable tie-break | Fixed |

## Detailed Finding
### PR8-INT-001 — `integrations_public.py` was scaffold-only (no enforceable list contract)
- Surface: `backend/app/hoc/api/cus/integrations/integrations_public.py`
- Symptom:
  - domain had no dedicated public integrations list facade endpoint; file contained scaffold TODO comments only.
- Risk:
  - frontend integrations page cannot rely on a stable CUS list boundary and must bind to broader legacy route surfaces.
- Root cause:
  - PR-0 scaffolding created domain shell files, but no read vertical-slice behavior was implemented for integrations.

### PR8-INT-002 — L6 integration list ordering had no unique tie-break
- Surface: `backend/app/hoc/cus/integrations/L6_drivers/cus_integration_driver.py`
- Symptom:
  - list query ordered by `created_at desc` only.
- Risk:
  - pagination order can drift when multiple rows share identical `created_at` values.
- Root cause:
  - prior implementation did not append a unique deterministic final sort key.

## Fix Implementation
- Implemented read-only integrations list facade endpoint:
  - `GET /cus/integrations/list`
  - file: `backend/app/hoc/api/cus/integrations/integrations_public.py`
- Enforced boundary rules:
  - strict allowlist (`status`, `provider_type`, `limit`, `offset`)
  - enum and bounds validation
  - one registry dispatch to `integrations.query`
  - `as_of` explicit unsupported in PR-8
  - request/correlation id propagation via `meta`
- Determinism hardening in L6 list query:
  - updated ordering to `created_at desc, id desc`
  - file: `backend/app/hoc/cus/integrations/L6_drivers/cus_integration_driver.py`
- Added acceptance tests:
  - `backend/tests/api/test_integrations_public_facade_pr8.py`

## Verification Evidence
Executed on 2026-02-16:

```bash
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest -q tests/api/test_integrations_public_facade_pr8.py
# Result: PASS

PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
# Result: CLEAN (no violations)
```

## Determinism Impact
- Facade preserves backend list ordering and does not mutate ordering.
- L6 ordering now includes stable unique tie-break (`id desc`) after `created_at desc`.

## Residual Risks (Tracked)
- Integrations detail/health/limits public facade slices remain on legacy routes; PR-8 intentionally scopes only list summary surface.
