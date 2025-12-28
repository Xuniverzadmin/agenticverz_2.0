# PIN-221: C2 Semantic Contract & Failure Modes

**Status:** ACTIVE (Design Phase)
**Created:** 2025-12-28
**Phase:** C2 (Prediction)
**Prerequisite:** PIN-220 APPROVED
**Playbook Reference:** `docs/playbooks/SESSION_PLAYBOOK.yaml` v1.2

---

## Purpose

This PIN defines the **C2 semantic contract** and **failure modes**.

This is governance, not implementation.

**Non-negotiable rule:** *Predictions may inform humans, never the system.*

If anything in this PIN is violated, **C2 is considered failed and must be rolled back**.

---

## What C2 IS

C2 introduces **predictions as advisory signals**.

Predictions answer questions like:
- "Is this likely to fail soon?"
- "Is this trending toward an incident?"
- "Is this pattern similar to past failures?"

They do **NOT** answer:
- "Should we stop?"
- "Should we retry?"
- "Should we block?"
- "Should we auto-fix?"

That distinction is non-negotiable.

---

## C2 Core Invariants (THESE ARE LAW)

### I-C2-1: Advisory Only

> Predictions must be explicitly labeled as advisory at every boundary.

- DB: `advisory = TRUE` column
- API: `advisory: true` in response
- UI: Advisory labeling visible
- Logs: Advisory context included

**If a prediction is consumed without advisory context → C2 FAIL**

---

### I-C2-2: No Control Path Influence

> No prediction may influence execution, control, retries, throttling, or enforcement.

**Explicitly forbidden:**
- Branching logic based on predictions
- Feature flags gated by predictions
- Backoff timers adjusted by predictions
- Rate limits influenced by predictions
- Kill switches triggered by predictions

**If behavior changes → C2 FAIL**

---

### I-C2-3: No Truth Mutation

> Predictions must not write to truth tables or alter incidents, traces, or replay.

Predictions can:
- Reference truth (read-only)
- Never modify truth

---

### I-C2-4: Replay Blindness

> Replay must not read predictions.

Replay is historical truth, not foresight.

---

### I-C2-5: Delete Safety

> Prediction deletion must not change system behavior or historical interpretation.

Predictions are disposable.

---

---

## C2 Failure Taxonomy

There are **exactly six classes of failure** in C2.

---

### FM-C2-1: False Positive Prediction

**Description:** Prediction says "high risk" when nothing bad happens.

**Why dangerous:** Humans overreact. Systems start trusting predictions emotionally.

**Required System Behavior:**
- No automatic mitigation
- No incident creation
- No control-path branching

**Acceptable Outcome:**
- Prediction expires quietly
- At most: human sees advisory and ignores it

**Invariant:** False positives must be *harmlessly ignorable*.

---

### FM-C2-2: False Negative Prediction

**Description:** Prediction misses a real incident.

**Why dangerous:** People assume "no warning = safe".

**Required System Behavior:**
- Incident still triggers normally (C1/B/A unaffected)
- No downgrade of severity
- No blame attribution to prediction layer

**Invariant:** Absence of prediction must never imply safety.

---

### FM-C2-3: Prediction Service Outage (LLM / Redis / Job Failure)

**Description:** Prediction pipeline is down.

**Why dangerous:** Systems accidentally become dependent on predictions.

**Required System Behavior:**
- Zero functional change
- No errors in O1/O2/O3
- O4 shows "No predictions available"

**Invariant:** C2 outage must be indistinguishable from C2 never existing.

---

### FM-C2-4: Redis Loss / Eviction / Inconsistency

**Description:** Redis keys vanish, evict, or corrupt.

**Why dangerous:** Redis becomes accidental source of truth.

**Required System Behavior:**
- Predictions may degrade or disappear
- No retries, throttles, or decisions change
- No "rebuild required" panic

**Invariant:** Redis loss must only reduce *advice*, never alter behavior.

---

### FM-C2-5: Prediction Data Corruption / Deletion

**Description:** Prediction rows deleted, expired, or malformed.

**Why dangerous:** Replay or audits get polluted.

**Required System Behavior:**
- Replay unchanged
- Incidents unchanged
- UI degrades gracefully

**Invariant:** Prediction deletion must be replay-safe and audit-safe.

---

### FM-C2-6: Semantic Leak (The Most Dangerous One)

**Description:** Prediction appears authoritative by language or placement.

**Examples:**
- Appears near O1 incidents
- Uses words like "confirmed", "will fail"
- Shown without advisory label

**Required System Behavior:**
- This is a **hard failure**
- C2 must be rolled back or blocked

**Invariant:** If a human can mistake prediction for truth → C2 FAIL.

---

## C2 Failure Handling Rules (Global)

These apply to **all scenarios**:

