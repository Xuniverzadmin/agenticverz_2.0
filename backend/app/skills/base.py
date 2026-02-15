# Skill Base Classes for M11
# Provides common patterns for idempotent, deterministic skills

import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ..metrics import (
    m11_circuit_breaker_closes_total,
    m11_circuit_breaker_failures_total,
    m11_circuit_breaker_opens_total,
    m11_circuit_breaker_rejected_total,
    m11_circuit_breaker_state,
    m11_circuit_breaker_successes_total,
    m11_skill_execution_seconds,
    m11_skill_executions_total,
    m11_skill_idempotency_conflicts_total,
    m11_skill_idempotency_hits_total,
)
from app.hoc.cus.logs.L6_drivers.idempotency_driver import (
    IdempotencyResult,
    get_idempotency_store,
)

logger = logging.getLogger("nova.skills.base")


# ============ Circuit Breaker for External Skills ============


class SkillCircuitBreaker:
    """
    Lightweight circuit breaker for M11 external skills.

    Uses m11_audit.circuit_breaker_state table for persistent state.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fast-fail
    - HALF_OPEN: Testing if service recovered

    Usage:
        breaker = SkillCircuitBreaker("slack_api")

        if await breaker.is_open():
            return {"error": "circuit_open", "retry_after": breaker.cooldown_until}

        try:
            result = await call_slack_api()
            await breaker.record_success()
        except Exception as e:
            await breaker.record_failure()
            raise
    """

    # Circuit breaker configuration
    FAILURE_THRESHOLD = 5  # Failures before opening
    COOLDOWN_SECONDS = 60  # How long to stay open
    HALF_OPEN_MAX_CALLS = 3  # Max calls in half-open state

    def __init__(self, target: str, database_url: Optional[str] = None):
        """
        Initialize circuit breaker.

        Args:
            target: External service target (e.g., "slack_api", "voyage_ai")
            database_url: Database URL (defaults to DATABASE_URL env var)
        """
        self.target = target
        self.database_url = database_url or os.environ.get("DATABASE_URL")

        if self.database_url:
            self.engine = create_engine(self.database_url)
            self.Session = sessionmaker(bind=self.engine)
        else:
            self.engine = None
            self.Session = None

    def _get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state from DB."""
        if not self.Session:
            return {"state": "CLOSED", "failure_count": 0}

        try:
            with self.Session() as session:
                result = session.execute(
                    text(
                        """
                        SELECT state, failure_count, last_failure_at, opened_at, cooldown_until
                        FROM m11_audit.circuit_breaker_state
                        WHERE target = :target
                    """
                    ),
                    {"target": self.target},
                )
                row = result.fetchone()

                if not row:
                    return {"state": "CLOSED", "failure_count": 0}

                return {
                    "state": row[0],
                    "failure_count": row[1],
                    "last_failure_at": row[2],
                    "opened_at": row[3],
                    "cooldown_until": row[4],
                }
        except Exception as e:
            logger.warning(f"Circuit breaker state check failed: {e}")
            return {"state": "CLOSED", "failure_count": 0}

    def _upsert_state(
        self,
        state: str,
        failure_count: int,
        opened_at: Optional[datetime] = None,
        cooldown_until: Optional[datetime] = None,
        last_failure_at: Optional[datetime] = None,
    ) -> None:
        """Update circuit breaker state in DB."""
        if not self.Session:
            return

        try:
            with self.Session() as session:
                session.execute(
                    text(
                        """
                        INSERT INTO m11_audit.circuit_breaker_state
                        (target, state, failure_count, last_failure_at, opened_at, cooldown_until, updated_at)
                        VALUES (:target, :state, :failure_count, :last_failure_at, :opened_at, :cooldown_until, now())
                        ON CONFLICT (target) DO UPDATE SET
                            state = :state,
                            failure_count = :failure_count,
                            last_failure_at = COALESCE(:last_failure_at, m11_audit.circuit_breaker_state.last_failure_at),
                            opened_at = COALESCE(:opened_at, m11_audit.circuit_breaker_state.opened_at),
                            cooldown_until = :cooldown_until,
                            updated_at = now()
                    """
                    ),
                    {
                        "target": self.target,
                        "state": state,
                        "failure_count": failure_count,
                        "last_failure_at": last_failure_at,
                        "opened_at": opened_at,
                        "cooldown_until": cooldown_until,
                    },
                )
                session.commit()
        except Exception as e:
            logger.warning(f"Circuit breaker state update failed: {e}")

    async def is_open(self) -> bool:
        """Check if circuit breaker is open (should reject requests)."""
        state_data = self._get_state()
        current_state = state_data.get("state", "CLOSED")
        cooldown_until = state_data.get("cooldown_until")

        if current_state == "CLOSED":
            return False

        if current_state == "OPEN":
            # Check if cooldown expired
            if cooldown_until:
                now = datetime.now(timezone.utc)
                cooldown_dt = cooldown_until
                if cooldown_dt.tzinfo is None:
                    cooldown_dt = cooldown_dt.replace(tzinfo=timezone.utc)

                if now >= cooldown_dt:
                    # Transition to HALF_OPEN
                    self._upsert_state(
                        state="HALF_OPEN",
                        failure_count=state_data.get("failure_count", 0),
                        cooldown_until=None,
                    )
                    logger.info(f"Circuit breaker {self.target}: OPEN -> HALF_OPEN")
                    return False
            return True

        # HALF_OPEN: allow requests to test recovery
        return False

    async def record_success(self) -> None:
        """Record a successful call (may close circuit)."""
        state_data = self._get_state()
        current_state = state_data.get("state", "CLOSED")

        # Record metric
        m11_circuit_breaker_successes_total.labels(target=self.target).inc()

        if current_state == "HALF_OPEN":
            # Success in half-open -> close the circuit
            self._upsert_state(
                state="CLOSED",
                failure_count=0,
                opened_at=None,
                cooldown_until=None,
            )
            m11_circuit_breaker_closes_total.labels(target=self.target).inc()
            m11_circuit_breaker_state.labels(target=self.target).set(0)  # CLOSED
            logger.info(f"Circuit breaker {self.target}: HALF_OPEN -> CLOSED (recovered)")
        elif current_state == "CLOSED" and state_data.get("failure_count", 0) > 0:
            # Reset failure count on success
            self._upsert_state(
                state="CLOSED",
                failure_count=0,
            )

    async def record_failure(self) -> None:
        """Record a failed call (may open circuit)."""
        state_data = self._get_state()
        current_state = state_data.get("state", "CLOSED")
        failure_count = state_data.get("failure_count", 0) + 1
        now = datetime.now(timezone.utc)

        # Record metric
        m11_circuit_breaker_failures_total.labels(target=self.target).inc()

        if current_state == "HALF_OPEN":
            # Failure in half-open -> reopen the circuit
            cooldown_until = now + timedelta(seconds=self.COOLDOWN_SECONDS * 2)  # Double cooldown
            self._upsert_state(
                state="OPEN",
                failure_count=failure_count,
                opened_at=now,
                cooldown_until=cooldown_until,
                last_failure_at=now,
            )
            m11_circuit_breaker_opens_total.labels(target=self.target).inc()
            m11_circuit_breaker_state.labels(target=self.target).set(1)  # OPEN
            logger.warning(f"Circuit breaker {self.target}: HALF_OPEN -> OPEN (still failing)")
        elif current_state == "CLOSED":
            if failure_count >= self.FAILURE_THRESHOLD:
                # Open the circuit
                cooldown_until = now + timedelta(seconds=self.COOLDOWN_SECONDS)
                self._upsert_state(
                    state="OPEN",
                    failure_count=failure_count,
                    opened_at=now,
                    cooldown_until=cooldown_until,
                    last_failure_at=now,
                )
                m11_circuit_breaker_opens_total.labels(target=self.target).inc()
                m11_circuit_breaker_state.labels(target=self.target).set(1)  # OPEN
                logger.warning(
                    f"Circuit breaker {self.target}: CLOSED -> OPEN "
                    f"(failures={failure_count}, cooldown_until={cooldown_until})"
                )
            else:
                self._upsert_state(
                    state="CLOSED",
                    failure_count=failure_count,
                    last_failure_at=now,
                )
        elif current_state == "OPEN":
            # Already open, just update failure count
            self._upsert_state(
                state="OPEN",
                failure_count=failure_count,
                last_failure_at=now,
            )

    def get_cooldown_remaining(self) -> Optional[int]:
        """Get seconds remaining in cooldown (None if not in cooldown)."""
        state_data = self._get_state()
        cooldown_until = state_data.get("cooldown_until")

        if not cooldown_until:
            return None

        now = datetime.now(timezone.utc)
        cooldown_dt = cooldown_until
        if cooldown_dt.tzinfo is None:
            cooldown_dt = cooldown_dt.replace(tzinfo=timezone.utc)

        remaining = (cooldown_dt - now).total_seconds()
        return max(0, int(remaining)) if remaining > 0 else None


# Global circuit breaker cache
_circuit_breakers: Dict[str, SkillCircuitBreaker] = {}


def get_circuit_breaker(target: str) -> SkillCircuitBreaker:
    """Get or create circuit breaker for a target."""
    if target not in _circuit_breakers:
        _circuit_breakers[target] = SkillCircuitBreaker(target)
    return _circuit_breakers[target]


class IdempotentSkill(ABC):
    """
    Base class for skills with idempotency support.

    Provides:
    - Automatic idempotency key handling
    - Cached result retrieval for duplicate requests
    - Consistent result format
    - Side-effect tracking

    Usage:
        class MySkill(IdempotentSkill):
            VERSION = "1.0.0"
            DESCRIPTION = "My skill description"

            async def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
                # Your skill logic here
                return {"my_result": "value"}
    """

    VERSION: str = "0.0.0"
    DESCRIPTION: str = "Base skill"

    def __init__(self, allow_external: bool = True, timeout: float = 30.0):
        """
        Initialize skill.

        Args:
            allow_external: If False, stub external calls (for testing)
            timeout: Default timeout for operations
        """
        self.allow_external = allow_external
        self.timeout = timeout
        self._idempotency_store = None

    async def _get_idempotency_store(self):
        """Lazy-load idempotency store."""
        if self._idempotency_store is None:
            self._idempotency_store = await get_idempotency_store()
        return self._idempotency_store

    @property
    def skill_name(self) -> str:
        """Get skill name from class name."""
        name = self.__class__.__name__
        # Convert CamelCase to snake_case
        import re

        name = re.sub(r"Skill$", "", name)
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        return name

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute skill with idempotency handling.

        Args:
            params: Skill parameters including optional idempotency_key

        Returns:
            Structured result dict
        """
        started_at = datetime.now(timezone.utc)
        start_time = time.time()

        idempotency_key = params.get("idempotency_key")
        tenant_id = params.get("tenant_id", "default")
        workflow_run_id = params.get("workflow_run_id", "")

        # Check idempotency if key provided
        if idempotency_key:
            try:
                store = await self._get_idempotency_store()
                check_result = await store.check(
                    idempotency_key=idempotency_key, request_data=params, tenant_id=tenant_id, trace_id=workflow_run_id
                )

                if check_result.result == IdempotencyResult.DUPLICATE:
                    # Record idempotency hit metric
                    m11_skill_idempotency_hits_total.labels(skill=self.skill_name).inc()
                    logger.info(
                        "skill_idempotency_cache_hit",
                        extra={
                            "skill": self.skill_name,
                            "idempotency_key": idempotency_key,
                        },
                    )
                    duration = time.time() - start_time
                    m11_skill_execution_seconds.labels(skill=self.skill_name).observe(duration)
                    m11_skill_executions_total.labels(skill=self.skill_name, status="ok", tenant_id=tenant_id).inc()
                    return {
                        "skill": self.skill_name,
                        "skill_version": self.VERSION,
                        "result": {
                            "status": "ok",
                            "from_cache": True,
                            "original_trace_id": check_result.stored_trace_id,
                        },
                        "duration": round(duration, 3),
                        "side_effects": {},
                        "started_at": started_at.isoformat(),
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                    }

                elif check_result.result == IdempotencyResult.CONFLICT:
                    # Record idempotency conflict metric
                    m11_skill_idempotency_conflicts_total.labels(skill=self.skill_name).inc()
                    logger.warning(
                        "skill_idempotency_conflict",
                        extra={
                            "skill": self.skill_name,
                            "idempotency_key": idempotency_key,
                        },
                    )
                    duration = time.time() - start_time
                    m11_skill_execution_seconds.labels(skill=self.skill_name).observe(duration)
                    m11_skill_executions_total.labels(skill=self.skill_name, status="error", tenant_id=tenant_id).inc()
                    return {
                        "skill": self.skill_name,
                        "skill_version": self.VERSION,
                        "result": {
                            "status": "error",
                            "error": "idempotency_conflict",
                            "message": "Request parameters differ from original",
                        },
                        "duration": round(duration, 3),
                        "side_effects": {},
                        "started_at": started_at.isoformat(),
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                    }
            except Exception as e:
                logger.warning(f"Idempotency check failed, proceeding: {e}")

        # Execute actual skill logic
        try:
            result = await self._execute_impl(params)

            # Record execution metrics
            duration = time.time() - start_time
            m11_skill_execution_seconds.labels(skill=self.skill_name).observe(duration)
            result_status = result.get("result", {}).get("status", "unknown")
            metric_status = "ok" if result_status in ("ok", "completed", "stubbed") else "error"
            m11_skill_executions_total.labels(skill=self.skill_name, status=metric_status, tenant_id=tenant_id).inc()

            # Mark idempotency key as completed
            if idempotency_key:
                try:
                    store = await self._get_idempotency_store()
                    await store.mark_completed(
                        idempotency_key=idempotency_key,
                        trace_id=workflow_run_id,
                        tenant_id=tenant_id,
                        response_data=result,
                    )
                except Exception as e:
                    logger.warning(f"Failed to mark idempotency completed: {e}")

            return result

        except Exception as e:
            # Mark idempotency key as failed
            if idempotency_key:
                try:
                    store = await self._get_idempotency_store()
                    await store.mark_failed(idempotency_key=idempotency_key, tenant_id=tenant_id, error=str(e))
                except Exception as mark_e:
                    logger.warning(f"Failed to mark idempotency failed: {mark_e}")

            duration = time.time() - start_time

            # Record error metrics
            m11_skill_execution_seconds.labels(skill=self.skill_name).observe(duration)
            m11_skill_executions_total.labels(skill=self.skill_name, status="error", tenant_id=tenant_id).inc()

            logger.error("skill_execution_failed", extra={"skill": self.skill_name, "error": str(e)[:200]})
            return {
                "skill": self.skill_name,
                "skill_version": self.VERSION,
                "result": {
                    "status": "error",
                    "error": "execution_error",
                    "message": str(e)[:500],
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

    @abstractmethod
    async def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement skill logic in subclass.

        Args:
            params: Skill parameters

        Returns:
            Structured result dict with 'skill', 'skill_version', 'result',
            'duration', 'side_effects', 'started_at', 'completed_at'
        """
        pass

    @classmethod
    def get_input_schema(cls) -> Optional[Type[BaseModel]]:
        """Return input schema for validation."""
        return None

    @classmethod
    def get_output_schema(cls) -> Optional[Type[BaseModel]]:
        """Return output schema for validation."""
        return None


class ExternalSkill(IdempotentSkill):
    """
    Base class for skills that call external APIs.

    Adds:
    - External call control (stubbing for tests)
    - Circuit breaker for external service protection
    - Rate limit handling
    - Timeout configuration
    """

    # Override in subclass to set circuit breaker target
    CIRCUIT_BREAKER_TARGET: Optional[str] = None

    def __init__(
        self,
        allow_external: bool = True,
        timeout: float = 30.0,
        max_retries: int = 3,
        use_circuit_breaker: bool = True,
    ):
        super().__init__(allow_external=allow_external, timeout=timeout)
        self.max_retries = max_retries
        self.use_circuit_breaker = use_circuit_breaker
        self._circuit_breaker: Optional[SkillCircuitBreaker] = None

    def _get_circuit_breaker(self) -> Optional[SkillCircuitBreaker]:
        """Get circuit breaker for this skill."""
        if not self.use_circuit_breaker:
            return None

        target = self.CIRCUIT_BREAKER_TARGET or self.skill_name
        if self._circuit_breaker is None:
            self._circuit_breaker = get_circuit_breaker(target)
        return self._circuit_breaker

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute with external call control and circuit breaker."""
        started_at = datetime.now(timezone.utc)
        start_time = time.time()

        if not self.allow_external:
            duration = time.time() - start_time
            logger.info(
                "skill_execution_stubbed",
                extra={
                    "skill": self.skill_name,
                    "reason": "external_calls_disabled",
                },
            )
            return {
                "skill": self.skill_name,
                "skill_version": self.VERSION,
                "result": {
                    "status": "stubbed",
                    "note": "External calls disabled in skill configuration",
                },
                "duration": round(duration, 3),
                "side_effects": {"stubbed": True},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Check circuit breaker
        breaker = self._get_circuit_breaker()
        if breaker and await breaker.is_open():
            cooldown = breaker.get_cooldown_remaining()
            duration = time.time() - start_time

            # Record rejection metric
            m11_circuit_breaker_rejected_total.labels(target=breaker.target).inc()
            tenant_id = params.get("tenant_id", "default")
            m11_skill_executions_total.labels(skill=self.skill_name, status="circuit_open", tenant_id=tenant_id).inc()

            logger.warning(
                "skill_circuit_open",
                extra={
                    "skill": self.skill_name,
                    "target": breaker.target,
                    "cooldown_remaining": cooldown,
                },
            )
            return {
                "skill": self.skill_name,
                "skill_version": self.VERSION,
                "result": {
                    "status": "error",
                    "error": "circuit_open",
                    "message": f"Circuit breaker open for {breaker.target}",
                    "retry_after_seconds": cooldown,
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Execute with circuit breaker tracking
        try:
            result = await super().execute(params)

            # Record success/failure based on result
            if breaker:
                result_status = result.get("result", {}).get("status", "")
                if result_status in ("ok", "stubbed", "completed"):
                    await breaker.record_success()
                elif result_status == "error":
                    error_code = result.get("result", {}).get("error", "")
                    # Don't count idempotency errors as circuit breaker failures
                    if error_code not in ("idempotency_conflict", "execution_error"):
                        await breaker.record_failure()

            return result

        except Exception:
            if breaker:
                await breaker.record_failure()
            raise
