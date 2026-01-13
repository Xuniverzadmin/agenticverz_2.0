# PIN-413: Domain Design — Overview & Logs (CORRECTED)

**Status:** BACKEND_COMPLETE
**Category:** Architecture / Domain Design / Aurora Runtime
**Created:** 2026-01-13
**Corrected:** 2026-01-13
**Author:** System
**Related:** PIN-412 (Incidents & Policies), PIN-411 (Activity), PIN-370 (SDSR)

---

## Summary

Complete domain design and implementation for **Overview** and **Logs** domains, completing the Customer Console v1 five-domain set. This PIN follows the O1-O5 epistemic depth model and schema-first discipline established in PIN-411 and PIN-412.

**Key Principle:**
> Data → Contracts → Projections → UX
> No UI without grounded schema.

---

## ARCHITECTURAL CORRECTION (2026-01-13)

**CRITICAL:** The original design violated frozen intent by introducing a `decisions` table.

### What Was Wrong

- Created a new `decisions` table (NOT approved, changes product philosophy)
- Treated Overview as a backend-owned domain with its own persistence
- Stubbed Logs endpoints improperly

### Corrected Architecture

**Overview MUST be PROJECTION-ONLY:**
- NO owned tables
- Aggregates/projects from existing domains (incidents, policy_proposals, limit_breaches, audit_ledger)
- All endpoints are READ-ONLY
- No write paths, no queues, no state transitions
- If an action exists, it must already exist elsewhere

**Logs MUST be GROUNDED:**
- Only Audit Ledger endpoint is implemented (grounded in real table)
- LLM Runs: DEFERRED (requires aos_traces capture path verification)
- System Logs: DEFERRED (requires external logging integration)

### Migration 092 Applied

Rolled back the `decisions` table while preserving `audit_ledger`:
```sql
DROP TABLE decisions;  -- Removed (architectural violation)
-- audit_ledger preserved (correctly scoped to Logs domain)
```

---

## Domain Status (Customer Console v1)

| Domain | Question | Status |
|--------|----------|--------|
| **Overview** | Is the system okay right now? | **BACKEND_COMPLETE (Projection-Only)** |
| Activity | What ran / is running? | V1_FROZEN (PIN-411) |
| Incidents | What went wrong? | V1_FROZEN (PIN-412) |
| Policies | How is behavior defined? | V1_FROZEN (PIN-412) |
| **Logs** | What is the raw truth? | **PARTIAL (Audit Ledger Only)** |

---

## Terminology Lock (FROZEN)

| Old Term | New Term | Rationale |
|----------|----------|-----------|
| Audit | **Audit Ledger** | "Ledger" implies append-only, immutable, accountable |
| audit_logs | **audit_ledger** | Matches governance + compliance mental model |

This rename propagates to: Sidebar, Breadcrumbs, Tables, APIs, DB schema, Docs.

---

## CORE PRIMITIVE: `audit_ledger` Table

**Purpose:** Immutable record of governance-relevant actions taken by actors.
**Owner:** Logs domain (NOT Overview)

```sql
audit_ledger
──────────
id              VARCHAR PK
tenant_id       VARCHAR NOT NULL FK → tenants.id

event_type      VARCHAR(64) NOT NULL
-- ENUM from canonical list (STRICT)

entity_type     VARCHAR(32) NOT NULL
-- POLICY_RULE | POLICY_PROPOSAL | LIMIT | INCIDENT

entity_id       VARCHAR NOT NULL

actor_type      VARCHAR(16) NOT NULL
-- HUMAN | SYSTEM | AGENT

actor_id        VARCHAR NULL
-- user_id, service_id, or agent_id

action_reason   TEXT NULL
-- Free text or system reason code

created_at      TIMESTAMP NOT NULL

before_state    JSONB NULL
after_state     JSONB NULL
-- Only for MODIFY actions
```

**Hard Invariants:**
- Append-only (no UPDATE, no DELETE - enforced by DB trigger)
- Time-ordered
- Tenant-isolated
- No joins required to read meaning

---

## Canonical Audit Events (V1 LOCK)

These are the ONLY audit events in v1.

### Policies › Governance

| Event | Description |
|-------|-------------|
| PolicyRuleCreated | New rule activated |
| PolicyRuleModified | Rule definition changed |
| PolicyRuleRetired | Rule deactivated |
| PolicyProposalApproved | Proposal accepted |
| PolicyProposalRejected | Proposal declined |

### Policies › Limits

| Event | Description |
|-------|-------------|
| LimitCreated | New limit defined |
| LimitUpdated | Limit value changed |
| LimitBreached | Enforcement applied |
| LimitOverrideGranted | Override approved |
| LimitOverrideRevoked | Override removed |

### Incidents

| Event | Description |
|-------|-------------|
| IncidentAcknowledged | Incident marked ACKED |
| IncidentResolved | Incident closed |
| IncidentManuallyClosed | Manual closure |

### System / Control

| Event | Description |
|-------|-------------|
| EmergencyOverrideActivated | Emergency bypass on |
| EmergencyOverrideDeactivated | Emergency bypass off |

