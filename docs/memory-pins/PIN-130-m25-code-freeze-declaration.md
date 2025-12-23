# PIN-130: M25 Code Freeze Declaration

**Status:** ENFORCED
**Created:** 2025-12-23
**Category:** Governance / Code Freeze
**Milestone:** M25 Learning Proof - FROZEN

---

## Declaration

**M25 Graduation Hardening is FROZEN as of 2025-12-23.**

No further changes to M25 graduation logic, schema, or endpoints are permitted until:
1. Real evidence trail is captured (not simulated)
2. Downgrade regression tests pass
3. M26 is proven to feed evidence (not bypass graduation)

---

## What is Frozen

### Schema (No Changes Allowed)
- `m25_graduation_status` table
- `graduation_history` table
- `timeline_views` table
- `capability_lockouts` table
- `is_simulated` columns on `prevention_records` and `regret_events`

### Logic (No Changes Allowed)
- `backend/app/integrations/graduation_engine.py` - Pure function, no modifications
- `backend/app/integrations/learning_proof.py` - Gate definitions frozen
- `backend/alembic/versions/043_m25_learning.py` - Sealed
- `backend/alembic/versions/044_m25_graduation_hardening.py` - Sealed

### Endpoints (Read-Only Additions Only)
- `GET /integration/graduation` - Frozen
- `POST /graduation/simulate/*` - Frozen (already marked as non-counting)
- `POST /graduation/record-view` - Frozen
- `POST /graduation/re-evaluate` - Frozen

### Jobs (No Changes Allowed)
- `backend/app/jobs/graduation_evaluator.py` - Periodic evaluator frozen

---

## What is Permitted

### Bug Fixes Only
- Fix crashes or data corruption
- Fix incorrect queries
- No "improvements" disguised as fixes

### Read-Only Introspection
- New GET endpoints for observability
- Prometheus metrics (already implemented)
- Logging improvements

### Evidence Capture
- Scripts to record real closed-loop proofs
- Test harnesses for downgrade scenarios
- Documentation

---

## What is Explicitly Forbidden

### DO NOT
- Add new graduation levels (alpha/beta/candidate/complete is final)
- Add new capability lockouts
- Add "temporary overrides" for graduation
- Add cost-specific graduation shortcuts
- Add parallel maturity models
- Modify the graduation engine to accept hints/nudges

### M26 Constraints
- M26 cost anomalies must become incidents (not separate maturity)
- M26 must NOT influence graduation logic
- M26 may only **feed evidence into the existing loop**

---

## Enforcement

### Pre-Commit Check
Any PR touching frozen files must:
1. Reference this PIN
2. Justify as bug fix with specific bug ID
3. Pass downgrade regression tests

### Review Gate
Changes to graduation logic require:
1. PIN-130 waiver (explicit approval)
2. Regression test for the change
3. Evidence that change doesn't break invariants

---

## Invariants That Must Hold

These are the non-negotiable truths of M25:

1. **Graduation is DERIVED** - Status computed from evidence, never manually set
2. **Simulation is QUARANTINED** - `is_simulated=true` records excluded from real graduation
3. **Degradation is AUTOMATIC** - When prevention rate drops or regret rate spikes
4. **Capabilities are GATED** - Features locked until gates pass (not advisory)
5. **Audit trail is IMMUTABLE** - `graduation_history` is append-only

---

## Next Steps Before M26

1. [ ] Capture one real closed-loop proof (not simulated)
2. [ ] Add downgrade regression tests
3. [ ] Verify graduation engine handles edge cases
4. [ ] Document evidence trail format

---

## Sign-off

This freeze is effective immediately. Violations will be reverted.

**Freeze declared by:** Claude (with user mandate)
**Freeze date:** 2025-12-23
**Freeze duration:** Until real evidence trail captured + downgrade tests pass

---

## Related PINs

- PIN-129: M25 Pillar Integration Blueprint
- PIN-044: M25 Graduation Hardening (migration)
- PIN-043: M25 Learning Proof (migration)
