# PIN-057: M10 Recovery Suggestion Engine Enhancement

**Date**: 2025-12-09
**Status**: COMPLETE (Phase 5 - Leader Election & DB-Backed Idempotency)
**Category**: Implementation / M10
**Author**: Claude Code Implementation
**Last Updated**: 2025-12-09 (Phase 5 Production Hardening)

---

## Summary

Enhancement to the M10 Recovery Suggestion Engine adding:
- Rule-based evaluation engine for automated action selection
- Action catalog with templates and effectiveness tracking
- Input/provenance tracking for audit and debugging
- Worker integration with hook system
- Enhanced API endpoints

### Phase 2 Additions (2025-12-09)

- **Migration 019**: pgcrypto extension, idempotency_key, materialized view, archive tables
- **Migration 020**: CONCURRENT index creation for production
- **Idempotent Ingest Endpoint**: `/api/v1/recovery/ingest` with IntegrityError handling
- **Worker Claim Pattern**: `FOR UPDATE SKIP LOCKED` for concurrent-safe batch processing
- **Retention Archive Job**: Automated archival with configurable retention periods
- **Operations Runbook**: `docs/runbooks/M10_RECOVERY_OPERATIONS.md`

---

## Changes Implemented

### 1. Database Schema Enhancement (`alembic/versions/018_add_m10_recovery_enhancements.py`)

**New Schema: `m10_recovery`**

Three new tables for enhanced functionality:

#### suggestion_input
Tracks structured inputs used in rule evaluation:
```sql
m10_recovery.suggestion_input (
    id SERIAL PRIMARY KEY,
    suggestion_id INT NOT NULL,
    input_type TEXT NOT NULL,  -- error_code, error_message, skill_context, etc.
    raw_value TEXT NOT NULL,
    normalized_value TEXT,
    parsed_data JSONB,
    confidence REAL DEFAULT 1.0,
    weight REAL DEFAULT 1.0,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
)
```

#### suggestion_action
Catalog of recovery actions with templates:
```sql
m10_recovery.suggestion_action (
    id SERIAL PRIMARY KEY,
    action_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    action_type TEXT NOT NULL,  -- retry, fallback, escalate, notify, etc.
    template JSONB NOT NULL,
    applies_to_error_codes TEXT[],
    applies_to_skills TEXT[],
    success_rate REAL DEFAULT 0.0,
    total_applications INT DEFAULT 0,
    is_automated BOOLEAN DEFAULT FALSE,
    requires_approval BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 50,
    is_active BOOLEAN DEFAULT TRUE
)
```

#### suggestion_provenance
Complete lineage tracking:
```sql
m10_recovery.suggestion_provenance (
    id SERIAL PRIMARY KEY,
    suggestion_id INT NOT NULL,
    event_type TEXT NOT NULL,  -- created, rule_evaluated, approved, executed, etc.
    details JSONB,
    rule_id TEXT,
    action_id INT,
    confidence_before REAL,
    confidence_after REAL,
    actor TEXT,
    actor_type TEXT,  -- system, human, agent
    created_at TIMESTAMPTZ,
    duration_ms INT
)
```

**Columns Added to recovery_candidates:**
- `selected_action_id` - Link to action catalog
- `rules_evaluated` - JSONB array of rule evaluation results
- `execution_status` - pending/executing/succeeded/failed/rolled_back/skipped
- `executed_at` - Timestamp of execution
- `execution_result` - JSONB result data

### 2. Rule Engine (`app/services/recovery_rule_engine.py`)

**Rule Types:**
- `ErrorCodeRule` - Match by error code pattern
- `HistoricalPatternRule` - Match based on historical success
- `SkillSpecificRule` - Match by skill ID
- `OccurrenceThresholdRule` - Escalate based on repeat count
- `CompositeRule` - Combine rules with AND/OR logic

**Default Rules:**
```python
DEFAULT_RULES = [
    ErrorCodeRule("timeout_retry", ["TIMEOUT"], "retry_exponential", priority=90),
    ErrorCodeRule("rate_limit_backoff", ["RATE_LIMIT", "429"], "retry_exponential", priority=85),
    ErrorCodeRule("server_error_fallback", ["HTTP_5XX"], "circuit_breaker", priority=80),
    ErrorCodeRule("budget_fallback", ["BUDGET"], "fallback_model", priority=75),
    HistoricalPatternRule("historical_success", min_occurrences=3, priority=60),
    OccurrenceThresholdRule("escalate_repeated", threshold=5, "notify_ops", priority=40),
]
```

**Usage:**
```python
from app.services.recovery_rule_engine import evaluate_rules

result = evaluate_rules(
    error_code="TIMEOUT",
    error_message="Connection timed out",
    skill_id="http_call",
    occurrence_count=3,
)

print(result.recommended_action)  # "retry_exponential"
print(result.confidence)  # 0.85
```

### 3. SQLAlchemy Models (`app/models/m10_recovery.py`)

Async SQLAlchemy models for all new tables:
- `SuggestionInput`
- `SuggestionAction`
- `SuggestionProvenance`

Each includes:
- Type hints
- Validation constraints
- `to_dict()` serialization
- Business logic methods (e.g., `matches_error()`)

### 4. Enhanced API Endpoints (`app/api/recovery.py`)

**New Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/recovery/candidates/{id}` | GET | Get candidate with full context |
| `/api/v1/recovery/candidates/{id}` | PATCH | Update execution status/action |
| `/api/v1/recovery/actions` | GET | List available actions |
| `/api/v1/recovery/evaluate` | POST | Evaluate rules without persisting |

**New Models:**
- `CandidateDetailResponse` - Full candidate with provenance, inputs, action
- `CandidateUpdateRequest` - Update execution status
- `EvaluateRequest/Response` - Rule evaluation
- `ActionResponse/ActionListResponse` - Action catalog

### 5. Worker Evaluator (`app/worker/recovery_evaluator.py`)

**Features:**
- Automatic failure evaluation
- Rule-based action selection
- Provenance recording
- Optional auto-execution

**Hook System:**
```python
from app.worker.recovery_evaluator import register_hook

def on_suggestion(event, candidate_id, confidence, **kwargs):
    print(f"Suggestion generated: {candidate_id} ({confidence:.1%})")

register_hook("on_suggestion_generated", on_suggestion)
```

**Available Hooks:**
- `on_evaluation_start`
- `on_suggestion_generated`
- `on_action_selected`
- `on_execution_start`
- `on_execution_complete`

### 6. Seeded Actions

Migration seeds default actions:
```
retry_exponential    - Retry with exponential backoff (priority: 80)
fallback_model       - Switch to fallback LLM model (priority: 70)
circuit_breaker      - Enable circuit breaker (priority: 60)
notify_ops           - Notify operations team (priority: 50)
rollback_state       - Rollback to checkpoint (priority: 40)
manual_intervention  - Flag for manual review (priority: 30)
skip_task            - Skip and continue (priority: 20)
```

---

## Environment Variables

```bash
# Rule Engine
RECOVERY_RULE_DEBUG=false          # Enable debug logging

