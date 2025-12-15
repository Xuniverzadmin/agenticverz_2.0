# M12 Registry Service
# Agent registration, heartbeats, and stale detection
#
# Pattern reused from M7 memory pins TTL + M2 SkillRegistry (50% reuse)

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger("nova.agents.registry_service")

# Default heartbeat settings
DEFAULT_HEARTBEAT_INTERVAL = 30  # seconds
DEFAULT_STALE_THRESHOLD = 60  # seconds


@dataclass
class AgentInstance:
    """Registered agent instance."""
    id: UUID
    agent_id: str
    instance_id: str
    job_id: Optional[UUID]
    status: str
    capabilities: Optional[Dict[str, Any]]
    heartbeat_at: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]
    heartbeat_age_seconds: Optional[float] = None


@dataclass
class RegistrationResult:
    """Result of agent registration."""
    success: bool
    instance_id: str
    db_id: Optional[UUID] = None
    error: Optional[str] = None


class RegistryService:
    """
    Agent registry service for M12 multi-agent system.

    Manages:
    - Agent instance registration
    - Heartbeat updates
    - Stale agent detection
    - Job item reclamation from dead workers
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL,
        stale_threshold: int = DEFAULT_STALE_THRESHOLD,
    ):
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL required for RegistryService")

        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self.Session = sessionmaker(bind=self.engine)
        self.heartbeat_interval = heartbeat_interval
        self.stale_threshold = stale_threshold

    def register(
        self,
        agent_id: str,
        instance_id: Optional[str] = None,
        job_id: Optional[UUID] = None,
        capabilities: Optional[Dict[str, Any]] = None,
    ) -> RegistrationResult:
        """
        Register an agent instance.

        Args:
            agent_id: Agent type/name (e.g., "scraper_worker")
            instance_id: Unique instance ID (generated if not provided)
            job_id: Optional job association
            capabilities: Optional capabilities dict

        Returns:
            RegistrationResult with instance_id
        """
        instance_id = instance_id or f"{agent_id}_{uuid4().hex[:8]}"
        db_id = uuid4()

        with self.Session() as session:
            try:
                session.execute(
                    text("""
                        INSERT INTO agents.instances (
                            id, agent_id, instance_id, job_id,
                            status, capabilities, heartbeat_at, created_at
                        ) VALUES (
                            :id, :agent_id, :instance_id, CAST(:job_id AS UUID),
                            'running', CAST(:capabilities AS JSONB), now(), now()
                        )
                        ON CONFLICT (instance_id) DO UPDATE SET
                            status = 'running',
                            job_id = CAST(:job_id AS UUID),
                            capabilities = CAST(:capabilities AS JSONB),
                            heartbeat_at = now()
                    """),
                    {
                        "id": str(db_id),
                        "agent_id": agent_id,
                        "instance_id": instance_id,
                        "job_id": str(job_id) if job_id else None,
                        "capabilities": json.dumps(capabilities) if capabilities else "{}",
                    }
                )

                session.commit()

                logger.info(
                    "agent_registered",
                    extra={
                        "agent_id": agent_id,
                        "instance_id": instance_id,
                        "job_id": str(job_id) if job_id else None,
                    }
                )

                return RegistrationResult(
                    success=True,
                    instance_id=instance_id,
                    db_id=db_id,
                )

            except Exception as e:
                session.rollback()
                logger.error(f"Agent registration failed: {e}")
                return RegistrationResult(
                    success=False,
                    instance_id=instance_id,
                    error=str(e)[:200],
                )

    def heartbeat(self, instance_id: str) -> bool:
        """
        Update heartbeat for an agent instance.

        Args:
            instance_id: Instance to update

        Returns:
            True if updated successfully
        """
        with self.Session() as session:
            try:
                result = session.execute(
                    text("""
                        UPDATE agents.instances
                        SET heartbeat_at = now(),
                            status = CASE
                                WHEN status = 'stale' THEN 'running'
                                ELSE status
                            END
                        WHERE instance_id = :instance_id
                        RETURNING id
                    """),
                    {"instance_id": instance_id}
                )
                row = result.fetchone()
                session.commit()

                if row:
                    logger.debug(f"Heartbeat: {instance_id}")
                    return True

                return False

            except Exception as e:
                session.rollback()
                logger.error(f"Heartbeat failed: {e}")
                return False

    def deregister(self, instance_id: str) -> bool:
        """
        Deregister an agent instance.

        Args:
            instance_id: Instance to deregister

        Returns:
            True if deregistered
        """
        with self.Session() as session:
            try:
                result = session.execute(
                    text("""
                        UPDATE agents.instances
                        SET status = 'stopped', completed_at = now()
                        WHERE instance_id = :instance_id
                        RETURNING id
                    """),
                    {"instance_id": instance_id}
                )
                row = result.fetchone()
                session.commit()

                if row:
                    logger.info(f"Agent deregistered: {instance_id}")
                    return True

                return False

            except Exception as e:
                session.rollback()
                logger.error(f"Deregister failed: {e}")
                return False

    def get_instance(self, instance_id: str) -> Optional[AgentInstance]:
        """Get agent instance by instance_id."""
        with self.Session() as session:
            result = session.execute(
                text("""
                    SELECT
                        id, agent_id, instance_id, job_id, status,
                        capabilities, heartbeat_at, created_at, completed_at,
                        EXTRACT(EPOCH FROM (now() - heartbeat_at)) as heartbeat_age
                    FROM agents.instances
                    WHERE instance_id = :instance_id
                """),
                {"instance_id": instance_id}
            )
            row = result.fetchone()

            if not row:
                return None

            return AgentInstance(
                id=UUID(str(row[0])),
                agent_id=row[1],
                instance_id=row[2],
                job_id=UUID(str(row[3])) if row[3] else None,
                status=row[4],
                capabilities=row[5],
                heartbeat_at=row[6],
                created_at=row[7],
                completed_at=row[8],
                heartbeat_age_seconds=float(row[9]) if row[9] else None,
            )

    def list_instances(
        self,
        agent_id: Optional[str] = None,
        job_id: Optional[UUID] = None,
        status: Optional[str] = None,
        include_stale: bool = False,
    ) -> List[AgentInstance]:
        """
        List agent instances.

        Args:
            agent_id: Filter by agent type
            job_id: Filter by job
            status: Filter by status
            include_stale: Include stale agents

        Returns:
            List of agent instances
        """
        with self.Session() as session:
            query = """
                SELECT
                    id, agent_id, instance_id, job_id, status,
                    capabilities, heartbeat_at, created_at, completed_at,
                    EXTRACT(EPOCH FROM (now() - heartbeat_at)) as heartbeat_age
                FROM agents.instances
                WHERE 1=1
            """
            params: Dict[str, Any] = {}

            if agent_id:
                query += " AND agent_id = :agent_id"
                params["agent_id"] = agent_id

            if job_id:
                query += " AND job_id = :job_id"
                params["job_id"] = str(job_id)

            if status:
                query += " AND status = :status"
                params["status"] = status
            elif not include_stale:
                query += " AND status IN ('running', 'idle')"

            query += " ORDER BY created_at DESC"

            result = session.execute(text(query), params)
            instances = []

            for row in result:
                instances.append(AgentInstance(
                    id=UUID(str(row[0])),
                    agent_id=row[1],
                    instance_id=row[2],
                    job_id=UUID(str(row[3])) if row[3] else None,
                    status=row[4],
                    capabilities=row[5],
                    heartbeat_at=row[6],
                    created_at=row[7],
                    completed_at=row[8],
                    heartbeat_age_seconds=float(row[9]) if row[9] else None,
                ))

            return instances

    def mark_instance_stale(self, instance_id: str) -> bool:
        """
        Mark a specific agent instance as stale.

        Used when a specific worker is known to be dead/unresponsive.

        Args:
            instance_id: Instance to mark as stale

        Returns:
            True if instance was marked stale
        """
        with self.Session() as session:
            try:
                result = session.execute(
                    text("""
                        UPDATE agents.instances
                        SET status = 'stale'
                        WHERE instance_id = :instance_id
                          AND status = 'running'
                        RETURNING id
                    """),
                    {"instance_id": instance_id}
                )
                row = result.fetchone()
                session.commit()

                if row:
                    logger.warning(f"Marked instance stale: {instance_id}")
                    return True

                return False

            except Exception as e:
                session.rollback()
                logger.error(f"Mark instance stale failed: {e}")
                return False

    def mark_stale(self, threshold_seconds: Optional[int] = None) -> int:
        """
        Mark agents as stale if heartbeat is too old.

        Args:
            threshold_seconds: Override default stale threshold

        Returns:
            Number of agents marked stale
        """
        threshold = threshold_seconds or self.stale_threshold

        with self.Session() as session:
            try:
                # Use the DB function if available
                try:
                    result = session.execute(
                        text("SELECT agents.mark_stale_instances(make_interval(secs => :threshold))"),
                        {"threshold": threshold}
                    )
                    count = result.fetchone()[0]
                    session.commit()
                    return count or 0
                except Exception:
                    pass

                # Fallback to raw SQL
                result = session.execute(
                    text("""
                        UPDATE agents.instances
                        SET status = 'stale'
                        WHERE status = 'running'
                          AND heartbeat_at < now() - make_interval(secs => :threshold)
                        RETURNING id
                    """),
                    {"threshold": threshold}
                )
                count = len(result.fetchall())
                session.commit()

                if count > 0:
                    logger.warning(f"Marked {count} agents as stale")

                return count

            except Exception as e:
                session.rollback()
                logger.error(f"Mark stale failed: {e}")
                return 0

    def reclaim_stale_items(self) -> int:
        """
        Reclaim job items from stale workers.

        Returns:
            Number of items reclaimed
        """
        with self.Session() as session:
            try:
                # Use the DB function if available
                try:
                    result = session.execute(text("SELECT agents.reclaim_stale_items()"))
                    count = result.fetchone()[0]
                    session.commit()
                    return count or 0
                except Exception:
                    pass

                # Fallback to raw SQL
                result = session.execute(
                    text("""
                        UPDATE agents.job_items ji
                        SET status = 'pending',
                            worker_instance_id = NULL,
                            claimed_at = NULL,
                            retry_count = retry_count + 1
                        FROM agents.instances i
                        WHERE ji.worker_instance_id = i.instance_id
                          AND i.status = 'stale'
                          AND ji.status IN ('claimed', 'running')
                          AND ji.retry_count < ji.max_retries
                        RETURNING ji.id
                    """)
                )
                count = len(result.fetchall())
                session.commit()

                if count > 0:
                    logger.info(f"Reclaimed {count} items from stale workers")

                return count

            except Exception as e:
                session.rollback()
                logger.error(f"Reclaim stale items failed: {e}")
                return 0

    def get_active_worker_count(self, job_id: Optional[UUID] = None) -> int:
        """Get count of active workers."""
        with self.Session() as session:
            query = """
                SELECT COUNT(*)
                FROM agents.instances
                WHERE status IN ('running', 'idle')
            """
            params = {}

            if job_id:
                query += " AND job_id = :job_id"
                params["job_id"] = str(job_id)

            result = session.execute(text(query), params)
            return result.fetchone()[0] or 0


# Singleton instance
_service: Optional[RegistryService] = None


def get_registry_service() -> RegistryService:
    """Get singleton registry service instance."""
    global _service
    if _service is None:
        _service = RegistryService()
    return _service
