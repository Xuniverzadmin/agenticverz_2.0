# M7 Pruning Decisions

**Date:** 2026-01-05
**Status:** IN PROGRESS
**Target:** < 10 M7 call sites before T8
**Reference:** docs/invariants/AUTHZ_AUTHORITY.md

---

## Summary

This document tracks pruning decisions for each M7 usage site identified in M7_USAGE_INVENTORY.md.

| Status | Count |
|--------|-------|
| MIGRATE | 4 |
| RECLASSIFY | 2 |
| DELETE | 2 |
| KEEP (temp) | 6 |
| **Total** | 14 |

---

## Decision Categories

| Decision | Meaning | Action |
|----------|---------|--------|
| **MIGRATE** | Replace with `authorize_action()` | Update code to use choke point |
| **RECLASSIFY** | Not actually M7, misclassified | Update inventory, no code change |
| **DELETE** | Legacy code, not used | Remove file/function |
| **KEEP** | Allowed M7 importer (temporary) | Document reason, plan removal |

---

## Production Code Decisions

### P0 - Critical (Must migrate first)

| File | Import | Decision | Reason | Assignee |
|------|--------|----------|--------|----------|
| `app/api/rbac_api.py` | `check_permission`, `get_rbac_engine` | **MIGRATE** | Direct M7 API exposure, replace with status endpoint | TBD |
| `app/main.py` | `init_rbac_engine`, `RBACMiddleware` | **KEEP** | Startup init, migrate after middleware replacement | - |

### P1 - High Priority

| File | Import | Decision | Reason | Assignee |
|------|--------|----------|--------|----------|
| `app/api/traces.py` | Inline `user.has_role()` | **MIGRATE** | 15+ inline checks → replace with `authorize_action()` | TBD |
| `app/api/policy.py` | `check_approver_permission` | **MIGRATE** | Approval authority → route through choke point | TBD |

### P2 - Medium Priority

| File | Import | Decision | Reason | Assignee |
|------|--------|----------|--------|----------|
| `app/auth/clerk_provider.py` | `get_max_approval_level` | **MIGRATE** | Role translation → use M28 role system | TBD |
| `app/auth/oidc_provider.py` | `map_external_roles_to_aos` | **MIGRATE** | Role translation → use M28 role system | TBD |
| `app/auth/rbac_integration.py` | Multiple | **KEEP** | Integration shim, delete after full migration | - |

### P3 - Low Priority

| File | Import | Decision | Reason | Assignee |
|------|--------|----------|--------|----------|
| `app/auth/__init__.py` | Re-exports | **RECLASSIFY** | Module facade, not M7 usage | - |
| `app/auth/rbac.py` | Module exports | **RECLASSIFY** | Helper types, not M7 engine usage | - |

---

## M7 Implementation Files

| File | Decision | Reason |
|------|----------|--------|
| `app/auth/rbac_engine.py` | **DELETE** | M7 implementation → delete after all usages migrated |
| `app/auth/rbac_middleware.py` | **DELETE** | M7 middleware → replace with M28 authorize_action |

---

## Test File Decisions

| File | Decision | Reason |
|------|----------|--------|
| `tests/auth/test_rbac_engine.py` | **KEEP** | Keep for regression during migration |
| `tests/auth/test_rbac_middleware.py` | **KEEP** | Keep for regression during migration |
| `tests/auth/test_rbac_integration.py` | **KEEP** | Keep for verifying M7↔M28 parity |
| `tests/auth/test_rbac_path_mapping.py` | **KEEP** | Keep for mapping verification |

---

## Migration Plan

### Phase 1: Read Path Migration (Phase A)
Target: Migrate all `read` action checks to `authorize_action()`

1. [ ] `app/api/traces.py` - Read operations
2. [ ] `app/api/policy.py` - Read policy checks

### Phase 2: Write Path Migration (Phase B)
Target: Migrate all `write` action checks to `authorize_action()`

1. [ ] `app/api/traces.py` - Write operations
2. [ ] `app/api/policy.py` - Approval checks
3. [ ] `app/auth/clerk_provider.py` - Role translation
4. [ ] `app/auth/oidc_provider.py` - Role translation

### Phase 3: API Cleanup (Phase B→C)
Target: Remove direct M7 API exposure

1. [ ] `app/api/rbac_api.py` - Replace with `/internal/authz/*` endpoints
2. [ ] `app/main.py` - Remove M7 initialization

### Phase 4: Deletion (Phase C)
Target: Delete M7 implementation

1. [ ] Delete `app/auth/rbac_engine.py`
2. [ ] Delete `app/auth/rbac_middleware.py`
3. [ ] Delete `app/auth/rbac_integration.py`
4. [ ] Update test files or delete if redundant

---

## Resource Coverage

### Resources Fully Covered by M28

These resources can use `authorize_action()` with `M28_DIRECT` source:

- `runs` - Execution traces
- `agents` - Agent management
- `skills` - Skill registry
- `traces` - Trace data
- `metrics` - Metrics emission
- `ops` - Operations
- `account` - Account management
- `team` - Team management
- `policies` - Policy management
- `replay` - Replay capability
- `predictions` - Prediction capability

### Resources Requiring Mapping (M7 Legacy)

These resources use `authorize_action()` with `M28_VIA_MAPPING` source:

- `memory_pin` - Memory PIN operations
- `costsim` - Cost simulation
- `agent` (heartbeat, register) - Agent lifecycle
- `runtime` - Runtime operations
- `recovery` - Recovery suggestions

### Resources to Add to M28 Natively

After mapping proves stable, migrate to M28 native:

1. `memory_pins` (from `memory_pin`)
2. `costsim` (keep name)
3. `runtime` (keep name)
4. `recovery` (keep name)

---

## Validation Checklist

Before moving to Phase C (T8):

- [ ] All production M7 call sites migrated or justified
- [ ] CI guard passes (`scripts/ci/m7_import_guard.py`)
- [ ] Metrics show < 1% M7 fallback rate
- [ ] All mapped resources tested in Phase B
- [ ] Strict mode tested (`AUTHZ_STRICT_MODE=true`)
- [ ] Integration tests pass without M7

---

## Changelog

| Date | Action | Author |
|------|--------|--------|
| 2026-01-05 | Initial pruning decisions | Claude Opus 4.5 |
