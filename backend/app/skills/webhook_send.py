# Webhook Send Skill (M11)
# Generic webhook with HMAC-SHA256 signing

import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type

import httpx
from pydantic import BaseModel

from .registry import skill
from ..schemas.skill import WebhookSendInput, WebhookSendOutput, HttpMethod, SkillStatus

logger = logging.getLogger("nova.skills.webhook_send")

# Webhook configuration
WEBHOOK_SIGNING_SECRET = os.getenv("WEBHOOK_SIGNING_SECRET", "")
DEFAULT_TIMEOUT = 30.0


class WebhookSendConfig(BaseModel):
    """Configuration schema for webhook_send skill."""
    allow_external: bool = True
    signing_secret: Optional[str] = None
    timeout: float = DEFAULT_TIMEOUT


def sign_payload(payload_bytes: bytes, secret: str, timestamp: int) -> str:
    """
    Generate HMAC-SHA256 signature for payload.

    Format: sha256=<hex_digest>
    Message: timestamp.payload
    """
    message = f"{timestamp}.{payload_bytes.decode()}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


def verify_signature(payload_bytes: bytes, secret: str, timestamp: int, signature: str) -> bool:
    """Verify HMAC-SHA256 signature."""
    expected = sign_payload(payload_bytes, secret, timestamp)
    return hmac.compare_digest(expected, signature)


