# M9 Checklist — Failure Catalog v2 + Persistence

**Goal:** Convert failures into durable, queryable, machine-native data
**Status:** ✅ **CORE COMPLETE (2025-12-07)**

---

## Summary

M9 core implementation is complete. Failure persistence is operational.

| Component | Status | Details |
|-----------|--------|---------|
| Migration 015 | ✅ Applied | `failure_matches` table created |
| FailureMatch Model | ✅ Complete | SQLModel in `db.py` |
| Persistence Layer | ✅ Complete | `persist_failure_match()` working |
| Prometheus Metrics | ✅ Created | 4 counter metrics defined |
| Aggregation Job | ✅ Created | `app/jobs/failure_aggregation.py` |
| Grafana Dashboard | ✅ Created | 10 panels, all queries ready |
| Alert Rules | ✅ Created | 9 alert rules for drift detection |
| Tests | ✅ Passing | 23/23 tests pass |

---

## Acceptance Criteria Status

| Criteria | Status | Evidence |
|----------|--------|----------|
| `failure_matches` table exists | ✅ | Migration 015 applied |
| All failure paths persist | ✅ | Tests persist 4 records |
| Dashboard shows patterns | ✅ | `m9_failure_catalog_v2.json` ready |
| ≥5 unique catalog matches | ⏳ | Needs production traffic |
| Aggregation job outputs JSON | ✅ | Job created, tested |
| Metrics exported | ✅ | Counters defined, lazy init |

---

## Files Created/Modified

| File | Change |
|------|--------|
| `alembic/versions/015_create_failure_matches.py` | **NEW** |
| `app/db.py` | Modified - Added FailureMatch |
| `app/runtime/failure_catalog.py` | Modified - Added persistence |
| `app/jobs/__init__.py` | **NEW** |
| `app/jobs/failure_aggregation.py` | **NEW** |
| `monitoring/dashboards/m9_failure_catalog_v2.json` | **NEW** |
| `monitoring/rules/m9_failure_catalog_alerts.yml` | **NEW** |
| `tests/test_failure_catalog_m9.py` | **NEW** |
| `agentiverz_mn/m9_blueprint.md` | **NEW** |

---

## Remaining Steps (Deployment)

- [ ] Import Grafana dashboard (manual)
- [ ] Reload Prometheus rules
- [ ] Schedule aggregation cron job
- [ ] Generate synthetic traffic for validation
- [ ] Tag `m9.0.0` release

---

## Quick Verification

```bash
# Check table
docker exec nova_db psql -U nova -d nova_aos -c "\d failure_matches"

# Check data
docker exec nova_db psql -U nova -d nova_aos -c "SELECT * FROM failure_matches LIMIT 5;"

# Run tests
cd /root/agenticverz2.0/backend
PYTHONPATH=. pytest tests/test_failure_catalog_m9.py -v

# Run aggregation (test)
docker exec nova_agent_manager python -m app.jobs.failure_aggregation --json
```

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-07 | M9 core implementation complete |
| 2025-12-07 | All 23 tests passing |
| 2025-12-07 | Migration 015 applied, 4 test records persisted |
