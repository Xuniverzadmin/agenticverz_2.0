# Recovery Semantic Contract

**Status:** ✅ APPROVED — FROZEN
**Phase:** 3.4 (CLOSED 2025-12-30)
**Approved:** 2025-12-30
**Created:** 2025-12-30
**Predecessor:** WORKER_LIFECYCLE_SEMANTIC_CONTRACT.md

---

## Purpose

This contract defines the **semantic meaning** of recovery in AOS.

**Core Principle:**
> Recovery is not retry. Recovery is a **deliberate, bounded, traceable transformation** from a failed state to a known-good state with full provenance.

---

## Semantic Axes (4 Axes)

### Axis 1: Representation (WHAT)

**Question:** What does recovery represent?

| Concept | Semantic Meaning |
|---------|------------------|
| Recovery Candidate | A potential recovery action for a failure, with confidence and provenance |
| Recovery Action | A defined template for recovery behavior (retry, fallback, escalate, etc.) |
| Recovery Scope | A bounded execution context with cost, time, and attempt limits |
| Provenance | Complete lineage of how a recovery decision was made and executed |
| Orphan | A run stuck in non-terminal state due to system crash |

**Key Distinction:**
- **Candidate** = potential (awaiting decision or execution)
- **Action** = template (defines what recovery does)
- **Scope** = boundary (defines where recovery is allowed)
- **Provenance** = audit trail (records what happened)

### Axis 2: Authority (WHO OWNS WHAT)

**Question:** Who has authority over what state?

| Authority Holder | Owns | Cannot Touch |
|------------------|------|-----------------|
| RecoveryMatcher | Candidate creation, confidence scoring | Action execution, run state |
| RecoveryEvaluator | Suggestion generation, action selection | Candidate approval, scope creation |
| RecoveryClaimWorker | Candidate claiming (pending → executing) | Candidate creation, action templates |
| RecoveryRuleEngine | Rule evaluation, action recommendation | Candidate state, execution results |
| OrphanRecovery | Orphan detection, crash marking | Run execution, historical mutation |
| ScopedExecution | Scope creation, execution gating | Candidate state, run completion |
| Human Reviewer | Approval decisions (pending → approved/rejected) | Direct execution, confidence scoring |

**Authority Rule:**
> Recovery authority is scoped. No single component owns the entire recovery lifecycle.

### Axis 3: Lifecycle (WHEN)

**Question:** What are the lifecycle states and their semantic meaning?

#### Recovery Candidate States

| State | Semantic Meaning | Transition Authority |
|-------|------------------|---------------------|
| `pending` | Candidate created, awaiting decision | Matcher (creation) |
| `approved` | Human approved for execution | Human Reviewer |
| `rejected` | Human rejected, will not execute | Human Reviewer |
| `executing` | Execution in progress | ClaimWorker |
| `succeeded` | Recovery action completed successfully | Evaluator |
| `failed` | Recovery action failed | Evaluator |
| `rolled_back` | Recovery action was reversed | Evaluator |
| `skipped` | Candidate skipped (policy decision) | Evaluator |

**State Semantics:**

1. **pending** — Awaiting decision
   - Candidate exists with confidence score
   - No execution has occurred
   - Can be approved or rejected

2. **approved** — Execution authorized
   - Human has approved this recovery
   - Ready for execution (within scope)
   - Audit trail records approver

3. **rejected** — Execution denied
   - Human has rejected this recovery
   - Will not execute
   - Terminal state

4. **executing** — In progress
   - Worker has claimed this candidate
   - Execution underway
   - Exactly-once guard active

5. **succeeded** — Recovery worked
   - Action completed successfully
   - Provenance recorded
   - Terminal state

6. **failed** — Recovery did not work
   - Action failed
   - Error recorded
   - Terminal state (may create new candidate)

7. **rolled_back** — Recovery reversed
   - Compensating action taken
   - Original state restored
   - Terminal state

8. **skipped** — Deliberately not executed
   - Policy decision to skip
   - May be scope exhaustion or low confidence
   - Terminal state

#### Execution Scope States

| State | Semantic Meaning |
|-------|------------------|
| `active` | Scope is valid, attempts remaining |
| `exhausted` | Max attempts reached, no more executions |
| `expired` | TTL exceeded, scope invalid |
| `revoked` | Administratively cancelled |

### Axis 4: Guarantees (WHAT IS PROMISED)

**Question:** What guarantees does recovery provide?

