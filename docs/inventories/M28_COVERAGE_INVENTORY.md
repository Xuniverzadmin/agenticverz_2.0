# M28 Coverage Inventory

**Date:** 2026-01-05
**Source:** `backend/app/auth/authorization.py`

---

## Actions

| Action | Description | M7 Equivalent |
|--------|-------------|---------------|
| `read` | View/query resources | `read` |
| `write` | Create/modify resources | `write` |
| `delete` | Remove resources | `delete` |
| `admin` | Administrative operations | `admin` |
| `execute` | Run/invoke operations | `execute` |
| `audit` | View audit trails | N/A |
| `billing` | Billing operations | N/A |

---

## Resources (from ROLE_PERMISSIONS)

| Resource | Actions Available | Notes |
|----------|-------------------|-------|
| `*` (wildcard) | read, write, delete, admin, execute, audit | Operator/admin only |
| `runs` | read, write | Execution traces |
| `agents` | read, write | Agent management |
| `skills` | read, write | Skill registry |
| `traces` | read, write | Trace data |
| `metrics` | read, write | Metrics emission |
| `ops` | read, write | Operations |
| `account` | admin | Account management |
| `team` | admin | Team management |
| `members` | admin | Member management |
| `members:team` | admin | Team-scoped members |
| `billing:account` | read, write | Account billing |
| `system` | read, delete, admin | System-level ops |
| `policies` | read, write | Policy management |
| `replay` | read, execute, audit, admin | Replay capability |
| `predictions` | read, execute, audit, admin | Prediction capability |

---

## Roles

### Operator Roles
| Role | Permissions | Description |
|------|-------------|-------------|
| `founder` | `*` (everything) | Full system access |
| `operator` | `read:*`, `write:*`, `delete:*`, `admin:*` | Platform operators |

### Enterprise Roles
| Role | Key Permissions | Description |
|------|-----------------|-------------|
| `admin` | read, write, delete, admin:account/team/members, billing | Account admin |
| `team_admin` | read, write, admin:team/members:team | Team leadership |
| `developer` | read, write:runs/agents/skills, execute | Engineering |
| `viewer` | read, audit | Read-only access |

### System Roles
| Role | Key Permissions | Description |
|------|-----------------|-------------|
| `machine` | read, write:runs/traces/metrics, execute | API key access |
| `ci` | read, write:metrics/traces | CI/CD systems |
| `replay` | read, execute:replay | Replay system |
| `predictions` | read, execute:predictions | Prediction system |
| `automation` | read, write:metrics | Automation |
| `worker` | read, write:runs/traces | Worker processes |

### Legacy Roles (Migration Compatibility)
| Role | Maps To |
|------|---------|
| `readonly` | `viewer` |
| `infra` | Custom (ops, metrics) |
| `dev` | `developer` |

---

## ActorTypes

| Type | Allowed Actions | Forbidden Actions |
|------|-----------------|-------------------|
| `EXTERNAL_PAID` | read, write, delete, admin:team, billing:read | admin:system, delete:system, read:system |
| `EXTERNAL_TRIAL` | read, write:runs/agents, execute | write:policies, delete, admin, billing, read:system |
| `INTERNAL_PRODUCT` | read, write, execute, audit | delete:system, admin:account/billing |
| `OPERATOR` | Everything | None |
| `SYSTEM` | read, write:runs/traces/metrics, execute | delete, admin, write:policies/billing |

---

## Capability Coverage

### Covered by M28 (Complete)
| Capability | Resource | Actions |
|------------|----------|---------|
| Replay | `replay` | read, execute, audit, admin |
| Predictions | `predictions` | read, execute, audit, admin |
| Runs | `runs` | read, write |
| Agents | `agents` | read, write |
| Traces | `traces` | read, write |

### Gaps (M7 has, M28 needs)

| M7 Resource | M7 Actions | M28 Status |
|-------------|------------|------------|
| `memory_pin` | read, write, delete, admin | **MISSING** |
| `prometheus` | reload, query | **MISSING** (reclassify as ops) |
| `costsim` | read, write | **MISSING** |
| `policy` | read, write, approve | **PARTIAL** (policies exists) |
| `agent` | heartbeat, register | **MISSING** (lifecycle actions) |
| `runtime` | simulate, capabilities, query | **MISSING** |
| `recovery` | suggest, execute | **MISSING** |

---

## Enforcement Points

### Covered by M28

1. **Gateway Authority** (`authority.py`)
   - `require_replay_read/execute/audit/admin`
   - `require_predictions_read/execute/audit/admin`

2. **Authorization Engine** (`authorization.py`)
   - `authorize(actor, resource, action)`
   - ActorType restrictions
   - Tenant isolation

### Not Yet Covered

1. Policy approval flows
2. Memory PIN operations
3. Cost simulation
4. Agent lifecycle (heartbeat, register)
5. Runtime operations
6. Recovery operations

---

## Migration Requirements

### Resources to Add to M28

```python
# Add to AuthorizationEngine.ROLE_PERMISSIONS
ROLE_PERMISSIONS = {
    ...
    "developer": {
        ...
        "read:memory_pin",
        "write:memory_pin",
        "read:costsim",
        "write:costsim",
        "read:runtime",
        "execute:runtime",
        "read:recovery",
    },
    "admin": {
        ...
        "admin:memory_pin",
        "delete:memory_pin",
        "admin:costsim",
        "execute:recovery",
    },
}
```

### Actions to Add

| Action | For Resources |
|--------|---------------|
| `approve` | policies |
| `heartbeat` | agents |
| `register` | agents |
| `simulate` | runtime |
| `query` | runtime |
| `suggest` | recovery |

---

## Summary

| Category | Count |
|----------|-------|
| Actions defined | 7 |
| Resources covered | 15+ |
| Roles defined | 15 |
| ActorTypes | 5 |
| M7 gaps to fill | 7 resources |

---

## Changelog

| Date | Action | Author |
|------|--------|--------|
| 2026-01-05 | Initial inventory | Claude Opus 4.5 |
