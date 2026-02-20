# PR1_PR10_COURSE_CORRECTION_PLAN_2026-02-20

## Final Goal
Deliver internal PR-1..PR-10 vertical slices to `origin/main` as clean, scoped, reviewable PRs, while stabilizing baseline CI enough to support deterministic merge flow.

## Workstream Model
- **Lane A**: CI baseline stabilization (repo-wide failing gates already red on `main`)
- **Lane B**: PR-1..PR-10 backend/frontend slice recovery (clean worktree PR sequence)

## Step Plan and Implementation Status
| Step | Goal | Status | Evidence |
|---|---|---|---|
| 1 | Rebaseline snapshot (`main` truth + source branch divergence + merged PR history) | DONE | `git rev-list --left-right --count origin/main...hoc/pr1-runs-facade-contract-hardening` => `14/11`; `gh pr list` confirms merged PRs #3-#7 |
| 2 | Build salvage matrix for PR-1..PR-10 artifacts | DONE | `backend/app/hoc/docs/architecture/usecases/PR1_PR10_SALVAGE_MATRIX_2026-02-20.md`; raw detail `/tmp/pr1_pr10_salvage_matrix.psv` |
| 3 | Initialize two recovery lanes in clean worktrees | DONE | `/tmp/ws-a-ci-baseline-20260220` on branch `hoc/ws-a-ci-baseline-stabilization`; `/tmp/ws-b-pr1-pr10-20260220` on branch `hoc/ws-b-pr1-pr10-slice-recovery` |
| 4 | Lane A: enumerate current `main` CI blockers and convert to fix queue | DONE | `backend/app/hoc/docs/architecture/usecases/CI_BASELINE_BLOCKER_QUEUE_2026-02-20.md`; `backend/app/hoc/docs/architecture/usecases/CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20.md`; `.github/workflows/{layer-segregation,import-hygiene,capability-registry}.yml` |
| 5 | Lane B: execute first clean recovery PR (PR-2 incidents) from `origin/main` | DONE | worktree `/tmp/pr2-incidents-recovery-20260220`; branch `hoc/pr2-incidents-list-recovery-clean`; commit `7df3db90`; PR `https://github.com/Xuniverzadmin/agenticverz_2.0/pull/8` |
| 6 | Continue per-slice recovery PRs (PR-10 then PR-1, PR-3..PR-9 as rebuilt slices) | DONE | PRs opened: #11 (PR-10), #12 (PR-1), #13 (PR-3), #14 (PR-4), #15 (PR-5), #16 (PR-6), #17 (PR-7), #18 (PR-8), #19 (PR-9); existing #8 (PR-2) |
| 7 | Sync frontend slice ledgers after corresponding backend merges | DONE | `backend/app/hoc/docs/architecture/usecases/PR1_PR10_STEP7_FRONTEND_LEDGER_SYNC_2026-02-20.md` |

## Immediate Execution Order
1. Merge and close Lane A baseline PR (`#9`) after reviewer sign-off.
2. Merge and close governance scope/tombstone PR (`#10`) after Step 7 doc sync validation.

## Notes
- `origin/main` is immutable truth source.
- `hoc/pr1-runs-facade-contract-hardening` is salvage source only and will not be merged directly.
