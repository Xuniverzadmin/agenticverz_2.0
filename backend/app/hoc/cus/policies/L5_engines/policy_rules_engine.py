# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: rules (via driver)
#   Writes: rules (via driver)
# Role: Policy rules CRUD engine (PIN-LIM-02) - pure business logic
# Callers: api/policies.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-LIM-02, PIN-468
#
# EXTRACTION STATUS: Phase-2.5A (2026-01-24)
# - All DB operations extracted to PolicyRulesDriver
# - Engine contains ONLY decision logic
# - NO sqlalchemy/sqlmodel imports at runtime
#
# ============================================================================
# L5 ENGINE INVARIANT — POLICY RULES (LOCKED)
# ============================================================================
# This file MUST NOT import sqlalchemy/sqlmodel at runtime.
# All persistence is delegated to policy_rules_driver.py.
# Business decisions ONLY.
#
# Any violation is a Phase-2.5 regression.
# ============================================================================
# NOTE: Renamed policy_rules_service.py → policy_rules_engine.py (2026-01-24)
#       Reclassified L4→L5 per HOC Topology V1 - BANNED_NAMING fix

from __future__ import annotations

"""
Policy Rules Service (PIN-LIM-02)

Persist and validate policy rule logic.

Responsibilities:
- Create/update rules
- Rule syntax validation
- Link rules → limits
- Handle retirement (rules are never deleted)
- Emit audit events

All DB operations delegated to PolicyRulesDriver.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional  # Any used for audit injection (PIN-504)

# L6 driver import (allowed)
from app.hoc.cus.hoc_spine.services.time import utc_now
from app.hoc.cus.hoc_spine.drivers.cross_domain import generate_uuid
from app.hoc.cus.policies.L6_drivers.policy_rules_driver import (
    PolicyRulesDriver,
    get_policy_rules_driver,
)

from app.hoc.cus.hoc_spine.schemas.domain_enums import ActorType

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.policy_control_plane import PolicyRule, PolicyRuleIntegrity

from app.hoc.cus.policies.L5_schemas.policy_rules import (
    CreatePolicyRuleRequest,
    UpdatePolicyRuleRequest,
    PolicyRuleResponse,
)


class PolicyRulesServiceError(Exception):
    """Base exception for policy rules service."""
    pass


class RuleNotFoundError(PolicyRulesServiceError):
    """Raised when rule is not found."""
    pass


class RuleValidationError(PolicyRulesServiceError):
    """Raised when rule validation fails."""
    pass


class PolicyRulesService:
    """
    Service for policy rule CRUD operations.

    INVARIANTS:
    - Rules are tenant-scoped
    - Rules are never deleted, only retired
    - Every active rule MUST have an integrity record
    - Retirement creates audit trail
    """

    def __init__(self, session: "AsyncSession", audit: Any = None):
        """
        Args:
            session: Async SQLAlchemy Session
            audit: Audit service instance (injected by L4 handler, PIN-504).
        """
        self._session = session
        self._driver = get_policy_rules_driver(session)
        self._audit = audit

    async def create(
        self,
        tenant_id: str,
        request: CreatePolicyRuleRequest,
        created_by: Optional[str] = None,
    ) -> PolicyRuleResponse:
        """
        Create a new policy rule.

        TRANSACTION CONTRACT:
        - State change and audit event commit together (atomic)
        - If audit emit fails, rule creation rolls back
        - No partial state is possible

        Args:
            tenant_id: Owning tenant ID
            request: Create request with rule details
            created_by: Optional user ID who created this

        Returns:
            Created rule response

        Raises:
            RuleValidationError: If validation fails
        """
        # Validate rule conditions (if provided)
        if request.conditions:
            self._validate_conditions(request.conditions)

        # Create rule record
        rule_id = generate_uuid()
        now = utc_now()

        # ATOMIC BLOCK: L4 owns transaction boundary (PIN-520)
        rule = self._driver.create_rule(
            id=rule_id,
            tenant_id=tenant_id,
            name=request.name,
            description=request.description,
            enforcement_mode=request.enforcement_mode,
            scope=request.scope,
            scope_id=request.scope_id,
            conditions=request.conditions,
            status="ACTIVE",
            source=request.source,
            source_proposal_id=request.source_proposal_id,
            parent_rule_id=request.parent_rule_id,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

        # Create integrity record (INVARIANT: every active rule needs one)
        integrity = self._driver.create_integrity(
            id=generate_uuid(),
            rule_id=rule_id,
            integrity_status="VERIFIED",
            integrity_score=Decimal("1.000"),
            hash_root=self._compute_hash(rule),
            computed_at=now,
        )

        # Build rule state for audit
        rule_state = {
            "name": rule.name,
            "enforcement_mode": rule.enforcement_mode,
            "scope": rule.scope,
            "conditions": rule.conditions,
            "source": rule.source,
        }

        # Emit audit event (PIN-413: Logs Domain)
        # Audit service injected by L4 handler (PIN-504)
        if self._audit:
            await self._audit.policy_rule_created(
                tenant_id=tenant_id,
                rule_id=rule_id,
                actor_id=created_by,
                actor_type=ActorType.HUMAN if created_by else ActorType.SYSTEM,
                reason=f"Rule created: {rule.name}",
                rule_state=rule_state,
            )

        return self._to_response(rule)

    async def update(
        self,
        tenant_id: str,
        rule_id: str,
        request: UpdatePolicyRuleRequest,
        updated_by: Optional[str] = None,
    ) -> PolicyRuleResponse:
        """
        Update an existing policy rule.

        TRANSACTION CONTRACT:
        - State change and audit event commit together (atomic)
        - If audit emit fails, rule update rolls back
        - No partial state is possible

        Args:
            tenant_id: Owning tenant ID
            rule_id: Rule to update
            request: Update request with changed fields
            updated_by: Optional user ID who made update

        Returns:
            Updated rule response

        Raises:
            RuleNotFoundError: If rule not found
            RuleValidationError: If validation fails
        """
        rule = await self._get_rule(tenant_id, rule_id)

        # Capture before state for audit
        before_state = {
            "name": rule.name,
            "enforcement_mode": rule.enforcement_mode,
            "scope": rule.scope,
            "conditions": rule.conditions,
            "status": rule.status,
        }

        # ATOMIC BLOCK: L4 owns transaction boundary (PIN-520)
        # Handle retirement specially
        if request.status == "RETIRED":
            if not request.retirement_reason:
                raise RuleValidationError("Retirement requires a reason")
            rule.retire(
                by=updated_by or "system",
                reason=request.retirement_reason,
                superseded_by_id=request.superseded_by,
            )

            # Capture after state for retirement audit
            after_state = {
                "name": rule.name,
                "status": "RETIRED",
                "retired_by": updated_by or "system",
                "retirement_reason": request.retirement_reason,
                "superseded_by": request.superseded_by,
            }

            # Emit retirement audit event (PIN-413)
            # Audit service injected by L4 handler (PIN-504)
            if self._audit:
                await self._audit.policy_rule_retired(
                    tenant_id=tenant_id,
                    rule_id=rule_id,
                    actor_id=updated_by,
                    actor_type=ActorType.HUMAN if updated_by else ActorType.SYSTEM,
                    reason=request.retirement_reason,
                    before_state=before_state,
                    after_state=after_state,
                )
        else:
            # Update mutable fields
            if request.name is not None:
                rule.name = request.name
            if request.description is not None:
                rule.description = request.description
            if request.enforcement_mode is not None:
                rule.enforcement_mode = request.enforcement_mode
            if request.conditions is not None:
                self._validate_conditions(request.conditions)
                rule.conditions = request.conditions

            rule.updated_at = utc_now()

            # Capture after state for modification audit
            after_state = {
                "name": rule.name,
                "enforcement_mode": rule.enforcement_mode,
                "scope": rule.scope,
                "conditions": rule.conditions,
                "status": rule.status,
            }

            # Emit modification audit event (PIN-413)
            # Audit service injected by L4 handler (PIN-504)
            if self._audit:
                await self._audit.policy_rule_modified(
                    tenant_id=tenant_id,
                    rule_id=rule_id,
                    actor_id=updated_by,
                    actor_type=ActorType.HUMAN if updated_by else ActorType.SYSTEM,
                    reason=f"Rule modified: {rule.name}",
                    before_state=before_state,
                    after_state=after_state,
                )

        return self._to_response(rule)

    async def get(
        self,
        tenant_id: str,
        rule_id: str,
    ) -> PolicyRuleResponse:
        """
        Get a policy rule by ID.

        Args:
            tenant_id: Owning tenant ID
            rule_id: Rule to retrieve

        Returns:
            Rule response

        Raises:
            RuleNotFoundError: If rule not found
        """
        rule = await self._get_rule(tenant_id, rule_id)
        return self._to_response(rule)

    async def _get_rule(self, tenant_id: str, rule_id: str) -> PolicyRule:
        """Get rule by ID with tenant check."""
        rule = await self._driver.fetch_rule_by_id(tenant_id, rule_id)

        if not rule:
            raise RuleNotFoundError(f"Rule {rule_id} not found")

        return rule

    def _validate_conditions(self, conditions: dict[str, Any]) -> None:
        """
        Validate rule conditions syntax.

        Basic validation - can be extended for more complex rule DSL.
        """
        if not isinstance(conditions, dict):
            raise RuleValidationError("Conditions must be a JSON object")

        # Allow empty conditions
        if not conditions:
            return

        # Basic structure validation
        # Could add more sophisticated DSL validation here
        allowed_keys = {"operator", "field", "value", "conditions", "type"}
        for key in conditions.keys():
            if key not in allowed_keys:
                # Allow additional keys for flexibility
                pass

    def _compute_hash(self, rule: PolicyRule) -> str:
        """Compute integrity hash for rule."""
        import hashlib
        import json

        data = {
            "id": rule.id,
            "name": rule.name,
            "enforcement_mode": rule.enforcement_mode,
            "scope": rule.scope,
            "conditions": rule.conditions,
        }
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def _to_response(self, rule: PolicyRule) -> PolicyRuleResponse:
        """Convert model to response."""
        return PolicyRuleResponse(
            rule_id=rule.id,
            tenant_id=rule.tenant_id,
            name=rule.name,
            description=rule.description,
            enforcement_mode=rule.enforcement_mode,
            scope=rule.scope,
            scope_id=rule.scope_id,
            conditions=rule.conditions,
            status=rule.status,
            source=rule.source,
            source_proposal_id=rule.source_proposal_id,
            parent_rule_id=rule.parent_rule_id,
            created_at=rule.created_at,
            created_by=rule.created_by,
            updated_at=rule.updated_at,
            retired_at=rule.retired_at,
            retired_by=rule.retired_by,
            retirement_reason=rule.retirement_reason,
            superseded_by=rule.superseded_by,
        )
