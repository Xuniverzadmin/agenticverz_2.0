# PIN-157: Numeric Pricing Anchors

**Status:** ACTIVE
**Category:** Pricing / Strategy / Phase A
**Created:** 2025-12-24
**Related PINs:** PIN-128, PIN-155, PIN-156

---

## Executive Summary

This PIN defines the concrete numeric price points for AOS tiers during Phase A (Learning Acceleration Era). These are **anchors**, not commitments.

> **Core Principle:** Maximize Currency B (system intelligence) now. Capture Currency A (cash) as it appears.

---

## The Two Currencies

| Currency | What It Is | When to Optimize |
|----------|------------|------------------|
| **Currency A** | Cash (revenue) | Phase B (Authority) |
| **Currency B** | System intelligence (data, patterns, edge cases) | Phase A (Learning) |

**Current Phase:** A (Learning Acceleration Era)

**Phase A Goal:** Build the chaos corpus that makes authority claims defensible.

---

## Numeric Anchors Summary

```
FREE ($0)       →  Currency B only (chaos corpus)
$9/month        →  Currency B > A (survival + learning)
$199/month      →  Currency A + B (first real revenue)
$1.5k-$5k/month →  Currency A (explore ceiling, don't publish)
```

---

## Band 1: The Floor ($0)

### Market Segment

| Who | Why They Matter |
|-----|-----------------|
| Indie developers | High volume, low stakes |
| Solo founders | Willing to experiment |
| Students / OSS builders | Free marketing |
| Pet projects | Long-tail edge cases |
| Early AI experiments | Novel failure modes |

### Price

**$0** (no hedging)

### Currency Captured

**Currency B (Primary):**
- Traffic volume
- Failure diversity
- Edge cases
- Early incident patterns
- Model/prompt chaos
- Long-tail behavior

**Currency A (Secondary):**
- Zero (intentionally)

### Why This Floor is Correct

| Factor | Implication |
|--------|-------------|
| Price elasticity | Infinite at this segment |
| $5 filter effect | Removes 70-80% of potential users |
| Value compound | Only at scale |
| Chaos source | Paid users won't generate this |

> This tier is **not a business model**. It is **infrastructure training data**.

### Infrastructure Mapping

| Config | Value |
|--------|-------|
| TenantTier | `OBSERVE` |
| Marketing Name | "Open Control Plane" |
| Retention | 7 days |
| SDK Access | None |
| Proxy Limit | Unlimited |

---

## Band 2: The Breathing Band ($9)

### Market Segment

| Who | Why They Matter |
|-----|-----------------|
| Indie founders shipping real products | Real workloads |
| Tiny startups (1-5 people) | Repeat usage |
| Internal tools teams | Consistent patterns |
| Early SaaS experiments | Longer retention |
| People who care but don't have budget | Higher signal quality |

### Price

**$9/month** (or $99/year)

### Why $9 is the Magic Number

| Alternative | Problem |
|-------------|---------|
| $5 | Signals "toy product" |
| $19 | Triggers comparison shopping |
| $29 | Requires justification |
| **$9** | Impulse buy, no procurement |

Additional benefits:
- Globally affordable (important for reach)
- Doesn't create entitlement expectations
- Blocks abuse effectively
- High enough to signal seriousness

### Currency Captured

**Currency B (Primary):**
- Higher-quality data
- Longer retention (30 days)
- Repeat usage patterns
- Real workloads (not demos)

**Currency A (Secondary):**
- Infrastructure cost offset
- Survival revenue
- Signal of seriousness

> This band **keeps you breathing** while feeding the system.

### Infrastructure Mapping

| Config | Value |
|--------|-------|
| TenantTier | `REACT` |
| Marketing Name | "Builder" |
| Retention | 30 days |
| SDK Access | Rate-limited (100/hour) |
| Proxy Limit | Unlimited |
| Kill Switch | Yes |
| Evidence Export | JSON only |

---

## Band 3: The First Ceiling ($199)

### Market Segment

| Who | Why They Matter |
|-----|-----------------|
| Seed-Series A startups | Budget exists |
| CTO-led teams | Pain-aware |
| AI-first SaaS | High stakes |
| Teams already feeling pain | Ready to buy |

### Price

**$199/month**

### Why $199 (Not $49 or $99)

| Price | Signal |
|-------|--------|
| $49 | "Cheap software" |
| $99 | "Tool subscription" |
| **$199** | "This is infrastructure" |

$199 signals:
- "This is real"
- "This might replace human toil"
- "This is worth paying attention to"

### What They're Paying For

| Capability | Value |
|------------|-------|
| Preventive control | Stop problems before they happen |
| Budget enforcement | Hard caps, not alerts |
| Strategy bounds | Constrain agent behavior |
| Deterministic replay | Debug any incident |
| Evidence certificates | Compliance-ready artifacts |

### Currency Captured

**Currency A (Primary):**
- Meaningful revenue per customer
- Proof of willingness to pay for authority

**Currency B (Secondary):**
- High-stakes failure data
- On-call-grade incidents
- Stress-tested recovery paths

> This is where **learning quality spikes**, not volume.

### Infrastructure Mapping

| Config | Value |
|--------|-------|
| TenantTier | `PREVENT` |
| Marketing Name | "Authority Explorer" |
| Retention | 90 days |
| SDK Access | Unlimited |
| Proxy Limit | Unlimited |
| Evidence Export | PDF + JSON + Certificates |
| SBA Access | Yes |
| Custom Guardrails | Yes |

---

## Band 4: The Explorative Ceiling ($1.5k-$5k)

### Market Segment

