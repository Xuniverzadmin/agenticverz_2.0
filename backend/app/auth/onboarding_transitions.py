# TOMBSTONE_EXPIRY: 2026-03-15
# DEPRECATED: Production callers use account L5/L6 via onboarding_handler.py
# Retained for: detect_stalled_onboarding (ops), test compatibility
# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api, worker
#   Execution: async
# Role: Central service for onboarding state transitions (DEPRECATED — see onboarding_handler.py)
# Callers: detect_stalled_onboarding (ops only), legacy tests
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: PIN-399 (Onboarding State Machine v1)

"""
Onboarding Transition Service

PIN-399: Central point of mutation for tenant onboarding state.

DESIGN INVARIANTS:
- ONBOARD-TRANS-001: Transitions are idempotent (repeated calls are no-ops)
- ONBOARD-TRANS-002: Transitions are monotonic (forward-only, never regress)
- ONBOARD-TRANS-003: All transitions are audited
- ONBOARD-TRANS-004: Single service owns all mutations

TRANSITION TRIGGERS:
- CREATED → IDENTITY_VERIFIED: First authenticated human request
- IDENTITY_VERIFIED → API_KEY_CREATED: First successful API key creation
- API_KEY_CREATED → SDK_CONNECTED: First successful SDK handshake
- SDK_CONNECTED → COMPLETE: Manual or automatic completion

USAGE:
    from app.auth.onboarding_transitions import get_onboarding_service

    service = get_onboarding_service()
    result = await service.advance_to_identity_verified(tenant_id, trigger="first_human_auth")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from .onboarding_state import OnboardingState

logger = logging.getLogger("nova.auth.onboarding_transitions")


class TransitionTrigger(str, Enum):
    """Known triggers for state transitions."""

    FIRST_HUMAN_AUTH = "first_human_auth"
    FIRST_API_KEY_CREATED = "first_api_key_created"
    FIRST_SDK_HANDSHAKE = "first_sdk_handshake"
    MANUAL_COMPLETION = "manual_completion"
    ADMIN_OVERRIDE = "admin_override"


@dataclass
class TransitionResult:
    """Result of a state transition attempt."""

    success: bool
    tenant_id: str
    from_state: OnboardingState
    to_state: OnboardingState
    trigger: str
    message: str
    was_no_op: bool = False  # True if already at or past target state


class OnboardingTransitionService:
    """
    Central service for managing onboarding state transitions.

    INVARIANTS:
    - All transitions go through this service
    - Transitions are idempotent (safe to call multiple times)
    - Transitions are monotonic (can only advance, never regress)
    - All transitions are logged for audit
    """

    async def advance_to_identity_verified(
        self,
        tenant_id: str,
        trigger: str = TransitionTrigger.FIRST_HUMAN_AUTH,
    ) -> TransitionResult:
        """
        Advance tenant to IDENTITY_VERIFIED state.

        Called when: First authenticated human request is received.

        Idempotent: If already at or past IDENTITY_VERIFIED, this is a no-op.
        """
        return await self._advance_to_state(
            tenant_id=tenant_id,
            target_state=OnboardingState.IDENTITY_VERIFIED,
            trigger=trigger,
        )

    async def advance_to_api_key_created(
        self,
        tenant_id: str,
        trigger: str = TransitionTrigger.FIRST_API_KEY_CREATED,
    ) -> TransitionResult:
        """
        Advance tenant to API_KEY_CREATED state.

        Called when: First API key is successfully created.

        Idempotent: If already at or past API_KEY_CREATED, this is a no-op.
        """
        return await self._advance_to_state(
            tenant_id=tenant_id,
            target_state=OnboardingState.API_KEY_CREATED,
            trigger=trigger,
        )

    async def advance_to_sdk_connected(
        self,
        tenant_id: str,
        trigger: str = TransitionTrigger.FIRST_SDK_HANDSHAKE,
    ) -> TransitionResult:
        """
        Advance tenant to SDK_CONNECTED state.

        Called when: First successful SDK handshake is completed.

        Idempotent: If already at or past SDK_CONNECTED, this is a no-op.
        """
        return await self._advance_to_state(
            tenant_id=tenant_id,
            target_state=OnboardingState.SDK_CONNECTED,
            trigger=trigger,
        )

    async def advance_to_complete(
        self,
        tenant_id: str,
        trigger: str = TransitionTrigger.MANUAL_COMPLETION,
    ) -> TransitionResult:
        """
        Advance tenant to COMPLETE state.

        Called when: Onboarding is manually or automatically marked complete.

        Idempotent: If already COMPLETE, this is a no-op.
        """
        return await self._advance_to_state(
            tenant_id=tenant_id,
            target_state=OnboardingState.COMPLETE,
            trigger=trigger,
        )

    async def _advance_to_state(
        self,
        tenant_id: str,
        target_state: OnboardingState,
        trigger: str,
    ) -> TransitionResult:
        """
        Core transition logic.

        INVARIANTS:
        - Monotonic: Only advances forward, never regresses
        - Idempotent: If already at or past target, returns success with was_no_op=True
        - Audited: Every transition (including no-ops) is logged
        """
        from ..db import get_session
        from ..models.tenant import Tenant

        try:
            session = next(get_session())
            try:
                tenant = session.get(Tenant, tenant_id)

                if tenant is None:
                    logger.warning(
                        "onboarding_transition_failed",
                        extra={
                            "tenant_id": tenant_id,
                            "target_state": target_state.name,
                            "trigger": trigger,
                            "reason": "tenant_not_found",
                        },
                    )
                    return TransitionResult(
                        success=False,
                        tenant_id=tenant_id,
                        from_state=OnboardingState.CREATED,
                        to_state=target_state,
                        trigger=trigger,
                        message="Tenant not found",
                    )

                current_state = OnboardingState(tenant.onboarding_state)

                # INVARIANT: Monotonic - already at or past target is a no-op
                if current_state >= target_state:
                    logger.debug(
                        "onboarding_transition_no_op",
                        extra={
                            "tenant_id": tenant_id,
                            "current_state": current_state.name,
                            "target_state": target_state.name,
                            "trigger": trigger,
                        },
                    )
                    return TransitionResult(
                        success=True,
                        tenant_id=tenant_id,
                        from_state=current_state,
                        to_state=current_state,
                        trigger=trigger,
                        message=f"Already at {current_state.name}",
                        was_no_op=True,
                    )

                # Perform the transition
                tenant.onboarding_state = target_state.value
                session.add(tenant)
                session.commit()

                # INVARIANT: Audit every transition
                self._log_transition(
                    tenant_id=tenant_id,
                    from_state=current_state,
                    to_state=target_state,
                    trigger=trigger,
                )

                return TransitionResult(
                    success=True,
                    tenant_id=tenant_id,
                    from_state=current_state,
                    to_state=target_state,
                    trigger=trigger,
                    message=f"Advanced from {current_state.name} to {target_state.name}",
                )

            finally:
                session.close()

        except Exception as e:
            logger.error(
                "onboarding_transition_error",
                extra={
                    "tenant_id": tenant_id,
                    "target_state": target_state.name,
                    "trigger": trigger,
                    "error": str(e),
                },
                exc_info=True,
            )
            return TransitionResult(
                success=False,
                tenant_id=tenant_id,
                from_state=OnboardingState.CREATED,
                to_state=target_state,
                trigger=trigger,
                message=f"Transition failed: {e}",
            )

    def _log_transition(
        self,
        tenant_id: str,
        from_state: OnboardingState,
        to_state: OnboardingState,
        trigger: str,
    ) -> None:
        """
        Log a state transition for audit.

        AUDIT FORMAT:
        - tenant_id: Which tenant
        - from_state: Previous state
        - to_state: New state
        - trigger: What caused the transition
        - timestamp: When it happened
        """
        logger.info(
            "onboarding_state_transition",
            extra={
                "tenant_id": tenant_id,
                "from_state": from_state.name,
                "to_state": to_state.name,
                "trigger": trigger,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def get_current_state(self, tenant_id: str) -> Optional[OnboardingState]:
        """
        Get the current onboarding state for a tenant.

        Returns None if tenant not found.
        """
        from ..db import get_session
        from ..models.tenant import Tenant

        try:
            session = next(get_session())
            try:
                tenant = session.get(Tenant, tenant_id)
                if tenant is None:
                    return None
                return OnboardingState(tenant.onboarding_state)
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get tenant onboarding state: {e}")
            return None


# =============================================================================
# STALLED ONBOARDING DETECTION
# =============================================================================

# Default threshold: 24 hours in a non-COMPLETE state
STALLED_THRESHOLD_HOURS = 24


@dataclass
class StalledTenant:
    """A tenant with stalled onboarding."""

    tenant_id: str
    current_state: OnboardingState
    created_at: datetime
    hours_in_state: float


async def detect_stalled_onboarding(
    threshold_hours: int = STALLED_THRESHOLD_HOURS,
) -> list[StalledTenant]:
    """
    Detect tenants with stalled onboarding.

    Returns list of tenants that have been in a non-COMPLETE state
    for longer than the threshold.

    This is an ops-only signal - not user-facing.
    """
    from sqlmodel import Session, select

    from ..db import engine
    from ..models.tenant import Tenant

    stalled = []
    threshold_time = datetime.now(timezone.utc) - timedelta(hours=threshold_hours)

    try:
        with Session(engine) as session:
            # Find tenants not COMPLETE and created before threshold
            statement = select(Tenant).where(
                Tenant.onboarding_state < OnboardingState.COMPLETE.value,
            )
            tenants = session.exec(statement).all()

            for tenant in tenants:
                # Check if created_at is before threshold
                created_at = tenant.created_at
                if created_at and created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

                if created_at and created_at < threshold_time:
                    hours_stalled = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
                    stalled.append(
                        StalledTenant(
                            tenant_id=tenant.id,
                            current_state=OnboardingState(tenant.onboarding_state),
                            created_at=created_at,
                            hours_in_state=hours_stalled,
                        )
                    )

    except Exception as e:
        logger.error(f"Failed to detect stalled onboarding: {e}")

    return stalled


async def emit_stalled_onboarding_signals(
    threshold_hours: int = STALLED_THRESHOLD_HOURS,
) -> int:
    """
    Detect and emit ops signals for stalled onboarding.

    Returns count of stalled tenants detected.

    This function is meant to be called periodically by a background task.
    """
    stalled = await detect_stalled_onboarding(threshold_hours)

    for tenant in stalled:
        logger.warning(
            "onboarding_stalled",
            extra={
                "tenant_id": tenant.tenant_id,
                "current_state": tenant.current_state.name,
                "hours_stalled": round(tenant.hours_in_state, 1),
                "created_at": tenant.created_at.isoformat(),
                "threshold_hours": threshold_hours,
            },
        )

    if stalled:
        logger.info(
            "onboarding_stalled_summary",
            extra={
                "stalled_count": len(stalled),
                "threshold_hours": threshold_hours,
                "states": {
                    state.name: sum(1 for t in stalled if t.current_state == state)
                    for state in OnboardingState
                    if state != OnboardingState.COMPLETE
                },
            },
        )

    return len(stalled)


# Singleton instance
_service: Optional[OnboardingTransitionService] = None


def get_onboarding_service() -> OnboardingTransitionService:
    """Get the singleton OnboardingTransitionService."""
    global _service
    if _service is None:
        _service = OnboardingTransitionService()
    return _service
