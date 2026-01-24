# HOC Overview Domain Analysis v1

**Date:** 2026-01-22
**Domain:** `app/hoc/cus/overview/`
**Status:** Analysis Complete — Governance Applied

---

## Executive Summary

| Aspect | Assessment |
|--------|------------|
| Architectural quality | Excellent |
| Role clarity | Near-textbook |
| Current risk | Low |
| Future risk | Medium (if guardrails not enforced) |
| Changes applied | Governance contract added |

**Verdict:** Overview is doing its job perfectly by doing almost nothing. That's the highest compliment in architecture.

---

## Directory Structure

```
app/hoc/cus/overview/
├── __init__.py                           (47 LOC) ← governance added
├── facades/
│   ├── __init__.py                       (11 LOC)
│   └── overview_facade.py                (716 LOC)
├── engines/
│   └── __init__.py                       (11 LOC)  ← intentionally empty
├── drivers/
│   └── __init__.py                       (11 LOC)
└── schemas/
    └── __init__.py                       (11 LOC)
                                          ──────────
                              Total:      807 LOC
```

---

## Domain Contract (Constitutional)

Added to `overview/__init__.py`:

### Invariants (Non-Negotiable)

| ID | Rule |
|----|------|
| INV-OVW-001 | Overview DOES NOT own any tables |
| INV-OVW-002 | Overview NEVER triggers side-effects |
| INV-OVW-003 | All mutations route to owning domains |
| INV-OVW-004 | No business rules — composition only |

### Allowed Operations

- Read from Activity, Incidents, Policies, Logs
- Aggregate counts and statuses
- Return links/references to other domains

### Forbidden Operations

- Write operations of any kind
- Inline approval/dismissal/escalation
- Threshold logic (belongs to Analytics)
- Anomaly classification (belongs to Analytics)
- Background jobs
- Internal caching

### Boundary with Analytics

| Domain | Question |
|--------|----------|
| Overview | "What is the current status?" |
| Analytics | "What patterns exist? What will happen?" |

---

## What Was Validated (No Changes Needed)

### 1. Projection-Only Rule — Correct

Overview is:
- A read model
- A status synthesizer
- A human-facing projection

Overview is NOT:
- A policy engine
- A workflow coordinator
- A cache owner

### 2. Empty Engines Directory — Correct by Design

There are no business rules, no domain truth — only composition. Adding engines would be lying to the architecture.

### 3. Cross-Domain Reads — Clean and Honest

Overview pulls directly from Activity, Incidents, Policies, Logs. This is fine because Overview is explicitly read-only.

### 4. Defensive Query Pattern — Correct

`try/except` around `LimitBreach` queries is exactly where it belongs. Failure handling is contextual, not reusable.

---

## File Analysis

### `overview/facades/overview_facade.py` (716 LOC)

**L2 API Routes Served:**

| Route | Order | Function |
|-------|-------|----------|
| `GET /api/v1/overview/highlights` | O1 | System pulse & domain counts |
| `GET /api/v1/overview/decisions` | O2 | Pending decisions queue |
| `GET /api/v1/overview/decisions/count` | O2 | Decisions count summary |
| `GET /api/v1/overview/costs` | O2 | Cost intelligence summary |
| `GET /api/v1/overview/recovery-stats` | O3 | Recovery statistics |

**DTOs (Dataclasses):**

| Class | Purpose |
|-------|---------|
| `SystemPulse` | Health status summary |
| `DomainCount` | Per-domain counts |
| `HighlightsResult` | O1 response |
| `DecisionItem` | Single pending decision |
| `DecisionsResult` | O2 decisions response |
| `CostPeriod` | Time window |
| `LimitCostItem` | Budget limit status |
| `CostsResult` | O2 costs response |
| `DecisionsCountResult` | O2 count summary |
| `RecoveryStatsResult` | O3 recovery response |

**Class: `OverviewFacade`**

| Method | Description |
|--------|-------------|
| `get_highlights()` | System pulse + domain counts |
| `get_decisions()` | Pending decisions from incidents + proposals |
| `get_costs()` | LLM costs, budget limits, breaches |
| `get_decisions_count()` | Counts by domain and priority |
| `get_recovery_stats()` | Incident recovery statistics |

**Exports:**
```python
__all__ = [
    "OverviewFacade", "get_overview_facade",
    "SystemPulse", "DomainCount", "HighlightsResult",
    "DecisionItem", "DecisionsResult",
    "CostPeriod", "LimitCostItem", "CostsResult",
    "DecisionsCountResult", "RecoveryStatsResult",
]
```

---

## Cross-Domain Dependencies (Data Sources)

| Domain | Model | Usage |
|--------|-------|-------|
| **Activity** | `WorkerRun` | Live/queued runs, LLM costs |
| **Incidents** | `Incident`, `IncidentLifecycleState` | Active incidents, recovery stats |
| **Policies** | `PolicyProposal` | Pending decisions (draft proposals) |
| **Policies** | `Limit`, `LimitBreach`, `LimitCategory` | Budget limits, breach counts |
| **Logs** | `AuditLedger` | Last activity timestamp |

---

## System Pulse Logic

```python
if critical_incidents > 0:
    status = "CRITICAL"
elif pending_decisions > 0 or recent_breaches > 0:
    status = "ATTENTION_NEEDED"
else:
    status = "HEALTHY"
```

---

## Key Architectural Properties

| Property | Status |
|----------|--------|
| Owns tables | **NO** (projection-only) |
| Write operations | **NONE** (read-only) |
| Defensive queries | **YES** (try/except for LimitBreach) |
| Singleton pattern | **YES** (`get_overview_facade()`) |
| DTOs with `to_dict()` | **YES** (all dataclasses) |
| Governance contract | **YES** (added 2026-01-22) |

---

## Future Protection Required

### Gravity Well Risk

Overview will attract requests like:
- "Can we add a quick mutation?"
- "Can we acknowledge a decision from here?"
- "Can we auto-dismiss something?"

**Response:** Route all actions to owning domains. Overview returns references only.

### What Must NEVER Happen

| Action | Why Forbidden |
|--------|---------------|
| Inline approval | Violates INV-OVW-002 |
| Inline dismissal | Violates INV-OVW-002 |
| Inline escalation | Violates INV-OVW-002 |
| Threshold logic | Belongs to Analytics |
| Forecasting | Belongs to Analytics |
| Anomaly classification | Belongs to Analytics |

---

## Changes Applied

| Date | Change |
|------|--------|
| 2026-01-22 | Added governance contract to `overview/__init__.py` |
| 2026-01-22 | Documented 4 invariants (INV-OVW-001 through INV-OVW-004) |
| 2026-01-22 | Defined boundary with Analytics domain |

---

## Conclusion

Overview is an exemplary projection-only domain. It demonstrates the correct pattern:

- Reads from other domains
- Owns no state
- Pure aggregation
- Explicit architectural constraints

The only ongoing task is to **defend its simplicity** and **reject feature creep aggressively**.

**If any invariant is violated, the domain is compromised.**
