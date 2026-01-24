# PIN-164: System Mental Model - Pillar Interactions & Dependencies

**Status:** REFERENCE
**Category:** Architecture / Mental Model / System Design
**Created:** 2025-12-25
**Purpose:** Document how milestones/functions map to pillars and their interactions

---

## Executive Summary

This document provides a mental model of how AOS components interact, complement, and potentially conflict with each other. It's designed to help understand the system before human testing.

**Key Insight:** AOS is designed as a **feedback loop system** where incidents flow through multiple pillars to become preventions.

---

## The Four Pillars

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AOS FOUR PILLAR ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │   ARCHITECTURE   │    │     SAFETY &     │    │   OPERATIONAL    │  │
│  │   & CORE         │◄──►│   GOVERNANCE     │◄──►│   INTELLIGENCE   │  │
│  │                  │    │                  │    │                  │  │
│  │ • Workflow (M4)  │    │ • Policy (M19)   │    │ • Recovery (M10) │  │
│  │ • Skills (M11)   │    │ • RBAC (M7)      │    │ • Cost Intel(M26)│  │
│  │ • Runtime (M5)   │    │ • SBA (M15-16)   │    │ • Ops Console(M24)│  │
│  │ • Traces (M6)    │    │ • CARE (M17-18)  │    │ • Guard (M23)    │  │
│  └────────┬─────────┘    │ • KillSwitch(M22)│    └────────┬─────────┘  │
│           │              └────────┬─────────┘             │            │
│           │                       │                       │            │
│           └───────────────────────┼───────────────────────┘            │
│                                   │                                    │
│                                   ▼                                    │
│                    ┌──────────────────────────────┐                    │
│                    │    DEVELOPER EXPERIENCE      │                    │
│                    │                              │                    │
│                    │ • SDK (M8)    • Tests        │                    │
│                    │ • CLI (M3)    • Prevention   │                    │
│                    │ • Docs        • Memory Trail │                    │
│                    └──────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Milestone to Pillar Mapping

### Pillar 1: Architecture & Core Systems

| Milestone | Component | Wired To | Status |
|-----------|-----------|----------|--------|
| **M4** | Workflow Engine | Skills, Traces | ✅ ACTIVE |
| **M5** | Runtime | Skills, Policy | ✅ ACTIVE |
| **M6** | Traces | Replay, Determinism | ✅ ACTIVE |
| **M11** | Skills | 26 skill classes | ✅ ACTIVE |
| **M12** | Multi-Agent | Blackboard, Credits | ✅ ACTIVE |

**Key File:** `app/workflow/engine.py` - Deterministic execution

### Pillar 2: Safety & Governance

| Milestone | Component | Wired To | Status |
|-----------|-----------|----------|--------|
| **M7** | RBAC | All API endpoints | ✅ ENFORCED |
| **M15-16** | SBA | Agent spawn, CARE | ✅ ACTIVE |
| **M17** | CARE Routing | Workers only | ⚠️ LIMITED |
| **M18** | CARE-L Evolution | SBA feedback | ✅ ACTIVE |
| **M19** | Policy Engine | Bridges, evaluation | ✅ ACTIVE |
| **M22** | KillSwitch | Proxy, incidents | ✅ ACTIVE |
| **M32** | Tier Gating | Auth, features | ✅ ACTIVE |

**Key File:** `app/policy/engine.py` - Constitutional governance

### Pillar 3: Operational Intelligence

| Milestone | Component | Wired To | Status |
|-----------|-----------|----------|--------|
| **M10** | Recovery Engine | Bridges, catalog | ✅ ACTIVE |
| **M23** | Guard Console | Customer UI | ✅ ACTIVE |
| **M24** | Ops Console | Founder UI | ✅ ACTIVE |
| **M25** | Integration Loop | All bridges | ✅ FROZEN |
| **M26** | Cost Intelligence | Snapshots | ✅ ACTIVE |
| **M27** | Cost Loop | Cost bridges | ✅ ACTIVE |
| **M28** | Unified Console | UI components | ✅ ACTIVE |

**Key File:** `app/integrations/L3_adapters.py` - 5 integration bridges

