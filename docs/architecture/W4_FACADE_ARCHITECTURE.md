# W4 Facade Architecture Plan

**Status:** IN PROGRESS
**Date:** 2026-01-21
**Reference:** GAP_WIRING_LEDGER_V1.md, GAP_IMPLEMENTATION_PLAN_V2.md

---

## Executive Summary

This document maps W4 gaps (GAP-090 to GAP-136) to L4 Service Facades and L2 API routes following the established facade architecture pattern.

**Architecture Principle:** All domain operations flow through L4 facades. L2 APIs are thin projection layers that call L4 facades.

---

## Existing Facades (Reference)

### L4 Service Facades (5 Total)

| Facade | Location | Domain | Status |
|--------|----------|--------|--------|
| IncidentFacade | `app/services/incidents/facade.py` | Incidents | ✅ Exists |
| PolicyFacade | `app/services/policy/facade.py` | Policies | ✅ Exists |
| OpsFacade | `app/services/ops/facade.py` | Ops | ✅ Exists |
| RunGovernanceFacade | `app/services/governance/run_governance_facade.py` | Governance | ✅ Exists |
| TraceFacade | `app/services/observability/trace_facade.py` | Traces | ✅ Exists |

### L2 API Facades (8 Total)

| API | Location | Domain | Status |
|-----|----------|--------|--------|
| Overview | `app/api/overview.py` | Overview | ✅ Exists |
| Activity | `app/api/activity.py` | Activity | ✅ Exists |
| Incidents | `app/api/incidents.py` | Incidents | ✅ Exists |
| Logs | `app/api/logs.py` | Logs | ✅ Exists |
| Policies | `app/api/policies.py` | Policies | ✅ Exists |
| Connectivity | `app/api/connectivity.py` | Connectivity | ✅ Exists |
| Accounts | `app/api/aos_accounts.py` | Accounts | ✅ Exists |
| Analytics | `app/api/analytics.py` | Analytics | ✅ Exists |

---

## W4 Domain → Facade Mapping

### Domain 1: Governance (CRITICAL)

**L4 Facade:** `GovernanceFacade` (NEW - extends RunGovernanceFacade)
**Location:** `app/services/governance/facade.py`
**L2 API:** `app/api/governance.py` → `/api/v1/governance/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-090 | Kill Switch API | `toggle_kill_switch()` | `POST /api/v1/governance/kill-switch` |
| GAP-091 | Degraded Mode API | `set_governance_mode()` | `POST /api/v1/governance/mode` |
| GAP-092 | Conflict Resolution API | `resolve_conflict()` | `POST /api/v1/governance/resolve-conflict` |
| GAP-095 | Boot Status API | `get_boot_status()` | `GET /api/v1/governance/boot-status` |
| GAP-096 | SDK Governance | N/A | SDK client wires to above endpoints |

**L4 Services Wrapped:**
- `runtime_switch.py` (GAP-069, GAP-070)
- `ConflictResolver` (GAP-068)
- `BootGuard` (GAP-067)

---

### Domain 2: Connectors

**L4 Facade:** `ConnectorsFacade` (NEW)
**Location:** `app/services/connectors/facade.py`
**L2 API:** `app/api/connectors.py` → `/api/v1/connectors/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-093 | Connector Registry API | `list_connectors()`, `register_connector()`, `test_connector()` | `GET/POST /api/v1/connectors` |
| GAP-097 | SDK Connector | N/A | SDK client wires to above endpoints |

**L4 Services Wrapped:**
- `HTTPConnector` (GAP-059)
- `SQLConnector` (GAP-060)
- `MCPConnector` (GAP-063)

---

### Domain 3: Retrieval

**L4 Facade:** `RetrievalFacade` (NEW)
**Location:** `app/services/retrieval/facade.py`
**L2 API:** `app/api/retrieval.py` → `/api/v1/retrieval/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-094 | Retrieval Mediator API | `execute_retrieval()` | `POST /api/v1/retrieval/execute` |
| GAP-098 | SDK Retrieval | N/A | SDK client wires to above endpoints |

**L4 Services Wrapped:**
- `RetrievalMediator` (GAP-065)

---

### Domain 4: Detection

**L4 Facade:** `DetectionFacade` (NEW)
**Location:** `app/services/detection/facade.py`
**L2 API:** `app/api/detection.py` → `/api/v1/detection/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-102 | Hallucination Check API | `check_hallucination()` | `POST /api/v1/detection/hallucination` |
| GAP-108 | SDK Detection | N/A | SDK client wires to above endpoints |

