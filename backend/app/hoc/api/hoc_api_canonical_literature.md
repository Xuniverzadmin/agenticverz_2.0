# HOC API Canonical Literature

**Version:** 1.0.0
**Created:** 2026-02-04
**Reference:** PIN-526, PLAN-HOC-API-WIRING.md

---

## Executive Summary

This document captures the canonical structure of the HOC (Hierarchical Operations Console) API layer following the successful migration from legacy `app/api/*` to `app/hoc/api/*`.

**Reality update (2026-02-07):** The legacy URL prefix `/api/v1/*` is now considered legacy and is served only via `410 Gone` handlers in `app/hoc/api/int/general/legacy_routes.py`. Canonical HOC routes no longer use `/api/v1`.

### Reality Metrics (2026-02-06, Evidence-Backed)

| Metric | Value |
|--------|-------|
| Total FastAPI routes (app.main) | 684 |
| Total HOC routes (app.hoc.api.*) | 661 |
| `/api/v1/*` routes | 4 (all legacy `410 Gone`) |
| `/health` routes | 1 (owned by `app.hoc.api.int.general.health`) |

---

## HOC API Layer Structure

```
app/hoc/api/
├── facades/                  # L2.1 surface map (router bundles by domain)
│   ├── cus/                  # Canonical 10 customer domains (non-optional)
│   ├── fdr/                  # Founder surfaces (bundled)
│   └── int/                  # Internal/system surfaces (health/legacy/etc.)
├── cus/                      # Customer-facing APIs (CUSTOMER audience)
│   ├── account/              # Account management
│   │   └── memory_pins.py    # Memory pin management
│   ├── activity/             # Activity domain
│   │   └── activity.py       # Activity unified facade
│   ├── analytics/            # Analytics domain
│   │   ├── costsim.py        # Cost simulation
│   │   ├── feedback.py       # Pattern feedback
│   │   ├── predictions.py    # Prediction events
│   │   └── scenarios.py      # Scenario simulation
│   ├── api_keys/             # API key management
│   │   ├── auth_helpers.py   # Auth dependencies (not router)
│   │   └── embedding.py      # Embedding quota
│   ├── controls/             # Controls domain
│   │   └── controls.py       # Controls facade
│   ├── incidents/            # Incident domain
│   │   ├── cost_guard.py     # Cost visibility
│   │   └── incidents.py      # Incidents facade
│   ├── integrations/         # Integration domain
│   │   ├── cus_telemetry.py  # Telemetry ingestion
│   │   ├── mcp_servers.py    # MCP server management
│   │   ├── protection_dependencies.py  # Dependencies (not router)
│   │   ├── session_context.py  # Session context
│   │   └── v1_proxy.py       # OpenAI-compatible proxy
│   ├── logs/                 # Logs domain
│   │   ├── cost_intelligence.py  # Cost intelligence
│   │   ├── guard_logs.py     # Customer logs
│   │   ├── tenants.py        # Tenant management
│   │   └── traces.py         # Trace viewing
│   ├── overview/             # Overview domain
│   │   └── overview.py       # Overview facade
│   ├── policies/             # Policy domain (largest)
│   │   ├── M25_integrations.py  # M25 integration loop
│   │   ├── alerts.py         # Alert management
│   │   ├── analytics.py      # Analytics facade
│   │   ├── aos_accounts.py   # AOS accounts
│   │   ├── aos_api_key.py    # AOS API keys
│   │   ├── aos_cus_integrations.py  # Customer integrations
│   │   ├── billing_dependencies.py  # Dependencies (not router)
│   │   ├── compliance.py     # Compliance management
│   │   ├── connectors.py     # Connector management (NEW)
│   │   ├── cus_enforcement.py  # Enforcement checks
│   │   ├── customer_visibility.py  # Customer visibility
│   │   ├── datasources.py    # Datasource management
│   │   ├── detection.py      # Detection management
│   │   ├── evidence.py       # Evidence management
│   │   ├── governance.py     # Governance endpoints (NEW)
│   │   ├── guard.py          # Guard console
│   │   ├── guard_policies.py # Policy constraints
│   │   ├── lifecycle.py      # Lifecycle management
│   │   ├── logs.py           # Logs facade
│   │   ├── monitors.py       # Monitor management
│   │   ├── notifications.py  # Notification management
│   │   ├── override.py       # Limit overrides
│   │   ├── policies.py       # Policies facade
│   │   ├── policy.py         # Policy CRUD
│   │   ├── policy_layer.py   # Policy layer
│   │   ├── policy_limits_crud.py  # Limits CRUD
│   │   ├── policy_proposals.py  # Policy proposals
│   │   ├── policy_rules_crud.py  # Rules CRUD
│   │   ├── rate_limits.py    # Rate limits
│   │   ├── rbac_api.py       # RBAC API
│   │   ├── replay.py         # Replay UX
│   │   ├── retrieval.py      # Retrieval API
│   │   ├── runtime.py        # Runtime API
│   │   ├── scheduler.py      # Scheduler API
│   │   ├── simulate.py       # Limit simulation
│   │   ├── status_history.py # Status history
│   │   ├── v1_killswitch.py  # KillSwitch MVP
│   │   └── workers.py        # Worker management
├── fdr/                      # Founder-facing APIs (FOUNDER audience)
│   ├── account/              # Founder account
│   │   ├── founder_explorer.py  # Cross-tenant explorer
│   │   └── founder_lifecycle.py  # Lifecycle management (NEW)
│   ├── agent/                # Founder agent
│   │   └── founder_contract_review.py  # Contract review
│   ├── incidents/            # Founder incidents
│   │   ├── founder_onboarding.py  # Onboarding recovery
│   │   └── ops.py            # Ops console
│   ├── logs/                 # Founder logs
│   │   ├── founder_review.py  # Evidence review
│   │   └── founder_timeline.py  # Decision timeline
│   └── ops/                  # Founder ops
│       ├── cost_ops.py         # Cost operations (founder-only)
│       ├── founder_actions.py  # Freeze/throttle actions
│       └── retrieval_admin.py  # Retrieval plane + evidence admin (founder-only)
└── int/                      # Internal APIs (INTERNAL audience)
    ├── agent/                # Internal agent surfaces
    │   ├── agents.py         # Multi-agent jobs
    │   ├── authz_status.py   # Authorization status
    │   ├── discovery.py      # Discovery ledger
    │   ├── onboarding.py     # Customer onboarding
    │   └── platform.py       # Platform health
    ├── general/              # System-wide internal surfaces
    │   ├── debug_auth.py     # Auth debugging
    │   ├── founder_auth.py   # Founder auth dependencies
    │   ├── health.py         # Health check (single owner)
    │   ├── legacy_routes.py  # 410 Gone handlers (only /api/v1 owner)
    │   └── sdk.py            # SDK endpoints
    ├── recovery/             # Recovery internal surfaces
    │   ├── recovery.py
    │   └── recovery_ingest.py
    ├── logs/                 # Internal logs (middleware re-exports)
    │   └── __init__.py
    └── policies/             # Internal policy gates
        └── billing_gate.py
```

