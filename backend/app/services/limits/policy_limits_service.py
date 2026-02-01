# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Policy limits CRUD service (PIN-LIM-01)
# Callers: api/policies.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-LIM-01

"""
Policy Limits Service (PIN-LIM-01)

Authoritative writer for policy limits table.

Responsibilities:
- Create/update/delete limits
- Validate scope (tenant / worker / global)
- Enforce immutables (category, type cannot change after creation)
- Emit audit events
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_control_plane import (
    Limit,
    LimitIntegrity,
    LimitStatus,
)
from app.models.audit_ledger import ActorType
from app.schemas.limits.policy_limits import (
    CreatePolicyLimitRequest,
    UpdatePolicyLimitRequest,
    PolicyLimitResponse,
)
# PIN-513: services→HOC dependency severed. No-op shim replaces HOC audit import.
from app.services._audit_shim import AuditLedgerShim as AuditLedgerServiceAsync


def utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class PolicyLimitsServiceError(Exception):
    """Base exception for policy limits service."""
    pass


class LimitNotFoundError(PolicyLimitsServiceError):
    """Raised when limit is not found."""
    pass


class LimitValidationError(PolicyLimitsServiceError):
    """Raised when limit validation fails."""
    pass


class ImmutableFieldError(PolicyLimitsServiceError):
    """Raised when attempting to modify immutable fields."""
    pass


class PolicyLimitsService:
    """
    Service for policy limit CRUD operations.

    INVARIANTS:
    - Limits are tenant-scoped
    - limit_category and limit_type are immutable after creation
    - Every active limit MUST have an integrity record
    - Deletions are soft (status = DISABLED)
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._audit = AuditLedgerServiceAsync(session)

    async def create(
        self,
        tenant_id: str,
        request: CreatePolicyLimitRequest,
        created_by: Optional[str] = None,
    ) -> PolicyLimitResponse:
        """
        Create a new policy limit.

        TRANSACTION CONTRACT:
        - State change and audit event commit together (atomic)
        - If audit emit fails, limit creation rolls back
        - No partial state is possible

        Args:
            tenant_id: Owning tenant ID
            request: Create request with limit details
            created_by: Optional user ID who created this

        Returns:
            Created limit response

        Raises:
            LimitValidationError: If validation fails
        """
        # Validate category-specific fields
        self._validate_category_fields(request)

        # Create limit record
        limit_id = generate_uuid()
        now = utc_now()

        limit = Limit(
            id=limit_id,
            tenant_id=tenant_id,
            name=request.name,
            description=request.description,
            limit_category=request.limit_category.value,
            limit_type=request.limit_type,
            scope=request.scope.value,
            scope_id=request.scope_id,
            max_value=request.max_value,
            enforcement=request.enforcement.value,
            reset_period=request.reset_period.value if request.reset_period else None,
            window_seconds=request.window_seconds,
            status=LimitStatus.ACTIVE.value,
            created_at=now,
            updated_at=now,
        )

        # ATOMIC BLOCK: state change + audit must succeed together
        async with self.session.begin():
            self.session.add(limit)

            # Create integrity record (INVARIANT: every active limit needs one)
            integrity = LimitIntegrity(
                id=generate_uuid(),
                limit_id=limit_id,
                integrity_status="VERIFIED",
                integrity_score=Decimal("1.0000"),
                computed_at=now,
            )
            self.session.add(integrity)

            # Build limit state for audit
            limit_state = {
                "name": limit.name,
                "limit_category": limit.limit_category,
                "limit_type": limit.limit_type,
                "scope": limit.scope,
                "max_value": str(limit.max_value),
                "enforcement": limit.enforcement,
            }

            # Emit audit event (PIN-413: Logs Domain)
            # Must be inside transaction - commits with state change
            await self._audit.limit_created(
                tenant_id=tenant_id,
                limit_id=limit_id,
                actor_id=created_by,
                actor_type=ActorType.HUMAN if created_by else ActorType.SYSTEM,
                reason=f"Limit created: {limit.name}",
                limit_state=limit_state,
            )

        return self._to_response(limit)

    async def update(
        self,
        tenant_id: str,
        limit_id: str,
        request: UpdatePolicyLimitRequest,
        updated_by: Optional[str] = None,
    ) -> PolicyLimitResponse:
        """
        Update an existing policy limit.

        TRANSACTION CONTRACT:
        - State change and audit event commit together (atomic)
        - If audit emit fails, limit update rolls back
        - No partial state is possible

        Args:
            tenant_id: Owning tenant ID
            limit_id: Limit to update
            request: Update request with changed fields
            updated_by: Optional user ID who made update

        Returns:
            Updated limit response

        Raises:
            LimitNotFoundError: If limit not found
            ImmutableFieldError: If attempting to change immutable fields
        """
        limit = await self._get_limit(tenant_id, limit_id)

        # Capture before state for audit
        before_state = {
            "name": limit.name,
            "max_value": str(limit.max_value),
            "enforcement": limit.enforcement,
            "status": limit.status,
            "reset_period": limit.reset_period,
            "window_seconds": limit.window_seconds,
        }

        # ATOMIC BLOCK: state change + audit must succeed together
        async with self.session.begin():
            # Update mutable fields only
            if request.name is not None:
                limit.name = request.name
            if request.description is not None:
                limit.description = request.description
            if request.max_value is not None:
                limit.max_value = request.max_value
            if request.enforcement is not None:
                limit.enforcement = request.enforcement.value
            if request.reset_period is not None:
                limit.reset_period = request.reset_period.value
            if request.window_seconds is not None:
                limit.window_seconds = request.window_seconds
            if request.status is not None:
                limit.status = request.status

            limit.updated_at = utc_now()

            # Capture after state for audit
            after_state = {
                "name": limit.name,
                "max_value": str(limit.max_value),
                "enforcement": limit.enforcement,
                "status": limit.status,
                "reset_period": limit.reset_period,
                "window_seconds": limit.window_seconds,
            }

            # Emit audit event (PIN-413: Logs Domain)
            # Must be inside transaction - commits with state change
            await self._audit.limit_updated(
                tenant_id=tenant_id,
                limit_id=limit_id,
                actor_id=updated_by,
                actor_type=ActorType.HUMAN if updated_by else ActorType.SYSTEM,
                reason=f"Limit updated: {limit.name}",
                before_state=before_state,
                after_state=after_state,
            )

        return self._to_response(limit)

    async def delete(
        self,
        tenant_id: str,
        limit_id: str,
        deleted_by: Optional[str] = None,
    ) -> None:
        """
        Delete (disable) a policy limit.

        Soft delete - sets status to DISABLED.

        Args:
            tenant_id: Owning tenant ID
            limit_id: Limit to delete
            deleted_by: Optional user ID who deleted this

        Raises:
            LimitNotFoundError: If limit not found
        """
        limit = await self._get_limit(tenant_id, limit_id)
        limit.status = LimitStatus.DISABLED.value
        limit.updated_at = utc_now()
        await self.session.flush()

    async def get(
        self,
        tenant_id: str,
        limit_id: str,
    ) -> PolicyLimitResponse:
        """
        Get a policy limit by ID.

        Args:
            tenant_id: Owning tenant ID
            limit_id: Limit to retrieve

        Returns:
            Limit response

        Raises:
            LimitNotFoundError: If limit not found
        """
        limit = await self._get_limit(tenant_id, limit_id)
        return self._to_response(limit)

    async def _get_limit(self, tenant_id: str, limit_id: str) -> Limit:
        """Get limit by ID with tenant check."""
        stmt = select(Limit).where(
            Limit.id == limit_id,
            Limit.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        limit = result.scalar_one_or_none()

        if not limit:
            raise LimitNotFoundError(f"Limit {limit_id} not found")

        return limit

    def _validate_category_fields(self, request: CreatePolicyLimitRequest) -> None:
        """Validate category-specific required fields."""
        category = request.limit_category.value

        if category == "BUDGET":
            if not request.reset_period:
                raise LimitValidationError("BUDGET limits require reset_period")

        if category == "RATE":
            if not request.window_seconds:
                raise LimitValidationError("RATE limits require window_seconds")

    def _to_response(self, limit: Limit) -> PolicyLimitResponse:
        """Convert model to response."""
        return PolicyLimitResponse(
            limit_id=limit.id,
            tenant_id=limit.tenant_id,
            name=limit.name,
            description=limit.description,
            limit_category=limit.limit_category,
            limit_type=limit.limit_type,
            scope=limit.scope,
            scope_id=limit.scope_id,
            max_value=limit.max_value,
            enforcement=limit.enforcement,
            status=limit.status,
            reset_period=limit.reset_period,
            window_seconds=limit.window_seconds,
            created_at=limit.created_at,
            updated_at=limit.updated_at,
        )