# Worker Evaluator
RECOVERY_EVALUATOR_ENABLED=true    # Enable/disable evaluator
RECOVERY_AUTO_EXECUTE=false        # Auto-execute automated actions
RECOVERY_MIN_CONFIDENCE=0.3        # Minimum confidence for suggestions
```

---

## Files Created/Modified

### New Files
| File | Purpose |
|------|---------|
| `alembic/versions/018_add_m10_recovery_enhancements.py` | Database migration |
| `app/models/m10_recovery.py` | SQLAlchemy models |
| `app/services/recovery_rule_engine.py` | Rule evaluation engine |
| `app/worker/recovery_evaluator.py` | Worker integration |
| `tests/test_m10_recovery_enhanced.py` | Comprehensive tests |

### Modified Files
| File | Changes |
|------|---------|
| `app/api/recovery.py` | Added new endpoints and models |

---

## Testing

```bash
cd /root/agenticverz2.0/backend

# Run M10 enhanced tests
PYTHONPATH=. python3 -m pytest tests/test_m10_recovery_enhanced.py -v

# Test rule engine
PYTHONPATH=. python3 -c "
from app.services.recovery_rule_engine import evaluate_rules

result = evaluate_rules(
    error_code='TIMEOUT',
    error_message='Connection timed out',
)
print(f'Action: {result.recommended_action}')
print(f'Confidence: {result.confidence:.2f}')
print(f'Rules evaluated: {len(result.rules_evaluated)}')
"

# Test worker evaluator
PYTHONPATH=. python3 -c "
import asyncio
from app.worker.recovery_evaluator import evaluate_failure

async def test():
    result = await evaluate_failure(
        failure_match_id='test-uuid',
        error_code='RATE_LIMITED',
        error_message='Too many requests',
    )
    print(f'Suggested action: {result.suggested_action}')
    print(f'Confidence: {result.confidence:.2f}')

asyncio.run(test())
"
```

---

## Migration

To apply the migration:
```bash
cd /root/agenticverz2.0/backend
DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic upgrade head
```

---

## API Examples

### Evaluate Rules
```bash
curl -X POST http://localhost:8000/api/v1/recovery/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "error_code": "TIMEOUT",
    "error_message": "Connection timed out after 30s",
    "skill_id": "http_call",
    "occurrence_count": 3
  }'
```

### Get Candidate Details
```bash
curl http://localhost:8000/api/v1/recovery/candidates/1?include_provenance=true
```

### Update Candidate Status
```bash
curl -X PATCH http://localhost:8000/api/v1/recovery/candidates/1 \
  -H "Content-Type: application/json" \
  -d '{
    "execution_status": "executing",
    "selected_action_id": 1
  }'
```

### List Actions
```bash
curl "http://localhost:8000/api/v1/recovery/actions?action_type=retry"
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Recovery Flow                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   ┌─────────┐    ┌──────────────┐    ┌─────────────────┐    │
│   │ Failure │───▶│  Evaluator   │───▶│ Rule Engine     │    │
│   │  Event  │    │   Worker     │    │ (10+ rules)     │    │
│   └─────────┘    └──────────────┘    └─────────────────┘    │
│                         │                    │               │
│                         ▼                    ▼               │
│                  ┌──────────────┐    ┌─────────────────┐    │
│                  │   Matcher    │    │ Action Catalog  │    │
│                  │  (existing)  │    │  (7 actions)    │    │
│                  └──────────────┘    └─────────────────┘    │
│                         │                    │               │
│                         ▼                    ▼               │
│                  ┌──────────────────────────────────┐       │
│                  │     recovery_candidates          │       │
│                  │  + suggestion_input              │       │
│                  │  + suggestion_provenance         │       │
│                  └──────────────────────────────────┘       │
│                                                               │
│                         │                                     │
│                         ▼                                     │
│                  ┌──────────────┐                            │
│                  │ Auto-Execute │ (if enabled & automated)   │
│                  └──────────────┘                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

---

## Phase 2: Production Hardening (2025-12-09)

### Migration 019: Enhancement Migration

**File**: `alembic/versions/019_m10_recovery_enhancements.py`

**Features:**
- Ensures `pgcrypto` extension for `gen_random_uuid()`
- Adds `idempotency_key` column to `recovery_candidates` for deduplication
- Creates `m10_recovery.mv_top_pending` materialized view for dashboard performance
- Creates worker claim index for unevaluated inputs
- Creates `retention_jobs` metadata table for archival tracking
- Creates archive tables: `suggestion_provenance_archive`, `suggestion_input_archive`
- Creates `refresh_mv_top_pending()` function for scheduled refreshes

```sql
-- New columns
ALTER TABLE recovery_candidates ADD COLUMN idempotency_key UUID UNIQUE;

-- Materialized view
CREATE MATERIALIZED VIEW m10_recovery.mv_top_pending AS
SELECT rc.id, rc.suggestion, rc.confidence, rc.occurrence_count, ...
FROM recovery_candidates rc
WHERE rc.decision = 'pending'
ORDER BY confidence DESC;

-- Archive tables
CREATE TABLE m10_recovery.suggestion_provenance_archive (
    LIKE m10_recovery.suggestion_provenance INCLUDING ALL,
    archived_at TIMESTAMPTZ DEFAULT now()
);
```

### Migration 020: Concurrent Indexes

**File**: `alembic/versions/020_m10_concurrent_indexes.py`

**Purpose**: Create heavy indexes using `CREATE INDEX CONCURRENTLY` during maintenance windows.

```sql
CREATE INDEX CONCURRENTLY idx_rc_confidence_desc ON recovery_candidates (confidence DESC);
CREATE INDEX CONCURRENTLY idx_rc_decision_created ON recovery_candidates (decision, created_at DESC);
CREATE INDEX CONCURRENTLY idx_sp_suggestion_created ON m10_recovery.suggestion_provenance (suggestion_id, created_at DESC);
```

### Idempotent Ingest Endpoint

**File**: `app/api/recovery_ingest.py`

**Endpoint**: `POST /api/v1/recovery/ingest`

**Features:**
- Idempotency key support: duplicate requests return existing candidate
- IntegrityError handling: catches constraint violations gracefully
- Occurrence count updates: duplicates increment occurrence_count
- Optional evaluation enqueue

```python
# Request
{
    "failure_match_id": "uuid",
    "failure_payload": {"error_type": "TIMEOUT", "raw": "..."},
    "idempotency_key": "optional-uuid",
    "enqueue_evaluation": true
}

# Response
{
    "candidate_id": 123,
    "status": "accepted|duplicate",
    "is_duplicate": false,
    "failure_match_id": "uuid"
}
```

### Worker Claim Pattern

**File**: `app/worker/recovery_claim_worker.py`

**Pattern**: `FOR UPDATE SKIP LOCKED` for concurrent-safe row claiming

```sql
WITH claimed AS (
    SELECT id FROM recovery_candidates
    WHERE decision = 'pending'
      AND (confidence IS NULL OR confidence <= 0.2)
    ORDER BY created_at ASC
    FOR UPDATE SKIP LOCKED
    LIMIT :batch_size
)
UPDATE recovery_candidates rc
SET execution_status = 'executing'
FROM claimed
WHERE rc.id = claimed.id
RETURNING rc.*;
```

**Features:**
- Multiple workers can run without conflicts
- Graceful shutdown releases claimed rows
- Async integration with RecoveryEvaluator

**Usage:**
```bash
python -m app.worker.recovery_claim_worker --batch-size 50 --poll-interval 10
```

### Retention Archive Job

**File**: `scripts/ops/m10_retention_archive.py`

