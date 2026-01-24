# Layer: L5 — Adapter (Facade)
# AUDIENCE: CUSTOMER
# Role: Lifecycle Facade - Thin translation layer for lifecycle operations
# PHASE: W4
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: L2 lifecycle.py API, SDK
# Allowed Imports: L5 (engines), L6 (drivers)
# Forbidden Imports: L1, L2
# Reference: GAP-131 to GAP-136 (Lifecycle APIs)
# NOTE: Reclassified L6→L3 (2026-01-24) - Per HOC topology, facades are L3 (adapters)


"""
Lifecycle Facade (L4 Domain Logic)

This facade provides the external interface for lifecycle operations.
All lifecycle APIs MUST use this facade instead of directly importing
internal lifecycle modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes agent and run lifecycle logic
- Provides unified access to state transitions
- Single point for audit emission

L2 API Routes (GAP-131 to GAP-136):
- POST /api/v1/lifecycle/agents (create agent)
- GET /api/v1/lifecycle/agents (list agents)
- GET /api/v1/lifecycle/agents/{id} (get agent)
- POST /api/v1/lifecycle/agents/{id}/start (start agent)
- POST /api/v1/lifecycle/agents/{id}/stop (stop agent)
- POST /api/v1/lifecycle/agents/{id}/terminate (terminate agent)
- POST /api/v1/lifecycle/runs (create run)
- GET /api/v1/lifecycle/runs (list runs)
- GET /api/v1/lifecycle/runs/{id} (get run)
- POST /api/v1/lifecycle/runs/{id}/pause (pause run)
- POST /api/v1/lifecycle/runs/{id}/resume (resume run)
- POST /api/v1/lifecycle/runs/{id}/cancel (cancel run)

Usage:
    from app.services.lifecycle.facade import get_lifecycle_facade

    facade = get_lifecycle_facade()

    # Start an agent
    agent = await facade.start_agent(agent_id="...", tenant_id="...")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("nova.services.lifecycle.facade")


class AgentState(str, Enum):
    """Agent lifecycle states."""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    TERMINATED = "terminated"
    ERROR = "error"


class RunState(str, Enum):
    """Run lifecycle states."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class AgentLifecycle:
    """Agent lifecycle information."""
    id: str
    tenant_id: str
    name: str
    state: str
    config: Dict[str, Any]
    created_at: str
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    terminated_at: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "state": self.state,
            "config": self.config,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "terminated_at": self.terminated_at,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class RunLifecycle:
    """Run lifecycle information."""
    id: str
    tenant_id: str
    agent_id: str
    state: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    created_at: str
    started_at: Optional[str] = None
    paused_at: Optional[str] = None
    resumed_at: Optional[str] = None
    completed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "agent_id": self.agent_id,
            "state": self.state,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "paused_at": self.paused_at,
            "resumed_at": self.resumed_at,
            "completed_at": self.completed_at,
            "cancelled_at": self.cancelled_at,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class LifecycleSummary:
    """Summary of lifecycle entities."""
    tenant_id: str
    total_agents: int
    running_agents: int
    stopped_agents: int
    total_runs: int
    pending_runs: int
    running_runs: int
    completed_runs: int
    failed_runs: int
    as_of: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "total_agents": self.total_agents,
            "running_agents": self.running_agents,
            "stopped_agents": self.stopped_agents,
            "total_runs": self.total_runs,
            "pending_runs": self.pending_runs,
            "running_runs": self.running_runs,
            "completed_runs": self.completed_runs,
            "failed_runs": self.failed_runs,
            "as_of": self.as_of,
        }


