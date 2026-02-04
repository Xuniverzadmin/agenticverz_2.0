# PIN-524: PIN-524 Phase 3 Legacy Import Deprecation Complete

**Status:** ✅ COMPLETE
**Created:** 2026-02-04
**Category:** HOC Migration

---

## Summary

Rewired 6 HOC files to use canonical HOC imports instead of legacy app.policy.* runtime modules. Classified app.policy.compiler/ir/ast/models/optimizer as shared infrastructure (acceptable). Runtime modules (prevention_engine, failure_mode_handler, binding_moment_enforcer, conflict_resolver, validators) must use HOC paths. Added get_prevention_engine() singleton to HOC prevention_engine.py.

---

## Details

### Import Classification

**Shared Infrastructure (Acceptable - like L7):**
- `app.policy.compiler.*` - Policy DSL compiler
- `app.policy.ir.*` - Intermediate representation
- `app.policy.ast.*` - Abstract syntax tree
- `app.policy.models` - Policy data models
- `app.policy.optimizer.*` - Policy optimizer

**Runtime Modules (Must Use HOC):**
- `app.policy.prevention_engine` → `app.hoc.cus.policies.L5_engines.prevention_engine`
- `app.policy.failure_mode_handler` → `app.hoc.cus.policies.L5_engines.failure_mode_handler`
- `app.policy.binding_moment_enforcer` → `app.hoc.cus.policies.L5_engines.binding_moment_enforcer`
- `app.policy.conflict_resolver` → `app.hoc.cus.policies.L5_engines.policy_conflict_resolver`
- `app.policy.validators.*` → `app.hoc.cus.policies.L5_engines.*`

### Files Modified

| File | Change |
|------|--------|
| `policies/L5_engines/prevention_engine.py` | Rewired 3 imports + added `get_prevention_engine()` singleton |
| `policies/L5_engines/prevention_hook.py` | Rewired `content_accuracy` import |
| `api/cus/policies/guard.py` | Rewired `evaluate_response` import |
| `int/general/drivers/step_enforcement.py` | Rewired `get_prevention_engine` import |
| `_domain_map/V4_DOMAIN_WORKBOOK_CANONICAL_FINAL.md` | Documented Phase 3 results |

### Commit

```
a92d8f2e refactor(hoc): Phase 3 - rewire legacy runtime imports to HOC canonical paths
```

---

## Related

- PIN-523: Phase 2 BLOCKING TODO Wiring Complete
- PIN-522: Auth Subdomain Migration Complete
- PIN-511: Legacy app/services/* Boundary
