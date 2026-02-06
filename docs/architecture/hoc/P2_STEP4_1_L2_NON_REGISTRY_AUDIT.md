# P2-Step4-1: L2 Non-Registry Usage Audit (Corrected)

**Date:** 2026-02-06
**Reference:** TODO_ITER3.2.md, PIN-520
**Status:** COMPLETE (Corrected Counts)
**Guard:** READ-ONLY. Update only with explicit user command.

---

## Executive Summary

**Scope:** `backend/app/hoc/api/cus/**` (APIRouter files only)

| Metric | Count | % |
|--------|-------|---|
| Total L2 Files | 69 | 100% |
| Using operation_registry | 32 | 46.4% |
| Not Using operation_registry | 37 | 53.6% |

---

## Files Using operation_registry

```
account/memory_pins.py
activity/activity.py
analytics/costsim.py
incidents/incidents.py
integrations/cus_telemetry.py
integrations/mcp_servers.py
ops/cost_ops.py
overview/overview.py
policies/analytics.py
policies/aos_accounts.py
policies/aos_api_key.py
policies/aos_cus_integrations.py
policies/connectors.py
policies/controls.py
policies/cus_enforcement.py
policies/datasources.py
policies/detection.py
policies/evidence.py
policies/governance.py
policies/guard.py
policies/logs.py
policies/notifications.py
policies/override.py
policies/policies.py
policies/policy.py
policies/policy_layer.py
policies/policy_limits_crud.py
policies/policy_rules_crud.py
policies/rate_limits.py
policies/simulate.py
policies/status_history.py
policies/workers.py
```

## Files Not Using operation_registry

```
agent/authz_status.py
agent/discovery.py
agent/onboarding.py
agent/platform.py
analytics/feedback.py
analytics/predictions.py
analytics/scenarios.py
api_keys/auth_helpers.py
api_keys/embedding.py
general/agents.py
general/debug_auth.py
general/health.py
general/legacy_routes.py
general/sdk.py
incidents/cost_guard.py
integrations/session_context.py
integrations/v1_proxy.py
logs/cost_intelligence.py
logs/guard_logs.py
logs/tenants.py
logs/traces.py
policies/M25_integrations.py
policies/alerts.py
policies/compliance.py
policies/customer_visibility.py
policies/guard_policies.py
policies/lifecycle.py
policies/monitors.py
policies/policy_proposals.py
policies/rbac_api.py
policies/replay.py
policies/retrieval.py
policies/runtime.py
policies/scheduler.py
policies/v1_killswitch.py
recovery/recovery.py
recovery/recovery_ingest.py
```

---

## Evidence Commands

```bash
# Count L2 APIRouter files (cus)
python3 - <<'PY'
from pathlib import Path
root = Path('backend/app/hoc/api/cus')
count = 0
for p in root.rglob('*.py'):
    try:
        text = p.read_text()
    except Exception:
        continue
    if 'APIRouter' in text:
        count += 1
print(count)
PY

# Count files using operation_registry
python3 - <<'PY'
from pathlib import Path
import re
root = Path('backend/app/hoc/api/cus')
rx = re.compile(r'\bget_operation_registry\b')
count = 0
for p in root.rglob('*.py'):
    try:
        text = p.read_text()
    except Exception:
        continue
    if 'APIRouter' in text and rx.search(text):
        count += 1
print(count)
PY

# List files without operation_registry
python3 - <<'PY'
from pathlib import Path
import re
root = Path('backend/app/hoc/api/cus')
rx = re.compile(r'\bget_operation_registry\b')
for p in sorted(root.rglob('*.py')):
    try:
        text = p.read_text()
    except Exception:
        continue
    if 'APIRouter' in text and not rx.search(text):
        print(p)
PY
```

---

## Notes
- This corrected audit does not classify *why* a file avoids the registry.
- Classification (stateless/utility/adapter/etc.) should be re-done from the corrected file list if needed.
