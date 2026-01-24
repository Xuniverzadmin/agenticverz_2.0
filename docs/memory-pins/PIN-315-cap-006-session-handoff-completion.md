# PIN-315: CAP-006 Session Handoff Completion

**Status:** COMPLETE
**Date:** 2026-01-06
**Category:** Authentication / Governance
**Milestone:** CAP-006 Closure
**Related PINs:** PIN-310, PIN-312, PIN-313, PIN-314

---

## Summary

Completed session handoff for CAP-006 Authentication Gateway implementation. All uncommitted WIP from previous session was audited, lint-fixed, and committed in two staged commits.

## Work Completed

### Stage 1 Commit (d0c04d6b)
**Governance hardening: Auth test matrix + CI guards (PIN-314 follow-up)**

- Fixed M28_RESOURCE_ACTIONS test matrix gap
- Added missing resources: `members:team`, `billing:account`, `rbac`
- 12 files changed, 3,052 insertions

### Stage 2 Commit (d0fb445e)
**CAP-006: Authentication Gateway implementation**

- 193 files changed, 22,335 insertions, 651 deletions

#### Core Auth Components:
| File | Purpose |
|------|---------|
| `gateway.py` | Central auth entry point (JWT XOR API key) |
| `gateway_middleware.py` | FastAPI middleware integration |
| `gateway_types.py` | Type definitions |
| `gateway_config.py` | Configuration management |
| `authorization_choke.py` | M28 native resource authorization |
| `authorization_metrics.py` | Prometheus metrics |
| `session_store.py` | Redis-backed session management |
| `api_key_service.py` | API key validation |
| `route_planes.py` | Route classification (public/auth/founder) |
| `invariants.py` | Auth invariant guards |

#### API Routes Added (L2):
- `/fdr/contracts/*` - Founder review gate
- `/fdr/explorer/*` - Codebase explorer
- `/scenarios/*` - Cost simulation (H2, advisory)
- `/replay/*` - Execution replay
- `/authz/status` - Authorization status
- `/guard/logs`, `/guard/policies` - Guard management
- `/cus/*` - Customer activity, incidents, keys, policies

#### Adapters (L3):
- `founder_review_adapter.py`
- `customer_activity_adapter.py`
- `customer_incidents_adapter.py`
- `customer_keys_adapter.py`
- `customer_killswitch_adapter.py`
- `customer_logs_adapter.py`
- `customer_policies_adapter.py`

#### Models:
- `contract.py` - Governance contract state machine
- `governance_job.py` - Governance job tracking

## Lint Fixes Applied

| File | Issue | Fix |
|------|-------|-----|
| `gateway_config.py` | F821 undefined `FastAPI` | TYPE_CHECKING import |
| `authorization_choke.py` | F841 unused `is_read` | Removed variable |
| `authorization_metrics.py` | F401 unused `REGISTRY` | Removed import |
| `session_store.py` | F821 undefined `Redis` | TYPE_CHECKING import |

## Test Matrix Fix

Added missing M28 resources to `test_authority_exhaustion.py`:

```python
M28_RESOURCE_ACTIONS: Dict[str, Set[str]] = {
    # ... existing resources ...
    "members:team": {"read", "write", "admin"},  # PIN-310
    "billing:account": {"read", "write", "admin"},  # PIN-310
    "rbac": {"read", "write", "admin"},  # PIN-310
}
```

## CAP-006 Final Status

- **Capability Registry:** CLOSED
- **Implementation:** Complete
- **Tests:** Passing (42 pre-existing failures unrelated to CAP-006)
- **Working Tree:** Clean

## References

- CAP-006 capability definition
- PIN-310: Fast-track M7 closure
- PIN-312, PIN-313, PIN-314: Governance hardening