| Guarantee | Scope | Mechanism |
|-----------|-------|-----------|
| Exactly-once execution | Per candidate | `UPDATE ... WHERE executed_at IS NULL RETURNING` |
| Provenance completeness | Per candidate | Provenance events recorded at each transition |
| Scope enforcement | Per execution | Scope validation before every execution |
| At-least-once evaluation | Per candidate | Retry on claim failure |
| Orphan detection | Per startup | Threshold-based detection on worker start |
| No silent loss | Per crash | PB-S2 guarantee (crashed runs marked, not lost) |

---

## Recovery Action Types

### Corrective Actions (Fix the Problem)

Actions that attempt to restore normal operation:

| Action Type | Semantic Meaning | Example |
|-------------|------------------|---------|
| `retry` | Attempt the same operation again | retry_exponential |
| `fallback` | Switch to alternative approach | fallback_model |
| `circuit_breaker` | Temporarily disable to allow recovery | circuit_breaker |
| `reconfigure` | Apply configuration change | reconfigure |
| `rollback` | Revert to previous known-good state | rollback |

### Compensating Actions (Mitigate Impact)

Actions that manage the impact without fixing the root cause:

| Action Type | Semantic Meaning | Example |
|-------------|------------------|---------|
| `escalate` | Escalate to higher authority | escalate_to_ops |
| `notify` | Alert stakeholders | notify_ops |
| `manual` | Flag for manual intervention | manual_intervention |
| `skip` | Skip and continue workflow | skip_step |

**Semantic Distinction:**
```
Corrective: "I will fix the problem"
Compensating: "I will manage the impact while you fix the problem"
```

---

## Allowed vs Forbidden Mutations

### ALLOWED Mutations

| Mutation | Semantic Justification |
|----------|----------------------|
| Candidate status transitions | Lifecycle progression is expected |
| Confidence score updates | Refinement based on new evidence |
| Decision recording (approved/rejected) | Human authority exercised |
| Provenance event insertion | Audit trail accumulation |
| Execution result recording | Outcome capture |
| Orphan marking (→ crashed) | Factual status (run DID crash) |
| NEW retry run creation | PB-S1 compliant (new run, not mutation) |

### FORBIDDEN Mutations

| Mutation | Why Forbidden |
|----------|--------------|
| Historical execution data | Violates S1/S6 truth guarantees |
| Completed run modification | Terminal states are immutable |
| Provenance deletion | Audit trail must be append-only |
| Silent crash loss | PB-S2 requires explicit crash marking |
| Multiple executions of same candidate | Exactly-once guarantee violation |
| Execution without valid scope | M6 invariant violation |

**The Line:**
```
Recording facts about recovery = ALLOWED
Rewriting history about execution = FORBIDDEN
```

---

## Eventual Consistency Guarantees

### EC-1: Terminal State Convergence

Every recovery candidate eventually reaches a terminal state.

**Terminal States:** `succeeded`, `failed`, `rolled_back`, `skipped`, `rejected`

**Mechanism:** Worker retry on failure, claim timeout handling

### EC-2: Orphan Detection Completeness

Every orphaned run is eventually detected and marked.

**Mechanism:** Threshold-based detection on worker startup

**Threshold:** ORPHAN_THRESHOLD_MINUTES (default: 30)

### EC-3: Provenance Completeness

Every significant recovery event is eventually recorded in provenance.

**Events Recorded:**
- `created` - Candidate creation
- `rule_evaluated` - Rule evaluation completed
- `action_selected` - Action chosen
- `approved` / `rejected` - Human decision
- `executed` - Execution started
- `success` / `failure` - Outcome recorded
- `rolled_back` - Rollback completed
- `manual_override` - Manual intervention

### EC-4: Scope Exhaustion

Every active scope eventually becomes inactive (exhausted, expired, or revoked).

**Mechanisms:**
- Attempt counting (max_attempts)
- TTL expiration (ttl_seconds)
- Administrative revocation

---

## Prohibitions

### P1: No Execution Without Scope (M6 Invariant)

> "A recovery action without a valid execution scope is invalid by definition."

**Enforcement:**
- API validates scope_id before execution
- Scope must be active (not exhausted/expired/revoked)
- Action must match scope's allowed_actions
- Incident must match scope's incident_id

### P2: No Historical Mutation

Recovery CANNOT modify historical execution data.

**Enforcement:**
- DB triggers reject trace mutation
- Run completion is final
- Provenance is append-only

### P3: No Silent Loss (PB-S2)

Crashed runs are never silently lost.

**Enforcement:**
- OrphanRecovery runs on startup
- Orphans marked as `crashed`
- Operator visibility via logs

### P4: No Duplicate Execution

Each candidate executes at most once.

**Enforcement:**
- `UPDATE ... WHERE executed_at IS NULL RETURNING id`
- First claim wins, subsequent claims get nothing
- Exactly-once side-effect guarantee

