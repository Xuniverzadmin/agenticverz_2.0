# HOC_CUS_APIs_Swagger_Stagetest_Rollout_2026_02_21_plan

**Created:** 2026-02-21 10:19:39 UTC
**Executor:** Claude
**Status:** DRAFT

## 1. Objective

- Primary outcome: Publish grouped CUS ledger/OpenAPI endpoints live on `https://stagetest.agenticverz.com` with runtime `200 application/json` evidence.
- Business/technical intent:
  - Close rollout gap between implemented code and live stagetest behavior.
  - Ensure `/apis/ledger/*` and `/apis/swagger/*` are backend-owned routes (not SPA fallback pages).
  - Produce audit-quality evidence with deterministic probes and references.

## 2. Scope

- In scope:
  - Backend route rollout from PR stream that includes:
    - `backend/app/hoc/api/apis/cus_publication.py`
    - `backend/app/hoc/api/facades/apis/__init__.py`
    - `backend/app/hoc/app.py`
    - `backend/app/hoc/cus/hoc_spine/authority/gateway_policy.py`
  - Stagetest routing/proxy behavior for:
    - `/apis/ledger/cus`
    - `/apis/ledger/cus/{domain}`
    - `/apis/swagger/cus`
    - `/apis/swagger/cus/{domain}`
  - Runtime verification and evidence refresh in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_CUS_Strict_Stabilization_Pass_2026_02_21_plan_implemented.md`
    - This plan pair.
- Out of scope:
  - Repo-wide unrelated CI failures not caused by this rollout.
  - Non-CUS domain redesign.
  - Clerk org/login model changes.

## 3. Assumptions and Constraints

- Assumptions:
  - Stagetest serves backend through a reverse proxy and a frontend SPA catch-all.
  - Code for grouped CUS publication endpoints exists in an open PR branch and can be merged/deployed.
- Constraints:
  - No secret material in logs/docs.
  - Preserve PR hygiene: only rollout-related files; no force-push history rewrite.
  - Avoid unrelated refactors while stabilizing this path.
- Non-negotiables:
  - Final proof must be runtime HTTP probes (not TestClient-only evidence).
  - `swagger` publication endpoints must return JSON/OpenAPI payload, not HTML shell.
  - Evidence must include UTC timestamps and exact command snippets.

## 4. Acceptance Criteria

1. `GET /apis/ledger/cus` and `GET /apis/ledger/cus/{domain}` return `200` with `content-type: application/json` on stagetest.
2. `GET /apis/swagger/cus` and `GET /apis/swagger/cus/{domain}` return `200` with `content-type: application/json` on stagetest.
3. `openapi.json` on stagetest contains `/apis/ledger/cus` and `/apis/swagger/cus` paths.
4. Evidence docs are updated with before/after matrix and command outputs.
5. Any unresolved blocker is explicitly recorded with owner and next action.

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| T1 | Baseline Audit | Confirm current runtime behavior and capture pre-rollout matrix (404/HTML vs expected JSON). | TODO | `artifacts/stagetest/<run_id>/pre_rollout_*` | Include exact UTC timestamp and headers. |
| T2 | Codeline Decision | Decide merge path: merge PR #33 as-is or create minimal replacement PR for same endpoints. | TODO | PR link + commit SHA | No force push; clean diff only. |
| T3 | Backend Rollout | Ensure backend includes CUS publication router + gateway public path allowance (`/apis/ledger/`, `/apis/swagger/`). | TODO | merged commit references | Verify on deployed commit, not local only. |
| T4 | Edge Routing Fix | Ensure stagetest proxy precedence routes `/apis/ledger/*` and `/apis/swagger/*` to backend before SPA fallback. | TODO | infra config diff / deploy logs | If not needed, record proof why. |
| T5 | Deploy | Deploy updated backend/proxy config to stagetest environment. | TODO | deployment run output | Record deployed revision hash. |
| T6 | Runtime Verification | Probe all 4 target endpoints + per-domain sample set (10 domains), assert JSON not HTML. | TODO | `artifacts/stagetest/<run_id>/post_rollout_*` | Include response snippets. |
| T7 | OpenAPI Parity | Verify stagetest `/openapi.json` includes new routes and route count changes are expected. | TODO | command output snapshot | Fail if missing. |
| T8 | Documentation & Pin | Update implemented report and save a memory pin with doc references and final verdict. | TODO | plan_implemented + memory pin path | Include blockers (if any). |

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
# 1) Baseline probes (pre-rollout)
BASE="https://stagetest.agenticverz.com"
for p in \
  "/apis/ledger/cus" \
  "/apis/ledger/cus/activity" \
  "/apis/swagger/cus" \
  "/apis/swagger/cus/activity"
do
  curl -sS -L -D /tmp/h.$$ -o /tmp/b.$$ -w "HTTP=%{http_code}\n" "$BASE$p"
  awk 'BEGIN{IGNORECASE=1} /^content-type:/{print}' /tmp/h.$$
  head -c 160 /tmp/b.$$; echo
done

# 2) OpenAPI check
curl -sS "$BASE/openapi.json" | jq -r '.paths | keys[]' | rg '^/apis/(ledger|swagger)/cus' || true

# 3) PR state (if using PR #33 path)
gh pr view --repo Xuniverzadmin/agenticverz_2.0 33 --json state,mergeStateStatus,url,headRefName,baseRefName
gh pr checks --repo Xuniverzadmin/agenticverz_2.0 33

# 4) Post-deploy probes (must be 200 JSON)
for p in \
  "/apis/ledger/cus" \
  "/apis/ledger/cus/activity" \
  "/apis/swagger/cus" \
  "/apis/swagger/cus/activity"
do
  curl -sS -L -D /tmp/h.$$ -o /tmp/b.$$ -w "HTTP=%{http_code}\n" "$BASE$p"
  awk 'BEGIN{IGNORECASE=1} /^content-type:/{print}' /tmp/h.$$
  head -c 160 /tmp/b.$$; echo
done

# 5) Domain sweep (10 domains)
for d in activity account api_keys analytics controls incidents integrations logs ops policies; do
  curl -sS -o /dev/null -w "/apis/ledger/cus/$d HTTP=%{http_code}\n" "$BASE/apis/ledger/cus/$d"
  curl -sS -o /dev/null -w "/apis/swagger/cus/$d HTTP=%{http_code}\n" "$BASE/apis/swagger/cus/$d"
done
```

## 8. Risks and Rollback

- Risks:
  - PR merge blocked by unrelated repo-wide failing checks.
  - Stagetest proxy continues serving SPA for `/apis/swagger/*`.
  - Partial deploy causes mixed results across routes.
- Rollback plan:
  - If rollout introduces regressions, revert the deployment commit(s) and proxy change.
  - Re-run baseline probe pack to verify return to pre-rollout behavior.
  - Keep evidence artifacts for both attempted rollout and rollback.

## 9. Claude Fill Rules

1. Update `Status` for each task: `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record concrete evidence path per task (file path, test output doc, or artifact).
3. If blocked, include blocker reason and minimal next action.
4. Do not delete plan sections; append execution facts.
5. Return completed results in `HOC_CUS_APIs_Swagger_Stagetest_Rollout_2026_02_21_plan_implemented.md`.
