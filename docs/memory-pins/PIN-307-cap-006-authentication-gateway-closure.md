# PIN-307: CAP-006 Authentication Gateway Closure

**Status:** ✅ COMPLETE
**Created:** 2026-01-05
**Category:** Capability Registry / Authentication
**Milestone:** CAP-006 CLOSED

---

## Summary

Closed CAP-006 (authentication) from PARTIAL to CLOSED by implementing a central auth gateway with JWT/API key mutual exclusivity, session revocation, audit emission, and CI enforcement.

---

## Details

## Overview

Closed CAP-006 (authentication) capability by implementing a central auth gateway that enforces:
- **Mutual exclusivity**: JWT XOR API Key (both = HARD FAIL)
- **Session revocation**: Redis-backed checking on human requests
- **Route plane enforcement**: HUMAN_ONLY, MACHINE_ONLY, BOTH per route
- **Audit emission**: Every gateway call emits audit event
- **CI guards**: `auth-guard` command blocks JWT parsing outside gateway

## Implementation Summary

### Phase 1-2: Core Gateway
- `contexts.py`: HumanAuthContext, MachineCapabilityContext
- `gateway_types.py`: GatewayResult, GatewayAuthError
- `gateway.py`: Central entry point for all authentication

### Phase 3: Supporting Services
- `session_store.py`: Redis-backed session revocation
- `api_key_service.py`: API key validation against database

### Phase 4-6: Middleware & Audit
- `gateway_middleware.py`: FastAPI middleware
- `route_planes.py`: Route plane declarations
- `gateway_audit.py`: Audit event emission with Prometheus metrics

### Phase 7-8: Integration & Guards
- `gateway_config.py`: Gateway initialization helper
- `invariants.py`: Hard-fail guards (I1-I5)
- `main.py`: Gateway middleware wired

### Phase 9-10: CI & Registry
- `capability_registry_enforcer.py`: Added `auth-guard` command
- Registry updated: authentication state = CLOSED
- Heatmap regenerated: 6 capabilities with gaps (down from 7)

## Files Created

| File | Purpose |
|------|---------|
| `backend/app/auth/contexts.py` | Auth context models |
| `backend/app/auth/gateway_types.py` | Result types and errors |
| `backend/app/auth/gateway.py` | Central auth gateway |
| `backend/app/auth/session_store.py` | Session revocation |
| `backend/app/auth/api_key_service.py` | API key validation |
| `backend/app/auth/gateway_middleware.py` | FastAPI middleware |
| `backend/app/auth/route_planes.py` | Route plane declarations |
| `backend/app/auth/gateway_audit.py` | Audit emission |
| `backend/app/auth/gateway_config.py` | Gateway config |
| `backend/app/auth/invariants.py` | Invariant guards |

## Invariants Enforced

| ID | Name | Description |
|----|------|-------------|
| I1 | no_mixed_auth | JWT XOR API Key, never both |
| I2 | plane_match | Auth plane matches route requirement |
| I3 | no_worker_jwt | Worker paths cannot use JWT |
| I4 | admin_no_api_key | Admin paths cannot use API key |
| I5 | headers_stripped | Auth headers removed after gateway |

## Technical Debt

Legacy auth files grandfathered in CI (to be migrated when RBACv2 promoted):
- rbac_middleware.py, rbac_engine.py, rbac_integration.py
- jwt_auth.py, console_auth.py, tenant_auth.py
- v1_proxy.py, onboarding.py

## Verification

```bash
# Auth guard passes
python3 scripts/ops/capability_registry_enforcer.py auth-guard --scan-all
# Output: ✅ All checks passed

# Registry shows CLOSED
grep -A 5 'authentication:' docs/capabilities/CAPABILITY_REGISTRY.yaml | grep state
# Output: state: CLOSED
```

## Reference

- Plan: `/root/.claude/plans/wondrous-churning-floyd.md`
- Registry: PIN-306 (Capability Registry Governance)
- Capability ID: CAP-006

---

## Related PINs

- [PIN-306](PIN-306-.md)
