# PIN-165: Pillar Definition Reconciliation - Product vs Infrastructure Views

**Status:** REFERENCE
**Category:** Architecture / Mental Model / Reconciliation
**Created:** 2025-12-25
**Purpose:** Reconcile product-focused and infrastructure-focused pillar definitions

---

## Executive Summary

Two pillar definitions exist in the AOS documentation:
1. **Product-Focused (Customer Journey):** Cost Intelligence, Incident Console, Self-Healing, Governance
2. **Infrastructure-Focused (Developer Architecture):** Architecture & Core, Safety & Governance, Operations, Developer Experience

**Key Finding:** Both definitions are **VALID AND COMPLEMENTARY** - they describe the same system from different perspectives.

---

## Two Valid Perspectives - Same System

| Perspective | Purpose | Audience |
|-------------|---------|----------|
| **Product-Focused (Earlier)** | Customer value journey | Founders, Sales, Customers |
| **Infrastructure-Focused (PIN-163/164)** | Developer architecture | Engineers, DevOps |

---

## Product Pillars (Customer-Facing View)

```
PILLAR 0: COST INTELLIGENCE (FinOps)
├── Budget tracking and anomaly detection
├── Spend optimization recommendations
└── Cost-based routing adjustments

PILLAR 1: INCIDENT CONSOLE (Reactive)
├── Real-time incident visibility
├── Failure pattern recognition
└── Customer-facing Guard Console

PILLAR 2: SELF-HEALING (Proactive)
├── Automatic recovery suggestions
├── Pattern → Recovery matching
└── Historical learning from incidents

PILLAR 3: GOVERNANCE (Preventive)
├── Policy generation from recoveries
├── Constitutional constraints
└── CARE routing adjustments
```

---

## Infrastructure Pillars (Developer-Facing View)

```
PILLAR 1: ARCHITECTURE & CORE SYSTEMS
├── Workflow Engine (M4)
├── Skills Registry (M11)
├── Runtime (M5)
└── Traces System (M6)

PILLAR 2: SAFETY & GOVERNANCE
├── Policy Engine (M19)
├── RBAC (M7)
├── SBA (M15-16)
├── CARE Routing (M17-18)
└── KillSwitch (M22)

PILLAR 3: OPERATIONAL INTELLIGENCE
├── Recovery Engine (M10)
├── Cost Intelligence (M26)
├── Ops Console (M24)
├── Guard Console (M23)
└── Integration Loop (M25)

PILLAR 4: DEVELOPER EXPERIENCE
├── SDK Python/JS (M8)
├── CLI (M3)
├── Prevention System (M29)
└── Memory Trail / Documentation
```

---

## Mapping: Product Pillars to Infrastructure Implementation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│               PRODUCT PILLAR TO INFRASTRUCTURE MAPPING                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PRODUCT PILLAR 0: COST INTELLIGENCE (FinOps)                               │
│  ├── M26 cost_intelligence.py ────────────────► Infra Pillar 3: Operations  │
│  ├── M27 cost_guard.py ───────────────────────► Infra Pillar 3: Operations  │
│  ├── M27 cost_ops.py ─────────────────────────► Infra Pillar 3: Operations  │
│  └── M27 cost_bridges.py (C1-C5) ─────────────► Infra Pillar 3: Operations  │
│      STATUS: FULLY IMPLEMENTED                                               │
│                                                                              │
│  PRODUCT PILLAR 1: INCIDENT CONSOLE (Reactive)                              │
│  ├── M23 guard.py (1,800+ lines) ─────────────► Infra Pillar 3: Operations  │
│  ├── M25 Bridge 1: IncidentToCatalog ─────────► Infra Pillar 3: Operations  │
│  └── Loop Stage: INCIDENT_CREATED                                            │
│      STATUS: FULLY IMPLEMENTED                                               │
│                                                                              │
│  PRODUCT PILLAR 2: SELF-HEALING (Proactive)                                 │
│  ├── M10 recovery_matcher.py ─────────────────► Infra Pillar 3: Operations  │
│  ├── M25 Bridge 2: PatternToRecovery ─────────► Infra Pillar 3: Operations  │
│  ├── M25 Bridge 3: RecoveryToPolicy ──────────► Infra Pillar 2: Safety      │
│  └── Loop Stages: PATTERN_MATCHED → RECOVERY_SUGGESTED                       │
│      STATUS: FULLY IMPLEMENTED                                               │
│                                                                              │
│  PRODUCT PILLAR 3: GOVERNANCE (Preventive)                                  │
│  ├── M19 policy/engine.py ────────────────────► Infra Pillar 2: Safety      │
│  ├── M7 RBAC ─────────────────────────────────► Infra Pillar 2: Safety      │
│  ├── M17 CARE routing ────────────────────────► Infra Pillar 2: Safety      │
│  ├── M25 Bridge 4: PolicyToRouting ───────────► Infra Pillar 2: Safety      │
│  └── Loop Stages: POLICY_GENERATED → ROUTING_ADJUSTED                        │
│      STATUS: FULLY IMPLEMENTED                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## M25 Integration Loop = Product Pillar Flow Engine

The M25 "Pillar Integration Loop" (main.py:338) is the **orchestrator** that connects product pillars:

