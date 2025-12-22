# PIN-124: Unified Identity Hybrid Architecture - Strategic Analysis

**Status:** STRATEGIC
**Created:** 2025-12-22
**Category:** Architecture / Strategy / Product
**Author:** Claude Opus 4.5
**Depends On:** PIN-122, PIN-123

---

## Executive Summary

This PIN synthesizes multiple strategic analyses to arrive at a **Unified Identity Hybrid Architecture** that combines:
1. GPT's identity-centric simplicity
2. AOS's deep capabilities (self-healing, governance, replay)
3. Market-ready positioning

**Core Insight:** Identity attribution should be the **foundation**, not a feature. Everything else is a **view** into that foundation.

---

## Analysis Journey

### Phase 1: Three Pillars (PIN-123)

Initial analysis identified three product pillars:

| Pillar | Product | Price | Core Value |
|--------|---------|-------|------------|
| **1** | AI Incident Console | $299/mo | Investigate AI failures like plane crashes |
| **2** | Self-Healing Platform | $599/mo | Agents that learn from mistakes |
| **3** | Governance Layer | $1,499/mo | Constitutional AI for enterprise |

**Problem Identified:** Pillars complement but have integration gaps.

### Phase 2: Missing Pillar 0

Analysis revealed a critical missing piece:

| Pillar | Product | Price | Core Value |
|--------|---------|-------|------------|
| **0** | AI Cost Intelligence | $99/mo | Know what AI costs before it runs |

**Insight:** Cost Intelligence is the gateway product - lowest friction, highest volume, upsell path to other pillars.

### Phase 3: GPT's Unified Control Cluster

External analysis proposed a different approach:

**Single Invariant:** "Every token spend, output, or failure must be attributable to exactly one identity (human, agent, or system)."

**Strengths:**
- Clean architectural principle
- Identity-centric model (Human/Agent/System)
- API Key as universal gateway
- No parallel systems
- Unified data model

**Weaknesses:**
- Breaks on agent-to-agent delegation chains
- No multi-tenant support
- No self-healing or learning
- No governance escalation
- No deterministic replay
- Tracks history but doesn't improve

**Verdict:** GPT built an accounting system, not an operating system.

### Phase 4: Hybrid Synthesis (This PIN)

Combining the best of both approaches into a unified architecture.

---

## Unified Identity Hybrid Architecture

### Core Principle

> **Every event in the system has exactly one owner (human, agent, or system) within exactly one tenant. All features are views into this unified event stream.**

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       UNIFIED IDENTITY LAYER                             │
│                                                                          │
│   Every event has: actor_id + actor_type + tenant_id + timestamp        │
│   Actor types: HUMAN | AGENT | SYSTEM                                    │
│   Immutable. Append-only. Cryptographically signed.                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ (events flow down)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY (M22 Proxy)                           │
│                                                                          │
│   - Single entry point for all AI calls                                 │
│   - API key validation + tenant resolution                              │
│   - Kill switch capability                                              │
│   - Rate limiting + circuit breakers                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────┬───────────┴───────────┬───────────────┐
        ▼               ▼                       ▼               ▼
┌─────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  COST VIEW  │ │  INCIDENT VIEW  │ │ SELF-HEAL VIEW  │ │ GOVERNANCE VIEW │
│  (Pillar 0) │ │   (Pillar 1)    │ │   (Pillar 2)    │ │   (Pillar 3)    │
│             │ │                 │ │                 │ │                 │
│ Per-identity│ │ Per-identity    │ │ Cross-identity  │ │ Per-identity    │
│ token spend │ │ failures +      │ │ pattern match + │ │ policy evals +  │
│ + forecast  │ │ replay +        │ │ recovery +      │ │ escalations +   │
│ + alerts    │ │ evidence        │ │ auto-apply      │ │ approvals       │
└─────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
       │               │                    │                    │
       └───────────────┴────────────────────┴────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │       FEEDBACK LOOPS          │
                    │                               │
                    │ 1. Incident → Failure Catalog │
                    │ 2. Recovery → Policy Promote  │
                    │ 3. Policy Block → Incident    │
                    │ 4. Cost Spike → Alert         │
                    └───────────────────────────────┘
