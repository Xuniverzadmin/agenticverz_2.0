# Phase-8 — Observability Unification (Design Template v1)

**Status:** DESIGN-ONLY
**Created:** 2026-01-12
**Depends on:** Phases 4–7 (Onboarding, Roles, Billing, Protection)
**Does NOT depend on:** UI, alerts, billing gateways, enforcement
**Primary Consumer:** Humans (debugging), Systems (correlation)
**Reference:** PIN-399

---

## 8.0 Prime Directive

> **Observability answers "what happened?" — never "what should happen?"**

Phase-8:

* records truth
* correlates signals
* preserves causality

It does **not**:

* enforce
* alert
* mutate state
* decide policy

---

## 8.1 Problem Statement (Explicit)

Before Phase-8, the system emits **parallel truths**:

| Source      | Emits                     |
| ----------- | ------------------------- |
| Onboarding  | state transitions         |
| Billing     | state + limits            |
| Protection  | ALLOW / THROTTLE / REJECT |
| Founder ops | force-complete audits     |

These truths are:

* temporally related
* causally related
* tenant-scoped

…but **not queryable as a whole**.

Phase-8 introduces **one correlation surface**.

---

## 8.2 Core Concept: Unified Event

Phase-8 defines a **single canonical event model**.

Everything becomes an event.
Events are **append-only**.
Events are **never mutated**.

---

## 8.3 Unified Event Model (Canonical)

```python
@dataclass(frozen=True)
class UnifiedEvent:
    event_id: str           # UUID
    event_type: str         # e.g., "onboarding_state_transition"
    event_source: str       # "onboarding" | "billing" | "protection" | "founder" | "system"
    tenant_id: str          # Primary query axis
    timestamp: datetime     # UTC, RFC3339
    severity: str           # "INFO" | "WARN" | "ERROR"
    actor: Actor            # Who triggered this
    context: EventContext   # Request/trace correlation
    payload: dict           # Domain-specific details
```

JSON representation:

```json
{
  "event_id": "uuid",
  "event_type": "string",
  "event_source": "onboarding | billing | protection | founder | system",
  "tenant_id": "string",
  "timestamp": "RFC3339",
  "severity": "INFO | WARN | ERROR",
  "actor": {
    "type": "human | machine | system",
    "id": "string | null"
  },
  "context": {
    "request_id": "string | null",
    "trace_id": "string | null"
  },
  "payload": { }
}
```

This schema is **global and frozen**.

---

## 8.4 Event Types (Initial Set)

Phase-8 does **not invent** new facts.
It **normalizes existing ones**.

### Onboarding Events

| Event Type | Payload |
|------------|---------|
| `onboarding_state_transition` | `from_state`, `to_state`, `trigger` |
| `onboarding_force_complete` | `from_state`, `reason`, `justification` |

### Billing Events

| Event Type | Payload |
|------------|---------|
| `billing_state_changed` | `from_state`, `to_state`, `plan_id` |
| `billing_limit_evaluated` | `limit_name`, `current_value`, `allowed_value`, `exceeded` |

### Protection Events

| Event Type | Payload |
|------------|---------|
| `protection_decision` | `decision`, `dimension`, `endpoint`, `retry_after_ms` |
| `protection_anomaly_detected` | `baseline`, `observed`, `window`, `severity` |

### Roles / Auth Events (Read-only)

| Event Type | Payload |
|------------|---------|
| `role_violation` | `required_role`, `actual_role`, `endpoint` |
| `unauthorized_access_attempt` | `reason`, `endpoint`, `method` |

---

## 8.5 Required Dimensions (Hard Constraints)

Every unified event **must include**:

| Field        | Reason             |
| ------------ | ------------------ |
| `event_id`   | Unique identifier  |
| `tenant_id`  | Primary query axis |
| `timestamp`  | Ordering           |
| `event_source` | Phase boundary   |
| `event_type` | Semantics          |
| `severity`   | Filtering          |
| `payload`    | Domain detail      |

If any required field is missing → **event is rejected**.

---

## 8.6 Immutability & Ordering Rules

### OBSERVE-IMMUTABLE-001

Events are append-only. No updates. No deletes.

### OBSERVE-ORDER-001

Event order is defined by `(timestamp, event_id)`.

No assumptions about:

* clock sync
* causal ordering beyond what's explicit

---

## 8.7 Correlation Semantics

Phase-8 supports correlation **without inference**.

### Correlation Keys (Optional but Standardized)

* `request_id` — ties events to a single API request
* `trace_id` — ties events across distributed operations
* `actor.id` — ties events to a user or machine identity

Correlation is:

* opt-in
* best-effort
* never assumed

---

## 8.8 Query Contract (Read-Only)

Phase-8 guarantees the system can answer:

> "What happened to tenant **X** between **T1** and **T2**?"

That's it.
No aggregations.
No rollups.
No alerts.

### Query Interface

```python
class ObservabilityProvider(Protocol):
    def query(
        self,
        tenant_id: str,
        start: datetime,
        end: datetime,
        event_types: Optional[list[str]] = None,
        event_sources: Optional[list[str]] = None,
    ) -> list[UnifiedEvent]:
        ...
```

