# Layer: L2 — Product APIs
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Policy sandbox evaluation and approval workflow management
# Authority: WRITE ApprovalRequest, PolicyApprovalLevel records
# Callers: External clients, SDK, Customer Console
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: M5 Policy System, PIN-158 Tier Gating, PIN-258 Phase F-3
# Contract: PHASE_F_FIX_DESIGN (F-P-RULE-1 to F-P-RULE-5)
#
# GOVERNANCE NOTE (F-P-RULE-1):
# This L2 module must ONLY call the L3 policy_adapter.
# Direct L5 workflow imports are FORBIDDEN.
#
# F-P-RULE-1: Policy Decisions Live Only in L4 - we call L3 which calls L4
# F-P-RULE-3: L3 Is Translation Only - we call L3, not L5

# api/policy.py
"""
Policy API Endpoints (M5)

Provides:
1. Policy sandbox evaluation (/api/v1/policy/eval)
2. Approval workflow endpoints (/api/v1/policy/requests/*)
3. Webhook callbacks for async approvals

Integrates with:
- PolicyEnforcer from workflow/policies.py
- PolicyApprovalLevel and ApprovalRequest from db.py
- Workflow metrics for observability
- CostSim V2 for simulation

NOTE: Policy subsystem MUST use AsyncSession - async endpoints + M17/M19 routing.
      Do NOT import sync Session from sqlmodel. See test_m19_policy.py guardrail tests.

Tier Gating (M32 - PIN-158):
- PREVENT ($199): Policy evaluation sandbox (pre-execution decisions)
- ASSIST ($1.5k+): Approval workflows (advanced orchestration)
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, cast
from uuid import uuid4

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import TenantTier, requires_feature, requires_tier
from app.db_async import get_async_session
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
)
from app.schemas.response import wrap_dict

logger = logging.getLogger("nova.api.policy")

router = APIRouter(prefix="/api/v1/policy", tags=["policy"])


# =============================================================================
# L3 Adapter Access (Phase F-3: F-P-RULE-1)
# =============================================================================


def _get_policy_adapter():
    """
    Get the L3 policy adapter.

    This is the ONLY way L2 should access policy functionality.
    F-P-RULE-1: Policy Decisions Live Only in L4.
    """
    from app.adapters.policy_adapter import get_policy_adapter

    return get_policy_adapter()


# =============================================================================
# Metrics Helpers (via L3 adapter)
# Phase F-3: These now delegate to L3 → L4 → L5 instead of L2 → L5
# =============================================================================


def _record_policy_decision(decision: str, policy_type: str) -> None:
    """Record policy decision metric via L3 adapter."""
    # No longer needed - metrics are recorded in L4 evaluate_policy
    pass


def _record_capability_violation(violation_type: str, skill_id: str, tenant_id: Optional[str] = None) -> None:
    """Record capability violation metric via L3 adapter."""
    # No longer needed - metrics are recorded in L4 check_policy_violations
    pass


def _record_budget_rejection(resource_type: str, skill_id: str) -> None:
    """Record budget rejection metric via L3 adapter."""
    # No longer needed - metrics are recorded in L4 check_policy_violations
    pass


def _record_approval_request_created(policy_type: str) -> None:
    """Record approval request creation metric via L3 adapter."""
    adapter = _get_policy_adapter()
    adapter.record_approval_created(policy_type)


def _record_approval_action(result: str) -> None:
    """Record approval action metric via L3 adapter."""
    adapter = _get_policy_adapter()
    adapter.record_approval_outcome(result)


def _record_approval_escalation() -> None:
    """Record approval escalation metric via L3 adapter."""
    adapter = _get_policy_adapter()
    adapter.record_escalation()


def _record_webhook_fallback() -> None:
    """Record webhook fallback metric via L3 adapter."""
    adapter = _get_policy_adapter()
    adapter.record_webhook_used()


# =============================================================================
# Request/Response Models
# =============================================================================


class PolicyType(str, Enum):
    """Types of policies that can be evaluated."""

    COST = "cost"
    CAPABILITY = "capability"
    RESOURCE = "resource"
    RATE_LIMIT = "rate_limit"


class ApprovalStatus(str, Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


class PolicyEvalRequest(BaseModel):
    """Request for policy sandbox evaluation."""

    skill_id: str = Field(..., description="Skill to evaluate")
    tenant_id: str = Field(..., description="Tenant context")
    agent_id: Optional[str] = Field(None, description="Agent context")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Skill parameters")
    policy_version: Optional[str] = Field(None, description="Specific policy version to use")
    simulate_cost: bool = Field(True, description="Include cost simulation")


class PolicyEvalResponse(BaseModel):
    """Response from policy sandbox evaluation."""

    decision: str = Field(..., description="allow, deny, or requires_approval")
    reasons: List[str] = Field(default_factory=list, description="Reasons for decision")
    simulated_cost_cents: Optional[int] = Field(None, description="Estimated cost")
    policy_version: str = Field(..., description="Policy version used")
    approval_level_required: Optional[int] = Field(None, description="Required approval level if denied")
    violations: List[Dict[str, Any]] = Field(default_factory=list, description="Policy violations")
    timestamp: str = Field(..., description="Evaluation timestamp")


class ApprovalRequestCreate(BaseModel):
    """Request to create an approval request."""

    policy_type: PolicyType = Field(..., description="Type of policy requiring approval")
    skill_id: str = Field(..., description="Skill requiring approval")
    tenant_id: str = Field(..., description="Tenant context")
    agent_id: Optional[str] = Field(None, description="Agent context")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Execution payload")
    requested_by: str = Field(..., description="Requester ID")
    justification: Optional[str] = Field(None, description="Why approval is needed")
    webhook_url: Optional[str] = Field(None, description="Webhook for async callback")
    webhook_secret: Optional[str] = Field(None, description="Secret for webhook HMAC")
    expires_in_seconds: int = Field(300, description="Expiration time")


class ApprovalRequestResponse(BaseModel):
    """Response when creating an approval request."""

    request_id: str
    status: ApprovalStatus
    required_level: int
    escalate_to: Optional[str]
    expires_at: str
    created_at: str


class ApprovalAction(BaseModel):
    """Action to approve or reject a request."""

    approver_id: str = Field(..., description="ID of approver")
    level: int = Field(..., ge=1, le=5, description="Approval level (1-5)")
    notes: Optional[str] = Field(None, description="Optional notes")


class ApprovalStatusResponse(BaseModel):
    """Full status of an approval request."""

    request_id: str
    correlation_id: Optional[str] = Field(None, description="Idempotency key for webhook deduplication")
    status: ApprovalStatus
    status_history: List[Dict[str, Any]] = Field(default_factory=list, description="Audit trail of status transitions")
    policy_type: PolicyType
    skill_id: str
    tenant_id: str
    agent_id: Optional[str]
    payload: Dict[str, Any]
    requested_by: str
    justification: Optional[str]
    required_level: int
    current_level: int
    approvers: List[Dict[str, Any]]
    escalate_to: Optional[str]
    webhook_attempts: int = Field(0, description="Number of webhook delivery attempts")
    last_webhook_status: Optional[str] = Field(None, description="Last webhook delivery status")
    expires_at: str
    created_at: str
    updated_at: str


# =============================================================================
# Webhook Configuration
# =============================================================================

WEBHOOK_MAX_RETRIES = 3
WEBHOOK_RETRY_DELAYS = [1, 5, 15]  # seconds

# Webhook key versioning for rotation support
# When rotating keys:
# 1. Add new key version to WEBHOOK_KEY_VERSIONS
# 2. Set WEBHOOK_CURRENT_KEY_VERSION to new version
# 3. Keep old key for grace period (WEBHOOK_KEY_GRACE_VERSIONS)
# 4. After grace period, remove old key version

WEBHOOK_CURRENT_KEY_VERSION = os.getenv("WEBHOOK_KEY_VERSION", "v1")
WEBHOOK_KEY_VERSIONS: Dict[str, str] = {
    # Version -> Secret mapping (loaded from env)
    # "v1": os.getenv("WEBHOOK_SECRET_V1", ""),
    # "v2": os.getenv("WEBHOOK_SECRET_V2", ""),
}
# Versions still accepted during rotation grace period
WEBHOOK_KEY_GRACE_VERSIONS = os.getenv("WEBHOOK_KEY_GRACE_VERSIONS", "").split(",")
WEBHOOK_KEY_GRACE_VERSIONS = [v.strip() for v in WEBHOOK_KEY_GRACE_VERSIONS if v.strip()]


# =============================================================================
# Rate Limiting Configuration
# =============================================================================

RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_DEFAULT_RPM = int(os.getenv("RATE_LIMIT_DEFAULT_RPM", "60"))  # requests per minute
RATE_LIMIT_BURST_RPM = int(os.getenv("RATE_LIMIT_BURST_RPM", "120"))  # burst limit


def _check_rate_limit(tenant_id: str, endpoint: str = "policy") -> None:
    """Check rate limit for tenant. Raises HTTPException if exceeded.

    Args:
        tenant_id: Tenant identifier for rate limiting
        endpoint: Endpoint category for different limits

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    if not RATE_LIMIT_ENABLED:
        return

    try:
        from app.utils.rate_limiter import allow_request

        key = f"tenant:{tenant_id}:{endpoint}"
        rpm = RATE_LIMIT_DEFAULT_RPM

        if not allow_request(key, rpm):
            logger.warning("rate_limit_exceeded", extra={"tenant_id": tenant_id, "endpoint": endpoint, "rpm": rpm})
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded: {rpm} requests per minute",
                    "tenant_id": tenant_id,
                    "retry_after_seconds": 60,
                },
            )
    except ImportError:
        logger.debug("Rate limiter not available - redis package may not be installed")
    except HTTPException:
        raise
    except Exception as e:
        # Fail open - allow request if rate limiter has issues
        logger.warning(f"Rate limiter error (allowing request): {e}")


