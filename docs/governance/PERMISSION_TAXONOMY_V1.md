# Permission Taxonomy v1

**Status:** ACTIVE (Constitutional)
**Created:** 2026-01-02
**Reference:** PIN-271 (RBAC Authority Separation)

---

## Purpose

This document defines the canonical permission model for AOS. Every permission
must be declared here before it can be used in code. No ad-hoc permissions.

---

## Permission Format

All permissions follow the pattern:

```
{action}:{resource}[:{scope}]
```

Where:
- `action` - what operation is being performed
- `resource` - what is being acted upon
- `scope` - optional scope modifier (team, account, system)

---

## Actions (Verbs)

| Action | Meaning | Mutating |
|--------|---------|----------|
| `read` | View, list, query | No |
| `write` | Create, update | Yes |
| `delete` | Remove, archive | Yes |
| `execute` | Trigger, invoke | Yes |
| `admin` | Manage settings, members | Yes |
| `audit` | View logs, traces, history | No |

---

## Resources (Nouns)

### Core Execution Resources

| Resource | Description | Owner Layer |
|----------|-------------|-------------|
| `runs` | Agent execution runs | L4 |
| `agents` | Agent definitions | L4 |
| `skills` | Skill definitions | L4 |
| `traces` | Execution traces | L6 |
| `policies` | Enforcement policies | L4 |

### Observability Resources

| Resource | Description | Owner Layer |
|----------|-------------|-------------|
| `metrics` | Prometheus metrics | L6 |
| `logs` | Application logs | L6 |
| `incidents` | Incident records | L4 |
| `alerts` | Alert configurations | L4 |

### Account Resources

| Resource | Description | Owner Layer |
|----------|-------------|-------------|
| `account` | Enterprise account settings | L4 |
| `team` | Team management | L4 |
| `members` | User membership | L4 |
| `billing` | Billing and usage | L4 |
| `keys` | API key management | L4 |

### System Resources

| Resource | Description | Owner Layer |
|----------|-------------|-------------|
| `system` | System-wide settings | L4 |
| `ops` | Ops console access | L4 |
| `replay` | Replay capabilities | L4 |

---

## Scope Modifiers

| Scope | Meaning | Example |
|-------|---------|---------|
| (none) | Actor's own tenant | `read:runs` |
| `:team` | Team-scoped | `admin:members:team` |
| `:account` | Account-scoped | `read:billing:account` |
| `:system` | Cross-tenant/system | `read:metrics:system` |

---

## Permission Matrix by ActorType

### EXTERNAL_PAID (Enterprise Customers)

```yaml
allowed:
  - read:runs
  - write:runs
  - read:agents
  - write:agents
  - read:skills
  - read:traces
  - read:policies
  - write:policies
  - read:metrics
  - read:logs
  - read:incidents
  - read:account
  - admin:team           # Team admin
  - admin:members:team   # Manage team members
  - read:billing:account
  - read:keys
  - write:keys

forbidden:
  - delete:*:system
  - admin:*:system
  - read:*:system        # No cross-tenant
  - ops:*
```

### EXTERNAL_TRIAL (Trial/Beta Users)

```yaml
allowed:
  - read:runs
  - write:runs           # Limited quota
  - read:agents
  - write:agents         # Limited quota
  - read:skills
  - read:traces
  - read:policies        # Can view, not create
  - read:metrics
  - read:incidents

forbidden:
  - write:policies       # No policy creation in trial
  - delete:*
  - admin:*
  - billing:*
  - read:*:system
```

### INTERNAL_PRODUCT (Xuniverz, AI Console, M12 Agents)

```yaml
allowed:
  - read:*               # Full read access
  - write:runs
  - write:agents
  - write:traces
  - execute:*
  - audit:*

forbidden:
  - delete:*:system
  - admin:account        # Cannot manage customer accounts
  - admin:billing
```

### OPERATOR (Founders, Ops Team)

```yaml
allowed:
  - "*"                  # Full access

forbidden:
  - (none)               # Operators can do anything

notes:
  - All actions audited
  - Cannot disable audit
```

### SYSTEM (CI, Workers, Replay)

```yaml
allowed:
  - read:*
  - write:runs
  - write:traces
  - write:metrics
  - execute:replay

forbidden:
  - delete:*
  - admin:*
  - write:policies
  - write:billing

notes:
  - Fixed permissions, not role-derived
  - Defined in SYSTEM_ACTORS
```

---

## Role → Permission Mapping

### Standard Roles

