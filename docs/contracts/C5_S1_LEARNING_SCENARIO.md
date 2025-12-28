# C5-S1: Learning from Rollback Frequency

**Version:** 1.0
**Status:** DESIGN
**Phase:** C5 Learning & Evolution
**Reference:** PIN-232, C5_CI_GUARDRAILS_DESIGN.md

---

## Purpose

C5-S1 is the first learning scenario in Phase C5. It observes **envelope rollback patterns** and produces **advisory suggestions** for humans to consider.

This is **meta-learning** — learning about the system's safety behavior, not learning to control.

### Why Rollback Frequency?

Rollbacks are the clearest signal that an envelope:
- was too aggressive
- had poorly calibrated bounds
- encountered unexpected conditions

High rollback frequency suggests the system is **trying and failing** repeatedly, which wastes resources and creates noise without producing value.

C5-S1 helps humans understand this pattern without automating any response.

---

## Core Principle (Single Sentence)

> **Learning observes rollbacks. Humans interpret. Existing envelopes apply.**

If this sentence ever becomes false, C5-S1 certification is invalid.

---

## What C5-S1 Observes (Allowed Inputs)

C5-S1 may read the following **metadata only**:

| Input | Source | Format |
|-------|--------|--------|
| Envelope rollback events | `coordination_audit_records` | Event records |
| Rollback reason codes | `revert_reason` field | Enum value |
| Envelope class | `envelope_class` field | SAFETY/RELIABILITY/COST/PERFORMANCE |
| Envelope parameter | `target_parameter` field | String |
| Time-to-rollback | Calculated: `reverted_at - applied_at` | Duration |
| Rollback frequency | Calculated: count per window | Integer |
| Window definition | Configuration | Duration (e.g., 24h, 7d) |

### Allowed Aggregations

| Aggregation | Description |
|-------------|-------------|
| Count by envelope class | How many rollbacks per class? |
| Count by parameter | Which parameters trigger rollbacks? |
| Average time-to-rollback | How quickly do envelopes fail? |
| Trend direction | Increasing, stable, decreasing? |

### Forbidden Inputs (Hard Boundary)

C5-S1 **must NOT** access:

| Forbidden | Reason |
|-----------|--------|
| Runtime metrics | One layer too close |
| Live performance signals | Real-time influence risk |
| Direct envelope internals | Bypass coordination |
| Control-plane state | Safety path |
| Prediction confidence | Creates feedback loop |
| Kill-switch state | Safety isolation |
| Live envelope parameters | Runtime, not metadata |

**Enforcement:** CI-C5-3 (Learning operates on metadata tables only)

---

## What C5-S1 Produces (Allowed Outputs)

C5-S1 produces exactly one artifact type:

### Learning Suggestion

```yaml
learning_suggestion:
  id: "LS-{uuid}"
  version: 1
  created_at: "2025-12-28T12:00:00Z"
  scenario: "C5-S1"
  observation_window:
    start: "2025-12-21T00:00:00Z"
    end: "2025-12-28T00:00:00Z"
  observation:
    envelope_class: "COST"
    target_parameter: "retry_multiplier"
    rollback_count: 7
    total_envelopes: 12
    rollback_rate: 0.583
    avg_time_to_rollback_seconds: 45.2
    trend: "increasing"
  suggestion:
    type: "advisory"
    confidence: "low|medium|high"
    text: "Rollback frequency suggests current bounds may be tight for retry_multiplier in COST class."
  status: "pending_review"
  human_action: null
  applied: false
```

### Allowed Language (Suggestion Text)

| Allowed | Example |
|---------|---------|
| Observational | "Rollback frequency suggests..." |
| Conditional | "You may want to review..." |
| Neutral | "This pattern has been observed for X days" |

### Forbidden Language (Hard Boundary)

| Forbidden | Reason |
|-----------|--------|
| Imperative | "Should reduce", "Must adjust" |
| Recommending | "System recommends applying" |
| Promising | "Will improve reliability" |
| Comparative | "Better than previous" |
| Action-oriented | "Apply this change" |

**Enforcement:** CI-C5-1 (Learning outputs are advisory only)

---

## What C5-S1 Must NOT Do (Non-Goals)

| Forbidden Action | Reason | Enforcement |
|------------------|--------|-------------|
| Modify envelopes | Bypasses coordination | CI-C5-2 |
| Modify bounds | Autonomous mutation | CI-C5-2 |
| Trigger kill-switch | Safety isolation | CI-C5-6 |
| Influence coordination | Runtime interference | CI-C5-3 |
| Auto-approve suggestions | Human gate bypass | CI-C5-2 |
| Generate new envelopes | Scope creep | CI-C5-3 |
| Access runtime tables | Metadata boundary | CI-C5-3 |
| Execute without logging | Audit requirement | CI-C5-4 |

If any of these occur, C5-S1 certification is immediately invalid.

---

## Human Approval Model (Strict)

### Suggestion Lifecycle

```
CREATED → PENDING_REVIEW → ACKNOWLEDGED → DISMISSED | APPLIED_EXTERNALLY
```

| State | Meaning |
|-------|---------|
| `created` | Learning produced suggestion |
| `pending_review` | Awaiting human attention |
| `acknowledged` | Human saw and understood |
| `dismissed` | Human chose not to act |
| `applied_externally` | Human made a change outside learning |

### Human Actions (All Require Explicit Click)

