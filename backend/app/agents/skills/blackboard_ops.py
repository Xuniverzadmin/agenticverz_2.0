# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: sync
# Role: Blackboard read/write operations skill
# Callers: agent runtime, workers
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Agent Skills

# M12 Blackboard Operation Skills
# Read, write, and lock operations on shared blackboard
#
# Credit costs:
# - blackboard_read: 1 credit
# - blackboard_write: 1 credit
# - blackboard_lock: 2 credits

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..services.blackboard_service import BlackboardService, get_blackboard_service
from ..services.credit_service import CREDIT_COSTS, CreditService, get_credit_service

logger = logging.getLogger("nova.agents.skills.blackboard_ops")


# ============ Blackboard Read Skill ============


class BlackboardReadInput(BaseModel):
    """Input schema for blackboard_read skill."""

    key: str = Field(..., description="Key to read")
    pattern: Optional[str] = Field(default=None, description="Optional pattern for scan (e.g., 'job:*:result')")
    max_results: int = Field(default=100, ge=1, le=1000, description="Max results for pattern scan")


class BlackboardReadOutput(BaseModel):
    """Output schema for blackboard_read skill."""

    success: bool
    value: Optional[Any] = None
    values: Optional[List[Dict[str, Any]]] = None  # For pattern reads
    found: bool = False
    error: Optional[str] = None


class BlackboardReadSkill:
    """
    Read values from shared blackboard.

    Supports single key reads and pattern scans.

    Credit cost: 1 credit
    """

    SKILL_ID = "blackboard_read"
    SKILL_VERSION = "1.0.0"
    CREDIT_COST = CREDIT_COSTS["blackboard_read"]

    def __init__(
        self,
        blackboard_service: Optional[BlackboardService] = None,
        credit_service: Optional[CreditService] = None,
    ):
        self.blackboard_service = blackboard_service or get_blackboard_service()
        self.credit_service = credit_service or get_credit_service()

    def execute(
        self,
        input_data: BlackboardReadInput,
        tenant_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
    ) -> BlackboardReadOutput:
        """Execute blackboard_read skill."""
        try:
            # Charge credits
            self.credit_service.charge_skill("blackboard_read", tenant_id)

            if input_data.pattern:
                # Pattern scan
                entries = self.blackboard_service.scan_pattern(
                    pattern=input_data.pattern,
                    count=input_data.max_results,
                )
                return BlackboardReadOutput(
                    success=True,
                    values=[{"key": e.key, "value": e.value, "ttl": e.ttl} for e in entries],
                    found=len(entries) > 0,
                )
            else:
                # Single key read
                value = self.blackboard_service.get(input_data.key)
                return BlackboardReadOutput(
                    success=True,
                    value=value,
                    found=value is not None,
                )

        except Exception as e:
            logger.error(f"blackboard_read error: {e}")
            return BlackboardReadOutput(
                success=False,
                error=str(e)[:200],
            )

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for skill."""
        return {
            "skill_id": self.SKILL_ID,
            "version": self.SKILL_VERSION,
            "description": "Read values from shared blackboard",
            "credit_cost": float(self.CREDIT_COST),
            "input_schema": BlackboardReadInput.model_json_schema(),
            "output_schema": BlackboardReadOutput.model_json_schema(),
        }


# ============ Blackboard Write Skill ============


class BlackboardWriteInput(BaseModel):
    """Input schema for blackboard_write skill."""

    key: str = Field(..., description="Key to write")
    value: Any = Field(..., description="Value to store")
    ttl: Optional[int] = Field(default=None, ge=1, le=86400, description="TTL in seconds")
    increment: Optional[int] = Field(default=None, description="Atomic increment amount (ignores value)")


class BlackboardWriteOutput(BaseModel):
    """Output schema for blackboard_write skill."""

    success: bool
    new_value: Optional[Any] = None  # For increments
    error: Optional[str] = None


class BlackboardWriteSkill:
    """
    Write values to shared blackboard.

    Supports set, set with TTL, and atomic increment.

    Credit cost: 1 credit
    """

    SKILL_ID = "blackboard_write"
    SKILL_VERSION = "1.0.0"
    CREDIT_COST = CREDIT_COSTS["blackboard_write"]

    def __init__(
        self,
        blackboard_service: Optional[BlackboardService] = None,
        credit_service: Optional[CreditService] = None,
    ):
        self.blackboard_service = blackboard_service or get_blackboard_service()
        self.credit_service = credit_service or get_credit_service()

    def execute(
        self,
        input_data: BlackboardWriteInput,
        tenant_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
    ) -> BlackboardWriteOutput:
        """Execute blackboard_write skill."""
        try:
            # Charge credits
            self.credit_service.charge_skill("blackboard_write", tenant_id)

            if input_data.increment is not None:
                # Atomic increment
                new_value = self.blackboard_service.increment(
                    key=input_data.key,
                    amount=input_data.increment,
                )
                return BlackboardWriteOutput(
                    success=new_value is not None,
                    new_value=new_value,
                )
            else:
                # Regular set
                success = self.blackboard_service.set(
                    key=input_data.key,
                    value=input_data.value,
                    ttl=input_data.ttl,
                )
                return BlackboardWriteOutput(success=success)

        except Exception as e:
            logger.error(f"blackboard_write error: {e}")
            return BlackboardWriteOutput(
                success=False,
                error=str(e)[:200],
            )

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for skill."""
        return {
            "skill_id": self.SKILL_ID,
            "version": self.SKILL_VERSION,
            "description": "Write values to shared blackboard",
            "credit_cost": float(self.CREDIT_COST),
            "input_schema": BlackboardWriteInput.model_json_schema(),
            "output_schema": BlackboardWriteOutput.model_json_schema(),
        }


