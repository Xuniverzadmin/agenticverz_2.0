# PIN-085: Worker Brainstorm & Moat Audit

**Date:** 2025-12-15
**Status:** DECISION MADE
**Context:** Product Strategy Brainstorm
**Dependency:** M0-M20 Complete

---

## Overview

Brainstorming session to identify what product to build on top of Agenticverz M0-M20 that:
1. Validates the Agent OS works in real-world scenarios
2. Demonstrates market value (not just SDK/OS)
3. Showcases unique capabilities (moats)

---

## GPT's Proposal: "Idea to Research to Launch Package Worker"

### Concept
A worker that takes an ambiguous business idea and produces a complete launch package:
- Market research
- Competitive analysis
- Brand positioning
- Landing page (deployed to Netlify)
- Blog posts
- SEO plan
- GTM strategy
- 15+ artifacts total

### GPT's Claimed Moat Usage
GPT claimed this would use "ALL M0-M20 moats" including:
- M4 AXE for orchestration
- M9 SFIL for pattern detection
- M10 Recovery for self-healing
- M12 Multi-Agent for specialists
- M15 SBA for strategy adherence
- M17 CARE for routing
- M18 CARE-L for learning
- M19/M20 for governance

---

## Moat Audit: 35 Unique Capabilities

Before evaluating the proposal, a comprehensive audit of M0-M20 identified **35 unique moats**:

### 15 Individual Moats

| # | Moat | Source | Description |
|---|------|--------|-------------|
| 1 | Deterministic Execution | M4 | Reproducible agent runs with seed control |
| 2 | Failure Pattern Catalog | M9 | Indexed failure patterns with R2 durability |
| 3 | Recovery Suggestion Engine | M10 | Auto-suggest fixes based on failure history |
| 4 | Multi-Skill Composition | M11 | Composable skills (slack, webhook, embed, kv) |
| 5 | Credit-Based Multi-Agent | M12 | Budget-aware agent spawning |
| 6 | Strategy-Bound Agents | M15 | Agents bound to organizational strategy |
| 7 | CARE Complexity Routing | M17 | Route by task complexity, not just type |
| 8 | CARE-L Evolution | M18 | Learning loop for routing improvement |
| 9 | Policy Constitutional | M19 | 5-category governance (SAFETY/PRIVACY/OPERATIONAL/ROUTING/CUSTOM) |
| 10 | PLang Compiler | M20 | Domain-specific policy language |
| 11 | Deterministic Runtime | M20 | No-randomness, step-based execution |
| 12 | Intent System | M20 | Structured action emission |
| 13 | Governance DAG | M20 | Category-ordered policy evaluation |
| 14 | IAEC Embeddings | M7+ | 4-slot instruction-aware embeddings |
| 15 | Temporal Mediation | IAEC v3.1 | Cross-version embedding transformation |

### 15 Combined Moats (Synergies)

| # | Combination | Moats Used | Unique Value |
|---|-------------|------------|--------------|
| 16 | Self-Healing Execution | M4 + M9 + M10 | Deterministic replay + failure catalog + auto-recovery |
| 17 | Governed Multi-Agent | M12 + M19 + M20 | Multi-agent with policy enforcement |
| 18 | Strategic Routing | M15 + M17 | Route based on strategy + complexity |
| 19 | Learning Governance | M18 + M19 | Evolve routing under policy constraints |
| 20 | Skill Orchestration | M4 + M11 + M12 | Multi-skill, multi-agent workflows |
| 21 | Failure-Aware Routing | M9 + M17 | Route away from failing patterns |
| 22 | Policy-Constrained Recovery | M10 + M19 | Suggest recovery within governance bounds |
| 23 | Strategic Evolution | M15 + M18 | Evolve while maintaining strategy alignment |
| 24 | Governed Skill Execution | M11 + M19 + M20 | Skills execute under policy control |
| 25 | Deterministic Governance | M4 + M20 | Reproducible policy evaluation |
| 26 | Intent-Driven Routing | M17 + M20 | Route based on policy intents |
| 27 | Multi-Agent Learning | M12 + M18 | Agents learn from each other |
| 28 | Failure Pattern Learning | M9 + M18 | Catalog feeds evolution loop |
| 29 | Strategy-Governed Recovery | M10 + M15 + M19 | Recovery suggestions aligned to strategy + policy |
| 30 | Full-Stack Governance | M19 + M20 + M17 | Policy → Runtime → Routing |

