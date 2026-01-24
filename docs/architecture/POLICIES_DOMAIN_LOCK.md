# POLICIES DOMAIN LOCK — Pre-Extraction Boundary

**Status:** LOCKED
**Date:** 2026-01-24
**Reference:** PIN-468, POLICIES_CROSS_DOMAIN_OWNERSHIP.md, driver_inventory.yaml

---

## Domain Boundary Declaration

This document declares the **write authority boundaries** for the policies domain during Phase-2.5A extraction. These boundaries are enforced by `driver_inventory.yaml` and must not be violated during extraction.

---

## Policies Domain DOES NOT WRITE

The following tables are **owned by incidents domain** for writes. Policies may READ but MUST NOT WRITE:

| Table | Write Owner | Policies Role |
|-------|-------------|---------------|
| `lessons_learned` | `incidents/lessons_driver.py` | READ-ONLY consumer |
| `prevention_records` | `incidents/policy_violation_driver.py` | READ-ONLY consumer |

**Canonical Authority:** `driver_inventory.yaml` → `cross_domain_ownership` section

---

## Policies Domain MAY WRITE

The following tables are candidates for policies domain write authority (to be confirmed during extraction):

| Table | Expected Driver | Status |
|-------|-----------------|--------|
| `policy_rules` | `policy_rules_driver.py` | PENDING extraction |
| `limits` | `policy_limits_driver.py` | PENDING extraction |
| `policy_proposals` | `proposal_driver.py` | SHARED with incidents |
| `policy_versions` | TBD | PENDING analysis |
| `policy_snapshots` | TBD | PENDING analysis |
| `policy_overrides` | `override_driver.py` | PENDING extraction |

---

## Extraction Rules

During policies domain extraction:

1. **DO NOT** create drivers that write to `lessons_learned`
2. **DO NOT** create drivers that write to `prevention_records`
3. **DO** verify each new driver against `driver_inventory.yaml` before creation
4. **DO** add new drivers to inventory before implementation
5. **DO** use read-only access for cross-domain tables

---

## Shared Table: policy_proposals

`policy_proposals` has **dual write authority**:

| Domain | Write Path | Trigger |
|--------|------------|---------|
| incidents | `incident_write_driver.py` | Incident creates proposal |
| incidents | `lessons_driver.py` | Lesson converts to draft |
| policies | TBD (`proposal_driver.py`) | Direct proposal creation |

This is the ONLY shared-write table. Both domains may create proposals from different triggers.

---

## Verification Gate

Before creating ANY new policy driver:

```
[ ] Check driver_inventory.yaml for existing authority
[ ] Verify table is not cross-domain owned
[ ] Add driver to inventory skeleton FIRST
[ ] Implement after inventory registration
```

---

## Reference

- `driver_inventory.yaml` — Canonical authority
- `POLICIES_CROSS_DOMAIN_OWNERSHIP.md` — Authority resolution
- `POLICIES_AUTHORITY_MAP.md` — Signal baseline and execution order
- `INCIDENTS_DOMAIN_LOCKED.md` — Incidents domain freeze

---

## Lock Invariant

> **Policies domain extraction MUST NOT introduce DB access to lessons_learned or prevention_records.**
> Any such access is a governance violation requiring rollback.
