# PIN-069: BudgetLLM Go-To-Market Plan (Revised)

**Date:** 2025-12-14
**Status:** PHASE 0 COMPLETE
**Version:** 1.1.0
**Category:** Strategy / GTM

---

## Executive Summary

**Product:** BudgetLLM - Hard budget limits for LLM APIs
**Tagline:** "Your agent stops before you overspend"
**Core Promise:** Prevention, not just visibility

**Differentiator:** Unlike Helicone/LangSmith (observability), BudgetLLM actively *prevents* overspend with kill-switches and prompt caching. You don't just see your bill - you control it.

---

## Current State (What's Already Built)

| Capability | Status | File |
|------------|--------|------|
| Hard budget cap (kill-switch) | ✅ Complete | `budgetllm/core/budget.py` |
| Per-run/per-day/per-model limits | ✅ Complete | `budgetllm/core/budget.py` |
| Auto-pause on limit | ✅ Complete | `budgetllm/core/budget.py` |
| Prompt caching (in-memory) | ✅ Complete | `budgetllm/core/cache.py` |
| Redis-backed cache | ✅ Complete | `budgetllm/core/backends/redis.py` |
| OpenAI-compatible wrapper | ✅ **NEW** | `budgetllm/core/client.py` |
| PyPI package | ✅ **NEW** | `pip install budgetllm` |
| 39 tests (15 OpenAI compat) | ✅ **NEW** | `budgetllm/tests/` |
| Web Console | ⚠️ Partial | Needs cost-focused views |
| Model routing | ❌ Not built | Phase 2 feature |

**Bottom line:** Phase 0 complete. Package ready for PyPI. Dashboard + beta users next.

---

## Target User

### Primary Persona: "Ravi the Indie Builder"

- Solo developer or 2-3 person team in India
- Building AI-powered SaaS/tool
- Monthly LLM spend: $50-500
- Pain: Unexpected API bills, no visibility until month-end
- Behavior: Active on Twitter/X, Indie Hackers, local Discord
- Payment: Razorpay/UPI preferred, can do international cards

### Secondary Persona: "Startup CTO"

- 5-20 person startup
- Multiple developers using LLM APIs
- Monthly spend: $500-5000
- Pain: No per-developer limits, hard to allocate costs
- Behavior: Less social, more enterprise-y
- Payment: Invoice/wire transfer acceptable

**Phase 1 focuses on Ravi. Phase 3 expands to CTOs.**

---

## Competitive Positioning

| Tool | Focus | BudgetLLM Advantage |
|------|-------|---------------------|
| OpenAI Dashboard | Basic usage view | No kill-switch, single provider |
| Helicone | Observability + caching | No hard limits, complex setup |
| LangSmith | Tracing + debugging | Dev-focused, not cost-focused |
| Portkey | Gateway + routing | Enterprise-priced, overkill for indies |
| **BudgetLLM** | **Prevention + savings** | Kill-switch, caching, simple, cheap |

**Positioning statement:**
> "Helicone shows you spent $500. BudgetLLM stops you at $100."

---

## Revised Phased Plan

### Phase 0: Package What Exists (Week 1) — ✅ COMPLETE

**Goal:** Make current capabilities usable without full AOS deployment.

| Task | Output | Status |
|------|--------|--------|
| Extract budget + cache into standalone module | `budgetllm/` package | ✅ Done |
| Create OpenAI-compatible wrapper | `client.chat.completions.create()` | ✅ Done |
| Add Redis cache backend | `RedisBackend` class | ✅ Done |
| Write README with examples | Full API documentation | ✅ Done |
| Add comprehensive tests | 39 tests (15 OpenAI compat) | ✅ Done |

**Deliverable:** `pip install budgetllm` works, wraps OpenAI calls with budget enforcement.

**Implementation Details (2025-12-14):**

```
budgetllm/
├── __init__.py              # Package exports
├── py.typed                 # PEP 561 type hints marker
├── pyproject.toml           # Package config
├── README.md                # Full documentation
├── LICENSE                  # MIT
├── core/
│   ├── client.py            # OpenAI-compatible Client
│   ├── budget.py            # BudgetTracker + BudgetExceededError
│   ├── cache.py             # PromptCache
│   └── backends/
│       ├── memory.py        # MemoryBackend (LRU + TTL)
│       └── redis.py         # RedisBackend
├── tests/
│   ├── test_budgetllm.py    # 24 core tests
│   └── test_openai_compat.py # 15 OpenAI compatibility tests
└── dist/
    ├── budgetllm-0.1.0-py3-none-any.whl
    └── budgetllm-0.1.0.tar.gz
```