---

## 8.9 Explicit Non-Goals (Certified)

These are **NOT** part of Phase-8:

❌ Dashboards
❌ Alerting / paging
❌ SLAs / SLOs
❌ Metrics math (aggregations, percentiles)
❌ Anomaly detection logic
❌ UI endpoints
❌ External integrations (Datadog, Splunk, etc.)
❌ Long-term retention policies
❌ Cost optimization

Those are **Phase-9+** concerns.

---

## 8.10 Mock-First Implementation Contract

### Provider Interface

```python
from typing import Protocol, Optional
from datetime import datetime

class ObservabilityProvider(Protocol):
    def emit(self, event: UnifiedEvent) -> None:
        """
        Emit an event to the observability store.

        MUST NOT block execution on failure.
        MUST NOT raise exceptions to caller.
        """
        ...

    def query(
        self,
        tenant_id: str,
        start: datetime,
        end: datetime,
        event_types: Optional[list[str]] = None,
        event_sources: Optional[list[str]] = None,
    ) -> list[UnifiedEvent]:
        """
        Query events for a tenant within a time range.

        Returns events ordered by (timestamp, event_id).
        """
        ...
```

### Mock Provider Requirements

* In-memory store
* Deterministic ordering
* No external dependencies
* No async background jobs
* Thread-safe for concurrent emit

Mock **must satisfy the same interface** as real provider (OBSERVE-005).

---

## 8.11 Integration Rules (Critical)

Other systems:

* **emit** events via the provider
* never query during request handling
* never depend on query latency

Observability is **write-through**, never blocking.

### Emit Pattern

```python
from app.observability import get_observability_provider, emit_event

# In billing state change:
emit_event(
    event_type="billing_state_changed",
    event_source="billing",
    tenant_id=tenant_id,
    severity="INFO",
    payload={
        "from_state": old_state.value,
        "to_state": new_state.value,
        "plan_id": plan.id,
    },
)
```

---

## 8.12 Failure Semantics

If observability fails:

* main operation proceeds
* error is logged locally (stderr)
* no retry storms
* no cascading failure

Truth loss is acceptable; system outage is not.

### Error Handling Contract

```python
def emit(self, event: UnifiedEvent) -> None:
    try:
        self._store.append(event)
    except Exception as e:
        # Log locally, never propagate
        logger.error(f"Observability emit failed: {e}")
        # Operation continues - OBSERVE-004
```

---

## 8.13 Phase-8 Invariants (LOCKED)

### OBSERVE-001

> Observability never mutates system state.

Emit is read-from-source, write-to-log. No callbacks. No triggers.

### OBSERVE-002

> Events are immutable once accepted.

No update operations. No delete operations. Append-only.

### OBSERVE-003

> All events are tenant-scoped.

Every event MUST have a tenant_id. System events use a sentinel tenant.

### OBSERVE-004

> Failure to emit must not block execution.

Main operations always complete. Observability is best-effort.

### OBSERVE-005

> Mock provider must be interface-compatible with real provider.

Zero refactor when real storage (Postgres, ClickHouse, etc.) is added.

---

## 8.14 Actor Model

```python
@dataclass(frozen=True)
class Actor:
    type: str  # "human" | "machine" | "system"
    id: Optional[str]  # User ID, API key ID, or None for system
```

### Actor Type Semantics

| Type | When Used | Example ID |
|------|-----------|------------|
| `human` | Console user action | Clerk user ID |
| `machine` | SDK/API key action | API key ID |
| `system` | Background job, scheduler | `None` or job name |

---

## 8.15 Event Context

```python
@dataclass(frozen=True)
class EventContext:
    request_id: Optional[str]  # From X-Request-ID header
    trace_id: Optional[str]    # From distributed tracing
```

Context enables correlation but is never required for event validity.

---

## 8.16 Severity Levels

| Severity | When Used |
|----------|-----------|
| `INFO` | Normal operations (state transitions, successful checks) |
| `WARN` | Anomalies, near-limits, unusual patterns |
| `ERROR` | Violations, rejections, failures |

---

## 8.17 Implementation Sequence (When Ready)

1. Create `app/observability/events.py` — UnifiedEvent, Actor, EventContext
2. Create `app/observability/provider.py` — ObservabilityProvider protocol
3. Create `app/observability/mock_provider.py` — MockObservabilityProvider
4. Create `app/observability/emitters.py` — Helper functions for each source
5. Wire emitters into existing systems (billing, protection, onboarding)
6. Add tests (deterministic, correlation validation)
7. Add E2E test: tenant timeline query

---

## 8.18 Completion Criteria (Design Phase)

Phase-8 design is complete when:

* Unified schema is defined
* Provider interface is fixed
* Invariants are written
* Non-goals are explicit
* No frozen files are touched

---

## Related Documents

- PIN-399: Onboarding State Machine (master PIN)
- PHASE_6_BILLING_LIMITS.md: Billing events source
- PHASE_7_ABUSE_PROTECTION.md: Protection events source
- FREEZE.md: Design freeze status
