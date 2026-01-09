# PIN-376: Auth Pattern Enforcement - Clerk/RBAC Gateway

**Status:** ✅ COMPLETE
**Created:** 2026-01-09
**Category:** Auth Architecture / RBAC

---

## Summary

Auth handled by Gateway Middleware only. Endpoints must NOT add Depends(get_jwt_auth). Two planes: HUMAN (Clerk JWT) vs MACHINE (API key). Behavioral gate BL-AUTH-001 prevents violations.

---

## Details

## Problem

Claude added `Depends(get_jwt_auth())` to API endpoints, causing 401 errors because:
1. Gateway middleware already authenticated the request
2. The duplicate auth dependency expected JWT but got API key (or vice versa)
3. Auth ran twice with different expectations

## Root Cause

Misunderstanding of auth architecture:
- Gateway middleware is the SINGLE auth entry point
- Endpoints receive pre-authenticated context
- Adding auth dependencies is REDUNDANT and BREAKS auth

## Auth Architecture

```
REQUEST ARRIVES
      ↓
AuthGatewayMiddleware
  • Extracts: Authorization OR X-AOS-Key header
  • Mutual Exclusivity: JWT XOR API Key (not both)
  • Result: request.state.auth_context
      ↓
YOUR ENDPOINT
  • Auth already done — don't add more
  • Access via: get_auth_context(request)
  • DO NOT: Depends(get_jwt_auth())  ← REDUNDANT
```

## Two Auth Planes (NEVER MIX)

| Plane | Header | Provider | Use Case |
|-------|--------|----------|----------|
| HUMAN | Authorization: Bearer <jwt> | Clerk | Console users |
| MACHINE | X-AOS-Key: <key> | Gateway | SDK, CLI, workers |

## Correct Pattern

**WRONG:**
```python
async def my_endpoint(auth: TokenPayload = Depends(get_jwt_auth())):
    # This runs auth AGAIN after gateway already did it
```

**RIGHT:**
```python
async def my_endpoint(request: Request):
    ctx = get_auth_context(request)  # Already authenticated by gateway
```

## Local Testing

For testing without Clerk:
```bash
# Use stub tokens (requires AUTH_STUB_ENABLED=true)
curl -H "Authorization: Bearer stub_admin_demo-tenant" /api/v1/endpoint

# Or use API key for machine plane
curl -H "X-AOS-Key: $AOS_API_KEY" /api/v1/endpoint
```

## Behavioral Gate Added

BL-AUTH-001 in CLAUDE.md blocks:
- Adding Depends(get_jwt_auth()) to endpoints
- Adding Depends(verify_api_key) to endpoints
- Debugging console endpoints with API keys (wrong plane)

## Key Artifacts

| Artifact | Location |
|----------|----------|
| Gateway Middleware | backend/app/auth/gateway_middleware.py |
| Gateway Core | backend/app/auth/gateway.py |
| Auth Semantic Contract | docs/architecture/AUTH_SEMANTIC_CONTRACT.md |
| RBAC Design | docs/governance/RBAC_AUTHORITY_SEPARATION_DESIGN.md |
| Stub Design | docs/infra/RBAC_STUB_DESIGN.md |

## Invariant

> Gateway middleware handles ALL auth. Endpoints consume context, never authenticate.

## Reference

- PIN-271 (RBAC Architecture Directive)
- CLAUDE.md Section: BL-AUTH-001
- docs/architecture/AUTH_SEMANTIC_CONTRACT.md

---

## Related PINs

- [PIN-271](PIN-271-.md)
