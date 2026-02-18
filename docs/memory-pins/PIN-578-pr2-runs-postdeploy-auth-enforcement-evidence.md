# PIN-578: PR2 Runs Post-Deploy Auth Enforcement Evidence

**Created:** 2026-02-18
**Status:** IN_PROGRESS
**Category:** Verification / Stagetest / Auth Rollout
**Depends on:** PIN-575, PIN-576, PIN-577, PR #5 merge (`a7121076`)

---

## Summary

Captured post-deploy stagetest evidence for PR2 rollout after backend redeploy from merged `main`.

Verified outcomes:
- unauthenticated requests are blocked (`401`) for both live and completed topics.
- legacy fixture headers no longer bypass auth (`401` for both live and completed).

This confirms scaffold fixture bypass retirement is active in deployed runtime.

## Execution Evidence (2026-02-18T08:21:00Z)

Command:

```bash
cd /root/agenticverz2.0
scripts/ops/verify_pr2_runs_auth_rollout.sh https://stagetest.agenticverz.com
```

Generated artifact:
- `artifacts/pr2_runs_rollout/pr2_runs_rollout_20260218T082100Z.md`

Observed status matrix:
1. `live_no_header` -> `401`
2. `completed_no_header` -> `401`
3. `live_with_fixture_header` -> `401`
4. `completed_with_fixture_header` -> `401`

## Interpretation

- PR2 bypass retirement behavior is confirmed in stagetest runtime.
- Temporary fixture-header path is no longer exploitable for scaffold payload access.

## Remaining Gate

Authenticated positive-path verification is still pending:
- `AUTH_COOKIE` probe for `topic=live` -> expected `200` contract-shaped real payload
- `AUTH_COOKIE` probe for `topic=completed` -> expected `200` contract-shaped real payload

## Next Action

1. Re-run verifier with a valid stagetest auth cookie.
2. Capture authenticated `200` evidence for both topics.
3. Mark PR2 rollout fully complete and kick PR3 scope.
