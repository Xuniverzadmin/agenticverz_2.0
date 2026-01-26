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

## 7. BANNED_NAMING Fixes (2026-01-24)

Files renamed to comply with HOC Layer Topology V1 (`*_service.py` banned):

### drivers/ fixes

| Old Name | New Name | Layer | Reason |
|----------|----------|-------|--------|
| `governance_signal_service.py` | `governance_signal_driver.py` | L6 | Has Session imports |
| `llm_threshold_service.py` | `llm_threshold_driver.py` | L6 | Has AsyncSession imports |
| `snapshot_service.py` | `snapshot_engine.py` | L5 | No Session imports (pure dataclass) |
| `recovery_write_service.py` | `recovery_write_driver.py` | L6 | Has Session imports |

**Note:** `snapshot_engine.py` reclassified L6→L5 (no DB boundary crossing).

### engines/ fixes (batch 1)

| Old Name | New Name | Layer | Reason |
|----------|----------|-------|--------|
| `keys_service.py` | `keys_shim.py` | L4 | Deprecated shim, delegates to keys_driver |
| `validator_service.py` | `validator_engine.py` | L5 | Pure advisory logic, no Session |
| `contract_service.py` | `contract_engine.py` | L5 | Pure state machine logic, no Session |
| `sandbox_service.py` | `sandbox_engine.py` | L5 | Pure sandbox logic, no Session |

### engines/ fixes (batch 2)

| Old Name | New Name | Layer | Reason |
|----------|----------|-------|--------|
| `customer_policy_read_service.py` | `customer_policy_read_engine.py` | L5 | Session in TYPE_CHECKING only |
| `policy_rules_service.py` | `policy_rules_engine.py` | L5 | AsyncSession in TYPE_CHECKING only |
| `policy_limits_service.py` | `policy_limits_engine.py` | L5 | AsyncSession in TYPE_CHECKING only |
| `override_service.py` | `drivers/override_driver.py` | L6 | Runtime AsyncSession - moved to drivers/ |

**Note:** All L4→L5 reclassified per HOC Topology V1. `override_driver.py` moved to drivers/ (L6) due to runtime AsyncSession import.

### engines/ fixes (batch 3)

| Old Name | New Name | Layer | Reason |
|----------|----------|-------|--------|
| `audit_service.py` | `audit_engine.py` | L8 | Pure verification logic, no Session |
| `controls/engines/customer_killswitch_read_service.py` | `controls/engines/customer_killswitch_read_engine.py` | L5 | Session in TYPE_CHECKING only |

**Note:** `audit_engine.py` remains L8 (Catalyst/Verification layer) - engine naming for consistency. `customer_killswitch_read_engine.py` reclassified L4→L5.

### drivers/ Layer Reclassification (batch 4)

Files in `drivers/` with no Session imports reclassified from L6→L5 (per Layer ≠ Directory principle):

| File | Layer | Reason |
|------|-------|--------|
| `policy_driver.py` | L5 | Orchestration logic, no Session |
| `nodes.py` | L5 | Pure AST node definitions |
| `ir_nodes.py` | L5 | Pure IR node definitions |
| `grammar.py` | L5 | Pure grammar definitions |
| `tokenizer.py` | L5 | Pure lexical analysis |
| `ir_compiler.py` | L5 | Pure compilation logic |
| `plan.py` | L5 | Pure model definitions |
| `limits.py` | L5 | Pure derivation logic |
| `profile.py` | L5 | Pure config logic |
| `authority_checker.py` | L5 | Pure check logic |
| `fatigue_controller.py` | L5 | Pure fatigue management |
| `folds.py` | L5 | Pure constant folding |
| `audit_evidence.py` | L5 | Pure audit emission |
| `hallucination_detector.py` | L5 | Pure detection logic |
| `kill_switch.py` | L5 | Pure state logic |
| `llm_policy_engine.py` | L5 | Pure enforcement logic |
| `content_accuracy.py` | L5 | Pure validation logic |
| `degraded_mode.py` | L5 | Pure state logic |
| `validator.py` | L5 | Pure semantic validation |
| `interpreter.py` | L5 | Pure IR evaluation |
| `dag_sorter.py` | L5 | Pure DAG algorithm |
| `policy_conflict_resolver.py` | L5 | Pure conflict logic |
| `ast.py` | L5 | Pure AST definitions |
| `dsl_parser.py` | L5 | Pure parsing |
| `state.py` | L5 | Pure enum definitions |
| `runtime_command.py` | L5 | Pure command logic |
| `controls/drivers/runtime_switch.py` | L5 | Pure state logic |

**Note:** Files remain in `drivers/` directory per Layer ≠ Directory principle (layer is determined by code behavior, not directory name). All files have no runtime Session imports.

### drivers/ → engines/ Directory Relocation (Phase 2.5E, 2026-01-24)

9 L5 Engine files relocated from `drivers/` to `engines/` to resolve HEADER_LOCATION_MISMATCH warnings:

| File | From | To | Layer |
|------|------|-----|-------|
| `ir_compiler.py` | drivers/ | engines/ | L5 |
| `grammar.py` | drivers/ | engines/ | L5 |
| `fatigue_controller.py` | drivers/ | engines/ | L5 |
| `plan.py` | drivers/ | engines/ | L5 |
| `profile.py` | drivers/ | engines/ | L5 |
| `tokenizer.py` | drivers/ | engines/ | L5 |
| `ir_nodes.py` | drivers/ | engines/ | L5 |
| `limits.py` | drivers/ | engines/ | L5 |
| `nodes.py` | drivers/ | engines/ | L5 |

**Rationale:** These files are pure L5 engines (no Session imports) and should reside in `engines/` directory for correct layer/directory alignment.

**BLCA Status:** 0 errors, 0 warnings for policies domain after relocation.

---

## 8. Forbidden Actions

| Action | Enforcement |
|--------|-------------|
| Add sqlalchemy imports to engine.py | CI BLOCK |
| Add new driver without inventory entry | CI BLOCK |
| Create `*_service.py` under policies/ | BLCA BLOCK |
| Refactor engine for "niceness" | GOVERNANCE BLOCK |
| Normalize driver method names | GOVERNANCE BLOCK |

---

## 9. Ownership

| Role | Owner |
|------|-------|
| Engine logic | PolicyEngine class |
| Persistence | PolicyEngineDriver class |
| Shim/facade | app/services/ (if any) |
| Governance | This document |

---

## 10. Verification

Run BLCA to verify layer compliance:

```bash
python3 scripts/ops/layer_validator.py --backend --ci
```

Expected: 0 violations in policies domain.

---

## 11. Next Domain

After policies lock is verified:

```
customer/analytics/engines/
```

Do not proceed to internal/agent or general runtime.

---

**This document is the line in the sand.**

---

## Changelog

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-01-24 | 1.0.0 | Initial lock | Claude |
| 2026-01-24 | 1.1.0 | BANNED_NAMING fixes (batches 1-4), L6→L5 reclassifications | Claude |
| 2026-01-24 | 1.2.0 | Phase 2.5E: 9 files relocated drivers/ → engines/ | Claude |
| 2026-01-24 | 1.3.0 | **Phase 3 Directory Restructure** — 18 L5 engine files relocated from L6_drivers/ to L5_engines/ based on content analysis (no DB ops). PIN-470. | Claude |
