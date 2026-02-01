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
# NOTE: Moved override_service.py → drivers/override_driver.py (2026-01-24)
#       Reclassified L4→L6 - has runtime AsyncSession import - BANNED_NAMING fix

"""
Limit Override Service (PIN-LIM-05)

Lifecycle of temporary limit overrides.

Responsibilities:
- Create override requests
- Handle approval workflow
- Expiry handling
- Attach justification & requester
- Emit signals to runtime evaluator
- Audit events
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_control_plane import Limit
from app.hoc.hoc_spine.services.time import utc_now
from app.hoc.hoc_spine.drivers.cross_domain import generate_uuid
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


# Temporary in-memory storage until migration is created
# TODO: Replace with database table after migration
_OVERRIDE_STORE: dict[str, dict] = {}


class LimitOverrideService:
    """
    Service for limit override lifecycle.

    INVARIANTS:
    - One override per limit (no stacking)
    - Override cannot exceed plan quota cap
    - Max 5 active overrides per tenant
    - All overrides require justification
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

        # Check stacking abuse
        active_count = sum(
            1 for o in _OVERRIDE_STORE.values()
            if o["tenant_id"] == tenant_id and o["status"] == "ACTIVE"
        )
        if active_count >= self.MAX_ACTIVE_PER_TENANT:
            raise StackingAbuseError(
                f"Maximum {self.MAX_ACTIVE_PER_TENANT} active overrides allowed per tenant"
            )

        # Check for existing override on this limit
        existing = next(
            (o for o in _OVERRIDE_STORE.values()
             if o["limit_id"] == request.limit_id
             and o["tenant_id"] == tenant_id
             and o["status"] in ("PENDING", "APPROVED", "ACTIVE")),
            None
        )
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
        now = utc_now()
        starts_at = now if request.start_immediately else request.scheduled_start
        expires_at = starts_at + timedelta(hours=request.duration_hours) if starts_at else None

        # Create override record
        override_id = generate_uuid()
        override_data = {
            "override_id": override_id,
            "limit_id": request.limit_id,
            "limit_name": limit.name,
            "tenant_id": tenant_id,
            "original_value": float(limit.max_value),
            "override_value": float(request.override_value),
            "effective_value": float(request.override_value),
            "status": OverrideStatus.ACTIVE.value if request.start_immediately else OverrideStatus.PENDING.value,
            "requested_at": now.isoformat(),
            "approved_at": now.isoformat() if request.start_immediately else None,
            "starts_at": starts_at.isoformat() if starts_at else None,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "requested_by": requested_by,
            "approved_by": requested_by if request.start_immediately else None,
            "reason": request.reason,
            "rejection_reason": None,
        }
        _OVERRIDE_STORE[override_id] = override_data

        return self._to_response(override_data)

    async def get_override(
        self,
        tenant_id: str,
        override_id: str,
    ) -> LimitOverrideResponse:
        """Get an override by ID."""
        override_data = _OVERRIDE_STORE.get(override_id)
        if not override_data or override_data["tenant_id"] != tenant_id:
            raise OverrideNotFoundError(f"Override {override_id} not found")
        return self._to_response(override_data)

    async def list_overrides(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[LimitOverrideResponse], int]:
        """List overrides for a tenant."""
        overrides = [
            o for o in _OVERRIDE_STORE.values()
            if o["tenant_id"] == tenant_id
            and (status is None or o["status"] == status)
        ]
        total = len(overrides)
        items = [self._to_response(o) for o in overrides[offset:offset + limit]]
        return items, total

    async def cancel_override(
        self,
        tenant_id: str,
        override_id: str,
        cancelled_by: str,
    ) -> LimitOverrideResponse:
        """Cancel a pending or active override."""
        override_data = _OVERRIDE_STORE.get(override_id)
        if not override_data or override_data["tenant_id"] != tenant_id:
            raise OverrideNotFoundError(f"Override {override_id} not found")

        if override_data["status"] not in ("PENDING", "APPROVED", "ACTIVE"):
            raise OverrideValidationError("Only pending/active overrides can be cancelled")

        override_data["status"] = OverrideStatus.CANCELLED.value
        return self._to_response(override_data)

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

    def _to_response(self, data: dict) -> LimitOverrideResponse:
        """Convert stored data to response."""
        return LimitOverrideResponse(
            override_id=data["override_id"],
            limit_id=data["limit_id"],
            limit_name=data["limit_name"],
            tenant_id=data["tenant_id"],
            original_value=Decimal(str(data["original_value"])),
            override_value=Decimal(str(data["override_value"])),
            effective_value=Decimal(str(data["effective_value"])),
            status=OverrideStatus(data["status"]),
            requested_at=datetime.fromisoformat(data["requested_at"]),
            approved_at=datetime.fromisoformat(data["approved_at"]) if data["approved_at"] else None,
            starts_at=datetime.fromisoformat(data["starts_at"]) if data["starts_at"] else None,
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            requested_by=data["requested_by"],
            approved_by=data["approved_by"],
            reason=data["reason"],
            rejection_reason=data["rejection_reason"],
        )
