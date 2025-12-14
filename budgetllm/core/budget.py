"""
Budget enforcement for LLM API calls.

Provides hard limits (daily, monthly, cumulative) with automatic kill-switch.
"""

import time
from datetime import datetime, timezone
from typing import Optional, Protocol, runtime_checkable


class BudgetExceededError(Exception):
    """Raised when budget limit is exceeded and auto_pause is enabled."""

    def __init__(self, message: str, limit_type: str, spent: int, limit: int):
        super().__init__(message)
        self.limit_type = limit_type
        self.spent = spent
        self.limit = limit


@runtime_checkable
class StateAdapter(Protocol):
    """Protocol for state storage backends."""

    def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        ...

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Set value with optional TTL in seconds."""
        ...

    def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter and return new value."""
        ...


class InMemoryStateAdapter:
    """Simple in-memory state adapter for single-process usage."""

    def __init__(self):
        self._store: dict = {}
        self._expiry: dict = {}

    def get(self, key: str) -> Optional[str]:
        if key in self._expiry:
            if time.time() > self._expiry[key]:
                del self._store[key]
                del self._expiry[key]
                return None
        return self._store.get(key)

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        self._store[key] = value
        if ttl:
            self._expiry[key] = time.time() + ttl

    def incr(self, key: str, amount: int = 1) -> int:
        current = int(self._store.get(key, 0))
        new_value = current + amount
        self._store[key] = str(new_value)
        return new_value


class RedisStateAdapter:
    """Redis-backed state adapter for multi-process usage."""

    def __init__(self, redis_url: str):
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Redis support requires 'redis' package. "
                "Install with: pip install budgetllm[redis]"
            )
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

    def get(self, key: str) -> Optional[str]:
        return self._client.get(key)

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        if ttl:
            self._client.setex(key, ttl, value)
        else:
            self._client.set(key, value)

    def incr(self, key: str, amount: int = 1) -> int:
        return self._client.incrby(key, amount)


