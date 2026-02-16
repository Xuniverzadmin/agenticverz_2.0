# UC Blocker Remediation Design V1 (2026-02-15)

## Scope
Stage 2 is intentionally postponed. This design addresses Stage 1.1/1.2 blocker classes with architecture-safe, deterministic closure.

## Current Blocker Classes (from V3 executed summary)

1. `UNMAPPED` (22 UCs)
- Why: no manifest runtime test linkage and no executable Stage 1.2 mapping.
- Affected UCs: `UC-005`, `UC-009`, `UC-012..UC-016`, `UC-024..UC-030`, `UC-033..UC-040`.

2. `TRACE_CERT_MISSING_ARTIFACT` (29 rows)
- Why: Stage 1.1 rows are structural/governance verifiers, not runtime executions. They produce log evidence but not per-case stagetest artifacts (`execution_trace`, `db_writes`).

3. `STAGE12_OPERATION_MISMATCH` (was 6 rows; now remediated in code)
- Why: emitted Stage 1.2 `operation_name` values diverged from manifest case operation strings.
- Affected previously: `UC-002`, `UC-017`, `UC-032`.

4. `ROUTE_UNRESOLVED` (9 rows across 8 UCs)
- Why: no concrete route-operation mapping for the case operation in runtime pack path.
- Affected UCs: `UC-001`, `UC-010`, `UC-019`, `UC-020`, `UC-021`, `UC-022`, `UC-023`, `UC-031`.

5. `LOCAL_HTTP_PREREQ_MISSING` (6 rows across 5 UCs)
- Why: Stage 1.2 command path depends on external runtime HTTP/auth env (`BASE_URL/AUTH_TOKEN/TENANT_ID`) for curl triggers.
- Affected UCs: `UC-001`, `UC-003`, `UC-007`, `UC-011`, `UC-018`.

## Code Fixes Already Applied (this cycle)

1. Operation mismatch remediation in Stage 1.2 emitter metadata.
- Updated operation names in `tests/uat/conftest.py` route metadata to align with manifest semantics for:
  - `UC-017`: all 3 rows
  - `UC-032`: 1 row

2. Added missing UC-002 runtime-structural Stage 1.2 cases to cover prior mismatch rows.
- New tests in `tests/uat/test_uc002_onboarding_flow.py`:
  - `test_connector_registry_cache_boundary_is_enforced`
  - `test_onboarding_transition_event_uses_schema_contract`

3. Validation after fixes:
- `STAGETEST_EMIT=1 PYTHONPATH=. pytest -q tests/uat/` -> `25 passed`
- `python3 scripts/verification/stagetest_artifact_check.py --strict --run-id 20260215T184701Z` -> `PASS: All 35 checks passed`
- Emitted operations now include canonical mismatch rows:
  - `UC-002`: `integrations.connector_registry (L6 runtime cache for onboarding)`, `event_schema_contract (shared authority)`
  - `UC-017`: all 3 canonical operation strings
  - `UC-032`: `find_matching_traces/update_trace_determinism`

## Proper Design to Clear Remaining Classes

### A) Separate Structural Evidence from Runtime Trace Certification

Problem:
- Stage 1.1 is structural by design but currently treated as runtime-cert required, causing predictable `TRACE_CERT_MISSING_ARTIFACT` blockers.

Design:
1. Stage 1.1 classified as `STRUCTURAL_EVIDENCE` lane.
2. Stage 1.2 classified as `RUNTIME_TRACE_CERT` lane.
3. Frontend publish readiness gates on Stage 1.2 (and later Stage 2), not on Stage 1.1 trace artifacts.
4. Stage 1.1 still mandatory for architecture/governance but not counted as runtime trace blocker.

Implementation targets:
- `/.codex/skills/uc-testcase-generator/scripts/uc_testcase_pack.py` readiness policy update.
- Executed template guidance: Stage 1.1 rows should be `SKIPPED`/`INFO` for trace-cert where structural-only.

### B) Add In-Process Runtime Trigger Harness for Route/Auth-Blocked Rows

Problem:
- `ROUTE_UNRESOLVED` and `LOCAL_HTTP_PREREQ_MISSING` block Stage 1.2 because execution path uses curl+env.

Design:
1. Add Stage 1.2 harness tests that execute via `OperationRegistry` in-process (no external HTTP/auth prerequisites).
2. Mark each case with canonical `operation_name` equal to manifest row operation string.
3. Capture deterministic stagetest artifacts (`execution_trace`, `db_writes`) from same plugin path.

Implementation targets:
- New tests under `tests/uat/` for the 13 mapped-but-blocked rows (`UC-001,003,007,010,011,018,019,020,021,022,023,031`).
- Update `tests/uat/conftest.py` `_ROUTE_META` for those tests.
- Update V3/V4 packs to prefer these in-process commands over curl for Stage 1.2 local runs.

### C) UNMAPPED Closure Program (22 UCs)

Problem:
- No runtime linkage exists, so generator creates placeholders only.

Design:
1. For each UNMAPPED UC, create at least one canonical manifest entry with:
  - `operation_name`
  - `handler_file`
  - `route_path` (or explicit symbolic key)
  - `test_refs` to runtime-trace-capable UAT test
2. Add minimal Stage 1.2 runtime test per UC that emits artifact.
3. Keep HOLD only where no runtime operation exists in codebase yet.

Implementation targets:
- `UC_OPERATION_MANIFEST_*.json`
- `UC_MONITORING_ROUTE_OPERATION_MAP.md`
- `tests/uat/test_uc0xx_*.py` additions

## Recommended Execution Order

1. Re-run V3 after mismatch fixes to confirm blocker class #3 is closed.
2. Implement readiness-lane separation (A) so Stage 1.1 does not cause false runtime blockers.
3. Implement in-process runtime trigger harness for route/auth blocked mapped rows (B).
4. Execute UNMAPPED closure wave in batches (C):
  - Wave 1: `UC-024..UC-030`
  - Wave 2: `UC-033..UC-040`
  - Wave 3: `UC-005, UC-009, UC-012..UC-016`

## Acceptance Targets (Stage 2 still postponed)

1. `STAGE12_OPERATION_MISMATCH == 0`
2. `ROUTE_UNRESOLVED == 0` for mapped UCs
3. `LOCAL_HTTP_PREREQ_MISSING == 0` for mapped UCs (by in-process harness)
4. `UNMAPPED` count reduced from 22 to <= 5 (explicit backlog-only)
5. `trace_policy.pass_without_debugger_trace_count == 0` maintained
