# PIN-198 — Acceptance Gate: Trace Integrity Truth (S6)

**Status:** ACCEPTED (constitutional)
**Phase:** A.5
**Scenario:** S6 — Trace Integrity
**Objective:** Prove that **system history is immutable, causally ordered, replayable, and audit-faithful**.
**Created:** 2025-12-26
**Frozen:** 2025-12-26

---

## CONSTITUTIONAL NOTICE

> **This PIN is FROZEN. No edits permitted.**
>
> PIN-198 documents the S6 acceptance gate that passed 31/31 checks.
> Any future trace-related changes require a **new gate** (S6.1+).
>
> Related frozen artifacts:
> - Migration `052_s6_trace_immutability.py` — DB triggers, never edit in place
> - `runtime/replay.py` — `emit_traces=False` default, never change
> - `pg_store.py` — `ON CONFLICT DO NOTHING` semantics, never revert to `DO UPDATE`
>
> See LESSONS_ENFORCED.md Invariants #13, #14, #15.

---

If S4 proved "the system tells the truth when it fails" and S5 proved "the system knows what it remembers," then S6 proves:

> **The system cannot lie about what happened, in what order, or why.**

---

## 1. Scope (Hard Boundary)

### Included

* Trace persistence (authoritative history)
* Causal ordering (parent → child)
* Replay determinism
* Trace ↔ run ↔ memory ↔ incident linkage
* Restart durability
* Audit fidelity (read-only after commit)

### Explicitly Excluded

* Performance optimization
* Compression
* Sampling
* Partial trace retention
* UI embellishment

If **any excluded behavior occurs** → **FAIL (scope breach)**.

---

## 2. Trace Truth Model (Authoritative)

```
Event Occurs
   ↓
Trace Entry Appended (immutable)
   ↓
Causal Link Recorded (parent_id)
   ↓
Trace Finalized
   ↓
Replay Produces Identical Graph
```

**Critical rule:**

> A trace is a *fact ledger*, not a debug log.

---

## 3. Acceptance Criteria

### AC-0: Preconditions

| Check             | Requirement       |
| ----------------- | ----------------- |
| S1–S5             | ACCEPTED / FROZEN |
| Verification Mode | Enabled           |
| Clean slate       | No orphan traces  |

---

### AC-1: Trace Persistence (Non-Negotiable)

**Must be true**

* Every run produces ≥1 trace entry
* Each trace entry is persisted **before** run completion
* Trace entries contain:
  * trace_id
  * run_id
  * tenant_id
  * event_type
  * created_at (UTC, tz-aware)

**Missing or ephemeral traces → FAIL (P0)**

---

### AC-2: Causal Ordering

**Must be true**

* Each trace entry (except root) references a valid parent
* Parent timestamps ≤ child timestamps
* No cycles in the trace graph

**Out-of-order or cyclic traces → FAIL**

---

### AC-3: Immutability

**Must be true**

* Trace entries are append-only
* No UPDATE or DELETE allowed post-commit
* Hash or checksum stored per entry or per trace

**Trace mutation detected → FAIL (P0)**

---

### AC-4: Replay Determinism

**Must be true**

* Replaying a trace produces:
  * identical event sequence
  * identical causal graph
  * identical outcomes (success/failure classification)
* No new traces created during replay

**Replay divergence → FAIL**

---

### AC-5: Cross-Artifact Consistency

**Must be true**

* Every:
  * memory injection
  * failure
  * advisory
  * policy violation
  * incident
  references at least one trace entry
* Trace references resolve correctly

**Orphan artifacts → FAIL**

---

### AC-6: Tenant Isolation

**Must be true**

* Traces are tenant-scoped
* No cross-tenant trace visibility
* Replay restricted to same tenant

**Cross-tenant trace access → FAIL (P0)**

---

### AC-7: Restart Durability

After backend restart:

* Trace graph unchanged
* No missing entries
* No duplicated entries
* Replay still deterministic

**Drift after restart → FAIL**

---

### AC-8: Negative Assertions (Strict)

Must be true:

* No trace gaps
* No inferred trace events
* No "best effort" reconstruction
* No lazy trace creation

Any violation → **FAIL**

---

## 4. Invariants (Lessons Baked In)

These are **mechanically enforced**, not advisory.

### Invariant 1 — No Lazy Wiring

* Trace service constructed explicitly
* No hidden dependencies

### Invariant 2 — Persistence First, Always

* Trace entry persisted before any subsequent action

### Invariant 3 — Immutability Is Absolute

* No UPDATE, no DELETE, no "fixing" traces
* DB trigger enforcement

### Invariant 4 — Replay Is Pure

* Replay calls no external services
* No time/randomness during replay
* No trace emission during replay

### Invariant 5 — Tenant Boundary Is Absolute

* Trace queries always scoped by tenant_id
* No cross-tenant leakage under any condition

---

## 5. Acceptance Rule

**PASS** only if **ALL AC-0 → AC-8 pass**.

No PARTIAL.
No "expected nondeterminism."
Trace must be **truthful**, not just present.

