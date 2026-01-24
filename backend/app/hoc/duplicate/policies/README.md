# Policies Domain — Quarantine Zone

**Status:** FROZEN
**Created:** 2026-01-23
**Reference Audit:** `houseofcards/HOC_policies_detailed_audit_report.md`

---

## Purpose

This folder contains **quarantined duplicate types** from the policies domain.

These types were identified during the policies domain deep audit as facade DTOs that duplicate engine DTOs with 100% field overlap.

---

## Rules

1. **DO NOT import from this package** — All imports are forbidden
2. **DO NOT modify these files** — They are FROZEN
3. **DO NOT add new files** — Quarantine is for existing duplicates only

---

## Quarantined Types

| File | Duplicate | Canonical | Issue |
|------|-----------|-----------|-------|
| `policy_conflict_result.py` | PolicyConflictResult | `engines/policy_graph_engine.py::PolicyConflict` | POL-DUP-004 |
| `policy_node_result.py` | PolicyNodeResult | `engines/policy_graph_engine.py::PolicyNode` | POL-DUP-001 |
| `policy_dependency_edge.py` | PolicyDependencyEdge | `engines/policy_graph_engine.py::PolicyDependency` | POL-DUP-002 |
| `dependency_graph_result.py` | DependencyGraphResult | `engines/policy_graph_engine.py::DependencyGraphResult` | POL-DUP-003 |

---

## Canonical Authority

All canonical types live in:

```
houseofcards/customer/policies/engines/policy_graph_engine.py
```

**Use the engine types, not the facade duplicates.**

---

## CI Guard

Add this to CI to prevent imports:

```bash
grep -R "houseofcards\.duplicate\.policies" app/ && exit 1
```

---

## Removal Policy

These files are eligible for removal after:

1. Phase 2 DTO unification is complete
2. All facade imports are updated to use engine types
3. Import cleanup is verified

Until then, retain for historical traceability.

---

## Deferred Issues (Not Quarantined)

| Issue | Type | Status |
|-------|------|--------|
| POL-DUP-005 | LimitNotFoundError duplicate exception | DEFERRED — Error taxonomy work |
| POL-DUP-006 | utc_now()/generate_uuid() helper duplication | DEFERRED — Utility drift tolerated |

These are not quarantined per architectural guidance (exceptions and utilities handled separately).
