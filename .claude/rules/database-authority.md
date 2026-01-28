---
paths:
  - "backend/alembic/**"
  - "backend/app/db/**"
---

# Database Authority Rules (DB-AUTH-001)

**Status:** BLOCKING | **Severity:** CRITICAL
**Reference:** docs/governance/DB_AUTH_001_INVARIANT.md, docs/runtime/DB_AUTHORITY.md

## Core Invariant

> At any point in time, the authoritative database MUST be explicitly declared and MUST NOT be inferred.

Authority is declared, validated, and enforced — never discovered.

## Database Roles (PIN-462)

| DB_ROLE | Meaning | Migrations |
|---------|---------|------------|
| staging | Pre-prod / local / CI | ✅ Allowed |
| prod | Production canonical | ✅ Allowed (with CONFIRM_PROD_MIGRATIONS=true) |
| replica | Read-only / analytics | ❌ Blocked |

## Environment Mapping

| Environment | DB_AUTHORITY | DB_ROLE |
|-------------|--------------|---------|
| Local dev | local | staging |
| Neon test | neon | staging |
| Neon prod | neon | prod |

## Permitted Operations Matrix

| Operation Type | Neon | Local |
|----------------|------|-------|
| Read canonical history | ✅ | ❌ |
| Validate runs | ✅ | ❌ |
| SDSR scenario execution | ✅ | ❌ |
| Schema experiments | ❌ | ✅ |
| Migration (staging) | ✅ | ✅ |
| Migration (prod) | ✅ (with confirm) | ❌ |
| Unit tests | ❌ | ✅ |

## Prohibited Behaviors

1. Inferring authority from data age
2. Switching databases mid-session
3. "Checking both" to decide correctness
4. Retrying against a different DB
5. Discovering authority after execution
6. Silent fallback from Neon → Local or vice-versa
7. Running migrations without declaring DB_ROLE
8. Running prod migrations without CONFIRM_PROD_MIGRATIONS=true

## Mandatory Pre-Check

```
DB AUTHORITY DECLARATION
- Declared Authority: <neon | local>
- DB_ROLE (if migration): <staging | prod>
- Intended Operation: <read | write | validate | test | migrate>
- Justification: <single sentence>
```
