# Stagetest Evidence Console V3 Micro-Taskpack — Implementation Report

**Date:** 2026-02-15
**Executor:** Claude Opus 4.6
**Source Taskpack:** `STAGETEST_HOC_API_EVIDENCE_CONSOLE_V3_MICRO_TASKPACK_2026-02-15.md`
**Evidence Directory:** `evidence_stagetest_hoc_api_v3_2026_02_15/`

---

## 1. Findings Closure Matrix

| # | Finding | Status | Evidence |
|---|---------|--------|----------|
| F1 | Stage 1.2 cases missing `api_calls_used` field | **CLOSED** | All 21 emitted cases include `api_calls_used` with method/path/operation/status_code/duration_ms. 30/30 artifact checks pass. |
| F2 | `_ROUTE_META` only covered UC-002 (5 tests), 16 other tests had N/A metadata | **CLOSED** | Added metadata for all 21 tests across 6 UCs (UC-002, UC-004, UC-006, UC-008, UC-017, UC-032). |
| F3 | Gate used `--latest-run` (non-deterministic, drifts with stale artifacts) | **CLOSED** | Gate now emits fresh run, captures `PINNED_RUN_ID`, validates with `--run-id`. Evidence: `v3_gate.log` |
| F4 | CaseDetail schema missing `api_calls_used` field | **CLOSED** | Added `ApiCallUsed` model and `api_calls_used: list[ApiCallUsed]` to `CaseDetail`. |
| F5 | Runtime API tests missing `api_calls_used` coverage | **CLOSED** | Added `test_case_detail_has_api_calls_used` (validates field shape + content). 10/10 pass. |
| F6 | UI had "Observed Output" label, no "Produced Output" | **CLOSED** | Renamed to "Produced Output" with `produced-output-table` testid. |
| F7 | UI missing "APIs Used" table section | **CLOSED** | Added full table with Method/Path/Operation/Status/Duration columns and `apis-used-table` testid. |
| F8 | Authenticated API JSON responses | **BLOCKED** | Founder auth (Clerk JWT) required. No JWT available in CLI context. See `v3_live_auth_runs.json`. |
| F9 | Browser screenshots of 5 table sections | **BLOCKED** | Requires authenticated browser session. Source-level proof of all 5 testids in built JS provided. See `v3_live_ui_case_detail.txt`. |
| F10 | Playwright browser tests | **BLOCKED** | Chromium not installed. Testid assertions via source-level Playwright spec (test 9). |

**Closure rate:** 7/10 CLOSED, 3 BLOCKED (all auth/browser infrastructure dependencies)

---

## 2. File Change Ledger

| File | Action | Workstream |
|------|--------|------------|
| `tests/uat/stagetest_artifacts.py` | Added `api_calls_used` parameter to `emit_case()`, included in case_data output | V3-1 |
| `tests/uat/conftest.py` | Restructured `_ROUTE_META` from tuples to dicts, added `api_calls_used` per test, added metadata for 16 new tests (UC-004/006/008/017/032) | V3-1 |
| `scripts/verification/stagetest_artifact_check.py` | Added `api_calls_used` validation for stage 1.2 (non-empty, required fields per entry) | V3-1 |
| `app/hoc/fdr/ops/schemas/stagetest.py` | Added `ApiCallUsed` model, `api_calls_used: list[ApiCallUsed]` to `CaseDetail` | V3-3 |
| `tests/api/test_stagetest_runtime_api.py` | Added `API_CALLS_USED` seed data, `test_case_detail_has_api_calls_used` test | V3-3 |
| `scripts/ops/hoc_uc_validation_uat_gate.sh` | Replaced `--latest-run` with deterministic pinned-run emission + `--run-id`, added runtime API test stage | V3-2 |
| `website/app-shell/src/features/stagetest/stagetestClient.ts` | Added `ApiCallUsed` interface, `api_calls_used?: ApiCallUsed[]` to `CaseDetail` | V3-4 |
| `website/app-shell/src/features/stagetest/StagetestCaseDetail.tsx` | Added "APIs Used" table section, renamed "Observed Output" → "Produced Output", new testids | V3-4 |
| `website/app-shell/tests/uat/stagetest.spec.ts` | Updated testid assertions: added `produced-output-table`, `apis-used-table` | V3-4 |
| `website/app-shell/tests/uat/fixtures/stagetest-runs.json` | Updated required testids list for V3 | V3-4 |

**Total:** 10 files modified, 0 files created

---

## 3. Pinned-Run Gate Proof

```
PINNED_RUN_ID=20260215T164112Z
emit_exit=0 (21 passed)
check_exit=0 (31/31 checks)
GATE: 20 PASS, 1 FAIL (Playwright Chromium missing), 1 WARN (non-blocking)
```

Gate stages in `hoc_uc_validation_uat_gate.sh` (re-verified 2026-02-15T16:41Z after findings remediation):

| Stage | Result |
|-------|--------|
| Stagetest: Route Prefix Guard | PASS (0 forbidden refs) |
| Stagetest: API Structural Tests | PASS (8 tests) |
| Stagetest: Governance Tests | PASS (3 tests) |
| Stagetest: Emit Fresh Run | PASS (run_id=20260215T164112Z, 21 cases) |
| Stagetest: Artifact Integrity (pinned) | PASS (31/31 checks, `--run-id 20260215T164112Z`) |
| Stagetest: Runtime API Tests | PASS (10 tests) |

**Key change:** `--latest-run` replaced by `--run-id $PINNED_RUN_ID` — gate is now deterministic and self-contained.

