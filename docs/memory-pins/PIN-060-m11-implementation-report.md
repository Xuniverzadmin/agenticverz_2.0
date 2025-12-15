# PIN-060: M11 Skill Expansion Implementation Report

**Created:** 2025-12-09
**Status:** COMPLETE
**Category:** Implementation / Post-Mortem
**Milestone:** M11 Skill Expansion
**Parent PIN:** PIN-059
**Author:** Claude Code

---

## Executive Summary

M11 Skill Expansion has been fully implemented. This PIN documents the implementation journey including issues encountered, architectural decisions made, fixes applied, and lessons learned for future milestones.

**Key Metrics:**
- 43/43 tests passing
- 5 skills implemented
- 15 Prometheus metrics added
- 5 database tables created
- 4 issues resolved

---

## Implementation Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Blueprint Review | - | Analyzed PIN-059, identified existing infrastructure |
| Core Skills | - | kv_store, slack_send, webhook_send, voyage_embed |
| Replay Infrastructure | - | AuditStore, WorkflowRunner, ReplayVerifier |
| Circuit Breaker | - | SkillCircuitBreaker in base.py |
| Prometheus Metrics | - | 15 M11-specific metrics |
| Testing & Fixes | - | 43 tests, SQL fixes, migration chain |

---

## Issues Encountered

### Issue 1: SQL Syntax Error - Parameter Binding Conflict

**Severity:** HIGH (Blocking)

**Symptom:**
```
psycopg2.errors.SyntaxError: syntax error at or near ":"
LINE 7:  :args::jsonb, ...
```

**Root Cause:**
SQLAlchemy's `text()` function uses `:param_name` for parameter binding. PostgreSQL uses `::type` for type casting. When combined (`:args::jsonb`), SQLAlchemy interprets `::jsonb` as a malformed parameter.

**Location:** `backend/tools/replay/audit.py` (3 occurrences)

**Fix Applied:**
```python
# BEFORE (broken)
text("INSERT INTO ... VALUES (:args::jsonb, ...)")
params = {"args": json.dumps(args)}

# AFTER (fixed)
text("INSERT INTO ... VALUES (CAST(:args_json AS jsonb), ...)")
params = {"args_json": json.dumps(args)}
```

**Lesson:** Always use explicit `CAST(x AS type)` syntax instead of `::type` shorthand when using SQLAlchemy's `text()` with named parameters.

---

### Issue 2: Neon Database Endpoint Changed

**Severity:** MEDIUM

**Symptom:**
```
connection refused / authentication failed
```

**Root Cause:**
Neon PostgreSQL endpoint changed from `ep-delicate-field-a1fd7srl` to `ep-long-surf-a1n0hv91` (documented in PIN-058 P5).

**Fix Applied:**
Updated DATABASE_URL in tests to use correct endpoint from `.env`.

**Lesson:** Always source environment variables from `.env` rather than hardcoding connection strings. PIN-058 documented this change but not all code paths were updated.

---

### Issue 3: Test Assertion Logic Error

**Severity:** LOW

**Symptom:**
```
AssertionError: assert 'critical' in '...CRITICAL...'
```

**Root Cause:**
Test checked for lowercase `"critical"` in an already-uppercased string. After `.upper()`, the string contains `"CRITICAL"`, not `"critical"`.

**Location:** `tests/replay/test_replay_end_to_end.py:349`

**Fix Applied:**
```python
# BEFORE
assert "critical" in report.upper()

# AFTER
assert "CRITICAL" in report.upper()
```

**Lesson:** When using case-insensitive comparisons, ensure both sides are normalized consistently.

---

### Issue 4: Migration Chain Gap

**Severity:** MEDIUM

**Symptom:**
```
alembic.util.exc.CommandError: Can't locate revision identified by '023_...'
```

**Root Cause:**
Migration 024 referenced `down_revision = '023_m10_archive_partitioning'`, but migration 023 was DEFERRED per PIN-058 and never applied to production.

**Fix Applied:**
```python
# BEFORE
down_revision = '023_m10_archive_partitioning'

# AFTER
down_revision = '022_m10_production_hardening'
```

