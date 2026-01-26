# Layer: L2 — Product APIs
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified COMPLIANCE facade - L2 API for compliance verification
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-103 (Compliance Verification API)
# GOVERNANCE NOTE:
# This is the ONE facade for COMPLIANCE domain.
# All compliance verification flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Compliance API (L2)

Provides compliance verification operations:
- POST /api/v1/compliance/verify (run verification)
- GET /api/v1/compliance/reports (list reports)
- GET /api/v1/compliance/reports/{id} (get report)
- GET /api/v1/compliance/rules (list rules)
- GET /api/v1/compliance/rules/{id} (get rule)
- GET /api/v1/compliance/status (overall status)

This is the ONLY facade for compliance verification.
All compliance APIs flow through this router.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
# L5 engine imports (migrated to HOC per SWEEP-23)
from app.hoc.cus.general.L5_engines.compliance_facade import (
    ComplianceFacade,
    get_compliance_facade,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/compliance", tags=["Compliance"])


# =============================================================================
# Request/Response Models
# =============================================================================


class VerifyComplianceRequest(BaseModel):
    """Request to run compliance verification."""
    scope: str = Field(
        "all",
        description="Verification scope: all, data, policy, cost, security",
    )


# =============================================================================
# Dependencies
# =============================================================================


def get_facade() -> ComplianceFacade:
    """Get the compliance facade."""
    return get_compliance_facade()


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/verify", response_model=Dict[str, Any])
async def verify_compliance(
    request: VerifyComplianceRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: ComplianceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("compliance.verify")),
):
    """
    Run compliance verification (GAP-103).

    **Tier: PREVENT ($199)** - Compliance verification.

    Scopes:
    - all: Run all compliance checks
    - data: Data handling compliance
    - policy: Policy enforcement compliance
    - cost: Cost governance compliance
    - security: Security compliance
    """
    actor = ctx.user_id or "system"

    report = await facade.verify_compliance(
        tenant_id=ctx.tenant_id,
        scope=request.scope,
        actor=actor,
    )

    return wrap_dict(report.to_dict())


@router.get("/reports", response_model=Dict[str, Any])
async def list_reports(
    scope: Optional[str] = Query(None, description="Filter by scope"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: ComplianceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("compliance.read")),
):
    """
    List compliance reports.

    Returns compliance verification reports for the tenant.
    """
    reports = await facade.list_reports(
        tenant_id=ctx.tenant_id,
        scope=scope,
        status=status,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "reports": [r.to_dict() for r in reports],
        "total": len(reports),
        "limit": limit,
        "offset": offset,
    })


@router.get("/reports/{report_id}", response_model=Dict[str, Any])
async def get_report(
    report_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: ComplianceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("compliance.read")),
):
    """
    Get a specific compliance report.
    """
    report = await facade.get_report(
        report_id=report_id,
        tenant_id=ctx.tenant_id,
    )

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return wrap_dict(report.to_dict())


@router.get("/rules", response_model=Dict[str, Any])
async def list_rules(
    scope: Optional[str] = Query(None, description="Filter by scope"),
    enabled_only: bool = Query(True, description="Only enabled rules"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: ComplianceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("compliance.read")),
):
    """
    List compliance rules.

    Returns all compliance rules that are checked during verification.
    """
    rules = await facade.list_rules(
        scope=scope,
        enabled_only=enabled_only,
    )

    return wrap_dict({
        "rules": [r.to_dict() for r in rules],
        "total": len(rules),
    })


@router.get("/rules/{rule_id}", response_model=Dict[str, Any])
async def get_rule(
    rule_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: ComplianceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("compliance.read")),
):
    """
    Get a specific compliance rule.
    """
    rule = await facade.get_rule(rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return wrap_dict(rule.to_dict())


@router.get("/status", response_model=Dict[str, Any])
async def get_compliance_status(
    ctx: TenantContext = Depends(get_tenant_context),
    facade: ComplianceFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("compliance.read")),
):
    """
    Get overall compliance status.

    Returns the current compliance status including:
    - Overall status (compliant, non_compliant, partially_compliant)
    - Last verification timestamp
    - Rule counts
    - Pending violations
    """
    status = await facade.get_compliance_status(tenant_id=ctx.tenant_id)
    return wrap_dict(status.to_dict())
