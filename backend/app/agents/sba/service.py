# M15.1 SBA Service
# Database operations for Strategy-Bound Agent registry
#
# Manages:
# - Agent registration with SBA
# - SBA validation at spawn time
# - SBA updates and versioning
# - Agent registry queries

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .generator import generate_sba_from_agent
from .schema import SBASchema
from .validator import SBAValidationResult, validate_at_spawn

logger = logging.getLogger("nova.agents.sba.service")


@dataclass
class AgentDefinition:
    """Agent definition from registry."""

    id: UUID
    agent_id: str
    agent_name: Optional[str]
    description: Optional[str]
    agent_type: str
    sba: Optional[Dict[str, Any]]
    sba_version: Optional[str]
    sba_validated: bool
    capabilities: Dict[str, Any]
    config: Dict[str, Any]
    status: str
    enabled: bool
    tenant_id: str
    created_at: datetime


class SBAService:
    """
    Service for SBA registry operations.

    Provides:
    - Agent registration with SBA
    - SBA validation and enforcement
    - Registry queries
    - Auto-generation for existing agents
    """

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url if database_url is not None else os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL required for SBAService")

        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self.Session = sessionmaker(bind=self.engine)

    # =========================================================================
    # Registry Operations
    # =========================================================================

    def register_agent(
        self,
        agent_id: str,
        sba: SBASchema,
        agent_name: Optional[str] = None,
        description: Optional[str] = None,
        agent_type: str = "worker",
        capabilities: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        tenant_id: str = "default",
        validate: bool = True,
    ) -> AgentDefinition:
        """
        Register an agent with its SBA schema.

        Args:
            agent_id: Unique agent identifier
            sba: Strategy Cascade schema
            agent_name: Human-readable name
            description: Agent description
            agent_type: worker, orchestrator, or aggregator
            capabilities: Agent capabilities
            config: Default configuration
            tenant_id: Tenant ID
            validate: Whether to validate SBA before registration

        Returns:
            Registered AgentDefinition

        Raises:
            ValueError: If SBA validation fails
        """
        # Validate SBA if requested
        if validate:
            result = validate_at_spawn(agent_id, sba.to_dict())
            if not result.valid:
                raise ValueError(f"SBA validation failed: {result.get_error_summary()}")

        sba_dict = sba.to_dict()
        sba_dict["agent_id"] = agent_id  # Ensure agent_id is set

        with self.Session() as session:
            session.execute(
                text(
                    """
                    INSERT INTO agents.agent_registry (
                        agent_id, agent_name, description, agent_type,
                        sba, sba_version, sba_validated, sba_validated_at,
                        capabilities, config, tenant_id
                    ) VALUES (
                        :agent_id, :agent_name, :description, :agent_type,
                        CAST(:sba AS JSONB), :sba_version, :validated, :validated_at,
                        CAST(:capabilities AS JSONB), CAST(:config AS JSONB), :tenant_id
                    )
                    ON CONFLICT (agent_id) DO UPDATE SET
                        agent_name = COALESCE(:agent_name, agents.agent_registry.agent_name),
                        description = COALESCE(:description, agents.agent_registry.description),
                        sba = CAST(:sba AS JSONB),
                        sba_version = :sba_version,
                        sba_validated = :validated,
                        sba_validated_at = :validated_at,
                        capabilities = CAST(:capabilities AS JSONB),
                        config = CAST(:config AS JSONB),
                        updated_at = now()
                """
                ),
                {
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "description": description,
                    "agent_type": agent_type,
                    "sba": json.dumps(sba_dict),
                    "sba_version": sba.sba_version,
                    "validated": validate,
                    "validated_at": datetime.now(timezone.utc) if validate else None,
                    "capabilities": json.dumps(capabilities or {}),
                    "config": json.dumps(config or {}),
                    "tenant_id": tenant_id,
                },
            )
            session.commit()

        logger.info(f"Registered agent: {agent_id} with SBA v{sba.sba_version}")
        return self.get_agent(agent_id)

    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        """Get agent definition by ID."""
        with self.Session() as session:
            result = session.execute(
                text(
                    """
                    SELECT
                        id, agent_id, agent_name, description, agent_type,
                        sba, sba_version, sba_validated, capabilities, config,
                        status, enabled, tenant_id, created_at
                    FROM agents.agent_registry
                    WHERE agent_id = :agent_id
                """
                ),
                {"agent_id": agent_id},
            )
            row = result.fetchone()

            if not row:
                return None

            return AgentDefinition(
                id=UUID(str(row[0])),
                agent_id=row[1],
                agent_name=row[2],
                description=row[3],
                agent_type=row[4],
                sba=row[5] if isinstance(row[5], dict) else json.loads(row[5]) if row[5] else None,
                sba_version=row[6],
                sba_validated=row[7],
                capabilities=row[8] if isinstance(row[8], dict) else json.loads(row[8]) if row[8] else {},
                config=row[9] if isinstance(row[9], dict) else json.loads(row[9]) if row[9] else {},
                status=row[10],
                enabled=row[11],
                tenant_id=row[12],
                created_at=row[13],
            )

    def list_agents(
        self,
        agent_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
        enabled_only: bool = True,
        sba_validated_only: bool = False,
    ) -> List[AgentDefinition]:
        """List agents from registry."""
        with self.Session() as session:
            query = """
                SELECT
                    id, agent_id, agent_name, description, agent_type,
                    sba, sba_version, sba_validated, capabilities, config,
                    status, enabled, tenant_id, created_at
                FROM agents.agent_registry
                WHERE 1=1
            """
            params: Dict[str, Any] = {}

            if agent_type:
                query += " AND agent_type = :agent_type"
                params["agent_type"] = agent_type

            if tenant_id:
                query += " AND tenant_id = :tenant_id"
                params["tenant_id"] = tenant_id

            if enabled_only:
                query += " AND enabled = true"

            if sba_validated_only:
                query += " AND sba_validated = true"

            query += " ORDER BY agent_id"

            result = session.execute(text(query), params)
            agents = []

            for row in result:
                agents.append(
                    AgentDefinition(
                        id=UUID(str(row[0])),
                        agent_id=row[1],
                        agent_name=row[2],
                        description=row[3],
                        agent_type=row[4],
                        sba=row[5] if isinstance(row[5], dict) else json.loads(row[5]) if row[5] else None,
                        sba_version=row[6],
                        sba_validated=row[7],
                        capabilities=row[8] if isinstance(row[8], dict) else json.loads(row[8]) if row[8] else {},
                        config=row[9] if isinstance(row[9], dict) else json.loads(row[9]) if row[9] else {},
                        status=row[10],
                        enabled=row[11],
                        tenant_id=row[12],
                        created_at=row[13],
                    )
                )

            return agents

    # =========================================================================
    # SBA Enforcement
    # =========================================================================

    def validate_for_spawn(
        self,
        agent_id: str,
        auto_generate: bool = True,
        orchestrator: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> SBAValidationResult:
        """
        Validate agent SBA for spawn.

        This is the ENFORCEMENT POINT called by agent_spawn.

        Args:
            agent_id: Agent to validate
            auto_generate: Auto-generate SBA if missing
            orchestrator: Orchestrator for auto-generation
            config: Config for auto-generation

        Returns:
            SBAValidationResult - if not valid, spawn MUST be blocked
        """
        # Get agent from registry
        agent = self.get_agent(agent_id)

        if agent is None:
            if auto_generate:
                # Auto-generate and register
                sba = generate_sba_from_agent(
                    agent_id=agent_id,
                    config=config,
                    orchestrator=orchestrator or "system",
                )
                try:
                    self.register_agent(
                        agent_id=agent_id,
                        sba=sba,
                        agent_type="worker",
                        validate=True,
                    )
                    return validate_at_spawn(agent_id, sba.to_dict())
                except ValueError as e:
                    return SBAValidationResult(
                        valid=False,
                        errors=[
                            {
                                "code": "AUTO_GENERATION_FAILED",
                                "field": "sba",
                                "message": str(e),
                            }
                        ],
                    )

            # No agent and no auto-generate
            return validate_at_spawn(agent_id, None)

        # Agent exists, validate its SBA
        return validate_at_spawn(agent_id, agent.sba)

    def check_spawn_allowed(
        self,
        agent_id: str,
        auto_generate: bool = True,
        orchestrator: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if agent is allowed to spawn.

        Convenience method that returns simple bool + error message.

        Args:
            agent_id: Agent to check
            auto_generate: Auto-generate SBA if missing
            orchestrator: Orchestrator for auto-generation
            config: Config for auto-generation

        Returns:
            Tuple of (allowed, error_message)
        """
        result = self.validate_for_spawn(
            agent_id=agent_id,
            auto_generate=auto_generate,
            orchestrator=orchestrator,
            config=config,
        )

        if result.valid:
            return True, None

        return False, result.get_error_summary()

    # =========================================================================
    # SBA Update Operations
    # =========================================================================

    def update_sba(
        self,
        agent_id: str,
        sba: SBASchema,
        validate: bool = True,
    ) -> AgentDefinition:
        """Update agent SBA."""
        if validate:
            result = validate_at_spawn(agent_id, sba.to_dict())
            if not result.valid:
                raise ValueError(f"SBA validation failed: {result.get_error_summary()}")

        sba_dict = sba.to_dict()
        sba_dict["agent_id"] = agent_id

        with self.Session() as session:
            session.execute(
                text(
                    """
                    UPDATE agents.agent_registry
                    SET sba = CAST(:sba AS JSONB),
                        sba_version = :sba_version,
                        sba_validated = :validated,
                        sba_validated_at = :validated_at
                    WHERE agent_id = :agent_id
                """
                ),
                {
                    "agent_id": agent_id,
                    "sba": json.dumps(sba_dict),
                    "sba_version": sba.sba_version,
                    "validated": validate,
                    "validated_at": datetime.now(timezone.utc) if validate else None,
                },
            )
            session.commit()

        return self.get_agent(agent_id)

    def update_fulfillment_metric(
        self,
        agent_id: str,
        fulfillment_metric: float,
        reason: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> bool:
        """
        Update the fulfillment metric for an agent.

        M15.1.1: Now includes history tracking for audit trail.

        Called by orchestrator after task completion.
        """
        if not 0.0 <= fulfillment_metric <= 1.0:
            raise ValueError("fulfillment_metric must be between 0.0 and 1.0")

        with self.Session() as session:
            # Get current metric for history
            result = session.execute(
                text(
                    """
                    SELECT sba->'how_to_win'->>'fulfillment_metric'
                    FROM agents.agent_registry
                    WHERE agent_id = :agent_id AND sba IS NOT NULL
                """
                ),
                {"agent_id": agent_id},
            )
            old_metric_row = result.fetchone()
            old_metric = float(old_metric_row[0]) if old_metric_row and old_metric_row[0] else 0.0

            # Update metric and append to history
            session.execute(
                text(
                    """
                    UPDATE agents.agent_registry
                    SET sba = jsonb_set(
                        jsonb_set(
                            sba,
                            '{how_to_win,fulfillment_metric}',
                            :metric::jsonb
                        ),
                        '{how_to_win,fulfillment_history}',
                        COALESCE(sba->'how_to_win'->'fulfillment_history', '[]'::jsonb) ||
                        jsonb_build_object(
                            'old_metric', :old_metric,
                            'new_metric', :metric,
                            'reason', :reason,
                            'job_id', :job_id,
                            'timestamp', :timestamp
                        )::jsonb
                    )
                    WHERE agent_id = :agent_id AND sba IS NOT NULL
                """
                ),
                {
                    "agent_id": agent_id,
                    "metric": str(fulfillment_metric),
                    "old_metric": old_metric,
                    "reason": reason,
                    "job_id": job_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            session.commit()

        logger.info(
            "fulfillment_metric_updated",
            extra={
                "agent_id": agent_id,
                "old_metric": old_metric,
                "new_metric": fulfillment_metric,
                "reason": reason,
            },
        )
        return True

    def compute_fulfillment_from_job(
        self,
        agent_id: str,
        job_id: str,
        total_items: int,
        completed_items: int,
        failed_items: int,
        blocked_items: int = 0,
        weight_success: float = 1.0,
        weight_failure: float = -0.5,
        weight_blocked: float = -0.25,
    ) -> float:
        """
        M15.1.1: Compute fulfillment metric from job results.

        This is the ORCHESTRATOR HOOK for computing fulfillment based on
        actual test/task results rather than self-reported metrics.

        Formula:
            fulfillment = max(0, (successes * weight_success + failures * weight_failure +
                                  blocked * weight_blocked)) / total_weighted

        Args:
            agent_id: Agent ID
            job_id: Job ID for audit trail
            total_items: Total items in job
            completed_items: Successfully completed items
            failed_items: Failed items
            blocked_items: Blocked (risk) items
            weight_success: Weight for success (default 1.0)
            weight_failure: Weight for failure (default -0.5)
            weight_blocked: Weight for blocked (default -0.25)

        Returns:
            Computed fulfillment metric (0.0-1.0)
        """
        if total_items == 0:
            return 0.0

        # Compute weighted score
        raw_score = completed_items * weight_success + failed_items * weight_failure + blocked_items * weight_blocked

        # Normalize to 0-1 range (max possible is all items * weight_success)
        max_score = total_items * weight_success
        fulfillment = max(0.0, min(1.0, raw_score / max_score))

        # Update with computed metric
        reason = (
            f"job_completion: {completed_items}/{total_items} success, {failed_items} failed, {blocked_items} blocked"
        )
        self.update_fulfillment_metric(
            agent_id=agent_id,
            fulfillment_metric=fulfillment,
            reason=reason,
            job_id=job_id,
        )

        return fulfillment

    def get_fulfillment_history(
        self,
        agent_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        M15.1.1: Get fulfillment metric history for an agent.

        Returns:
            List of historical fulfillment metric changes
        """
        with self.Session() as session:
            result = session.execute(
                text(
                    """
                    SELECT sba->'how_to_win'->'fulfillment_history'
                    FROM agents.agent_registry
                    WHERE agent_id = :agent_id AND sba IS NOT NULL
                """
                ),
                {"agent_id": agent_id},
            )
            row = result.fetchone()

            if not row or not row[0]:
                return []

            history = row[0] if isinstance(row[0], list) else json.loads(row[0])
            return history[-limit:] if limit > 0 else history

    # =========================================================================
    # Retrofit Operations
    # =========================================================================

    def retrofit_missing_sba(
        self,
        tenant_id: str = "default",
        orchestrator: str = "system",
    ) -> List[str]:
        """
        Generate SBA for all agents without one.

        Returns list of retrofitted agent IDs.
        """
        retrofitted = []

        with self.Session() as session:
            # Find agents without SBA
            result = session.execute(
                text(
                    """
                    SELECT agent_id, capabilities, config
                    FROM agents.agent_registry
                    WHERE sba IS NULL AND tenant_id = :tenant_id
                """
                ),
                {"tenant_id": tenant_id},
            )

            for row in result:
                agent_id = row[0]
                capabilities = row[1] if isinstance(row[1], dict) else json.loads(row[1]) if row[1] else {}
                config = row[2] if isinstance(row[2], dict) else json.loads(row[2]) if row[2] else {}

                # Generate SBA
                sba = generate_sba_from_agent(
                    agent_id=agent_id,
                    capabilities=capabilities,
                    config=config,
                    orchestrator=orchestrator,
                )

                # Update in DB
                sba_dict = sba.to_dict()
                sba_dict["agent_id"] = agent_id

                session.execute(
                    text(
                        """
                        UPDATE agents.agent_registry
                        SET sba = CAST(:sba AS JSONB),
                            sba_version = :sba_version,
                            sba_validated = false
                        WHERE agent_id = :agent_id
                    """
                    ),
                    {
                        "agent_id": agent_id,
                        "sba": json.dumps(sba_dict),
                        "sba_version": sba.sba_version,
                    },
                )

                retrofitted.append(agent_id)
                logger.info(f"Retrofitted SBA for agent: {agent_id}")

            session.commit()

        return retrofitted


# =============================================================================
# Singleton
# =============================================================================

_service: Optional[SBAService] = None


def get_sba_service() -> SBAService:
    """Get singleton SBA service instance."""
    global _service
    if _service is None:
        _service = SBAService()
    return _service
