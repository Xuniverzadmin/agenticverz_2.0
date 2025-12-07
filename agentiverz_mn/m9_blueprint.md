# M9 BLUEPRINT — Failure Catalog v2 + Persistence + Metrics

**Duration:** 2 Weeks
**Status:** IN PROGRESS
**Created:** 2025-12-07
**Objective:** Convert all failures into durable, queryable, machine-native data.

---

## Executive Summary

M9 adds persistence to the failure catalog, enabling:
- Learning from runtime errors
- Recovery suggestion engine (M10 foundation)
- Failure analytics dashboards
- Pattern aggregation for unknown errors

---

## Implementation Status

### Completed Components

| Component | File | Status |
|-----------|------|--------|
| Migration 015 | `alembic/versions/015_create_failure_matches.py` | ✅ Created |
| FailureMatch SQLModel | `app/db.py` | ✅ Added |
| Persistence Layer | `app/runtime/failure_catalog.py` | ✅ Updated |
| Prometheus Metrics | `app/runtime/failure_catalog.py` | ✅ Added |
| Aggregation Job | `app/jobs/failure_aggregation.py` | ✅ Created |
| Grafana Dashboard | `monitoring/dashboards/m9_failure_catalog_v2.json` | ✅ Created |
| Alert Rules | `monitoring/rules/m9_failure_catalog_alerts.yml` | ✅ Created |
| Unit Tests | `tests/test_failure_catalog_m9.py` | ✅ Created |

### Pending Steps

| Step | Description | Status |
|------|-------------|--------|
| Apply migration | Run `alembic upgrade head` | ⏳ Pending |
| Deploy backend | Rebuild and deploy with new code | ⏳ Pending |
| Import dashboard | Add to Grafana | ⏳ Pending |
| Reload Prometheus | Load new alert rules | ⏳ Pending |
| Generate test traffic | Verify persistence | ⏳ Pending |
| Tag release | Create m9.0.0 tag | ⏳ Pending |

---

## Technical Specification

### 1. Database Table: `failure_matches`

```sql
CREATE TABLE failure_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id TEXT NOT NULL,
    tenant_id TEXT,
    error_code TEXT NOT NULL,
    error_message TEXT,
    catalog_entry_id TEXT,
    match_type TEXT NOT NULL DEFAULT 'unknown',
    confidence_score FLOAT NOT NULL DEFAULT 0.0,
    category TEXT,
    severity TEXT,
    is_retryable BOOLEAN DEFAULT FALSE,
    recovery_mode TEXT,
    recovery_suggestion TEXT,
    recovery_attempted BOOLEAN DEFAULT FALSE,
    recovery_succeeded BOOLEAN DEFAULT FALSE,
    skill_id TEXT,
    step_index INTEGER,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Indexes:**
- `idx_fm_run_id` - Run correlation
- `idx_fm_error_code` - Error code lookup
- `idx_fm_catalog_entry` - Catalog entry lookup
- `idx_fm_created_at` - Time-series queries
- `idx_fm_unmatched` - Unknown error aggregation
- `idx_fm_recovery_pending` - Recovery tracking

### 2. Prometheus Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `failure_match_hits_total` | Counter | error_code, category, recovery_mode | Matched catalog entries |
| `failure_match_misses_total` | Counter | error_code | Unmatched errors |
| `recovery_success_total` | Counter | recovery_mode, error_code | Successful recoveries |
| `recovery_failure_total` | Counter | recovery_mode, error_code | Failed recoveries |

### 3. API Functions

```python
# Persist a failure match
persist_failure_match(
    run_id: str,
    result: MatchResult,
    error_code: str,
    error_message: Optional[str] = None,
    tenant_id: Optional[str] = None,
    skill_id: Optional[str] = None,
    step_index: Optional[int] = None,
    context: Optional[Dict] = None,
) -> Optional[str]

# Async version
persist_failure_match_async(...)

# Update recovery status
update_recovery_status(
    failure_match_id: str,
    succeeded: bool,
) -> bool

# Match and persist in one call (recommended)
match_and_persist(
    code_or_message: str,
    run_id: str,
    tenant_id: Optional[str] = None,
    skill_id: Optional[str] = None,
    step_index: Optional[int] = None,
    context: Optional[Dict] = None,
    error_message: Optional[str] = None,
) -> MatchResult
```

### 4. Aggregation Job

**Location:** `app/jobs/failure_aggregation.py`

**Usage:**
```bash
# Run manually
python -m app.jobs.failure_aggregation

# With options
python -m app.jobs.failure_aggregation --days 14 --min-occurrences 5

