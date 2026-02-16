# UC ALL UseCase Trace-Cert Rerun Taskpack V3 (Claude)

Date: 2026-02-15
Objective: Re-run with V3 pack so trace-capable UCs can be lifted using real stagetest artifacts.

## Inputs

1. Source pack:
- `backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V3_2026_02_15.md`

2. Executed template to fill:
- `backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V3_2026_02_15_executed.md`

3. Synthetic input file:
- `backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V3_2026_02_15_synthetic_inputs.json`

## Mandatory Lane + Trace-Cert Rule

1. Stage 1.1 is `STRUCTURAL_EVIDENCE` lane.
- Stage 1.1 PASS does **not** require runtime trace/db artifacts.
- Do not mark Stage 1.1 `BLOCKED` solely for missing trace/db artifacts.

2. Stage 1.2 + Stage 2 are `RUNTIME_TRACE_CERT` lanes.
- Any case marked `PASS` in Stage 1.2 or Stage 2 must include both:
  - `Trace Artifact`
  - `DB Writes Artifact`
- Else mark `BLOCKED` with `TRACE_CERT_MISSING_ARTIFACT`.

## Execution Rules

1. Stage 1.1
- Execute deterministic verifier commands from the pack.
- Treat outcomes as structural evidence (wiring/governance); trace/db artifacts are optional in this lane.

2. Stage 1.2
- Run the trace-capable suites generated in the V3 pack for:
  - `UC-001`, `UC-002`, `UC-003`, `UC-004`, `UC-006`, `UC-007`, `UC-008`, `UC-010`, `UC-011`, `UC-017`, `UC-018`, `UC-019`, `UC-020`, `UC-021`, `UC-022`, `UC-023`, `UC-031`, `UC-032`
- Use emitted files under `backend/artifacts/stagetest/<run_id>/cases/*.json` as trace/db artifact evidence.
- For unresolved-route or unmapped cases, keep `BLOCKED` with exact reason.

3. Stage 2
- Execute only if real env credentials are present.
- Otherwise mark `BLOCKED` per case with missing prerequisites.

4. Governance gates
- Run and record all required gates once.

5. Marker blocks
- Fill required marker blocks only; do not replace with prose.

## Required Evidence Directory

Store logs under:
- `backend/app/hoc/docs/architecture/usecases/evidence_uc_all_trace_cert_v3_2026_02_15/`

## Final Summarize Step

```bash
~/.codex/skills/uc-testcase-generator/scripts/uc_testcase_pack.py summarize \
  --executed-file /root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V3_2026_02_15_executed.md \
  --output-json /root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V3_2026_02_15_executed_summary.json \
  --output-md /root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V3_2026_02_15_executed_summary.md
```

Acceptance:
1. `total_cases > 0`
2. `trace_policy.pass_without_debugger_trace_count == 0`
3. At least trace-capable UCs move off all-stage BLOCKED where runtime suites passed.

## Claude Command

```bash
claude -p "In /root/agenticverz2.0 execute backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_TRACE_CERT_RERUN_TASKPACK_V3_FOR_CLAUDE_2026-02-15.md exactly. Fill only backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V3_2026_02_15_executed.md using required marker blocks. Enforce runtime-lane trace-cert: no PASS in Stage 1.2 or Stage 2 without Trace Artifact + DB Writes Artifact. Save logs in backend/app/hoc/docs/architecture/usecases/evidence_uc_all_trace_cert_v3_2026_02_15/. Then run summarize and produce *_executed_summary.json and *_executed_summary.md." 
```