class LifecycleFacade:
    """
    Facade for lifecycle operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    lifecycle services.

    Layer: L4 (Domain Logic)
    Callers: lifecycle.py (L2), aos_sdk
    """

    def __init__(self):
        """Initialize facade."""
        self._agents: Dict[str, AgentLifecycle] = {}
        self._runs: Dict[str, RunLifecycle] = {}

    # =========================================================================
    # Agent Lifecycle Operations (GAP-131, GAP-132)
    # =========================================================================

    async def create_agent(
        self,
        tenant_id: str,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentLifecycle:
        """
        Create a new agent.

        Args:
            tenant_id: Tenant ID
            name: Agent name
            config: Agent configuration
            metadata: Additional metadata

        Returns:
            Created AgentLifecycle
        """
        now = datetime.now(timezone.utc)
        agent_id = str(uuid.uuid4())

        agent = AgentLifecycle(
            id=agent_id,
            tenant_id=tenant_id,
            name=name,
            state=AgentState.CREATED.value,
            config=config or {},
            created_at=now.isoformat(),
            metadata=metadata or {},
        )

        self._agents[agent_id] = agent

        logger.info(
            "facade.create_agent",
            extra={"agent_id": agent_id, "tenant_id": tenant_id, "name": name}
        )

        return agent

    async def list_agents(
        self,
        tenant_id: str,
        state: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AgentLifecycle]:
        """
        List agents for a tenant.

        Args:
            tenant_id: Tenant ID
            state: Optional filter by state
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of AgentLifecycle
        """
        results = []
        for agent in self._agents.values():
            if agent.tenant_id != tenant_id:
                continue
            if state and agent.state != state:
                continue
            results.append(agent)

        results.sort(key=lambda a: a.created_at, reverse=True)
        return results[offset:offset + limit]

    async def get_agent(
        self,
        agent_id: str,
        tenant_id: str,
    ) -> Optional[AgentLifecycle]:
        """
        Get a specific agent.

        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID for authorization

        Returns:
            AgentLifecycle or None if not found
        """
        agent = self._agents.get(agent_id)
        if agent and agent.tenant_id == tenant_id:
            return agent
        return None

    async def start_agent(
        self,
        agent_id: str,
        tenant_id: str,
    ) -> Optional[AgentLifecycle]:
        """
        Start an agent.

        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID for authorization

        Returns:
            Updated AgentLifecycle or None if not found
        """
        agent = self._agents.get(agent_id)
        if not agent or agent.tenant_id != tenant_id:
            return None

        if agent.state not in [AgentState.CREATED.value, AgentState.STOPPED.value]:
            logger.warning(
                "facade.start_agent.invalid_state",
                extra={"agent_id": agent_id, "current_state": agent.state}
            )
            return agent

        now = datetime.now(timezone.utc)
        agent.state = AgentState.RUNNING.value
        agent.started_at = now.isoformat()

        logger.info(
            "facade.start_agent",
            extra={"agent_id": agent_id, "tenant_id": tenant_id}
        )

        return agent

    async def stop_agent(
        self,
        agent_id: str,
        tenant_id: str,
    ) -> Optional[AgentLifecycle]:
        """
        Stop an agent.

        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID for authorization

        Returns:
            Updated AgentLifecycle or None if not found
        """
        agent = self._agents.get(agent_id)
        if not agent or agent.tenant_id != tenant_id:
            return None

        if agent.state != AgentState.RUNNING.value:
            logger.warning(
                "facade.stop_agent.invalid_state",
                extra={"agent_id": agent_id, "current_state": agent.state}
            )
            return agent

        now = datetime.now(timezone.utc)
        agent.state = AgentState.STOPPED.value
        agent.stopped_at = now.isoformat()

        logger.info(
            "facade.stop_agent",
            extra={"agent_id": agent_id, "tenant_id": tenant_id}
        )

        return agent

    async def terminate_agent(
        self,
        agent_id: str,
        tenant_id: str,
    ) -> Optional[AgentLifecycle]:
        """
        Terminate an agent.

        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID for authorization

        Returns:
            Updated AgentLifecycle or None if not found
        """
        agent = self._agents.get(agent_id)
        if not agent or agent.tenant_id != tenant_id:
            return None

        if agent.state == AgentState.TERMINATED.value:
            return agent

        now = datetime.now(timezone.utc)
        agent.state = AgentState.TERMINATED.value
        agent.terminated_at = now.isoformat()

        logger.info(
            "facade.terminate_agent",
            extra={"agent_id": agent_id, "tenant_id": tenant_id}
        )

        return agent

    # =========================================================================
    # Run Lifecycle Operations (GAP-133, GAP-134, GAP-135, GAP-136)
    # =========================================================================

    async def create_run(
        self,
        tenant_id: str,
        agent_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[RunLifecycle]:
        """
        Create a new run.

        Args:
            tenant_id: Tenant ID
            agent_id: Agent ID
            input_data: Input data for the run
            metadata: Additional metadata

        Returns:
            Created RunLifecycle or None if agent not found
        """
        agent = self._agents.get(agent_id)
        if not agent or agent.tenant_id != tenant_id:
            return None

        now = datetime.now(timezone.utc)
        run_id = str(uuid.uuid4())

        run = RunLifecycle(
            id=run_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            state=RunState.PENDING.value,
            input_data=input_data or {},
            output_data=None,
            created_at=now.isoformat(),
            metadata=metadata or {},
        )

        self._runs[run_id] = run

        # Auto-start if agent is running
        if agent.state == AgentState.RUNNING.value:
            run.state = RunState.RUNNING.value
            run.started_at = now.isoformat()

        logger.info(
            "facade.create_run",
            extra={"run_id": run_id, "agent_id": agent_id, "tenant_id": tenant_id}
        )

        return run

    async def list_runs(
        self,
        tenant_id: str,
        agent_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RunLifecycle]:
        """
        List runs for a tenant.

        Args:
            tenant_id: Tenant ID
            agent_id: Optional filter by agent
            state: Optional filter by state
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of RunLifecycle
        """
        results = []
        for run in self._runs.values():
            if run.tenant_id != tenant_id:
                continue
            if agent_id and run.agent_id != agent_id:
                continue
            if state and run.state != state:
                continue
            results.append(run)

        results.sort(key=lambda r: r.created_at, reverse=True)
        return results[offset:offset + limit]

    async def get_run(
        self,
        run_id: str,
        tenant_id: str,
    ) -> Optional[RunLifecycle]:
        """
        Get a specific run.

        Args:
            run_id: Run ID
            tenant_id: Tenant ID for authorization

        Returns:
            RunLifecycle or None if not found
        """
        run = self._runs.get(run_id)
        if run and run.tenant_id == tenant_id:
            return run
        return None

    async def pause_run(
        self,
        run_id: str,
        tenant_id: str,
    ) -> Optional[RunLifecycle]:
        """
        Pause a run.

        Args:
            run_id: Run ID
            tenant_id: Tenant ID for authorization

        Returns:
            Updated RunLifecycle or None if not found
        """
        run = self._runs.get(run_id)
        if not run or run.tenant_id != tenant_id:
            return None

        if run.state != RunState.RUNNING.value:
            logger.warning(
                "facade.pause_run.invalid_state",
                extra={"run_id": run_id, "current_state": run.state}
            )
            return run

        now = datetime.now(timezone.utc)
        run.state = RunState.PAUSED.value
        run.paused_at = now.isoformat()

        logger.info(
            "facade.pause_run",
            extra={"run_id": run_id, "tenant_id": tenant_id}
        )

        return run

    async def resume_run(
        self,
        run_id: str,
        tenant_id: str,
    ) -> Optional[RunLifecycle]:
        """
        Resume a paused run.

        Args:
            run_id: Run ID
            tenant_id: Tenant ID for authorization

        Returns:
            Updated RunLifecycle or None if not found
        """
        run = self._runs.get(run_id)
        if not run or run.tenant_id != tenant_id:
            return None

        if run.state != RunState.PAUSED.value:
            logger.warning(
                "facade.resume_run.invalid_state",
                extra={"run_id": run_id, "current_state": run.state}
            )
            return run

        now = datetime.now(timezone.utc)
        run.state = RunState.RUNNING.value
        run.resumed_at = now.isoformat()

        logger.info(
            "facade.resume_run",
            extra={"run_id": run_id, "tenant_id": tenant_id}
        )

        return run

    async def cancel_run(
        self,
        run_id: str,
        tenant_id: str,
    ) -> Optional[RunLifecycle]:
        """
        Cancel a run.

        Args:
            run_id: Run ID
            tenant_id: Tenant ID for authorization

        Returns:
            Updated RunLifecycle or None if not found
        """
        run = self._runs.get(run_id)
        if not run or run.tenant_id != tenant_id:
            return None

        if run.state in [RunState.COMPLETED.value, RunState.CANCELLED.value, RunState.FAILED.value]:
            return run

        now = datetime.now(timezone.utc)
        run.state = RunState.CANCELLED.value
        run.cancelled_at = now.isoformat()

        logger.info(
            "facade.cancel_run",
            extra={"run_id": run_id, "tenant_id": tenant_id}
        )

        return run

    # =========================================================================
    # Summary Operations
    # =========================================================================

    async def get_summary(
        self,
        tenant_id: str,
    ) -> LifecycleSummary:
        """
        Get lifecycle summary for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            LifecycleSummary
        """
        now = datetime.now(timezone.utc)

        total_agents = 0
        running_agents = 0
        stopped_agents = 0

        for agent in self._agents.values():
            if agent.tenant_id != tenant_id:
                continue
            total_agents += 1
            if agent.state == AgentState.RUNNING.value:
                running_agents += 1
            elif agent.state == AgentState.STOPPED.value:
                stopped_agents += 1

        total_runs = 0
        pending_runs = 0
        running_runs = 0
        completed_runs = 0
        failed_runs = 0

        for run in self._runs.values():
            if run.tenant_id != tenant_id:
                continue
            total_runs += 1
            if run.state == RunState.PENDING.value:
                pending_runs += 1
            elif run.state == RunState.RUNNING.value:
                running_runs += 1
            elif run.state == RunState.COMPLETED.value:
                completed_runs += 1
            elif run.state == RunState.FAILED.value:
                failed_runs += 1

        return LifecycleSummary(
            tenant_id=tenant_id,
            total_agents=total_agents,
            running_agents=running_agents,
            stopped_agents=stopped_agents,
            total_runs=total_runs,
            pending_runs=pending_runs,
            running_runs=running_runs,
            completed_runs=completed_runs,
            failed_runs=failed_runs,
            as_of=now.isoformat(),
        )


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[LifecycleFacade] = None


def get_lifecycle_facade() -> LifecycleFacade:
    """
    Get the lifecycle facade instance.

    This is the recommended way to access lifecycle operations
    from L2 APIs and the SDK.

    Returns:
        LifecycleFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = LifecycleFacade()
    return _facade_instance
