# PIN-576: PR2 Runs Real-Data Auth Rollout — Iteration 2 (Pre-Deploy Evidence)

**Created:** 2026-02-18
**Status:** IN_PROGRESS
**Category:** Frontend / Auth / Stagetest Validation
**Depends on:** PIN-575, PR #4 (`hoc/pr2-runs-realdata-auth-rollout`)

---

## Summary

Captured pre-deploy stagetest evidence after PR2 iteration-1 code changes were pushed.

Current stagetest runtime is still on pre-PR2 deployment behavior:
- No fixture header: `401 not_authenticated` (expected auth path)
- Fixture header still accepted: `200` fixture payload (legacy behavior still deployed)

This confirms repository changes are ready, but environment rollout is still required to retire fixture behavior at runtime.

## Evidence (2026-02-18)

```bash
# live without fixture header
curl -ksS -o /tmp/pr2_live_nohdr.json -w '%{http_code} %{content_type}\n' \
  'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=live&limit=2&offset=0'
# 401 application/json

# completed without fixture header
curl -ksS -o /tmp/pr2_completed_nohdr.json -w '%{http_code} %{content_type}\n' \
  'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=completed&limit=2&offset=0'
# 401 application/json

# live with legacy fixture header (still active in deployed runtime)
curl -ksS -o /tmp/pr2_live_withfixture.json -w '%{http_code} %{content_type}\n' \
  -H 'X-HOC-Scaffold-Fixture: pr1-runs-live-v1' \
  'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=live&limit=2&offset=0'
# 200 application/json

# completed with legacy fixture header (still active in deployed runtime)
curl -ksS -o /tmp/pr2_completed_withfixture.json -w '%{http_code} %{content_type}\n' \
  -H 'X-HOC-Scaffold-Fixture: pr1-runs-completed-v1' \
  'https://stagetest.agenticverz.com/hoc/api/cus/activity/runs?topic=completed&limit=2&offset=0'
# 200 application/json
```

## Interpretation

- PR2 code removes fixture header injection and temporary RBAC bypass in repository source.
- Stagetest still returns fixture payload when explicit header is manually sent, meaning deployed backend/runtime has not yet picked PR2 state.
- This is expected until PR #4 is merged and deployed.

## Next Action

1. Merge PR #4 (`PR2: retire runs scaffold bypasses (iteration 1)`).
2. Deploy updated backend/frontend config to stagetest.
3. Re-run probe checks and record post-deploy evidence showing fixture-header path no longer returns 200 on stagetest.
