# HOC Layer Segregation Plan (Scope: hoc, 2026-02-20)

## Final Goal
Drive `layer_segregation_guard --scope hoc` to zero violations without tombstoning any `hoc/*` debt.

## Baseline
- Source: `scripts/ops/layer_segregation_guard.py --check --scope hoc`
- Baseline at plan creation: `14` violation instances across `8` files.

## Step Plan
| Step | Goal | Status | Evidence |
|---|---|---|---|
| 1 | Record residual violating file set and exact violation lines | DONE | `.tmp_layer_now.txt` snapshot; 8 files identified |
| 2 | Remediate founder/platform residual files with safe boundary patterns | DONE | 8 residual files remediated (`fdr/*` engines + `int/platform` sandbox/memory driver) |
| 3 | Re-run layer segregation audit and verify delta | DONE | `python3 scripts/ops/layer_segregation_guard.py --check --scope hoc` -> PASS (`14 -> 0`) |
| 4 | Update blocker ledgers with before/after counts | DONE | `CI_BASELINE_BLOCKER_QUEUE_2026-02-20.md` and `CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20.md` refreshed |
| 5 | Report residual and next wave | DONE | Residual `hoc/*` layer violations: `0` |

## Implementation Rules
1. Keep runtime behavior stable.
2. No HOC tombstones.
3. Prefer compatibility wrappers or driver delegation over broad refactors.
4. Ensure changed files retain layer headers.

## Exit Criteria
- Layer violations reduced from baseline.
- No import-hygiene regressions in HOC scope.

## Outcome
- Final result: `layer_segregation_guard --scope hoc` is fully green.
- Baseline: `14` violations.
- Current: `0` violations.
- Delta: `-14`.