### Pillar 4: Developer Experience

| Milestone | Component | Wired To | Status |
|-----------|-----------|----------|--------|
| **M3** | CLI | 14,398 lines | ✅ ACTIVE |
| **M8** | SDK (Python/JS) | Both published | ✅ ACTIVE |
| **M29** | Prevention System | Pre/Post-flight | ✅ ACTIVE |
| **M24** | Memory Trail | PIN automation | ✅ ACTIVE |

**Key File:** `sdk/python/aos_sdk/cli.py` - SDK CLI

---

## The Integration Loop (M25) - Central Nervous System

The M25 Integration Loop is the **central nervous system** that connects all pillars:

```
              THE M25 INTEGRATION LOOP
              ========================

    INCIDENT                              PREVENTION
       │                                      ▲
       ▼                                      │
┌──────────────┐                    ┌─────────────────┐
│   Bridge 1   │ ─────────────────► │    Bridge 5     │
│  Incident →  │                    │   Loop Status   │
│   Catalog    │                    │   → Console     │
└──────────────┘                    └─────────────────┘
       │                                      ▲
       ▼                                      │
┌──────────────┐                    ┌─────────────────┐
│   Bridge 2   │                    │    Bridge 4     │
│  Pattern →   │ ─────────────────► │   Policy →      │
│   Recovery   │                    │    Routing      │
└──────────────┘                    └─────────────────┘
       │                                      ▲
       ▼                                      │
       └──────────► ┌──────────────┐ ─────────┘
                    │   Bridge 3   │
                    │  Recovery →  │
                    │    Policy    │
                    └──────────────┘

  FROZEN: 2025-12-23 (PIN-140)
  Version: LOOP_MECHANICS_VERSION = "1.0.0"
```

### Bridge Details (Verified)

| Bridge | From | To | Key Class | File:Line |
|--------|------|-----|-----------|-----------|
| **B1** | Incident | Catalog | `IncidentToCatalogBridge` | `bridges.py:192` |
| **B2** | Pattern | Recovery | `PatternToRecoveryBridge` | `bridges.py:465` |
| **B3** | Recovery | Policy | `RecoveryToPolicyBridge` | `bridges.py:701` |
| **B4** | Policy | Routing | `PolicyToRoutingBridge` | `bridges.py:906` |
| **B5** | Loop | Console | `LoopStatusBridge` | `bridges.py:1164` |

### Cost Loop Bridges (M27)

| Bridge | Purpose | Status |
|--------|---------|--------|
| **C1** | Cost Anomaly → Incident | ✅ |
| **C2** | Cost Pattern → Catalog | ✅ |
| **C3** | Cost Recovery Generator | ✅ |
| **C4** | Cost Policy Generator | ✅ |
| **C5** | Cost Routing Adjuster | ✅ |

---

## Component Relationships: Complementary

### How Pillars Complement Each Other

