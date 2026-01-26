# Auth Design Sanitization Report

**Date:** 2026-01-12
**Status:** COMPLETE
**PIN:** PIN-398
**Reference:** docs/AUTH_DESIGN.md

---

## Executive Summary

This document records the systematic elimination of deprecated authentication patterns from the Agenticverz codebase. The work achieved **0 violations** of AUTH_DESIGN.md invariants, down from 31 violations.

### Key Outcomes

| Metric | Before | After |
|--------|--------|-------|
| Scanner Violations | 31 | 0 |
| Files Modified | - | 18 |
| Deleted Files | - | 2 (console_auth.py, stub.py) |
| Pre-commit Enforcement | No | Yes |

---

## Background

### The Problem

The codebase had accumulated multiple authentication mechanisms over time:

1. **Console JWT (HS256)** - Internal JWT issuance for humans
2. **Stub Tokens** - Test tokens that bypassed real authentication
3. **Tenant Fallbacks** - Silent fallback to "default" tenant
4. **Grace Periods** - Temporary acceptance of unknown issuers

These patterns violated the AUTH_DESIGN.md specification which mandates:
- Clerk (RS256 JWKS) as the ONLY human authentication path
- API Keys as the ONLY machine authentication path
- No tenant fallbacks - missing tenant is a hard failure

### The Solution

1. **Create AUTH_DESIGN.md** - Single source of truth for auth invariants
2. **Build auth_invariant_scanner.py** - Mechanical enforcement of invariants
3. **Execute deletions** - Remove all forbidden patterns
4. **Wire into pre-commit** - Prevent future violations

---

## Detailed Changes

### 1. Tenant Fallback Elimination (AUTH-TENANT-005)

**Before:**
```python
tenant_id = request.tenant_id or "default"
```

**After:**
```python
# AUTH_DESIGN.md: AUTH-TENANT-005 - No fallback tenant. Missing tenant is hard failure.
if not request.tenant_id:
    raise HTTPException(status_code=400, detail="tenant_id is required")
tenant_id = request.tenant_id
```

**Files affected:** 10 files across API, services, and stores layers

### 2. Stub Authentication Removal (AUTH-HUMAN-004)

**Deleted:**
- `backend/app/auth/stub.py` - Stub token parsing
- `backend/app/auth/console_auth.py` - Console JWT issuance

**Modified:**
- `identity_adapter.py` - Removed StubIdentityAdapter class
- `identity_chain.py` - Removed stub adapter from chain
- `conftest.py` - Renamed `stub_*` fixtures to `test_*`
- `infra.py` - Replaced `_check_stub_auth` with `_check_clerk_auth`

### 3. Console Auth Removal (AUTH-HUMAN-001, AUTH-HUMAN-003)

**Deleted:**
- `IdentitySource.CONSOLE` enum value
- All references to `CONSOLE_JWT_SECRET`
- All references to `console.*HS256`

**Modified:**
- `actor.py` - Removed CONSOLE from IdentitySource enum
- `contexts.py` - Removed AuthSource.CONSOLE (prior session)
- `onboarding.py` - Removed login endpoints (prior session)

### 4. Frontend Cleanup

**Modified:**
- `LoginPage.tsx` - Removed DEV_LOGIN_PASSWORD reference
- Updated error handling to reference Clerk authentication

---

## Scanner Implementation

### Pattern Matching

The scanner uses regex patterns to detect forbidden code:

```python
FORBIDDEN_PATTERNS = [
    ("FORBIDDEN-001", r"CONSOLE_JWT_SECRET", "..."),
    ("FORBIDDEN-002", r"AuthSource\.CONSOLE", "..."),
    ("FORBIDDEN-003", r"console.*HS256|human.*HS256|...", "..."),
    ("FORBIDDEN-004", r"permissions\s*=\s*\[\s*[\"']\*[\"']\s*\]", "..."),
    ("FORBIDDEN-005", r"(?:tenant_id|org_id).*(?:or|if.*else|\?\?).*[\"']default[\"']", "..."),
    # ... etc
]
```

