# C5-S2: Learning from Coordination Friction

**Version:** 1.0
**Status:** DESIGN (LOCKED)
**Phase:** C5 Learning & Evolution
**Reference:** PIN-232, C5_CI_GUARDRAILS_DESIGN.md
**Prerequisite:** C5-S1 CERTIFIED
**Does NOT unlock implementation**

---

## 1. Purpose (Why C5-S2 Exists)

C5-S2 answers **one question only**:

> *"Are envelopes repeatedly conflicting in ways that indicate structural design issues?"*

This is **not** optimization.
This is **diagnostics for humans**.

### Why Coordination Friction?

Friction occurs when:
- The same parameter is rejected repeatedly
- Envelopes oscillate between priority levels
- Different envelope classes conflict recurrently
- Envelopes are applied but short-lived (not due to rollback)

High friction suggests:
- Envelope scope may be poorly defined
- Priority assignments may be inconsistent
- Parameter boundaries may overlap unnecessarily

C5-S2 helps humans understand these patterns without automating any response.

---

## 2. Core Principle (Single Sentence)

> **Learning observes friction. Humans interpret. Existing envelopes apply.**

If this sentence ever becomes false, C5-S2 certification is invalid.

---

## 3. What C5-S2 Observes (Allowed Inputs)

C5-S2 is allowed to read **only immutable coordination history**.

### Allowed Data Sources

| Source | Fields |
|--------|--------|
| `coordination_audit_records` | All decision records |
| Envelope metadata | class, parameter, bounds |
| Coordination decisions | APPLIED, REJECTED, PREEMPTED |

### Allowed Aggregations

| Aggregation | Description |
|-------------|-------------|
| Same-parameter rejection count | How many times was a parameter rejected? |
| Priority oscillation count | How often do envelopes swap positions? |
| Class friction frequency | How often do COST/RELIABILITY conflict? |
| Envelope lifespan distribution | How long do envelopes survive? |

### Explicitly Forbidden Inputs

C5-S2 **must NOT** access:

| Forbidden | Reason |
|-----------|--------|
| Live runtime state | One layer too close |
| Prediction confidence scores | Feedback loop risk |
| Incident severity | Operational coupling |
| Cost metrics | Business logic bleeding |
| Replay traces | Execution path |
| Any control-path signal | Safety isolation |
| User data | Privacy boundary |

**Rule:** If the data didn't already exist in C4, C5-S2 cannot use it.

**Enforcement:** CI-C5-3 (Learning operates on metadata tables only)

---

## 4. What C5-S2 Detects (Signals)

C5-S2 detects **patterns**, not outcomes.

### Core Signals

| Signal ID | Name | Definition | Threshold |
|-----------|------|------------|-----------|
| S2-F1 | Repeated Same-Parameter Rejection | Same parameter rejected >= N times in window | N = 3 |
| S2-F2 | Priority Oscillation | Same envelope repeatedly preempted and re-applied | >= 2 cycles |
| S2-F3 | Class Friction | COST vs RELIABILITY (or other class) conflicts recur | >= 3 conflicts |
| S2-F4 | Short-Lived Envelopes | Applied -> ended quickly (not rollback, not preemption) | < 10% of timebox |

These are **descriptive signals**, not scores.

---

## 5. What C5-S2 Produces (Allowed Outputs)

C5-S2 produces exactly one artifact type:

### Learning Suggestion

```yaml
learning_suggestion:
  id: "LS-{uuid}"
  version: 1
  created_at: "2025-12-28T12:00:00Z"
  scenario: "C5-S2"
  observation_window:
    start: "2025-12-21T00:00:00Z"
    end: "2025-12-28T00:00:00Z"
  observed_pattern:
    signal_id: "S2-F1"
    signal_name: "Repeated Same-Parameter Rejection"
    description: "Parameter 'retry_backoff' rejected 6 times"
  supporting_evidence:
    audit_record_ids:
      - "audit-001"
      - "audit-002"
      - "audit-003"
    conflicting_envelope_classes:
      - "COST"
      - "RELIABILITY"
    conflicting_parameter: "retry_backoff"
  suggestion:
    type: "advisory"
    text: "Envelope 'retry_backoff' was rejected 6 times due to same-parameter conflicts. Consider consolidating control into a single envelope."
  status: "pending_review"
  human_action: null
  applied: false
```

