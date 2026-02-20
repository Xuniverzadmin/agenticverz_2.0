# FE-PR1-RUNS-COMPLETED-STAGETEST Frontend Slice Findings Ledger

## Status
- Date: 2026-02-20
- Slice ID: FE-PR1-RUNS-COMPLETED-STAGETEST
- Contract Source: `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`

## Issue Register
| Issue ID | Severity | Category | Status |
|---|---|---|---|
| FE-PR1-RUNS-COMPLETED-STAGETEST-001 | Medium | Auth Evidence Gap | Open |
| FE-PR1-RUNS-COMPLETED-STAGETEST-002 | Low | Ledger Drift | Closed |

## Detailed Findings
### FE-PR1-RUNS-COMPLETED-STAGETEST-001 — Browser positive-path evidence still missing
- Surface: `/page/activity/runs-completed` runtime probe on stagetest.
- Symptom: unauthenticated CUS API probe returns `401`.
- Risk: completed slice cannot be promoted without authenticated browser session evidence for `200` payload rendering.
- Root Cause: PR2 correctly enforces CUS auth and retires public/fixture bypass.
- Required Follow-up: capture page-level `200` evidence using valid authenticated session context.

### FE-PR1-RUNS-COMPLETED-STAGETEST-002 — Historical fixture-path assumptions became stale
- Surface: prior acceptance/findings narrative.
- Symptom: old text treated temporary fixture-based checks as active rollout state.
- Risk: stale governance reporting for auth posture.
- Resolution: Step 7 sync updated ledgers to current runtime truth (`401` unauthenticated; authenticated context required for `200`).

## Verification Evidence
```bash
curl -ksS -o /tmp/pr1_completed_page.html -w '%{http_code} %{content_type}\n' \
  https://stagetest.agenticverz.com/page/activity/runs-completed
# outcome: 200 text/html

curl -ksS -o /tmp/pr1_completed_noauth.json -w '%{http_code} %{content_type}\n' \
  'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=completed&limit=2&offset=0'
# outcome: 401 application/json
```

## Residual Risks
- Browser session acquisition for tenant-bound auth is still unavailable in this execution context.
- Slice remains scaffold-level and not eligible for production promotion until authenticated tenant runtime evidence is attached.
