# HOC Migration Plan

**Version:** 1.1.0
**Status:** DRAFT
**Created:** 2026-01-23
**Reference:** `HOC_LAYER_TOPOLOGY_V1.md` (v1.2.0)

---

## Detailed Phase Plans

| Phase | Document |
|-------|----------|
| **Phase 1** | [`migration/PHASE1_MIGRATION_PLAN.md`](migration/PHASE1_MIGRATION_PLAN.md) |
| **Phase 2** | TBD |
| **Phase 3** | TBD |
| **Phase 4** | TBD |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-23 | Founder + Claude | Initial migration plan |
| 1.1.0 | 2026-01-23 | Founder + Claude | Corrected scope: only L7 models stay, all else migrates. Added link to detailed Phase 1 plan. |

---

## Executive Summary

This document outlines the four-phase migration plan for restructuring the codebase from `app/services/*` to `app/hoc/{audience}/{domain}/*` following the HOC Layer Topology V1.2.0.

**Architectural Decision (2026-01-23):** Keep HOC inside `app/` directory (Option B).
- Target: `app/hoc/` (NOT `hoc/` outside app)
- Rationale: 248 files already structured in `app/hoc/`, no relocation needed
- Cleanup: Delete `app/services/*` after migration complete

**Current State:**
- `app/services/`: 220 files in 41 subdirectories
- `app/api/`: 78 files
- `app/models/`: 30 files
- `app/hoc/`: 248 files (partial migration already started)

**Target State:**
- All domain logic in `app/hoc/{audience}/{domain}/`
- Layer contracts enforced (L2.1, L2, L3, L4, L5, L6, L7)
- Headers on all files
- BLCA passing with 0 violations
- `app/services/*` deleted

---

## Phase Overview

| Phase | Name | Objective |
|-------|------|-----------|
| **P1** | Migration | Move files to `app/hoc/`, insert headers |
| **P2** | Gap Analysis | Identify missing pieces at each layer |
| **P3** | Development | Build missing components |
| **P4** | Wiring | Connect all layers, validate contracts |
| **P5** | Cleanup | Delete `app/services/*` and legacy code |

---

# PHASE 1: MIGRATION

## 1.1 Migration Scope

### Files That WILL Migrate

| Source | Target | Layer | Count |
|--------|--------|-------|-------|
| `app/services/*_facade.py` | `hoc/{audience}/{domain}/adapters/` | L3 | ~25 |
| `app/services/**/*_engine.py` | `hoc/{audience}/{domain}/engines/` | L5 | ~40 |
| `app/services/**/*_service.py` | `hoc/{audience}/{domain}/engines/` or `drivers/` | L5/L6 | ~80 |
| `app/services/**/schemas/` | `hoc/{audience}/{domain}/schemas/` | L5 | ~15 |
| `app/api/*.py` | `hoc/api/{audience}/*.py` | L2 | ~50 |
| `app/worker/*.py` | `hoc/{audience}/general/L4_runtime/` or `{domain}/workers/` | L4/L5 | ~20 |
| `app/auth/*.py` | `hoc/int/platform/auth/` | L4-Internal | ~40 |
| `app/core/*.py` | `hoc/int/platform/core/` | L6-Internal | ~15 |
| `app/events/*.py` | `hoc/int/platform/events/` | L6-Internal | ~10 |
| `app/middleware/*.py` | `hoc/api/middleware/` | L2-Infra | ~10 |

### Files That WILL NOT Migrate (Stay in `app/`) — L7 ONLY

| Location | Reason | Layer |
|----------|--------|-------|
| `app/models/*.py` (shared) | Cross-audience DB tables (tenant, audit_ledger, base) | L7 |
| `app/cus/models/*.py` | Customer-specific DB tables | L7 |
| `app/fdr/models/*.py` | Founder-specific DB tables | L7 |
| `app/int/models/*.py` | Internal-specific DB tables | L7 |

**Note:** Only database table definitions (L7) stay in `app/`. Everything else migrates to `hoc/`.

### Files to DELETE (Legacy/Duplicate)

