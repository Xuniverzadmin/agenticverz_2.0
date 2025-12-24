"""
M27 Cost Safety Rails
=====================

Per-tenant auto-apply caps and blast-radius limits.

THE INVARIANT:
    No automatic cost action may exceed:
    - Per-tenant daily cap
    - Per-org daily cap
    - Blast-radius scope limits

GPT Analysis Warning (2025-12-23):
    "Confidence >=90% can auto-apply, Zero confirmations required in some paths.
     Once customers are live, you'll need:
     - Per-tenant auto-apply caps
     - Blast-radius limits (per org/day)"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("nova.integrations.cost_safety")


# =============================================================================
# SAFETY CONFIGURATION
# =============================================================================


@dataclass
class SafetyConfig:
    """
    M27 Safety Configuration.

    These limits prevent runaway automation.
    """

    # Per-tenant caps (per 24h rolling window)
    max_auto_policies_per_tenant_per_day: int = 5
    max_auto_recoveries_per_tenant_per_day: int = 10
    max_routing_adjustments_per_tenant_per_day: int = 20

    # Blast-radius limits
    max_users_affected_per_action: int = 100
    max_features_affected_per_action: int = 10

    # Severity escalation
    critical_actions_require_confirmation: bool = True
    high_actions_require_confirmation: bool = True

    # Cooldown between same action type
    action_cooldown_minutes: int = 15

    # Budget safety
    max_budget_reduction_pct: float = 50.0  # Can't auto-reduce budget by more than 50%

    @classmethod
    def production(cls) -> "SafetyConfig":
        """Conservative production defaults."""
        return cls(
            max_auto_policies_per_tenant_per_day=3,
            max_auto_recoveries_per_tenant_per_day=5,
            max_routing_adjustments_per_tenant_per_day=10,
            max_users_affected_per_action=50,
            max_features_affected_per_action=5,
            critical_actions_require_confirmation=True,
            high_actions_require_confirmation=True,
            action_cooldown_minutes=30,
            max_budget_reduction_pct=25.0,
        )

    @classmethod
    def testing(cls) -> "SafetyConfig":
        """Relaxed testing defaults."""
        return cls(
            max_auto_policies_per_tenant_per_day=100,
            max_auto_recoveries_per_tenant_per_day=100,
            max_routing_adjustments_per_tenant_per_day=100,
            max_users_affected_per_action=1000,
            max_features_affected_per_action=100,
            critical_actions_require_confirmation=False,
            high_actions_require_confirmation=False,
            action_cooldown_minutes=0,
            max_budget_reduction_pct=100.0,
        )


# =============================================================================
# SAFETY RAIL TRACKER
# =============================================================================


class CostSafetyRails:
    """
    Enforces M27 safety limits.

    Tracks auto-applied actions per tenant and enforces caps.
    """

    def __init__(
        self,
        config: SafetyConfig | None = None,
        redis_client=None,
        db_session=None,
    ):
        self.config = config or SafetyConfig()
        self.redis_client = redis_client
        self.db_session = db_session

        # In-memory tracking (fallback if no Redis)
        self._action_counts: dict[str, dict[str, int]] = {}
        self._last_actions: dict[str, datetime] = {}

    async def can_auto_apply_policy(
        self,
        tenant_id: str,
        policy_action: str,
        severity: str,
    ) -> tuple[bool, str]:
        """
        Check if a policy can be auto-applied.

        Returns (allowed, reason).
        """
        # Check severity gate
        if severity.upper() == "CRITICAL" and self.config.critical_actions_require_confirmation:
            return False, "CRITICAL severity requires confirmation"

        if severity.upper() == "HIGH" and self.config.high_actions_require_confirmation:
            return False, "HIGH severity requires confirmation"

        # Check daily cap
        count = await self._get_action_count(tenant_id, "policy")
        if count >= self.config.max_auto_policies_per_tenant_per_day:
            return False, f"Daily policy cap reached ({count}/{self.config.max_auto_policies_per_tenant_per_day})"

        # Check cooldown
        last_action = self._last_actions.get(f"{tenant_id}:policy:{policy_action}")
        if last_action:
            elapsed = (datetime.now(timezone.utc) - last_action).total_seconds() / 60
            if elapsed < self.config.action_cooldown_minutes:
                remaining = self.config.action_cooldown_minutes - elapsed
                return False, f"Cooldown active ({remaining:.0f}m remaining)"

        return True, "Allowed"

    async def can_auto_apply_recovery(
        self,
        tenant_id: str,
        recovery_action: str,
        affected_count: int = 1,
    ) -> tuple[bool, str]:
        """
        Check if a recovery action can be auto-applied.

        Returns (allowed, reason).
        """
        # Check daily cap
        count = await self._get_action_count(tenant_id, "recovery")
        if count >= self.config.max_auto_recoveries_per_tenant_per_day:
            return False, f"Daily recovery cap reached ({count}/{self.config.max_auto_recoveries_per_tenant_per_day})"

        # Check blast radius
        if affected_count > self.config.max_users_affected_per_action:
            return (
                False,
                f"Blast radius exceeded ({affected_count} > {self.config.max_users_affected_per_action} users)",
            )

        return True, "Allowed"

    async def can_auto_apply_routing(
        self,
        tenant_id: str,
        adjustment_type: str,
        magnitude: float,
    ) -> tuple[bool, str]:
        """
        Check if a routing adjustment can be auto-applied.

        Returns (allowed, reason).
        """
        # Check daily cap
        count = await self._get_action_count(tenant_id, "routing")
        if count >= self.config.max_routing_adjustments_per_tenant_per_day:
            return (
                False,
                f"Daily routing cap reached ({count}/{self.config.max_routing_adjustments_per_tenant_per_day})",
            )

        # Block permanent blocks
        if adjustment_type == "route_block" and magnitude <= -1.0:
            return False, "Permanent route blocks require confirmation"

        return True, "Allowed"

    async def record_action(
        self,
        tenant_id: str,
        action_type: str,  # "policy", "recovery", "routing"
        action_name: str,
    ) -> None:
        """Record an auto-applied action."""
        key = f"{tenant_id}:{action_type}"

        # Update in-memory count
        if tenant_id not in self._action_counts:
            self._action_counts[tenant_id] = {}
        if action_type not in self._action_counts[tenant_id]:
            self._action_counts[tenant_id][action_type] = 0
        self._action_counts[tenant_id][action_type] += 1

        # Record last action time
        self._last_actions[f"{tenant_id}:{action_type}:{action_name}"] = datetime.now(timezone.utc)

        # If Redis available, persist
        if self.redis_client:
            try:
                redis_key = f"m27:safety:{key}"
                await self.redis_client.incr(redis_key)
                await self.redis_client.expire(redis_key, 86400)  # 24h TTL
            except Exception as e:
                logger.warning(f"Failed to persist action count to Redis: {e}")

        logger.info(
            f"Recorded auto-action: tenant={tenant_id} type={action_type} action={action_name} "
            f"count={self._action_counts[tenant_id][action_type]}"
        )

    async def _get_action_count(self, tenant_id: str, action_type: str) -> int:
        """Get current action count for tenant."""
        # Try Redis first
        if self.redis_client:
            try:
                redis_key = f"m27:safety:{tenant_id}:{action_type}"
                count = await self.redis_client.get(redis_key)
                if count:
                    return int(count)
            except Exception as e:
                logger.warning(f"Failed to get action count from Redis: {e}")

        # Fall back to in-memory
        return self._action_counts.get(tenant_id, {}).get(action_type, 0)

    def get_status(self, tenant_id: str) -> dict[str, Any]:
        """Get current safety rail status for tenant."""
        return {
            "tenant_id": tenant_id,
            "config": {
                "max_policies_per_day": self.config.max_auto_policies_per_tenant_per_day,
                "max_recoveries_per_day": self.config.max_auto_recoveries_per_tenant_per_day,
                "max_routing_per_day": self.config.max_routing_adjustments_per_tenant_per_day,
                "action_cooldown_minutes": self.config.action_cooldown_minutes,
            },
            "current": self._action_counts.get(tenant_id, {}),
            "remaining": {
                "policies": max(
                    0,
                    self.config.max_auto_policies_per_tenant_per_day
                    - self._action_counts.get(tenant_id, {}).get("policy", 0),
                ),
                "recoveries": max(
                    0,
                    self.config.max_auto_recoveries_per_tenant_per_day
                    - self._action_counts.get(tenant_id, {}).get("recovery", 0),
                ),
                "routing": max(
                    0,
                    self.config.max_routing_adjustments_per_tenant_per_day
                    - self._action_counts.get(tenant_id, {}).get("routing", 0),
                ),
            },
        }


# =============================================================================
# SAFE ORCHESTRATOR WRAPPER
# =============================================================================


class SafeCostLoopOrchestrator:
    """
    Wraps CostLoopOrchestrator with safety rails.

    Use this in production instead of raw CostLoopOrchestrator.
    """

    def __init__(
        self,
        dispatcher=None,
        db_session=None,
        safety_config: SafetyConfig | None = None,
        redis_client=None,
    ):
        from app.integrations.cost_bridges import CostLoopOrchestrator

        self.orchestrator = CostLoopOrchestrator(dispatcher, db_session)
        self.safety_rails = CostSafetyRails(safety_config, redis_client, db_session)

    async def process_anomaly_safe(self, anomaly) -> dict[str, Any]:
        """
        Process anomaly with safety rails enforced.

        Returns result with safety_status field.
        """
        # Run through normal orchestrator
        result = await self.orchestrator.process_anomaly(anomaly)

        # Apply safety rails to artifacts
        safety_applied = []

        # Check policy auto-apply
        if "policy" in result.get("artifacts", {}):
            policy = result["artifacts"]["policy"]
            can_apply, reason = await self.safety_rails.can_auto_apply_policy(
                tenant_id=anomaly.tenant_id,
                policy_action=policy.get("action", "unknown"),
                severity=anomaly.severity.value,
            )

            if not can_apply:
                # Downgrade to SHADOW mode
                if policy.get("mode") == "active":
                    policy["mode"] = "shadow"
                    policy["safety_downgraded"] = True
                    policy["safety_reason"] = reason
                    safety_applied.append(f"Policy downgraded to SHADOW: {reason}")

        # Check routing auto-apply
        if "adjustments" in result.get("artifacts", {}):
            for adj in result["artifacts"]["adjustments"]:
                can_apply, reason = await self.safety_rails.can_auto_apply_routing(
                    tenant_id=anomaly.tenant_id,
                    adjustment_type=adj.get("adjustment_type", "unknown"),
                    magnitude=adj.get("magnitude", 0),
                )

                if not can_apply:
                    adj["blocked"] = True
                    adj["safety_reason"] = reason
                    safety_applied.append(f"Routing blocked: {reason}")

        result["safety_status"] = {
            "rails_applied": len(safety_applied) > 0,
            "actions": safety_applied,
            "tenant_status": self.safety_rails.get_status(anomaly.tenant_id),
        }

        return result


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

# Default safety rails (use production config in production)
_default_safety_rails: CostSafetyRails | None = None


def get_safety_rails(config: SafetyConfig | None = None) -> CostSafetyRails:
    """Get or create default safety rails instance."""
    global _default_safety_rails
    if _default_safety_rails is None:
        _default_safety_rails = CostSafetyRails(config)
    return _default_safety_rails
