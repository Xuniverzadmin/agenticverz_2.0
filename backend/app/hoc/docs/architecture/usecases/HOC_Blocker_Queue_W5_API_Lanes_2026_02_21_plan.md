# HOC_Blocker_Queue_W5_API_Lanes_2026_02_21_plan

**Created:** 2026-02-21 05:21:04 UTC
**Executor:** Claude
**Status:** COMPLETED

## 1. Objective

- Primary outcome: Clear W5 API-lane `MISSING_CAPABILITY_ID` backlog (`83` files).
- Business/technical intent: Reduce full-HOC blockers from `157` to `74` while holding governance guards green.

## 2. Scope

- In scope:
  - `backend/app/hoc/api/cus/**`
  - `backend/app/hoc/api/facades/**`
  - `backend/app/hoc/api/int/**`
  - `backend/app/hoc/api/fdr/**`
- Out of scope:
  - CUS internal domains (W4)
  - INT/FDR long-tail non-API clusters (W6)

## 3. Assumptions and Constraints

- Assumptions:
  - W4 is complete before W5 starts.
  - API capability mappings mirror owning domain/facade.
- Constraints:
  - No API behavior refactor; metadata/evidence only.
- Non-negotiables:
  - Layer segregation `0`.
  - HOC relative imports `0`.
  - Capability warnings `0`.

## 4. Acceptance Criteria

1. W5 queue file reaches `0`.
2. Full-HOC blockers reduce from `157` to `74`.
3. Changed-file capability checks pass for all W5 batches.

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| T1 | Setup | Validate W5 queue and split into A/B/C batches (34/22/27) | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W5_FILE_QUEUE_2026-02-21.txt` | |
| T2 | Core | Apply capability headers and registry evidence updates across W5 batches | TODO | code diff + registry diff | |
| T3 | Validation | Run changed-file checks per batch and full-HOC sweep post-W5 | TODO | sweep logs | expect `157 -> 74` |
| T4 | Documentation | Publish W5 implemented artifact and update queue trackers | TODO | implemented md + tracker docs | |

## 6. Execution Order

1. T1
2. T2
3. T3
4. T4

## 7. Verification Commands

```bash
python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(cat backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W5_FILE_QUEUE_2026-02-21.txt)
python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(git ls-files 'backend/app/hoc/**/*.py')
python3 scripts/ops/layer_segregation_guard.py --check --scope hoc
(rg -n "^\s*from \.\." backend/app/hoc --glob '*.py' || true) | cut -d: -f1 | sort -u | wc -l
```

## 8. Risks and Rollback

- Risks:
  - API folders with mixed capability usage may fail initial mapping.
  - Facade and API evidence lists can drift without synchronized edits.
- Rollback plan:
  - Roll back failed batch only, re-run mapping on smallest failing subfolder, re-apply.

## 9. Claude Fill Rules

1. Update `Status` for each task: `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record concrete evidence path per task (file path, test output doc, or artifact).
3. If blocked, include blocker reason and minimal next action.
4. Do not delete plan sections; append execution facts.
5. Return completed results in `HOC_Blocker_Queue_W5_API_Lanes_2026_02_21_plan_implemented.md`.
