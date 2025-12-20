# PIN-095: AI Incident Console - Strategic Pivot & Product Design

**Date:** 2025-12-17
**Status:** ACTIVE - STRATEGIC DIRECTION
**Category:** Strategy / Product / GTM
**Author:** Claude Code + Human Review
**Depends:** M4, M9, M10, M19, M20, BudgetLLM

---

## Executive Summary

**Strategic Pivot:** From "Agent OS / SDK" to "AI Incident Console" as the wedge product.

**Core Insight:** Nobody buys an unknown, unproven SDK. They buy a PRODUCT that secretly installs an SDK.

**The Product:** AI Incident Investigation & Audit Console
- Solves immediate, high-fear problem (AI screws up, need answers)
- Produces visible, business-facing output (evidence, reports)
- Quietly depends on AOS infrastructure internally

**Target Market:** B2B SaaS companies that embed AI in their products

**30-Year Problem:** AI Accountability Infrastructure (audit, compliance, trust)

---

## The Strategic Route

### Why SDK-First Fails

If you launch as:
- "AI accountability SDK"
- "Compliance layer"
- "Agent OS"

You will get:
- Polite interest
- Zero urgency
- Long security reviews
- Stalled pilots

Because SDKs are:
- Invisible to business value
- Risky to integrate
- Impossible to justify without proof

### The Proven Pattern

**You do NOT sell an SDK first.**

You sell a **painkiller product** that:
1. Solves an immediate, undeniable problem
2. Produces visible, business-facing output
3. Quietly depends on your SDK internally

**Historical Proof:**
| Company | Sold First | Became |
|---------|-----------|--------|
| Stripe | Payments | Payments API |
| Twilio | SMS delivery | Comms infra |
| Datadog | Dashboards | Observability agent |
| Segment | Analytics UI | Data pipeline |
| Sentry | Error UI | SDK everywhere |

None started with "install our SDK".

---

## The 30-Year Problem: AI Accountability

### Why This Lasts

```
2024: "We use AI for customer support"
2030: "We must prove our AI didn't discriminate"
2040: "Insurance requires AI audit trails for coverage"
2050: "AI decisions are legally binding, require evidence chain"
```

**Historical parallel:**
- 1990s: "We use databases" → 2020s: "We need audit logs, SOC2, GDPR compliance"
- Same will happen with AI

### Why AOS is Uniquely Positioned

| AOS Capability | Accountability Function |
|----------------|------------------------|
| **M4 Golden Replay** | "Reproduce exactly what happened" (evidence) |
| **M9 Failure Catalog** | "What went wrong and how often" (incident data) |
| **M10 Recovery Engine** | "What we did about it" (remediation proof) |
| **M15 Strategy-Bound** | "Aligned to stated objectives" (intent proof) |
| **M17 CARE Routing** | "Why this path was chosen" (decision trace) |
| **M18 CARE-L Learning** | "How the system improved" (continuous compliance) |
| **M19 Constitutional** | "Policy was enforced" (governance proof) |
| **M20 PLang Compiler** | "Policies are machine-verifiable" (formal methods) |

**No one else has this combination.**

---

## Target Market

### Primary Segment: B2B SaaS with Embedded AI

Companies that:
- Build products with AI features (chatbots, copilots, automation)
- Sell to OTHER businesses (B2B)
- Need to prove to THEIR customers that AI is safe

**Examples:**
- Customer support platforms with AI
- Sales tools with AI
- Legal tech with AI
- HR tech with AI
- Marketing tech with AI

### Why They Buy NOW

1. **Their customers are asking:** "How do I know your AI won't leak my data / say something inappropriate?"
2. **They need regression testing:** Every prompt update needs verification
3. **They need incident investigation:** When AI goes wrong, customers ask "what happened?"
4. **They're already paying for LLMs:** Cost control is immediate pain
5. **They're software companies:** Fast decision makers

---

## The Product: AI Incident Console

### Positioning

**Not:** "Agent operating system" (too abstract)
**Not:** "LLM framework" (commoditized)
**Yes:** "Incident investigation & audit console for AI-powered products"

**One-liner:**
> "When your AI screws up, can you explain what happened?"

### The Trigger Moment

**Scene:** CTO gets a Slack message at 11 PM:

