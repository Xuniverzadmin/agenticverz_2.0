# Three-Mode Authority System

**Status:** RATIFIED
**Version:** 1.0.0
**Created:** 2026-01-18
**PIN Reference:** PIN-440
**Authority:** Authentication / Customer Integrations

---

## Executive Summary

The Three-Mode Authority System provides a controlled mechanism for testing customer integration APIs (`/api/v1/cus/*`) across different deployment contexts without compromising production security.

**Core Principle:**

> **Authority is orthogonal.** Auth Authority, DB Authority, and Cost Authority are independent variables that can be combined safely without coupling.

---

## The Problem

Testing customer integration APIs required navigating a complex interplay of:

1. **Database Authority** - Which database holds canonical truth?
2. **Authentication Authority** - Who validates identity?
3. **Environment Safety** - Can sandbox credentials be used?

The original implementation conflated these concerns:
- `DB_AUTHORITY=neon` implied production auth was required
- No way to test with real Neon data using sandbox credentials
- Local testing required a completely isolated database

---

## The Solution: Three-Mode Authority Matrix

| Mode | `AOS_MODE` | `DB_AUTHORITY` | Sandbox Auth | Production Auth | Use Case |
|------|------------|----------------|--------------|-----------------|----------|
| **LOCAL** | `local` | `local` | ✅ Allowed | ✅ Allowed | Isolated local development |
| **TEST** | `test` | `neon` | ✅ Allowed | ✅ Allowed | Integration testing with real data |
| **PROD** | `prod` | `neon` | ❌ Blocked | ✅ Required | Live production traffic |

### Mode Definitions

#### LOCAL Mode (`AOS_MODE=local`)
- **Purpose:** Isolated local development and unit testing
- **Database:** Local PostgreSQL (ephemeral, disposable)
- **Auth:** Sandbox credentials OR production credentials
- **Cost:** No LLM billing, no Neon costs
- **Data:** Seeded test data only

#### TEST Mode (`AOS_MODE=test`)
- **Purpose:** Integration testing against real infrastructure
- **Database:** Neon (authoritative, shared test data)
- **Auth:** Sandbox credentials OR production credentials
- **Cost:** Neon costs incurred, LLM usage may be billed
- **Data:** Real test tenant data in Neon

#### PROD Mode (`AOS_MODE=prod`)
- **Purpose:** Live production traffic
- **Database:** Neon (authoritative, production data)
- **Auth:** Production credentials ONLY (Clerk JWT, API keys)
- **Cost:** Full billing active
- **Data:** Real customer data

---

## Environment Configuration

### Required Environment Variables

```env
# Mode Selection (REQUIRED)
AOS_MODE=prod                    # "local" | "test" | "prod"

# Database Authority (REQUIRED)
DB_AUTHORITY=neon               # "local" | "neon"

# Sandbox Feature Flag (OPTIONAL)
CUSTOMER_SANDBOX_ENABLED=false  # "true" | "false"
```

### Mode Configurations

#### Local Development
```env
AOS_MODE=local
DB_AUTHORITY=local
CUSTOMER_SANDBOX_ENABLED=true
```

#### Integration Testing
```env
AOS_MODE=test
DB_AUTHORITY=neon
CUSTOMER_SANDBOX_ENABLED=true
```

#### Production
```env
AOS_MODE=prod
DB_AUTHORITY=neon
CUSTOMER_SANDBOX_ENABLED=false  # Ignored anyway, PROD blocks sandbox
```

---

## Authentication Architecture

### Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      REQUEST ARRIVES                             │
│                   (with auth headers)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               1. SANDBOX AUTH CHECK (First)                      │
│                                                                  │
│   IF (AOS_MODE ∈ {"local", "test"})                            │
│     AND CUSTOMER_SANDBOX_ENABLED=true                           │
│     AND NOT (DB_AUTHORITY="neon" AND AOS_MODE="prod")          │
│     AND header "X-AOS-Customer-Key" present:                    │
│       → Resolve to SandboxCustomerPrincipal                     │
│       → Set request.state.auth_context                          │
│       → Set request.state.is_sandbox = true                     │
│       → CONTINUE to handler (skip normal auth)                  │
│                                                                  │
│   ELSE:                                                          │
│       → Continue to normal auth chain                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (if no sandbox auth)
┌─────────────────────────────────────────────────────────────────┐
│               2. NORMAL AUTH GATEWAY                             │
│                                                                  │
│   • JWT validation (Clerk) via Authorization: Bearer <jwt>      │
│   • API key validation via X-AOS-Key: <key>                     │
│   • Machine capability resolution                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               3. RBAC MIDDLEWARE                                 │
│                                                                  │
│   • Extracts capabilities from auth context                     │
│   • Validates path against RBAC_RULES.yaml                      │
│   • Enforces required permissions                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               4. ENDPOINT HANDLER                                │
│                                                                  │
│   • Receives authenticated request                               │
│   • Access auth via: get_auth_context(request)                  │
│   • Tenant isolation enforced                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Sandbox Authentication

#### Sandbox Keys (Predefined)