**Features:**
- Configurable retention periods per table (default: 90 days)
- Dry-run mode for testing
- Atomic archive + delete operations
- Updates `retention_jobs` table with metadata

**Usage:**
```bash
# Dry run
python m10_retention_archive.py --dry-run

# Archive with default retention
python m10_retention_archive.py

# Specific job
python m10_retention_archive.py --job provenance_archive --retention-days 60
```

---

## Phase 2 Files Created

| File | Purpose |
|------|---------|
| `alembic/versions/019_m10_recovery_enhancements.py` | Enhancement migration |
| `alembic/versions/020_m10_concurrent_indexes.py` | Concurrent indexes |
| `app/api/recovery_ingest.py` | Idempotent ingest endpoint with Prometheus metrics |
| `app/worker/recovery_claim_worker.py` | FOR UPDATE SKIP LOCKED worker |
| `app/tasks/recovery_queue.py` | Redis-based task queue for evaluation |
| `scripts/ops/m10_retention_archive.py` | Retention archive job |
| `docs/runbooks/M10_RECOVERY_OPERATIONS.md` | Operations runbook |

## Phase 2 Files Modified

| File | Changes |
|------|---------|
| `app/main.py` | Registered `recovery_ingest_router` |
| `app/metrics.py` | Added M10 ingest metrics (counter, histogram, gauges) |
| `tests/test_m10_recovery_enhanced.py` | Added concurrent ingest race test, worker claim tests |

---

## Redis Task Queue

**File**: `app/tasks/recovery_queue.py`

Async Redis-based queue for candidate evaluation:

```python
from app.tasks.recovery_queue import enqueue_evaluation, dequeue_evaluation

# Enqueue candidate
await enqueue_evaluation(candidate_id=123, priority=0)

# Dequeue (worker side)
task = await dequeue_evaluation(timeout=5)
if task:
    await process(task["candidate_id"])
```

**Queue Keys:**
- `m10:evaluate` - Normal priority queue (FIFO)
- `m10:evaluate:priority` - Priority queue (sorted set)
- `m10:evaluate:processing` - Currently processing (hash)
- `m10:evaluate:failed` - Failed tasks for retry

**Environment Variables:**
- `REDIS_URL` - Redis connection URL (default: `redis://localhost:6379/0`)
- `RECOVERY_QUEUE_KEY` - Queue key name (default: `m10:evaluate`)

---

## Prometheus Metrics

**File**: `app/metrics.py`

New M10 ingest metrics:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `recovery_ingest_total` | Counter | status, source | Total ingest requests |
| `recovery_ingest_latency_seconds` | Histogram | status | Ingest latency |
| `recovery_ingest_duplicates_total` | Counter | detection_method | Duplicate detections |
| `recovery_ingest_enqueue_total` | Counter | status | Enqueue attempts |
| `recovery_evaluation_queue_depth` | Gauge | - | Queue depth |

**Labels:**
- `status`: accepted, duplicate, error
- `source`: api, webhook, worker
- `detection_method`: idempotency_key, failure_match_id, integrity_error

---

## Migration Commands

```bash
cd /root/agenticverz2.0/backend

# Apply enhancement migration
DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic upgrade 019_m10_recovery_enhancements

# Apply concurrent indexes (run during maintenance)
DATABASE_URL="$DATABASE_URL" PYTHONPATH=. alembic upgrade 020_m10_concurrent_indexes
```

---

## Verification SQL

```sql
-- Verify idempotency_key column
SELECT column_name FROM information_schema.columns
WHERE table_name = 'recovery_candidates' AND column_name = 'idempotency_key';

-- Verify materialized view
SELECT COUNT(*) FROM m10_recovery.mv_top_pending;

-- Verify retention jobs seeded
SELECT name, retention_days FROM m10_recovery.retention_jobs;

-- Verify archive tables
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'm10_recovery' AND table_name LIKE '%_archive';
```

---

---

## Phase 3: Observability (2025-12-09)

### Overview

Phase 3 addresses observability gaps identified in production readiness review:
- Redis Streams durability with dead-letter handling
- DB fallback queue for Redis outages
- Comprehensive Prometheus metrics
- Grafana dashboard for M10 subsystem
- Redis HA/persistence documentation

### Migration 021: Durable Queue Fallback

**File**: `alembic/versions/021_m10_durable_queue_fallback.py`

**Features:**
- `m10_recovery.work_queue` - DB fallback queue table
- `uq_rc_fmid_sig` - Unique index for upsert deduplication
- `matview_freshness` - Tracking table for matview age
- Queue functions: `enqueue_work()`, `claim_work()`, `complete_work()`, `release_stalled_work()`
- `refresh_mv_tracked()` - Matview refresh with logging

```sql
-- DB fallback queue
CREATE TABLE m10_recovery.work_queue (
    id BIGSERIAL PRIMARY KEY,
    candidate_id INT NOT NULL,
    method TEXT DEFAULT 'db_fallback',
    priority INT DEFAULT 0,
    enqueued_at TIMESTAMPTZ DEFAULT now(),
    claimed_at TIMESTAMPTZ,
    claimed_by TEXT,
    processed_at TIMESTAMPTZ,
    success BOOLEAN,
    error_message TEXT
);

-- Unique index for upsert
CREATE UNIQUE INDEX uq_rc_fmid_sig ON recovery_candidates
    (failure_match_id, error_signature);
```

### Redis Streams with Dead-Letter

**File**: `app/tasks/recovery_queue_stream.py`

**Features:**
- Redis Streams (XADD/XREADGROUP/XCLAIM/XACK) for durable messaging
- Consumer groups for distributed processing
- Dead-letter stream for poison messages (after 3 reclaim attempts)
- Automatic consumer group creation (idempotent)

**Key Functions:**
```python
# Enqueue to stream
await enqueue_stream(candidate_id, priority=0)

# Dequeue with consumer group
msgs = await dequeue_stream(consumer_id, count=10)

# Acknowledge processed
await ack_stream(msg_id)

# Process stalled with dead-letter
results = await process_stalled_with_dead_letter(idle_ms=60000)
# Returns: {"reclaimed": N, "dead_lettered": M}

# Replay from dead-letter
new_id = await replay_dead_letter(msg_id)
```

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `M10_STREAM_KEY` | `m10:evaluate:stream` | Stream key |
| `M10_CONSUMER_GROUP` | `m10:evaluate:group` | Consumer group |
| `M10_STREAM_MAX_LEN` | `100000` | Max stream length |
| `M10_CLAIM_IDLE_MS` | `60000` | Idle time before XCLAIM |
| `M10_MAX_RECLAIM_ATTEMPTS` | `3` | Max reclaims before dead-letter |
| `M10_DEAD_LETTER_STREAM` | `m10:evaluate:dead-letter` | Dead-letter stream |

### Metrics Collection Task

**File**: `app/tasks/m10_metrics_collector.py`

Periodic Prometheus gauge updates for:
- Redis stream length, pending, consumers
- DB queue depth and stalled count
- Matview freshness age
- Pending candidates count

**Usage:**
```bash
# One-time collection
PYTHONPATH=. python -m app.tasks.m10_metrics_collector

# Background loop (30s interval)
PYTHONPATH=. python -c "
import asyncio
from app.tasks.m10_metrics_collector import run_metrics_collector
asyncio.run(run_metrics_collector(interval=30))
"
```

