# Phase 2B — Batch 1 Structural Diff Preview

**Status:** PENDING APPROVAL
**Created:** 2025-12-30
**Reference:** PIN-250, PHASE2_ALIGNMENT_PLAN_v2.md

---

## Executive Summary

This document provides the **Structural Diff Preview** required before Phase 2B execution can be approved.

**Batch 1 Scope:** 2 API files with DB writes (guard.py, onboarding.py)
**Total DB Write Sites:** 22
**Proposed New Services:** 2 (GuardWriteService, UserWriteService)

---

## Batch Independence Report

**Validation performed:** 2025-12-30
**Method:** grep for cross-batch imports + manual review

### Findings

| Check | Result |
|-------|--------|
| Batch 1 files imported by Batch 2 | NONE |
| Batch 1 files imported by Batch 3 | NONE |
| Batch 2 files imported by Batch 3 | Not yet validated |
| Import-time side effects in Batch 1 | NONE |

### Decision

**Proceed as planned** — Batch 1 files are independently modifiable.

### Rationale

- guard.py, onboarding.py, customer_visibility.py, tenants.py have zero cross-imports
- No other API files import from these
- All 4 files pass import-time safety check

---

## Batch 1 File Classification

| File | DB Writes | Status | Notes |
|------|-----------|--------|-------|
| `api/guard.py` | 12 sites | **IN SCOPE** | KillSwitch, Incident, IncidentEvent writes |
| `api/onboarding.py` | 10 sites | **IN SCOPE** | User, Tenant, TenantMembership writes |
| `api/customer_visibility.py` | 0 | **OUT OF SCOPE** | Read-only (raw SQL) |
| `api/tenants.py` | 0 | **OUT OF SCOPE** | Already delegates to TenantService |

**Actual Batch 1 Files:** 2 (guard.py, onboarding.py)

---

## Structural Diff Table: guard.py

| Line | DB Write | Model | New Owner | Layer | Before | After |
|------|----------|-------|-----------|-------|--------|-------|
| 461-462 | session.add(state), session.commit() | KillSwitchState | guard_write_service.activate_killswitch() | L4 | direct | via service |
| 494-495 | session.add(state), session.commit() | KillSwitchState | guard_write_service.deactivate_killswitch() | L4 | direct | via service |
| 651-652 | session.add(incident), session.commit() | Incident | guard_write_service.acknowledge_incident() | L4 | direct | via service |
| 675-676 | session.add(incident), session.commit() | Incident | guard_write_service.resolve_incident() | L4 | direct | via service |
| 1244-1245 | session.add(state), session.commit() | KillSwitchState | guard_write_service.freeze_api_key() | L4 | direct | via service |
| 1269-1270 | session.add(state), session.commit() | KillSwitchState | guard_write_service.unfreeze_api_key() | L4 | direct | via service |
| 2254 | session.add(incident) | Incident | guard_write_service.create_demo_incident() | L4 | direct | via service |
| 2272 | session.add(event) | IncidentEvent | guard_write_service.create_demo_incident() | L4 | direct | via service |
| 2274 | session.commit() | - | guard_write_service.create_demo_incident() | L4 | direct | via service |
| 2306 | session.add(incident) | Incident | guard_write_service.create_demo_incident() | L4 | direct | via service |
| 2323 | session.add(event) | IncidentEvent | guard_write_service.create_demo_incident() | L4 | direct | via service |
| 2325 | session.commit() | - | guard_write_service.create_demo_incident() | L4 | direct | via service |

**Summary for guard.py:**
- 12 DB write sites → 6 service methods
- New service: `guard_write_service.py` (~150 LOC)
- Models affected: KillSwitchState, Incident, IncidentEvent

---

## Structural Diff Table: onboarding.py

| Line | DB Write | Model | New Owner | Layer | Before | After |
|------|----------|-------|-----------|-------|--------|-------|
| 246-248 | session.add(user), session.commit(), session.refresh(user) | User | user_write_service.create_user() | L4 | direct | via service |
| 256-258 | session.add(user), session.commit(), session.refresh(user) | User | user_write_service.update_user_login() | L4 | direct | via service |
| 293-295 | session.add(user), session.commit(), session.refresh(user) | User | user_write_service.create_user() | L4 | direct | via service |
| 303-305 | session.add(user), session.commit(), session.refresh(user) | User | user_write_service.update_user_login() | L4 | direct | via service |
| 341-343 | session.add(tenant), session.commit(), session.refresh(tenant) | Tenant | tenant_service.create_tenant() | L4 | direct | via service (existing) |
| 351-358 | session.add(membership), session.add(user), session.commit() | TenantMembership, User | tenant_service.create_membership_with_default() | L4 | direct | via service (existing) |