**L4 Services Wrapped:**
- `HallucinationDetector` (GAP-023)

---

### Domain 5: Compliance

**L4 Facade:** `ComplianceFacade` (NEW)
**Location:** `app/services/compliance/facade.py`
**L2 API:** `app/api/compliance.py` → `/api/v1/compliance/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-103 | SOC2 Mapping API | `get_soc2_controls()` | `GET /api/v1/compliance/soc2-controls` |
| GAP-107 | SDK Compliance | N/A | SDK client wires to above endpoints |

**L4 Services Wrapped:**
- `SOC2Mapper` (GAP-025)

---

### Domain 6: Evidence

**L4 Facade:** `EvidenceFacade` (NEW)
**Location:** `app/services/evidence/facade.py`
**L2 API:** `app/api/evidence.py` → `/api/v1/evidence/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-104 | Override Authority API | `request_override()` | `POST /api/v1/governance/override` |
| GAP-105 | Evidence Export API | `export_evidence()` | `GET /api/v1/exports/evidence/{run_id}` |
| GAP-106 | SDK Evidence | N/A | SDK client wires to above endpoints |

**L4 Services Wrapped:**
- `OverrideAuthority` (GAP-034)
- `EvidenceExporter` (GAP-027, GAP-058)

---

### Domain 7: Notifications

**L4 Facade:** `NotificationsFacade` (NEW)
**Location:** `app/services/notifications/facade.py`
**L2 API:** `app/api/notifications.py` → `/api/v1/notifications/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-109 | Notification Channels API | `list_channels()`, `create_channel()` | `GET/POST /api/v1/notifications/channels` |
| GAP-115 | SDK Notifications | N/A | SDK client wires to above endpoints |

**L4 Services Wrapped:**
- `NotifyChannels` (GAP-036)
- `AlertLogLinker` (GAP-037)

---

### Domain 8: Alerts

**L4 Facade:** `AlertsFacade` (NEW)
**Location:** `app/services/alerts/facade.py`
**L2 API:** `app/api/alerts.py` → `/api/v1/alerts/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-110 | Alert Log Link API | `get_alert_logs()` | `GET /api/v1/alerts/{id}/logs` |
| GAP-111 | Alert Fatigue API | `get_fatigue_status()` | `GET /api/v1/alerts/fatigue-status` |
| GAP-124 | Alert Rules API | `list_rules()`, `create_rule()` | `GET/POST /api/v1/alerts/rules` |
| GAP-116 | SDK Alerts | N/A | SDK client wires to above endpoints |

**L4 Services Wrapped:**
- `AlertLogLinker` (GAP-037)
- `AlertFatigue` (GAP-038)
- `AlertRules` (GAP-057)

---

### Domain 9: Scheduler

**L4 Facade:** `SchedulerFacade` (NEW)
**Location:** `app/services/scheduler/facade.py`
**L2 API:** `app/api/scheduler.py` → `/api/v1/scheduler/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-112 | Job Scheduler API | `list_jobs()`, `create_job()` | `GET/POST /api/v1/scheduler/jobs` |
| GAP-117 | SDK Scheduler | N/A | SDK client wires to above endpoints |

**L4 Services Wrapped:**
- `JobScheduler` (GAP-039)

---

### Domain 10: DataSources

**L4 Facade:** `DataSourcesFacade` (NEW)
**Location:** `app/services/datasources/facade.py`
**L2 API:** `app/api/datasources.py` → `/api/v1/datasources/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-113 | Customer Data Source API | `list_sources()`, `create_source()` | `GET/POST /api/v1/datasources` |
| GAP-118 | SDK DataSources | N/A | SDK client wires to above endpoints |

