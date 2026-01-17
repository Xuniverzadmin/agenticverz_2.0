# Analytics Signal Reconciliation Rules (v1)

**Status:** LOCKED
**Effective:** 2026-01-17
**Reference:** Analytics Domain Declaration v1

This document defines **hard, enforceable signal reconciliation rules** for **Analytics → Statistics → Usage**.
These are **binding rules** the facade must apply. Any deviation is a defect.

---

## 0. Authority Model (Non-Negotiable)

**Facade is the source of truth.**
Signals are **inputs**, never authorities.

> If two signals disagree, the facade resolves.
> If resolution fails, the facade degrades deterministically.

---

## 1. Signal Classes & Semantics

| Signal             | Class       | Semantic Meaning            |
| ------------------ | ----------- | --------------------------- |
| `gateway.metrics`  | ENTRY       | External request accepted   |
| `worker.execution` | EXECUTION   | Backend work actually run   |
| `llm.usage`        | CONSUMPTION | Token & compute consumption |

**Rule:** No signal may report outside its semantic scope.

---

## 2. Canonical Usage Dimensions

All reconciliation produces **exactly three dimensions**:

```
requests
compute_units
tokens
```

No signal may introduce a fourth dimension in v1.

---

## 3. Time Normalization Rules

### 3.1 Clock Authority

* **UTC only**
* Facade truncates timestamps to resolution bucket start

### 3.2 Resolution Alignment

* `hour` → truncate to `YYYY-MM-DDTHH:00:00Z`
* `day` → truncate to `YYYY-MM-DDT00:00:00Z`

**Rule:**
Signals with higher granularity are **downsampled**, never upsampled.

---

## 4. Cardinality & Identity Rules

### 4.1 Request Identity

A **request** is counted **once and only once** if:

```
gateway.metrics.accepted == true
```

* Retries → **NOT new requests**
* Internal fan-out → **NOT new requests**

**Authoritative source:** `gateway.metrics`

---

### 4.2 Compute Units

Compute units are counted when:

```
worker.execution.status == SUCCESS
```

* Partial failures → proportional compute (if reported)
* Retries → count only executed units

**Authoritative source:** `worker.execution`

---

### 4.3 Tokens

Tokens are counted when:

```
llm.usage.finalized == true
```

* Prompt + completion included
* Streaming partials ignored until finalized

**Authoritative source:** `llm.usage`

---

## 5. Cross-Signal Join Rules

### 5.1 Join Key

Signals are correlated using:

```
trace_id (preferred)
request_id (fallback)
```

If **neither exists** → signal is **orphaned**.

---

### 5.2 Orphan Handling

| Signal                    | Action                 |
| ------------------------- | ---------------------- |
| Orphan `gateway.metrics`  | COUNT request          |
| Orphan `worker.execution` | COUNT compute_units    |
| Orphan `llm.usage`        | COUNT tokens           |
| Cross-signal mismatch     | DO NOT fabricate joins |

**Rule:** Orphans are visible but **never merged speculatively**.

---

## 6. Deduplication Rules

### 6.1 Duplicate Detection

Duplicates are detected by:

```
(signal_type, trace_id, bucket_ts)
```

### 6.2 Resolution

* Keep **first finalized** event
* Discard late duplicates

**Rule:** Late data never mutates closed buckets.

---

## 7. Freshness & Staleness Rules

### 7.1 Freshness Clock

```
freshness_sec = now() - newest_signal_ts
```

### 7.2 Degradation Thresholds

| Freshness | Status  |
| --------- | ------- |
| ≤ 60s     | LIVE    |
| 61s–300s  | DELAYED |
| > 300s    | STALE   |

Facade must surface this verbatim.

---

## 8. Conflict Resolution Matrix

| Conflict                       | Resolution                      |
| ------------------------------ | ------------------------------- |
| Requests > executions          | Valid (fast reject / cache hit) |
| Executions > requests          | **INVALID** → log + metric      |
| Tokens > executions            | Valid (batch / async)           |
| Zero requests, non-zero tokens | Valid (background jobs)         |

Facade **never normalizes conflicts away**.

---

## 9. Aggregation Precedence Rules

Aggregation order is **fixed**:

1. Normalize timestamps
2. Deduplicate per signal
3. Aggregate per signal
4. Merge dimensions
5. Compute totals
6. Attach metadata

Changing this order is a breaking change.

---

## 10. Export Consistency Rule

CSV / JSON exports **must be bit-equivalent** to:

```
GET /analytics/statistics/usage
```

No alternate code paths.
No recomputation.

---

## 11. Observability & Enforcement

Facade **must emit**:

* `analytics_orphan_signals_total{signal}`
* `analytics_conflict_total{type}`
* `analytics_freshness_seconds`

Silent reconciliation is forbidden.

---

## 12. Explicit Non-Rules (v1)

The facade **does not**:

* Infer cost
* Infer user intent
* Correct upstream bugs
* Retroactively mutate history

---

## 13. Contract Stability Guarantee

These rules are **frozen for v1**.

Any of the following requires:

* Version bump
* OpenAPI change
* Console notice

Changes requiring versioning:
* New signal
* New dimension
* Changed precedence
* Backfill mutation

---

## Final Truth

This reconciliation model ensures:

* Determinism
* Auditability
* Legal defensibility
* Zero "analytics magic"
