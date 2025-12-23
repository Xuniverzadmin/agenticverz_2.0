# M25 Pillar Integration Module
# Implements the feedback loop: Incident → Pattern → Recovery → Policy → Routing
#
# Status: M25-ALPHA (loop-enabled, not loop-proven)
# See learning_proof.py for graduation gates

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Singleton dispatcher instance
_dispatcher: Optional["IntegrationDispatcher"] = None

from .events import (
    LoopStage,
    LoopFailureState,
    ConfidenceBand,
    PolicyMode,
    HumanCheckpointType,
    LoopEvent,
    PatternMatchResult,
    RecoverySuggestion,
    PolicyRule,
    RoutingAdjustment,
    LoopStatus,
    HumanCheckpoint,
)
from .dispatcher import IntegrationDispatcher
from .bridges import (
    IncidentToCatalogBridge,
    PatternToRecoveryBridge,
    RecoveryToPolicyBridge,
    PolicyToRoutingBridge,
    LoopStatusBridge,
)
from .learning_proof import (
    # Gate 1: Prevention Proof
    PreventionOutcome,
    PreventionRecord,
    PreventionTracker,
    # Gate 2: Regret Rollback
    RegretType,
    RegretEvent,
    PolicyRegretTracker,
    GlobalRegretTracker,
    # Adaptive Confidence
    PatternCalibration,
    AdaptiveConfidenceSystem,
    # Checkpoint Prioritization
    CheckpointPriority,
    CheckpointConfig,
    PrioritizedCheckpoint,
    # Graduation
    M25GraduationStatus,
    PreventionTimeline,
)

__all__ = [
    # Events
    "LoopStage",
    "LoopFailureState",
    "ConfidenceBand",
    "PolicyMode",
    "HumanCheckpointType",
    "LoopEvent",
    "PatternMatchResult",
    "RecoverySuggestion",
    "PolicyRule",
    "RoutingAdjustment",
    "LoopStatus",
    "HumanCheckpoint",
    # Dispatcher
    "IntegrationDispatcher",
    # Bridges
    "IncidentToCatalogBridge",
    "PatternToRecoveryBridge",
    "RecoveryToPolicyBridge",
    "PolicyToRoutingBridge",
    "LoopStatusBridge",
    # Learning Proof (M25 Graduation)
    "PreventionOutcome",
    "PreventionRecord",
    "PreventionTracker",
    "RegretType",
    "RegretEvent",
    "PolicyRegretTracker",
    "GlobalRegretTracker",
    "PatternCalibration",
    "AdaptiveConfidenceSystem",
    "CheckpointPriority",
    "CheckpointConfig",
    "PrioritizedCheckpoint",
    "M25GraduationStatus",
    "PreventionTimeline",
    # Dispatcher factory
    "get_dispatcher",
    "trigger_integration_loop",
]


def get_dispatcher() -> IntegrationDispatcher:
    """
    Get the singleton M25 integration dispatcher.

    Creates and configures the dispatcher on first call:
    - Connects to Redis for pub/sub
    - Configures database session factory
    - Registers all 5 bridges

    Returns:
        IntegrationDispatcher: Configured dispatcher instance
    """
    global _dispatcher

    if _dispatcher is not None:
        return _dispatcher

    import os
    import redis.asyncio as redis
    from app.db import get_async_session

    # Initialize Redis client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url)

    # Create dispatcher with async session factory
    _dispatcher = IntegrationDispatcher(
        redis_client=redis_client,
        db_session_factory=get_async_session,
    )

    # Register all bridges
    bridges = [
        IncidentToCatalogBridge(_dispatcher.db_factory),
        PatternToRecoveryBridge(_dispatcher.db_factory),
        RecoveryToPolicyBridge(_dispatcher.db_factory),
        PolicyToRoutingBridge(_dispatcher.db_factory),
        LoopStatusBridge(_dispatcher.db_factory, redis_client),
    ]

    for bridge in bridges:
        bridge.register(_dispatcher)

    logger.info("M25 IntegrationDispatcher initialized with 5 bridges")

    return _dispatcher


async def trigger_integration_loop(
    incident_id: str,
    tenant_id: str,
    incident_data: dict,
) -> "LoopEvent":
    """
    Trigger the M25 integration loop for a newly created incident.

    This is the entry point to start processing an incident through:
    1. Pattern matching (Bridge 1)
    2. Recovery suggestion (Bridge 2)
    3. Policy generation (Bridge 3)
    4. Routing adjustment (Bridge 4)
    5. Console update (Bridge 5)

    Args:
        incident_id: The incident ID
        tenant_id: The tenant ID
        incident_data: Incident details for pattern matching

    Returns:
        LoopEvent: The final event after processing through all stages
    """
    dispatcher = get_dispatcher()

    # Create the initial loop event
    initial_event = LoopEvent.create(
        incident_id=incident_id,
        tenant_id=tenant_id,
        stage=LoopStage.INCIDENT_CREATED,
        details={
            "incident": incident_data,
            "trigger_source": "api",
        },
    )

    logger.info(f"Triggering M25 integration loop for incident {incident_id}")

    # Dispatch through the loop
    result = await dispatcher.dispatch(initial_event)

    logger.info(
        f"M25 loop completed for incident {incident_id}: "
        f"stage={result.stage.value}, success={result.is_success}"
    )

    return result
