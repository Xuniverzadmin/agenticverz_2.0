# DSM-L2.1 — Domain Surface Manifest

**Schema ID:** `DSM_L2_1`
**Version:** 1.0.0
**Status:** FROZEN (aligned with L1 Constitution)
**Created:** 2026-01-07
**Authority:** NONE

---

## 0. Canonical Source of Truth

> **This document is a rendered reference view.**
> The authoritative definition of L2.1 domains lives in:
> - `l2_1_domain_registry` (table)
>
> **If discrepancies exist, tables take precedence.**

### Document Restrictions

This document may not introduce:
- New domains
- New subdomains
- New topics
- Authority semantics

All such changes must be applied at table level first.

### Table Mapping

```
Source Table: l2_1_domain_registry
Schema Location: design/l2_1/schema/l2_1_domain_registry.schema.sql
Seed Location: design/l2_1/seeds/l2_1_domain_registry.seed.sql
Selection Criteria: ALL (this defines the complete domain set)
```

---

## 1. Definition

**Full Name:** Domain Surface Manifest — L2.1

**Purpose:**
Declares which **L1 Domains / Subdomains / Topics** are supported in L2.1.

**Key Rule:**
> Must be a **subset of the L1 Constitution**.
> No new domains. Ever.

---

## 2. L1 Constitution Alignment

This manifest is derived from and constrained by the **Customer Console v1 Constitution**.
Any domain listed here MUST exist in the L1 Constitution.

**Violation Response:** If a domain is proposed that does not exist in L1 Constitution → REJECT

---

## 3. Frozen Domains (v1)

The following five domains are **frozen** and must not be renamed, merged, or modified.

| Domain ID | Domain Name | Core Question | L1 Constitution Ref |
|-----------|-------------|---------------|---------------------|
| `overview` | Overview | Is the system okay right now? | CUSTOMER_CONSOLE_V1_CONSTITUTION §3.1 |
| `activity` | Activity | What ran / is running? | CUSTOMER_CONSOLE_V1_CONSTITUTION §3.2 |
| `incidents` | Incidents | What went wrong? | CUSTOMER_CONSOLE_V1_CONSTITUTION §3.3 |
| `policies` | Policies | How is behavior defined? | CUSTOMER_CONSOLE_V1_CONSTITUTION §3.4 |
| `logs` | Logs | What is the raw truth? | CUSTOMER_CONSOLE_V1_CONSTITUTION §3.5 |

---

## 4. Domain Definitions

### 4.1 Overview

```yaml
domain_id: overview
name: "Overview"
question: "Is the system okay right now?"
object_family:
  - Status
  - Health
  - Pulse

subdomains:
  - id: system_health
    name: "System Health"
    topics:
      - id: current_status
        name: "Current Status"
        question: "What is the current system state?"
      - id: health_metrics
        name: "Health Metrics"
        question: "What are the key health indicators?"

forbidden:
  - Execution history (belongs to Activity)
  - Failure details (belongs to Incidents)
  - Rule definitions (belongs to Policies)
```

### 4.2 Activity

```yaml
domain_id: activity
name: "Activity"
question: "What ran / is running?"
object_family:
  - Runs
  - Traces
  - Jobs

subdomains:
  - id: executions
    name: "Executions"
    topics:
      - id: active_runs
        name: "Active Runs"
        question: "What is currently running?"
      - id: completed_runs
        name: "Completed Runs"
        question: "What has finished recently?"
      - id: run_details
        name: "Run Details"
        question: "What happened in this specific run?"

forbidden:
  - Failure classification (belongs to Incidents)
  - Policy evaluation (belongs to Policies)
  - Raw audit (belongs to Logs)
```

### 4.3 Incidents