### Prometheus Metrics (Extended)

**File**: `app/metrics.py`

New M10 queue/worker/matview metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `recovery_stream_length` | Gauge | Messages in Redis stream |
| `recovery_stream_pending` | Gauge | Pending (unacknowledged) messages |
| `recovery_stream_consumers` | Gauge | Active consumers |
| `recovery_db_queue_depth` | Gauge | Items in DB fallback queue |
| `recovery_db_queue_stalled` | Gauge | Stalled items (claimed > 5min) |
| `recovery_worker_claimed_total` | Counter | Work items claimed by workers |
| `recovery_worker_processed_total` | Counter | Work items processed |
| `recovery_worker_processing_seconds` | Histogram | Processing duration |
| `recovery_matview_age_seconds` | Gauge | Matview age since last refresh |
| `recovery_matview_last_refresh_timestamp` | Gauge | Last refresh timestamp |
| `recovery_matview_refresh_duration_seconds` | Histogram | Refresh duration |
| `recovery_matview_refresh_total` | Counter | Refresh attempts |

### Prometheus Alert Rules

**File**: `monitoring/rules/m10_recovery_alerts.yml`

15 alert rules across 5 groups:

| Group | Alerts |
|-------|--------|
| `m10_recovery_ingest` | Error rate, duplicate rate, latency |
| `m10_recovery_queue` | Enqueue failures, queue depth, pending messages, no consumers |
| `m10_recovery_worker` | Failure rate, latency, no activity |
| `m10_recovery_matview` | Stale matview, refresh failures, slow refresh |
| `m10_recovery_candidates` | Pending backlog, suggestion latency |

**Key Alerts:**

| Alert | Threshold | Severity |
|-------|-----------|----------|
| M10IngestErrorRateHigh | >5% for 5m | Critical |
| M10EnqueueFailureRateHigh | >1% for 5m | Critical |
| M10QueueDepthCritical | >5000 for 5m | Critical |
| M10MatviewVeryStale | >1 hour | Critical |
| M10NoStreamConsumers | 0 for 5m | Critical |

### Grafana Dashboard

**File**: `monitoring/grafana/provisioning/dashboards/files/m10_recovery_dashboard.json`

**Dashboard Sections:**
1. **Overview Row:** Total queue depth, active consumers, matview age, pending ACKs, candidates pending, DB stalled
2. **Ingest Row:** Ingest rate by status, ingest latency percentiles (p50/p95/p99)
3. **Queue Row:** Queue depth stacked (Redis + DB), enqueue rate
4. **Worker Row:** Worker claims, processed rate, processing time percentiles
5. **Suggestions & Matview Row:** Suggestions by decision, matview age, refresh duration
6. **Alerts Row:** Active M10 alerts panel

**Access:** http://localhost:3000/d/m10-recovery

### Redis Outage Fallback Tests

**File**: `tests/test_m10_recovery_enhanced.py`

New test classes:
- `TestRedisOutageScenarios` - Complete Redis outage, timeout handling, dead-letter operations
- `TestMetricsCollection` - Metrics collector runs, Redis unavailable handling

### Redis HA/Persistence Documentation

**File**: `docs/runbooks/M10_RECOVERY_OPERATIONS.md`

New sections added:
- Redis HA & Persistence Requirements (AOF, memory policy, Sentinel, Cluster)
- Production Checklist
- Disaster Recovery procedures
- Dead-Letter Operations (monitor, replay, bulk replay)
- Metrics Collection (start, Grafana dashboard)
- Environment Variables reference table

---

## Phase 3 Files Created

| File | Purpose |
|------|---------|
| `alembic/versions/021_m10_durable_queue_fallback.py` | DB fallback queue migration |
| `app/tasks/recovery_queue_stream.py` | Redis Streams + dead-letter |
| `app/tasks/m10_metrics_collector.py` | Prometheus metrics collection |
| `monitoring/rules/m10_recovery_alerts.yml` | 15 Prometheus alert rules |
| `monitoring/grafana/provisioning/dashboards/files/m10_recovery_dashboard.json` | Grafana dashboard |

## Phase 3 Files Modified

| File | Changes |
|------|---------|
| `app/api/recovery_ingest.py` | Redis Streams + DB fallback enqueue |
| `app/metrics.py` | Added 13 new M10 metrics |
| `monitoring/prometheus.yml` | Added `recovery_.*` to remote write filter |
| `tests/test_m10_recovery_enhanced.py` | Added Redis outage and metrics tests |
| `docs/runbooks/M10_RECOVERY_OPERATIONS.md` | Added Redis HA, dead-letter, metrics sections |

---

## Architecture (Phase 3)

```
                                    ┌─────────────────────────────────────┐
                                    │         Prometheus                  │
                                    │  (scrapes /metrics every 5s)        │
                                    └──────────────┬──────────────────────┘
                                                   │
┌─────────────┐    ┌─────────────┐    ┌────────────▼────────────┐
│   Ingest    │───▶│   Redis     │───▶│   m10:evaluate:stream   │
│  Endpoint   │    │  Streams    │    │  (consumer group)       │
└──────┬──────┘    └──────┬──────┘    └────────────┬────────────┘
       │                  │                        │
       │ (on Redis fail)  │                        ▼
       │                  │           ┌────────────────────────┐
       ▼                  │           │   Recovery Workers     │
┌─────────────┐           │           │  (XREADGROUP/XACK)     │
│  DB Queue   │◀──────────┘           └────────────┬───────────┘
│  (fallback) │                                    │
└─────────────┘                                    │ (on 3+ failures)
                                                   ▼
                                    ┌─────────────────────────────┐
                                    │  m10:evaluate:dead-letter   │
                                    │  (poison messages)          │
                                    └─────────────────────────────┘
                                                   │
                                                   ▼ (manual replay)
                                    ┌─────────────────────────────┐
                                    │   replay_dead_letter()      │
                                    └─────────────────────────────┘
```

---

## Pending Production Tasks

| Priority | Task | Notes |
|----------|------|-------|
| P1 | Run migrations on production | `alembic upgrade 021_m10_durable_queue_fallback` |
| P1 | Configure Redis persistence | Enable AOF, `noeviction` policy |
| P2 | Set up metrics collector service | Add to systemd/supervisor |
| P2 | Configure matview refresh cron | Every 5 minutes |
| P2 | Verify Prometheus alerts loading | `curl /api/v1/rules \| grep m10` |
| P3 | Set up Redis Sentinel for HA | Optional for production |
| P3 | Add dead-letter alerting | Alert when DL count > 10 |

---

---

## Phase 4: Production Hardening (2025-12-09)

### Overview

Phase 4 addresses critical production risks identified in code review:
- Dead-letter reconciliation for XADD/XACK failure window
- Idempotent replay to prevent poison message reintroduction
- Exponential backoff for reclaims to prevent thundering herd
- Worker exactly-once execution guard
- Operational automation (matview refresh, DL reconcile)
- Redis durable configuration template
- Comprehensive chaos/load tests

### Key Issues Addressed

| Risk | Resolution |
|------|------------|
| XADD/XACK non-atomic failure window | DL reconciliation script cleans orphaned pending entries |
| Dead-letter replay idempotence | Redis SET tracking + DB executed_at check |
| Reclaim thundering herd | Exponential backoff per-message (1m, 2m, 4m... up to 24h) |
| Worker duplicate execution | Atomic `UPDATE ... WHERE executed_at IS NULL RETURNING` guard |
| Redis persistence not enforced | Durable config template with AOF + noeviction |
| Missing operational automation | Systemd timers for matview refresh and DL reconcile |