### Allowed Language (Suggestion Text)

| Allowed | Example |
|---------|---------|
| Observational | "Pattern observed..." |
| Conditional | "Consider reviewing..." |
| Neutral | "This conflict has occurred X times" |
| Evidence-based | "Audit records show..." |

### Forbidden Language (Hard Boundary)

| Forbidden | Reason |
|-----------|--------|
| Imperative | "Should consolidate", "Must redesign" |
| Recommending | "System recommends changing" |
| Priority suggestions | "Change priority to X" |
| Auto-resolution | "Merge these envelopes" |
| Action-oriented | "Disable this envelope" |

**Enforcement:** CI-C5-1 (Learning outputs are advisory only)

---

## 6. Hard Invariants (Non-Negotiable)

### I-C5-S2-1 - Advisory Only

C5-S2 **cannot** apply changes.

```python
# FORBIDDEN
if rejection_count > 5:
    disable_envelope()
```

### I-C5-S2-2 - No Priority Suggestions

Learning **cannot recommend** changing priority order.

```python
# FORBIDDEN
suggest_priority_change()
```

### I-C5-S2-3 - No Auto-Resolution

No auto-merge, auto-disable, or auto-redesign.

```python
# FORBIDDEN
auto_merge_envelopes()
```

### I-C5-S2-4 - No System Memory Mutation

Suggestions do not alter envelopes, schemas, or configs.

```python
# FORBIDDEN
rank_envelopes_by_conflict_score()
```

### I-C5-S2-5 - Replay Independence

Replaying without C5 produces identical system behavior.

### I-C5-S2-6 - Kill-Switch Independence

Kill-switch has zero dependency on learning.

---

## 7. What C5-S2 Must NOT Do (Non-Goals)

| Forbidden Action | Reason | Enforcement |
|------------------|--------|-------------|
| Suggest priority changes | Crosses into control | CI-C5-2 |
| Merge or consolidate envelopes | Autonomous mutation | CI-C5-2 |
| Disable conflicting envelopes | Bypasses coordination | CI-C5-2 |
| Rank envelopes by "quality" | Implies authority | CI-C5-1 |
| Trigger kill-switch | Safety isolation | CI-C5-6 |
| Auto-approve suggestions | Human gate bypass | CI-C5-2 |
| Access runtime tables | Metadata boundary | CI-C5-3 |

If any of these occur, C5-S2 certification is immediately invalid.

---

## 8. Human Approval Model (Strict)

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

### Human Actions (All Require Explicit Click)

| Action | Effect |
|--------|--------|
| Acknowledge | Marks as seen, no system change |
| Dismiss | Marks as rejected, no system change |
| Mark Applied | Human indicates they changed something |

### What "Mark Applied" Does NOT Do

- Does NOT modify any envelope
- Does NOT change any priority
- Does NOT merge any envelopes
- Only records that human took external action

**Enforcement:** CI-C5-2 (No learned change applies without approval flag)

---

## 9. Suggestion Versioning (Mandatory)

All suggestions must be:

| Requirement | Implementation |
|-------------|----------------|
| Immutable | Once created, never modified |
| Versioned | `version` field, starts at 1 |
| Timestamped | `created_at` field |
| Linked | `id` field, UUID |
| Evidence-linked | `supporting_evidence.audit_record_ids` |
| Auditable | Stored in `learning_suggestions` table |

**Enforcement:** CI-C5-4 (All learned suggestions are versioned)

---

## 10. Learning Disable Flag (Required)

C5-S2 must check `LEARNING_ENABLED` flag before execution:

```python
if not config.learning_enabled:
    log.info("Learning disabled, skipping C5-S2")
    return
```

When disabled:
- No observations collected
- No suggestions generated
- Coordination continues unchanged
- No error, no warning, silent skip

**Enforcement:** CI-C5-5 (Learning disable flag exists and works)

---

## 11. Kill-Switch Isolation (Mandatory)