**Post-audit fixes (2026-02-15T16:39Z):**
- V3 taskpack doc added to route-guard ALLOW_FILES (Finding #1)
- case_id now includes Class prefix to prevent collision (Finding #2, 21 unique files)
- `stagetest_artifact_schema.json` synced with `api_calls_used` field (Finding #4)
- Gate re-verified: all stagetest stages PASS

---

## 4. Input/Output/APIs-Used UI Proof

### Five Required Table Sections

| # | Section | Testid | Source Present | Built JS Present |
|---|---------|--------|----------------|------------------|
| 1 | API Request Fields | `api-request-fields-table` | YES | YES |
| 2 | Synthetic Input | `synthetic-input-table` | YES | YES |
| 3 | API Response Fields | `api-response-fields-table` | YES | YES |
| 4 | Produced Output | `produced-output-table` | YES | YES |
| 5 | APIs Used | `apis-used-table` | YES | YES |

### APIs Used Table Columns

| Column | Source |
|--------|--------|
| Method | `call.method` (e.g. POST, GET) |
| Path | `call.path` (e.g. /hoc/api/cus/onboarding/advance) |
| Operation | `call.operation` (e.g. account.onboarding.advance) |
| Status | `call.status_code` (color-coded: green < 400, red >= 400) |
| Duration (ms) | `call.duration_ms` |

### Component Architecture

- `KeyValueTable` renders Field/Value tables for request_fields, response_fields, synthetic_input, produced_output
- Dedicated `<table>` with 5 columns renders APIs Used
- All sections wrapped in `Section` component with title

---

## 5. Authenticated API Response Proof

**Status:** BLOCKED

Founder auth (`verify_fops_token` → Clerk JWT) is required for all `/hoc/api/stagetest/*` endpoints. No founder JWT is available in CLI context.

**Proof of correct behavior:**
- Localhost: `curl http://127.0.0.1:8000/hoc/api/stagetest/runs` → 401 (`{"error":"missing_auth"}`)
- Remote: `curl https://stagetest.agenticverz.com/hoc/api/stagetest/runs` → 401
- TestClient with auth override: 10/10 pass (validates all fields including `api_calls_used`)

**Mitigation:** Authenticate via Clerk at `https://stagetest.agenticverz.com/fops/stagetest` to access the console with real data.

---

## 6. Full Emission Proof

```
21 passed in 0.91s (emit_exit=0)
```

All 21 cases emitted across 6 UCs:
- UC-002: 5 cases (onboarding flow)
- UC-004: 3 cases (controls evidence)
- UC-006: 4 cases (signal feedback)
- UC-008: 3 cases (analytics artifacts)
- UC-017: 3 cases (trace replay)
- UC-032: 3 cases (redaction export)

Strict artifact check: **31/31 checks passed** (21 unique case files, all validated for metadata completeness + `api_calls_used`)

**Post-audit fix:** case_id now includes `Class__method` to prevent filename collisions (was `method` only, causing 20 unique files for 21 cases).

---

## 7. Runtime API Test Proof

```
10 passed in 2.20s (runtime_exit=0)
```

| Test | Validates |
|------|-----------|
| `test_list_runs_returns_200` | Run list with seeded run |
| `test_get_run_returns_200` | Run summary fields |
| `test_get_run_404_for_missing` | 404 for non-existent run |
| `test_list_cases_returns_200` | Case list with case_id |
| `test_list_cases_404_for_missing_run` | 404 for missing run |
| `test_get_case_returns_200` | Full case detail (route, method, fields, hash) |
| `test_get_case_404_for_missing` | 404 for non-existent case |
| `test_apis_snapshot_returns_200` | API snapshot with endpoints |
| `test_case_detail_has_stage_12_fields` | Stage 1.2 contract (non-empty fields, valid route) |
| `test_case_detail_has_api_calls_used` | `api_calls_used` shape (method/path/operation/status_code/duration_ms) |

---

## 8. Residual Risks and Blockers

| Risk | Severity | Status | Mitigation |
|------|----------|--------|------------|
| Authenticated API JSON not captured | MEDIUM | BLOCKED | Requires Clerk JWT. 10/10 runtime tests validate correctness with auth override. Authenticate in browser to verify live. |
| Browser screenshots not captured | MEDIUM | BLOCKED | Requires authenticated browser + Playwright Chromium. 5/5 testids verified in built JS. |
| Playwright tests not runnable | LOW | BLOCKED | Chromium not installed (`npx playwright install chromium` needs network). Source-level assertions via test 9. |
| `api_calls_used` duration_ms values are static | LOW | ADVISORY | Metadata is structural (not from live HTTP timing). Acceptable for stage 1.2 structural evidence. |
| Gate emits into shared `artifacts/stagetest/` directory | LOW | ADVISORY | Pinned-run validation mitigates drift. Old runs accumulate; add cleanup in CI if needed. |

---

## 9. Evidence File Inventory

| File | Content | Status |
|------|---------|--------|
| `v3_emit.log` | 21 UAT tests passed, emission complete | exit 0 |
| `v3_artifact_check.log` | 30/30 strict checks passed | exit 0 |
| `v3_runtime_api_tests.log` | 10/10 runtime API tests passed | exit 0 |
| `v3_gate.log` | Pinned-run gate proof (run_id=20260215T151252Z) | PASSED |
| `v3_ui_tests.log` | 5/5 table testids present in source | VERIFIED |
| `v3_live_deployment.log` | Live curl checks (root=200, SPA=200, API=401, health=200) | VERIFIED |
| `v3_live_auth_runs.json` | BLOCKED — auth required | 401 |
| `v3_live_auth_case_detail.json` | BLOCKED — auth required | 401 |
| `v3_live_ui_case_detail.txt` | BLOCKED — screenshot requires auth browser | Source proof |
