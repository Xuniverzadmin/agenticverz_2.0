# PIN-392: Query Authority — Data Access Privileges

**Status:** ACTIVE
**Created:** 2026-01-11
**Category:** Architecture / Security / Authorization
**Related:** PIN-391 (RBAC Unification)

---

## Summary

Query Authority controls WHAT KIND OF DATA a request may ask for. This is orthogonal to route access (WHO may touch WHAT). Both RBAC and Query Authority must be declared, not inferred.

---

## Core Principle (LOCKED)

> **Data queries are privileges.**
> They must be declared, authorized, constrained, and observable — not inferred from routes or roles.

---

## What Query Authority Governs

| Constraint | Purpose |
|------------|---------|
| `include_synthetic` | Whether synthetic/test data is visible |
| `include_deleted` | Whether soft-deleted records are visible |
| `include_internal` | Whether internal/system records are visible |
| `max_rows` | Maximum number of rows per request |
| `max_time_range_days` | Maximum time range for queries |
| `aggregation` | Aggregation level (NONE/BASIC/FULL) |
| `export_allowed` | Whether bulk export is permitted |

---

## Schema

### Defaults (in RBAC_RULES.yaml)

```yaml
query_authority_defaults:
  version: 1
  include_synthetic: false
  include_deleted: false
  include_internal: false
  max_rows: 100
  max_time_range_days: 7
  aggregation: "NONE"
  export_allowed: false
```

### Per-Rule Declaration

```yaml
- rule_id: INCIDENTS_READ_PREFLIGHT
  path_prefix: /api/v1/incidents/
  methods: [GET]
  access_tier: PUBLIC
  allow_console: [customer]
  allow_environment: [preflight]
  query_authority:
    include_synthetic: true
    max_rows: 500
    max_time_range_days: 30
    aggregation: "BASIC"
```

---

## Aggregation Levels

| Level | Description |
|-------|-------------|
| `NONE` | No aggregation, raw records only |
| `BASIC` | Count, sum, avg on non-sensitive fields |
| `FULL` | All aggregations including sensitive metrics |

---

## Enforcement

### Python API

```python
from app.auth.rbac_rules_loader import resolve_rbac_rule
from app.auth.query_authority import enforce_query_authority

# Resolve the rule
rule = resolve_rbac_rule(path, method, console, env, strict=True)

# Enforce constraints
enforce_query_authority(
    rule.query_authority,
    include_synthetic=request.query.get("include_synthetic", False),
    requested_rows=int(request.query.get("limit", 100)),
)
```

### Exception Handling

```python
from app.auth.query_authority import QueryAuthorityViolation

try:
    enforce_query_authority(qa, include_synthetic=True)
except QueryAuthorityViolation as e:
    return JSONResponse(
        status_code=403,
        content={"error": str(e), "constraint": e.constraint}
    )
```

---

## Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| Schema | `design/auth/RBAC_RULES.yaml` | query_authority_defaults + per-rule |
| Loader | `backend/app/auth/rbac_rules_loader.py` | QueryAuthority dataclass |
| Enforcement | `backend/app/auth/query_authority.py` | enforce_query_authority() |
| CI Guard | `scripts/ci/check_rbac_alignment.py` | Validates declarations |

---

## CI Validations

1. **query_authority_defaults exists** in RBAC_RULES.yaml
2. **Production rules cannot allow include_synthetic**
3. **Preflight data endpoints should declare query_authority**
4. **Expired temporary rules are BLOCKING errors**

---

## Promotion Rules

Production can only be **more restrictive** than preflight:

| Constraint | Promotion Rule |
|------------|----------------|
| `include_synthetic` | Must be `false` in production |
| `max_rows` | prod ≤ preflight |
| `max_time_range_days` | prod ≤ preflight |
| `aggregation` | prod ≤ preflight (NONE < BASIC < FULL) |

Validation:
```python
from app.auth.query_authority import validate_promotion_safety

violations = validate_promotion_safety(preflight_qa, production_qa)
if violations:
    raise PromotionBlocked(violations)
```

---

## Mental Model

```
RBAC answers:          "WHO may touch WHAT?"
QueryAuthority answers: "HOW MUCH may they see?"
SDSR answers:          "Does the system actually behave that way?"
UI answers:            "What should the user be allowed to try?"
```

Each layer does **one job**.

---

## Migration Path

### Phase 1 (COMPLETE)
- [x] Add query_authority_defaults to RBAC_RULES.yaml
- [x] Add QueryAuthority dataclass to loader
- [x] Add query_authority to SDSR preflight rules
- [x] Add query_authority to production rules
- [x] Create enforcement helpers
- [x] Add CI validation

### Phase 2 (TODO)
- [ ] Wire enforcement into API endpoints
- [ ] Add query_authority to UI projection
- [ ] Add SDSR verification for query_authority

### Phase 3 (TODO)
- [ ] Generate OpenAPI docs from query_authority
- [ ] Add rate limiting tiers based on query_authority

---

## Related PINs

- [PIN-391](PIN-391-rbac-unification-schema-first-authorization.md) - RBAC Unification
- [PIN-390](PIN-390-four-console-query-authority-model.md) - Four-Console Query Authority Model
- [PIN-370](PIN-370-sdsr-activity-incident-lifecycle.md) - SDSR Lifecycle

---

## Key Insight

> **Route access ≠ data access.**
> A user may reach an endpoint but still be constrained in what they can query.
> Both layers must be declared, both must be enforced.
