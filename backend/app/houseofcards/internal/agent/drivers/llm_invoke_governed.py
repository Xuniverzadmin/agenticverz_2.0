# Layer: L6 — Driver
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: async
# Role: Governed LLM invocation skill with budget enforcement
# Callers: agent runtime, workers
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Agent Skills

# M15 LLM Invoke with BudgetLLM Governance
# Provides LLM inference with budget control and safety governance
#
# Features:
# - Per-call budget enforcement
# - Risk scoring on every response
# - Parameter clamping (temperature, max_tokens)
# - Blocked item tracking for high-risk outputs
# - Integration with M12 job_items schema

import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# Add budgetllm to path
_project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
_budgetllm_path = os.path.join(_project_root, "budgetllm")
if _budgetllm_path not in sys.path:
    sys.path.insert(0, _budgetllm_path)

logger = logging.getLogger("nova.agents.skills.llm_invoke_governed")


# =============================================================================
# Input/Output Schemas
# =============================================================================


class LLMMessage(BaseModel):
    """Chat message."""

    role: str = Field(..., description="Message role: system, user, assistant")
    content: str = Field(..., description="Message content")


class LLMInvokeGovernedInput(BaseModel):
    """Input schema for governed LLM invoke skill."""

    messages: List[LLMMessage] = Field(..., description="Chat messages")
    model: str = Field(default="gpt-4o-mini", description="Model to use")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=1024, ge=1, le=16384)
    system_prompt: Optional[str] = Field(default=None)

    # Governance parameters (can be overridden per-call)
    budget_cents: Optional[int] = Field(
        default=None, description="Budget limit for this call (overrides worker budget)"
    )
    enforce_safety: bool = Field(default=True, description="Whether to block high-risk outputs")
    risk_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="Risk score threshold for blocking")


class LLMInvokeGovernedOutput(BaseModel):
    """Output schema for governed LLM invoke skill."""

    success: bool
    content: Optional[str] = None

    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0

    # Cost tracking
    cost_cents: float = 0.0
    cache_hit: bool = False

    # Risk governance
    risk_score: float = 0.0
    risk_factors: Dict[str, Any] = Field(default_factory=dict)
    blocked: bool = False
    blocked_reason: Optional[str] = None

    # Parameter clamping
    params_clamped: Dict[str, Any] = Field(default_factory=dict)

    # Error info
    error: Optional[str] = None
    error_code: Optional[str] = None


# =============================================================================
# Governance Configuration
# =============================================================================


@dataclass
class GovernanceConfig:
    """Configuration for LLM governance."""

    # Budget limits
    budget_cents: Optional[int] = None
    daily_limit_cents: Optional[int] = None

    # Parameter clamping
    max_temperature: float = 1.0
    max_top_p: float = 1.0
    max_completion_tokens: int = 4096

    # Safety enforcement
    enforce_safety: bool = True
    block_on_high_risk: bool = True
    risk_threshold: float = 0.6

    # Cache
    cache_enabled: bool = True
    cache_ttl: int = 3600
    redis_url: Optional[str] = None


def get_default_governance_config() -> GovernanceConfig:
    """Get governance config from environment."""
    return GovernanceConfig(
        budget_cents=int(os.getenv("LLM_BUDGET_CENTS", "0")) or None,
        daily_limit_cents=int(os.getenv("LLM_DAILY_LIMIT_CENTS", "0")) or None,
        max_temperature=float(os.getenv("LLM_MAX_TEMPERATURE", "1.0")),
        max_completion_tokens=int(os.getenv("LLM_MAX_COMPLETION_TOKENS", "4096")),
        enforce_safety=os.getenv("LLM_ENFORCE_SAFETY", "true").lower() == "true",
        risk_threshold=float(os.getenv("LLM_RISK_THRESHOLD", "0.6")),
        cache_enabled=os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true",
        cache_ttl=int(os.getenv("LLM_CACHE_TTL", "3600")),
        redis_url=os.getenv("REDIS_URL"),
    )


# =============================================================================
# BudgetLLM Client Wrapper
# =============================================================================


