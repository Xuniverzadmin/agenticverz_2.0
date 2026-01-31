# PIN-498: Integrations Domain Canonical Consolidation

**Status:** COMPLETE
**Date:** 2026-01-31
**Domain:** integrations
**Scope:** 52 files (16 L5_engines, 2 credentials, 5 L6_drivers, 23 adapters, 5 L5_schemas, __init__.py)

---

## Actions Taken

### 1. Naming Violations Fixed (6 renames)

**L5 (5):**

| Old Name | New Name |
|----------|----------|
| cus_integration_service.py | cus_integration_engine.py |
| bridges.py | bridges_engine.py |
| dispatcher.py | dispatcher_engine.py |
| http_connector.py | http_connector_engine.py |
| mcp_connector.py | mcp_connector_engine.py |

**L6 (1):**

| Old Name | New Name |
|----------|----------|
| connector_registry.py | connector_registry_driver.py |

### 2. Header Correction (1)

- `integrations/__init__.py`: L4 → L5

### 3. Legacy Disconnection (1)

- `cus_integration_engine.py`: Disconnected `from app.services.cus_integration_engine import (...)`. Stubbed CusIntegrationEngine, CusIntegrationService, EnableResult, DeleteResult, HealthCheckResult with TODO: rewire to HOC equivalent candidate during rewiring phase.

### 4. Import Path Fixes (4)

- `integrations_facade.py`: `cus_integration_service` → `cus_integration_engine`
- `connectors_facade.py`: `connector_registry` → `connector_registry_driver`
- `bridges_engine.py`: `.dispatcher` → `.dispatcher_engine`, `.bridges_driver` → `L6_drivers.bridges_driver`

### 5. Schema Import Fixes (2)

- `bridges_engine.py`: `..schemas.audit_schemas` → absolute `L5_schemas.audit_schemas`
- `bridges_engine.py`: `..schemas.loop_events` → absolute `L5_schemas.loop_events`

### 6. Broken Import Restored (1)

- `L6_drivers/bridges_driver.py` was missing (referenced by `__init__.py`). Restored from Phase 3 backup with import paths corrected to absolute HOC paths.

### 7. Duplicate Files Resolved (13 + 8 moved)

- Deleted `L5_engines/external_adapters/` directory entirely (13 duplicates of files in `adapters/`)
- Moved 8 unique files from `external_adapters/` to `adapters/` before deletion: customer_activity_adapter, customer_incidents_adapter, customer_keys_adapter, customer_logs_adapter, customer_policies_adapter, founder_ops_adapter, runtime_adapter, workers_adapter

### 8. Hybrid Files (Documented)

- `bridges_engine.py` — M25_FROZEN, L5/L6 HYBRID. DB ops extraction to L6 pending.
- `dispatcher_engine.py` — M25_FROZEN, L5/L6 HYBRID. DB ops extraction to L6 pending.

### 9. Cross-Domain Imports (Deferred to Rewiring)

5 boundary adapters in `adapters/` make L3→L5 cross-domain calls:
- customer_incidents_adapter → incidents L5
- customer_logs_adapter → logs L5
- customer_policies_adapter → policies L5
- customer_activity_adapter → activity L5
- customer_keys_adapter → api_keys L5

Correct architecture: L3→L4→L5. Deferred to rewiring phase.

---

## Artifacts

| Artifact | Path |
|----------|------|
| Literature | `literature/hoc_domain/integrations/INTEGRATIONS_CANONICAL_SOFTWARE_LITERATURE.md` |
| Tally Script | `scripts/ops/hoc_integrations_tally.py` |
| PIN | This file |

## Tally Result

35/35 checks PASS.

## L4 Handler

`integrations_handler.py` — 3 operations registered. No import updates required (facades were not renamed).
