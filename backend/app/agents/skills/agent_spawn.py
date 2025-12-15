# M12 Agent Spawn Skill
# Spawns parallel worker agents for job execution
#
# Credit cost: 5 credits
# M15.1: SBA validation at spawn time

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

from ..services.job_service import JobService, JobConfig, get_job_service
from ..services.registry_service import RegistryService, get_registry_service
from ..services.credit_service import CreditService, get_credit_service, CREDIT_COSTS

# M15.1: SBA imports
try:
    from ..sba.service import SBAService, get_sba_service
    SBA_AVAILABLE = True
except ImportError:
    SBA_AVAILABLE = False
    SBAService = None

logger = logging.getLogger("nova.agents.skills.agent_spawn")

# Environment flag to enforce SBA validation (default: True in production)
SBA_ENFORCE = os.environ.get("SBA_ENFORCE", "true").lower() == "true"
SBA_AUTO_GENERATE = os.environ.get("SBA_AUTO_GENERATE", "true").lower() == "true"


class AgentSpawnInput(BaseModel):
    """Input schema for agent_spawn skill."""
    orchestrator_agent: str = Field(..., description="Orchestrator agent type")
    worker_agent: str = Field(..., description="Worker agent type to spawn")
    task: str = Field(..., description="Task name/description")
    items: List[Any] = Field(..., description="Items to process in parallel")
    parallelism: int = Field(default=10, ge=1, le=100, description="Max parallel workers")
    timeout_per_item: int = Field(default=60, ge=1, le=3600, description="Timeout per item in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Max retries per item")

    # M15: LLM Governance parameters
    llm_budget_cents: Optional[int] = Field(
        default=None,
        description="Total LLM budget in cents for this job (None = unlimited)"
    )
    llm_budget_per_item: Optional[int] = Field(
        default=None,
        description="LLM budget per item in cents (auto-calculated from total if not set)"
    )
    llm_risk_threshold: float = Field(
        default=0.6,
        ge=0.0, le=1.0,
        description="Risk score threshold for blocking (0.6 = moderate)"
    )
    llm_max_temperature: float = Field(
        default=1.0,
        ge=0.0, le=2.0,
        description="Max temperature allowed for LLM calls"
    )
    llm_enforce_safety: bool = Field(
        default=True,
        description="Whether to block high-risk LLM outputs"
    )


class AgentSpawnOutput(BaseModel):
    """Output schema for agent_spawn skill."""
    success: bool
    job_id: Optional[str] = None
    orchestrator_instance_id: Optional[str] = None
    total_items: int = 0
    credits_reserved: float = 0
    error: Optional[str] = None

    # M15: LLM Budget info
    llm_budget_cents: Optional[int] = None
    llm_budget_per_item: Optional[int] = None