| Location | Reason |
|----------|--------|
| `hoc/duplicate/` | Legacy structures (30 files) |
| `app/api/legacy_routes.py` | Deprecated routes |
| `app/api/v1_*.py` | V1 proxy routes (deprecated) |

---

## 1.2 Migration by Audience/Domain

### CUSTOMER Audience

#### Overview Domain (`customer/overview/`)

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/overview_facade.py` | `adapters/overview_adapter.py` | L3 |
| `app/api/overview.py` | `hoc/api/cus/overview.py` | L2 |
| — | `facades/overview.py` (NEW - L2.1) | L2.1 |

**Missing (to be created in P3):**
- `engines/` — business logic
- `drivers/` — data access
- `schemas/` — data contracts

---

#### Activity Domain (`customer/activity/`)

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/activity_facade.py` | `adapters/activity_adapter.py` | L3 |
| `app/services/activity/attention_ranking_service.py` | `engines/attention_ranking.py` | L5 |
| `app/services/activity/cost_analysis_service.py` | `engines/cost_analysis.py` | L5 |
| `app/services/activity/pattern_detection_service.py` | `engines/pattern_detection.py` | L5 |
| `app/services/activity/signal_feedback_service.py` | `engines/signal_feedback.py` | L5 |
| `app/services/activity/signal_identity.py` | `engines/signal_identity.py` | L5 |
| `app/api/activity.py` | `hoc/api/cus/activity.py` | L2 |

**Already exists in HOC:** Most engines already migrated

**Missing:**
- `facades/activity.py` (L2.1)
- `drivers/activity_driver.py` (L6)
- `schemas/activity_models.py` (L5)

---

#### Incidents Domain (`customer/incidents/`)

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/incidents_facade.py` | `adapters/incidents_adapter.py` | L3 |
| `app/services/incidents/incident_engine.py` | `engines/incident_engine.py` | L5 |
| `app/services/incidents/incident_pattern_service.py` | `engines/pattern_service.py` | L5 |
| `app/services/incidents/postmortem_service.py` | `engines/postmortem.py` | L5 |
| `app/services/incidents/recurrence_analysis_service.py` | `engines/recurrence.py` | L5 |
| `app/services/incident_read_service.py` | `drivers/incident_driver.py` | L6 |
| `app/services/incident_write_service.py` | `drivers/incident_driver.py` | L6 |
| `app/services/incident_aggregator.py` | `engines/aggregator.py` | L5 |
| `app/api/incidents.py` | `hoc/api/cus/incidents.py` | L2 |

**Already exists in HOC:** Most engines already migrated

**Missing:**
- `facades/incidents.py` (L2.1)
- Schema consolidation

---

#### Policies Domain (`customer/policies/`)

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/policies_facade.py` | `adapters/policies_adapter.py` | L3 |
| `app/services/limits_facade.py` | `adapters/limits_adapter.py` | L3 |
| `app/services/governance_facade.py` | `adapters/governance_adapter.py` | L3 |
| `app/services/controls_facade.py` | `adapters/controls_adapter.py` | L3 |
| `app/services/policy/*_service.py` | `engines/*.py` | L5 |
| `app/services/limits/*_service.py` | `engines/*.py` | L5 |
| `app/services/killswitch/*` | `controls/KillSwitch/engines/` | L5 |
| `app/api/policies.py` | `hoc/api/cus/policies.py` | L2 |
| `app/api/policy_*.py` | `hoc/api/cus/policies.py` | L2 |

**Already exists in HOC:** Extensive policies structure

**Missing:**
- `facades/policies.py` (L2.1)
- `facades/limits.py` (L2.1)
- Driver consolidation

---

