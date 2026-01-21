# Backend-to-Domain Inventory

**Status:** ACTIVE
**Created:** 2026-01-20
**Purpose:** Map backend files, APIs, and routes to Console domains, subdomains, topics, and panels
**Reference:** `CUSTOMER_CONSOLE_V2_CONSTITUTION.md`

---

## Overview

This document provides a complete inventory of backend resources mapped to the AI Governance Console domain hierarchy. Use this as the source of truth for frontend development.

---

## 1. OVERVIEW Domain

### 1.1 Summary → Highlights

**Question:** "Is the system okay right now?"

| Resource Type | Path | Purpose |
|--------------|------|---------|
| **API Router** | `backend/app/api/overview.py` | Unified facade for Overview domain |
| **Route Prefix** | `/api/v1/overview/*` | All Overview endpoints |

**Endpoints:**

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/overview/highlights` | OVR-SUM-HL-O1 | System highlights (activity, incidents, policies snapshot) |
| `GET /api/v1/overview/pulse` | OVR-SUM-HL-O2 | System pulse (3-state: PROTECTED/ATTENTION/ACTION) |
| `GET /api/v1/overview/cost-summary` | OVR-SUM-CI-O1 | Cost summary card |
| `GET /api/v1/overview/recent-activity` | OVR-SUM-HL-O3 | Recent activity items |

### 1.2 Summary → Decisions

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/overview/decisions` | OVR-SUM-DEC-O1 | Pending decisions queue |
| `GET /api/v1/overview/approvals` | OVR-SUM-DEC-O2 | Pending approval items |

**Services:**

| Service | Path | Purpose |
|---------|------|---------|
| `OverviewProjectionService` | `backend/app/services/overview_projection.py` | Aggregate data for Overview |

---

## 2. ACTIVITY Domain

### 2.1 LLM Runs → Live

**Question:** "What is running right now?"

| Resource Type | Path | Purpose |
|--------------|------|---------|
| **API Router** | `backend/app/api/activity.py` | Unified facade for Activity domain |
| **Route Prefix** | `/api/v1/activity/*` | All Activity endpoints |

**Endpoints:**

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/activity/runs/live` | ACT-LLM-LIVE-O1 | Live runs list |
| `GET /api/v1/activity/runs/live/by-dimension` | ACT-LLM-LIVE-O2 | Live runs by dimension |
| `GET /api/v1/activity/runs/live/count` | ACT-LLM-LIVE-O3 | Live run count |
| `GET /api/v1/activity/jobs` | ACT-LLM-LIVE-O4 | Worker jobs list |
| `GET /api/v1/activity/health` | ACT-LLM-LIVE-O5 | Worker health status |

### 2.2 LLM Runs → Completed

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/activity/runs/completed` | ACT-LLM-COMP-O1 | Completed runs list |
| `GET /api/v1/activity/runs/completed/by-dimension` | ACT-LLM-COMP-O2 | Completed runs by dimension |
| `GET /api/v1/activity/runs/completed/summary` | ACT-LLM-COMP-O3 | Completion summary stats |
| `GET /api/v1/activity/runs/{run_id}` | ACT-LLM-COMP-O4 | Run detail |
| `GET /api/v1/activity/runs/{run_id}/traces` | ACT-LLM-COMP-O5 | Run traces |

