# HOC Remaining Domains Analysis v1.0

**Domains Analyzed:** analytics, api_keys, general, integrations, logs, overview
**Date:** 2026-01-22
**Status:** 2 VIOLATIONS DETECTED - CLEANUP REQUIRED

---

## 1. SUMMARY BY DOMAIN

| Domain | Files | Status | Violations |
|--------|-------|--------|------------|
| analytics | 12 | CLEAN | 0 |
| api_keys | 7 | CLEAN | 0 |
| general | 39 | CLEAN | 0 |
| integrations | 21 | **VIOLATIONS** | 2 |
| logs | 20 | CLEAN | 0 |
| overview | 6 | CLEAN | 0 |

**Total Files:** 105
**Total Violations:** 2

---

## 2. ANALYTICS DOMAIN (12 files) - CLEAN

```
analytics/
├── __init__.py
├── facades/
│   ├── __init__.py
│   ├── analytics_facade.py      # AUDIENCE: CUSTOMER
│   └── detection_facade.py      # L4 Domain Engine
├── engines/
│   ├── __init__.py              # AUDIENCE: CUSTOMER
│   ├── cost_model_engine.py     # L4 Domain Engine
│   ├── cost_anomaly_detector.py # L4 Domain Engine
│   ├── cost_write_service.py    # L4 Domain Engine
│   ├── pattern_detection.py     # L4 Domain Engine
│   └── prediction.py            # L3 Boundary Adapter
├── drivers/
│   └── __init__.py              # Empty
└── schemas/
    └── __init__.py              # Empty
```

**Purpose:** Cost analytics, anomaly detection, pattern detection, predictions

---

## 3. API_KEYS DOMAIN (7 files) - CLEAN

```
api_keys/
├── __init__.py
├── facades/
│   ├── __init__.py              # AUDIENCE: CUSTOMER
│   └── api_keys_facade.py       # AUDIENCE: CUSTOMER
├── engines/
│   ├── __init__.py              # AUDIENCE: CUSTOMER
│   └── keys_service.py          # L4 Domain Engine
├── drivers/
│   └── __init__.py              # Empty
└── schemas/
    └── __init__.py              # Empty
```

**Purpose:** API key lifecycle management for customers

---

## 4. GENERAL DOMAIN (39 files) - CLEAN

```
general/
├── __init__.py
├── facades/
│   ├── __init__.py
│   ├── alerts_facade.py         # L4 Domain Engine
│   ├── compliance_facade.py     # L4 Domain Engine
│   ├── lifecycle_facade.py      # AUDIENCE: CUSTOMER
│   ├── monitors_facade.py       # AUDIENCE: CUSTOMER
│   └── scheduler_facade.py      # L4 Domain Engine
├── engines/
│   ├── __init__.py
│   ├── alert_emitter.py         # L3 Boundary Adapter
│   ├── alert_fatigue.py         # L4 Domain Engine
│   ├── alert_log_linker.py      # L4 Domain Engines
│   ├── cus_enforcement_service.py # L4 Domain Engines
│   ├── cus_health_service.py    # L4 Domain Engines
│   ├── cus_telemetry_service.py # L4 Domain Engines
│   ├── fatigue_controller.py    # L4 Domain Engines
│   ├── knowledge_lifecycle_manager.py # L4 Domain Engine
│   ├── knowledge_sdk.py         # L2 Product APIs
│   └── panel_invariant_monitor.py # L4 Domain Engines
├── controls/
│   ├── __init__.py
│   └── engines/
│       ├── __init__.py
│       └── guard_write_service.py # L4 Domain Engine
├── cross-domain/
│   └── engines/
│       └── cross_domain.py      # L4 Domain Engine
├── lifecycle/
│   └── engines/
│       ├── base.py              # L4 Domain Engine
│       ├── execution.py         # L4 Domain Engines
│       ├── knowledge_plane.py   # L4 Domain Engines
│       ├── offboarding.py       # L4 Domain Engine
│       ├── onboarding.py        # L4 Domain Engine
│       └── pool_manager.py      # L4 Domain Engines
├── runtime/
│   └── engines/
│       ├── __init__.py
│       ├── constraint_checker.py # L4 Domain Engines
│       ├── governance_orchestrator.py # L4 Domain Engine
│       ├── phase_status_invariants.py # L4 Domain Engines
│       ├── plan_generation_engine.py # L4 Domain Engine
│       ├── run_governance_facade.py # L4 Domain Engine
│       └── transaction_coordinator.py # L4 Domain Engine
├── ui/
│   └── engines/
│       └── rollout_projection.py # L4 Domain Engine
├── workflow/
│   └── contracts/
│       └── engines/
│           └── contract_service.py # L4 Domain Engine
├── drivers/
│   └── __init__.py              # Empty
└── schemas/
    └── __init__.py              # Empty
```

**Purpose:** General-purpose engines for alerts, monitoring, lifecycle, governance

---