| Action | Effect |
|--------|--------|
| Acknowledge | Marks as seen, no system change |
| Dismiss | Marks as rejected, no system change |
| Mark Applied | Human indicates they changed something |

### What "Mark Applied" Does NOT Do

- Does NOT modify any envelope
- Does NOT change any bound
- Does NOT trigger any system behavior
- Only records that human took external action

**Enforcement:** CI-C5-2 (No learned change applies without approval flag)

---

## Suggestion Versioning (Mandatory)

All suggestions must be:

| Requirement | Implementation |
|-------------|----------------|
| Immutable | Once created, never modified |
| Versioned | `version` field, starts at 1 |
| Timestamped | `created_at` field |
| Linked | `id` field, UUID |
| Auditable | Stored in `learning_suggestions` table |

**Enforcement:** CI-C5-4 (All learned suggestions are versioned)

---

## Learning Disable Flag (Required)

C5-S1 must check `LEARNING_ENABLED` flag before execution:

```python
if not config.learning_enabled:
    log.info("Learning disabled, skipping C5-S1")
    return
```

When disabled:
- No observations collected
- No suggestions generated
- Coordination continues unchanged
- No error, no warning, silent skip

**Enforcement:** CI-C5-5 (Learning disable flag exists and works)

---

## Kill-Switch Isolation (Mandatory)

C5-S1 must have **zero imports** from:
- `optimization/killswitch.py`
- `optimization/coordinator.py`
- Any runtime coordination modules

Learning and control are **completely separate**.

**Enforcement:** CI-C5-6 (Kill-switch behavior unchanged by learning)

---

## Data Model (Design Only)

### Table: `learning_suggestions`

```sql
CREATE TABLE learning_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version INTEGER NOT NULL DEFAULT 1,
    scenario VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    observation_window_start TIMESTAMPTZ NOT NULL,
    observation_window_end TIMESTAMPTZ NOT NULL,
    observation JSONB NOT NULL,
    suggestion_type VARCHAR(20) NOT NULL DEFAULT 'advisory',
    suggestion_confidence VARCHAR(10) NOT NULL,
    suggestion_text TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending_review',
    human_action VARCHAR(30),
    human_action_at TIMESTAMPTZ,
    human_actor_id VARCHAR(100),
    applied BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT status_valid CHECK (status IN (
        'pending_review', 'acknowledged', 'dismissed', 'applied_externally'
    )),
    CONSTRAINT confidence_valid CHECK (suggestion_confidence IN (
        'low', 'medium', 'high'
    )),
    CONSTRAINT type_advisory CHECK (suggestion_type = 'advisory')
);

-- Immutability: suggestions cannot be updated, only status can change
CREATE OR REPLACE FUNCTION prevent_suggestion_mutation()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.observation != NEW.observation OR
       OLD.suggestion_text != NEW.suggestion_text OR
       OLD.suggestion_confidence != NEW.suggestion_confidence THEN
        RAISE EXCEPTION 'Learning suggestions are immutable';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER learning_suggestion_immutable
    BEFORE UPDATE ON learning_suggestions
    FOR EACH ROW
    EXECUTE FUNCTION prevent_suggestion_mutation();
```

---

## Acceptance Criteria (See Separate Document)

Acceptance criteria are defined in `C5_S1_ACCEPTANCE_CRITERIA.md`.

All criteria must be:
- Binary (pass/fail)
- Testable (automatable)
- Independent (no dependencies between tests)

---

## Test Scenarios (Design Only)

| Scenario | Description | Expected Outcome |
|----------|-------------|------------------|
| S1-T1 | No rollbacks in window | No suggestion generated |
| S1-T2 | Single rollback | No suggestion (below threshold) |
| S1-T3 | High rollback rate | Advisory suggestion generated |
| S1-T4 | Learning disabled | No observation, no suggestion |
| S1-T5 | Human acknowledges | Status changes, no system change |
| S1-T6 | Human dismisses | Status changes, no system change |
| S1-T7 | Suggestion immutability | Update rejected |
| S1-T8 | Kill-switch isolation | Zero imports verified |

---

## Implementation Order (When Unlocked)

| Step | Description | Status |
|------|-------------|--------|
| 1 | Freeze C5-S1 design | ⏳ IN PROGRESS |
| 2 | Define acceptance criteria | ⏳ NEXT |
| 3 | Create CI guardrail mapping | ⏳ PENDING |
| 4 | Implement data model (migration) | 🔒 LOCKED |
| 5 | Implement observation logic | 🔒 LOCKED |
| 6 | Implement suggestion generation | 🔒 LOCKED |
| 7 | Implement human review UI | 🔒 LOCKED |
| 8 | C5-S1 certification | 🔒 LOCKED |

---

## Re-Certification Triggers

C5-S1 certification becomes invalid if:

| Trigger | Severity |
|---------|----------|
| Suggestion becomes non-advisory | CRITICAL |
| Human approval gate bypassed | CRITICAL |
| Learning accesses runtime tables | CRITICAL |
| Kill-switch imports appear | CRITICAL |
| Suggestion mutated after creation | HIGH |
| Learning runs when disabled | HIGH |
| Forbidden language appears | MEDIUM |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| PIN-232 | C5 Entry Conditions |
| C5_CI_GUARDRAILS_DESIGN.md | CI enforcement rules |
| C5_S1_ACCEPTANCE_CRITERIA.md | Pass/fail criteria |
| C4_STABILITY_EVIDENCE_PACK_20251228.md | C4 stability gate evidence |
