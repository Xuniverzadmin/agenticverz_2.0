# Layer: L5 — Domain Engine
# Product: system-wide
# Wiring Type: policy-gate
# Parent Gap: GAP-063 (MCPConnector), GAP-087 (PolicyGate)
# Reference: GAP-142
# Depends On: GAP-141 (MCPServerRegistry)
# Temporal:
#   Trigger: worker (tool invocation)
#   Execution: async
# Role: Map MCP tool invocations to policy gates
# Callers: Runner, skill executor
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L5

"""
Module: policy_mapper
Purpose: Map MCP tool invocations to policy gates.

Wires:
    - Source: app/services/mcp/server_registry.py (tools)
    - Source: app/services/policies/policy_engine.py (policy evaluation)
    - Target: Tool invocations are gated by policy

This module:
    1. Maps MCP tool invocations to policy checks
    2. Determines required permissions for each tool
    3. Evaluates policy before allowing invocation
    4. Provides deny-by-default for unknown tools

Acceptance Criteria:
    - AC-142-01: Tools are mapped to policies
    - AC-142-02: Deny-by-default for unmapped tools
    - AC-142-03: Dangerous tools require explicit allow
    - AC-142-04: Policy decisions are logged
    - AC-142-05: Tenant policies are respected
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.services.mcp.policy_mapper")


class MCPPolicyDecisionType(str, Enum):
    """Types of policy decisions for MCP tools."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class MCPDenyReason(str, Enum):
    """Reasons for denying MCP tool invocation."""

    UNKNOWN_TOOL = "unknown_tool"
    TOOL_DISABLED = "tool_disabled"
    DANGEROUS_TOOL_NOT_ALLOWED = "dangerous_tool_not_allowed"
    POLICY_VIOLATION = "policy_violation"
    TENANT_BLOCKED = "tenant_blocked"
    RATE_LIMITED = "rate_limited"
    SERVER_OFFLINE = "server_offline"


@dataclass
class MCPPolicyDecision:
    """
    Policy decision for MCP tool invocation.

    Contains the decision and context for audit.
    """

    tool_name: str
    server_id: str
    decision: MCPPolicyDecisionType
    deny_reason: Optional[MCPDenyReason] = None
    policy_id: Optional[str] = None
    message: Optional[str] = None
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "tool_name": self.tool_name,
            "server_id": self.server_id,
            "decision": self.decision.value,
            "deny_reason": self.deny_reason.value if self.deny_reason else None,
            "policy_id": self.policy_id,
            "message": self.message,
            "checked_at": self.checked_at,
        }

    @classmethod
    def allow(
        cls,
        tool_name: str,
        server_id: str,
        policy_id: Optional[str] = None,
    ) -> "MCPPolicyDecision":
        """Create an allow decision."""
        return cls(
            tool_name=tool_name,
            server_id=server_id,
            decision=MCPPolicyDecisionType.ALLOW,
            policy_id=policy_id,
        )

    @classmethod
    def deny(
        cls,
        tool_name: str,
        server_id: str,
        reason: MCPDenyReason,
        message: Optional[str] = None,
        policy_id: Optional[str] = None,
    ) -> "MCPPolicyDecision":
        """Create a deny decision."""
        return cls(
            tool_name=tool_name,
            server_id=server_id,
            decision=MCPPolicyDecisionType.DENY,
            deny_reason=reason,
            message=message or f"Tool invocation denied: {reason.value}",
            policy_id=policy_id,
        )


