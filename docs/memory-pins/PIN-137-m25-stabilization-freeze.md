# PIN-137: M25 Stabilization & Hygiene Freeze

**Status:** FROZEN
**Category:** M25 Graduation / Stabilization
**Created:** 2025-12-23
**Milestone:** M25 Graduation

---

## Summary

Hard freeze of M25 loop mechanics after successful integration wiring. All confidence logic, dispatcher behavior, and event handling are now immutable for graduation proof.

---

## Frozen Components

### Version Information

```python
LOOP_MECHANICS_VERSION = "1.0.0"
LOOP_MECHANICS_FROZEN_AT = "2025-12-23"
CONFIDENCE_VERSION = "CONFIDENCE_V1"
```

### Files Frozen

| File | Purpose |
|------|---------|
| `backend/app/integrations/events.py` | Event types, ConfidenceCalculator, JSON guard |
| `backend/app/integrations/L3_adapters.py` | 5 bridges, PolicyActivationAudit |
| `backend/app/integrations/dispatcher.py` | Dispatch flow, idempotency |

---

## Hygiene Tasks Completed

| # | Task | Implementation | Purpose |
|---|------|----------------|---------|
| H1 | JSON-only guard | `ensure_json_serializable()` | Prevents silent evidence poisoning |
| H2 | Centralized confidence | `ConfidenceCalculator` class | Makes regret analysis meaningful |
| H3 | Policy activation audit | Migration 045, `policy_activation_audit` table | Ties authority + causality |
| H4 | Dispatcher idempotency | In-memory set + DB check | Prevents false learning inflation |
| H5 | Negative overreach tests | 11 tests in `test_m25_policy_overreach.py` | Protects unrelated traffic |

---

## ConfidenceCalculator (FROZEN)

```python
class ConfidenceCalculator:
    VERSION = "CONFIDENCE_V1"

    # Thresholds - DO NOT MODIFY
    STRONG_MATCH_THRESHOLD = 0.85
    WEAK_MATCH_THRESHOLD = 0.6

    # Occurrence-based boosting - DO NOT MODIFY
    BOOST_2_OCCURRENCES = 0.10
    BOOST_3_OCCURRENCES = 0.20
    MAX_CONFIDENCE = 0.90

    # Auto-apply thresholds - DO NOT MODIFY
    AUTO_APPLY_CONFIDENCE = 0.85
    AUTO_APPLY_MIN_OCCURRENCES = 3
```

---

## Policy Activation Record

```
Policy ID:      pol_eff9bcd477874df3
Pattern ID:     pat_1a1fcbbf6cd2483a
Confidence:     0.90 (CONFIDENCE_V1)
Occurrences:    8
Tenant:         tenant_demo
Mode:           ACTIVE
Approval Path:  manual:m25_graduation
Activated At:   2025-12-23 06:24:11 UTC
```

---

## Modification Rules

### What's Allowed

- Bug fixes that don't change semantics
- Logging improvements (read-only)
- Documentation updates

### What's NOT Allowed

- Confidence threshold changes
- Occurrence boost modifications
- Auto-apply logic changes
- Dispatcher flow changes
- Bridge processing order changes

### Future Versions

If changes are required:

1. Create `CONFIDENCE_V2` (don't modify V1)
2. Document migration path
3. Ensure V1 policies remain under V1 rules
4. Increment `LOOP_MECHANICS_VERSION`

---

## Test Coverage

### Negative Tests (11 tests, all PASS)

```
TestPolicyOverreach:
  - test_policy_does_not_match_different_error_type
  - test_policy_does_not_match_different_tenant
  - test_confidence_calculator_does_not_auto_apply_weak_match
  - test_confidence_calculator_requires_3_occurrences_for_auto_apply
  - test_shadow_mode_policy_does_not_block
  - test_policy_with_high_regret_is_disabled
  - test_loop_event_failure_state_blocks_next_stage
  - test_novel_pattern_requires_human_review

TestPreventionContract:
  - test_prevention_requires_same_tenant
  - test_prevention_requires_active_policy
  - test_prevention_must_not_create_incident
```

---

## Related PINs

- PIN-135: M25 Integration Loop Wiring
- PIN-136: M25 Prevention Contract
- PIN-130: M25 Graduation System Design

---

## Changelog

- 2025-12-23: Initial creation - M25 mechanics frozen for graduation
