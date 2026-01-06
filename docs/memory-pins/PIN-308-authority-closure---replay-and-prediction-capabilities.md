# PIN-308: Authority Closure - Replay and Prediction Capabilities

**Status:** ✅ COMPLETE
**Created:** 2026-01-05
**Category:** Capability Registry / Authority

---

## Summary

Closed authority gaps for CAP-001 (replay) and CAP-004 (predictions) via RBAC v2 enforcement

---

## Details

## Overview

Closed the MISSING_AUTHORITY gaps for replay (CAP-001) and prediction_plane (CAP-004) capabilities.

## Implementation Summary

### Phase A: Authority Surfaces Declared
- Added capability-specific permissions to PERMISSION_TAXONOMY_V1.md:
  - `read:replay`, `execute:replay`, `audit:replay`, `admin:replay`
  - `read:predictions`, `execute:predictions`, `audit:predictions`, `admin:predictions`
- Updated AuthorizationEngine ROLE_PERMISSIONS with capability permissions

### Phase B: RBAC v2 Enforcement
Created `backend/app/auth/authority.py` with:
- `AuthorityResult` dataclass
- `gateway_context_to_actor()` - converts GatewayContext to ActorContext
- `require_replay_execute`, `require_replay_read`, etc.
- `require_predictions_read`, `require_predictions_execute`, etc.

Updated routes:
- `backend/app/api/predictions.py` (4 endpoints)
- `backend/app/api/runtime.py` (replay endpoint)
- `backend/app/api/guard.py` (replay endpoint)
- `backend/app/api/workers.py` (replay endpoint)
- `backend/app/api/v1_killswitch.py` (replay endpoint)

### Phase C: Audit Completion
- Added Prometheus metrics (`nova_authority_allow_total`, `nova_authority_deny_total`)
- `emit_authority_audit()` logs + writes to DB + records metrics

### Phase D: Quarantine Evaluation
- No quarantine needed - semantics are clear
- Replay: PARTIAL (authority complete, client missing)
- Predictions: READ_ONLY (appropriate for advisory-only)

### Phase E: Registry Update
- CAP-001 (replay): authority=true, authority_wired=true
- CAP-004 (predictions): authority=true, audit_replay=true, state=READ_ONLY
- Gap summary updated: blocking_gaps reduced

### Phase F: CI Guards
Added to `capability_registry_enforcer.py`:
- `authority-guard` command
- `check_authority_guard()` function
- `scan_all_for_authority_violations()` function

## Files Modified

| File | Change |
|------|--------|
| docs/governance/PERMISSION_TAXONOMY_V1.md | Added capability permissions |
| backend/app/auth/authorization.py | Added ROLE_PERMISSIONS |
| backend/app/auth/authority.py | NEW - Authority enforcement |
| backend/app/api/predictions.py | RBAC v2 + audit |
| backend/app/api/runtime.py | RBAC v2 + audit |
| backend/app/api/guard.py | RBAC v2 + audit |
| backend/app/api/workers.py | RBAC v2 + audit |
| backend/app/api/v1_killswitch.py | RBAC v2 + audit |
| docs/capabilities/CAPABILITY_REGISTRY.yaml | State updates |
| scripts/ops/capability_registry_enforcer.py | authority-guard command |

## Verification

```bash
# Authority guard passes
python3 scripts/ops/capability_registry_enforcer.py authority-guard --scan-all
# Output: ✅ All checks passed
```

## Registry Status After

| Capability | State | Authority |
|------------|-------|-----------|
| replay (CAP-001) | PARTIAL | ✅ true |
| prediction_plane (CAP-004) | READ_ONLY | ✅ true |

## Reference

- PIN-307: CAP-006 Authentication Gateway Closure
- PIN-306: Capability Registry Governance
- PIN-271: RBAC Authority Separation

---

## Related PINs

- [PIN-307](PIN-307-.md)
- [PIN-306](PIN-306-.md)
- [PIN-271](PIN-271-.md)
