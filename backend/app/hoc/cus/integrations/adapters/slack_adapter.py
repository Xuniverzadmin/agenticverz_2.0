# Layer: L2 — Adapter
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Slack notification adapter
# Callers: NotificationService, AlertManager
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-152 (Slack Notification Adapter)

"""
Slack Notification Adapter (GAP-152)

Provides Slack notifications:
- Channel and DM messaging
- Rich message formatting (blocks)
- File uploads
- Thread replies
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional
import uuid

from .base import (
    NotificationAdapter,
    NotificationMessage,
    NotificationPriority,
    NotificationResult,
    NotificationStatus,
)

logger = logging.getLogger(__name__)


class SlackAdapter(NotificationAdapter):
    """
    Slack notification adapter.

    Uses slack_sdk for async Slack API operations.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        default_channel: Optional[str] = None,
        app_name: Optional[str] = None,
    ):
        self._bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self._default_channel = default_channel or os.getenv("SLACK_DEFAULT_CHANNEL", "#general")
        self._app_name = app_name or os.getenv("SLACK_APP_NAME", "AOS")
        self._client = None
        self._sent_messages: Dict[str, NotificationResult] = {}

    async def connect(self) -> bool:
        """Connect to Slack API."""
        try:
            from slack_sdk.web.async_client import AsyncWebClient

            self._client = AsyncWebClient(token=self._bot_token)

            # Test connection
            response = await self._client.auth_test()
            if not response.get("ok"):
                raise RuntimeError(f"Slack auth failed: {response.get('error')}")

            logger.info(f"Connected to Slack as {response.get('user')}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Slack: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Slack API."""
        self._client = None
        logger.info("Disconnected from Slack")

    async def send(
        self,
        message: NotificationMessage,
    ) -> NotificationResult:
        """Send a Slack notification."""
        if not self._client:
            raise RuntimeError("Not connected to Slack")

        message_id = str(uuid.uuid4())
        recipients_succeeded = []
        recipients_failed = []
        slack_ts = None
        error = None

        try:
            # Build message blocks
            blocks = self._build_blocks(message)

            for recipient in message.recipients:
                channel = recipient.address or self._default_channel

                try:
                    response = await self._client.chat_postMessage(
                        channel=channel,
                        text=message.body,
                        blocks=blocks,
                        unfurl_links=False,
                        unfurl_media=False,
                    )

                    if response.get("ok"):
                        recipients_succeeded.append(channel)
                        slack_ts = response.get("ts")
                    else:
                        recipients_failed.append(channel)
                        error = response.get("error")

                except Exception as e:
                    recipients_failed.append(channel)
                    error = str(e)

            status = NotificationStatus.SENT if recipients_succeeded else NotificationStatus.FAILED

            result = NotificationResult(
                message_id=message_id,
                status=status,
                recipients_succeeded=recipients_succeeded,
                recipients_failed=recipients_failed,
                error=error,
                metadata={"slack_ts": slack_ts} if slack_ts else {},
            )

            self._sent_messages[message_id] = result
            logger.info(f"Sent Slack message {message_id} to {len(recipients_succeeded)} channels")
            return result

        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            result = NotificationResult(
                message_id=message_id,
                status=NotificationStatus.FAILED,
                recipients_failed=[r.address for r in message.recipients],
                error=str(e),
            )
            self._sent_messages[message_id] = result
            return result

    def _build_blocks(
        self,
        message: NotificationMessage,
    ) -> List[Dict[str, Any]]:
        """Build Slack blocks for rich formatting."""
        blocks = []

        # Header block with subject
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": message.subject[:150],
                "emoji": True,
            },
        })

        # Priority indicator
        priority_emoji = self._get_priority_emoji(message.priority)
        if priority_emoji:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"{priority_emoji} *Priority:* {message.priority.value.upper()}",
                    }
                ],
            })

        # Divider
        blocks.append({"type": "divider"})

        # Body section
        body_text = message.body
        if len(body_text) > 3000:
            body_text = body_text[:2997] + "..."

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": body_text,
            },
        })

        # Metadata footer
        if message.correlation_id:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_Correlation ID: {message.correlation_id}_",
                    }
                ],
            })

        return blocks

    def _get_priority_emoji(self, priority: NotificationPriority) -> str:
        """Get emoji for priority level."""
        return {
            NotificationPriority.LOW: "",
            NotificationPriority.NORMAL: "",
            NotificationPriority.HIGH: ":warning:",
            NotificationPriority.URGENT: ":rotating_light:",
        }.get(priority, "")

    async def send_batch(
        self,
        messages: List[NotificationMessage],
        max_concurrent: int = 10,
    ) -> List[NotificationResult]:
        """Send multiple Slack messages concurrently."""
        if not self._client:
            raise RuntimeError("Not connected to Slack")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_with_semaphore(msg: NotificationMessage) -> NotificationResult:
            async with semaphore:
                return await self.send(msg)

        tasks = [send_with_semaphore(msg) for msg in messages]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    NotificationResult(
                        message_id=str(uuid.uuid4()),
                        status=NotificationStatus.FAILED,
                        recipients_failed=[r.address for r in messages[i].recipients],
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    async def get_status(
        self,
        message_id: str,
    ) -> Optional[NotificationResult]:
        """Get the status of a sent Slack message."""
        return self._sent_messages.get(message_id)

    async def send_thread_reply(
        self,
        channel: str,
        thread_ts: str,
        text: str,
    ) -> NotificationResult:
        """Send a reply to a thread."""
        if not self._client:
            raise RuntimeError("Not connected to Slack")

        message_id = str(uuid.uuid4())

        try:
            response = await self._client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=text,
            )

            if response.get("ok"):
                result = NotificationResult(
                    message_id=message_id,
                    status=NotificationStatus.SENT,
                    recipients_succeeded=[channel],
                    metadata={"slack_ts": response.get("ts")},
                )
            else:
                result = NotificationResult(
                    message_id=message_id,
                    status=NotificationStatus.FAILED,
                    recipients_failed=[channel],
                    error=response.get("error"),
                )

            self._sent_messages[message_id] = result
            return result

        except Exception as e:
            result = NotificationResult(
                message_id=message_id,
                status=NotificationStatus.FAILED,
                recipients_failed=[channel],
                error=str(e),
            )
            self._sent_messages[message_id] = result
            return result
