# PIN-391: RBAC Unification — Schema-First Authorization

**Status:** ACTIVE
**Created:** 2026-01-11
**Category:** Architecture / Security / Governance

---

## Summary

Introduced a canonical RBAC schema (`RBAC_RULES.yaml`) as the single source of truth for authorization rules. This prevents 403 drift between gateway and RBAC middleware by declaring access rules once and deriving enforcement from the schema.

---

## Problem

With dual authority sources (gateway_config.py + rbac_middleware.py):

```
Endpoint added to gateway → not in middleware → 403
Endpoint removed from one → other still allows → security gap
Claude guesses access level → inconsistent enforcement
```

This creates:
- Silent 403 errors in preflight
- Configuration drift between components
- No single source of truth for access control
- Claude inventing access rules instead of declaring them

---

## Solution

Single canonical RBAC schema with loader and CI enforcement:

```
RBAC_RULES.yaml (schema)
    ↓
rbac_rules_loader.py (loader)
    ↓
rbac_middleware.py (enforcement, mirrors schema)
    ↓
check_rbac_alignment.py (CI guard)
```

### Authorization is Declarative

- Rules MUST be declared in RBAC_RULES.yaml
- Code may mirror rules temporarily, but must not invent them
- Claude MUST NOT classify endpoints by inference
- Missing rules = BLOCKED, not guessed

---

## Schema

**Location:** `design/auth/RBAC_RULES.yaml`

### Access Tiers

| Tier | Description | Auth Required |
|------|-------------|---------------|
| `PUBLIC` | Unauthenticated access. Extremely rare. | No |
| `SESSION` | Authenticated user session required. | Yes |
| `PRIVILEGED` | Specific permission or role required. | Yes + permissions |
| `SYSTEM` | Engine / SDSR / control-plane only. | Yes + system |

### Rule Structure

```yaml
rules:
  - rule_id: INCIDENTS_READ_PREFLIGHT
    pin: PIN-370
    path_prefix: /api/v1/incidents/
    methods: [GET]
    access_tier: PUBLIC
    allow_console: [customer]
    allow_environment: [preflight]
    temporary: true
    expires: "2026-03-01"
    description: >
      SDSR Incidents API for preflight validation.
      TEMPORARY - must be SESSION tier in production.
```

### Dimensions

| Dimension | Values |
|-----------|--------|
| `console_kind` | customer, founder |
| `environment` | preflight, production |

---

## Artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| RBAC Schema | `design/auth/RBAC_RULES.yaml` | Single source of truth |
| Loader | `backend/app/auth/rbac_rules_loader.py` | Python API for rules |
| CI Guard | `scripts/ci/check_rbac_alignment.py` | Alignment validation |
| Playbook | `docs/playbooks/SESSION_PLAYBOOK.yaml` (Section 26) | Claude guardrail |
| PIN-391 | This document | Memory pin reference |

---

## Loader API

```python
from app.auth.rbac_rules_loader import (
    load_rbac_rules,
    resolve_rbac_rule,
    get_public_paths,
    is_path_public,
    RBACRule,
    AccessTier,
)

# Get all rules
rules = load_rbac_rules()

# Resolve for specific context
rule = resolve_rbac_rule(
    path="/api/v1/incidents/",
    method="GET",
    console_kind="customer",
    environment="preflight",
)

# Get PUBLIC paths for backward compatibility
public_paths = get_public_paths(environment="preflight")

# Check if path is public
if is_path_public("/api/v1/incidents/", "GET", "customer", "preflight"):
    # Skip auth
```

---

## CI Guard

The alignment guard validates RBAC consistency:

```bash
# Basic validation
python3 scripts/ci/check_rbac_alignment.py

# Verbose output
python3 scripts/ci/check_rbac_alignment.py --verbose

# With fix suggestions
python3 scripts/ci/check_rbac_alignment.py --fix-suggestions
```

