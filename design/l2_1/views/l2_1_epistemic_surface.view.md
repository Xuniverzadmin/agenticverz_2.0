# L2.1 Epistemic Surface View

> **AUTO-GENERATED REFERENCE VIEW**
> This file is rendered from `l2_1_epistemic_surface` table data.
> **DO NOT EDIT MANUALLY** — regenerate from tables.
>
> Generated: 2026-01-07
> Source: `design/l2_1/schema/l2_1_epistemic_surface.schema.sql`

---

## Generation Command

```bash
# Regenerate this file from database:
psql -h localhost -U nova -d nova_aos -f design/l2_1/scripts/generate_view.sql > design/l2_1/views/l2_1_epistemic_surface.view.md
```

---

## Domain Summary

| Domain | Subdomains | Topics | Status |
|--------|------------|--------|--------|
| overview | 1 | 2 | frozen |
| activity | 1 | 3 | frozen |
| incidents | 2 | 3 | frozen |
| policies | 2 | 4 | frozen |
| logs | 2 | 3 | frozen |

**Total:** 5 domains, 8 subdomains, 15 topics

---

## Order Summary

| Order | Name | Depth | Terminal | Navigates To |
|-------|------|-------|----------|--------------|
| O1 | Snapshot | shallow | No | O2 |
| O2 | Presence | list | No | O3 |
| O3 | Explanation | single | No | O4, O5 |
| O4 | Context | relational | No | O5 |
| O5 | Proof | terminal | **Yes** | (none) |

---

## Surface ID Format

```
{DOMAIN}.{SUBDOMAIN}.{TOPIC}

Examples:
  OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS
  ACTIVITY.EXECUTIONS.ACTIVE_RUNS
  INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS
  POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES
  LOGS.AUDIT_LOGS.SYSTEM_AUDIT
```

---

## Domain: OVERVIEW

**Core Question:** Is the system okay right now?
**Object Family:** Status, Health, Pulse

### Subdomains & Topics

| Subdomain | Topic ID | Topic Name | Question |
|-----------|----------|------------|----------|
| system_health | current_status | Current Status | What is the current system state? |
| system_health | health_metrics | Health Metrics | What are the key health indicators? |

### Surface IDs

```
OVERVIEW.SYSTEM_HEALTH.CURRENT_STATUS
OVERVIEW.SYSTEM_HEALTH.HEALTH_METRICS
```

---

## Domain: ACTIVITY

**Core Question:** What ran / is running?
**Object Family:** Runs, Traces, Jobs

### Subdomains & Topics

| Subdomain | Topic ID | Topic Name | Question |
|-----------|----------|------------|----------|
| executions | active_runs | Active Runs | What is currently running? |
| executions | completed_runs | Completed Runs | What has finished recently? |
| executions | run_details | Run Details | What happened in this specific run? |

### Surface IDs

```
ACTIVITY.EXECUTIONS.ACTIVE_RUNS
ACTIVITY.EXECUTIONS.COMPLETED_RUNS
ACTIVITY.EXECUTIONS.RUN_DETAILS
```

---

## Domain: INCIDENTS

**Core Question:** What went wrong?
**Object Family:** Incidents, Violations, Failures

### Subdomains & Topics

| Subdomain | Topic ID | Topic Name | Question |
|-----------|----------|------------|----------|
| active_incidents | open_incidents | Open Incidents | What incidents need attention? |
| active_incidents | incident_details | Incident Details | What is the full context of this incident? |
| historical_incidents | resolved_incidents | Resolved Incidents | What incidents were resolved? |

### Surface IDs

```
INCIDENTS.ACTIVE_INCIDENTS.OPEN_INCIDENTS
INCIDENTS.ACTIVE_INCIDENTS.INCIDENT_DETAILS
INCIDENTS.HISTORICAL_INCIDENTS.RESOLVED_INCIDENTS
```

---

## Domain: POLICIES

**Core Question:** How is behavior defined?
**Object Family:** Rules, Limits, Constraints, Approvals

### Subdomains & Topics

| Subdomain | Topic ID | Topic Name | Question |
|-----------|----------|------------|----------|
| active_policies | budget_policies | Budget Policies | What budget constraints are in effect? |
| active_policies | rate_limits | Rate Limits | What rate limits are configured? |
| active_policies | approval_rules | Approval Rules | What requires approval? |
| policy_audit | policy_changes | Policy Changes | What policies have changed? |

### Surface IDs

```
POLICIES.ACTIVE_POLICIES.BUDGET_POLICIES
POLICIES.ACTIVE_POLICIES.RATE_LIMITS
POLICIES.ACTIVE_POLICIES.APPROVAL_RULES
POLICIES.POLICY_AUDIT.POLICY_CHANGES
```

---

## Domain: LOGS

**Core Question:** What is the raw truth?
**Object Family:** Traces, Audit, Proof

### Subdomains & Topics

| Subdomain | Topic ID | Topic Name | Question |
|-----------|----------|------------|----------|
| audit_logs | system_audit | System Audit | What system-level events occurred? |
| audit_logs | user_audit | User Audit | What user actions were recorded? |
| execution_traces | trace_details | Trace Details | What is the full execution trace? |

### Surface IDs

```
LOGS.AUDIT_LOGS.SYSTEM_AUDIT
LOGS.AUDIT_LOGS.USER_AUDIT
LOGS.EXECUTION_TRACES.TRACE_DETAILS
```

---

## Governance Constraints (All Surfaces)

| Constraint | Value | Source |
|------------|-------|--------|
| authority | NONE | GA-001 |
| tenant_isolation | true | GA-004 |
| enrichment_allowed | false | GA-005 |
| mutable | false | GA-002 |
| cross_tenant_aggregation | false | GA-004 |

---

## View Regeneration

This view should be regenerated when:
- New topics are added to domains
- Surface configurations change
- Order definitions are updated

**Never manually edit this file.**