| Who | Why They Matter |
|-----|-----------------|
| Scaleups | High budget |
| Enterprises | Complex requirements |
| Regulated industries | Compliance needs |
| AI as core business logic | High stakes |

### Price

**$1,500 → $5,000/month** (DO NOT PUBLISH)

Quote manually. Probe WTP.

### Purpose

| Goal | Method |
|------|--------|
| Measure real WTP | Custom conversations |
| Understand buyer psychology | Discovery calls |
| Learn what authority is worth | Contract negotiations |

### Currency Captured

**Currency A (Primary):**
- High-margin revenue
- Confidence to scale company

**Currency B (Secondary):**
- Deep governance insights
- Compliance edge cases
- High-liability scenarios

> This ceiling should **move**, not be fixed.

### Infrastructure Mapping

| Config | Value |
|--------|-------|
| TenantTier | `ASSIST` / `GOVERN` |
| Marketing Name | "Scale" / "Enterprise" |
| Retention | 180-365 days (custom) |
| SDK Access | Unlimited + priority |
| Everything | Yes |
| SLA | Custom |
| Support | Priority / Dedicated |

---

## The Complete Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PRICING BANDS                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  FREE ($0)                                                              │
│  ├─ Market: Indie / OSS / Chaos                                        │
│  ├─ Currency: B (system intelligence)                                   │
│  ├─ TenantTier: OBSERVE                                                │
│  └─ Marketing: "Open Control Plane"                                     │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  $9/month                                                               │
│  ├─ Market: Builders / Small teams                                      │
│  ├─ Currency: B > A (learning > revenue)                                │
│  ├─ TenantTier: REACT                                                  │
│  └─ Marketing: "Builder"                                                │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  $199/month                                                             │
│  ├─ Market: Startups / Pain-aware teams                                 │
│  ├─ Currency: A + B (both currencies)                                   │
│  ├─ TenantTier: PREVENT                                                │
│  └─ Marketing: "Authority Explorer"                                     │
│                                                                         │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  $1.5k-$5k/month (explorative - DO NOT PUBLISH)                        │
│  ├─ Market: Scaleups / Enterprise                                       │
│  ├─ Currency: A (revenue primary)                                       │
│  ├─ TenantTier: ASSIST / GOVERN                                        │
│  └─ Marketing: "Scale" / "Enterprise"                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Why This Path Preserves Optionality

| Anchor | Effect |
|--------|--------|
| Floor stays zero forever | Data gravity never stops |
| $9 band scales infinitely | Breathing + learning |
| $199 band tests authority value | Early monetization signal |
| Top band explores WTP | Future pricing confidence |

You can:
- Add modules later
- Bundle later
- Raise ceilings later

**But you will never need to lower prices** — which is the real trap.

---

## Phase Transition Criteria

### Exit Criteria for Phase A → Phase B

| Criterion | Threshold |
|-----------|-----------|
| Chaos corpus size | 10,000+ unique failure patterns |
| Prevention evidence | 100+ incidents prevented (documented) |
| Customer testimonials | 10+ attributable quotes |
| Recovery success rate | 80%+ automated recovery |
| Authority claim | Can say "We've seen X and know what works" |

### What Changes in Phase B

| Aspect | Phase A | Phase B |
|--------|---------|---------|
| Floor | Soft limits | Hard limits |
| $9 band | Generous | Tighter |
| $199 band | Exploratory | Assertive |
| Top band | Custom quotes | Published tiers |
| Messaging | "Build with us" | "We protect you" |

---

## Implementation in M32

### PricingPhase Enum

```python
class PricingPhase(str, Enum):
    LEARNING = "learning"      # Phase A: Soft limits
    AUTHORITY = "authority"    # Phase B: Hard limits

# Set via environment or database
CURRENT_PHASE = os.getenv("PRICING_PHASE", PricingPhase.LEARNING)
```

### Phase-Aware Gating

```python
def check_feature_access(tenant: Tenant, feature: str) -> bool:
    """
    In Phase A: Soft limits (warn but allow)
    In Phase B: Hard limits (block)
    """
    allowed = feature_allowed(tenant.tier, feature)

    if not allowed and CURRENT_PHASE == PricingPhase.LEARNING:
        # Log for learning, but allow
        log.info(f"Soft gate: {tenant.id} accessed {feature} beyond tier")
        return True  # Allow in learning phase

    return allowed
```

---

## Relationship to Other PINs

| PIN | Relationship |
|-----|--------------|
| PIN-155 (M32) | Implements infrastructure for these bands |
| PIN-156 | Provides marketing language for these bands |
| PIN-128 | Overall M25-M32 roadmap |
| PIN-154 (M31) | Trust model for key safety (supports all bands) |

---

## Key Decisions

### Decisions Made

| Decision | Rationale |
|----------|-----------|
| Floor = $0 | Maximize chaos corpus |
| Breathing = $9 | Magic number for impulse buy |
| First ceiling = $199 | Signals infrastructure, not tool |
| Top = Explorative | Don't lock in until WTP is known |

### Decisions Deferred

| Decision | When to Decide |
|----------|----------------|
| Exact feature bundling | After customer feedback |
| Enterprise pricing | After 10+ enterprise conversations |
| Annual discounts | After understanding retention |
| Usage-based pricing | After metering data |

---

## Final Warning

> 🚨 **Do NOT anchor identity to the free tier**
> 🚨 **Do NOT market "free forever"**
> 🚨 **Do NOT promise stability yet**

Call it: **"Open Control Plane (Foundational Access)"**

See PIN-156 for complete language guidelines.

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-24 | Created PIN-157 Numeric Pricing Anchors |
