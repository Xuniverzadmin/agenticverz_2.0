# Transaction Coordination Rationale

**Date:** 2026-01-25
**Reference:** PIN-470, SWEEP_01_TRANSACTION_BYPASS_LOG.md
**Status:** RATIFIED

## The Invariant

> **Only L4 Runtime Coordinators may call commit/rollback.**

This document explains the real-world implications of this architectural decision.

---

## Example Flow: Activity Run → Incident Capture

Consider this common execution path:

```
Activity Run
    ↓
Policy Violation Detected
    ↓
Incident Captured (LLM failure)
    ↓
Logs Stored
    ↓
Analytics Updated
    ↓
Account Notified
```

---

## Before: Distributed Commits (Anti-Pattern)

```
Activity Run
    ↓
Policy Violation Detected
    → driver.commit() ✓  [Transaction 1 - committed]
    ↓
Incident Captured
    → driver.commit() ✓  [Transaction 2 - committed]
    ↓
Logs Stored
    → driver.commit() ✓  [Transaction 3 - committed]
    ↓
Analytics Updated
    → driver.commit() ✗  [Transaction 4 - FAILS]
    ↓
Account Notification
    → never reached
```

### Problem

You now have:
- Policy violation ✓ recorded
- Incident ✓ recorded
- Logs ✓ recorded
- Analytics ✗ missing (doesn't know about the incident)
- Notification ✗ never sent

### Result

**Inconsistent state.** The incident exists but analytics dashboards don't show it. Support gets tickets about "missing data." The system has silently lied about the state of the world.

---

## After: L4 Coordinated Transaction (Correct Pattern)

```
L4 Transaction Coordinator: BEGIN
    ↓
Activity Run
    ↓
Policy Violation Detected
    → session.add() + flush()  [staged, not committed]
    ↓
Incident Captured
    → session.add()  [staged, not committed]
    ↓
Logs Stored
    → session.add()  [staged, not committed]
    ↓
Analytics Updated
    → session.add() ✗  [FAILS]
    ↓
L4 Transaction Coordinator: ROLLBACK (automatic)
```

### Result

**Everything rolls back.** The system stays consistent - nothing half-recorded. The failure is visible and can be retried.

---

## Trade-off Analysis

| Aspect | Before (Distributed) | After (L4 Coordinated) |
|--------|---------------------|------------------------|
| Partial success | Yes (dangerous) | No (all-or-nothing) |
| Data consistency | Risk of orphans | Always consistent |
| Failure visibility | Hidden gaps | Explicit failure |
| Retry semantics | Complex (what already committed?) | Simple (retry entire flow) |
| Performance | Faster per-step | Slightly longer transaction |

---

## Real-World Scenario

**Scenario:** LLM call fails, triggering policy violation + incident

### Old behavior (distributed commits):

```
1. Policy violation committed ✓
2. Incident committed ✓
3. Trace logging fails (disk full)
4. Analytics never updated
5. User sees incident in UI but no trace, no cost impact shown
```

**User experience:** Confused. Data appears incomplete. Trust erodes.

### New behavior (L4 coordinated):

```
1. Policy violation staged
2. Incident staged
3. Trace logging fails (disk full)
4. L4 ROLLBACK - everything reverts
5. System logs: "Transaction failed: disk full"
6. Retry job picks up the original event
7. Disk cleared, retry succeeds
8. User sees complete, consistent data
```

**User experience:** Either sees complete data or sees nothing (with clear error). Trust maintained.

---

## Key Insight

> **The old way hid failures. The new way makes them visible.**

When analytics doesn't update, the old system silently had a data gap. The new system fails loudly and can be retried. This is the "truth-grade system" principle:

> **The system cannot lie about what happened.**

The L4 coordinator now owns the question: *"Did this entire business operation succeed?"* — not each layer independently guessing.

---

## Layer Responsibilities

| Layer | Transaction Role | Allowed Operations |
|-------|------------------|-------------------|
| L5 Engine | Business logic only | `session.add()`, `session.flush()` |
| L6 Driver | Data access only | `session.add()`, `session.execute()` |
| L4 Coordinator | Transaction boundary owner | `session.commit()`, `session.rollback()` |

### Why flush() is allowed

`flush()` sends data to the database but keeps the transaction open. This allows:
- Getting auto-generated IDs (for foreign key references)
- Validating constraints before final commit
- Rolling back everything if later steps fail

```python
# L6 Driver - correct pattern
session.add(incident)
session.flush()  # Get incident.id for use in logs
session.refresh(incident)
# NO COMMIT — L4 coordinator owns transaction boundary
```

---

## Enforcement

All files in `hoc/cus/` now include:

```python
# Forbidden: session.commit(), session.rollback() — L{x} DOES NOT COMMIT
```

Legitimate commit locations:

```
app/hoc/cus/hoc_spine/orchestrator/handlers/*_handler.py  (L4 handlers)
```

Note: The original `L4_runtime/transaction_coordinator.py` pattern has been replaced
by per-domain L4 handlers that own transaction boundaries for their operations.
See PIN-520 for migration details.

---

## Summary

| Metric | Value |
|--------|-------|
| Violations eliminated | 101 → 0 |
| Pattern | All-or-nothing transactions |
| Benefit | Data consistency guaranteed |
| Trade-off | Slightly longer transactions |
| Principle | Truth-grade system - no silent failures |

---

## References

- `SWEEP_01_TRANSACTION_BYPASS_LOG.md` - Elimination progress
- `HOC_LAYER_TOPOLOGY_V1.md` - Layer definitions
- PIN-470 - HOC Architecture
