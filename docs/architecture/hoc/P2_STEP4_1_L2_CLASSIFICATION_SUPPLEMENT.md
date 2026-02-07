# P2-Step4-1: L2 Non-Registry Classification Supplement (Live)

**Created:** 2026-02-06  
**Last verified:** 2026-02-07
**Scope:** `backend/app/hoc/api/cus/**`
**Reference:** `docs/architecture/hoc/P2_STEP4_1_L2_NON_REGISTRY_AUDIT.md` (READ-ONLY snapshot)
**Guard:** Update only with explicit user command.

This document classifies L2 modules (router files) by whether they dispatch through `hoc_spine` `operation_registry` (via `registry.execute(...)`) or not, and provides an evidence-backed file list for each category.

---

## Reality Drift vs The READ-ONLY Snapshot

`docs/architecture/hoc/P2_STEP4_1_L2_NON_REGISTRY_AUDIT.md` is guarded as READ-ONLY and reflects an earlier snapshot.
The codebase has changed since that snapshot.

| Metric | READ-ONLY snapshot | Current scan (this document) |
|--------|---------------------|------------------------------|
| Total L2 APIRouter string-scan files | 69 | 57 |
| Using `operation_registry` | 32 | 43 |
| Not using `operation_registry` | 37 | 14 |

**Audience cleansing note (2026-02-07):** the CUS surface was cleansed to contain **only** the canonical 10 customer domains.
Non-domain surfaces (`general/`, `agent/`, `recovery/`, `ops/`) were re-homed to `int/` or `fdr/`, shrinking the CUS scan scope.

<details>
<summary>Pre-audience-cleansing drift detail (historical)</summary>

These files were in the snapshot’s “not using operation_registry” list, but later gained `registry.execute(...)` dispatch (before the audience re-home):

- `agent/discovery.py`
- `agent/platform.py`
- `analytics/feedback.py`
- `analytics/predictions.py`
- `general/agents.py`
- `general/health.py`
- `incidents/cost_guard.py`
- `integrations/v1_proxy.py`
- `logs/tenants.py`
- `logs/traces.py`
- `policies/M25_integrations.py`
- `policies/customer_visibility.py`
- `policies/policy_proposals.py`
- `policies/rbac_api.py`
- `policies/replay.py`
- `policies/v1_killswitch.py`
- `recovery/recovery.py`
- `recovery/recovery_ingest.py`

</details>

---

## Classification Summary (Current Code)

**Input set definition:** files under `backend/app/hoc/api/cus/**` that contain the token `APIRouter(` (string-scan).

| Category | Count | Criteria (machine-checkable) |
|----------|-------|-----------------------------|
| Registry dispatch | 43 | Module contains `registry.execute(` |
| Non-registry: Utility (no router) | 1 | `APIRouter(` appears only in docstring/example; no `APIRouter(...)` call and no `@router.<verb>` decorators (AST) |
| Non-registry: Console adapter (PIN-281) | 2 | Module is a guarded console adapter surface (currently: `guard_logs.py`, `guard_policies.py`) |
| Non-registry: Adapters boundary | 1 | Imports `app.adapters.*` and delegates into adapter (no registry) |
| Non-registry: hoc_spine services facade | 7 | Imports `app.hoc.cus.hoc_spine.services.*` (no registry) |
| Non-registry: hoc_spine bridge pattern | 0 | Uses `get_*_bridge` or imports `hoc_spine...bridges...` (no registry) |
| Non-registry: Session helpers (no registry) | 0 | Uses `get_sync_session_dep` / `get_async_session_context` / `sql_text` without registry dispatch |
| Non-registry: Stateless/local | 3 | None of the above markers |

**Total (string-scan):** 57

---

## Re-Verification (2026-02-07)

Re-ran the reproducible scan scripts in this document against the live tree.

| Check | Result |
|-------|--------|
| APIRouter token files | 57 |
| Registry dispatch (`registry.execute`) | 43 |
| Non-registry | 14 |
| Category partition of non-registry set | PASS (0 missing, 0 extra, 0 duplicates) |

## Registry Dispatch (43)

These files currently contain `registry.execute(...)`.

<details>
<summary>Registry dispatch file list (click to expand)</summary>

- `account/memory_pins.py`
- `activity/activity.py`
- `analytics/costsim.py`
- `analytics/feedback.py`
- `analytics/predictions.py`
- `controls/controls.py`
- `incidents/cost_guard.py`
- `incidents/incidents.py`
- `integrations/cus_telemetry.py`
- `integrations/mcp_servers.py`
- `integrations/v1_proxy.py`
- `logs/tenants.py`
- `logs/traces.py`
- `overview/overview.py`
- `policies/M25_integrations.py`
- `policies/analytics.py`
- `policies/aos_accounts.py`
- `policies/aos_api_key.py`
- `policies/aos_cus_integrations.py`
- `policies/connectors.py`
- `policies/cus_enforcement.py`
- `policies/customer_visibility.py`
- `policies/datasources.py`
- `policies/detection.py`
- `policies/evidence.py`
- `policies/governance.py`
- `policies/guard.py`
- `policies/logs.py`
- `policies/notifications.py`
- `policies/override.py`
- `policies/policies.py`
- `policies/policy.py`
- `policies/policy_layer.py`
- `policies/policy_limits_crud.py`
- `policies/policy_proposals.py`
- `policies/policy_rules_crud.py`
- `policies/rate_limits.py`
- `policies/rbac_api.py`
- `policies/replay.py`
- `policies/simulate.py`
- `policies/status_history.py`
- `policies/v1_killswitch.py`
- `policies/workers.py`

</details>

---

## Non-Registry (14)

These files do **not** contain `registry.execute(...)` today.

### Utility (No Router) — 1

