# UC Codebase Elicitation + Validation + UAT Taskpack (2026-02-15)

## Goal
Create a deterministic path from script-level UC mapping to executable validation tests and frontend UAT flows, without force-fitting scripts into incorrect UC ownership.

## Required Context Load (Do First)
1. `codex_agents_agenticverz2.md`
2. `project_aware_agenticverz2.md`
3. `vision_mission_self_audit.md`
4. `architecture/topology/HOC_LAYER_TOPOLOGY_V2.0.0.md`
5. `docs/architecture/architecture_core/LAYER_MODEL.md`
6. `docs/architecture/architecture_core/DRIVER_ENGINE_PATTERN_LOCKED.md`
7. Domain docs in scope:
 - `literature/hoc_domain/activity/SOFTWARE_BIBLE.md`
 - `literature/hoc_domain/analytics/SOFTWARE_BIBLE.md`
 - `literature/hoc_domain/controls/SOFTWARE_BIBLE.md`
 - `literature/hoc_domain/incidents/SOFTWARE_BIBLE.md`
 - `literature/hoc_domain/integrations/SOFTWARE_BIBLE.md`
 - `literature/hoc_domain/logs/SOFTWARE_BIBLE.md`

## Baseline Inputs
1. `backend/app/hoc/docs/architecture/usecases/HOC_CUS_UC_MATCH_ITERATION1_2026-02-15.csv`
2. `backend/app/hoc/docs/architecture/usecases/HOC_CUS_UC_MATCH_ITERATION2_SKEPTICAL_2026-02-15.md`
3. `backend/app/hoc/docs/architecture/usecases/HOC_CUS_UC_MATCH_ITERATION2_FLAGS_2026-02-15.csv`
4. `backend/app/hoc/docs/architecture/usecases/HOC_CUS_UC_MATCH_ITERATION3_DECISION_TABLE_2026-02-15.csv`
5. `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`
6. `backend/app/hoc/docs/architecture/usecases/UC_MONITORING_ROUTE_OPERATION_MAP.md`

## Current Truth Snapshot
1. Iteration-3 scope: 30 unresolved rows from Iteration-1.
2. Decisions: `ASSIGN=7`, `SPLIT=8`, `HOLD=15`.
3. No new UC IDs discovered; all decisions map within existing `UC-001..UC-040`.
4. No forced single-UC mapping for ambiguous scripts (`HOLD`/`SPLIT` preserved).

## Non-Negotiable Architecture Rules
1. Preserve layering: `L2.1 -> L2 -> L4 -> L5 -> L6 -> L7`.
2. No direct `L2 -> L5/L6` business calls.
3. Business decisions live in L5; side effects/persistence live in L6.
4. No DB/ORM imports in L5 engines.
5. No business conditionals in L6 drivers.
6. Preserve router -> handler -> engine -> driver contract boundaries.

## Deterministic Gate Pack
Run from `/root/agenticverz2.0/backend`:
1. `PYTHONPATH=. python3 scripts/ops/hoc_cross_domain_validator.py --output json`
2. `PYTHONPATH=. python3 scripts/ci/check_layer_boundaries.py`
3. `PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci`
4. `PYTHONPATH=. python3 scripts/ops/l5_spine_pairing_gap_detector.py --json`
5. `PYTHONPATH=. python3 scripts/verification/uc_mon_validation.py --strict`
6. `PYTHONPATH=. pytest -q tests/governance/t4/test_uc018_uc032_expansion.py`

## Workstream A: Mapping Closure (No Force-Fit)

