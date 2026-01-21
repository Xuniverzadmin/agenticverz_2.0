# PIN-445: Incidents Domain V2 Migration Complete

**Status:** 📋 LOCKED
**Created:** 2026-01-18
**Category:** Architecture / Domain Migration

---

## Summary

Complete 5-phase migration from query-param-based topic filtering to endpoint-scoped topic boundaries. Establishes reference pattern for future domain migrations.

---

## Details

## Executive Summary

The Incidents domain underwent a **reference-quality architectural migration** on 2026-01-18, establishing a repeatable pattern for fixing domain anti-patterns across the system.

## Migration Outcome

| Property | Status |
|----------|--------|
| Semantic correctness | ✅ Topics enforced at boundaries |
| Control-plane truthfulness | ✅ Registry matches reality |
| Mechanical enforcement | ✅ CI + locks prevent regression |
| Institutional memory | ✅ Pattern documented |

## Key Changes

### Before (Broken)
- Generic `/incidents` endpoint with query-param topic filtering
- Caller-controlled semantics (could request wrong scope)
- Frontend aggregation for historical views
- 5 capabilities, some with 0/3 invariants

### After (Correct)
- Topic-scoped endpoints: `/incidents/active`, `/incidents/resolved`, `/incidents/historical`
- Backend-computed analytics endpoints
- 7 new OBSERVED capabilities with 3/3 invariants
- 6 legacy capabilities DEPRECATED
- CI guard prevents regression

## Artifacts Created

| Artifact | Location |
|----------|----------|
| Migration Plan (LOCKED) | `docs/architecture/incidents/INCIDENTS_DOMAIN_MIGRATION_PLAN.md` |
| Domain Audit (Updated) | `docs/architecture/incidents/INCIDENTS_DOMAIN_AUDIT.md` |
| Domain README | `docs/architecture/incidents/README.md` |
| Migration Playbook | `docs/architecture/DOMAIN_MIGRATION_PLAYBOOK.md` |
| CI Guard | `scripts/preflight/check_incidents_deprecation.py` |
| Registry Lock | `backend/AURORA_L2_CAPABILITY_REGISTRY/REGISTRY_LOCKS.yaml` |

## The 5-Phase Pattern

1. **Phase 0: Freeze Semantics** - Declare boundaries (paper change)
2. **Phase 1: Add Endpoints** - Topic-scoped endpoints (additive)
3. **Phase 2: Shadow Validation** - Prove parity before rebinding
4. **Phase 3: Panel Rebinding** - Update frontend (controlled)
5. **Phase 4: Registry Update** - New capabilities, deprecate old
6. **Phase 5: Lockdown** - CI guard, runtime warning, registry lock

## Strategic Value

This migration proved:
> **Topic-scoped endpoints + shadow validation + registry locks scale better than any review process.**

The pattern is now documented in `DOMAIN_MIGRATION_PLAYBOOK.md` for reuse on other domains (Alerts, Jobs, Policies, etc.).

## Maintenance Rules

### Do NOT
- Remove `/incidents` endpoint yet
- "Simplify" registry locks
- Merge deprecated capabilities back
- Treat CI guards as optional

### DO
- Use topic-scoped endpoints for all new work
- Run the same playbook on other domains
- Treat Phase 5 locks as sacred
