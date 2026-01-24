# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: Tier-based feature gating engine
# Callers: API routes, services
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Auth System

"""
Tier-Based Feature Gating (M32 Implementation)

Provides:
- TenantTier enum (OBSERVE, REACT, PREVENT, ASSIST, GOVERN)
- PricingPhase toggle (LEARNING = soft limits, AUTHORITY = hard limits)
- Feature→Tier mapping for 60+ features
- @requires_tier decorator for FastAPI endpoints
- Prometheus metrics for tier access decisions

Based on:
- PIN-155: M32 Tier Infrastructure Blueprint
- PIN-157: Numeric Pricing Anchors

Usage:
    from app.auth.tier_gating import requires_tier, TenantTier

    @router.get("/evidence/export/pdf")
    async def export_pdf(
        ctx: TenantContext = Depends(get_tenant_context),
        _: None = Depends(requires_tier(TenantTier.PREVENT)),
    ):
        ...
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status

from ..utils.metrics_helpers import get_or_create_counter

logger = logging.getLogger("nova.auth.tier_gating")


# =============================================================================
# Enums
# =============================================================================


class TenantTier(str, Enum):
    """
    Tenant subscription tiers.

    Ordered by capability level (OBSERVE < REACT < PREVENT < ASSIST < GOVERN).
    Each tier includes all capabilities of lower tiers.

    Strategic semantics (from pricing strategy analysis):
    - OBSERVE: Free tier, "Open Control Plane" - maximizes Currency B (system intelligence)
    - REACT: "High-Signal Learning Tier" - "You see the fire" (emergency response)
    - PREVENT: "Decision Tier" - "You stop the fire" (pre-execution authority)
    - ASSIST/GOVERN: Revenue primary - custom quotes

    Pricing principle: "Freeze the floor, stretch the ceiling"
    - FREE stays forever ($0)
    - REACT stays stable ($9)
    - PREVENT may move up later ($199+)
    - ASSIST/GOVERN elastic ($1.5k-$5k+)
    """

    OBSERVE = "observe"  # $0/month - Open Control Plane (Currency B only)
    REACT = "react"  # $9/month - High-Signal Learning ("You see the fire")
    PREVENT = "prevent"  # $199/month - Decision Tier ("You stop the fire")
    ASSIST = "assist"  # $1.5k+/month - Scale (custom quote)
    GOVERN = "govern"  # $5k+/month - Enterprise (custom quote)

    def __ge__(self, other: "TenantTier") -> bool:
        order = [TenantTier.OBSERVE, TenantTier.REACT, TenantTier.PREVENT, TenantTier.ASSIST, TenantTier.GOVERN]
        return order.index(self) >= order.index(other)

    def __gt__(self, other: "TenantTier") -> bool:
        order = [TenantTier.OBSERVE, TenantTier.REACT, TenantTier.PREVENT, TenantTier.ASSIST, TenantTier.GOVERN]
        return order.index(self) > order.index(other)

    def __le__(self, other: "TenantTier") -> bool:
        order = [TenantTier.OBSERVE, TenantTier.REACT, TenantTier.PREVENT, TenantTier.ASSIST, TenantTier.GOVERN]
        return order.index(self) <= order.index(other)

    def __lt__(self, other: "TenantTier") -> bool:
        order = [TenantTier.OBSERVE, TenantTier.REACT, TenantTier.PREVENT, TenantTier.ASSIST, TenantTier.GOVERN]
        return order.index(self) < order.index(other)


class PricingPhase(str, Enum):
    """
    Pricing phase determines enforcement mode.

    LEARNING (Phase A): Soft limits - warn but allow, maximize Currency B (data)
    AUTHORITY (Phase B): Hard limits - block, monetize Currency A (cash)
    """

    LEARNING = "learning"  # Phase A: Soft limits, maximize system intelligence
    AUTHORITY = "authority"  # Phase B: Hard limits, monetize authority


# =============================================================================
# Configuration
# =============================================================================

# Current pricing phase (set via environment or dynamically)
CURRENT_PHASE = PricingPhase(os.getenv("PRICING_PHASE", PricingPhase.LEARNING.value))

# Price anchors (reference values - actual enforcement uses tier comparisons)
PRICE_ANCHORS = {
    TenantTier.OBSERVE: {
        "price_monthly_cents": 0,
        "price_annual_cents": 0,
        "marketing_name": "Open Control Plane",
        "currency_focus": "B",  # System intelligence only
        "retention_days": 7,
    },
    TenantTier.REACT: {
        "price_monthly_cents": 900,  # $9
        "price_annual_cents": 9900,  # $99/year
        "marketing_name": "Builder",
        "currency_focus": "B>A",  # Learning > Revenue
        "retention_days": 30,
    },
    TenantTier.PREVENT: {
        "price_monthly_cents": 19900,  # $199
        "price_annual_cents": 199000,  # ~$1990/year (16% discount)
        "marketing_name": "Authority Explorer",
        "currency_focus": "A+B",  # Both currencies
        "retention_days": 90,
    },
    TenantTier.ASSIST: {
        "price_monthly_cents": None,  # Custom quote $1.5k-$3k
        "price_annual_cents": None,
        "marketing_name": "Scale",
        "currency_focus": "A",  # Revenue primary
        "retention_days": 180,
    },
    TenantTier.GOVERN: {
        "price_monthly_cents": None,  # Custom quote $3k-$5k+
        "price_annual_cents": None,
        "marketing_name": "Enterprise",
        "currency_focus": "A",  # Revenue primary
        "retention_days": 365,
    },
}


# =============================================================================
# Feature → Tier Mapping
# =============================================================================

FEATURE_TIER_MAP: dict[str, TenantTier] = {
    # =========================================================================
    # OBSERVE ($0) - "Open Control Plane"
    # Basic observability, proxy access, 7-day retention
    # Currency focus: B (system intelligence, no revenue target)
    # =========================================================================
    # Proxy
    "proxy.chat_completions": TenantTier.OBSERVE,
    "proxy.completions": TenantTier.OBSERVE,
    "proxy.embeddings": TenantTier.OBSERVE,
    # Basic Dashboard
    "dashboard.status": TenantTier.OBSERVE,
    "dashboard.health": TenantTier.OBSERVE,
    # Cost (read-only totals)
    "cost.daily_total": TenantTier.OBSERVE,
    "cost.monthly_total": TenantTier.OBSERVE,
    # Basic Observability
    "logs.read.7d": TenantTier.OBSERVE,
    "metrics.basic": TenantTier.OBSERVE,
    # =========================================================================
    # REACT ($9) - "High-Signal Learning Tier" / "You see the fire"
    # KillSwitch (emergency response), Alerts, 30-day retention
    # Currency focus: B>A (learning > revenue, prevent comfortable lock-in)
    # Semantic: Users REACT to incidents, they don't PREVENT them yet
    # =========================================================================
    # KillSwitch
    "killswitch.read": TenantTier.REACT,
    "killswitch.write": TenantTier.REACT,
    "killswitch.freeze_agent": TenantTier.REACT,
    "killswitch.freeze_model": TenantTier.REACT,
    # Alerts
    "alerts.read": TenantTier.REACT,
    "alerts.configure": TenantTier.REACT,
    "alerts.webhook": TenantTier.REACT,
    # Extended Observability
    "logs.read.30d": TenantTier.REACT,
    "metrics.detailed": TenantTier.REACT,
    # SDK (rate-limited)
    "sdk.simulate.limited": TenantTier.REACT,  # 100 calls/hour
    "sdk.query.limited": TenantTier.REACT,
    # Cost (per-feature breakdown)
    "cost.per_feature": TenantTier.REACT,
    "cost.per_user": TenantTier.REACT,
    "cost.budget_alerts": TenantTier.REACT,
    # Basic Incident
    "incident.read": TenantTier.REACT,
    "incident.list": TenantTier.REACT,
    # Decision Timeline (read-only)
    "timeline.read": TenantTier.REACT,
    # =========================================================================
    # PREVENT ($199) - "Decision Tier" / "You stop the fire"
    # Pre-execution simulation, full SDK, evidence export, 90-day retention
    # Currency focus: A+B (both revenue and intelligence)
    # Semantic: This is the FIRST TIER where AOS makes decisions BEFORE execution
    # Authority framing: "before money is spent", "before damage occurs"
    # =========================================================================
    # SDK (unlimited)
    "sdk.simulate.full": TenantTier.PREVENT,
    "sdk.query.full": TenantTier.PREVENT,
    "sdk.capabilities": TenantTier.PREVENT,
    "sdk.skills": TenantTier.PREVENT,
    # SBA (Strategy Bounds Advisor)
    "sba.read": TenantTier.PREVENT,
    "sba.configure": TenantTier.PREVENT,
    "sba.recommendations": TenantTier.PREVENT,
    # Evidence Export
    "evidence.export.json": TenantTier.PREVENT,
    "evidence.export.pdf": TenantTier.PREVENT,
    "evidence.certificates": TenantTier.PREVENT,
    "evidence.replay": TenantTier.PREVENT,  # Replay for compliance verification
    # Extended Observability
    "logs.read.90d": TenantTier.PREVENT,
    "metrics.prometheus": TenantTier.PREVENT,
    # Budget Enforcement
    "budget.hard_caps": TenantTier.PREVENT,
    "budget.per_agent": TenantTier.PREVENT,
    # Incident Management
    "incident.create": TenantTier.PREVENT,
    "incident.update": TenantTier.PREVENT,
    "incident.resolve": TenantTier.PREVENT,
    # Decision Timeline (full)
    "timeline.export": TenantTier.PREVENT,
    "timeline.replay": TenantTier.PREVENT,
    # Custom Guardrails
    "guardrails.read": TenantTier.PREVENT,
    "guardrails.write": TenantTier.PREVENT,
    # Policy Evaluation Sandbox
    "policy.audit": TenantTier.PREVENT,  # Pre-execution policy evaluation
    # =========================================================================
    # ASSIST ($1.5k+) - "Scale" / Advanced Orchestration
    # CARE routing, recovery automation, 180-day retention
    # Currency focus: A (revenue primary)
    # Elastic pricing: custom quote based on usage
    # =========================================================================
    # CARE Routing
    "care.routing": TenantTier.ASSIST,
    "care.configure": TenantTier.ASSIST,
    "care.fallback_chains": TenantTier.ASSIST,
    # Recovery Automation
    "recovery.read": TenantTier.ASSIST,
    "recovery.auto_apply": TenantTier.ASSIST,
    "recovery.custom_strategies": TenantTier.ASSIST,
    # Extended Observability
    "logs.read.180d": TenantTier.ASSIST,
    "metrics.custom": TenantTier.ASSIST,
    # Failure Catalog
    "failure_catalog.read": TenantTier.ASSIST,
    "failure_catalog.contribute": TenantTier.ASSIST,
    # Priority Support
    "support.priority": TenantTier.ASSIST,
    "support.slack": TenantTier.ASSIST,
    # API Priority
    "api.priority_queue": TenantTier.ASSIST,
    "api.higher_rate_limits": TenantTier.ASSIST,
    # =========================================================================
    # GOVERN ($5k+) - "Enterprise" / Full Governance
    # Custom policies, compliance (SOC2/HIPAA/GDPR), 365-day retention, SLA
    # Currency focus: A (revenue primary)
    # Elastic pricing: custom quote, do NOT quote until readiness signals met
    # =========================================================================
    # Custom Policies
    "policy.custom": TenantTier.GOVERN,
    "policy.approval_workflows": TenantTier.GOVERN,
    "policy.audit_trail": TenantTier.GOVERN,
    # Compliance
    "compliance.soc2": TenantTier.GOVERN,
    "compliance.hipaa": TenantTier.GOVERN,
    "compliance.gdpr": TenantTier.GOVERN,
    "compliance.reports": TenantTier.GOVERN,
    # Extended Observability
    "logs.read.365d": TenantTier.GOVERN,
    "logs.export.full": TenantTier.GOVERN,
    # Dedicated Support
    "support.dedicated": TenantTier.GOVERN,
    "support.sla": TenantTier.GOVERN,
    "support.onboarding": TenantTier.GOVERN,
    # SSO & Security
    "sso.saml": TenantTier.GOVERN,
    "sso.oidc": TenantTier.GOVERN,
    "security.ip_allowlist": TenantTier.GOVERN,
    "security.audit_logs": TenantTier.GOVERN,
    # Multi-environment
    "environments.staging": TenantTier.GOVERN,
    "environments.multiple": TenantTier.GOVERN,
    # Data Residency
    "data.residency": TenantTier.GOVERN,
    "data.encryption_byok": TenantTier.GOVERN,
}


# =============================================================================
# Prometheus Metrics
# =============================================================================

TIER_ACCESS_DECISIONS = get_or_create_counter(
    "tier_access_decisions_total",
    "Tier-based access decisions",
    ["feature", "required_tier", "tenant_tier", "decision", "phase"],
)

TIER_SOFT_BLOCKS = get_or_create_counter(
    "tier_soft_blocks_total",
    "Features accessed beyond tier (soft block in learning phase)",
    ["feature", "required_tier", "tenant_tier"],
)


# =============================================================================
# Tier Resolution
# =============================================================================

# Map legacy plan names to TenantTier
PLAN_TO_TIER: dict[str, TenantTier] = {
    # Legacy names
    "free": TenantTier.OBSERVE,
    "pro": TenantTier.REACT,
    "enterprise": TenantTier.GOVERN,
    # New tier names (direct mapping)
    "observe": TenantTier.OBSERVE,
    "react": TenantTier.REACT,
    "prevent": TenantTier.PREVENT,
    "assist": TenantTier.ASSIST,
    "govern": TenantTier.GOVERN,
    # Marketing names
    "open_control_plane": TenantTier.OBSERVE,
    "builder": TenantTier.REACT,
    "authority_explorer": TenantTier.PREVENT,
    "scale": TenantTier.ASSIST,
}


def resolve_tier(plan: str) -> TenantTier:
    """
    Resolve a plan string to a TenantTier.

    Handles legacy plan names (free, pro, enterprise) and new tier names.
    Defaults to OBSERVE if unknown.
    """
    normalized = plan.lower().strip().replace("-", "_").replace(" ", "_")
    return PLAN_TO_TIER.get(normalized, TenantTier.OBSERVE)


# =============================================================================
# Access Check Result
# =============================================================================


@dataclass
class TierAccessResult:
    """Result of a tier access check."""

    allowed: bool
    required_tier: TenantTier
    tenant_tier: TenantTier
    feature: str
    phase: PricingPhase
    soft_blocked: bool = False  # True if would be blocked but allowed in learning phase
    reason: Optional[str] = None

    @property
    def upgrade_required(self) -> bool:
        """True if tenant needs to upgrade to access this feature."""
        return self.tenant_tier < self.required_tier


# =============================================================================
# Core Access Check
# =============================================================================


def check_tier_access(
    feature: str,
    tenant_tier: TenantTier,
    phase: Optional[PricingPhase] = None,
) -> TierAccessResult:
    """
    Check if a tenant tier has access to a feature.

    Args:
        feature: Feature identifier (e.g., "sdk.simulate.full")
        tenant_tier: The tenant's current tier
        phase: Pricing phase (defaults to CURRENT_PHASE)

    Returns:
        TierAccessResult with access decision and metadata
    """
    phase = phase or CURRENT_PHASE
    required_tier = FEATURE_TIER_MAP.get(feature, TenantTier.OBSERVE)

    # Check if tenant tier is sufficient
    tier_sufficient = tenant_tier >= required_tier

    if tier_sufficient:
        # Access granted
        result = TierAccessResult(
            allowed=True,
            required_tier=required_tier,
            tenant_tier=tenant_tier,
            feature=feature,
            phase=phase,
            reason=f"Tier {tenant_tier.value} >= {required_tier.value}",
        )
        TIER_ACCESS_DECISIONS.labels(
            feature=feature,
            required_tier=required_tier.value,
            tenant_tier=tenant_tier.value,
            decision="allowed",
            phase=phase.value,
        ).inc()
        return result

    # Tier insufficient - check phase
    if phase == PricingPhase.LEARNING:
        # Soft block: log but allow
        logger.info(
            f"Soft gate: feature={feature} requires {required_tier.value}, "
            f"tenant has {tenant_tier.value} (allowing in learning phase)"
        )
        TIER_SOFT_BLOCKS.labels(
            feature=feature,
            required_tier=required_tier.value,
            tenant_tier=tenant_tier.value,
        ).inc()
        TIER_ACCESS_DECISIONS.labels(
            feature=feature,
            required_tier=required_tier.value,
            tenant_tier=tenant_tier.value,
            decision="soft_allowed",
            phase=phase.value,
        ).inc()
        return TierAccessResult(
            allowed=True,
            required_tier=required_tier,
            tenant_tier=tenant_tier,
            feature=feature,
            phase=phase,
            soft_blocked=True,
            reason=f"Soft allow: {tenant_tier.value} < {required_tier.value} (learning phase)",
        )

    # Hard block in authority phase
    TIER_ACCESS_DECISIONS.labels(
        feature=feature,
        required_tier=required_tier.value,
        tenant_tier=tenant_tier.value,
        decision="denied",
        phase=phase.value,
    ).inc()
    return TierAccessResult(
        allowed=False,
        required_tier=required_tier,
        tenant_tier=tenant_tier,
        feature=feature,
        phase=phase,
        reason=f"Upgrade required: {tenant_tier.value} < {required_tier.value}",
    )


# =============================================================================
# FastAPI Dependency
# =============================================================================


def requires_tier(
    required_tier: TenantTier,
    feature: Optional[str] = None,
):
    """
    FastAPI dependency factory for tier-based access control.

    Usage:
        @router.get("/evidence/export/pdf")
        async def export_pdf(
            ctx: TenantContext = Depends(get_tenant_context),
            _: None = Depends(requires_tier(TenantTier.PREVENT, "evidence.export.pdf")),
        ):
            ...

    Args:
        required_tier: Minimum tier required for access
        feature: Optional feature name for logging/metrics (auto-derived from endpoint if not provided)

    Returns:
        FastAPI dependency that checks tier access
    """
    from .tenant_auth import TenantContext, get_tenant_context

    async def tier_checker(
        request: Request,
        ctx: TenantContext = Depends(get_tenant_context),
    ) -> TierAccessResult:
        # Resolve tenant tier from plan
        tenant_tier = resolve_tier(ctx.plan)

        # Derive feature name from request path if not provided
        feature_name = feature or f"{request.method.lower()}.{request.url.path}"

        # Check access
        result = check_tier_access(feature_name, tenant_tier)

        if not result.allowed:
            # Get marketing name for upgrade message
            required_marketing = PRICE_ANCHORS.get(required_tier, {}).get("marketing_name", required_tier.value)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "tier_upgrade_required",
                    "message": f"This feature requires {required_marketing} tier or higher",
                    "current_tier": tenant_tier.value,
                    "required_tier": required_tier.value,
                    "feature": feature_name,
                    "upgrade_url": "/settings/billing",
                },
            )

        # Store result in request state for downstream use
        request.state.tier_access_result = result

        return result

    return tier_checker


def requires_feature(feature: str):
    """
    FastAPI dependency factory that checks tier based on feature name.

    Looks up required tier from FEATURE_TIER_MAP automatically.

    Usage:
        @router.get("/sba/recommendations")
        async def get_recommendations(
            ctx: TenantContext = Depends(get_tenant_context),
            _: None = Depends(requires_feature("sba.recommendations")),
        ):
            ...
    """
    required_tier = FEATURE_TIER_MAP.get(feature, TenantTier.OBSERVE)
    return requires_tier(required_tier, feature)


# =============================================================================
# Decorator (Alternative Syntax)
# =============================================================================


def tier_gated(required_tier: TenantTier, feature: Optional[str] = None):
    """
    Decorator for tier-gated endpoints (alternative to Depends).

    Usage:
        @router.get("/evidence/export/pdf")
        @tier_gated(TenantTier.PREVENT, "evidence.export.pdf")
        async def export_pdf(request: Request, ctx: TenantContext):
            ...

    Note: Prefer using Depends(requires_tier()) for better FastAPI integration.
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get tenant context from request state or kwargs
            ctx = getattr(request.state, "tenant_context", None)
            if ctx is None:
                ctx = kwargs.get("ctx")

            if ctx is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Resolve tier and check access
            tenant_tier = resolve_tier(ctx.plan)
            feature_name = feature or f"{request.method.lower()}.{request.url.path}"
            result = check_tier_access(feature_name, tenant_tier)

            if not result.allowed:
                required_marketing = PRICE_ANCHORS.get(required_tier, {}).get("marketing_name", required_tier.value)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "tier_upgrade_required",
                        "message": f"This feature requires {required_marketing} tier or higher",
                        "current_tier": tenant_tier.value,
                        "required_tier": required_tier.value,
                        "feature": feature_name,
                    },
                )

            request.state.tier_access_result = result
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# Utility Functions
# =============================================================================


