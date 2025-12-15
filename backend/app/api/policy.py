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
"""

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_async import get_async_session

logger = logging.getLogger("nova.api.policy")

router = APIRouter(prefix="/api/v1/policy", tags=["policy"])


# =============================================================================
# Metrics Helper (safe import with fallback)
# =============================================================================

def _record_policy_decision(decision: str, policy_type: str) -> None:
    """Safely record policy decision metric."""
    try:
        from app.workflow.metrics import record_policy_decision
        record_policy_decision(decision, policy_type)
    except Exception as e:
        logger.debug(f"Failed to record policy decision metric: {e}")


def _record_capability_violation(violation_type: str, skill_id: str, tenant_id: Optional[str] = None) -> None:
    """Safely record capability violation metric."""
    try:
        from app.workflow.metrics import record_capability_violation
        record_capability_violation(violation_type, skill_id, tenant_id)
    except Exception as e:
        logger.debug(f"Failed to record capability violation metric: {e}")


def _record_budget_rejection(resource_type: str, skill_id: str) -> None:
    """Safely record budget rejection metric."""
    try:
        from app.workflow.metrics import record_budget_rejection
        record_budget_rejection(resource_type, skill_id)
    except Exception as e:
        logger.debug(f"Failed to record budget rejection metric: {e}")


def _record_approval_request_created(policy_type: str) -> None:
    """Safely record approval request creation metric."""
    try:
        from app.workflow.metrics import record_approval_request_created
        record_approval_request_created(policy_type)
    except Exception as e:
        logger.debug(f"Failed to record approval request metric: {e}")


def _record_approval_action(result: str) -> None:
    """Safely record approval action metric."""
    try:
        from app.workflow.metrics import record_approval_action
        record_approval_action(result)
    except Exception as e:
        logger.debug(f"Failed to record approval action metric: {e}")


def _record_approval_escalation() -> None:
    """Safely record approval escalation metric."""
    try:
        from app.workflow.metrics import record_approval_escalation
        record_approval_escalation()
    except Exception as e:
        logger.debug(f"Failed to record approval escalation metric: {e}")


def _record_webhook_fallback() -> None:
    """Safely record webhook fallback metric."""
    try:
        from app.workflow.metrics import record_webhook_fallback
        record_webhook_fallback()
    except Exception as e:
        logger.debug(f"Failed to record webhook fallback metric: {e}")


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
import os
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
            logger.warning(
                "rate_limit_exceeded",
                extra={"tenant_id": tenant_id, "endpoint": endpoint, "rpm": rpm}
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded: {rpm} requests per minute",
                    "tenant_id": tenant_id,
                    "retry_after_seconds": 60
                }
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
    skill_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get approval level configuration from PolicyApprovalLevel table.
    """
    try:
        from app.db import PolicyApprovalLevel

        stmt = select(PolicyApprovalLevel).where(
            PolicyApprovalLevel.policy_type == policy_type.value
        )

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


async def _simulate_cost(
    skill_id: str,
    tenant_id: str,
    payload: Dict[str, Any]
) -> Optional[int]:
    """Simulate cost for a skill execution."""
    try:
        from app.workflow.cost_sim import CostSimulator
        sim = CostSimulator()
        result = await sim.simulate(skill_id=skill_id, tenant_id=tenant_id, payload=payload)
        return result.estimated_cost_cents
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Cost simulation failed: {e}")

    # Fallback estimate
    return 10


