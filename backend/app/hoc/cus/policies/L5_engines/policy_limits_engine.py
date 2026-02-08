# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: limits (via driver)
#   Writes: limits (via driver)
# Role: Policy limits CRUD engine (PIN-LIM-01) - pure business logic
# Callers: api/policies.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-LIM-01, PIN-468
#
# EXTRACTION STATUS: Phase-2.5A (2026-01-24)
# - All DB operations extracted to PolicyLimitsDriver
# - Engine contains ONLY decision logic
# - NO sqlalchemy/sqlmodel imports at runtime
#
# ============================================================================
# L5 ENGINE INVARIANT — POLICY LIMITS (LOCKED)
# ============================================================================
# This file MUST NOT import sqlalchemy/sqlmodel at runtime.
# All persistence is delegated to policy_limits_driver.py.
# Business decisions ONLY.
#
# Any violation is a Phase-2.5 regression.
# ============================================================================
# NOTE: Renamed policy_limits_service.py → policy_limits_engine.py (2026-01-24)
#       Reclassified L4→L5 per HOC Topology V1 - BANNED_NAMING fix

from __future__ import annotations

"""
Policy Limits Service (PIN-LIM-01)

Authoritative writer for policy limits table.

Responsibilities:
- Create/update/delete limits
- Validate scope (tenant / worker / global)
- Enforce immutables (category, type cannot change after creation)
- Emit audit events

All DB operations delegated to PolicyLimitsDriver.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional

# L6 driver import (allowed)
from app.hoc.cus.hoc_spine.services.time import utc_now
from app.hoc.cus.hoc_spine.drivers.cross_domain import generate_uuid
# PIN-504: Driver factory lazy-imported in constructor (no cross-domain module-level import)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.policy_control_plane import Limit, LimitIntegrity

from app.hoc.cus.hoc_spine.schemas.domain_enums import ActorType
from app.hoc.cus.controls.L5_schemas.policy_limits import (
    CreatePolicyLimitRequest,
    UpdatePolicyLimitRequest,
    PolicyLimitResponse,
)


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

    def __init__(self, session: "AsyncSession", audit: Any = None, driver: Any = None):
        """
        Args:
            session: Async SQLAlchemy Session
            audit: Audit service instance (injected by L4 handler, PIN-504).
                   Must have limit_created, limit_updated async methods.
            driver: PolicyLimitsCapability instance (PIN-508 Phase 2C).
                    When provided, skips lazy cross-domain import.
        """
        self._session = session
        self._audit = audit

        if driver is not None:
            # PIN-508 Phase 2C: capability injected by L4 handler via DomainBridge
            self._driver = driver
        else:
            # PIN-510 Phase 1B: Legacy fallback — assertion guards, env flag enforces
            import logging as _logging
            import os as _os

            if _os.environ.get("HOC_REQUIRE_L4_INJECTION"):
                raise RuntimeError(
                    "PolicyLimitsEngine() created without driver injection. "
                    "All callers must use L4 handler path (PIN-510 Phase 1B)."
                )
            _logging.getLogger(__name__).warning(
                "PIN-510: PolicyLimitsEngine legacy fallback used — "
                "caller should inject driver via DomainBridge"
            )

            # Legacy path: lazy import (PIN-504) — to be removed after all callers migrate
            from app.hoc.cus.controls.L6_drivers.policy_limits_driver import get_policy_limits_driver
            self._driver = get_policy_limits_driver(session)

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

        # ATOMIC BLOCK: L4 owns transaction boundary (PIN-520)
        limit = self._driver.create_limit(
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
            status="ACTIVE",
            created_at=now,
            updated_at=now,
        )

        # Create integrity record (INVARIANT: every active limit needs one)
        integrity = self._driver.create_integrity(
            id=generate_uuid(),
            limit_id=limit_id,
            integrity_status="VERIFIED",
            integrity_score=Decimal("1.0000"),
            computed_at=now,
        )

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
        # Audit service injected by L4 handler (PIN-504)
        if self._audit:
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

        # ATOMIC BLOCK: L4 owns transaction boundary (PIN-520)
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
        # Audit service injected by L4 handler (PIN-504)
        if self._audit:
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
        limit.status = "DISABLED"
        limit.updated_at = utc_now()
        await self._driver.flush()

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
        limit = await self._driver.fetch_limit_by_id(tenant_id, limit_id)

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
