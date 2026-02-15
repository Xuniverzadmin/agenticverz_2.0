# HANDOVER_BATCH_02_LOGS_ACTIVITY — Implemented

**Date:** 2026-02-11
**Handover Source:** `HANDOVER_BATCH_02_LOGS_ACTIVITY.md`
**Status:** COMPLETE — all exit criteria met

---

## 1. Activity Feedback Lifecycle (End-to-End)

### L6 Driver: `signal_feedback_driver.py` (CREATED)

**File:** `app/hoc/cus/activity/L6_drivers/signal_feedback_driver.py`

New L6 driver for signal_feedback table persistence. Methods:

| Method | Purpose |
|--------|---------|
| `insert_feedback` | INSERT with RETURNING, supports all feedback states + bulk fields |
| `query_feedback` | Most recent feedback for signal (tenant-scoped) |
| `update_feedback_state` | State transition UPDATE |
| `list_active_suppressions` | Active (non-expired) suppressions for tenant |
| `count_expired` | Count expired suppressions for audit |
| `mark_expired_as_evaluated` | Batch UPDATE expired → EVALUATED |

Uses raw SQL `text()` from sqlalchemy, AsyncSession. L6 invariant: never commit/rollback.

### L5 Engine: `signal_feedback_engine.py` (REWRITTEN)

**File:** `app/hoc/cus/activity/L5_engines/signal_feedback_engine.py`

Replaced stub implementation with L6-wired engine:

| Method | Session | Driver Call |
|--------|---------|------------|
| `acknowledge_signal` | async, session first | `_driver.insert_feedback(ACKNOWLEDGED)` |
| `suppress_signal` | async, session first | `_driver.insert_feedback(SUPPRESSED)` with TTL |
| `reopen_signal` | async, session first | `_driver.insert_feedback(REOPENED)` |
| `get_signal_feedback_status` | async, read-only | `_driver.query_feedback` |
| `get_bulk_signal_feedback` | async, read-only | N× `_driver.query_feedback` |
| `evaluate_expired` | async, batch | `_driver.mark_expired_as_evaluated` |

Bulk feedback: accepts `bulk_action_id`, `target_set_hash`, `target_count` per UC-MON spec.

### L4 Handler: `activity_handler.py` (UPDATED)

**File:** `app/hoc/cus/hoc_spine/orchestrator/handlers/activity_handler.py`

Expanded `ActivitySignalFeedbackHandler` from 1 method to 6 methods:

| L4 Method | Transaction | L5 Call |
|-----------|-------------|---------|
| `acknowledge` | `async with ctx.session.begin()` | `service.acknowledge_signal` |
| `suppress` | `async with ctx.session.begin()` | `service.suppress_signal` |
| `reopen` | `async with ctx.session.begin()` | `service.reopen_signal` |
| `get_feedback_status` | read-only (no txn) | `service.get_signal_feedback_status` |
| `get_bulk_feedback` | read-only (no txn) | `service.get_bulk_signal_feedback` |
| `evaluate_expired` | `async with ctx.session.begin()` | `service.evaluate_expired` |

---

## 2. Activity Events (Wired)

Added `_emit_feedback_event()` helper with `validate_event_payload` from event schema contract.

### Events Emitted

| Event Type | Trigger | Extension Fields |
|------------|---------|-----------------|
| `activity.SignalAcknowledged` | After acknowledge | `signal_id`, `feedback_state`, `as_of` |
| `activity.SignalSuppressed` | After suppress | `signal_id`, `feedback_state`, `as_of`, `ttl_seconds`, `expires_at` |
| `activity.SignalReopened` | After reopen | `signal_id`, `feedback_state`, `as_of` |
| `activity.SignalFeedbackEvaluated` | After evaluate_expired (count > 0) | `signal_id`, `feedback_state`, `as_of`, `evaluated_count` |

Bulk suppression events include `bulk_action_id`, `target_set_hash`, `target_count` fields.

All events validated against `REQUIRED_EVENT_FIELDS` (9 base fields) before emission.

---

## 3. Logs Replay-Mode Contract

### L5 Schema: `traces_models.py` (UPDATED)

Added 4 replay fields to `TraceRecord`:

```python
replay_mode: str | None = None  # "FULL" or "TRACE_ONLY"
replay_attempt_id: str | None = None
replay_artifact_version: str | None = None
trace_completeness_status: str | None = None
```

Updated `to_dict()` and `from_dict()` for serialization.

### L6 Driver: `pg_store.py` (UPDATED)

Wired 4 replay columns in both trace storage paths:

| Method | Change |
|--------|--------|
| `store_trace()` | Added 4 replay params, INSERT now $1-$25 (was $1-$21), reads from trace dict override |
| `start_trace()` | Added 4 replay params, INSERT now $1-$19 (was $1-$15) |
| `get_trace()` | TraceRecord construction includes `replay_mode`, `replay_attempt_id`, `replay_artifact_version`, `trace_completeness_status` |

### L5 Engine: `trace_api_engine.py` (UPDATED)

`store_trace()` now accepts and forwards:
- `replay_mode` (FULL | TRACE_ONLY)
- `replay_attempt_id`
- `replay_artifact_version`
- `trace_completeness_status`

Return dict includes `replay_mode` for consumer awareness.

---

## 4. as_of Determinism Stable

No regressions. 34/34 deterministic read checks pass:
- 9 endpoints fully wired with `_normalize_as_of`
- TTL fields stable in signal_feedback migration
- Replay fields stable in traces migration

---

## Validation Command Outputs

### Deterministic Read Verifier
```
Total: 34 | PASS: 34 | WARN: 0 | FAIL: 0
```

### Event Contract Verifier
```
Total: 49 | PASS: 49 | FAIL: 0
```

### Storage Contract Verifier
```
Total: 58 | PASS: 58 | FAIL: 0
```

### Aggregator (Strict)
```
Total: 32 | PASS: 32 | WARN: 0 | FAIL: 0
Exit code: 0
```

---

## PASS/WARN/FAIL Matrix

| Verifier | PASS | WARN | FAIL |
|----------|------|------|------|
| Deterministic read | 34 | 0 | 0 |
| Event contract | 49 | 0 | 0 |
| Storage contract | 58 | 0 | 0 |
| Aggregator (strict) | 32 | 0 | 0 |
| **Total** | **173** | **0** | **0** |

---

## Files Modified

| File | Change |
|------|--------|
| `activity/L6_drivers/signal_feedback_driver.py` | CREATED — L6 driver for signal_feedback persistence |
| `activity/L5_engines/signal_feedback_engine.py` | REWRITTEN — L6-wired engine with 6 methods |
| `hoc_spine/orchestrator/handlers/activity_handler.py` | Updated — 6 feedback methods, event emissions, `_emit_feedback_event` helper |
| `logs/L5_schemas/traces_models.py` | Updated — 4 replay fields on TraceRecord, to_dict/from_dict |
| `logs/L6_drivers/pg_store.py` | Updated — replay columns in store_trace, start_trace, get_trace |
| `logs/L5_engines/trace_api_engine.py` | Updated — replay params forwarded in store_trace |
| `scripts/verification/uc_mon_event_contract_check.py` | Updated — activity_handler emitter + L6/L5 replay wiring checks |
| `scripts/verification/uc_mon_storage_contract_check.py` | Updated — replay wiring + feedback driver checks |

## Blockers

None. All exit criteria satisfied.
