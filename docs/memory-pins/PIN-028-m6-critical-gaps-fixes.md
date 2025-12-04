# PIN-028: M6 Critical Gaps & Fixes

**Status:** COMPLETE
**Created:** 2025-12-04
**Category:** Milestone / Implementation
**Depends On:** PIN-026, PIN-027

---

## Executive Summary

This PIN documents the implementation of 6 critical gaps identified in the M6 CostSim V2 Circuit Breaker implementation. All gaps have been addressed with proper fixes, tests verified, and CI updated.

---

## Critical Gaps Addressed

### 1. Sync-Compatibility Hack Fix (P0)

**Problem:** `AsyncCircuitBreaker.is_open()` returned `True` (disabled) when called from a running event loop, causing false-positive V2 disables.

**Root Cause:** Calling `asyncio.run()` from within a running event loop raises `RuntimeError`, and the fallback was too conservative.

**Solution:** Created thread-safe sync wrapper using `ThreadPoolExecutor`:

**File Created:** `backend/app/costsim/cb_sync_wrapper.py`

```python
def is_v2_disabled_sync(timeout: float = 5.0) -> bool:
    try:
        from app.costsim.circuit_breaker_async import is_v2_disabled
        try:
            loop = asyncio.get_running_loop()
            # We're in a running loop - use thread pool
            return _run_async_in_thread(is_v2_disabled(), timeout)
        except RuntimeError:
            # No running loop - safe to use asyncio.run()
            return asyncio.run(is_v2_disabled())
    except Exception as e:
        logger.error(f"is_v2_disabled_sync error: {e}, returning False (enabled)")
        return False  # Return False to avoid false-positive disables
```

**Decision:** Return `False` (enabled) on errors to avoid false-positive V2 disables.

---

### 2. Auto-Recovery SELECT FOR UPDATE (P0)

**Problem:** TOCTOU (Time-Of-Check-To-Time-Of-Use) race condition in auto-recovery where multiple workers could simultaneously recover the circuit breaker.

**Solution:** Added `_try_auto_recover()` function with proper row-level locking:

**File Modified:** `backend/app/costsim/circuit_breaker_async.py`

```python
async def _try_auto_recover(state_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                select(CostSimCBStateModel)
                .where(CostSimCBStateModel.id == state_id)
                .with_for_update()  # Critical: lock the row
            )
            state = result.scalars().first()
            if not state or not state.disabled:
                return False  # Already recovered by another worker
            # ... recovery logic within transaction ...
```

---

### 3. Provenance Backfill Script (P1)

**Problem:** No way to backfill historical V1 baseline data for comparison.

**Solution:** Created comprehensive CLI script with multiple modes:

**File Created:** `backend/scripts/backfill_provenance.py`

**Features:**
- Backfill from directory of JSONL files
- Backfill from single JSON/JSONL file
- Dry-run mode for preview
- Verification mode
- Deduplication via input_hash

**Usage:**
```bash
# Backfill from directory
DATABASE_URL="postgresql://..." python3 scripts/backfill_provenance.py --dir /var/lib/aos/provenance

# Verify results
DATABASE_URL="postgresql://..." python3 scripts/backfill_provenance.py --verify

# Dry-run mode
DATABASE_URL="postgresql://..." python3 scripts/backfill_provenance.py --dir /var/lib/aos/provenance --dry-run
```

---

### 4. Prometheus Metrics for CB Events (P1)

**Problem:** Missing observability for circuit breaker events.

**Solution:** Added 7 new metrics with recording methods:

**File Modified:** `backend/app/costsim/metrics.py`

| Metric | Type | Description |
|--------|------|-------------|
| `costsim_cb_disabled_total` | Counter | Total CB disable events |
| `costsim_cb_incidents_total` | Counter | Total CB incidents |
| `costsim_cb_alert_queue_depth` | Gauge | Current alert queue depth |
| `costsim_cb_alert_send_failures_total` | Counter | Alert send failures |
| `costsim_cb_enabled_total` | Counter | CB enable (recovery) events |
| `costsim_cb_auto_recovery_total` | Counter | Auto-recovery events |
| `costsim_cb_consecutive_failures` | Gauge | Current consecutive failures |

