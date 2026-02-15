# UC Stage 1.1 + 1.2 Detailed Taskpack For Claude (2026-02-15)

## Objective

Execute only:
1. Stage 1.1: wiring/trigger-output/governance checks.
2. Stage 1.2: synthetic deterministic UC scenario checks.

Do not execute Stage 2 (real-data environment) in this pack.

## Scope

Priority UC set:
1. `UC-002` Customer Onboarding
2. `UC-004` Runtime Controls Evaluation
3. `UC-006` Activity Stream + Feedback
4. `UC-008` Reproducible Analytics Artifacts
5. `UC-017` Logs Replay Mode + Integrity Versioning
6. `UC-032` Logs Redaction Governance + Trace-Safe Export

Canonical sources:
1. `backend/app/hoc/docs/architecture/usecases/INDEX.md`
2. `backend/app/hoc/docs/architecture/usecases/HOC_USECASE_CODE_LINKAGE.md`
3. `backend/app/hoc/docs/architecture/usecases/UC_OPERATION_MANIFEST_2026-02-15.json`
4. `backend/app/hoc/docs/architecture/usecases/UC_MONITORING_ROUTE_OPERATION_MAP.md`

## Execution Contract

1. Execute from `/root/agenticverz2.0/backend`.
2. Use `PYTHONPATH=.` for all Python/pytest commands.
3. Capture evidence logs under:
   - `/root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/evidence_stage11_stage12_2026_02_15/`
4. Update only:
   - `backend/app/hoc/docs/architecture/usecases/UC_STAGE11_STAGE12_DETAILED_TASKPACK_FOR_CLAUDE_2026_02_15_executed.md`
5. Do not modify this source taskpack.

## Setup

Run:

```bash
cd /root/agenticverz2.0/backend
export PYTHONPATH=.
EVIDENCE_DIR=/root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/evidence_stage11_stage12_2026_02_15
mkdir -p "$EVIDENCE_DIR"
```

## Stage 1.1 Detailed Test Cases (Wiring + Governance)

### TC-S11-001 Manifest Integrity Strict

Command:

```bash
python3 scripts/verification/uc_operation_manifest_check.py --strict | tee "$EVIDENCE_DIR/tc_s11_001_manifest_strict.log"
```

Pass criteria:
1. Exit code `0`.
2. Summary shows `6 passed, 0 failed [strict]`.

### TC-S11-002 Decision Table + Manifest Governance Tests

Command:

```bash
python3 -m pytest -q \
  tests/governance/t4/test_uc_mapping_decision_table.py \
  tests/governance/t4/test_uc_operation_manifest_integrity.py \
  | tee "$EVIDENCE_DIR/tc_s11_002_governance_mapping.log"
```

Pass criteria:
1. Exit code `0`.
2. Expected: `29 passed`.

### TC-S11-003 Layer Boundary Gate

Command:

```bash
python3 scripts/ci/check_layer_boundaries.py | tee "$EVIDENCE_DIR/tc_s11_003_layer_boundaries.log"
```

Pass criteria:
1. Exit code `0`.
2. Output contains `CLEAN: No layer boundary violations found`.

### TC-S11-004 Init Hygiene Gate

Command:

```bash
python3 scripts/ci/check_init_hygiene.py --ci | tee "$EVIDENCE_DIR/tc_s11_004_init_hygiene.log"
```

Pass criteria:
1. Exit code `0`.
2. Output contains `All checks passed. 0 blocking violations`.

### TC-S11-005 Route-Operation Mapping Guard (UC-MON)

Command:

```bash
python3 scripts/verification/uc_mon_route_operation_map_check.py | tee "$EVIDENCE_DIR/tc_s11_005_uc_mon_route_map.log"
```

Pass criteria:
1. Exit code `0`.
2. No route-operation map mismatch failures.

### TC-S11-006 UC-001 Route-Operation Mapping Guard

Command:

```bash
python3 scripts/verification/uc001_route_operation_map_check.py | tee "$EVIDENCE_DIR/tc_s11_006_uc001_route_map.log"
```

Pass criteria:
1. Exit code `0`.
2. No UC-001 route-operation mismatch failures.

## Stage 1.2 Detailed Test Cases (Synthetic Deterministic UC Scenarios)

Synthetic source artifact for traceability:
1. `backend/app/hoc/docs/architecture/usecases/UC_STAGE11_STAGE12_DETAILED_TASKPACK_FOR_CLAUDE_2026_02_15_synthetic_inputs.json`

### TC-S12-001 UC-002 Onboarding Synthetic Scenarios

Command:

