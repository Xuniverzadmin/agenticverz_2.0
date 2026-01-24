# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Policy intent model and declaration
# Callers: policy engine, evaluators
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Policy System

# M20 Policy Runtime - Intent System
# M18 intent emission for governance-aware execution
"""
Intent system for PLang v2.0 runtime.

Intents are the bridge between policy decisions and M18 execution:
- Policy compiler emits intents based on actions
- M18 executes intents with governance constraints
- M19 validates intents before execution

Intent types:
- ROUTE: Route to specific agent
- ESCALATE: Escalate to higher authority
- EXECUTE: Execute with constraints
- DENY: Block execution with reason
- ALLOW: Permit execution
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class IntentType(Enum):
    """Types of intents emitted by policy runtime."""

    ROUTE = auto()  # Route to agent
    ESCALATE = auto()  # Escalate for approval
    EXECUTE = auto()  # Execute action
    DENY = auto()  # Deny request
    ALLOW = auto()  # Allow request
    LOG = auto()  # Audit log only
    ALERT = auto()  # Alert without blocking


@dataclass
class IntentPayload:
    """
    Payload data for an intent.

    Contains all data needed for M18 to execute the intent.
    """

    # Target information
    target_agent: Optional[str] = None
    target_skill: Optional[str] = None

    # Request data
    request_id: Optional[str] = None
    user_id: Optional[str] = None

    # Constraints
    budget_limit: Optional[float] = None
    time_limit_ms: Optional[int] = None
    retry_limit: int = 3

    # Context
    context: Dict[str, Any] = field(default_factory=dict)

    # Reason (for DENY/ESCALATE)
    reason: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "target_agent": self.target_agent,
            "target_skill": self.target_skill,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "budget_limit": self.budget_limit,
            "time_limit_ms": self.time_limit_ms,
            "retry_limit": self.retry_limit,
            "context": self.context,
            "reason": self.reason,
            "alternatives": self.alternatives,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntentPayload":
        """Create from dictionary."""
        return cls(
            target_agent=data.get("target_agent"),
            target_skill=data.get("target_skill"),
            request_id=data.get("request_id"),
            user_id=data.get("user_id"),
            budget_limit=data.get("budget_limit"),
            time_limit_ms=data.get("time_limit_ms"),
            retry_limit=data.get("retry_limit", 3),
            context=data.get("context", {}),
            reason=data.get("reason"),
            alternatives=data.get("alternatives", []),
        )


@dataclass
class Intent:
    """
    An intent emitted by the policy runtime.

    Represents a governance-validated action to be executed by M18.
    """

    id: str
    intent_type: IntentType
    payload: IntentPayload
    priority: int = 50
    requires_confirmation: bool = False

    # Governance metadata
    source_policy: Optional[str] = None
    source_rule: Optional[str] = None
    category: Optional[str] = None

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None

    # Status
    validated: bool = False
    validation_errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate deterministic intent ID."""
        content = json.dumps(
            {
                "type": self.intent_type.name,
                "payload": self.payload.to_dict(),
                "policy": self.source_policy,
                "rule": self.source_rule,
            },
            sort_keys=True,
        )
        return f"int_{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for M18 consumption."""
        return {
            "id": self.id,
            "type": self.intent_type.name,
            "payload": self.payload.to_dict(),
            "priority": self.priority,
            "requires_confirmation": self.requires_confirmation,
            "governance": {
                "source_policy": self.source_policy,
                "source_rule": self.source_rule,
                "category": self.category,
            },
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "validated": self.validated,
            "validation_errors": self.validation_errors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Intent":
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            intent_type=IntentType[data["type"]],
            payload=IntentPayload.from_dict(data.get("payload", {})),
            priority=data.get("priority", 50),
            requires_confirmation=data.get("requires_confirmation", False),
            source_policy=data.get("governance", {}).get("source_policy"),
            source_rule=data.get("governance", {}).get("source_rule"),
            category=data.get("governance", {}).get("category"),
            created_at=data.get("created_at", ""),
            expires_at=data.get("expires_at"),
            validated=data.get("validated", False),
            validation_errors=data.get("validation_errors", []),
        )


