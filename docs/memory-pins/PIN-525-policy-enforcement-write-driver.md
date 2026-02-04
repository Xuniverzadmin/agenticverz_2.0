# PIN-525: PolicyEnforcementWriteDriver Implementation

**Status:** ✅ COMPLETE
**Created:** 2026-02-04
**Category:** HOC Migration / Enforcement Audit Trail

---

## Summary

Created PolicyEnforcementWriteDriver (L6) to close the gap where policy enforcement outcomes were evaluated but never persisted. Wired into step_enforcement.py to record STOP/KILL/ABORT/BLOCK outcomes to the `policy_enforcements` table.

---

## Problem Statement

The TODO audit (PIN-524 Phase 3) identified a mismatch:
- Original TODO referenced "ledger.py `record_outcome()` TransactionCoordinator"
- Investigation revealed the actual gap: `PolicyEnforcement` model exists (policy_control_plane.py:244), and `PolicyEnforcementReadDriver` exists, but **no write driver** existed

**Impact:**
- `trigger_count_30d` derivations had no data source
- `last_triggered_at` was always empty
- No audit trail of policy enforcement history

---

## Solution

### Files Created

| File | Purpose |
|------|---------|
| `app/hoc/cus/policies/L6_drivers/policy_enforcement_write_driver.py` | L6 driver for recording enforcement outcomes |

### Files Modified

| File | Change |
|------|--------|
| `app/hoc/cus/policies/L6_drivers/__init__.py` | Export new driver |
| `app/hoc/int/general/drivers/step_enforcement.py` | Wire recording into enforcement halt |

### API

```python
# Within existing session (caller owns commit)
driver = PolicyEnforcementWriteDriver(session)
await driver.record_enforcement(
    tenant_id="tenant_123",
    rule_id="rule_456",
    action_taken="BLOCKED",
    run_id="run_789",
    details={"reason": "Budget exceeded"}
)

# Fire-and-forget (creates own session, commits immediately)
from app.hoc.cus.policies.L6_drivers import record_enforcement_standalone
await record_enforcement_standalone(
    tenant_id="tenant_123",
    rule_id="rule_456",
    action_taken="STOPPED",
    run_id="run_789",
)
```

### Data Flow

```
step_enforcement.py                          policy_enforcement_write_driver.py
      |                                               |
      ↓                                               |
enforce_before_step_completion()                      |
      |                                               |
      ↓  (if STOP/KILL/ABORT/BLOCK)                  |
_record_enforcement_outcome() ──────────────────→ record_enforcement_standalone()
      |                                               |
      ↓                                               ↓
raise StepEnforcementError()               INSERT INTO policy_enforcements
```

---

## Design Decisions

1. **Fail-safe recording:** Recording failures are logged but never block enforcement. The system must halt runs even if DB write fails.

2. **Async from sync context:** `_record_enforcement_outcome()` uses `asyncio.run()` or `loop.create_task()` depending on context.

3. **Append-only:** Following PIN-412 invariant, the driver only supports INSERT, no UPDATE or DELETE.

4. **Session ownership:** When using `PolicyEnforcementWriteDriver` directly, caller owns the transaction (no commit). `record_enforcement_standalone()` creates and commits its own session.

---

## Commit

```
3f3d2f38 feat(hoc): add PolicyEnforcementWriteDriver for recording enforcement outcomes
```

---

## Tests

All enforcement tests pass:
```
tests/governance/t0/test_step_enforcement.py: 9 passed ✅
tests/governance/t0/test_enforcement_guard.py: 10 passed ✅
```

---

## Related

- PIN-524: Phase 3 Legacy Import Deprecation Complete
- PIN-523: Phase 2 BLOCKING TODO Wiring Complete
- PIN-412: Policy Enforcement Append-Only History
- GAP-016: Step Enforcement Single Choke Point