**L4 Services Wrapped:**
- `CustomerDataSource` (GAP-040)

---

### Domain 11: Policy Extensions (Extend Existing)

**L4 Facade:** `PolicyFacade` (EXISTS - extend)
**Location:** `app/services/policy/facade.py`
**L2 API:** `app/api/policies.py` → `/api/v1/policies/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-114 | Policy Snapshot API | `list_snapshots()`, `create_snapshot()` | `GET/POST /api/v1/policies/snapshots` |
| GAP-119 | Scope Selector API | `list_scopes()`, `create_scope()` | `GET/POST /api/v1/policies/scopes` |
| GAP-125 | Policy Lifecycle API | `transition_state()` | `POST /api/v1/policies/{id}/lifecycle` |
| GAP-126 | SDK Scopes | N/A | SDK client |
| GAP-130 | SDK PolicyLifecycle | N/A | SDK client |

**L4 Services Wrapped:**
- `PolicySnapshot` (GAP-044)
- `PolicyScope` (GAP-052)
- `PolicyLifecycle` (GAP-064)

---

### Domain 12: Monitors

**L4 Facade:** `MonitorsFacade` (NEW)
**Location:** `app/services/monitors/facade.py`
**L2 API:** `app/api/monitors.py` → `/api/v1/monitors/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-120 | Usage Monitor API | `get_usage()` | `GET /api/v1/monitors/usage` |
| GAP-121 | Health Monitor API | `get_health()` | `GET /api/v1/monitors/health` |
| GAP-127 | SDK Monitors | N/A | SDK client wires to above endpoints |

**L4 Services Wrapped:**
- `UsageMonitor` (GAP-053)
- `HealthMonitor` (GAP-054)

---

### Domain 13: Limits

**L4 Facade:** `LimitsFacade` (NEW)
**Location:** `app/services/limits/facade.py`
**L2 API:** `app/api/limits.py` → `/api/v1/limits/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-122 | Limit Enforcer API | `list_limits()`, `create_limit()` | `GET/POST /api/v1/limits` |
| GAP-128 | SDK Limits | N/A | SDK client wires to above endpoints |

**L4 Services Wrapped:**
- `LimitEnforcer` (GAP-055)

---

### Domain 14: Controls

**L4 Facade:** `ControlsFacade` (NEW)
**Location:** `app/services/controls/facade.py`
**L2 API:** `app/api/controls.py` → `/api/v1/controls/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-123 | Control Actions API | `execute_action()` | `POST /api/v1/controls/execute` |
| GAP-129 | SDK Controls | N/A | SDK client wires to above endpoints |

**L4 Services Wrapped:**
- `ControlActions` (GAP-056)

---

### Domain 15: Lifecycle

**L4 Facade:** `LifecycleFacade` (NEW)
**Location:** `app/services/lifecycle/facade.py`
**L2 API:** `app/api/lifecycle.py` → `/api/v1/lifecycle/*`

| Gap ID | Name | Facade Method | API Endpoint |
|--------|------|---------------|--------------|
| GAP-131 | Lifecycle State API | `get_state()` | `GET /api/v1/lifecycle/{plane_id}/state` |
| GAP-132 | Lifecycle Transition API | `request_transition()` | `POST /api/v1/lifecycle/{plane_id}/transition` |
| GAP-133 | Lifecycle Audit API | `get_audit()` | `GET /api/v1/lifecycle/{plane_id}/audit` |
| GAP-134 | Lifecycle Stages API | `get_stages()` | `GET /api/v1/lifecycle/{plane_id}/stages` |
| GAP-135 | SDK Lifecycle L2 Binding | N/A | SDK client wires to L2 routes |
| GAP-136 | SDK Lifecycle HTTP Client | N/A | SDK HTTP transport |

**L4 Services Wrapped:**
- `LifecycleManager` (GAP-086)
- `StateMachine` (GAP-089)
- `AuditEvents` (GAP-088)
- Stage handlers (GAP-071 to GAP-082)

---

## Implementation Order (Critical Path)

### Phase 1: Governance Core (CRITICAL)
1. GovernanceFacade + governance.py API (GAP-090, 091, 092, 095)
2. SDK Governance namespace (GAP-096)

