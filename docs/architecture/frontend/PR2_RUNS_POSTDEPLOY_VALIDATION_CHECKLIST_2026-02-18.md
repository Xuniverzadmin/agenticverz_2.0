# PR2 Runs Post-Deploy Validation Checklist (2026-02-18)

- capability_id: `CAP-CUS-ACT-RUNS-REALDATA-PR2`
- Scope: Validate stagetest behavior after PR2 rollout deployment.

## Command

```bash
cd /root/agenticverz2.0
scripts/ops/verify_pr2_runs_auth_rollout.sh https://stagetest.agenticverz.com
```

Optional authenticated check:

```bash
AUTH_COOKIE='session=<cookie-value>' scripts/ops/verify_pr2_runs_auth_rollout.sh https://stagetest.agenticverz.com
```

## Expected Results (post-deploy)

1. `live_no_header` -> `401`
2. `completed_no_header` -> `401`
3. `live_with_fixture_header` -> NOT `200` fixture payload (expected `401`/`400`)
4. `completed_with_fixture_header` -> NOT `200` fixture payload (expected `401`/`400`)
5. `live_authenticated` (if cookie provided) -> `200` contract-shaped real payload
6. `completed_authenticated` (if cookie provided) -> `200` contract-shaped real payload

## Evidence Artifacts

- Markdown summary: `artifacts/pr2_runs_rollout/pr2_runs_rollout_<timestamp>.md`
- Raw headers/body files in same directory.

## Closure Criteria

- Fixture header path no longer returns scaffold fixture payloads on stagetest.
- Authenticated requests return real-data payloads for both live/completed topics.
- Update memory pin with post-deploy results and mark PR2 rollout complete.
