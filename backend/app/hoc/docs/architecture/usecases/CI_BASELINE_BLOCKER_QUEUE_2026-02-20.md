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
- Active `hoc/*` blocker queue is tracked in:
  - `backend/app/hoc/docs/architecture/usecases/HOC_ACTIVE_BLOCKER_QUEUE_2026-02-20.md`
- Active `hoc/*` wave execution plan is tracked in:
  - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_WAVE_PLAN_2026-02-20.md`
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
- HOC layer/capability remediation Wave 1 (INT/agent engine hotspot) is complete:
  - Replaced 7 DB-heavy HOC engine modules with compatibility wrappers to canonical service/driver implementations.
  - Layer-segregation backlog reduced from `93` to `14` violation instances.
  - Full HOC capability sweep reduced from `972` to `965` blocking `MISSING_CAPABILITY_ID`.
  - Evidence updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_LAYER_CAPABILITY_REMEDIATION_WAVE1_IMPLEMENTED_2026-02-20.md`
- HOC layer/capability remediation Wave 2 (residual closure) is complete:
  - Remediated remaining 8 `hoc/*` layer-segregation residual files (`fdr/*` engines + `int/platform` sandbox/memory).
  - Layer-segregation (`--scope hoc`) reduced from `14` to `0` violations.
  - Full HOC capability sweep reduced from `965` to `929` blocking `MISSING_CAPABILITY_ID`.
  - Full HOC capability warnings remain `13`.
  - Wave plans updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_LAYER_SEGREGATION_SCOPE_HOC_PLAN_2026-02-20.md`
    - `backend/app/hoc/docs/architecture/usecases/HOC_CAPABILITY_SWEEP_PLAN_2026-02-20.md`
- HOC CUS capability sweep Wave C1 is complete:
  - Scope: `cus/hoc_spine/orchestrator/**` + `cus/hoc_spine/authority/contracts/**`.
  - Capability header wiring: `CAP-012` (orchestrator), `CAP-011` (authority contracts).
  - Full HOC capability sweep reduced from `929` to `851` blocking `MISSING_CAPABILITY_ID`.
  - Full HOC capability warnings remain `13`.
  - Changed-file capability check passed for all C1 remediated files.
  - Plan updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_CUS_CAPABILITY_SWEEP_WAVES_PLAN_2026-02-20.md`
- HOC CUS capability sweep Wave C2 is complete:
  - Scope: `cus/policies/L5_engines/**` + `cus/policies/L6_drivers/**` + `api/cus/policies/**`.
  - Capability header wiring: `CAP-009` (policy engine), `CAP-003` (`policy_proposals.py`), `CAP-007` (`rbac_api.py`).
  - CAP-001/CAP-018 evidence linkage repaired for:
    - `backend/app/hoc/api/cus/policies/replay.py`
    - `backend/app/hoc/api/cus/policies/M25_integrations.py`
  - Full HOC capability sweep reduced from `851` to `728` blocking `MISSING_CAPABILITY_ID`.
  - Full HOC capability warnings reduced from `13` to `11`.
  - Changed-file capability check passed for all C2 remediated files.
  - Plan updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_CUS_CAPABILITY_SWEEP_WAVES_PLAN_2026-02-20.md`
- HOC CUS capability sweep Wave C3 is complete:
  - Scope: `cus/logs/**` + `cus/analytics/**` + `cus/incidents/**` + `cus/integrations/**`.
  - Capability header wiring:
    - `CAP-001` for logs and incidents surfaces.
    - `CAP-002` for analytics surfaces.
    - `CAP-018` for integrations surfaces.
  - Full HOC capability sweep reduced from `728` to `550` blocking `MISSING_CAPABILITY_ID`.
  - Full HOC capability warnings remain `11`.
  - Changed-file capability check passed for all C3 remediated files.
  - Plan updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_CUS_CAPABILITY_SWEEP_WAVES_PLAN_2026-02-20.md`
- HOC CUS capability sweep Wave C4 (warning cleanup) is complete:
  - Scope: full-HOC `MISSING_EVIDENCE` backlog after C3.
  - Registry evidence synchronized for CAP-001, CAP-006, CAP-018 warning set.
  - Full HOC capability warnings reduced from `11` to `0`.
  - Full HOC capability blocking remains `550` (`MISSING_CAPABILITY_ID` backlog).
  - Plan updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_CUS_CAPABILITY_SWEEP_WAVES_PLAN_2026-02-20.md`
- HOC blocker queue Wave W1 (`hoc_spine`) is complete:
  - Scope: `backend/app/hoc/cus/hoc_spine/**` (`101` files).
  - Capability header wiring:
    - `CAP-011` (`auth_wiring.py` + `authority/**`)
    - `CAP-012` (remaining `hoc_spine/**`)
  - Registry evidence synchronized for CAP-011/CAP-012 in:
    - `docs/capabilities/CAPABILITY_REGISTRY.yaml`
  - Full HOC capability sweep reduced from `550` to `449` blocking `MISSING_CAPABILITY_ID`.
  - Full HOC capability warnings remain `0`.
  - Plan/artifacts updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_WAVE_PLAN_2026-02-20.md`
    - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W1_HOC_SPINE_IMPLEMENTED_2026-02-20.md`
    - `backend/app/hoc/docs/architecture/usecases/HOC_ACTIVE_BLOCKER_QUEUE_2026-02-20.md`
- HOC blocker queue Wave W2 (`int/platform` + `int/agent`) is complete:
  - Scope: `backend/app/hoc/int/platform/**` + `backend/app/hoc/int/agent/**` (`91` files).
  - Capability header wiring:
    - `CAP-008` (`int/agent/**`)
    - `CAP-012` (`int/platform/**`)
  - Registry evidence synchronized for CAP-008/CAP-012 in:
    - `docs/capabilities/CAPABILITY_REGISTRY.yaml`
  - Full HOC capability sweep reduced from `449` to `358` blocking `MISSING_CAPABILITY_ID`.
  - Full HOC capability warnings remain `0`.
  - Plan/artifacts updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_WAVE_PLAN_2026-02-20.md`
    - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W2_INT_PLATFORM_AGENT_IMPLEMENTED_2026-02-20.md`
    - `backend/app/hoc/docs/architecture/usecases/HOC_ACTIVE_BLOCKER_QUEUE_2026-02-20.md`
- HOC blocker queue Wave W3 (`int/general` + `int/worker` + `int/policies`) is complete:
  - Scope: `backend/app/hoc/int/general/**` + `backend/app/hoc/int/worker/**` + `backend/app/hoc/int/policies/**` (`78` files).
  - Capability header wiring:
    - `CAP-006` (`int/general/**`)
    - `CAP-012` (`int/worker/**`)
    - `CAP-009` (`int/policies/**`)
  - Registry evidence synchronized for CAP-006/CAP-009/CAP-012 in:
    - `docs/capabilities/CAPABILITY_REGISTRY.yaml`
  - Full HOC capability sweep reduced from `358` to `280` blocking `MISSING_CAPABILITY_ID`.
  - Full HOC capability warnings remain `0`.
  - Plan/artifacts updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_WAVE_PLAN_2026-02-20.md`
    - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W3_INT_GENERAL_WORKER_POLICIES_IMPLEMENTED_2026-02-20.md`
    - `backend/app/hoc/docs/architecture/usecases/HOC_ACTIVE_BLOCKER_QUEUE_2026-02-20.md`
- HOC blocker queue Wave W4 (CUS internals) is complete:
  - Scope: `backend/app/hoc/cus/account/**` + `cus/activity/**` + `cus/controls/**` + `cus/policies/**` + `cus/api_keys/**` + `cus/overview/**` + `cus/ops/**` + `cus/agent/**` + `cus/apis/**` + `cus/__init__.py` (`123` files).
  - Capability header wiring:
    - `CAP-012` (`account/activity/overview/ops/apis/__init__`)
    - `CAP-009` (`controls/policies`)
    - `CAP-006` (`api_keys`)
    - `CAP-008` (`agent`)
  - Registry evidence synchronized in:
    - `docs/capabilities/CAPABILITY_REGISTRY.yaml`
  - Full HOC capability sweep reduced from `280` to `157` blocking `MISSING_CAPABILITY_ID`.
  - Full HOC capability warnings remain `0`.
  - Plan/artifacts updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_WAVE_PLAN_2026-02-20.md`
    - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W4_CUS_DOMAINS_IMPLEMENTED_2026-02-21.md`
    - `backend/app/hoc/docs/architecture/usecases/HOC_ACTIVE_BLOCKER_QUEUE_2026-02-20.md`
- HOC blocker queue Wave W5 (API lanes) is complete:
  - Scope: `backend/app/hoc/api/cus/**` + `api/facades/**` + `api/int/**` + `api/fdr/**` (`83` files).
  - Capability header wiring:
    - `CAP-012` (`api/cus`, `api/facades`, `api/int`)
    - `CAP-005` (`api/fdr`)
  - Registry evidence synchronized in:
    - `docs/capabilities/CAPABILITY_REGISTRY.yaml`
  - Full HOC capability sweep reduced from `157` to `74` blocking `MISSING_CAPABILITY_ID`.
  - Full HOC capability warnings remain `0`.
  - Plan/artifacts updated in:
    - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_WAVE_PLAN_2026-02-20.md`
    - `backend/app/hoc/docs/architecture/usecases/HOC_BLOCKER_QUEUE_W5_API_LANES_IMPLEMENTED_2026-02-21.md`
    - `backend/app/hoc/docs/architecture/usecases/HOC_ACTIVE_BLOCKER_QUEUE_2026-02-20.md`

## Notes
- This queue is baseline debt on `main`, not introduced solely by PR #7.
- Lane A should address P0 first, then P1 in smallest reviewable PRs.
- Skeptical audit (2026-02-21) confirms changed-file capability linkage is clear for HOC remediation PRs; after blocker Wave W5, full HOC-wide capability scan remains a separate backlog at `74` blocking `MISSING_CAPABILITY_ID` (warnings `0`) outside current CI changed-file contract.
