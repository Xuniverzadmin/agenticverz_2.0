"""
M25 Integration Dispatcher

Orchestrates the feedback loop with:
- Event-driven architecture (Redis pub/sub + PostgreSQL durability)
- Failure state handling
- Human checkpoint integration
- Guardrail enforcement

FROZEN: 2025-12-23
Do NOT modify loop mechanics without explicit approval.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Optional
from uuid import uuid4

from .events import (
    LOOP_MECHANICS_FROZEN_AT,
    LOOP_MECHANICS_VERSION,
    ConfidenceBand,
    HumanCheckpoint,
    HumanCheckpointType,
    LoopEvent,
    LoopFailureState,
    LoopStage,
    LoopStatus,
    ensure_json_serializable,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DISPATCHER CONFIGURATION
# =============================================================================


@dataclass
class DispatcherConfig:
    """Configuration for the integration dispatcher."""

    # Feature flags
    enabled: bool = True
    bridge_1_enabled: bool = True  # Incident → Catalog
    bridge_2_enabled: bool = True  # Pattern → Recovery
    bridge_3_enabled: bool = True  # Recovery → Policy
    bridge_4_enabled: bool = True  # Policy → Routing
    bridge_5_enabled: bool = True  # Loop → Console

    # Timeouts
    stage_timeout_seconds: float = 30.0
    loop_timeout_seconds: float = 300.0  # 5 minutes max

    # Guardrails
    max_routing_delta: float = 0.2
    routing_decay_days: int = 7
    policy_confirmations_required: int = 3
    auto_apply_confidence_threshold: float = 0.85

    # Human checkpoints
    require_human_for_weak_match: bool = True
    require_human_for_novel: bool = True

    @classmethod
    def from_env(cls) -> "DispatcherConfig":
        """Load config from environment variables."""
        import os

        return cls(
            enabled=os.getenv("INTEGRATION_LOOP_ENABLED", "true").lower() == "true",
            bridge_1_enabled=os.getenv("BRIDGE_1_ENABLED", "true").lower() == "true",
            bridge_2_enabled=os.getenv("BRIDGE_2_ENABLED", "true").lower() == "true",
            bridge_3_enabled=os.getenv("BRIDGE_3_ENABLED", "true").lower() == "true",
            bridge_4_enabled=os.getenv("BRIDGE_4_ENABLED", "true").lower() == "true",
            bridge_5_enabled=os.getenv("BRIDGE_5_ENABLED", "true").lower() == "true",
            policy_confirmations_required=int(os.getenv("POLICY_CONFIRMATIONS", "3")),
            max_routing_delta=float(os.getenv("MAX_ROUTING_DELTA", "0.2")),
        )


# =============================================================================
# HANDLER TYPE
# =============================================================================

Handler = Callable[[LoopEvent], Coroutine[Any, Any, Optional[LoopEvent]]]


# =============================================================================
# INTEGRATION DISPATCHER
# =============================================================================


class IntegrationDispatcher:
    """
    Central dispatcher for the M25 integration loop.

    Responsibilities:
    - Route events to appropriate bridge handlers
    - Persist events for durability
    - Publish events for real-time updates
    - Handle failures gracefully
    - Enforce guardrails
    - Create human checkpoints when needed
    """

    def __init__(
        self,
        redis_client: Any,  # Redis async client
        db_session_factory: Callable,  # SQLAlchemy session factory
        config: DispatcherConfig | None = None,
    ):
        self.redis = redis_client
        self.db_factory = db_session_factory
        self.config = config or DispatcherConfig.from_env()

        # Handler registry - will be populated by bridges
        self._handlers: dict[LoopStage, list[Handler]] = {stage: [] for stage in LoopStage}

        # Active loop statuses (in-memory cache, backed by DB)
        self._active_loops: dict[str, LoopStatus] = {}

        # Pending human checkpoints
        self._pending_checkpoints: dict[str, HumanCheckpoint] = {}

        # HYGIENE #4: Idempotency tracking
        self._processed_events: set[str] = set()

        logger.info(
            f"IntegrationDispatcher initialized (v{LOOP_MECHANICS_VERSION}, frozen {LOOP_MECHANICS_FROZEN_AT}), "
            f"enabled={self.config.enabled}"
        )

    def register_handler(self, stage: LoopStage, handler: Handler) -> None:
        """Register a handler for a specific loop stage."""
        self._handlers[stage].append(handler)
        logger.debug(f"Registered handler for {stage.value}: {handler.__name__}")

    def is_bridge_enabled(self, stage: LoopStage) -> bool:
        """Check if a bridge is enabled by its stage."""
        stage_to_bridge = {
            LoopStage.INCIDENT_CREATED: self.config.bridge_1_enabled,
            LoopStage.PATTERN_MATCHED: self.config.bridge_2_enabled,
            LoopStage.RECOVERY_SUGGESTED: self.config.bridge_3_enabled,
            LoopStage.POLICY_GENERATED: self.config.bridge_4_enabled,
            LoopStage.ROUTING_ADJUSTED: self.config.bridge_5_enabled,
        }
        return stage_to_bridge.get(stage, True)

    # =========================================================================
    # MAIN DISPATCH FLOW
    # =========================================================================

    async def dispatch(self, event: LoopEvent) -> LoopEvent:
        """
        Dispatch an event through the integration loop.

        Flow:
        1. Validate event and check if dispatcher is enabled
        2. HYGIENE #4: Check idempotency (skip if already processed)
        3. Get or create loop status
        4. Persist event to database (durability first)
        5. Check for required human checkpoints
        6. If checkpoint needed, block and wait
        7. Execute handlers
        8. Publish to Redis (real-time updates)
        9. Update loop status
        10. Trigger next stage if successful
        """
        if not self.config.enabled:
            logger.debug("Integration loop disabled, skipping dispatch")
            return event

        if not self.is_bridge_enabled(event.stage):
            logger.debug(f"Bridge for {event.stage.value} disabled, skipping")
            return event

        # HYGIENE #4: Idempotency check
        idempotency_key = f"{event.incident_id}:{event.stage.value}"
        if idempotency_key in self._processed_events:
            logger.warning(
                f"Idempotency blocked: {idempotency_key} already processed. Duplicate event {event.event_id} ignored."
            )
            # Return existing loop status if available
            existing_status = await self._load_loop_status(event.incident_id)
            if existing_status:
                event.details["idempotency_blocked"] = True
                event.details["existing_loop_id"] = existing_status.loop_id
            return event

        # Also check database for persistence-based idempotency
        if await self._check_db_idempotency(event.incident_id, event.stage):
            logger.warning(f"DB idempotency blocked: {idempotency_key} exists in database.")
            event.details["idempotency_blocked"] = True
            return event

        try:
            # Get or create loop status
            loop_status = await self._get_or_create_loop_status(event)

            # Persist event first (durability)
            await self._persist_event(event)

            # Check if human checkpoint is needed
            checkpoint = await self._check_human_checkpoint_needed(event)
            if checkpoint:
                self._pending_checkpoints[checkpoint.checkpoint_id] = checkpoint
                await self._persist_checkpoint(checkpoint)

                # Update event with blocked state
                event.failure_state = LoopFailureState.HUMAN_CHECKPOINT_PENDING
                loop_status.is_blocked = True
                loop_status.pending_checkpoints.append(checkpoint.checkpoint_id)

                # Publish checkpoint needed event
                await self._publish_checkpoint_needed(checkpoint)

                return event

            # Execute handlers
            result_event = await self._execute_handlers(event)

            # Publish to Redis
            await self._publish_event(result_event)

            # Update loop status
            await self._update_loop_status(loop_status, result_event)

            # Trigger next stage if successful
            if result_event.is_success:
                next_event = await self._trigger_next_stage(result_event, loop_status)
                if next_event:
                    return await self.dispatch(next_event)

            # HYGIENE #4: Mark as processed AFTER successful handler execution
            self._processed_events.add(idempotency_key)

            return result_event

        except asyncio.TimeoutError:
            logger.error(f"Timeout dispatching event {event.event_id}")
            event.failure_state = LoopFailureState.TIMEOUT
            await self._persist_event(event)
            return event

        except Exception as e:
            logger.exception(f"Error dispatching event {event.event_id}: {e}")
            event.failure_state = LoopFailureState.ERROR
            event.details["error"] = str(e)
            await self._persist_event(event)
            return event

    async def _check_db_idempotency(self, incident_id: str, stage: LoopStage) -> bool:
        """
        HYGIENE #4: Check if this incident+stage was already processed.

        Returns True if already processed (should skip).
        """
        try:
            async with self.db_factory() as session:
                from sqlalchemy import text

                result = await session.execute(
                    text(
                        """
                        SELECT 1 FROM loop_events
                        WHERE incident_id = :incident_id
                        AND stage = :stage
                        LIMIT 1
                    """
                    ),
                    {"incident_id": incident_id, "stage": stage.value},
                )
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"DB idempotency check failed: {e}")
            return False  # Fail open (allow processing)

    async def _execute_handlers(self, event: LoopEvent) -> LoopEvent:
        """Execute all handlers for an event stage."""
        handlers = self._handlers.get(event.stage, [])

        if not handlers:
            logger.warning(f"No handlers registered for {event.stage.value}")
            return event

        result_event = event
        for handler in handlers:
            try:
                handler_result = await asyncio.wait_for(
                    handler(result_event),
                    timeout=self.config.stage_timeout_seconds,
                )
                if handler_result:
                    result_event = handler_result
            except asyncio.TimeoutError:
                logger.error(f"Handler {handler.__name__} timed out")
                result_event.failure_state = LoopFailureState.TIMEOUT
                break
            except Exception as e:
                logger.exception(f"Handler {handler.__name__} failed: {e}")
                result_event.failure_state = LoopFailureState.ERROR
                result_event.details["handler_error"] = str(e)
                break

        return result_event

    # =========================================================================
    # HUMAN CHECKPOINT HANDLING
    # =========================================================================

    async def _check_human_checkpoint_needed(self, event: LoopEvent) -> Optional[HumanCheckpoint]:
        """
        Check if a human checkpoint is needed for this event.

        Checkpoints are created for:
        - Weak match confidence (if configured)
        - Novel patterns (if configured)
        - Policy activation
        - Routing adjustments above threshold
        """
        if not event.confidence_band:
            return None

        # Weak match checkpoint
        if event.confidence_band == ConfidenceBand.WEAK_MATCH and self.config.require_human_for_weak_match:
            return HumanCheckpoint.create(
                checkpoint_type=HumanCheckpointType.APPROVE_RECOVERY,
                incident_id=event.incident_id,
                tenant_id=event.tenant_id,
                stage=event.stage,
                target_id=event.details.get("pattern_id", event.event_id),
                description=(
                    f"Weak match confidence ({event.details.get('confidence', 0):.0%}). "
                    "Review pattern match before proceeding."
                ),
            )

        # Novel pattern checkpoint
        if event.confidence_band == ConfidenceBand.NOVEL and self.config.require_human_for_novel:
            return HumanCheckpoint.create(
                checkpoint_type=HumanCheckpointType.APPROVE_POLICY,
                incident_id=event.incident_id,
                tenant_id=event.tenant_id,
                stage=event.stage,
                target_id=event.details.get("pattern_id", event.event_id),
                description=("Novel pattern detected (low confidence). Review before creating new failure pattern."),
            )

        return None

    async def resolve_checkpoint(
        self,
        checkpoint_id: str,
        user_id: str,
        resolution: str,
    ) -> Optional[LoopEvent]:
        """
        Resolve a pending human checkpoint.

        Returns the event to resume if approved, None if rejected.
        """
        checkpoint = self._pending_checkpoints.get(checkpoint_id)
        if not checkpoint:
            # Try loading from DB
            checkpoint = await self._load_checkpoint(checkpoint_id)
            if not checkpoint:
                raise ValueError(f"Checkpoint {checkpoint_id} not found")

        checkpoint.resolve(user_id, resolution)
        await self._persist_checkpoint(checkpoint)

        # Remove from pending
        self._pending_checkpoints.pop(checkpoint_id, None)

        # Get loop status and update
        loop_status = self._active_loops.get(checkpoint.incident_id)
        if loop_status:
            loop_status.pending_checkpoints.remove(checkpoint_id)
            loop_status.is_blocked = len(loop_status.pending_checkpoints) > 0

        # If approved, create resume event
        if resolution in ("approve", "apply", "confirm_revert", "override"):
            resume_event = LoopEvent.create(
                incident_id=checkpoint.incident_id,
                tenant_id=checkpoint.tenant_id,
                stage=checkpoint.stage,
                details={
                    "checkpoint_resolved": True,
                    "checkpoint_id": checkpoint_id,
                    "resolved_by": user_id,
                    "resolution": resolution,
                },
            )
            return await self.dispatch(resume_event)

        return None

    # =========================================================================
    # LOOP STATUS MANAGEMENT
    # =========================================================================

    async def _get_or_create_loop_status(self, event: LoopEvent) -> LoopStatus:
        """Get existing loop status or create new one."""
        if event.incident_id in self._active_loops:
            return self._active_loops[event.incident_id]

        # Try loading from DB
        loop_status = await self._load_loop_status(event.incident_id)
        if loop_status:
            self._active_loops[event.incident_id] = loop_status
            return loop_status

        # Create new
        loop_status = LoopStatus(
            loop_id=f"loop_{uuid4().hex[:16]}",
            incident_id=event.incident_id,
            tenant_id=event.tenant_id,
            current_stage=event.stage,
            stages_completed=[],
            stages_failed=[],
        )
        self._active_loops[event.incident_id] = loop_status
        await self._persist_loop_status(loop_status)

        return loop_status

    async def _update_loop_status(self, loop_status: LoopStatus, event: LoopEvent) -> None:
        """Update loop status after event processing."""
        loop_status.current_stage = event.stage

        if event.is_success:
            if event.stage.value not in loop_status.stages_completed:
                loop_status.stages_completed.append(event.stage.value)
        else:
            if event.stage.value not in loop_status.stages_failed:
                loop_status.stages_failed.append(event.stage.value)
            loop_status.failure_state = event.failure_state

        # Store stage-specific results
        if event.stage == LoopStage.PATTERN_MATCHED:
            loop_status.pattern_match_result = event.details.get("match_result")
        elif event.stage == LoopStage.RECOVERY_SUGGESTED:
            loop_status.recovery_suggestion = event.details.get("recovery")
        elif event.stage == LoopStage.POLICY_GENERATED:
            loop_status.policy_rule = event.details.get("policy")
        elif event.stage == LoopStage.ROUTING_ADJUSTED:
            loop_status.routing_adjustment = event.details.get("adjustment")

        # Check if loop is complete
        all_stages = {
            "incident_created",
            "pattern_matched",
            "recovery_suggested",
            "policy_generated",
            "routing_adjusted",
        }
        if set(loop_status.stages_completed) >= all_stages:
            loop_status.is_complete = True
            loop_status.completed_at = datetime.now(timezone.utc)

        await self._persist_loop_status(loop_status)

    async def _trigger_next_stage(self, event: LoopEvent, loop_status: LoopStatus) -> Optional[LoopEvent]:
        """Determine and create the next stage event if needed."""
        stage_sequence = [
            LoopStage.INCIDENT_CREATED,
            LoopStage.PATTERN_MATCHED,
            LoopStage.RECOVERY_SUGGESTED,
            LoopStage.POLICY_GENERATED,
            LoopStage.ROUTING_ADJUSTED,
            LoopStage.LOOP_COMPLETE,
        ]

        try:
            current_idx = stage_sequence.index(event.stage)
            if current_idx < len(stage_sequence) - 1:
                next_stage = stage_sequence[current_idx + 1]

                if next_stage == LoopStage.LOOP_COMPLETE:
                    return None

                return LoopEvent.create(
                    incident_id=event.incident_id,
                    tenant_id=event.tenant_id,
                    stage=next_stage,
                    details=event.details,  # Pass through context
                    confidence_band=event.confidence_band,
                )
        except ValueError:
            logger.error(f"Unknown stage: {event.stage}")

        return None

    # =========================================================================
    # PERSISTENCE LAYER
    # =========================================================================

    async def _persist_event(self, event: LoopEvent) -> None:
        """
        Persist event to database for durability.

        HYGIENE #1: Applies JSON guard to ensure all details are serializable.
        """
        try:
            # HYGIENE #1: Apply JSON guard - fail fast if non-serializable
            event_dict = event.to_dict()
            validated_dict = ensure_json_serializable(event_dict, path="event")

            async with self.db_factory() as session:
                from sqlalchemy import text

                await session.execute(
                    text(
                        """
                        INSERT INTO loop_events (id, incident_id, tenant_id, stage, details, created_at)
                        VALUES (:id, :incident_id, :tenant_id, :stage, CAST(:details AS jsonb), :created_at)
                        ON CONFLICT (id) DO UPDATE SET details = CAST(:details AS jsonb)
                    """
                    ),
                    {
                        "id": event.event_id,
                        "incident_id": event.incident_id,
                        "tenant_id": event.tenant_id,
                        "stage": event.stage.value,
                        "details": json.dumps(validated_dict),
                        "created_at": event.timestamp,
                    },
                )
                await session.commit()
        except TypeError as e:
            # JSON serialization failed - this is a bug, log and raise
            logger.error(f"JSON serialization failed for event {event.event_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to persist event {event.event_id}: {e}")

    async def _persist_loop_status(self, status: LoopStatus) -> None:
        """Persist loop status to database."""
        try:
            async with self.db_factory() as session:
                from sqlalchemy import text

                await session.execute(
                    text(
                        """
                        INSERT INTO loop_traces (id, incident_id, tenant_id, stages, started_at, completed_at, is_complete)
                        VALUES (:id, :incident_id, :tenant_id, CAST(:stages AS jsonb), :started_at, :completed_at, :is_complete)
                        ON CONFLICT (id) DO UPDATE SET
                            stages = CAST(:stages AS jsonb),
                            completed_at = :completed_at,
                            is_complete = :is_complete
                    """
                    ),
                    {
                        "id": status.loop_id,
                        "incident_id": status.incident_id,
                        "tenant_id": status.tenant_id,
                        "stages": json.dumps(
                            {
                                "completed": status.stages_completed,
                                "failed": status.stages_failed,
                            }
                        ),
                        "started_at": status.started_at,
                        "completed_at": status.completed_at,
                        "is_complete": status.is_complete,
                    },
                )
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to persist loop status {status.loop_id}: {e}")

    async def _persist_checkpoint(self, checkpoint: HumanCheckpoint) -> None:
        """Persist human checkpoint to database."""
        try:
            async with self.db_factory() as session:
                from sqlalchemy import text

                await session.execute(
                    text(
                        """
                        INSERT INTO human_checkpoints
                        (id, checkpoint_type, incident_id, tenant_id, stage, target_id,
                         description, options, created_at, resolved_at, resolved_by, resolution)
                        VALUES (:id, :type, :incident_id, :tenant_id, :stage, :target_id,
                                :description, CAST(:options AS jsonb), :created_at, :resolved_at, :resolved_by, :resolution)
                        ON CONFLICT (id) DO UPDATE SET
                            resolved_at = :resolved_at,
                            resolved_by = :resolved_by,
                            resolution = :resolution
                    """
                    ),
                    {
                        "id": checkpoint.checkpoint_id,
                        "type": checkpoint.checkpoint_type.value,
                        "incident_id": checkpoint.incident_id,
                        "tenant_id": checkpoint.tenant_id,
                        "stage": checkpoint.stage.value,
                        "target_id": checkpoint.target_id,
                        "description": checkpoint.description,
                        "options": json.dumps(checkpoint.options),
                        "created_at": checkpoint.created_at,
                        "resolved_at": checkpoint.resolved_at,
                        "resolved_by": checkpoint.resolved_by,
                        "resolution": checkpoint.resolution,
                    },
                )
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to persist checkpoint {checkpoint.checkpoint_id}: {e}")

    async def _load_loop_status(self, incident_id: str) -> Optional[LoopStatus]:
        """Load loop status from database."""
        try:
            async with self.db_factory() as session:
                from sqlalchemy import text

                result = await session.execute(
                    text(
                        """
                        SELECT id, incident_id, tenant_id, stages, started_at, completed_at, is_complete
                        FROM loop_traces
                        WHERE incident_id = :incident_id
                        ORDER BY started_at DESC
                        LIMIT 1
                    """
                    ),
                    {"incident_id": incident_id},
                )
                row = result.fetchone()
                if row:
                    stages = json.loads(row.stages) if isinstance(row.stages, str) else row.stages
                    return LoopStatus(
                        loop_id=row.id,
                        incident_id=row.incident_id,
                        tenant_id=row.tenant_id,
                        current_stage=LoopStage.INCIDENT_CREATED,
                        stages_completed=stages.get("completed", []),
                        stages_failed=stages.get("failed", []),
                        started_at=row.started_at,
                        completed_at=row.completed_at,
                        is_complete=row.is_complete,
                    )
        except Exception as e:
            logger.error(f"Failed to load loop status for {incident_id}: {e}")
        return None

    async def _load_checkpoint(self, checkpoint_id: str) -> Optional[HumanCheckpoint]:
        """Load checkpoint from database."""
        try:
            async with self.db_factory() as session:
                from sqlalchemy import text

                result = await session.execute(
                    text(
                        """
                        SELECT * FROM human_checkpoints WHERE id = :id
                    """
                    ),
                    {"id": checkpoint_id},
                )
                row = result.fetchone()
                if row:
                    return HumanCheckpoint(
                        checkpoint_id=row.id,
                        checkpoint_type=HumanCheckpointType(row.checkpoint_type),
                        incident_id=row.incident_id,
                        tenant_id=row.tenant_id,
                        stage=LoopStage(row.stage),
                        target_id=row.target_id,
                        description=row.description,
                        options=json.loads(row.options) if isinstance(row.options, str) else row.options,
                        created_at=row.created_at,
                        resolved_at=row.resolved_at,
                        resolved_by=row.resolved_by,
                        resolution=row.resolution,
                    )
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
        return None

    # =========================================================================
    # REDIS PUBLISHING
    # =========================================================================

    async def _publish_event(self, event: LoopEvent) -> None:
        """Publish event to Redis for real-time updates."""
        try:
            channel = f"loop:{event.tenant_id}:{event.incident_id}"
            await self.redis.publish(channel, json.dumps(event.to_dict()))
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")

    async def _publish_checkpoint_needed(self, checkpoint: HumanCheckpoint) -> None:
        """Publish checkpoint needed event for console notification."""
        try:
            channel = f"checkpoints:{checkpoint.tenant_id}"
            await self.redis.publish(
                channel,
                json.dumps(
                    {
                        "type": "checkpoint_needed",
                        "checkpoint_id": checkpoint.checkpoint_id,
                        "incident_id": checkpoint.incident_id,
                        "checkpoint_type": checkpoint.checkpoint_type.value,
                        "description": checkpoint.description,
                    }
                ),
            )
        except Exception as e:
            logger.error(f"Failed to publish checkpoint needed: {e}")

    # =========================================================================
    # API METHODS
    # =========================================================================

    async def get_loop_status(self, incident_id: str) -> Optional[LoopStatus]:
        """Get current loop status for an incident."""
        if incident_id in self._active_loops:
            return self._active_loops[incident_id]
        return await self._load_loop_status(incident_id)

    async def get_pending_checkpoints(self, tenant_id: str) -> list[HumanCheckpoint]:
        """Get all pending human checkpoints for a tenant."""
        return [cp for cp in self._pending_checkpoints.values() if cp.tenant_id == tenant_id and cp.is_pending]

    async def retry_failed_stage(self, incident_id: str, stage: LoopStage, tenant_id: str) -> Optional[LoopEvent]:
        """Retry a failed stage in the loop."""
        loop_status = await self.get_loop_status(incident_id)
        if not loop_status:
            raise ValueError(f"No loop found for incident {incident_id}")

        if stage.value not in loop_status.stages_failed:
            raise ValueError(f"Stage {stage.value} did not fail")

        # Remove from failed, allow retry
        loop_status.stages_failed.remove(stage.value)
        loop_status.failure_state = None
        loop_status.is_blocked = False

        retry_event = LoopEvent.create(
            incident_id=incident_id,
            tenant_id=tenant_id,
            stage=stage,
            details={"is_retry": True},
        )

        return await self.dispatch(retry_event)

    async def revert_loop(self, incident_id: str, user_id: str, reason: str) -> None:
        """
        Revert all changes made by a loop.

        This is the ultimate human override.
        """
        loop_status = await self.get_loop_status(incident_id)
        if not loop_status:
            raise ValueError(f"No loop found for incident {incident_id}")

        logger.warning(f"Reverting loop {loop_status.loop_id} for incident {incident_id} by user {user_id}: {reason}")

        # Revert each applied change
        if loop_status.routing_adjustment:
            loop_status.routing_adjustment.rollback(f"Manual revert by {user_id}: {reason}")

        if loop_status.policy_rule:
            loop_status.policy_rule.mode = PolicyMode.DISABLED

        # Mark loop as reverted
        loop_status.is_complete = False
        loop_status.failure_state = LoopFailureState.ERROR
        loop_status.stages_completed.clear()

        await self._persist_loop_status(loop_status)


# Import PolicyMode for use in revert_loop
from .events import PolicyMode
