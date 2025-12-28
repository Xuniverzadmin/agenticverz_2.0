# C5-S3: Learning from Optimization Effectiveness

**Version:** 1.0
**Status:** FROZEN (2025-12-28)
**Phase:** C5 Learning & Evolution
**Reference:** PIN-232, C5_CI_GUARDRAILS_DESIGN.md
**Prerequisite:** C5-S1 CERTIFIED, C5-S2 DESIGNED
**Does NOT unlock implementation**

---

## 1. Purpose (Why C5-S3 Exists)

C5-S3 answers **one question only**:

> *"Did the envelope actually help?"*

Not *how*. Not *when*. Not *apply*.
Just: **did it help?**

This is **not** optimization.
This is **outcome observation for humans**.

---

## 2. Core Principle (Single Sentence)

> **Learning observes outcomes. Humans interpret. Existing envelopes apply.**

If this sentence ever becomes false, C5-S3 certification is invalid.

---

## 3. What C5-S3 Answers

C5-S3 compares two states:

| State | Definition |
|-------|------------|
| Baseline | System behavior without the envelope |
| With-Envelope | System behavior during envelope application |

And asks:

> "Was there a measurable difference in the intended direction?"

### What "Help" Means

"Help" is defined narrowly:

| Envelope Class | "Help" Definition |
|----------------|-------------------|
| COST | Cost decreased or stayed same |
| RELIABILITY | Error rate decreased or latency improved |
| PERFORMANCE | Throughput increased or latency decreased |
| SAFETY | No incidents, no violations |

**C5-S3 does NOT define thresholds.**
**C5-S3 does NOT recommend actions.**
**C5-S3 only reports what happened.**

---

## 4. What C5-S3 Observes (Allowed Inputs)

C5-S3 is allowed to read **only historical, immutable data**.

### Allowed Data Sources

| Source | Fields |
|--------|--------|
| `coordination_audit_records` | Envelope lifecycle (applied, ended, outcome) |
| Envelope metadata | class, parameter, bounds, timebox |
| Historical metrics | Pre/post aggregates (if persisted) |

### Allowed Comparisons

| Comparison | Description |
|------------|-------------|
| Before vs After | Metrics before envelope vs during envelope |
| Baseline period | Configurable window before application |
| Envelope period | Duration of envelope application |

### Explicitly Forbidden Inputs

C5-S3 **must NOT** access:

| Forbidden | Reason |
|-----------|--------|
| Live runtime state | One layer too close |
| Prediction confidence | Feedback loop risk |
| Real-time metrics | Creates coupling |
| Control-path signals | Safety isolation |
| User-level data | Privacy boundary |
| Kill-switch state | Safety isolation |

**Rule:** C5-S3 only sees what already happened, never what's happening.

**Enforcement:** CI-C5-3 (Learning operates on metadata tables only)

---

## 5. What C5-S3 Detects (Signals)

C5-S3 detects **outcomes**, not causes.

### Core Signals

| Signal ID | Name | Definition |
|-----------|------|------------|
| S3-E1 | Positive Effect | Metrics improved in intended direction |
| S3-E2 | Neutral Effect | No measurable change |
| S3-E3 | Negative Effect | Metrics moved opposite to intended direction |
| S3-E4 | Indeterminate | Insufficient data or confounding factors |

### Signal Properties

| Property | Requirement |
|----------|-------------|
| No thresholds | Do not define "how much" is enough |
| No recommendations | Do not suggest what to do |
| No rankings | Do not compare envelopes |
| Direction only | Only report which way metrics moved |

---

## 6. What C5-S3 Produces (Allowed Outputs)

C5-S3 produces exactly one artifact type:

### Learning Suggestion

```yaml
learning_suggestion:
  id: "LS-{uuid}"
  version: 1
  created_at: "2025-12-28T12:00:00Z"
  scenario: "C5-S3"
  observation_window:
    baseline_start: "2025-12-20T00:00:00Z"
    baseline_end: "2025-12-21T00:00:00Z"
    envelope_start: "2025-12-21T00:00:00Z"
    envelope_end: "2025-12-22T00:00:00Z"
  observed_outcome:
    envelope_id: "env-001"
    envelope_class: "COST"
    target_parameter: "retry_multiplier"
    signal_id: "S3-E1"
    signal_name: "Positive Effect"
    baseline_metrics:
      avg_cost_per_request: 0.0045
    envelope_metrics:
      avg_cost_per_request: 0.0038
    direction: "decreased"
    intended_direction: "decrease"
    aligned: true
  suggestion:
    type: "advisory"
    text: "Envelope 'retry_multiplier' in COST class showed positive effect. Cost per request decreased from $0.0045 to $0.0038 during envelope period."
  status: "pending_review"
  human_action: null
  applied: false
```