# Custom output
python -m app.jobs.failure_aggregation --output /custom/path/patterns.json
```

**Output:** `candidate_failure_patterns.json`
```json
{
  "generated_at": "2025-12-07T10:00:00Z",
  "pattern_count": 15,
  "patterns": [
    {
      "signature": "abc123...",
      "primary_error_code": "HTTP_CUSTOM_ERROR",
      "total_occurrences": 47,
      "suggested_category": "TRANSIENT",
      "suggested_recovery": "RETRY_EXPONENTIAL",
      "examples": [...]
    }
  ]
}
```

**Schedule:**
```bash
# Cron (nightly at 2 AM)
0 2 * * * cd /root/agenticverz2.0/backend && python -m app.jobs.failure_aggregation
```

---

## Grafana Dashboard

**Name:** M9 - Failure Catalog v2
**UID:** `m9-failure-catalog-v2`
**File:** `monitoring/dashboards/m9_failure_catalog_v2.json`

**Panels:**
1. Catalog Hit Rate (stat)
2. Catalog Hits 24h (stat)
3. Catalog Misses 24h (stat)
4. Recovery Success Rate (stat)
5. Failure Frequency by Error Code (timeseries)
6. Failure Frequency by Category (timeseries)
7. Top 10 Unknown Error Classes (timeseries)
8. Catalog Miss Rate - Drift Signal (timeseries)
9. Recovery Success by Mode (timeseries)
10. Recovery Failures by Mode (timeseries)

---

## Alert Rules

**File:** `monitoring/rules/m9_failure_catalog_alerts.yml`

| Alert | Threshold | Severity |
|-------|-----------|----------|
| FailureCatalogHighMissRate | >30% miss rate for 15m | warning |
| FailureCatalogCriticalMissRate | >50% miss rate for 5m | critical |
| FailureRecoveryLowSuccessRate | <50% recovery for 30m | warning |
| FailureCodeSpike | >10/s for any code | warning |
| FailurePersistenceDown | No persistence while runs active | critical |
| FailureAggregationStale | Job not run in 2+ days | warning |
| HighTransientErrorVolume | >5/s transient errors | warning |
| PermissionErrorSpike | >1/s auth errors | warning |
| ResourceExhaustionErrors | >0.5/s budget errors | warning |

---

## Acceptance Criteria

| Requirement | Verification |
|-------------|--------------|
| `failure_matches` table exists | `\d failure_matches` in psql |
| All failure paths persist | Integration tests pass |
| Dashboard shows patterns | Grafana panels render |
| ≥5 unique catalog matches | Query `SELECT COUNT(DISTINCT catalog_entry_id) FROM failure_matches` |
| Aggregation job outputs JSON | File exists at output path |
| Metrics exported | Check `/metrics` endpoint |
| Alert rules loaded | Prometheus `/rules` shows alerts |

---

## Deployment Steps

```bash
# 1. Apply migration
cd /root/agenticverz2.0/backend
alembic upgrade head

# 2. Rebuild and deploy
cd /root/agenticverz2.0
docker compose up -d --build backend worker

# 3. Verify table exists
docker exec -it nova_db psql -U nova -d nova_aos -c "\d failure_matches"

# 4. Import Grafana dashboard
# Manual: Import monitoring/dashboards/m9_failure_catalog_v2.json

# 5. Reload Prometheus rules
curl -X POST http://localhost:9090/-/reload

# 6. Run aggregation job (test)
docker exec nova_agent_manager python -m app.jobs.failure_aggregation --json

# 7. Generate test traffic
# Run integration tests or create synthetic failures

# 8. Verify metrics
curl -s http://localhost:8000/metrics | grep failure_match

# 9. Tag release
git tag m9.0.0
git push origin m9.0.0
```

---

## Files Created/Modified

| File | Change |
|------|--------|
| `alembic/versions/015_create_failure_matches.py` | **NEW** - Migration |
| `app/db.py` | Modified - Added FailureMatch model |
| `app/runtime/failure_catalog.py` | Modified - Added persistence layer |
| `app/jobs/__init__.py` | **NEW** - Jobs module |
| `app/jobs/failure_aggregation.py` | **NEW** - Aggregation job |
| `monitoring/dashboards/m9_failure_catalog_v2.json` | **NEW** - Dashboard |
| `monitoring/rules/m9_failure_catalog_alerts.yml` | **NEW** - Alert rules |
| `tests/test_failure_catalog_m9.py` | **NEW** - Test suite |

---

## Next Steps (M10)

After M9 is complete:
1. Recovery Suggestion API (`POST /api/v1/recovery/suggest`)
2. `recovery_candidates` table
3. Confidence scoring model
4. CLI commands for recovery management

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-07 | Created M9 blueprint |
| 2025-12-07 | Created migration 015_create_failure_matches.py |
| 2025-12-07 | Added FailureMatch SQLModel to db.py |
| 2025-12-07 | Updated failure_catalog.py with persistence |
| 2025-12-07 | Created aggregation job |
| 2025-12-07 | Created Grafana dashboard |
| 2025-12-07 | Created alert rules |
| 2025-12-07 | Created test suite |
