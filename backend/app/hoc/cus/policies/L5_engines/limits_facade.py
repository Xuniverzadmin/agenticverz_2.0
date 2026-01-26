# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# PHASE: W4
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: limits, quotas (via driver)
#   Writes: limits (via driver)
# Role: Limits Facade - Centralized access to rate limits and quotas
# Callers: L2 limits.py API, SDK
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-122 (Limits API)

"""
Limits Facade (L4 Domain Logic)

This facade provides the external interface for limit operations.
All limit APIs MUST use this facade instead of directly importing
internal limit modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes rate limit and quota logic
- Provides unified access to usage tracking
- Single point for audit emission

L2 API Routes (GAP-122):
- GET /api/v1/limits (list limits)
- GET /api/v1/limits/{id} (get limit)
- PUT /api/v1/limits/{id} (update limit)
- GET /api/v1/limits/usage (current usage)
- POST /api/v1/limits/check (check limit)
- POST /api/v1/limits/reset (reset usage)

Usage:
    from app.hoc.cus.policies.L5_engines.limits_facade import get_limits_facade

    facade = get_limits_facade()

    # Check a limit
    result = await facade.check_limit(
        tenant_id="...",
        limit_type="api_calls",
    )
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("nova.services.limits.facade")


class LimitType(str, Enum):
    """Types of limits."""
    API_CALLS = "api_calls"
    TOKEN_USAGE = "token_usage"
    STORAGE = "storage"
    AGENTS = "agents"
    RUNS = "runs"
    CUSTOM = "custom"


class LimitPeriod(str, Enum):
    """Limit period."""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    MONTH = "month"


@dataclass
class LimitConfig:
    """Limit configuration."""
    id: str
    tenant_id: str
    limit_type: str
    period: str
    max_value: int
    current_value: int
    reset_at: str
    enabled: bool
    created_at: str
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "limit_type": self.limit_type,
            "period": self.period,
            "max_value": self.max_value,
            "current_value": self.current_value,
            "reset_at": self.reset_at,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
            "remaining": max(0, self.max_value - self.current_value),
            "percentage_used": round(
                (self.current_value / self.max_value) * 100 if self.max_value > 0 else 0, 2
            ),
        }


@dataclass
class LimitCheckResult:
    """Result of checking a limit."""
    allowed: bool
    limit_type: str
    current_value: int
    max_value: int
    remaining: int
    reset_at: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "allowed": self.allowed,
            "limit_type": self.limit_type,
            "current_value": self.current_value,
            "max_value": self.max_value,
            "remaining": self.remaining,
            "reset_at": self.reset_at,
            "message": self.message,
        }


@dataclass
class UsageSummary:
    """Usage summary across all limits."""
    tenant_id: str
    limits: List[Dict[str, Any]]
    total_api_calls: int
    total_token_usage: int
    as_of: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "limits": self.limits,
            "total_api_calls": self.total_api_calls,
            "total_token_usage": self.total_token_usage,
            "as_of": self.as_of,
        }


class LimitsFacade:
    """
    Facade for limit operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    limit services.

    Layer: L4 (Domain Logic)
    Callers: limits.py (L2), aos_sdk
    """

    def __init__(self):
        """Initialize facade."""
        self._limits: Dict[str, LimitConfig] = {}

    def _get_or_create_limit(
        self,
        tenant_id: str,
        limit_type: str,
        period: str = "day",
        max_value: int = 10000,
    ) -> LimitConfig:
        """Get or create a limit configuration."""
        key = f"{tenant_id}:{limit_type}"
        if key not in self._limits:
            now = datetime.now(timezone.utc)
            from datetime import timedelta

            # Calculate reset time based on period
            if period == LimitPeriod.MINUTE.value:
                reset_at = now + timedelta(minutes=1)
            elif period == LimitPeriod.HOUR.value:
                reset_at = now + timedelta(hours=1)
            elif period == LimitPeriod.MONTH.value:
                reset_at = now + timedelta(days=30)
            else:  # day
                reset_at = now + timedelta(days=1)

            self._limits[key] = LimitConfig(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                limit_type=limit_type,
                period=period,
                max_value=max_value,
                current_value=0,
                reset_at=reset_at.isoformat(),
                enabled=True,
                created_at=now.isoformat(),
            )
        return self._limits[key]

    # =========================================================================
    # Limit Operations (GAP-122)
    # =========================================================================

    async def list_limits(
        self,
        tenant_id: str,
        limit_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[LimitConfig]:
        """
        List limits for a tenant.

        Args:
            tenant_id: Tenant ID
            limit_type: Optional filter by type
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of LimitConfig
        """
        # Ensure default limits exist
        for lt in LimitType:
            self._get_or_create_limit(tenant_id, lt.value)

        results = []
        for lim in self._limits.values():
            if lim.tenant_id != tenant_id:
                continue
            if limit_type and lim.limit_type != limit_type:
                continue
            results.append(lim)

        results.sort(key=lambda l: l.limit_type)
        return results[offset:offset + limit]

    async def get_limit(
        self,
        limit_id: str,
        tenant_id: str,
    ) -> Optional[LimitConfig]:
        """
        Get a specific limit.

        Args:
            limit_id: Limit ID
            tenant_id: Tenant ID for authorization

        Returns:
            LimitConfig or None if not found
        """
        for lim in self._limits.values():
            if lim.id == limit_id and lim.tenant_id == tenant_id:
                return lim
        return None

    async def update_limit(
        self,
        limit_id: str,
        tenant_id: str,
        max_value: Optional[int] = None,
        enabled: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[LimitConfig]:
        """
        Update a limit.

        Args:
            limit_id: Limit ID
            tenant_id: Tenant ID for authorization
            max_value: New maximum value
            enabled: New enabled state
            metadata: New metadata

        Returns:
            Updated LimitConfig or None if not found
        """
        lim = None
        for l in self._limits.values():
            if l.id == limit_id and l.tenant_id == tenant_id:
                lim = l
                break

        if not lim:
            return None

        now = datetime.now(timezone.utc)

        if max_value is not None:
            lim.max_value = max_value
        if enabled is not None:
            lim.enabled = enabled
        if metadata:
            lim.metadata.update(metadata)

        lim.updated_at = now.isoformat()
        return lim

    async def check_limit(
        self,
        tenant_id: str,
        limit_type: str,
        increment: int = 1,
    ) -> LimitCheckResult:
        """
        Check if a limit allows the operation.

        Args:
            tenant_id: Tenant ID
            limit_type: Type of limit to check
            increment: Amount to increment if allowed

        Returns:
            LimitCheckResult
        """
        lim = self._get_or_create_limit(tenant_id, limit_type)

        now = datetime.now(timezone.utc)

        # Check if reset is needed
        reset_at = datetime.fromisoformat(lim.reset_at.replace("Z", "+00:00"))
        if now >= reset_at:
            lim.current_value = 0
            from datetime import timedelta
            if lim.period == LimitPeriod.MINUTE.value:
                lim.reset_at = (now + timedelta(minutes=1)).isoformat()
            elif lim.period == LimitPeriod.HOUR.value:
                lim.reset_at = (now + timedelta(hours=1)).isoformat()
            elif lim.period == LimitPeriod.MONTH.value:
                lim.reset_at = (now + timedelta(days=30)).isoformat()
            else:
                lim.reset_at = (now + timedelta(days=1)).isoformat()

        # Check if allowed
        remaining = lim.max_value - lim.current_value
        allowed = lim.enabled and (lim.current_value + increment <= lim.max_value)

        if allowed:
            lim.current_value += increment
            message = "Allowed"
        else:
            message = f"Limit exceeded: {lim.current_value}/{lim.max_value}"

        return LimitCheckResult(
            allowed=allowed,
            limit_type=limit_type,
            current_value=lim.current_value,
            max_value=lim.max_value,
            remaining=max(0, remaining - (increment if allowed else 0)),
            reset_at=lim.reset_at,
            message=message,
        )

    async def get_usage(
        self,
        tenant_id: str,
    ) -> UsageSummary:
        """
        Get current usage summary.

        Args:
            tenant_id: Tenant ID

        Returns:
            UsageSummary
        """
        # Ensure default limits exist
        for lt in LimitType:
            self._get_or_create_limit(tenant_id, lt.value)

        limits = []
        total_api_calls = 0
        total_token_usage = 0

        for lim in self._limits.values():
            if lim.tenant_id != tenant_id:
                continue
            limits.append(lim.to_dict())
            if lim.limit_type == LimitType.API_CALLS.value:
                total_api_calls = lim.current_value
            elif lim.limit_type == LimitType.TOKEN_USAGE.value:
                total_token_usage = lim.current_value

        now = datetime.now(timezone.utc)

        return UsageSummary(
            tenant_id=tenant_id,
            limits=limits,
            total_api_calls=total_api_calls,
            total_token_usage=total_token_usage,
            as_of=now.isoformat(),
        )

    async def reset_limit(
        self,
        tenant_id: str,
        limit_type: str,
    ) -> Optional[LimitConfig]:
        """
        Reset a limit's current value.

        Args:
            tenant_id: Tenant ID
            limit_type: Type of limit to reset

        Returns:
            Updated LimitConfig or None if not found
        """
        key = f"{tenant_id}:{limit_type}"
        lim = self._limits.get(key)
        if not lim:
            return None

        now = datetime.now(timezone.utc)
        lim.current_value = 0
        lim.updated_at = now.isoformat()

        logger.info(
            "facade.reset_limit",
            extra={"tenant_id": tenant_id, "limit_type": limit_type}
        )

        return lim


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[LimitsFacade] = None


def get_limits_facade() -> LimitsFacade:
    """
    Get the limits facade instance.

    This is the recommended way to access limit operations
    from L2 APIs and the SDK.

    Returns:
        LimitsFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = LimitsFacade()
    return _facade_instance
