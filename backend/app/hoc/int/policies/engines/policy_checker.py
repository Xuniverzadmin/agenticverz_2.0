# Layer: L5 — Execution & Workers
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: sync
# Role: Mid-execution policy checking for reactive enforcement
# Callers: RunRunner (L5)
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L3
# Reference: PIN-454, FIX-005 (Phase 5)

"""
Mid-Execution Policy Checker

Checks policy constraints during execution, not just at submission.
Enables reactive policy enforcement for long-running runs.

DESIGN CONSTRAINTS:
1. Layer L5 — Execution & Workers
2. Interval-based checking (not every step)
3. Three decisions: CONTINUE, PAUSE, TERMINATE
4. Non-blocking design (async-ready)
5. Feature flag controlled

Key Features:
- Detects policy changes since submission
- Checks budget consumption against new limits
- Detects runtime policy violations
- Supports pause-for-approval workflow

Usage:
    checker = MidExecutionPolicyChecker()

    # Before each step
    decision = checker.check_before_step(
        run_id="...",
        tenant_id="...",
        step_index=5,
        cost_so_far=1.50,
    )

    if decision == PolicyDecision.TERMINATE:
        raise PolicyTermination("Run terminated by policy change")
    elif decision == PolicyDecision.PAUSE:
        await pause_for_approval()
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, FrozenSet, List, Optional
from uuid import UUID

from sqlmodel import Session, select

logger = logging.getLogger("nova.worker.policy_checker")

# Configuration
MID_EXECUTION_POLICY_CHECK_ENABLED = (
    os.getenv("MID_EXECUTION_POLICY_CHECK_ENABLED", "false").lower() == "true"
)
POLICY_CHECK_INTERVAL_SECONDS = int(os.getenv("POLICY_CHECK_INTERVAL_SECONDS", "30"))
POLICY_CHECK_MIN_STEPS = int(os.getenv("POLICY_CHECK_MIN_STEPS", "3"))

# =============================================================================
# PAUSE Semantics Configuration (PIN-454 Section 3.2)
# =============================================================================
#
# These settings define the behavior of paused runs:
# - Who can resume a paused run
# - Maximum time a run can stay paused (SLA)
# - What happens when pause times out

PAUSE_SLA_SECONDS = int(os.getenv("PAUSE_SLA_SECONDS", "3600"))  # 1 hour default
PAUSE_TIMEOUT_BEHAVIOR = os.getenv("PAUSE_TIMEOUT_BEHAVIOR", "TERMINATE")  # TERMINATE or CONTINUE
PAUSE_NOTIFY_BEFORE_TIMEOUT_SECONDS = int(os.getenv("PAUSE_NOTIFY_BEFORE_TIMEOUT_SECONDS", "300"))  # 5 min warning

# Prometheus metrics (optional)
try:
    from prometheus_client import Counter, Histogram

    POLICY_CHECKS = Counter(
        "aos_policy_checks_total",
        "Total mid-execution policy checks",
        ["decision"],
    )
    POLICY_CHECK_DURATION = Histogram(
        "aos_policy_check_duration_seconds",
        "Duration of policy check execution",
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False


class PolicyDecision(str, Enum):
    """Decision from mid-execution policy check."""

    CONTINUE = "CONTINUE"  # Proceed with next step
    PAUSE = "PAUSE"  # Hold for approval
    TERMINATE = "TERMINATE"  # Stop run immediately
    SKIP = "SKIP"  # Check skipped (too soon)


class PolicyViolationType(str, Enum):
    """Types of policy violations detected during execution."""

    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    LIMIT_CHANGED = "LIMIT_CHANGED"
    POLICY_DISABLED = "POLICY_DISABLED"
    TENANT_SUSPENDED = "TENANT_SUSPENDED"
    RATE_LIMIT_HIT = "RATE_LIMIT_HIT"
    MANUAL_STOP = "MANUAL_STOP"


@dataclass
class PolicyViolation:
    """Details of a detected policy violation."""

    violation_type: PolicyViolationType
    message: str
    current_value: Optional[float] = None
    limit_value: Optional[float] = None
    policy_id: Optional[str] = None
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# PAUSE Semantics (PIN-454 Section 3.2)
# =============================================================================


class PauseReason(str, Enum):
    """Why a run was paused."""

    POLICY_CHANGE = "POLICY_CHANGE"  # Policy changed during execution
    BUDGET_WARNING = "BUDGET_WARNING"  # Near budget limit (not exceeded yet)
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"  # Manual approval needed
    RATE_LIMIT_SOFT = "RATE_LIMIT_SOFT"  # Soft rate limit hit
    MANUAL_PAUSE = "MANUAL_PAUSE"  # User requested pause


class PauseResumeAuthority(str, Enum):
    """
    Who can resume a paused run.

    Per PIN-454 Section 3.2: "Who can resume?"
    Different pause reasons may require different authorities to resume.
    """

    TENANT_ADMIN = "TENANT_ADMIN"  # Tenant admin only
    TENANT_USER = "TENANT_USER"  # Any tenant user
    SYSTEM_AUTO = "SYSTEM_AUTO"  # System can auto-resume
    API_KEY_OWNER = "API_KEY_OWNER"  # Owner of the API key used
    FOUNDER_ONLY = "FOUNDER_ONLY"  # Founder/ops approval required


class PauseTimeoutBehavior(str, Enum):
    """What happens when pause SLA expires."""

    TERMINATE = "TERMINATE"  # Run is terminated
    CONTINUE = "CONTINUE"  # Run continues automatically
    ESCALATE = "ESCALATE"  # Escalate to higher authority


# Default resume authority for each pause reason
PAUSE_RESUME_AUTHORITY: Dict[PauseReason, FrozenSet[PauseResumeAuthority]] = {
    PauseReason.POLICY_CHANGE: frozenset({
        PauseResumeAuthority.TENANT_ADMIN,
        PauseResumeAuthority.FOUNDER_ONLY,
    }),
    PauseReason.BUDGET_WARNING: frozenset({
        PauseResumeAuthority.TENANT_ADMIN,
        PauseResumeAuthority.API_KEY_OWNER,
    }),
    PauseReason.APPROVAL_REQUIRED: frozenset({
        PauseResumeAuthority.TENANT_ADMIN,
    }),
    PauseReason.RATE_LIMIT_SOFT: frozenset({
        PauseResumeAuthority.SYSTEM_AUTO,  # Auto-resume after cooldown
        PauseResumeAuthority.TENANT_ADMIN,
    }),
    PauseReason.MANUAL_PAUSE: frozenset({
        PauseResumeAuthority.TENANT_ADMIN,
        PauseResumeAuthority.TENANT_USER,
        PauseResumeAuthority.API_KEY_OWNER,
    }),
}


@dataclass
class PausedRunState:
    """
    State of a paused run.

    Per PIN-454 Section 3.2, this captures:
    - Why the run was paused
    - When it was paused
    - Who can resume it
    - When the pause will timeout
    - Callback for timeout events
    """

    run_id: str
    tenant_id: str
    pause_reason: PauseReason
    paused_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    violations: List[PolicyViolation] = field(default_factory=list)
    pause_message: str = ""

    # Resume authorization
    resume_authorities: FrozenSet[PauseResumeAuthority] = field(default_factory=frozenset)

    # SLA/Timeout
    sla_expires_at: Optional[datetime] = None
    timeout_behavior: PauseTimeoutBehavior = PauseTimeoutBehavior.TERMINATE

    # Tracking
    resume_attempts: int = 0
    last_resume_attempt_at: Optional[datetime] = None
    last_resume_attempt_by: Optional[str] = None

    def __post_init__(self):
        """Set default values after initialization."""
        # Set resume authorities from pause reason if not provided
        if not self.resume_authorities:
            self.resume_authorities = PAUSE_RESUME_AUTHORITY.get(
                self.pause_reason,
                frozenset({PauseResumeAuthority.TENANT_ADMIN}),
            )

        # Set SLA expiry if not provided
        if self.sla_expires_at is None:
            self.sla_expires_at = self.paused_at + timedelta(seconds=PAUSE_SLA_SECONDS)

        # Set timeout behavior from config if default
        if self.timeout_behavior == PauseTimeoutBehavior.TERMINATE:
            behavior_str = PAUSE_TIMEOUT_BEHAVIOR.upper()
            if hasattr(PauseTimeoutBehavior, behavior_str):
                self.timeout_behavior = PauseTimeoutBehavior(behavior_str)

    @property
    def is_expired(self) -> bool:
        """Check if pause has exceeded SLA."""
        if self.sla_expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.sla_expires_at

    @property
    def time_until_expiry(self) -> timedelta:
        """Time remaining until SLA expires."""
        if self.sla_expires_at is None:
            return timedelta.max
        remaining = self.sla_expires_at - datetime.now(timezone.utc)
        return max(remaining, timedelta(0))

    @property
    def should_notify_expiry_warning(self) -> bool:
        """Check if we should send an expiry warning notification."""
        if self.sla_expires_at is None:
            return False
        warning_threshold = timedelta(seconds=PAUSE_NOTIFY_BEFORE_TIMEOUT_SECONDS)
        return self.time_until_expiry <= warning_threshold

    def can_resume(self, authority: PauseResumeAuthority) -> bool:
        """Check if the given authority can resume this run."""
        return authority in self.resume_authorities

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage/logging."""
        return {
            "run_id": self.run_id,
            "tenant_id": self.tenant_id,
            "pause_reason": self.pause_reason.value,
            "paused_at": self.paused_at.isoformat(),
            "pause_message": self.pause_message,
            "resume_authorities": [a.value for a in self.resume_authorities],
            "sla_expires_at": self.sla_expires_at.isoformat() if self.sla_expires_at else None,
            "timeout_behavior": self.timeout_behavior.value,
            "is_expired": self.is_expired,
            "time_until_expiry_seconds": self.time_until_expiry.total_seconds(),
            "violations": [
                {
                    "type": v.violation_type.value,
                    "message": v.message,
                }
                for v in self.violations
            ],
        }