```

### Data Model

```sql
-- Foundation: Unified Identity Layer
CREATE TABLE identities (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    actor_type VARCHAR(10) NOT NULL CHECK (actor_type IN ('HUMAN', 'AGENT', 'SYSTEM')),
    actor_id VARCHAR(255) NOT NULL,  -- user_id, agent_id, or system_name
    api_key_hash VARCHAR(64),        -- for API key attribution
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Core: Unified Event Stream
CREATE TABLE events (
    id UUID PRIMARY KEY,
    identity_id UUID NOT NULL REFERENCES identities(id),
    tenant_id UUID NOT NULL,         -- denormalized for partitioning
    event_type VARCHAR(50) NOT NULL, -- 'llm_call', 'policy_eval', 'incident', etc.
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Common fields
    tokens_in INTEGER,
    tokens_out INTEGER,
    cost_usd DECIMAL(10,6),
    duration_ms INTEGER,

    -- Type-specific payload
    payload JSONB NOT NULL,

    -- Traceability
    trace_id UUID,
    parent_event_id UUID REFERENCES events(id),

    -- Integrity
    signature VARCHAR(64) NOT NULL   -- HMAC for tamper detection
);

-- Indexes for each view
CREATE INDEX idx_events_cost ON events(tenant_id, identity_id, timestamp) WHERE cost_usd IS NOT NULL;
CREATE INDEX idx_events_incidents ON events(tenant_id, event_type, timestamp) WHERE event_type = 'incident';
CREATE INDEX idx_events_policy ON events(tenant_id, event_type, timestamp) WHERE event_type = 'policy_eval';
```

### View Definitions

Each pillar is a **materialized view** into the unified event stream:

```sql
-- Pillar 0: Cost View
CREATE MATERIALIZED VIEW cost_summary AS
SELECT
    tenant_id,
    identity_id,
    DATE_TRUNC('hour', timestamp) as hour,
    SUM(tokens_in) as total_tokens_in,
    SUM(tokens_out) as total_tokens_out,
    SUM(cost_usd) as total_cost,
    COUNT(*) as call_count
FROM events
WHERE event_type = 'llm_call'
GROUP BY tenant_id, identity_id, DATE_TRUNC('hour', timestamp);

-- Pillar 1: Incident View
CREATE MATERIALIZED VIEW incident_summary AS
SELECT
    tenant_id,
    identity_id,
    payload->>'error_code' as error_code,
    payload->>'severity' as severity,
    COUNT(*) as occurrence_count,
    MAX(timestamp) as last_occurrence
FROM events
WHERE event_type = 'incident'
GROUP BY tenant_id, identity_id, payload->>'error_code', payload->>'severity';

-- Pillar 2: Self-Heal View (patterns across identities)
CREATE MATERIALIZED VIEW failure_patterns AS
SELECT
    tenant_id,
    payload->>'error_code' as error_code,
    payload->>'context_hash' as context_hash,
    COUNT(DISTINCT identity_id) as affected_identities,
    COUNT(*) as total_occurrences,
    ARRAY_AGG(DISTINCT identity_id) as identity_list
FROM events
WHERE event_type = 'incident'
GROUP BY tenant_id, payload->>'error_code', payload->>'context_hash'
HAVING COUNT(*) >= 3;  -- Pattern threshold

-- Pillar 3: Governance View
CREATE MATERIALIZED VIEW policy_decisions AS
SELECT
    tenant_id,
    identity_id,
    payload->>'policy_id' as policy_id,
    payload->>'decision' as decision,
    COUNT(*) as eval_count,
    COUNT(*) FILTER (WHERE payload->>'decision' = 'DENY') as deny_count
FROM events
WHERE event_type = 'policy_eval'
GROUP BY tenant_id, identity_id, payload->>'policy_id', payload->>'decision';
```

---

## Product Positioning

### One Console, Four Views

**Tagline:** "One AI console. Complete visibility. Every token tracked."

**Not four products. One product with four views:**

| View | Question It Answers | Persona |
|------|---------------------|---------|
| **Cost** | "How much is AI costing me?" | Finance, Founders |
| **Incident** | "What went wrong and why?" | Engineering, Safety |
| **Self-Heal** | "Can this fix itself?" | Platform, Ops |
| **Governance** | "Is AI following the rules?" | Compliance, Legal |

### Pricing Strategy (Unified)

| Tier | Price | Includes | Target |
|------|-------|----------|--------|
| **Starter** | $99/mo | Cost View only + 10K calls | Individual developers |
| **Team** | $299/mo | Cost + Incident Views + 100K calls | Small teams |
| **Business** | $599/mo | All views + Self-Heal + 500K calls | Growing companies |
| **Enterprise** | $1,499/mo | All views + Governance + SLA + Unlimited | Enterprise |

**Upsell Path:**
```
Starter ($99) → "Seeing high costs? See why with Incident View" → Team ($299)
Team ($299) → "Same errors repeating? Enable Self-Heal" → Business ($599)
Business ($599) → "Need compliance audit trail?" → Enterprise ($1,499)
```

---

## Implementation Mapping

### What We Already Have (M0-M24)

| Capability | Milestone | Maps To |
|------------|-----------|---------|
| Deterministic execution | M0-M4 | All views (replay) |
| Skill circuit breakers | M11 | Self-Heal View |
| Failure catalog | M9 | Self-Heal View |
| Recovery suggestions | M10 | Self-Heal View |
| Policy layer | M19 | Governance View |
| SBA/CARE routing | M15-M18 | Governance View |
| Kill switch | M22 | Gateway |
| Decision timeline | M23 | Incident View |
| Evidence export | M23 | Incident View |
| Credit billing | M12 | Cost View |
| Tenant/Auth | M21 | Identity Layer |

### What We Need to Build

| Component | Priority | Effort | Description |
|-----------|----------|--------|-------------|
| **Unified Event Stream** | P0 | Medium | Single events table with identity_id |
| **Identity Resolution** | P0 | Low | Map API keys → identities |
| **Cost Forecast** | P1 | Medium | Predict spend based on patterns |
| **Cross-Identity Patterns** | P1 | Medium | Failure patterns across actors |
| **View Materializations** | P2 | Low | SQL views for each pillar |
| **Feedback Loop Automation** | P2 | Medium | Auto-feed between views |

---

## Competitive Differentiation

### vs. LangSmith (Tracing)
- They trace. We **attribute** (every token has an owner).
- They show history. We **predict** and **prevent**.

### vs. Guardrails AI (Validation)
- They validate outputs. We **govern the entire lifecycle**.
- They're a library. We're an **operating system**.

### vs. AgentOps (Observability)
- They observe. We **heal**.
- They track metrics. We **learn from failures**.

### vs. Custom Solutions
- They build from scratch. We provide **turnkey identity attribution**.
- They maintain infrastructure. We **scale automatically**.

---

## Success Metrics

### Technical Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Event ingestion latency | <50ms | Prometheus p99 |
| Identity resolution accuracy | 100% | No orphan events |
| View refresh time | <5min | Materialization lag |
| Cross-identity pattern detection | <1hr | Time to first pattern |

### Business Metrics

| Metric | 30-Day | 90-Day | 180-Day |
|--------|--------|--------|---------|
| Starter signups | 100 | 500 | 2000 |
| Paid conversions | 10 | 50 | 200 |
| MRR | $1,000 | $10,000 | $50,000 |
| Upsell rate | - | 20% | 30% |

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Event volume overwhelms DB | Medium | High | Partition by tenant + time |
| Identity resolution gaps | Low | High | Strict API key validation |
| View refresh too slow | Medium | Medium | Incremental refresh |
| Feature sprawl returns | High | Medium | Enforce "view not product" |
| Pricing confusion | Medium | Medium | Clear tier comparison |

---

## Next Steps

### Immediate (This Week)
1. [ ] Add `actor_type` enum to existing events
2. [ ] Create identity resolution from API keys
3. [ ] Build Cost View materialized query
4. [ ] Update console to show "Views" not "Products"

### Short-term (Next 2 Weeks)
1. [ ] Implement unified event stream migration
2. [ ] Build cross-identity pattern detection
3. [ ] Create feedback loop: Incident → Failure Catalog
4. [ ] Launch Starter tier ($99) with Cost View only

### Medium-term (Next Month)
1. [ ] Complete all four view materializations
2. [ ] Implement cost forecasting
3. [ ] Build upsell prompts in UI
4. [ ] Launch Team tier ($299)

---

## Appendix: Comparison Matrix

| Dimension | GPT Approach | Original Pillars | Hybrid (This PIN) |
|-----------|--------------|------------------|-------------------|
| Core principle | Single invariant | Feature domains | Identity + Views |
| Data model | Identity-centric | Feature-centric | Event stream + Views |
| Scalability | Unclear | Proven (SKIP LOCKED) | Proven + Partitioned |
| Self-healing | None | Full (M9-M10) | Full + Cross-identity |
| Governance | None | Full (M15-M19) | Full |
| Cost control | Track only | Track + Bill | Track + Forecast + Alert |
| Marketing | Confusing | Complex (4 products) | Simple (1 product, 4 views) |
| Implementation | Rebuild needed | Already built | Refactor existing |

---

## Related PINs

- PIN-122: Master Milestone Compendium (M0-M21)
- PIN-123: Strategic Product Plan 2025
- PIN-100: M23 AI Incident Console
- PIN-089: M21 Tenant, Auth & Billing

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-22 | Initial hybrid architecture created |

---

*PIN-124: Unified Identity Hybrid Architecture - One console, four views, every token tracked.*