If it's not in this list → no audit row.

---

## DOMAIN 1: OVERVIEW (PROJECTION-ONLY)

### Purpose (Locked)

> "What requires my attention or decision right now?"

### CRITICAL CONSTRAINT

**Overview DOES NOT own any tables.**

Overview is a **pure projection layer** that:
- Reads from existing domain tables
- Aggregates counts and status
- Projects pending decisions
- Never writes, never creates state

### Data Sources (OWNED BY OTHER DOMAINS)

| Table | Owner Domain | What Overview Projects |
|-------|--------------|----------------------|
| incidents | Incidents | ACTIVE incidents = pending ACK decisions |
| policy_proposals | Policies | draft status = pending approval decisions |
| limit_breaches | Policies | Recent breach events |
| audit_ledger | Logs | Recent governance actions |

### Structure

```
Overview (Domain) — PROJECTION-ONLY
└── My Project (Subdomain)
    ├── Cross-Domain Highlights  ← "What's changed?" (aggregates)
    ├── Cost Intelligence        ← "What's my budget status?" (v1 baseline)
    └── Decisions                ← "What do I need to decide?" (projection)
```

---

### Topic 1: Cross-Domain Highlights

#### O2 — System Pulse + Domain Counts

**Endpoint:**
```
GET /api/v1/runtime/overview/highlights
```

**Source tables (NOT owned by Overview):**
- incidents (for active_incidents count)
- policy_proposals (for pending approvals)
- limit_breaches (for recent breaches)
- audit_ledger (for last_activity_at)

**Response Shape:**
```json
{
  "pulse": {
    "status": "HEALTHY|ATTENTION_NEEDED|CRITICAL",
    "active_incidents": 2,
    "pending_decisions": 5,
    "recent_breaches": 1
  },
  "domain_counts": [
    {
      "domain": "Incidents",
      "total": 15,
      "pending": 2,
      "critical": 0
    },
    {
      "domain": "Policies",
      "total": 8,
      "pending": 3,
      "critical": 0
    }
  ],
  "last_activity_at": "2026-01-13T12:00:00Z"
}
```

---

### Topic 2: Cost Intelligence (V1 BASELINE)

**This is realized cost data, not speculation.**

#### O2 — Cost Summary

**Endpoint:**
```
GET /api/v1/runtime/overview/costs
```

**Source tables (NOT owned by Overview):**
- worker_runs (for actual LLM spend via cost_cents)
- limits (for budget limits where category=BUDGET)
- limit_breaches (for breach counts and overage)

**Response Shape:**
```json
{
  "currency": "USD",
  "period": {
    "start": "2026-01-01T00:00:00Z",
    "end": "2026-01-31T23:59:59Z"
  },
  "actuals": {
    "llm_run_cost": 1234.56
  },
  "limits": [{
    "limit_id": "LIM-001",
    "name": "Monthly LLM Budget",
    "category": "BUDGET",
    "max_value": 2000,
    "used_value": 1234.56,
    "remaining_value": 765.44,
    "status": "OK|NEAR_THRESHOLD|BREACHED"
  }],
  "violations": {
    "breach_count": 2,
    "total_overage": 145.23
  }
}
```

**V1 Scope (Explicit):**
- Actual LLM spend
- Budget limits and status
- Breach counts and overage

**Explicitly Excluded (v2+):**
- "Saved cost" / policy-prevented attribution
- Forecasts or projections
- Synthetic attribution

---

### Topic 3: Decisions (PROJECTION)

**This is the heart of Overview — but it's a PROJECTION, not a source of truth.**

#### O2 — Decision Queue

**Endpoint:**
```
GET /api/v1/runtime/overview/decisions
```

**Source tables (NOT owned by Overview):**
- incidents (ACTIVE = pending ACK)
- policy_proposals (draft = pending approval)

**Response Shape:**
```json
{
  "items": [{
    "source_domain": "INCIDENT|POLICY",
    "entity_type": "INCIDENT|POLICY_PROPOSAL",
    "entity_id": "...",
    "decision_type": "ACK|APPROVE",
    "priority": "CRITICAL|HIGH|MEDIUM|LOW",
    "summary": "...",
    "created_at": "..."
  }],
  "total": 5,
  "has_more": false
}
```

**Key Distinction:**
- OLD (WRONG): `decisions` table as source of truth
- NEW (CORRECT): Project pending items from existing domain tables

---

## DOMAIN 2: LOGS

### Purpose (Locked)

> "Show raw records for inspection and accountability."

Logs NEVER summarize.
Logs NEVER decide.
Logs ALWAYS explain.

### Structure

```
Logs (Domain)
└── Records (Subdomain)
    ├── LLM Runs       ← DEFERRED (requires aos_traces verification)
    ├── System Logs    ← DEFERRED (requires logging integration)
    └── Audit Ledger   ← IMPLEMENTED (grounded in real table)
```

---

### Topic 1: LLM Runs (DEFERRED)

**Status:** DEFERRED until aos_traces capture path is verified.

**Why Deferred:**
- Need to verify aos_traces table population
- Need to confirm trace capture is working end-to-end
- NO STUBS allowed at this stage