---

## Domain Classification

### Customer (CUS) Domains

| Domain | Path | Purpose |
|--------|------|---------|
| account | `/accounts/*`, `/memory/*`, `/tenant/*` | Account management, memory pins, tenant tools |
| activity | `/activity/*` | Activity tracking |
| analytics | `/analytics/*`, `/cost/*`, `/feedback/*`, `/predictions/*` | Cost simulation, predictions, feedback |
| api_keys | `/api-keys/*`, `/embedding/*` | API key management, embedding |
| controls | `/controls/*` | Control configuration and control state |
| incidents | `/incidents/*`, `/guard/costs/*` | Incident management |
| integrations | `/integrations/*`, `/v1/*` | LLM integrations, proxy |
| logs | `/logs/*`, `/traces/*`, `/guard/logs/*` | Log viewing, traces |
| overview | `/overview/*` | Dashboard overview |
| policies | `/policies/*`, `/policy/*`, `/policy-layer/*`, `/policy-proposals/*`, `/runtime/*`, `/rbac/*`, `/workers/*`, `/guard/*`, `/v1/killswitch/*` | Policy management (largest) |

### Internal (INT) Surfaces

INT is the system/internal audience. These routes may exist at public paths (e.g., `/health`) but are owned by the internal surface.

| Surface | Path | Notes |
|---------|------|------|
| general | `/health`, `/sdk/*`, `/debug/*`, legacy 410 | System utilities and legacy routing |
| agent | `/discovery/*`, internal agent surfaces | System/ops agent surfaces |
| recovery | `/recovery/*` | Recovery system surfaces |