### 2.3 LLM Runs → Signals

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/activity/signals` | ACT-LLM-SIG-O1 | Risk signals list |
| `GET /api/v1/activity/predictions` | ACT-LLM-SIG-O2 | Predictions list |
| `GET /api/v1/activity/predictions/summary` | ACT-LLM-SIG-O3 | Prediction summary |
| `GET /api/v1/activity/anomalies` | ACT-LLM-SIG-O4 | Anomaly detection results |

**Services:**

| Service | Path | Purpose |
|---------|------|---------|
| `ActivityProjectionService` | `backend/app/services/activity_projection.py` | Activity aggregation |
| `RunService` | `backend/app/services/run_service.py` | Run lifecycle |
| `SignalService` | `backend/app/signals/service.py` | Signal detection |

**Database Tables:**

| Table | Purpose |
|-------|---------|
| `runs` | LLM run records |
| `aos_traces` | Execution traces |
| `aos_trace_steps` | Trace steps |
| `predictions` | Prediction events |

---

## 3. INCIDENTS Domain

### 3.1 Events → Active

**Question:** "What needs attention?"

| Resource Type | Path | Purpose |
|--------------|------|---------|
| **API Router** | `backend/app/api/incidents.py` | Unified facade for Incidents domain |
| **Route Prefix** | `/api/v1/incidents/*` | All Incidents endpoints |

**Endpoints:**

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/incidents/active` | INC-EV-ACT-O1 | Active incidents list |
| `GET /api/v1/incidents/active/by-severity` | INC-EV-ACT-O2 | Active by severity |
| `GET /api/v1/incidents/{id}` | INC-EV-ACT-O3 | Incident detail |
| `GET /api/v1/incidents/{id}/timeline` | INC-EV-ACT-O4 | Incident timeline |
| `POST /api/v1/incidents/{id}/acknowledge` | - | Acknowledge incident |

### 3.2 Events → Resolved

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/incidents/resolved` | INC-EV-RES-O1 | Resolved incidents list |
| `GET /api/v1/incidents/resolved/{id}` | INC-EV-RES-O2 | Resolution details |
| `GET /api/v1/incidents/resolved/stats` | INC-EV-RES-O3 | Resolution statistics |

### 3.3 Events → Historical

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/incidents/historical` | INC-EV-HIST-O1 | Historical incidents |
| `GET /api/v1/incidents/trends` | INC-EV-HIST-O2 | Incident trends |
| `GET /api/v1/incidents/patterns` | INC-EV-HIST-O3 | Incident patterns |

**Services:**

| Service | Path | Purpose |
|---------|------|---------|
| `IncidentService` | `backend/app/services/incident_service.py` | Incident lifecycle |
| `IncidentEngine` | `backend/app/engines/incident_engine.py` | Incident detection |

**Database Tables:**

| Table | Purpose |
|-------|---------|
| `incidents` | Incident records |
| `incident_events` | Incident timeline events |

---

## 4. POLICIES Domain

### 4.1 Governance → Active

**Question:** "What rules are enforced?"

| Resource Type | Path | Purpose |
|--------------|------|---------|
| **API Router** | `backend/app/api/policies.py` | Unified facade for Policies domain |
| **Route Prefix** | `/api/v1/policies/*` | All Policies endpoints |

**Endpoints:**

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/policies/active` | POL-GOV-ACT-O1 | Active policies list |
| `GET /api/v1/policies/{id}` | POL-GOV-ACT-O2 | Policy detail |
| `GET /api/v1/policies/by-type` | POL-GOV-ACT-O3 | Policies by type |
| `GET /api/v1/policies/coverage` | POL-GOV-ACT-O4 | Policy coverage stats |

### 4.2 Governance → Lessons

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/policies/lessons` | POL-GOV-LES-O1 | Learned patterns list |
| `GET /api/v1/policies/lessons/{id}` | POL-GOV-LES-O2 | Lesson detail |
| `GET /api/v1/policies/lessons/stats` | POL-GOV-LES-O3 | Learning statistics |
| `GET /api/v1/policy-proposals` | POL-GOV-LES-O4 | Policy proposals |
| `POST /api/v1/policy-proposals/{id}/accept` | - | Accept proposal |
| `POST /api/v1/policy-proposals/{id}/defer` | - | Defer proposal |

### 4.3 Governance → Policy Library

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/policies/library/templates` | POL-GOV-LIB-O1 | Policy templates |
| `GET /api/v1/policies/library/templates/{id}` | POL-GOV-LIB-O2 | Template detail |
| `GET /api/v1/policies/library/ethical` | POL-GOV-LIB-O3 | Ethical constraints |

### 4.4 Limits → Controls

| Resource Type | Path | Purpose |
|--------------|------|---------|
| **API Router** | `backend/app/api/policy_limits_crud.py` | Limits CRUD |
| **Route Prefix** | `/api/v1/policy-limits/*` | Limits endpoints |

**Endpoints:**

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/policy-limits` | POL-LIM-CTR-O1 | Controls list |
| `GET /api/v1/policy-limits/{id}` | POL-LIM-CTR-O2 | Control detail |
| `PUT /api/v1/policy-limits/{id}` | - | Update control |
| `POST /api/v1/limits/simulate` | POL-LIM-CTR-O3 | Simulate limit |

### 4.5 Limits → Violations

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/policies/violations` | POL-LIM-VIO-O1 | Violations list |
| `GET /api/v1/policies/violations/{id}` | POL-LIM-VIO-O2 | Violation detail |
| `GET /api/v1/policies/violations/by-limit` | POL-LIM-VIO-O3 | Violations by limit |

**Services:**

| Service | Path | Purpose |
|---------|------|---------|
| `PolicyService` | `backend/app/services/policy_service.py` | Policy lifecycle |
| `PolicyEngine` | `backend/app/engines/policy_engine.py` | Policy evaluation |
| `LimitService` | `backend/app/services/limit_service.py` | Limit management |

**Database Tables:**

| Table | Purpose |
|-------|---------|
| `policy_rules` | Policy rule definitions |
| `policy_limits` | Limit configurations |
| `policy_proposals` | Policy proposals |
| `limit_violations` | Violation records |

---

## 5. LOGS Domain

### 5.1 Records → LLM Runs

**Question:** "What is the raw truth?"

| Resource Type | Path | Purpose |
|--------------|------|---------|
| **API Router** | `backend/app/api/logs.py` | Unified facade for Logs domain |
| **Route Prefix** | `/api/v1/logs/*` | All Logs endpoints |

**Endpoints:**

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/logs/llm-runs` | LOG-REC-LLM-O1 | LLM run logs |
| `GET /api/v1/logs/llm-runs/{id}` | LOG-REC-LLM-O2 | Run log detail |
| `GET /api/v1/logs/llm-runs/{id}/trace` | LOG-REC-LLM-O3 | Run trace detail |

### 5.2 Records → System Logs

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/logs/system` | LOG-REC-SYS-O1 | System logs summary |
| `GET /api/v1/logs/system/entries` | LOG-REC-SYS-O2 | System log entries |
| `GET /api/v1/logs/system/{id}` | LOG-REC-SYS-O3 | System log detail |

### 5.3 Records → Audit Logs

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/logs/audit` | LOG-REC-AUD-O1 | Audit log list |
| `GET /api/v1/logs/audit/{id}` | LOG-REC-AUD-O2 | Audit event detail |
| `GET /api/v1/logs/audit/by-actor` | LOG-REC-AUD-O3 | Audit by actor |

**Database Tables (IMMUTABLE):**

| Table | Purpose | Triggers |
|-------|---------|----------|
| `llm_run_records` | LLM execution records | `trg_llm_run_records_immutable` |
| `system_records` | Worker events | `trg_system_records_immutable` |
| `audit_ledger` | Governance actions | `trg_audit_ledger_immutable` |

---

## 6. ANALYTICS Domain

### 6.1 Insights → Cost Intelligence

**Question:** "What can we learn about costs?"

| Resource Type | Path | Purpose |
|--------------|------|---------|
| **API Router** | `backend/app/api/analytics.py` | Unified facade for Analytics |
| **Route Prefix** | `/api/v1/analytics/*` | All Analytics endpoints |
| **Secondary Router** | `backend/app/api/cost_intelligence.py` | Cost-specific APIs |

**Endpoints:**

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/analytics/cost/summary` | ANA-INS-CST-O1 | Cost summary |
| `GET /api/v1/analytics/cost/by-model` | ANA-INS-CST-O2 | Cost by model |
| `GET /api/v1/analytics/cost/by-feature` | ANA-INS-CST-O3 | Cost by feature |
| `GET /api/v1/analytics/cost/trend` | ANA-INS-CST-O4 | Cost trend |
| `GET /api/v1/analytics/cost/anomalies` | ANA-INS-CST-O5 | Cost anomalies |
| `GET /api/v1/analytics/cost/forecast` | ANA-INS-CST-O6 | Cost forecast |

### 6.2 Usage Statistics → Policies Usage

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/analytics/policies/usage` | ANA-USG-POL-O1 | Policy usage stats |
| `GET /api/v1/analytics/policies/effectiveness` | ANA-USG-POL-O2 | Policy effectiveness |
| `GET /api/v1/analytics/policies/coverage` | ANA-USG-POL-O3 | Policy coverage |

### 6.3 Usage Statistics → Productivity

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/analytics/productivity/saved-time` | ANA-USG-PRD-O1 | Time saved metrics |
| `GET /api/v1/analytics/productivity/efficiency` | ANA-USG-PRD-O2 | Efficiency gains |
| `GET /api/v1/analytics/productivity/trend` | ANA-USG-PRD-O3 | Productivity trend |

**Services:**

| Service | Path | Purpose |
|---------|------|---------|
| `CostIntelligenceService` | `backend/app/services/cost_intelligence.py` | Cost analytics |
| `AnalyticsService` | `backend/app/services/analytics_service.py` | General analytics |

---

## 7. CONNECTIVITY Domain

### 7.1 Integrations → SDK Integration

**Question:** "How does the system connect?"

| Resource Type | Path | Purpose |
|--------------|------|---------|
| **API Router** | `backend/app/api/connectivity.py` | Unified facade for Connectivity |
| **Route Prefix** | `/api/v1/connectivity/*` | All Connectivity endpoints |
| **Secondary Router** | `backend/app/api/cus_integrations.py` | Customer integrations |

**Endpoints:**

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/connectivity/integrations` | CON-INT-SDK-O1 | Integration status |
| `GET /api/v1/connectivity/integrations/sdk` | CON-INT-SDK-O2 | SDK setup status |
| `GET /api/v1/connectivity/providers` | CON-INT-SDK-O3 | Provider connections |
| `POST /api/v1/customer/integrations/register` | - | Register integration |

### 7.2 API → API Keys

| Resource Type | Path | Purpose |
|--------------|------|---------|
| **Additional Router** | `backend/app/api/guard.py` | Guard endpoints (includes keys) |

**Endpoints:**

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/connectivity/api-keys` | CON-API-KEY-O1 | API keys list |
| `POST /api/v1/connectivity/api-keys` | - | Create API key |
| `DELETE /api/v1/connectivity/api-keys/{id}` | - | Revoke API key |
| `POST /api/v1/connectivity/api-keys/{id}/rotate` | - | Rotate API key |

---

## 8. ACCOUNT Domain

### 8.1 Profile

**Question:** "Who am I?"

| Resource Type | Path | Purpose |
|--------------|------|---------|
| **API Router** | `backend/app/api/accounts.py` | Unified facade for Accounts |
| **Route Prefix** | `/api/v1/accounts/*` | All Account endpoints |

**Endpoints:**

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/accounts/profile` | ACC-PRO-O1 | Organization profile |
| `PUT /api/v1/accounts/profile` | - | Update profile |
| `GET /api/v1/accounts/profile/contacts` | ACC-PRO-O2 | Admin contacts |

### 8.2 Billing

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/accounts/billing/usage` | ACC-BIL-USG-O1 | Usage summary |
| `GET /api/v1/accounts/billing/invoices` | ACC-BIL-INV-O1 | Invoice list |
| `GET /api/v1/accounts/billing/invoices/{id}` | ACC-BIL-INV-O2 | Invoice detail |
| `GET /api/v1/accounts/billing/plan` | ACC-BIL-PLN-O1 | Current plan |

### 8.3 Subuser Management (Admin RBAC)

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/accounts/users` | ACC-USR-O1 | Team members list |
| `POST /api/v1/accounts/users/invite` | - | Invite user |
| `PUT /api/v1/accounts/users/{id}/role` | - | Update role |
| `DELETE /api/v1/accounts/users/{id}` | - | Remove user |
| `GET /api/v1/accounts/invitations` | ACC-USR-O2 | Pending invitations |

### 8.4 Account Management

| Endpoint | Panel ID | Description |
|----------|----------|-------------|
| `GET /api/v1/accounts/support` | ACC-MGT-SUP-O1 | Support contact |
| `POST /api/v1/accounts/support/tickets` | - | Create support ticket |
| `GET /api/v1/accounts/support/tickets` | ACC-MGT-SUP-O2 | Support tickets |

---

## Summary Statistics

| Domain | API File | Endpoints | Tables |
|--------|----------|-----------|--------|
| Overview | `overview.py` | ~5 | - (projection) |
| Activity | `activity.py` | ~19 | `runs`, `aos_traces`, `aos_trace_steps`, `predictions` |
| Incidents | `incidents.py` | ~16 | `incidents`, `incident_events` |
| Policies | `policies.py`, `policy_limits_crud.py`, `policy_rules_crud.py` | ~16 | `policy_rules`, `policy_limits`, `policy_proposals` |
| Logs | `logs.py` | ~19 | `llm_run_records`, `system_records`, `audit_ledger` |
| Analytics | `analytics.py`, `cost_intelligence.py` | ~8 | - (aggregation) |
| Connectivity | `connectivity.py`, `cus_integrations.py` | ~4 | `api_keys`, `integrations` |
| Account | `accounts.py` | ~17 | `tenants`, `tenant_users`, `invitations` |

**Total Endpoints:** ~104
**Total API Files:** 12 primary routers
**Total Tables:** ~15 domain tables

---

## Service Layer Mapping

| Domain | Primary Service | Path |
|--------|-----------------|------|
| Overview | `OverviewProjectionService` | `backend/app/services/overview_projection.py` |
| Activity | `ActivityProjectionService` | `backend/app/services/activity_projection.py` |
| Incidents | `IncidentService` | `backend/app/services/incident_service.py` |
| Policies | `PolicyService` | `backend/app/services/policy_service.py` |
| Logs | `LogsProjectionService` | `backend/app/services/logs_projection.py` |
| Analytics | `AnalyticsService` | `backend/app/services/analytics_service.py` |
| Connectivity | `ConnectivityService` | `backend/app/services/connectivity_service.py` |
| Account | `AccountService` | `backend/app/services/account_service.py` |

---

## References

- `CUSTOMER_CONSOLE_V2_CONSTITUTION.md` — Domain definitions
- `design/l2_1/INTENT_LEDGER.md` — Panel IDs and facets
- `backend/app/main.py` — Router registration
- `docs/architecture/INDEX.md` — Architecture overview
