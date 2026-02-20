# capability_id: CAP-002
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: FeatureTag, CostRecord, CostBudget
#   Writes: FeatureTag, CostRecord, CostBudget
# Database:
#   Scope: domain (analytics)
#   Models: FeatureTag, CostRecord, CostBudget
# Role: Data access for cost write operations
# Callers: cost_write.py (L5)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-470, PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
#
# GOVERNANCE NOTE:
# This L6 driver provides pure data access for cost writes.
# NO business logic - only DB operations.
#
# EXTRACTION STATUS: RECLASSIFIED (2026-01-23)

"""
Cost Write Driver (L6)

Pure database write operations for Cost Intelligence.

L4 (CostWriteService) → L6 (this driver)

Responsibilities:
- Persist FeatureTag records
- Persist CostRecord records
- Persist CostBudget records
- NO business logic (L4 responsibility)

Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session

from app.db import CostBudget, CostRecord, FeatureTag


class CostWriteDriver:
    """
    L6 driver for cost write operations.

    Pure database access - no business logic.
    """

    def __init__(self, session: Session):
        self._session = session

    # =========================================================================
    # FeatureTag Operations
    # =========================================================================

    def create_feature_tag(
        self,
        tenant_id: str,
        tag: str,
        display_name: str,
        description: Optional[str] = None,
        budget_cents: Optional[int] = None,
    ) -> FeatureTag:
        """
        Create a new feature tag and persist.

        Args:
            tenant_id: Tenant ID
            tag: Feature namespace (e.g., 'customer_support.chat')
            display_name: Human-readable name
            description: Optional description
            budget_cents: Optional per-feature budget

        Returns:
            Created FeatureTag instance
        """
        feature_tag = FeatureTag(
            tenant_id=tenant_id,
            tag=tag,
            display_name=display_name,
            description=description,
            budget_cents=budget_cents,
        )
        self._session.add(feature_tag)
        self._session.flush()  # Get generated ID, NO COMMIT — L4 owns transaction
        self._session.refresh(feature_tag)
        return feature_tag

    def update_feature_tag(
        self,
        feature_tag: FeatureTag,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        budget_cents: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> FeatureTag:
        """
        Update a feature tag and persist.

        Args:
            feature_tag: The feature tag to update
            display_name: New display name (if provided)
            description: New description (if provided)
            budget_cents: New budget (if provided)
            is_active: New active status (if provided)

        Returns:
            Updated FeatureTag instance
        """
        if display_name is not None:
            feature_tag.display_name = display_name
        if description is not None:
            feature_tag.description = description
        if budget_cents is not None:
            feature_tag.budget_cents = budget_cents
        if is_active is not None:
            feature_tag.is_active = is_active

        feature_tag.updated_at = datetime.now(timezone.utc)

        self._session.add(feature_tag)
        self._session.flush()  # Get updated data, NO COMMIT — L4 owns transaction
        self._session.refresh(feature_tag)
        return feature_tag

    # =========================================================================
    # CostRecord Operations
    # =========================================================================

    def create_cost_record(
        self,
        tenant_id: str,
        user_id: Optional[str],
        feature_tag: Optional[str],
        request_id: Optional[str],
        workflow_id: Optional[str],
        skill_id: Optional[str],
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_cents: int,
    ) -> CostRecord:
        """
        Create a new cost record and persist.

        Args:
            tenant_id: Tenant ID
            user_id: User ID
            feature_tag: Feature tag
            request_id: Request ID
            workflow_id: Workflow ID
            skill_id: Skill ID
            model: Model name
            input_tokens: Input token count
            output_tokens: Output token count
            cost_cents: Cost in cents

        Returns:
            Created CostRecord instance
        """
        record = CostRecord(
            tenant_id=tenant_id,
            user_id=user_id,
            feature_tag=feature_tag,
            request_id=request_id,
            workflow_id=workflow_id,
            skill_id=skill_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_cents=cost_cents,
        )
        self._session.add(record)
        # NO COMMIT — L4 coordinator owns transaction boundary
        return record

    # =========================================================================
    # CostBudget Operations
    # =========================================================================

    def create_or_update_budget(
        self,
        existing_budget: Optional[CostBudget],
        tenant_id: str,
        budget_type: str,
        entity_id: Optional[str],
        daily_limit_cents: Optional[int],
        monthly_limit_cents: Optional[int],
        warn_threshold_pct: int,
        hard_limit_enabled: bool,
    ) -> CostBudget:
        """
        Create a new budget or update existing one and persist.

        Args:
            existing_budget: Existing budget to update (or None to create)
            tenant_id: Tenant ID
            budget_type: Budget type
            entity_id: Entity ID
            daily_limit_cents: Daily limit
            monthly_limit_cents: Monthly limit
            warn_threshold_pct: Warning threshold percentage
            hard_limit_enabled: Whether hard limit is enabled

        Returns:
            Created or updated CostBudget instance
        """
        if existing_budget:
            existing_budget.daily_limit_cents = daily_limit_cents
            existing_budget.monthly_limit_cents = monthly_limit_cents
            existing_budget.warn_threshold_pct = warn_threshold_pct
            existing_budget.hard_limit_enabled = hard_limit_enabled
            existing_budget.updated_at = datetime.now(timezone.utc)
            budget = existing_budget
        else:
            budget = CostBudget(
                tenant_id=tenant_id,
                budget_type=budget_type,
                entity_id=entity_id,
                daily_limit_cents=daily_limit_cents,
                monthly_limit_cents=monthly_limit_cents,
                warn_threshold_pct=warn_threshold_pct,
                hard_limit_enabled=hard_limit_enabled,
            )
            self._session.add(budget)

        self._session.flush()  # Get generated/updated data, NO COMMIT — L4 owns transaction
        self._session.refresh(budget)
        return budget


def get_cost_write_driver(session: Session) -> CostWriteDriver:
    """Factory function to get CostWriteDriver instance."""
    return CostWriteDriver(session)


__all__ = [
    "CostWriteDriver",
    "get_cost_write_driver",
]