### Founder (FDR) Domains

| Domain | Path | Purpose |
|--------|------|---------|
| account | `/explorer/*`, `/fdr/lifecycle/*` | Cross-tenant explorer, lifecycle |
| agent | `/fdr/contracts/*` | Contract review |
| incidents | `/fdr/onboarding/*`, `/ops/*` | Onboarding recovery, ops console |
| logs | `/fdr/review/*`, `/fdr/timeline/*` | Evidence review, timeline |
| ops | `/ops/actions/*` | Founder actions (freeze, throttle) |

---

## Router Import Mapping

The following table shows the complete mapping from legacy imports to HOC imports:

**Phase 5 note:** entrypoints should not import routers directly; they should import `app.hoc.app:include_hoc` (L2.1 wiring) and let L2.1 facades define the surface.

| Legacy Import | HOC Import |
|---------------|------------|
| `.api.aos_accounts` | `.hoc.api.cus.policies.aos_accounts` |
| `.api.activity` | `.hoc.api.cus.activity.activity` |
| `.api.agents` | `.hoc.api.int.agent.agents` |
| `.api.alerts` | `.hoc.api.cus.policies.alerts` |
| `.api.analytics` | `.hoc.api.cus.policies.analytics` |
| `.api.authz_status` | `.hoc.api.int.agent.authz_status` |
| `.api.compliance` | `.hoc.api.cus.policies.compliance` |
| `.api.cost_guard` | `.hoc.api.cus.incidents.cost_guard` |
| `.api.cost_intelligence` | `.hoc.api.cus.logs.cost_intelligence` |
| `.api.cost_ops` | `.hoc.api.fdr.ops.cost_ops` |
| `.api.costsim` | `.hoc.api.cus.analytics.costsim` |
| `.api.discovery` | `.hoc.api.int.agent.discovery` |
| `.api.embedding` | `.hoc.api.cus.api_keys.embedding` |
| `.api.feedback` | `.hoc.api.cus.analytics.feedback` |
| `.api.founder_actions` | `.hoc.api.fdr.ops.founder_actions` |
| `.api.founder_contract_review` | `.hoc.api.fdr.agent.founder_contract_review` |
| `.api.founder_explorer` | `.hoc.api.fdr.account.founder_explorer` |
| `.api.founder_onboarding` | `.hoc.api.fdr.incidents.founder_onboarding` |
| `.api.founder_review` | `.hoc.api.fdr.logs.founder_review` |
| `.api.founder_timeline` | `.hoc.api.fdr.logs.founder_timeline` |
| `.api.guard` | `.hoc.api.cus.policies.guard` |
| `.api.guard_logs` | `.hoc.api.cus.logs.guard_logs` |
| `.api.guard_policies` | `.hoc.api.cus.policies.guard_policies` |
| `.api.health` | `.hoc.api.int.general.health` |
| `.api.incidents` | `.hoc.api.cus.incidents.incidents` |
| `.api.legacy_routes` | `.hoc.api.int.general.legacy_routes` |
| `.api.logs` | `.hoc.api.cus.policies.logs` |
| `.api.memory_pins` | `.hoc.api.cus.account.memory_pins` |
| `.api.onboarding` | `.hoc.api.int.agent.onboarding` |
| `.api.ops` | `.hoc.api.fdr.incidents.ops` |
| `.api.overview` | `.hoc.api.cus.overview.overview` |
| `.api.platform` | `.hoc.api.int.agent.platform` |
| `.api.policies` | `.hoc.api.cus.policies.policies` |
| `.api.policy` | `.hoc.api.cus.policies.policy` |
| `.api.predictions` | `.hoc.api.cus.analytics.predictions` |
| `.api.rbac_api` | `.hoc.api.cus.policies.rbac_api` |
| `.api.recovery` | `.hoc.api.int.recovery.recovery` |
| `.api.replay` | `.hoc.api.cus.policies.replay` |
| `.api.runtime` | `.hoc.api.cus.policies.runtime` |
| `.api.scenarios` | `.hoc.api.cus.analytics.scenarios` |
| `.api.sdk` | `.hoc.api.int.general.sdk` |
| `.api.session_context` | `.hoc.api.cus.integrations.session_context` |
| `.api.tenants` | `.hoc.api.cus.logs.tenants` |
| `.api.traces` | `.hoc.api.cus.logs.traces` |
| `.api.v1_killswitch` | `.hoc.api.cus.policies.v1_killswitch` |
| `.api.v1_proxy` | `.hoc.api.cus.integrations.v1_proxy` |

