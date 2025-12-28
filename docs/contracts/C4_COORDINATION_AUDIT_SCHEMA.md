# C4 Coordination Audit Schema

**Version:** 1.0
**Status:** DESIGN
**Created:** 2025-12-28
**Reference:** PIN-232, C4_ENVELOPE_COORDINATION_CONTRACT.md

---

## 1. Purpose

This document defines the persistence schema for C4 coordination audit records.

**Problem:** C4 coordination decisions are certified but only exist in-memory.
**Solution:** Persist audit records to enable C5 learning observability.

**Key Constraint:** This change adds observability only. It does NOT change C4 behavior.

---

## 2. Design Principles

| Principle | Requirement |
|-----------|-------------|
| Append-only | Records are INSERT only, never UPDATE |
| Immutable | Core fields cannot be modified after creation |
| Synchronous | Written in same transaction as coordination decision |
| Isolated | No learning imports in C4 code |
| Replay-safe | Audit emission respects `emit_traces` flag |
| Non-blocking | Audit failure does not block coordination |

---

## 3. Table Schema

### `coordination_audit_records`

```sql
CREATE TABLE coordination_audit_records (
    -- Primary key
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Envelope identification
    envelope_id VARCHAR(100) NOT NULL,
    envelope_class VARCHAR(20) NOT NULL,

    -- Decision outcome
    decision VARCHAR(20) NOT NULL,
    reason TEXT NOT NULL,

    -- Timing
    decision_timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Conflict context (nullable)
    conflicting_envelope_id VARCHAR(100),
    preempting_envelope_id VARCHAR(100),

    -- State snapshot
    active_envelopes_count INTEGER NOT NULL DEFAULT 0,

    -- Multi-tenancy (optional)
    tenant_id VARCHAR(100),

    -- Constraints
    CONSTRAINT audit_envelope_class_valid CHECK (
        envelope_class IN ('SAFETY', 'RELIABILITY', 'COST', 'PERFORMANCE')
    ),
    CONSTRAINT audit_decision_valid CHECK (
        decision IN ('APPLIED', 'REJECTED', 'PREEMPTED')
    )
);
```

### Indexes

```sql
-- Query by envelope
CREATE INDEX ix_coord_audit_envelope_id ON coordination_audit_records(envelope_id);

-- Query by time window (C5-S1 observation)
CREATE INDEX ix_coord_audit_timestamp ON coordination_audit_records(decision_timestamp);

-- Query by class (C5-S1 aggregation)
CREATE INDEX ix_coord_audit_class ON coordination_audit_records(envelope_class);

-- Query by decision type
CREATE INDEX ix_coord_audit_decision ON coordination_audit_records(decision);

-- Multi-tenant queries
CREATE INDEX ix_coord_audit_tenant ON coordination_audit_records(tenant_id);
```

---

## 4. Immutability Guarantees

### Trigger: Prevent Audit Mutation

```sql
CREATE OR REPLACE FUNCTION prevent_audit_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'coordination_audit_records are immutable. Updates forbidden.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER coordination_audit_immutable
    BEFORE UPDATE ON coordination_audit_records
    FOR EACH ROW
    EXECUTE FUNCTION prevent_audit_mutation();
```

### No DELETE Policy

Deletes are prevented by application-level policy:
- No DELETE endpoints exposed
- No DELETE in any C4/C5 code
- CI guardrail checks for DELETE patterns

---

## 5. Write Path

### Where Audit Records Are Emitted

```
CoordinationManager.check_allowed()
    └─> CoordinationDecision (allow/reject/preempt)
        └─> emit_audit_record()  ← NEW
            └─> INSERT INTO coordination_audit_records
```

### Emit Logic (Pseudocode)

```python
def emit_audit_record(
    envelope: Envelope,
    decision: CoordinationDecision,
    active_count: int,
    emit_traces: bool = True,  # Respects replay flag
) -> None:
    """
    Persist coordination audit record.

    MUST be called synchronously within coordination decision.
    MUST NOT import from app.learning (isolation).
    MUST respect emit_traces flag (replay safety).
    """
    if not emit_traces:
        return  # Skip during replay

    record = CoordinationAuditRecord(
        audit_id=str(uuid.uuid4()),
        envelope_id=envelope.id,
        envelope_class=envelope.envelope_class,
        decision=decision.decision_type,
        reason=decision.reason,
        timestamp=datetime.now(timezone.utc),
        conflicting_envelope_id=decision.conflicting_id,
        preempting_envelope_id=decision.preempting_id,
        active_envelopes_count=active_count,
    )

    # Synchronous insert (same transaction)
    db.execute(insert(coordination_audit_records).values(...))
```

---

## 6. Isolation Requirements

### C4 → Audit (Allowed)