async def _check_policy_violations(
    skill_id: str,
    tenant_id: str,
    agent_id: Optional[str],
    payload: Dict[str, Any],
    simulated_cost: Optional[int]
) -> List[Dict[str, Any]]:
    """Check for policy violations."""
    violations = []

    try:
        from app.workflow.policies import PolicyEnforcer, BudgetExceededError, PolicyViolationError
        from dataclasses import dataclass

        @dataclass
        class MinimalStep:
            id: str = "sandbox_eval"
            estimated_cost_cents: int = 0
            max_cost_cents: Optional[int] = None
            idempotency_key: Optional[str] = "sandbox"
            retry: bool = False
            max_retries: int = 0
            inputs: Dict[str, Any] = None

            def __post_init__(self):
                if self.inputs is None:
                    self.inputs = {}

        @dataclass
        class MinimalContext:
            run_id: str = "sandbox_eval"

        step = MinimalStep(estimated_cost_cents=simulated_cost or 0, inputs=payload)
        ctx = MinimalContext()
        enforcer = PolicyEnforcer()

        try:
            await enforcer.check_can_execute(step, ctx, agent_id=agent_id)
        except BudgetExceededError as e:
            violations.append({
                "type": "BudgetExceededError",
                "message": str(e),
                "policy": "budget",
                "details": {"breach_type": e.breach_type, "limit_cents": e.limit_cents}
            })
            _record_budget_rejection("cost", skill_id)
        except PolicyViolationError as e:
            violations.append({
                "type": "PolicyViolationError",
                "message": str(e),
                "policy": e.policy,
                "details": e.details
            })
            _record_capability_violation(e.policy, skill_id, tenant_id)
        except Exception as e:
            violations.append({
                "type": type(e).__name__,
                "message": str(e),
                "policy": "unknown",
                "details": {}
            })

    except ImportError:
        logger.debug("PolicyEnforcer not available")

    return violations


