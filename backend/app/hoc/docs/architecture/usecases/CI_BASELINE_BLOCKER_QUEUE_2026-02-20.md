# CI_BASELINE_BLOCKER_QUEUE_2026-02-20

## Scope
Baseline blockers on `origin/main` after merge commit `da89f8d479bae9c1930be25e5cac3d8c892ba13e`.

## Source Runs (main)
- CI: `https://github.com/Xuniverzadmin/agenticverz_2.0/actions/runs/22221850390`
- CI Preflight: `https://github.com/Xuniverzadmin/agenticverz_2.0/actions/runs/22221850380`
- DB Authority Guard: `https://github.com/Xuniverzadmin/agenticverz_2.0/actions/runs/22221850399`
- Layer Segregation Guard: `https://github.com/Xuniverzadmin/agenticverz_2.0/actions/runs/22221850385`
- Import Hygiene Check: `https://github.com/Xuniverzadmin/agenticverz_2.0/actions/runs/22221850419`
- Truth Preflight Gate: `https://github.com/Xuniverzadmin/agenticverz_2.0/actions/runs/22221850368`
- Mypy Autofix: `https://github.com/Xuniverzadmin/agenticverz_2.0/actions/runs/22221850405`
- SQLModel Pattern Linter: `https://github.com/Xuniverzadmin/agenticverz_2.0/actions/runs/22221850402`
- Integration Integrity: `https://github.com/Xuniverzadmin/agenticverz_2.0/actions/runs/22221850398`

## Active Blockers
| Priority | Workflow/Job | Failure Signal | Candidate Fix Direction |
|---|---|---|---|
| P0 | CI Preflight / Consistency Check | multiple alembic revision IDs exceed 32 chars (`Revision too long ...`) | either relax invariant in consistency script or normalize historical revision-id policy |
| P0 | DB Authority Guard / DB-AUTH-001 | `.env.example` missing `DB_AUTHORITY` | add `DB_AUTHORITY=` to `.env.example` (and align env files) |
| P0 | Truth Preflight / Truth Preflight (BLOCKING) | cannot reach backend at `http://localhost:8000`; script exits fail-closed | stabilize backend startup wait/health probing and truth-preflight preconditions |
| P1 | Layer Segregation Guard / Enforce L4/L6 Boundaries | `Run Layer Segregation Guard` fails (99 violations baseline) | clear violations under `backend/app/hoc/**`; tombstone non-hoc legacy files |
| P1 | Import Hygiene Check / Import Hygiene | **RESOLVED (Wave 2 complete):** HOC relative imports reduced to `0` | keep non-HOC relative-import debt tombstoned and prevent regressions |
| P1 | SQLModel Pattern Linter / SQLModel Pattern Lint (Full) | DB guard violation in linter execution context | fix linter invocation env/DB_AUTHORITY contract |
| P1 | Mypy Autofix / Mypy Type Safety | fails during `Set up Python` (workflow/tooling path) | repair workflow/tool bootstrap |
| P1 | CI / run-migrations | `DB ROLE GATE: BLOCKED` in alembic migration job | align CI migration role/auth setup to expected DB role gate |
| P1 | CI / unit-tests | pytest internal error during skill tests collection | debug test plugin/collection stack trace and hard-fail condition |
| P2 | CI / env-misuse-guard | baseline violations above configured cap | reduce violations or reset baseline cap with ratified policy |
| P2 | CI / sql-misuse-guard | detects `session.exec(text())` misuse | patch offending call sites |
| P2 | CI / layer-enforcement | L5->L4 violations + missing layer headers | remediate boundary violations + annotate headers |
| P2 | CI / priority5-intent-guard | multiple `FILE_MISSING` | add/restore required intent files or adjust guard config |
| P2 | CI / claude-authority-guard | `CLAUDE_AUTHORITY.md` hash mismatch without ratification | ratify/update hash or restore ratified authority file |
| P2 | Integration Integrity / LIT tests | `Run LIT tests` fail | fix failing `tests/lit` assertions and seam contracts |

## HOC-Only Remediation Scope (2026-02-20)
- Active cleanup scope is now `backend/app/hoc/**`.
- Non-`hoc/*` violations are explicitly tombstoned as legacy debt and tracked in:
  - `backend/app/hoc/docs/architecture/usecases/CI_NON_HOC_TOMBSTONE_LEDGER_2026-02-20.md`
- Enforcement updates for this split:
  - `.github/workflows/layer-segregation.yml` runs `layer_segregation_guard.py --scope hoc`
  - `.github/workflows/import-hygiene.yml` scans `backend/app/hoc/**` only
  - `.github/workflows/capability-registry.yml` capability-linkage scans `backend/app/hoc/**/*.py` only

## Wave Progress (2026-02-20)
- HOC capability-linkage remediation Wave 1 is complete:
  - `MISSING_CAPABILITY_ID` in `backend/app/hoc/**` reduced from `5` to `0`.
  - Evidence + registry linkage updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_CAPABILITY_LINKAGE_WAVE1_REMEDIATION_2026-02-20.md`
- HOC import-hygiene remediation Wave 2 (CUS scope batch) is complete:
  - Relative imports in `backend/app/hoc/cus/**` reduced from `4` to `0`.
  - HOC total relative-import backlog reduced from `34` files to `30` files.
  - Evidence updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_IMPORT_HYGIENE_WAVE2_CUS_STABILIZATION_2026-02-20.md`
- HOC import-hygiene remediation Wave 2 (API/Auth stabilization batch) is complete:
  - Relative imports remediated in 5 HOC files (`api/cus`, `api/int`, `int/agent`, `int/general`).
  - HOC total relative-import backlog reduced from `30` files to `25` files.
  - Capability-linkage metadata wired for remediated files (CAP-014, CAP-008, CAP-007).
  - Evidence updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_IMPORT_HYGIENE_WAVE2_BATCH2_API_AUTH_STABILIZATION_2026-02-20.md`
- HOC import-hygiene remediation Wave 2 (INT/agent cluster batch) is complete:
  - Relative imports remediated in 14 HOC files under `backend/app/hoc/int/agent/**`.
  - HOC total relative-import backlog reduced from `25` files to `11` files.
  - Capability-linkage metadata wired for remediated files (CAP-008, CAP-016) and registry evidence synchronized.
  - Evidence updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_IMPORT_HYGIENE_WAVE2_BATCH3_INT_AGENT_CLUSTER_2026-02-20.md`
- HOC import-hygiene remediation Wave 2 (remaining residual cluster batch) is complete:
  - Relative imports remediated in final 10 HOC files (`int/analytics`, `int/general`, `int/logs`, `int/platform`, `int/policies`).
  - HOC total relative-import backlog reduced from `10` files to `0` files.
  - CUS relative-import backlog remains `0`.
  - Capability-linkage metadata and registry evidence synchronized (CAP-007, CAP-009, CAP-010, CAP-012, CAP-014).
  - Evidence updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_IMPORT_HYGIENE_WAVE2_BATCH4_REMAINING_CLUSTER_2026-02-20.md`

## Notes
- This queue is baseline debt on `main`, not introduced solely by PR #7.
- Lane A should address P0 first, then P1 in smallest reviewable PRs.
- Skeptical audit (2026-02-20) confirms changed-file capability linkage is clear for HOC remediation PRs, while full HOC-wide capability scan still reports `972` historical `MISSING_CAPABILITY_ID` blockers outside current CI changed-file contract.
