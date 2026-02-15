# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: override_signal
#   Subscribes: none
# Data Access:
#   Reads: limits, limit_overrides
#   Writes: limit_overrides
# Database:
#   Scope: domain (policies)
#   Models: Limit, LimitOverride
# Role: Limit override driver (PIN-LIM-05) - DB boundary crossing
# Callers: L5 engines, api/limits/override.py
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, PIN-LIM-05

"""
Limit Override Driver (PIN-LIM-05)

L6 driver for limit_overrides table. All persistence logic
for temporary limit overrides lives here.

L6 contract:
- Receives AsyncSession from caller (L5 or L4 coordinator)
- NEVER commits — caller owns transaction
- Returns domain objects (LimitOverrideResponse) or raises typed errors
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_control_plane import Limit, LimitOverride
from app.hoc.cus.controls.L5_schemas.overrides import (
    LimitOverrideRequest,
    LimitOverrideResponse,
    OverrideStatus,
)

# Re-export error types from L5_schemas for backward compatibility (PIN-504)
from app.hoc.cus.controls.L5_schemas.override_types import (
    LimitOverrideServiceError,
    LimitNotFoundError,
    OverrideNotFoundError,
    OverrideValidationError,
    StackingAbuseError,
)


class LimitOverrideService:
    """
    Driver for limit override lifecycle.

    INVARIANTS:
    - One override per limit (no stacking)
    - Override cannot exceed plan quota cap
    - Max 5 active overrides per tenant
    - All overrides require justification

    Transaction contract:
    - All methods receive an AsyncSession
    - No method calls session.commit()
    - Caller (L4 coordinator) owns commit authority
    """

    MAX_ACTIVE_PER_TENANT = 5
    MAX_DURATION_HOURS = 168  # 1 week

    def __init__(self, session: AsyncSession):
        self.session = session

    async def request_override(
        self,
        tenant_id: str,
        request: LimitOverrideRequest,
        requested_by: str,
    ) -> LimitOverrideResponse:
        """
        Request a temporary limit override.

        Args:
            tenant_id: Requesting tenant ID
            request: Override request details
            requested_by: User ID making the request

        Returns:
            Override response

        Raises:
            LimitNotFoundError: If limit not found
            OverrideValidationError: If validation fails
            StackingAbuseError: If too many active overrides
        """
        # Validate limit exists
        limit = await self._get_limit(tenant_id, request.limit_id)

        # Check stacking abuse — count ACTIVE overrides for tenant
        active_count_stmt = select(func.count()).select_from(LimitOverride).where(
            and_(
                LimitOverride.tenant_id == tenant_id,
                LimitOverride.status == OverrideStatus.ACTIVE.value,
            )
        )
        active_count = (await self.session.execute(active_count_stmt)).scalar_one()
        if active_count >= self.MAX_ACTIVE_PER_TENANT:
            raise StackingAbuseError(
                f"Maximum {self.MAX_ACTIVE_PER_TENANT} active overrides allowed per tenant"
            )

        # Check for existing override on this limit (no stacking)
        existing_stmt = select(LimitOverride.id).where(
            and_(
                LimitOverride.limit_id == request.limit_id,
                LimitOverride.tenant_id == tenant_id,
                LimitOverride.status.in_([
                    OverrideStatus.PENDING.value,
                    OverrideStatus.APPROVED.value,
                    OverrideStatus.ACTIVE.value,
                ]),
            )
        ).limit(1)
        existing = (await self.session.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            raise OverrideValidationError(
                f"Override already exists for limit {request.limit_id}"
            )

        # Validate duration
        if request.duration_hours > self.MAX_DURATION_HOURS:
            raise OverrideValidationError(
                f"Maximum override duration is {self.MAX_DURATION_HOURS} hours"
            )

        # Calculate timing
        now = datetime.now(timezone.utc)
        starts_at = now if request.start_immediately else request.scheduled_start
        expires_at = starts_at + timedelta(hours=request.duration_hours) if starts_at else None

        # Determine initial status
        status = OverrideStatus.ACTIVE.value if request.start_immediately else OverrideStatus.PENDING.value

        # Create override record
        override = LimitOverride(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            limit_id=request.limit_id,
            original_value=limit.max_value,
            override_value=request.override_value,
            status=status,
            requested_at=now,
            approved_at=now if request.start_immediately else None,
            starts_at=starts_at,
            expires_at=expires_at,
            requested_by=requested_by,
            approved_by=requested_by if request.start_immediately else None,
            reason=request.reason,
        )
        self.session.add(override)
        await self.session.flush()

        return self._to_response(override, limit.name)

    async def get_override(
        self,
        tenant_id: str,
        override_id: str,
    ) -> LimitOverrideResponse:
        """Get an override by ID."""
        stmt = (
            select(LimitOverride, Limit.name)
            .join(Limit, LimitOverride.limit_id == Limit.id)
            .where(
                and_(
                    LimitOverride.id == override_id,
                    LimitOverride.tenant_id == tenant_id,
                )
            )
        )
        row = (await self.session.execute(stmt)).one_or_none()
        if not row:
            raise OverrideNotFoundError(f"Override {override_id} not found")
        override, limit_name = row
        return self._to_response(override, limit_name)

    async def list_overrides(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[LimitOverrideResponse], int]:
        """List overrides for a tenant."""
        base_where = [LimitOverride.tenant_id == tenant_id]
        if status is not None:
            base_where.append(LimitOverride.status == status)

        # Total count
        count_stmt = select(func.count()).select_from(LimitOverride).where(and_(*base_where))
        total = (await self.session.execute(count_stmt)).scalar_one()

        # Fetch page with limit name
        items_stmt = (
            select(LimitOverride, Limit.name)
            .join(Limit, LimitOverride.limit_id == Limit.id)
            .where(and_(*base_where))
            .order_by(LimitOverride.requested_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = (await self.session.execute(items_stmt)).all()
        items = [self._to_response(ov, ln) for ov, ln in rows]
        return items, total

    async def cancel_override(
        self,
        tenant_id: str,
        override_id: str,
        cancelled_by: str,
    ) -> LimitOverrideResponse:
        """Cancel a pending or active override."""
        stmt = (
            select(LimitOverride, Limit.name)
            .join(Limit, LimitOverride.limit_id == Limit.id)
            .where(
                and_(
                    LimitOverride.id == override_id,
                    LimitOverride.tenant_id == tenant_id,
                )
            )
        )
        row = (await self.session.execute(stmt)).one_or_none()
        if not row:
            raise OverrideNotFoundError(f"Override {override_id} not found")

        override, limit_name = row

        if override.status not in (
            OverrideStatus.PENDING.value,
            OverrideStatus.APPROVED.value,
            OverrideStatus.ACTIVE.value,
        ):
            raise OverrideValidationError("Only pending/active overrides can be cancelled")

        override.status = OverrideStatus.CANCELLED.value
        override.cancelled_at = datetime.now(timezone.utc)
        override.cancelled_by = cancelled_by
        await self.session.flush()

        return self._to_response(override, limit_name)

    async def approve_override(
        self,
        tenant_id: str,
        override_id: str,
        approved_by: str,
        adjusted_value: Decimal | None = None,
        adjusted_duration_hours: int | None = None,
    ) -> LimitOverrideResponse:
        """Approve a pending override. Moves to APPROVED or ACTIVE."""
        stmt = (
            select(LimitOverride, Limit.name)
            .join(Limit, LimitOverride.limit_id == Limit.id)
            .where(
                and_(
                    LimitOverride.id == override_id,
                    LimitOverride.tenant_id == tenant_id,
                )
            )
        )
        row = (await self.session.execute(stmt)).one_or_none()
        if not row:
            raise OverrideNotFoundError(f"Override {override_id} not found")

        override, limit_name = row

        if override.status != OverrideStatus.PENDING.value:
            raise OverrideValidationError("Only PENDING overrides can be approved")

        now = datetime.now(timezone.utc)
        override.approved_at = now
        override.approved_by = approved_by

        if adjusted_value is not None:
            override.override_value = adjusted_value
        if adjusted_duration_hours is not None:
            starts_at = override.starts_at or now
            override.expires_at = starts_at + timedelta(hours=adjusted_duration_hours)

        # Activate immediately if starts_at is in the past or now
        if override.starts_at and override.starts_at <= now:
            override.status = OverrideStatus.ACTIVE.value
        else:
            override.status = OverrideStatus.APPROVED.value

        await self.session.flush()
        return self._to_response(override, limit_name)

    async def reject_override(
        self,
        tenant_id: str,
        override_id: str,
        rejected_by: str,
        rejection_reason: str,
    ) -> LimitOverrideResponse:
        """Reject a pending override."""
        stmt = (
            select(LimitOverride, Limit.name)
            .join(Limit, LimitOverride.limit_id == Limit.id)
            .where(
                and_(
                    LimitOverride.id == override_id,
                    LimitOverride.tenant_id == tenant_id,
                )
            )
        )
        row = (await self.session.execute(stmt)).one_or_none()
        if not row:
            raise OverrideNotFoundError(f"Override {override_id} not found")

        override, limit_name = row

        if override.status != OverrideStatus.PENDING.value:
            raise OverrideValidationError("Only PENDING overrides can be rejected")

        override.status = OverrideStatus.REJECTED.value
        override.rejection_reason = rejection_reason
        override.approved_by = rejected_by  # Record who acted
        override.approved_at = datetime.now(timezone.utc)
        await self.session.flush()

        return self._to_response(override, limit_name)

    async def expire_overrides(self) -> int:
        """Mark expired ACTIVE overrides as EXPIRED. Returns count updated."""
        from sqlalchemy import update

        now = datetime.now(timezone.utc)
        stmt = (
            update(LimitOverride)
            .where(
                and_(
                    LimitOverride.status == OverrideStatus.ACTIVE.value,
                    LimitOverride.expires_at.isnot(None),
                    LimitOverride.expires_at <= now,
                )
            )
            .values(status=OverrideStatus.EXPIRED.value)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def _get_limit(self, tenant_id: str, limit_id: str) -> Limit:
        """Get limit by ID with tenant check."""
        stmt = select(Limit).where(
            and_(
                Limit.id == limit_id,
                Limit.tenant_id == tenant_id,
            )
        )
        result = await self.session.execute(stmt)
        limit = result.scalar_one_or_none()

        if not limit:
            raise LimitNotFoundError(f"Limit {limit_id} not found")

        return limit

    def _to_response(self, override: LimitOverride, limit_name: str) -> LimitOverrideResponse:
        """Convert DB model to response."""
        return LimitOverrideResponse(
            override_id=override.id,
            limit_id=override.limit_id,
            limit_name=limit_name,
            tenant_id=override.tenant_id,
            original_value=override.original_value,
            override_value=override.override_value,
            effective_value=override.override_value if override.status == OverrideStatus.ACTIVE.value else override.original_value,
            status=OverrideStatus(override.status),
            requested_at=override.requested_at,
            approved_at=override.approved_at,
            starts_at=override.starts_at,
            expires_at=override.expires_at,
            requested_by=override.requested_by,
            approved_by=override.approved_by,
            reason=override.reason,
            rejection_reason=override.rejection_reason,
        )