```
app/optimization/coordinator.py
    └─> WRITES TO coordination_audit_records  ✅
```

### C5 → Audit (Allowed, Read-Only)

```
app/learning/s1_rollback.py
    └─> READS FROM coordination_audit_records  ✅
```

### Audit → C4 (Forbidden)

```
coordination_audit_records
    └─> MUST NOT influence CoordinationManager  ❌
```

### C5 → C4 (Forbidden)

```
app/learning/*
    └─> MUST NOT import from app/optimization/coordinator  ❌
    └─> MUST NOT import from app/optimization/killswitch  ❌
```

---

## 7. Replay Safety

### The Problem

During replay:
- Coordination decisions are re-evaluated
- But we don't want duplicate audit records

### The Solution

Audit emission respects the existing `emit_traces` flag:

```python
if not emit_traces:
    return  # Skip audit during replay
```

This is consistent with how traces and other side effects are handled.

---

## 8. Failure Handling

### Audit Write Failure

If audit INSERT fails:
- Log error
- Continue coordination (do NOT block)
- Increment `coordination_audit_failures` metric

Rationale: Coordination correctness > audit completeness.

### Mitigation

- Retry logic (1 retry, 100ms delay)
- Dead-letter logging for failed audits
- Alert on failure rate > 1%

---

## 9. C4 Re-Certification Scope

### What Changes

| Change | Impact |
|--------|--------|
| New table | Schema only |
| New trigger | Immutability enforcement |
| New function | `emit_audit_record()` |
| Coordinator modification | Adds audit emission call |

### What Does NOT Change

| Invariant | Status |
|-----------|--------|
| C4 coordination logic | Unchanged |
| Priority ordering | Unchanged |
| Same-parameter rejection | Unchanged |
| Kill-switch behavior | Unchanged |
| Replay determinism | Unchanged |

### Re-Certification Criteria

1. All existing C4 tests pass
2. New audit emission tests pass
3. Replay produces no audit duplicates
4. Audit failure does not block coordination
5. CI-C4-* guardrails still pass

---

## 10. CI Guardrails (New)

### CI-C4-7: Audit Immutability

```bash
# No UPDATE on coordination_audit_records
grep -rn "UPDATE.*coordination_audit_records" backend/ | grep -v "__pycache__"
# Expected: 0 matches
```

### CI-C4-8: Audit Isolation

```bash
# No learning imports in coordinator
grep -rn "from app.learning" backend/app/optimization/
# Expected: 0 matches
```

### CI-C4-9: Audit Replay Safety

```bash
# emit_audit_record respects emit_traces
grep -n "emit_traces" backend/app/optimization/coordinator.py
# Expected: emit_traces check before audit emission
```

---

## 11. Migration Plan

### Migration: `063_c4_coordination_audit.py`

```python
"""
C4 Coordination Audit Persistence.

Adds coordination_audit_records table for C5 learning observability.
Does NOT change C4 coordination behavior.

Reference: C4_COORDINATION_AUDIT_SCHEMA.md, PIN-232
"""

def upgrade():
    # 1. Create table
    # 2. Create indexes
    # 3. Create immutability trigger

def downgrade():
    # 1. Drop trigger
    # 2. Drop table
```

---

## 12. Acceptance Criteria

| ID | Criterion | Test |
|----|-----------|------|
| AC-A1 | Table exists | `\d coordination_audit_records` |
| AC-A2 | Immutability trigger exists | Attempt UPDATE, expect exception |
| AC-A3 | Indexes exist | `\di *coord_audit*` |
| AC-A4 | Coordinator emits audits | Run coordination, query table |
| AC-A5 | Replay skips audits | Run replay, verify no duplicates |
| AC-A6 | Audit failure non-blocking | Mock failure, verify coordination continues |
| AC-A7 | C4 tests pass | `pytest tests/optimization/` |
| AC-A8 | C5-S1 can read audits | Query from RollbackObserver |

---

## 13. Status

| Step | Status |
|------|--------|
| Schema design | ✅ COMPLETE |
| Contract drafted | ✅ COMPLETE |
| Migration | ✅ COMPLETE (063_c4_coordination_audit) |
| Coordinator wiring | ✅ COMPLETE (audit_persistence.py) |
| CI Guardrails | ✅ COMPLETE (CI-C4-7/8/9, 9/9 passing) |
| C4 re-certification | ✅ COMPLETE (14/14 tests pass) |
| C5-S1 unlock | ✅ READY |

---

## 14. References

- PIN-232: C5 Entry Conditions
- C4_ENVELOPE_COORDINATION_CONTRACT.md
- C5_S1_ACCEPTANCE_CRITERIA.md
- LESSONS_ENFORCED.md (L-007: emit_traces flag)