class BudgetTracker:
    """
    Track and enforce LLM API spend limits.

    Supports:
    - Daily limit (resets at midnight UTC)
    - Monthly limit (resets on 1st of month)
    - Hard limit (cumulative, never resets)
    - Auto-pause (raises BudgetExceededError when limit hit)

    Example:
        tracker = BudgetTracker(
            daily_limit_cents=500,    # $5/day
            monthly_limit_cents=5000, # $50/month
            hard_limit_cents=10000,   # $100 total
            auto_pause=True,
        )

        # Before each LLM call:
        if not tracker.check_limits():
            raise BudgetExceededError(...)

        # After each LLM call:
        tracker.record_cost(cost_cents)
    """

    def __init__(
        self,
        daily_limit_cents: Optional[int] = None,
        monthly_limit_cents: Optional[int] = None,
        hard_limit_cents: Optional[int] = None,
        auto_pause: bool = True,
        state_adapter: Optional[StateAdapter] = None,
        key_prefix: str = "budgetllm",
    ):
        """
        Initialize budget tracker.

        Args:
            daily_limit_cents: Max spend per day (resets midnight UTC)
            monthly_limit_cents: Max spend per month (resets 1st of month)
            hard_limit_cents: Max cumulative spend (never resets)
            auto_pause: If True, raises BudgetExceededError when limit hit
            state_adapter: Storage backend (defaults to in-memory)
            key_prefix: Prefix for storage keys
        """
        self.daily_limit_cents = daily_limit_cents
        self.monthly_limit_cents = monthly_limit_cents
        self.hard_limit_cents = hard_limit_cents
        self.auto_pause = auto_pause
        self.key_prefix = key_prefix

        self._state = state_adapter or InMemoryStateAdapter()
        self._paused = False

    def _get_daily_key(self) -> str:
        """Get storage key for today's spend."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{self.key_prefix}:daily:{today}"

    def _get_monthly_key(self) -> str:
        """Get storage key for this month's spend."""
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        return f"{self.key_prefix}:monthly:{month}"

    def _get_total_key(self) -> str:
        """Get storage key for cumulative spend."""
        return f"{self.key_prefix}:total"

    def get_daily_spend(self) -> int:
        """Get today's spend in cents."""
        value = self._state.get(self._get_daily_key())
        return int(value) if value else 0

    def get_monthly_spend(self) -> int:
        """Get this month's spend in cents."""
        value = self._state.get(self._get_monthly_key())
        return int(value) if value else 0

    def get_total_spend(self) -> int:
        """Get cumulative spend in cents."""
        value = self._state.get(self._get_total_key())
        return int(value) if value else 0

    def record_cost(self, cost_cents: int) -> None:
        """
        Record a cost and update all counters.

        Args:
            cost_cents: Cost in cents to record
        """
        if cost_cents <= 0:
            return

        # Increment all counters
        self._state.incr(self._get_daily_key(), cost_cents)
        self._state.incr(self._get_monthly_key(), cost_cents)
        self._state.incr(self._get_total_key(), cost_cents)

    def check_limits(self) -> bool:
        """
        Check if any limit is exceeded.

        Returns:
            True if within limits, False if exceeded

        Raises:
            BudgetExceededError: If auto_pause=True and limit exceeded
        """
        if self._paused:
            if self.auto_pause:
                raise BudgetExceededError(
                    "Budget tracker is paused",
                    limit_type="paused",
                    spent=0,
                    limit=0,
                )
            return False

        # Check daily limit
        if self.daily_limit_cents is not None:
            daily_spend = self.get_daily_spend()
            if daily_spend >= self.daily_limit_cents:
                if self.auto_pause:
                    raise BudgetExceededError(
                        f"Daily limit exceeded: {daily_spend} >= {self.daily_limit_cents} cents",
                        limit_type="daily",
                        spent=daily_spend,
                        limit=self.daily_limit_cents,
                    )
                return False

        # Check monthly limit
        if self.monthly_limit_cents is not None:
            monthly_spend = self.get_monthly_spend()
            if monthly_spend >= self.monthly_limit_cents:
                if self.auto_pause:
                    raise BudgetExceededError(
                        f"Monthly limit exceeded: {monthly_spend} >= {self.monthly_limit_cents} cents",
                        limit_type="monthly",
                        spent=monthly_spend,
                        limit=self.monthly_limit_cents,
                    )
                return False

        # Check hard limit
        if self.hard_limit_cents is not None:
            total_spend = self.get_total_spend()
            if total_spend >= self.hard_limit_cents:
                if self.auto_pause:
                    raise BudgetExceededError(
                        f"Hard limit exceeded: {total_spend} >= {self.hard_limit_cents} cents",
                        limit_type="hard",
                        spent=total_spend,
                        limit=self.hard_limit_cents,
                    )
                return False

        return True

    def pause(self) -> None:
        """Manually pause the budget tracker (kill switch)."""
        self._paused = True

    def resume(self) -> None:
        """Resume the budget tracker."""
        self._paused = False

    def is_paused(self) -> bool:
        """Check if tracker is paused."""
        return self._paused

    def get_status(self) -> dict:
        """
        Get current budget status.

        Returns:
            Dict with spend and limit info for all tiers
        """
        daily_spend = self.get_daily_spend()
        monthly_spend = self.get_monthly_spend()
        total_spend = self.get_total_spend()

        return {
            "paused": self._paused,
            "daily": {
                "spent_cents": daily_spend,
                "limit_cents": self.daily_limit_cents,
                "remaining_cents": (
                    self.daily_limit_cents - daily_spend
                    if self.daily_limit_cents
                    else None
                ),
                "exceeded": (
                    daily_spend >= self.daily_limit_cents
                    if self.daily_limit_cents
                    else False
                ),
            },
            "monthly": {
                "spent_cents": monthly_spend,
                "limit_cents": self.monthly_limit_cents,
                "remaining_cents": (
                    self.monthly_limit_cents - monthly_spend
                    if self.monthly_limit_cents
                    else None
                ),
                "exceeded": (
                    monthly_spend >= self.monthly_limit_cents
                    if self.monthly_limit_cents
                    else False
                ),
            },
            "total": {
                "spent_cents": total_spend,
                "limit_cents": self.hard_limit_cents,
                "remaining_cents": (
                    self.hard_limit_cents - total_spend
                    if self.hard_limit_cents
                    else None
                ),
                "exceeded": (
                    total_spend >= self.hard_limit_cents
                    if self.hard_limit_cents
                    else False
                ),
            },
        }

    def reset_daily(self) -> None:
        """Reset daily spend counter (for testing)."""
        self._state.set(self._get_daily_key(), "0")

    def reset_monthly(self) -> None:
        """Reset monthly spend counter (for testing)."""
        self._state.set(self._get_monthly_key(), "0")

    def reset_total(self) -> None:
        """Reset total spend counter (for testing)."""
        self._state.set(self._get_total_key(), "0")

    def reset_all(self) -> None:
        """Reset all spend counters (for testing)."""
        self.reset_daily()
        self.reset_monthly()
        self.reset_total()
        self._paused = False