class AgentSpawnSkill:
    """
    Skill to spawn parallel worker agents.

    Creates a job with items, registers the orchestrator,
    and returns job context for worker coordination.

    Credit cost: 5 credits + 2 per item

    M15.1: Enforces SBA validation before spawn.
    """

    SKILL_ID = "agent_spawn"
    SKILL_VERSION = "1.1.0"  # Bumped for M15.1 SBA enforcement
    CREDIT_COST = CREDIT_COSTS["agent_spawn"]

    def __init__(
        self,
        job_service: Optional[JobService] = None,
        registry_service: Optional[RegistryService] = None,
        credit_service: Optional[CreditService] = None,
        sba_service: Optional["SBAService"] = None,
    ):
        self.job_service = job_service or get_job_service()
        self.registry_service = registry_service or get_registry_service()
        self.credit_service = credit_service or get_credit_service()

        # M15.1: SBA service for strategy cascade validation
        if SBA_AVAILABLE:
            self.sba_service = sba_service or get_sba_service()
        else:
            self.sba_service = None

    def execute(
        self,
        input_data: AgentSpawnInput,
        tenant_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentSpawnOutput:
        """
        Execute agent_spawn skill.

        Args:
            input_data: Spawn parameters
            tenant_id: Tenant for billing
            context: Optional execution context

        Returns:
            AgentSpawnOutput with job details
        """
        try:
            # M15.1: Validate SBA for both orchestrator and worker agents
            if SBA_ENFORCE and self.sba_service:
                # Build config for auto-generation
                spawn_config = {
                    "task": input_data.task,
                    "parallelism": input_data.parallelism,
                    "timeout_per_item": input_data.timeout_per_item,
                    "max_retries": input_data.max_retries,
                    "llm_budget_cents": input_data.llm_budget_cents,
                    "llm_risk_threshold": input_data.llm_risk_threshold,
                }

                # Validate orchestrator SBA
                orch_allowed, orch_error = self.sba_service.check_spawn_allowed(
                    agent_id=input_data.orchestrator_agent,
                    auto_generate=SBA_AUTO_GENERATE,
                    orchestrator="system",
                    config={"role": "orchestrator", **spawn_config},
                )
                if not orch_allowed:
                    return AgentSpawnOutput(
                        success=False,
                        error=f"AGENT_INVALID_SBA_SCHEMA: Orchestrator '{input_data.orchestrator_agent}' - {orch_error}",
                    )

                # Validate worker SBA
                worker_allowed, worker_error = self.sba_service.check_spawn_allowed(
                    agent_id=input_data.worker_agent,
                    auto_generate=SBA_AUTO_GENERATE,
                    orchestrator=input_data.orchestrator_agent,
                    config={"role": "worker", **spawn_config},
                )
                if not worker_allowed:
                    return AgentSpawnOutput(
                        success=False,
                        error=f"AGENT_INVALID_SBA_SCHEMA: Worker '{input_data.worker_agent}' - {worker_error}",
                    )

                logger.info(
                    "sba_validation_passed",
                    extra={
                        "orchestrator": input_data.orchestrator_agent,
                        "worker": input_data.worker_agent,
                    }
                )

            # Register orchestrator
            reg_result = self.registry_service.register(
                agent_id=input_data.orchestrator_agent,
                capabilities={"role": "orchestrator", "task": input_data.task},
            )

            if not reg_result.success:
                return AgentSpawnOutput(
                    success=False,
                    error=f"Orchestrator registration failed: {reg_result.error}",
                )

            orchestrator_instance_id = reg_result.instance_id

            # M15: Calculate per-item budget if total budget provided
            llm_budget_per_item = input_data.llm_budget_per_item
            if input_data.llm_budget_cents and not llm_budget_per_item:
                # Distribute budget across items
                llm_budget_per_item = input_data.llm_budget_cents // len(input_data.items)

            # Create job config
            job_config = JobConfig(
                orchestrator_agent=input_data.orchestrator_agent,
                worker_agent=input_data.worker_agent,
                task=input_data.task,
                items=input_data.items,
                parallelism=input_data.parallelism,
                timeout_per_item=input_data.timeout_per_item,
                max_retries=input_data.max_retries,
                # M15: LLM Governance
                llm_budget_cents=input_data.llm_budget_cents,
                llm_budget_per_item=llm_budget_per_item,
                llm_risk_threshold=input_data.llm_risk_threshold,
                llm_max_temperature=input_data.llm_max_temperature,
                llm_enforce_safety=input_data.llm_enforce_safety,
            )

            # Create job (includes credit reservation)
            job = self.job_service.create_job(
                config=job_config,
                orchestrator_instance_id=orchestrator_instance_id,
                tenant_id=tenant_id,
            )

            # Update orchestrator with job_id
            self.registry_service.register(
                agent_id=input_data.orchestrator_agent,
                instance_id=orchestrator_instance_id,
                job_id=job.id,
            )

            logger.info(
                "agent_spawn_success",
                extra={
                    "job_id": str(job.id),
                    "orchestrator_instance_id": orchestrator_instance_id,
                    "task": input_data.task,
                    "item_count": len(input_data.items),
                    "parallelism": input_data.parallelism,
                    "credits_reserved": float(job.credits.reserved),
                    # M15
                    "llm_budget_cents": input_data.llm_budget_cents,
                    "llm_budget_per_item": llm_budget_per_item,
                }
            )

            return AgentSpawnOutput(
                success=True,
                job_id=str(job.id),
                orchestrator_instance_id=orchestrator_instance_id,
                total_items=len(input_data.items),
                credits_reserved=float(job.credits.reserved),
                # M15
                llm_budget_cents=input_data.llm_budget_cents,
                llm_budget_per_item=llm_budget_per_item,
            )

        except RuntimeError as e:
            # Credit or validation error
            logger.warning(f"agent_spawn failed: {e}")
            return AgentSpawnOutput(
                success=False,
                error=str(e),
            )

        except Exception as e:
            logger.error(f"agent_spawn error: {e}", exc_info=True)
            return AgentSpawnOutput(
                success=False,
                error=f"Internal error: {str(e)[:100]}",
            )

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for skill."""
        return {
            "skill_id": self.SKILL_ID,
            "version": self.SKILL_VERSION,
            "description": "Spawn parallel worker agents for job execution",
            "credit_cost": float(self.CREDIT_COST),
            "input_schema": AgentSpawnInput.model_json_schema(),
            "output_schema": AgentSpawnOutput.model_json_schema(),
        }
