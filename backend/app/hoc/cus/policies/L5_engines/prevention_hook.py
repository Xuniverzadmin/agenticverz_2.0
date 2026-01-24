# Layer: L5 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Prevention hook for policy enforcement
# Callers: workers, execution runtime
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5
# Reference: Policy System

# M23 Prevention Hook
# Pre-response and post-response hooks for policy enforcement
#
# This module provides hooks that can be called:
# 1. BEFORE sending response to client (post-LLM, pre-delivery)
# 2. AFTER response delivery (for async audit)
#
# The key prevention mechanism for CONTENT_ACCURACY:
# - Validate LLM output against context data
# - Block responses that make unsupported assertions
# - Log policy violations for incident creation

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from app.policy.validators.content_accuracy import (
    ContentAccuracyValidator,
    ValidationResult,
)


class PreventionAction(str, Enum):
    """Action to take when prevention hook triggers."""

    ALLOW = "allow"  # Let response through
    BLOCK = "block"  # Block response completely
    MODIFY = "modify"  # Modify response before delivery
    WARN = "warn"  # Allow but log warning
    ESCALATE = "escalate"  # Require human approval


@dataclass
class PreventionContext:
    """Context for prevention hook evaluation."""

    tenant_id: str
    call_id: str
    user_id: Optional[str]
    model: str

    # Request data
    user_query: str
    system_prompt: Optional[str]

    # Context data (from RAG, database, etc.)
    context_data: Dict[str, Any]

    # LLM response
    llm_output: str
    output_tokens: int

    # Metadata
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class PreventionResult:
    """Result of prevention hook evaluation."""

    action: PreventionAction
    policy: str  # Which policy triggered
    result: str  # PASS/FAIL/WARN
    reason: Optional[str]
    modified_output: Optional[str]  # If action is MODIFY

    # For incident creation
    expected_behavior: Optional[str]
    actual_behavior: Optional[str]

    # Metadata
    evaluation_id: Optional[str] = None
    evaluation_ms: int = 0

    def __post_init__(self):
        if self.evaluation_id is None:
            self.evaluation_id = str(uuid4())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "policy": self.policy,
            "result": self.result,
            "reason": self.reason,
            "modified_output": self.modified_output[:100] if self.modified_output else None,
            "expected_behavior": self.expected_behavior,
            "actual_behavior": self.actual_behavior,
            "evaluation_id": self.evaluation_id,
            "evaluation_ms": self.evaluation_ms,
        }


class PreventionHook:
    """
    Prevention hook for pre-response validation.

    Usage:
        hook = PreventionHook(strict_mode=True)

        # Before sending response to client
        result = hook.evaluate(PreventionContext(
            tenant_id="tenant_123",
            call_id="call_abc",
            user_id="cust_8372",
            model="gpt-4.1",
            user_query="Is my contract auto-renewed?",
            system_prompt="You are a helpful assistant.",
            context_data={"auto_renew": None, "contract_status": "active"},
            llm_output="Yes, your contract is set to auto-renew...",
            output_tokens=18,
        ))

        if result.action == PreventionAction.BLOCK:
            # Don't send response, return error or safe message
            pass
        elif result.action == PreventionAction.MODIFY:
            # Send modified response
            pass
    """

    def __init__(
        self,
        strict_mode: bool = True,
        block_on_fail: bool = True,
        fallback_message: Optional[str] = None,
    ):
        self.strict_mode = strict_mode
        self.block_on_fail = block_on_fail
        self.fallback_message = fallback_message or (
            "I apologize, but I don't have enough information to answer that question "
            "accurately. Could you please provide more details or check your account settings?"
        )

        self.content_validator = ContentAccuracyValidator(strict_mode=strict_mode)

    def evaluate(self, ctx: PreventionContext) -> PreventionResult:
        """
        Evaluate the LLM output against policies.

        Returns a PreventionResult indicating what action to take.
        """
        import time

        start = time.time()

        # Run content accuracy validation
        accuracy_result = self.content_validator.validate(
            output=ctx.llm_output,
            context=ctx.context_data,
            user_query=ctx.user_query,
        )

        eval_ms = int((time.time() - start) * 1000)

        # Determine action based on result
        if accuracy_result.result == ValidationResult.FAIL:
            if self.block_on_fail:
                action = PreventionAction.MODIFY
                modified_output = self.fallback_message
            else:
                action = PreventionAction.WARN
                modified_output = None
        elif accuracy_result.result == ValidationResult.WARN:
            action = PreventionAction.WARN
            modified_output = None
        else:
            action = PreventionAction.ALLOW
            modified_output = None

        return PreventionResult(
            action=action,
            policy="CONTENT_ACCURACY",
            result=accuracy_result.result.value,
            reason=accuracy_result.overall_reason,
            modified_output=modified_output,
            expected_behavior=accuracy_result.expected_behavior,
            actual_behavior=accuracy_result.actual_behavior,
            evaluation_ms=eval_ms,
        )

    def get_safe_response(self, ctx: PreventionContext) -> str:
        """
        Generate a safe response when the original fails validation.

        This creates a response that:
        1. Acknowledges the user's question
        2. Indicates uncertainty about the specific data
        3. Suggests next steps
        """
        # Could use LLM to generate a better safe response, but for now use template
        templates = {
            "auto_renew": (
                "I don't have access to your current auto-renewal settings. "
                "To check your contract renewal status, please log into your account "
                "or contact our support team who can verify this information for you."
            ),
            "contract": (
                "I'd be happy to help with your contract question, but I don't currently "
                "have access to your specific contract details. Please contact your account "
                "manager or check your customer portal for accurate information."
            ),
            "default": self.fallback_message,
        }

        # Check which template to use based on query
        query_lower = ctx.user_query.lower() if ctx.user_query else ""

        if "auto" in query_lower and "renew" in query_lower:
            return templates["auto_renew"]
        elif "contract" in query_lower:
            return templates["contract"]
        else:
            return templates["default"]


def create_prevention_hook(
    strict_mode: bool = True,
    block_on_fail: bool = True,
) -> PreventionHook:
    """Factory function to create a prevention hook."""
    return PreventionHook(
        strict_mode=strict_mode,
        block_on_fail=block_on_fail,
    )


# Singleton for global access
_prevention_hook: Optional[PreventionHook] = None


def get_prevention_hook() -> PreventionHook:
    """Get the global prevention hook instance."""
    global _prevention_hook
    if _prevention_hook is None:
        _prevention_hook = create_prevention_hook()
    return _prevention_hook


def evaluate_response(
    tenant_id: str,
    call_id: str,
    user_query: str,
    context_data: Dict[str, Any],
    llm_output: str,
    model: str = "unknown",
    user_id: Optional[str] = None,
) -> PreventionResult:
    """
    Convenience function to evaluate an LLM response.

    Usage:
        result = evaluate_response(
            tenant_id="tenant_123",
            call_id="call_abc",
            user_query="Is my contract auto-renewed?",
            context_data={"auto_renew": None},
            llm_output="Yes, your contract is set to auto-renew...",
        )

        if result.action != PreventionAction.ALLOW:
            # Handle blocked/modified response
            pass
    """
    hook = get_prevention_hook()

    ctx = PreventionContext(
        tenant_id=tenant_id,
        call_id=call_id,
        user_id=user_id,
        model=model,
        user_query=user_query,
        system_prompt=None,
        context_data=context_data,
        llm_output=llm_output,
        output_tokens=len(llm_output.split()),  # Rough estimate
    )

    return hook.evaluate(ctx)
