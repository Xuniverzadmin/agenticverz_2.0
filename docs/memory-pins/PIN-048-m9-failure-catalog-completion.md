# PIN-048: M9 Failure Catalog Persistence Layer - Complete

**Status:** ✅ COMPLETE
**Created:** 2025-12-07
**Milestone:** M9
**Tag:** `m9.0.0`
**Commit:** `fee4548`

---

## Executive Summary

M9 Failure Catalog Persistence Layer is complete with all P0 deliverables implemented, tested, and tagged. The system provides:
- Hardened database schema for failure persistence
- Non-blocking persistence with circuit breaker protection
- Recovery tracking API for operator workflows
- Synthetic validation tooling
- Automated monitoring deployment

All 23 M9 tests pass. Ready for canary deployment.

---

## Implementation Summary

### P0 Deliverables (Critical - All Complete)

| Deliverable | Status | Location |
|-------------|--------|----------|
| Hardened migration 015b | ✅ COMPLETE | `backend/alembic/versions/015b_harden_failure_matches.py` |
| Non-blocking persistence | ✅ COMPLETE | `backend/app/runtime/failure_catalog.py` (circuit breaker) |
| Recovery tracking API | ✅ COMPLETE | `backend/app/api/failures.py` |
| Synthetic validation generator | ✅ COMPLETE | `tools/generate_synthetic_failures.py` |
| Monitoring automation | ✅ COMPLETE | `scripts/ops/m9_monitoring_deploy.sh` |

### P1 Deliverables (Short-term - Complete)

| Deliverable | Status | Location |
|-------------|--------|----------|
| Failures list/stats/unrecovered | ✅ COMPLETE | `GET /api/v1/failures/*` endpoints |
| Prometheus cardinality safeguards | ✅ COMPLETE | `monitoring/prometheus.yml` relabel rules |
| Secrets rotation runbook | ✅ COMPLETE | `docs/runbooks/SECRETS_ROTATION.md` |

---

## Schema Details

### FailureMatch Table (23 columns)

```sql
failure_matches (
    -- Identity
    id UUID PRIMARY KEY,
    run_id VARCHAR NOT NULL,
    tenant_id UUID,  -- Nullable for now, P1 to enforce

    -- Error Details
    error_code VARCHAR(255) NOT NULL,
    error_message TEXT,
    catalog_entry_id VARCHAR(100),
    match_type VARCHAR(20),
    match_confidence FLOAT,

    -- Classification
    category VARCHAR(50),
    severity VARCHAR(20),
    is_retryable BOOLEAN DEFAULT FALSE,

    -- Recovery
    recovery_mode VARCHAR(50),
    recovery_suggestion TEXT,
    recovery_attempted BOOLEAN DEFAULT FALSE,
    recovery_succeeded BOOLEAN DEFAULT FALSE,
    recovered_at TIMESTAMP,
    recovered_by VARCHAR(100),
    recovery_notes TEXT,

    -- Context
    skill_id VARCHAR(100),
    step_index INTEGER,
    context_json JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)
```

### Indexes (12)

| Index | Purpose |
|-------|---------|
| `idx_fm_run_id` | Run lookup |
| `idx_fm_tenant_id` | Tenant filtering |
| `idx_fm_error_code` | Error code queries |
| `idx_fm_catalog_entry_id` | Catalog match lookup |
| `idx_fm_created_at` | Time-based queries |
| `idx_fm_category` | Category filtering |
| `idx_fm_severity` | Severity filtering |
| `idx_fm_recovery_mode` | Recovery mode filtering |
| `idx_fm_tenant_error` | Composite: tenant + error |
| `idx_fm_tenant_time` | Composite: tenant + time |
| `idx_fm_recovery_pending` | Partial: unrecovered failures |
| `idx_fm_recent_misses` | Partial: recent unmatched |

---

## API Endpoints

### Recovery Tracking API (`/api/v1/failures`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/failures` | GET | List failures with filters |
| `/api/v1/failures/{id}` | GET | Get failure details |
| `/api/v1/failures/{id}/recovery` | PATCH | Update recovery status |
| `/api/v1/failures/stats` | GET | Aggregate statistics |
| `/api/v1/failures/unrecovered` | GET | List failures needing attention |

### Query Parameters

| Parameter | Endpoints | Description |
|-----------|-----------|-------------|
| `tenant_id` | list, stats, unrecovered | Filter by tenant |
| `run_id` | list | Filter by run |
| `error_code` | list | Filter by error code |
| `category` | list, unrecovered | Filter by category |
| `status` | list | `unrecovered`, `recovered`, `all` |
| `since_hours` | all | Time window (default: 24) |
| `limit` | list, unrecovered | Max results (default: 100) |
| `offset` | list, unrecovered | Pagination offset |

