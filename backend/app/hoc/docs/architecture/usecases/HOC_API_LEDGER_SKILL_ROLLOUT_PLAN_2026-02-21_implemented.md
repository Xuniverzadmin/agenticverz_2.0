# HOC API Ledger Skill Rollout Plan (hoc/*) — Implemented Status

**Date:** 2026-02-21  
**Plan Source:** `backend/app/hoc/docs/architecture/usecases/HOC_API_LEDGER_SKILL_ROLLOUT_PLAN_2026-02-21.md`  
**Execution Scope:** Wave 1 (CUS)

## Status Matrix
1. Phase 0 (Bootstrap + clean lane): DONE.
2. Phase 1 (CUS inventory): DONE.
3. Phase 2 (CUS ledger artifacts): DONE.
4. Phase 3 (CUS mismatch audit): DONE.
5. Phase 4 (runtime publication evidence): DONE.
6. Phase 5 (governance audit commands): DONE (captured; legacy violations observed in full hoc scope).
7. Phase 6 (PR/doc closure): DONE for Wave 1.

## Artifacts Produced
- `docs/api/HOC_CUS_API_LEDGER.json`
- `docs/api/HOC_CUS_API_LEDGER.csv`
- `docs/api/HOC_CUS_API_LEDGER.md`
- `docs/api/HOC_CUS_API_LEDGER_MISMATCH_AUDIT_2026-02-21.md`
- `docs/api/HOC_CUS_API_LEDGER_MISMATCH_AUDIT_2026-02-21.json`
- `docs/api/HOC_CUS_API_LEDGER_WAVE1_AUDIT_2026-02-21.md`
- `docs/api/_stagetest_openapi_2026-02-21.json` (captured non-JSON response body)
- `scripts/deploy/apache/stagetest.agenticverz.com.conf` (runtime proxy template for OpenAPI + ledger publication)

## Key Findings
1. CUS ledger produced `502` rows (`499` unique method+path).
2. Local `docs/openapi.json` has `0` `/hoc/api/cus/*` paths.
3. Backend `.openapi_snapshot.json` also has `0` `/hoc/api/cus/*` paths under this prefix; uses alternate namespaces (`/api/*`, `/ops/*`, `/customer/*`).
4. Runtime proxy correction applied: stagetest `/openapi.json` now returns JSON and `/apis/ledger` returns non-empty payload.
5. Live verification (2026-02-21 UTC):
   - `https://stagetest.agenticverz.com/openapi.json` => `200 application/json`
   - `https://stagetest.agenticverz.com/hoc/api/openapi.json` => `200 application/json`
   - `https://stagetest.agenticverz.com/apis/ledger` => `200 application/json` (`endpoints_count=502`, `run_id=ledger_20260221T071020Z`)

## Next Actions
1. Decide canonical route namespace to be represented in OpenAPI vs runtime (`/hoc/api/cus/*` vs transformed prefixes).
2. Start Wave 2 (`fdr/*`) and keep publication contract stable on `/apis/ledger`.
3. Keep full-HOC legacy capability backlog in separate queue; do not mix with Wave 2 route/ledger PR scope.