### Dead-Letter Reconciliation

**File**: `scripts/ops/reconcile_dl.py`

Periodic job that finds messages in both dead-letter AND still pending in main stream, resolving by XACKing the original (preferring DL state).

```bash
# One-time run
python -m scripts.ops.reconcile_dl

# Dry-run mode
python -m scripts.ops.reconcile_dl --dry-run

# As systemd timer (every 10 minutes)
systemctl enable m10-dl-reconcile.timer
```

### Idempotent Replay

**File**: `app/tasks/recovery_queue_stream.py` (updated)

`replay_dead_letter()` now includes:
1. Redis SET membership check (`m10:replay:processed`)
2. DB `executed_at IS NOT NULL` check
3. Replay metadata tracking (`replayed_from_dl`, `replayed_at`)

```python
# Idempotent replay - won't reprocess already-handled messages
new_id = await replay_dead_letter(
    msg_id,
    check_idempotency=True,      # Check Redis SET
    check_db_processed=True,      # Check DB executed_at
)

# Bulk replay all DL messages
results = await replay_all_dead_letters(max_replays=1000)
# Returns: {"replayed": N, "skipped": M, "errors": K}
```

### Exponential Backoff for Reclaims

**File**: `app/tasks/recovery_queue_stream.py` (updated)

Per-message reclaim attempts tracked in Redis HASH, with exponential backoff:

| Attempt | Backoff |
|---------|---------|
| 1 | 1 minute |
| 2 | 2 minutes |
| 3 | 4 minutes |
| 4 | 8 minutes |
| 5 | 16 minutes |
| ... | ... |
| Max | 24 hours |

```python
# New functions
attempts = await get_reclaim_attempts(msg_id)
backoff_ms = calculate_backoff_ms(attempts)  # Exponential
await increment_reclaim_attempts(msg_id)
await clear_reclaim_attempts(msg_id)  # On successful ACK or DL

# process_stalled_with_dead_letter now uses backoff
results = await process_stalled_with_dead_letter(use_exponential_backoff=True)
# Returns: {"reclaimed": N, "dead_lettered": M, "skipped": K, "backoff_deferred": P}
```

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `M10_RECLAIM_ATTEMPTS_KEY` | `m10:reclaim:attempts` | Redis HASH key |
| `M10_RECLAIM_BASE_BACKOFF_MS` | `60000` | Base backoff (1 min) |
| `M10_RECLAIM_MAX_BACKOFF_MS` | `86400000` | Max backoff (24 hours) |

### Worker Exactly-Once Execution Guard

**File**: `app/worker/recovery_evaluator.py` (updated)

`_auto_execute()` now uses atomic UPDATE guard:

```python
# Before executing ANY side-effects, atomically claim:
claim_result = session.execute(text("""
    UPDATE recovery_candidates
    SET execution_status = 'executing', updated_at = now()
    WHERE id = :id
      AND (executed_at IS NULL OR execution_status = 'pending')
    RETURNING id
"""))

if not claim_result.fetchone():
    # Another worker already claimed - skip
    return False, {"skipped": True, "reason": "already_executed"}

# Only now execute side-effects...
```

### Matview Refresh Automation

**File**: `scripts/ops/refresh_matview.py`

```bash
# One-time refresh
python -m scripts.ops.refresh_matview

# Status check
python -m scripts.ops.refresh_matview --status

# As systemd timer (every 5 minutes)
systemctl enable m10-matview-refresh.timer
```

### Systemd Units

**Files**: `deployment/systemd/m10-*.{service,timer}`

| Unit | Schedule | Purpose |
|------|----------|---------|
| `m10-matview-refresh.timer` | Every 5 minutes | Refresh mv_top_pending |
| `m10-dl-reconcile.timer` | Every 10 minutes | Reconcile DL duplicates |

```bash
# Deploy
sudo cp deployment/systemd/m10-*.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable m10-matview-refresh.timer m10-dl-reconcile.timer
sudo systemctl start m10-matview-refresh.timer m10-dl-reconcile.timer
```

### Redis Durable Configuration

**File**: `deployment/redis/redis-m10-durable.conf`

Mandatory production settings:
```conf
# PERSISTENCE - REQUIRED
appendonly yes
appendfsync everysec
save 900 1
save 300 10

# MEMORY - CRITICAL
maxmemory 2gb
maxmemory-policy noeviction  # MUST be noeviction for Streams
```

### Chaos/Load Tests

**File**: `tests/test_m10_recovery_chaos.py`

| Test Class | Coverage |
|------------|----------|
| `TestConcurrentUpsert` | 100 concurrent upserts verify occurrence_count == 100 |
| `TestDeadLetterReplayIdempotence` | Replay same message twice is idempotent |
| `TestExponentialBackoff` | Backoff calculations and tracking |
| `TestRedisFailoverToDb` | DB fallback when Redis unavailable |
| `TestWorkerExecutionGuard` | Only one concurrent execution succeeds |
| `TestHighVolumeIngest` | 1000 concurrent ingests (load test) |
| `TestMetricsCollection` | Dead-letter metrics update |

```bash
# Run chaos tests
pytest tests/test_m10_recovery_chaos.py -v --timeout=120

# Run with coverage
pytest tests/test_m10_recovery_chaos.py -v --cov=app.tasks.recovery_queue_stream
```

---

## Phase 4 Files Created

| File | Purpose |
|------|---------|
| `scripts/ops/reconcile_dl.py` | Dead-letter reconciliation job |
| `scripts/ops/refresh_matview.py` | Matview refresh automation |
| `deployment/systemd/m10-matview-refresh.{service,timer}` | Systemd units |
| `deployment/systemd/m10-dl-reconcile.{service,timer}` | Systemd units |
| `deployment/redis/redis-m10-durable.conf` | Redis production config |
| `tests/test_m10_recovery_chaos.py` | Chaos and load tests |

## Phase 4 Files Modified

| File | Changes |
|------|---------|
| `app/tasks/recovery_queue_stream.py` | Exponential backoff, idempotent replay, reclaim tracking |
| `app/worker/recovery_evaluator.py` | Exactly-once execution guard |

---

## Production Deployment Checklist

### Pre-Deployment

- [ ] Apply Redis durable config (`redis-m10-durable.conf`)
- [ ] Verify AOF enabled: `redis-cli CONFIG GET appendonly`
- [ ] Verify noeviction: `redis-cli CONFIG GET maxmemory-policy`
- [ ] Run migration: `alembic upgrade head`

### Deployment

- [ ] Deploy updated code
- [ ] Install systemd units
- [ ] Enable and start timers
- [ ] Verify metrics collection

### Post-Deployment

- [ ] Run chaos tests in staging
- [ ] Verify DL reconciliation runs
- [ ] Verify matview refresh runs
- [ ] Check Grafana dashboard
- [ ] Verify alerts loading in Prometheus

### Verification Commands