# ============ Blackboard Lock Skill ============


class BlackboardLockInput(BaseModel):
    """Input schema for blackboard_lock skill."""

    key: str = Field(..., description="Lock name")
    holder: str = Field(..., description="Lock holder identity")
    action: str = Field(default="acquire", description="Action: acquire, release, extend")
    ttl: int = Field(default=30, ge=1, le=300, description="Lock TTL in seconds")


class BlackboardLockOutput(BaseModel):
    """Output schema for blackboard_lock skill."""

    success: bool
    acquired: Optional[bool] = None
    released: Optional[bool] = None
    extended: Optional[bool] = None
    current_holder: Optional[str] = None
    error: Optional[str] = None


class BlackboardLockSkill:
    """
    Distributed lock operations on blackboard.

    Supports acquire (SET NX), release, and extend.

    Credit cost: 2 credits
    """

    SKILL_ID = "blackboard_lock"
    SKILL_VERSION = "1.0.0"
    CREDIT_COST = CREDIT_COSTS["blackboard_lock"]

    def __init__(
        self,
        blackboard_service: Optional[BlackboardService] = None,
        credit_service: Optional[CreditService] = None,
    ):
        self.blackboard_service = blackboard_service or get_blackboard_service()
        self.credit_service = credit_service or get_credit_service()

    def execute(
        self,
        input_data: BlackboardLockInput,
        tenant_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
    ) -> BlackboardLockOutput:
        """Execute blackboard_lock skill."""
        try:
            # Charge credits
            self.credit_service.charge_skill("blackboard_lock", tenant_id)

            if input_data.action == "acquire":
                result = self.blackboard_service.acquire_lock(
                    key=input_data.key,
                    holder=input_data.holder,
                    ttl=input_data.ttl,
                )
                return BlackboardLockOutput(
                    success=result.acquired,
                    acquired=result.acquired,
                    current_holder=result.holder,
                )

            elif input_data.action == "release":
                released = self.blackboard_service.release_lock(
                    key=input_data.key,
                    holder=input_data.holder,
                )
                return BlackboardLockOutput(
                    success=released,
                    released=released,
                )

            elif input_data.action == "extend":
                extended = self.blackboard_service.extend_lock(
                    key=input_data.key,
                    holder=input_data.holder,
                    ttl=input_data.ttl,
                )
                return BlackboardLockOutput(
                    success=extended,
                    extended=extended,
                )

            else:
                return BlackboardLockOutput(
                    success=False,
                    error=f"Unknown action: {input_data.action}",
                )

        except Exception as e:
            logger.error(f"blackboard_lock error: {e}")
            return BlackboardLockOutput(
                success=False,
                error=str(e)[:200],
            )

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for skill."""
        return {
            "skill_id": self.SKILL_ID,
            "version": self.SKILL_VERSION,
            "description": "Distributed lock operations",
            "credit_cost": float(self.CREDIT_COST),
            "input_schema": BlackboardLockInput.model_json_schema(),
            "output_schema": BlackboardLockOutput.model_json_schema(),
        }