```
PRODUCT PILLAR FLOW (M25 Loop)
==============================

PILLAR 1          PILLAR 2          PILLAR 3
INCIDENT   ──────► SELF-HEALING ────► GOVERNANCE
   │                   │                  │
   ▼                   ▼                  ▼
┌────────────┐   ┌────────────┐    ┌────────────┐
│ INCIDENT   │   │ PATTERN    │    │ POLICY     │
│ CREATED    │──►│ MATCHED    │───►│ GENERATED  │
│ (Bridge 1) │   │ (Bridge 2) │    │ (Bridge 3) │
└────────────┘   └────────────┘    └────────────┘
                       │                  │
                       ▼                  ▼
                 ┌────────────┐    ┌────────────┐
                 │ RECOVERY   │    │ ROUTING    │
                 │ SUGGESTED  │    │ ADJUSTED   │
                 │ (Bridge 2) │    │ (Bridge 4) │
                 └────────────┘    └────────────┘
                                         │
                                         ▼
                            ┌────────────────────┐
                            │   LOOP_COMPLETE    │
                            │    (Bridge 5)      │
                            └────────────────────┘
                                         │
                                         ▼
                              PILLAR 0: COST
                           (M26/M27 Parallel Track)
```

---

## Loop Stages (Verified in events.py:197-202)

| Loop Stage | Bridge | Product Pillar | File:Line |
|------------|--------|----------------|-----------|
| `INCIDENT_CREATED` | Bridge 1 | Pillar 1: Incident | bridges.py:192 |
| `PATTERN_MATCHED` | Bridge 2 | Pillar 2: Self-Healing | bridges.py:465 |
| `RECOVERY_SUGGESTED` | Bridge 2 | Pillar 2: Self-Healing | bridges.py:465 |
| `POLICY_GENERATED` | Bridge 3 | Pillar 3: Governance | bridges.py:701 |
| `ROUTING_ADJUSTED` | Bridge 4 | Pillar 3: Governance | bridges.py:906 |
| `LOOP_COMPLETE` | Bridge 5 | Console Update | bridges.py:1164 |

---

## Verified Integration Status

| Integration | Code Evidence | Status |
|-------------|---------------|--------|
| Incident → Self-Healing auto-feed | `PatternToRecoveryBridge` @ bridges.py:465 | IMPLEMENTED |
| Recovery → Policy promotion | `RecoveryToPolicyBridge` @ bridges.py:701 | IMPLEMENTED |
| Policy → Routing adjustment | `PolicyToRoutingBridge` @ bridges.py:906 | IMPLEMENTED |
| All 5 bridges enabled by default | dispatcher.py:51-55 (all `True`) | ENABLED |
| M25 Loop frozen | PIN-140, version 1.0.0 | FROZEN |

---

## Bridge Enable Configuration (dispatcher.py:51-55)

```python
bridge_1_enabled: bool = True  # Incident → Catalog
bridge_2_enabled: bool = True  # Pattern → Recovery
bridge_3_enabled: bool = True  # Recovery → Policy
bridge_4_enabled: bool = True  # Policy → Routing
bridge_5_enabled: bool = True  # Loop → Console
```

Environment overrides: `BRIDGE_1_ENABLED`, `BRIDGE_2_ENABLED`, etc.

---

## Remaining Gaps (Apply to Both Views)

| Gap | Impact | Required For |
|-----|--------|--------------|
| `PLANNER_BACKEND=stub` (default) | No real LLM planning | Production |
| `MEMORY_CONTEXT_INJECTION=false` | Agents don't learn | Production |
| CARE only in workers | API calls bypass CARE | Design Decision |
| M21 Tenants DISABLED | No multi-tenant API | Beta+ |
| `EVENT_PUBLISHER=logging` | No real-time UI | Production |

---

## Why Two Definitions Exist

### Historical Context

1. **Product Pillars** emerged from go-to-market strategy (PIN-033, PIN-128)
   - Focus: What value do customers receive?
   - Flow: Incident → Analysis → Healing → Prevention

2. **Infrastructure Pillars** emerged from code organization (PIN-163, PIN-164)
   - Focus: How is the system built?
   - Layers: Core → Safety → Ops → DX

### Reconciliation Insight

The M25 Integration Loop is the **bridge** between views:
- **Product View:** Loop stages = customer value delivery
- **Infra View:** Loop bridges = module integration points

Both are accurate - use the appropriate view for your audience.

---

## Recommendations

### For Customer Communication
Use **Product Pillars** (Cost → Incident → Self-Healing → Governance)
- Emphasizes value journey
- Maps to customer problems

### For Developer Documentation
Use **Infrastructure Pillars** (Architecture → Safety → Ops → DX)
- Maps to codebase organization
- Clear module boundaries

### For System Understanding
Use **Both Views Together**
- Product pillars show the "what"
- Infrastructure pillars show the "how"
- M25 Loop shows the "flow"

---

## Related PINs

- PIN-163: M0-M28 Utilization Report (infrastructure pillar analysis)
- PIN-164: System Mental Model - Pillar Interactions
- PIN-140: M25 Complete - Rollback Safe (loop verification)
- PIN-128: Master Plan M25-M32 (product pillar origins)
- PIN-033: M8-M14 Machine-Native Realignment (early product thinking)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-25 | Initial creation - Reconciliation of two pillar views |
