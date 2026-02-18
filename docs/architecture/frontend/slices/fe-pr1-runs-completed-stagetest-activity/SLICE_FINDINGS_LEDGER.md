# FE-PR1-RUNS-COMPLETED-STAGETEST Frontend Slice Findings Ledger

## Status
- Date: 2026-02-18
- Slice ID: FE-PR1-RUNS-COMPLETED-STAGETEST
- Contract Source: `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`

## Issue Register
| Issue ID | Severity | Category | Status |
|---|---|---|---|
| FE-PR1-RUNS-COMPLETED-STAGETEST-001 | Medium | Env/Auth | Closed |
| FE-PR1-RUNS-COMPLETED-STAGETEST-002 | Medium | Fixture Contract | Closed |
| FE-PR1-RUNS-COMPLETED-STAGETEST-003 | Low | Guardrail | Closed |

## Detailed Findings
### FE-PR1-RUNS-COMPLETED-STAGETEST-001 — Completed facade probe is auth-gated by default
- Surface: `https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=completed&limit=2&offset=0`
- Symptom: no-fixture probe returns `401 not_authenticated`.
- Risk: scaffold UI cannot validate completed payload shape without authenticated session.
- Root Cause: normal auth/RBAC path is active for CUS facade routes.
- Resolution: temporary, explicit fixture path for preflight testing only.

### FE-PR1-RUNS-COMPLETED-STAGETEST-002 — Completed topic required dedicated fixture payload
- Surface: completed topic probe route and payload preview.
- Symptom: live-only fixture would not satisfy completed contract slice.
- Risk: false confidence from wrong topic payload.
- Root Cause: completed fixture key/payload path was missing in initial run.
- Resolution: added `pr1-runs-completed-v1` fixture key and deterministic completed payload set.

### FE-PR1-RUNS-COMPLETED-STAGETEST-003 — Fixture misuse needed fail-fast behavior
- Surface: fixture header parsing on `/cus/activity/runs`.
- Symptom: potential fallback paths when fixture key/topic misuse occurs.
- Risk: accidental bypass or ambiguous behavior during scaffold checks.
- Root Cause: fixture-topic mismatch was not explicitly rejected.
- Resolution: enforce `400 INVALID_QUERY` for fixture/topic mismatch and unknown fixture ids; keep fixture-disabled path on auth (`401`).

## Fix Implementation
- Fix item 1: wire scaffold completed probe header in catalog (`X-HOC-Scaffold-Fixture: pr1-runs-completed-v1`).
- Fix item 2: extend backend PR1 fixture handling for `topic=completed` with contract-shaped payload.
- Fix item 3: enforce fixture allowlist + topic/fixture compatibility validation.
- Fix item 4: add test coverage for mismatch and fixture-disabled auth fallback behavior.

## Verification Evidence
```bash
# stagetest completed page route
curl -ksS -o /tmp/pr1_completed_page.html -w '%{http_code} %{content_type}\n' \
  https://stagetest.agenticverz.com/page/activity/runs-completed
# outcome: 200 text/html

# stagetest completed facade without fixture header
curl -ksS -o /tmp/pr1_completed_nohdr.json -w '%{http_code} %{content_type}\n' \
  'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=completed&limit=2&offset=0'
# outcome: 401 application/json

# stagetest completed facade with fixture header
curl -ksS -o /tmp/pr1_completed_fixture.json -w '%{http_code} %{content_type}\n' \
  -H 'X-HOC-Scaffold-Fixture: pr1-runs-completed-v1' \
  'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=completed&limit=2&offset=0'
# outcome: 200 application/json, payload includes run_comp_003/run_comp_002

# invalid fixture key reject
curl -ksS -o /tmp/pr1_completed_badfixture.json -w '%{http_code} %{content_type}\n' \
  -H 'X-HOC-Scaffold-Fixture: bad-fixture-id' \
  'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=completed&limit=2&offset=0'
# outcome: 400 application/json, code=INVALID_QUERY

# backend contract checks
cd /root/agenticverz2.0/backend && PYTHONPATH=. pytest -q tests/api/test_runs_facade_pr1.py
# outcome: 20 passed
```

## Residual Risks
- Current acceptance is scaffold-fixture based; authenticated tenant runtime payload evidence is deferred to PR-2.
- Temporary preflight allowances (fixture + RBAC rule) must be removed before production promotion.
- Completed page still renders raw JSON preview; production display components are pending.