> "Our AI just told a customer their contract was auto-renewed when it wasn't. Customer threatening legal. What happened?"

**What they need:**
1. What did the AI actually say? (exact output)
2. What inputs led to this? (context, history)
3. Why did it say this? (policy/reasoning trace)
4. Can we prove this wasn't malicious? (evidence)
5. How do we prevent this again? (remediation)

**Current state:** 4-8 hours of log digging
**With AI Incident Console:** 5 minutes

### Core Capabilities

| Capability | Customer Problem | AOS Solution |
|------------|------------------|--------------|
| **Audit Trails** | "Customer asks what AI did" | Complete decision trace with M4 replay |
| **Policy Enforcement** | "AI must follow content/safety rules" | M19/M20 constitutional layer |
| **Regression Testing** | "Did prompt change break anything?" | Golden replay comparison |
| **Incident Investigation** | "Why did AI do wrong thing?" | M9 failure catalog + trace |
| **Cost Control** | "LLM bills are unpredictable" | BudgetLLM (already built) |
| **Compliance Reports** | "Auditor needs evidence" | Export to PDF/JSON/SOC2 format |

---

## UX Design: The Incident Flow

### Flow Overview

```
TRIGGER → SEARCH → INSPECT → REPLAY → EXPORT
   │         │         │         │         │
"What    "Find the  "Full    "Prove   "Package
happened" decision"  trace"   it"      for legal"
```

### Screen 1: Incident Search

```
┌─────────────────────────────────────────────────────────────────┐
│  AI INCIDENT CONSOLE                          [Search] [Export] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🔍 Search: user_id:cust_8372 time:last_24h "contract"          │
│                                                                  │
│  MATCHING DECISIONS (3)                                         │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ ⚠️ Dec 17, 23:47 │ cust_8372 │ "Your contract is..."      │ │
│  │    Policy: CONTENT_ACCURACY │ Confidence: 0.73 │ [INSPECT] │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │ ✓ Dec 17, 23:45 │ cust_8372 │ "Here are your..."          │ │
│  │    Policy: PASSED │ Confidence: 0.91 │ [INSPECT]           │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**AOS Integration:**
- Search uses M9 Failure Catalog indexed by user/time/content
- Policy status from M19 Constitutional evaluation
- Confidence from M17 CARE routing scores

### Screen 2: Decision Inspector (Core Screen)

```
┌─────────────────────────────────────────────────────────────────┐
│  DECISION TRACE: dec_a8f3c2                   [Replay] [Export] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SUMMARY                                                        │
│  Time: Dec 17, 2025 23:47:12 UTC                               │
│  User: cust_8372 (Acme Corp)                                   │
│  Model: claude-sonnet-4-20250514                               │
│  Cost: $0.0023 │ Latency: 1.2s                                 │
│  Policy: ⚠️ CONTENT_ACCURACY (0.73 confidence)                 │
│                                                                  │
│  ──────────────────── TIMELINE ────────────────────────        │
│                                                                  │
│  [23:47:12.001] INPUT RECEIVED                                 │
│  User: "Is my contract auto-renewed?"                          │
│  Context Retrieved:                                             │
│   • contract_status: "active"                                  │
│   • auto_renew: null (⚠️ MISSING DATA)                        │
│                                                                  │
│  [23:47:12.050] POLICY EVALUATION (M19)                        │
│  ✓ SAFETY: Passed                                              │
│  ✓ PRIVACY: Passed                                             │
│  ⚠️ CONTENT_ACCURACY: Missing data for definitive answer       │
│     → Should have triggered: Uncertainty response               │
│     → Actually did: Made assertion                              │
│  🔴 ROOT CAUSE: Policy enforcement gap                         │
│                                                                  │
│  [23:47:12.847] OUTPUT                                         │
│  "Yes, your contract is set to auto-renew..."                  │
│  ⚠️ PROBLEMATIC: Asserted when data was null                   │
│                                                                  │
│  [23:47:12.900] LOGGED                                         │
│  Replay Token: rpl_7f3a2b │ Hash: e3b0c44...                   │
│                                                                  │
│  [🔄 REPLAY] [📄 EXPORT PDF] [🔗 SHARE]                        │
└─────────────────────────────────────────────────────────────────┘
```

**AOS Integration:**
| UI Element | AOS Component |
|------------|---------------|
| Timeline | M4 Golden Replay execution trace |
| Policy Evaluation | M19 Constitutional + M20 PLang |
| Root Cause | M9 Failure Catalog pattern matching |
| Confidence | M17 CARE routing score |
| Replay Token | M4 Golden Hash |

### Screen 3: Replay Verification

```
┌─────────────────────────────────────────────────────────────────┐
│  REPLAY VERIFICATION                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  REPLAY COMPLETE ✓                                              │
│                                                                  │
│  ┌──────────────────────┬──────────────────────┐               │
│  │     ORIGINAL         │       REPLAY         │               │
│  ├──────────────────────┼──────────────────────┤               │
│  │ "Yes, your contract  │ "Yes, your contract  │               │
│  │ is set to auto..."   │ is set to auto..."   │               │
│  ├──────────────────────┼──────────────────────┤               │
│  │ Hash: e3b0c442...    │ Hash: e3b0c442...    │               │
│  │ ✓ EXACT MATCH        │ ✓ DETERMINISTIC      │               │
│  └──────────────────────┴──────────────────────┘               │
│                                                                  │
│  📋 EVIDENCE CERTIFICATE                                        │
│  This decision is cryptographically verified as reproducible.  │
│  Verification Hash: sha256:7f3a2b9c...                          │
│  Timestamp: Dec 17, 2025 23:52:01 UTC                           │
│                                                                  │
│  [📄 DOWNLOAD CERTIFICATE] [📧 EMAIL TO LEGAL]                  │
└─────────────────────────────────────────────────────────────────┘
```

### Screen 4: Export Package

```
┌─────────────────────────────────────────────────────────────────┐
│  EXPORT INCIDENT PACKAGE                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SELECT FORMAT:                                                 │
│  [✓] PDF Report (human-readable)                               │
│  [✓] JSON Evidence Pack (machine-readable)                     │
│  [ ] SOC2 Audit Format                                         │
│  [ ] Legal Discovery Format                                    │
│                                                                  │
│  INCLUDE:                                                       │
│  [✓] Full decision trace                                       │
│  [✓] Policy evaluation log                                     │
│  [✓] Replay verification certificate                           │
│  [✓] Root cause analysis                                       │
│  [ ] Raw model inputs/outputs                                  │
│                                                                  │
│  [📦 GENERATE EXPORT PACKAGE]                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integration Strategy: Drop-In Wrapper