# =============================================================================
# Helper Functions
# =============================================================================


def _get_policy_version() -> str:
    """Get current policy version."""
    return "v1.0.0"


def _hash_webhook_secret(secret: str) -> str:
    """Hash webhook secret for storage."""
    return hashlib.sha256(secret.encode()).hexdigest()


async def _get_approval_level_config(
    session: AsyncSession,
    policy_type: PolicyType,
    tenant_id: str,
    agent_id: Optional[str] = None,
    skill_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get approval level configuration from PolicyApprovalLevel table.
    """
    try:
        from app.db import PolicyApprovalLevel

        stmt = select(PolicyApprovalLevel).where(PolicyApprovalLevel.policy_type == policy_type.value)

        result = await session.execute(stmt)
        configs = result.scalars().all()

        # Find best match (most specific first)
        for config in configs:
            if config.tenant_id == tenant_id:
                if config.agent_id == agent_id and config.skill_id == skill_id:
                    return _config_to_dict(config)
            elif config.tenant_id is None:
                return _config_to_dict(config)

    except Exception as e:
        logger.warning(f"Failed to load approval config from DB: {e}")

    # Default configuration
    return {
        "approval_level": 3,
        "auto_approve_max_cost_cents": 100,
        "auto_approve_max_tokens": 1000,
        "escalate_to": None,
        "escalation_timeout_seconds": 300,
    }


def _config_to_dict(config) -> Dict[str, Any]:
    """Convert PolicyApprovalLevel to dict."""
    return {
        "approval_level": int(config.approval_level) if config.approval_level.isdigit() else 3,
        "auto_approve_max_cost_cents": config.auto_approve_max_cost_cents or 100,
        "auto_approve_max_tokens": config.auto_approve_max_tokens or 1000,
        "escalate_to": config.escalate_to,
        "escalation_timeout_seconds": config.escalation_timeout_seconds,
    }


async def _simulate_cost(skill_id: str, tenant_id: str, payload: Dict[str, Any]) -> Optional[int]:
    """
    Simulate cost for a skill execution via L3 adapter.

    Phase F-3: This replaces the direct L5 CostSimulator import.
    F-P-RULE-4: No Dual Ownership - CostSimulator logic stays intact in L5.
    """
    adapter = _get_policy_adapter()
    return await adapter.simulate_cost(
        skill_id=skill_id,
        tenant_id=tenant_id,
        payload=payload,
    )


async def _check_policy_violations(
    skill_id: str, tenant_id: str, agent_id: Optional[str], payload: Dict[str, Any], simulated_cost: Optional[int]
) -> List[Dict[str, Any]]:
    """
    Check for policy violations via L3 adapter.

    Phase F-3: This replaces the direct L5 PolicyEnforcer import.
    F-P-RULE-1: Policy Decisions Live Only in L4 - L4 handles enforcement.
    F-P-RULE-2: Metrics Are Effects - L4 emits metrics via L5.
    """
    adapter = _get_policy_adapter()
    return await adapter.check_policy_violations(
        skill_id=skill_id,
        tenant_id=tenant_id,
        agent_id=agent_id,
        payload=payload,
        simulated_cost=simulated_cost,
    )


def _compute_webhook_signature(payload: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature for webhook."""
    import hmac

    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


async def _send_webhook(
    url: str,
    payload: Dict[str, Any],
    secret: Optional[str] = None,
    key_version: Optional[str] = None,
    retry_count: int = 0,
) -> bool:
    """Send webhook callback with retry logic and key versioning.

    Args:
        url: Webhook endpoint URL
        payload: JSON payload to send
        secret: HMAC secret for signing
        key_version: Version of the key used for signing (for rotation support)
        retry_count: Current retry attempt

    Returns:
        True if webhook delivered successfully
    """
    try:
        headers = {"Content-Type": "application/json"}
        body = json.dumps(payload)

        if secret:
            signature = _compute_webhook_signature(body, secret)
            headers["X-Webhook-Signature"] = f"sha256={signature}"
            # Add key version header for rotation support
            version = key_version or WEBHOOK_CURRENT_KEY_VERSION
            headers["X-Webhook-Key-Version"] = version
            logger.debug(f"Webhook signed with key version: {version}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=body, headers=headers)

            if 200 <= response.status_code < 300:
                logger.info(f"Webhook sent successfully to {url}")
                return True
            else:
                logger.warning(f"Webhook failed with status {response.status_code}")

    except Exception as e:
        logger.error(f"Webhook error: {e}")

    if retry_count < WEBHOOK_MAX_RETRIES:
        delay = WEBHOOK_RETRY_DELAYS[retry_count]
        logger.info(f"Retrying webhook in {delay}s (attempt {retry_count + 1})")
        await asyncio.sleep(delay)
        return await _send_webhook(url, payload, secret, key_version, retry_count + 1)

    logger.error(f"Webhook fallback: Failed to deliver to {url}")
    # Record fallback metric
    _record_webhook_fallback()
    return False


def verify_webhook_signature(body: str, signature: str, key_version: str, secrets: Dict[str, str]) -> bool:
    """Verify webhook signature with version support for rotation.

    During key rotation, accepts signatures from:
    1. Current key version
    2. Any version in grace period (WEBHOOK_KEY_GRACE_VERSIONS)

    Args:
        body: Raw request body
        signature: Signature from X-Webhook-Signature header (sha256=...)
        key_version: Version from X-Webhook-Key-Version header
        secrets: Dict mapping version -> secret

    Returns:
        True if signature is valid
    """
    if not signature.startswith("sha256="):
        return False

    provided_sig = signature[7:]  # Remove "sha256=" prefix

    # Try the specified version first
    if key_version in secrets:
        expected = _compute_webhook_signature(body, secrets[key_version])
        if hmac.compare_digest(expected, provided_sig):
            return True

    # During rotation, also accept grace period versions
    for grace_version in WEBHOOK_KEY_GRACE_VERSIONS:
        if grace_version in secrets and grace_version != key_version:
            expected = _compute_webhook_signature(body, secrets[grace_version])
            if hmac.compare_digest(expected, provided_sig):
                logger.info(f"Webhook verified with grace period key: {grace_version}")
                return True

    return False


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/eval", response_model=PolicyEvalResponse)
async def evaluate_policy(
    request: PolicyEvalRequest,
    session: AsyncSession = Depends(get_async_session),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("policy.audit")),
) -> PolicyEvalResponse:
    """
    Sandbox evaluation of policy for a skill execution.

    **Tier: PREVENT ($199)** - Pre-execution policy evaluation. "You stop the fire."
    """
    # Rate limiting per tenant
    _check_rate_limit(request.tenant_id, "policy_eval")

    timestamp = datetime.now(timezone.utc).isoformat()
    policy_version = request.policy_version or _get_policy_version()

    # Simulate cost if requested
    simulated_cost = None
    if request.simulate_cost:
        simulated_cost = await _simulate_cost(
            skill_id=request.skill_id, tenant_id=request.tenant_id, payload=request.payload
        )

    # Check for policy violations
    violations = await _check_policy_violations(
        skill_id=request.skill_id,
        tenant_id=request.tenant_id,
        agent_id=request.agent_id,
        payload=request.payload,
        simulated_cost=simulated_cost,
    )

    # Get approval level config
    config = await _get_approval_level_config(
        session=session,
        policy_type=PolicyType.COST,
        tenant_id=request.tenant_id,
        agent_id=request.agent_id,
        skill_id=request.skill_id,
    )

    # Determine decision
    if not violations:
        auto_approve_cost = config.get("auto_approve_max_cost_cents", 0)
        if simulated_cost is not None and simulated_cost <= auto_approve_cost:
            decision = "allow"
            reasons = ["Within auto-approve threshold"]
        else:
            decision = "allow"
            reasons = ["No policy violations"]
        _record_policy_decision("allow", "cost")
    else:
        decision = "deny"
        reasons = [v["message"] for v in violations]

        overridable = all(v.get("type") in ("BudgetExceededError", "PolicyViolationError") for v in violations)
        if overridable:
            decision = "requires_approval"
            reasons.append(f"Requires level {config['approval_level']} approval")

        _record_policy_decision(decision, "cost")

    return PolicyEvalResponse(
        decision=decision,
        reasons=reasons,
        simulated_cost_cents=simulated_cost,
        policy_version=policy_version,
        approval_level_required=config["approval_level"] if decision == "requires_approval" else None,
        violations=violations,
        timestamp=timestamp,
    )


@router.post("/requests", response_model=ApprovalRequestResponse)
async def create_approval_request(
    request: ApprovalRequestCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
) -> ApprovalRequestResponse:
    """
    Create a new approval request (persisted to DB).
    """
    # Rate limiting per tenant
    _check_rate_limit(request.tenant_id, "approval_create")

    from app.db import ApprovalRequest as ApprovalRequestModel

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=request.expires_in_seconds)

    # Get approval level config
    config = await _get_approval_level_config(
        session=session,
        policy_type=request.policy_type,
        tenant_id=request.tenant_id,
        agent_id=request.agent_id,
        skill_id=request.skill_id,
    )

    # Create DB model - PERSIST FIRST before any external calls
    approval = ApprovalRequestModel(
        policy_type=request.policy_type.value,
        skill_id=request.skill_id,
        tenant_id=request.tenant_id,
        agent_id=request.agent_id,
        requested_by=request.requested_by,
        justification=request.justification,
        required_level=config["approval_level"],
        escalate_to=config.get("escalate_to"),
        escalation_timeout_seconds=config.get("escalation_timeout_seconds", 300),
        webhook_url=request.webhook_url,
        webhook_secret_hash=_hash_webhook_secret(request.webhook_secret) if request.webhook_secret else None,
        expires_at=expires_at,
    )
    approval.set_payload(request.payload)

    session.add(approval)
    await session.commit()
    await session.refresh(approval)

    # Record metric
    _record_approval_request_created(request.policy_type.value)

    logger.info(f"Created approval request {approval.id} for {request.skill_id}")

    # Send initial webhook if configured (after DB persist)
    if request.webhook_url:
        background_tasks.add_task(
            _send_webhook,
            request.webhook_url,
            {
                "event": "approval_request_created",
                "request_id": approval.id,
                "status": ApprovalStatus.PENDING.value,
                "required_level": config["approval_level"],
                "expires_at": expires_at.isoformat(),
            },
            request.webhook_secret,
        )

    return ApprovalRequestResponse(
        request_id=approval.id,
        status=ApprovalStatus.PENDING,
        required_level=config["approval_level"],
        escalate_to=config.get("escalate_to"),
        expires_at=expires_at.isoformat(),
        created_at=approval.created_at.isoformat(),
    )