```bash
# Check Redis persistence
redis-cli CONFIG GET appendonly
redis-cli CONFIG GET maxmemory-policy

# Check stream health
redis-cli XINFO STREAM m10:evaluate:stream
redis-cli XLEN m10:evaluate:dead-letter

# Check reclaim attempts
redis-cli HGETALL m10:reclaim:attempts

# Check replay tracking
redis-cli SMEMBERS m10:replay:processed

# Check systemd timers
systemctl list-timers | grep m10

# Check matview freshness
psql -c "SELECT * FROM m10_recovery.matview_freshness"
```

---

---

## Phase 5: Leader Election & DB-Backed Idempotency (2025-12-09)

### Overview

Phase 5 addresses final production hardening concerns:
- Distributed leader election for reconcile and matview refresh jobs
- DB-backed replay idempotency (survives Redis restarts)
- Dead-letter archival before trimming
- Auto-GC for reclaim attempts HASH
- Redis config enforcement check for CI/IaC

### Migration 022: Production Hardening

**File**: `alembic/versions/022_m10_production_hardening.py`

**New Tables:**

| Table | Purpose |
|-------|---------|
| `m10_recovery.distributed_locks` | Distributed lock storage for leader election |
| `m10_recovery.replay_log` | Durable replay tracking (survives Redis restarts) |
| `m10_recovery.dead_letter_archive` | Archive DL messages before trimming |
| `m10_recovery.outbox` | Transactional outbox for external side-effects |

**New Functions:**

| Function | Purpose |
|----------|---------|
| `acquire_lock(lock_name, holder_id, ttl)` | Acquire distributed lock with TTL |
| `release_lock(lock_name, holder_id)` | Release lock (only holder can release) |
| `extend_lock(lock_name, holder_id, ttl)` | Extend lock TTL |
| `record_replay(original_msg_id, ...)` | Record replay with ON CONFLICT idempotency |
| `archive_dead_letter(...)` | Archive DL message to DB |
| `publish_outbox(...)` | Publish event to transactional outbox |
| `claim_outbox_events(...)` | Claim batch with FOR UPDATE SKIP LOCKED |
| `complete_outbox_event(...)` | Mark event processed or schedule retry |
| `cleanup_expired_locks()` | Remove expired locks |

### Leader Election

**Files Updated:**
- `scripts/ops/reconcile_dl.py` - Uses `acquire_lock`/`release_lock`
- `scripts/ops/refresh_matview.py` - Per-view locking

**Lock Pattern:**
```python
# Reconcile job
LOCK_NAME = "m10:reconcile_dl"
HOLDER_ID = f"{hostname}:{pid}:{uuid}"

if acquire_lock():
    try:
        await reconcile_once()
    finally:
        release_lock()
else:
    # Another instance running - exit gracefully
    return
```

**CLI Flags:**
```bash
# Skip leader election for debugging
python -m scripts.ops.reconcile_dl --skip-leader-election
python -m scripts.ops.refresh_matview --skip-leader-election
```

### DB-Backed Replay Idempotency

**File**: `app/tasks/recovery_queue_stream.py` (updated)

`replay_dead_letter()` now uses DB-backed idempotency:

```python
# Idempotency check order:
# 1. Check replay_log table (durable)
# 2. Check Redis SET (fast cache, not durable)
# 3. Check recovery_candidates.executed_at

new_id = await replay_dead_letter(
    msg_id,
    check_idempotency=True,
    check_db_processed=True,
    use_db_idempotency=True,  # NEW: DB-backed
)
```

**Why DB-backed?**
- Redis SET is lost on restart
- Redis persistence may lag behind writes
- DB provides ACID guarantees
- `ON CONFLICT DO NOTHING` prevents race conditions

### Dead-Letter Archival

**File**: `app/tasks/recovery_queue_stream.py` (updated)

New functions for safe DL trimming:

```python
# Archive single message to DB
archive_id = await archive_dead_letter_to_db(dl_msg_id, fields)

# Archive + trim (safe trim workflow)
results = await archive_and_trim_dead_letter(max_len=10000)
# Returns: {"archived": N, "trimmed": M, "errors": K}
```

**Workflow:**
1. Read oldest DL entries that will be trimmed
2. Archive each to `dead_letter_archive` table
3. Only XDEL entries that were successfully archived
4. Never lose DL messages on trim

### Reclaim Attempts Auto-GC

**File**: `app/tasks/recovery_queue_stream.py` (updated)

```python
# Garbage collect stale reclaim attempt entries
results = await gc_reclaim_attempts(max_entries_to_check=1000)
# Returns: {"checked": N, "cleaned": M}
```

**Purpose:**
- Reclaim attempts HASH can grow unbounded
- Entries for messages that were ACKed (not reclaimed) accumulate
- GC removes entries not in pending list

### Redis Config Enforcement

**File**: `scripts/ops/check_redis_config.py`

```bash
# Basic check
python -m scripts.ops.check_redis_config

# Strict mode (fail on warnings too)
python -m scripts.ops.check_redis_config --strict

# JSON output for CI
python -m scripts.ops.check_redis_config --json
```

**Required Settings:**
- `appendonly = yes`
- `maxmemory-policy = noeviction`

**Recommended Settings:**
- `appendfsync = everysec` or `always`
- `maxmemory` set to non-zero value

**Exit Codes:**
- 0: All required settings OK
- 1: Required settings missing/incorrect
- 2: Connection error

### Leader Election Tests

**File**: `tests/test_m10_leader_election.py`

| Test Class | Coverage |
|------------|----------|
| `TestDistributedLocks` | acquire/release/extend/conflict/expired |
| `TestReplayLog` | record_replay idempotency |
| `TestDeadLetterArchive` | archive + idempotency |
| `TestReconcileLeaderElection` | Script uses lock functions |
| `TestReclaimAttemptsGC` | GC cleans stale entries |
| `TestRedisConfigCheck` | Script checks required config |

```bash
# Run leader election tests
PYTHONPATH=. pytest tests/test_m10_leader_election.py -v
```

---

## Phase 5 Issues, Decisions & Fixes

### Issues Faced

| Issue | Description | Resolution |
|-------|-------------|------------|
| Reconcile job race condition | Multiple instances could run reconcile_dl.py simultaneously | Added distributed lock via `acquire_lock()` |
| Replay idempotency not durable | Redis SET lost on restart | Added DB-backed `replay_log` table |
| DL data loss on trim | XTRIM could remove DL messages before investigation | Added `archive_dead_letter_to_db()` |
| Reclaim attempts HASH growth | HASH grows unbounded for normally ACKed messages | Added `gc_reclaim_attempts()` |
| Redis config not enforced | Production Redis could run without AOF/noeviction | Created `check_redis_config.py` |
| Matview refresh contention | Multiple instances could refresh same view | Added per-view locking |

### Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Lock storage | PostgreSQL (not Redis) | Survives Redis restarts, ACID guarantees |
| Lock TTL default | 600s (reconcile), 300s (matview) | Long enough for jobs, short enough for failover |
| Holder ID format | `{hostname}:{pid}:{uuid8}` | Unique per process, debuggable |
| Replay idempotency order | DB check first, Redis second | DB is source of truth |
| DL archival trigger | Before trim (not periodic) | Guarantees no data loss |
| GC scope | Only entries not in pending | Safe - won't remove active tracking |
| Config check exit codes | 0=OK, 1=required missing | Standard CI convention |

### Fixes & Workarounds

