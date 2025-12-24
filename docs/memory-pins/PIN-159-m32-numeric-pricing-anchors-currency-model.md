# PIN-159: M32 Numeric Pricing Anchors & Currency Model

**Status:** ✅ COMPLETE
**Created:** 2025-12-24
**Category:** Pricing / Strategy
**Milestone:** M32 Pricing Infrastructure

---

## Summary

Defines numeric price anchors, Currency A/B model, tier semantics, and pricing phase enforcement

---

## Details

## Overview

Documents the numeric pricing anchors and currency model for AOS tier-based pricing. This PIN establishes the reference values that inform tier gating enforcement.

## Currency Model

AOS operates with two currencies:
- **Currency A ($)**: Cash revenue
- **Currency B (data)**: System intelligence, usage patterns, failure catalogs

### Currency Focus by Tier

| Tier | Price | Currency Focus | Semantic |
|------|-------|----------------|----------|
| OBSERVE | $0/month | B only | Open Control Plane - maximize learning |
| REACT | $9/month | B>A | High-Signal Learning - "You see the fire" |
| PREVENT | $199/month | A+B | Decision Tier - "You stop the fire" |
| ASSIST | $1.5k+/month | A | Scale - custom quote |
| GOVERN | $5k+/month | A | Enterprise - custom quote |

## Pricing Principle

**"Freeze the floor, stretch the ceiling"**

- FREE ($0) stays forever - never touch
- REACT ($9) stays stable for a long time
- PREVENT ($199) may move UP later
- ASSIST/GOVERN are elastic ($1.5k-$5k+)

Never raise the floor. If revenue is needed, stretch the ceiling.

## Semantic Tier Definitions

### OBSERVE ($0) - "Open Control Plane"
- Basic observability (proxy, 7-day retention)
- No revenue target
- Currency B dominant: Maximize system intelligence

### REACT ($9) - "High-Signal Learning"
- KillSwitch (emergency response)
- Alerts (what happened, not prevention)
- Partial evidence (not court-grade)
- **Semantic: "You see the fire"**
- Don't over-deliver value here to avoid comfortable lock-in

### PREVENT ($199) - "Decision Tier"
- First tier where AOS makes decisions BEFORE execution
- Full simulation, court-grade evidence, replay
- **Semantic: "You stop the fire"**
- Authority framing: "before money is spent", "before damage occurs"

### ASSIST ($1.5k+) - "Scale"
- CARE routing, recovery automation
- Custom quote based on usage
- Revenue primary

### GOVERN ($5k+) - "Enterprise"
- Custom policies, compliance (SOC2/HIPAA/GDPR)
- Do NOT quote until readiness signals met
- Revenue primary

## Readiness Signals for Enterprise

Before quoting ASSIST/GOVERN, require:
1. X prevented incidents
2. Y% cost avoided
3. Z automated mitigations executed safely

Until then, treat enterprise quotes as learning probes, not revenue targets.

## Price Anchors (Config)

```python
PRICE_ANCHORS = {
    TenantTier.OBSERVE: {
        "price_monthly_cents": 0,
        "marketing_name": "Open Control Plane",
        "retention_days": 7,
    },
    TenantTier.REACT: {
        "price_monthly_cents": 900,
        "marketing_name": "Builder",
        "retention_days": 30,
    },
    TenantTier.PREVENT: {
        "price_monthly_cents": 19900,
        "marketing_name": "Authority Explorer",
        "retention_days": 90,
    },
    TenantTier.ASSIST: {
        "price_monthly_cents": None,
        "marketing_name": "Scale",
        "retention_days": 180,
    },
    TenantTier.GOVERN: {
        "price_monthly_cents": None,
        "marketing_name": "Enterprise",
        "retention_days": 365,
    },
}
```

## Pricing Phase

| Phase | Enforcement | Purpose |
|-------|-------------|---------|
| LEARNING | Soft limits (warn but allow) | Maximize Currency B, understand usage |
| AUTHORITY | Hard limits (403 block) | Monetize Currency A, enforce tiers |

Controlled by PRICING_PHASE env var. Default: LEARNING.

## Implementation Status

- [x] PRICE_ANCHORS config in tier_gating.py
- [x] Tier semantics documented in docstrings
- [x] See the fire / Stop the fire language applied
- [x] Tier decorators wired to API endpoints
- [x] Prometheus metrics for tier access decisions

## Related Files

- backend/app/auth/tier_gating.py - Core implementation
- backend/tests/test_tier_gating.py - 41 tests covering all scenarios

---

## Related PINs

- [PIN-155](PIN-155-.md)
- [PIN-156](PIN-156-.md)
- [PIN-158](PIN-158-.md)
- [PIN-128](PIN-128-.md)
