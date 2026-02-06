# PIN-335: Admin Surface Capability Closure Report

**Status:** COMPLETE
**Date:** 2026-01-06
**Type:** SURGICAL CLOSURE (minimal changes)
**Predecessor:** PIN-334 (System-Level Capability Re-Audit)

---

## Executive Summary

This PIN closes the **last remaining gap** identified in PIN-334 by mapping legacy `/admin` HTTP routes to existing capabilities and ensuring execution envelope emission.

### CONCLUSION: System capability universe is now **CLOSED**.

All executable paths are mapped to declared capabilities. All EXECUTE-power paths emit attribution envelopes.

---

## 1. Routes Mapped

| Route | Method | Capability | Invoker | Scope | Audit |
|-------|--------|------------|---------|-------|-------|
| `/admin/retry` | POST | **CAP-019** (Run Management) | FOUNDER | TENANT | MANDATORY |
| `/admin/failed-runs` | GET | **CAP-001** (Replay & Activity) | FOUNDER | TENANT | OPTIONAL |
| `/admin/rerun` | POST | N/A | DISABLED | N/A | EXCLUDED |

---

## 2. CAP Reuse Justification

**No new capability was created.**

| Route | Why Existing CAP Works |
|-------|------------------------|
| `/admin/retry` | Creates new WorkerRun → same semantics as CAP-019 (Run Management) routes |
| `/admin/failed-runs` | Lists failed runs → same semantics as CAP-001 (Replay & Activity) observation routes |

**Principle:** Admin routes exercise the same powers as SDK/API routes — they differ only in invoker (FOUNDER vs CUSTOMER), not in capability.

---

## 3. Envelope Emission Confirmation

### /admin/retry Envelope

```python
# backend/app/main.py:1332-1345
envelope = ExecutionEnvelopeFactory.create_admin_envelope(
    subject="founder",
    tenant_id=original_run.tenant_id,
    route="/admin/retry",
    raw_input={"run_id": payload.run_id, "reason": payload.reason},
    resolved_plan={
        "action": "create_retry_run",
        "original_run_id": original_run.id,
        "tenant_id": original_run.tenant_id,
    },
    reason_code=payload.reason or "manual_retry",
)
emit_envelope(envelope)  # Non-blocking, never fails execution
```

### Envelope Schema (PIN-335 additions)

```python
# backend/app/auth/execution_envelope.py
class CapabilityId(str, Enum):
    CAP_019 = "CAP-019"  # Run Management (PIN-335: Admin retry)
    ...

class ExecutionVector(str, Enum):
    HTTP_ADMIN = "HTTP_ADMIN"  # PIN-335: Admin HTTP routes
    ...
```

### /admin/failed-runs

No envelope required — READ_ONLY power, no state mutation.

---

## 4. Updated Negative Assertions

| Assertion | PIN-334 Answer | PIN-335 Answer |
|-----------|----------------|----------------|
| **5.1 Hidden Capability** | YES (2 unmapped routes) | **NO** |
| **5.2 Undeclared Authority** | YES (/admin/retry) | **NO** |
| **5.3 Non-enveloped Execution** | YES (/admin/retry) | **NO** |

All assertions now return **NO**.

---

## 5. Files Modified

| File | Change |
|------|--------|
| `docs/capabilities/CAPABILITY_REGISTRY_UNIFIED.yaml` | Added `/admin/retry` to CAP-019, `/admin/failed-runs` to CAP-001 |
| `backend/app/auth/execution_envelope.py` | Added `CAP_019` enum, `HTTP_ADMIN` vector, `create_admin_envelope()` factory |
| `backend/app/main.py` | Added envelope emission to `/admin/retry` |

---

## 6. Authority Model

| Route | Auth Mechanism | Access Level |
|-------|----------------|--------------|
| `/admin/retry` | `Depends(verify_api_key)` | FOUNDER-only (AOS_API_KEY) |
| `/admin/failed-runs` | `Depends(verify_api_key)` | FOUNDER-only (AOS_API_KEY) |

No new RBAC rules added — existing `verify_api_key` dependency reused.

---

## 7. Behavioral Verification

| Guarantee | Status |
|-----------|--------|
| PB-S1 (Immutable History) | PRESERVED — retry creates NEW run |
| No Logic Change | VERIFIED — only envelope emission added |
| Non-Blocking | VERIFIED — `emit_envelope()` never blocks |

---

## 8. Closure Statement

> **System capability universe is now closed.**
>
> Every executable HTTP route, worker path, CLI command, SDK method, and auto-execute trigger is mapped to a declared FIRST_CLASS capability or SYSTEM SUBSTRATE.
>
> Every EXECUTE-power path emits an execution envelope for attribution.
>
> No shadow execution surfaces remain.

---

## 9. Governance Compliance

| Constraint | Satisfied |
|------------|-----------|
| ❌ No new "Admin" capability created | ✅ |
| ❌ No runtime behavior change | ✅ |
| ❌ No approval/gating/UI controls added | ✅ |
| ❌ No recovery logic refactored | ✅ |
| ❌ No PB-S1 weakening | ✅ |
| ✅ Reuse existing FIRST_CLASS CAPs only | ✅ |
| ✅ Ensure execution envelopes emitted | ✅ |
| ✅ Founder-only authority, tenant-scoped | ✅ |

---

**PIN-335 Complete. Capability governance is DONE.**
