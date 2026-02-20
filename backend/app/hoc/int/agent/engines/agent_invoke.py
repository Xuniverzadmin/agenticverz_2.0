# Layer: L4 — Domain Engine
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: async
# Role: Agent-to-agent invocation skill
# Callers: agent runtime, workers
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3
# Reference: Agent Skills
# capability_id: CAP-008

# M12 Agent Invoke Skill
# Invoke another agent and wait for response with correlation ID
#
# Credit cost: 10 credits

import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.agents.services.credit_service import CREDIT_COSTS, CreditService, get_credit_service
from app.agents.services.invoke_audit_driver import InvokeAuditService, get_invoke_audit_service  # PIN-468
from app.agents.services.message_service import MessageService, get_message_service
from app.agents.services.registry_service import RegistryService, get_registry_service

logger = logging.getLogger("nova.agents.skills.agent_invoke")


def _sanitize_channel_name(channel: str) -> str:
    """
    Sanitize PostgreSQL LISTEN/NOTIFY channel name.

    PostgreSQL identifiers should only contain alphanumeric chars and underscores.
    This prevents any SQL injection attempts via channel names.
    """
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "", channel)
    if not sanitized:
        raise ValueError(f"Invalid channel name: {channel!r}")
    return sanitized


class AgentInvokeInput(BaseModel):
    """Input schema for agent_invoke skill."""

    caller_instance_id: str = Field(..., description="Caller agent instance ID")
    target_instance_id: str = Field(..., description="Target agent instance ID")
    request_payload: Dict[str, Any] = Field(..., description="Request data to send")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Timeout for response")
    job_id: Optional[str] = Field(default=None, description="Optional job context")


class AgentInvokeOutput(BaseModel):
    """Output schema for agent_invoke skill."""

    success: bool
    invoke_id: Optional[str] = None
    response_payload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timeout: bool = False
    latency_ms: Optional[int] = None


