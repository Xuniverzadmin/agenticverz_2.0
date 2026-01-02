# RBAC Stub Design for CI

**Status:** PROPOSED
**Created:** 2026-01-01
**Purpose:** Promote Clerk from State A → State B
**Reference:** PIN-270 (Infra Governance), PIN-271 (CI North Star)

---

## Goal

Create a minimal local RBAC stub that:

1. Exercises the same contract as Clerk
2. Requires no external API keys
3. Is deterministic (same input → same output)
4. Enables all `@requires_infra("Clerk")` tests to run

---

## What This Is NOT

| Anti-Goal | Reason |
|-----------|--------|
| Full OAuth flow | CI doesn't need real OAuth |
| Session management | Stateless is sufficient |
| User database | Deterministic roles are enough |
| Clerk SDK integration | Contract shape only |

---

## Contract Shape (Must Match Clerk)

### 1. Authentication Header

**Production (Clerk):**
```
X-AOS-Key: <jwt_or_api_key>
```

**Stub:**
```
X-AOS-Key: stub_<role>_<tenant>
```

Example: `X-AOS-Key: stub_admin_tenant123`

### 2. Claims Structure

The stub must produce claims matching Clerk's shape:

```python
@dataclass
class StubClaims:
    sub: str          # Subject (user ID)
    org_id: str       # Organization/tenant ID
    roles: list[str]  # Role names
    permissions: list[str]  # Permission strings
    exp: int          # Expiration timestamp
    iat: int          # Issued at timestamp
```

### 3. Role Definitions

| Role | Permissions | Use Case |
|------|-------------|----------|
| `admin` | `*` | Full access |
| `developer` | `read:*`, `write:runs`, `write:agents` | Normal user |
| `viewer` | `read:*` | Read-only access |
| `machine` | `read:*`, `write:runs` | API key access |

---

## Implementation

### File Location

```
backend/app/auth/stub.py
```

### Core Function

```python
def parse_stub_token(token: str) -> Optional[StubClaims]:
    """Parse a stub token into claims.

    Stub tokens have format: stub_<role>_<tenant>
    Example: stub_admin_tenant123

    Returns None if token doesn't match stub format.
    """
    if not token.startswith("stub_"):
        return None

    parts = token.split("_", 2)
    if len(parts) != 3:
        return None

    _, role, tenant = parts

    # Validate role
    if role not in STUB_ROLES:
        return None

    return StubClaims(
        sub=f"stub_user_{role}",
        org_id=tenant,
        roles=[role],
        permissions=STUB_ROLES[role],
        exp=int(time.time()) + 3600,
        iat=int(time.time()),
    )
```

### Integration Point

The auth middleware should:

1. Try Clerk validation first (if configured)
2. Fall back to stub parsing (if not in production)
3. Never mix both in the same request

```python
def get_current_user(request: Request) -> Claims:
    token = request.headers.get("X-AOS-Key")

    if not token:
        raise HTTPException(401, "Missing auth header")

    # Production: use Clerk
    if settings.CLERK_ENABLED:
        return validate_clerk_token(token)

    # Development/CI: use stub
    claims = parse_stub_token(token)
    if claims:
        return claims

    raise HTTPException(401, "Invalid token")
```

---

## Configuration

### Environment Variables

```bash
# Enable stub auth (CI/development only)
AUTH_STUB_ENABLED=true

# Disable Clerk (when not configured)
CLERK_ENABLED=false
```

### Activation Rules

| Environment | CLERK_ENABLED | AUTH_STUB_ENABLED | Behavior |
|-------------|---------------|-------------------|----------|
| Production | true | false | Clerk only |
| Staging | true | true | Clerk + stub fallback |
| CI | false | true | Stub only |
| Development | false | true | Stub only |

---

## Test Fixtures

### conftest.py Addition

```python
@pytest.fixture
def stub_admin_headers():
    """Headers for admin access in tests."""
    return {"X-AOS-Key": "stub_admin_test_tenant"}

@pytest.fixture
def stub_developer_headers():
    """Headers for developer access in tests."""
    return {"X-AOS-Key": "stub_developer_test_tenant"}

@pytest.fixture
def stub_viewer_headers():
    """Headers for read-only access in tests."""
    return {"X-AOS-Key": "stub_viewer_test_tenant"}

@pytest.fixture
def stub_machine_headers():
    """Headers for machine/API access in tests."""
    return {"X-AOS-Key": "stub_machine_test_tenant"}
```

---

## Tests to Enable

After implementing this stub, these tests should run (not skip):

| Test File | Current Behavior | After Stub |
|-----------|------------------|------------|
| `test_integration.py` | Skip (403) | Run |
| `test_m7_rbac_memory.py` | Skip (403) | Run |
| `tests/lit/test_l2_l6_api_platform.py` | Partial | Full |
| Any `@requires_infra("Clerk")` | Skip | Run |

---

## Success Criteria

1. **All RBAC tests run** (not skip)
2. **No external dependencies** in CI
3. **Deterministic behavior** (same test input → same result)
4. **Contract compatibility** (stub claims match Clerk shape)

---

## Implementation Checklist

- [ ] Create `backend/app/auth/stub.py`
- [ ] Add `StubClaims` dataclass
- [ ] Implement `parse_stub_token()`
- [ ] Add environment variable handling
- [ ] Update auth middleware with fallback
- [ ] Add test fixtures to conftest.py
- [ ] Update INFRA_REGISTRY.md (Clerk A → B)
- [ ] Verify all `@requires_infra("Clerk")` tests run
- [ ] Create PIN documenting completion

---

## References

- PIN-270 (Infrastructure State Governance)
- PIN-271 (CI North Star)
- INFRA_REGISTRY.md
- `backend/app/auth/` (existing auth code)
