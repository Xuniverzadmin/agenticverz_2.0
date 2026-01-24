# PIN-344: GC_L JIT Tradeoffs, Signal Feedback UX, Cross-Tenant Benchmarking

**Status:** DECISION
**Date:** 2026-01-07
**Category:** Governance / Architecture Decisions
**Reference:** PIN-343 (IR Optimizer), PIN-342 (Interpreter), PIN-341 (Signals)
**Authority:** Human-specified, governance-tight

---

## Executive Summary

This PIN documents three architectural decisions:

1. **Policy IR: JIT vs Interpreter** — Interpreter-first, JIT as optional optimization
2. **Signal Usefulness Feedback** — UX contract for human-aligned learning
3. **Cross-Tenant Benchmarking** — Founder-only anonymized aggregates

**Core Principle:** Correctness > speed, human authority > AI learning, privacy > insight.

---

# PART 1: Policy IR Interpreter — JIT vs Interpreter

## 1.1 Baseline Facts

Given the constrained DSL:

| Property | Value |
|----------|-------|
| Loop-free | ✅ |
| Branch-free (AND/OR only) | ✅ |
| Side-effect free | ✅ |
| Deterministic | ✅ |
| Policies evaluated | Often |
| Policies changed | Rarely |
| Audit requirement | Heavy |

**Bias:** Correctness > raw speed

---

## 1.2 Option Comparison

### Option A: Pure Interpreter

| Aspect | Assessment |
|--------|------------|
| Reasoning | Extremely easy |
| Replay/Audit | Perfect |
| Code generation | None |
| Attack surface | Minimal |
| Sandboxing | Simple |
| Speed | ~2-5× slower than JIT |

**Ideal for:** ≤ hundreds of policies, strong audit focus, early-mid scale

### Option B: JIT Compilation

| Aspect | Assessment |
|--------|------------|
| Speed | Fast (high-frequency evaluation) |
| Metrics | Can be hoisted |
| Branches | Optimized away |
| Audit | Harder line-by-line |
| Determinism | Must enforce explicitly |
| Attack surface | Larger |
| Debugging | Complex |

---

## 1.3 Decision: Hybrid Model (RECOMMENDED)

**Rule:**
> **Interpreter is canonical. JIT is an optimization, never a source of truth.**

### Execution Model

```
┌─────────────────────────────────────────────────────┐
│                   Policy Execution                   │
├─────────────────────────────────────────────────────┤
│  1. Always compile DSL → IR                          │
│  2. Default execution = Interpreter                  │
│  3. JIT allowed only if:                             │
│     - Policy is ACTIVE                               │
│     - IR hash is stable                              │
│     - Interpreter result == JIT result (verified)    │
└─────────────────────────────────────────────────────┘
```

### JIT Safety Rules

| Rule | Enforcement |
|------|-------------|
| JIT output includes IR hash | Required |
| JIT output includes deterministic fingerprint | Required |
| Mismatch → JIT disabled automatically | Automatic |
| Replay always uses interpreter | Mandatory |
| Production may use JIT | Optional |

### Governance Outcome

| Context | Execution Mode |
|---------|----------------|
| Replay | Interpreter (always) |
| Audit | Interpreter (always) |
| Simulation | Interpreter (always) |
| Production (active policy) | JIT (if verified) |
| Production (fallback) | Interpreter |

---

## 1.4 Decision Summary

| Criterion | Interpreter | JIT |
|-----------|-------------|-----|
| Auditability | ✅ Excellent | ⚠️ Medium |
| Determinism | ✅ Strong | ⚠️ Must enforce |
| Performance | ⚠️ Moderate | ✅ High |
| Attack Surface | ✅ Minimal | ❌ Higher |

**Final Decision:** Interpreter-first, JIT as optional optimization.

---

# PART 2: Signal Usefulness Feedback — UX Contract

## 2.1 Purpose

Signals improve only if **humans tell the system whether they were useful**.