```bash
python3 -m pytest -q tests/uat/test_uc002_onboarding_flow.py \
  | tee "$EVIDENCE_DIR/tc_s12_001_uc002.log"
```

Pass criteria:
1. Exit code `0`.
2. Expected: `5 passed`.

### TC-S12-002 UC-004 Controls Evidence Synthetic Scenarios

Command:

```bash
python3 -m pytest -q tests/uat/test_uc004_controls_evidence.py \
  | tee "$EVIDENCE_DIR/tc_s12_002_uc004.log"
```

Pass criteria:
1. Exit code `0`.
2. Expected: `3 passed`.

### TC-S12-003 UC-006 Signal Feedback Synthetic Scenarios

Command:

```bash
python3 -m pytest -q tests/uat/test_uc006_signal_feedback_flow.py \
  | tee "$EVIDENCE_DIR/tc_s12_003_uc006.log"
```

Pass criteria:
1. Exit code `0`.
2. Expected: `4 passed`.

### TC-S12-004 UC-008 Analytics Artifacts Synthetic Scenarios

Command:

```bash
python3 -m pytest -q tests/uat/test_uc008_analytics_artifacts.py \
  | tee "$EVIDENCE_DIR/tc_s12_004_uc008.log"
```

Pass criteria:
1. Exit code `0`.
2. Expected: `3 passed`.

### TC-S12-005 UC-017 Trace Replay Integrity Synthetic Scenarios

Command:

```bash
python3 -m pytest -q tests/uat/test_uc017_trace_replay_integrity.py \
  | tee "$EVIDENCE_DIR/tc_s12_005_uc017.log"
```

Pass criteria:
1. Exit code `0`.
2. Expected: `3 passed`.

### TC-S12-006 UC-032 Redaction/Export Safety Synthetic Scenarios

Command:

```bash
python3 -m pytest -q tests/uat/test_uc032_redaction_export_safety.py \
  | tee "$EVIDENCE_DIR/tc_s12_006_uc032.log"
```

Pass criteria:
1. Exit code `0`.
2. Expected: `3 passed`.

### TC-S12-007 Aggregate Synthetic UC Suite

Command:

```bash
python3 -m pytest -q tests/uat/ | tee "$EVIDENCE_DIR/tc_s12_007_uat_aggregate.log"
```

Pass criteria:
1. Exit code `0`.
2. Expected total: `21 passed`.

### TC-S12-008 Determinism Re-run Check (UC-017)

Commands:

```bash
python3 -m pytest -q tests/uat/test_uc017_trace_replay_integrity.py > "$EVIDENCE_DIR/tc_s12_008_uc017_run1.log"
python3 -m pytest -q tests/uat/test_uc017_trace_replay_integrity.py > "$EVIDENCE_DIR/tc_s12_008_uc017_run2.log"
diff -u "$EVIDENCE_DIR/tc_s12_008_uc017_run1.log" "$EVIDENCE_DIR/tc_s12_008_uc017_run2.log" > "$EVIDENCE_DIR/tc_s12_008_uc017_diff.log" || true
```

Pass criteria:
1. Both pytest runs exit code `0`.
2. Both runs show `3 passed`.
3. `tc_s12_008_uc017_diff.log` has no assertion or failure drift.

## Expected Stage Outcomes

1. Stage 1.1: `PASS` if TC-S11-001..006 all pass.
2. Stage 1.2: `PASS` if TC-S12-001..008 all pass.
3. Stage 2: mark `SKIPPED` in this taskpack.

## Required Update to Executed Artifact

File:
1. `backend/app/hoc/docs/architecture/usecases/UC_STAGE11_STAGE12_DETAILED_TASKPACK_FOR_CLAUDE_2026_02_15_executed.md`

Must include:
1. Stage status table updates.
2. Per-command result matrix (`PASS/FAIL/BLOCKED`).
3. Per-UC case status updates.
4. Metric scorecard update:
   - quality
   - quantity
   - velocity
   - veracity
   - determinism
5. Command outputs and evidence log paths.

## Claude Execution Prompt

```bash
claude -p "In /root/agenticverz2.0 execute only Stage 1.1 and Stage 1.2 from backend/app/hoc/docs/architecture/usecases/UC_STAGE11_STAGE12_DETAILED_TASKPACK_FOR_CLAUDE_2026_02_15.md. Run each test case command exactly as written, capture logs in the specified evidence directory, and update only backend/app/hoc/docs/architecture/usecases/UC_STAGE11_STAGE12_DETAILED_TASKPACK_FOR_CLAUDE_2026_02_15_executed.md with stage outcomes, per-case status, metric scorecard, and command evidence. Mark Stage 2 as SKIPPED. Do not edit the source taskpack."
```
