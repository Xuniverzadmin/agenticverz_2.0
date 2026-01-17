# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: api, sdk
#   Execution: sync
# Role: Enforcement policy evaluation for customer LLM integrations
# Callers: SDK (via API), cus_telemetry API
# Allowed Imports: L6 (models, db)
# Forbidden Imports: L1, L2, L3
# Reference: docs/architecture/CUSTOMER_INTEGRATIONS_ARCHITECTURE.md Section 15

"""Customer Enforcement Service

PURPOSE:
    Evaluate enforcement policies for customer LLM calls.
    Returns policy DECISIONS, not actions.

RESPONSIBILITIES:
    - Evaluate integration status (enabled/disabled/error)
    - Check budget limits against current usage
    - Check token limits against current usage
    - Check rate limits (requests per minute)
    - Return structured decision with explainability

DESIGN PRINCIPLES:
    1. NO SIDE EFFECTS: This service only evaluates and returns decisions
    2. SINGLE SOURCE: Limits read only from CusIntegration model
    3. TELEMETRY TRUTH: Usage calculated from cus_llm_usage, not aggregates
    4. EXPLICIT PRECEDENCE: Checks follow locked precedence order (Section 15.1)
    5. DEGRADATION: Missing telemetry → ALLOW with degraded flag

ENFORCEMENT RESULT HIERARCHY:
    HARD_BLOCKED > BLOCKED > THROTTLED > WARNED > ALLOWED
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlmodel import Session, func, select

from app.db import get_engine
from app.models.cus_models import (
    CusHealthState,
    CusIntegration,
    CusIntegrationStatus,
    CusLLMUsage,
)

logger = logging.getLogger(__name__)


class EnforcementResult(str, Enum):
    """Enforcement decision result.

    Ordered from most restrictive to least restrictive.
    """

    HARD_BLOCKED = "hard_blocked"  # System-level denial (disabled, error, invalid creds)
    BLOCKED = "blocked"  # Limit exceeded (budget, tokens)
    THROTTLED = "throttled"  # Rate limit exceeded
    WARNED = "warned"  # Approaching limit (>80%)
    ALLOWED = "allowed"  # Normal execution


@dataclass
class EnforcementReason:
    """Explanation for an enforcement decision."""

    code: str  # Machine-readable code
    message: str  # Human-readable explanation
    limit_type: Optional[str] = None  # budget, tokens, rate, status
    limit_value: Optional[int] = None  # The configured limit
    current_value: Optional[int] = None  # Current usage
    threshold_percent: Optional[float] = None  # Percentage used
    retry_after_seconds: Optional[int] = None  # For rate limits


@dataclass
class EnforcementDecision:
    """Complete enforcement decision with explainability.

    This is the contract between enforcement service and SDK.
    """

    result: EnforcementResult
    integration_id: str
    tenant_id: str
    reasons: List[EnforcementReason] = field(default_factory=list)
    degraded: bool = False  # True if decision made with incomplete data
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "result": self.result.value,
            "integration_id": self.integration_id,
            "tenant_id": self.tenant_id,
            "reasons": [
                {
                    "code": r.code,
                    "message": r.message,
                    "limit_type": r.limit_type,
                    "limit_value": r.limit_value,
                    "current_value": r.current_value,
                    "threshold_percent": r.threshold_percent,
                    "retry_after_seconds": r.retry_after_seconds,
                }
                for r in self.reasons
            ],
            "degraded": self.degraded,
            "evaluated_at": self.evaluated_at.isoformat(),
            "metadata": self.metadata,
        }


class CusEnforcementService:
    """Service for evaluating enforcement policies.

    Phase 5: Authority layer. Returns decisions, not actions.
    """

    # Warning threshold (percentage of limit)
    WARNING_THRESHOLD = 0.80  # 80%

    # Rate limit window
    RATE_LIMIT_WINDOW_SECONDS = 60  # 1 minute

    def __init__(self):
        """Initialize enforcement service."""
        pass

    # =========================================================================
    # MAIN EVALUATION
    # =========================================================================

    async def evaluate(
        self,
        tenant_id: str,
        integration_id: str,
        estimated_cost_cents: int = 0,
        estimated_tokens: int = 0,
    ) -> EnforcementDecision:
        """Evaluate enforcement policy for an LLM call.

        This is the main entry point. Checks follow the locked precedence order
        defined in Section 15.1 of the architecture document.

        Args:
            tenant_id: Tenant ID
            integration_id: Integration ID
            estimated_cost_cents: Estimated cost of the call (for pre-flight checks)
            estimated_tokens: Estimated tokens for the call

        Returns:
            EnforcementDecision with result and reasons
        """
        engine = get_engine()
        reasons: List[EnforcementReason] = []
        degraded = False

        with Session(engine) as session:
            # Fetch integration
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == integration_id,
                    CusIntegration.tenant_id == tenant_id,
                )
            ).first()

            if not integration:
                return EnforcementDecision(
                    result=EnforcementResult.HARD_BLOCKED,
                    integration_id=integration_id,
                    tenant_id=tenant_id,
                    reasons=[
                        EnforcementReason(
                            code="integration_not_found",
                            message="Integration does not exist or does not belong to this tenant",
                            limit_type="status",
                        )
                    ],
                )

            # =========================================================
            # CHECK 1: Integration Disabled?
            # =========================================================
            if integration.status == CusIntegrationStatus.DISABLED:
                return EnforcementDecision(
                    result=EnforcementResult.HARD_BLOCKED,
                    integration_id=integration_id,
                    tenant_id=tenant_id,
                    reasons=[
                        EnforcementReason(
                            code="integration_disabled",
                            message="Integration is disabled. Enable it to make LLM calls.",
                            limit_type="status",
                        )
                    ],
                )

            # =========================================================
            # CHECK 2: Integration in ERROR state?
            # =========================================================
            if integration.status == CusIntegrationStatus.ERROR:
                return EnforcementDecision(
                    result=EnforcementResult.HARD_BLOCKED,
                    integration_id=integration_id,
                    tenant_id=tenant_id,
                    reasons=[
                        EnforcementReason(
                            code="integration_error",
                            message=f"Integration is in error state: {integration.health_message or 'Unknown error'}",
                            limit_type="status",
                        )
                    ],
                )

            # =========================================================
            # CHECK 3: Credentials Invalid? (health check)
            # =========================================================
            if integration.health_state == CusHealthState.FAILING:
                return EnforcementDecision(
                    result=EnforcementResult.HARD_BLOCKED,
                    integration_id=integration_id,
                    tenant_id=tenant_id,
                    reasons=[
                        EnforcementReason(
                            code="credentials_invalid",
                            message=f"Credentials appear invalid: {integration.health_message or 'Health check failed'}",
                            limit_type="status",
                        )
                    ],
                )

            # =========================================================
            # CHECK 4: Budget Exceeded?
            # =========================================================
            if integration.has_budget_limit:
                budget_result = await self._check_budget(
                    session=session,
                    integration=integration,
                    estimated_cost_cents=estimated_cost_cents,
                )
                if budget_result:
                    if budget_result.code == "budget_exceeded":
                        return EnforcementDecision(
                            result=EnforcementResult.BLOCKED,
                            integration_id=integration_id,
                            tenant_id=tenant_id,
                            reasons=[budget_result],
                        )
                    elif budget_result.code == "budget_degraded":
                        degraded = True
                    else:
                        reasons.append(budget_result)

            # =========================================================
            # CHECK 5: Token Limit Exceeded?
            # =========================================================
            if integration.has_token_limit:
                token_result = await self._check_tokens(
                    session=session,
                    integration=integration,
                    estimated_tokens=estimated_tokens,
                )
                if token_result:
                    if token_result.code == "token_limit_exceeded":
                        return EnforcementDecision(
                            result=EnforcementResult.BLOCKED,
                            integration_id=integration_id,
                            tenant_id=tenant_id,
                            reasons=[token_result],
                        )
                    elif token_result.code == "token_degraded":
                        degraded = True
                    else:
                        reasons.append(token_result)

            # =========================================================
            # CHECK 6: Rate Limit Exceeded?
            # =========================================================
            if integration.has_rate_limit:
                rate_result = await self._check_rate(
                    session=session,
                    integration=integration,
                )
                if rate_result:
                    if rate_result.code == "rate_limit_exceeded":
                        return EnforcementDecision(
                            result=EnforcementResult.THROTTLED,
                            integration_id=integration_id,
                            tenant_id=tenant_id,
                            reasons=[rate_result],
                        )
                    elif rate_result.code == "rate_degraded":
                        degraded = True

            # =========================================================
            # CHECKS 7-8: Warning thresholds (already collected in reasons)
            # =========================================================
            if reasons:
                return EnforcementDecision(
                    result=EnforcementResult.WARNED,
                    integration_id=integration_id,
                    tenant_id=tenant_id,
                    reasons=reasons,
                    degraded=degraded,
                )

            # =========================================================
            # CHECK 9: All checks pass
            # =========================================================
            return EnforcementDecision(
                result=EnforcementResult.ALLOWED,
                integration_id=integration_id,
                tenant_id=tenant_id,
                reasons=[
                    EnforcementReason(
                        code="all_checks_passed",
                        message="All enforcement checks passed",
                    )
                ],
                degraded=degraded,
            )

    # =========================================================================
    # INDIVIDUAL CHECKS
    # =========================================================================

    async def _check_budget(
        self,
        session: Session,
        integration: CusIntegration,
        estimated_cost_cents: int,
    ) -> Optional[EnforcementReason]:
        """Check budget limit.

        Args:
            session: Database session
            integration: The integration
            estimated_cost_cents: Estimated cost of upcoming call

        Returns:
            EnforcementReason if limit exceeded/warning, None otherwise
        """
        try:
            # Get current month's usage from cus_llm_usage (NOT aggregates)
            today = date.today()
            period_start = today.replace(day=1)

            result = session.exec(
                select(func.coalesce(func.sum(CusLLMUsage.cost_cents), 0)).where(
                    CusLLMUsage.integration_id == integration.id,
                    CusLLMUsage.tenant_id == integration.tenant_id,
                    func.date(CusLLMUsage.created_at) >= period_start,
                )
            ).first()

            current_cost = int(result) if result else 0
            projected_cost = current_cost + estimated_cost_cents
            limit = integration.budget_limit_cents

            # Check if exceeded
            if projected_cost >= limit:
                return EnforcementReason(
                    code="budget_exceeded",
                    message=f"Monthly budget limit exceeded: {current_cost}¢ used, limit is {limit}¢",
                    limit_type="budget",
                    limit_value=limit,
                    current_value=current_cost,
                    threshold_percent=min(100.0, (current_cost / limit) * 100),
                )

            # Check warning threshold
            threshold = limit * self.WARNING_THRESHOLD
            if current_cost >= threshold:
                return EnforcementReason(
                    code="budget_warning",
                    message=f"Approaching budget limit: {current_cost}¢ of {limit}¢ ({(current_cost/limit)*100:.1f}%)",
                    limit_type="budget",
                    limit_value=limit,
                    current_value=current_cost,
                    threshold_percent=(current_cost / limit) * 100,
                )

            return None

        except Exception as e:
            logger.warning(f"Budget check failed, allowing with degraded flag: {e}")
            return EnforcementReason(
                code="budget_degraded",
                message="Budget check unavailable - allowing with degraded status",
                limit_type="budget",
            )

    async def _check_tokens(
        self,
        session: Session,
        integration: CusIntegration,
        estimated_tokens: int,
    ) -> Optional[EnforcementReason]:
        """Check token limit.

        Args:
            session: Database session
            integration: The integration
            estimated_tokens: Estimated tokens for upcoming call

        Returns:
            EnforcementReason if limit exceeded/warning, None otherwise
        """
        try:
            # Get current month's token usage from cus_llm_usage
            today = date.today()
            period_start = today.replace(day=1)

            result = session.exec(
                select(
                    func.coalesce(
                        func.sum(CusLLMUsage.tokens_in + CusLLMUsage.tokens_out), 0
                    )
                ).where(
                    CusLLMUsage.integration_id == integration.id,
                    CusLLMUsage.tenant_id == integration.tenant_id,
                    func.date(CusLLMUsage.created_at) >= period_start,
                )
            ).first()

            current_tokens = int(result) if result else 0
            projected_tokens = current_tokens + estimated_tokens
            limit = integration.token_limit_month

            # Check if exceeded
            if projected_tokens >= limit:
                return EnforcementReason(
                    code="token_limit_exceeded",
                    message=f"Monthly token limit exceeded: {current_tokens:,} tokens used, limit is {limit:,}",
                    limit_type="tokens",
                    limit_value=limit,
                    current_value=current_tokens,
                    threshold_percent=min(100.0, (current_tokens / limit) * 100),
                )

            # Check warning threshold
            threshold = limit * self.WARNING_THRESHOLD
            if current_tokens >= threshold:
                return EnforcementReason(
                    code="token_warning",
                    message=f"Approaching token limit: {current_tokens:,} of {limit:,} ({(current_tokens/limit)*100:.1f}%)",
                    limit_type="tokens",
                    limit_value=limit,
                    current_value=current_tokens,
                    threshold_percent=(current_tokens / limit) * 100,
                )

            return None

        except Exception as e:
            logger.warning(f"Token check failed, allowing with degraded flag: {e}")
            return EnforcementReason(
                code="token_degraded",
                message="Token check unavailable - allowing with degraded status",
                limit_type="tokens",
            )

    async def _check_rate(
        self,
        session: Session,
        integration: CusIntegration,
    ) -> Optional[EnforcementReason]:
        """Check rate limit (requests per minute).

        Args:
            session: Database session
            integration: The integration

        Returns:
            EnforcementReason if rate limit exceeded, None otherwise
        """
        try:
            # Count requests in the last minute from cus_llm_usage
            window_start = datetime.now(timezone.utc) - timedelta(
                seconds=self.RATE_LIMIT_WINDOW_SECONDS
            )

            result = session.exec(
                select(func.count()).where(
                    CusLLMUsage.integration_id == integration.id,
                    CusLLMUsage.created_at >= window_start,
                )
            ).first()

            current_rpm = int(result) if result else 0
            limit = integration.rate_limit_rpm

            # Check if exceeded
            if current_rpm >= limit:
                # Calculate retry-after (seconds until oldest request expires)
                retry_after = self.RATE_LIMIT_WINDOW_SECONDS

                return EnforcementReason(
                    code="rate_limit_exceeded",
                    message=f"Rate limit exceeded: {current_rpm} requests in last minute, limit is {limit} RPM",
                    limit_type="rate",
                    limit_value=limit,
                    current_value=current_rpm,
                    threshold_percent=min(100.0, (current_rpm / limit) * 100),
                    retry_after_seconds=retry_after,
                )

            return None

        except Exception as e:
            logger.warning(f"Rate check failed, allowing with degraded flag: {e}")
            return EnforcementReason(
                code="rate_degraded",
                message="Rate check unavailable - allowing with degraded status",
                limit_type="rate",
            )

    # =========================================================================
    # BATCH EVALUATION
    # =========================================================================

    async def evaluate_batch(
        self,
        tenant_id: str,
        requests: List[Dict[str, Any]],
    ) -> List[EnforcementDecision]:
        """Evaluate multiple requests (for batch pre-flight checks).

        Args:
            tenant_id: Tenant ID
            requests: List of {integration_id, estimated_cost_cents, estimated_tokens}

        Returns:
            List of EnforcementDecisions (same order as requests)
        """
        results = []
        for req in requests:
            decision = await self.evaluate(
                tenant_id=tenant_id,
                integration_id=req["integration_id"],
                estimated_cost_cents=req.get("estimated_cost_cents", 0),
                estimated_tokens=req.get("estimated_tokens", 0),
            )
            results.append(decision)
        return results

    # =========================================================================
    # STATUS QUERIES
    # =========================================================================

    async def get_enforcement_status(
        self,
        tenant_id: str,
        integration_id: str,
    ) -> Dict[str, Any]:
        """Get current enforcement status without making a decision.

        Useful for SDK to display current limits and usage.

        Args:
            tenant_id: Tenant ID
            integration_id: Integration ID

        Returns:
            Status dict with limits and current usage
        """
        engine = get_engine()

        with Session(engine) as session:
            integration = session.exec(
                select(CusIntegration).where(
                    CusIntegration.id == integration_id,
                    CusIntegration.tenant_id == tenant_id,
                )
            ).first()

            if not integration:
                return {"error": "integration_not_found"}

            # Get current period usage
            today = date.today()
            period_start = today.replace(day=1)

            # Budget usage
            budget_result = session.exec(
                select(func.coalesce(func.sum(CusLLMUsage.cost_cents), 0)).where(
                    CusLLMUsage.integration_id == integration.id,
                    CusLLMUsage.tenant_id == integration.tenant_id,
                    func.date(CusLLMUsage.created_at) >= period_start,
                )
            ).first()
            budget_used = int(budget_result) if budget_result else 0

            # Token usage
            token_result = session.exec(
                select(
                    func.coalesce(
                        func.sum(CusLLMUsage.tokens_in + CusLLMUsage.tokens_out), 0
                    )
                ).where(
                    CusLLMUsage.integration_id == integration.id,
                    CusLLMUsage.tenant_id == integration.tenant_id,
                    func.date(CusLLMUsage.created_at) >= period_start,
                )
            ).first()
            tokens_used = int(token_result) if token_result else 0

            # Rate (last minute)
            window_start = datetime.now(timezone.utc) - timedelta(
                seconds=self.RATE_LIMIT_WINDOW_SECONDS
            )
            rate_result = session.exec(
                select(func.count()).where(
                    CusLLMUsage.integration_id == integration.id,
                    CusLLMUsage.created_at >= window_start,
                )
            ).first()
            current_rpm = int(rate_result) if rate_result else 0

            return {
                "integration_id": integration_id,
                "integration_status": integration.status.value,
                "health_state": integration.health_state.value,
                "budget": {
                    "limit_cents": integration.budget_limit_cents,
                    "used_cents": budget_used,
                    "remaining_cents": max(
                        0, integration.budget_limit_cents - budget_used
                    ),
                    "percent_used": (
                        (budget_used / integration.budget_limit_cents * 100)
                        if integration.budget_limit_cents > 0
                        else 0
                    ),
                    "has_limit": integration.has_budget_limit,
                },
                "tokens": {
                    "limit": integration.token_limit_month,
                    "used": tokens_used,
                    "remaining": max(0, integration.token_limit_month - tokens_used),
                    "percent_used": (
                        (tokens_used / integration.token_limit_month * 100)
                        if integration.token_limit_month > 0
                        else 0
                    ),
                    "has_limit": integration.has_token_limit,
                },
                "rate": {
                    "limit_rpm": integration.rate_limit_rpm,
                    "current_rpm": current_rpm,
                    "percent_used": (
                        (current_rpm / integration.rate_limit_rpm * 100)
                        if integration.rate_limit_rpm > 0
                        else 0
                    ),
                    "has_limit": integration.has_rate_limit,
                },
                "period_start": period_start.isoformat(),
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
            }
