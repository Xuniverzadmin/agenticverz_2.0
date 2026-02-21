# HOC_Blocker_Queue_W6_Long_Tail_2026_02_21_plan

**Created:** 2026-02-21 05:21:04 UTC
**Executor:** Claude
**Status:** DRAFT

## 1. Objective

- Primary outcome: Clear W6 long-tail `MISSING_CAPABILITY_ID` backlog (`74` files).
- Business/technical intent: Bring full-HOC blockers from `74` to `0`.

## 2. Scope

- In scope:
  - `backend/app/hoc/int/recovery/**`
  - `backend/app/hoc/int/logs/**`
  - `backend/app/hoc/int/integrations/**`
  - `backend/app/hoc/int/incidents/**`
  - `backend/app/hoc/int/analytics/**`
  - `backend/app/hoc/int/activity/**`
  - `backend/app/hoc/int/account/**`
  - `backend/app/hoc/int/__init__.py`
  - `backend/app/hoc/fdr/ops/**`
  - `backend/app/hoc/fdr/logs/**`
  - `backend/app/hoc/fdr/agent/**`
  - `backend/app/hoc/fdr/account/**`
  - `backend/app/hoc/fdr/platform/**`
  - `backend/app/hoc/fdr/__init__.py`
- Out of scope:
  - previously completed waves (W1-W5)

## 3. Assumptions and Constraints

- Assumptions:
  - W5 completed and backlog entering W6 is exactly `74`.
  - Queue artifact covers all remaining blockers.
- Constraints:
  - Metadata/evidence remediation only.
- Non-negotiables:
  - End-state full-HOC blockers `0`, warnings `0`.
  - Layer/import guards remain green.

## 4. Acceptance Criteria

1. W6 queue file reaches `0`.
2. Full-HOC blockers reach `0`.
3. Changed-file and full-sweep checks pass with zero warnings.

## 5. Task Matrix (Claude Fill)

| Task ID | Workstream | Task | Status | Evidence Path | Notes |
|---------|------------|------|--------|---------------|-------|
| T1 | Setup | Lock W6 A/B/C batch queues (24/22/28) | TODO | `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W6_FILE_QUEUE_2026-02-21.txt` | |
| T2 | Core | Apply capability headers + registry evidence for each W6 batch | TODO | code + registry diffs | |
| T3 | Validation | Run changed-file checks, then full sweep for zero blockers | TODO | sweep logs | target `74 -> 0` |
| T4 | Documentation | Publish W6 implemented artifact and update queue trackers | TODO | implemented md + docs | |

## 6. Execution Order

1. T1
2. T2
3. T3
4. T4

## 7. Verification Commands

```bash
python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(cat backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W6_FILE_QUEUE_2026-02-21.txt)
python3 scripts/ops/capability_registry_enforcer.py check-pr --files $(git ls-files 'backend/app/hoc/**/*.py')
python3 scripts/ops/layer_segregation_guard.py --check --scope hoc
(rg -n "^\s*from \.\." backend/app/hoc --glob '*.py' || true) | cut -d: -f1 | sort -u | wc -l
```

## 8. Risks and Rollback

- Risks:
  - Remaining files are long-tail and may have weaker mapping examples.
  - FDR/INT cross-lane evidence updates can be missed.
- Rollback plan:
  - Revert failed batch changes and re-run with smaller sub-batches by folder.

## 9. Claude Fill Rules

1. Update `Status` for each task: `DONE`, `PARTIAL`, `BLOCKED`, or `SKIPPED`.
2. Record concrete evidence path per task (file path, test output doc, or artifact).
3. If blocked, include blocker reason and minimal next action.
4. Do not delete plan sections; append execution facts.
5. Return completed results in `HOC_Blocker_Queue_W6_Long_Tail_2026_02_21_plan_implemented.md`.