Requirements:
- Lightweight
- Non-intrusive
- Non-gamable
- Auditable

---

## 2.2 Feedback Collection Rules (STRICT)

Feedback may be requested **only when**:

| Condition | Required |
|-----------|----------|
| FACILITATION recommendation was shown | ✅ |
| Human took GC_L action OR dismissed it | ✅ |
| No auto-action occurred | ✅ |

**Never interrupt unrelated workflows.**

---

## 2.3 Allowed Feedback Inputs (CLOSED SET)

| Input | Meaning | Updates Accuracy |
|-------|---------|------------------|
| 👍 Useful | Signal helped decision | Yes (+1.0) |
| 👎 Not useful | Signal was noise | Yes (+0.0) |
| ⏭ Ignored | Seen, not evaluated | No (neutral) |

**Forbidden:**
- Free text
- Scoring scales
- Star ratings
- Detailed forms

---

## 2.4 Feedback Event Schema

```json
{
  "feedback_id": "uuid",
  "signal_id": "COST_RATE_SPIKE",
  "recommendation_id": "uuid",
  "actor_id": "uuid",
  "tenant_id": "uuid",
  "feedback": "USEFUL | NOT_USEFUL | IGNORED",
  "timestamp": "RFC3339",
  "context": {
    "action_taken": "KILLSWITCH | POLICY_ACTIVATE | DISMISS | NONE",
    "time_to_decision_ms": 5000
  }
}
```

---

## 2.5 Database Schema

```sql
CREATE TABLE signal_feedback (
  feedback_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  signal_id           TEXT NOT NULL,
  recommendation_id   UUID NOT NULL,
  actor_id            UUID NOT NULL,
  tenant_id           UUID NOT NULL,
  feedback            TEXT NOT NULL,
  action_taken        TEXT,
  time_to_decision_ms INTEGER,
  created_at          TIMESTAMP NOT NULL DEFAULT NOW(),

  CONSTRAINT valid_feedback CHECK (feedback IN ('USEFUL', 'NOT_USEFUL', 'IGNORED')),
  CONSTRAINT one_feedback_per_signal UNIQUE (signal_id, recommendation_id, actor_id)
);

CREATE INDEX idx_signal_feedback_tenant ON signal_feedback(tenant_id, created_at);
CREATE INDEX idx_signal_feedback_signal ON signal_feedback(signal_id);
```

---

## 2.6 Governance Constraints

| Rule | Enforcement |
|------|-------------|
| Feedback updates confidence only | Code constraint |
| Feedback never changes thresholds | Code constraint |
| Feedback never modifies rules | Code constraint |
| Feedback never activates actions | Code constraint |
| One signal → one feedback per actor per window | DB unique constraint |
| Feedback is tenant-local | Tenant isolation |
| Never cross-tenant learning | Hard boundary |

---

## 2.7 UX Copy Contract (MANDATORY)

### Allowed Copy

- "Was this recommendation helpful?"
- "Did this alert help you decide?"
- "Rate this suggestion"

### Forbidden Copy

- "Did the system make the right decision?"
- "Help train the AI"
- "Improve our algorithm"
- "Your feedback trains the model"

**Principle:** Language must reinforce **human authority**, not AI agency.

---

## 2.8 Feedback API

```
POST /api/cus/signals/{signal_id}/feedback
```

**Request:**
```json
{
  "recommendation_id": "uuid",
  "feedback": "USEFUL",
  "action_taken": "POLICY_ACTIVATE",
  "confirmation": true
}
```

**Response:** `201 Created`
```json
{
  "feedback_id": "uuid",
  "accuracy_updated": true
}
```

---

# PART 3: Cross-Tenant Anonymized Benchmarking

## 3.1 Purpose

Enable founders to answer:

| Question | Allowed |
|----------|---------|
| Are we seeing outliers? | ✅ |
| Are defaults sane? | ✅ |
| Is a tenant misconfigured? | ✅ |
| Rank customers | ❌ |
| Compare identities | ❌ |
| Expose sensitive patterns | ❌ |