| Fix | Description |
|-----|-------------|
| Lock conflict handling | `acquire_lock()` returns false immediately if held (no blocking) |
| Expired lock cleanup | Auto-cleanup on acquire via `cleanup_expired_locks()` |
| Same holder reacquire | Same holder can extend their own lock |
| Wrong holder release | `release_lock()` only succeeds if caller is holder |
| Replay race condition | `INSERT ON CONFLICT DO NOTHING` + `SELECT` pattern |
| DL archive idempotency | `ON CONFLICT DO NOTHING` - safe to call multiple times |

### Pending To-Dos (Phase 5)

| Priority | Task | Notes |
|----------|------|-------|
| P1 | Run migration 022 on production | `alembic upgrade 022_m10_production_hardening` |
| P1 | Add Redis config check to CI | `python -m scripts.ops.check_redis_config --strict` |
| P1 | Verify leader election in staging | Run two jobs simultaneously |
| P2 | Add outbox processor worker | Tables created, no worker yet |
| P2 | Add DL archive retention policy | Archive table will grow |
| P2 | Add replay_log retention policy | replay_log will grow |
| P3 | Add Prometheus metrics for locks | `m10_lock_acquired_total` |
| P3 | Integrate GC into systemd timer | Periodic cleanup |

---

## Phase 5 Files Created

| File | Purpose |
|------|---------|
| `alembic/versions/022_m10_production_hardening.py` | Migration: locks, replay_log, DL archive, outbox |
| `scripts/ops/check_redis_config.py` | Redis config enforcement check |
| `tests/test_m10_leader_election.py` | Leader election and Phase 5 tests |

## Phase 5 Files Modified

| File | Changes |
|------|---------|
| `scripts/ops/reconcile_dl.py` | Added leader election with acquire_lock/release_lock |
| `scripts/ops/refresh_matview.py` | Added per-view leader election |
| `app/tasks/recovery_queue_stream.py` | DB-backed replay idempotency, DL archival, GC |

---

## Production Deployment Checklist (Phase 5)

### Pre-Deployment

- [ ] Run migration: `alembic upgrade 022_m10_production_hardening`
- [ ] Run Redis config check: `python -m scripts.ops.check_redis_config --strict`
- [ ] Verify all tests pass: `pytest tests/test_m10_leader_election.py -v`

### Deployment

- [ ] Deploy updated scripts (reconcile_dl.py, refresh_matview.py)
- [ ] Deploy updated recovery_queue_stream.py
- [ ] Add config check to CI pipeline

### Post-Deployment

- [ ] Verify locks work: Run two reconcile jobs simultaneously
- [ ] Verify replay idempotency: Replay same message twice
- [ ] Test DL archival: Archive + trim, verify DB records
- [ ] Test GC: Run gc_reclaim_attempts, check cleaned count

### Verification Commands

```bash
# Check distributed locks
psql -c "SELECT * FROM m10_recovery.distributed_locks"

# Check replay log
psql -c "SELECT * FROM m10_recovery.replay_log ORDER BY replayed_at DESC LIMIT 10"

# Check DL archive
psql -c "SELECT COUNT(*) FROM m10_recovery.dead_letter_archive"

# Check outbox
psql -c "SELECT COUNT(*), processed_at IS NULL AS pending FROM m10_recovery.outbox GROUP BY 2"

# Run Redis config check
python -m scripts.ops.check_redis_config

# Test leader election
python -m scripts.ops.reconcile_dl --json
# Run second instance - should report "skipped"
```

---

---

## Phase 6: Operational Automation & Testing (2025-12-09)

### Overview

Phase 6 completes production readiness with:
- Outbox processor worker for exactly-once external side-effects
- Retention cleanup jobs for archive, replay_log, outbox tables
- Additional Prometheus metrics for locks, archive, outbox
- Grafana dashboard enhancements
- Systemd timers for all automation jobs
- Comprehensive chaos and scale tests
- Migration deployment runbook

### Outbox Processor Worker

**File**: `app/worker/outbox_processor.py`

Transactional outbox pattern for exactly-once external HTTP calls:

**Features:**
- Leader election via distributed locks
- `FOR UPDATE SKIP LOCKED` for concurrent-safe claiming
- Idempotent HTTP calls with `Idempotency-Key` header
- Exponential backoff on failures
- Dead-letter after max retries

**Event Types:**
- `http:*` - HTTP calls with idempotency key
- `webhook:*` - Webhook delivery
- `notify:*` - Notifications (log, Slack)

**Usage:**
```bash
# Run as worker (continuous)
python -m app.worker.outbox_processor

# One-time processing
python -m app.worker.outbox_processor --once

# With custom batch size
python -m app.worker.outbox_processor --batch-size 50
```

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `OUTBOX_BATCH_SIZE` | 20 | Events per batch |
| `OUTBOX_POLL_INTERVAL` | 5 | Seconds between polls |
| `OUTBOX_MAX_RETRIES` | 5 | Max retries before DL |
| `OUTBOX_LOCK_TTL` | 300 | Lock TTL in seconds |

### Retention Cleanup Jobs

**File**: `scripts/ops/m10_retention_cleanup.py`

Periodic cleanup for all Phase 5/6 tables:

| Table | Default Retention | Purpose |
|-------|-------------------|---------|
| `dead_letter_archive` | 90 days | DL investigation |
| `replay_log` | 30 days | Replay audit trail |
| `outbox` | 7 days | Processed events |
| `distributed_locks` | expired only | Stale locks |

**Features:**
- Leader election (only one instance runs)
- Batched deletion (1000 rows at a time to avoid long locks)
- Dry-run mode for testing
- JSON output for logging

**Usage:**
```bash
# Dry run
python -m scripts.ops.m10_retention_cleanup --dry-run

# Run cleanup
python -m scripts.ops.m10_retention_cleanup

# Custom retention
python -m scripts.ops.m10_retention_cleanup --dl-archive-days 180 --replay-days 60

# JSON output
python -m scripts.ops.m10_retention_cleanup --json
```

### Prometheus Metrics (Phase 6)

**File**: `app/metrics.py`

New metrics added:

**Distributed Locks:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `m10_lock_acquired_total` | Counter | lock_name | Lock acquisitions |
| `m10_lock_failed_total` | Counter | lock_name | Lock failures (contention) |
| `m10_lock_released_total` | Counter | lock_name | Lock releases |
| `m10_lock_duration_seconds` | Histogram | lock_name | Lock hold duration |
| `m10_lock_active` | Gauge | lock_name | Currently held locks |

**Dead-Letter Archive:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `m10_archive_total` | Counter | source | Messages archived |
| `m10_archive_size` | Gauge | - | Archive table rows |
| `m10_archive_retention_deleted_total` | Counter | - | Rows deleted by retention |

**Replay Log:**
| Metric | Type | Description |
|--------|------|-------------|
| `m10_replay_log_size` | Gauge | Replay log rows |
| `m10_replay_log_retention_deleted_total` | Counter | Rows deleted by retention |

**Outbox:**
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `m10_outbox_published_total` | Counter | aggregate_type, event_type | Events published |
| `m10_outbox_processed_total` | Counter | aggregate_type, event_type | Events processed |
| `m10_outbox_failed_total` | Counter | aggregate_type, event_type | Events failed |
| `m10_outbox_pending` | Gauge | - | Pending events |
| `m10_outbox_processing_seconds` | Histogram | event_type | Processing duration |
| `m10_outbox_lag_seconds` | Gauge | - | Oldest pending event age |
| `m10_outbox_retry_count` | Histogram | - | Retries before success |

