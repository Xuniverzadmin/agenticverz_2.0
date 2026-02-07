# HOC Spine Import Matrix — CUS Domains

**Scope:** `backend/app/hoc/cus/{domain}/{L5_engines|L5_schemas|L6_drivers}/*.py`
**Date:** 2026-02-07

This is a *line-level* evidence inventory of imports **from** `app.hoc.cus.hoc_spine.*` within the canonical 10 CUS domains.

---

## Canonical Domains (10)

`overview`, `activity`, `incidents`, `policies`, `controls`, `logs`, `analytics`, `integrations`, `api_keys`, `account`

---

## Summary (Files With hoc_spine Imports)

| Domain | Files with hoc_spine imports |
|--------|------------------------------:|
| `overview` | 2 |
| `activity` | 5 |
| `incidents` | 6 |
| `policies` | 8 |
| `controls` | 5 |
| `logs` | 4 |
| `analytics` | 7 |
| `integrations` | 2 |
| `api_keys` | 1 |
| `account` | 3 |

**Domains with zero hoc_spine imports (GAP):** (none)

Policy: Canonical 10 CUS domains are non-optional. Zero imports is a **gap** that must be designed and implemented, not an exemption.

---

## Import Lines (by Domain / Layer / Component)

| Domain | Layer | hoc_spine component | File | Line | Import |
|--------|-------|---------------------|------|-----:|--------|
| `account` | `L5_engines` | `services` | `L5_engines/tenant_engine.py` | 49 | `app.hoc.cus.hoc_spine.services.time` |
| `account` | `L6_drivers` | `services` | `L6_drivers/tenant_driver.py` | 53 | `app.hoc.cus.hoc_spine.services.time` |
| `account` | `L6_drivers` | `services` | `L6_drivers/user_write_driver.py` | 46 | `app.hoc.cus.hoc_spine.services.time` |
| `activity` | `L5_engines` | `services` | `L5_engines/attention_ranking_engine.py` | 25 | `app.hoc.cus.hoc_spine.services.time` |
| `activity` | `L5_engines` | `services` | `L5_engines/cost_analysis_engine.py` | 25 | `app.hoc.cus.hoc_spine.services.time` |
| `activity` | `L5_engines` | `services` | `L5_engines/pattern_detection_engine.py` | 25 | `app.hoc.cus.hoc_spine.services.time` |
| `activity` | `L5_engines` | `services` | `L5_engines/signal_feedback_engine.py` | 25 | `app.hoc.cus.hoc_spine.services.time` |
| `activity` | `L6_drivers` | `schemas` | `L6_drivers/__init__.py` | 17 | `app.hoc.cus.hoc_spine.schemas.threshold_types` |
| `analytics` | `L5_engines` | `schemas` | `L5_engines/cost_anomaly_detector_engine.py` | 974 | `app.hoc.cus.hoc_spine.schemas.anomaly_types` |
| `analytics` | `L5_engines` | `services` | `L5_engines/config_engine.py` | 34 | `app.hoc.cus.hoc_spine.services.costsim_config` |
| `analytics` | `L5_engines` | `services` | `L5_engines/metrics_engine.py` | 34 | `app.hoc.cus.hoc_spine.services.costsim_metrics` |
| `analytics` | `L5_engines` | `services` | `L5_engines/pattern_detection_engine.py` | 54 | `app.hoc.cus.hoc_spine.services.time` |
| `analytics` | `L5_engines` | `services` | `L5_engines/prediction_engine.py` | 65 | `app.hoc.cus.hoc_spine.services.time` |
| `analytics` | `L6_drivers` | `drivers` | `L6_drivers/__init__.py` | 17 | `app.hoc.cus.hoc_spine.drivers.alert_driver` |
| `analytics` | `L6_drivers` | `services` | `L6_drivers/cost_write_driver.py` | 50 | `app.hoc.cus.hoc_spine.services.time` |
| `api_keys` | `L5_engines` | `services` | `L5_engines/keys_engine.py` | 54 | `app.hoc.cus.hoc_spine.services.time` |
| `controls` | `L6_drivers` | `drivers` | `L6_drivers/override_driver.py` | 43 | `app.hoc.cus.hoc_spine.drivers.cross_domain` |
| `controls` | `L6_drivers` | `schemas` | `L6_drivers/threshold_driver.py` | 67 | `app.hoc.cus.hoc_spine.schemas.threshold_types` |
| `controls` | `L6_drivers` | `services` | `L6_drivers/circuit_breaker_async_driver.py` | 79 | `app.hoc.cus.hoc_spine.services.costsim_config` |
| `controls` | `L6_drivers` | `services` | `L6_drivers/circuit_breaker_async_driver.py` | 80 | `app.hoc.cus.hoc_spine.services.costsim_metrics` |
| `controls` | `L6_drivers` | `services` | `L6_drivers/circuit_breaker_driver.py` | 84 | `app.hoc.cus.hoc_spine.services.costsim_config` |
| `controls` | `L6_drivers` | `services` | `L6_drivers/limits_read_driver.py` | 29 | `app.hoc.cus.hoc_spine.services.time` |
| `controls` | `L6_drivers` | `services` | `L6_drivers/override_driver.py` | 42 | `app.hoc.cus.hoc_spine.services.time` |
| `incidents` | `L5_engines` | `schemas` | `L5_engines/anomaly_bridge.py` | 64 | `app.hoc.cus.hoc_spine.schemas.anomaly_types` |
| `incidents` | `L5_engines` | `services` | `L5_engines/incident_engine.py` | 75 | `app.hoc.cus.hoc_spine.services.time` |
| `incidents` | `L5_engines` | `services` | `L5_engines/incident_pattern_engine.py` | 65 | `app.hoc.cus.hoc_spine.services.time` |
| `incidents` | `L5_engines` | `services` | `L5_engines/recurrence_analysis_engine.py` | 44 | `app.hoc.cus.hoc_spine.services.time` |
| `incidents` | `L6_drivers` | `schemas` | `L6_drivers/export_bundle_driver.py` | 59 | `app.hoc.cus.hoc_spine.schemas.protocols` |
| `incidents` | `L6_drivers` | `schemas` | `L6_drivers/incident_driver.py` | 214 | `app.hoc.cus.hoc_spine.schemas.rac_models` |
| `incidents` | `L6_drivers` | `services` | `L6_drivers/incident_driver.py` | 215 | `app.hoc.cus.hoc_spine.services.audit_store` |
| `integrations` | `L5_engines` | `schemas` | `L5_engines/mcp_tool_invocation_engine.py` | 63 | `app.hoc.cus.hoc_spine.schemas.protocols` |
| `integrations` | `L5_engines` | `services` | `L5_engines/cus_health_engine.py` | 64 | `app.hoc.cus.hoc_spine.services.cus_credential_engine` |
| `logs` | `L5_engines` | `schemas` | `L5_engines/audit_reconciler.py` | 50 | `app.hoc.cus.hoc_spine.schemas.rac_models` |
| `logs` | `L5_engines` | `schemas` | `L5_engines/trace_facade.py` | 240 | `app.hoc.cus.hoc_spine.schemas.rac_models` |
| `logs` | `L5_engines` | `services` | `L5_engines/audit_reconciler.py` | 58 | `app.hoc.cus.hoc_spine.services.audit_store` |
| `logs` | `L5_engines` | `services` | `L5_engines/cost_intelligence_engine.py` | 45 | `app.hoc.cus.hoc_spine.services.time` |
| `logs` | `L5_engines` | `services` | `L5_engines/mapper.py` | 33 | `app.hoc.cus.hoc_spine.services.time` |
| `logs` | `L5_engines` | `services` | `L5_engines/mapper.py` | 35 | `app.hoc.cus.hoc_spine.services.control_registry` |
| `logs` | `L5_engines` | `services` | `L5_engines/trace_facade.py` | 241 | `app.hoc.cus.hoc_spine.services.audit_store` |
| `overview` | `L5_engines` | `services` | `L5_engines/overview_facade.py` | 67 | `app.hoc.cus.hoc_spine.services.time` |
| `overview` | `L6_drivers` | `services` | `L6_drivers/overview_facade_driver.py` | 46 | `app.hoc.cus.hoc_spine.services.time` |
| `policies` | `L5_engines` | `drivers` | `L5_engines/policy_limits_engine.py` | 57 | `app.hoc.cus.hoc_spine.drivers.cross_domain` |
| `policies` | `L5_engines` | `drivers` | `L5_engines/policy_rules_engine.py` | 58 | `app.hoc.cus.hoc_spine.drivers.cross_domain` |
| `policies` | `L5_engines` | `services` | `L5_engines/lessons_engine.py` | 62 | `app.hoc.cus.hoc_spine.services.time` |
| `policies` | `L5_engines` | `services` | `L5_engines/policy_limits_engine.py` | 56 | `app.hoc.cus.hoc_spine.services.time` |
| `policies` | `L5_engines` | `services` | `L5_engines/policy_proposal_engine.py` | 39 | `app.hoc.cus.hoc_spine.services.time` |
| `policies` | `L5_engines` | `services` | `L5_engines/policy_rules_engine.py` | 57 | `app.hoc.cus.hoc_spine.services.time` |
| `policies` | `L5_engines` | `utilities` | `L5_engines/recovery_evaluation_engine.py` | 57 | `app.hoc.cus.hoc_spine.utilities.recovery_decisions` |
| `policies` | `L6_drivers` | `services` | `L6_drivers/policy_proposal_write_driver.py` | 31 | `app.hoc.cus.hoc_spine.services.time` |
| `policies` | `L6_drivers` | `services` | `L6_drivers/policy_rules_read_driver.py` | 30 | `app.hoc.cus.hoc_spine.services.time` |
| `policies` | `L6_drivers` | `services` | `L6_drivers/proposals_read_driver.py` | 34 | `app.hoc.cus.hoc_spine.services.time` |

---

## Sanity Checks (Evidence)

- L5_engines imports from hoc_spine `orchestrator`/`authority`/`consequences`: 0
- L6_drivers imports from hoc_spine `orchestrator`/`authority`/`consequences`: 0
