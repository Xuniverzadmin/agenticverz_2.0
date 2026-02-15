# NORTH_STAR_UC_GREEN_WORKSTREAM_PLAN.md

## North Star
Move all registered usecases (`UC-001`..`UC-017`) to `GREEN` with:
1. Codebase compliance
2. Architecture compliance (L2 -> L4 -> L5 -> L6 -> L7)
3. Domain authority compliance
4. Verifiable audit evidence

## Current Baseline (2026-02-11)
1. `GREEN`: `UC-001`, `UC-002`
2. `YELLOW`: `UC-003`..`UC-009`
3. `RED`: `UC-010`..`UC-017`

## Execution Model
1. Execute batches strictly in order.
2. Each batch must produce an implementation evidence doc.
3. Do not promote any UC to `GREEN` without:
- verifier pass
- tests pass
- docs sync (`INDEX.md` + `HOC_USECASE_CODE_LINKAGE.md`)

## Batch Sequence
1. Batch-01: Governance + authority lock + strict validation baseline
2. Batch-02: Logs + activity determinism and replay integrity closure
3. Batch-03: Controls + policies authority and override lifecycle closure
4. Batch-04: Incidents + analytics reproducibility and lifecycle closure
5. Batch-05: Cross-UC hardening, regression, and status promotion

## Canonical Batch Docs
1. `backend/app/hoc/docs/architecture/usecases/HANDOVER_BATCH_01_GOVERNANCE_BASELINE.md`
2. `backend/app/hoc/docs/architecture/usecases/HANDOVER_BATCH_02_LOGS_ACTIVITY.md`
3. `backend/app/hoc/docs/architecture/usecases/HANDOVER_BATCH_03_CONTROLS_POLICIES.md`
4. `backend/app/hoc/docs/architecture/usecases/HANDOVER_BATCH_04_INCIDENTS_ANALYTICS.md`
5. `backend/app/hoc/docs/architecture/usecases/HANDOVER_BATCH_05_GREEN_PROMOTION.md`

## Guardrails
1. No destructive refactors without preserving route compatibility.
2. No side writes outside canonical evented flows.
3. No domain authority drift:
- proposals do not mutate enforcement
- onboarding authority remains in canonical domains
4. Keep all evidence docs under:
- `backend/app/hoc/docs/architecture/usecases/`
