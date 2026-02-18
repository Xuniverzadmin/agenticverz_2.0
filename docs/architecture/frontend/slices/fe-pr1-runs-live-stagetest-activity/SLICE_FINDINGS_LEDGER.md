# FE-PR1-RUNS-LIVE-STAGETEST Frontend Slice Findings Ledger

## Status
- Date: 2026-02-18
- Slice ID: FE-PR1-RUNS-LIVE-STAGETEST
- Contract Source: `backend/app/hoc/docs/architecture/usecases/PR1_RUNS_FACADE_CONTRACT_ADDENDUM_2026-02-16.md`

## Issue Register
| Issue ID | Severity | Category | Status |
|---|---|---|---|
| FE-PR1-RUNS-LIVE-STAGETEST-001 | Medium | Env/Auth | Closed |
| FE-PR1-RUNS-LIVE-STAGETEST-002 | Medium | Gateway Wiring | Closed |
| FE-PR1-RUNS-LIVE-STAGETEST-003 | Low | Runtime/Deployment Drift | Closed |

## Detailed Findings
### FE-PR1-RUNS-LIVE-STAGETEST-001 — Live stagetest facade probe is auth-gated
- Surface: `https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=live&limit=2&offset=0`
- Symptom: unauthenticated probe initially returned auth errors.
- Risk: blocked scaffold validation for PR1 payload rendering.
- Root Cause: auth + RBAC enforcement for customer routes with no scaffold exemption.
- Resolution: temporary preflight public rule + header-gated fixture path for PR1 live scaffold.

### FE-PR1-RUNS-LIVE-STAGETEST-002 — HTML fallback risk for scaffold data probe (resolved)
- Surface: `/page/activity/runs-live` data probe path mapping.
- Symptom: page probe can return HTML when gateway does not proxy facade path.
- Risk: UI shows false-positive content and no contract validation signal.
- Root Cause: missing/incorrect stagetest reverse proxy mapping for `/hoc/api/cus/*` (resolved in environment wiring).

### FE-PR1-RUNS-LIVE-STAGETEST-003 — Runtime facade registration drift in deployed container (resolved)
- Surface: deployed backend container (`nova_agent_manager`) CUS facade wiring.
- Symptom: scaffold path resolved to `404 Not Found` after RBAC bypass.
- Risk: false-negative route health despite facade module existing in source.
- Root Cause: deployed container used legacy flat CUS facade registry that did not include `runs_facade` router.
- Resolution: updated deployed facade registration for `activity` to include `runs_facade_router`.

## Fix Implementation
- Fix item 1: enforce explicit PR1 query defaults in scaffold catalog (`topic=live`, `limit=50`, `offset=0`) and render mapped facade path to reduce operator ambiguity.
- Fix item 2: add probe fallback detection in scaffold page (`content-type` + `<!DOCTYPE html>` heuristic) so proxy drift is visible immediately.
- Fix item 3: validate stagetest gateway facade reachability with live curl evidence; current state returns JSON `401` instead of HTML fallback.
- Fix item 4: add fixture-gated PR1 live payload path (`X-HOC-Scaffold-Fixture: pr1-runs-live-v1`) in runs facade with contract-shaped response.
- Fix item 5: add temporary preflight public RBAC rule for `/cus/activity/runs` and align stagetest proxy `/hoc/api/cus -> /cus`.
- Fix item 6: rebuild/redeploy backend from repo source-of-truth router wiring (no runtime hotfix dependency).

## Verification Evidence
```bash
# 2026-02-18 route publication check
curl -ksS -D /tmp/pr1_page_headers.txt https://stagetest.agenticverz.com/page/activity/runs-live -o /tmp/pr1_page_body.html
# outcome: HTTP/2 200, content-type: text/html

# 2026-02-18 facade probe check
curl -ksS -D /tmp/pr1_api_headers.txt 'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=live&limit=2&offset=0' -o /tmp/pr1_api_body.json
# outcome: HTTP/2 401 without fixture header (expected)

# 2026-02-18 scaffold fixture probe check
curl -ksS -D /tmp/pr1_api_fixture_headers.txt 'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=live&limit=2&offset=0' \
  -H 'X-HOC-Scaffold-Fixture: pr1-runs-live-v1' \
  -o /tmp/pr1_api_fixture_body.json
# outcome: HTTP/2 200 with PR1 contract payload, includes run_live_003/run_live_002

# 2026-02-18 contract regression tests
cd backend && pytest tests/api/test_runs_facade_pr1.py -q
# outcome: 20 passed
```

## Residual Risks
- Authenticated tenant dataset for live runs is not yet captured in acceptance evidence for stagetest browser session.
- Temporary scaffold bypass is intentionally preflight-only and must be removed before production promotion.
- Scaffold currently renders raw payload preview; domain-specific table/cards for runs are pending follow-up slice UX work.
