# HOC Blocker Queue W5 Plan (API Lanes, 2026-02-21)

## Goal
Clear the remaining API-lane capability-linkage backlog under `backend/app/hoc/api/**`.

## Audited Scope
- Full-HOC backlog entering W5 (post-W4 target): `157` blocking.
- W5 exact queue: `83` files.
- Queue artifact: `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W5_FILE_QUEUE_2026-02-21.txt`

## Cluster Breakdown (83)
- `backend/app/hoc/api/cus/**`: `34`
- `backend/app/hoc/api/facades/**`: `22`
- `backend/app/hoc/api/int/**`: `16`
- `backend/app/hoc/api/fdr/**`: `11`

## Execution Batches
1. Batch W5-A: `api/cus/**` (`34`)
2. Batch W5-B: `api/facades/**` (`22`)
3. Batch W5-C: `api/int/**` + `api/fdr/**` (`27`)

## Per-Batch Procedure
1. Confirm W5 queue count and target batch list.
2. Add missing `# capability_id:` headers.
3. Synchronize registry evidence entries.
4. Run changed-file capability check for batch files.
5. Re-run HOC layer/import guard spot-checks after each batch.

## Capability Mapping Rule
API files may be multi-capability by domain. For each API subfolder, mirror the capability mapping used by its owning domain engine/facade and validate by changed-file check before broad rollout in that subfolder.

## Exit Criteria
- W5 queue file reaches `0` lines.
- Full HOC sweep reduces from `157` to `74` (`-83`).
- Warnings remain `0`.
- Layer segregation remains `0`.
- HOC relative-import count remains `0`.

## Evidence Artifacts To Produce
- `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W5_API_LANES_IMPLEMENTED_2026-02-21.md`
- Updated queue/plan/baseline docs and W5 progress in memory pin trail.
