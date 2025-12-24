# PIN-158: M32 Tier Gating Implementation

**Status:** ✅ COMPLETE
**Created:** 2025-12-24
**Category:** Authentication / Tier Gating
**Milestone:** M32 Pricing Infrastructure

---

## Summary

Implemented tier-based feature gating with TenantTier enum, PricingPhase modes, FEATURE_TIER_MAP (67 features), and FastAPI decorators

---

## Details

## Overview

Implements the tier gating system designed in PIN-155/157, providing runtime feature access control based on tenant subscription tier.

## Components Created

### 1. TenantTier Enum
```python
class TenantTier(str, Enum):
    OBSERVE = "observe"   # $0/month (Free)
    REACT = "react"       # $9/month (Builder)
    PREVENT = "prevent"   # $199/month (Authority Explorer)
    ASSIST = "assist"     # $1.5k+/month (Scale)
    GOVERN = "govern"     # $5k+/month (Enterprise)
```

Supports comparison operators for tier hierarchy checks.

### 2. PricingPhase Enum
- **LEARNING**: Soft limits - log violations but allow access (analytics mode)
- **AUTHORITY**: Hard limits - return 403 for insufficient tier

### 3. FEATURE_TIER_MAP (67 features)
Maps features to required minimum tier:
- OBSERVE: proxy.*, traces.read, telemetry.basic
- REACT: killswitch.*, sdk.basic, runs.scheduling
- PREVENT: sdk.simulate.full, evidence.export.*, policy.audit
- ASSIST: care.*, orchestration.advanced, failover.multi_region
- GOVERN: policy.custom, compliance.*, audit.full

### 4. Decorators
- `@requires_tier(TenantTier.PREVENT)` - Check tier directly
- `@requires_feature("sdk.simulate.full")` - Look up tier from feature map

### 5. Helper Functions
- `resolve_tier(plan_name)` - Convert legacy plans to TenantTier
- `check_tier_access(feature, tier, phase)` - Returns TierAccessResult
- `get_tier_features(tier)` - All features accessible at tier
- `get_tier_info(tier)` - Pricing, retention, marketing name
- `get_upgrade_path(current, feature)` - Upgrade CTA info

## Files Changed

| File | Change |
|------|--------|
| `backend/app/auth/tier_gating.py` | NEW - Core tier gating module (~690 lines) |
| `backend/app/models/tenant.py` | Added .tier property and has_feature() method |
| `backend/app/auth/tenant_auth.py` | Added tier/has_feature to TenantContext |
| `backend/tests/test_tier_gating.py` | NEW - 41 comprehensive tests |

## Usage Examples

### In FastAPI Endpoints
```python
from app.auth.tier_gating import requires_tier, requires_feature, TenantTier

@router.post("/simulate")
async def simulate_run(
    ctx: TenantContext = Depends(get_tenant_context),
    _: TierAccessResult = Depends(requires_tier(TenantTier.PREVENT, "sdk.simulate.full")),
):
    # Only PREVENT tier and above can access
    ...

@router.post("/policy/custom")
async def create_custom_policy(
    ctx: TenantContext = Depends(get_tenant_context),
    _: TierAccessResult = Depends(requires_feature("policy.custom")),
):
    # Automatically looks up required tier from FEATURE_TIER_MAP
    ...
```

### Checking Access Programmatically
```python
from app.auth.tier_gating import check_tier_access, resolve_tier, PricingPhase

tenant_tier = resolve_tier(tenant.plan)  # "free" -> OBSERVE
result = check_tier_access("sdk.simulate.full", tenant_tier, phase=PricingPhase.AUTHORITY)

if not result.allowed:
    print(f"Upgrade to {result.required_tier.value} to access this feature")
```

## Metrics

Prometheus metrics exposed:
- `tier_access_decisions_total{feature, tier, allowed}`
- `tier_soft_blocks_total{feature, tier}`

## Test Coverage

41 tests covering:
- TenantTier ordering (< > <= >=)
- resolve_tier for legacy/new plan names
- check_tier_access for all scenarios
- FEATURE_TIER_MAP completeness
- get_tier_features hierarchy
- Price anchor configuration
- TierAccessResult properties

## Integration with Existing Auth

Seamlessly integrates with M21 tenant auth:
- TenantContext.tier property uses resolve_tier
- TenantContext.has_feature() uses check_tier_access
- Tenant model also has tier property

## Next Steps

- [ ] Wire decorators to actual API endpoints (M33)
- [ ] Implement Stripe webhook for tier upgrades
- [ ] Add tier change audit logging
- [ ] Console UI for tier comparison/upgrade CTAs

---

## Commits

- `916077c`

---

## Related PINs

- [PIN-155](PIN-155-.md)
- [PIN-156](PIN-156-.md)
- [PIN-157](PIN-157-.md)
- [PIN-128](PIN-128-.md)
