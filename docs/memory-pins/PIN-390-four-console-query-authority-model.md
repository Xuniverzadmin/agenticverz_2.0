# PIN-390: Four-Console Query Authority Model

**Status:** ACTIVE
**Created:** 2026-01-11
**Category:** Architecture / Security / Governance

---

## Summary

Formalized the `query_authority` schema for the four-console model (customer×preflight, customer×production, founder×preflight, founder×production). Prevents 403 noise by checking authority **before** API calls, not after.

---

## Problem

With four consoles and implicit permission logic:

```
Panel exists → UI queries → backend denies → UI retries → 403 noise
```

This creates:
- False error signals in logs
- Confusing user experience
- Backend load from denied queries
- No clear authority model

---

## Solution

Explicit `query_authority` in projection output:

```
Panel exists
→ query_authority check
→ UI shows boundary (no API call)
→ ZERO 403s
```

### Authority is Declarative

- UI MUST NOT infer query permissions
- Backend MUST NOT be relaxed for preflight
- Projection MUST declare `query_authority`
- Claude MUST NOT guess authority from endpoint names
- Any panel without `query_authority` is INVALID

---

## Schema

**Location:** `docs/schemas/query_authority_schema.json`

```json
{
  "query_authority": {
    "level": "USER | SYSTEM | SYNTHETIC | INTERNAL",
    "requires": {
      "permissions": ["string"],
      "roles": ["string"]
    },
    "allow_in": {
      "customer": { "preflight": true, "production": false },
      "founder": { "preflight": true, "production": true }
    },
    "failure_mode": "HIDE | DISABLE | EXPLAIN",
    "notes": "string"
  }
}
```

---

## Authority Levels

| Level | Meaning |
|-------|---------|
| `USER` | Tenant-scoped, customer-safe data |
| `SYSTEM` | Engine / control-plane derived data |
| `SYNTHETIC` | Test, injected, SDSR-derived data |
| `INTERNAL` | Staff-only / governance / debugging |

### Forbidden Shortcuts

- SYSTEM ≠ USER in preflight
- SYNTHETIC ≠ SYSTEM
- INTERNAL ≠ founder by default

---

## Four-Console Authority Matrix

| Console | Env | USER | SYSTEM | SYNTHETIC | INTERNAL |
|---------|-----|------|--------|-----------|----------|
| customer | preflight | YES | NO | NO | NO |
| customer | production | YES | NO | NO | NO |
| founder | preflight | YES | YES | YES | NO |
| founder | production | YES | YES | NO | NO |

### Hard Invariants

1. **SYNTHETIC is NEVER allowed in production**
2. **INTERNAL is never projection-exposed**
3. **Founder ≠ god mode**

---

## Failure Modes

| Mode | UI Behavior |
|------|-------------|
| `HIDE` | Panel not rendered |
| `DISABLE` | Visible but grayed/non-interactive |
| `EXPLAIN` | Shows explanation of access denial |

---

## Fail-Closed Default

When authority is unknown:

```json
{
  "level": "SYSTEM",
  "allow_in": {
    "customer": { "preflight": false, "production": false },
    "founder": { "preflight": false, "production": false }
  },
  "failure_mode": "HIDE"
}
```

---

## Key Distinctions

> **Visibility ≠ Queryability**
> A panel can be visible but not queryable.

> **Queryability ≠ Executability**
> User can see data but not act on it.

---

## Governance Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| JSON Schema | `docs/schemas/query_authority_schema.json` | Machine-parseable law |
| Governance Doc | `docs/governance/QUERY_AUTHORITY_MODEL.md` | Human-readable specification |
| CI Guard | `scripts/ci/query_authority_guard.py` | CI enforcement script |
| PIN-390 | This document | Memory pin reference |

---

## CI Guard (Enforcement)

The query authority guard validates projections in CI:

```bash
# Verbose output
python3 scripts/ci/query_authority_guard.py --verbose

# Strict mode (warnings as errors)
python3 scripts/ci/query_authority_guard.py --strict
```

### Validations Performed

1. **Contract Declaration** - `_contract.query_authority_required` is true
2. **Panel Presence** - Every panel has `query_authority` field
3. **Schema Compliance** - All fields match the JSON schema
4. **Hard Invariants** - No SYNTHETIC in production, no INTERNAL exposed
5. **Matrix Compliance** - `allow_in` values match four-console matrix

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All validations passed |
| 1 | Query authority violations detected |
| 2 | File not found or invalid JSON |

---

## UI Contract

Before **any** API call:

```typescript
if (!canQuery(panel.query_authority, consoleContext, authContext)) {
  return renderBoundary(panel.query_authority.failure_mode);
}
```

### UI MUST NOT

- Retry on 403
- Infer permission from response
- Log denied queries as errors
- Mask as "backend error"

---

## Compiler Contract

AURORA_L2 compiler MUST:

1. Emit `query_authority` for every panel
2. Use fail-closed default if unsure
3. Fail compilation if missing

AURORA_L2 compiler MUST NOT:

- Infer from endpoint name
- Infer from domain
- Infer from console kind

---

## Relationship to PIN-389

This PIN extends the epistemic safety protocol (PIN-389) to query authority:

- **PIN-389:** Claude must not guess schema values
- **PIN-390:** Claude must not guess query authority

Both enforce: **Schema is law. Guessing is forbidden.**

---

## Related PINs

- [PIN-389](PIN-389-projection-route-separation-and-console-isolation.md) - Epistemic Safety Protocol
- [PIN-352](PIN-352-.md) - L2.1 UI Projection Pipeline
- [PIN-368](PIN-368-.md) - Route Architecture
