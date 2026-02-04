# PIN-523: PIN-523 Phase 2 BLOCKING TODO Wiring Complete

**Status:** ✅ COMPLETE
**Created:** 2026-02-04
**Category:** HOC Migration

---

## Summary

Wired 4 BLOCKING TODOs to HOC canonical implementations: governance_facade ConflictResolver (GAP-068), policy_mapper explicit allow check and Redis rate limiting (GAP-087), prevention_engine policy loading from PolicyDriver (GAP-001). Also completed Phase 0-1 invocation_safety migration and PolicyEngine caller rewiring from previous session.

---

## Details

### Phase 0-1 Completion (from previous session)

| Task | From | To | Status |
|------|------|-----|--------|
| invocation_safety.py | `app/auth/` | `app/hoc/cus/account/auth/L5_engines/` | MIGRATED |
| PolicyEngine callers (4) | `app.services.policies` | `app.hoc.cus.policies.L5_engines` | REWIRED |
| ledger.emit_signal() | N/A | Added optional `session` param | COMPLETE |

### Phase 2 BLOCKING TODO Wiring

| File | TODO | Wired To | GAP |
|------|------|----------|-----|
| `governance_facade.py` | ConflictResolver | `policy_conflict_resolver`, `PolicyDriver` | GAP-068 |
| `policy_mapper.py` | Explicit allow check | `PolicyDriver.get_safety_rules()` | GAP-087 |
| `policy_mapper.py` | Rate limiting | Redis sliding window | GAP-087 |
| `prevention_engine.py` | Load policies | `PolicyDriver.get_safety_rules()`, `get_risk_ceilings()` | GAP-001 |

### Key Implementation Notes

1. **governance_facade.py**: Sync facade wraps async PolicyDriver calls using `asyncio.run()` for standalone contexts
2. **policy_mapper.py explicit allow**: Checks safety rules for explicit allows, supports wildcard patterns (`mcp:server:*`)
3. **policy_mapper.py rate limiting**: Uses Redis sorted sets for sliding window, fail-open if Redis unavailable
4. **prevention_engine.py**: Falls back to hardcoded defaults if PolicyDriver load fails

### Files Modified

- `app/hoc/cus/_domain_map/V4_DOMAIN_WORKBOOK_CANONICAL_FINAL.md`
- `app/hoc/cus/policies/L5_engines/governance_facade.py`
- `app/hoc/cus/policies/L5_engines/policy_mapper.py`
- `app/hoc/cus/policies/L5_engines/prevention_engine.py`
- `app/hoc/cus/policies/L5_engines/policy_driver.py`
- `app/hoc/int/platform/policy/engines/policy_driver.py`
- `app/hoc/api/cus/policies/policy.py`
- `app/hoc/api/cus/policies/workers.py`
- `app/hoc/cus/account/auth/L5_engines/__init__.py`
- `app/hoc/cus/account/auth/L5_engines/invocation_safety.py` (new)
- `app/hoc/cus/hoc_spine/drivers/ledger.py`
- `cli/aos.py`
- `tests/auth/test_invocation_safety.py`

### Commit

```
fb56e682 feat(hoc): wire Phase 2 BLOCKING TODOs to HOC canonical implementations
```

---

## Related

- PIN-522: Auth Subdomain Migration Complete
- PIN-511: Legacy app/services/* Boundary
- GAP-001: Prevention hook integration
- GAP-068: Policy Conflict Resolution
- GAP-087: MCP Policy Gate