class PauseManager:
    """
    Manages paused runs with SLA enforcement.

    Per PIN-454 Section 3.2, this provides:
    - Pause state tracking
    - Resume authorization checking
    - SLA timeout monitoring
    - Notification callbacks

    Layer: L5 (Execution & Workers)
    """

    def __init__(self):
        """Initialize pause manager."""
        self._paused_runs: Dict[str, PausedRunState] = {}
        self._on_timeout_callback: Optional[Callable[[PausedRunState], None]] = None
        self._on_expiry_warning_callback: Optional[Callable[[PausedRunState], None]] = None

    def pause_run(
        self,
        run_id: str,
        tenant_id: str,
        reason: PauseReason,
        message: str,
        violations: Optional[List[PolicyViolation]] = None,
        custom_sla_seconds: Optional[int] = None,
        custom_resume_authorities: Optional[FrozenSet[PauseResumeAuthority]] = None,
    ) -> PausedRunState:
        """
        Pause a run.

        Args:
            run_id: Run to pause
            tenant_id: Tenant owning the run
            reason: Why the run is being paused
            message: Human-readable pause message
            violations: Optional list of policy violations
            custom_sla_seconds: Override default SLA
            custom_resume_authorities: Override default resume authorities

        Returns:
            PausedRunState for the paused run
        """
        sla_expires_at = None
        if custom_sla_seconds is not None:
            sla_expires_at = datetime.now(timezone.utc) + timedelta(seconds=custom_sla_seconds)

        state = PausedRunState(
            run_id=run_id,
            tenant_id=tenant_id,
            pause_reason=reason,
            pause_message=message,
            violations=violations or [],
            sla_expires_at=sla_expires_at,
            resume_authorities=custom_resume_authorities or frozenset(),
        )

        self._paused_runs[run_id] = state

        logger.info(
            "policy_checker.run_paused",
            extra={
                "run_id": run_id,
                "tenant_id": tenant_id,
                "reason": reason.value,
                "sla_expires_at": state.sla_expires_at.isoformat() if state.sla_expires_at else None,
                "resume_authorities": [a.value for a in state.resume_authorities],
            },
        )

        return state

    def get_paused_state(self, run_id: str) -> Optional[PausedRunState]:
        """Get pause state for a run."""
        return self._paused_runs.get(run_id)

    def is_paused(self, run_id: str) -> bool:
        """Check if run is paused."""
        return run_id in self._paused_runs

    def try_resume(
        self,
        run_id: str,
        authority: PauseResumeAuthority,
        actor_id: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Attempt to resume a paused run.

        Args:
            run_id: Run to resume
            authority: Authority level of the actor
            actor_id: Optional ID of the actor attempting resume

        Returns:
            Tuple of (success, message)
        """
        state = self._paused_runs.get(run_id)
        if state is None:
            return False, "Run is not paused"

        # Check authorization
        if not state.can_resume(authority):
            state.resume_attempts += 1
            state.last_resume_attempt_at = datetime.now(timezone.utc)
            state.last_resume_attempt_by = actor_id

            logger.warning(
                "policy_checker.unauthorized_resume_attempt",
                extra={
                    "run_id": run_id,
                    "authority": authority.value,
                    "actor_id": actor_id,
                    "allowed_authorities": [a.value for a in state.resume_authorities],
                },
            )
            return False, f"Authority {authority.value} cannot resume this run"

        # Check if expired
        if state.is_expired:
            return False, "Pause SLA has expired, run must be handled according to timeout behavior"

        # Remove from paused runs
        del self._paused_runs[run_id]

        logger.info(
            "policy_checker.run_resumed",
            extra={
                "run_id": run_id,
                "authority": authority.value,
                "actor_id": actor_id,
                "pause_duration_seconds": (datetime.now(timezone.utc) - state.paused_at).total_seconds(),
            },
        )

        return True, "Run resumed successfully"

    def check_timeouts(self) -> List[PausedRunState]:
        """
        Check for expired pauses and handle them.

        Should be called periodically by a scheduler.

        Returns:
            List of expired PausedRunState objects that were handled
        """
        expired: List[PausedRunState] = []
        to_remove: List[str] = []

        for run_id, state in self._paused_runs.items():
            # Check for expiry warning
            if state.should_notify_expiry_warning and self._on_expiry_warning_callback:
                self._on_expiry_warning_callback(state)

            # Check for full expiry
            if state.is_expired:
                expired.append(state)
                to_remove.append(run_id)

                logger.warning(
                    "policy_checker.pause_expired",
                    extra={
                        "run_id": run_id,
                        "pause_reason": state.pause_reason.value,
                        "timeout_behavior": state.timeout_behavior.value,
                        "pause_duration_seconds": (datetime.now(timezone.utc) - state.paused_at).total_seconds(),
                    },
                )

                # Execute timeout callback
                if self._on_timeout_callback:
                    self._on_timeout_callback(state)

        # Remove expired runs from tracking
        for run_id in to_remove:
            del self._paused_runs[run_id]

        return expired

    def set_timeout_callback(self, callback: Callable[[PausedRunState], None]) -> None:
        """Set callback for when a pause times out."""
        self._on_timeout_callback = callback

    def set_expiry_warning_callback(self, callback: Callable[[PausedRunState], None]) -> None:
        """Set callback for when a pause is about to expire."""
        self._on_expiry_warning_callback = callback

    def get_all_paused(self) -> List[PausedRunState]:
        """Get all paused runs."""
        return list(self._paused_runs.values())

    def clear_run(self, run_id: str) -> None:
        """Clear pause state for a run (e.g., on run completion)."""
        self._paused_runs.pop(run_id, None)

    @property
    def paused_count(self) -> int:
        """Number of currently paused runs."""
        return len(self._paused_runs)


# Singleton instance
_pause_manager_instance: Optional[PauseManager] = None


def get_pause_manager() -> PauseManager:
    """Get or create PauseManager singleton."""
    global _pause_manager_instance
    if _pause_manager_instance is None:
        _pause_manager_instance = PauseManager()
    return _pause_manager_instance


@dataclass
class PolicyCheckResult:
    """Result of a mid-execution policy check."""

    decision: PolicyDecision
    reason: str
    violations: List[PolicyViolation] = field(default_factory=list)
    check_duration_ms: float = 0.0
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def should_continue(self) -> bool:
        """Whether the run should continue."""
        return self.decision in (PolicyDecision.CONTINUE, PolicyDecision.SKIP)


class PolicyTermination(Exception):
    """Exception raised when policy terminates a run."""

    def __init__(self, message: str, violations: Optional[List[PolicyViolation]] = None):
        super().__init__(message)
        self.message = message
        self.violations = violations or []


class PolicyPause(Exception):
    """Exception raised when policy pauses a run for approval."""

    def __init__(self, message: str, violations: Optional[List[PolicyViolation]] = None):
        super().__init__(message)
        self.message = message
        self.violations = violations or []


class MidExecutionPolicyChecker:
    """
    Check policy constraints during execution.

    Called before each step to detect:
    - Policy changes since submission
    - Budget consumption exceeding new limits
    - Runtime policy violations

    Layer: L5 (Execution & Workers)
    """

    def __init__(
        self,
        check_interval: timedelta = timedelta(seconds=POLICY_CHECK_INTERVAL_SECONDS),
        min_steps_between_checks: int = POLICY_CHECK_MIN_STEPS,
    ):
        """
        Initialize policy checker.

        Args:
            check_interval: Minimum time between checks
            min_steps_between_checks: Minimum steps between checks
        """
        self._check_interval = check_interval
        self._min_steps = min_steps_between_checks
        self._last_check_time: Dict[str, datetime] = {}
        self._last_check_step: Dict[str, int] = {}
        self._cached_limits: Dict[str, Dict[str, Any]] = {}

    def check_before_step(
        self,
        run_id: str,
        tenant_id: str,
        step_index: int,
        cost_so_far: float,
        agent_id: Optional[str] = None,
        session: Optional[Session] = None,
    ) -> PolicyCheckResult:
        """
        Check if run should continue before next step.

        Args:
            run_id: Run ID
            tenant_id: Tenant ID
            step_index: Current step index (0-based)
            cost_so_far: Total cost consumed so far
            agent_id: Optional agent ID
            session: Optional database session

        Returns:
            PolicyCheckResult with decision and details
        """
        import time

        start_time = time.time()
        _ = agent_id  # Reserved for future per-agent policy checks

        # Check if policy checking is enabled
        if not MID_EXECUTION_POLICY_CHECK_ENABLED:
            return PolicyCheckResult(
                decision=PolicyDecision.SKIP,
                reason="Mid-execution policy checking disabled",
            )

        # Check interval throttling
        if self._should_skip_check(run_id, step_index):
            return PolicyCheckResult(
                decision=PolicyDecision.SKIP,
                reason="Check skipped (interval throttle)",
            )

        # Record this check
        self._last_check_time[run_id] = datetime.now(timezone.utc)
        self._last_check_step[run_id] = step_index

        # Perform actual policy check
        violations: List[PolicyViolation] = []

        try:
            # Check 1: Budget limit
            budget_violation = self._check_budget_limit(
                run_id, tenant_id, cost_so_far, session
            )
            if budget_violation:
                violations.append(budget_violation)

            # Check 2: Policy changes
            policy_violation = self._check_policy_changes(
                run_id, tenant_id, session
            )
            if policy_violation:
                violations.append(policy_violation)

            # Check 3: Manual stop request
            stop_violation = self._check_manual_stop(run_id, session)
            if stop_violation:
                violations.append(stop_violation)

            # Check 4: Tenant status
            tenant_violation = self._check_tenant_status(tenant_id, session)
            if tenant_violation:
                violations.append(tenant_violation)

        except Exception as e:
            logger.error(
                "policy_check_error",
                extra={"run_id": run_id, "error": str(e)},
            )
            # On error, allow continuation (fail-open)
            return PolicyCheckResult(
                decision=PolicyDecision.CONTINUE,
                reason=f"Policy check error (fail-open): {e}",
                check_duration_ms=(time.time() - start_time) * 1000,
            )

        # Determine decision based on violations
        decision, reason = self._determine_decision(violations)

        duration_ms = (time.time() - start_time) * 1000

        # Record metrics
        if METRICS_ENABLED:
            POLICY_CHECKS.labels(decision=decision.value).inc()
            POLICY_CHECK_DURATION.observe(duration_ms / 1000)

        result = PolicyCheckResult(
            decision=decision,
            reason=reason,
            violations=violations,
            check_duration_ms=duration_ms,
        )

        if violations:
            logger.info(
                "policy_violations_detected",
                extra={
                    "run_id": run_id,
                    "decision": decision.value,
                    "violation_count": len(violations),
                    "violations": [v.violation_type.value for v in violations],
                },
            )

        return result

    def _should_skip_check(self, run_id: str, step_index: int) -> bool:
        """Determine if check should be skipped due to throttling."""
        now = datetime.now(timezone.utc)

        # Check time interval
        last_time = self._last_check_time.get(run_id)
        if last_time and (now - last_time) < self._check_interval:
            return True

        # Check step interval
        last_step = self._last_check_step.get(run_id, -self._min_steps)
        if (step_index - last_step) < self._min_steps:
            return True

        return False

    def _check_budget_limit(
        self,
        run_id: str,
        tenant_id: str,
        cost_so_far: float,
        session: Optional[Session],
    ) -> Optional[PolicyViolation]:
        """Check if budget limit has been exceeded."""
        try:
            # Import here to avoid circular imports
            from app.db import engine
            from app.models.policy_rule import PolicyRule

            with Session(engine) if session is None else _dummy_context(session) as sess:
                # Get active budget policies for tenant
                stmt = select(PolicyRule).where(
                    PolicyRule.tenant_id == tenant_id,
                    PolicyRule.is_active == True,  # noqa: E712
                    PolicyRule.metric.in_(["cost", "budget", "total_cost"]),
                )
                policies = sess.exec(stmt).all()

                for policy in policies:
                    limit = policy.threshold_value or 0
                    if cost_so_far > limit:
                        return PolicyViolation(
                            violation_type=PolicyViolationType.BUDGET_EXCEEDED,
                            message=f"Budget exceeded: ${cost_so_far:.2f} > ${limit:.2f}",
                            current_value=cost_so_far,
                            limit_value=limit,
                            policy_id=str(policy.id),
                        )

        except Exception as e:
            logger.warning(
                "budget_check_failed",
                extra={"run_id": run_id, "error": str(e)},
            )

        return None

    def _check_policy_changes(
        self,
        run_id: str,
        tenant_id: str,
        session: Optional[Session],
    ) -> Optional[PolicyViolation]:
        """Check if relevant policies have changed since run started."""
        try:
            from app.db import engine
            from app.models.run import Run

            with Session(engine) if session is None else _dummy_context(session) as sess:
                # Get run start time
                run = sess.get(Run, run_id)
                if not run:
                    return None

                run_started = run.created_at

                # Check for policy changes after run started
                # This is a simplified check - in production, you'd compare
                # the policy version at run start vs now
                from app.models.policy_rule import PolicyRule

                stmt = select(PolicyRule).where(
                    PolicyRule.tenant_id == tenant_id,
                    PolicyRule.updated_at > run_started,
                    PolicyRule.is_active == False,  # noqa: E712 - Policy was disabled
                )
                disabled_policies = sess.exec(stmt).all()

                if disabled_policies:
                    return PolicyViolation(
                        violation_type=PolicyViolationType.POLICY_DISABLED,
                        message=f"Policy disabled during execution: {len(disabled_policies)} policies",
                        policy_id=str(disabled_policies[0].id) if disabled_policies else None,
                    )

        except Exception as e:
            logger.warning(
                "policy_change_check_failed",
                extra={"run_id": run_id, "error": str(e)},
            )

        return None

    def _check_manual_stop(
        self,
        run_id: str,
        session: Optional[Session],
    ) -> Optional[PolicyViolation]:
        """Check if manual stop was requested for this run."""
        try:
            from app.db import engine
            from app.models.run import Run

            with Session(engine) if session is None else _dummy_context(session) as sess:
                run = sess.get(Run, run_id)
                if run and getattr(run, "stop_requested", False):
                    return PolicyViolation(
                        violation_type=PolicyViolationType.MANUAL_STOP,
                        message="Manual stop requested",
                    )

        except Exception as e:
            logger.warning(
                "manual_stop_check_failed",
                extra={"run_id": run_id, "error": str(e)},
            )

        return None

    def _check_tenant_status(
        self,
        tenant_id: str,
        session: Optional[Session],
    ) -> Optional[PolicyViolation]:
        """Check if tenant has been suspended."""
        try:
            from app.db import engine
            from app.models.tenant import Tenant

            with Session(engine) if session is None else _dummy_context(session) as sess:
                tenant = sess.get(Tenant, tenant_id)
                if tenant and getattr(tenant, "is_suspended", False):
                    return PolicyViolation(
                        violation_type=PolicyViolationType.TENANT_SUSPENDED,
                        message="Tenant suspended",
                    )

        except Exception as e:
            logger.warning(
                "tenant_status_check_failed",
                extra={"tenant_id": tenant_id, "error": str(e)},
            )

        return None

    def _determine_decision(
        self, violations: List[PolicyViolation]
    ) -> tuple[PolicyDecision, str]:
        """Determine decision based on violations."""
        if not violations:
            return PolicyDecision.CONTINUE, "No violations detected"

        # Categorize violations by severity
        terminate_types = {
            PolicyViolationType.BUDGET_EXCEEDED,
            PolicyViolationType.TENANT_SUSPENDED,
            PolicyViolationType.MANUAL_STOP,
        }
        pause_types = {
            PolicyViolationType.LIMIT_CHANGED,
            PolicyViolationType.POLICY_DISABLED,
        }

        for v in violations:
            if v.violation_type in terminate_types:
                return PolicyDecision.TERMINATE, v.message

        for v in violations:
            if v.violation_type in pause_types:
                return PolicyDecision.PAUSE, v.message

        # Default to pause for unknown violations
        return PolicyDecision.PAUSE, violations[0].message

    def clear_run_state(self, run_id: str) -> None:
        """Clear cached state for a completed run."""
        self._last_check_time.pop(run_id, None)
        self._last_check_step.pop(run_id, None)
        self._cached_limits.pop(run_id, None)


class _dummy_context:
    """Dummy context manager for when session is already provided."""

    def __init__(self, session: Session):
        self._session = session

    def __enter__(self) -> Session:
        return self._session

    def __exit__(self, *args: Any) -> None:
        del args  # Unused but required by context manager protocol


# Singleton instance
_checker_instance: Optional[MidExecutionPolicyChecker] = None


def get_policy_checker() -> MidExecutionPolicyChecker:
    """
    Get or create MidExecutionPolicyChecker singleton.

    Returns:
        MidExecutionPolicyChecker instance
    """
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = MidExecutionPolicyChecker()
    return _checker_instance


def reset_policy_checker() -> None:
    """Reset checker instance (for testing)."""
    global _checker_instance
    _checker_instance = None