- `api_keys/auth_helpers.py`

**Why it appears in the 57-file set:** it contains an `APIRouter(...)` example inside a module docstring, but it does not define a router.

### Console Adapter (PIN-281) — 2

- `logs/guard_logs.py` (console-scoped adapter surface; `app.adapters.customer_logs_adapter`; PIN-281)
- `policies/guard_policies.py` (console-scoped adapter surface; `app.adapters.customer_policies_adapter`; PIN-281)

### Adapters Boundary — 1

- `policies/runtime.py` (runtime adapter; `app.adapters.runtime_adapter`; PIN-258)

### hoc_spine Services Facade (No Registry) — 7

These import `app.hoc.cus.hoc_spine.services.*` and delegate to facade/services modules instead of registry dispatch.

- `logs/cost_intelligence.py`
- `policies/alerts.py`
- `policies/compliance.py`
- `policies/lifecycle.py`
- `policies/monitors.py`
- `policies/retrieval.py`
- `policies/scheduler.py`

### hoc_spine Bridge Pattern (No Registry) — 0

No files match this category in the current scan.

### Session Helpers (No Registry) — 0

### Stateless/Local (No Registry) — 3

No registry dispatch, no hoc_spine services, no hoc_spine bridges, no session helper pattern.

- `analytics/scenarios.py`
- `api_keys/embedding.py`
- `integrations/session_context.py`

---

## Evidence Commands (Reproducible)

```bash
# Current: list all 57 APIRouter string-scan files and split into
# (a) registry dispatch (has registry.execute) vs (b) non-registry
python3 - <<'PY'
from __future__ import annotations
from pathlib import Path
import re

root = Path('backend/app/hoc/api/cus')
apirouter_pat = re.compile(r'\bAPIRouter\s*\(')
registry_exec_pat = re.compile(r'\bregistry\.execute\s*\(')

apirouter_files = []
registry = []
non = []

for p in sorted(root.rglob('*.py')):
    if not p.is_file():
        continue
    txt = p.read_text(errors='ignore')
    if not apirouter_pat.search(txt):
        continue
    rel = str(p.relative_to(root))
    apirouter_files.append(rel)
    if registry_exec_pat.search(txt):
        registry.append(rel)
    else:
        non.append(rel)

print('total', len(apirouter_files))
print('registry_dispatch', len(registry))
print('non_registry', len(non))
print('\nNON_REGISTRY:')
print('\n'.join(non))
PY

# Drift vs READ-ONLY audit snapshot
python3 - <<'PY'
from __future__ import annotations
from pathlib import Path
import re

root = Path('backend/app/hoc/api/cus')
audit = Path('docs/architecture/hoc/P2_STEP4_1_L2_NON_REGISTRY_AUDIT.md').read_text(errors='ignore')

m_using = re.search(r"## Files Using operation_registry\s*\n\n```\n(.*?)\n```", audit, re.S)
m_not = re.search(r"## Files Not Using operation_registry\s*\n\n```\n(.*?)\n```", audit, re.S)

audit_not = set(ln.strip() for ln in (m_not.group(1).splitlines() if m_not else []) if ln.strip())

registry_exec_pat = re.compile(r'\bregistry\.execute\s*\(')

current_registry = set()
for p in root.rglob('*.py'):
    txt = p.read_text(errors='ignore')
    if registry_exec_pat.search(txt):
        current_registry.add(str(p.relative_to(root)))

moved = sorted(audit_not & current_registry)
print('audit_non_registry_now_registry_execute', len(moved))
print('\n'.join(moved))
PY

# Category breakdown for the CURRENT 22-file non-registry set (AST-backed)
python3 - <<'PY'
from __future__ import annotations
from pathlib import Path
import ast
import re

root = Path('backend/app/hoc/api/cus')

apirouter_pat = re.compile(r'\bAPIRouter\s*\(')
registry_exec_pat = re.compile(r'\bregistry\.execute\s*\(')

HTTP_DECORATORS = {'get', 'post', 'put', 'patch', 'delete', 'options', 'head'}

def is_router_module(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'APIRouter':
            return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in node.decorator_list:
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute):
                    if isinstance(d.func.value, ast.Name) and d.func.value.id == 'router' and d.func.attr in HTTP_DECORATORS:
                        return True
    return False

def non_registry_files() -> list[Path]:
    out: list[Path] = []
    for p in sorted(root.rglob('*.py')):
        if not p.is_file():
            continue
        txt = p.read_text(errors='ignore')
        if not apirouter_pat.search(txt):
            continue
        if registry_exec_pat.search(txt):
            continue
        out.append(p)
    return out

def classify(p: Path) -> str:
    txt = p.read_text(errors='ignore')
    tree = ast.parse(txt, filename=str(p))

    if not is_router_module(tree):
        return 'utility_no_router'

    if p.name in {'guard_logs.py', 'guard_policies.py'}:
        return 'console_adapter_pin281'

    if re.search(r'\bapp\.adapters\.', txt):
        return 'adapters_boundary'

    if re.search(r'app\.hoc\.cus\.hoc_spine\.services\.', txt):
        return 'spine_services_facade'

    if re.search(r'get_\w+_bridge|hoc_spine\.orchestrator\.coordinators\.bridges', txt):
        return 'spine_bridge_pattern'

    if re.search(r'\b(get_sync_session_dep|get_async_session_context|sql_text)\b', txt):
        return 'session_helpers_no_registry'

    return 'stateless_or_local'

cats: dict[str, list[str]] = {}
for p in non_registry_files():
    k = classify(p)
    cats.setdefault(k, []).append(str(p.relative_to(root)))

for k in sorted(cats):
    print(k, len(cats[k]))
    for rel in cats[k]:
        print(' ', rel)
PY
```