C5-S2 must have **zero imports** from:
- `optimization/killswitch.py`
- `optimization/coordinator.py`
- Any runtime coordination modules

Learning and control are **completely separate**.

**Enforcement:** CI-C5-6 (Kill-switch behavior unchanged by learning)

---

## 12. Relationship to Other Phases

| Phase | Relationship |
|-------|--------------|
| C3 | C5-S2 never touches envelopes directly |
| C4 | C5-S2 only observes coordination outcomes |
| C5-S1 | S1 observes rollback frequency; S2 observes coordination friction |
| C5-S3 | S3 adds cost/reliability effectiveness; S2 stays structural |

### S1 vs S2 Comparison

| Aspect | S1 | S2 |
|--------|----|----|
| Observes | Rollback frequency | Coordination friction |
| Indicates | Bounds too aggressive | Structural design issues |
| Signals | High revert rate | Repeated rejections, oscillation |
| Window | 24h default | 7d default |
| Evidence | Rollback counts | Audit record chains |

---

## 13. Why C5-S2 Is Locked

C5-S2 becomes dangerous if rushed because it *feels* like it knows what to fix.

Locking ensures:
- Humans remain designers
- Learning remains descriptive
- Coordination remains deterministic

---

## 14. Exit Condition (Future)

C5-S2 may be **unlocked for implementation only if**:

| Condition | Status |
|-----------|--------|
| C5-S1 has >= 2 stable cycles | PENDING |
| No envelope redesign was auto-applied | PENDING |
| Humans consistently agree with S1 suggestions | PENDING |
| Re-certification rules are in place | READY |
| S2 design frozen | DRAFT |

---

## 15. Test Scenarios (Design Only)

| Scenario | Description | Expected Outcome |
|----------|-------------|------------------|
| S2-T1 | No friction in window | No suggestion generated |
| S2-T2 | Single rejection | No suggestion (below threshold) |
| S2-T3 | Repeated same-parameter rejection | S2-F1 suggestion generated |
| S2-T4 | Priority oscillation detected | S2-F2 suggestion generated |
| S2-T5 | Class friction detected | S2-F3 suggestion generated |
| S2-T6 | Learning disabled | No observation, no suggestion |
| S2-T7 | Human acknowledges | Status changes, no system change |
| S2-T8 | Human dismisses | Status changes, no system change |
| S2-T9 | Suggestion immutability | Update rejected |
| S2-T10 | Kill-switch isolation | Zero imports verified |

---

## 16. Implementation Order (When Unlocked)

| Step | Description | Status |
|------|-------------|--------|
| 1 | Freeze C5-S2 design | DRAFT |
| 2 | Define acceptance criteria | PENDING |
| 3 | Create s2_friction.py module | LOCKED |
| 4 | Implement pattern detection | LOCKED |
| 5 | Implement suggestion generation | LOCKED |
| 6 | Add tests (S2-T1 to S2-T10) | LOCKED |
| 7 | C5-S2 certification | LOCKED |

---

## 17. Re-Certification Triggers

C5-S2 certification becomes invalid if:

| Trigger | Severity |
|---------|----------|
| Suggestion becomes non-advisory | CRITICAL |
| Priority change suggested | CRITICAL |
| Auto-resolution code appears | CRITICAL |
| Human approval gate bypassed | CRITICAL |
| Kill-switch imports appear | CRITICAL |
| Suggestion mutated after creation | HIGH |
| Learning runs when disabled | HIGH |
| Forbidden language appears | MEDIUM |

---

## 18. Final Verdict

- **C5-S2 is a mirror, not a brain**
- **It diagnoses friction, not resolves it**
- **It strengthens human judgment, not replaces it**

---

## Related Documents

| Document | Purpose |
|----------|---------|
| PIN-232 | C5 Entry Conditions |
| C5_CI_GUARDRAILS_DESIGN.md | CI enforcement rules |
| C5_S1_LEARNING_SCENARIO.md | S1 design (reference) |
| C5_S1_CERTIFICATION_STATEMENT.md | S1 certification |
| C5_S2_ACCEPTANCE_CRITERIA.md | Pass/fail criteria |