---

## 6. Official Acceptance Statement (Template)

> **S6 acceptance passed.**
> System traces are immutable, causally ordered, replay-deterministic, and audit-faithful.
> Historical truth cannot be altered, inferred, or reconstructed inaccurately.
> Phase A.5 is COMPLETE.

---

## 7. Implementation Infrastructure

### 7.1 Trace Tables

**Expected schema:**
- `traces` or `trace_entries` table
- Columns: id, trace_id, run_id, tenant_id, parent_id, event_type, payload, checksum, created_at

### 7.2 Immutability Enforcement

**Approach:**
- DB trigger rejecting UPDATE/DELETE
- Checksum column for integrity verification

### 7.3 Verification Script

**File:** `backend/scripts/verification/s6_trace_integrity_verification.py`

---

## 8. Pre-Emptive Hardening (Before You Run S6)

Check for these 5 failure patterns:

### Pattern 1: Hidden Non-Determinism in Replay
- `uuid4()` during replay
- `utc_now()` during replay
- unordered dict iteration

### Pattern 2: Trace Gaps at Async Boundaries
- Missing events in long async flows
- Exceptions bypass trace emission

### Pattern 3: Mutable Trace Rows
- ORM allowing UPDATE
- JSONB mutation post-commit

### Pattern 4: Orphan Artifacts
- Artifacts without trace references
- Scripts bypass trace layer

### Pattern 5: Replay Re-Emits Traces
- Replaying creates new trace entries
- History grows during audit

---

## 9. What NOT to Do (Critical)

Do **not**:

* reconstruct traces from logs
* infer missing trace events
* allow "minor" trace corrections
* sample or compress traces
* skip traces for "performance"

S6 is about **historical truth**, not observability.

---

## 10. Why This Gate Is Harder Than S5

S5 tested:

> "Does the system know what it knows?"

S6 tests:

> **"Can the system prove what happened, and that no one altered it?"**

Most systems fail here by:

* allowing trace updates
* replaying with fresh IDs
* creating traces lazily

This gate forbids all of that.

---

## 11. Verification Evidence

### Execution Date: 2025-12-26

**Trace ID:** `trace_3c1a0411-b65c-45`
**Run ID:** `run_3c1a0411-b65c-45`
**Replay Hash:** `c3e0c65b796619b0`

### Check Results

| Check | Result |
|-------|--------|
| AC-0: Preconditions | ✅ PASS (3/3) |
| AC-1: Trace Persistence | ✅ PASS (5/5) |
| AC-2: Causal Ordering | ✅ PASS (1/1) |
| AC-3: Immutability | ✅ PASS (5/5) |
| AC-4: Replay Determinism | ✅ PASS (4/4) |
| AC-5: Cross-Artifact Consistency | ✅ PASS (3/3) |
| AC-6: Tenant Isolation | ✅ PASS (2/2) |
| AC-7: Restart Durability | ✅ PASS (5/5) |
| AC-8: Negative Assertions | ✅ PASS (3/3) |

**Total: 31/31 checks passed**

---

## 12. Next Steps (Exact)

1. [x] Freeze **PIN-198** ✅
2. [x] Pre-harden against 5 failure patterns ✅
   - Pattern 1 (non-determinism): OK - trace models have determinism hashing
   - Pattern 2 (trace gaps): OK - verified
   - Pattern 3 (mutable traces): FIXED - added DB triggers
   - Pattern 4 (orphan artifacts): OK - verified
   - Pattern 5 (replay re-emits): FIXED - added emit_traces=False flag
3. [x] Create verification script ✅
4. [x] Run verification script ✅
5. [x] Verify AC-0 → AC-8 ✅ (31/31 passed)
6. [x] Accept — **S6 COMPLETE** ✅
7. [x] **Phase A.5 COMPLETE** ✅

---

## 13. Related PINs

| PIN | Topic | Relationship |
|-----|-------|--------------|
| PIN-193 | Truth Propagation (S1) | Prerequisite |
| PIN-194 | Cost Advisory Truth (S2) | Prerequisite |
| PIN-195 | Policy Violation Truth (S3) | Prerequisite |
| PIN-196 | LLM Failure Truth (S4) | Prerequisite |
| PIN-197 | Memory Injection Truth (S5) | Prerequisite |

---

## 14. Changelog

| Date | Change |
|------|--------|
| 2025-12-26 | Created PIN-198 with all acceptance criteria |
| 2025-12-26 | Pre-hardened against 5 failure patterns |
| 2025-12-26 | Fixed Pattern 3: Added DB immutability triggers |
| 2025-12-26 | Fixed Pattern 5: Added emit_traces=False to replay |
| 2025-12-26 | S6 VERIFICATION PASSED (31/31 checks) |
| 2025-12-26 | Status: FROZEN → ACCEPTED (constitutional) |

---

### Bottom Line

PIN-198 makes it **impossible for your system to rewrite history**.

That's the difference between:

* an AI tool with logs
* and a governance-grade system with audit-faithful traces
