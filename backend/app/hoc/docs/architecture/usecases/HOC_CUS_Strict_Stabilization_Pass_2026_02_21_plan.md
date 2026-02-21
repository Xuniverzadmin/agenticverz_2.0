# HOC_CUS_Strict_Stabilization_Pass_2026_02_21_plan

**Created:** 2026-02-21 07:41:41 UTC  
**Executor:** Claude  
**Status:** DRAFT  
**Mode:** CUS-only strict stabilization (FDR/INT deferred)

## 1. Objective

- Primary outcome: Stabilize `hoc/cus/*` contract truth end-to-end so CUS registry, OpenAPI, and runtime publication are deterministic and consistent.
- Publish goal: Domain-grouped CUS registry + Swagger/OpenAPI grouped publication with `200` evidence and parity guarantees.
- Business/technical intent:
1. Remove ambiguity about what CUS APIs exist.
2. Publish CUS APIs by domain for consumption.
3. Make drift visible and enforceable in PR gates.

## 2. Scope

- In scope:
1. `backend/app/hoc/api/cus/**`
2. `backend/app/hoc/cus/**` only if needed for CUS wiring parity
3. `apis` lane for grouped CUS publication surfaces
4. `hoc_spine` lane for CUS dispatch conformance checks (`L2 -> L4 -> L5 -> L6`)
5. CUS docs, CUS ledger artifacts, CUS evidence pins

- Out of scope:
1. `backend/app/hoc/api/fdr/**`
2. `backend/app/hoc/api/int/**`
3. hoc-wide debt remediation outside CUS stabilization PR

## 3. Deep Analysis Baseline (Audit Facts)

1. Local OpenAPI CUS rows (`docs/openapi.json`, `/hoc/api/cus/*`): `0`
2. Runtime OpenAPI CUS rows (`https://stagetest.agenticverz.com/openapi.json`, `/hoc/api/cus/*`): `0`
3. Local CUS ledger rows: `502` (`499` unique method+path)
4. Runtime `/apis/ledger` CUS rows: `502` (`499` unique method+path)
5. Local/runtime CUS parity (unique method+path): zero diff both directions
6. `check_layer_boundaries.py`: PASS
7. `layer_segregation_guard.py --scope hoc`: 93 active canonical HOC debt (deferred in this plan)

Analysis conclusion:
1. Publication and ledger parity currently hold for CUS.
2. OpenAPI visibility for `/hoc/api/cus/*` is the primary stabilization gap.
3. Domain-grouped publication and grouped Swagger views are not yet formalized and must be added as explicit deliverables.

## 4. Assumptions and Constraints

- Assumptions:
1. `hoc/cus/*` remains canonical customer surface.
2. Runtime OpenAPI and local OpenAPI may diverge due to wiring/proxy/spec generation behavior.
3. Domain list is fixed for this pass:
   `overview`, `activity`, `incidents`, `policies`, `controls`, `logs`, `analytics`, `integrations`, `api_keys`, `account`.

- Constraints:
1. One objective lane per PR.
2. No unrelated FDR/INT changes.
3. No force-push, no history rewrite.
4. Work in clean worktree only.

- Non-negotiables:
1. Deterministic artifact generation.
2. Explicit evidence for every gate.
3. Domain-by-domain execution chronology.

## 5. Acceptance Criteria

1. OpenAPI CUS drift is closed or explicitly mapped with authoritative alias contract and evidence.
2. Domain-grouped CUS registry artifacts exist and are published by domain.
3. Domain publication endpoints return `200` with non-empty payload where applicable.
4. Domain parity checks pass (`method+path` diff zero) for local vs runtime.
5. Changed-file governance gates pass and evidence is recorded.
6. PR hygiene is clean and reproducible.

