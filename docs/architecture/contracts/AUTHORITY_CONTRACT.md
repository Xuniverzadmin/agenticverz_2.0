# AUTHORITY CONTRACT

**Status:** ENFORCED
**Effective:** 2026-01-17
**Scope:** All database, auth, and tenant state operations
**Reference:** PIN-LIM Design Fix (Authority-Driven System)

---

## Prime Directive

> **Every critical decision must have a single declared authority, enforced at runtime, and visible to tooling.**

Authority is **declared**, not discovered. Inference is a violation.

---

## 1. Database Authority (DB_AUTHORITY)

### The Rule

> Alembic migrations MUST target the authoritative database (Neon). No inference, no fallback.

### Authority Assignment

| Database | Authority Level | Allowed Operations |
|----------|-----------------|-------------------|
| **Neon** | Authoritative | Migrations, canonical truth |
| **Local / Docker** | Non-authoritative | Schema experiments, tests |

### Enforcement

**Location:** `backend/alembic/env.py`

The DB Authority guard validates before any migration:

```python
def validate_db_authority() -> tuple[str, str]:
    db_authority = os.getenv("DB_AUTHORITY")
    database_url = os.getenv("DATABASE_URL", "")

    # Rule 1: Authority must be declared
    if not db_authority:
        raise RuntimeError("DB_AUTHORITY must be set (neon|local|test)")

    # Rule 2: Only 'neon' allowed for migrations
    if db_authority != "neon":
        raise RuntimeError(
            f"Alembic blocked: DB_AUTHORITY={db_authority} is not allowed. "
            "Only DB_AUTHORITY=neon is permitted."
        )

    # Rule 3: DATABASE_URL must match authority
    if "localhost" in database_url.lower() or "127.0.0.1" in database_url.lower():
        raise RuntimeError(
            "DB_AUTHORITY=neon but DATABASE_URL contains localhost. "
            "Authority and URL must match."
        )

    return db_authority, database_url
```

### Required Environment

```bash
# For migrations
export DB_AUTHORITY=neon
export DATABASE_URL=postgresql://...neon.tech/...
```

### Violation Response

```
DB AUTHORITY GATE: BLOCKED

DB_AUTHORITY={value} is not allowed for migrations.
Only DB_AUTHORITY=neon is permitted.

Set:
  export DB_AUTHORITY=neon
  export DATABASE_URL=<your-neon-connection-string>
```

---

## 2. Tenant State Authority (TenantStateResolver)

### The Rule

> Tenant `onboarding_state` is COMPUTED from account/user/binding readiness, never manually toggled.

### Authority Source

**Location:** `backend/app/domain/tenants/state_resolver.py`

The `TenantStateResolver` is the AUTHORITATIVE source of tenant state:

```python
class TenantStateResolver:
    """Derives tenant state from account/user readiness."""

    async def resolve(self, tenant_id: str) -> TenantState:
        """
        Derive state from:
        1. Does tenant exist?
        2. Is tenant archived/suspended?
        3. Does account exist?
        4. Does at least one user exist?
        5. Is at least one user verified?
        6. Are RBAC bindings in place?
        """
```

### State Derivation

| State | Value | Derivation Rule |
|-------|-------|-----------------|
| CREATED | 0 | Tenant record exists |
| CONFIGURING | 1 | Account created |
| VALIDATING | 2 | At least one user exists |
| PROVISIONING | 3 | User verified, bindings created |
| COMPLETE | 4 | ≥1 ACTIVE user bound, billing ok |
| SUSPENDED | 5 | Billing hold or policy violation |
| ARCHIVED | 6 | Soft deleted |

### State Properties

```python
@property
def is_operational(self) -> bool:
    """Only COMPLETE (4) allows full operations."""
    return self == TenantState.COMPLETE

@property
def allows_write(self) -> bool:
    """Only COMPLETE tenants can write."""
    return self == TenantState.COMPLETE
```

### Usage

```python
# Gate function for endpoints requiring full tenant operations
from app.domain.tenants import require_tenant_ready

state = await require_tenant_ready(session, tenant_id)
# Raises HTTPException(403) if not COMPLETE
```

### Enforcement

- **Database column:** `tenants.onboarding_state` is a CACHE
- **Cache updates:** Only via `TenantStateResolver.resolve_and_cache()`
- **No direct updates:** UPDATE statements on `onboarding_state` are forbidden

---

## 3. Auth Plane Authority (JWT XOR API Key)

### The Rule