**Lesson:** When deferring migrations, ensure subsequent migrations chain to the last *applied* revision, not the last *created* revision.

---

## Architectural Decisions

### Decision 1: Generic Circuit Breaker vs CostSim-Specific

**Context:** CostSim has a DB-backed circuit breaker (`app/costsim/circuit_breaker.py`) with drift detection, alerting, and TTL-based recovery.

**Decision:** Create a simpler `SkillCircuitBreaker` class in `app/skills/base.py`.

**Rationale:**
- CostSim breaker is tightly coupled to drift scoring
- M11 skills need simple failure-count based breaking
- External services (Slack, Voyage) need per-target isolation

**Implementation:**
```python
class SkillCircuitBreaker:
    FAILURE_THRESHOLD = 5
    COOLDOWN_SECONDS = 60

    # States: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
```

---

### Decision 2: Metrics in Base Class

**Context:** Need Prometheus metrics for all M11 skills.

**Decision:** Add metric recording directly in `IdempotentSkill.execute()` and `ExternalSkill.execute()`.

**Rationale:**
- Automatic instrumentation for all skills
- Consistent labeling (skill, status, tenant_id)
- No per-skill boilerplate

**Trade-off:** Less flexibility for custom metrics per skill (acceptable).

---

### Decision 3: CAST() Over :: Syntax

**Context:** Need to insert JSONB data via SQLAlchemy text queries.

**Decision:** Always use `CAST(:param AS jsonb)` instead of `:param::jsonb`.

**Rationale:**
- Avoids SQLAlchemy parameter binding conflicts
- Explicit and readable
- Same pattern used in M10 after similar issues (PIN-058)

---

### Decision 4: Transient Flag for Ops

**Context:** Some workflow operations shouldn't be verified during replay (e.g., logging, metrics).

**Decision:** Add `transient: bool` field to ops table and skip transient ops during replay verification.

**Rationale:**
- Allows mixing deterministic and non-deterministic ops
- Replay verifier focuses on business-critical ops
- Documented intent in audit trail

---

### Decision 5: DB-Backed Circuit Breaker State

**Context:** Circuit breaker state needs to persist across restarts.

**Decision:** Store state in `m11_audit.circuit_breaker_state` table.

**Rationale:**
- Survives container restarts
- Multi-replica safe (no stale in-memory state)
- Queryable for debugging

**Trade-off:** Slightly higher latency than in-memory (acceptable for external calls).

---

### Decision 6: Skip Deferred Migration 023

**Context:** Migration 023 (archive partitioning) was marked DEFERRED in PIN-058.

**Decision:** Chain migration 024 directly to 022, skipping 023.

**Rationale:**
- 023 is premature optimization (<1K rows)
- Applying 023 would add unnecessary complexity
- Can apply 023 later when tables exceed 100K rows

---

## Fixes & Workarounds Summary

### Code Fixes

| File | Change | Lines |
|------|--------|-------|
| `tools/replay/audit.py` | CAST syntax for args | 111 |
| `tools/replay/audit.py` | CAST syntax for result | 158 |
| `tools/replay/audit.py` | CAST syntax for diff | 303 |
| `tools/replay/audit.py` | Renamed params to `*_json` | Multiple |
| `tests/replay/test_replay_end_to_end.py` | Fixed assertion case | 349 |
| `alembic/versions/024_m11_skill_audit.py` | Fixed down_revision | Header |

### Workarounds

| Workaround | Context | Permanent? |
|------------|---------|------------|
| `pytest.mark.skipif(not DATABASE_URL)` | Skip DB tests in CI without DB | Yes - appropriate |
| Fallback to CLOSED state | Circuit breaker graceful degradation | Yes - safe default |
| Graceful metric import | Tests without prometheus | Yes - appropriate |

---

## Test Results

