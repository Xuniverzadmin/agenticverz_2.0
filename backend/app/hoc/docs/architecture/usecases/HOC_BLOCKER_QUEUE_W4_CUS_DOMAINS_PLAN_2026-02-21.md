# HOC Blocker Queue W4 Plan (CUS Domain Internals, 2026-02-21)

## Goal
Clear the remaining CUS internal-domain capability-linkage backlog under `backend/app/hoc/cus/**`.

## Audited Scope
- Source audit: `python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(git ls-files 'backend/app/hoc/**/*.py')`
- Current full-HOC backlog: `280` blocking, `0` warnings.
- W4 exact queue: `123` files.
- Queue artifact: `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W4_FILE_QUEUE_2026-02-21.txt`

## Cluster Breakdown (123)
- `backend/app/hoc/cus/account/**`: `37`
- `backend/app/hoc/cus/controls/**`: `24`
- `backend/app/hoc/cus/activity/**`: `21`
- `backend/app/hoc/cus/policies/**`: `12`
- `backend/app/hoc/cus/api_keys/**`: `10`
- `backend/app/hoc/cus/overview/**`: `6`
- `backend/app/hoc/cus/ops/**`: `5`
- `backend/app/hoc/cus/agent/**`: `5`
- `backend/app/hoc/cus/apis/**`: `2`
- `backend/app/hoc/cus/__init__.py`: `1`

## Execution Batches
1. Batch W4-A: `cus/account/**` + `cus/controls/**` (`61`)
2. Batch W4-B: `cus/activity/**` + `cus/policies/**` (`33`)
3. Batch W4-C: `cus/api_keys/**` + `cus/overview/**` + `cus/ops/**` + `cus/agent/**` + `cus/apis/**` + `cus/__init__.py` (`29`)

## Per-Batch Procedure
1. Capture pre-batch count from W4 queue file.
2. Add missing `# capability_id:` headers for batch files.
3. Synchronize registry evidence in `docs/capabilities/CAPABILITY_REGISTRY.yaml`.
4. Run changed-file check:
   - `python3 scripts/ops/capability_registry_enforcer.py check-pr --files <batch files>`
5. Update queue file by removing completed files.

## Capability Mapping Rule
Use existing domain mapping already present in nearby code/registry where clear; if mixed or ambiguous in a directory, resolve mapping before edit by running changed-file check on a small pilot subset (3-5 files) and lock mapping for the rest of that batch.

## Exit Criteria
- W4 queue file reaches `0` lines.
- Full HOC sweep reduces from `280` to `157` (`-123`).
- Warnings remain `0`.
- Layer segregation remains `0`.
- HOC relative-import count remains `0`.

## Evidence Artifacts To Produce
- `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W4_CUS_DOMAINS_IMPLEMENTED_2026-02-21.md`
- Updated:
  - `backend/app/hoc/docs/architecture/usecases/HOC_ACTIVE_BLOCKER_QUEUE_2026-02-20.md`
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_WAVE_PLAN_2026-02-20.md`
  - `backend/app/hoc/docs/architecture/usecases/CI_BASELINE_BLOCKER_QUEUE_2026-02-20.md`