**Usage - Drop-in OpenAI replacement:**

```python
# Change one import line:
# from openai import OpenAI
from budgetllm import Client as OpenAI

client = OpenAI(openai_key="sk-...", budget_cents=1000)

# Same API works:
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Same response access:
print(response["choices"][0]["message"]["content"])
print(response["usage"]["total_tokens"])

# Plus cost tracking:
print(f"Cost: {response['cost_cents']} cents")
print(f"Cache hit: {response['cache_hit']}")
```

**Shortcut syntax also works:**

```python
response = client.chat("What is 2+2?")
```

---

### Phase 1: MVP Dashboard + Launch (Weeks 2-4)

**Goal:** Usable web product for 10 beta users.

#### Week 2: Dashboard Core

| Feature | Priority | Notes |
|---------|----------|-------|
| Sign up (email, no card) | P0 | Passwordless magic link |
| Connect API key (OpenAI first) | P0 | Store encrypted in Vault |
| Set budget limit | P0 | Daily/monthly, hard cap |
| View spend chart | P0 | Last 7 days, by model |
| See "$ saved by cache" | P0 | Hero metric on dashboard |

**Tech:** Simple React dashboard, reuse existing Console components.

#### Week 3: Landing Page + Waitlist

| Asset | Content |
|-------|---------|
| Hero | "Hard budget limits for LLM APIs" |
| Problem | "Surprise $500 OpenAI bill? Never again." |
| Solution | "Set a limit. We stop your agent before you overspend." |
| Social proof | "Saved users $X in cached calls" (aggregate metric) |
| CTA | "Start free - no credit card" |
| Waitlist | Email capture for launch notification |

**Tech:** Static site (Astro/Next), Razorpay-ready for later.

#### Week 4: Beta Launch

| Activity | Target |
|----------|--------|
| Invite 10 beta users | Personal outreach, Twitter DMs |
| 1:1 onboarding calls | 30 min each, screen share |
| Collect feedback | What's missing? What's confusing? |
| Track metrics | Signups, active users, cache hit rate, $ saved |

**Success criteria:** 5/10 users active after 1 week, at least 1 "this saved me money" testimonial.

---

### Phase 2: Validate Willingness to Pay (Months 2-3)

**Goal:** Find 10 paying users before building more features.

#### Pricing Tiers (Test)

| Tier | Price | Limits | Target |
|------|-------|--------|--------|
| Free | $0 | 1 API key, $100/mo budget cap, 7-day history | Hobbyists |
| Pro | $19/mo | 5 keys, unlimited budget, 90-day history, Slack alerts | Indie builders |
| Team | $49/mo | 20 keys, team dashboard, priority support | Small startups |

**Payment:** Razorpay for India, LemonSqueezy for international.

#### Validation Activities

| Week | Activity |
|------|----------|
| 5-6 | Ask beta users: "Would you pay $19/mo for this?" |
| 7-8 | Soft paywall: Free tier limits enforced |
| 9-10 | First paid conversions (target: 10) |
| 11-12 | Analyze churn, gather testimonials |

**Key question to answer:** Do users value *prevention* enough to pay, or is *visibility* (free) sufficient?

#### Feature Additions (Only If Validated)

| Feature | Add When | Rationale |
|---------|----------|-----------|
| Anthropic support | 3+ users request | Multi-provider demand |
| Model routing | Users want cheaper options | Cost optimization |
| Slack/Discord alerts | Users want async notification | Convenience |
| Team/org features | CTO persona interest | Expansion signal |

**Rule:** No new features until 10 paying users. Focus on activation, not feature bloat.

---

### Phase 3: Scale (Months 4-6)

**Only enter Phase 3 if:**
- ≥10 paying users
- <20% monthly churn
- ≥1 organic referral

#### Growth Activities

| Channel | Activity |
|---------|----------|
| Product Hunt | Launch with testimonials |
| Indie Hackers | "I built a tool to stop LLM overspend" post |
| Twitter/X | Build in public thread, daily updates |
| YourStory/Inc42 | Pitch for Indian startup coverage |
| Dev communities | r/OpenAI, r/LocalLLaMA, AI Discord servers |

#### Enterprise Prep (If Demand)

| Feature | Purpose |
|---------|---------|
| SSO/SAML | Enterprise requirement |
| Audit logs | Compliance |
| Invoice billing | No-card procurement |
| SLA | Enterprise trust |