@skill(
    "webhook_send",
    input_schema=WebhookSendInput,
    output_schema=WebhookSendOutput,
    tags=["http", "webhook", "notification", "integration"],
    default_config={"allow_external": True, "timeout": DEFAULT_TIMEOUT},
)
class WebhookSendSkill:
    """Generic webhook skill with HMAC signing.

    Features:
    - HTTP POST/PUT/PATCH to arbitrary webhooks
    - HMAC-SHA256 payload signing
    - Timestamp header for replay protection
    - Idempotency support
    - External call control (can stub for testing)

    Environment Variables:
    - WEBHOOK_SIGNING_SECRET: Default signing secret

    Signature Headers Added:
    - X-Signature-256: sha256=<hex_digest>
    - X-Signature-Timestamp: <unix_timestamp>

    Usage in workflow:
        {
            "skill": "webhook_send",
            "params": {
                "url": "https://example.com/webhook",
                "payload": {"event": "workflow_complete", "run_id": "123"},
                "sign_payload": true,
                "idempotency_key": "workflow_123_webhook"
            }
        }
    """

    VERSION = "1.0.0"
    DESCRIPTION = "Send webhook requests with HMAC-SHA256 signing"

    def __init__(
        self,
        *,
        allow_external: bool = True,
        signing_secret: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.allow_external = allow_external
        self.signing_secret = signing_secret or WEBHOOK_SIGNING_SECRET
        self.timeout = timeout
        self._idempotency_cache: Dict[str, Dict] = {}

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute webhook request.

        Args:
            params: Dict with url, method, payload, headers, sign_payload, etc.

        Returns:
            Structured result with status_code, response_body, signature_sent
        """
        url = params.get("url", "")
        method = params.get("method", "POST")
        payload = params.get("payload", {})
        headers = params.get("headers", {})
        sign_payload_flag = params.get("sign_payload", True)
        signature_header = params.get("signature_header", "X-Signature-256")
        timestamp_header = params.get("timestamp_header", "X-Signature-Timestamp")
        timeout_seconds = params.get("timeout_seconds", self.timeout)
        idempotency_key = params.get("idempotency_key")

        started_at = datetime.now(timezone.utc)
        start_time = time.time()

        logger.info(
            "webhook_send_execution_start",
            extra={
                "skill": "webhook_send",
                "url": url[:100],
                "method": method,
                "sign_payload": sign_payload_flag,
            }
        )

        # Validate URL
        if not url:
            duration = time.time() - start_time
            return {
                "skill": "webhook_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "error",
                    "error": "validation_error",
                    "message": "URL is required",
                    "status_code": 0,
                    "response_body": None,
                    "signature_sent": False,
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Check stub mode
        if not self.allow_external:
            duration = time.time() - start_time
            logger.info(
                "webhook_send_stubbed",
                extra={"skill": "webhook_send", "reason": "external_calls_disabled"}
            )
            return {
                "skill": "webhook_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "stubbed",
                    "status_code": 200,
                    "response_body": "ok (stubbed)",
                    "signature_sent": sign_payload_flag,
                    "from_cache": False,
                },
                "duration": round(duration, 3),
                "side_effects": {"webhook_stubbed": True, "would_post_to": url},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Check idempotency
        if idempotency_key and idempotency_key in self._idempotency_cache:
            logger.info(
                "webhook_send_idempotency_hit",
                extra={"idempotency_key": idempotency_key}
            )
            cached = self._idempotency_cache[idempotency_key]
            return {**cached, "result": {**cached.get("result", {}), "from_cache": True}}

        # Prepare payload
        payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        timestamp = int(time.time())

        # Build request headers
        request_headers = {
            "Content-Type": "application/json",
            **headers,
        }

        # Add signature if enabled
        signature_sent = False
        if sign_payload_flag and self.signing_secret:
            signature = sign_payload(payload_bytes, self.signing_secret, timestamp)
            request_headers[signature_header] = signature
            request_headers[timestamp_header] = str(timestamp)
            signature_sent = True
        elif sign_payload_flag and not self.signing_secret:
            logger.warning(
                "webhook_send_no_secret",
                extra={"skill": "webhook_send", "url": url[:100]}
            )

        # Send webhook request
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    content=payload_bytes,
                    headers=request_headers,
                )

                duration = time.time() - start_time
                completed_at = datetime.now(timezone.utc)

                # Extract request ID from response headers
                request_id = response.headers.get("X-Request-ID") or response.headers.get("X-Request-Id")

                response_body = response.text[:10000]  # Truncate large responses

                status = "ok" if 200 <= response.status_code < 300 else "error"

                logger.info(
                    "webhook_send_execution_end",
                    extra={
                        "skill": "webhook_send",
                        "url": url[:100],
                        "status_code": response.status_code,
                        "duration": round(duration, 3),
                    }
                )

                result = {
                    "skill": "webhook_send",
                    "skill_version": self.VERSION,
                    "result": {
                        "status": status,
                        "status_code": response.status_code,
                        "response_body": response_body,
                        "request_id": request_id,
                        "signature_sent": signature_sent,
                        "from_cache": False,
                    },
                    "duration": round(duration, 3),
                    "side_effects": {
                        "webhook_sent": True,
                        "url": url,
                        "method": method.upper(),
                        "signed": signature_sent,
                    },
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                }

                # Cache successful results for idempotency
                if idempotency_key and status == "ok":
                    self._idempotency_cache[idempotency_key] = result

                return result

        except httpx.TimeoutException:
            duration = time.time() - start_time
            logger.warning(
                "webhook_send_timeout",
                extra={"skill": "webhook_send", "url": url[:100], "timeout": timeout_seconds}
            )
            return {
                "skill": "webhook_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "timeout",
                    "error": "timeout",
                    "message": f"Request timed out after {timeout_seconds}s",
                    "status_code": 0,
                    "response_body": None,
                    "signature_sent": signature_sent,
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        except httpx.RequestError as e:
            duration = time.time() - start_time
            logger.error(
                "webhook_send_failed",
                extra={"skill": "webhook_send", "url": url[:100], "error": str(e)[:200]}
            )
            return {
                "skill": "webhook_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "error",
                    "error": "network_error",
                    "message": f"Network error: {str(e)[:200]}",
                    "status_code": 0,
                    "response_body": None,
                    "signature_sent": signature_sent,
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

    @classmethod
    def get_input_schema(cls) -> Type[BaseModel]:
        return WebhookSendInput

    @classmethod
    def get_output_schema(cls) -> Type[BaseModel]:
        return WebhookSendOutput