---

## 3.2 Eligibility Rules (STRICT)

Only include tenants that:

| Condition | Threshold |
|-----------|-----------|
| Opted in (contractual) | Required |
| Minimum executions (k-anonymity) | K ≥ 20 |
| Minimum tenant pool | N ≥ 10 |

---

## 3.3 Data Classification

### Allowed (Aggregates Only)

| Metric | Aggregation |
|--------|-------------|
| Error rate | Percentiles (p50/p90/p99) |
| Cost distribution | Bands (0-10, 10-50, 50-200, 200+) |
| Policy fire-rate | Histograms |
| Signal frequency | Frequency bands |

### Forbidden (Never)

| Data | Reason |
|------|--------|
| Tenant IDs | Direct identification |
| Names | Direct identification |
| Absolute spend | Sensitive |
| Absolute volumes | Fingerprinting risk |
| Unique behavioral patterns | Re-identification risk |

---

## 3.4 Aggregation Model

```
Metric → Bucket → Percentile → Band
```

### Example: Error Rate

```json
{
  "metric": "error_rate",
  "aggregation": "percentile",
  "values": {
    "p50": 0.02,
    "p90": 0.08,
    "p99": 0.15
  },
  "tenant_count": 47,
  "computed_at": "RFC3339"
}
```

### Example: Cost Bands

```json
{
  "metric": "cost_per_hour",
  "aggregation": "band_distribution",
  "bands": [
    { "range": "0-10", "percentage": 45 },
    { "range": "10-50", "percentage": 35 },
    { "range": "50-200", "percentage": 15 },
    { "range": "200+", "percentage": 5 }
  ],
  "tenant_count": 47,
  "computed_at": "RFC3339"
}
```

---

## 3.5 Access Control

| Surface | Access |
|---------|--------|
| Customer Console | ❌ Never |
| Ops Console | ❌ Never |
| Founder Console | ✅ Only |

### Founder Console Rules

- Clearly labeled "Aggregated / Anonymized"
- No drill-down to individual tenants
- No export of raw tables
- All access logged

---

## 3.6 Infrastructure Separation

| Component | Separation |
|-----------|------------|
| Data pipeline | Separate |
| Storage | Separate database/schema |
| Access control | Separate RBAC rules |
| Audit logging | All founder access logged |

---

## 3.7 Incident Definition

Any attempt to de-anonymize → **INCIDENT**

| Action | Classification |
|--------|----------------|
| Query for individual tenant | Incident |
| Export raw data | Incident |
| Join with identifiable data | Incident |
| Bypass aggregation | Incident |

---

## 3.8 Benchmark API (Founder-Only)

```
GET /api/fdr/benchmarks
```

**Headers:**
```
X-Actor-Type: FOUNDER
X-Audit-Reason: required
```

**Response:**
```json
{
  "benchmarks": [
    {
      "metric": "error_rate",
      "aggregation": "percentile",
      "values": { "p50": 0.02, "p90": 0.08, "p99": 0.15 },
      "tenant_count": 47
    }
  ],
  "computed_at": "RFC3339",
  "anonymization_level": "K_ANONYMITY_20"
}
```

---

# Implementation Priority

| Component | Priority | Dependency |
|-----------|----------|------------|
| Interpreter (canonical) | P0 | None |
| JIT harness | P2 | Interpreter working |
| Feedback schema | P1 | Signal catalog |
| Feedback API | P1 | Feedback schema |
| Feedback UI | P1 | Feedback API |
| Benchmark pipeline | P3 | Production data |
| Benchmark API | P3 | Pipeline |

---

## References

- PIN-343: IR Optimizer, Confidence, Anchoring
- PIN-342: UI Contract, Interpreter, Hash-Chain
- PIN-341: Formal Governance Pillars
- PIN-340: Implementation Specification

---

**Status:** DECISION
**Governance State:** JIT optional, feedback human-aligned, benchmarking privacy-preserving.
