# PIN-519: System Run Introspection Protocols

**Status:** COMPLETE
**Created:** 2026-02-03
**Predecessor:** PIN-517 (cus_vault), PIN-518 (Analytics Storage)
**Reference:** Activity L5 Red-Lines, Integrity Decision Tree

---

## Problem Statement

Three TODOs in `activity_facade.py` represented missing **L4 coordination** for cross-domain system facts:

1. `get_run_evidence()` (line 629) - returned empty shell
2. `get_run_proof()` (line 653) - returned UNKNOWN integrity
3. Signal feedback (line 1027) - `feedback=None`

**Root cause:** Activity L5 cannot answer cross-domain questions. These require L4 coordinators.

---

## Architecture Decision

Per first-principles analysis:
- **Trust boundary:** SYSTEM (Postgres)
- **Integrity model:** HASH_CHAIN (now) -> MERKLE_TREE (later)
- **Coordination layer:** L4 coordinators via bridges

---

## Implementation Summary

### Phase 1: L7 Model Extension

**File:** `app/models/audit_ledger.py`

Added missing event type:
```python
SIGNAL_ESCALATED = "SignalEscalated"
```

### Phase 2: L6 Driver Extensions

| File | Changes |
|------|---------|
| `audit_ledger_driver.py` | Added `signal_acknowledged()`, `signal_suppressed()`, `signal_escalated()` |
| `audit_ledger_read_driver.py` | NEW - Read-only query driver for signal feedback |
| `limits_read_driver.py` | Added `fetch_limit_breaches_for_run()` |
| `policy_enforcement_driver.py` | NEW - Policy evaluation queries for runs |

### Phase 3: Bridge Extensions

| Bridge | New Capability |
|--------|----------------|
| `incidents_bridge.py` | `incidents_for_run_capability()` |
| `policies_bridge.py` | `policy_evaluations_capability()` |
| `controls_bridge.py` | `limit_breaches_capability()` |
| `logs_bridge.py` | `traces_store_capability()`, `audit_ledger_read_capability()` |

### Phase 4: L4 Coordinators

| Coordinator | Purpose |
|-------------|---------|
| `run_evidence_coordinator.py` | Cross-domain evidence aggregation |
| `run_proof_coordinator.py` | Integrity verification via traces |
| `signal_feedback_coordinator.py` | Signal feedback from audit ledger |

### Phase 5: Activity Facade Integration

Updated `activity_facade.py`:
- `get_run_evidence()` now delegates to `RunEvidenceCoordinator`
- `get_run_proof()` now delegates to `RunProofCoordinator`
- `get_signals()` now fetches feedback via `SignalFeedbackCoordinator`

### Phase 6: Protocol Definitions

**File:** `app/hoc/cus/hoc_spine/schemas/run_introspection_protocols.py`

Defines:
- `RunEvidenceProvider` protocol
- `RunProofProvider` protocol
- `SignalFeedbackProvider` protocol
- Result dataclasses for all coordinator outputs
- `INTEGRITY_CONFIG` system-wide declaration

---

## Files Changed

| Phase | Action | File |
|-------|--------|------|
| 1 | MODIFY | `app/models/audit_ledger.py` |
| 2.1 | MODIFY | `app/hoc/cus/logs/L6_drivers/audit_ledger_driver.py` |
| 2.2 | CREATE | `app/hoc/cus/logs/L6_drivers/audit_ledger_read_driver.py` |
| 2.3 | MODIFY | `app/hoc/cus/controls/L6_drivers/limits_read_driver.py` |
| 2.4 | CREATE | `app/hoc/cus/policies/L6_drivers/policy_enforcement_driver.py` |
| 3.1 | MODIFY | `bridges/incidents_bridge.py` |
| 3.2 | MODIFY | `bridges/policies_bridge.py` |
| 3.3 | MODIFY | `bridges/controls_bridge.py` |
| 3.4 | MODIFY | `bridges/logs_bridge.py` |
| 4.1 | CREATE | `coordinators/run_evidence_coordinator.py` |
| 4.2 | CREATE | `coordinators/run_proof_coordinator.py` |
| 4.3 | CREATE | `coordinators/signal_feedback_coordinator.py` |
| 5 | MODIFY | `activity/L5_engines/activity_facade.py` |
| 6 | CREATE | `hoc_spine/schemas/run_introspection_protocols.py` |
| 7.1 | CREATE | `tests/test_run_introspection_coordinators.py` |
| 7.2 | CREATE | `tests/test_activity_facade_introspection.py` |

