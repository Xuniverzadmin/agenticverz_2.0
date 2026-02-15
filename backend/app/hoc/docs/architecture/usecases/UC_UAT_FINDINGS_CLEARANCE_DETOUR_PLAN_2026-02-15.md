# UC UAT Findings Clearance Detour Plan (2026-02-15)

## Objective
Clear the current reality-audit findings by making the UAT validation path reproducible, truthful, and CI-safe.

Primary reference:
- `backend/app/hoc/docs/architecture/usecases/UC_CODEBASE_ELICITATION_VALIDATION_UAT_REALITY_AUDIT_2026-02-15.md`

## Findings to Clear
1. Non-reproducible signoff claim: global app-shell typecheck currently fails.
2. Playwright runtime not deterministic in local app-shell environment.
3. Ambiguous gate script path references (`scripts/ops/...` vs `backend/scripts/ops/...`).

## Baseline Audit Snapshot
From `website/app-shell`:
1. `npm run typecheck` exits non-zero with `293` errors.
2. Error distribution:
 - `../fops`: `232`
 - `src`: `42`
 - `../onboarding`: `19`
3. Current UAT backend validation is already green and reproducible.

## Detour Principles
1. Do not force a fake "all green" state.
2. Separate UAT-scope enforcement from pre-existing global frontend debt.
3. Keep architecture and governance gates deterministic.
4. Publish corrected signoff with exact command outputs.

## Workstream E1: Scope-Correct Typecheck for UAT

### Tasks
1. Add UAT-scoped TS config:
 - `website/app-shell/tsconfig.uat.json`
2. Limit scope to files required by UAT console:
 - `src/features/uat/**`
 - route wiring touched by UAT (`src/routes/index.tsx` and direct UAT dependencies only)
3. Add scripts in `website/app-shell/package.json`:
 - `typecheck:uat`
 - `typecheck:global` (existing full `tsc --noEmit`, renamed or retained)
4. Keep `typecheck:global` as informational debt gate for now (non-blocking in UAT gate script), but retain report output.

### Acceptance
1. `npm run typecheck:uat` exits `0`.
2. `npm run typecheck:global` still runs and emits debt report artifact without blocking UAT release.

## Workstream E2: Playwright Determinism

### Tasks
1. Add explicit Playwright dependency in app-shell:
 - `@playwright/test` in `devDependencies`.
2. Add scripts:
 - `test:bit`
 - `test:uat`
 - `test:uat:list`
3. Validate/fix UAT Playwright config cwd and startup:
 - `website/app-shell/tests/uat/playwright.config.ts`
4. Ensure CI/local setup doc includes browser install step when needed.

### Acceptance
1. `npm run test:uat:list` executes and lists tests.
2. `npm run test:uat` is runnable in configured environment.
3. `npm run test:bit` remains runnable.

## Workstream E3: Unified Gate Script Corrections

### Tasks
1. Update:
 - `backend/scripts/ops/hoc_uc_validation_uat_gate.sh`
2. Replace blocking frontend typecheck stage:
 - from `npm run typecheck`
 - to `npm run typecheck:uat` (blocking)
3. Add global typecheck stage as non-blocking informational output with explicit warning.
4. Keep backend deterministic gates and backend UAT tests blocking.
5. Keep Playwright BIT/UAT stages blocking only when Playwright dependency and browsers are present; otherwise fail with actionable setup message (not silent skip).

### Acceptance
1. Script exit code and summary match declared policy.
2. No ambiguous path references; commands documented from repo root and backend root.

## Workstream E4: Documentation and Signoff Reconciliation

### Tasks
1. Replace or supersede signoff with corrected evidence:
 - `backend/app/hoc/docs/architecture/usecases/UC_CODEBASE_ELICITATION_VALIDATION_UAT_SIGNOFF_2026-02-15_v2.md`
2. Amend claims:
 - remove "TypeScript compilation PASS" global claim
 - add exact `typecheck:uat` pass result
 - add global typecheck debt note with counts
3. Update path references to explicit backend location:
 - `backend/scripts/ops/hoc_uc_validation_uat_gate.sh`
4. Publish closure addendum to reality audit with status per finding: `CLOSED` / `OPEN`.

### Acceptance
1. Every finding from the reality audit has a status and evidence pointer.
2. No claim in signoff contradicts executable checks.

## Workstream E5: Optional Debt Burn-Down Starter (Non-blocking)

### Tasks
1. Generate TS debt inventory artifact:
 - `backend/app/hoc/docs/architecture/usecases/APP_SHELL_TS_DEBT_INVENTORY_2026-02-15.md`
2. Group debt by bucket:
 - `src/quarantine/*`
 - cross-app imports `../fops/*`, `../onboarding/*`
 - app-shell core `src/*`
3. Create prioritized remediation waves (separate from UAT gate).

### Acceptance
1. Debt inventory exists and is separated from UAT release criteria.

## Required Output Artifacts
1. `backend/app/hoc/docs/architecture/usecases/UC_UAT_FINDINGS_CLEARANCE_DETOUR_IMPLEMENTED_2026-02-15.md`
2. `backend/app/hoc/docs/architecture/usecases/UC_CODEBASE_ELICITATION_VALIDATION_UAT_SIGNOFF_2026-02-15_v2.md`
3. `backend/app/hoc/docs/architecture/usecases/UC_CODEBASE_ELICITATION_VALIDATION_UAT_REALITY_AUDIT_ADDENDUM_2026-02-15.md`
4. Optional:
 - `backend/app/hoc/docs/architecture/usecases/APP_SHELL_TS_DEBT_INVENTORY_2026-02-15.md`

## Deterministic Verification Commands
From `/root/agenticverz2.0/backend`:
1. `PYTHONPATH=. python3 scripts/verification/uc_operation_manifest_check.py --strict`
2. `PYTHONPATH=. pytest -q tests/governance/t4/test_uc_mapping_decision_table.py tests/governance/t4/test_uc_operation_manifest_integrity.py`
3. `PYTHONPATH=. pytest -q tests/uat/test_uc002_onboarding_flow.py tests/uat/test_uc004_controls_evidence.py tests/uat/test_uc006_signal_feedback_flow.py tests/uat/test_uc008_analytics_artifacts.py tests/uat/test_uc017_trace_replay_integrity.py tests/uat/test_uc032_redaction_export_safety.py`
4. `./scripts/ops/hoc_uc_validation_uat_gate.sh`

From `/root/agenticverz2.0/website/app-shell`:
1. `npm run typecheck:uat`
2. `npm run typecheck:global` (informational, non-blocking for this detour)
3. `npm run test:uat:list`
4. `npm run test:bit`
5. `npm run test:uat`

## Definition of Done
1. All three findings are closed with reproducible evidence.
2. UAT gate is deterministic and aligned to declared scope.
3. New signoff matches real executable outcomes.
4. Index updated with this detour and resulting closure artifacts.

