# HOC_Auth_Seam_V1_Runtime_Validation_plan

**Created:** 2026-02-21 16:58:28 UTC
**Executor:** Claude
**Status:** DRAFT

## 1. Objective

- Primary outcome:
  - Validate that HOC in-house auth seam hardening is operationally safe and test-backed.
- Business/technical intent:
  - Ensure no accidental Clerk fallback, confirm provider observability, and verify minimal EdDSA/JWKS human-token path works end-to-end at provider layer.

## 2. Scope

- In scope:
  - Execute canonical test case:
    - `backend/app/hoc/docs/architecture/usecases/HOC_AUTH_SEAM_V1_TESTCASE_2026-02-21.md`
  - Run targeted auth seam tests and full auth seam packs in backend.
  - Validate policy behavior:
    - non-`hoc_identity` provider value emits warning in non-prod.
    - non-`hoc_identity` provider value fails fast in prod.
  - Validate HOC Identity verification path:
    - EdDSA token verification against static JWKS test fixture.
    - Clerk issuer rejection in gateway routing.
  - Validate observability surface:
    - `GET /hoc/api/auth/provider/status` test contract via TestClient.
  - Produce execution evidence in plan_implemented file.
- Out of scope:
  - Stagetest deployment.
  - Clerk module deletion across entire repository.
  - Full identity lifecycle implementation (`/hoc/api/auth/login|refresh|logout` business logic).

## 3. Assumptions and Constraints

- Assumptions:
  - Work is executed in `/root/agenticverz2.0`.
  - Python test dependencies are already available in backend environment.
- Constraints:
  - Do not modify locked design/plan docs beyond this execution report pack.
  - Keep changes and evidence scoped to auth seam validation only.
- Non-negotiables:
  - No force-push.
  - No unrelated file edits.
  - Record exact commands + outputs in implemented report.

## 4. Acceptance Criteria

1. Targeted critical tests pass:
   - `test_invalid_provider_emits_warning`
   - `test_invalid_provider_fails_fast_in_prod`
   - `test_verifies_token_via_static_jwks_file`
   - `test_clerk_issuer_rejected`
2. Provider status route test passes (`/hoc/api/auth/provider/status` returns 200 with `effective_provider=hoc_identity`).
3. Full auth seam packs pass:
   - `tests/auth/test_auth_provider_seam.py`
   - `tests/auth/test_auth_identity_routes.py`
4. Capability enforcer check on touched files has 0 blocking violations.
5. `HOC_Auth_Seam_V1_Runtime_Validation_plan_implemented.md` is fully populated with evidence.

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| T1 | Setup | Confirm branch/worktree hygiene and collect changed-file scope | TODO | `git status`, `git diff --name-only` output in implemented report | Must note unrelated dirty files but do not revert |
| T2 | Core Test Cases | Execute targeted auth test cases (warning/fail-fast/EdDSA/JWKS/issuer reject/provider status) | TODO | pytest outputs in implemented report | If any fail, fix within scope and rerun |
| T3 | Validation | Run full auth seam test pack + capability enforcer on touched files | TODO | pytest + enforcer outputs in implemented report | 0 blocking required |
| T4 | Documentation | Fill implemented report with results, deviations, blockers, and final verdict | TODO | `HOC_Auth_Seam_V1_Runtime_Validation_plan_implemented.md` | Include pass/fail matrix and next actions |

## 6. Execution Order

1. T1
2. T2
3. T3
4. T4

## 7. Verification Commands

```bash
set -euo pipefail
cd /root/agenticverz2.0

# T1: scope and hygiene
git status --short --branch
git diff --name-only

# T2: targeted auth seam tests (critical cases)
cd backend
PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py::TestProviderFactory::test_invalid_provider_emits_warning -q
PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py::TestProviderFactory::test_invalid_provider_fails_fast_in_prod -q
PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py::TestHocIdentityVerification::test_verifies_token_via_static_jwks_file -q
PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py::TestGatewayProviderIntegration::test_clerk_issuer_rejected -q
PYTHONPATH=. python3 -m pytest tests/auth/test_auth_identity_routes.py::TestScaffoldResponses::test_provider_status_returns_200 -q

# T3: full pack
PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py tests/auth/test_auth_identity_routes.py -q

# T3: capability gate (list exact touched files if adjusted)
cd /root/agenticverz2.0
python3 scripts/ops/capability_registry_enforcer.py check-pr --files \
  backend/app/auth/auth_provider.py \
  backend/app/auth/auth_provider_hoc_identity.py \
  backend/app/auth/gateway.py \
  backend/app/auth/tenant_auth.py \
  backend/app/hoc/api/auth/routes.py \
  backend/app/hoc/api/auth/schemas.py \
  backend/tests/auth/test_auth_provider_seam.py \
  backend/tests/auth/test_auth_identity_routes.py
```

## 8. Risks and Rollback

- Risks:
  - Environment-level auth config could cause expected fail-fast behavior in prod simulation tests.
  - Existing unrelated dirty files can confuse scope if not explicitly ignored.
- Rollback plan:
  - Revert only auth seam files changed in this effort if validation fails.
  - Keep docs-only changes isolated if code rollback is required.
  - Do not revert unrelated workspace changes.

## 9. Claude Fill Rules

1. Update `Status` for each task: `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record concrete evidence path per task (file path, test output doc, or artifact).
3. If blocked, include blocker reason and minimal next action.
4. Do not delete plan sections; append execution facts.
5. Return completed results in `HOC_Auth_Seam_V1_Runtime_Validation_plan_implemented.md`.
