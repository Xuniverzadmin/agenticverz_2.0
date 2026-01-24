# POLICIES DOMAIN LOCK — FINAL

**Status:** LOCKED
**Date:** 2026-01-24
**Reference:** PIN-468 (Phase-2.5A)

---

## 1. Structural Guarantee

| Component | State | Invariant |
|-----------|-------|-----------|
| `engines/engine.py` | LOCKED | Zero runtime DB access (only SQLAlchemyError) |
| `drivers/policy_engine_driver.py` | FROZEN | All persistence operations registered |
| L4/L6 boundary | ENFORCED | Engine decides, Driver persists |

---

## 2. Engine Authority (L4)

`PolicyEngine` owns all policy reasoning:

- DAG validation and cycle detection
- Temporal threshold decisions
- Activation integrity checks
- Dependency reasoning
- Conflict resolution semantics

**No SQL. No persistence. No orchestration.**

---

## 3. Driver Inventory (L6)

`PolicyEngineDriver` owns persistence for 14 tables:

| Table | Operations |
|-------|------------|
| policy.evaluations | write |
| policy.violations | read/write |
| policy.ethical_constraints | read |
| policy.risk_ceilings | read/write |
| policy.safety_rules | read/write |
| policy.business_rules | read |
| policy.policy_versions | read/write |
| policy.policy_provenance | read/write |
| policy.policy_dependencies | read/write |
| policy.policy_conflicts | read/write |
| policy.temporal_policies | read/write |
| policy.temporal_metric_events | read/write |
| policy.temporal_metric_windows | read/write |

**Adding tables requires inventory update.**

---

## 4. Extraction Manifest

24 methods extracted (M1-M24):

```
M1.  _load_policies()              POLICY_CONFIG_READ
M2.  _persist_evaluation()         POLICY_EVALUATION_WRITE
M3.  get_violations()              POLICY_VIOLATION_READ
M4.  get_violation()               POLICY_VIOLATION_READ
M5.  acknowledge_violation()       POLICY_VIOLATION_WRITE
M6.  update_risk_ceiling()         POLICY_CEILING_WRITE
M7.  reset_risk_ceiling()          POLICY_CEILING_WRITE
M8.  update_safety_rule()          POLICY_RULE_WRITE
M9.  get_policy_versions()         POLICY_VERSION_READ
M10. get_current_version()         POLICY_VERSION_READ
M11. create_policy_version()       POLICY_VERSION_WRITE
M12. rollback_to_version()         POLICY_VERSION_WRITE
M13. get_version_provenance()      POLICY_PROVENANCE_READ
M14. get_dependency_graph()        POLICY_GRAPH_READ
M15. get_policy_conflicts()        POLICY_GRAPH_READ
M16. resolve_conflict()            POLICY_GRAPH_WRITE
M17. get_temporal_policies()       POLICY_TEMPORAL_READ
M18. create_temporal_policy()      POLICY_TEMPORAL_WRITE
M19. get_temporal_utilization()    POLICY_TEMPORAL_READ
M20. validate_dependency_dag()     POLICY_GRAPH_READ
M21. add_dependency_with_dag_check() POLICY_GRAPH_WRITE
M22. prune_temporal_metrics()      POLICY_TEMPORAL_WRITE
M23. get_temporal_storage_stats()  POLICY_TEMPORAL_READ
M24. activate_policy_version()     POLICY_INTEGRITY_READ
```

---

## 5. SQL Construction Rules

Driver uses f-strings **only** for integer INTERVAL values:

```python
# ALLOWED (int only, no user input)
sql = f"... INTERVAL '{retention_hours} hours'"

# FORBIDDEN
sql = f"... WHERE name = '{user_input}'"
```

No identifiers or predicates interpolated.

---

## 6. Shim Existence

`app/services/` may contain thin shims for API compatibility.
These shims delegate to `PolicyEngine` — they do not own logic.

---

## 7. Forbidden Actions

| Action | Enforcement |
|--------|-------------|
| Add sqlalchemy imports to engine.py | CI BLOCK |
| Add new driver without inventory entry | CI BLOCK |
| Create `_service.py` under engines/ | CI BLOCK |
| Refactor engine for "niceness" | GOVERNANCE BLOCK |
| Normalize driver method names | GOVERNANCE BLOCK |

---

## 8. Ownership

| Role | Owner |
|------|-------|
| Engine logic | PolicyEngine class |
| Persistence | PolicyEngineDriver class |
| Shim/facade | app/services/ (if any) |
| Governance | This document |

---

## 9. Verification

Run BLCA to verify layer compliance:

```bash
python3 scripts/ops/layer_validator.py --backend --ci
```

Expected: 0 violations in policies domain.

---

## 10. Next Domain

After policies lock is verified:

```
customer/analytics/engines/
```

Do not proceed to internal/agent or general runtime.

---

**This document is the line in the sand.**