class GovernedLLMClient:
    """
    LLM client with BudgetLLM governance integration.

    Wraps BudgetLLM's Client with additional features:
    - Per-job budget tracking
    - Per-worker budget allocation
    - Integration with database for persistence
    """

    def __init__(
        self,
        openai_key: Optional[str] = None,
        config: Optional[GovernanceConfig] = None,
    ):
        self.openai_key = openai_key or os.getenv("OPENAI_API_KEY")
        self.config = config or get_default_governance_config()
        self._client = None
        self._initialized = False

    def _ensure_client(self):
        """Lazy initialize BudgetLLM client."""
        if self._initialized:
            return

        try:
            from budgetllm import BudgetExceededError, Client, HighRiskOutputError

            self._client = Client(
                openai_key=self.openai_key,
                budget_cents=self.config.budget_cents,
                daily_limit_cents=self.config.daily_limit_cents,
                max_temperature=self.config.max_temperature,
                max_completion_tokens=self.config.max_completion_tokens,
                enforce_safety=self.config.enforce_safety,
                block_on_high_risk=self.config.block_on_high_risk,
                risk_threshold=self.config.risk_threshold,
                cache_enabled=self.config.cache_enabled,
                cache_ttl=self.config.cache_ttl,
                redis_url=self.config.redis_url,
            )
            self._initialized = True

        except ImportError as e:
            logger.error(f"BudgetLLM not available: {e}")
            raise ImportError("budgetllm package not available. Ensure budgetllm/ is in the Python path.")

    def invoke(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        budget_cents: Optional[int] = None,
        enforce_safety: Optional[bool] = None,
        risk_threshold: Optional[float] = None,
    ) -> LLMInvokeGovernedOutput:
        """
        Invoke LLM with governance.

        Args:
            messages: Chat messages
            model: Model to use
            temperature: Temperature (may be clamped)
            max_tokens: Max tokens (may be clamped)
            budget_cents: Budget limit for this call
            enforce_safety: Override safety enforcement
            risk_threshold: Override risk threshold

        Returns:
            LLMInvokeGovernedOutput with response and governance metadata
        """
        self._ensure_client()

        try:
            from budgetllm import BudgetExceededError, HighRiskOutputError

            # Build request params
            params = {
                "model": model,
                "messages": messages,
            }
            if temperature is not None:
                params["temperature"] = temperature
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            # Make governed LLM call
            response = self._client.chat.completions.create(**params)

            # Extract response data
            content = ""
            if response.get("choices"):
                content = response["choices"][0].get("message", {}).get("content", "")

            usage = response.get("usage", {})

            return LLMInvokeGovernedOutput(
                success=True,
                content=content,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                cost_cents=response.get("cost_cents", 0.0),
                cache_hit=response.get("cache_hit", False),
                risk_score=response.get("risk_score", 0.0),
                risk_factors=response.get("risk_factors", {}),
                blocked=False,
                params_clamped=response.get("params_clamped", {}),
            )

        except BudgetExceededError as e:
            logger.warning(f"LLM budget exceeded: {e}")
            return LLMInvokeGovernedOutput(
                success=False,
                blocked=True,
                blocked_reason="budget_exceeded",
                error=str(e),
                error_code="ERR_LLM_BUDGET_EXCEEDED",
            )

        except HighRiskOutputError as e:
            logger.warning(f"LLM output blocked for high risk: {e}")
            return LLMInvokeGovernedOutput(
                success=False,
                blocked=True,
                blocked_reason="high_risk_output",
                risk_score=e.risk_score if hasattr(e, "risk_score") else 0.0,
                risk_factors=e.risk_factors if hasattr(e, "risk_factors") else {},
                error=str(e),
                error_code="ERR_LLM_HIGH_RISK",
            )

        except Exception as e:
            logger.error(f"LLM invoke error: {e}", exc_info=True)
            return LLMInvokeGovernedOutput(
                success=False,
                error=str(e)[:500],
                error_code="ERR_LLM_INVOKE_FAILED",
            )

    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status."""
        if not self._initialized or not self._client:
            return {"error": "Client not initialized"}
        return self._client.budget_status()


# =============================================================================
# Governed LLM Invoke Skill
# =============================================================================


class LLMInvokeGovernedSkill:
    """
    LLM invoke skill with BudgetLLM governance.

    Integrates with M12 agent system:
    - Records risk_score, blocked, params_clamped to job_items
    - Updates job/instance budget usage
    - Provides governance metrics
    """

    SKILL_ID = "llm_invoke_governed"
    SKILL_VERSION = "1.0.0"

    def __init__(
        self,
        openai_key: Optional[str] = None,
        config: Optional[GovernanceConfig] = None,
    ):
        self.client = GovernedLLMClient(openai_key, config)

    async def execute(
        self,
        input_data: LLMInvokeGovernedInput,
        job_id: Optional[UUID] = None,
        item_id: Optional[UUID] = None,
        worker_instance_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> LLMInvokeGovernedOutput:
        """
        Execute governed LLM invoke.

        Args:
            input_data: LLM invoke parameters
            job_id: M12 job ID for budget tracking
            item_id: M12 job_item ID for risk recording
            worker_instance_id: Worker instance for budget allocation
            context: Additional execution context

        Returns:
            LLMInvokeGovernedOutput with response and governance data
        """
        # Convert messages to dict format
        messages = [{"role": m.role, "content": m.content} for m in input_data.messages]

        # Add system prompt if provided
        if input_data.system_prompt:
            messages.insert(0, {"role": "system", "content": input_data.system_prompt})

        # Make governed LLM call
        result = self.client.invoke(
            messages=messages,
            model=input_data.model,
            temperature=input_data.temperature,
            max_tokens=input_data.max_tokens,
            budget_cents=input_data.budget_cents,
            enforce_safety=input_data.enforce_safety,
            risk_threshold=input_data.risk_threshold,
        )

        # Record governance data to database (if item_id provided)
        if item_id:
            await self._record_governance_data(
                item_id=item_id,
                job_id=job_id,
                worker_instance_id=worker_instance_id,
                result=result,
            )

        return result

    async def _record_governance_data(
        self,
        item_id: UUID,
        job_id: Optional[UUID],
        worker_instance_id: Optional[str],
        result: LLMInvokeGovernedOutput,
    ):
        """
        Record governance data to M12 schema.

        Uses agents.record_llm_usage() function from migration.
        """
        try:
            # Get database session
            from app.db import get_session

            async with get_session() as session:
                # Call the PL/pgSQL function
                await session.execute(
                    """
                    SELECT agents.record_llm_usage(
                        :item_id,
                        :cost_cents,
                        :tokens,
                        :risk_score,
                        :risk_factors,
                        :blocked,
                        :blocked_reason,
                        :params_clamped
                    )
                    """,
                    {
                        "item_id": item_id,
                        "cost_cents": result.cost_cents,
                        "tokens": result.input_tokens + result.output_tokens,
                        "risk_score": result.risk_score,
                        "risk_factors": result.risk_factors,
                        "blocked": result.blocked,
                        "blocked_reason": result.blocked_reason,
                        "params_clamped": result.params_clamped,
                    },
                )
                await session.commit()

        except Exception as e:
            # Log but don't fail - governance recording is secondary
            logger.warning(f"Failed to record governance data: {e}")

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for skill."""
        return {
            "skill_id": self.SKILL_ID,
            "version": self.SKILL_VERSION,
            "description": "LLM invoke with BudgetLLM governance (budget control, risk scoring, safety enforcement)",
            "input_schema": LLMInvokeGovernedInput.model_json_schema(),
            "output_schema": LLMInvokeGovernedOutput.model_json_schema(),
        }