---

## Non-Router Files

The following files in HOC API directories are NOT routers (they are dependency modules):

| File | Purpose |
|------|---------|
| `cus/api_keys/auth_helpers.py` | FastAPI auth dependencies |
| `cus/integrations/protection_dependencies.py` | Protection gate dependencies |

Additional non-router dependency modules exist under `int/` and `infrastructure/` for middleware/dependency wiring.
| `cus/policies/billing_dependencies.py` | Billing gate dependencies |

These files should NOT be included in router registration.

---

## Special Cases

### 1. Predictions Router (NOT Migrated)

```python
from .predictions.api import router as c2_predictions_router
```

This router is from `app/predictions/api.py`, NOT from legacy `app/api/`. It remains unchanged.

### 2. MCP Servers Router (Already HOC)

```python
from .hoc.api.cus.integrations.mcp_servers import router as mcp_servers_router
```

This router was already in HOC before migration (PIN-516).

---

## Migration Fixes Applied

During migration, the following fixes were required to address broken imports:

### 1. Relative Import Fixes

Many HOC files had broken relative imports (`from ..auth import`) that were fixed to absolute imports (`from app.auth import`). Affected files include:
- All files in `hoc/api/fdr/*`
- Many files in `hoc/api/cus/*`

### 2. Missing Module Shims

| File | Purpose |
|------|---------|
| `app/services/_audit_shim.py` | No-op shim for broken audit ledger import |

### 3. Legacy `__init__.py` Cleanup

- `app/hoc/api/cus/policies/__init__.py` - Removed legacy router re-exports
- `app/adapters/__init__.py` - Disabled broken `customer_incidents_adapter` import

### 4. Dead Code Deletion

| File | Size | Reason |
|------|------|--------|
| `app/hoc/api/int/agent/main.py` | 85KB | Duplicate of main.py in wrong location |

---

## Legacy Deletion (Completed)

- Legacy `backend/app/api/**` has been deleted (2026-02-08). HOC (`backend/app/hoc/api/**`) is the only canonical API surface.
- Remaining compatibility shims (if any) should be deleted only after their last caller is removed (tracked in memory pins).

---

## Verification

### Startup Test
```bash
cd backend && python -c "from app.main import app; print('OK')"
```

### Route Count
- Total API routes: 688
- All routes functional after migration

---

## References

- PIN-526: HOC API Wiring Migration
- PIN-532: Delete Legacy backend/app/api
- PLAN-HOC-API-WIRING.md: Migration plan with audit findings
- HOC Layer Topology V2.0.0: Layer definitions
- PIN-511: Legacy `app/services/*` boundary

---

## Changelog

### 1.0.0 (2026-02-04)
- Initial documentation after migration completion
- 68 legacy routers migrated to HOC
- 4 new HOC-only routers wired
- 25+ broken imports fixed
- Dead code deleted
- Tombstones added to deprecated files
