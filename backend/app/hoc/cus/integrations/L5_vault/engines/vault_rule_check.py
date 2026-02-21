# capability_id: CAP-018
# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none (rule evaluation)
#   Writes: none
# Role: Credential access rule checker protocol and default implementations
# Callers: CredentialService, CusCredentialService
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-517 (cus_vault Authority Refactor)

"""
Credential Access Rule Checker (PIN-517 FIX 4.1)

Defines the protocol for credential access rule validation.
Rule checking is ASYNC and happens at L4 orchestrator
BEFORE entering the sync vault path.

Implementations:
- DefaultCredentialAccessRuleChecker: Permissive (system scope)
- DenyAllRuleChecker: Fail-closed (for testing)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable


@dataclass(frozen=True)
class CredentialAccessResult:
    """Result of credential access rule check."""

    allowed: bool
    rule_id: Optional[str] = None
    deny_reason: Optional[str] = None


@runtime_checkable
class CredentialAccessRuleChecker(Protocol):
    """Protocol for credential access rule validation."""

    async def check_credential_access(
        self,
        tenant_id: str,
        credential_ref: str,
        accessor_id: str,
        accessor_type: str,  # "human", "machine", "mcp_tool"
        access_reason: Optional[str] = None,
    ) -> CredentialAccessResult:
        """
        Check if credential access is allowed by rules.

        Args:
            tenant_id: Tenant identifier
            credential_ref: The credential reference being accessed
            accessor_id: Who is accessing (user_id, run_id, tool_id)
            accessor_type: Type of accessor
            access_reason: Why access is needed

        Returns:
            CredentialAccessResult with allowed status
        """
        ...


class DefaultCredentialAccessRuleChecker:
    """
    Default rule checker - allows all access.

    Use for SYSTEM scope where permissive access is acceptable.
    NOT for customer credentials without explicit rules.
    """

    async def check_credential_access(
        self,
        tenant_id: str,
        credential_ref: str,
        accessor_id: str,
        accessor_type: str,
        access_reason: Optional[str] = None,
    ) -> CredentialAccessResult:
        # Parameters used for audit/logging if needed
        _ = (tenant_id, credential_ref, accessor_id, accessor_type, access_reason)
        return CredentialAccessResult(
            allowed=True,
            rule_id="default-permissive",
        )


class DenyAllRuleChecker:
    """
    Fail-closed rule checker - denies all access.

    Use as default for customer scope when no rules configured.
    Forces explicit rule configuration.
    """

    async def check_credential_access(
        self,
        tenant_id: str,
        credential_ref: str,
        accessor_id: str,
        accessor_type: str,
        access_reason: Optional[str] = None,
    ) -> CredentialAccessResult:
        _ = (tenant_id, credential_ref, accessor_id, accessor_type, access_reason)
        return CredentialAccessResult(
            allowed=False,
            rule_id="fail-closed-default",
            deny_reason="No rule checker configured for customer vault",
        )