**Summary for onboarding.py:**
- 10 DB write sites → 4 service methods
- New service: `user_write_service.py` (~100 LOC)
- Existing service extension: `tenant_service.py` (+2 methods, ~50 LOC)
- Models affected: User, Tenant, TenantMembership

---

## Proposed Service Architecture

### New: `app/services/guard_write_service.py`

```python
# Layer: L4 — Domain Engine
# Product: AI Console (Guard)
# Role: DB write delegation for Guard API

class GuardWriteService:
    """
    DB write operations for Guard Console.

    No business logic — just delegation + session management.
    """

    def __init__(self, session: Session):
        self.session = session

    def activate_killswitch(self, tenant_id: str, reason: str) -> KillSwitchState:
        """Create or update killswitch state to frozen."""
        ...

    def deactivate_killswitch(self, tenant_id: str) -> KillSwitchState:
        """Unfreeze killswitch state."""
        ...

    def freeze_api_key(self, key_id: str, tenant_id: str, reason: str) -> KillSwitchState:
        """Freeze an API key."""
        ...

    def unfreeze_api_key(self, key_id: str) -> KillSwitchState:
        """Unfreeze an API key."""
        ...

    def acknowledge_incident(self, incident_id: str) -> Incident:
        """Mark incident as acknowledged."""
        ...

    def resolve_incident(self, incident_id: str) -> Incident:
        """Mark incident as resolved."""
        ...

    def create_demo_incident(
        self,
        tenant_id: str,
        test_type: str,
        **kwargs
    ) -> Tuple[Incident, List[IncidentEvent]]:
        """Create demo incident for onboarding verification."""
        ...
```

**Estimated LOC:** ~150
**Layer:** L4 (Domain Engine)

---

### New: `app/services/user_write_service.py`

```python
# Layer: L4 — Domain Engine
# Product: system-wide
# Role: DB write delegation for User management

class UserWriteService:
    """
    DB write operations for User management.

    No business logic — just delegation + session management.
    """

    def __init__(self, session: Session):
        self.session = session

    def create_user(
        self,
        email: str,
        name: Optional[str] = None,
        clerk_user_id: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> User:
        """Create a new user."""
        ...

    def update_user_login(self, user: User) -> User:
        """Update user's last_login_at timestamp."""
        ...
```

**Estimated LOC:** ~100
**Layer:** L4 (Domain Engine)

---

### Extension: `app/services/tenant_service.py`

Extend existing TenantService with:

```python
def create_tenant(
    self,
    name: str,
    slug: str,
    plan: str = "free",
    status: str = "active",
) -> Tenant:
    """Create a new tenant."""
    ...

def create_membership_with_default(
    self,
    tenant: Tenant,
    user_id: str,
    role: str = "owner",
    set_as_default: bool = True,
) -> TenantMembership:
    """Create membership and optionally set as user's default tenant."""
    ...
```

**Estimated LOC:** ~50 additional
**Layer:** L4 (existing)

---

## Rollback Criteria (Batch 1)

After Batch 1 completion, verify:

- [ ] All existing tests pass
- [ ] No `session.add()` or `session.commit()` in guard.py
- [ ] No `session.add()` or `session.commit()` in onboarding.py
- [ ] GuardWriteService is < 200 LOC
- [ ] UserWriteService is < 200 LOC
- [ ] Each service file has L4 layer header
- [ ] Import paths: API → L4 Service → L6 (no API → L6)
- [ ] Minimum Runnable Definition checks pass

---

## Call Path Changes

### Before (L2 Collapse)

```
guard.py (L2) ──► session.add() (L6)
                ──► session.commit() (L6)

onboarding.py (L2) ──► session.add() (L6)
                    ──► session.commit() (L6)
```

### After (Proper Layering)

```
guard.py (L2) ──► guard_write_service (L4) ──► session (L6)

onboarding.py (L2) ──► user_write_service (L4) ──► session (L6)
                   ──► tenant_service (L4) ──► session (L6)
```

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Service introduces business logic | Service methods are pure delegation (no conditionals) |
| Session scope mismatch | Services receive session via dependency injection |
| Cache invalidation timing | Cache invalidation remains in API layer (after service call) |
| Transaction boundary changes | Each service method owns one commit (same as before) |

---

## Approval Request

This preview has been produced per Phase 2B requirements.

**Questions for approval:**

1. Are the proposed service boundaries correct?
2. Should GuardWriteService be split into separate KillSwitchService and IncidentService?
3. Should UserWriteService be merged into existing TenantService?

**Awaiting human approval before execution.**

---

## References

- PIN-250: Structural Truth Extraction Lifecycle
- PHASE2_ALIGNMENT_PLAN_v2.md: Phase 2 Execution Plan
- STRUCTURAL_TRUTH_MAP.md: Phase 1 Findings
