# Staging Readiness Checklist — M9 entrance

**Last Verified:** 2025-12-06

## Prerequisites (must be green before staging sign-off)
- [x] Code: Latest images built from main (verified: commit 0f1d7aa)
- [x] DB: Alembic HEAD == 014_trace_mismatches (verified via psql)
- [x] Redis: REDIS_URL points to Upstash and `redis_connected==1` (verified)
- [x] Grafana: 4 dashboards provisioned (AOS Traces, M4 Workflow, M4.5 Failure, Basic)
- [ ] Logs: central logging (ELK/CloudWatch) receives backend logs **[PROD SETUP]**
- [x] Secrets: SLACK_MISMATCH_WEBHOOK present; GITHUB_TOKEN **[MISSING - add for issue creation]**
- [x] CI: `e2e-parity-check.yml` exists (workflow_dispatch only)

## Smoke Tests (post-deploy to staging)
- [x] `curl /healthz` returns 200 (verified)
- [x] `aos simulate` works, trace storage via Postgres works
- [ ] `aos replay` needs PostgresTraceStore method parity **[TODO: align SQLite/PG interfaces]**
- [x] Rate-limit: 60 allowed, 5 blocked at free tier (verified)
- [ ] Idempotency atomicity: `tools/test_idempotency_atomicity.py` **[NEEDS TEST]**
- [x] Retention: `aos_traces_retention_log` has 2 entries
- [ ] Mismatch automation: trigger mismatch → GitHub/Slack **[BLOCKED: GITHUB_TOKEN]**
- [x] Metrics: Grafana shows `aos_*` metrics (rate_limit, traces, redis)
- [ ] k6 baseline: run `load-tests/simulate_k6.js` **[NEEDS RUN]**
- [ ] E2E report: `tools/e2e_results_parser.py` **[NEEDS RUN]**

## Operational checks
- [x] nftables rules persist after reboot (verified)
- [ ] Backups: nightly DB backup configured and tested **[PROD SETUP]**
- [x] Alert routing: Alertmanager healthy (status=ready)
- [x] Runbook: `docs/ONCALL_RUNBOOK.md` created with recovery steps

## Code Changes This Session

1. **docker-compose.yml**: Added `USE_POSTGRES_TRACES=true` for Postgres trace storage
2. **backend/app/traces/pg_store.py**:
   - Added PgBouncer compatibility (`statement_cache_size=0`)
   - Added `start_trace`, `record_step`, `complete_trace` methods for replay
3. **backend/app/runtime/replay.py**: Added `get_trace_store()` factory with USE_POSTGRES support
4. **backend/app/api/runtime.py**: Updated list_traces/get_trace to use get_trace_store()
5. **monitoring/grafana/provisioning/dashboards/files/**: Fixed dashboard permissions, extracted aos_traces from wrapper

## Known Gaps

| Gap | Priority | Notes |
|-----|----------|-------|
| GITHUB_TOKEN missing | P1 | Needed for mismatch issue creation |
| Replay PostgresTraceStore parity | P2 | `start_trace` schema mismatch |
| Central logging not configured | P2 | ELK/CloudWatch for prod |
| DB backup automation | P2 | Cron job needed |
| k6 SLO baseline | P3 | Run before prod |

## Sign-off acceptance (QA + SRE)
- [ ] QA lead confirms smoke tests (above)
- [ ] SRE confirms infra (Redis, DB, Prometheus)
- [ ] Product owner approves demo checklist
