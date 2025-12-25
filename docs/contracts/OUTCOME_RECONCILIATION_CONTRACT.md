# OUTCOME RECONCILIATION CONTRACT

**Version:** 0.1 (skeletal)
**Created:** 2025-12-25
**Status:** DRAFT - Obligation definition only

---

## Question This Contract Answers

> **How do we reconcile what happened with what was promised?**

---

## Core Obligation

**Outcomes MUST map back to Intent + Constraint + Decision.**

"Success" is not binary. It is decomposed.

---

## Outcome Decomposition (Mandatory)

### 1. Success Is Not Binary

| Field | Obligation |
|-------|------------|
| execution_completed | MUST state if execution finished |
| constraints_satisfied | MUST state which constraints were met/violated |
| intent_fulfilled | MUST state if declared intent was achieved |
| decisions_executed | MUST reference decisions that led to outcome |

**Forbidden:** `success: true` without decomposition.

### 2. Outcome-to-Intent Traceability

Every outcome MUST reference:

| Link | Obligation |
|------|------------|
| pre_run_contract_id | MUST link to the pre-run declaration |
| constraints_declared | MUST list constraints that applied |
| constraints_violated | MUST list constraints that were violated |
| decisions_made | MUST reference decision record |

**Forbidden:** Outcomes that cannot be traced to intent.

---

## Historical Data Obligations

### 1. Cost Recording

| Obligation | Rule |
|------------|------|
| Workflow costs MUST be recorded | Cost tables cannot show 0 when tokens consumed |
| Recording is synchronous | Cost recorded before response returned |
| Cost reconciliation | Recorded cost MUST match reported cost_report |

**Forbidden:** Cost tables empty despite workflow execution.

### 2. Observability Surface

| Resource | Obligation |
|----------|------------|
| Metrics existence | IF metrics exist, their existence MUST be documented |
| Metrics location | Access path MUST be discoverable without code |
| Dashboard existence | IF dashboards exist, they MUST be listed |

**Forbidden:** Undocumented observability infrastructure.

### 3. Access Paths

| Resource | Obligation |
|----------|------------|
| Ops endpoints | IF /ops/* exists, access requirements MUST be documented |
| Credential domains | Auth domain requirements MUST be explicit |
| Elevation path | IF elevated access needed, path MUST be documented |

**Forbidden:** `AUTH_DOMAIN_MISMATCH` without documented resolution.

---

## Field Semantics (Mandatory Definitions)

Every outcome field MUST have documented semantics:

| Field | Required Documentation |
|-------|------------------------|
| recovery_log | MUST define: when populated, what triggers entry, what empty means |
| routing_stability | MUST define: what 1.0 means, what N/A means, when calculated |
| cost_report | MUST define: units, timing, reconciliation method |

**Forbidden:** Fields that exist without defined semantics.

---

## What This Contract Does NOT Specify

- How to display outcomes
- Storage format
- Retention policy
- Aggregation methods

Those are implementation. This is obligation.

---

## Ledger Entries This Contract Addresses

| Entry | Surface | Gap | How Contract Addresses |
|-------|---------|-----|------------------------|
| S3: recovery_log meaning opaque | Outcome | Opaque | Field semantics mandatory |
| S5: Cost tables not populated | Outcome | Missing | Cost recording synchronous obligation |
| S5: Prometheus/Grafana undocumented | Outcome | Opaque | Observability surface documentation |
| S5: Ops console access missing | Outcome | Missing | Access paths documentation |

---

## Contract Violation

If an outcome cannot be reconciled to its origin:
- The run is **contract-violating**
- Historical data is unreliable
- Trust degrades over time
