# Deployment Gate Policy — M9

## Overview
All merges to `main` (or `release/*`) require passing automated checks to ensure no determinism/regression.

## Required CI checks (all must PASS)
1. **Unit tests** — `pytest` (Python) and `npm test` (JS)
2. **Static checks** — `flake8`/`eslint`
3. **Determinism CI** — `.github/workflows/determinism-check.yml`:
   - cross-language parity job (Python → JS)
   - canonical JSON stability
   - trace root_hash verification across runtimes
4. **E2E parity check** — `.github/workflows/e2e-parity-check.yml`:
   - run against a disposable staging environment
   - simulate → run → replay → diff success (root_hash match)
   - k6 smoke with `--vus 10 --duration 1m` and `tools/k6_slo_mapper.py` produces SLO suggestion
5. **Security scan** — Snyk/Trivy for images
6. **Infrastructure apply plan** — Terraform plan (if infra changes)

## Merge conditions
- All CI checks green for the PR
- No open critical severity issues in security scan
- Post-merge: deployment must run `e2e-parity-check.yml` automatically; if parity fails, rollback policies apply.

## Post-merge (Automatic monitor & rollback)
1. On production deploy, run `e2e-parity-check` with `run_k6=false` by default.
2. If parity check fails (root_hash mismatch) OR `aos_replay_mismatch_total` increases above threshold in 5m:
   - Trigger automatic rollback (revert to previous image tag)
   - Open operator incident and create a high-priority GitHub issue via mismatch automation
   - Notify #oncall and #platform Slack

## Thresholds & actions
- Parity failure: immediate rollback
- p95 > target (from SLO mapper): create an alerting ticket and notify #platform
- Rate-limit failover (redis_connected==0): if > 60s -> alert SRE

## Exceptions & manual approval
- If a PR intentionally changes trace schema, it must include:
  - golden fixture updates
  - migration plan (alembic)
  - SLO migration notes
- Schema-change PRs require explicit approval from 2 reviewers (one backend, one QA) and a sign-off by the product owner.

## Enforcement
- Apply this policy via GitHub branch protection (require status checks), and ensure `e2e-parity-check.yml` is required.