### A1) Lock the 7 ASSIGN Rows into Canonical Linkage
Rows:
1. `app/hoc/cus/activity/L5_engines/signal_feedback_engine.py -> UC-006`
2. `app/hoc/cus/activity/L6_drivers/signal_feedback_driver.py -> UC-006`
3. `app/hoc/cus/analytics/L6_drivers/analytics_artifacts_driver.py -> UC-008`
4. `app/hoc/cus/controls/L6_drivers/evaluation_evidence_driver.py -> UC-004`
5. `app/hoc/cus/hoc_spine/authority/onboarding_policy.py -> UC-002`
6. `app/hoc/cus/hoc_spine/orchestrator/handlers/onboarding_handler.py -> UC-002`
7. `app/hoc/cus/integrations/L6_drivers/connector_registry_driver.py -> UC-002`

Tasks:
1. Update corresponding UC sections in `HOC_USECASE_CODE_LINKAGE.md` with explicit script anchors and evidence notes.
2. Add/adjust governance assertions so each assignment is verified by handler operation names and at least one test reference.
3. Record acceptance evidence in a new artifact:
 - `backend/app/hoc/docs/architecture/usecases/UC_ASSIGN_LOCK_WAVE1_2026-02-15_implemented.md`

Acceptance:
1. All 7 rows have explicit canonical anchors in linkage doc.
2. Gate pack passes with no new architecture violations.
3. Evidence artifact includes proof table: script, operation(s), test refs, gate outputs.

### A2) Resolve the 8 SPLIT Rows with Explicit Multi-UC Contract
Rows:
1. `event_schema_contract.py -> UC-001|UC-002`
2. `activity_handler.py -> UC-001|UC-006|UC-010`
3. `controls_handler.py -> UC-004|UC-021`
4. `incidents_handler.py -> UC-007|UC-011|UC-031`
5. `policies_handler.py -> UC-018|UC-019|UC-020|UC-021|UC-022|UC-023`
6. `trace_api_engine.py -> UC-003|UC-017`
7. `pg_store.py -> UC-003|UC-017`
8. `trace_store.py -> UC-017|UC-032`

Tasks:
1. Add a per-operation mapping matrix for each split script:
 - operation name
 - handler function
 - engine/driver touchpoint
 - assigned UC
2. Decide per row:
 - keep as shared multi-UC script with explicit operation partition, or
 - refactor into UC-scoped components (if ownership is too broad).
3. Add tests for operation-to-UC partition invariants.
4. Publish artifact:
 - `backend/app/hoc/docs/architecture/usecases/UC_SPLIT_PARTITION_PLAN_2026-02-15_implemented.md`

Acceptance:
1. Every split script has operation-level UC partition documented.
2. No split row remains ambiguous at operation granularity.
3. Gate pack passes.

### A3) Triage the 15 HOLD Rows into Evidence Backlog
Tasks:
1. For each HOLD row, define one of:
 - `EVIDENCE_PENDING` (needs stronger proof),
 - `NON_UC_SUPPORT` (infra/helper),
 - `REFACTOR_REQUIRED` (too broad to map safely).
2. Add targeted next evidence action:
 - handler operation extraction,
 - route-map extension,
 - missing test instrumentation.
3. Publish artifact:
 - `backend/app/hoc/docs/architecture/usecases/UC_HOLD_TRIAGE_BACKLOG_2026-02-15.md`

Acceptance:
1. All 15 HOLD rows carry a deterministic next action and owner label.
2. No HOLD row is silently dropped.

## Workstream B: Backend Validation Suite (UC as Executable Contract)

### B1) Introduce a UC Operation Manifest
Create:
1. `backend/app/hoc/docs/architecture/usecases/UC_OPERATION_MANIFEST_2026-02-15.json`
2. `backend/scripts/verification/uc_operation_manifest_check.py`

Manifest minimum schema per entry:
1. `uc_id`
2. `operation_name`
3. `route_path`
4. `handler_file`
5. `engine_or_driver_files`
6. `test_refs`
7. `decision_type` (`ASSIGN|SPLIT|HOLD`)

Tasks:
1. Seed manifest from Iteration-3 CSV + route-operation map.
2. Add validator to fail on:
 - missing handler for mapped operation,
 - missing test refs for `ASSIGN`,
 - unknown UC ID,
 - duplicated conflicting mappings.