| Role | Permissions | Typical ActorType |
|------|-------------|-------------------|
| `founder` | `*` | OPERATOR |
| `admin` | `read:*`, `write:*`, `admin:account` | EXTERNAL_PAID |
| `team_admin` | `read:*`, `write:*`, `admin:team`, `admin:members:team` | EXTERNAL_PAID |
| `developer` | `read:*`, `write:runs`, `write:agents` | EXTERNAL_PAID |
| `viewer` | `read:*` | EXTERNAL_PAID, EXTERNAL_TRIAL |
| `machine` | `read:*`, `write:runs`, `write:traces` | SYSTEM |
| `ci` | `read:*`, `write:metrics` | SYSTEM |
| `replay` | `read:*` | SYSTEM |

### Role Permission Expansion

```python
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "founder": {"*"},

    "admin": {
        "read:*", "write:*", "delete:*",
        "admin:account", "admin:team", "admin:members",
        "read:billing:account", "write:billing:account",
    },

    "team_admin": {
        "read:*", "write:*",
        "admin:team", "admin:members:team",
    },

    "developer": {
        "read:*",
        "write:runs", "write:agents", "write:skills",
        "execute:*",
    },

    "viewer": {
        "read:*",
        "audit:*",
    },

    "machine": {
        "read:*",
        "write:runs", "write:traces", "write:metrics",
        "execute:*",
    },

    "ci": {
        "read:*",
        "write:metrics", "write:traces",
    },

    "replay": {
        "read:*",
        "execute:replay",
    },
}
```

---

## Permission Evaluation Rules

### Rule 1: Explicit Deny Wins

If a permission is in the forbidden list for an ActorType, it is denied
regardless of roles.

### Rule 2: ActorType Restricts Roles

Roles cannot grant permissions beyond what ActorType allows.

```python
def authorize(actor, permission):
    # 1. Check ActorType restrictions first
    if permission in ACTOR_TYPE_FORBIDDEN[actor.actor_type]:
        return DENY

    # 2. Then check role grants
    if actor.has_permission(permission):
        return ALLOW

    return DENY
```

### Rule 3: Scope Inheritance

- Team scope implies own resources within team
- Account scope implies all teams in account
- System scope implies all tenants (operator only)

```python
# If actor has "read:runs:account"
# They can read runs in any team within their account
```

### Rule 4: Wildcard Expansion

Wildcards expand at evaluation time, not storage time.

```python
# "read:*" matches "read:runs", "read:agents", etc.
# But NOT "write:runs"

def matches_permission(granted: str, requested: str) -> bool:
    if granted == "*":
        return True

    granted_parts = granted.split(":")
    requested_parts = requested.split(":")

    for g, r in zip(granted_parts, requested_parts):
        if g == "*":
            continue
        if g != r:
            return False

    return len(granted_parts) >= len(requested_parts)
```

---

## Enterprise Team Hierarchy

```
Account (account_id)
├── Admin (account-level admin)
├── Billing (account-level billing viewer)
│
├── Team A (team_id: team_a)
│   ├── Team Admin (admin:team, admin:members:team)
│   ├── Developer 1 (developer)
│   └── Developer 2 (developer)
│
└── Team B (team_id: team_b)
    ├── Team Admin (admin:team, admin:members:team)
    └── Viewer (viewer)
```

### Permission Scoping Examples

| Actor | Permission | Can Access |
|-------|------------|------------|
| Team A Developer | `read:runs` | Team A runs only |
| Account Admin | `read:runs:account` | All teams' runs |
| Team A Admin | `admin:members:team` | Team A members only |
| Account Admin | `admin:members` | All account members |

---

## Adding New Permissions

### Process

1. **Propose** in this document (PR required)
2. **Review** for:
   - Does this overlap with existing permissions?
   - Is the scope correct?
   - Which ActorTypes should have it?
3. **Add** to ROLE_PERMISSIONS mapping
4. **Update** AuthorizationEngine if new evaluation logic needed
5. **Document** in changelog below

### Forbidden Patterns

| Pattern | Why Forbidden |
|---------|---------------|
| `super:*` | No "super" powers, use explicit permissions |
| `all:*` | Too broad, use specific resources |
| `bypass:*` | No bypasses, use operator role |
| `temp:*` | No temporary permissions |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-02 | Initial taxonomy created (v1) |

---

## Related Documents

- `docs/governance/RBAC_AUTHORITY_SEPARATION_DESIGN.md` - Architecture
- `docs/memory-pins/PIN-271-rbac-authority-separation.md` - Governance PIN
- `backend/app/auth/authorization.py` - Implementation (pending)

---

## Invariant

> **Permissions must be declared before they can be used.**
> **Roles cannot exceed ActorType limits.**
> **No ad-hoc permission strings.**
