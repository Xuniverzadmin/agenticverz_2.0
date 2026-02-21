# capability_id: CAP-012
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L4 handler)
#   Execution: sync
# Role: Onboarding business logic — monotonic state transitions
# Callers: onboarding_handler.py (L4)
# Allowed Imports: L5_schemas (same domain)
# Forbidden Imports: sqlalchemy, sqlmodel, app.db, app.models
# Reference: PIN-399 (Onboarding State Machine v1)
# artifact_class: CODE

"""
Onboarding Engine (L5)

Business logic for onboarding state transitions.
Monotonic, idempotent state machine.

INVARIANTS:
- ONBOARD-TRANS-001: Transitions are idempotent (repeated calls are no-ops)
- ONBOARD-TRANS-002: Transitions are monotonic (forward-only, never regress)

NO COMMIT — L4 coordinator owns transaction boundary.
No sqlalchemy/sqlmodel imports (L5 purity).
"""

from __future__ import annotations

import logging
from typing import Optional

from app.hoc.cus.account.L5_schemas.onboarding_state import (
    ONBOARDING_STATUS_NAMES,
    is_complete,
)
from app.hoc.cus.account.L5_schemas.onboarding_dtos import (
    OnboardingStateSnapshot,
    OnboardingTransitionResult,
)

logger = logging.getLogger("nova.hoc.account.onboarding_engine")


class OnboardingEngine:
    """
    L5 Engine for onboarding state transitions.

    Driver is injected (duck-typed: needs fetch_onboarding_state, write_onboarding_state).
    """

    def __init__(self, driver):
        self._driver = driver

    def get_state(self, tenant_id: str) -> Optional[OnboardingStateSnapshot]:
        """
        Get current onboarding state snapshot.

        Returns None if tenant not found.
        """
        state = self._driver.fetch_onboarding_state(tenant_id)
        if state is None:
            return None

        return OnboardingStateSnapshot(
            tenant_id=tenant_id,
            state_value=state,
            state_name=ONBOARDING_STATUS_NAMES.get(state, f"UNKNOWN_{state}"),
            is_complete=is_complete(state),
        )

    def advance(
        self,
        tenant_id: str,
        target_state: int,
        trigger: str,
    ) -> OnboardingTransitionResult:
        """
        Advance onboarding state to target.

        ONBOARD-TRANS-001: Idempotent — if current >= target, return success + was_no_op.
        ONBOARD-TRANS-002: Monotonic — only advances forward.

        NO COMMIT — L4 coordinator owns transaction boundary.
        """
        current = self._driver.fetch_onboarding_state(tenant_id)

        if current is None:
            return OnboardingTransitionResult(
                success=False,
                tenant_id=tenant_id,
                from_state="UNKNOWN",
                to_state=ONBOARDING_STATUS_NAMES.get(target_state, f"UNKNOWN_{target_state}"),
                trigger=trigger,
                message="Tenant not found",
            )

        current_name = ONBOARDING_STATUS_NAMES.get(current, f"UNKNOWN_{current}")
        target_name = ONBOARDING_STATUS_NAMES.get(target_state, f"UNKNOWN_{target_state}")

        # ONBOARD-TRANS-001: Idempotent — already at or past target
        if current >= target_state:
            return OnboardingTransitionResult(
                success=True,
                tenant_id=tenant_id,
                from_state=current_name,
                to_state=current_name,
                trigger=trigger,
                message=f"Already at {current_name}",
                was_no_op=True,
            )

        # ONBOARD-TRANS-002: Monotonic — advance forward
        self._driver.write_onboarding_state(tenant_id, target_state)

        logger.info(
            "onboarding_state_transition",
            extra={
                "tenant_id": tenant_id,
                "from_state": current_name,
                "to_state": target_name,
                "trigger": trigger,
            },
        )

        return OnboardingTransitionResult(
            success=True,
            tenant_id=tenant_id,
            from_state=current_name,
            to_state=target_name,
            trigger=trigger,
            message=f"Advanced from {current_name} to {target_name}",
        )


def get_onboarding_engine(driver) -> OnboardingEngine:
    """Get an OnboardingEngine instance."""
    return OnboardingEngine(driver)


__all__ = [
    "OnboardingEngine",
    "get_onboarding_engine",
]