```
┌─────────────────────────────────────────────────────────────────────┐
│                     COMPLEMENTARY RELATIONSHIPS                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ARCHITECTURE ──────► SAFETY                                        │
│  • Workflow provides structured execution for Policy to govern      │
│  • Skills expose capabilities for RBAC to restrict                  │
│  • Traces enable replay for determinism verification                │
│                                                                      │
│  SAFETY ──────► OPERATIONS                                          │
│  • Policy violations create incidents for Ops                       │
│  • SBA validation failures feed Recovery suggestions                │
│  • CARE routing adjustments show in Guard console                   │
│                                                                      │
│  OPERATIONS ──────► ARCHITECTURE                                    │
│  • Recovery suggestions improve skill error handling                │
│  • Cost intelligence informs budget constraints                     │
│  • Failure patterns drive skill contract improvements               │
│                                                                      │
│  ALL ──────► DEVELOPER EXPERIENCE                                   │
│  • Every component exports metrics for SDK                          │
│  • Prevention system enforces quality across all                    │
│  • Memory PINs document decisions from all pillars                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Positive Feedback Loops

1. **Incident → Prevention Loop** (M25 proven)
   - Incident created → Pattern matched → Recovery suggested → Policy generated → Prevention enforced
   - **Proof:** PIN-140 shows real incident → real prevention

2. **Cost → Budget Loop** (M27)
   - Cost anomaly detected → Budget adjusted → Spending reduced → Anomaly prevented

3. **SBA → CARE-L Loop** (M18)
   - Agent performance tracked → Reputation updated → Routing adjusted → Performance improved

---

## Component Relationships: Potential Conflicts

### Known Friction Points

```
┌─────────────────────────────────────────────────────────────────────┐
│                      POTENTIAL CONFLICTS                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. PLANNER_BACKEND = "stub" (DEFAULT)                              │
│     ├── Workflow can execute                                        │
│     ├── But plans are static test plans                             │
│     └── Real LLM planning disabled until env var set                │
│                                                                      │
│  2. CARE Routing NOT in API layer                                   │
│     ├── Only wired to: workers.py:661, worker.py:141                │
│     ├── General API calls bypass CARE                               │
│     └── Routing only affects worker execution path                  │
│                                                                      │
│  3. Memory Features OFF by default                                  │
│     ├── MEMORY_CONTEXT_INJECTION = "false"                          │
│     ├── MEMORY_POST_UPDATE = "false"                                │
│     └── Agents don't learn from memory unless enabled               │
│                                                                      │
│  4. Tenants Router DISABLED                                         │
│     ├── M21 disabled: "Premature for beta stage"                    │
│     └── Multi-tenant isolation exists but API disabled              │
│                                                                      │
│  5. Event Publisher = "logging" (DEFAULT)                           │
│     ├── Events logged but not published to Redis                    │
│     └── Real-time features require REDIS publisher                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Dependency Chain Risks

| Chain | Risk | Mitigation |
|-------|------|------------|
| Policy → Routing | If Policy evaluates slow, routing blocks | MAX_EVALUATION_TIME_MS = 100 |
| Recovery → Policy | Bad recovery → bad policy | 3 confirmations required |
| Cost → Budget | Over-aggressive limits → blocked users | Guardrails in place |
| SBA → CARE | Invalid SBA → routing failures | validate_at_spawn() |

---

## Verified Wiring Matrix

### What Calls What (Verified by grep)

| Caller | Calls | Evidence |
|--------|-------|----------|
| `api/policy_layer.py` | PolicyEngine | ✅ Verified |
| `api/agents.py` | SBAService | ✅ Verified |
| `api/recovery.py` | RecoveryMatcher | ✅ Verified |
| `api/workers.py` | RecoveryMatcher, CareRouter | ✅ Verified |
| `workers/business_builder/worker.py` | CareRouter, PolicyEngine, RecoveryMatcher | ✅ Verified |
| `integrations/bridges.py` | All services | ✅ Verified |

### What's NOT Wired (Gaps)

| Component | Expected Wiring | Actual | Gap? |
|-----------|----------------|--------|------|
| CARE Router | All API endpoints | Workers only | ⚠️ DESIGN DECISION |
| Policy Engine | All decisions | Bridges + explicit calls | ⚠️ Not automatic |
| Memory Context | All agents | Off by default | ⚠️ NEEDS ENV VAR |
| LLM Planner | Plan generation | Stub by default | ⚠️ NEEDS ENV VAR |

---

## Defaults That Need Changing for Production

### Environment Variables OFF by Default

| Variable | Default | Production Value | Why |
|----------|---------|------------------|-----|
| `PLANNER_BACKEND` | "stub" | "llm" | Enable real planning |
| `MEMORY_CONTEXT_INJECTION` | "false" | "true" | Enable agent memory |
| `MEMORY_POST_UPDATE` | "false" | "true" | Enable memory updates |
| `DRIFT_DETECTION_ENABLED` | "false" | "true" | Detect configuration drift |
| `CALENDAR_PROVIDER` | "mock" | "google"/"microsoft" | Real calendar |
| `EVENT_PUBLISHER` | "logging" | "redis" | Real-time events |

### Features Disabled

| Feature | Reason | Impact |
|---------|--------|--------|
| Tenants Router (M21) | "Premature for beta" | No tenant management API |
| Deprecated SBA versions | None defined | All versions work |

