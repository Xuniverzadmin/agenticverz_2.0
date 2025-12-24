# PIN-128: Master Plan - M25 to M32

**Status:** STRATEGIC
**Category:** Planning / Architecture / Roadmap
**Created:** 2025-12-22
**Related PINs:** PIN-123, PIN-124, PIN-095, PIN-033, PIN-154, PIN-155

---

## The Strategic Question

> Build missing components (Cost View) first, then integrate?
> Or integrate existing pillars first, then build missing?

---

## Current State Analysis

### What's Built (M0-M24)

| Pillar | Components | Completeness |
|--------|------------|--------------|
| **Incident Console** | M22 KillSwitch, M23 Guard Console, Decision Timeline, Evidence Export | 95% |
| **Self-Healing** | M9 Failure Catalog, M10 Recovery Engine, Pattern Matching | 85% |
| **Governance** | M19 Policy Layer, M15 SBA, M17-18 CARE Routing | 90% |
| **Cost Tracking** | M13 Cost Calculator, M14 BudgetLLM | 60% (backend only) |

### What's Missing

| Component | Effort | Infrastructure Exists? |
|-----------|--------|------------------------|
| Cost Intelligence Dashboard | 1 week | Yes (M13 backend) |
| Pillar Integration (wiring) | 2 weeks | Partial |
| Quality Evidence Pack | 3 weeks | Partial (M11 LLM skills) |
| Trust Badge | 1 week | Needs all pillars |

---

## Recommendation: INTEGRATE FIRST

### Why Integration Before Building

