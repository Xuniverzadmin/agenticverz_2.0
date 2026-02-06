# HOC Spine Import Matrix — CUS Domains

**Scope:** backend/app/hoc/cus/{domain}/{L5_engines|L5_schemas|L6_drivers}/*.py
**Date:** 2026-02-06

**Domains with zero hoc_spine imports (GAP):** api_keys  
**Policy:** Canonical 10 CUS domains are non-optional. Zero imports is a **gap** that must be designed and implemented, not an exemption.

## Import Lines (by Domain / Layer / Category)

| Domain | Layer | Category | File | Line | Import |
|--------|-------|----------|------|------|--------|
| overview | L5_engines | governance | L5_engines/overview_facade.py | 68 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| overview | L6_drivers | governance | L6_drivers/overview_facade_driver.py | 47 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| activity | L5_engines | governance | L5_engines/pattern_detection_engine.py | 26 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| activity | L5_engines | governance | L5_engines/attention_ranking_engine.py | 26 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| activity | L5_engines | governance | L5_engines/signal_feedback_engine.py | 26 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| activity | L5_engines | orchestration_runtime_execution | L5_engines/__init__.py | 33 | `from app.hoc.cus.hoc_spine.orchestrator.run_governance_facade import (` |
| activity | L5_engines | governance | L5_engines/cost_analysis_engine.py | 26 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| activity | L6_drivers | governance | L6_drivers/__init__.py | 17 | `from app.hoc.cus.hoc_spine.schemas.threshold_types import LimitSnapshot  # noqa: F401` |
| incidents | L5_engines | governance | L5_engines/incident_engine.py | 75 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| incidents | L5_engines | governance | L5_engines/anomaly_bridge.py | 64 | `from app.hoc.cus.hoc_spine.schemas.anomaly_types import CostAnomalyFact` |
| incidents | L5_engines | governance | L5_engines/recurrence_analysis_engine.py | 45 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| incidents | L5_engines | governance | L5_engines/incident_pattern_engine.py | 65 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| incidents | L6_drivers | governance | L6_drivers/export_bundle_driver.py | 59 | `from app.hoc.cus.hoc_spine.schemas.protocols import TraceStorePort` |
| policies | L5_engines | orchestration_runtime_execution | L5_engines/eligibility_engine.py | 75 | `from app.hoc.cus.hoc_spine.orchestrator import (` |
| policies | L5_engines | governance | L5_engines/policy_limits_engine.py | 56 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| policies | L5_engines | governance | L5_engines/policy_limits_engine.py | 57 | `from app.hoc.cus.hoc_spine.drivers.cross_domain import generate_uuid` |
| policies | L5_engines | governance | L5_engines/policy_rules_engine.py | 57 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| policies | L5_engines | governance | L5_engines/policy_rules_engine.py | 58 | `from app.hoc.cus.hoc_spine.drivers.cross_domain import generate_uuid` |
| policies | L5_engines | governance | L5_engines/lessons_engine.py | 63 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| policies | L5_engines | governance | L5_engines/recovery_evaluation_engine.py | 57 | `from app.hoc.cus.hoc_spine.utilities.recovery_decisions import (` |
| policies | L5_engines | governance | L5_engines/policy_proposal_engine.py | 40 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| policies | L6_drivers | governance | L6_drivers/policy_rules_read_driver.py | 31 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| policies | L6_drivers | governance | L6_drivers/proposals_read_driver.py | 35 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| policies | L6_drivers | governance | L6_drivers/policy_proposal_write_driver.py | 32 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| controls | L6_drivers | governance | L6_drivers/circuit_breaker_async_driver.py | 79 | `from app.hoc.cus.hoc_spine.services.costsim_config import get_config` |
| controls | L6_drivers | governance | L6_drivers/circuit_breaker_async_driver.py | 80 | `from app.hoc.cus.hoc_spine.services.costsim_metrics import get_metrics` |
| controls | L6_drivers | governance | L6_drivers/override_driver.py | 42 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| controls | L6_drivers | governance | L6_drivers/override_driver.py | 43 | `from app.hoc.cus.hoc_spine.drivers.cross_domain import generate_uuid` |
| controls | L6_drivers | governance | L6_drivers/limits_read_driver.py | 30 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| controls | L6_drivers | governance | L6_drivers/threshold_driver.py | 67 | `from app.hoc.cus.hoc_spine.schemas.threshold_types import LimitSnapshot  # noqa: F401` |
| controls | L6_drivers | governance | L6_drivers/circuit_breaker_driver.py | 84 | `from app.hoc.cus.hoc_spine.services.costsim_config import get_config` |
| logs | L5_engines | governance | L5_engines/mapper.py | 34 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| logs | L5_engines | governance | L5_engines/mapper.py | 35 | `from app.hoc.cus.hoc_spine.services.control_registry import (` |
| logs | L5_engines | governance | L5_engines/audit_reconciler.py | 50 | `from app.hoc.cus.hoc_spine.schemas.rac_models import (` |
| logs | L5_engines | governance | L5_engines/audit_reconciler.py | 58 | `from app.hoc.cus.hoc_spine.services.audit_store import AuditStore, get_audit_store` |
| analytics | L5_engines | governance | L5_engines/pattern_detection_engine.py | 55 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| analytics | L5_engines | governance | L5_engines/prediction_engine.py | 66 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| analytics | L5_engines | governance | L5_engines/metrics_engine.py | 34 | `from app.hoc.cus.hoc_spine.services.costsim_metrics import (` |
| analytics | L5_engines | governance | L5_engines/config_engine.py | 34 | `from app.hoc.cus.hoc_spine.services.costsim_config import (` |
| analytics | L6_drivers | uncategorized | L6_drivers/__init__.py | 18 | `from app.hoc.cus.hoc_spine.drivers.alert_driver import (` |
| analytics | L6_drivers | governance | L6_drivers/cost_write_driver.py | 50 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| integrations | L5_engines | governance | L5_engines/cus_health_engine.py | 64 | `from app.hoc.cus.hoc_spine.services.cus_credential_engine import CusCredentialService` |
| integrations | L5_engines | governance | L5_engines/mcp_tool_invocation_engine.py | 63 | `from app.hoc.cus.hoc_spine.schemas.protocols import MCPAuditEmitterPort` |
| integrations | L5_engines | orchestration_runtime_execution | L5_engines/cost_bridges_engine.py | 50 | `from app.hoc.cus.hoc_spine.orchestrator import create_incident_from_cost_anomaly_sync` |
| account | L5_engines | governance | L5_engines/tenant_engine.py | 50 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| account | L6_drivers | governance | L6_drivers/user_write_driver.py | 47 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
| account | L6_drivers | governance | L6_drivers/tenant_driver.py | 54 | `from app.hoc.cus.hoc_spine.services.time import utc_now` |
