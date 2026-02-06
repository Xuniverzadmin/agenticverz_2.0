# Layer: L2 — Product APIs
# Product: ai-console (Customer Console)
# Temporal:
#   Trigger: external (HTTP)
#   Execution: async (request-response)
# Role: Policy rules mutating operations (PIN-LIM-02)
# Callers: Customer Console frontend, Admin tools
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: PIN-LIM-02

"""
Policy Rules CRUD API (PIN-LIM-02)

Mutating endpoints for policy rules.

Extends the read-only policies.py facade with write operations.

Endpoints:
    POST /api/v1/policies/rules              → Create rule
    PUT  /api/v1/policies/rules/{rule_id}    → Update rule

Rules are never deleted - they are retired with reason.
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.gateway_middleware import get_auth_context
from app.db import get_async_session_dep
from app.schemas.limits.policy_rules import (
    CreatePolicyRuleRequest,
    PolicyRuleResponse,
    UpdatePolicyRuleRequest,
)
from app.hoc.cus.policies.L5_engines.policy_rules_engine import (
    PolicyRulesService,
    PolicyRulesServiceError,
    RuleNotFoundError,
    RuleValidationError,
)


router = APIRouter(prefix="/policies", tags=["policies"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateRuleRequest(BaseModel):
    """API request to create a policy rule."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    enforcement_mode: str = Field(default="AUDIT", description="BLOCK, WARN, AUDIT, DISABLED")
    scope: str = Field(default="TENANT", description="GLOBAL, TENANT, PROJECT, AGENT")
    scope_id: Optional[str] = Field(default=None, description="Scope target ID")
    conditions: Optional[dict[str, Any]] = Field(default=None, description="Rule conditions JSON")
    source: str = Field(default="MANUAL", description="MANUAL, SYSTEM, LEARNED")
    source_proposal_id: Optional[str] = Field(default=None)
    parent_rule_id: Optional[str] = Field(default=None)


class UpdateRuleRequest(BaseModel):
    """API request to update a policy rule."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    enforcement_mode: Optional[str] = Field(default=None)
    conditions: Optional[dict[str, Any]] = Field(default=None)
    status: Optional[str] = Field(default=None, description="ACTIVE or RETIRED")
    retirement_reason: Optional[str] = Field(default=None, max_length=500)
    superseded_by: Optional[str] = Field(default=None, description="ID of rule that supersedes this")


class RuleDetail(BaseModel):
    """Full rule response."""

    rule_id: str
    tenant_id: str
    name: str
    description: Optional[str]
    enforcement_mode: str
    scope: str
    scope_id: Optional[str]
    conditions: Optional[dict[str, Any]]
    status: str
    source: str
    source_proposal_id: Optional[str]
    parent_rule_id: Optional[str]
    created_at: datetime
    created_by: Optional[str]
    updated_at: datetime
    retired_at: Optional[datetime]
    retired_by: Optional[str]
    retirement_reason: Optional[str]
    superseded_by: Optional[str]


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/rules",
    response_model=RuleDetail,
    status_code=201,
    summary="Create a policy rule",
    description="Create a new policy rule for the tenant.",
)
async def create_rule(
    request: Request,
    body: CreateRuleRequest,
    session: AsyncSession = Depends(get_async_session_dep),
) -> RuleDetail:
    """
    Create a new policy rule.

    Rules can be created from:
    - MANUAL: User-defined rules
    - SYSTEM: System-generated rules
    - LEARNED: ML/AI proposed rules (from policy proposals)
    """
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id
    user_id = getattr(auth_context, "user_id", None)

    service = PolicyRulesService(session)

    try:
        create_request = CreatePolicyRuleRequest(
            name=body.name,
            description=body.description,
            enforcement_mode=body.enforcement_mode,
            scope=body.scope,
            scope_id=body.scope_id,
            conditions=body.conditions,
            source=body.source,
            source_proposal_id=body.source_proposal_id,
            parent_rule_id=body.parent_rule_id,
        )

        result = await service.create(
            tenant_id=tenant_id,
            request=create_request,
            created_by=user_id,
        )

        return _to_detail(result)

    except RuleValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "validation_error", "message": str(e)},
        )
    except PolicyRulesServiceError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "create_error", "message": str(e)},
        )


@router.put(
    "/rules/{rule_id}",
    response_model=RuleDetail,
    summary="Update a policy rule",
    description="Update a policy rule or retire it.",
)
async def update_rule(
    request: Request,
    rule_id: str,
    body: UpdateRuleRequest,
    session: AsyncSession = Depends(get_async_session_dep),
) -> RuleDetail:
    """
    Update an existing policy rule.

    To retire a rule:
    - Set status to "RETIRED"
    - Provide retirement_reason (required)
    - Optionally set superseded_by

    Rules are never deleted, only retired.
    """
    auth_context = get_auth_context(request)
    tenant_id = auth_context.tenant_id
    user_id = getattr(auth_context, "user_id", None)

    service = PolicyRulesService(session)

    try:
        update_request = UpdatePolicyRuleRequest(
            name=body.name,
            description=body.description,
            enforcement_mode=body.enforcement_mode,
            conditions=body.conditions,
            status=body.status,
            retirement_reason=body.retirement_reason,
            superseded_by=body.superseded_by,
        )

        result = await service.update(
            tenant_id=tenant_id,
            rule_id=rule_id,
            request=update_request,
            updated_by=user_id,
        )

        return _to_detail(result)

    except RuleNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={"error": "rule_not_found", "message": str(e)},
        )
    except RuleValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "validation_error", "message": str(e)},
        )
    except PolicyRulesServiceError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "update_error", "message": str(e)},
        )


# =============================================================================
# Helpers
# =============================================================================


def _to_detail(result: PolicyRuleResponse) -> RuleDetail:
    """Convert service response to API response."""
    return RuleDetail(
        rule_id=result.rule_id,
        tenant_id=result.tenant_id,
        name=result.name,
        description=result.description,
        enforcement_mode=result.enforcement_mode,
        scope=result.scope,
        scope_id=result.scope_id,
        conditions=result.conditions,
        status=result.status,
        source=result.source,
        source_proposal_id=result.source_proposal_id,
        parent_rule_id=result.parent_rule_id,
        created_at=result.created_at,
        created_by=result.created_by,
        updated_at=result.updated_at,
        retired_at=result.retired_at,
        retired_by=result.retired_by,
        retirement_reason=result.retirement_reason,
        superseded_by=result.superseded_by,
    )