**Files Modified for Metrics Recording:**
- `circuit_breaker_async.py` - Added metrics in `_trip()`, `enable_v2()`, `_try_auto_recover()`, `report_drift()`
- `alert_worker.py` - Added queue depth and failure metrics

---

### 5. Leader Election Verification (P1)

**Problem:** Need to verify PostgreSQL advisory lock implementation is correct.

**Status:** VERIFIED CORRECT

**File:** `backend/app/costsim/leader.py`

**Implementation Review:**
- Uses `pg_try_advisory_lock()` for non-blocking acquisition
- Session-scoped locks automatically released on connection close
- Proper timeout handling with `asyncio.wait_for()`
- Error handling with logging
- All 16 leader election tests pass

---

### 6. CI Integration Tests with Real DB (P2)

**Problem:** Unit tests with mocks pass but don't catch real integration issues.

**Solution:** Added new CI job with real PostgreSQL and Alertmanager:

**File Modified:** `.github/workflows/ci.yml`

**New Job: `costsim-integration`**
```yaml
costsim-integration:
  runs-on: ubuntu-latest
  needs: costsim
  services:
    postgres:
      image: postgres:15
      # ... configuration ...
    alertmanager:
      image: prom/alertmanager:latest
      # ... configuration ...
  steps:
    - Run Alembic migrations
    - Run CB integration tests
    - Verify CB state table
    - Verify provenance table
    - Verify alert queue table
```

---

## Additional Issues & Fixes

### PgBouncer + asyncpg Prepared Statement Conflict

**Issue:** `DuplicatePreparedStatementError: prepared statement "__asyncpg_stmt_1__" already exists`

**Fix:** Added PgBouncer compatibility settings in `backend/app/db_async.py`:

```python
async_engine = create_async_engine(
    DATABASE_URL_ASYNC,
    connect_args={
        "prepared_statement_cache_size": 0,  # Required for PgBouncer
        "statement_cache_size": 0,
    },
)
```

### Alembic Migration Revision ID Too Long

**Issue:** `StringDataRightTruncation: value too long for type character varying(32)`

**Fix:** Shortened revision IDs:
```python
# Before
revision = '007_add_costsim_cb_state'  # 24 chars
revision = '008_add_provenance_and_alert_queue'  # 35 chars - TOO LONG

# After
revision = '007_costsim_cb'  # 14 chars
revision = '008_provenance_alerts'  # 21 chars
```

### Test Mock Update for Auto-Recovery

**Issue:** Test patching old `_auto_recover` function instead of new `_try_auto_recover`

**Fix:** Updated test in `tests/costsim/test_circuit_breaker_async.py`:
```python
# Before
with patch("app.costsim.circuit_breaker_async._auto_recover", new_callable=AsyncMock):

# After
with patch("app.costsim.circuit_breaker_async._try_auto_recover", new_callable=AsyncMock) as mock_recover:
    mock_recover.return_value = True
```

---

## Alert Rules Added

**File Modified:** `ops/prometheus_rules/alerts.yml`

Added 8 new CostSim-specific alert rules:

| Alert | Severity | Condition |
|-------|----------|-----------|
| CostSimV2HighDrift | P1 | p95 drift > 0.2 for 5m |
| CostSimV2DriftWarning | P2 | p95 drift > 0.15 for 15m |
| CostSimV2CircuitBreakerOpen | P1 | CB state == 1 (open) |
| CostSimV2CanaryFailure | P2 | Canary run failed in 24h |
| CostSimAlertQueueBacklog | P2 | Queue depth > 10 for 5m |
| CostSimAlertSendFailures | P2 | > 5 send failures in 1h |
| CostSimRapidCBTrips | P1 | > 3 trips in 1h |
| CostSimHighConsecutiveFailures | P2 | Consecutive failures > 2 |

