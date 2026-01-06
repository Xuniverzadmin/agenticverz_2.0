# Authorization Authority Surface Matrix

**Generated:** 2026-01-05
**Status:** T10 COMPLETE
**Reference:** PIN-310 (Fast-Track M7 Closure)

---

## Purpose

This document provides an **exhaustive enumeration** of all authorization decisions in AOS.
It is the foundation for authority exhaustion testing (T12-T13).

---

## Principal Types

| ID | ActorType | Description | Scope |
|----|-----------|-------------|-------|
| P1 | EXTERNAL_PAID | Paying customers | Tenant-scoped |
| P2 | EXTERNAL_TRIAL | Beta/trial users | Tenant-scoped |
| P3 | INTERNAL_PRODUCT | Xuniverz, AI Console, M12 agents | No tenant scope |
| P4 | OPERATOR | Founders, ops team | Cross-tenant |
| P5 | SYSTEM | CI, workers, replay | No tenant scope |

---

## System Actors (Pre-defined)

| Actor ID | ActorType | Roles | Permissions |
|----------|-----------|-------|-------------|
| system:ci | SYSTEM | ci, automation | read:*, write:metrics, write:traces |
| system:worker | SYSTEM | machine, worker | read:*, write:runs, write:traces |
| system:replay | SYSTEM | replay, readonly | read:*, execute:replay |
| system:internal_product | INTERNAL_PRODUCT | internal, product | read:*, write:runs, write:agents, execute:* |

---

## M28 Native Resources

These resources are handled directly by M28 (`AuthorizationEngine`):

| Resource | Actions | Notes |
|----------|---------|-------|
| runs | read, write, delete | Execution traces |
| agents | read, write, delete | Agent management |
| skills | read, write, delete | Skill registry |
| traces | read, write | Trace data |
| metrics | read, write, admin | Metrics emission |
| ops | read, write | Operations |
| account | read, write, admin | Account management |
| team | read, write, admin | Team management |
| members | read, write, admin | Member management |
| members:team | read, write, admin | Team member management |
| billing:account | read, write | Account billing |
| system | read, admin, delete | System administration |
| policies | read, write, admin | Policy management |
| replay | read, execute, admin, audit | Replay capability (CAP-001) |
| predictions | read, execute, admin, audit | Prediction capability (CAP-004) |

---

## M7 Legacy Resources (Mapped via M7→M28)

These resources require mapping before M28 evaluation:

| M7 Resource | M7 Action | M28 Resource | M28 Action | Scope | Status |
|-------------|-----------|--------------|------------|-------|--------|
| memory_pin | read | memory_pins | read | - | VALID |
| memory_pin | write | memory_pins | write | - | VALID |
| memory_pin | delete | memory_pins | delete | - | VALID |
| memory_pin | admin | memory_pins | admin | - | VALID |
| costsim | read | costsim | read | - | VALID |
| costsim | write | costsim | write | - | VALID |
| policy | read | policies | read | - | VALID |
| policy | write | policies | write | - | VALID |
| policy | approve | policies | admin | - | VALID |
| agent | read | agents | read | - | VALID |
| agent | write | agents | write | - | VALID |
| agent | delete | agents | delete | - | VALID |
| agent | heartbeat | agents | write | lifecycle | VALID |
| agent | register | agents | write | lifecycle | VALID |
| runtime | simulate | runtime | execute | - | VALID |
| runtime | capabilities | runtime | read | - | VALID |
| runtime | query | runtime | read | - | VALID |
| recovery | suggest | recovery | read | - | VALID |
| recovery | execute | recovery | execute | - | VALID |
| prometheus | query | metrics | read | - | DEPRECATED |
| prometheus | reload | metrics | admin | - | DEPRECATED |

---

## Actions by Category

### Read Actions
| Action | Description | Entry Points |
|--------|-------------|--------------|
| read | Standard read | API, Worker |
| query | Query operations | API |
| suggest | Get suggestions | API |
| capabilities | Get capabilities | API |
| audit | Audit access | API |