### Allowed Language (Suggestion Text)

| Allowed | Example |
|---------|---------|
| Observational | "Effect observed..." |
| Factual | "Metrics changed from X to Y" |
| Directional | "Cost decreased during envelope period" |
| Neutral | "This pattern was observed over N hours" |

### Forbidden Language (Hard Boundary)

| Forbidden | Reason |
|-----------|--------|
| "Effective" / "Ineffective" | Implies judgment |
| "Should keep" / "Should remove" | Implies action |
| "Recommend continuing" | Crosses advisory |
| "Will improve" | Promises outcome |
| "Better than baseline" | Implies ranking |
| Percentages as thresholds | Creates implicit standards |

**Enforcement:** CI-C5-1 (Learning outputs are advisory only)

---

## 7. Hard Invariants (Non-Negotiable)

### I-C5-S3-1 - Observation Only

C5-S3 **cannot** apply changes or influence decisions.

```python
# FORBIDDEN
if effect == "positive":
    extend_envelope()
```

### I-C5-S3-2 - No Thresholds

C5-S3 **cannot** define what counts as "enough" effect.

```python
# FORBIDDEN
if cost_reduction > 0.10:
    mark_as_effective()
```

### I-C5-S3-3 - No Rankings

C5-S3 **cannot** compare envelopes to each other.

```python
# FORBIDDEN
rank_envelopes_by_effectiveness()
```

### I-C5-S3-4 - No Recommendations

C5-S3 **cannot** suggest future actions.

```python
# FORBIDDEN
suggest_reapply_envelope()
```

### I-C5-S3-5 - Replay Independence

Replaying without C5 produces identical system behavior.

### I-C5-S3-6 - Kill-Switch Independence

Kill-switch has zero dependency on learning.

---

## 8. What C5-S3 Must NOT Do (Non-Goals)

| Forbidden Action | Reason | Enforcement |
|------------------|--------|-------------|
| Define effectiveness thresholds | Crosses into policy | CI-C5-1 |
| Rank envelopes | Implies authority | CI-C5-1 |
| Recommend envelope renewal | Autonomous decision | CI-C5-2 |
| Recommend envelope removal | Autonomous decision | CI-C5-2 |
| Score envelopes | Creates implicit hierarchy | CI-C5-1 |
| Trigger kill-switch | Safety isolation | CI-C5-6 |
| Auto-approve suggestions | Human gate bypass | CI-C5-2 |
| Access runtime tables | Metadata boundary | CI-C5-3 |

If any of these occur, C5-S3 certification is immediately invalid.

---

## 9. Human Approval Model (Strict)

### Suggestion Lifecycle

```
CREATED -> PENDING_REVIEW -> ACKNOWLEDGED -> DISMISSED | APPLIED_EXTERNALLY
```

| State | Meaning |
|-------|---------|
| `created` | Learning produced suggestion |
| `pending_review` | Awaiting human attention |
| `acknowledged` | Human saw and understood |
| `dismissed` | Human chose not to act |
| `applied_externally` | Human made a change outside learning |

### What "Mark Applied" Does NOT Do

- Does NOT extend any envelope
- Does NOT renew any envelope
- Does NOT modify any bounds
- Only records that human took external action

**Enforcement:** CI-C5-2 (No learned change applies without approval flag)

---

## 10. Suggestion Versioning (Mandatory)

All suggestions must be:

| Requirement | Implementation |
|-------------|----------------|
| Immutable | Once created, never modified |
| Versioned | `version` field, starts at 1 |
| Timestamped | `created_at` field |
| Linked | `id` field, UUID |
| Evidence-linked | Baseline + envelope metrics |
| Auditable | Stored in `learning_suggestions` table |

**Enforcement:** CI-C5-4 (All learned suggestions are versioned)

---

## 11. Learning Disable Flag (Required)

C5-S3 must check `LEARNING_ENABLED` flag before execution:

```python
if not config.learning_enabled:
    log.info("Learning disabled, skipping C5-S3")
    return
```

When disabled:
- No observations collected
- No suggestions generated
- Coordination continues unchanged
- No error, no warning, silent skip

**Enforcement:** CI-C5-5 (Learning disable flag exists and works)

---