### Phase 2: Lifecycle Core (CRITICAL)
3. LifecycleFacade + lifecycle.py API (GAP-131, 132, 133, 134)
4. SDK Lifecycle binding (GAP-135, 136)

### Phase 3: Connectors & Retrieval (HIGH)
5. ConnectorsFacade + connectors.py API (GAP-093)
6. RetrievalFacade + retrieval.py API (GAP-094)
7. SDK Connectors + Retrieval (GAP-097, 098)

### Phase 4: Detection & Compliance (HIGH)
8. DetectionFacade + detection.py API (GAP-102)
9. ComplianceFacade + compliance.py API (GAP-103)
10. EvidenceFacade + evidence.py API (GAP-104, 105)
11. SDK Detection, Compliance, Evidence (GAP-106, 107, 108)

### Phase 5: Notifications & Alerts (HIGH)
12. NotificationsFacade + notifications.py API (GAP-109)
13. AlertsFacade + alerts.py API (GAP-110, 111, 124)
14. SDK Notifications, Alerts (GAP-115, 116)

### Phase 6: Scheduler & DataSources (HIGH)
15. SchedulerFacade + scheduler.py API (GAP-112)
16. DataSourcesFacade + datasources.py API (GAP-113)
17. SDK Scheduler, DataSources (GAP-117, 118)

### Phase 7: Monitors, Limits, Controls (MEDIUM)
18. MonitorsFacade + monitors.py API (GAP-120, 121)
19. LimitsFacade + limits.py API (GAP-122)
20. ControlsFacade + controls.py API (GAP-123)
21. SDK Monitors, Limits, Controls (GAP-127, 128, 129)

### Phase 8: Policy Extensions (HIGH)
22. Extend PolicyFacade (GAP-114, 119, 125)
23. SDK Scopes, PolicyLifecycle (GAP-126, 130)

---

## Summary

| New L4 Facades | Count |
|----------------|-------|
| GovernanceFacade | 1 |
| ConnectorsFacade | 1 |
| RetrievalFacade | 1 |
| DetectionFacade | 1 |
| ComplianceFacade | 1 |
| EvidenceFacade | 1 |
| NotificationsFacade | 1 |
| AlertsFacade | 1 |
| SchedulerFacade | 1 |
| DataSourcesFacade | 1 |
| MonitorsFacade | 1 |
| LimitsFacade | 1 |
| ControlsFacade | 1 |
| LifecycleFacade | 1 |
| **TOTAL NEW** | **14** |

| Extended L4 Facades | Count |
|---------------------|-------|
| PolicyFacade (existing) | 1 |

| New L2 API Routes | Count |
|-------------------|-------|
| governance.py | 1 |
| connectors.py | 1 |
| retrieval.py | 1 |
| detection.py | 1 |
| compliance.py | 1 |
| evidence.py | 1 |
| notifications.py | 1 |
| alerts.py | 1 |
| scheduler.py | 1 |
| datasources.py | 1 |
| monitors.py | 1 |
| limits.py | 1 |
| controls.py | 1 |
| lifecycle.py | 1 |
| **TOTAL NEW** | **14** |

| SDK Namespaces | Count |
|----------------|-------|
| aos_sdk.governance.* | 1 |
| aos_sdk.connectors.* | 1 |
| aos_sdk.retrieval.* | 1 |
| aos_sdk.evidence.* | 1 |
| aos_sdk.compliance.* | 1 |
| aos_sdk.detection.* | 1 |
| aos_sdk.notifications.* | 1 |
| aos_sdk.alerts.* | 1 |
| aos_sdk.scheduler.* | 1 |
| aos_sdk.datasources.* | 1 |
| aos_sdk.scopes.* | 1 |
| aos_sdk.monitors.* | 1 |
| aos_sdk.limits.* | 1 |
| aos_sdk.controls.* | 1 |
| aos_sdk.policy.lifecycle.* | 1 |
| aos_sdk.lifecycle.* | 1 |
| **TOTAL NEW** | **16** |

---

**End of W4 Facade Architecture Plan**