### Write Actions
| Action | Description | Entry Points |
|--------|-------------|--------------|
| write | Standard write | API, Worker |
| delete | Delete resource | API |
| admin | Administrative action | API |
| execute | Execute operation | API, Worker |
| approve | Approval action | API |
| heartbeat | Lifecycle heartbeat | Worker |
| register | Registration | Worker |
| reload | Configuration reload | API (ops) |
| simulate | Run simulation | API |

---

## Role → Permission Matrix

| Role | Permissions |
|------|-------------|
| founder | * (all) |
| operator | read:*, write:*, delete:*, admin:* |
| admin | read:*, write:*, delete:*, admin:account, admin:team, admin:members, read:billing:account, write:billing:account, admin:replay, admin:predictions |
| team_admin | read:*, write:*, admin:team, admin:members:team |
| developer | read:*, write:runs, write:agents, write:skills, execute:*, execute:replay, execute:predictions |
| viewer | read:*, audit:*, read:replay, read:predictions, audit:replay, audit:predictions |
| machine | read:*, write:runs, write:traces, write:metrics, execute:*, execute:replay, execute:predictions |
| ci | read:*, write:metrics, write:traces |
| replay | read:*, execute:replay |
| predictions | read:*, execute:predictions |
| automation | read:*, write:metrics |
| worker | read:*, write:runs, write:traces |
| internal | read:*, write:runs, write:agents, execute:* |
| product | read:*, write:* |
| readonly | read:* |
| infra | read:*, write:ops, write:metrics |
| dev | read:*, write:runs, write:agents |

---

## ActorType Allowed/Forbidden Matrix

### EXTERNAL_PAID
| Allowed | Forbidden |
|---------|-----------|
| read:*, write:*, delete:*, admin:team, admin:members:team, read:billing:account | admin:system, delete:system, read:system |

### EXTERNAL_TRIAL
| Allowed | Forbidden |
|---------|-----------|
| read:*, write:runs, write:agents, execute:* | write:policies, delete:*, admin:*, billing:*, read:system |

### INTERNAL_PRODUCT
| Allowed | Forbidden |
|---------|-----------|
| read:*, write:*, execute:*, audit:* | delete:system, admin:account, admin:billing |

### OPERATOR
| Allowed | Forbidden |
|---------|-----------|
| * (everything) | (none) |

### SYSTEM
| Allowed | Forbidden |
|---------|-----------|
| read:*, write:runs, write:traces, write:metrics, execute:* | delete:*, admin:*, write:policies, write:billing |

---

## Authority Surface Matrix (Exhaustive)

This is the complete matrix of (Principal, Action, Resource) combinations to test.

### M28 Native Resources × Principals

| Resource | Action | P1 (PAID) | P2 (TRIAL) | P3 (INTERNAL) | P4 (OPERATOR) | P5 (SYSTEM) |
|----------|--------|-----------|------------|---------------|---------------|-------------|
| runs | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| runs | write | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| runs | delete | ALLOW | DENY | DENY | ALLOW | DENY |
| agents | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| agents | write | ALLOW | ALLOW | ALLOW | ALLOW | DENY |
| agents | delete | ALLOW | DENY | DENY | ALLOW | DENY |
| skills | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| skills | write | ALLOW | ALLOW | ALLOW | ALLOW | DENY |
| skills | delete | ALLOW | DENY | DENY | ALLOW | DENY |
| traces | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| traces | write | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| metrics | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| metrics | write | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| metrics | admin | ALLOW | DENY | DENY | ALLOW | DENY |
| ops | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| ops | write | ALLOW | DENY | ALLOW | ALLOW | DENY |
| account | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| account | write | ALLOW | DENY | DENY | ALLOW | DENY |
| account | admin | ALLOW | DENY | DENY | ALLOW | DENY |
| team | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| team | write | ALLOW | DENY | ALLOW | ALLOW | DENY |
| team | admin | ALLOW | DENY | DENY | ALLOW | DENY |
| policies | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| policies | write | ALLOW | DENY | ALLOW | ALLOW | DENY |
| policies | admin | ALLOW | DENY | DENY | ALLOW | DENY |
| system | read | DENY | DENY | ALLOW | ALLOW | ALLOW |
| system | admin | DENY | DENY | DENY | ALLOW | DENY |
| system | delete | DENY | DENY | DENY | ALLOW | DENY |
| replay | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| replay | execute | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| replay | admin | ALLOW | DENY | DENY | ALLOW | DENY |
| replay | audit | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| predictions | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| predictions | execute | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| predictions | admin | ALLOW | DENY | DENY | ALLOW | DENY |
| predictions | audit | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |

### M7 Legacy Resources × Principals (via Mapping)

| M7 Resource | M7 Action | P1 (PAID) | P2 (TRIAL) | P3 (INTERNAL) | P4 (OPERATOR) | P5 (SYSTEM) |
|-------------|-----------|-----------|------------|---------------|---------------|-------------|
| memory_pin | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| memory_pin | write | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| memory_pin | delete | ALLOW | DENY | DENY | ALLOW | DENY |
| memory_pin | admin | ALLOW | DENY | DENY | ALLOW | DENY |
| costsim | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| costsim | write | ALLOW | ALLOW | ALLOW | ALLOW | DENY |
| policy | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| policy | write | ALLOW | DENY | ALLOW | ALLOW | DENY |
| policy | approve | ALLOW | DENY | DENY | ALLOW | DENY |
| agent | read | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| agent | write | ALLOW | ALLOW | ALLOW | ALLOW | DENY |
| agent | delete | ALLOW | DENY | DENY | ALLOW | DENY |
| agent | heartbeat | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| agent | register | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| runtime | simulate | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| runtime | capabilities | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| runtime | query | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| recovery | suggest | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| recovery | execute | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| prometheus | query | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| prometheus | reload | ALLOW | DENY | DENY | ALLOW | DENY |

---

## Entry Points

| Entry Point | ActorType | Authentication |
|-------------|-----------|----------------|
| API (Customer Console) | EXTERNAL_PAID, EXTERNAL_TRIAL | Clerk JWT |
| API (Ops Console) | OPERATOR | Clerk JWT |
| API (Founder Console) | OPERATOR | Clerk JWT |
| Worker (Background) | SYSTEM | System Identity |
| Worker (Webhook) | INTERNAL_PRODUCT | API Key |
| CI Pipeline | SYSTEM | System Identity |
| Replay System | SYSTEM | System Identity |

---

## Test Matrix Summary

| Category | Count |
|----------|-------|
| Principal Types | 5 |
| M28 Native Resources | 15 |
| M7 Legacy Resources | 9 (20 action combinations) |
| Total Resource-Action Pairs | ~68 |
| Total Test Combinations | ~340 (68 × 5 principals) |

---

## Usage for T12 (Replay Harness)

```python
# Generate all test cases from this matrix
MATRIX_ROWS = [
    ("runs", "read", ["EXTERNAL_PAID", "EXTERNAL_TRIAL", "INTERNAL_PRODUCT", "OPERATOR", "SYSTEM"]),
    ("runs", "write", ["EXTERNAL_PAID", "EXTERNAL_TRIAL", "INTERNAL_PRODUCT", "OPERATOR", "SYSTEM"]),
    # ... etc
]

for resource, action, principals in MATRIX_ROWS:
    for principal_type in principals:
        actor = create_actor(principal_type)
        result = authorize_action(actor, resource, action)
        assert_expected(result, expected_from_matrix(resource, action, principal_type))
```

---

## Changelog

| Date | Action | Author |
|------|--------|--------|
| 2026-01-05 | Matrix created (T10) | Claude Opus 4.5 |
