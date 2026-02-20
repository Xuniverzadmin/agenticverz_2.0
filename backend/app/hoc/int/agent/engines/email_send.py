# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: Configuration schema for email_send skill.
# Email Send Skill (Resend)
# Pluggable email skill using Resend API with external call control
# capability_id: CAP-016

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type

import httpx
from pydantic import BaseModel

from app.schemas.skill import EmailSendInput, EmailSendOutput
from .registry import skill

logger = logging.getLogger("nova.skills.email_send")

# Resend configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_API_URL = "https://api.resend.com/emails"
DEFAULT_FROM_ADDRESS = os.getenv("RESEND_FROM_ADDRESS", "notifications@agenticverz.com")


class EmailSendConfig(BaseModel):
    """Configuration schema for email_send skill."""

    allow_external: bool = True
    api_key: Optional[str] = None
    from_address: Optional[str] = None
    timeout: float = 30.0


@skill(
    "email_send",
    input_schema=EmailSendInput,
    output_schema=EmailSendOutput,
    tags=["communication", "email", "notification"],
    default_config={"allow_external": True, "timeout": 30.0},
)
class EmailSendSkill:
    """Email sending skill using Resend API.

    Features:
    - Send emails via Resend API
    - Support for HTML and plain text
    - Multiple recipients (to, cc, bcc)
    - External call control (can stub for testing)
    - Structured result format with side effects tracking

    Environment Variables:
    - RESEND_API_KEY: API key for Resend
    - RESEND_FROM_ADDRESS: Default from address

    Usage in workflow:
        {
            "skill": "email_send",
            "params": {
                "to": "user@example.com",
                "subject": "Workflow Complete",
                "body": "Your workflow has finished successfully."
            }
        }
    """

    VERSION = "1.0.0"
    DESCRIPTION = "Send emails via Resend API for notifications and alerts"

    # Default configuration
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        *,
        allow_external: bool = True,
        api_key: Optional[str] = None,
        from_address: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize Email skill.

        Args:
            allow_external: If False, stub email sending
            api_key: Resend API key (uses env var if not provided)
            from_address: Default from address (uses env var if not provided)
            timeout: Request timeout
        """
        self.allow_external = allow_external
        self.api_key = api_key or RESEND_API_KEY
        self.from_address = from_address or DEFAULT_FROM_ADDRESS
        self.timeout = timeout

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email send.

        Args:
            params: Dict with to, subject, body, and optional fields

        Returns:
            Structured result with status, message_id, duration, side_effects
        """
        # Extract parameters
        to = params.get("to", [])
        if isinstance(to, str):
            to = [to]
        subject = params.get("subject", "")
        body = params.get("body", "")
        from_address = params.get("from_address", self.from_address)
        reply_to = params.get("reply_to")
        cc = params.get("cc", [])
        if isinstance(cc, str):
            cc = [cc]
        bcc = params.get("bcc", [])
        if isinstance(bcc, str):
            bcc = [bcc]
        is_html = params.get("html", False)
        tags = params.get("tags", {})

        started_at = datetime.now(timezone.utc)
        start_time = time.time()

        all_recipients = to + (cc or []) + (bcc or [])

        logger.info(
            "skill_execution_start",
            extra={
                "skill": "email_send",
                "recipients_count": len(all_recipients),
                "subject_preview": subject[:50] if subject else "",
            },
        )

        # Check if external calls are allowed
        if not self.allow_external:
            duration = time.time() - start_time
            logger.info(
                "skill_execution_stubbed",
                extra={
                    "skill": "email_send",
                    "reason": "external_calls_disabled",
                    "recipients": all_recipients,
                },
            )
            return {
                "skill": "email_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "stubbed",
                    "message_id": f"stub_{int(start_time)}",
                    "recipients": all_recipients,
                    "accepted": len(all_recipients),
                    "rejected": 0,
                    "note": "Email sending disabled in skill configuration",
                },
                "duration": round(duration, 3),
                "side_effects": {
                    "email_stubbed": True,
                    "would_send_to": all_recipients,
                },
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Check API key
        if not self.api_key:
            duration = time.time() - start_time
            logger.error(
                "skill_execution_failed", extra={"skill": "email_send", "error": "RESEND_API_KEY not configured"}
            )
            return {
                "skill": "email_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "error",
                    "error": "configuration_error",
                    "message": "RESEND_API_KEY not configured",
                    "recipients": all_recipients,
                    "accepted": 0,
                    "rejected": len(all_recipients),
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Validate inputs
        if not to:
            duration = time.time() - start_time
            return {
                "skill": "email_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "error",
                    "error": "validation_error",
                    "message": "No recipients specified",
                    "recipients": [],
                    "accepted": 0,
                    "rejected": 0,
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        if not subject:
            duration = time.time() - start_time
            return {
                "skill": "email_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "error",
                    "error": "validation_error",
                    "message": "Subject is required",
                    "recipients": all_recipients,
                    "accepted": 0,
                    "rejected": len(all_recipients),
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Build request payload
        payload: Dict[str, Any] = {
            "from": from_address,
            "to": to,
            "subject": subject,
        }

        # Set body as text or html
        if is_html:
            payload["html"] = body
        else:
            payload["text"] = body

        # Optional fields
        if reply_to:
            payload["reply_to"] = reply_to
        if cc:
            payload["cc"] = cc
        if bcc:
            payload["bcc"] = bcc
        if tags:
            payload["tags"] = [{"name": k, "value": v} for k, v in tags.items()]

        # Send via Resend API
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    RESEND_API_URL,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )

                duration = time.time() - start_time
                completed_at = datetime.now(timezone.utc)

                if response.status_code == 200:
                    result_data = response.json()
                    message_id = result_data.get("id", "")

                    logger.info(
                        "skill_execution_end",
                        extra={
                            "skill": "email_send",
                            "status": "ok",
                            "message_id": message_id,
                            "recipients_count": len(all_recipients),
                            "duration": round(duration, 3),
                        },
                    )

                    return {
                        "skill": "email_send",
                        "skill_version": self.VERSION,
                        "result": {
                            "status": "ok",
                            "message_id": message_id,
                            "recipients": all_recipients,
                            "accepted": len(all_recipients),
                            "rejected": 0,
                        },
                        "duration": round(duration, 3),
                        "side_effects": {
                            "email_sent": True,
                            "provider": "resend",
                            "message_id": message_id,
                        },
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                    }
                else:
                    # API error
                    error_body = response.text[:500]
                    logger.warning(
                        "skill_execution_failed",
                        extra={
                            "skill": "email_send",
                            "http_status": response.status_code,
                            "error": error_body,
                        },
                    )

                    return {
                        "skill": "email_send",
                        "skill_version": self.VERSION,
                        "result": {
                            "status": "error",
                            "error": "api_error",
                            "message": f"Resend API error ({response.status_code}): {error_body}",
                            "recipients": all_recipients,
                            "accepted": 0,
                            "rejected": len(all_recipients),
                        },
                        "duration": round(duration, 3),
                        "side_effects": {},
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                    }

        except httpx.TimeoutException:
            duration = time.time() - start_time
            logger.warning("skill_execution_timeout", extra={"skill": "email_send", "timeout": self.timeout})
            return {
                "skill": "email_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "timeout",
                    "error": "timeout",
                    "message": f"Request timed out after {self.timeout}s",
                    "recipients": all_recipients,
                    "accepted": 0,
                    "rejected": len(all_recipients),
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        except httpx.RequestError as e:
            duration = time.time() - start_time
            logger.error("skill_execution_failed", extra={"skill": "email_send", "error": str(e)[:200]})
            return {
                "skill": "email_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "error",
                    "error": "network_error",
                    "message": f"Network error: {str(e)[:200]}",
                    "recipients": all_recipients,
                    "accepted": 0,
                    "rejected": len(all_recipients),
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

    @classmethod
    def get_input_schema(cls) -> Type[BaseModel]:
        """Return input schema for validation."""
        return EmailSendInput

    @classmethod
    def get_output_schema(cls) -> Type[BaseModel]:
        """Return output schema for validation."""
        return EmailSendOutput


# Registration happens via @skill decorator above
