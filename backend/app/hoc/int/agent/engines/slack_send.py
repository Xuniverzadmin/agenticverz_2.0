# Layer: L5 — Domain Engine
# AUDIENCE: INTERNAL
# Role: Configuration schema for slack_send skill.
# Slack Send Skill (M11)
# Send messages to Slack via webhook with idempotency support

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type

import httpx
from pydantic import BaseModel

from ..schemas.skill import SlackSendInput, SlackSendOutput
from .registry import skill

logger = logging.getLogger("nova.skills.slack_send")

# Slack configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_MISMATCH_WEBHOOK = os.getenv("SLACK_MISMATCH_WEBHOOK", "")
DEFAULT_TIMEOUT = 30.0
IDEMPOTENCY_TTL = 86400  # 24 hours


class SlackSendConfig(BaseModel):
    """Configuration schema for slack_send skill."""

    allow_external: bool = True
    webhook_url: Optional[str] = None
    timeout: float = DEFAULT_TIMEOUT


@skill(
    "slack_send",
    input_schema=SlackSendInput,
    output_schema=SlackSendOutput,
    tags=["communication", "slack", "notification", "webhook"],
    default_config={"allow_external": True, "timeout": DEFAULT_TIMEOUT},
)
class SlackSendSkill:
    """Slack message sending skill via webhook.

    Features:
    - Send messages via Slack incoming webhooks
    - Support for Block Kit blocks
    - Idempotency support to prevent duplicate posts
    - External call control (can stub for testing)

    Environment Variables:
    - SLACK_WEBHOOK_URL: Default Slack webhook URL
    - SLACK_MISMATCH_WEBHOOK: Alternative webhook (for alerts)

    Usage in workflow:
        {
            "skill": "slack_send",
            "params": {
                "text": "Workflow completed successfully!",
                "channel": "#alerts",
                "idempotency_key": "workflow_123_slack"
            }
        }
    """

    VERSION = "1.0.0"
    DESCRIPTION = "Send messages to Slack via incoming webhooks"

    def __init__(
        self,
        *,
        allow_external: bool = True,
        webhook_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.allow_external = allow_external
        self.webhook_url = webhook_url or SLACK_WEBHOOK_URL
        self.timeout = timeout
        self._idempotency_cache: Dict[str, Dict] = {}

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Slack message send.

        Args:
            params: Dict with text, optional webhook_url, blocks, channel, etc.

        Returns:
            Structured result with status, webhook_response, duration
        """
        text = params.get("text", "")
        webhook_url = params.get("webhook_url") or self.webhook_url
        blocks = params.get("blocks")
        attachments = params.get("attachments")
        channel = params.get("channel")
        username = params.get("username")
        icon_emoji = params.get("icon_emoji")
        unfurl_links = params.get("unfurl_links", False)
        unfurl_media = params.get("unfurl_media", True)
        idempotency_key = params.get("idempotency_key")

        started_at = datetime.now(timezone.utc)
        start_time = time.time()

        logger.info(
            "slack_send_execution_start",
            extra={
                "skill": "slack_send",
                "channel": channel,
                "has_blocks": blocks is not None,
                "text_preview": text[:50] if text else "",
            },
        )

        # Check stub mode
        if not self.allow_external:
            duration = time.time() - start_time
            logger.info("slack_send_stubbed", extra={"skill": "slack_send", "reason": "external_calls_disabled"})
            return {
                "skill": "slack_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "stubbed",
                    "webhook_response": "ok (stubbed)",
                    "channel": channel,
                    "from_cache": False,
                },
                "duration": round(duration, 3),
                "side_effects": {"slack_stubbed": True, "would_post_to": channel},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Check webhook URL
        if not webhook_url:
            duration = time.time() - start_time
            logger.error("slack_send_failed", extra={"skill": "slack_send", "error": "No webhook URL configured"})
            return {
                "skill": "slack_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "error",
                    "error": "configuration_error",
                    "message": "SLACK_WEBHOOK_URL not configured",
                    "webhook_response": "",
                    "channel": channel,
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        # Check idempotency
        if idempotency_key and idempotency_key in self._idempotency_cache:
            logger.info("slack_send_idempotency_hit", extra={"idempotency_key": idempotency_key})
            cached = self._idempotency_cache[idempotency_key]
            return {**cached, "result": {**cached.get("result", {}), "from_cache": True}}

        # Build payload
        payload: Dict[str, Any] = {}

        if text:
            payload["text"] = text

        if blocks:
            payload["blocks"] = blocks

        if attachments:
            payload["attachments"] = attachments

        if channel:
            payload["channel"] = channel

        if username:
            payload["username"] = username

        if icon_emoji:
            payload["icon_emoji"] = icon_emoji

        payload["unfurl_links"] = unfurl_links
        payload["unfurl_media"] = unfurl_media

        # Send to Slack
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                duration = time.time() - start_time
                completed_at = datetime.now(timezone.utc)

                if response.status_code == 200:
                    webhook_response = response.text.strip()

                    logger.info(
                        "slack_send_execution_end",
                        extra={
                            "skill": "slack_send",
                            "status": "ok",
                            "channel": channel,
                            "duration": round(duration, 3),
                        },
                    )

                    result = {
                        "skill": "slack_send",
                        "skill_version": self.VERSION,
                        "result": {
                            "status": "ok",
                            "webhook_response": webhook_response,
                            "channel": channel,
                            "from_cache": False,
                        },
                        "duration": round(duration, 3),
                        "side_effects": {
                            "slack_message_sent": True,
                            "channel": channel,
                        },
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                    }

                    # Cache for idempotency
                    if idempotency_key:
                        self._idempotency_cache[idempotency_key] = result

                    return result

                else:
                    error_body = response.text[:500]
                    logger.warning(
                        "slack_send_failed",
                        extra={
                            "skill": "slack_send",
                            "http_status": response.status_code,
                            "error": error_body,
                        },
                    )

                    return {
                        "skill": "slack_send",
                        "skill_version": self.VERSION,
                        "result": {
                            "status": "error",
                            "error": "webhook_error",
                            "message": f"Slack webhook error ({response.status_code}): {error_body}",
                            "webhook_response": error_body,
                            "channel": channel,
                        },
                        "duration": round(duration, 3),
                        "side_effects": {},
                        "started_at": started_at.isoformat(),
                        "completed_at": completed_at.isoformat(),
                    }

        except httpx.TimeoutException:
            duration = time.time() - start_time
            logger.warning("slack_send_timeout", extra={"skill": "slack_send", "timeout": self.timeout})
            return {
                "skill": "slack_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "timeout",
                    "error": "timeout",
                    "message": f"Request timed out after {self.timeout}s",
                    "webhook_response": "",
                    "channel": channel,
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

        except httpx.RequestError as e:
            duration = time.time() - start_time
            logger.error("slack_send_failed", extra={"skill": "slack_send", "error": str(e)[:200]})
            return {
                "skill": "slack_send",
                "skill_version": self.VERSION,
                "result": {
                    "status": "error",
                    "error": "network_error",
                    "message": f"Network error: {str(e)[:200]}",
                    "webhook_response": "",
                    "channel": channel,
                },
                "duration": round(duration, 3),
                "side_effects": {},
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

    @classmethod
    def get_input_schema(cls) -> Type[BaseModel]:
        return SlackSendInput

    @classmethod
    def get_output_schema(cls) -> Type[BaseModel]:
        return SlackSendOutput
