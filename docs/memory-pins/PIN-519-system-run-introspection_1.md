# PIN-519: System Run Introspection Protocols

**Status:** COMPLETE
**Date:** 2026-02-03
**Predecessor:** PIN-517 (cus_vault), PIN-518 (Analytics Storage)
**Reference:** Activity L5 Red-Lines, Integrity Decision Tree

---

## Problem Statement

Three TODOs in `activity_facade.py` represented missing **L4 coordination** for cross-domain system facts:

1. `get_run_evidence()` — returned empty shell
2. `get_run_proof()` — returned UNKNOWN integrity
3. Signal feedback — `feedback=None`

**Root cause:** Activity L5 cannot answer cross-domain questions directly. These require L4 coordinators.

---

## Solution Architecture

### Trust Boundary

| Aspect | Decision |
|--------|----------|
| Trust boundary | SYSTEM (Postgres) |
| Integrity model | HASH_CHAIN (Phase 1) |
| Coordination layer | L4 coordinators via bridges |

### Layer Responsibilities

| Layer | Component | Role |
|-------|-----------|------|
| L4 | RunEvidenceCoordinator | Aggregates cross-domain impact |
| L4 | RunProofCoordinator | Verifies trace integrity |
| L4 | SignalFeedbackCoordinator | Queries audit ledger feedback |
| L5 | ActivityFacade | Delegates to L4 coordinators |
| L6 | audit_ledger_read_driver | Read-only audit queries |
| L6 | limits_read_driver | Limit breach queries |
| L6 | policy_enforcement_driver | Policy evaluation queries |

---

## Implementation

### Protocols (L4 Contracts)

**File:** `app/hoc/cus/hoc_spine/schemas/run_introspection_protocols.py`

```python
INTEGRITY_CONFIG = {
    "model": "HASH_CHAIN",  # NONE | HASH_CHAIN | MERKLE_TREE
    "trust_boundary": "SYSTEM",  # LOCAL | SYSTEM
    "storage": "POSTGRES",
}

@runtime_checkable
class RunEvidenceProvider(Protocol):
    async def get_run_evidence(*, session, tenant_id, run_id) -> RunEvidenceResult: ...

@runtime_checkable
class RunProofProvider(Protocol):
    async def get_run_proof(*, session, tenant_id, run_id, include_payloads) -> RunProofResult: ...

@runtime_checkable
class SignalFeedbackProvider(Protocol):
    async def get_signal_feedback(*, session, tenant_id, signal_fingerprint) -> SignalFeedbackResult | None: ...
```

### Result Types

| Type | Purpose |
|------|---------|
| `RunEvidenceResult` | Cross-domain impact (incidents, policies, limits, decisions) |
| `RunProofResult` | Integrity proof (traces, hash chain, verification status) |
| `SignalFeedbackResult` | Feedback status (acknowledged, suppressed, escalated) |
| `IntegrityVerificationResult` | Hash chain verification (VERIFIED | FAILED | UNSUPPORTED) |

### Bridge Extensions

| Bridge | Capability | Driver |
|--------|-----------|--------|
| IncidentsBridge | `incidents_for_run_capability()` | IncidentReadService |
| PoliciesBridge | `policy_evaluations_capability()` | PolicyEnforcementReadDriver |
| ControlsBridge | `limit_breaches_capability()` | LimitsReadDriver |
| LogsBridge | `traces_store_capability()` | SQLiteTraceStore |
| LogsBridge | `audit_ledger_read_capability()` | AuditLedgerReadDriver |

---

## Integrity Model

### HASH_CHAIN (Phase 1)

```python
def compute_hash_chain(run_id: str, steps: list) -> str:
    h = hashlib.sha256(run_id.encode())
    for step in steps:
        step_data = f"{step.step_index}:{step.skill_name}:{step.status}"
        h.update(step_data.encode())
    return h.hexdigest()
```

### Verification States

| Status | Meaning |
|--------|---------|
| VERIFIED | Hash chain computed successfully |
| FAILED | Hash computation failed (exception) |
| UNSUPPORTED | No trace/steps found, or integrity disabled |

---

## Files Changed

| Phase | File | Change |
|-------|------|--------|
| 1 | `app/models/audit_ledger.py` | SIGNAL_ESCALATED event type (already present) |
| 2.1 | `logs/L6_drivers/audit_ledger_driver.py` | Signal write methods |
| 2.2 | `logs/L6_drivers/audit_ledger_read_driver.py` | NEW - Signal feedback queries |
| 2.3 | `controls/L6_drivers/limits_read_driver.py` | `fetch_limit_breaches_for_run()` |
| 2.4 | `policies/L6_drivers/policy_enforcement_driver.py` | NEW - Policy evaluation queries |
| 3 | `bridges/*.py` | Capability methods added |
| 4.1 | `run_evidence_coordinator.py` | NEW - Cross-domain evidence |
| 4.2 | `run_proof_coordinator.py` | NEW - Integrity verification |
| 4.3 | `signal_feedback_coordinator.py` | NEW - Audit ledger feedback |
| 5 | `activity_facade.py` | Delegation to L4 coordinators |
| 6 | `run_introspection_protocols.py` | NEW - Protocol definitions |
| 7 | `tests/test_run_introspection_*.py` | NEW - Coordinator tests |

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
- [x] No "UNKNOWN" steady state (VERIFIED | FAILED | UNSUPPORTED)

---

## Verification

```bash
# Import checks
PYTHONPATH=. python3 -c "
from app.hoc.cus.hoc_spine.orchestrator.coordinators.run_evidence_coordinator import get_run_evidence_coordinator
from app.hoc.cus.hoc_spine.orchestrator.coordinators.run_proof_coordinator import get_run_proof_coordinator
from app.hoc.cus.hoc_spine.orchestrator.coordinators.signal_feedback_coordinator import get_signal_feedback_coordinator
print('OK: All coordinators import cleanly')
"

# CI checks
PYTHONPATH=. python3 scripts/ci/check_init_hygiene.py --ci

# Tests
PYTHONPATH=. python3 -m pytest tests/test_run_introspection_coordinators.py -v
PYTHONPATH=. python3 -m pytest tests/test_activity_facade_introspection.py -v
```

---

## Future Work

1. **MERKLE_TREE** - Implement Merkle tree integrity model for efficient partial verification
2. **Deduplication** - Add incident deduplication in AnomalyIncidentBridge
3. **Signal run_id mapping** - Store run_id in signal after_state for `get_signal_events_for_run()`