```
======================== 43 passed in 85.53s =========================

tests/skills/test_m11_skills.py (27 tests)
├── TestKVStoreSkill: 6 passed
├── TestSlackSendSkill: 4 passed
├── TestWebhookSendSkill: 5 passed
├── TestVoyageEmbedSkill: 6 passed
├── TestSkillRegistry: 2 passed
└── TestInputSchemas: 4 passed

tests/e2e/test_m11_workflow.py (6 tests)
├── TestM11FiveStepWorkflow: 4 passed
├── TestM11WorkflowWithMockedBackends: 1 passed
└── TestM11WorkflowJSON: 1 passed

tests/replay/test_replay_end_to_end.py (10 tests)
├── TestReplayEndToEnd: 5 passed
├── TestVerifier: 3 passed
└── TestAuditStore: 2 passed
```

---

## Database Schema Created

### Schema: m11_audit

```sql
-- 1. Operations audit log (append-only)
CREATE TABLE m11_audit.ops (
    op_id TEXT PRIMARY KEY,
    workflow_run_id TEXT NOT NULL,
    op_index INTEGER NOT NULL,
    op_type TEXT NOT NULL,
    skill_version TEXT,
    args JSONB NOT NULL,
    args_hash TEXT NOT NULL,
    result JSONB,
    result_hash TEXT,
    status TEXT DEFAULT 'pending',
    error_code TEXT,
    error_message TEXT,
    duration_ms INTEGER,
    transient BOOLEAN DEFAULT FALSE,
    idempotency_key TEXT,
    tenant_id TEXT DEFAULT 'default',
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- 2. Replay verification tracking
CREATE TABLE m11_audit.replay_runs (
    replay_id TEXT PRIMARY KEY,
    workflow_run_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    status TEXT DEFAULT 'running',
    ops_total INTEGER,
    ops_verified INTEGER,
    ops_failed INTEGER,
    ops_skipped INTEGER,
    first_mismatch_op_index INTEGER,
    mismatch_diff JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- 3. Circuit breaker state
CREATE TABLE m11_audit.circuit_breaker_state (
    target TEXT PRIMARY KEY,
    state TEXT DEFAULT 'CLOSED',
    failure_count INTEGER DEFAULT 0,
    last_failure_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    cooldown_until TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Skill metrics aggregation
CREATE TABLE m11_audit.skill_metrics (
    id SERIAL PRIMARY KEY,
    skill_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC,
    labels JSONB,
    recorded_at TIMESTAMPTZ DEFAULT now()
);

-- 5. Workflow summary view
CREATE TABLE m11_audit.workflow_summary (
    workflow_run_id TEXT PRIMARY KEY,
    total_ops INTEGER,
    completed_ops INTEGER,
    failed_ops INTEGER,
    first_op_at TIMESTAMPTZ,
    last_op_at TIMESTAMPTZ,
    total_duration_ms INTEGER
);

-- Function for monotonic op_index
CREATE FUNCTION m11_audit.next_op_index(wf_id TEXT) RETURNS INTEGER AS $$
    SELECT COALESCE(MAX(op_index), 0) + 1
    FROM m11_audit.ops
    WHERE workflow_run_id = wf_id;
$$ LANGUAGE SQL;
```

---

## Prometheus Metrics Added

### Skill Execution Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `m11_skill_executions_total` | Counter | skill, status, tenant_id | Total executions |
| `m11_skill_execution_seconds` | Histogram | skill | Latency distribution |
| `m11_skill_idempotency_hits_total` | Counter | skill | Cache hits |
| `m11_skill_idempotency_conflicts_total` | Counter | skill | Param conflicts |

### Circuit Breaker Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `m11_circuit_breaker_state` | Gauge | target | 0=CLOSED, 1=OPEN, 2=HALF_OPEN |
| `m11_circuit_breaker_failures_total` | Counter | target | Recorded failures |
| `m11_circuit_breaker_successes_total` | Counter | target | Recorded successes |
| `m11_circuit_breaker_opens_total` | Counter | target | Open events |
| `m11_circuit_breaker_closes_total` | Counter | target | Recovery events |
| `m11_circuit_breaker_rejected_total` | Counter | target | Rejected requests |

### Replay Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `m11_audit_ops_total` | Counter | skill, status | Audit log entries |
| `m11_replay_runs_total` | Counter | mode, status | Replay executions |
| `m11_replay_ops_verified_total` | Counter | - | Verified operations |
| `m11_replay_ops_mismatched_total` | Counter | - | Mismatched operations |
| `m11_replay_verification_seconds` | Histogram | - | Verification latency |

