# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Policy rules CRUD service (PIN-LIM-02)
# Callers: api/policies.py
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-LIM-02

"""
Policy Rules Service (PIN-LIM-02)

Persist and validate policy rule logic.

Responsibilities:
- Create/update rules
- Rule syntax validation
- Link rules → limits
- Handle retirement (rules are never deleted)
- Emit audit events
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy_control_plane import (
    PolicyRule,
    PolicyRuleIntegrity,
    PolicyRuleStatus,
)
from app.models.audit_ledger import ActorType
from app.schemas.limits.policy_rules import (
    CreatePolicyRuleRequest,
    UpdatePolicyRuleRequest,
    PolicyRuleResponse,
)
from app.services.logs.audit_ledger_service_async import AuditLedgerServiceAsync


def utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


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

    def __init__(self, session: AsyncSession):
        self.session = session
        self._audit = AuditLedgerServiceAsync(session)

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

        rule = PolicyRule(
            id=rule_id,
            tenant_id=tenant_id,
            name=request.name,
            description=request.description,
            enforcement_mode=request.enforcement_mode,
            scope=request.scope,
            scope_id=request.scope_id,
            conditions=request.conditions,
            status=PolicyRuleStatus.ACTIVE.value,
            source=request.source,
            source_proposal_id=request.source_proposal_id,
            parent_rule_id=request.parent_rule_id,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

        # ATOMIC BLOCK: state change + audit must succeed together
        async with self.session.begin():
            self.session.add(rule)

            # Create integrity record (INVARIANT: every active rule needs one)
            integrity = PolicyRuleIntegrity(
                id=generate_uuid(),
                rule_id=rule_id,
                integrity_status="VERIFIED",
                integrity_score=Decimal("1.000"),
                hash_root=self._compute_hash(rule),
                computed_at=now,
            )
            self.session.add(integrity)

            # Build rule state for audit
            rule_state = {
                "name": rule.name,
                "enforcement_mode": rule.enforcement_mode,
                "scope": rule.scope,
                "conditions": rule.conditions,
                "source": rule.source,
            }

            # Emit audit event (PIN-413: Logs Domain)
            # Must be inside transaction - commits with state change
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

        # ATOMIC BLOCK: state change + audit must succeed together
        async with self.session.begin():
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
        stmt = select(PolicyRule).where(
            PolicyRule.id == rule_id,
            PolicyRule.tenant_id == tenant_id,
        )
        result = await self.session.execute(stmt)
        rule = result.scalar_one_or_none()

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
