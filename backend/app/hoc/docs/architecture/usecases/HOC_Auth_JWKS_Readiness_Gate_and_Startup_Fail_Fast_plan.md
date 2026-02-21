# HOC_Auth_JWKS_Readiness_Gate_and_Startup_Fail_Fast_plan

**Created:** 2026-02-21 18:39:48 UTC
**Executor:** Claude
**Status:** READY_FOR_EXECUTION

## 1. Objective

- Primary outcome: enforce deterministic Clove JWKS readiness gating so misconfigured auth never starts silently in production and is observable via a stable status API.
- Business/technical intent: remove ambiguity around `401/503` auth failures by making readiness explicit (`configured` + check details), boot behavior deterministic (fail-fast policy), and runtime diagnostics queryable.

## 2. Scope

- In scope:
- Implement hard readiness checks for Clove provider configuration (issuer, audience, JWKS source).
- Extend provider status contract with explicit readiness check list and aggregate status.
- Enforce startup fail-fast semantics for production when Clove readiness is not met.
- Add non-prod strict mode switch for startup gate (opt-in), preserving developer flexibility.
- Decide and implement `/hoc/api/auth/provider/status` gateway exposure policy for browser troubleshooting.
- Add/adjust tests for startup gating, status contract, and route behavior.
- Run capability and test gates; update plan_implemented evidence.

- Out of scope:
- Implementing full auth lifecycle endpoints (`login`, `refresh`, `logout`, `switch-tenant`) beyond scaffold.
- Reworking RBAC architecture or full auth replacement waves (Pre-Wave0 T1-T8).
- Legacy repo-wide CI debt outside touched files.

## 3. Assumptions and Constraints

- Assumptions:
- Clove is canonical provider (`AUTH_PROVIDER=clove` effective policy).
- JWKS verification remains EdDSA/Ed25519 and existing token claim contract remains unchanged.
- Existing auth middleware order is preserved (gateway -> onboarding -> RBAC -> veil).

- Constraints:
- No force-push, no amend, no unrelated-file edits.
- Preserve machine auth (`X-AOS-Key`) behavior.
- Keep changes in `hoc/*` and auth runtime surfaces only.
- Keep API response structures backward-compatible where possible; additive fields preferred.

- Non-negotiables:
- Production must fail startup on unconfigured Clove readiness.
- Status endpoint must expose actionable diagnostics without leaking secrets.
- Capability enforcer must remain 0 blocking on changed files.

## 4. Acceptance Criteria