> Authentication planes are mutually exclusive. JWT XOR API Key. Both = HARD FAIL. Neither = HARD FAIL.

### Authority Source

**Location:** `backend/app/auth/gateway.py`

```python
async def authenticate(
    self,
    authorization_header: Optional[str],
    api_key_header: Optional[str],
) -> GatewayResult:
    # Check for mutual exclusivity FIRST
    has_jwt = authorization_header is not None
    has_api_key = api_key_header is not None

    if has_jwt and has_api_key:
        # HARD FAIL: Both headers present
        return error_mixed_auth()

    if not has_jwt and not has_api_key:
        # HARD FAIL: No auth provided
        return error_missing_auth()
```

### Auth Planes

| Plane | Header | Provider | Context Type |
|-------|--------|----------|--------------|
| **HUMAN** | `Authorization: Bearer <jwt>` | Clerk (RS256) | `HumanAuthContext` |
| **MACHINE** | `X-AOS-Key: <api_key>` | API Key Service | `MachineCapabilityContext` |
| **FOUNDER** | `Authorization: Bearer <fops>` | FOPS (HS256) | `FounderAuthContext` |

### Routing Rules

1. **Issuer-based routing:** Tokens route by `iss` claim, not `alg` header
2. **No fallbacks:** Unknown issuer → REJECT
3. **No grace periods:** Expired → REJECT

### Debug Endpoint

**GET /debug/auth/context**

Returns the interpreted auth context:

```json
{
  "auth_plane": "HUMAN",
  "actor_id": "user_xxx",
  "actor_type": "human",
  "tenant_id": "tenant_123",
  "tenant_state": "COMPLETE",
  "tenant_state_value": 4,
  "context_type": "HumanAuthContext"
}
```

**GET /debug/auth/planes**

Returns auth plane reference documentation.

**GET /debug/auth/tenant-states**

Returns tenant state definitions and derivation rules.

---

## 4. Authority Violations

### Detection

| Violation | Detection Method |
|-----------|------------------|
| DB Authority mismatch | `alembic/env.py` gate |
| Tenant state manual update | Code review, trigger (future) |
| Mixed auth headers | Gateway middleware |
| Missing auth | Gateway middleware |

### Response

All authority violations are **HARD FAILS**:

- No fallbacks
- No inference
- No "fixing" by guessing
- Clear error message with exact violation

---

## 5. Claude/LLM Rules

### Forbidden Behaviors

| Action | Reason |
|--------|--------|
| Inferring database from data age | Authority is declared |
| Checking "both databases" | Violates single authority |
| Assuming tenant state from UI | State is computed |
| Guessing auth plane | Planes are mutually exclusive |

### Required Behaviors

| Action | Implementation |
|--------|----------------|
| Check DB_AUTHORITY before queries | Explicit env check |
| Use TenantStateResolver for state | Never raw column read |
| Route auth by issuer only | Never by `alg` header |
| Report ambiguity as error | Never resolve by inference |

---

## 6. Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│              AUTHORITY QUICK REFERENCE                      │
├─────────────────────────────────────────────────────────────┤
│  DB Authority:                                              │
│    - Migrations: DB_AUTHORITY=neon ONLY                     │
│    - Enforcement: alembic/env.py gate                       │
│                                                             │
│  Tenant State:                                              │
│    - Source: TenantStateResolver.resolve()                  │
│    - Rule: COMPUTED from account/user/bindings              │
│    - Column: onboarding_state is CACHE only                 │
│                                                             │
│  Auth Plane:                                                │
│    - Rule: JWT XOR API Key (mutual exclusivity)             │
│    - Human: Authorization: Bearer <clerk_jwt>               │
│    - Machine: X-AOS-Key: <api_key>                          │
│    - Both = FAIL, Neither = FAIL                            │
│                                                             │
│  Debug Endpoints:                                           │
│    - GET /debug/auth/context                                │
│    - GET /debug/auth/planes                                 │
│    - GET /debug/auth/tenant-states                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Related Documents

| Document | Purpose |
|----------|---------|
| `docs/runtime/DB_AUTHORITY.md` | DB authority rules |
| `docs/governance/DB_AUTH_001_INVARIANT.md` | DB authority invariant |
| `docs/architecture/AUTH_SEMANTIC_CONTRACT.md` | Auth contract |
| `backend/app/domain/tenants/state_resolver.py` | Tenant state implementation |
| `backend/app/auth/gateway.py` | Auth gateway implementation |
| `backend/alembic/env.py` | DB authority gate |
