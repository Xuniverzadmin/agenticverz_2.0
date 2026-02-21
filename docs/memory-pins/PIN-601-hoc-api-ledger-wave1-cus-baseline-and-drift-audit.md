# PIN-601: HOC API Ledger Wave 1 (CUS) Baseline and Drift Audit

## Metadata
- Date: 2026-02-21
- Scope: HOC `cus/*` API registry wave
- Branch: `hoc/wave1-hoc-api-ledger`
- Plan: `backend/app/hoc/docs/architecture/usecases/HOC_API_LEDGER_SKILL_ROLLOUT_PLAN_2026-02-21.md`

## What Was Done
1. Established clean execution lane from `origin/main` using dedicated worktree.
2. Generated deterministic CUS API ledger artifacts:
   - `docs/api/HOC_CUS_API_LEDGER.json`
   - `docs/api/HOC_CUS_API_LEDGER.csv`
   - `docs/api/HOC_CUS_API_LEDGER.md`
3. Produced skeptical mismatch audits:
   - `docs/api/HOC_CUS_API_LEDGER_MISMATCH_AUDIT_2026-02-21.md`
   - `docs/api/HOC_CUS_API_LEDGER_MISMATCH_AUDIT_2026-02-21.json`
4. Captured command-level audit evidence:
   - `docs/api/HOC_CUS_API_LEDGER_WAVE1_AUDIT_2026-02-21.md`
5. Updated plan status and implemented report:
   - `backend/app/hoc/docs/architecture/usecases/HOC_API_LEDGER_SKILL_ROLLOUT_PLAN_2026-02-21.md`
   - `backend/app/hoc/docs/architecture/usecases/HOC_API_LEDGER_SKILL_ROLLOUT_PLAN_2026-02-21_implemented.md`

## Key Results
- Ledger raw rows: 502
- Ledger unique method+path: 499
- Local `docs/openapi.json` `/hoc/api/cus/*` entries: 0
- Backend `.openapi_snapshot.json` `/hoc/api/cus/*` entries: 0
- Stagetest `/openapi.json`: returned HTML shell payload, not JSON OpenAPI

## Interpretation
- Wave 1 successfully establishes a deterministic CUS ledger baseline.
- OpenAPI namespace drift remains unresolved for `/hoc/api/cus/*` prefix mapping.
- Runtime publication evidence for `/apis/ledger` remains pending until route namespace and gateway/proxy behavior are clarified.

## Next Actions
1. Lock canonical API namespace contract for HOC (`/hoc/api/cus/*` vs transformed prefixes).
2. Implement/verify `/apis/ledger` publication path with 200 JSON evidence.
3. Start Wave 2 (`fdr/*`) after namespace decision is merged.
