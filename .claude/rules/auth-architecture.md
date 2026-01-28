---
paths:
  - "backend/app/auth/**"
  - "backend/app/api/**"
---

# Auth Architecture Rules

## Environment Contract (BL-ENV-CONTRACT-001)

Three-plane separation:

| Plane | Auth | Use |
|-------|------|-----|
| Database | DATABASE_URL only | Migrations, seeds, schema |
| Human | Authorization: Bearer <clerk_jwt> | /api/v1/accounts/*, console APIs |
| Machine | X-AOS-Key: <api_key> | /api/v1/runs/*, SDK, telemetry |

Never mix auth planes. Never weaken auth to make tests pass.

## RBAC Architecture (PIN-271) — RBAC-D1 to RBAC-D8

| Rule | Requirement |
|------|-------------|
| RBAC-D1 | ActorContext is the only auth input |
| RBAC-D2 | Identity ≠ Authorization. Adapters extract identity, Engine decides permissions |
| RBAC-D3 | No Fake Production. Dev uses DevIdentityAdapter |
| RBAC-D4 | System actors are real actors (CI, workers, replay) |
| RBAC-D5 | Enterprise structure is first-class (account_id, team_id) |
| RBAC-D6 | Same rules everywhere. Prod/CI/local share AuthorizationEngine |
| RBAC-D7 | Every new feature must declare: ActorType, permissions, scope |
| RBAC-D8 | Tests import from L4/L6 facades only |

## Authorization Constitution (PIN-391, PIN-392)

### Invariants (Cannot Be Violated)

| Invariant | Enforcement |
|-----------|-------------|
| INV-001: No Silent Auth Bypass | strict=True default |
| INV-002: No Inferred Access | Claude guardrail |
| INV-003: No Undocumented PUBLIC | CI guard |
| INV-004: No Expired Rules | Expiry check in CI |
| INV-005: No Schema-Code Drift | Shadow logging → hard block |

## Auth Pattern Enforcement (BL-AUTH-001)

Gateway middleware handles ALL auth. Endpoints receive pre-authenticated context.

WRONG: `async def endpoint(auth = Depends(get_jwt_auth())):`
RIGHT: `async def endpoint(request: Request): ctx = get_auth_context(request)`

Auth Planes (NEVER MIX):
- HUMAN: Authorization: Bearer <jwt> (Clerk, console users)
- MACHINE: X-AOS-Key: <key> (SDK, CLI, workers)

## Auth Architecture Lock (BL-AUTH-002)

Auth architecture is FINALIZED and LOCKED. Claude is a maintainer, not an inventor.
Canonical: docs/architecture/auth/AUTH_ARCHITECTURE_BASELINE.md

Prohibited without approval: reintroduce algorithm-based routing, add secret fallback chains, merge Console and Clerk authenticators, remove feature flags/metrics.

Allowed: bug fixes, logging, additional metrics, test coverage, docs, feature flag values.
