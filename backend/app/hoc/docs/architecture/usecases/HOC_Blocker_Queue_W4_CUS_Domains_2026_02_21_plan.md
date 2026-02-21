# HOC_Blocker_Queue_W4_CUS_Domains_2026_02_21_plan

**Created:** 2026-02-21 05:21:04 UTC
**Executor:** Claude
**Status:** COMPLETED

## 1. Objective

- Primary outcome: Clear W4 CUS-domain `MISSING_CAPABILITY_ID` blockers (`123` files).
- Business/technical intent: Reduce full-HOC blocker backlog from `280` to `157` without regressing layer/import guard status.

## 2. Scope

- In scope:
  - `backend/app/hoc/cus/account/**`
  - `backend/app/hoc/cus/activity/**`
  - `backend/app/hoc/cus/controls/**`
  - `backend/app/hoc/cus/policies/**`
  - `backend/app/hoc/cus/api_keys/**`
  - `backend/app/hoc/cus/overview/**`
  - `backend/app/hoc/cus/ops/**`
  - `backend/app/hoc/cus/agent/**`
  - `backend/app/hoc/cus/apis/**`
  - `backend/app/hoc/cus/__init__.py`
- Out of scope:
  - `backend/app/hoc/api/**` (W5)
  - INT/FDR long-tail clusters (W6)

## 3. Assumptions and Constraints

- Assumptions:
  - Queue artifact is canonical for W4 file set.
  - Capability mapping can be validated incrementally via changed-file checks.
- Constraints:
  - Metadata/evidence synchronization only; no broad runtime refactor.
  - HOC-only governance scope.
- Non-negotiables:
  - Layer segregation `0`.
  - HOC relative imports `0`.
  - Capability warnings remain `0`.

## 4. Acceptance Criteria

1. W4 queue file reaches `0` remaining lines.
2. Full-HOC sweep decreases from `280` to `157` blockers.
3. Changed-file checks pass for each W4 batch and docs are updated.

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| T1 | Setup | Capture W4 before-state and lock batch queues from W4 file list | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W4_FILE_QUEUE_2026-02-21.txt` | use deterministic partitions |
| T2 | Core | Apply capability headers + registry evidence sync for W4 batches | TODO | code diff + `docs/capabilities/CAPABILITY_REGISTRY.yaml` | three batches (61/33/29) |
| T3 | Validation | Run changed-file checks and full-HOC sweep after W4 completion | TODO | command logs + sweep output | expect `280 -> 157` |
| T4 | Documentation | Publish W4 implemented artifact + queue/baseline updates + PIN | TODO | implemented md + pin path | update wave tracker |

## 6. Execution Order

1. T1
2. T2
3. T3
4. T4

## 7. Verification Commands

```bash
python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(cat backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W4_FILE_QUEUE_2026-02-21.txt)
python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(git ls-files 'backend/app/hoc/**/*.py')
python3 scripts/ops/layer_segregation_guard.py --check --scope hoc
(rg -n "^\s*from \.\." backend/app/hoc --glob '*.py' || true) | cut -d: -f1 | sort -u | wc -l
```

## 8. Risks and Rollback

- Risks:
  - Mixed capability ownership in some CUS folders may cause failed changed-file checks.
  - Registry evidence drift if headers and evidence paths are not updated together.
- Rollback plan:
  - Revert only current batch changes, re-run mapping pilot on 3-5 files, then reapply batch.

## 9. Claude Fill Rules

1. Update `Status` for each task: `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record concrete evidence path per task (file path, test output doc, or artifact).
3. If blocked, include blocker reason and minimal next action.
4. Do not delete plan sections; append execution facts.
5. Return completed results in `HOC_Blocker_Queue_W4_CUS_Domains_2026_02_21_plan_implemented.md`.