---

## Files Created/Modified

### New Files

| File | Purpose |
|------|---------|
| `app/skills/kv_store.py` | Redis KV operations skill |
| `app/skills/slack_send.py` | Slack webhook skill |
| `app/skills/webhook_send.py` | HMAC-signed webhook skill |
| `app/skills/voyage_embed.py` | Voyage AI embeddings skill |
| `app/skills/base.py` | IdempotentSkill, ExternalSkill, SkillCircuitBreaker |
| `app/utils/deterministic.py` | Seeded backoff, idempotency key generation |
| `tools/replay/__init__.py` | Replay module exports |
| `tools/replay/audit.py` | AuditStore class |
| `tools/replay/runner.py` | WorkflowRunner class |
| `tools/replay/verifier.py` | ReplayVerifier class |
| `alembic/versions/024_m11_skill_audit.py` | M11 audit schema migration |
| `tests/skills/test_m11_skills.py` | 27 skill unit tests |
| `tests/e2e/test_m11_workflow.py` | 6 E2E workflow tests |
| `tests/replay/test_replay_end_to_end.py` | 10 replay tests |

### Modified Files

| File | Changes |
|------|---------|
| `app/skills/__init__.py` | Export M11 skills |
| `app/metrics.py` | Add 15 M11 metrics |

---

## Lessons Learned

### For Future Milestones

1. **SQL Syntax:** Use `CAST(x AS type)` not `x::type` with SQLAlchemy text queries
2. **Migration Chains:** Reference last *applied* migration, not last *created*
3. **Endpoint Changes:** Always source connection strings from environment
4. **Test Assertions:** Normalize case consistently when comparing strings
5. **Circuit Breakers:** DB-backed state for multi-replica safety
6. **Base Class Metrics:** Automatic instrumentation reduces boilerplate

### Patterns to Reuse

```python
# Pattern 1: Safe JSONB insertion
CAST(:param_json AS jsonb)

# Pattern 2: Circuit breaker in external skills
class MySkill(ExternalSkill):
    CIRCUIT_BREAKER_TARGET = "my_api"

# Pattern 3: Transient ops for non-critical operations
{"skill": "log", "transient": True}

# Pattern 4: Skip tests without required infrastructure
@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="...")
```

---

## Related PINs

| PIN | Relationship |
|-----|--------------|
| PIN-059 | Parent blueprint (now COMPLETE) |
| PIN-058 | M10 simplification (predecessor, Neon endpoint change) |
| PIN-057 | M10 production hardening (migration 022) |
| PIN-033 | M8-M14 roadmap |
| PIN-005 | Machine-native architecture principles |

---

## Verification Checklist

- [x] All 43 tests passing
- [x] Migration 024 applied to Neon production
- [x] M11 audit tables created (5 tables)
- [x] Circuit breaker wired into ExternalSkill
- [x] Prometheus metrics recording
- [x] PIN-059 marked COMPLETE
- [x] SQL syntax issues resolved
- [x] No hardcoded connection strings

---

## Next Steps (M12+)

1. **OAuth Skills (Deferred):** `outlook_send`, `gmail_send` when needed
2. **KV Load Test:** Create `scripts/m11_kv_load_test.sh`
3. **Integration Smoke Tests:** Real Slack/Email sends in staging
4. **Audit Retention:** Add cleanup job for old ops records
5. **HMAC Key Rotation:** Document rotation procedure

---

## Appendix: Error Messages Reference

### SQL Syntax Error
```
psycopg2.errors.SyntaxError: syntax error at or near ":"
LINE 7:  :args::jsonb, :args_hash, 'pending', ...
         ^
```
**Fix:** Use `CAST(:args_json AS jsonb)`

### Migration Chain Error
```
alembic.util.exc.CommandError: Can't locate revision identified by '023_m10_archive_partitioning'
```
**Fix:** Update `down_revision` to last applied migration

### Neon Auth Error
```
FATAL: password authentication failed for user "neondb_owner"
```
**Fix:** Use correct endpoint from `.env` (ep-long-surf-a1n0hv91)