**Reclaim GC:**
| Metric | Type | Description |
|--------|------|-------------|
| `m10_reclaim_gc_cleaned_total` | Counter | Stale entries cleaned |
| `m10_reclaim_gc_checked_total` | Counter | Entries checked |

### Grafana Dashboard Enhancements

**File**: `monitoring/grafana/provisioning/dashboards/files/m10_recovery_dashboard.json`

New dashboard sections:

**Distributed Locks Row:**
- Lock Acquisitions/sec (by lock_name)
- Lock Failures (contention)
- Lock Hold Duration (p95)
- Active Locks (stat)

**Outbox Row:**
- Outbox Pending (stat)
- Outbox Lag (stat)
- Outbox Published/sec (by event_type)
- Outbox Processed/sec (success vs failed)
- Outbox Processing Latency (p50/p95)

**Archive & Retention Row:**
- DL Archive Size (stat)
- Replay Log Size (stat)
- Archive Rate by Source
- Retention Cleanup (hourly bar chart)

### Systemd Timers

**Files**: `deployment/systemd/m10-*.{service,timer}`

New timers:

| Timer | Schedule | Purpose |
|-------|----------|---------|
| `m10-outbox-processor.timer` | Every 30s | Process outbox events |
| `m10-retention-cleanup.timer` | Weekly (Sun 3am) | Cleanup old rows |
| `m10-reclaim-gc.timer` | Hourly | GC stale reclaim entries |

**Deployment:**
```bash
# Copy service files
sudo cp /root/agenticverz2.0/deployment/systemd/m10-*.{service,timer} /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable timers
sudo systemctl enable m10-outbox-processor.timer
sudo systemctl enable m10-dl-reconcile.timer
sudo systemctl enable m10-matview-refresh.timer
sudo systemctl enable m10-retention-cleanup.timer
sudo systemctl enable m10-reclaim-gc.timer

# Start timers
sudo systemctl start m10-outbox-processor.timer
sudo systemctl start m10-dl-reconcile.timer
sudo systemctl start m10-matview-refresh.timer
sudo systemctl start m10-retention-cleanup.timer
sudo systemctl start m10-reclaim-gc.timer

# Verify timers
systemctl list-timers | grep m10
```

### Chaos & Scale Tests

**File**: `tests/test_m10_production_hardening.py`

| Test Class | Coverage |
|------------|----------|
| `TestLeaderElectionChaos` | Single lock, concurrent acquisition, expiry takeover, lock extension |
| `TestOutboxE2E` | Publish/claim/complete, retry on failure, processor integration |
| `TestArchiveAndTrimSafety` | Archive preserves content |
| `TestReplayLogDurability` | Replay idempotency |
| `TestRetentionGC` | Dry-run mode, expired locks cleanup |
| `TestScaleConcurrency` | High-volume outbox (100 events), concurrent lock operations |

**Run Tests:**
```bash
# Run all Phase 6 tests
DATABASE_URL="$DATABASE_URL" PYTHONPATH=. pytest tests/test_m10_production_hardening.py -v

# Run specific test class
pytest tests/test_m10_production_hardening.py::TestLeaderElectionChaos -v

# Run with timeout
pytest tests/test_m10_production_hardening.py -v --timeout=120
```

### Migration Deployment Runbook

**File**: `docs/runbooks/M10_MIGRATION_022_RUNBOOK.md`

Comprehensive runbook covering:
- Pre-migration checklist (environment, backup, Redis config)
- Step-by-step staging deployment
- Step-by-step production deployment
- Post-migration verification
- Rollback procedures
- Troubleshooting guide
- Systemd timer setup

---

## Phase 6 Files Created

| File | Purpose |
|------|---------|
| `app/worker/outbox_processor.py` | Transactional outbox processor worker |
| `scripts/ops/m10_retention_cleanup.py` | Retention cleanup for all Phase 5/6 tables |
| `deployment/systemd/m10-outbox-processor.{service,timer}` | Outbox processor automation |
| `deployment/systemd/m10-retention-cleanup.{service,timer}` | Retention cleanup automation |
| `deployment/systemd/m10-reclaim-gc.{service,timer}` | Reclaim GC automation |
| `tests/test_m10_production_hardening.py` | Chaos and scale tests |
| `docs/runbooks/M10_MIGRATION_022_RUNBOOK.md` | Migration deployment runbook |

## Phase 6 Files Modified

| File | Changes |
|------|---------|
| `app/metrics.py` | Added 20+ new metrics for locks, archive, outbox, GC |
| `monitoring/grafana/provisioning/dashboards/files/m10_recovery_dashboard.json` | Added Lock, Outbox, Archive rows |

---

## Production Deployment Checklist (Phase 6)

### Pre-Deployment

- [ ] Review migration runbook: `docs/runbooks/M10_MIGRATION_022_RUNBOOK.md`
- [ ] Create database backup
- [ ] Run Redis config check: `python -m scripts.ops.check_redis_config --strict`
- [ ] Apply to staging first

### Migration

- [ ] Run migration: `alembic upgrade 022_m10_production_hardening`
- [ ] Verify tables created (4 tables, 9 functions)
- [ ] Run post-migration verification tests from runbook

### Deployment

- [ ] Deploy outbox processor worker
- [ ] Deploy retention cleanup script
- [ ] Install systemd timers
- [ ] Enable and start all timers

### Post-Deployment

- [ ] Verify metrics appearing: `curl /metrics | grep m10_lock`
- [ ] Verify Grafana dashboard panels
- [ ] Run chaos tests in staging
- [ ] Monitor first retention cleanup run (Sunday 3am)

### Verification Commands

```bash
# Check outbox
psql -c "SELECT COUNT(*), processed_at IS NULL AS pending FROM m10_recovery.outbox GROUP BY 2"

# Check archive size
psql -c "SELECT COUNT(*) FROM m10_recovery.dead_letter_archive"

# Check replay log
psql -c "SELECT COUNT(*) FROM m10_recovery.replay_log"

# Check active locks
psql -c "SELECT * FROM m10_recovery.distributed_locks WHERE expires_at > now()"

# Check timers
systemctl list-timers | grep m10

# Test outbox processor
python -m app.worker.outbox_processor --once

# Test retention cleanup dry-run
python -m scripts.ops.m10_retention_cleanup --dry-run --json
```

---

## References

- PIN-050: M10 Recovery Suggestion Engine - Complete (base implementation)
- PIN-055: M11 Store Factories & LLM Adapter Implementation
- PIN-056: M11 Production Hardening
- Runbook: `docs/runbooks/M10_RECOVERY_OPERATIONS.md`
- Migration Runbook: `docs/runbooks/M10_MIGRATION_022_RUNBOOK.md`
- Grafana Dashboard: `monitoring/grafana/provisioning/dashboards/files/m10_recovery_dashboard.json`
- Alert Rules: `monitoring/rules/m10_recovery_alerts.yml`
- Redis Config: `deployment/redis/redis-m10-durable.conf`
- Chaos Tests: `tests/test_m10_recovery_chaos.py`
- Leader Election Tests: `tests/test_m10_leader_election.py`
- Production Hardening Tests: `tests/test_m10_production_hardening.py`
