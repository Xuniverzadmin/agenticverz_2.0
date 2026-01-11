# Query Authority Model (Four-Console)

**Status:** MANDATORY
**Effective:** 2026-01-11
**Reference:** PIN-390, QUERY_AUTHORITY_SCHEMA_V1
**Schema:** `docs/schemas/query_authority_schema.json`

---

## Prime Directive

> **Query authority is declarative.**
> UI MUST NOT infer query permissions.
> Backend MUST NOT be relaxed for preflight.
> Projection MUST declare `query_authority`.
> Claude MUST NOT guess authority based on endpoint names.
> Any panel without `query_authority` is INVALID.

---

## The Problem This Solves

Without explicit query authority:

```
Panel exists → UI queries → backend denies → UI retries → noise
```

With this design:

```
Panel exists
→ query_authority denies
→ UI shows boundary
→ NO API CALL
→ ZERO 403s
```

403 is **truth**, not error.

---

## Authority Levels (Locked Semantics)

| Level | Meaning | Example |
|-------|---------|---------|
| `USER` | Tenant-scoped, customer-safe data | Activity runs, policies |
| `SYSTEM` | Engine / control-plane derived data | Incidents, system health |
| `SYNTHETIC` | Test, injected, SDSR-derived data | Scenarios, synthetic runs |
| `INTERNAL` | Staff-only / governance / debugging | Admin tools, governance data |

### Forbidden Shortcuts

- SYSTEM ≠ USER in preflight
- SYNTHETIC ≠ SYSTEM
- INTERNAL ≠ founder by default

**No collapsing allowed.**

---

## Four-Console Authority Matrix (Core)

| Console | Env | USER | SYSTEM | SYNTHETIC | INTERNAL |
|---------|-----|------|--------|-----------|----------|
| customer | preflight | YES | NO | NO | NO |
| customer | production | YES | NO | NO | NO |
| founder | preflight | YES | YES | YES | NO |
| founder | production | YES | YES | NO | NO |

### Hard Invariants

1. **SYNTHETIC is NEVER allowed in production** (any console)
2. **INTERNAL is never projection-exposed** (use direct routes)
3. **Founder ≠ god mode** (still has restrictions)

This matrix must be **hardcoded in UI runtime**, not inferred.

---

## Schema (Authoritative)

```json
{
  "query_authority": {
    "level": "USER | SYSTEM | SYNTHETIC | INTERNAL",
    "requires": {
      "permissions": ["string"],
      "roles": ["string"]
    },
    "allow_in": {
      "customer": {
        "preflight": true,
        "production": false
      },
      "founder": {
        "preflight": true,
        "production": true
      }
    },
    "failure_mode": "HIDE | DISABLE | EXPLAIN",
    "notes": "string"
  }
}
```

### Field Semantics

| Field | Meaning |
|-------|---------|
| `level` | What kind of data is being queried |
| `requires.permissions` | Backend permissions required |
| `requires.roles` | Optional role constraint |
| `allow_in` | Hard console/environment gate |
| `failure_mode` | How UI must behave if denied |
| `notes` | Human-readable, non-functional |

---

## Failure Modes

| Mode | UI Behavior |
|------|-------------|
| `HIDE` | Panel is not rendered at all |
| `DISABLE` | Panel visible but non-interactive (grayed) |
| `EXPLAIN` | Panel shows explanation of why access denied |

---

## Examples

### Incidents (System-level, founder-only)

```json
{
  "query_authority": {
    "level": "SYSTEM",
    "requires": {
      "permissions": ["INCIDENTS_READ"]
    },
    "allow_in": {
      "customer": { "preflight": false, "production": false },
      "founder": { "preflight": true, "production": true }
    },
    "failure_mode": "EXPLAIN",
    "notes": "System-generated incidents, not customer-visible"
  }
}
```

### Activity Runs (User-level, customer-safe)

```json
{
  "query_authority": {
    "level": "USER",
    "requires": {
      "permissions": ["ACTIVITY_READ"]
    },
    "allow_in": {
      "customer": { "preflight": true, "production": true },
      "founder": { "preflight": true, "production": true }
    },
    "failure_mode": "HIDE"
  }
}
```

### SDSR / Synthetic Data (Preflight founder only)

```json
{
  "query_authority": {
    "level": "SYNTHETIC",
    "requires": {
      "permissions": ["SDSR_READ"]
    },
    "allow_in": {
      "customer": { "preflight": false, "production": false },
      "founder": { "preflight": true, "production": false }
    },
    "failure_mode": "EXPLAIN",
    "notes": "Synthetic scenarios are never production-visible"
  }
}
```

### Fail-Closed Default

When unsure, use this default:

```json
{
  "query_authority": {
    "level": "SYSTEM",
    "requires": {
      "permissions": ["UNKNOWN"]
    },
    "allow_in": {
      "customer": { "preflight": false, "production": false },
      "founder": { "preflight": false, "production": false }
    },
    "failure_mode": "HIDE",
    "notes": "Fail-closed default - requires explicit promotion"
  }
}
```

---

## Compiler Responsibilities (AURORA_L2)

The compiler **MUST**:

1. Emit `query_authority` for **every panel**
2. Default explicitly - **no implicit fallbacks**
3. Fail compilation if missing

### Forbidden (Compiler)

| Forbidden | Why |
|-----------|-----|
| Infer from endpoint | Endpoint name is not authority |
| Infer from domain | Domain is not authority |
| Infer from console kind | Console kind is environment, not authority |
| Silent default | Missing authority must fail, not assume |

---

## UI Responsibilities (Non-Negotiable)

Before **any API call**:

```typescript
if (!canQuery(panel.query_authority, consoleContext, authContext)) {
  return renderBoundary(panel.query_authority.failure_mode);
}
```

### UI Must NEVER

| Forbidden | Correct Behavior |
|-----------|------------------|
| Retry on 403 | 403 is truth |
| Infer permission from response | Check before call |
| Log errors for denied queries | Denied is expected |
| Mask as "backend error" | Show appropriate boundary |

---

## Relationship to Other Dimensions

| Dimension | Controlled by | Question |
|-----------|---------------|----------|
| What exists | AURORA_L2 intent | Is this panel in the projection? |
| What can be done | Capability binding | Can user trigger this action? |
| What can be queried | Query authority | Can user see this data? |

These are **orthogonal**. A panel can exist but not be queryable.

---

## Key Distinctions

> **Visibility ≠ Queryability**
> A panel can be visible in projection but not queryable by user.

> **Queryability ≠ Executability**
> A user can see data but not take action on it.

---

## Prevention Rules (Claude & Humans)

### Claude MUST NOT

1. Guess authority based on endpoint names
2. Infer authority from domain placement
3. Assume founder has access to everything
4. Default to USER level without verification
5. Skip `query_authority` in projection output

### Humans MUST NOT

1. Relax backend permissions for preflight
2. Add `allow_in` flags without verification
3. Use SYNTHETIC in production
4. Expose INTERNAL data through projection

---

## Validation

Before any panel reaches production:

```
QUERY AUTHORITY CHECK
- query_authority present: YES / NO
- level valid enum: YES / NO
- requires.permissions non-empty: YES / NO
- allow_in.customer declared: YES / NO
- allow_in.founder declared: YES / NO
- failure_mode valid enum: YES / NO
- SYNTHETIC in production: MUST BE NO
```

If any check fails → **panel is INVALID**.

---

## References

- Schema: `docs/schemas/query_authority_schema.json`
- PIN-390: Four-Console Query Authority Model
- PIN-389: Epistemic Safety Protocol
- SESSION_PLAYBOOK.yaml: Section 41 (Query Authority)
