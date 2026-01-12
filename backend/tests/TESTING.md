# Test Architecture Guide

**Status:** LOCKED
**Reference:** PIN-399 Phase-5
**Last Updated:** 2026-01-12

---

## Prime Rule

> **Tests must reinforce architecture, not encode temporary implementation details.**

Tests are documentation. Wrong names teach wrong models.

---

## Auth Test Layers

This codebase has **two complementary auth systems**. Tests for each live in different conceptual spaces.

### Layer 1: RBAC Gateway (L3/L4)

**Purpose:** Route-level access control

**Question answered:** "Can this principal access this route?"

**Components:**
- `AuthGatewayMiddleware` - Extracts principal from headers
- `RBACEngine` - Evaluates policies against principals
- `ActorContext` - Unified auth context

**Test files:**
```
tests/auth/test_rbac_engine.py
tests/auth/test_rbac_middleware.py
tests/auth/test_rbac_integration.py
tests/auth/test_rbac_path_mapping.py
tests/auth/test_actor.py
tests/auth/test_authorization.py
tests/auth/test_role_mapping.py
```

**Terminology (allowed):**
- `permission` (RBAC policies)
- `has_permission()` (Actor method)
- `check_permission()` (RBAC function)
- `PrincipalType.CONSOLE`, `PrincipalType.MACHINE`
- `operator_bypass` (RBAC exemption)

---

### Layer 2: Phase-5 TenantRole (L3/L4)

**Purpose:** Endpoint-level business authorization

**Question answered:** "Does this tenant member have the right role for this action?"

**Components:**
- `TenantRole` enum (VIEWER, MEMBER, ADMIN, OWNER)
- `require_role()` dependency
- `role_has_permission()` - Role-derived permissions

**Test files:**
```
tests/auth/test_role_guard.py
tests/api/test_founder_onboarding_force_complete.py
```

**Terminology (required):**
- `role` (not "permission" alone)
- `TenantRole.MEMBER` (not "admin user")
- `require_role()` (not "check_access")
- `RoleViolationError` (not "access denied")

---

## Terminology Rules

### BANNED (in new tests)

| Term | Replacement | Reason |
|------|-------------|--------|
| `permission` alone | `role` or `role-derived permission` | Confuses RBAC with Phase-5 |
| `admin user` | `user with ADMIN role` | Role is explicit |
| `superuser` | `founder` | Different auth system |
| `console access` | `UI surface` | Console != authority |
| `has_access` | `has_role` | Phase-5 uses roles |

### ALLOWED (legacy RBAC tests)

These terms are correct in RBAC layer tests:
- `has_permission()` - Actor method
- `permission` in `permission_gaps` - Skill context
- `PERMISSION_DENIED` - Error code
- `operator_bypass` - RBAC exemption

---

## Test File Naming

### Correct

```
test_role_guard.py           # Phase-5 role guards
test_onboarding_*.py         # Onboarding state machine
test_rbac_*.py               # RBAC gateway layer
test_{domain}_roles.py       # Domain-specific role tests
```

### Forbidden

```
test_permissions.py          # Ambiguous layer
test_admin_access.py         # Wrong terminology
test_console_auth.py         # Console != auth
test_user_rights.py          # Wrong mental model
```

---

## Test Class Naming

### Correct

```python
class TestRequireRole:        # Phase-5
class TestRoleViolation:      # Phase-5
class TestRBACEngine:         # RBAC
class TestActorPermissions:   # RBAC
```

### Forbidden

```python
class TestAdminPermissions:   # Mixes layers
class TestConsoleUser:        # Wrong model
class TestPrivilegedAccess:   # Vague
```

---

## Test Function Naming

Must answer: "What invariant is this test protecting?"

### Correct

```python
def test_member_cannot_approve_without_required_role():
def test_force_complete_requires_founder_auth():
def test_viewer_has_only_read_permissions():
```

### Forbidden

```python
def test_admin_can_do_everything():
def test_user_has_permissions():
def test_access_works():
```

---

## When to Add Tests

### Phase-5 TenantRole Tests

Add when:
- New role is introduced
- New permission is derived
- Endpoint gets new role guard
- Role subsumption rules change

Do NOT add:
- Tests that iterate routers to check guards (use CI scanner)
- Tests that mock request.state for roles (use dependency injection)

### RBAC Tests

Add when:
- New principal type
- New RBAC policy
- Route mapping changes
- Actor context changes

---

## CI Enforcement

### Test Terminology Lint

```bash
python scripts/ci/check_test_terminology.py
```

Warns on banned terms. Use `--strict` to fail.

### Role Guard Scanner

```bash
python scripts/ops/check_role_guards.py
```

Fails if mutating endpoints lack role guards.

---

## HYGIENE-001

> No test may assert behavior that the architecture already forbids structurally.

If a test fails after deletion and **no invariant breaks**, the test was noise.

---

## Reference

- PIN-399: Onboarding State Machine (Phase-4, Phase-5)
- PIN-271: RBAC Architecture Directive
- PIN-391: Authorization Constitution