@router.get("/requests/{request_id}", response_model=ApprovalStatusResponse)
async def get_approval_request(
    request_id: str, session: AsyncSession = Depends(get_async_session)
) -> ApprovalStatusResponse:
    """Get the current status of an approval request."""
    from app.db import ApprovalRequest as ApprovalRequestModel

    approval = await session.get(ApprovalRequestModel, request_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    # Check if expired
    now = datetime.now(timezone.utc)
    expires_at = (
        approval.expires_at.replace(tzinfo=timezone.utc) if approval.expires_at.tzinfo is None else approval.expires_at
    )

    if now > expires_at and approval.status == "pending":
        approval.status = "expired"
        approval.updated_at = now
        await session.commit()
        _record_approval_action("expired")

    data = approval.to_dict()
    return ApprovalStatusResponse(
        request_id=data["request_id"],
        correlation_id=data.get("correlation_id"),
        status=ApprovalStatus(data["status"]),
        status_history=data.get("status_history", []),
        policy_type=PolicyType(data["policy_type"]),
        skill_id=data["skill_id"],
        tenant_id=data["tenant_id"],
        agent_id=data["agent_id"],
        payload=data["payload"],
        requested_by=data["requested_by"],
        justification=data["justification"],
        required_level=data["required_level"],
        current_level=data["current_level"],
        approvers=data["approvers"],
        escalate_to=data["escalate_to"],
        webhook_attempts=data.get("webhook_attempts", 0),
        last_webhook_status=data.get("last_webhook_status"),
        expires_at=data["expires_at"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _check_approver_authorization(approver_id: str, level: int, tenant_id: Optional[str] = None) -> None:
    """
    RBAC: Verify approver has permission to approve at the given level.

    Uses the RBAC module when RBAC_ENABLED=true, otherwise allows all approvals.

    Approval Levels:
    - Level 1-2: Any authenticated user (team_member, engineer)
    - Level 3: Team lead, senior_engineer, tech_lead
    - Level 4: Manager, director, policy_admin
    - Level 5: Owner override (requires audit)

    Raises:
        HTTPException: If approver lacks required permissions
    """
    try:
        from app.auth.rbac import RBAC_ENABLED, RBACError, check_approver_permission

        if not RBAC_ENABLED:
            # RBAC disabled - allow all but log level 5
            if level >= 5:
                logger.warning(
                    "level5_approval_rbac_disabled",
                    extra={
                        "approver_id": approver_id,
                        "level": level,
                        "tenant_id": tenant_id,
                        "warning": "RBAC disabled - owner override allowed without verification",
                    },
                )
            return

        # RBAC enabled - perform full authorization check
        result = check_approver_permission(approver_id=approver_id, required_level=level, tenant_id=tenant_id)

        logger.info(
            "rbac_authorization_success",
            extra={
                "approver_id": approver_id,
                "required_level": level,
                "granted_level": result.granted_level,
                "roles": result.roles,
                "tenant_id": tenant_id,
            },
        )

    except ImportError:
        # RBAC module not available - allow with warning
        logger.warning("RBAC module not available - allowing approval without verification")
        if level >= 5:
            logger.warning(f"Level 5 (owner override) approval by {approver_id} - requires audit")

    except RBACError as e:
        logger.warning(
            "rbac_authorization_denied",
            extra={
                "approver_id": approver_id,
                "required_level": e.required_level,
                "message": e.message,
                "tenant_id": tenant_id,
            },
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "authorization_denied",
                "message": e.message,
                "approver_id": approver_id,
                "required_level": e.required_level,
            },
        )


@router.post("/requests/{request_id}/approve", response_model=ApprovalStatusResponse)
async def approve_request(
    request_id: str,
    action: ApprovalAction,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
) -> ApprovalStatusResponse:
    """Approve an approval request."""
    from app.db import ApprovalRequest as ApprovalRequestModel

    approval = await session.get(ApprovalRequestModel, request_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    # RBAC check: verify approver can approve at this level
    _check_approver_authorization(action.approver_id, action.level, approval.tenant_id)

    if approval.status not in ("pending", "escalated"):
        raise HTTPException(status_code=400, detail=f"Cannot approve request in status {approval.status}")

    # Check expiration
    now = datetime.now(timezone.utc)
    expires_at = (
        approval.expires_at.replace(tzinfo=timezone.utc) if approval.expires_at.tzinfo is None else approval.expires_at
    )

    if now > expires_at:
        approval.status = "expired"
        approval.updated_at = now
        await session.commit()
        raise HTTPException(status_code=400, detail="Approval request has expired")

    # Record the approval
    approval.add_approval(action.approver_id, action.level, "approve", action.notes)

    # Check if fully approved
    if approval.current_level >= approval.required_level:
        approval.transition_status("approved", actor=action.approver_id, reason=f"Approved at level {action.level}")
        approval.resolved_at = now

    await session.commit()

    # Record metric
    if approval.status == "approved":
        _record_approval_action("approved")

    logger.info(f"Approval request {request_id} approved by {action.approver_id} (level {action.level})")

    # Send webhook if configured (with correlation_id for idempotency)
    if approval.webhook_url:
        background_tasks.add_task(
            _send_webhook,
            approval.webhook_url,
            {
                "event": "approval_request_approved" if approval.status == "approved" else "approval_added",
                "request_id": request_id,
                "correlation_id": approval.correlation_id,
                "status": approval.status,
                "approver_id": action.approver_id,
                "level": action.level,
            },
            None,  # Secret not stored in plain text
        )

    return await get_approval_request(request_id, session)


@router.post("/requests/{request_id}/reject", response_model=ApprovalStatusResponse)
async def reject_request(
    request_id: str,
    action: ApprovalAction,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
) -> ApprovalStatusResponse:
    """Reject an approval request."""
    from app.db import ApprovalRequest as ApprovalRequestModel

    approval = await session.get(ApprovalRequestModel, request_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    # RBAC check: verify rejector can reject at this level
    _check_approver_authorization(action.approver_id, action.level, approval.tenant_id)

    if approval.status not in ("pending", "escalated"):
        raise HTTPException(status_code=400, detail=f"Cannot reject request in status {approval.status}")

    now = datetime.now(timezone.utc)
    approval.add_approval(action.approver_id, action.level, "reject", action.notes)
    approval.transition_status("rejected", actor=action.approver_id, reason=action.notes or "Rejected")
    approval.resolved_at = now
    await session.commit()

    # Record metric
    _record_approval_action("rejected")

    logger.info(f"Approval request {request_id} rejected by {action.approver_id}")

    if approval.webhook_url:
        background_tasks.add_task(
            _send_webhook,
            approval.webhook_url,
            {
                "event": "approval_request_rejected",
                "request_id": request_id,
                "status": "rejected",
                "rejector_id": action.approver_id,
            },
            None,
        )

    return await get_approval_request(request_id, session)


@router.get("/requests", response_model=List[ApprovalStatusResponse])
async def list_approval_requests(
    status: Optional[ApprovalStatus] = None,
    tenant_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
) -> List[ApprovalStatusResponse]:
    """List approval requests with optional filtering."""
    from app.db import ApprovalRequest as ApprovalRequestModel

    stmt = select(ApprovalRequestModel)

    if status:
        stmt = stmt.where(ApprovalRequestModel.status == status.value)
    if tenant_id:
        stmt = stmt.where(ApprovalRequestModel.tenant_id == tenant_id)

    stmt = stmt.order_by(cast(Any, ApprovalRequestModel.created_at).desc())
    stmt = stmt.offset(offset).limit(limit)

    result = await session.execute(stmt)
    results = result.scalars().all()

    responses = []
    now = datetime.now(timezone.utc)

    for approval in results:
        # Check expiration
        expires_at = (
            approval.expires_at.replace(tzinfo=timezone.utc)
            if approval.expires_at.tzinfo is None
            else approval.expires_at
        )
        if now > expires_at and approval.status == "pending":
            approval.status = "expired"
            approval.updated_at = now

        data = approval.to_dict()
        responses.append(
            ApprovalStatusResponse(
                request_id=data["request_id"],
                correlation_id=data.get("correlation_id"),
                status=ApprovalStatus(data["status"]),
                status_history=data.get("status_history", []),
                policy_type=PolicyType(data["policy_type"]),
                skill_id=data["skill_id"],
                tenant_id=data["tenant_id"],
                agent_id=data["agent_id"],
                payload=data["payload"],
                requested_by=data["requested_by"],
                justification=data["justification"],
                required_level=data["required_level"],
                current_level=data["current_level"],
                approvers=data["approvers"],
                escalate_to=data["escalate_to"],
                webhook_attempts=data.get("webhook_attempts", 0),
                last_webhook_status=data.get("last_webhook_status"),
                expires_at=data["expires_at"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
            )
        )

    await session.commit()
    return wrap_dict({"items": [r.model_dump() for r in responses], "total": len(responses)})


# =============================================================================
# Escalation Worker (called by scheduler)
# =============================================================================


async def run_escalation_check(session: AsyncSession) -> int:
    """
    Check for pending requests that need escalation.
    Called by external scheduler (cron/celery).
    """
    from app.db import ApprovalRequest as ApprovalRequestModel

    now = datetime.now(timezone.utc)
    escalated_count = 0

    # Find pending requests past their escalation timeout
    stmt = select(ApprovalRequestModel).where(ApprovalRequestModel.status == "pending")

    result = await session.execute(stmt)
    results = result.scalars().all()

    for approval in results:
        created_at = (
            approval.created_at.replace(tzinfo=timezone.utc)
            if approval.created_at.tzinfo is None
            else approval.created_at
        )
        timeout = timedelta(seconds=approval.escalation_timeout_seconds)

        if now - created_at > timeout:
            approval.transition_status(
                "escalated", actor="escalation_worker", reason=f"Timeout after {timeout.total_seconds()}s"
            )
            escalated_count += 1

            # Record escalation metric
            _record_approval_escalation()

            logger.info(f"Escalated approval request {approval.id} after {timeout.total_seconds()}s")

            if approval.webhook_url:
                await _send_webhook(
                    approval.webhook_url,
                    {
                        "event": "approval_request_escalated",
                        "request_id": approval.id,
                        "correlation_id": approval.correlation_id,
                        "status": "escalated",
                        "escalate_to": approval.escalate_to,
                    },
                    None,
                )

    await session.commit()

    if escalated_count > 0:
        logger.info(f"Escalation check complete: {escalated_count} requests escalated")

    return escalated_count


# =============================================================================
# Scheduled Task Entry Point
# =============================================================================


def run_escalation_task():
    """
    Entry point for scheduled escalation check.
    Can be called from cron, celery, or APScheduler.
    """
    import asyncio

    from app.db_async import AsyncSessionLocal

    async def _run():
        async with AsyncSessionLocal() as session:
            return await run_escalation_check(session)

    return asyncio.run(_run())


# =============================================================================
# POLICY V2 FACADE — Cross-Domain Authority Endpoints (PIN-447)
# =============================================================================
#
# These endpoints form the V2 facade layer for cross-domain access.
# Domains (Activity, Incidents) MUST use these endpoints, not internal APIs.
#
# Reference: docs/architecture/policies/POLICY_DOMAIN_V2_DESIGN.md
# Contract: docs/contracts/CROSS_DOMAIN_POLICY_CONTRACT.md
# =============================================================================


# =============================================================================
# Governance Metadata Schema (PIN-447 — aos_sdk-grade traceability)
# =============================================================================


class PolicyMetadata(BaseModel):
    """
    Governance metadata for policy artifacts (aos_sdk-grade).

    STATUS: DECLARED (PARTIALLY MATERIALIZED)
    Reference: docs/contracts/CROSS_DOMAIN_INVARIANTS.md Section IX
    Maturity: docs/contracts/METADATA_MATURITY.md

    Provides provenance, lifecycle, and accountability traceability
    for cross-domain consumers per CROSS_DOMAIN_INVARIANTS.md.

    NULL SEMANTICS (INV-META-NULL-001):
    ===================================
    A null field means "NOT YET MATERIALIZED", not "NOT APPLICABLE" or "DENIED".
    Consumers MUST NOT:
    - Branch on `field is None` to infer absence
    - Treat null as negative truth (e.g., null approved_by ≠ rejected)
    - Auto-populate nulls with system actors

    FIELD CLASSIFICATION:
    =====================
    Class A (Immutable Provenance) — DB-backed, never changes once written:
      - created_by, created_at, origin, source_proposal_id

    Class B (Governance Decisions) — Human-gated, requires workflow:
      - approved_by, approved_at (null until proposal workflow is real)

    Class C (Temporal Validity) — Required before historical analytics:
      - effective_from, effective_until (default: effective_from = created_at)
    """

    # CLASS A — Immutable Provenance (MATERIALIZED)
    created_by: Optional[str] = None  # actor_id who created (null = system-generated)
    created_at: datetime  # when created (REQUIRED - always present)
    origin: str  # SYSTEM_DEFAULT, MANUAL, LEARNED, INCIDENT, MIGRATION (REQUIRED)
    source_proposal_id: Optional[str] = None  # if promoted from proposal

    # CLASS B — Governance Decisions (DECLARED, NOT MATERIALIZED)
    approved_by: Optional[str] = None  # actor_id who approved (null = pending or N/A)
    approved_at: Optional[datetime] = None  # when approved (null = pending or N/A)

    # CLASS C — Temporal Validity (DECLARED, NOT MATERIALIZED)
    effective_from: Optional[datetime] = None  # start of validity (null = created_at)
    effective_until: Optional[datetime] = None  # end of validity (null = no expiry)

    # Updated tracking
    updated_at: Optional[datetime] = None  # last modification time


def _build_policy_metadata_from_rule(rule) -> PolicyMetadata:
    """
    Build PolicyMetadata from a PolicyRule model instance.

    Maps available model fields to governance metadata schema.
    Fields not in the model are left as None (to be populated when
    the underlying schema evolves).
    """
    return PolicyMetadata(
        created_by=getattr(rule, "created_by", None),
        created_at=rule.created_at,
        approved_by=None,  # Not yet in PolicyRule model
        approved_at=None,  # Not yet in PolicyRule model
        effective_from=None,  # Not yet in PolicyRule model
        effective_until=None,  # Not yet in PolicyRule model
        origin=rule.source,  # MANUAL, SYSTEM, LEARNED maps to origin
        source_proposal_id=getattr(rule, "source_proposal_id", None),
        updated_at=getattr(rule, "updated_at", None),
    )


def _build_policy_metadata_from_limit(limit) -> PolicyMetadata:
    """
    Build PolicyMetadata from a Limit model instance.

    Maps available model fields to governance metadata schema.
    """
    return PolicyMetadata(
        created_by=None,  # Not in Limit model
        created_at=limit.created_at,
        approved_by=None,  # Not in Limit model
        approved_at=None,  # Not in Limit model
        effective_from=None,  # Not in Limit model
        effective_until=None,  # Not in Limit model
        origin="MANUAL",  # Limits are typically manually configured
        source_proposal_id=None,
        updated_at=getattr(limit, "updated_at", None),
    )


def _build_policy_metadata_from_violation(v) -> PolicyMetadata:
    """
    Build PolicyMetadata from a violation object (from policy engine).

    Violations are system-generated enforcement events.
    """
    return PolicyMetadata(
        created_by=None,  # System-generated
        created_at=v.detected_at,
        approved_by=None,  # Violations don't need approval
        approved_at=None,
        effective_from=None,
        effective_until=None,
        origin="SYSTEM",  # Violations are always system-generated
        source_proposal_id=None,
        updated_at=None,  # Violations are immutable
    )


def _build_policy_metadata_from_lesson(lesson: dict) -> PolicyMetadata:
    """
    Build PolicyMetadata from a lesson dict (from lessons_learned_engine).

    Maps available dict fields to governance metadata schema.
    """
    created_at_str = lesson.get("created_at")
    created_at = (
        datetime.fromisoformat(created_at_str)
        if created_at_str
        else datetime.now(timezone.utc)
    )

    converted_at_str = lesson.get("converted_at")
    converted_at = (
        datetime.fromisoformat(converted_at_str)
        if converted_at_str
        else None
    )

    # Lessons originate from incidents or system detection
    origin = "INCIDENT" if lesson.get("source_event_id") else "SYSTEM"

    return PolicyMetadata(
        created_by=lesson.get("created_by"),  # May be system or operator
        created_at=created_at,
        approved_by=None,  # Lessons in DRAFT don't have approval yet
        approved_at=converted_at,  # Conversion time acts as informal approval
        effective_from=None,  # Lessons don't have temporal validity
        effective_until=lesson.get("deferred_until"),  # Deferred lessons have end time
        origin=origin,
        source_proposal_id=lesson.get("draft_proposal_id"),
        updated_at=None,  # Lessons are immutable once created
    )


class PolicyContextSummary(BaseModel):
    """Summary of an active policy for cross-domain consumption."""

    policy_id: str
    policy_name: str
    status: str  # ACTIVE
    enforcement_mode: str  # BLOCK, WARN, AUDIT, DISABLED
    scope: str  # GLOBAL, TENANT, PROJECT, AGENT
    source: str  # MANUAL, SYSTEM, LEARNED
    created_at: datetime
    # Facade reference (navigable)
    facade_ref: str  # "/policy/active/{policy_id}"
    # Governance metadata (PIN-447 — aos_sdk-grade traceability)
    metadata: Optional[PolicyMetadata] = None


class ActivePoliciesResponse(BaseModel):
    """GET /policy/active response — What governs execution now?"""

    items: List[PolicyContextSummary]
    total: int
    has_more: bool
    # Cross-domain navigation hint
    library_ref: str = "/policy/library"


class PolicyLibrarySummary(BaseModel):
    """Summary of a policy rule in the library."""

    rule_id: str
    name: str
    enforcement_mode: str
    scope: str
    source: str
    status: str  # ACTIVE, RETIRED
    rule_type: Optional[str] = None  # SYSTEM, SAFETY, ETHICAL, TEMPORAL
    created_at: datetime
    facade_ref: str  # "/policy/library/{rule_id}"
    # Governance metadata (PIN-447 — aos_sdk-grade traceability)
    metadata: Optional[PolicyMetadata] = None


class PolicyLibraryResponse(BaseModel):
    """GET /policy/library response — What patterns are available?"""

    items: List[PolicyLibrarySummary]
    total: int
    has_more: bool


class PolicyLessonSummary(BaseModel):
    """Summary of a lesson or draft for cross-domain consumption."""

    lesson_id: str
    title: str
    lesson_type: str  # failure, near_threshold, critical_success
    status: str  # pending, converted_to_draft, deferred, dismissed
    severity: Optional[str] = None  # CRITICAL, HIGH, MEDIUM, LOW
    source_event_type: str
    has_proposed_action: bool
    created_at: datetime
    facade_ref: str  # "/policy/lessons/{lesson_id}"
    # Governance metadata (PIN-447 — aos_sdk-grade traceability)
    metadata: Optional[PolicyMetadata] = None


class LessonsResponse(BaseModel):
    """GET /policy/lessons response — What governance emerged?"""

    items: List[PolicyLessonSummary]
    total: int
    has_more: bool
    pending_count: int
    converted_count: int


class ThresholdSummary(BaseModel):
    """Summary of an enforced limit/threshold."""

    threshold_id: str
    name: str
    limit_category: str  # BUDGET, RATE, THRESHOLD
    limit_type: str  # COST_USD, TOKENS_*, etc.
    scope: str
    enforcement: str  # BLOCK, WARN, REJECT, etc.
    max_value: str  # String for Decimal serialization
    status: str  # ACTIVE, DISABLED
    facade_ref: str  # "/policy/thresholds/{threshold_id}"
    # Governance metadata (PIN-447 — aos_sdk-grade traceability)
    metadata: Optional[PolicyMetadata] = None


class ThresholdsResponse(BaseModel):
    """GET /policy/thresholds response — What limits are enforced?"""

    items: List[ThresholdSummary]
    total: int
    has_more: bool


class ViolationSummary(BaseModel):
    """Summary of a policy violation for cross-domain consumption."""

    violation_id: str
    policy_id: Optional[str] = None
    policy_name: Optional[str] = None
    violation_type: str
    severity: float
    source: str  # guard, sim, runtime
    occurred_at: datetime
    facade_ref: str  # "/policy/violations/{violation_id}"
    # Cross-domain linking
    run_id: Optional[str] = None
    # Governance metadata (PIN-447 — aos_sdk-grade traceability)
    metadata: Optional[PolicyMetadata] = None


class ViolationsResponse(BaseModel):
    """GET /policy/violations response — What enforcement occurred?"""

    items: List[ViolationSummary]
    total: int
    has_more: bool


# =============================================================================
# V2 Facade: GET /policy/active
# =============================================================================


@router.get(
    "/active",
    response_model=ActivePoliciesResponse,
    summary="Active policies (V2 Facade)",
    description="""
    Returns currently active policies that govern execution.

    **Cross-Domain Usage:** Activity and Incidents domains use this
    endpoint to embed policy_context in their responses.

    Reference: PIN-447, CROSS_DOMAIN_POLICY_CONTRACT.md
    """,
    tags=["policy-v2-facade"],
)
async def get_active_policies(
    scope: Optional[str] = None,
    enforcement_mode: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    ctx: TenantContext = Depends(get_tenant_context),
) -> ActivePoliciesResponse:
    """V2 Facade: What governs execution now?"""
    from sqlalchemy import and_, select

    from app.models.policy_control_plane import PolicyRule

    try:
        # Build query for active policies
        stmt = select(PolicyRule).where(
            and_(
                PolicyRule.tenant_id == ctx.tenant_id,
                PolicyRule.status == "ACTIVE",
            )
        )

        if scope:
            stmt = stmt.where(PolicyRule.scope == scope)
        if enforcement_mode:
            stmt = stmt.where(PolicyRule.enforcement_mode == enforcement_mode)

        # Count total
        from sqlalchemy import func

        count_stmt = select(func.count(PolicyRule.id)).where(
            and_(
                PolicyRule.tenant_id == ctx.tenant_id,
                PolicyRule.status == "ACTIVE",
            )
        )
        if scope:
            count_stmt = count_stmt.where(PolicyRule.scope == scope)
        if enforcement_mode:
            count_stmt = count_stmt.where(PolicyRule.enforcement_mode == enforcement_mode)

        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Execute with pagination
        stmt = stmt.order_by(PolicyRule.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        rules = result.scalars().all()

        items = [
            PolicyContextSummary(
                policy_id=str(rule.id),
                policy_name=rule.name,
                status=rule.status,
                enforcement_mode=rule.enforcement_mode,
                scope=rule.scope,
                source=rule.source,
                created_at=rule.created_at,
                facade_ref=f"/policy/active/{rule.id}",
                metadata=_build_policy_metadata_from_rule(rule),
            )
            for rule in rules
        ]

        return ActivePoliciesResponse(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
            library_ref="/policy/library",
        )

    except Exception as e:
        logger.exception("Failed to get active policies")
        raise HTTPException(status_code=500, detail={"error": "query_failed", "message": str(e)})


# =============================================================================
# V2 Facade: GET /policy/active/{policy_id}
# =============================================================================


@router.get(
    "/active/{policy_id}",
    summary="Active policy detail (V2 Facade)",
    description="Returns detail of a specific active policy.",
    tags=["policy-v2-facade"],
)
async def get_active_policy_detail(
    policy_id: str,
    session: AsyncSession = Depends(get_async_session),
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    """V2 Facade: Policy detail for cross-domain navigation."""
    from sqlalchemy import and_, select

    from app.models.policy_control_plane import PolicyRule, PolicyRuleIntegrity

    try:
        stmt = (
            select(PolicyRule, PolicyRuleIntegrity.integrity_status, PolicyRuleIntegrity.integrity_score)
            .outerjoin(PolicyRuleIntegrity, PolicyRuleIntegrity.rule_id == PolicyRule.id)
            .where(
                and_(
                    PolicyRule.id == policy_id,
                    PolicyRule.tenant_id == ctx.tenant_id,
                )
            )
        )

        result = await session.execute(stmt)
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail="Policy not found")

        rule = row[0]

        return wrap_dict(
            {
                "policy_id": str(rule.id),
                "policy_name": rule.name,
                "description": getattr(rule, "description", None),
                "status": rule.status,
                "enforcement_mode": rule.enforcement_mode,
                "scope": rule.scope,
                "source": rule.source,
                "rule_type": getattr(rule, "rule_type", None),
                "rule_definition": getattr(rule, "rule_definition", None),
                "created_at": rule.created_at.isoformat() if rule.created_at else None,
                "updated_at": rule.updated_at.isoformat() if getattr(rule, "updated_at", None) else None,
                "integrity_status": row[1] if row[1] else "UNKNOWN",
                "integrity_score": str(row[2]) if row[2] else "0",
                "facade_ref": f"/policy/active/{rule.id}",
                # Cross-domain references
                "thresholds_ref": "/policy/thresholds",
                "violations_ref": "/policy/violations",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get policy detail")
        raise HTTPException(status_code=500, detail={"error": "query_failed", "message": str(e)})


# =============================================================================
# V2 Facade: GET /policy/library
# =============================================================================


@router.get(
    "/library",
    response_model=PolicyLibraryResponse,
    summary="Policy library (V2 Facade)",
    description="""
    Returns all available policy patterns (active and retired).

    **Cross-Domain Usage:** Provides the policy catalog for reference.

    Reference: PIN-447
    """,
    tags=["policy-v2-facade"],
)
async def get_policy_library(
    status: Optional[str] = None,  # None = all, ACTIVE, RETIRED
    rule_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    ctx: TenantContext = Depends(get_tenant_context),
) -> PolicyLibraryResponse:
    """V2 Facade: What patterns are available?"""
    from sqlalchemy import select

    from app.models.policy_control_plane import PolicyRule

    try:
        stmt = select(PolicyRule).where(PolicyRule.tenant_id == ctx.tenant_id)

        if status:
            stmt = stmt.where(PolicyRule.status == status)
        if rule_type:
            stmt = stmt.where(PolicyRule.rule_type == rule_type)

        # Count
        from sqlalchemy import func

        count_stmt = select(func.count(PolicyRule.id)).where(PolicyRule.tenant_id == ctx.tenant_id)
        if status:
            count_stmt = count_stmt.where(PolicyRule.status == status)
        if rule_type:
            count_stmt = count_stmt.where(PolicyRule.rule_type == rule_type)

        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = stmt.order_by(PolicyRule.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        rules = result.scalars().all()

        items = [
            PolicyLibrarySummary(
                rule_id=str(rule.id),
                name=rule.name,
                enforcement_mode=rule.enforcement_mode,
                scope=rule.scope,
                source=rule.source,
                status=rule.status,
                rule_type=getattr(rule, "rule_type", None),
                created_at=rule.created_at,
                facade_ref=f"/policy/library/{rule.id}",
                metadata=_build_policy_metadata_from_rule(rule),
            )
            for rule in rules
        ]

        return PolicyLibraryResponse(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
        )

    except Exception as e:
        logger.exception("Failed to get policy library")
        raise HTTPException(status_code=500, detail={"error": "query_failed", "message": str(e)})


# =============================================================================
# V2 Facade: GET /policy/lessons
# =============================================================================


@router.get(
    "/lessons",
    response_model=LessonsResponse,
    summary="Policy lessons (V2 Facade)",
    description="""
    Returns lessons learned and governance that emerged from execution.

    **Cross-Domain Usage:** Incidents domain links to lessons via lesson_ref
    when resolving incidents.

    Reference: PIN-447, CROSS_DOMAIN_POLICY_CONTRACT.md
    """,
    tags=["policy-v2-facade"],
)
async def get_policy_lessons(
    status: Optional[str] = None,  # pending, converted_to_draft, deferred, dismissed
    lesson_type: Optional[str] = None,  # failure, near_threshold, critical_success
    limit: int = 50,
    offset: int = 0,
    ctx: TenantContext = Depends(get_tenant_context),
) -> LessonsResponse:
    """V2 Facade: What governance emerged?"""
    # L4 operation registry dispatch (replaced L5 inline import per HOC Topology V2)
    registry = get_operation_registry()

    try:
        # Fetch lessons via registry
        lessons_op = await registry.execute(
            "policies.lessons",
            OperationContext(
                session=None,
                tenant_id=ctx.tenant_id,
                params={
                    "method": "list_lessons",
                    "lesson_type": lesson_type,
                    "status": status,
                    "limit": limit,
                    "offset": offset,
                },
            ),
        )
        if not lessons_op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": lessons_op.error})
        lessons = lessons_op.data

        # Fetch stats via registry
        stats_op = await registry.execute(
            "policies.lessons",
            OperationContext(
                session=None,
                tenant_id=ctx.tenant_id,
                params={"method": "get_lesson_stats"},
            ),
        )
        if not stats_op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": stats_op.error})
        stats = stats_op.data

        items = [
            PolicyLessonSummary(
                lesson_id=lesson["id"],
                title=lesson["title"],
                lesson_type=lesson["lesson_type"],
                status=lesson["status"],
                severity=lesson.get("severity"),
                source_event_type=lesson["source_event_type"],
                has_proposed_action=lesson["has_proposed_action"],
                created_at=datetime.fromisoformat(lesson["created_at"]) if lesson["created_at"] else datetime.utcnow(),
                facade_ref=f"/policy/lessons/{lesson['id']}",
                metadata=_build_policy_metadata_from_lesson(lesson),
            )
            for lesson in lessons
        ]

        return LessonsResponse(
            items=items,
            total=len(items),
            has_more=len(items) == limit,
            pending_count=stats.get("by_status", {}).get("pending", 0),
            converted_count=stats.get("by_status", {}).get("converted_to_draft", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get lessons")
        raise HTTPException(status_code=500, detail={"error": "query_failed", "message": str(e)})


# =============================================================================
# V2 Facade: GET /policy/lessons/{lesson_id}
# =============================================================================


@router.get(
    "/lessons/{lesson_id}",
    summary="Lesson detail (V2 Facade)",
    description="Returns detail of a specific lesson.",
    tags=["policy-v2-facade"],
)
async def get_policy_lesson_detail(
    lesson_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    """V2 Facade: Lesson detail for cross-domain navigation."""
    from uuid import UUID

    # L4 operation registry dispatch (replaced L5 inline import per HOC Topology V2)
    registry = get_operation_registry()

    try:
        op = await registry.execute(
            "policies.lessons",
            OperationContext(
                session=None,
                tenant_id=ctx.tenant_id,
                params={"method": "get_lesson", "lesson_id": str(UUID(lesson_id))},
            ),
        )
        if not op.success:
            raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})
        lesson = op.data

        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        return wrap_dict(
            {
                "lesson_id": lesson["id"],
                "title": lesson["title"],
                "description": lesson["description"],
                "lesson_type": lesson["lesson_type"],
                "status": lesson["status"],
                "severity": lesson.get("severity"),
                "source_event_id": lesson.get("source_event_id"),
                "source_event_type": lesson["source_event_type"],
                "source_run_id": lesson.get("source_run_id"),
                "proposed_action": lesson.get("proposed_action"),
                "detected_pattern": lesson.get("detected_pattern"),
                "draft_proposal_id": lesson.get("draft_proposal_id"),
                "created_at": lesson["created_at"],
                "converted_at": lesson.get("converted_at"),
                "deferred_until": lesson.get("deferred_until"),
                "facade_ref": f"/policy/lessons/{lesson['id']}",
                # Cross-domain reference
                "source_incident_ref": f"/incidents/{lesson['source_event_id']}" if lesson.get("source_event_id") else None,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get lesson detail")
        raise HTTPException(status_code=500, detail={"error": "query_failed", "message": str(e)})


# =============================================================================
# V2 Facade: GET /policy/thresholds
# =============================================================================


@router.get(
    "/thresholds",
    response_model=ThresholdsResponse,
    summary="Policy thresholds (V2 Facade)",
    description="""
    Returns enforced limits and thresholds.

    **Cross-Domain Usage:** Activity domain embeds threshold_ref in
    policy_context for runs near limits.

    Reference: PIN-447, CROSS_DOMAIN_POLICY_CONTRACT.md
    """,
    tags=["policy-v2-facade"],
)
async def get_policy_thresholds(
    limit_category: Optional[str] = None,  # BUDGET, RATE, THRESHOLD
    scope: Optional[str] = None,
    status: str = "ACTIVE",
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    ctx: TenantContext = Depends(get_tenant_context),
) -> ThresholdsResponse:
    """V2 Facade: What limits are enforced?"""
    from sqlalchemy import and_, func, select

    from app.models.policy_control_plane import Limit

    try:
        stmt = select(Limit).where(
            and_(
                Limit.tenant_id == ctx.tenant_id,
                Limit.status == status,
            )
        )

        if limit_category:
            stmt = stmt.where(Limit.limit_category == limit_category)
        if scope:
            stmt = stmt.where(Limit.scope == scope)

        # Count
        count_stmt = select(func.count(Limit.id)).where(
            and_(
                Limit.tenant_id == ctx.tenant_id,
                Limit.status == status,
            )
        )
        if limit_category:
            count_stmt = count_stmt.where(Limit.limit_category == limit_category)
        if scope:
            count_stmt = count_stmt.where(Limit.scope == scope)

        count_result = await session.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = stmt.order_by(Limit.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        limits = result.scalars().all()

        items = [
            ThresholdSummary(
                threshold_id=str(lim.id),
                name=lim.name,
                limit_category=lim.limit_category,
                limit_type=lim.limit_type,
                scope=lim.scope,
                enforcement=lim.enforcement,
                max_value=str(lim.max_value),
                status=lim.status,
                facade_ref=f"/policy/thresholds/{lim.id}",
                metadata=_build_policy_metadata_from_limit(lim),
            )
            for lim in limits
        ]

        return ThresholdsResponse(
            items=items,
            total=total,
            has_more=(offset + len(items)) < total,
        )

    except Exception as e:
        logger.exception("Failed to get thresholds")
        raise HTTPException(status_code=500, detail={"error": "query_failed", "message": str(e)})


# =============================================================================
# V2 Facade: GET /policy/thresholds/{threshold_id}
# =============================================================================


@router.get(
    "/thresholds/{threshold_id}",
    summary="Threshold detail (V2 Facade)",
    description="Returns detail of a specific threshold/limit.",
    tags=["policy-v2-facade"],
)
async def get_policy_threshold_detail(
    threshold_id: str,
    session: AsyncSession = Depends(get_async_session),
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    """V2 Facade: Threshold detail for cross-domain navigation."""
    from sqlalchemy import and_, select

    from app.models.policy_control_plane import Limit, LimitIntegrity

    try:
        stmt = (
            select(Limit, LimitIntegrity.integrity_status, LimitIntegrity.integrity_score)
            .outerjoin(LimitIntegrity, LimitIntegrity.limit_id == Limit.id)
            .where(
                and_(
                    Limit.id == threshold_id,
                    Limit.tenant_id == ctx.tenant_id,
                )
            )
        )

        result = await session.execute(stmt)
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail="Threshold not found")

        lim = row[0]

        return wrap_dict(
            {
                "threshold_id": str(lim.id),
                "name": lim.name,
                "description": getattr(lim, "description", None),
                "limit_category": lim.limit_category,
                "limit_type": lim.limit_type,
                "scope": lim.scope,
                "enforcement": lim.enforcement,
                "max_value": str(lim.max_value),
                "window_seconds": lim.window_seconds,
                "reset_period": lim.reset_period,
                "status": lim.status,
                "created_at": lim.created_at.isoformat() if lim.created_at else None,
                "updated_at": lim.updated_at.isoformat() if getattr(lim, "updated_at", None) else None,
                "integrity_status": row[1] if row[1] else "UNKNOWN",
                "integrity_score": str(row[2]) if row[2] else "0",
                "facade_ref": f"/policy/thresholds/{lim.id}",
                # Cross-domain references
                "violations_ref": f"/policy/violations?threshold_id={lim.id}",
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get threshold detail")
        raise HTTPException(status_code=500, detail={"error": "query_failed", "message": str(e)})


# =============================================================================
# V2 Facade: GET /policy/violations
# =============================================================================


@router.get(
    "/violations",
    response_model=ViolationsResponse,
    summary="Policy violations (V2 Facade)",
    description="""
    Returns policy enforcement events (violations).

    **Cross-Domain Usage:** Incidents domain links to violations
    when creating incidents from policy breaches.

    **Invariant:** Violations MUST exist before incidents.

    Reference: PIN-447, CROSS_DOMAIN_POLICY_CONTRACT.md
    """,
    tags=["policy-v2-facade"],
)
async def get_policy_violations_v2(
    violation_type: Optional[str] = None,
    severity_min: Optional[float] = None,
    hours: int = 24,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
    ctx: TenantContext = Depends(get_tenant_context),
) -> ViolationsResponse:
    """V2 Facade: What enforcement occurred?"""
    from app.policy.engine import get_policy_engine

    try:
        engine = get_policy_engine()

        # Convert string violation_type to enum if provided
        from app.policy.models import ViolationType as ViolationTypeEnum

        violation_type_enum = None
        if violation_type:
            type_mapping = {
                "cost": ViolationTypeEnum.RISK_CEILING_BREACH,
                "quota": ViolationTypeEnum.TEMPORAL_LIMIT_EXCEEDED,
                "rate": ViolationTypeEnum.TEMPORAL_LIMIT_EXCEEDED,
                "temporal": ViolationTypeEnum.TEMPORAL_LIMIT_EXCEEDED,
                "safety": ViolationTypeEnum.SAFETY_RULE_TRIGGERED,
                "ethical": ViolationTypeEnum.ETHICAL_VIOLATION,
            }
            violation_type_enum = type_mapping.get(violation_type)

        violations = await engine.get_violations(
            session,
            tenant_id=ctx.tenant_id,
            violation_type=violation_type_enum,
            severity_min=severity_min,
            since=datetime.now(timezone.utc) - timedelta(hours=hours),
            limit=limit + 1,
        )

        has_more = len(violations) > limit
        violations = violations[:limit]

        items = [
            ViolationSummary(
                violation_id=str(v.id),
                policy_id=getattr(v, "policy_id", None),
                policy_name=getattr(v, "policy_name", None),
                violation_type=str(v.violation_type.value) if hasattr(v.violation_type, "value") else str(v.violation_type),
                severity=v.severity,
                source=getattr(v, "source", "runtime"),
                occurred_at=v.detected_at,
                facade_ref=f"/policy/violations/{v.id}",
                run_id=getattr(v, "run_id", None),
                metadata=_build_policy_metadata_from_violation(v),
            )
            for v in violations
        ]

        return ViolationsResponse(
            items=items,
            total=len(items),
            has_more=has_more,
        )

    except Exception as e:
        logger.exception("Failed to get violations")
        raise HTTPException(status_code=500, detail={"error": "query_failed", "message": str(e)})


# =============================================================================
# V2 Facade: GET /policy/violations/{violation_id}
# =============================================================================


@router.get(
    "/violations/{violation_id}",
    summary="Violation detail (V2 Facade)",
    description="Returns detail of a specific violation.",
    tags=["policy-v2-facade"],
)
async def get_policy_violation_detail(
    violation_id: str,
    session: AsyncSession = Depends(get_async_session),
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    """V2 Facade: Violation detail for cross-domain navigation."""
    from app.policy.engine import get_policy_engine

    try:
        engine = get_policy_engine()

        # Get violation by ID
        violations = await engine.get_violations(
            session,
            tenant_id=ctx.tenant_id,
            limit=1000,  # Search all recent
        )

        violation = None
        for v in violations:
            if str(v.id) == violation_id:
                violation = v
                break

        if not violation:
            raise HTTPException(status_code=404, detail="Violation not found")

        return wrap_dict(
            {
                "violation_id": str(violation.id),
                "policy_id": getattr(violation, "policy_id", None),
                "policy_name": getattr(violation, "policy_name", None),
                "violation_type": (
                    str(violation.violation_type.value)
                    if hasattr(violation.violation_type, "value")
                    else str(violation.violation_type)
                ),
                "severity": violation.severity,
                "source": getattr(violation, "source", "runtime"),
                "description": getattr(violation, "description", None),
                "run_id": getattr(violation, "run_id", None),
                "agent_id": violation.agent_id,
                "detected_at": violation.detected_at.isoformat() if violation.detected_at else None,
                "context": getattr(violation, "context", {}),
                "facade_ref": f"/policy/violations/{violation.id}",
                # Cross-domain references
                "run_ref": f"/activity/runs/{violation.run_id}" if getattr(violation, "run_id", None) else None,
                "policy_ref": (
                    f"/policy/active/{violation.policy_id}" if getattr(violation, "policy_id", None) else None
                ),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get violation detail")
        raise HTTPException(status_code=500, detail={"error": "query_failed", "message": str(e)})