```yaml
domain_id: incidents
name: "Incidents"
question: "What went wrong?"
object_family:
  - Incidents
  - Violations
  - Failures

subdomains:
  - id: active_incidents
    name: "Active Incidents"
    topics:
      - id: open_incidents
        name: "Open Incidents"
        question: "What incidents need attention?"
      - id: incident_details
        name: "Incident Details"
        question: "What is the full context of this incident?"
  - id: historical_incidents
    name: "Historical Incidents"
    topics:
      - id: resolved_incidents
        name: "Resolved Incidents"
        question: "What incidents were resolved?"

forbidden:
  - Execution traces (belongs to Activity)
  - Policy definitions (belongs to Policies)
  - Success metrics (belongs to Overview)
```

### 4.4 Policies

```yaml
domain_id: policies
name: "Policies"
question: "How is behavior defined?"
object_family:
  - Rules
  - Limits
  - Constraints
  - Approvals

subdomains:
  - id: active_policies
    name: "Active Policies"
    topics:
      - id: budget_policies
        name: "Budget Policies"
        question: "What budget constraints are in effect?"
      - id: rate_limits
        name: "Rate Limits"
        question: "What rate limits are configured?"
      - id: approval_rules
        name: "Approval Rules"
        question: "What requires approval?"
  - id: policy_audit
    name: "Policy Audit"
    topics:
      - id: policy_changes
        name: "Policy Changes"
        question: "What policies have changed?"

forbidden:
  - Policy violations (belongs to Incidents)
  - Execution under policy (belongs to Activity)
  - Raw policy logs (belongs to Logs)
```

### 4.5 Logs

```yaml
domain_id: logs
name: "Logs"
question: "What is the raw truth?"
object_family:
  - Traces
  - Audit
  - Proof

subdomains:
  - id: audit_logs
    name: "Audit Logs"
    topics:
      - id: system_audit
        name: "System Audit"
        question: "What system-level events occurred?"
      - id: user_audit
        name: "User Audit"
        question: "What user actions were recorded?"
  - id: execution_traces
    name: "Execution Traces"
    topics:
      - id: trace_details
        name: "Trace Details"
        question: "What is the full execution trace?"

forbidden:
  - Interpreted summaries (belongs to Overview)
  - Failure analysis (belongs to Incidents)
  - Policy evaluation (belongs to Policies)
```

---

## 5. Forbidden Actions

| Action | Reason | Violation Response |
|--------|--------|-------------------|
| Add new domain | Breaks L1 Constitution alignment | REJECT |
| Rename domain | Breaks mental model | REJECT |
| Merge domains | Collapses distinct questions | REJECT |
| Split domain | Creates L1 divergence | REJECT |
| Reorder domains | Changes semantic priority | REJECT |

---

## 6. Validation Rules

### 6.1 Domain Existence Check

```python
def validate_domain(domain_id: str) -> bool:
    """Domain must exist in this manifest."""
    valid_domains = {"overview", "activity", "incidents", "policies", "logs"}
    return domain_id in valid_domains
```

### 6.2 Subdomain Existence Check

```python
def validate_subdomain(domain_id: str, subdomain_id: str) -> bool:
    """Subdomain must exist under declared domain."""
    # Implementation references this manifest
    pass
```

### 6.3 Topic Existence Check

```python
def validate_topic(domain_id: str, subdomain_id: str, topic_id: str) -> bool:
    """Topic must exist under declared subdomain."""
    # Implementation references this manifest
    pass
```

---

## 7. Amendment Process

To amend this manifest:

1. **Propose** amendment with rationale
2. **Verify** L1 Constitution allows the change
3. **Human ratification** required
4. **Update** L1 Constitution if necessary
5. **Update** this manifest
6. **Regenerate** all dependent ESM-L2.1 instances

**No silent amendments. No Claude-initiated amendments.**

---

## 8. References

- `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md` — L1 Authority
- `ESM_L2_1_TEMPLATE.md` — Epistemic Surface Matrix
- `L2_1_GOVERNANCE_ASSERTIONS.md` — Governance constraints

---

**STATUS:** FROZEN — Aligned with L1 Constitution v1.
