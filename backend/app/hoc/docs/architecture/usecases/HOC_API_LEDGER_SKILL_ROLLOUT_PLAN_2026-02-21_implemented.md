# HOC API Ledger Skill Rollout Plan (hoc/*) — Implemented Status

**Date:** 2026-02-21  
**Plan Source:** `backend/app/hoc/docs/architecture/usecases/HOC_API_LEDGER_SKILL_ROLLOUT_PLAN_2026-02-21.md`  
**Execution Scope:** Wave 1 (CUS) + Wave 2 (FDR)

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

## Wave 2 Update (FDR)
1. Added deterministic FDR ledger artifacts:
   - `docs/api/HOC_FDR_API_LEDGER.json`
   - `docs/api/HOC_FDR_API_LEDGER.csv`
   - `docs/api/HOC_FDR_API_LEDGER.md`
2. Added merged HOC ledger artifacts (CUS + FDR):
   - `docs/api/HOC_API_LEDGER_ALL.json`
   - `docs/api/HOC_API_LEDGER_ALL.csv`
   - `docs/api/HOC_API_LEDGER_ALL.md`
3. Added skeptical mismatch artifacts for FDR:
   - `docs/api/HOC_FDR_API_LEDGER_MISMATCH_AUDIT_2026-02-21.md`
   - `docs/api/HOC_FDR_API_LEDGER_MISMATCH_AUDIT_2026-02-21.json`
4. Updated stagetest publication engine to load merged HOC ledger first, then scoped ledgers, then artifact/source fallback.
5. Local verification after Wave 2 code:
   - `get_apis_ledger_snapshot().run_id` => `ledger-hoc-all`
   - merged endpoints => `568`
   - includes both `/hoc/api/cus/*` and `/hoc/api/fdr/*` rows
6. Wave 2 governance outputs:
   - `pytest tests/api/test_stagetest_read_api.py` => `10 passed`
   - `check_layer_boundaries.py` => PASS
   - `check_openapi_snapshot.py` => PASS
   - `capability_registry_enforcer.py check-pr` => PASS (2 non-blocking `MISSING_EVIDENCE` warnings)
   - `layer_segregation_guard.py --scope hoc` => 93 legacy violations (unchanged baseline debt)

## Next Actions
1. Execute Wave 3 (`int/*`) and generate `HOC_INT_API_LEDGER.*`.
2. Rebuild `HOC_API_LEDGER_ALL.*` for CUS+FDR+INT and re-verify publication payload shape.
3. Keep full-HOC legacy capability backlog in separate queue; do not mix with wave-scoped API-ledger PRs.