**Don't build these until inbound enterprise interest.**

---

## Metrics Dashboard

### North Star Metric

**$ Saved Per User Per Month**

This directly measures value delivered. Target: >$20 saved (justifies $19/mo price).

### Supporting Metrics

| Metric | Target (Phase 1) | Target (Phase 2) |
|--------|------------------|------------------|
| Signups | 50 | 200 |
| Active users (weekly) | 10 | 50 |
| Cache hit rate | 30% | 40% |
| Avg $ saved/user/week | $5 | $15 |
| Paid conversions | 0 | 10 |
| Churn (monthly) | N/A | <20% |

---

## Technical Roadmap

### Phase 0-1 (Weeks 1-4)

```
budgetllm/
├── core/
│   ├── client.py          # OpenAI-compatible wrapper
│   ├── budget.py          # Extract from budget_tracker.py
│   ├── cache.py           # Redis-backed prompt cache
│   └── metrics.py         # Prometheus counters
├── api/
│   ├── main.py            # FastAPI proxy server
│   └── auth.py            # API key validation
├── dashboard/
│   ├── pages/
│   │   ├── index.tsx      # Spend overview
│   │   ├── settings.tsx   # Budget limits
│   │   └── keys.tsx       # API key management
│   └── components/
│       ├── SpendChart.tsx
│       └── SavingsCard.tsx
└── landing/
    └── index.html         # Static landing page
```

### Phase 2-3 (Months 2-6)

```
Additions:
├── providers/
│   ├── openai.py
│   ├── anthropic.py
│   └── router.py          # Smart model routing
├── alerts/
│   ├── slack.py
│   └── discord.py
└── billing/
    ├── razorpay.py
    └── lemonsqueezy.py
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Users don't pay | Validate with $5 "coffee" tier first |
| Competitors copy | Speed + community + niche focus |
| Redis costs | Start with free tier (Upstash), upgrade with revenue |
| Legal (storing API keys) | Clear ToS, encrypted storage, user can delete anytime |
| India payment friction | Razorpay + UPI, no international cards needed |

---

## Open Source Strategy

### What's Open

| Component | License | Rationale |
|-----------|---------|-----------|
| `budgetllm-core` SDK | MIT | Adoption, trust, contributions |
| Prometheus metrics | MIT | Observability standard |
| CLI tool | MIT | Developer convenience |

### What's Proprietary

| Component | Rationale |
|-----------|-----------|
| Hosted dashboard | Convenience = paid value |
| Team features | Enterprise differentiator |
| Managed Redis cache | Operational burden = paid value |

**Model:** Open core, hosted convenience. Like Supabase, PostHog.

---

## 90-Day Milestones

| Day | Milestone | Success Criteria |
|-----|-----------|------------------|
| 7 | `budgetllm` package on PyPI | `pip install budgetllm` works |
| 14 | Dashboard MVP deployed | Can connect key, see spend, set limit |
| 21 | Landing page live | Waitlist collecting emails |
| 28 | 10 beta users onboarded | 5+ active after 1 week |
| 45 | Pricing tiers announced | Free limits enforced |
| 60 | First paid user | $19 collected via Razorpay |
| 75 | 10 paying users | $190 MRR |
| 90 | Product Hunt launch | Top 5 of the day |

---

## Immediate Next Steps (This Week)

1. ~~**Extract budget + cache into standalone package**~~ ✅ Done
2. ~~**Create OpenAI-compatible wrapper**~~ ✅ Done
3. **Publish to PyPI**
   - `twine upload dist/*`
   - Verify `pip install budgetllm` works globally

4. **Write landing page copy**
   - Hero, problem, solution, CTA
   - Deploy to budgetllm.com (or similar)

5. **Identify 10 beta users**
   - Personal network first
   - Twitter DMs to indie builders posting about LLM costs

---

## Related PINs

- **PIN-070:** BudgetLLM Safety Governance Layer (extends BudgetLLM with risk scoring)
- PIN-068: M13 Prompt Caching Implementation
- PIN-067: M13 Iterations Cost Calculator Fix
- PIN-033: M8-M14 Machine-Native Realignment Roadmap

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2025-12-14 | Claude | Initial plan based on validation feedback |
| 2025-12-14 | Claude | Phase 0 complete: OpenAI-compatible wrapper, 39 tests, PyPI-ready package |
| 2025-12-14 | Claude | Comprehensive README for adoption: Why BudgetLLM, Budget/Cache behavior, Error handling, Redis backend, Common patterns |