Acceptance:
1. Validator is deterministic and exits non-zero on contract drift.
2. Manifest covers all 30 Iteration-3 rows.

### B2) Add Governance Tests for UC Mapping Integrity
Create/extend tests:
1. `backend/tests/governance/t4/test_uc_mapping_decision_table.py`
2. `backend/tests/governance/t4/test_uc_operation_manifest_integrity.py`

Required assertions:
1. ASSIGN rows have exactly one canonical UC.
2. SPLIT rows have explicit per-operation partition.
3. HOLD rows are not assigned a canonical UC without evidence delta.
4. Every mapped operation exists in route-operation map or handler registry evidence.

Acceptance:
1. New tests pass locally.
2. Tests fail if mapping file is edited without evidence sync.

### B3) Add Scenario Validation Tests for UAT-critical UCs
Priority UC set:
1. `UC-002`
2. `UC-004`
3. `UC-006`
4. `UC-008`
5. `UC-017`
6. `UC-032`

Create scenario tests:
1. `backend/tests/uat/test_uc002_onboarding_flow.py`
2. `backend/tests/uat/test_uc004_controls_evidence.py`
3. `backend/tests/uat/test_uc006_signal_feedback_flow.py`
4. `backend/tests/uat/test_uc008_analytics_artifacts.py`
5. `backend/tests/uat/test_uc017_trace_replay_integrity.py`
6. `backend/tests/uat/test_uc032_redaction_export_safety.py`

Acceptance:
1. Each test covers happy path + one fail path.
2. Each test emits deterministic evidence IDs/logs for UAT display.

## Workstream C: Frontend UAT Console in `website/app-shell`

### C1) Add UAT Panel Contract and Routing
Targets:
1. Add a new UAT panel route under existing app-shell projection model.
2. Keep V2 constitution source of truth in sync:
 - `design/v2_constitution/ui_projection_lock.json`
 - `website/app-shell/src/contracts/ui_plan_scaffolding.ts`

Create:
1. `website/app-shell/src/features/uat/UcUatConsolePage.tsx`
2. `website/app-shell/src/features/uat/UcUatResultCard.tsx`
3. `website/app-shell/src/features/uat/UcUatEvidencePanel.tsx`
4. `website/app-shell/src/features/uat/ucUatClient.ts`

Acceptance:
1. UAT page loads without console errors.
2. No route namespace violations.
3. Projection checks pass.

### C2) Bind Backend Validation Data to UI
Tasks:
1. Load manifest + scenario execution results into UI state.
2. Display per UC:
 - preconditions
 - run action
 - pass/fail
 - evidence (operation, trace/event IDs, assertion summary)
3. Include filter modes:
 - `ASSIGN`
 - `SPLIT`
 - `HOLD`
 - `FAILED_LAST_RUN`

Acceptance:
1. UAT UI can run and render the 6 priority UC scenarios.
2. Evidence details are copyable and auditable.

### C3) Add Playwright UAT Regression Pack
Create:
1. `website/app-shell/tests/uat/uc-uat.spec.ts`
2. `website/app-shell/tests/uat/fixtures/uc-scenarios.json`

Assertions:
1. UAT page loads with zero console errors.
2. Scenario execution updates result cards deterministically.
3. Evidence panel renders required fields for each UC scenario.

Acceptance:
1. `npx playwright test tests/uat/uc-uat.spec.ts` passes locally.
2. BIT tests remain green (`tests/bit/bit.spec.ts`).

## Workstream D: CI and Release Criteria

### D1) Add Unified Validation Command
Create:
1. `scripts/ops/hoc_uc_validation_uat_gate.sh`

Command sequence:
1. Backend deterministic gate pack.
2. New governance tests for mapping/manifest.
3. UAT backend scenario tests.
4. App-shell guardrails:
 - `npm run hygiene:ci`
 - `npm run boundary:ci`
 - `npm run typecheck`
 - `npm run build`
5. Playwright:
 - BIT
 - UAT spec

