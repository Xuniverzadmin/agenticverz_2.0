# PIN-602: HOC API Ledger Wave 2 (FDR) + Publication Expansion

## Metadata
- Date: 2026-02-21
- Scope: HOC `fdr/*` API registry wave + merged publication path
- Branch: `hoc/wave2-hoc-api-ledger-fdr`
- Depends on: PR #30 (`25862f73`, Wave 1 merged)

## What Was Done
1. Generated deterministic FDR ledger artifacts:
   - `docs/api/HOC_FDR_API_LEDGER.json`
   - `docs/api/HOC_FDR_API_LEDGER.csv`
   - `docs/api/HOC_FDR_API_LEDGER.md`
2. Generated FDR mismatch evidence:
   - `docs/api/HOC_FDR_API_LEDGER_MISMATCH_AUDIT_2026-02-21.md`
   - `docs/api/HOC_FDR_API_LEDGER_MISMATCH_AUDIT_2026-02-21.json`
3. Generated merged HOC ledger artifacts (CUS + FDR):
   - `docs/api/HOC_API_LEDGER_ALL.json`
   - `docs/api/HOC_API_LEDGER_ALL.csv`
   - `docs/api/HOC_API_LEDGER_ALL.md`
4. Expanded stagetest ledger publication engine:
   - prefers `HOC_API_LEDGER_ALL.json`
   - falls back to scoped ledgers (`CUS`, `FDR`)
   - then artifact snapshot
   - then source-derived fallback
5. Captured Wave 2 audit evidence:
   - `docs/api/HOC_FDR_API_LEDGER_WAVE2_AUDIT_2026-02-21.md`

## Key Results
- FDR source ledger rows: 66
- OpenAPI `/hoc/api/fdr/*` rows in `docs/openapi.json`: 0
- Merged ledger rows (CUS + FDR): 568
- Publication function local result:
  - `run_id=ledger-hoc-all`
  - contains both `/hoc/api/cus/*` and `/hoc/api/fdr/*` routes

## Governance Results
- `pytest tests/api/test_stagetest_read_api.py`: PASS (10 passed)
- `check_layer_boundaries.py`: PASS
- `check_openapi_snapshot.py`: PASS
- `capability_registry_enforcer.py check-pr`: PASS (warnings only)
- `layer_segregation_guard.py --scope hoc`: 93 violations (legacy debt lane, unchanged)

## Next Actions
1. Wave 3: generate `HOC_INT_API_LEDGER.*` and mismatch audit.
2. Rebuild merged HOC ledger for CUS+FDR+INT.
3. Validate stagetest `/apis/ledger` live payload after Wave 2 deploy.