## 12. Kill-Switch Isolation (Mandatory)

C5-S3 must have **zero imports** from:
- `optimization/killswitch.py`
- `optimization/coordinator.py`
- Any runtime coordination modules

Learning and control are **completely separate**.

**Enforcement:** CI-C5-6 (Kill-switch behavior unchanged by learning)

---

## 13. Relationship to Other Scenarios

| Scenario | Observes | Question |
|----------|----------|----------|
| S1 | Rollback frequency | "Are bounds too aggressive?" |
| S2 | Coordination friction | "Are envelopes structurally conflicting?" |
| **S3** | **Outcome direction** | **"Did the envelope help?"** |

### S1 + S2 + S3 Together

| Scenario | Symptom | Diagnosis |
|----------|---------|-----------|
| S1 High | Many rollbacks | Bounds too tight |
| S2 High | Many conflicts | Architecture issue |
| S3 Negative | Wrong direction | Envelope design wrong |
| S3 Neutral | No effect | Envelope scope too narrow |
| S3 Positive | Right direction | Envelope worked |

**Humans synthesize these signals. Learning does not.**

---

## 14. Why C5-S3 Is Locked

C5-S3 is the most dangerous learning scenario because it *looks* like it knows what works.

Locking ensures:
- Humans define what "effective" means
- Learning never optimizes for a metric
- Coordination remains deterministic

---

## 15. Exit Condition (Future)

C5-S3 may be **unlocked for implementation only if**:

| Condition | Status |
|-----------|--------|
| C5-S1 certified | CERTIFIED |
| C5-S2 design frozen | DRAFT |
| S3 design frozen | DRAFT |
| Humans consistently agree with S1/S2 suggestions | PENDING |
| No threshold creep in S1/S2 | PENDING |
| Re-certification rules in place | READY |

---

## 16. Test Scenarios (Design Only)

| Scenario | Description | Expected Outcome |
|----------|-------------|------------------|
| S3-T1 | Positive effect observed | S3-E1 suggestion generated |
| S3-T2 | Neutral effect observed | S3-E2 suggestion generated |
| S3-T3 | Negative effect observed | S3-E3 suggestion generated |
| S3-T4 | Insufficient data | S3-E4 suggestion generated |
| S3-T5 | No threshold applied | No "effective" judgment |
| S3-T6 | No ranking produced | No comparison language |
| S3-T7 | Learning disabled | Silent skip |
| S3-T8 | Human acknowledges | Status change only |
| S3-T9 | Human dismisses | Status change only |
| S3-T10 | Suggestion immutability | Update rejected |
| S3-T11 | Kill-switch isolation | Zero imports verified |

---

## 17. Implementation Order (When Unlocked)

| Step | Description | Status |
|------|-------------|--------|
| 1 | Freeze C5-S3 design | DRAFT |
| 2 | Define acceptance criteria | DRAFT |
| 3 | Create s3_effectiveness.py module | LOCKED |
| 4 | Implement outcome observation | LOCKED |
| 5 | Implement suggestion generation | LOCKED |
| 6 | Add tests (S3-T1 to S3-T11) | LOCKED |
| 7 | C5-S3 certification | LOCKED |

---

## 18. Re-Certification Triggers

C5-S3 certification becomes invalid if:

| Trigger | Severity |
|---------|----------|
| Thresholds appear in code | CRITICAL |
| Rankings appear in output | CRITICAL |
| "Effective" judgment in language | CRITICAL |
| Action recommendations appear | CRITICAL |
| Human approval gate bypassed | CRITICAL |
| Kill-switch imports appear | CRITICAL |
| Suggestion mutated after creation | HIGH |
| Learning runs when disabled | HIGH |
| Forbidden language appears | MEDIUM |

---

## 19. Final Verdict

- **C5-S3 is a thermometer, not a doctor**
- **It reports direction, not diagnosis**
- **It strengthens human judgment, not replaces it**

The hardest thing about S3 is **not adding thresholds**.
The system must resist the urge to say "this was effective."
Only humans can decide what "effective" means.

---

## Related Documents

| Document | Purpose |
|----------|---------|
| PIN-232 | C5 Entry Conditions |
| C5_CI_GUARDRAILS_DESIGN.md | CI enforcement rules |
| C5_S1_LEARNING_SCENARIO.md | S1 design (rollback) |
| C5_S2_LEARNING_SCENARIO.md | S2 design (friction) |
| C5_S3_ACCEPTANCE_CRITERIA.md | Pass/fail criteria |