Acceptance:
1. Script exits `0` only when all checks pass.
2. Emits concise summary with pass/fail per stage.

## New Usecase Creation Policy (Anti Force-Fit)
Create a new UC only when all are true:
1. Operation cluster cannot be semantically contained by any existing UC section.
2. Requires unique acceptance criteria and unique deterministic evidence contract.
3. Requires unique governance test coverage not shared by current UC suite.
4. Skeptical review documents why split/hold/refactor cannot solve it.

If any condition fails, do not create a new UC. Use `ASSIGN`, `SPLIT`, `HOLD`, or `NON_UC_SUPPORT`.

## Deliverables Checklist
1. Updated `HOC_USECASE_CODE_LINKAGE.md` with locked assign anchors and split partitions.
2. Iteration-3 follow-up artifacts:
 - `UC_ASSIGN_LOCK_WAVE1_2026-02-15_implemented.md`
 - `UC_SPLIT_PARTITION_PLAN_2026-02-15_implemented.md`
 - `UC_HOLD_TRIAGE_BACKLOG_2026-02-15.md`
3. Manifest + validator + governance tests.
4. 6 backend UAT scenario tests.
5. App-shell UAT panel + Playwright UAT spec.
6. Unified gate script.
7. Index updates in `backend/app/hoc/docs/architecture/usecases/INDEX.md`.

## Claude Execution Prompts (Run in Order)

### Prompt 1: Mapping Closure (A1+A2+A3)
```bash
claude -p "In /root/agenticverz2.0 execute Workstream A from backend/app/hoc/docs/architecture/usecases/UC_CODEBASE_ELICITATION_VALIDATION_UAT_TASKPACK_2026-02-15.md. Use Iteration-3 decision table as source of truth. Lock 7 ASSIGN rows into HOC_USECASE_CODE_LINKAGE.md with concrete evidence, partition 8 SPLIT rows by operation->UC mapping, and triage 15 HOLD rows into deterministic backlog statuses. Do not force-fit ambiguous scripts. Run backend deterministic gate pack and publish the 3 required artifacts exactly as named in the plan."
```

### Prompt 2: Backend Validation Suite (B1+B2+B3)
```bash
claude -p "In /root/agenticverz2.0 execute Workstream B from backend/app/hoc/docs/architecture/usecases/UC_CODEBASE_ELICITATION_VALIDATION_UAT_TASKPACK_2026-02-15.md. Create UC_OPERATION_MANIFEST_2026-02-15.json, add uc_operation_manifest_check.py, add governance tests for mapping integrity, and implement 6 backend UAT scenario tests for UC-002/004/006/008/017/032. Keep tests deterministic and architecture-safe. Run deterministic gates plus new tests and publish a results summary artifact."
```

### Prompt 3: Frontend UAT Console + Playwright (C1+C2+C3)
```bash
claude -p "In /root/agenticverz2.0 execute Workstream C from backend/app/hoc/docs/architecture/usecases/UC_CODEBASE_ELICITATION_VALIDATION_UAT_TASKPACK_2026-02-15.md. Build UAT panel(s) in website/app-shell, sync projection constitution files, bind backend validation/manifest data, and add Playwright UAT regression tests. Preserve existing frontend architecture and guardrails. Run npm hygiene/boundary/typecheck/build plus BIT and UAT tests, then publish evidence."
```

### Prompt 4: Unified Gate and Final Signoff (D1)
```bash
claude -p "In /root/agenticverz2.0 execute Workstream D from backend/app/hoc/docs/architecture/usecases/UC_CODEBASE_ELICITATION_VALIDATION_UAT_TASKPACK_2026-02-15.md. Create scripts/ops/hoc_uc_validation_uat_gate.sh to run backend gates, mapping tests, UAT backend tests, app-shell guardrails, and Playwright BIT+UAT checks. Update usecase INDEX and produce final signoff artifact with pass/fail matrix and residual risks."
```

