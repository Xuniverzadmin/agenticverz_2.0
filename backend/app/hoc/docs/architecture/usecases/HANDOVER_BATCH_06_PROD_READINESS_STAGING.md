# HANDOVER_BATCH_06_PROD_READINESS_STAGING.md

## Objective
Run staging-grade production-readiness validation for `UC-001..UC-017` without changing architecture status semantics.

## Scope
1. Use `PROD_READINESS_TRACKER.md` as source of truth for readiness status.
2. Validate real-provider/real-env behavior in staging.
3. Capture auditable evidence per UC cluster.

## UC Clusters
1. Cluster A: `UC-001..UC-003`, `UC-017` (trace/replay)
2. Cluster B: `UC-004..UC-006`, `UC-010`, `UC-014`, `UC-015` (controls/activity)
3. Cluster C: `UC-007`, `UC-011`, `UC-012` (incidents lifecycle)
4. Cluster D: `UC-008`, `UC-016`, `UC-009`, `UC-013` (analytics/policy proposals)

## Tasks
1. Execute staging smoke suite per cluster:
- BYOK + managed-key path
- connector handshake
- SDK attestation checks
- replay mode checks (`FULL|TRACE_ONLY`)
- rotation/revocation checks
2. Record evidence rows in `PROD_READINESS_TRACKER.md` template format.
3. Update readiness status per UC:
- `NOT_STARTED` -> `IN_PROGRESS` or `BLOCKED` or `READY_FOR_GO_LIVE`

## Required Output
Create:
- `backend/app/hoc/docs/architecture/usecases/HANDOVER_BATCH_06_PROD_READINESS_STAGING_implemented.md`

Include:
1. UC-by-UC evidence matrix
2. PASS/FAIL/BLOCKED with concrete blockers
3. commands/tests run and timestamps