@dataclass
class MCPToolPolicy:
    """
    Policy configuration for an MCP tool.

    Defines what permissions are required to invoke the tool.
    """

    tool_name: str
    server_id: str
    required_permissions: List[str] = field(default_factory=list)
    is_enabled: bool = True
    is_dangerous: bool = False
    requires_explicit_allow: bool = False
    max_calls_per_minute: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class MCPPolicyMapper:
    """
    Maps MCP tool invocations to policy gates.

    This service:
    1. Maintains tool→policy mappings
    2. Evaluates policies before tool invocation
    3. Enforces deny-by-default
    4. Handles dangerous tool restrictions
    """

    # Default rate limit for tools
    DEFAULT_RATE_LIMIT_PER_MINUTE = 60

    def __init__(self, policy_engine: Optional[Any] = None):
        """
        Initialize policy mapper.

        Args:
            policy_engine: Policy engine for evaluation (lazy loaded if None)
        """
        self._policy_engine = policy_engine
        self._tool_policies: Dict[str, MCPToolPolicy] = {}
        self._default_deny = True  # INVARIANT: deny-by-default

    async def check_tool_invocation(
        self,
        tenant_id: str,
        server_id: str,
        tool_name: str,
        run_id: str,
        input_params: Optional[Dict[str, Any]] = None,
    ) -> MCPPolicyDecision:
        """
        Check if tool invocation is allowed.

        INVARIANT: Deny-by-default for unknown tools.

        Args:
            tenant_id: Tenant making the request
            server_id: MCP server hosting the tool
            tool_name: Tool to invoke
            run_id: Run context
            input_params: Tool input parameters

        Returns:
            MCPPolicyDecision with allow/deny outcome
        """
        logger.debug(
            "mcp_policy.checking",
            extra={
                "tenant_id": tenant_id,
                "server_id": server_id,
                "tool_name": tool_name,
                "run_id": run_id,
            },
        )

        # Get tool policy
        policy_key = f"{server_id}:{tool_name}"
        tool_policy = self._tool_policies.get(policy_key)

        # Check 1: Unknown tool (deny-by-default)
        if tool_policy is None:
            if self._default_deny:
                logger.warning(
                    "mcp_policy.unknown_tool_denied",
                    extra={
                        "tenant_id": tenant_id,
                        "server_id": server_id,
                        "tool_name": tool_name,
                    },
                )
                return MCPPolicyDecision.deny(
                    tool_name=tool_name,
                    server_id=server_id,
                    reason=MCPDenyReason.UNKNOWN_TOOL,
                    message="Unknown tool - not allowed by default",
                )
            # If not deny-by-default (testing only), allow
            return MCPPolicyDecision.allow(tool_name, server_id)

        # Check 2: Tool disabled
        if not tool_policy.is_enabled:
            return MCPPolicyDecision.deny(
                tool_name=tool_name,
                server_id=server_id,
                reason=MCPDenyReason.TOOL_DISABLED,
            )

        # Check 3: Dangerous tool requires explicit allow
        if tool_policy.is_dangerous:
            has_explicit_allow = await self._check_explicit_allow(
                tenant_id, server_id, tool_name
            )
            if not has_explicit_allow:
                return MCPPolicyDecision.deny(
                    tool_name=tool_name,
                    server_id=server_id,
                    reason=MCPDenyReason.DANGEROUS_TOOL_NOT_ALLOWED,
                    message="Dangerous tool requires explicit allow policy",
                )

        # Check 4: Policy engine evaluation
        policy_result = await self._evaluate_policy(
            tenant_id=tenant_id,
            server_id=server_id,
            tool_name=tool_name,
            run_id=run_id,
            required_permissions=tool_policy.required_permissions,
        )

        if not policy_result.allowed:
            return MCPPolicyDecision.deny(
                tool_name=tool_name,
                server_id=server_id,
                reason=MCPDenyReason.POLICY_VIOLATION,
                message=policy_result.message,
                policy_id=policy_result.policy_id,
            )

        # Check 5: Rate limiting (if configured)
        if tool_policy.max_calls_per_minute is not None:
            is_rate_limited = await self._check_rate_limit(
                tenant_id=tenant_id,
                tool_key=policy_key,
                max_per_minute=tool_policy.max_calls_per_minute,
            )
            if is_rate_limited:
                return MCPPolicyDecision.deny(
                    tool_name=tool_name,
                    server_id=server_id,
                    reason=MCPDenyReason.RATE_LIMITED,
                    message="Rate limit exceeded for this tool",
                )

        # All checks passed - allow
        logger.info(
            "mcp_policy.allowed",
            extra={
                "tenant_id": tenant_id,
                "server_id": server_id,
                "tool_name": tool_name,
            },
        )

        return MCPPolicyDecision.allow(
            tool_name=tool_name,
            server_id=server_id,
            policy_id=policy_result.policy_id if policy_result else None,
        )

    async def register_tool_policy(
        self,
        server_id: str,
        tool_name: str,
        required_permissions: Optional[List[str]] = None,
        is_dangerous: bool = False,
        max_calls_per_minute: Optional[int] = None,
    ) -> MCPToolPolicy:
        """
        Register policy for a tool.

        Args:
            server_id: Server hosting the tool
            tool_name: Tool name
            required_permissions: Permissions required to invoke
            is_dangerous: Whether tool can have side effects
            max_calls_per_minute: Rate limit

        Returns:
            Created MCPToolPolicy
        """
        policy = MCPToolPolicy(
            tool_name=tool_name,
            server_id=server_id,
            required_permissions=required_permissions or [],
            is_dangerous=is_dangerous,
            max_calls_per_minute=max_calls_per_minute,
        )

        policy_key = f"{server_id}:{tool_name}"
        self._tool_policies[policy_key] = policy

        logger.info(
            "mcp_policy.tool_registered",
            extra={
                "server_id": server_id,
                "tool_name": tool_name,
                "is_dangerous": is_dangerous,
            },
        )

        return policy

    async def _evaluate_policy(
        self,
        tenant_id: str,
        server_id: str,
        tool_name: str,
        run_id: str,
        required_permissions: List[str],
    ) -> Any:
        """Evaluate policy engine for required permissions."""

        @dataclass
        class PolicyResult:
            allowed: bool
            message: Optional[str] = None
            policy_id: Optional[str] = None

        # Try to get policy engine
        policy_engine = self._get_policy_engine()
        if policy_engine is None:
            # No policy engine - allow if no permissions required
            if not required_permissions:
                return PolicyResult(allowed=True)
            # Otherwise deny (fail-closed)
            return PolicyResult(
                allowed=False,
                message="No policy engine available - deny by default",
            )

        try:
            # Check each required permission
            for permission in required_permissions:
                has_permission = await policy_engine.check_permission(
                    tenant_id=tenant_id,
                    permission=permission,
                    resource=f"mcp:{server_id}:{tool_name}",
                    run_id=run_id,
                )
                if not has_permission:
                    return PolicyResult(
                        allowed=False,
                        message=f"Missing permission: {permission}",
                    )

            return PolicyResult(allowed=True)

        except Exception as e:
            logger.warning(
                "mcp_policy.evaluation_failed",
                extra={"error": str(e)},
            )
            # Fail-closed on error
            return PolicyResult(
                allowed=False,
                message=f"Policy evaluation failed: {e}",
            )

    async def _check_explicit_allow(
        self,
        tenant_id: str,
        server_id: str,
        tool_name: str,
    ) -> bool:
        """Check if tenant has explicit allow for dangerous tool."""
        # TODO: Implement explicit allow check against policy store
        return False

    async def _check_rate_limit(
        self,
        tenant_id: str,
        tool_key: str,
        max_per_minute: int,
    ) -> bool:
        """Check if rate limit exceeded."""
        # TODO: Implement rate limiting with Redis
        return False

    def _get_policy_engine(self) -> Optional[Any]:
        """Get policy engine (lazy initialization)."""
        if self._policy_engine is not None:
            return self._policy_engine

        try:
            from app.services.policies import get_policy_engine
            return get_policy_engine()
        except ImportError:
            logger.debug("mcp_policy.policy_engine_not_available")
            return None


# =========================
# Singleton Management
# =========================

_mcp_policy_mapper: Optional[MCPPolicyMapper] = None


def get_mcp_policy_mapper() -> MCPPolicyMapper:
    """
    Get or create the singleton MCPPolicyMapper.

    Returns:
        MCPPolicyMapper instance
    """
    global _mcp_policy_mapper

    if _mcp_policy_mapper is None:
        _mcp_policy_mapper = MCPPolicyMapper()
        logger.info("mcp_policy_mapper.created")

    return _mcp_policy_mapper


def configure_mcp_policy_mapper(
    policy_engine: Optional[Any] = None,
) -> MCPPolicyMapper:
    """
    Configure the singleton MCPPolicyMapper.

    Args:
        policy_engine: Policy engine to use

    Returns:
        Configured MCPPolicyMapper
    """
    global _mcp_policy_mapper

    _mcp_policy_mapper = MCPPolicyMapper(policy_engine=policy_engine)

    logger.info(
        "mcp_policy_mapper.configured",
        extra={"has_policy_engine": policy_engine is not None},
    )

    return _mcp_policy_mapper


def reset_mcp_policy_mapper() -> None:
    """Reset the singleton (for testing)."""
    global _mcp_policy_mapper
    _mcp_policy_mapper = None
