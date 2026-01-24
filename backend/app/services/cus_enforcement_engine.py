# Layer: L4 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api, sdk
#   Execution: sync
# Role: Enforcement policy evaluation for customer LLM integrations
# Callers: SDK (via API), cus_telemetry API
# Allowed Imports: L6 drivers (via injection)
# Forbidden Imports: sqlalchemy, sqlmodel, app.models
# Reference: PIN-468, DRIVER_ENGINE_CONTRACT.md

"""Customer Enforcement Engine

L4 engine for enforcement policy decisions.

Decides: Integration status, budget limits, token limits, rate limits
Delegates: All data access to CusEnforcementDriver

ENFORCEMENT RESULT HIERARCHY:
    HARD_BLOCKED > BLOCKED > THROTTLED > WARNED > ALLOWED
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.services.cus_enforcement_driver import (
    CusEnforcementDriver,
    IntegrationRow,
    get_cus_enforcement_driver,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class EnforcementResult(str, Enum):
    """Enforcement decision result.

    Ordered from most restrictive to least restrictive.
    """

    HARD_BLOCKED = "hard_blocked"  # System-level denial
    BLOCKED = "blocked"  # Limit exceeded
    THROTTLED = "throttled"  # Rate limit exceeded
    WARNED = "warned"  # Approaching limit
    ALLOWED = "allowed"  # Normal execution


@dataclass
class EnforcementReason:
    """Explanation for an enforcement decision."""

    code: str
    message: str
    limit_type: Optional[str] = None
    limit_value: Optional[int] = None
    current_value: Optional[int] = None
    threshold_percent: Optional[float] = None
    retry_after_seconds: Optional[int] = None


@dataclass
class EnforcementDecision:
    """Complete enforcement decision with explainability."""

    result: EnforcementResult
    integration_id: str
    tenant_id: str
    reasons: List[EnforcementReason] = field(default_factory=list)
    degraded: bool = False
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


class CusEnforcementEngine:
    """L4 engine for enforcement policy decisions.

    Decides: Status checks, budget limits, token limits, rate limits
    Delegates: All data access to CusEnforcementDriver
    """

    # Status values (avoid importing enums at runtime)
    STATUS_DISABLED = "disabled"
    STATUS_ERROR = "error"
    HEALTH_FAILING = "failing"

    # Warning threshold (percentage of limit)
    WARNING_THRESHOLD = 0.80  # 80%

    # Rate limit window
    RATE_LIMIT_WINDOW_SECONDS = 60  # 1 minute

    def __init__(self, driver: CusEnforcementDriver):
        """Initialize engine with driver.

        Args:
            driver: CusEnforcementDriver instance for data access
        """
        self._driver = driver

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

        Business logic:
        - Check integration status (disabled, error)
        - Check credentials health (failing)
        - Check budget limits
        - Check token limits
        - Check rate limits

        Args:
            tenant_id: Tenant ID
            integration_id: Integration ID
            estimated_cost_cents: Estimated cost (pre-flight)
            estimated_tokens: Estimated tokens

        Returns:
            EnforcementDecision with result and reasons
        """
        reasons: List[EnforcementReason] = []
        degraded = False

        # Fetch integration data
        integration = self._driver.fetch_integration(tenant_id, integration_id)

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

        # DECISION 1: Integration Disabled?
        if integration.status == self.STATUS_DISABLED:
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

        # DECISION 2: Integration in ERROR state?
        if integration.status == self.STATUS_ERROR:
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

        # DECISION 3: Credentials Invalid?
        if integration.health_state == self.HEALTH_FAILING:
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

        # DECISION 4: Budget Exceeded?
        if integration.has_budget_limit:
            budget_result = self._check_budget(
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

        # DECISION 5: Token Limit Exceeded?
        if integration.has_token_limit:
            token_result = self._check_tokens(
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

        # DECISION 6: Rate Limit Exceeded?
        if integration.has_rate_limit:
            rate_result = self._check_rate(integration=integration)
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

        # DECISION 7-8: Warning thresholds
        if reasons:
            return EnforcementDecision(
                result=EnforcementResult.WARNED,
                integration_id=integration_id,
                tenant_id=tenant_id,
                reasons=reasons,
                degraded=degraded,
            )

        # DECISION 9: All checks pass
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
    # INDIVIDUAL CHECKS (Business Logic)
    # =========================================================================

    def _check_budget(
        self,
        integration: IntegrationRow,
        estimated_cost_cents: int,
    ) -> Optional[EnforcementReason]:
        """Check budget limit.

        Business logic:
        - Fetch current usage from driver
        - Calculate projected cost
        - Compare against limit
        - Check warning threshold
        """
        try:
            today = date.today()
            period_start = today.replace(day=1)

            current_cost = self._driver.fetch_budget_usage(
                integration.id, integration.tenant_id, period_start
            )
            projected_cost = current_cost + estimated_cost_cents
            limit = integration.budget_limit_cents

            # DECISION: Exceeded?
            if projected_cost >= limit:
                return EnforcementReason(
                    code="budget_exceeded",
                    message=f"Monthly budget limit exceeded: {current_cost}¢ used, limit is {limit}¢",
                    limit_type="budget",
                    limit_value=limit,
                    current_value=current_cost,
                    threshold_percent=min(100.0, (current_cost / limit) * 100),
                )

            # DECISION: Warning threshold?
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

    def _check_tokens(
        self,
        integration: IntegrationRow,
        estimated_tokens: int,
    ) -> Optional[EnforcementReason]:
        """Check token limit.

        Business logic:
        - Fetch current usage from driver
        - Calculate projected tokens
        - Compare against limit
        - Check warning threshold
        """
        try:
            today = date.today()
            period_start = today.replace(day=1)

            current_tokens = self._driver.fetch_token_usage(
                integration.id, integration.tenant_id, period_start
            )
            projected_tokens = current_tokens + estimated_tokens
            limit = integration.token_limit_month

            # DECISION: Exceeded?
            if projected_tokens >= limit:
                return EnforcementReason(
                    code="token_limit_exceeded",
                    message=f"Monthly token limit exceeded: {current_tokens:,} tokens used, limit is {limit:,}",
                    limit_type="tokens",
                    limit_value=limit,
                    current_value=current_tokens,
                    threshold_percent=min(100.0, (current_tokens / limit) * 100),
                )

            # DECISION: Warning threshold?
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

    def _check_rate(
        self,
        integration: IntegrationRow,
    ) -> Optional[EnforcementReason]:
        """Check rate limit.

        Business logic:
        - Fetch current RPM from driver
        - Compare against limit
        """
        try:
            window_start = datetime.now(timezone.utc) - timedelta(
                seconds=self.RATE_LIMIT_WINDOW_SECONDS
            )

            current_rpm = self._driver.fetch_rate_count(integration.id, window_start)
            limit = integration.rate_limit_rpm

            # DECISION: Exceeded?
            if current_rpm >= limit:
                return EnforcementReason(
                    code="rate_limit_exceeded",
                    message=f"Rate limit exceeded: {current_rpm} requests in last minute, limit is {limit} RPM",
                    limit_type="rate",
                    limit_value=limit,
                    current_value=current_rpm,
                    threshold_percent=min(100.0, (current_rpm / limit) * 100),
                    retry_after_seconds=self.RATE_LIMIT_WINDOW_SECONDS,
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
        """Evaluate multiple requests (batch pre-flight).

        Args:
            tenant_id: Tenant ID
            requests: List of {integration_id, estimated_cost_cents, estimated_tokens}

        Returns:
            List of EnforcementDecisions (same order)
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

        Args:
            tenant_id: Tenant ID
            integration_id: Integration ID

        Returns:
            Status dict with limits and current usage
        """
        integration = self._driver.fetch_integration(tenant_id, integration_id)

        if not integration:
            return {"error": "integration_not_found"}

        today = date.today()
        period_start = today.replace(day=1)
        rate_window_start = datetime.now(timezone.utc) - timedelta(
            seconds=self.RATE_LIMIT_WINDOW_SECONDS
        )

        snapshot = self._driver.fetch_usage_snapshot(
            integration_id, tenant_id, period_start, rate_window_start
        )

        return {
            "integration_id": integration_id,
            "integration_status": integration.status,
            "health_state": integration.health_state,
            "budget": {
                "limit_cents": integration.budget_limit_cents,
                "used_cents": snapshot.budget_used_cents,
                "remaining_cents": max(0, integration.budget_limit_cents - snapshot.budget_used_cents),
                "percent_used": (
                    (snapshot.budget_used_cents / integration.budget_limit_cents * 100)
                    if integration.budget_limit_cents > 0
                    else 0
                ),
                "has_limit": integration.has_budget_limit,
            },
            "tokens": {
                "limit": integration.token_limit_month,
                "used": snapshot.tokens_used,
                "remaining": max(0, integration.token_limit_month - snapshot.tokens_used),
                "percent_used": (
                    (snapshot.tokens_used / integration.token_limit_month * 100)
                    if integration.token_limit_month > 0
                    else 0
                ),
                "has_limit": integration.has_token_limit,
            },
            "rate": {
                "limit_rpm": integration.rate_limit_rpm,
                "current_rpm": snapshot.current_rpm,
                "percent_used": (
                    (snapshot.current_rpm / integration.rate_limit_rpm * 100)
                    if integration.rate_limit_rpm > 0
                    else 0
                ),
                "has_limit": integration.has_rate_limit,
            },
            "period_start": period_start.isoformat(),
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }


# Factory function
def get_cus_enforcement_engine() -> CusEnforcementEngine:
    """Get engine instance with default driver.

    Returns:
        CusEnforcementEngine instance
    """
    driver = get_cus_enforcement_driver()
    return CusEnforcementEngine(driver=driver)


# Backward compatibility alias
CusEnforcementService = CusEnforcementEngine
get_cus_enforcement_service = get_cus_enforcement_engine