## 6. Chronological Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| T1 | Setup | Bootstrap strict context and lock CUS-only scope in clean worktree | TODO |  |  |
| T2 | Audit | Re-run baseline metrics and persist snapshot doc | TODO |  |  |
| T3 | Design | Define grouped publication contract (`/apis/ledger/cus`, `/apis/ledger/cus/<domain>`, `/apis/swagger/cus`, `/apis/swagger/cus/<domain>`) | TODO |  |  |
| T4 | Core | Implement/adjust CUS OpenAPI visibility closure path | TODO |  |  |
| T5 | Core | Generate global CUS ledger artifacts (`HOC_CUS_API_LEDGER.*`) deterministically | TODO |  |  |
| T6 | Core | Generate domain-ledger artifacts under `docs/api/cus/` for all 10 domains | TODO |  |  |
| T7 | Core | Implement grouped runtime publication views for CUS domains | TODO |  |  |
| T8 | Core | Verify `hoc_spine` dispatch conformance for CUS route set | TODO |  |  |
| T9 | Validation | Run global + per-domain parity checks (local vs runtime) and persist diffs | TODO |  |  |
| T10 | Validation | Run governance gates on changed files and targeted tests | TODO |  |  |
| T11 | Documentation | Update stabilization audit docs, plan-implemented, and memory pin | TODO |  |  |
| T12 | Release Hygiene | Commit/push/open PR with strict scope and explicit blocker report | TODO |  |  |

## 7. Execution Order

1. T1
2. T2
3. T3
4. T4
5. T5
6. T6
7. T7
8. T8
9. T9
10. T10
11. T11
12. T12

## 8. Verification Commands

```bash
# bootstrap
scripts/ops/hoc_session_bootstrap.sh --strict

# openapi and ledger audits
python3 scripts/ci/check_openapi_snapshot.py
python3 /root/.codex/skills/hoc-cus-api-ledger-rollout/scripts/build_cus_api_ledger.py \
  --repo-root <repo_root> \
  --openapi-source <repo_root>/docs/openapi.json \
  --path-prefix /hoc/api/cus/ \
  --source-scan-root <repo_root>/backend/app/hoc/api/cus \
  --out-json docs/api/HOC_CUS_API_LEDGER.json \
  --out-csv docs/api/HOC_CUS_API_LEDGER.csv \
  --out-md docs/api/HOC_CUS_API_LEDGER.md

# runtime probes
curl -i https://stagetest.agenticverz.com/openapi.json
curl -i https://stagetest.agenticverz.com/apis/ledger
curl -i https://stagetest.agenticverz.com/apis/ledger/cus
curl -i https://stagetest.agenticverz.com/apis/ledger/cus/<domain>
curl -i https://stagetest.agenticverz.com/apis/swagger/cus
curl -i https://stagetest.agenticverz.com/apis/swagger/cus/<domain>

# gates
cd backend && PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py
python3 scripts/ops/capability_registry_enforcer.py check-pr --files <changed_py_files>
cd backend && PYTHONPATH=. pytest -q tests/api/test_stagetest_read_api.py
```

## 9. PR Hygiene (Mandatory)

1. Clean worktree from `origin/main`; no dirty-tree commits.
2. Stage only CUS-scope and evidence files listed in this plan.
3. One PR for this stabilization objective only.
4. No force-push, no amend after review starts, no unrelated reformat churn.
5. PR body must include:
   - baseline vs after metrics
   - exact commands run
   - publish-goal evidence URLs/status codes
   - open blockers with explicit owner lane

## 10. Risks and Rollback

- Risks:
1. OpenAPI generator may emit non-canonical aliases.
2. Runtime proxy path may not match local publication path.
3. Domain grouping may expose sparse/empty domains requiring policy decisions.

- Rollback plan:
1. Revert only changed CUS publication/spec files.
2. Keep generated audit artifacts for traceability.
3. Re-open with reduced scope (OpenAPI closure only) if grouped publication is blocked.

## 11. Claude Fill Rules

1. Update task `Status` using only: `DONE`, `PARTIAL`, `BLOCKED`, `SKIPPED`.
2. Record concrete evidence per task (file path, URL probe, command output path).
3. If blocked, include exact blocker and minimum next action.
4. Do not delete sections; append facts.
5. Return completion in `HOC_CUS_Strict_Stabilization_Pass_2026_02_21_plan_implemented.md`.
