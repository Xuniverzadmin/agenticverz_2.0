# PIN-318: Phase 1.2 — Authority & Boundary Hardening

**Status:** IN_PROGRESS
**Date:** 2026-01-06
**Category:** Governance / Security
**Phase:** Phase 1.2 (Blocking for Phase 2)
**Related PINs:** PIN-317, PIN-316

---

## Phase Declaration

> **Phase 1.2 Scope:** "Authority, Auth, Boundary Enforcement"

### Explicitly Forbidden:
- UI redesign
- Business logic changes
- Behavior expansion
- Feature work

### STOP Conditions:
- If a route's authority is ambiguous → STOP and clarify
- If audience semantics are unclear → STOP and define

### Purpose:
Authority must be explicit, enforced, and impossible to infer incorrectly.
No UI or API surface may rely on implicit trust.

---

## Task Checklist

### P1.2-0 — Phase Declaration
- [ ] P1.2-0.1 Lock Phase Intent

### P1.2-1 — Authority Model Formalization
- [ ] P1.2-1.1 Define Audiences
- [ ] P1.2-1.2 Define Roles

### P1.2-2 — Frontend Authority Enforcement (L1)
- [ ] P1.2-2.1 Harden ProtectedRoute
- [ ] P1.2-2.2 Explicit Route Classification
- [ ] P1.2-2.3 Remove Ghost Routes

### P1.2-3 — Backend Authority Enforcement (L2)
- [ ] P1.2-3.1 Inventory Founder APIs
- [ ] P1.2-3.2 Enforce Auth Middleware
- [ ] P1.2-3.3 Explicit Deny for Customer Tokens

### P1.2-4 — Boundary Verification
- [ ] P1.2-4.1 Authority Contract Check
- [ ] P1.2-4.2 Negative Path Tests

### P1.2-5 — Survey & Governance Update
- [ ] P1.2-5.1 Re-run BLCA & Authority Survey
- [ ] P1.2-5.2 Update Governance Artifacts

---

## Exit Criteria (ALL REQUIRED)

- [ ] `ProtectedRoute` enforces audience + role
- [ ] All founder APIs require auth + RBAC
- [ ] Customer tokens are explicitly denied from founder APIs
- [ ] No ghost or fallback routes remain
- [ ] Frontend and backend authority semantics match 1:1
- [ ] BLCA remains clean

---

## Execution Log

### 2026-01-06 — Phase 1.2 Start

Phase 1.2 initiated following Phase 1.1 completion (PIN-317).

Critical gaps from Phase 1.1 that this phase addresses:
- GAP-001: ProtectedRoute has no audience/role check
- GAP-002-006: 5 founder APIs have zero auth
- Ghost route `/dashboard` needs cleanup

---

## Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Authority Model | `docs/inventories/P1_2_AUTHORITY_MODEL.md` | Pending |
| Route Classifications | `docs/inventories/P1_2_ROUTE_CLASSIFICATIONS.md` | Pending |
| Backend Auth Audit | `docs/inventories/P1_2_BACKEND_AUTH_AUDIT.md` | Pending |
| Boundary Verification | `docs/inventories/P1_2_BOUNDARY_VERIFICATION.md` | Pending |