**Total:** 17 files (8 new, 9 modified)

---

## Integrity Model

### Phase 1: HASH_CHAIN

```python
def compute_hash_chain(run_id: str, steps: list) -> str:
    """Compute sequential hash chain of trace steps."""
    h = hashlib.sha256(run_id.encode())
    for step in steps:
        step_data = f"{step.step_index}:{step.skill_name}:{step.status}"
        h.update(step_data.encode())
    return h.hexdigest()
```

### Verification Status

| Status | Meaning |
|--------|---------|
| `VERIFIED` | Hash chain computed and valid |
| `FAILED` | Hash chain computation failed |
| `UNSUPPORTED` | No trace or no steps to verify |

Note: `UNKNOWN` is no longer a valid steady state (per formal spec).

---

## Red-Line Compliance

- [x] Activity L5 does not import other domains
- [x] Activity L5 does not write data
- [x] Activity L5 does not evaluate policy
- [x] Activity L5 does not compute integrity (delegated to coordinator)
- [x] Activity L5 does not trigger execution
- [x] All cross-domain queries go through L4 coordinators
- [x] Bridges expose capabilities only, not narratives
- [x] Integrity model explicitly declared (HASH_CHAIN)
- [x] No "UNKNOWN" steady state

---

## Single Activity Facade Enforcement

**Canonical path:** `app/hoc/cus/activity/L5_engines/activity_facade.py`

### CI Guard (Check 31)

```python
# scripts/ci/check_init_hygiene.py
def check_single_activity_facade(violations):
    """Only one activity_facade.py allowed in HOC tree."""
```

### Architectural Lock

The canonical file contains an `ARCHITECTURAL LOCK` comment block that:
- Documents red-line constraints
- References CI check 31
- Forbids cross-domain access at L5

### Test Enforcement

```python
# tests/test_activity_facade_introspection.py
class TestSingleActivityFacadeEnforcement:
    def test_single_activity_facade_exists_in_hoc(self): ...
    def test_canonical_facade_has_architectural_lock_comment(self): ...
```

### Legacy Facade Status

The legacy `app/services/activity_facade.py` is:
- Tolerated (scheduled for deletion per PIN-511)
- Isolated from HOC tree (no cross-imports allowed)
- Called only by legacy `app/api/activity.py`

---

## Verification Commands

```bash
# 1. Import checks
PYTHONPATH=. python3 -c "
from app.hoc.cus.hoc_spine.orchestrator.coordinators.run_evidence_coordinator import get_run_evidence_coordinator
from app.hoc.cus.hoc_spine.orchestrator.coordinators.run_proof_coordinator import get_run_proof_coordinator
from app.hoc.cus.hoc_spine.orchestrator.coordinators.signal_feedback_coordinator import get_signal_feedback_coordinator
print('OK: All coordinators import cleanly')
"

# 2. CI checks pass
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci

# 3. Run coordinator tests
PYTHONPATH=. python3 -m pytest tests/test_run_introspection_coordinators.py -v

# 4. Run integration tests
PYTHONPATH=. python3 -m pytest tests/test_activity_facade_introspection.py -v

# 5. Verify Activity facade TODOs removed
grep -n "TODO" app/hoc/cus/activity/L5_engines/activity_facade.py | grep -E "(evidence|proof|feedback)"
# Should return nothing
```

---

## Future Work

1. **MERKLE_TREE integrity model** - More efficient verification for large trace sets
2. **Audit ledger compaction** - Aggregate old signal feedback events
3. **Cross-tenant integrity proofs** - For multi-tenant compliance

---

## References

- Activity L5 Red-Lines specification
- Integrity Decision Tree (formal spec)
- HOC Layer Topology V2.0.0 (PIN-484)
- PIN-513 L4 Coordinator patterns
