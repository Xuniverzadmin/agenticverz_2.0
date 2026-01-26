# Phase-7 — Abuse & Protection Layer (Design Template v1)

**Status:** DESIGN-ONLY
**Created:** 2026-01-12
**Applies when:** `tenant.onboarding_state == COMPLETE`
**Frozen dependencies:** Auth (Phase-0), Onboarding (Phase-4), Roles (Phase-5), Billing Design (Phase-6)
**Reference:** PIN-399

---

## 7.0 Prime Directive

> **Abuse protection constrains behavior, not identity.**

This layer:

* never authenticates
* never authorizes
* never mutates onboarding
* never assigns roles
* never changes billing state

It only answers:
**"Should this action proceed right now?"**

---

## 7.1 Threat Model (Explicit)

Phase-7 protects against:

| Threat              | Example                           |
| ------------------- | --------------------------------- |
| Accidental overuse  | Buggy SDK loop                    |
| Cost explosion      | Prompt runaway / tool recursion   |
| Burst abuse         | Sudden traffic spike              |
| Slow bleed abuse    | Sustained high usage              |
| Cross-tenant impact | One tenant degrading shared infra |

Non-goals:

* Fraud detection
* Payment enforcement
* Account trust scoring

---

## 7.2 Protection Dimensions (Orthogonal)

Phase-7 introduces **four independent controls**:

| Dimension       | Scope         | Example          |
| --------------- | ------------- | ---------------- |
| Rate limits     | Time-based    | 1000 req/min     |
| Burst control   | Short window  | 100 req/sec      |
| Cost guards     | Value-based   | $500/day compute |
| Anomaly signals | Pattern-based | Sudden 10x jump  |

Each control:

* can trigger independently
* emits its own signal
* does not know about others

---

## 7.3 Enforcement Surface

### Enforcement applies at:

* SDK endpoints
* Runtime execution paths
* Background workers

### Enforcement does NOT apply to:

* Onboarding endpoints
* Auth endpoints
* Founder endpoints
* Internal ops endpoints

---

## 7.4 Decision Outcomes (Finite, Locked)

Every check returns exactly one of:

| Outcome  | Meaning             |
| -------- | ------------------- |
| ALLOW    | Proceed             |
| THROTTLE | Delay / slow        |
| REJECT   | Hard stop           |
| WARN     | Allow + emit signal |

No silent drops.
No implicit retries.

---

## 7.5 Failure Contracts (Design-Locked)

### Rate / Burst Rejection

```json
{
  "error": "rate_limited",
  "dimension": "burst",
  "retry_after_ms": 1200
}
```

### Cost Guard Rejection

```json
{
  "error": "cost_limit_exceeded",
  "limit": "daily_compute_budget",
  "current_value": 512.45,
  "allowed_value": 500.00
}
```

### Anomaly Warning (Non-Blocking)

```json
{
  "signal": "usage_anomaly_detected",
  "baseline": 120,
  "observed": 980,
  "window": "5m"
}
```

Warnings are **never user-blocking**.

---

## 7.6 Mock-First Control Providers

No real enforcement engines yet.

### Provider Interface

```python
from enum import Enum
from typing import Optional, Protocol
from dataclasses import dataclass


class Decision(Enum):
    ALLOW = "allow"
    THROTTLE = "throttle"
    REJECT = "reject"
    WARN = "warn"


@dataclass
class ProtectionResult:
    decision: Decision
    dimension: str
    retry_after_ms: Optional[int] = None
    current_value: Optional[float] = None
    allowed_value: Optional[float] = None
    message: Optional[str] = None


@dataclass
class AnomalySignal:
    baseline: float
    observed: float
    window: str
    severity: str


class AbuseProtectionProvider(Protocol):
    def check_rate_limit(self, tenant_id: str, endpoint: str) -> ProtectionResult: ...
    def check_burst(self, tenant_id: str, endpoint: str) -> ProtectionResult: ...
    def check_cost(self, tenant_id: str, operation: str) -> ProtectionResult: ...
    def detect_anomaly(self, tenant_id: str) -> Optional[AnomalySignal]: ...
```

### Initial Implementation Constraints

* Deterministic thresholds
* Static configs
* No external calls
* No ML

---

## 7.7 Ordering Rule (Critical)

Checks execute in this order:

```
1. Rate limit
2. Burst control
3. Cost guard
4. Anomaly detection
```

First **REJECT** stops evaluation.

This order is **locked** to preserve predictability.

---

## 7.8 Relationship to Billing (Explicit)

| Aspect        | Relationship         |
| ------------- | -------------------- |
| Plans         | Provide limit inputs |
| Billing state | Read-only input      |
| Enforcement   | Independent          |
| Mutation      | Forbidden            |

Abuse controls **read billing**, never write to it.

---

## 7.9 Observability & Ops Signals

All rejections emit structured events:

```json
{
  "event": "abuse_protection_triggered",
  "tenant_id": "...",
  "dimension": "cost_guard",
  "action": "reject",
  "timestamp": "..."
}
```

These are:

* Ops-only
* Never user-visible by default
* Usable for dashboards later

---

## 7.10 Console Behavior (Non-Authoritative)

| Console               | Visibility                   |
| --------------------- | ---------------------------- |
| customer console      | Friendly error + retry hints |
| preflight-agenticverz | Same as customer             |
| preflight-fops        | Aggregated signals           |
| fops.com              | Full raw signals             |

No console changes enforcement behavior.

---

## 7.11 Phase-7 Invariants (LOCKED)

### ABUSE-001

> Protection does not affect onboarding, roles, or billing state.

### ABUSE-002

> All enforcement outcomes are explicit (no silent failure).

### ABUSE-003

> Anomaly detection never blocks user traffic.

### ABUSE-004

> Protection providers are swappable behind a fixed interface.

### ABUSE-005

> Mock provider must be behavior-compatible with real provider.

---

## 7.12 Explicit Non-Goals

These are **NOT** part of Phase-7:

* ML models
* Adaptive pricing
* Auto-suspension
* Cross-tenant scoring
* Blacklists
* IP blocking

Those are **Phase-8+**, if ever.

---

## 7.13 API Surface (Design Only)

### Internal Middleware (Not User-Facing)

Protection checks are middleware, not explicit API endpoints.

### Ops APIs (Founder Only)

```
GET  /fdr/abuse/signals/{tenant_id}
POST /fdr/abuse/override
```

Rules:

* Explicit audit
* Explicit reason
* Time-limited overrides only

---

## 7.14 Implementation Sequence (When Ready)

1. Create `Decision` enum in `app/protection/decisions.py`
2. Create `AbuseProtectionProvider` protocol
3. Create `MockAbuseProtectionProvider`
4. Create middleware integration point
5. Add tests (deterministic, no real limits)
6. Wire to ops dashboard

---

## 7.15 Completion Criteria (Design Phase)

Phase-7 design is complete when:

* Provider interface is fixed
* Decision outcomes are finite
* Invariants are written
* No existing frozen files are touched

---

## Related Documents

- PIN-399: Onboarding State Machine (master PIN)
- PHASE_6_BILLING_LIMITS.md: Billing design (read-only input)
- FREEZE.md: Design freeze status