## 5. INTEGRATIONS DOMAIN (21 files) - VIOLATIONS

```
integrations/
├── __init__.py
├── facades/
│   ├── __init__.py
│   ├── integrations_facade.py   # AUDIENCE: CUSTOMER
│   ├── connectors_facade.py     # L4 Domain Engine
│   ├── datasources_facade.py    # L4 Domain Engine
│   └── retrieval_facade.py      # L4 Domain Engine
├── engines/
│   ├── __init__.py
│   ├── connector_registry.py    # (no header)
│   ├── http_connector.py        # L4 Domain Engine
│   ├── mcp_connector.py         # L4 Domain Engine
│   ├── sql_gateway.py           # L4 Domain Engine
│   ├── server_registry.py       # **VIOLATION: AUDIENCE: INTERNAL**
│   ├── cus_integration_service.py # AUDIENCE: CUSTOMER
│   ├── external_response_service.py # L4 Domain Engine
│   └── retrieval_mediator.py    # L4 Domain Engine
├── vault/
│   └── engines/
│       ├── cus_credential_service.py # L4 Domain Engine
│       ├── service.py           # L4 Domain Engine
│       └── vault.py             # **VIOLATION: AUDIENCE: INTERNAL**
├── schemas/
│   └── datasource_model.py      # Schema (no header)
└── drivers/
    └── __init__.py              # Empty
```

### VIOLATIONS:

#### 5.1 server_registry.py - AUDIENCE: INTERNAL

| Attribute | Value |
|-----------|-------|
| File | `engines/server_registry.py` |
| Header | `# AUDIENCE: INTERNAL` |
| Current Path | `customer/integrations/L5_engines/server_registry.py` |
| Required Path | `internal/platform/mcp/engines/server_registry.py` |

#### 5.2 vault.py - AUDIENCE: INTERNAL

| Attribute | Value |
|-----------|-------|
| File | `vault/engines/vault.py` |
| Header | `# AUDIENCE: INTERNAL` |
| Current Path | `customer/integrations/vault/engines/vault.py` |
| Required Path | `internal/platform/vault/engines/vault.py` |

---

## 6. LOGS DOMAIN (20 files) - CLEAN

```
logs/
├── __init__.py
├── facades/
│   ├── __init__.py
│   ├── logs_facade.py           # AUDIENCE: CUSTOMER
│   ├── evidence_facade.py       # L4 Domain Engine
│   └── trace_facade.py          # L4 Domain Engine
├── engines/
│   ├── __init__.py
│   ├── audit_evidence.py        # L4 Domain Engine
│   ├── certificate.py           # (no header)
│   ├── completeness_checker.py  # L4 Domain Engine
│   ├── durability.py            # L4 Domain Engine
│   ├── evidence_report.py       # (no header)
│   ├── export_bundle_service.py # L4 Domain Engine
│   ├── logs_read_service.py     # L4 Domain Engine
│   ├── pdf_renderer.py          # L4 Domain Engine
│   ├── reconciler.py            # L4 Domain Engine
│   ├── replay_determinism.py    # (no header)
│   └── store.py                 # L4 Domain Engine
├── schemas/
│   └── models.py                # Schema
└── drivers/
    └── __init__.py              # Empty
```

**Purpose:** Logs, traces, evidence, audit, compliance exports

---

## 7. OVERVIEW DOMAIN (6 files) - CLEAN

```
overview/
├── __init__.py
├── facades/
│   ├── __init__.py
│   └── overview_facade.py       # AUDIENCE: CUSTOMER
├── engines/
│   └── __init__.py              # Empty
├── drivers/
│   └── __init__.py              # Empty
└── schemas/
    └── __init__.py              # Empty
```

**Purpose:** Overview/dashboard aggregation for customer console

---

## 8. CLEANUP ACTIONS REQUIRED

### 8.1 Move server_registry.py

**From:** `customer/integrations/L5_engines/server_registry.py`
**To:** `internal/platform/mcp/engines/server_registry.py`

### 8.2 Move vault.py

**From:** `customer/integrations/vault/engines/vault.py`
**To:** `internal/platform/vault/engines/vault.py`

---

## 9. DECISION: DEFER MOVES

**Rationale:** These two files are deep in subdirectories with existing callers. Moving them requires:
1. Creating new directory structures
2. Moving files
3. Updating all callers (Phase 5 work)

**Recommendation:** Document violations and defer to Phase 5 (Wire Imports) when all import paths will be updated systematically.

---

## 10. TOTAL VIOLATION COUNT ACROSS ALL DOMAINS

| Domain | Violation | Status |
|--------|-----------|--------|
| policies | policy_driver.py | **MOVED** |
| policies | KillSwitch/facade.py | **DELETED** (duplicate) |
| account | iam_service.py | **MOVED** |
| integrations | server_registry.py | DEFERRED |
| integrations | vault.py | DEFERRED |

**Completed:** 3 actions
**Deferred:** 2 actions