#### Logs Domain (`customer/logs/`)

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/logs_facade.py` | `adapters/logs_adapter.py` | L3 |
| `app/services/evidence_facade.py` | `adapters/evidence_adapter.py` | L3 |
| `app/services/logs_read_service.py` | `drivers/logs_driver.py` | L6 |
| `app/services/audit/*` | `engines/audit/` | L5 |
| `app/services/export/*` | `engines/export/` | L5 |
| `app/api/logs.py` | `hoc/api/cus/logs.py` | L2 |
| `app/api/evidence.py` | `hoc/api/cus/evidence.py` | L2 |
| `app/api/traces.py` | `hoc/api/cus/traces.py` | L2 |

**Missing:**
- `facades/logs.py` (L2.1)
- `facades/evidence.py` (L2.1)

---

#### Analytics Domain (`customer/analytics/`)

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/analytics_facade.py` | `adapters/analytics_adapter.py` | L3 |
| `app/services/detection_facade.py` | `adapters/detection_adapter.py` | L3 |
| `app/services/cost_anomaly_detector.py` | `engines/anomaly_detector.py` | L5 |
| `app/services/cost_model_engine.py` | `engines/cost_model.py` | L5 |
| `app/services/prediction.py` | `engines/prediction.py` | L5 |
| `app/api/analytics.py` | `hoc/api/cus/analytics.py` | L2 |
| `app/api/detection.py` | `hoc/api/cus/detection.py` | L2 |

**Missing:**
- `facades/analytics.py` (L2.1)
- `drivers/analytics_driver.py` (L6)

---

#### Integrations Domain (`customer/integrations/`)

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/integrations_facade.py` | `adapters/integrations_adapter.py` | L3 |
| `app/services/connectors_facade.py` | `adapters/connectors_adapter.py` | L3 |
| `app/services/datasources_facade.py` | `adapters/datasources_adapter.py` | L3 |
| `app/services/connectors/*` | `engines/connectors/` | L5 |
| `app/services/credentials/*` | `engines/credentials/` | L5 |
| `app/services/mcp/*` | `engines/mcp/` | L5 |
| `app/api/connectors.py` | `hoc/api/cus/connectors.py` | L2 |
| `app/api/datasources.py` | `hoc/api/cus/datasources.py` | L2 |

**Missing:**
- `facades/integrations.py` (L2.1)

---

#### API Keys Domain (`customer/api_keys/`)

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/api_keys_facade.py` | `adapters/api_keys_adapter.py` | L3 |
| `app/services/key_service.py` | `engines/key_service.py` | L5 |
| `app/api/aos_api_key.py` | `hoc/api/cus/api_keys.py` | L2 |

**Missing:**
- `facades/api_keys.py` (L2.1)
- `drivers/api_keys_driver.py` (L6)

---

#### Account Domain (`customer/account/`)

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/accounts_facade.py` | `adapters/accounts_adapter.py` | L3 |
| `app/services/tenant_service.py` | `engines/tenant.py` | L5 |
| `app/services/user_write_service.py` | `drivers/user_driver.py` | L6 |
| `app/api/aos_accounts.py` | `hoc/api/cus/account.py` | L2 |
| `app/api/tenants.py` | `hoc/api/cus/tenants.py` | L2 |
| `app/api/onboarding.py` | `hoc/api/cus/onboarding.py` | L2 |

**Missing:**
- `facades/account.py` (L2.1)

---

### FOUNDER Audience

#### Ops Domain (`founder/ops/`)

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/ops_facade.py` | `adapters/ops_adapter.py` | L3 |
| `app/services/ops/*` | `engines/*` | L5 |
| `app/api/ops.py` | `hoc/api/fdr/ops.py` | L2 |
| `app/api/founder_*.py` | `hoc/api/fdr/ops.py` | L2 |

**Missing:**
- `facades/ops.py` (L2.1)
- Driver consolidation

---

### INTERNAL Audience

#### Platform Domain (`internal/platform/`)

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/scheduler/*` | `engines/scheduler/` | L5 |
| `app/services/sandbox/*` | `engines/sandbox/` | L5 |
| `app/services/pools/*` | `engines/pools/` | L5 |
| `app/services/platform/*` | `engines/platform/` | L5 |
| `app/api/scheduler.py` | `hoc/api/int/scheduler.py` | L2 |
| `app/api/platform.py` | `hoc/api/int/platform.py` | L2 |

---

#### Recovery Domain (`internal/recovery/`)

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/orphan_recovery.py` | `engines/orphan_recovery.py` | L5 |
| `app/services/recovery_*.py` | `engines/recovery/` | L5 |
| `app/api/recovery.py` | `hoc/api/int/recovery.py` | L2 |

---

#### Agent Domain (`internal/agent/`)

| Source | Target | Layer |
|--------|--------|-------|
| `app/services/ai_console_panel_adapter/*` | `engines/panel/` | L5 |
| `app/services/worker_registry_service.py` | `engines/worker_registry.py` | L5 |
| `app/api/workers.py` | `hoc/api/int/workers.py` | L2 |

---

## 1.3 Header Insertion

Every migrated file must have the appropriate header based on its layer.

### Header Templates by Layer

**L2.1 Facade:**
```python
# Layer: L2.1 — API Facade
# AUDIENCE: {CUSTOMER | FOUNDER | INTERNAL}
# Role: {single-line description}
# Callers: L1 Frontend, External Clients
# Reference: HOC_LAYER_TOPOLOGY_V1.md
#
# L2.1 FACADE CONTRACT:
# - Organizers only, no business logic
# - May import L2 routers ONLY
```

**L2 API:**
```python
# Layer: L2 — Product API
# AUDIENCE: {CUSTOMER | FOUNDER | INTERNAL}
# Role: {single-line description}
# Callers: L2.1 Facades
# Reference: HOC_LAYER_TOPOLOGY_V1.md
```

**L3 Adapter:**
```python
# Layer: L3 — Boundary Adapter
# AUDIENCE: {CUSTOMER | FOUNDER | INTERNAL}
# Role: {single-line description}
# Callers: L2 APIs
# Reference: HOC_LAYER_TOPOLOGY_V1.md
#
# ADAPTER CONTRACT:
# - Translation + aggregation only
# - No state mutation
# - No retries
# - No policy decisions
```

**L4 Runtime:**
```python
# Layer: L4 — Governed Runtime ({PART})
# AUDIENCE: {CUSTOMER | FOUNDER | INTERNAL}
# Role: {single-line description}
# Callers: L3 Adapters
# Reference: HOC_LAYER_TOPOLOGY_V1.md
#
# L4 RUNTIME CONTRACT:
# - Part: {authority | execution | consequences}
# - Independence guarantee applies
```

**L5 Engine:**
```python
# Layer: L5 — Domain Engine
# AUDIENCE: {CUSTOMER | FOUNDER | INTERNAL}
# Role: {single-line description}
# Callers: L4 Runtime, L3 Adapters (cross-domain)
# Reference: HOC_LAYER_TOPOLOGY_V1.md
```

**L5 Worker:**
```python
# Layer: L5 — Domain Worker
# AUDIENCE: {CUSTOMER | FOUNDER | INTERNAL}
# Role: {single-line description}
# Idempotent: YES | NO (if NO, explain why)
# Callers: L4 Runtime
# Reference: HOC_LAYER_TOPOLOGY_V1.md
#
# WORKER CONTRACT:
# - Restart-safe
# - No incident creation
# - No retry management
```

**L6 Driver:**
```python
# Layer: L6 — Database Driver
# AUDIENCE: {CUSTOMER | FOUNDER | INTERNAL}
# Role: {single-line description}
# Callers: L5 Engines, L4 Runtime
# Reference: HOC_LAYER_TOPOLOGY_V1.md
#
# DRIVER CONTRACT:
# - Returns domain objects, not ORM models
# - Owns query logic
# - Owns data shape transformation
```

---

## 1.4 Migration Checklist

### Per-File Migration Steps

- [ ] Identify source file and target location
- [ ] Determine layer classification
- [ ] Copy file to target location
- [ ] Insert appropriate header
- [ ] Update imports to new paths
- [ ] Update callers to use new path
- [ ] Run BLCA to verify no violations
- [ ] Mark source file as deprecated (add `# DEPRECATED: Migrated to {path}`)
- [ ] Add to quarantine registry if violations remain

### Domain Migration Order (Recommended)

1. **API Keys** — smallest, isolated
2. **Account** — next smallest
3. **Overview** — simple aggregation
4. **Activity** — well-defined boundaries
5. **Logs** — audit requirements clear
6. **Analytics** — depends on Activity
7. **Incidents** — depends on Activity, Logs
8. **Policies** — depends on Incidents
9. **Integrations** — external dependencies
10. **Ops (Founder)** — cross-cutting
11. **Platform (Internal)** — infrastructure
12. **Recovery (Internal)** — depends on Platform
13. **Agent (Internal)** — depends on Platform

---

# PHASE 2: GAP ANALYSIS

## 2.1 Layer Gap Identification

After Phase 1 migration, identify missing pieces at each layer.

### Gap Analysis Template

For each `hoc/{audience}/{domain}/`:

| Layer | Expected | Exists? | Gap |
|-------|----------|---------|-----|
| L2.1 Facade | `facades/{domain}.py` | ❌ | Create |
| L2 API | `api/{audience}/{domain}.py` | ✅ | — |
| L3 Adapter | `adapters/{domain}_adapter.py` | ✅ | — |
| L4 Runtime | `general/runtime/authority/` | ⚠️ | Partial |
| L4 Runtime | `general/runtime/execution/` | ⚠️ | Partial |
| L4 Runtime | `general/runtime/consequences/` | ❌ | Create |
| L4 Runtime | `general/runtime/contracts/` | ❌ | Create |
| L5 Engines | `engines/*.py` | ✅ | — |
| L5 Workers | `workers/*.py` | ⚠️ | Some missing |
| L5 Schemas | `schemas/*.py` | ⚠️ | Consolidate |
| L6 Drivers | `drivers/*.py` | ⚠️ | Some missing |

---

## 2.2 Gap Analysis by Domain

### Customer Domains

| Domain | L2.1 | L2 | L3 | L4 | L5-E | L5-W | L5-S | L6 |
|--------|------|----|----|----|----|----|----|----|
| overview | ❌ | ✅ | ✅ | ⚠️ | ❌ | — | ❌ | ❌ |
| activity | ❌ | ✅ | ✅ | ⚠️ | ✅ | ❌ | ⚠️ | ❌ |
| incidents | ❌ | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| policies | ❌ | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| logs | ❌ | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| analytics | ❌ | ✅ | ✅ | ⚠️ | ✅ | ❌ | ❌ | ❌ |
| integrations | ❌ | ✅ | ✅ | ⚠️ | ✅ | ❌ | ⚠️ | ⚠️ |
| api_keys | ❌ | ✅ | ✅ | ⚠️ | ✅ | — | ❌ | ❌ |
| account | ❌ | ✅ | ✅ | ⚠️ | ✅ | — | ⚠️ | ⚠️ |

**Legend:** ✅ Complete | ⚠️ Partial | ❌ Missing | — Not Applicable

### Shared Runtime (L4)

| Part | Customer | Founder | Internal |
|------|----------|---------|----------|
| authority/ | ❌ | ❌ | ❌ |
| execution/ | ⚠️ | ❌ | ❌ |
| consequences/ | ❌ | ❌ | ❌ |
| contracts/ | ❌ | ❌ | ❌ |

---

## 2.3 Gap Inventory Format

```yaml
# gap_inventory.yaml
customer:
  overview:
    missing:
      - layer: L2.1
        path: facades/overview.py
        purpose: Organize overview API routes
      - layer: L5-Engine
        path: engines/overview_engine.py
        purpose: Aggregate health status from multiple domains
      - layer: L6-Driver
        path: drivers/overview_driver.py
        purpose: Query aggregated metrics

  activity:
    missing:
      - layer: L2.1
        path: facades/activity.py
        purpose: Organize activity API routes
      - layer: L6-Driver
        path: drivers/activity_driver.py
        purpose: Query run history
```

---

# PHASE 3: DEVELOPMENT

## 3.1 Development Order

Build missing pieces in dependency order:

### Round 1: Contracts and Runtime (L4)

1. `contracts/runtime_verdict.py` — Immutable verdict object
2. `authority/governance_gate.py` — Grant/deny execution
3. `execution/orchestrator.py` — Trigger engines
4. `consequences/enforcement.py` — React to outcomes

### Round 2: Drivers (L6)

Build drivers for each domain to ensure L5 engines have data access.

| Domain | Driver | Purpose |
|--------|--------|---------|
| overview | `overview_driver.py` | Aggregate metrics |
| activity | `activity_driver.py` | Query runs |
| incidents | `incident_driver.py` | Query incidents |
| policies | `policy_driver.py` | Query policies |
| logs | `logs_driver.py` | Query logs/traces |
| analytics | `analytics_driver.py` | Query cost data |
| integrations | `integrations_driver.py` | Query connectors |
| api_keys | `api_keys_driver.py` | Query API keys |
| account | `account_driver.py` | Query accounts |

### Round 3: Schemas (L5)

Consolidate and standardize schemas for each domain.

### Round 4: Missing Engines (L5)

Build any engines not migrated from `app/services/`.

### Round 5: Missing Workers (L5)

Build background workers for heavy computation.

### Round 6: Facades (L2.1)

Build API organizers after all L2 routes are stable.

---

## 3.2 Development Template

### Driver Template (L6)

```python
# hoc/cus/{domain}/drivers/{domain}_driver.py
# Layer: L6 — Database Driver
# AUDIENCE: CUSTOMER
# Role: Database operations for {domain}
# Callers: L5 Engines
# Reference: HOC_LAYER_TOPOLOGY_V1.md
#
# DRIVER CONTRACT:
# - Returns domain objects, not ORM models
# - Owns query logic
# - Owns data shape transformation

from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.cus.models.{model} import {Model}


@dataclass
class {Domain}Snapshot:
    """Immutable snapshot returned to engines."""
    id: str
    # ... fields


class {Domain}Driver:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_by_tenant(self, tenant_id: str) -> list[{Domain}Snapshot]:
        query = select({Model}).where({Model}.tenant_id == tenant_id)
        result = await self._session.execute(query)
        return [self._to_snapshot(row) for row in result.scalars().all()]

    def _to_snapshot(self, model: {Model}) -> {Domain}Snapshot:
        """Transform ORM model to domain snapshot (L6 contract)."""
        return {Domain}Snapshot(
            id=str(model.id),
            # ... mapping
        )
```

### Facade Template (L2.1)

```python
# hoc/api/facades/cus/{domain}.py
# Layer: L2.1 — API Facade
# AUDIENCE: CUSTOMER
# Role: Organizes {domain}-related API access
# Callers: L1 Frontend, External Clients
# Reference: HOC_LAYER_TOPOLOGY_V1.md
#
# L2.1 FACADE CONTRACT:
# - Organizers only, no business logic
# - May import L2 routers ONLY

from hoc.api.customer import {domain}


class Customer{Domain}Facade:
    """Groups all {domain}-related API routers."""

    routers = [
        {domain}.router,
    ]
```

---

# PHASE 4: WIRING

## 4.1 Layer Wiring

Connect all layers following import rules.

### Wiring Order

1. **L7 → L6**: Drivers import models
2. **L6 → L5**: Engines receive drivers via DI
3. **L5 → L4**: Runtime calls engines
4. **L4 → L3**: Adapters call runtime
5. **L3 → L2**: APIs call adapters
6. **L2 → L2.1**: Facades organize APIs

### Dependency Injection Pattern

```python
# L3 Adapter receives L4 Runtime and L5 Engines
class PoliciesAdapter:
    def __init__(
        self,
        session: AsyncSession,
        runtime: CustomerOrchestrator,  # L4
        engine: PolicyEngine,           # L5
    ):
        self._session = session
        self._runtime = runtime
        self._engine = engine

# L5 Engine receives L6 Driver
class PolicyEngine:
    def __init__(self, driver: PolicyDriver):  # L6
        self._driver = driver

# L6 Driver receives session only
class PolicyDriver:
    def __init__(self, session: AsyncSession):
        self._session = session
```

---

## 4.2 Wiring Validation

### BLCA Checks

Run BLCA after wiring to verify:

```bash
python3 scripts/ops/layer_validator.py --backend --ci
```

**Expected:** 0 violations

### Contract Checks

| Contract | Validation |
|----------|------------|
| L2.1 Facade | No L3-L7 imports |
| L3 Adapter | No retry patterns |
| L4 Runtime | Parts don't call each other |
| L5 Worker | No incident creation |
| L6 Driver | No ORM in return types |

### Import Graph

Generate import graph to visualize dependencies:

```bash
python3 scripts/ops/import_graph.py --output docs/architecture/import_graph.svg
```

---

## 4.3 Final Validation

### Acceptance Criteria

- [ ] All files have headers
- [ ] BLCA passes with 0 violations
- [ ] All contracts satisfied
- [ ] No circular imports
- [ ] All tests pass
- [ ] Quarantine registry empty

---

# PHASE 5: CLEANUP

## 5.1 Cleanup Scope

After Phase 4 wiring is complete and validated, delete legacy code.

### Files to DELETE

| Location | Condition | Action |
|----------|-----------|--------|
| `app/services/**/*.py` | All files migrated to `app/hoc/` | DELETE entire directory |
| `app/hoc/duplicate/` | Legacy duplicates | DELETE entire directory |
| `app/api/legacy_routes.py` | Deprecated | DELETE |
| `app/api/v1_*.py` | Deprecated v1 proxies | DELETE |

### Pre-Cleanup Checklist

Before deleting any files:

- [ ] All imports updated to use `app.hoc.*` paths
- [ ] BLCA passes with 0 violations
- [ ] All tests pass
- [ ] No references to `app.services.*` in codebase
- [ ] Git commit with all migrations complete

### Cleanup Steps

1. **Verify no references:**
   ```bash
   grep -r "from app.services" backend/ --include="*.py" | wc -l
   # Expected: 0
   ```

2. **Delete app/services/:**
   ```bash
   rm -rf backend/app/services/
   ```

3. **Delete app/hoc/duplicate/:**
   ```bash
   rm -rf backend/app/hoc/duplicate/
   ```

4. **Run tests:**
   ```bash
   cd backend && pytest tests/ -v
   ```

5. **Run BLCA:**
   ```bash
   python3 scripts/ops/layer_validator.py --backend --ci
   ```

### Acceptance Criteria (Phase 5)

- [ ] `app/services/` directory deleted
- [ ] `app/hoc/duplicate/` directory deleted
- [ ] No `app.services.*` imports in codebase
- [ ] All tests pass
- [ ] BLCA passes with 0 violations

---

# Appendix A: File Mapping Table

| Source | Target | Layer | Status |
|--------|--------|-------|--------|
| `app/services/overview_facade.py` | `customer/overview/L3_adapters/overview_adapter.py` | L3 | Pending |
| `app/services/activity_facade.py` | `customer/activity/L3_adapters/activity_adapter.py` | L3 | Pending |
| `app/services/incidents_facade.py` | `customer/incidents/L3_adapters/incidents_adapter.py` | L3 | Pending |
| `app/services/policies_facade.py` | `customer/policies/L3_adapters/policies_adapter.py` | L3 | Pending |
| `app/services/logs_facade.py` | `customer/logs/L3_adapters/logs_adapter.py` | L3 | Pending |
| `app/services/analytics_facade.py` | `customer/analytics/L3_adapters/analytics_adapter.py` | L3 | Pending |
| `app/services/integrations_facade.py` | `customer/integrations/L3_adapters/integrations_adapter.py` | L3 | Pending |
| `app/services/api_keys_facade.py` | `customer/api_keys/L3_adapters/api_keys_adapter.py` | L3 | Pending |
| `app/services/accounts_facade.py` | `customer/account/L3_adapters/accounts_adapter.py` | L3 | Pending |
| `app/services/ops_facade.py` | `founder/ops/adapters/ops_adapter.py` | L3 | Pending |
| ... | ... | ... | ... |

*Full mapping in `docs/architecture/MIGRATION_FILE_MAP.yaml`*

---

# Appendix B: Quarantine Registry Template

```markdown
# Quarantine Registry

| File | Violation | Migration Plan | Target Date |
|------|-----------|----------------|-------------|
| `app/services/legacy_thing.py` | L3 imports L5 | Extract to adapter | 2026-02-01 |
```

---

**Document Status:** DRAFT
**Next Review:** After Phase 1 completion
