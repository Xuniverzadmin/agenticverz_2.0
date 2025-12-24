# PIN-155: M32 Tier Infrastructure Blueprint

**Status:** READY
**Category:** Infrastructure / Pricing / Feature Gating
**Created:** 2025-12-24
**Related PINs:** PIN-128, PIN-154, PIN-070, PIN-075

---

## Executive Summary

M32 builds the infrastructure to support tiered pricing without locking in specific pricing models. This is **plumbing, not pricing**.

> **Principle:** Build the gates first, decide what goes through them later.

---

## What This Milestone Does NOT Do

- Does NOT freeze tier definitions
- Does NOT set prices
- Does NOT integrate with Stripe (that's M33+)
- Does NOT define feature bundles permanently

**This milestone builds the machinery. Pricing decisions remain flexible.**

---

## Gap Analysis (From Pricing Architecture Review)

| Gap | Description | Current State |
|-----|-------------|---------------|
| **Tenant tier config** | No tier field on Tenant model | Tenant has no tier awareness |
| **Feature flags per tier** | SDK methods not gated | All features available to all |
| **Retention config** | Fixed retention periods | No per-tenant customization |
| **Rate limits per tier** | No simulate() throttling | Unlimited for all tenants |
| **Usage metering** | No SDK call counting | Can't bill by usage if needed |

---

## Deliverable 1: Tenant Tier Model

### Schema Addition

```python
# app/models/tenant.py

class TenantTier(str, Enum):
    """
    Tier levels for feature gating.

    NOTE: These are infrastructure labels, not marketing names.
    Marketing names (Free, Starter, Pro, etc.) are a separate concern.
    """
    OBSERVE = "observe"      # Wrapper only, read-only
    REACT = "react"          # Reactive controls, limited SDK
    PREVENT = "prevent"      # Full SDK, preventive controls
    ASSIST = "assist"        # Guided autonomy, CARE routing
    GOVERN = "govern"        # Full platform, custom policies


class Tenant(SQLModel, table=True):
    # ... existing fields ...

    # M32: Tier infrastructure
    tier: TenantTier = Field(default=TenantTier.OBSERVE)
    tier_updated_at: Optional[datetime] = Field(default=None)
    tier_expires_at: Optional[datetime] = Field(default=None)  # For trials

    # M32: Retention config (days)
    retention_days: int = Field(default=7)

    # M32: Rate limits (per hour)
    simulate_limit_hourly: Optional[int] = Field(default=None)  # None = unlimited
    query_limit_hourly: Optional[int] = Field(default=None)
```

### Migration

```python
# alembic/versions/050_m32_tier_infrastructure.py

def upgrade():
    # Add tier column with default
    op.add_column('tenant', sa.Column('tier', sa.String(20),
                  nullable=False, server_default='observe'))
    op.add_column('tenant', sa.Column('tier_updated_at', sa.DateTime, nullable=True))
    op.add_column('tenant', sa.Column('tier_expires_at', sa.DateTime, nullable=True))
    op.add_column('tenant', sa.Column('retention_days', sa.Integer,
                  nullable=False, server_default='7'))
    op.add_column('tenant', sa.Column('simulate_limit_hourly', sa.Integer, nullable=True))
    op.add_column('tenant', sa.Column('query_limit_hourly', sa.Integer, nullable=True))

    # Index for tier queries
    op.create_index('ix_tenant_tier', 'tenant', ['tier'])

def downgrade():
    op.drop_index('ix_tenant_tier')
    op.drop_column('tenant', 'query_limit_hourly')
    op.drop_column('tenant', 'simulate_limit_hourly')
    op.drop_column('tenant', 'retention_days')
    op.drop_column('tenant', 'tier_expires_at')
    op.drop_column('tenant', 'tier_updated_at')
    op.drop_column('tenant', 'tier')
```

---

## Deliverable 2: Feature Gate Decorator

### Core Implementation

```python
# app/auth/tier_gate.py

from functools import wraps
from fastapi import HTTPException, Depends
from app.models.tenant import TenantTier

# Tier hierarchy (higher includes lower)
TIER_HIERARCHY = {
    TenantTier.OBSERVE: 0,
    TenantTier.REACT: 1,
    TenantTier.PREVENT: 2,
    TenantTier.ASSIST: 3,
    TenantTier.GOVERN: 4,
}


def requires_tier(minimum_tier: TenantTier):
    """
    Decorator to gate endpoints by tenant tier.

    Usage:
        @router.post("/simulate")
        @requires_tier(TenantTier.PREVENT)
        async def simulate(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, auth=Depends(get_current_auth), **kwargs):
            tenant = await get_tenant(auth.tenant_id)

            if TIER_HIERARCHY[tenant.tier] < TIER_HIERARCHY[minimum_tier]:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "tier_required",
                        "message": f"This feature requires tier '{minimum_tier.value}' or higher",
                        "current_tier": tenant.tier.value,
                        "required_tier": minimum_tier.value,
                        "upgrade_url": f"/settings/billing?upgrade_to={minimum_tier.value}"
                    }
                )

            return await func(*args, auth=auth, **kwargs)
        return wrapper
    return decorator


def tier_check(tenant_tier: TenantTier, required: TenantTier) -> bool:
    """Simple tier check for use in business logic."""
    return TIER_HIERARCHY[tenant_tier] >= TIER_HIERARCHY[required]
```

### Feature Registry

```python
# app/auth/feature_registry.py

from app.models.tenant import TenantTier

# Feature → Minimum tier mapping
# This is the ONLY place feature gates are defined
FEATURE_TIER_MAP = {
    # Wrapper features (all tiers)
    "proxy.chat_completions": TenantTier.OBSERVE,
    "proxy.embeddings": TenantTier.OBSERVE,
    "killswitch.read": TenantTier.OBSERVE,
    "incidents.read": TenantTier.OBSERVE,

    # Tier 1: React
    "killswitch.write": TenantTier.REACT,
    "alerts.configure": TenantTier.REACT,
    "budget.caps": TenantTier.REACT,
    "evidence.export": TenantTier.REACT,
    "sdk.simulate.limited": TenantTier.REACT,  # Rate-limited

    # Tier 2: Prevent
    "sdk.simulate.full": TenantTier.PREVENT,
    "sdk.query": TenantTier.PREVENT,
    "sba.read": TenantTier.PREVENT,
    "sba.write": TenantTier.PREVENT,
    "shadow.routing": TenantTier.PREVENT,
    "cost.projections": TenantTier.PREVENT,

    # Tier 3: Assist
    "care.routing": TenantTier.ASSIST,
    "recovery.suggestions": TenantTier.ASSIST,
    "auto.throttling": TenantTier.ASSIST,
    "canary.enforcement": TenantTier.ASSIST,

    # Tier 4: Govern
    "policy.custom": TenantTier.GOVERN,
    "automation.full": TenantTier.GOVERN,
    "infra.dedicated": TenantTier.GOVERN,
    "compliance.artifacts": TenantTier.GOVERN,
}


def feature_allowed(tenant_tier: TenantTier, feature: str) -> bool:
    """Check if a tenant tier allows a feature."""
    required = FEATURE_TIER_MAP.get(feature)
    if required is None:
        return True  # Unknown features are allowed (fail open for flexibility)
    return tier_check(tenant_tier, required)


def get_allowed_features(tenant_tier: TenantTier) -> list[str]:
    """Get all features allowed for a tier."""
    return [
        feature for feature, required in FEATURE_TIER_MAP.items()
        if tier_check(tenant_tier, required)
    ]
```

---

## Deliverable 3: Usage Metering

### Meter Model

```python
# app/models/metering.py

class UsageMeter(SQLModel, table=True):
    """
    Tracks usage for potential billing.

    Granularity: per-tenant, per-hour, per-feature.
    Aggregation happens at billing time, not ingestion.
    """
    __tablename__ = "usage_meter"

    id: int = Field(primary_key=True)
    tenant_id: str = Field(index=True)
    feature: str = Field(index=True)  # e.g., "sdk.simulate", "proxy.chat"
    hour_bucket: datetime = Field(index=True)  # Truncated to hour
    count: int = Field(default=0)

    # Optional: track cost-relevant metadata
    tokens_in: Optional[int] = Field(default=None)
    tokens_out: Optional[int] = Field(default=None)
    cost_cents: Optional[int] = Field(default=None)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'feature', 'hour_bucket',
                        name='uq_usage_meter_tenant_feature_hour'),
    )
```

### Metering Middleware

```python
# app/middleware/metering.py

from datetime import datetime, timezone
from sqlmodel import Session
from app.models.metering import UsageMeter

async def record_usage(
    tenant_id: str,
    feature: str,
    session: Session,
    tokens_in: int = 0,
    tokens_out: int = 0,
    cost_cents: int = 0,
):
    """
    Record feature usage for potential billing.

    Uses upsert pattern for efficiency.
    """
    now = datetime.now(timezone.utc)
    hour_bucket = now.replace(minute=0, second=0, microsecond=0)

    # Upsert: increment if exists, insert if not
    stmt = text("""
        INSERT INTO usage_meter (tenant_id, feature, hour_bucket, count, tokens_in, tokens_out, cost_cents)
        VALUES (:tenant_id, :feature, :hour_bucket, 1, :tokens_in, :tokens_out, :cost_cents)
        ON CONFLICT (tenant_id, feature, hour_bucket)
        DO UPDATE SET
            count = usage_meter.count + 1,
            tokens_in = usage_meter.tokens_in + EXCLUDED.tokens_in,
            tokens_out = usage_meter.tokens_out + EXCLUDED.tokens_out,
            cost_cents = usage_meter.cost_cents + EXCLUDED.cost_cents
    """)

    await session.execute(stmt, {
        "tenant_id": tenant_id,
        "feature": feature,
        "hour_bucket": hour_bucket,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_cents": cost_cents,
    })
```

### Integration with SDK Endpoints

```python
# app/api/v1_runtime.py

@router.post("/simulate")
@requires_tier(TenantTier.REACT)  # Minimum tier
async def simulate(
    request: SimulateRequest,
    auth: AuthContext = Depends(get_current_auth),
    session: Session = Depends(get_session),
):
    tenant = await get_tenant(auth.tenant_id, session)

    # Check rate limit for REACT tier (limited simulate)
    if tenant.tier == TenantTier.REACT:
        if not await check_rate_limit(tenant, "sdk.simulate", session):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": "Simulate call limit reached. Upgrade for unlimited access.",
                    "upgrade_url": "/settings/billing?upgrade_to=prevent"
                }
            )

    # Record usage
    await record_usage(auth.tenant_id, "sdk.simulate", session)

    # Execute
    result = await runtime_simulate(request, tenant)
    return result
```

---

## Deliverable 4: Rate Limiting per Tier

### Rate Limit Checker

```python
# app/auth/rate_limiter.py

from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select, func
from app.models.metering import UsageMeter

async def check_rate_limit(
    tenant: Tenant,
    feature: str,
    session: Session,
) -> bool:
    """
    Check if tenant is within rate limits.

    Returns True if allowed, False if limit exceeded.
    """
    # Get limit for this feature
    limit = get_feature_limit(tenant, feature)
    if limit is None:
        return True  # No limit

    # Count usage in current hour
    now = datetime.now(timezone.utc)
    hour_bucket = now.replace(minute=0, second=0, microsecond=0)

    stmt = select(UsageMeter.count).where(
        UsageMeter.tenant_id == tenant.id,
        UsageMeter.feature == feature,
        UsageMeter.hour_bucket == hour_bucket,
    )
    result = await session.execute(stmt)
    current_count = result.scalar() or 0

    return current_count < limit


def get_feature_limit(tenant: Tenant, feature: str) -> Optional[int]:
    """
    Get rate limit for a feature based on tenant config.
    """
    if feature == "sdk.simulate":
        return tenant.simulate_limit_hourly
    if feature == "sdk.query":
        return tenant.query_limit_hourly
    return None  # No limit for other features
```

### Default Limits by Tier

```python
# app/auth/tier_defaults.py

# Default rate limits per tier (per hour)
# These are suggestions, actual limits are on Tenant model
TIER_DEFAULTS = {
    TenantTier.OBSERVE: {
        "retention_days": 7,
        "simulate_limit_hourly": 0,  # Not allowed
        "query_limit_hourly": 0,
    },
    TenantTier.REACT: {
        "retention_days": 30,
        "simulate_limit_hourly": 100,  # Limited
        "query_limit_hourly": 100,
    },
    TenantTier.PREVENT: {
        "retention_days": 90,
        "simulate_limit_hourly": None,  # Unlimited
        "query_limit_hourly": None,
    },
    TenantTier.ASSIST: {
        "retention_days": 180,
        "simulate_limit_hourly": None,
        "query_limit_hourly": None,
    },
    TenantTier.GOVERN: {
        "retention_days": 365,
        "simulate_limit_hourly": None,
        "query_limit_hourly": None,
    },
}


async def apply_tier_defaults(tenant: Tenant, session: Session):
    """Apply default limits when tier changes."""
    defaults = TIER_DEFAULTS.get(tenant.tier, {})

    tenant.retention_days = defaults.get("retention_days", 7)
    tenant.simulate_limit_hourly = defaults.get("simulate_limit_hourly")
    tenant.query_limit_hourly = defaults.get("query_limit_hourly")
    tenant.tier_updated_at = datetime.now(timezone.utc)

    session.add(tenant)
    await session.commit()
```

---

## Deliverable 5: Retention Enforcement

### Retention Job

```python
# app/jobs/retention_cleanup.py

async def enforce_retention():
    """
    Cron job to delete data beyond retention period.

    Runs daily. Respects per-tenant retention_days.
    """
    async with get_session() as session:
        tenants = await session.execute(select(Tenant))

        for tenant in tenants.scalars():
            cutoff = datetime.now(timezone.utc) - timedelta(days=tenant.retention_days)

            # Delete old proxy calls
            await session.execute(
                delete(ProxyCall).where(
                    ProxyCall.tenant_id == tenant.id,
                    ProxyCall.created_at < cutoff,
                )
            )

            # Delete old incidents (unless marked for preservation)
            await session.execute(
                delete(Incident).where(
                    Incident.tenant_id == tenant.id,
                    Incident.created_at < cutoff,
                    Incident.preserved == False,
                )
            )

            # Delete old usage meters
            await session.execute(
                delete(UsageMeter).where(
                    UsageMeter.tenant_id == tenant.id,
                    UsageMeter.hour_bucket < cutoff,
                )
            )

        await session.commit()
```

---

## Deliverable 6: Tier Admin API

### Founder-Only Endpoints

```python
# app/api/fops/tier_admin.py

@router.get("/tenants/{tenant_id}/tier")
@requires_founder_auth
async def get_tenant_tier(tenant_id: str, session: Session = Depends(get_session)):
    """Get tenant tier and limits."""
    tenant = await get_tenant(tenant_id, session)
    return {
        "tenant_id": tenant.id,
        "tier": tenant.tier.value,
        "tier_updated_at": tenant.tier_updated_at,
        "tier_expires_at": tenant.tier_expires_at,
        "retention_days": tenant.retention_days,
        "simulate_limit_hourly": tenant.simulate_limit_hourly,
        "query_limit_hourly": tenant.query_limit_hourly,
        "allowed_features": get_allowed_features(tenant.tier),
    }


@router.patch("/tenants/{tenant_id}/tier")
@requires_founder_auth
async def update_tenant_tier(
    tenant_id: str,
    update: TierUpdateRequest,
    session: Session = Depends(get_session),
    founder: FounderContext = Depends(get_founder_auth),
):
    """
    Update tenant tier. Founder action - logged and auditable.
    """
    tenant = await get_tenant(tenant_id, session)
    old_tier = tenant.tier

    # Update tier
    tenant.tier = update.tier
    tenant.tier_updated_at = datetime.now(timezone.utc)
    if update.expires_at:
        tenant.tier_expires_at = update.expires_at

    # Apply defaults if requested
    if update.apply_defaults:
        await apply_tier_defaults(tenant, session)

    # Override specific limits if provided
    if update.retention_days is not None:
        tenant.retention_days = update.retention_days
    if update.simulate_limit_hourly is not None:
        tenant.simulate_limit_hourly = update.simulate_limit_hourly

    # Log founder action
    await create_founder_action(
        action_type="CHANGE_TIER",
        target_type="TENANT",
        target_id=tenant_id,
        reason_code=update.reason_code,
        reason_note=update.reason_note,
        founder_id=founder.id,
        old_value={"tier": old_tier.value},
        new_value={"tier": tenant.tier.value},
        session=session,
    )

    await session.commit()

    return {"status": "updated", "tier": tenant.tier.value}
```

---

## Implementation Plan

### Phase 1: Schema & Migration (Day 1-2)

| Task | Effort |
|------|--------|
| Add TenantTier enum | 1 hour |
| Add tier fields to Tenant model | 2 hours |
| Create migration 050 | 2 hours |
| Backfill existing tenants to OBSERVE | 1 hour |
| Write schema tests | 2 hours |

### Phase 2: Feature Gating (Day 3-4)

| Task | Effort |
|------|--------|
| Implement `requires_tier` decorator | 2 hours |
| Create feature registry | 2 hours |
| Apply gates to SDK endpoints | 4 hours |
| Write gate tests | 4 hours |

### Phase 3: Metering (Day 5-6)

| Task | Effort |
|------|--------|
| Create UsageMeter model | 1 hour |
| Implement `record_usage` | 2 hours |
| Integrate with SDK endpoints | 4 hours |
| Write metering tests | 3 hours |

### Phase 4: Rate Limiting (Day 7-8)

| Task | Effort |
|------|--------|
| Implement rate limit checker | 2 hours |
| Create tier defaults | 1 hour |
| Wire rate limits to endpoints | 3 hours |
| Write rate limit tests | 2 hours |

### Phase 5: Retention & Admin (Day 9-10)

| Task | Effort |
|------|--------|
| Implement retention job | 3 hours |
| Create tier admin API | 4 hours |
| Wire to founder actions | 2 hours |
| Write admin tests | 3 hours |

---

## Success Criteria

### P0 (Must Have)

- [ ] Tenant model has tier field with enum values
- [ ] `@requires_tier` decorator works on SDK endpoints
- [ ] Feature registry maps features to tiers
- [ ] UsageMeter records SDK calls
- [ ] Tier admin API allows founder tier changes

### P1 (Should Have)

- [ ] Rate limiting enforced for REACT tier
- [ ] Retention job respects per-tenant config
- [ ] Tier changes logged as FounderAction
- [ ] Tier expiry (for trials) supported

### P2 (Nice to Have)

- [ ] Usage dashboard for founders
- [ ] Tier upgrade prompts in 403 responses
- [ ] Automatic tier downgrade on expiry

---

## What This Enables (But Doesn't Decide)

| Enabled | Still Flexible |
|---------|----------------|
| Gate features by tier | Which features in which tier |
| Track usage for billing | How to price usage |
| Set rate limits | What limits to set |
| Enforce retention | What retention periods |
| Change tiers via API | When to change tiers |

---

## Dependencies

| Dependency | Source | Required By |
|------------|--------|-------------|
| FounderAction | M29 | Tier admin audit |
| KillSwitch | M22 | Tier downgrade enforcement |
| SDK endpoints | M8 | Feature gating targets |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-24 | Created PIN-155 M32 Tier Infrastructure Blueprint |