### 5 Compound Moats (3+ Combined)

| # | Compound | Moats | Description |
|---|----------|-------|-------------|
| 31 | Autonomous Self-Healing | M4+M9+M10+M17 | Detect failure, catalog it, suggest fix, route around it |
| 32 | Governed Agent Evolution | M12+M15+M18+M19 | Multi-agent that evolves under strategy + policy |
| 33 | Full Governance Stack | M17+M18+M19+M20 | Route → Evolve → Govern → Execute |
| 34 | Strategic Failure Recovery | M9+M10+M15+M19 | Failure → Catalog → Recover → Align to strategy |
| 35 | Complete Agent OS | ALL | Only system with all 35 capabilities |

---

## Critique: GPT's Proposal Uses ~15% of Moats

| Moat | GPT Claimed | Reality |
|------|-------------|---------|
| M4 AXE | "Orchestrates" | Yes - basic workflow |
| M9 SFIL | "Pattern detection" | No - greenfield generation, no failures to catalog |
| M10 Recovery | "Self-healing" | No - no recovery scenarios |
| M11 Skills | "Webhook, embed" | Partial - 2 of 5 skills |
| M12 Multi-Agent | "Researcher + Writer" | Weak - could be single agent with tools |
| M15 SBA | "Strategy adherent" | No - no strategy to bind to |
| M17 CARE | "Routes to specialists" | Forced - no real complexity variance |
| M18 CARE-L | "Learns preferences" | No - one-shot generation |
| M19 Policy | "Governance" | No - no sensitive decisions |
| M20 PLang | "Policy execution" | No - no policies to evaluate |

**Honest assessment: 2-3 moats actually exercised**

### Why the Proposal Falls Short

1. **Linear workflow** - No branching decisions that need governance
2. **No failure scenarios** - Content generation rarely fails catastrophically
3. **One-shot execution** - No learning loop opportunity
4. **No constraints** - No budget/strategy/policy to enforce
5. **Replicable with LangChain** - GPT-4 + web search + templates achieves same result

---

## Revised Approach: Phased Worker

| Phase | Product | Moats Exercised |
|-------|---------|-----------------|
| Phase 1 | Launch Package Worker (GPT's idea) | M4, M11, M12 (basic) |
| Phase 2 | + Budget constraints + brand guidelines | + M15, M19 |
| Phase 3 | + Track conversion, learn from failures | + M9, M18 |
| Phase 4 | + Full governance, complexity routing | + M17, M20 |

Start simple, layer complexity as users demand it.

---

## Alternative Domains (Higher Moat Utilization)

### Option A: Sales Pipeline Manager
- Qualify leads → Route to reps → Enforce discount policies → Learn from won/lost
- **Moats:** M4, M9, M10, M15, M17, M18, M19, M20

### Option B: Incident Response Coordinator
- Triage alerts → Route to on-call → Escalate per policy → Learn from postmortems
- **Moats:** M4, M9, M10, M12, M17, M18, M19, M20

### Option C: Hiring Workflow Agent
- Screen resumes → Schedule interviews → Enforce diversity policies → Learn from hires
- **Moats:** M4, M11, M15, M17, M18, M19, M20

---

## Decision

**Build a worker and iterate.**

The goal is not to showcase all 35 moats on day one, but to:
1. Ship something tangible
2. Gather real-world usage data
3. Layer moat-exercising features based on actual pain points
4. Use the worker to find bugs/improvements in M0-M20

---

## Properties for Ideal Worker Domain

| Property | Why It Matters |
|----------|----------------|
| Recurring decisions | Exercises M18 learning |
| Constraints/policies | Exercises M19/M20 |
| Failure modes | Exercises M9/M10 |
| Complexity variance | Exercises M17 CARE |
| Strategic alignment | Exercises M15 SBA |
| Multi-step workflows | Exercises M4/M12 |

---

## Next Steps

1. Finalize worker domain selection
2. Design workflow that can layer moat features
3. Implement Phase 1 (basic execution)
4. Add governance/constraints in Phase 2
5. Add learning loop in Phase 3

---

*PIN-085 created 2025-12-15 (Worker Brainstorm & Moat Audit)*