| Factor | Build First | Integrate First |
|--------|-------------|-----------------|
| **Risk Discovery** | Late (after building) | Early (before building) |
| **Wasted Work** | High (may not fit) | Low (build what's needed) |
| **Time to Value** | Longer (complete then wire) | Shorter (cohesive core) |
| **Customer Signal** | Hypothetical | Real (what's actually broken) |
| **Refactoring** | Major (post-integration) | Minor (iterative) |

### The Integration-First Principle

```
WRONG:  Build A → Build B → Build C → Wire A+B+C
RIGHT:  Wire A+B → Discover gaps → Build C to fill gaps → Wire C
```

### Why This Works for Agenticverz

1. **Three pillars already exist** - Incident, Self-Healing, Governance are built but isolated
2. **Integration reveals real gaps** - You'll discover what's actually missing, not hypothetical
3. **Cost View is 60% done** - It's mostly a dashboard exercise, not new backend
4. **Quality Evidence Pack is speculative** - Don't build until customers ask for it

---

## Master Plan: M25-M30

### Phase 1: Integration (M25)

**M25: Pillar Integration - "The Wire"**

Wire the existing three pillars into a feedback loop:

```
Incident Console ──────────────────────► Failure Catalog
     │                                        │
     │ "What went wrong"                      │ "Pattern detected"
     │                                        │
     ▼                                        ▼
Kill Switch ◄─────────────────────────── Recovery Engine
     │                                        │
     │ "Block this"                           │ "Fix suggested"
     │                                        │
     ▼                                        ▼
Policy Layer ◄─────────────────────────── CARE Routing
     │                                        │
     │ "New rule created"                     │ "Route adjusted"
     │                                        │
     └────────────────────────────────────────┘
                     FEEDBACK LOOP
```

**Deliverables:**
1. Incident → Failure Catalog auto-ingestion
2. Pattern → Recovery Suggestion display in Console
3. Recovery → Policy rule generation
4. Policy → CARE routing adjustment
5. Integration tests proving the loop

**Duration:** 2 weeks
**Risk:** Medium (discovering hidden gaps)

---

### Phase 2: Cost View (M26)

**M26: Cost Intelligence Dashboard**

Build the missing Pillar 0 - but AFTER integration proves the pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│  AI COST INTELLIGENCE                        December 2025     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Total Spend: $4,847          Budget: $5,000    [██████████░]  │
│                                                                 │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │ COST BY FEATURE         │  │ COST ANOMALIES              │  │
│  │ Customer Support $2,100 │  │ ⚠️ user_8372: $89 today     │  │
│  │ Content Gen      $1,500 │  │ ⚠️ Content Gen +340%        │  │
│  │ Code Assistant     $800 │  │ ✓ Code Assistant normal     │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
│                                                                 │
│  COST PER USER: $0.12/user/day (avg)                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**What Already Exists (60%):**
- M13: Cost tracking per call
- M14: BudgetLLM governance
- M21: Tenant tracking

**What to Build (40%):**
- Feature tagging API
- Cost attribution dashboard
- Budget alerts (extend M5 policies)
- Cost anomaly detection (reuse M9 patterns)
- Cost projection logic

**Duration:** 1.5 weeks
**Risk:** Low (infrastructure exists)

---

### Phase 3: Cost Integration (M27)

**M27: Cost → Loop Integration**

Wire Cost Intelligence into the feedback loop:

```
Cost Anomaly ("User X spent $89")
     │
     ▼
Auto-create Incident ("Unusual AI spend")
     │
     ▼
Decision Timeline shows root cause
     │
     ▼
Recovery Suggestion ("Chunk documents before summarization")
     │
     ▼
Policy Rule ("Block requests > $1 per call")
     │
     ▼
CARE Routing ("Route expensive tasks to cheaper models first")
```

**Deliverables:**
1. Cost anomaly → Incident auto-creation
2. Cost patterns in Failure Catalog
3. Cost-aware recovery suggestions
4. Budget-enforcement policies
5. Cost-optimizing CARE routing

**Duration:** 1 week
**Risk:** Low (pattern established in M25)

---

### Phase 4: Unified Console (M28)

**M28: One Console, Four Views**

Rebrand as unified system, not separate products:

```
┌─────────────────────────────────────────────────────────────────┐
│  AGENTICVERZ CONTROL CENTER                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [COST] [INCIDENT] [SELF-HEAL] [GOVERNANCE]                    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │              CURRENTLY SELECTED VIEW                    │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  CROSS-CUTTING METRICS                                          │
│  ├─ Active Incidents: 3                                        │
│  ├─ Recovery Suggestions: 12 pending                           │
│  ├─ Policies Active: 47                                        │
│  └─ Cost This Month: $4,847 / $5,000                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Change:** Add `actor_id` (human/agent/system) to every event.

**Deliverables:**
1. Unified navigation (four views, one console)
2. Cross-view metrics strip
3. Actor attribution on all events
4. View-to-view deep linking
5. Unified search across all pillars

**Duration:** 1.5 weeks
**Risk:** Low (UI consolidation)

---

### Phase 5: Quality Evidence Pack (M29) - CONDITIONAL

**M29: Quality Evidence Pack (Only If Customers Demand)**

Don't build until you hear "Is our AI accurate?" from 3+ customers.

```
┌─────────────────────────────────────────────────────────────────┐
│  QUALITY EVIDENCE PACK                       Last 7 Days       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Overall Quality: 94.2%        ▲ +1.3% from last week          │
│                                                                 │
│  ACCURACY        [████████████████████░░░░]  87%               │
│  RELEVANCE       [██████████████████████░░]  92%               │
│  SAFETY          [████████████████████████]  99.7%             │
│                                                                 │
│  ISSUES DETECTED: 23 potential hallucinations                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Requires:**
- Feedback API (thumbs up/down)
- LLM-as-judge evaluation (M11 skills)
- Ground truth dataset
- Hallucination detection

**Duration:** 3 weeks
**Risk:** High (new infrastructure)

---

### Phase 6: Trust Badge (M30) - CONDITIONAL

**M30: Customer Trust Badge (Enterprise Upsell)**

Only after all pillars are integrated:

```
┌─────────────────────────────────────────────┐
│                                             │
│   🛡️ Protected by Agenticverz             │
│                                             │
│   ✓ 99.7% Response Accuracy                │
│   ✓ 0 Safety Incidents (Last 30 Days)      │
│   ✓ $0.08 Average Cost Per Interaction     │
│   ✓ <2s Average Response Time              │
│                                             │
│   [View Full Report]  [Verify Certificate] │
│                                             │
└─────────────────────────────────────────────┘
```

**Duration:** 1 week
**Risk:** Low (aggregation of existing data)

---

## Timeline Summary

| Milestone | Name | Duration | Dependencies | Priority |
|-----------|------|----------|--------------|----------|
| M25 | Pillar Integration | 2 weeks | M22-M24 | **P0 - DO FIRST** |
| M26 | Cost Intelligence | 1.5 weeks | M13, M25 | P0 |
| M27 | Cost → Loop | 1 week | M25, M26 | P0 |
| M28 | Unified Console | 1.5 weeks | M25-M27 | P1 |
| M29 | Quality Evidence Pack | 3 weeks | M28 | P2 (conditional) |
| M30 | Trust Badge | 1 week | M28-M29 | P2 (conditional) |
| M31 | Key Safety Contract | 2 weeks | M22, M26/27 | P1 (trust foundation) |
| M32 | Tier Infrastructure | 1.5 weeks | M8, M29 | P1 (monetization plumbing) |

**Total (P0 only):** 6 weeks
**Total (P0+P1):** 11 weeks
**Total (all):** 15 weeks

---

## Decision Framework

### Build Now (M25-M28, M31, M32)
- Pillar Integration - core value proposition
- Cost Intelligence - 60% exists, universal pain
- Cost → Loop - completes feedback cycle
- Unified Console - marketable as "one product"
- Key Safety Contract - trust foundation for proxy customers
- Tier Infrastructure - monetization plumbing (gates, meters, limits)

### Build If Asked (M29-M30)
- Quality Evidence Pack - only if 3+ customers ask "Is our AI accurate?"
- Trust Badge - only for enterprise deals requiring certification

### Never Build (Until Revenue)
- Model comparison dashboard
- Multi-cloud cost optimization
- Compliance reporting

---

## The One-Page Answer

**Question:** Build missing, then integrate? Or integrate, then build?

**Answer:** INTEGRATE FIRST.

**Sequence:**
```
M25: Wire existing pillars → discover real gaps
M26: Build Cost View → it's 60% done anyway
M27: Wire Cost into loop → complete the cycle
M28: Unify the console → one product, four views
```

**Why:**
1. Integration reveals what's actually missing (not hypothetical)
2. Cost View is mostly dashboard (backend exists)
3. Quality Evidence Pack is speculative (wait for demand)
4. Ship faster (6 weeks to complete core vs 12 weeks building first)

**The Invariant:**
> Every token attributable to one identity.
> Every identity visible in one console.
> Every action feedable back into the loop.

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-24 | Added M32 Tier Infrastructure to roadmap (P1, 1.5 weeks, monetization plumbing) |
| 2025-12-24 | Added M31 Key Safety Contract to roadmap (P1, 2 weeks, trust foundation) |
| 2025-12-24 | M29 renamed: "Quality Score" → "Quality Evidence Pack" per expert review |
| 2025-12-22 | Created PIN-128 with M25-M30 master plan |