| Key | Tenant | Role | Use Case |
|-----|--------|------|----------|
| `cus_sandbox_demo` | `demo-tenant` | `customer_admin` | General testing |
| `cus_sandbox_readonly` | `demo-tenant` | `customer_viewer` | Read-only testing |
| `cus_sandbox_tenant2` | `tenant-2` | `customer_admin` | Multi-tenant testing |
| `cus_ci_test` | `ci-tenant` | `customer_admin` | CI/CD pipelines |

#### Sandbox Principal Structure

```python
@dataclass
class SandboxCustomerPrincipal:
    tenant_id: str           # e.g., "demo-tenant"
    customer_id: str         # e.g., "cus_sandbox_demo"
    role: str                # "customer_admin" | "customer_viewer"
    authority: str           # Always "sandbox"
    permissions: list[str]   # Derived from role
```

#### Sandbox Capability Mapping

| Role | Capabilities |
|------|-------------|
| `customer_admin` | `customer:integrations:read`, `customer:integrations:write`, `customer:enforcement:read`, `customer:enforcement:write`, `customer:telemetry:read`, `customer:visibility:read`, `integration:read`, `integration:write` |
| `customer_viewer` | `customer:integrations:read`, `customer:enforcement:read`, `customer:telemetry:read`, `customer:visibility:read`, `integration:read` |

---

## RBAC Integration

### Customer Integration Rules

The following RBAC rules are defined in `design/auth/RBAC_RULES.yaml`:

| Rule ID | Path | Methods | Tier | Required Permissions |
|---------|------|---------|------|---------------------|
| `CUS_INTEGRATIONS_READ` | `/api/v1/cus/integrations` | `GET` | SESSION | `customer:integrations:read` |
| `CUS_INTEGRATIONS_WRITE` | `/api/v1/cus/integrations` | `POST`, `PUT`, `DELETE` | PRIVILEGED | `customer:integrations:write` |
| `CUS_ENFORCEMENT_READ` | `/api/v1/cus/enforcement` | `GET` | SESSION | `customer:enforcement:read` |
| `CUS_ENFORCEMENT_WRITE` | `/api/v1/cus/enforcement` | `POST`, `PUT`, `DELETE` | PRIVILEGED | `customer:enforcement:write` |
| `CUS_TELEMETRY_READ` | `/api/v1/cus/telemetry` | `GET` | SESSION | `customer:telemetry:read` |
| `CUS_VISIBILITY_READ` | `/api/v1/cus/visibility` | `GET` | SESSION | `customer:visibility:read` |

### RBAC Middleware Integration

The RBAC middleware recognizes `SandboxCustomerPrincipal` and maps it to capabilities:

```python
# In rbac_middleware.py
if isinstance(context, SandboxCustomerPrincipal):
    if context.role == "customer_admin":
        return [
            "customer:integrations:read",
            "customer:integrations:write",
            # ... full admin capabilities
        ]
    elif context.role == "customer_viewer":
        return [
            "customer:integrations:read",
            # ... read-only capabilities
        ]
```

---

## Safety Guarantees

### Hard Invariants

| Invariant | Enforcement | Description |
|-----------|-------------|-------------|
| **INV-001** | Code gate in `is_sandbox_allowed()` | PROD mode NEVER allows sandbox auth |
| **INV-002** | Code gate in `is_sandbox_allowed()` | `CUSTOMER_SANDBOX_ENABLED=false` disables sandbox everywhere |
| **INV-003** | RBAC middleware | Unknown principal types are REJECTED |
| **INV-004** | Gateway middleware | Sandbox keys ONLY work with `X-AOS-Customer-Key` header |
| **INV-005** | Audit logging | All sandbox auth events are logged with `is_sandbox=true` |
| **INV-006** | Permission ceiling | Sandbox principals NEVER exceed `SANDBOX_ALLOWED_PERMISSIONS` |
| **INV-007** | Header precedence | Mixed auth headers (sandbox + JWT/API key) are REJECTED |
| **INV-008** | Environment drift | DATABASE_URL production indicators trigger critical logs |

### Security Properties

1. **No Credential Leakage:** Sandbox keys are hardcoded and cannot authenticate in production
2. **Tenant Isolation:** Sandbox principals are bound to specific test tenants
3. **Audit Trail:** All sandbox requests are tagged for audit visibility
4. **Fail Closed:** Unknown modes default to production behavior (sandbox blocked)
5. **Permission Ceiling:** Sandbox cannot escalate beyond customer-level permissions
6. **Telemetry Tagging:** All sandbox calls include `billable: false` and `auth_origin: sandbox`

---

## Security Edge Cases (Addressed)

### Edge Case 1: Environment Drift
**Risk:** `AOS_MODE=test` but `DATABASE_URL` points to production.

**Mitigation:**
- Module-load safety check detects production indicators in DATABASE_URL
- Critical log emitted if drift detected
- Heuristics: "prod" without "test", "-prod.", "_production"

### Edge Case 2: Permission Escalation
**Risk:** Sandbox principal receives admin/operator permissions.

**Mitigation:**
- `SANDBOX_ALLOWED_PERMISSIONS` is a hardcoded ceiling
- Permissions are intersected: `granted ∩ allowed`
- Forbidden permissions explicitly listed (operator:*, admin:*, etc.)