---

## Files Modified/Created

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/costsim/cb_sync_wrapper.py` | Created | Thread-safe sync wrapper |
| `backend/app/costsim/circuit_breaker_async.py` | Modified | SELECT FOR UPDATE, metrics |
| `backend/app/costsim/metrics.py` | Modified | 7 new CB metrics |
| `backend/app/costsim/alert_worker.py` | Modified | Queue/failure metrics |
| `backend/app/costsim/__init__.py` | Modified | Sync wrapper exports |
| `backend/app/api/costsim.py` | Modified | Async method calls |
| `backend/app/db_async.py` | Modified | PgBouncer compatibility |
| `backend/scripts/backfill_provenance.py` | Created | Backfill CLI tool |
| `backend/alembic/versions/007_*.py` | Modified | Short revision ID |
| `backend/alembic/versions/008_*.py` | Modified | Short revision ID |
| `backend/tests/costsim/test_circuit_breaker_async.py` | Modified | Fixed auto-recovery test |
| `.github/workflows/ci.yml` | Modified | Integration test job |
| `ops/prometheus_rules/alerts.yml` | Modified | 8 CostSim alerts |

---

## Test Results

```
======================== 55 passed, 3 skipped in 1.56s =========================
```

- **55 passed**: All unit tests with mocks
- **3 skipped**: Integration tests (require real DB - run in CI `costsim-integration` job)

---

## Pending Items

| Priority | Item | Description |
|----------|------|-------------|
| P1 | Create runbook documents | `docs/runbooks/costsim-circuit-breaker.md`, `costsim-canary.md`, `costsim-alert-queue.md` |
| P2 | Add `@pytest.mark.integration` | To DB-backed tests for selective CI execution |
| P2 | Implement canary report storage | `GET /costsim/canary/reports` returns "not yet implemented" |
| P3 | Add CB state to `/health` | Expose circuit breaker state in health endpoint |
| P3 | Create Grafana dashboard | Dashboard for new CB metrics |
| P3 | Configure alert routing | Route CostSim alerts to appropriate channels |

---

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Return `False` on sync wrapper errors | Avoids false-positive V2 disables |
| Use `ThreadPoolExecutor` for sync wrapper | Safely executes async from any context |
| Use `SELECT FOR UPDATE` in separate transaction | Prevents TOCTOU race in auto-recovery |
| Keep metrics lazy-initialized | Avoids circular imports |
| Add comprehensive CI job with real services | Unit tests with mocks miss real issues |
| Short revision IDs (≤32 chars) | Alembic default column is `varchar(32)` |

---

## Verification Commands

```bash
# Run all CostSim tests
PYTHONPATH=/root/agenticverz2.0/backend python3 -m pytest tests/costsim/ -v

# Verify provenance backfill
DATABASE_URL="postgresql://nova:novapass@localhost:6432/nova_aos" \
  python3 scripts/backfill_provenance.py --verify

# Check CB state table
docker exec nova_db psql -U nova -d nova_aos -c "SELECT * FROM costsim_cb_state;"

# Check provenance table
docker exec nova_db psql -U nova -d nova_aos -c "SELECT count(*) FROM costsim_provenance;"
```

---

## Conclusion

All 6 critical gaps from the M6 implementation have been addressed:

1. ✅ Sync-compatibility hack replaced with thread-safe wrapper
2. ✅ Auto-recovery uses SELECT FOR UPDATE to prevent races
3. ✅ Provenance backfill script created and verified
4. ✅ Prometheus metrics added for CB events
5. ✅ Leader election verified correct
6. ✅ CI updated with integration test job

The M6 CostSim V2 implementation is now production-ready pending the P1-P3 pending items.