def get_tier_features(tier: TenantTier) -> list[str]:
    """Get all features available at a given tier (including lower tiers)."""
    return [feature for feature, required_tier in FEATURE_TIER_MAP.items() if tier >= required_tier]


def get_tier_info(tier: TenantTier) -> dict:
    """Get complete information about a tier."""
    anchor = PRICE_ANCHORS.get(tier, {})
    return {
        "tier": tier.value,
        "marketing_name": anchor.get("marketing_name", tier.value),
        "price_monthly_cents": anchor.get("price_monthly_cents"),
        "price_annual_cents": anchor.get("price_annual_cents"),
        "currency_focus": anchor.get("currency_focus"),
        "retention_days": anchor.get("retention_days"),
        "features": get_tier_features(tier),
        "feature_count": len(get_tier_features(tier)),
    }


def get_upgrade_path(current_tier: TenantTier, target_feature: str) -> dict:
    """
    Get upgrade information for accessing a feature.

    Returns tier needed and price difference.
    """
    required_tier = FEATURE_TIER_MAP.get(target_feature, TenantTier.OBSERVE)

    if current_tier >= required_tier:
        return {
            "upgrade_needed": False,
            "current_tier": current_tier.value,
            "feature": target_feature,
        }

    current_price = PRICE_ANCHORS.get(current_tier, {}).get("price_monthly_cents", 0) or 0
    required_price = PRICE_ANCHORS.get(required_tier, {}).get("price_monthly_cents")

    return {
        "upgrade_needed": True,
        "current_tier": current_tier.value,
        "required_tier": required_tier.value,
        "current_marketing_name": PRICE_ANCHORS.get(current_tier, {}).get("marketing_name"),
        "required_marketing_name": PRICE_ANCHORS.get(required_tier, {}).get("marketing_name"),
        "price_difference_cents": (required_price - current_price) if required_price else None,
        "feature": target_feature,
    }


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "TenantTier",
    "PricingPhase",
    # Configuration
    "CURRENT_PHASE",
    "PRICE_ANCHORS",
    "FEATURE_TIER_MAP",
    "PLAN_TO_TIER",
    # Functions
    "resolve_tier",
    "check_tier_access",
    "get_tier_features",
    "get_tier_info",
    "get_upgrade_path",
    # FastAPI Dependencies
    "requires_tier",
    "requires_feature",
    # Decorator
    "tier_gated",
    # Result Type
    "TierAccessResult",
]
