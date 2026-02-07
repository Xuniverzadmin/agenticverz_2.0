# P2-Step4-1: L2 Non-Registry Justified Exceptions

**Created:** 2026-02-06  
**Last verified:** 2026-02-07
**Scope:** `backend/app/hoc/api/cus/**` (APIRouter token files only)
**Reference:** `docs/architecture/hoc/P2_STEP4_1_L2_CLASSIFICATION_SUPPLEMENT.md` (live)
**Guard:** Update only with explicit user command.

---

## Summary

This document justifies the **current** non-registry L2 set, where:
- **Registry dispatch** means the module contains `registry.execute(...)`.
- **Non-registry** means the module does **not** contain `registry.execute(...)`.

| Category | Count | Justification |
|----------|-------|---------------|
| Utility (no router) | 1 | `APIRouter(` appears only in docstring/example; no router defined |
| Console adapter (PIN-281) | 2 | External boundary pattern |
| Adapters boundary | 1 | Delegates into `app.adapters.*` boundary module |
| hoc_spine services facade | 7 | Delegates into L4 `hoc_spine.services.*` (no registry dispatch) |
| Session helpers (no registry) | 0 | Uses L4 session helpers without registry dispatch |
| Stateless/local | 3 | No DB access; local introspection/translation only |

**Current totals (live scan):**
- Total L2 APIRouter token files: 57
- Registry dispatch: 43
- Non-registry: 14

**Result:** All 14 non-registry files are justified exceptions (no backlog).

---

## Category 1: Utility (No Router) — 1

These modules appear in the APIRouter token scan but do not define an actual router.

- `api_keys/auth_helpers.py`

**Justification:** This file contains an `APIRouter(...)` example in a docstring but does not define endpoints.

---

## Category 2: Console Adapter Pattern (PIN-281) — 2

PIN-281 pattern: thin L2 boundary → L3 adapter → L4 bridge.

- `logs/guard_logs.py` (auth: `verify_console_token`; adapter: `customer_logs_adapter`)
- `policies/guard_policies.py` (auth: `verify_console_token`; adapter: `customer_policies_adapter`)

**Justification:** External console boundary requires custom auth translation.

---

## Category 3: Adapters Boundary — 1

- `policies/runtime.py`

**Justification:** This module delegates to the `app.adapters.*` boundary layer (explicit adapter boundary; no registry dispatch).

---

## Category 4: hoc_spine Services Facade (No Registry) — 7

These L2 files import `app.hoc.cus.hoc_spine.services.*` and delegate to L4 services/facades without using registry dispatch:

- `logs/cost_intelligence.py`
- `policies/alerts.py`
- `policies/compliance.py`
- `policies/lifecycle.py`
- `policies/monitors.py`
- `policies/retrieval.py`
- `policies/scheduler.py`

**Justification:** These remain L2 → L4 (hoc_spine) calls, but bypass registry dispatch for service/facade style operations.

---

## Category 5: Stateless/Local (No Registry) — 3

No registry dispatch; no hoc_spine services; no adapter boundary; no DB access.

- `analytics/scenarios.py`
- `api_keys/embedding.py`
- `integrations/session_context.py`

**Justification:** Request translation, stubs, or local computation only.

---

## Evidence Commands (Reproducible)

```bash
# List all APIRouter token files and split by registry dispatch
python3 - <<'PY'
import re
from pathlib import Path
root = Path("backend/app/hoc/api/cus")
apirouter = re.compile(r"\bAPIRouter\s*\(")
reg = re.compile(r"\bregistry\.execute\s*\(")
all_=[]; yes=[]; no=[]
for p in sorted(root.rglob("*.py")):
    t = p.read_text(errors="ignore")
    if not apirouter.search(t):
        continue
    rel = str(p.relative_to(root))
    all_.append(rel)
    (yes if reg.search(t) else no).append(rel)
print("total", len(all_))
print("registry_dispatch", len(yes))
print("non_registry", len(no))
print("\nNON_REGISTRY:")
print("\n".join(no))
PY

# Categorize the NON_REGISTRY set (heuristic/AST-backed)
python3 - <<'PY'
from pathlib import Path
import ast
import re

root = Path("backend/app/hoc/api/cus")
apirouter = re.compile(r"\bAPIRouter\s*\(")
reg = re.compile(r"\bregistry\.execute\s*\(")

RE_ADAPTERS = re.compile(r"\bapp\.adapters\b")
RE_SERVICES = re.compile(r"\bapp\.hoc\.cus\.hoc_spine\.services\b")
RE_SESSION = re.compile(r"\bget_(?:sync_)?session_dep\b|\bget_async_session_context\b|\bsql_text\b")
CONSOLE = {"logs/guard_logs.py","policies/guard_policies.py"}

cats = {
  "utility_no_router": [],
  "console_adapter_pin281": [],
  "adapters_boundary": [],
  "spine_services_facade": [],
  "session_helpers_no_registry": [],
  "stateless_or_local": [],
}

for p in sorted(root.rglob("*.py")):
    t = p.read_text(errors="ignore")
    if not apirouter.search(t) or reg.search(t):
        continue
    rel = str(p.relative_to(root))

    try:
        tree = ast.parse(t)
        has_call = any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "APIRouter"
            for n in ast.walk(tree)
        )
    except SyntaxError:
        has_call = True

    if not has_call:
        cats["utility_no_router"].append(rel); continue
    if rel in CONSOLE or "PIN-281" in t:
        cats["console_adapter_pin281"].append(rel); continue
    if RE_ADAPTERS.search(t):
        cats["adapters_boundary"].append(rel); continue
    if RE_SERVICES.search(t):
        cats["spine_services_facade"].append(rel); continue
    if RE_SESSION.search(t):
        cats["session_helpers_no_registry"].append(rel); continue
    cats["stateless_or_local"].append(rel)

for k in cats:
    print(k, len(cats[k]))
    for rel in cats[k]:
        print(" ", rel)
PY
```

---

## Final Metrics

| Metric | Count |
|--------|-------|
| Total L2 APIRouter files | 57 |
| Registry dispatch (`registry.execute`) | 43 |
| Non-registry (`no registry.execute`) | 14 |
| — Utility (no router) | 1 |
| — Console adapter (PIN-281) | 2 |
| — Adapters boundary | 1 |
| — hoc_spine services facade | 7 |
| — Session helpers (no registry) | 0 |
| — Stateless/local | 3 |
| **Needs conversion** | **0** |

**Compliance:** 100% (all files compliant or justified)

---

## Sign-Off

**Documented by:** Claude (Iter3.2)
**Date:** 2026-02-06
**Approved patterns:**
1. `registry.execute(...)` - Registry dispatch pattern
2. hoc_spine services facade - L2 delegates into L4 `hoc_spine.services.*`
3. Console adapter - PIN-281 boundary pattern
4. Adapters boundary - explicit adapter delegation
5. Stateless/local - no DB access

---

*This document supplements `docs/architecture/hoc/P2_STEP4_1_L2_CLASSIFICATION_SUPPLEMENT.md` and does not modify the READ-ONLY audit snapshot.*
