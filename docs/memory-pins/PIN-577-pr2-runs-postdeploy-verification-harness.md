# PIN-577: PR2 Runs Post-Deploy Verification Harness

**Created:** 2026-02-18
**Status:** IN_PROGRESS
**Category:** Verification / Stagetest / Auth Rollout
**Depends on:** PIN-575, PIN-576, PR #4 merge (`822f5bca`)

---

## Summary

Created deterministic verification tooling for PR2 rollout closure.

This iteration adds:
- runnable stagetest probe script for live/completed runs
- post-deploy checklist with expected auth-path outcomes

Goal: capture deploy-time evidence that fixture-header behavior is retired and authenticated real-data behavior is active.

## Artifacts Added

1. `scripts/ops/verify_pr2_runs_auth_rollout.sh`
- capability_id: `CAP-CUS-ACT-RUNS-REALDATA-PR2`
- probes:
  - live/completed without fixture header
  - live/completed with legacy fixture headers
  - optional authenticated probes via `AUTH_COOKIE`
- emits markdown + raw headers/bodies under `artifacts/pr2_runs_rollout/`

2. `docs/architecture/frontend/PR2_RUNS_POSTDEPLOY_VALIDATION_CHECKLIST_2026-02-18.md`
- expected status matrix for post-deploy verification
- command examples for unauth and authenticated runs

## Harness Smoke Test

- Executed unauth probe run on 2026-02-18 against `https://stagetest.agenticverz.com`.
- Result confirms harness output generation and current pre-deploy behavior capture:
  - no header -> `401`
  - legacy fixture headers -> `200` (still active on currently deployed runtime)

## Next Action

1. Run verification script after stagetest deployment of PR2 changes.
2. Capture and store generated evidence artifacts.
3. Add post-deploy memory pin with final PASS criteria and retire rollout blockers.
