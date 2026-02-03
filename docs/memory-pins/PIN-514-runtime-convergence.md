# PIN-514: Runtime Convergence — Eliminate Dual Runtime Copies

**Status:** ✅ COMPLETE
**Created:** 2026-02-03
**Category:** Architecture
**Predecessor:** Category D Fixes (Batch 1)

---

## Summary

Eliminated duplicate runtime copies. The policy runtime now has a single canonical location at `app/hoc/cus/policies/L5_engines/` per HOC Layer Topology V2.0.0.

---

## Finding

Two copies of the M20 policy runtime existed:
- `app/policy/runtime/` — outside HOC topology
- `app/hoc/cus/policies/L5_engines/` — proper L5 location (was orphaned)

Per PIN-484 (HOC Topology V2.0.0), L5 engines belong in `hoc/cus/{domain}/L5_engines/`.

---

## Action Taken

1. **Restored** canonical L5_engines files with proper L5 headers:
   - `app/hoc/cus/policies/L5_engines/intent.py`
   - `app/hoc/cus/policies/L5_engines/deterministic_engine.py`
   - `app/hoc/cus/policies/L5_engines/dag_executor.py`

2. **Updated** all imports from `app.policy.runtime` to `app.hoc.cus.policies.L5_engines`:
   - `app/hoc/int/integrations/engines/worker.py`
   - `app/workers/business_builder/worker.py`
   - `app/api/workers.py`
   - `app/hoc/api/cus/policies/workers.py`
   - `app/hoc/cus/hoc_spine/drivers/dag_executor.py`
   - `tests/test_m20_runtime.py`

3. **Deleted** `app/policy/runtime/` directory (non-canonical location)

4. **L5_schemas unchanged** — the protocol files (`intent_validation.py`, `policy_check.py`) are correctly placed in `app/hoc/cus/policies/L5_schemas/`.

---

## Files Changed

| Action | File |
|--------|------|
| CREATE | `app/hoc/cus/policies/L5_engines/intent.py` |
| CREATE | `app/hoc/cus/policies/L5_engines/deterministic_engine.py` |
| CREATE | `app/hoc/cus/policies/L5_engines/dag_executor.py` |
| UPDATE | `app/hoc/cus/policies/L5_engines/__init__.py` (exports) |
| DELETE | `app/policy/runtime/` (entire directory) |
| UPDATE | 6 files with import path changes |
| CREATE | `docs/memory-pins/PIN-514-runtime-convergence.md` |

---

## Canonical Runtime Location

```
app/hoc/cus/policies/L5_engines/
├── __init__.py              # Exports all runtime components
├── intent.py                # IntentEmitter, Intent, IntentPayload, IntentType
├── deterministic_engine.py  # DeterministicEngine, ExecutionContext, ExecutionResult
└── dag_executor.py          # DAGExecutor, StageResult, ExecutionTrace
```

**Import path:** `from app.hoc.cus.policies.L5_engines.intent import IntentEmitter`

---

## Verification

```bash
# Canonical path works
PYTHONPATH=. python3 -c "from app.hoc.cus.policies.L5_engines.intent import IntentEmitter; print('OK')"

# No remaining references to old path
grep -r "app.policy.runtime" app/ --include="*.py"  # Should return nothing

# All 24 M20 runtime tests pass
PYTHONPATH=. python3 -m pytest tests/test_m20_runtime.py -v
```

---

## Related PINs

- **PIN-515**: Production Wiring Contract (documents validator injection points)
- **PIN-513**: Topology Completion & Hygiene
- **PIN-484**: HOC Layer Topology V2.0.0 (ratified)