def _compute_webhook_signature(payload: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature for webhook."""
    import hmac
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


async def _send_webhook(
    url: str,
    payload: Dict[str, Any],
    secret: Optional[str] = None,
    key_version: Optional[str] = None,
    retry_count: int = 0
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


def verify_webhook_signature(
    body: str,
    signature: str,
    key_version: str,
    secrets: Dict[str, str]
) -> bool:
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
    session: AsyncSession = Depends(get_async_session)
) -> PolicyEvalResponse:
    """
    Sandbox evaluation of policy for a skill execution.
    """
    # Rate limiting per tenant
    _check_rate_limit(request.tenant_id, "policy_eval")

    timestamp = datetime.now(timezone.utc).isoformat()
    policy_version = request.policy_version or _get_policy_version()

    # Simulate cost if requested
    simulated_cost = None
    if request.simulate_cost:
        simulated_cost = await _simulate_cost(
            skill_id=request.skill_id,
            tenant_id=request.tenant_id,
            payload=request.payload
        )

    # Check for policy violations
    violations = await _check_policy_violations(
        skill_id=request.skill_id,
        tenant_id=request.tenant_id,
        agent_id=request.agent_id,
        payload=request.payload,
        simulated_cost=simulated_cost
    )

    # Get approval level config
    config = await _get_approval_level_config(
        session=session,
        policy_type=PolicyType.COST,
        tenant_id=request.tenant_id,
        agent_id=request.agent_id,
        skill_id=request.skill_id
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

        overridable = all(
            v.get("type") in ("BudgetExceededError", "PolicyViolationError")
            for v in violations
        )
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
        timestamp=timestamp
    )


@router.post("/requests", response_model=ApprovalRequestResponse)
async def create_approval_request(
    request: ApprovalRequestCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
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
        skill_id=request.skill_id
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
            request.webhook_secret
        )

    return ApprovalRequestResponse(
        request_id=approval.id,
        status=ApprovalStatus.PENDING,
        required_level=config["approval_level"],
        escalate_to=config.get("escalate_to"),
        expires_at=expires_at.isoformat(),
        created_at=approval.created_at.isoformat()
    )


@router.get("/requests/{request_id}", response_model=ApprovalStatusResponse)
async def get_approval_request(
    request_id: str,
    session: AsyncSession = Depends(get_async_session)
) -> ApprovalStatusResponse:
    """Get the current status of an approval request."""
    from app.db import ApprovalRequest as ApprovalRequestModel

    approval = await session.get(ApprovalRequestModel, request_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    # Check if expired
    now = datetime.now(timezone.utc)
    expires_at = approval.expires_at.replace(tzinfo=timezone.utc) if approval.expires_at.tzinfo is None else approval.expires_at

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
        updated_at=data["updated_at"]
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
        from app.auth.rbac import check_approver_permission, RBACError, RBAC_ENABLED

        if not RBAC_ENABLED:
            # RBAC disabled - allow all but log level 5
            if level >= 5:
                logger.warning(
                    "level5_approval_rbac_disabled",
                    extra={
                        "approver_id": approver_id,
                        "level": level,
                        "tenant_id": tenant_id,
                        "warning": "RBAC disabled - owner override allowed without verification"
                    }
                )
            return

        # RBAC enabled - perform full authorization check
        result = check_approver_permission(
            approver_id=approver_id,
            required_level=level,
            tenant_id=tenant_id
        )

        logger.info(
            "rbac_authorization_success",
            extra={
                "approver_id": approver_id,
                "required_level": level,
                "granted_level": result.granted_level,
                "roles": result.roles,
                "tenant_id": tenant_id
            }
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
                "tenant_id": tenant_id
            }
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "authorization_denied",
                "message": e.message,
                "approver_id": approver_id,
                "required_level": e.required_level
            }
        )


@router.post("/requests/{request_id}/approve", response_model=ApprovalStatusResponse)
async def approve_request(
    request_id: str,
    action: ApprovalAction,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
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
    expires_at = approval.expires_at.replace(tzinfo=timezone.utc) if approval.expires_at.tzinfo is None else approval.expires_at

    if now > expires_at:
        approval.status = "expired"
        approval.updated_at = now
        await session.commit()
        raise HTTPException(status_code=400, detail="Approval request has expired")

    # Record the approval
    approval.add_approval(action.approver_id, action.level, "approve", action.notes)

    # Check if fully approved
    if approval.current_level >= approval.required_level:
        approval.transition_status(
            "approved",
            actor=action.approver_id,
            reason=f"Approved at level {action.level}"
        )
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
            None  # Secret not stored in plain text
        )

    return await get_approval_request(request_id, session)


@router.post("/requests/{request_id}/reject", response_model=ApprovalStatusResponse)
async def reject_request(
    request_id: str,
    action: ApprovalAction,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
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
    approval.transition_status(
        "rejected",
        actor=action.approver_id,
        reason=action.notes or "Rejected"
    )
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
            None
        )

    return await get_approval_request(request_id, session)


@router.get("/requests", response_model=List[ApprovalStatusResponse])
async def list_approval_requests(
    status: Optional[ApprovalStatus] = None,
    tenant_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session)
) -> List[ApprovalStatusResponse]:
    """List approval requests with optional filtering."""
    from app.db import ApprovalRequest as ApprovalRequestModel

    stmt = select(ApprovalRequestModel)

    if status:
        stmt = stmt.where(ApprovalRequestModel.status == status.value)
    if tenant_id:
        stmt = stmt.where(ApprovalRequestModel.tenant_id == tenant_id)

    stmt = stmt.order_by(ApprovalRequestModel.created_at.desc())
    stmt = stmt.offset(offset).limit(limit)

    result = await session.execute(stmt)
    results = result.scalars().all()

    responses = []
    now = datetime.now(timezone.utc)

    for approval in results:
        # Check expiration
        expires_at = approval.expires_at.replace(tzinfo=timezone.utc) if approval.expires_at.tzinfo is None else approval.expires_at
        if now > expires_at and approval.status == "pending":
            approval.status = "expired"
            approval.updated_at = now

        data = approval.to_dict()
        responses.append(ApprovalStatusResponse(
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
            updated_at=data["updated_at"]
        ))

    await session.commit()
    return responses


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
    stmt = select(ApprovalRequestModel).where(
        ApprovalRequestModel.status == "pending"
    )

    result = await session.execute(stmt)
    results = result.scalars().all()

    for approval in results:
        created_at = approval.created_at.replace(tzinfo=timezone.utc) if approval.created_at.tzinfo is None else approval.created_at
        timeout = timedelta(seconds=approval.escalation_timeout_seconds)

        if now - created_at > timeout:
            approval.transition_status(
                "escalated",
                actor="escalation_worker",
                reason=f"Timeout after {timeout.total_seconds()}s"
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
                    None
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