class AgentInvokeSkill:
    """
    Skill to invoke another agent and wait for response.

    Uses correlation ID (invoke_id) for request-response routing.
    Creates an invocation record and waits for response.

    Credit cost: 10 credits
    """

    SKILL_ID = "agent_invoke"
    SKILL_VERSION = "1.0.0"
    CREDIT_COST = CREDIT_COSTS["agent_invoke"]

    def __init__(
        self,
        database_url: Optional[str] = None,
        message_service: Optional[MessageService] = None,
        registry_service: Optional[RegistryService] = None,
        credit_service: Optional[CreditService] = None,
        invoke_audit_service: Optional[InvokeAuditService] = None,
    ):
        self.database_url = database_url if database_url is not None else os.environ.get("DATABASE_URL")
        self.message_service = message_service or get_message_service()
        self.registry_service = registry_service or get_registry_service()
        self.credit_service = credit_service or get_credit_service()
        self.invoke_audit = invoke_audit_service or get_invoke_audit_service()

        if self.database_url:
            self.engine = create_engine(self.database_url, pool_pre_ping=True)
            self.Session = sessionmaker(bind=self.engine)
        else:
            self.engine = None
            self.Session = None

    def execute(
        self,
        input_data: AgentInvokeInput,
        tenant_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentInvokeOutput:
        """
        Execute agent_invoke skill.

        Args:
            input_data: Invoke parameters
            tenant_id: Tenant for billing
            context: Optional execution context

        Returns:
            AgentInvokeOutput with response or error
        """
        start_time = time.time()
        invoke_id = f"inv_{uuid4().hex[:16]}"
        job_id = UUID(input_data.job_id) if input_data.job_id else None

        # Start audit trail
        self.invoke_audit.start_invoke(
            invoke_id=invoke_id,
            caller_instance_id=input_data.caller_instance_id,
            target_instance_id=input_data.target_instance_id,
            request_payload=input_data.request_payload,
            job_id=job_id,
        )

        try:
            # Check target exists
            target = self.registry_service.get_instance(input_data.target_instance_id)
            if not target or target.status not in ("running", "idle"):
                error_msg = f"Target agent not available: {input_data.target_instance_id}"
                self.invoke_audit.fail_invoke(invoke_id, error_msg)
                return AgentInvokeOutput(
                    success=False,
                    invoke_id=invoke_id,
                    error=error_msg,
                )

            # Check credits
            has_credits, reason = self.credit_service.check_credits(tenant_id, self.CREDIT_COST)
            if not has_credits:
                self.invoke_audit.fail_invoke(invoke_id, f"Credit check failed: {reason}")
                return AgentInvokeOutput(
                    success=False,
                    invoke_id=invoke_id,
                    error=reason,
                )

            # Create invocation record
            timeout_at = datetime.now(timezone.utc) + timedelta(seconds=input_data.timeout_seconds)

            self._create_invocation(
                invoke_id=invoke_id,
                caller_instance_id=input_data.caller_instance_id,
                target_instance_id=input_data.target_instance_id,
                job_id=job_id,
                request_payload=input_data.request_payload,
                timeout_at=timeout_at,
            )

            # Send request message
            send_result = self.message_service.send(
                from_instance_id=input_data.caller_instance_id,
                to_instance_id=input_data.target_instance_id,
                message_type="invoke_request",
                payload={
                    "invoke_id": invoke_id,
                    "request": input_data.request_payload,
                },
                job_id=job_id,
            )

            if not send_result.success:
                error_msg = f"Send failed: {send_result.error}"
                self._fail_invocation(invoke_id, error_msg)
                self.invoke_audit.fail_invoke(invoke_id, error_msg)
                return AgentInvokeOutput(
                    success=False,
                    invoke_id=invoke_id,
                    error=f"Failed to send request: {send_result.error}",
                )

            # Wait for response
            response = self._wait_for_response(
                invoke_id=invoke_id,
                timeout_seconds=input_data.timeout_seconds,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            if response is None:
                self._timeout_invocation(invoke_id)
                self.invoke_audit.fail_invoke(invoke_id, "Invocation timed out", status="timeout")
                return AgentInvokeOutput(
                    success=False,
                    invoke_id=invoke_id,
                    timeout=True,
                    error="Invocation timed out",
                    latency_ms=latency_ms,
                )

            # Charge credits on success
            self.credit_service.charge_skill(
                skill="agent_invoke",
                tenant_id=tenant_id,
                job_id=job_id,
                context={"invoke_id": invoke_id},
            )

            # Record successful completion in audit trail
            self.invoke_audit.complete_invoke(
                invoke_id=invoke_id,
                response_payload=response,
                credits_charged=self.CREDIT_COST,
            )

            logger.info(
                "agent_invoke_success",
                extra={
                    "invoke_id": invoke_id,
                    "target": input_data.target_instance_id,
                    "latency_ms": latency_ms,
                },
            )

            return AgentInvokeOutput(
                success=True,
                invoke_id=invoke_id,
                response_payload=response,
                latency_ms=latency_ms,
            )

        except Exception as e:
            error_msg = f"Internal error: {str(e)[:100]}"
            logger.error(f"agent_invoke error: {e}", exc_info=True)
            self.invoke_audit.fail_invoke(invoke_id, error_msg)
            return AgentInvokeOutput(
                success=False,
                invoke_id=invoke_id,
                error=error_msg,
            )

    def _create_invocation(
        self,
        invoke_id: str,
        caller_instance_id: str,
        target_instance_id: str,
        job_id: Optional[UUID],
        request_payload: Dict[str, Any],
        timeout_at: datetime,
    ) -> None:
        """Create invocation record in DB."""
        if not self.Session:
            return

        with self.Session() as session:
            session.execute(
                text(
                    """
                    INSERT INTO agents.invocations (
                        invoke_id, caller_instance_id, target_instance_id,
                        job_id, request_payload, status, timeout_at, created_at
                    ) VALUES (
                        :invoke_id, :caller_instance_id, :target_instance_id,
                        CAST(:job_id AS UUID), CAST(:request_payload AS JSONB),
                        'pending', :timeout_at, now()
                    )
                """
                ),
                {
                    "invoke_id": invoke_id,
                    "caller_instance_id": caller_instance_id,
                    "target_instance_id": target_instance_id,
                    "job_id": str(job_id) if job_id else None,
                    "request_payload": json.dumps(request_payload),
                    "timeout_at": timeout_at,
                },
            )
            session.commit()

    def _wait_for_response(
        self,
        invoke_id: str,
        timeout_seconds: int,
        poll_interval: float = 0.5,
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for invocation response using PostgreSQL LISTEN/NOTIFY.

        M12.1: Uses LISTEN/NOTIFY for sub-second latency instead of polling.
        Falls back to polling if LISTEN fails.
        """
        if not self.database_url:
            time.sleep(min(timeout_seconds, 5))
            return None

        # Sanitize channel name to prevent SQL injection (defense in depth)
        channel = _sanitize_channel_name(f"invoke_{invoke_id}")

        try:
            import select

            import psycopg2

            # Use raw psycopg2 for LISTEN
            conn = psycopg2.connect(self.database_url)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            # LISTEN doesn't support parameterized queries, but channel is sanitized
            cur.execute(f"LISTEN {channel}")  # postflight: ignore[security]

            deadline = time.time() + timeout_seconds

            while time.time() < deadline:
                remaining = deadline - time.time()
                if remaining <= 0:
                    break

                # Wait for notification with 1s max intervals
                if select.select([conn], [], [], min(remaining, 1.0)) != ([], [], []):
                    conn.poll()
                    # Got notification - check response
                    if conn.notifies:
                        conn.notifies.clear()

                # Check DB for response
                with self.Session() as session:
                    result = session.execute(
                        text(
                            """
                            SELECT response_payload, status
                            FROM agents.invocations
                            WHERE invoke_id = :invoke_id
                        """
                        ),
                        {"invoke_id": invoke_id},
                    )
                    row = result.fetchone()

                    if row:
                        response_payload, status = row
                        if status == "completed" and response_payload:
                            cur.close()
                            conn.close()
                            return response_payload
                        elif status in ("failed", "timeout"):
                            cur.close()
                            conn.close()
                            return None

            cur.close()
            conn.close()
            return None

        except Exception as e:
            logger.warning(f"LISTEN/NOTIFY failed, falling back to polling: {e}")
            # Fallback to polling
            return self._poll_for_response(invoke_id, timeout_seconds, poll_interval)

    def _poll_for_response(
        self,
        invoke_id: str,
        timeout_seconds: int,
        poll_interval: float = 0.5,
    ) -> Optional[Dict[str, Any]]:
        """Fallback polling method for response."""
        if not self.Session:
            return None

        deadline = time.time() + timeout_seconds

        while time.time() < deadline:
            with self.Session() as session:
                result = session.execute(
                    text(
                        """
                        SELECT response_payload, status
                        FROM agents.invocations
                        WHERE invoke_id = :invoke_id
                    """
                    ),
                    {"invoke_id": invoke_id},
                )
                row = result.fetchone()

                if row:
                    response_payload, status = row
                    if status == "completed" and response_payload:
                        return response_payload
                    elif status in ("failed", "timeout"):
                        return None

            time.sleep(poll_interval)

        return None

    def _fail_invocation(self, invoke_id: str, error: str) -> None:
        """Mark invocation as failed."""
        if not self.Session:
            return

        with self.Session() as session:
            session.execute(
                text(
                    """
                    UPDATE agents.invocations
                    SET status = 'failed', error_message = :error, completed_at = now()
                    WHERE invoke_id = :invoke_id
                """
                ),
                {"invoke_id": invoke_id, "error": error[:500]},
            )
            session.commit()

    def _timeout_invocation(self, invoke_id: str) -> None:
        """Mark invocation as timed out."""
        if not self.Session:
            return

        with self.Session() as session:
            session.execute(
                text(
                    """
                    UPDATE agents.invocations
                    SET status = 'timeout', completed_at = now()
                    WHERE invoke_id = :invoke_id
                """
                ),
                {"invoke_id": invoke_id},
            )
            session.commit()

    @staticmethod
    def respond_to_invoke(
        invoke_id: str,
        response_payload: Dict[str, Any],
        database_url: Optional[str] = None,
    ) -> bool:
        """
        Static method for workers to respond to an invocation.

        Args:
            invoke_id: Invocation to respond to
            response_payload: Response data

        Returns:
            True if response recorded
        """
        db_url = database_url if database_url is not None else os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("No DATABASE_URL for respond_to_invoke")
            return False

        engine = create_engine(db_url, pool_pre_ping=True)
        Session = sessionmaker(bind=engine)

        with Session() as session:
            try:
                result = session.execute(
                    text(
                        """
                        UPDATE agents.invocations
                        SET status = 'completed',
                            response_payload = CAST(:response AS JSONB),
                            completed_at = now()
                        WHERE invoke_id = :invoke_id AND status = 'pending'
                        RETURNING invoke_id
                    """
                    ),
                    {
                        "invoke_id": invoke_id,
                        "response": json.dumps(response_payload),
                    },
                )
                row = result.fetchone()

                if row:
                    # M12.1: Notify caller via LISTEN/NOTIFY for sub-second latency
                    session.execute(
                        text("SELECT pg_notify(:channel, :payload)"),
                        {
                            "channel": f"invoke_{invoke_id}",
                            "payload": json.dumps({"status": "completed"}),
                        },
                    )

                session.commit()

                if row:
                    logger.debug(f"Responded to invoke: {invoke_id}")
                    return True

                return False

            except Exception as e:
                session.rollback()
                logger.error(f"respond_to_invoke failed: {e}")
                return False

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for skill."""
        return {
            "skill_id": self.SKILL_ID,
            "version": self.SKILL_VERSION,
            "description": "Invoke another agent and wait for response",
            "credit_cost": float(self.CREDIT_COST),
            "input_schema": AgentInvokeInput.model_json_schema(),
            "output_schema": AgentInvokeOutput.model_json_schema(),
        }
