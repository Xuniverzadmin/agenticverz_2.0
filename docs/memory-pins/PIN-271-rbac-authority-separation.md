# PIN-271: RBAC Authority Separation

**Status:** ACTIVE (Governance Invariant)
**Created:** 2026-01-02
**Category:** Architecture / Security / RBAC
**Severity:** CONSTITUTIONAL

---

## Summary

Codifies the separation of identity, authorization, and execution context in RBAC. Establishes that Clerk is an identity provider, not an authorization engine, and that all actors (external, internal, system) must flow through the same AuthorizationEngine.

---

## The Problem Solved

The current RBAC implementation conflates three orthogonal concerns:

1. **Identity Provider** (Clerk) - Who is this?
2. **Authorization Semantics** (roles, permissions) - What can they do?
3. **Execution Context** (local dev, CI, production) - Where are we running?

This causes:

| Issue | Impact |
|-------|--------|
| Stubs fake Clerk tokens | CI doesn't test real authorization |
| JWT claim inspection scattered | Security review impossible |
| No actor type classification | Internal products treated like customers |
| CI skips RBAC | Production semantics differ from tests |

---

## The Solution

### Prime Directive

> **RBAC must be provider-agnostic and environment-aware, but semantics must be identical everywhere.**

- Clerk is **identity** (L3 Boundary Adapter)
- AOS owns **authorization** (L4 Domain Engine)
- Environment decides **token source**, not rules

---

## Architecture Model

### Actor Classification

All actors must be explicitly classified:

| ActorType | Description | Example |
|-----------|-------------|---------|
| EXTERNAL_PAID | Paying customers | Customer tenants |
| EXTERNAL_TRIAL | Beta, trial users | Early adopters |
| INTERNAL_PRODUCT | Internal products | Xuniverz, AI Console, M12 agents |
| OPERATOR | Founders, ops team | Admin access |
| SYSTEM | CI, workers, automation | Machine actors |

### Identity Sources

Identity can come from multiple sources, all producing ActorContext:

| Source | Provider | Usage |
|--------|----------|-------|
| CLERK | Clerk JWT | Production customer auth |
| OIDC | Keycloak/generic | Enterprise SSO |
| INTERNAL | Service-to-service | Internal APIs |
| SYSTEM | Machine tokens | CI, workers |
| DEV | Dev headers | Local development |

---

## Component Layering

```
┌─────────────────────────────────────────────────┐
│                L2: Product APIs                 │
│           (consumes ActorContext)               │
└────────────────────────┬────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│            L4: AuthorizationEngine              │
│   Single source of truth for all decisions      │
│   - compute_permissions(actor) → actor          │
│   - authorize(actor, resource, action) → result │
└────────────────────────┬────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│             L3: IdentityAdapters                │
│   - ClerkAdapter (JWT → ActorContext)           │
│   - SystemIdentityAdapter (machine tokens)      │
│   - DevIdentityAdapter (dev headers)            │
└────────────────────────┬────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│             L6: ActorContext                    │
│   Immutable, canonical actor representation     │
│   - actor_id, actor_type, source               │
│   - tenant_id, roles, permissions              │
└─────────────────────────────────────────────────┘
```

---

## Key Invariants

### INV-001: No JWT Logic Outside Adapters

JWT parsing, validation, and claim extraction must only occur in:
- `app/auth/identity_adapter.py`
- `app/auth/clerk_provider.py`

**Pattern banned everywhere else:**
```python
# FORBIDDEN outside adapters
jwt.decode(...)
claims["sub"]
payload["org_id"]
token_data["roles"]
```

### INV-002: All Auth Checks Use ActorContext

Every authorization check function must accept `actor: ActorContext`:

```python
# CORRECT
def authorize(actor: ActorContext, resource: str, action: str) -> bool:
    ...

# FORBIDDEN
def authorize(user_id: str, roles: List[str]) -> bool:
    ...
```

### INV-003: System Actors Are Real Actors

CI and workers must NOT use stub tokens that fake Clerk. They must use:

```python
# CORRECT - Real system actor
SYSTEM_ACTORS["ci"]  # Returns ActorContext with ActorType.SYSTEM

# FORBIDDEN - Fake Clerk token
X-AOS-Key: stub-token-that-looks-like-clerk
```

