# M10 Outbox Contract

**Status:** LOCKED
**Effective:** 2026-01-02
**Reference:** PIN-276 (Contract Authority Enforcement)

---

## Purpose

This document defines the **canonical contracts** for M10 transactional outbox infrastructure.

**Invariant:** These contracts are immutable. Any change requires human approval and a new PIN.

---

## Canonical Function Signatures

### `claim_outbox_events`

```sql
m10_recovery.claim_outbox_events(
    p_processor_id TEXT,
    p_batch_size INTEGER DEFAULT 10
) RETURNS TABLE(
    id BIGINT,
    aggregate_type TEXT,
    aggregate_id TEXT,
    event_type TEXT,
    payload JSONB,
    retry_count INT
)
```

**Parameter order:** `processor_id` FIRST, `batch_size` SECOND.

**Source of truth:** `app/worker/outbox_processor.py` line 187.

---

### `complete_outbox_event`

```sql
m10_recovery.complete_outbox_event(
    p_event_id BIGINT,
    p_processor_id TEXT,
    p_success BOOLEAN,
    p_error TEXT DEFAULT NULL
) RETURNS VOID
```

**Parameter order:** `event_id`, `processor_id`, `success`, `error`.

**Source of truth:** `app/worker/outbox_processor.py` line 356.

---

### `publish_outbox`

```sql
m10_recovery.publish_outbox(
    p_aggregate_type TEXT,
    p_aggregate_id TEXT,
    p_event_type TEXT,
    p_payload JSONB
) RETURNS BIGINT
```

---

## Retry Authority

### Single Field: `process_after`

The **only** field that controls retry scheduling is `process_after`.

| Field | Authority | Mutation Allowed |
|-------|-----------|------------------|
| `process_after` | **AUTHORITATIVE** | YES - controls when event can be claimed |
| `next_retry_at` | DEPRECATED | NO - must not be mutated |

**Backoff formula:**
```sql
process_after = now() + (POWER(2, LEAST(retry_count, 10)) || ' seconds')::INTERVAL
```

This provides exponential backoff capped at ~17 minutes.

---

## Worker Selection Rule

Events are claimed using `FOR UPDATE SKIP LOCKED`:

1. `processed_at IS NULL` - not yet completed
2. `process_after IS NULL OR process_after <= now()` - ready for processing
3. `claimed_at IS NULL OR claimed_at < now() - INTERVAL '5 minutes'` - not stale-claimed

This ensures:
- Non-blocking concurrent claims
- Automatic recovery from crashed workers
- No double-processing

---

## Completion Semantics

### On Success (`p_success = TRUE`)
- Set `processed_at = now()`
- Event is permanently complete

### On Failure (`p_success = FALSE`)
- Increment `retry_count`
- Set `process_after` to future (exponential backoff)
- Clear `claimed_at` and `claimed_by`
- Event becomes eligible for re-claim after backoff

---

## Absolute Rules

### NO OVERLOADS

```
RULE: Each M10 function has exactly ONE signature.

VIOLATION: Creating a second signature for any function.

ENFORCEMENT: Migration 003_m10_canonical_contracts.py verifies
             signature count = 1 for each function.
```

If production and tests disagree on signature:
- **Production wins**
- Tests are fixed
- No "compatibility overloads"

### NO PARALLEL TRUTH

```
RULE: One field controls one semantic.

VIOLATION: Updating both process_after AND next_retry_at.

ENFORCEMENT: complete_outbox_event only updates process_after.
```

### NO TEST-DRIVEN PRODUCTION

```
RULE: Tests conform to contracts. Contracts don't bend to tests.

VIOLATION: Changing function signature to make tests pass.

ENFORCEMENT: decision_guardrails in SESSION_PLAYBOOK v2.32.
```

---

## Schema Reference

### `m10_recovery.outbox` Table

| Column | Type | Purpose |
|--------|------|---------|
| `id` | BIGINT | Primary key |
| `aggregate_type` | TEXT | Event source type |
| `aggregate_id` | TEXT | Event source ID |
| `event_type` | TEXT | Event classification |
| `payload` | JSONB | Event data |
| `created_at` | TIMESTAMPTZ | When published |
| `processed_at` | TIMESTAMPTZ | When completed (NULL if pending) |
| `retry_count` | INTEGER | Failure count |
| `process_after` | TIMESTAMPTZ | **Retry authority** |
| `claimed_at` | TIMESTAMPTZ | When claimed by worker |
| `claimed_by` | TEXT | Worker ID holding claim |

---

## Migration Reference

| Migration | Purpose |
|-----------|---------|
| `002_m10_recovery_outbox.py` | Creates schema and tables |
| `003_m10_canonical_contracts.py` | Canonicalizes function signatures |

---

## Governance

| Change Type | Required |
|-------------|----------|
| New function | Human approval + PIN |
| Signature change | Human approval + PIN |
| New retry field | FORBIDDEN |
| Function overload | FORBIDDEN |

---

## History

| Date | Change | Reference |
|------|--------|-----------|
| 2026-01-02 | Contract canonicalization | PIN-276 REDO |
| 2026-01-02 | Overloads dropped | Migration 003 |
| 2026-01-02 | Single retry authority | `process_after` |

---

**This contract is the source of truth for M10 outbox semantics.**
