# Attribution Migration Readiness Checklist

**Status:** ACTIVE
**Effective:** 2026-01-18
**Scope:** v_runs_o2 + SDK Enforcement — Safe Rollout
**Reference:** ATTRIBUTION_ARCHITECTURE.md

---

## Purpose

This checklist defines the **ordered, non-optional steps** to roll out attribution enforcement safely, avoiding data corruption, downtime, or silent regressions.

---

## Phase 0 — Pre-Flight (No Writes)

### Inventory

- [ ] Inventory all run creation paths:
  - [ ] SDK (AOS Python)
  - [ ] SDK (AOS JavaScript)
  - [ ] Internal services
  - [ ] Cron / policy triggers
  - [ ] SDSR synthetic injection

### Impact Analysis

- [ ] Confirm no downstream consumer relies on missing `agent_id`
- [ ] Identify all queries that would break if `agent_id` becomes NOT NULL
- [ ] Document current null rate for attribution fields

### Governance Lock

- [ ] Freeze new capability declarations involving attribution dimensions
- [ ] Notify stakeholders of upcoming behavioral change

---

## Phase 1 — Data Plane Hardening (Backward-Compatible)

### Schema Updates

- [ ] Add `agent_id` to `runs` table (if not already present)
- [ ] Add `actor_type` to `runs` table (if not already present)
- [ ] Add `actor_id` to `runs` table (if not already present)
- [ ] Add `source` to `runs` table (if not already present)

### Backfill Historical Data

- [ ] Backfill historical runs with:
  ```sql
  UPDATE runs SET
    agent_id = 'legacy-unknown',
    actor_type = 'SYSTEM',
    actor_id = NULL,
    source = 'SYSTEM'
  WHERE agent_id IS NULL;
  ```

- [ ] Document backfill as **non-authoritative legacy data**

> **Warning:** This backfill exists only to keep analytics stable.
> It does **not** relax future invariants.

### Verification

- [ ] Confirm zero NULL values in `agent_id` after backfill
- [ ] Confirm zero NULL values in `actor_type` after backfill
- [ ] Existing queries continue to function

---

## Phase 2 — View Integrity Fix (Critical)

### View Update

- [ ] Update `v_runs_o2` to explicitly project:
  - [ ] `agent_id`
  - [ ] `actor_id`
  - [ ] `actor_type`
  - [ ] `source`

### Migration Script

```sql
CREATE OR REPLACE VIEW v_runs_o2 AS
SELECT
  id,
  tenant_id,
  agent_id,          -- REQUIRED: attribution
  actor_type,        -- REQUIRED: attribution
  actor_id,          -- REQUIRED: attribution (nullable)
  source,            -- REQUIRED: attribution
  provider_type,
  status,
  state,
  risk_level,
  created_at,
  started_at,
  completed_at,
  -- ... other existing fields
FROM runs;
```

### Verification

- [ ] `/runs/live/by-dimension?dim=agent_id` returns data (not error)
- [ ] `/runs/live/by-dimension?dim=provider_type` unchanged
- [ ] `/runs/live/by-dimension?dim=risk_level` unchanged
- [ ] No JOINs introduce nullability
- [ ] State filtering remains intact

### Gate

- [ ] **Block merge if any declared dimension is missing from view**

---

## Phase 3 — SDK Enforcement (Behavioral Change)

### AOS Python SDK

- [ ] Add hard validation for `agent_id` (reject if missing)
- [ ] Add hard validation for `actor_type` (reject if missing)
- [ ] Add consistency check: `actor_type=HUMAN` requires `actor_id`
- [ ] Add consistency check: `actor_type=SYSTEM` requires `actor_id=NULL`
- [ ] Emit typed errors (not generic failures)
- [ ] Add rejection logging (distinct log category)

### AOS JavaScript SDK

- [ ] Mirror Python SDK validation rules
- [ ] Ensure parity in error types and messages

### Deployment Order

- [ ] Deploy SDK enforcement **AFTER** schema + view fixes
- [ ] Canary deployment to catch unexpected failures
- [ ] Monitor rejection rate for first 24 hours

---

## Phase 4 — Control-Plane Lock

### SDSR Integration

- [ ] Add `SDSR-ATTRIBUTION-INVARIANT-001` to SDSR scenario library
- [ ] Create scenario that validates dimension existence in view

### Capability Review Gate

- [ ] Update capability review checklist:
  - "Declared dimensions MUST exist in views"
- [ ] Add to PR template for capability changes

### Documentation

- [ ] Update CAPABILITY_SURFACE_RULES.md (RULE-CAP-007) — DONE
- [ ] Update INTENT_LEDGER.md with attribution requirements
- [ ] Add attribution section to developer onboarding

---

## Phase 5 — Post-Migration Validation

### LIVE-O5 Panel

- [ ] "By Agent" → populated with agent distribution
- [ ] "By Provider" → unchanged behavior
- [ ] "By Risk" → unchanged behavior
- [ ] "By Source" → populated

### Signals Domain

- [ ] Agent attribution visible in signal context
- [ ] No "mystery runs" (runs without agent)
- [ ] Cost signals include agent breakdown

### Cost Analysis

- [ ] Costs attributable to specific agents
- [ ] Anomaly detection includes agent context

### Data Integrity

- [ ] Confirm **zero silent nulls** for new runs (created after enforcement)
- [ ] Legacy runs clearly marked as `legacy-unknown`
- [ ] No new runs with missing attribution

---

## Rollback Plan

If critical issues discovered:

### Phase 3 Rollback (SDK)

1. Disable SDK validation (feature flag)
2. Runs continue to be created without hard enforcement
3. Log violations as warnings instead of rejections

### Phase 2 Rollback (View)

1. Revert view to previous definition
2. Remove projected columns
3. Dimension capabilities return to error state

### Phase 1 Rollback (Schema)

1. Not recommended — backfill is non-destructive
2. If required: document which runs are legacy-backfilled

---

## Success Criteria

| Metric | Target |
|--------|--------|
| New runs with agent_id | 100% |
| New runs with actor_type | 100% |
| LIVE-O5 "By Agent" functional | YES |
| Zero silent null attributions | YES |
| SDK rejection rate (steady state) | < 0.1% |

---

## Timeline (Recommended)

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 0 | 1 day | None |
| Phase 1 | 1 day | Phase 0 complete |
| Phase 2 | 1 day | Phase 1 complete, view tested |
| Phase 3 | 2 days | Phase 2 complete, SDK released |
| Phase 4 | 1 day | Phase 3 stable |
| Phase 5 | 1 day | All phases complete |

**Total: 7 days** (with buffer for issues)

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `ATTRIBUTION_ARCHITECTURE.md` | Contract chain diagram |
| `AOS_SDK_ATTRIBUTION_CONTRACT.md` | SDK enforcement rules |
| `RUN_VALIDATION_RULES.md` | Structural completeness |
| `SDSR_ATTRIBUTION_INVARIANT.md` | Control-plane law |
| `CAPABILITY_SURFACE_RULES.md` | Dimension integrity rules |

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-01-18 | Initial creation | Governance |
