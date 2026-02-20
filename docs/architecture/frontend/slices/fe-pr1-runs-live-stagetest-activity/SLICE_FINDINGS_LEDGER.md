# FE-PR1-RUNS-LIVE-STAGETEST Frontend Slice Findings Ledger

## Status
- Date: 2026-02-20
- Slice ID: FE-PR1-RUNS-LIVE-STAGETEST
- Contract Source: `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`

## Issue Register
| Issue ID | Severity | Category | Status |
|---|---|---|---|
| FE-PR1-RUNS-LIVE-STAGETEST-001 | Medium | Auth Evidence Gap | Open |
| FE-PR1-RUNS-LIVE-STAGETEST-002 | Low | Ledger Drift | Closed |

## Detailed Findings
### FE-PR1-RUNS-LIVE-STAGETEST-001 — Browser positive-path evidence still missing
- Surface: `/page/activity/runs-live` runtime probe on stagetest.
- Symptom: unauthenticated CUS API probe returns `401`.
- Risk: slice cannot be promoted without authenticated browser session evidence for `200` payload rendering.
- Root Cause: PR2 correctly enforces CUS auth and retires public/fixture bypass.
- Required Follow-up: capture page-level `200` evidence using a valid authenticated session (Clerk org-backed or tenant-bound key flow routed through supported client auth surface).

### FE-PR1-RUNS-LIVE-STAGETEST-002 — Historical fixture-bypass claims became stale
- Surface: prior acceptance/findings narrative.
- Symptom: old text referenced temporary preflight bypass as active.
- Risk: governance drift and incorrect rollout state reporting.
- Resolution: Step 7 sync updated ledgers to current post-PR2 auth-enforced behavior (`401` unauth, authenticated path required for `200`).

## Verification Evidence
```bash
curl -ksS -o /tmp/pr1_live_page.html -w '%{http_code} %{content_type}\n' \
  https://stagetest.agenticverz.com/page/activity/runs-live
# outcome: 200 text/html

curl -ksS -o /tmp/pr1_live_noauth.json -w '%{http_code} %{content_type}\n' \
  'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=live&limit=2&offset=0'
# outcome: 401 application/json
```

## Residual Risks
- Browser session acquisition path is currently blocked for this operator context (no Clerk org session available).
- Slice remains scaffold-level and not eligible for production promotion until authenticated tenant runtime evidence is attached.
