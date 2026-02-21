# PIN-603: HOC Blocker Queue Wave W3 - INT General + Worker + Policies Clearance

## Metadata
- Date: 2026-02-20
- Status: COMPLETE
- Scope: `backend/app/hoc/int/general/**`, `backend/app/hoc/int/worker/**`, `backend/app/hoc/int/policies/**`
- Workstream: HOC-only capability-linkage blocker queue

## Context
Wave W3 continued the HOC capability-linkage reduction plan after W2 (`449 -> 358`) and targeted the next largest INT runtime cluster. The work remained metadata-first: file headers plus capability-registry evidence synchronization, with no broad runtime refactors.

## What Was Implemented
1. Added missing file-level `# capability_id:` metadata to `78` INT files:
   - `CAP-006` for `int/general/**`
   - `CAP-012` for `int/worker/**`
   - `CAP-009` for `int/policies/**`
2. Updated `docs/capabilities/CAPABILITY_REGISTRY.yaml` evidence mappings for the W3 file set.
3. Updated blocker tracking/governance docs:
   - `backend/app/hoc/docs/architecture/usecases/HOC_ACTIVE_BLOCKER_QUEUE_2026-02-20.md`
   - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_WAVE_PLAN_2026-02-20.md`
   - `backend/app/hoc/docs/architecture/usecases/CI_BASELINE_BLOCKER_QUEUE_2026-02-20.md`
   - `literature/hoc_domain/ops/SOFTWARE_BIBLE.md`
   - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W3_INT_GENERAL_WORKER_POLICIES_IMPLEMENTED_2026-02-20.md`

## Audit Results
- Changed-file capability check (W3 scope): PASS
- Layer segregation (`--scope hoc`): PASS (`0`)
- HOC strict relative-import count: `0`
- Full HOC capability sweep:
  - Before: blocking `358`, warnings `0`
  - After: blocking `280`, warnings `0`
  - Delta: `-78` blocking

## Remaining HOC Backlog (Post-W3)
- Full-HOC `MISSING_CAPABILITY_ID`: `280`
- Largest residual clusters:
  - `backend/app/hoc/cus/account/**` (`37`)
  - `backend/app/hoc/api/cus/**` (`34`)
  - `backend/app/hoc/cus/controls/**` (`24`)
  - `backend/app/hoc/api/facades/**` (`22`)
  - `backend/app/hoc/cus/activity/**` (`21`)

## Artifacts
- W3 implemented artifact:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W3_INT_GENERAL_WORKER_POLICIES_IMPLEMENTED_2026-02-20.md`
- Wave plan tracker:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_WAVE_PLAN_2026-02-20.md`
- Active queue snapshot:
  - `backend/app/hoc/docs/architecture/usecases/HOC_ACTIVE_BLOCKER_QUEUE_2026-02-20.md`
