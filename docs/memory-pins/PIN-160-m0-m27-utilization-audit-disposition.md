# PIN-160: M0-M27 Utilization Audit & Disposition

**Status:** ACTIVE
**Created:** 2025-12-24
**Category:** Architecture / Milestone Audit
**Milestone:** M32+ Planning

---

## Summary

Comprehensive audit of milestones M0-M27 determining consumption status, pillar alignment, and disposition. Establishes clear groupings: Fully Consumed (20), Partial → Consume (5), Internal Consume (2), Abandon (0).

---

## Disposition Framework

A milestone is **FULLY CONSUMED** when:
1. Has at least one pillar owner
2. Participates in at least one production flow
3. Removal would break a visible invariant

---

## GROUP 1: FULLY CONSUMED (20 milestones)

| Milestone | Component | Pillar Owner | Production Flow | Removal Invariant |
|-----------|-----------|--------------|-----------------|-------------------|
| M0 | Foundations/Alembic/DB | Infra | All systems | Nothing runs |
| M1 | Runtime interfaces | Infra | API layer | No execution |
| M2 | Skill registration | Infra | All skills | Skills unloadable |
| M3 | Core skills (http, llm, kv) | Infra | Execution | No LLM calls |
| M5 | Policy API | Governance | M19, CARE | No policy enforcement |
| M9 | Failure Catalog | Self-Heal | M10 | No failure tracking |
| M10 | Recovery Engine | Self-Heal | Recovery flows | No auto-recovery |
| M11 | OpenAI Adapter | Infra | LLM execution | OpenAI calls fail |
| M11 | Claude Adapter | Infra | LLM execution | Claude calls fail |
| M13 | Cost tracking | Cost | M26, M27 | No cost data |
| M14 | BudgetLLM | Governance | M17, M18 | No budget enforcement |
| M15 | SBA Backend | Governance | CARE routing | CARE has no bounds |
| M17 | CARE Routing | Governance | Request routing | No intelligent routing |
| M18 | CARE-L Learning | Governance | M17 | Routing never improves |
| M19 | Policy Constitutional | Governance | Policy enforcement | No constitutional rules |
| M21 | Tenant tracking | Cost | Per-user metering | No per-tenant cost |
| M22 | KillSwitch | Incident | Incident Console | No emergency stop |
| M23 | Guard Console | Incident | Customer UI | No incident visibility |
| M25 | Integration Loop | All | Pillar bridges | Pillars disconnected |
| M26 | Cost Intelligence | Cost | Ops Console | No cost insights |
| M27 | Cost Loop | Cost | M25 bridges | Cost data stale |

---

## GROUP 2: PARTIAL → TO CONSUME (5 milestones)

| Milestone | Component | Current State | Action Required | Target Invariant | Effort |
|-----------|-----------|---------------|-----------------|------------------|--------|
| M4 | Golden Replay | Tests only | Wire to Incident Console | "Incident detail offers replay verification" | 3 days |
| M6 | Scoped Execution Context | Circuit breaker used, canary orphaned | Bind to recovery validation | "MEDIUM+ risk recovery requires scoped pre-execution" | 2 days |
| M7 | Memory/RBAC | Auth used, RBAC partial | Complete RBAC in M28 | "Permission checks route through M7" | M28 scope |
| M8 | SDK | Exists, not emphasized | Elevate as Day-0 entry | "Customer onboarding requires SDK install" | 1 day |
| M16 | SBA Console UI | UI exists, not surfaced | Surface in Guard Console | "Strategy health visible to customers" | 2 days |

### Promotion Criteria

```
Milestone promoted to FULLY CONSUMED when:
1. Pillar explicitly claims it in CODEOWNERS or dependency manifest
2. At least one API route or console page invokes it
3. A test exists that fails if component is removed
```

---

## GROUP 3: INTERNAL CONSUME (2 milestones)

| Milestone | Component | Internal Use Case | Consumer |
|-----------|-----------|-------------------|----------|
| M11 | Voyage Adapter | Embeddings for similarity matching | Founder Ops Console |
| M12 | Multi-Agent / CRM Agent | Customer feedback, L1/L2/L3 decision routing | Founder Ops Console |

### M12 CRM Agent Specification

```
L1: Automated response (templated, no human)
L2: Flagged for founder review (async)
L3: Escalated for immediate action (sync alert)
```

### Internal Consumer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  FOUNDER OPS CONSOLE (Internal)                             │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ M11 Voyage      │    │ M12 CRM Agent   │                │
│  │ - Similarity    │    │ - L1 Auto       │                │
│  │ - Embeddings    │    │ - L2 Review     │                │
│  │                 │    │ - L3 Escalate   │                │
│  └────────┬────────┘    └────────┬────────┘                │
│           │                      │                          │
│           └──────────┬───────────┘                          │
│                      ▼                                      │
│           ┌─────────────────────┐                          │
│           │ Customer Feedback   │                          │
│           │ Intelligence Loop   │                          │
│           └─────────────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## GROUP 4: ABANDON (0 milestones)

No milestones abandoned. All infrastructure has designated consumer.

---

## Final Tally

| Group | Count | Milestones |
|-------|-------|------------|
| **FULLY CONSUMED** | 20 | M0, M1, M2, M3, M5, M9, M10, M11 (OpenAI/Claude), M13, M14, M15, M17, M18, M19, M21, M22, M23, M25, M26, M27 |
| **PARTIAL → CONSUME** | 5 | M4, M6, M7, M8, M16 |
| **INTERNAL CONSUME** | 2 | M11 Voyage, M12 |
| **ABANDON** | 0 | — |

**Total: 27 milestones accounted for. Zero waste.**

---

## Pillar Coverage Summary

| Pillar | Fully Backed | Partial | Internal |
|--------|--------------|---------|----------|
| **Cost** | M13, M21, M26, M27 | — | — |
| **Incident** | M22, M23 | M4 (replay evidence) | — |
| **Self-Heal** | M9, M10 | M6 (scoped execution) | — |
| **Governance** | M5, M14, M15, M17, M18, M19 | M16 (SBA UI) | — |
| **Infra** | M0, M1, M2, M3, M11 (adapters) | M7 (RBAC), M8 (SDK) | M11 Voyage, M12 |

---

## Next Steps

1. Execute Partial → Consume plan (8 days immediate, M7 in M28)
2. Wire M11 Voyage + M12 CRM to Founder Ops Console
3. Validate pillar invariants after promotions

---

## Related PINs

- [PIN-158](PIN-158-m32-tier-gating-implementation.md) - Tier Gating
- [PIN-159](PIN-159-m32-numeric-pricing-anchors-currency-model.md) - Pricing Anchors

---

## Commits

- (pending)
