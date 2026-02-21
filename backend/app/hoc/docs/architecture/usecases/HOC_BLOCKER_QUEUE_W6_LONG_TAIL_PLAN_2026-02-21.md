# HOC Blocker Queue W6 Plan (INT/FDR Long Tail, 2026-02-21)

## Goal
Clear the residual long-tail capability-linkage backlog in INT and FDR lanes and reach zero blocking issues.

## Audited Scope
- Full-HOC backlog entering W6 (post-W5 target): `74` blocking.
- W6 exact queue: `74` files.
- Queue artifact: `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W6_FILE_QUEUE_2026-02-21.txt`

## Cluster Breakdown (74)
- `backend/app/hoc/fdr/ops/**`: `16`
- `backend/app/hoc/int/recovery/**`: `12`
- `backend/app/hoc/int/logs/**`: `10`
- `backend/app/hoc/int/incidents/**`: `8`
- `backend/app/hoc/int/integrations/**`: `8`
- `backend/app/hoc/int/analytics/**`: `7`
- `backend/app/hoc/fdr/account/**`: `2`
- `backend/app/hoc/fdr/agent/**`: `2`
- `backend/app/hoc/fdr/logs/**`: `2`
- `backend/app/hoc/int/account/**`: `2`
- `backend/app/hoc/int/activity/**`: `2`
- `backend/app/hoc/fdr/platform/**`: `1`
- `backend/app/hoc/fdr/__init__.py`: `1`
- `backend/app/hoc/int/__init__.py`: `1`

## Execution Batches
1. Batch W6-A: FDR lane (`fdr/ops`, `fdr/logs`, `fdr/account`, `fdr/agent`, `fdr/platform`, `fdr/__init__.py`) (`24`)
2. Batch W6-B: INT recovery/log lane (`int/recovery`, `int/logs`) (`22`)
3. Batch W6-C: INT residual lane (`int/incidents`, `int/integrations`, `int/analytics`, `int/activity`, `int/account`, `int/__init__.py`) (`28`)

## Per-Batch Procedure
1. Apply file-level `# capability_id:` metadata.
2. Sync evidence paths in `docs/capabilities/CAPABILITY_REGISTRY.yaml`.
3. Run changed-file capability check.
4. Run full-HOC sweep after each batch to verify descending trend.

## Exit Criteria
- W6 queue file reaches `0` lines.
- Full HOC sweep blocking reaches `0`.
- Warnings remain `0`.
- Layer segregation remains `0`.
- HOC relative-import count remains `0`.

## Evidence Artifacts To Produce
- `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W6_LONG_TAIL_IMPLEMENTED_2026-02-21.md`
- Queue/baseline/literature updates showing full-HOC blocker clearance.