### INV-004: Same Rules Everywhere

Authorization rules must be identical in all environments:

| Environment | Identity Source | Authorization |
|-------------|-----------------|---------------|
| Production | ClerkAdapter | AuthorizationEngine |
| CI | SystemIdentityAdapter | AuthorizationEngine |
| Dev | DevIdentityAdapter | AuthorizationEngine |

---

## CI Enforcement Rules

```yaml
rules:
  - id: RBAC-001
    name: No JWT logic outside adapters
    pattern: "jwt\\.|decode.*token|verify.*token"
    allowed_in:
      - app/auth/identity_adapter.py
      - app/auth/clerk_provider.py

  - id: RBAC-002
    name: No direct claim access
    pattern: "claims\\[|payload\\[|token_data\\["
    allowed_in:
      - app/auth/identity_adapter.py

  - id: RBAC-003
    name: All auth checks use ActorContext
    pattern: "def authorize|def check_permission"
    required_param: "actor: ActorContext"

  - id: RBAC-004
    name: No X-Roles header in production
    pattern: 'headers\\.get\\(["\']X-Roles'
    allowed_in:
      - tests/
```

---

## Migration Path

### Phase 1: Create Core Components (No Breaking Changes)

1. Create `app/auth/actor.py` with ActorContext
2. Create `app/auth/authorization.py` with AuthorizationEngine
3. Create `app/auth/identity_adapter.py` with protocol + adapters
4. Add comprehensive tests

### Phase 2: Parallel Path (Shadow Mode)

1. Add identity chain alongside existing middleware
2. Log comparison: old decision vs new decision
3. Validate 100% alignment before switching

### Phase 3: Switch Over

1. Replace `extract_roles_from_request()` with identity chain
2. Replace RBAC_MATRIX checks with AuthorizationEngine
3. Remove stub token format (use SystemIdentityAdapter)
4. Update all tests to use new API

### Phase 4: Cleanup

1. Remove legacy token parsing code
2. Remove stub.py (replaced by SystemIdentityAdapter)
3. Update documentation

---

## Success Criteria

After implementation:

- [ ] All authorization decisions go through AuthorizationEngine
- [ ] No JWT parsing outside identity adapters
- [ ] CI uses SystemIdentityAdapter (real actor, not fake token)
- [ ] Same authorization rules in all environments
- [ ] Actor types explicitly classified
- [ ] 100% test coverage on authorization engine
- [ ] Shadow audit shows 0 divergence before switchover

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `docs/governance/RBAC_AUTHORITY_SEPARATION_DESIGN.md` | Full design document |
| `docs/governance/PERMISSION_TAXONOMY_V1.md` | Permission definitions |
| `docs/memory-pins/PIN-271-rbac-authority-separation.md` | This PIN |
| `docs/memory-pins/INDEX.md` | Updated with PIN-271 |
| `CLAUDE.md` | RBAC Directive added |

---

## Related PINs

- PIN-265 (RBAC Stub Implementation) - Current state being improved
- PIN-270 (Engineering Authority) - Governance principles
- PIN-266 (Infra Registry) - Infrastructure conformance model

---

## Design Reference

Full implementation details in: `docs/governance/RBAC_AUTHORITY_SEPARATION_DESIGN.md`

Includes:
- ActorContext dataclass (complete code)
- IdentityAdapter protocol (complete code)
- AuthorizationEngine (complete code)
- IdentityChain (complete code)
- Migration phases
- CI invariant rules

---

## Authority Hierarchy

This PIN establishes RBAC architecture at **Priority 3** (Infrastructure conformance truth) per PIN-270:

| Priority | Authority |
|----------|-----------|
| 1 | Layer Model (L1-L8) - immutable |
| 2 | Domain boundaries - L4 owns authorization |
| **3** | **Infrastructure conformance truth** |
| 4 | Session Playbook |
| 5 | Memory PINs |
| 6 | Tests |
| 7 | CI tooling |

**Rule:** If tests contradict this design, fix the tests.

---

## Invariant Lock

> **Identity is not authorization.**
> **Stubs are not actors.**
> **Environment decides source, not rules.**
> **Same authorization path everywhere.**