class IntentEmitter:
    """
    Emits intents from policy runtime to M18.

    Handles:
    - Intent creation
    - M19 validation
    - M18 delivery
    - Audit logging
    """

    def __init__(self):
        self.pending_intents: List[Intent] = []
        self.emitted_intents: List[Intent] = []
        self._intent_handlers: Dict[IntentType, List[callable]] = {t: [] for t in IntentType}

    def create_intent(
        self,
        intent_type: IntentType,
        payload: Optional[IntentPayload] = None,
        priority: int = 50,
        source_policy: Optional[str] = None,
        source_rule: Optional[str] = None,
        category: Optional[str] = None,
        requires_confirmation: bool = False,
    ) -> Intent:
        """
        Create a new intent.

        Args:
            intent_type: Type of intent
            payload: Intent payload data
            priority: Execution priority
            source_policy: Policy that generated this intent
            source_rule: Rule that generated this intent
            category: Governance category
            requires_confirmation: Whether intent needs confirmation

        Returns:
            Created intent
        """
        intent = Intent(
            id="",  # Will be generated
            intent_type=intent_type,
            payload=payload or IntentPayload(),
            priority=priority,
            requires_confirmation=requires_confirmation,
            source_policy=source_policy,
            source_rule=source_rule,
            category=category,
        )

        self.pending_intents.append(intent)
        return intent

    async def validate_intent(self, intent: Intent) -> bool:
        """
        Validate intent against M19 policy engine.

        Args:
            intent: Intent to validate

        Returns:
            True if valid, False otherwise
        """
        errors: List[str] = []

        # Basic validation
        if not intent.intent_type:
            errors.append("Intent type is required")

        # ESCALATE requires target or reason
        if intent.intent_type == IntentType.ESCALATE:
            if not intent.payload.target_agent and not intent.payload.reason:
                errors.append("ESCALATE intent requires target_agent or reason")
            intent.requires_confirmation = True

        # ROUTE requires target
        if intent.intent_type == IntentType.ROUTE:
            if not intent.payload.target_agent:
                errors.append("ROUTE intent requires target_agent")

        # DENY requires reason
        if intent.intent_type == IntentType.DENY:
            if not intent.payload.reason:
                errors.append("DENY intent requires reason")

        # TODO: Call M19 policy engine for full validation
        # result = await policy_engine.validate_intent(intent)
        # if not result.allowed:
        #     errors.extend(result.errors)

        intent.validation_errors = errors
        intent.validated = len(errors) == 0
        return intent.validated

    async def emit(self, intent: Intent) -> bool:
        """
        Emit a validated intent to M18.

        Args:
            intent: Intent to emit

        Returns:
            True if successfully emitted
        """
        if not intent.validated:
            is_valid = await self.validate_intent(intent)
            if not is_valid:
                return False

        # Remove from pending
        if intent in self.pending_intents:
            self.pending_intents.remove(intent)

        # Call handlers
        handlers = self._intent_handlers.get(intent.intent_type, [])
        for handler in handlers:
            try:
                await handler(intent)
            except Exception as e:
                intent.validation_errors.append(f"Handler error: {e}")
                return False

        # Add to emitted
        self.emitted_intents.append(intent)

        # TODO: Send to M18 via message queue or direct call
        # await m18_client.emit_intent(intent.to_dict())

        return True

    async def emit_all(self) -> List[Intent]:
        """
        Emit all pending intents.

        Returns:
            List of successfully emitted intents
        """
        emitted = []
        for intent in list(self.pending_intents):
            if await self.emit(intent):
                emitted.append(intent)
        return emitted

    def register_handler(self, intent_type: IntentType, handler: Callable[..., Any]) -> None:
        """
        Register a handler for an intent type.

        Args:
            intent_type: Type of intent to handle
            handler: Async function to call when intent is emitted
        """
        self._intent_handlers[intent_type].append(handler)

    def get_pending(self) -> List[Intent]:
        """Get all pending intents."""
        return list(self.pending_intents)

    def get_emitted(self) -> List[Intent]:
        """Get all emitted intents."""
        return list(self.emitted_intents)

    def clear(self) -> None:
        """Clear all intents."""
        self.pending_intents.clear()
        self.emitted_intents.clear()
