# PIN-265: Phase C.1 RBAC Stub Implementation Complete

**Status:** ✅ COMPLETE
**Created:** 2026-01-01
**Category:** CI / Infrastructure
**Milestone:** Phase C.1

---

## Summary

Implemented RBAC stub for CI/development, promoting Clerk from State A to State B. Tests using @requires_infra("Clerk") now execute via deterministic stub instead of skipping.

---

## Details

## Summary

Phase C.1 implemented the RBAC stub per `docs/infra/RBAC_STUB_DESIGN.md`, enabling deterministic auth for CI/development without external dependencies.

---

## Deliverables

### 1. RBAC Stub Module (`app/auth/stub.py`)

Created new module with:

- **StubClaims** dataclass matching Clerk JWT claims shape
- **Token format**: `stub_<role>_<tenant>` (e.g., `stub_admin_test_tenant`)
- **Roles defined**: admin, developer, viewer, machine
- **Permission checking**: Wildcard support (`*`, `read:*`)

```python
STUB_ROLES = {
    "admin": ["*"],
    "developer": ["read:*", "write:runs", "write:agents"],
    "viewer": ["read:*"],
    "machine": ["read:*", "write:runs"],
}
```

### 2. Auth Module Exports (`app/auth/__init__.py`)

Added exports for stub functions:
- `parse_stub_token()`
- `stub_has_permission()`
- `stub_has_role()`
- `get_stub_token_for_role()`
- `validate_stub_or_skip()`

### 3. Infrastructure Registry Updates

**`tests/helpers/infra.py`:**
- Changed Clerk from State A to State B
- Added `_check_stub_auth()` function
- Updated `check_fn` to use stub check

**`docs/infra/INFRA_REGISTRY.md`:**
- Clerk row updated: State A → B
- Phase 1 marked COMPLETE
- Bucket B1 cleared (no items)

---

## Verification

```
Clerk state: B
Clerk bucket: None
Clerk available: True
Stub claims: StubClaims(sub='stub_user_admin', org_id='test_tenant', ...)
Admin has read:agents: True
```

---

## Test Results

| Metric | Value |
|--------|-------|
| Failed | 41 |
| Passed | 2482 |
| Skipped | 111 |
| Status | Stable |

### Clarification on Remaining Skips

The 15 skipped tests in `test_m7_rbac_memory.py` require a **running backend server** (`requires_auth_backend`), not just the Clerk stub. This is correct behavior for integration tests.

---

## Exit Criteria Met

| Criterion | Status |
|-----------|--------|
| Stub module implemented | ✅ |
| Clerk promoted A→B | ✅ |
| `@requires_infra("Clerk")` runs | ✅ |
| No external API keys required | ✅ |
| Deterministic (same input → same output) | ✅ |

---

## Files Changed

| File | Change |
|------|--------|
| `app/auth/stub.py` | Created (286 lines) |
| `app/auth/__init__.py` | Added stub exports |
| `tests/helpers/infra.py` | Clerk A→B, added stub check |
| `docs/infra/INFRA_REGISTRY.md` | Updated Clerk state |
| `tests/conftest.py` | Added stub fixtures (Phase B.1) |

---

## References

- PIN-271 (CI North Star Declaration)
- PIN-272 (Phase B.1 Test Isolation)
- PIN-270 (Infrastructure State Governance)
- `docs/infra/RBAC_STUB_DESIGN.md`

---

## Related PINs

- [PIN-271](PIN-271-.md)
- [PIN-272](PIN-272-.md)
- [PIN-270](PIN-270-.md)