### The Key: No Architecture Changes Required

```python
# BEFORE (customer's existing code)
from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": user_input}]
)

# AFTER (one import change)
from aiconsole import Client  # <-- Your wrapper
client = Client(openai_key="sk-...", console_key="aic-...")

response = client.chat.completions.create(  # Same API
    model="gpt-4",
    messages=[{"role": "user", "content": user_input}],
    user_id=user_id,      # Optional: for search
    session_id=session_id # Optional: for grouping
)
# Everything else works the same
# But now every decision is logged, policy-evaluated, replayable
```

### Wrapper Internal Flow

```
1. CAPTURE INPUT → Store messages, user_id, timestamp
2. RETRIEVE CONTEXT → Log what data fetched
3. EVALUATE POLICIES (M19) → Run safety, privacy, content rules
4. CALL LLM (pass-through) → Forward to OpenAI/Anthropic
5. CAPTURE OUTPUT → Store response, golden hash, replay token
6. RETURN (unchanged) → Same response format
```

---

## Build Requirements

### What Already Exists

| Component | Status | Location |
|-----------|--------|----------|
| Decision logging | ✅ | M4 golden replay infrastructure |
| Policy evaluation | ✅ | M19/M20 constitutional layer |
| Failure catalog | ✅ | M9 with pattern matching |
| Replay engine | ✅ | M4 deterministic replay |
| Cost tracking | ✅ | BudgetLLM |
| Console UI base | ⚠️ Partial | Worker Console exists |
| OpenAI wrapper base | ⚠️ Partial | BudgetLLM wraps |

### What Needs to Be Built

