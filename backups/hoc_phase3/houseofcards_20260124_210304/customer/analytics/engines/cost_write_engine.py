# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide (Cost Intelligence)
# Temporal:
#   Trigger: api
#   Execution: sync (delegates to L6 driver)
# Role: Cost write operations (L5 facade over L6 driver)
# Callers: api/cost_intelligence.py
# Allowed Imports: L6 (drivers only, NOT ORM models)
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
# NOTE: Renamed cost_write_service.py → cost_write_engine.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_engine.py)
#       Layer reclassified L4→L5 per HOC Layer Topology V1
#
# GOVERNANCE NOTE:
# This L5 engine delegates ALL database operations to CostWriteDriver (L6).
# NO direct database access - only driver calls.
# Phase 2 extraction: DB operations moved to drivers/cost_write_driver.py
#
# EXTRACTION STATUS: COMPLETE (2026-01-23)

"""
Cost Write Engine (L5)

DB write operations for Cost Intelligence API.
Delegates to CostWriteDriver (L6) for all database access.

L2 (API) → L4 (this service) → L6 (CostWriteDriver)

Responsibilities:
- Delegate to L6 driver for data access
- Maintain backward compatibility for callers

Reference: PIN-250, PHASE2_EXTRACTION_PROTOCOL.md
"""

from typing import TYPE_CHECKING, Optional

# L6 driver import (allowed)
from app.houseofcards.customer.analytics.drivers.cost_write_driver import (
    CostWriteDriver,
    get_cost_write_driver,
)

if TYPE_CHECKING:
    from sqlmodel import Session
    from app.db import CostBudget, CostRecord, FeatureTag


class CostWriteService:
    """
    DB write operations for Cost Intelligence.

    Delegates all operations to CostWriteDriver (L6).
    NO DIRECT DB ACCESS - driver calls only.
    """

    def __init__(self, session: "Session"):
        self._driver = get_cost_write_driver(session)

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
    ) -> "FeatureTag":
        """Delegate to driver."""
        return self._driver.create_feature_tag(
            tenant_id=tenant_id,
            tag=tag,
            display_name=display_name,
            description=description,
            budget_cents=budget_cents,
        )

    def update_feature_tag(
        self,
        feature_tag: "FeatureTag",
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        budget_cents: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> "FeatureTag":
        """Delegate to driver."""
        return self._driver.update_feature_tag(
            feature_tag=feature_tag,
            display_name=display_name,
            description=description,
            budget_cents=budget_cents,
            is_active=is_active,
        )

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
    ) -> "CostRecord":
        """Delegate to driver."""
        return self._driver.create_cost_record(
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

    # =========================================================================
    # CostBudget Operations
    # =========================================================================

    def create_or_update_budget(
        self,
        existing_budget: Optional["CostBudget"],
        tenant_id: str,
        budget_type: str,
        entity_id: Optional[str],
        daily_limit_cents: Optional[int],
        monthly_limit_cents: Optional[int],
        warn_threshold_pct: int,
        hard_limit_enabled: bool,
    ) -> "CostBudget":
        """Delegate to driver."""
        return self._driver.create_or_update_budget(
            existing_budget=existing_budget,
            tenant_id=tenant_id,
            budget_type=budget_type,
            entity_id=entity_id,
            daily_limit_cents=daily_limit_cents,
            monthly_limit_cents=monthly_limit_cents,
            warn_threshold_pct=warn_threshold_pct,
            hard_limit_enabled=hard_limit_enabled,
        )
