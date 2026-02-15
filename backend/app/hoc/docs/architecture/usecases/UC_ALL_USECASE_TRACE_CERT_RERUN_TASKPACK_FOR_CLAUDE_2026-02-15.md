# UC ALL UseCase Trace-Cert Rerun Taskpack (Claude)

Date: 2026-02-15  
Objective: Re-run full UC staged execution, correct prior report claim drift, and enforce debugger-trace certification policy.

## Inputs

1. Source pack:
- `backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V2_2026_02_15.md`

2. Executed template to fill (must preserve marker blocks):
- `backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V2_2026_02_15_executed.md`

3. Synthetic input file (already generated):
- `backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V2_2026_02_15_synthetic_inputs.json`

## Mandatory Certification Rule

A test case cannot be marked `PASS` in Stage 1.1 / 1.2 / 2 unless both are present:
1. `Trace Artifact` (path to debugger trace evidence)
2. `DB Writes Artifact` (path to DB write evidence; may show `[]` for no-write scenarios, but artifact path is mandatory)

If either is missing, case must be `BLOCKED` with reason: `TRACE_CERT_MISSING_ARTIFACT`.

## Reality Corrections Required

1. Do not claim missing synthetic input file if it exists.
2. Derive all summary numbers from case table rows (no manual headline arithmetic).
3. Keep count consistency across:
- Executive summary
- Stage tables
- Blockers section
- Conclusion
4. If route/method unresolved, mark affected stages `BLOCKED` with exact blocker reason; do not estimate.

## Execution Steps (strict)

1. Stage 1.1
- Execute deterministic evidence commands per case.
- For each PASS/BLOCKED/SKIPPED row, fill `Case Results` markers.
- For PASS rows, attach trace + db artifact paths.

2. Stage 1.2
- Use synthetic file provided above.
- Execute only where route/method/data path is concrete.
- For unresolved route/method cases, mark `BLOCKED` with exact reason.
- For PASS rows, include artifact evidence from stagetest runtime JSON.

3. Stage 2
- Execute only if real env credentials are present.
- Otherwise mark `BLOCKED` per case with missing prerequisite(s).

4. Trace/DB table
- Fill `<!-- TRACE_DB_TABLE_START -->` block for all 51 cases.
- Include event counts and artifact paths.

5. Governance gates
- Run and record all required gates exactly once.

6. No narrative-only format
- Preserve and fill required marker blocks in executed template.
- Do not replace template with freeform prose.

## Required Command Output Artifacts

Store logs under:
- `backend/app/hoc/docs/architecture/usecases/evidence_uc_all_trace_cert_2026_02_15/`

Minimum expected logs:
1. Stage command outputs
2. Governance command outputs
3. Trace/db extraction outputs (`jq` extracts)
4. Final consistency check outputs

## Final Validation (must run)

Run summarize and include outputs:

```bash
~/.codex/skills/uc-testcase-generator/scripts/uc_testcase_pack.py summarize \
  --executed-file /root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V2_2026_02_15_executed.md \
  --output-json /root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V2_2026_02_15_executed_summary.json \
  --output-md /root/agenticverz2.0/backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V2_2026_02_15_executed_summary.md
```

Acceptance requirements:
1. Summary parser returns non-zero `total_cases`.
2. `trace_policy.pass_without_debugger_trace_count == 0`.
3. Frontend publish labels must reflect actual stage and trace compliance.

## Claude Command

```bash
claude -p "In /root/agenticverz2.0 execute backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_TRACE_CERT_RERUN_TASKPACK_FOR_CLAUDE_2026-02-15.md exactly. Fill only backend/app/hoc/docs/architecture/usecases/UC_ALL_USECASE_STAGED_TESTPACK_TRACE_CERT_V2_2026_02_15_executed.md using required marker blocks. Enforce trace-cert rule: no PASS without Trace Artifact and DB Writes Artifact. Record command logs under backend/app/hoc/docs/architecture/usecases/evidence_uc_all_trace_cert_2026_02_15/. Run summarize and output *_executed_summary.json and *_executed_summary.md."
```