---

## Circuit Breaker Configuration

```python
_CIRCUIT_BREAKER_THRESHOLD = 5   # Open after 5 consecutive failures
_CIRCUIT_BREAKER_TIMEOUT = 60.0  # Reset after 60 seconds
_PERSIST_TIMEOUT = 2.0           # Max seconds per persist operation
```

### Metrics

| Metric | Description |
|--------|-------------|
| `failure_match_hits_total` | Catalog matches (hit) |
| `failure_match_misses_total` | Catalog misses |
| `recovery_success_total` | Successful recoveries |
| `recovery_failure_total` | Failed recoveries |
| `failure_persist_dropped_total` | Dropped due to circuit/timeout |

---

## Issues Faced & Resolutions

| Issue | Resolution |
|-------|------------|
| `now()` in partial index | Removed time filter; done at query time |
| CI check grep `-A 50` insufficient | Increased to `-A 150` for long job blocks |
| `((WARNINGS++))` exit code 1 | Changed to `WARNINGS=$((WARNINGS + 1))` |
| grep pattern script exit | Added `-q` flag and `2>/dev/null` |

---

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Non-blocking with 2s timeout | Balance reliability vs latency |
| Circuit breaker: 5 failures | Prevents cascade, auto-recovers |
| Tenant_id nullable | P1 enforcement; gradual migration |
| Recovery audit columns | Full audit trail for compliance |

---

## Files Created

| File | Purpose |
|------|---------|
| `backend/alembic/versions/015b_harden_failure_matches.py` | Hardened migration |
| `backend/app/api/failures.py` | Recovery tracking API |
| `tools/generate_synthetic_failures.py` | Synthetic validation |
| `scripts/ops/m9_monitoring_deploy.sh` | Monitoring automation |
| `docs/runbooks/SECRETS_ROTATION.md` | Secrets rotation guide |

---

## Pending To-Dos (P1/P2 for next sprint)

### P1 - Short-term

| Task | Owner |
|------|-------|
| Add tenant_id enforcement migration + backfill | DB lead |
| Schedule aggregation cron job | Ops |
| Make aggregation durable (S3 upload) | Backend |
| Add backfill job for historical errors | Dev |
| Add fast unit tests with DI (SQLite swap) | Test lead |

### P2 - Nice to have

| Task | Owner |
|------|-------|
| Async aggregation via worker queue | Backend |
| Slack/email notifications for high-miss alerts | Ops |
| UI for recovery review (M13) | Frontend |
| Data retention policy | DB lead |

---

## Validation Commands

```bash
# 1. Verify table structure
docker exec nova_db psql -U nova -d nova_aos -c "\d+ failure_matches"

# 2. Run M9 tests
cd /root/agenticverz2.0/backend
PYTHONPATH=. DATABASE_URL="postgresql://nova:novapass@localhost:6432/nova_aos" \
  python -m pytest tests/test_failure_catalog_m9.py -v

# 3. Generate synthetic traffic
python tools/generate_synthetic_failures.py --validate

# 4. Check metrics
curl localhost:9090/api/v1/query?query=failure_match_hits_total

# 5. Deploy monitoring
./scripts/ops/m9_monitoring_deploy.sh

# 6. Test recovery API
curl -X PATCH http://localhost:8000/api/v1/failures/{id}/recovery \
  -H "Content-Type: application/json" \
  -d '{"recovery_succeeded": true, "notes": "Manual fix applied"}'
```

---

## Post-Deployment Checklist

### Staging Validation

- [ ] `SELECT count(*) FROM failure_matches` shows test inserts
- [ ] `curl localhost:9090/metrics | grep failure_match` returns non-zero
- [ ] Grafana M9 dashboard shows expected data
- [ ] Alerts not firing unexpectedly for 1 hour

### Production Canary (10% traffic)

- [ ] Deploy to canary tenant/traffic subset
- [ ] Monitor miss rate for 24h
- [ ] Monitor latency impact
- [ ] If critical alert triggers, rollback

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-033 | M8-M14 Roadmap (M9 specification) |
| PIN-045 | CI Infrastructure Fixes (script fixes) |
| PIN-032 | RBAC Enablement (auth context) |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-07 | M9 implementation complete, all 23 tests passing |
| 2025-12-07 | Tagged `m9.0.0` release |
| 2025-12-07 | Created PIN-048 |
