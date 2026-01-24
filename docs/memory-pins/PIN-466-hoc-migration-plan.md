# PIN-466: HOC Migration Plan

**Status:** DRAFT
**Created:** 2026-01-23
**Category:** Architecture / Migration
**Reference:** `docs/architecture/HOC_MIGRATION_PLAN.md`

---

## Summary

Four-phase migration plan for restructuring codebase from `app/services/*` to `houseofcards/{audience}/{domain}/*` following HOC Layer Topology V1.2.0.

---

## Phase Overview

| Phase | Name | Objective |
|-------|------|-----------|
| **P1** | Migration | Move files, insert headers, identify what stays |
| **P2** | Gap Analysis | Identify missing pieces at each layer |
| **P3** | Development | Build missing components |
| **P4** | Wiring | Connect all layers, validate contracts |

---

## Key Decisions

### What Migrates

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/*_facade.py` | `houseofcards/{audience}/{domain}/adapters/` | L3 |
| `app/services/**/*_engine.py` | `houseofcards/{audience}/{domain}/engines/` | L5 |
| `app/services/**/*_service.py` | `engines/` or `drivers/` | L5/L6 |
| `app/api/*.py` | `houseofcards/api/{audience}/*.py` | L2 |

### What Stays

| Location | Reason |
|----------|--------|
| `app/models/*.py` (shared) | Cross-audience tables |
| `app/worker/*.py` | Infrastructure workers |
| `app/auth/*.py` | Authentication infrastructure |
| `app/core/*.py` | Core utilities |

### What Gets Deleted

- `houseofcards/duplicate/` — Legacy structures
- `app/api/legacy_routes.py` — Deprecated routes
- `app/api/v1_*.py` — V1 proxy routes

---

## Gap Summary (Post-Migration)

### Missing L2.1 Facades (All Domains)

All 10 customer domains need facade creation:
- overview, activity, incidents, policies, logs
- analytics, integrations, api_keys, account
- Plus: founder/ops, internal/*

### Missing L4 Runtime Parts

| Part | Status |
|------|--------|
| `authority/` | ❌ Missing |
| `execution/` | ⚠️ Partial |
| `consequences/` | ❌ Missing |
| `contracts/` | ❌ Missing |

### Missing L6 Drivers

Most domains lack proper drivers that return domain objects (not ORM).

---

## Domain Migration Order

1. API Keys (smallest, isolated)
2. Account
3. Overview
4. Activity
5. Logs
6. Analytics
7. Incidents
8. Policies
9. Integrations
10. Ops (Founder)
11. Platform (Internal)
12. Recovery (Internal)
13. Agent (Internal)

---

## Acceptance Criteria

- [ ] All files have headers
- [ ] BLCA passes with 0 violations
- [ ] All layer contracts satisfied
- [ ] No circular imports
- [ ] All tests pass
- [ ] Quarantine registry empty
- [ ] Legacy `app/services/` deleted

---

## Related PINs

- PIN-465: HOC Layer Topology V1
- PIN-464: HOC Customer Domain Comprehensive Audit

---

## Document Location

```
docs/architecture/HOC_MIGRATION_PLAN.md
```
