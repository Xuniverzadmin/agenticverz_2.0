# Layer: L4 — Domain Engine
# Product: system-wide (Cost Intelligence)
# Temporal:
#   Trigger: api
#   Execution: sync
# Role: DB write delegation for Cost Intelligence API (Phase 2B extraction)
# Callers: api/cost_intelligence.py
# Allowed Imports: L6 (models, db)
# Forbidden Imports: L2 (api), L3 (adapters)
# Reference: PIN-250 Phase 2B Batch 2

"""
Cost Write Service - DB write operations for Cost Intelligence API.

Phase 2B Batch 2: Extracted from api/cost_intelligence.py.

Constraints (enforced by PIN-250):
- Write-only: No policy logic
- No cross-service calls
- No domain refactoring
- Call-path relocation only
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session

from app.db import CostBudget, CostRecord, FeatureTag


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


class CostWriteService:
    """
    DB write operations for Cost Intelligence.

    Write-only facade. No policy logic, no branching beyond DB operations.
    """

    def __init__(self, session: Session):
        self.session = session

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
        self.session.add(feature_tag)
        self.session.commit()
        self.session.refresh(feature_tag)
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

        feature_tag.updated_at = utc_now()

        self.session.add(feature_tag)
        self.session.commit()
        self.session.refresh(feature_tag)
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
        self.session.add(record)
        self.session.commit()
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
            existing_budget.updated_at = utc_now()
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
            self.session.add(budget)

        self.session.commit()
        self.session.refresh(budget)
        return budget