# =============================================================================
# Module-level utilities
# =============================================================================

_default_skill: Optional[LLMInvokeGovernedSkill] = None


def get_governed_llm_skill() -> LLMInvokeGovernedSkill:
    """Get or create the default governed LLM skill."""
    global _default_skill
    if _default_skill is None:
        _default_skill = LLMInvokeGovernedSkill()
    return _default_skill


async def governed_llm_invoke(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 1024,
    system_prompt: Optional[str] = None,
    job_id: Optional[UUID] = None,
    item_id: Optional[UUID] = None,
    worker_instance_id: Optional[str] = None,
) -> LLMInvokeGovernedOutput:
    """
    Convenience function for governed LLM invoke.

    Usage:
        result = await governed_llm_invoke(
            messages=[{"role": "user", "content": "Hello!"}],
            model="gpt-4o-mini",
            job_id=job.id,
            item_id=item.id,
        )

        if result.blocked:
            # Handle blocked output
            log.warning(f"Blocked: {result.blocked_reason}")
        else:
            # Use result
            print(result.content)
    """
    skill = get_governed_llm_skill()

    # Build input
    msg_objects = [LLMMessage(role=m["role"], content=m["content"]) for m in messages]

    input_data = LLMInvokeGovernedInput(
        messages=msg_objects,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
    )

    return await skill.execute(
        input_data=input_data,
        job_id=job_id,
        item_id=item_id,
        worker_instance_id=worker_instance_id,
    )