---

## How It's Supposed to Work (Human Testing Flow)

### Happy Path

```
USER ACTION                     SYSTEM RESPONSE
───────────────────────────────────────────────────────────────────
1. User creates API key     →   Key stored, tier assigned (M32)
2. User calls /v1/chat      →   Proxy intercepts (M22)
3. Proxy checks policy      →   Policy Engine evaluates (M19)
4. Request allowed          →   Forward to LLM
5. LLM responds             →   Cost recorded (M26)
6. Response to user         →   Latency/tokens logged
7. (If error)               →   Incident created (M25 Bridge 1)
8. Pattern matched          →   Recovery suggested (M25 Bridge 2)
9. Policy generated         →   Shadow mode (M25 Bridge 3)
10. 3 occurrences           →   Policy ACTIVE (M25 Bridge 3)
11. Next similar request    →   BLOCKED (Prevention)
12. User sees in Console    →   Guard Console (M23)
```

### Unhappy Paths (Designed Behaviors)

| Scenario | Expected Behavior | Evidence |
|----------|------------------|----------|
| Budget exceeded | Request blocked, error returned | `v1_proxy.py` checks |
| Rate limited | 429 returned with retry-after | `rate_limit.py` |
| Policy violation | Request blocked, incident created | `policy/engine.py` |
| SBA invalid | Agent spawn blocked | `validate_at_spawn()` |
| Recovery failed | Incident stays in catalog | Bridge 2 failure state |
| Novel pattern | Human checkpoint required | `ConfidenceBand.NOVEL` |

---

## Missing/Pending Items

### P0 - Must Have for Human Testing

| Item | Current State | Impact |
|------|---------------|--------|
| Set `PLANNER_BACKEND=llm` | Defaults to stub | No real planning |
| Set `ANTHROPIC_API_KEY` | Not set = stub mode | LLM calls fail |
| Run migrations | Must be current | DB schema issues |

### P1 - Should Have

| Item | Current State | Impact |
|------|---------------|--------|
| Enable memory features | Off by default | No learning |
| Set event publisher to Redis | Logging only | No real-time UI |
| Enable drift detection | Off | No config monitoring |

### P2 - Nice to Have

| Item | Current State | Impact |
|------|---------------|--------|
| Enable M21 tenants API | Disabled | No tenant mgmt UI |
| Real calendar provider | Mock | Calendar skill stubs |

---

## Summary: The Mental Model

### The Core Invariant (PIN-140)

> **Every incident can become a prevention, without manual runtime intervention.**

This is what M25 proves. The system is designed to:

1. **Observe** - Capture incidents with structured metadata
2. **Correlate** - Match patterns across incidents
3. **Suggest** - Generate recovery recommendations
4. **Protect** - Create and activate policies
5. **Prevent** - Block repeat failures automatically

### Pillar Interaction Summary

| Interaction | Type | Strength |
|-------------|------|----------|
| Architecture → Safety | Complementary | Strong - workflows enforce policies |
| Safety → Operations | Complementary | Strong - violations create incidents |
| Operations → Architecture | Complementary | Medium - recoveries improve skills |
| CARE ↔ SBA | Bidirectional | Strong - routing uses SBA, SBA learns from routing |
| Policy ↔ Bridges | Bidirectional | Strong - policies from bridges, bridges check policy |
| Cost ↔ Budget | Negative Feedback | Medium - anomalies trigger limits |

### What Could Break

1. **Missing API keys** → Stub mode, no real intelligence
2. **Memory disabled** → Agents don't learn
3. **Wrong planner backend** → Static test plans
4. **Redis unavailable** → Rate limiting degraded, no real-time
5. **Migrations not run** → Schema mismatches

---

## Related PINs

- PIN-140: M25 Complete - Rollback Safe (proves the loop works)
- PIN-163: M0-M28 Utilization Report (component verification)
- PIN-128: Master Plan M25-M32 (roadmap)
- PIN-122: Master Milestone Compendium (history)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-25 | Initial creation - Mental model with verified wiring |
