# PIN-132: M26 Hygiene Gate Checklist

**Status:** ENFORCED
**Created:** 2025-12-23
**Category:** Governance / Code Review
**Milestone:** M26 Preparation

---

## Purpose

This checklist gates any M26 implementation code.
All items must pass before M26 code is merged.

M26 is **Economic Governance** (cost awareness).
It must feed evidence into the existing loop, NOT bypass graduation.

---

## Pre-M26 Gate (Must Pass First)

Before any M26 coding begins:

- [ ] M25 code freeze is in effect (PIN-130)
- [ ] Real evidence trail is captured (PIN-131)
- [ ] Downgrade regression tests pass
- [ ] Graduation engine unchanged for 48+ hours

If any fail, M26 coding is blocked.

---

## Architecture Constraints

### MUST Have

| Requirement | Rationale |
|-------------|-----------|
| ✅ Cost anomalies become incidents | Reuse existing loop |
| ✅ Anomaly incidents have `incident_id` | Link to loop_traces |
| ✅ Aggregation is async/background | No blocking API calls |
| ✅ Feature tags validated at write-time | Bad data must hurt visibly |
| ✅ Savings computed from before/after | No marketing math |
| ✅ Same tenant, feature, time window | Apples to apples |

### MUST NOT Have

| Forbidden Pattern | Why |
|-------------------|-----|
| ❌ New dispatcher | Loop dispatcher is frozen |
| ❌ New loop engine | Integration loop is frozen |
| ❌ Cost-only graduation shortcuts | Graduation is M25's domain |
| ❌ "Estimated" savings fields | Claims must be evidence-backed |
| ❌ UI logic in backend | Keep backend pure |
| ❌ Parallel maturity model | One graduation system |

---

## Code Review Checklist

When reviewing M26 PR:

### 1. Schema Check
- [ ] No new tables that bypass incidents
- [ ] Cost anomalies reference `incident_id`
- [ ] No graduation-related columns added
- [ ] No new maturity enums

### 2. Logic Check
- [ ] No writes inside graduation engine
- [ ] No graduation level modifications
- [ ] Cost calculations are deterministic
- [ ] Aggregation does not block request path

### 3. Evidence Check
- [ ] Savings claims cite specific records
- [ ] Before/after windows are explicit
- [ ] Feature tag coverage is gated
- [ ] No inferred or projected values

### 4. Integration Check
- [ ] Cost anomalies flow through loop
- [ ] Loop traces include cost context
- [ ] Graduation engine sees cost incidents
- [ ] No special handling for cost vs other incidents

---

## Specific File Rules

### May Create
- `backend/app/cost/` - Cost domain logic
- `backend/app/api/cost.py` - Cost API endpoints
- `backend/app/jobs/cost_aggregator.py` - Background aggregation
- `backend/tests/test_m26_*.py` - M26 tests

### May NOT Modify
- `backend/app/integrations/graduation_engine.py` - FROZEN
- `backend/app/integrations/learning_proof.py` - FROZEN
- `backend/alembic/versions/043_*.py` - SEALED
- `backend/alembic/versions/044_*.py` - SEALED

### May Modify (With Caution)
- `backend/app/integrations/dispatcher.py` - Only to add cost incident type
- `backend/app/api/integration.py` - Only new read-only endpoints
- Loop tables - Only to add cost context fields

---

## Feature Tag Hygiene

M26 projections require feature attribution.
Before enabling projections:

```sql
-- Check feature tag coverage
SELECT
  COUNT(*) as total_records,
  COUNT(*) FILTER (WHERE feature_tag IS NOT NULL) as tagged,
  ROUND(100.0 * COUNT(*) FILTER (WHERE feature_tag IS NOT NULL) / COUNT(*), 2) as coverage_pct
FROM cost_records
WHERE created_at > NOW() - INTERVAL '7 days'
```

**Gate:**
- If `coverage_pct < 80%`, projections are LOCKED
- Surface as degradation signal (not graduation modification)

---

## Savings Claim Format

When M26 shows "Saved ₹X / $Y", the calculation must be:

```python
# CORRECT
savings = (
    aggregate_cost(tenant, feature, before_window) -
    aggregate_cost(tenant, feature, after_window)
)

# Claims cite:
{
    "tenant_id": "...",
    "feature_tag": "...",
    "before_window": {"start": "...", "end": "..."},
    "after_window": {"start": "...", "end": "..."},
    "before_cost": 1234.56,
    "after_cost": 987.65,
    "savings": 246.91,
    "savings_pct": 20.0
}
```

**Forbidden:**
```python
# WRONG - Inferred savings
savings = estimated_without_optimization - actual

# WRONG - Marketing math
savings = industry_average - actual
```

---

## Review Response Matrix

| Finding | Action |
|---------|--------|
| New graduation logic | **REJECT** - Violates M25 freeze |
| Cost bypasses incidents | **REJECT** - Must flow through loop |
| Estimated savings | **REJECT** - Claims must be evidence-backed |
| No feature tag validation | **REQUEST CHANGES** - Add validation |
| Aggregation blocks API | **REQUEST CHANGES** - Make async |
| Tests missing | **REQUEST CHANGES** - Add coverage |

---

## Sign-off

M26 code requires explicit sign-off that:

1. All architecture constraints are met
2. No forbidden patterns are present
3. Graduation engine is untouched
4. Evidence trail exists before merge

**Reviewer sign-off template:**
```
M26 Hygiene Review:
- [ ] Architecture constraints: PASS
- [ ] Forbidden patterns: NONE
- [ ] Graduation engine: UNCHANGED
- [ ] Evidence trail: EXISTS

Approved for merge: Yes/No
Reviewer: ___
Date: ___
```

---

## Related PINs

- PIN-130: M25 Code Freeze Declaration
- PIN-131: M25 Evidence Trail Protocol
- PIN-129: M25 Pillar Integration Blueprint
