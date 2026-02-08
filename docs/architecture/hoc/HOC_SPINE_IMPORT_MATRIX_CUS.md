# HOC Spine Import Matrix — CUS Domains

**Scope:** `backend/app/hoc/cus/{domain}/{L5_engines|L5_schemas|L6_drivers}/*.py`
**Date:** 2026-02-08

This is a line-level evidence inventory of imports **from** `app.hoc.cus.hoc_spine.*` within the canonical 10 CUS domains.

---

## Canonical Domains (10)

`overview`, `activity`, `incidents`, `policies`, `controls`, `logs`, `analytics`, `integrations`, `api_keys`, `account`

---

## Summary (Files With hoc_spine Imports)

| Domain | Files with hoc_spine imports |
|--------|------------------------------:|
| `overview` | 1 |
| `activity` | 4 |
| `incidents` | 6 |
| `policies` | 5 |
| `controls` | 0 |
| `logs` | 4 |
| `analytics` | 6 |
| `integrations` | 2 |
| `api_keys` | 1 |
| `account` | 1 |

---

## Import Lines (by Domain / Layer / Component)

| Domain | Layer | hoc_spine component | File | Line | Import |
|--------|-------|---------------------|------|-----:|--------|
| `account` | `L5_engines` | `services` | `L5_engines/tenant_engine.py` | 50 | `app.hoc.cus.hoc_spine.services.time` |
| `activity` | `L5_engines` | `services` | `L5_engines/attention_ranking.py` | 28 | `app.hoc.cus.hoc_spine.services.time` |
| `activity` | `L5_engines` | `services` | `L5_engines/cost_analysis.py` | 28 | `app.hoc.cus.hoc_spine.services.time` |
| `activity` | `L5_engines` | `services` | `L5_engines/pattern_detection.py` | 28 | `app.hoc.cus.hoc_spine.services.time` |
| `activity` | `L5_engines` | `services` | `L5_engines/signal_feedback_engine.py` | 26 | `app.hoc.cus.hoc_spine.services.time` |
| `analytics` | `L5_engines` | `services` | `L5_engines/canary_engine.py` | 53 | `app.hoc.cus.hoc_spine.services.cross_domain_gateway` |
| `analytics` | `L5_engines` | `services` | `L5_engines/canary_engine.py` | 54 | `app.hoc.cus.hoc_spine.services.cross_domain_gateway` |
| `analytics` | `L5_engines` | `services` | `L5_engines/config_engine.py` | 34 | `app.hoc.cus.hoc_spine.services.costsim_config` |
| `analytics` | `L5_engines` | `services` | `L5_engines/cost_anomaly_detector_engine.py` | 47 | `app.hoc.cus.hoc_spine.services.time` |
| `analytics` | `L5_engines` | `schemas` | `L5_engines/cost_anomaly_detector_engine.py` | 951 | `app.hoc.cus.hoc_spine.schemas.anomaly_types` |
| `analytics` | `L5_engines` | `services` | `L5_engines/metrics_engine.py` | 34 | `app.hoc.cus.hoc_spine.services.costsim_metrics` |
| `analytics` | `L5_engines` | `services` | `L5_engines/prediction_engine.py` | 66 | `app.hoc.cus.hoc_spine.services.time` |
| `analytics` | `L5_engines` | `services` | `L5_engines/sandbox_engine.py` | 38 | `app.hoc.cus.hoc_spine.services.cross_domain_gateway` |
| `api_keys` | `L5_engines` | `services` | `L5_engines/keys_engine.py` | 55 | `app.hoc.cus.hoc_spine.services.time` |
| `incidents` | `L5_engines` | `schemas` | `L5_engines/anomaly_bridge.py` | 64 | `app.hoc.cus.hoc_spine.schemas.anomaly_types` |
| `incidents` | `L5_engines` | `services` | `L5_engines/incident_engine.py` | 75 | `app.hoc.cus.hoc_spine.services.time` |
| `incidents` | `L5_engines` | `services` | `L5_engines/incident_pattern.py` | 67 | `app.hoc.cus.hoc_spine.services.time` |
| `incidents` | `L5_engines` | `schemas` | `L5_engines/incident_write_engine.py` | 57 | `app.hoc.cus.hoc_spine.schemas.domain_enums` |
| `incidents` | `L5_engines` | `services` | `L5_engines/recurrence_analysis.py` | 47 | `app.hoc.cus.hoc_spine.services.time` |
| `incidents` | `L5_schemas` | `schemas` | `L5_schemas/severity_policy.py` | 24 | `app.hoc.cus.hoc_spine.schemas.domain_enums` |
| `integrations` | `L5_engines` | `services` | `L5_engines/cus_health_engine.py` | 62 | `app.hoc.cus.hoc_spine.services.cus_credential_engine` |
| `integrations` | `L5_engines` | `schemas` | `L5_engines/mcp_tool_invocation_engine.py` | 63 | `app.hoc.cus.hoc_spine.schemas.protocols` |
| `logs` | `L5_engines` | `schemas` | `L5_engines/audit_ledger_engine.py` | 44 | `app.hoc.cus.hoc_spine.schemas.domain_enums` |
| `logs` | `L5_engines` | `schemas` | `L5_engines/audit_reconciler.py` | 50 | `app.hoc.cus.hoc_spine.schemas.rac_models` |
| `logs` | `L5_engines` | `services` | `L5_engines/audit_reconciler.py` | 58 | `app.hoc.cus.hoc_spine.services.audit_store` |
| `logs` | `L5_engines` | `services` | `L5_engines/cost_intelligence_engine.py` | 45 | `app.hoc.cus.hoc_spine.services.time` |
| `logs` | `L5_engines` | `services` | `L5_engines/mapper.py` | 34 | `app.hoc.cus.hoc_spine.services.time` |
| `logs` | `L5_engines` | `services` | `L5_engines/mapper.py` | 35 | `app.hoc.cus.hoc_spine.services.control_registry` |
| `overview` | `L5_engines` | `services` | `L5_engines/overview_facade.py` | 68 | `app.hoc.cus.hoc_spine.services.time` |
| `policies` | `L5_engines` | `services` | `L5_engines/lessons_engine.py` | 63 | `app.hoc.cus.hoc_spine.services.time` |
| `policies` | `L5_engines` | `services` | `L5_engines/policy_limits_engine.py` | 58 | `app.hoc.cus.hoc_spine.services.time` |
| `policies` | `L5_engines` | `drivers` | `L5_engines/policy_limits_engine.py` | 59 | `app.hoc.cus.hoc_spine.drivers.cross_domain` |
| `policies` | `L5_engines` | `schemas` | `L5_engines/policy_limits_engine.py` | 66 | `app.hoc.cus.hoc_spine.schemas.domain_enums` |
| `policies` | `L5_engines` | `services` | `L5_engines/policy_proposal_engine.py` | 42 | `app.hoc.cus.hoc_spine.services.time` |
| `policies` | `L5_engines` | `schemas` | `L5_engines/policy_proposal_engine.py` | 51 | `app.hoc.cus.hoc_spine.schemas.domain_enums` |
| `policies` | `L5_engines` | `services` | `L5_engines/policy_rules_engine.py` | 59 | `app.hoc.cus.hoc_spine.services.time` |
| `policies` | `L5_engines` | `drivers` | `L5_engines/policy_rules_engine.py` | 60 | `app.hoc.cus.hoc_spine.drivers.cross_domain` |
| `policies` | `L5_engines` | `schemas` | `L5_engines/policy_rules_engine.py` | 66 | `app.hoc.cus.hoc_spine.schemas.domain_enums` |
| `policies` | `L5_engines` | `utilities` | `L5_engines/recovery_evaluation_engine.py` | 57 | `app.hoc.cus.hoc_spine.utilities.recovery_decisions` |
| `policies` | `L5_engines` | `services` | `L5_engines/recovery_evaluation_engine.py` | 63 | `app.hoc.cus.hoc_spine.services.cross_domain_gateway` |

---

## Sanity Checks (Evidence)

- L6_drivers imports from hoc_spine `orchestrator`/`authority`/`consequences`: 0
- L6_drivers imports from hoc_spine (any): 0 (strict T0 mode)
