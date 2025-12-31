# Registry Change: SIG-100 GraduationStatus

**Change ID:** RC-001
**Date:** 2025-12-31
**Status:** APPLIED
**Severity:** P1 (Semantic Integrity)

---

## Reason

Original registry classified SIG-100 as in-memory and L4-produced.
Code inspection confirms SIG-100 is a **persistent L5-produced signal**
consumed by L6 runtime feature gating and L2 APIs.

This was identified as GAP-001 in L7→L6 Sufficiency Analysis.

---

## Evidence

### Producer: graduation_evaluator.py (L5)

**File:** `backend/app/jobs/graduation_evaluator.py`

```python
# Lines 83-121: INSERT INTO graduation_history (audit trail)
await session.execute(text("""
    INSERT INTO graduation_history (
        level, gates_json, computed_at, is_degraded,
        degraded_from, degradation_reason, evidence_snapshot
    ) VALUES (...)
"""))

# Lines 124-150: UPDATE m25_graduation_status (derived state)
await session.execute(text("""
    UPDATE m25_graduation_status SET ...
"""))

# Lines 159-174: UPDATE capability_lockouts (gates features)
await session.execute(text("""
    UPDATE capability_lockouts SET is_unlocked = :is_unlocked ...
"""))

# Line 176: session.commit()
await session.commit()
```

### Consumer: L6 Runtime (capability_lockouts)

**File:** `backend/app/integrations/graduation_engine.py`

```python
class CapabilityGates:
    @staticmethod
    def can_auto_apply_recovery(status) -> bool:
        """Gate 1 required: Auto-apply recovery only after prevention proven."""
        return gate1.passed

    @staticmethod
    def can_auto_activate_policy(status) -> bool:
        """Gate 2 required: Auto-activate policies only after self-correction proven."""
        return gate2.passed

    @staticmethod
    def can_full_auto_routing(status) -> bool:
        """All gates required: Full autonomous routing only after proven."""
        return status.is_graduated
```

### Tables Written

| Table | Purpose | Layer |
|-------|---------|-------|
| `graduation_history` | Immutable audit trail | L7 (ops) |
| `m25_graduation_status` | Current derived state | L4/L2 |
| `capability_lockouts` | **Runtime feature gates** | **L6** |

---

## Change Summary

| Field | Before | After |
|-------|--------|-------|
| Producer | graduation_engine.py | graduation_evaluator.py |
| P-Layer | L4 | L5 |
| Consumer | integration.py | capability_lockouts (L6), integration.py (L2) |
| C-Layer | L2 | L6, L2 |
| Persistence | In-memory | PostgreSQL |

---

## Impact

1. **L7→L6 Sufficiency Analysis:** GAP-001 resolved
2. **L6→L5 Coherency:** capability_lockouts now explicit L6 artifact
3. **CI Enforcement:** Auditor can correctly track this signal
4. **Runtime Behavior:** No change (code was always correct; only registry was wrong)

---

## Verification

After applying this change:
- Re-run `signal_auditor.py` in observe-only mode
- GAP-001 should disappear from L7_L6_SUFFICIENCY_ANALYSIS.md
- No new warnings related to graduation logic expected

---

## Approval

This change corrects a **semantic error** in the frozen baseline.
The registry was wrong; the code was always correct.

Applied as version 1.0.1 of the Signal Registry.