### Validations Performed

1. **Middleware Alignment** - PUBLIC_PATHS matches RBAC_RULES.yaml
2. **Schema Coverage** - All YAML PUBLIC paths are in middleware
3. **Temporary Rules Audit** - Flags rules nearing expiry

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All validations passed |
| 1 | RBAC alignment violations detected |
| 2 | File not found or parse error |

---

## Claude Guardrail (LOCKED)

**Location:** `docs/playbooks/SESSION_PLAYBOOK.yaml` Section 26

### Hard Rules

| Rule ID | Name | Description |
|---------|------|-------------|
| RBAC-001 | No Inference | Claude MUST NOT classify endpoints by inference |
| RBAC-002 | No PUBLIC_PATHS Mod | MUST NOT modify without schema update |
| RBAC-003 | Schema First | All decisions reference RBAC_RULES.yaml |
| RBAC-004 | Report Missing | If no rule exists, report "RBAC RULE MISSING" |

### Decision Ladder

1. **Is endpoint in RBAC_RULES.yaml?**
   - Yes → Modify rule in schema
   - No → STOP and propose new rule

2. **Is this preflight-only?**
   - Yes → SYSTEM tier, preflight-only
   - Default → Never PUBLIC

3. **Is PUBLIC_PATHS involved?**
   - Only as temporary mirror
   - Must reference a PIN

---

## Migration Path

### Phase 0 (COMPLETE)
- [x] Create RBAC_RULES.yaml schema
- [x] Create rbac_rules_loader.py
- [x] Add temporary exception comments
- [x] Create CI alignment guard
- [x] Add Claude guardrail to playbook

### Phase 1 (TODO)
- [ ] Replace hardcoded PUBLIC_PATHS with `get_public_paths()`
- [ ] Wire resolve_rbac_rule into authorization flow
- [ ] Add all API routes to RBAC_RULES.yaml

### Phase 2 (TODO)
- [ ] Remove temporary SDSR rules (after hardening)
- [ ] Deprecate PUBLIC_PATHS behind feature flag
- [ ] Full schema-driven enforcement

### Phase 3 (TODO)
- [ ] Generate query_authority from RBAC_RULES
- [ ] Unify gateway_config.py with schema
- [ ] Remove all legacy mappers

---

## Temporary Rules

The following rules are temporary and require review:

| Rule ID | Path | Expires |
|---------|------|---------|
| ACTIVITY_READ_PREFLIGHT | /api/v1/activity/ | 2026-03-01 |
| POLICY_PROPOSALS_READ_PREFLIGHT | /api/v1/policy-proposals/ | 2026-03-01 |
| INCIDENTS_READ_PREFLIGHT | /api/v1/incidents/ | 2026-03-01 |

These exist for SDSR preflight validation and must be migrated to SESSION tier for production.

---

## Root Cause Analysis

The 403 incident on `/api/v1/incidents` occurred because:

1. `gateway_config.py` had the path marked as public
2. `rbac_middleware.py` did not have it in PUBLIC_PATHS
3. No single source of truth existed
4. Claude was asked to "fix" without a schema to reference

The fix (adding to PUBLIC_PATHS) was tactical. This PIN establishes the structural fix: a canonical schema that both components derive from.

---

## Related PINs

- [PIN-370](PIN-370-sdsr-activity-incident-lifecycle.md) - SDSR Activity/Incident Lifecycle
- [PIN-373](PIN-373-sdsr-policy-proposal-lifecycle.md) - SDSR Policy Proposal Lifecycle
- [PIN-390](PIN-390-four-console-query-authority-model.md) - Four-Console Query Authority Model
- [PIN-271](PIN-271-rbac-architecture-directive.md) - RBAC Architecture Directive

---

## Key Insight

> **Authorization is declared, not inferred.**
> Code may mirror rules temporarily, but must not invent them.

This PIN makes that invariant enforceable.