### Edge Case 3: Mixed Auth Headers
**Risk:** Ambiguous auth with both sandbox and JWT/API key headers.

**Mitigation:**
- `has_conflicting_auth_headers()` detects conflicts
- Request is rejected (returns None, falls through to normal auth)
- Warning logged for audit

### Edge Case 4: Telemetry Trust Confusion
**Risk:** Sandbox calls pollute production dashboards.

**Mitigation:**
- `SandboxCustomerPrincipal.billable = False` (immutable)
- `SandboxCustomerPrincipal.to_telemetry_context()` provides audit tags
- All telemetry should filter on `auth_origin != "sandbox"`

### Edge Case 5: Silent Fallback
**Risk:** Sandbox auth fails silently and falls through.

**Mitigation:**
- Explicit warning logs for all rejection reasons
- No silent downgrade to anonymous or partial principal
- Gateway logs `GatewayErrorCode.MISSING_AUTH` for rejected requests

---

## Sandbox Correctness Checklist (Lock This)

Before shipping, verify all boxes are checked:

- [x] Sandbox auth fails hard in `AOS_MODE=prod`
- [x] Sandbox auth cannot touch prod DB (environment drift detection)
- [x] Sandbox principals have capped permissions (`SANDBOX_ALLOWED_PERMISSIONS`)
- [x] Sandbox calls are tagged non-billable (`billable: false`)
- [x] Mixed auth headers are rejected
- [x] Rate limits can be enforced differently (via RBAC rules)
- [x] Telemetry distinguishes sandbox vs real (`auth_origin: sandbox`)

**If any box is unchecked, the sandbox is unsafe.**

---

## Testing Protocol

### Testing LOCAL Mode

```bash
# Set environment
AOS_MODE=local DB_AUTHORITY=local CUSTOMER_SANDBOX_ENABLED=true \
  docker compose up -d backend

# Test sandbox auth
curl -H "X-AOS-Customer-Key: cus_sandbox_demo" \
  http://localhost:8000/api/v1/cus/integrations

# Expected: HTTP 200 or 404 (auth passed, may have no data)
```

### Testing TEST Mode

```bash
# Set environment
AOS_MODE=test DB_AUTHORITY=neon CUSTOMER_SANDBOX_ENABLED=true \
  docker compose up -d backend

# Test sandbox auth
curl -H "X-AOS-Customer-Key: cus_sandbox_demo" \
  http://localhost:8000/api/v1/cus/integrations

# Expected: HTTP 200 or 404 (auth passed, queries Neon)
```

### Testing PROD Mode

```bash
# Set environment (or use defaults)
AOS_MODE=prod DB_AUTHORITY=neon \
  docker compose up -d backend

# Test sandbox auth (should FAIL)
curl -H "X-AOS-Customer-Key: cus_sandbox_demo" \
  http://localhost:8000/api/v1/cus/integrations

# Expected: HTTP 401 (sandbox blocked in prod)

# Test production auth (should PASS)
curl -H "Authorization: Bearer <clerk_jwt>" \
  http://localhost:8000/api/v1/cus/integrations

# Expected: HTTP 200 (production auth works)
```

---

## Implementation Files

| File | Purpose |
|------|---------|
| `backend/app/auth/customer_sandbox.py` | Sandbox auth module, `is_sandbox_allowed()` |
| `backend/app/auth/gateway_middleware.py` | Auth gateway, sandbox integration |
| `backend/app/auth/rbac_middleware.py` | RBAC enforcement, capability mapping |
| `design/auth/RBAC_RULES.yaml` | RBAC rule definitions |
| `docker-compose.yml` | Environment variable definitions |
| `backend/scripts/test_three_mode_authority.py` | Logic test suite |
| `backend/scripts/test_http_three_modes.sh` | HTTP integration tests |

---

## Troubleshooting

### Sandbox Auth Returns 401 in TEST Mode

**Check:**
1. `AOS_MODE=test` (not `prod`)
2. `CUSTOMER_SANDBOX_ENABLED=true`
3. Using `X-AOS-Customer-Key` header (not `X-AOS-Key`)
4. Key is valid (e.g., `cus_sandbox_demo`)

**Logs to check:**
```bash
docker logs nova_agent_manager | grep -i sandbox
```

### Sandbox Auth Works in PROD Mode (Security Issue!)

**This should never happen.** If it does:
1. Verify `AOS_MODE=prod` is set
2. Check `is_sandbox_allowed()` logic
3. Escalate immediately - this is a security incident

### RBAC Returns 403 for Sandbox Principal

**Check:**
1. RBAC middleware recognizes `SandboxCustomerPrincipal`
2. Role has required permission
3. Path is covered in `RBAC_RULES.yaml`

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-01-18 | 1.0.0 | Initial release - Three-Mode Authority System |

---

## References

- PIN-440: Customer Sandbox Authentication Mode
- PIN-391: RBAC Rules YAML Authority
- `docs/governance/AUTHORIZATION_CONSTITUTION.md`
- `docs/architecture/auth/AUTH_ARCHITECTURE_BASELINE.md`
