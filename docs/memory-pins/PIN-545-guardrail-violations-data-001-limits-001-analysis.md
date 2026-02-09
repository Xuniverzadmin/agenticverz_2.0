# PIN-545: Guardrail Violations DATA-001 & LIMITS-001 Analysis

**Status:** ✅ COMPLETE
**Created:** 2026-02-09
**Category:** Database

---

## Summary

DATA-001: incidents.source_run_id is de facto canonical (all writes+reads) but has no FK; llm_run_id has FK but is never written post-migration-087. LIMITS-001: false positive — limits (governance) and cost_budgets (analytics) are intentionally separate per domain architecture.

---

## Context

Pre-commit guardrail blocked commits with two violations: DATA-001 (missing FK on incidents) and
LIMITS-001 (parallel limit tables). Investigation reveals one is real, one is a false positive.

---

## DATA-001: incidents.source_run_id → runs (REAL ISSUE)

### Dual-Field Confusion

The Incident model (`app/models/killswitch.py`) has **two** run-linkage fields:

| Field | FK Constraint | Written at Creation | Used in Queries | Canonical per PIN-412 |
|-------|---------------|--------------------|-----------------|-----------------------|
| `source_run_id` | None (index only) | Yes (always) | Yes (all reads) | No (legacy) |
| `llm_run_id` | Yes → `runs.id` (`SET NULL`) | Never | Never | Yes (declared) |

### What Happened

1. **Migration 087** (PIN-412, 2026-01-13) introduced `llm_run_id` as canonical FK
2. Backfilled all existing `source_run_id` → `llm_run_id`
3. **But:** L5 incident engines were **never updated** to write `llm_run_id`

### Evidence

**Writers (all write `source_run_id` only):**
- `incidents/L5_engines/incident_engine.py:415` — `create_incident_for_run_with_outcome()`
- `incidents/L5_engines/incident_engine.py:574` — `create_incident_for_failed_run()`

**Readers (all query `source_run_id` only):**
- `incidents/L6_drivers/incidents_facade_driver.py` — `fetch_incidents_by_run()` filters on `source_run_id`

**Result:** Post-migration-087 incidents have `source_run_id` populated, `llm_run_id = NULL`.

### Fix Options

| Option | Action | Risk |
|--------|--------|------|
| **A: Adopt PIN-412 intent** | Update engines to write `llm_run_id`, update readers to query it, backfill gap, deprecate `source_run_id` | Medium — requires coordinated L5/L6 changes |
| **B: Formalize reality** | Add FK on `source_run_id`, deprecate unused `llm_run_id`, update guardrail rule | Low — matches actual runtime behavior |

### Migration (either option, safe approach)

```sql
-- Option B example (NOT VALID + VALIDATE pattern)
ALTER TABLE incidents ADD CONSTRAINT incidents_source_run_id_fkey
  FOREIGN KEY (source_run_id) REFERENCES runs(id) NOT VALID;
-- Backfill or nullify invalid rows first
ALTER TABLE incidents VALIDATE CONSTRAINT incidents_source_run_id_fkey;
```

### Key Files

| File | Role |
|------|------|
| `app/models/killswitch.py:290,309` | Model: both fields defined |
| `incidents/L5_engines/incident_engine.py:415,574` | Writers: `source_run_id` only |
| `incidents/L6_drivers/incidents_facade_driver.py` | Reader: queries `source_run_id` |
| `alembic/versions/087_incidents_lifecycle_repair.py` | Migration: introduced `llm_run_id` + backfill |

---

## LIMITS-001: Parallel Limit Tables (FALSE POSITIVE)

### They Are NOT Duplicates

| Table | Domain | Purpose | PIN | Status |
|-------|--------|---------|-----|--------|
| `limits` | Policies (governance) | Hard enforce: BUDGET, RATE, THRESHOLD | PIN-412 | RATIFIED |
| `cost_budgets` | Analytics (cost tracking) | Track spend, alert on anomalies | PIN-141 | FROZEN |

### Key Distinction

- **`limits`**: "This tenant **cannot** spend more than $X" — governance enforcement (block/warn/reject)
- **`cost_budgets`**: "This tenant **has** spent $Y; project overage" — analytics alerting (soft, observational)

### Separate Code Paths

| Aspect | `limits` | `cost_budgets` |
|--------|----------|----------------|
| L5 Engine | `policies/L5_engines/policy_limits_engine.py` | `analytics/L5_engines/cost_anomaly_detector` |
| L6 Driver | `controls/L6_drivers/policy_limits_driver.py` | `analytics/L6_drivers/cost_write_driver.py` |
| Domain | Policies (governance) | Analytics (cost tracking) |
| Enforcement | Hard block/warn/reject | Soft warning → incident escalation |

### Full Limits Ecosystem

**Policy Control Plane (4 tables):**
- `limits` — policy limit definitions
- `limit_breaches` — append-only violation history
- `limit_overrides` — temporary limit increases (PIN-LIM-05)
- `limit_integrity` — integrity state per limit

**Cost Analytics (5 tables, PIN-141 FROZEN):**
- `cost_budgets` — per-tenant/feature/user budget thresholds
- `cost_records` — raw cost metering (append-only)
- `cost_anomalies` — detected anomalies
- `cost_daily_aggregates` — pre-aggregated daily costs
- `feature_tags` — cost attribution tags

### Guardrail Fix Needed

The LIMITS-001 rule should be updated to recognize the governance/analytics domain split.
These tables are **intentionally separate** per HOC domain architecture (PIN-484).

---

## Verdict & Resolution

| Violation | Real Issue? | Action | Status |
|-----------|------------|--------|--------|
| **DATA-001** | Yes | Added FK on `source_run_id` via migration 123 (NOT VALID). Model updated in `killswitch.py`. Long-term: rewire to `llm_run_id` (Option A, deferred). | **RESOLVED** |
| **LIMITS-001** | No (false positive) | Added `cost_budgets` to `ALLOWED_LIMIT_TABLES` in `check_limit_tables.py`. Updated `GOVERNANCE_GUARDRAILS.md`. | **RESOLVED** |

Both guardrails now pass. Pre-commit hook unblocked.

---

## Files Changed (Remediation)

| File | Change |
|------|--------|
| `backend/alembic/versions/123_incidents_source_run_fk.py` | New migration: FK `fk_incidents_source_run_id` (NOT VALID, idempotent) |
| `backend/app/models/killswitch.py` | `source_run_id` now has `foreign_key="runs.id"` |
| `scripts/ci/check_limit_tables.py` | `cost_budgets` added to `ALLOWED_LIMIT_TABLES` |
| `docs/.../GOVERNANCE_GUARDRAILS.md` | Updated with domain separation rationale |

## Commit

All changes committed and pushed in `ee87a605` (2026-02-09).

---

## Related

- **[PIN-412](PIN-412-domain-design-incidents-policies.md):** Domain Design — Incidents & Policies (V1_FROZEN). Introduced `llm_run_id` in migration 087 as canonical FK, but write paths were never updated. PIN-412 updated with post-freeze discovery section referencing this PIN.
- **PIN-141:** Cost intelligence (FROZEN `cost_budgets`)
- **PIN-484:** HOC Topology V2.0.0 (domain separation rationale)
- **PIN-542:** Local DB migration issues (same commit session)
