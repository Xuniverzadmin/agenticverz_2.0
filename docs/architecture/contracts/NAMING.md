# NAMING CONTRACT

**Status:** ENFORCED
**Effective:** 2026-01-17
**Scope:** All runtime schemas, API responses, database columns
**Reference:** PIN-LIM Post-Implementation Design Fix

---

## Prime Directive

> **Names are contracts. Inconsistent names are bugs.**

---

## 1. Runtime Schema Naming (L4/L5)

Runtime objects use **semantic field names** — short, domain-accurate, no context suffix.

| Pattern | Example | Rationale |
|---------|---------|-----------|
| `{noun}` | `tokens`, `runs`, `cost_cents` | Direct, unambiguous |
| `{noun}_{unit}` | `cost_cents`, `duration_ms` | Unit in name prevents confusion |
| `{state}` | `status`, `decision` | Single-word states |

**Forbidden in runtime schemas:**

| Anti-Pattern | Why Forbidden |
|--------------|---------------|
| `tokens_remaining` | Adds context that belongs in API layer |
| `current_cost` | "Current" is temporal — runtime is snapshot |
| `total_runs_count` | Redundant suffix |
| `is_tokens_exceeded` | Boolean prefix belongs in predicate methods |

---

## 2. API Response Naming (L2)

API responses **may add context** for client clarity, but **must map explicitly**.

| Runtime Field | API Field | Mapping Location |
|---------------|-----------|------------------|
| `tokens` | `tokens_remaining` | `app/api/_adapters/` |
| `runs` | `runs_remaining` | `app/api/_adapters/` |
| `cost_cents` | `cost_remaining_cents` | `app/api/_adapters/` |

**Rule:** API field names are **derived**, never authoritative.

---

## 3. Database Column Naming (L6)

Database columns follow **snake_case**, match runtime schemas.

| Runtime | Database | Notes |
|---------|----------|-------|
| `tokens` | `tokens` | Exact match |
| `cost_cents` | `cost_cents` | Exact match |
| `created_at` | `created_at` | Timestamps use `_at` suffix |

**Forbidden:**

| Anti-Pattern | Why Forbidden |
|--------------|---------------|
| `tokenCount` | camelCase in DB |
| `remaining_tokens` | Context in DB column |
| `createdDate` | Use `_at` for timestamps |

---

## 4. Enum and Constant Naming

| Type | Pattern | Example |
|------|---------|---------|
| Enum values | `UPPER_SNAKE` | `ALLOW`, `BLOCK`, `WARN` |
| Enum classes | `PascalCase` | `SimulationDecision`, `LimitCategory` |
| Constants | `UPPER_SNAKE` | `MAX_OVERRIDE_HOURS = 168` |

---

## 5. File and Module Naming

| Type | Pattern | Example |
|------|---------|---------|
| Service modules | `{domain}_service.py` | `simulation_service.py` |
| Schema modules | `{domain}.py` | `simulation.py` |
| API routers | `{action}.py` or `{domain}_crud.py` | `simulate.py`, `policy_limits_crud.py` |
| Adapters | `{domain}.py` in `_adapters/` | `_adapters/limits.py` |

---

## 6. Naming Drift Detection

**CI Check:** `scripts/ci/check_naming_contract.py`

Detects:
- Runtime schemas with `_remaining`, `_current`, `_total` suffixes
- API responses accessing runtime fields directly (no adapter)
- Database columns with camelCase

---

## 7. Violation Response

```
NAMING CONTRACT VIOLATION

Field: {field_name}
Location: {file}:{line}
Rule violated: {rule_id}

Expected pattern: {expected}
Found: {actual}

Fix: {specific guidance}
```

---

## Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│                  NAMING AUTHORITY STACK                     │
├─────────────────────────────────────────────────────────────┤
│  1. Runtime schemas: semantic, short, no context            │
│  2. Database columns: match runtime exactly                 │
│  3. API responses: may add context via adapters             │
│  4. Adapters: explicit mapping, single location             │
│  5. Never: infer API names from runtime field names         │
└─────────────────────────────────────────────────────────────┘
```