| Component | Priority | Effort | Description |
|-----------|----------|--------|-------------|
| **Search API** | P0 | 2 days | Index decisions by user/time/content |
| **Decision Trace API** | P0 | 2 days | Full trace retrieval endpoint |
| **Wrapper Enhancement** | P0 | 2 days | Extend BudgetLLM to log traces |
| **Console UI (3 screens)** | P0 | 3 days | Search, Inspector, Replay |
| **Export API** | P1 | 2 days | PDF/JSON generation |
| **Evidence Certificates** | P1 | 1 day | Signed replay verification |
| **SIEM Integration** | P2 | 3 days | Splunk/Datadog export |

### Build Priority (Week 1)

| Day | Task |
|-----|------|
| 1-2 | Wrapper Enhancement (extend BudgetLLM) |
| 3-4 | Search & Decision Trace APIs |
| 5-6 | Console UI (3 screens) |
| 7 | Export (PDF/JSON) |

---

## Go-To-Market

### Phase 1: Design Partners (Month 1)

**Find 5 companies that:**
- Have AI in their product
- Sell B2B
- Have gotten customer questions about AI safety
- Have <50 employees (fast decisions)

**Offer:**
- Free for 3 months
- Weekly calls
- They shape the product

**Where to find:**
- YC companies (AI category)
- ProductHunt AI launches
- Twitter/X AI builder community
- Personal network

### Phase 2: Paid Pilots (Months 2-3)

**Convert design partners:**
- $99/mo minimum (validates WTP)
- Case studies for marketing

**Pricing Tiers:**
| Tier | Price | Decisions/mo |
|------|-------|--------------|
| Starter | $99 | 100K |
| Growth | $499 | 1M |
| Enterprise | $2,000+ | Unlimited + SLA |

### Phase 3: Scale (Months 4-6)

**If validated (10+ paying, <20% churn):**
- ProductHunt launch
- Integration with LangChain, Vercel AI SDK
- Enterprise sales motion

---

## The Strategic Funnel

```
Sell fear → Earn trust → Embed infrastructure → Become inevitable
     │           │              │                    │
 Incident     Console       Wrapper/SDK         Required for
 Console      adoption      everywhere          compliance
```

### Evolution Path

```
Phase 1: AI Incident Console (wedge product)
    ↓
Phase 2: Regression Testing ("catch before customers do")
    ↓
Phase 3: Policy Governance ("enforce rules proactively")
    ↓
Phase 4: Full AOS SDK ("build governed AI from day 1")
```

---

## Landing Page Copy

**Headline:**
> When your AI screws up, can you explain what happened?

**Subhead:**
> AI Incident Console gives you instant answers when customers, lawyers, or auditors ask questions.

**Problem:**
> Your AI chatbot just told a customer the wrong thing. Now you're digging through logs, trying to reconstruct what happened. It takes hours. Legal is waiting. The customer is angry.

**Solution:**
> Drop in one line of code. Get complete audit trails for every AI decision. Replay any incident. Export evidence in seconds.

**CTA:**
> [Get Started — No Code Changes Required]

---

## Success Metrics

### Phase 1 (Design Partners)
- 5 companies onboarded
- 3+ active after 2 weeks
- 1+ "this saved me during an incident" story

### Phase 2 (Paid Pilots)
- 10 paying customers
- <20% monthly churn
- $1K+ MRR

### Phase 3 (Scale)
- 50+ customers
- $10K+ MRR
- 1+ enterprise deal

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Sales execution (small team) | Start with design partners, warm intros |
| LangChain copies feature | Be "compliance expert" not "framework competitor" |
| Customers don't know they need it | Target those who already had incidents |
| Integration complexity | OpenAI wrapper first, expand later |

---

## Related PINs

- **PIN-069:** BudgetLLM Go-To-Market (cost control component)
- **PIN-085:** Worker Brainstorm & Moat Audit (35 moats inventory)
- **PIN-005:** Machine-Native Architecture (foundational vision)
- **PIN-019:** M19 Constitutional Governance (policy layer)
- **PIN-004:** M4 Golden Replay (determinism foundation)
- **PIN-009:** M9 Failure Catalog (incident data)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-17 | Initial PIN created - Strategic pivot from SDK to Incident Console |

---

*PIN-095 created 2025-12-17 (AI Incident Console Strategy)*
