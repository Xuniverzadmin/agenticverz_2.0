# capability_id: CAP-009
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: policy_rules, policy_rule_integrity
#   Writes: policy_rules, policy_rule_integrity
# Database:
#   Scope: domain (policies)
#   Models: PolicyRule, PolicyRuleIntegrity
# Role: Data access for policy rules CRUD operations
# Callers: policy_rules_service.py (L5 engine)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, PIN-468, POLICIES_DOMAIN_LOCK.md
#
# EXTRACTION STATUS: Phase-2.5A (2026-01-24)
# - Created from policy_rules_service.py extraction
# - All DB operations moved here
# - Engine contains ONLY decision logic
#
# ============================================================================
# L6 DRIVER INVARIANT — POLICY RULES (LOCKED)
# ============================================================================
# This file MUST contain ONLY data access operations.
# No business logic, no validation, no decisions.
# Any violation is a Phase-2.5 regression.
# ============================================================================

"""
Policy Rules Driver

Pure data access for policy rules table.
No business logic - only DB operations.

Authority: RULE_PERSISTENCE
Tables: policy_rules, policy_rule_integrity
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.models.policy_control_plane import PolicyRule, PolicyRuleIntegrity


class PolicyRulesDriver:
    """
    Data access driver for policy rules.

    INVARIANTS (L6):
    - No business branching
    - No validation
    - No cross-domain calls
    - Pure persistence operations only
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_rule_by_id(
        self,
        tenant_id: str,
        rule_id: str,
    ) -> Optional["PolicyRule"]:
        """
        Fetch a rule by ID with tenant scope.

        Args:
            tenant_id: Tenant scope
            rule_id: Rule to fetch

        Returns:
            PolicyRule if found, None otherwise
        """
        from app.models.policy_control_plane import PolicyRule

        stmt = select(PolicyRule).where(
            PolicyRule.id == rule_id,
            PolicyRule.tenant_id == tenant_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    def add_rule(self, rule: "PolicyRule") -> None:
        """
        Add a rule to the session.

        Args:
            rule: Rule to add
        """
        self._session.add(rule)

    def add_integrity(self, integrity: "PolicyRuleIntegrity") -> None:
        """
        Add an integrity record to the session.

        Args:
            integrity: Integrity record to add
        """
        self._session.add(integrity)

    def create_rule(self, **kwargs) -> "PolicyRule":
        """
        Construct a PolicyRule ORM object, add it to the session, and return it.

        Args:
            **kwargs: Fields forwarded to PolicyRule constructor.

        Returns:
            The newly created PolicyRule instance.
        """
        from app.models.policy_control_plane import PolicyRule

        rule = PolicyRule(**kwargs)
        self._session.add(rule)
        return rule

    def create_integrity(self, **kwargs) -> "PolicyRuleIntegrity":
        """
        Construct a PolicyRuleIntegrity ORM object, add it to the session, and return it.

        Args:
            **kwargs: Fields forwarded to PolicyRuleIntegrity constructor.

        Returns:
            The newly created PolicyRuleIntegrity instance.
        """
        from app.models.policy_control_plane import PolicyRuleIntegrity

        integrity = PolicyRuleIntegrity(**kwargs)
        self._session.add(integrity)
        return integrity

    async def flush(self) -> None:
        """Flush pending changes without committing."""
        await self._session.flush()


def get_policy_rules_driver(session: AsyncSession) -> PolicyRulesDriver:
    """Factory function for PolicyRulesDriver."""
    return PolicyRulesDriver(session)
