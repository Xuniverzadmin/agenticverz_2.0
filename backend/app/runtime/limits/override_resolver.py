# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: runtime
#   Execution: sync
# Role: Override resolution for limits evaluation (PIN-LIM-05)
# Callers: runtime/limits/evaluator.py, services/limits/simulation_service.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Override Resolver (Section C10)

"""
Override Resolver (PIN-LIM-05)

Resolves and applies active overrides during limit evaluation.

Responsibilities:
- Check override validity window
- Merge override values
- Prevent override stacking abuse
- Track applied overrides for audit
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional


@dataclass
class OverrideRecord:
    """Database record representation for an override."""
    override_id: str
    limit_id: str
    tenant_id: str
    original_value: Decimal
    override_value: Decimal
    status: str  # PENDING, APPROVED, ACTIVE, EXPIRED, REJECTED, CANCELLED
    starts_at: Optional[datetime]
    expires_at: Optional[datetime]
    requested_by: str
    approved_by: Optional[str]
    reason: str


@dataclass
class ResolvedOverride:
    """Output: resolved override for evaluation."""
    override_id: str
    limit_id: str
    original_value: Decimal
    override_value: Decimal
    is_active: bool
    remaining_seconds: Optional[int]


class OverrideResolver:
    """
    Resolves active overrides for limit evaluation.

    INVARIANTS:
    - Only ACTIVE overrides with valid time window are applied
    - One override per limit (no stacking)
    - Override value cannot exceed plan quota (safety cap)
    """

    def __init__(self, plan_quota_cap: Optional[Decimal] = None):
        """
        Initialize resolver with optional plan quota cap.

        Args:
            plan_quota_cap: Maximum value an override can set (safety limit)
        """
        self.plan_quota_cap = plan_quota_cap

    def resolve(
        self,
        overrides: list[OverrideRecord],
        as_of: Optional[datetime] = None,
    ) -> list[ResolvedOverride]:
        """
        Resolve which overrides are currently active.

        Args:
            overrides: List of override records to evaluate
            as_of: Time to evaluate against (defaults to now)

        Returns:
            List of resolved overrides that are currently active
        """
        if as_of is None:
            as_of = datetime.now(timezone.utc)

        resolved = []
        seen_limits: set[str] = set()

        for override in overrides:
            # Skip if not ACTIVE status
            if override.status != "ACTIVE":
                continue

            # Skip if limit already has an override (no stacking)
            if override.limit_id in seen_limits:
                continue

            # Check time window
            is_active = self._is_within_window(override, as_of)
            if not is_active:
                continue

            # Calculate remaining time
            remaining_seconds = None
            if override.expires_at:
                delta = override.expires_at - as_of
                remaining_seconds = max(0, int(delta.total_seconds()))

            # Apply safety cap
            effective_value = override.override_value
            if self.plan_quota_cap and effective_value > self.plan_quota_cap:
                effective_value = self.plan_quota_cap

            resolved.append(ResolvedOverride(
                override_id=override.override_id,
                limit_id=override.limit_id,
                original_value=override.original_value,
                override_value=effective_value,
                is_active=True,
                remaining_seconds=remaining_seconds,
            ))

            seen_limits.add(override.limit_id)

        return resolved

    def resolve_for_limit(
        self,
        limit_id: str,
        overrides: list[OverrideRecord],
        as_of: Optional[datetime] = None,
    ) -> Optional[ResolvedOverride]:
        """
        Resolve override for a specific limit.

        Args:
            limit_id: The limit to find override for
            overrides: List of override records
            as_of: Time to evaluate against

        Returns:
            Resolved override if found and active, None otherwise
        """
        relevant = [o for o in overrides if o.limit_id == limit_id]
        resolved = self.resolve(relevant, as_of)
        return resolved[0] if resolved else None

    def _is_within_window(
        self,
        override: OverrideRecord,
        as_of: datetime,
    ) -> bool:
        """Check if override is within its validity window."""
        # Must have started
        if override.starts_at:
            # Make both datetimes timezone-aware for comparison
            starts_at = self._ensure_tz_aware(override.starts_at)
            as_of_aware = self._ensure_tz_aware(as_of)
            if as_of_aware < starts_at:
                return False

        # Must not have expired
        if override.expires_at:
            expires_at = self._ensure_tz_aware(override.expires_at)
            as_of_aware = self._ensure_tz_aware(as_of)
            if as_of_aware >= expires_at:
                return False

        return True

    def _ensure_tz_aware(self, dt: datetime) -> datetime:
        """Ensure datetime is timezone-aware (UTC)."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def check_stacking_abuse(
        self,
        tenant_id: str,
        overrides: list[OverrideRecord],
        max_active_per_tenant: int = 5,
    ) -> bool:
        """
        Check if tenant has too many active overrides.

        Args:
            tenant_id: Tenant to check
            overrides: All override records
            max_active_per_tenant: Maximum allowed active overrides

        Returns:
            True if stacking limit exceeded
        """
        active_count = sum(
            1 for o in overrides
            if o.tenant_id == tenant_id and o.status == "ACTIVE"
        )
        return active_count >= max_active_per_tenant

    def compute_effective_limit(
        self,
        limit_value: Decimal,
        override: Optional[ResolvedOverride],
    ) -> Decimal:
        """
        Compute effective limit value with override applied.

        Args:
            limit_value: Original limit value
            override: Resolved override (if any)

        Returns:
            Effective limit value to use for evaluation
        """
        if override and override.is_active:
            return override.override_value
        return limit_value