---

### Topic 2: System Logs (DEFERRED)

**Status:** DEFERRED until external logging integration is complete.

**Why Deferred:**
- Requires integration with application logging infrastructure
- Need to define log aggregation pipeline
- NO STUBS allowed at this stage

---

### Topic 3: Audit Ledger (IMPLEMENTED)

**Audit Ledger = governance spine**

#### O2 — Governance Actions

**Endpoint:**
```
GET /api/v1/runtime/logs/audit
```

**Source:**
- audit_ledger (append-only)

**Filters:**
- event_type
- entity_type (POLICY_RULE, POLICY_PROPOSAL, LIMIT, INCIDENT)
- actor_type (HUMAN, SYSTEM, AGENT)
- created_after / created_before

**Response Shape:**
```json
{
  "items": [{
    "id": "...",
    "event_type": "PolicyProposalApproved",
    "entity_type": "POLICY_PROPOSAL",
    "entity_id": "prop_...",
    "actor_type": "HUMAN",
    "actor_id": "user_...",
    "action_reason": "Approved per review",
    "created_at": "..."
  }],
  "total": 50,
  "has_more": true
}
```

#### O3 — Audit Entry Detail

**Endpoint:**
```
GET /api/v1/runtime/logs/audit/{entry_id}
```

Shows:
- before_state
- after_state
- Full audit context

This is where overrides, approvals, emergency actions are **proven**, not described.

---

## Logs vs Audit Ledger — Clean Separation

| Dimension | Logs | Audit Ledger |
|-----------|------|--------------|
| Purpose | Debug / inspect | Accountability / trust |
| Volume | High | Low |
| Mutability | Rotatable | Immutable |
| Actors | Systems | Humans + systems |
| Questions answered | "What happened?" | "Who decided?" |

If you ever feel the need to filter Audit Ledger by severity → you're doing it wrong.

---

## Implementation Progress

| Component | Status | Notes |
|-----------|--------|-------|
| PIN-413 created | **COMPLETE** | This document |
| Migration 091 - audit_ledger | **APPLIED** | Table, indexes, triggers |
| Migration 092 - rollback decisions | **APPLIED** | Removed decisions table |
| SQLModel definitions | **COMPLETE** | `app/models/audit_ledger.py` |
| Overview O2 APIs | **IMPLEMENTED** | highlights, costs, decisions (projection-only) |
| Logs O2 APIs | **PARTIAL** | audit only (llm-runs and system deferred) |
| Router integration | **COMPLETE** | Mounted at `/api/v1/runtime/` |
| Frontend integration | PENDING | |

### Backend Files Delivered

```
backend/app/runtime_projections/
├── router.py                    # Updated with Overview + Logs
├── overview/
│   ├── __init__.py
│   └── router.py               # OVW-RT-O2 (highlights, decisions) — PROJECTION-ONLY
└── logs/
    ├── __init__.py
    └── router.py               # LOG-RT-O2 (audit only)

backend/app/models/
└── audit_ledger.py             # AuditLedger, enums (NO Decision model)

backend/alembic/versions/
├── 091_decisions_and_audit_ledger.py  # Created both tables
└── 092_rollback_decisions_table.py    # Removed decisions table
```

---

## Invariants

### INV-OVERVIEW-001: Projection-Only

> Overview DOES NOT own any tables. It aggregates/projects from existing domains.

### INV-OVERVIEW-002: Decision-Centric Projection

> Overview projects pending decisions from incidents (ACTIVE) and policy_proposals (draft). It does NOT create decision state.

### INV-OVERVIEW-003: No Billing Fantasies

> Cost Intelligence derives from Limits only. No external billing integration. (DEFERRED)

### INV-LOGS-001: Audit Ledger Immutability

> audit_ledger is append-only. No UPDATE, no DELETE.

### INV-LOGS-002: Canonical Events Only

> Only events from the canonical list create audit rows.

### INV-LOGS-003: Grounded Endpoints Only

> NO STUBS. Every Logs endpoint must be grounded in real capture paths. LLM Runs and System Logs are deferred until verified.

### INV-LOGS-004: Logs vs Activity Separation

> Logs show raw traces. Activity shows structured views. No overlap.

---

## What Was Removed (Architectural Correction)

| Item | Why Removed |
|------|-------------|
| `decisions` table | Overview must be projection-only, not a new source of truth |
| Decision model in Python | No backing table |
| DecisionType, DecisionStatus enums | Not needed without table |
| Decision-related audit events | Decisions are not first-class objects |
| `/api/v1/runtime/logs/llm-runs` endpoint | Deferred until aos_traces verified |
| `/api/v1/runtime/logs/system` endpoint | Deferred until logging integration |

---

## References

- PIN-412: Incidents & Policies (V1_FROZEN)
- PIN-411: Activity Domain (CLOSED)
- PIN-370: SDSR System Contract
- `docs/contracts/UX_INVARIANTS_CHECKLIST.md`
- `docs/contracts/CUSTOMER_CONSOLE_V1_CONSTITUTION.md`