### False Positive Prevention

The scanner includes negative lookbehinds and context-specific patterns to avoid false positives:

```python
# Don't flag "No grace periods" as a violation
r"(?<!no\s)(?<!No\s)grace[_\s]*period"

# Don't flag all stub_ prefixes, only auth tokens
r"stub_(admin|developer|viewer|machine|user|operator)_"
```

### Pre-commit Integration

```yaml
- id: auth-invariant-scanner
  name: Auth Invariant Scanner
  entry: python scripts/ops/auth_invariant_scanner.py --files
  language: python
  pass_filenames: true
  stages: [pre-commit]
  files: |
    (?x)^(
      backend/app/auth/.*|
      backend/app/api/.*|
      backend/app/services/.*
    )$
```

---

## Verification

### Scanner Output

```
======================================================================
AUTH INVARIANT SCANNER
Enforcing: docs/AUTH_DESIGN.md
======================================================================

No violations found.
======================================================================
SCANNER PASSED
======================================================================
```

### Grep Verification

```bash
# No console JWT references
$ grep -r "CONSOLE_JWT\|AuthSource.CONSOLE" backend/app/
(no output)

# No stub auth references (only deletion comments)
$ grep -r "AUTH_STUB\|parse_stub_token" backend/app/
identity_adapter.py:# StubIdentityAdapter DELETED
identity_chain.py:    # StubIdentityAdapter DELETED - AUTH_DESIGN.md (AUTH-HUMAN-004)
```

---

## Architecture After Sanitization

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    REQUEST ARRIVES                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              AuthGatewayMiddleware                          │
│                                                             │
│  Human Path:                                                │
│    Authorization: Bearer <clerk_jwt>                        │
│    → ClerkAdapter → verify RS256 JWKS → HumanAuthContext    │
│                                                             │
│  Machine Path:                                              │
│    X-AOS-Key: <api_key>                                     │
│    → SystemAdapter → validate key → MachineCapabilityContext│
│                                                             │
│  Mutual Exclusivity: JWT XOR API Key (never both)           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Endpoint Handler                               │
│  • Auth already done — don't add more                       │
│  • Access via: get_auth_context(request)                    │
│  • Tenant ID: REQUIRED (no fallback to "default")           │
└─────────────────────────────────────────────────────────────┘
```

### Identity Chain (After)

```python
def create_identity_chain() -> IdentityChain:
    adapters: List[IdentityAdapter] = []

    # 1. System adapter always first (machine tokens)
    adapters.append(SystemIdentityAdapter())

    # 2. Clerk in production (human auth)
    if os.getenv("CLERK_SECRET_KEY"):
        adapters.append(ClerkAdapter())

    # 3. Dev adapter in development
    if os.getenv("DEV_AUTH_ENABLED", "").lower() == "true":
        adapters.append(DevIdentityAdapter())

    # StubIdentityAdapter DELETED - AUTH_DESIGN.md (AUTH-HUMAN-004)

    return IdentityChain(adapters)
```

---

## Future Considerations

### LoginPage.tsx Replacement

The frontend `LoginPage.tsx` still contains legacy password/OTP login flows. Per AUTH_DESIGN.md, this should be replaced with Clerk React components:

```tsx
// Future state - use Clerk components
import { SignIn } from "@clerk/clerk-react";

export default function LoginPage() {
  return <SignIn />;
}
```

### Test Fixtures

Test fixtures were renamed from `stub_*` to `test_*`. Tests should use:
- `test_admin_headers` instead of `stub_admin_headers`
- API key authentication for machine tests
- DEV_AUTH_ENABLED=true for dev mode tests

---

## References

- **AUTH_DESIGN.md**: `docs/AUTH_DESIGN.md`
- **Scanner**: `scripts/ops/auth_invariant_scanner.py`
- **Pre-commit Config**: `.pre-commit-config.yaml`
- **PIN-398**: Auth Design Sanitization PIN
- **PIN-377**: Console-Clerk Auth Unification
- **PIN-271**: RBAC Architecture Directive