1. `CloveHumanAuthProvider` publishes deterministic readiness checks with pass/fail per required input.
2. `get_human_auth_provider_status()` includes readiness aggregate and check details.
3. In `prod`/`production`, startup fails when Clove readiness is not met (clear fatal log + raised exception).
4. In non-prod, startup behavior is controlled by explicit strict flag (default non-fatal unless strict enabled).
5. `/hoc/api/auth/provider/status` accessibility policy is explicit and implemented (not implicit/accidental).
6. Status endpoint returns deterministic payload fields: `requested_provider`, `effective_provider`, `canonical_provider`, `configured`, `readiness`, `provider_diagnostics`, `deprecation`.
7. Existing seam tests continue passing and new gate tests pass.
8. `python3 scripts/ops/capability_registry_enforcer.py check-pr --files <changed_files>` returns 0 blocking.
9. `plan_implemented.md` is fully updated with exact commands, outputs, and blockers (if any).

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| T1 | Baseline | Re-audit current behavior and lock exact gaps before edits (`provider/status`, startup, gateway policy/public-path). | TODO | backend/app/hoc/docs/architecture/usecases/HOC_Auth_JWKS_Readiness_Gate_and_Startup_Fail_Fast_plan_implemented.md | Include file:line references and current runtime semantics. |
| T2 | Readiness Contract | Implement provider readiness hard checks + additive status schema/response contract. | TODO | backend/app/auth/auth_provider_clove.py, backend/app/auth/auth_provider.py, backend/app/hoc/api/auth/schemas.py | No secret leakage in diagnostics. |
| T3 | Startup Gate | Implement startup fail-fast policy for prod and strict-mode flag for non-prod. | TODO | backend/app/main.py, backend/app/hoc/cus/hoc_spine/auth_wiring.py (if needed) | Keep behavior deterministic and logged. |
| T4 | Route Exposure | Implement explicit policy for `/hoc/api/auth/provider/status` through gateway public-path/RBAC wiring (or explicit protected policy with evidence). | TODO | design/auth/RBAC_RULES.yaml and/or relevant gateway policy loaders | Must be intentional and documented. |
| T5 | Tests | Add/update tests for readiness checks, startup gating logic, and provider/status endpoint behavior. | TODO | backend/tests/auth/test_auth_provider_seam.py, backend/tests/auth/test_auth_identity_routes.py, additional startup tests if needed | Include negative and positive cases. |
| T6 | Validation | Run targeted tests and governance checks (capability enforcer + relevant local gates). | TODO | backend/app/hoc/docs/architecture/usecases/HOC_Auth_JWKS_Readiness_Gate_and_Startup_Fail_Fast_plan_implemented.md | Record exact commands and key lines of output. |
| T7 | Documentation | Update implementation evidence doc and memory pin references impacted by this change. | TODO | backend/app/hoc/docs/architecture/usecases/*, docs/memory-pins/* | Keep statements date-accurate and non-stale. |
| T8 | PR Hygiene | Commit scoped files, push branch, update PR #34 description/checklist with this wave evidence. | TODO | PR #34 | No amend/force-push. Include commit SHA in report. |

## 6. Execution Order

1. T1
2. T2
3. T3
4. T4
5. T5
6. T6
7. T7
8. T8

## 7. Verification Commands

```bash
# 1) Baseline state
cd /root/agenticverz2.0
git status --short --branch
rg -n "provider/status|is_configured|AUTH_PROVIDER|CLOVE|JWKS|configure_auth_gateway|AUTH_GATEWAY_REQUIRED" backend/app/auth backend/app/hoc/api/auth backend/app/main.py

# 2) Targeted tests
cd /root/agenticverz2.0/backend
PYTHONPATH=. python3 -m pytest tests/auth/test_auth_provider_seam.py tests/auth/test_auth_identity_routes.py -q

# 3) Optional startup gate test slice (if new test file created)
PYTHONPATH=. python3 -m pytest tests/auth -k "startup or readiness or provider_status" -q

# 4) Capability enforcer on changed files
cd /root/agenticverz2.0
python3 scripts/ops/capability_registry_enforcer.py check-pr --files <changed_files>

# 5) Registry sanity if RBAC_RULES/registry touched
python3 scripts/ops/capability_registry_enforcer.py validate-registry
```

## 8. Risks and Rollback

- Risks:
- Overly strict startup gate could block non-prod local/dev unexpectedly.
- Public exposure of status endpoint could leak operational details if diagnostics are not sanitized.
- RBAC/public-path changes can affect unrelated auth behavior if path match patterns are too broad.

- Rollback plan:
- Revert only this wave commit(s) from PR branch.
- Disable strict non-prod startup behavior via env flag.
- Temporarily keep status endpoint protected if public policy causes risk, while preserving startup gate.

## 9. Claude Fill Rules

1. Update `Status` per task: `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record concrete evidence path per task (file path, test output, or artifact).
3. Include exact commands run and key output lines; do not summarize without evidence.
4. If blocked, include blocker reason and smallest next executable action.
5. Keep edits scoped; do not touch unrelated files.
6. Return completed results in `HOC_Auth_JWKS_Readiness_Gate_and_Startup_Fail_Fast_plan_implemented.md`.

## 10. Return Format (Required)

1. Files changed (grouped by code/tests/docs).
2. Before/after behavior for:
- startup with missing Clove/JWKS config in prod and non-prod,
- `/hoc/api/auth/provider/status` response and HTTP status,
- gateway behavior when provider unconfigured.
3. Test/gate results with exact counts.
4. Commit SHA(s) and PR link.
5. Remaining blockers (if any) with ownership (`PR-owned` vs `repo-wide`).