1. Predictions are **disposable**
2. Predictions are **expiring**
3. Predictions are **non-blocking**
4. Predictions are **never replayed**
5. Predictions are **never enforced**

If you ever need to "fix" C2 by adding coupling — you're already wrong.

---

## C2 Prediction Scenarios (Minimal & Sufficient)

### Scenario C2-S1: Incident Risk Prediction (Single-Tenant)

**Description:** Predict elevated risk for a specific tenant based on recent telemetry patterns.

**Inputs:**
- C1 telemetry aggregates (read-only)
- Rolling error counts
- Latency spikes

**Output:**
```yaml
prediction_type: incident_risk
subject: tenant:<id>
confidence_score: 0.0-1.0
advisory: TRUE
expires_at: +30m
```

**Covered Failure Modes:** FM-C2-1, FM-C2-2, FM-C2-3

**Why this scenario matters:** It tempts people to automate actions. You explicitly *do not*.

---

### Scenario C2-S2: Cost Spike Prediction (Resource Trend)

**Description:** Predict likely cost increase based on recent usage trends.

**Inputs:**
- Aggregated usage metrics
- Cost telemetry (read-only)

**Output:**
```yaml
prediction_type: cost_spike
subject: tenant:<id>
confidence_score: 0.0-1.0
advisory: TRUE
expires_at: +1h
```

**Explicitly Forbidden:**
- Auto-throttling
- Budget enforcement
- Alerts that block execution

**Covered Failure Modes:** FM-C2-1, FM-C2-4, FM-C2-6

**Why this scenario matters:** Cost predictions *feel* like control. This proves restraint.

---

### Scenario C2-S3: Policy Drift Prediction (Pattern Similarity)

**Description:** Predict that a workflow is drifting toward patterns that historically violated policy.

**Inputs:**
- Trace metadata
- Policy evaluation outcomes (read-only)

**Output:**
```yaml
prediction_type: policy_drift
subject: workflow:<id>
confidence_score: 0.0-1.0
advisory: TRUE
expires_at: +2h
```

**Explicitly Forbidden:**
- Blocking execution
- Auto-policy tightening
- Incident creation

**Covered Failure Modes:** FM-C2-5, FM-C2-6

**Why this scenario matters:** This is the hardest to keep advisory. That's why it's included.

---

## Scenario → Failure Coverage Matrix

| Scenario | FM-1 | FM-2 | FM-3 | FM-4 | FM-5 | FM-6 |
|----------|------|------|------|------|------|------|
| S1 Incident Risk | X | X | X | - | - | ! |
| S2 Cost Spike | X | - | - | X | - | ! |
| S3 Policy Drift | - | - | - | - | X | X |

- X = Covered
- ! = Semantic vigilance required

Together, **S1-S3 are sufficient** to cover all failure classes.

---

## Redis in C2 (Constrained)

Redis (Upstash) is now **allowed**, but only under these constraints:

### Allowed Uses
- Rolling aggregates
- Sliding windows
- Feature extraction
- Short-lived prediction inputs

### Forbidden Uses
- Gating logic
- Thresholds that change behavior
- Durability assumptions
- Replay inputs

**Invariant:** Redis outage must not change system behavior.

If Redis disappears and anything changes → **design bug**.

---

## UI Scope for C2 (O4 Only)

Predictions may appear **only in O4 (Advisory / Insights UI)**.

### Explicitly Forbidden
- O1 (Truth)
- O2 (Metrics)
- O3 (Operational control)

If a prediction appears near incidents or controls → **semantic leak**.

---

## Conceptual Data Model

```yaml
prediction_event:
  prediction_id: uuid
  subject_type: trace | incident | policy | tenant
  subject_id: string
  prediction_type: risk | drift | anomaly | saturation | cost_spike
  confidence_score: 0.0-1.0  # Informational only
  advisory: TRUE             # Hard-coded invariant
  created_at: timestamp
  expires_at: timestamp      # Required
```

**Rules:**
- No FK to truth tables (ID reference only)
- Expiry required
- Deletable at any time

---

## C2 Acceptance Criteria (Non-Negotiable)

C2 is considered **valid** only if:

1. All scenarios run on **Neon**
2. Claude executes real LLM + DB
3. Deleting all predictions changes nothing
4. Redis outage changes nothing
5. Replay output hashes identical
6. Human confirms O4 labeling is advisory

**If any one fails → C2 rollback.**

---

## What C2 Will NOT Do (Explicit Boundaries)

To be crystal clear, C2 is **not doing**:

- Network effects
- Cross-tenant learning
- Auto-actions
- Memory writing
- Optimization

Those belong to later stages (C3+).

---

## Truth Anchor

> Predictions that influence execution are not predictions — they are hidden control paths.
>
> C2 must be advisory, or it corrupts the truth-grade guarantees of C1.

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-28 | PIN-221 created with C2 semantic contract, 5 invariants, 6 failure modes, 3 scenarios |
