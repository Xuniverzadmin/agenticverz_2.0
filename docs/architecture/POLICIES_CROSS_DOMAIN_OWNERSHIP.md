# POLICIES CROSS-DOMAIN OWNERSHIP — Authority Resolution

**Status:** CONTAINMENT COMPLETE (6/6 checklist items done)
**Date:** 2026-01-24
**Reference:** PIN-468, INCIDENTS_DOMAIN_LOCKED.md, POLICIES_AUTHORITY_MAP.md

---

## Root Invariant

> **A persistence authority must be owned by exactly one domain.**

---

## Duplicate Files Discovered

### Triple Duplication Pattern

Both `lessons_engine.py` and `policy_violation_service.py` exist in THREE locations:

| File | Legacy (app/services/) | Policies HOC | Incidents HOC |
|------|------------------------|--------------|---------------|
| lessons_engine.py | `app/services/policy/lessons_engine.py` | `policies/engines/lessons_engine.py` | `incidents/engines/lessons_engine.py` |
| policy_violation_service.py | `app/services/policy_violation_service.py` | `policies/engines/policy_violation_service.py` | `incidents/engines/policy_violation_service.py` |

### Current State

| Location | Extraction Status | DB Signals | Callers |
|----------|-------------------|------------|---------|
| **app/services/** | NOT extracted | Yes (raw SQL) | Facades import from here |
| **policies/engines/** | NOT extracted | Yes (raw SQL) | None found |
| **incidents/engines/** | **EXTRACTED** ✅ | None (uses driver) | Internal only |

---

## Canonical Ownership Decision

### lessons_learned Table

| Aspect | Decision |
|--------|----------|
| **Write Authority** | incidents domain (lessons_driver.py) |
| **Canonical Engine** | `incidents/engines/lessons_engine.py` |
| **Read-Only Consumers** | policies domain (via driver read methods) |

**Rationale:**
- Lessons are created from **failure events** (incidents domain)
- Lessons feed into **policy proposals** (policies domain consumes)
- Incident domain owns the fact creation, policies domain owns the proposal creation

### prevention_records Table

| Aspect | Decision |
|--------|----------|
| **Write Authority** | incidents domain (policy_violation_driver.py) |
| **Canonical Engine** | `incidents/engines/policy_violation_service.py` |
| **Read-Only Consumers** | policies domain (via driver read methods) |

**Rationale:**
- Violations are **facts** about run failures (incidents domain)
- Policy evaluation **reads** violations to make decisions (policies domain)
- Incident domain owns fact persistence, policies domain owns evaluation logic

### policy_proposals Table

| Aspect | Decision |
|--------|----------|
| **Write Authority** | SHARED (both domains) |
| **incidents domain** | Creates proposals from incidents (incident_write_driver.py) |
| **policies domain** | Creates proposals from lessons (policy_proposal.py) |

**Rationale:**
- Both domains can create proposals from different triggers
- No single owner — but each has distinct creation paths
- Driver inventory must document both write paths

---

## Resolution Actions

### Action 1: Delete Policies Domain Duplicates

The following files are **exact duplicates** with no unique functionality:

```
DELETE: app/houseofcards/customer/policies/engines/lessons_engine.py
DELETE: app/houseofcards/customer/policies/engines/policy_violation_service.py
```

**Verification before delete:**
- [ ] No unique methods in policies versions
- [ ] No callers import from policies versions
- [ ] Incidents versions are complete

### Action 2: Update Legacy Shims

The `app/services/` files must delegate to incidents domain:

**app/services/policy/lessons_engine.py → shim to incidents**
```python
# DEPRECATED: Use app.houseofcards.customer.incidents.engines.lessons_engine
from app.houseofcards.customer.incidents.engines.lessons_engine import *
```

**app/services/policy_violation_service.py → shim to incidents**
```python
# DEPRECATED: Use app.houseofcards.customer.incidents.engines.policy_violation_service
from app.houseofcards.customer.incidents.engines.policy_violation_service import *
```

### Action 3: Update driver_inventory.yaml

Add ownership column:

```yaml
lessons_driver:
  owner: incidents
  consumers: [policies]

policy_violation_driver:
  owner: incidents
  consumers: [policies]

# policies domain does NOT own writes to:
# - lessons_learned
# - prevention_records
```

---

## Signal Reduction Impact

If duplicates are deleted:

| Domain | Before | After | Reduction |
|--------|--------|-------|-----------|
| Policies engines with signals | 19 | **17** | -2 files |
| Policies total signals | 119 | **93** | -26 signals |

This removes **22% of policies extraction work** by resolving duplication.

---

## Pre-Extraction Checklist (Updated)

Before any policies extraction:

- [x] Delete `policies/engines/lessons_engine.py` (duplicate) — DONE 2026-01-24
- [x] Delete `policies/engines/policy_violation_service.py` (duplicate) — DONE 2026-01-24
- [x] Update `app/services/policy/lessons_engine.py` → shim to incidents — DONE 2026-01-24
- [x] Update `app/services/policy_violation_service.py` → shim to incidents — DONE 2026-01-24
- [x] Update `driver_inventory.yaml` with ownership column — DONE 2026-01-24
- [x] Verify facades still work after shim updates — DONE 2026-01-24 (import graph passes)

---

## Table Ownership Matrix (Cross-Domain)

| Table | Write Owner | Read Consumers |
|-------|-------------|----------------|
| lessons_learned | incidents (lessons_driver) | policies |
| prevention_records | incidents (policy_violation_driver) | policies |
| policy_proposals | incidents (incident_write_driver), policies (proposal_driver) | both |
| policy_rules | policies (to be extracted) | incidents |
| limits | policies (to be extracted) | incidents |

---

## Next Step

**Execute Action 1 and Action 2** (delete duplicates, create shims) before any extraction.

This is a **containment operation**, not an extraction.