### P5: No Auto-Execution Without Gate

Automated execution requires:
- `is_automated = True` AND
- `requires_approval = False` AND
- `confidence >= 0.8` AND
- Valid execution scope

---

## Ambiguities Resolved

### Ambiguity 1: What is "recovery" vs "retry"?

**Resolution:**
- **Recovery** = Deliberate, bounded, traceable transformation with provenance
- **Retry** = One possible recovery action (retry_exponential)

Recovery is the semantic concept. Retry is one implementation.

### Ambiguity 2: When does a candidate become "executed"?

**Resolution:** When a worker successfully claims it via the exactly-once guard.

The moment `UPDATE ... WHERE executed_at IS NULL` returns a row, execution has begun.

### Ambiguity 3: What happens to orphaned runs?

**Resolution:** They are marked as `crashed` (factual status), not mutated.

Recovery for orphans = creating a NEW retry run, not modifying the crashed run.

### Ambiguity 4: Who decides if recovery should auto-execute?

**Resolution:** The SuggestionAction catalog + confidence threshold + scope validity.

Three gates must pass:
1. Action is marked automated and doesn't require approval
2. Confidence meets threshold (>= 0.8)
3. Valid execution scope exists

---

## Invariants

### RI-1: Provenance Monotonicity

Provenance events can only be added, never removed or modified.

### RI-2: Terminal State Finality

Terminal states (`succeeded`, `failed`, `rolled_back`, `skipped`, `rejected`) are permanent.

### RI-3: Confidence Bounds

`0.0 <= confidence <= 1.0` always.

### RI-4: Scope Attempt Monotonicity

`attempts_used` can only increase, never decrease.

### RI-5: Idempotency Key Uniqueness

No two candidates with the same `(failure_match_id, error_signature)` can exist in non-terminal state.

---

## File Inventory

| File | Layer | Role | SSA Status |
|------|-------|------|------------|
| `worker/recovery_claim_worker.py` | L5 | Candidate claiming and processing | MATCH |
| `worker/recovery_evaluator.py` | L5 | Failure evaluation and suggestion | MATCH |
| `services/recovery_rule_engine.py` | L4 | Rule-based action recommendation | MATCH |
| `services/recovery_matcher.py` | L4 | Pattern matching and confidence | MATCH |
| `services/orphan_recovery.py` | L4 | Orphan detection (PB-S2) | MATCH |
| `services/recovery_write_service.py` | L4 | DB write delegation | MATCH |
| `api/recovery.py` | L2 | REST API for recovery operations | - |
| `api/recovery_ingest.py` | L2 | Failure ingestion endpoint | - |
| `tasks/recovery_queue.py` | L5 | Redis queue for evaluation tasks | - |
| `models/m10_recovery.py` | L6 | Recovery data models | - |

---

## References

- WORKER_LIFECYCLE_SEMANTIC_CONTRACT.md: Worker lifecycle semantics
- EXECUTION_SEMANTIC_CONTRACT.md: Execution model guarantees
- PIN-199: PB-S1/S2 Implementation (retry immutability, crash recovery)
- PIN-240: M10 Recovery Rule Engine
- PIN-242: Baseline Freeze
- PIN-250: Phase 2B Write Service Extraction
- PIN-251: Phase 3 Semantic Alignment

---

## Session Handoff

**Status:** ✅ APPROVED — FROZEN (2025-12-30)

> **PHASE 3.4 CLOSED:** This contract is now frozen and immutable.
> Recovery semantics are locked. Future changes require formal amendment process.

**Ratification Sequence (COMPLETE):**
1. ✅ Discovery notes produced (6 recovery files analyzed)
2. ✅ Phase 3.4 formally entered with scope constraint
3. ✅ 4 Semantic Axes documented
4. ✅ Allowed vs Forbidden Mutations codified
5. ✅ Corrective vs Compensating distinguished
6. ✅ Eventual Consistency Guarantees specified (EC-1 to EC-4)
7. ✅ SSA executed: 6/6 core files MATCH
8. ✅ Final review: No semantic gaps within scope
9. ✅ APPROVED and FROZEN

**Approval Notes:**
- Recovery semantics define MEANING only, not transaction ownership
- All write authority questions deferred to Phase 3.5
- Semantic Auditor remains observational
- No authority leaks occurred
- Boundaries with Phase 3.3 (Workers) and Phase 3.5 (Transactions) clean

**Scope Constraint Honored:**
- ✅ Defined MEANING of recovery
- ✅ Did NOT define transaction ownership (→ Phase 3.5)
- ✅ No code changes proposed
