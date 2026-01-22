# Layer: L3 — Boundary Adapter (Console → Platform)
# Product: AI Console
# Temporal:
#   Trigger: worker
#   Execution: async
# Role: Emit alerts for near-threshold and breach events
# Callers: policy/prevention_engine.py
# Allowed Imports: L4, L5, L6
# Forbidden Imports: L1, L2
# Reference: POLICY_CONTROL_LEVER_IMPLEMENTATION_PLAN.md PCL-007

"""
Alert Emitter Service

Emits alerts for threshold events via configured channels:
- UI notifications
- Webhooks
- Email (future)
- Slack (future)

Alert flow:
1. ThresholdSignal created
2. AlertEmitter checks AlertConfig
3. If enabled and not throttled, send via configured channels
4. Record alert sent status
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlmodel import Session, select

from app.db import engine
from app.models.alert_config import AlertChannel, AlertConfig
from app.models.threshold_signal import SignalType, ThresholdSignal

logger = logging.getLogger("nova.services.alert_emitter")


class AlertEmitter:
    """
    Emits alerts for threshold events.

    Handles alert throttling, channel routing, and delivery tracking.
    """

    def __init__(
        self,
        session: Optional[Session] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """
        Initialize alert emitter.

        Args:
            session: Optional SQLModel session (for testing)
            http_client: Optional HTTP client (for testing)
        """
        self._session = session
        self._http_client = http_client

    async def emit_near_threshold(
        self,
        signal: ThresholdSignal,
        alert_config: AlertConfig,
        run_alert_count: int = 0,
    ) -> bool:
        """
        Emit near-threshold alert via configured channels.

        Args:
            signal: ThresholdSignal record
            alert_config: AlertConfig for the policy
            run_alert_count: Number of alerts already sent for this run

        Returns:
            True if alert was sent, False if throttled or disabled
        """
        # Check if alerting is enabled
        if not alert_config.near_threshold_enabled:
            logger.debug(
                "near_threshold_alert_disabled",
                extra={"policy_id": signal.policy_id},
            )
            return False

        # Check throttling
        if not alert_config.can_send_alert(run_alert_count):
            logger.debug(
                "near_threshold_alert_throttled",
                extra={
                    "policy_id": signal.policy_id,
                    "run_alert_count": run_alert_count,
                },
            )
            return False

        # Send via configured channels
        channels_sent: list[str] = []
        for channel in alert_config.enabled_channels:
            try:
                sent = await self._send_via_channel(
                    channel,
                    signal,
                    alert_config,
                    is_breach=False,
                )
                if sent:
                    channels_sent.append(channel.value)
            except Exception as e:
                logger.error(
                    "alert_channel_error",
                    extra={
                        "channel": channel.value,
                        "error": str(e),
                        "signal_id": signal.signal_id,
                    },
                )

        # Record alert sent
        if channels_sent:
            signal.mark_alert_sent(channels_sent)
            alert_config.record_alert_sent()
            await self._persist_signal(signal)
            await self._persist_config(alert_config)

            logger.info(
                "near_threshold_alert_sent",
                extra={
                    "signal_id": signal.signal_id,
                    "channels": channels_sent,
                    "metric": signal.metric,
                    "percentage": signal.percentage,
                },
            )
            return True

        return False

    async def emit_breach(
        self,
        signal: ThresholdSignal,
        alert_config: AlertConfig,
        action_taken: str,
    ) -> bool:
        """
        Emit breach alert with enforcement action.

        Breach alerts are always sent (not throttled) because they
        indicate enforcement action was taken.

        Args:
            signal: ThresholdSignal record (BREACH type)
            alert_config: AlertConfig for the policy
            action_taken: Enforcement action taken (pause, stop, kill)

        Returns:
            True if alert was sent
        """
        # Check if breach alerting is enabled
        if not alert_config.breach_alert_enabled:
            logger.debug(
                "breach_alert_disabled",
                extra={"policy_id": signal.policy_id},
            )
            return False

        # Breach alerts bypass throttling
        channels_sent: list[str] = []
        for channel in alert_config.enabled_channels:
            try:
                sent = await self._send_via_channel(
                    channel,
                    signal,
                    alert_config,
                    is_breach=True,
                    action_taken=action_taken,
                )
                if sent:
                    channels_sent.append(channel.value)
            except Exception as e:
                logger.error(
                    "breach_alert_channel_error",
                    extra={
                        "channel": channel.value,
                        "error": str(e),
                        "signal_id": signal.signal_id,
                    },
                )

        # Record alert sent
        if channels_sent:
            signal.mark_alert_sent(channels_sent)
            await self._persist_signal(signal)

            logger.info(
                "breach_alert_sent",
                extra={
                    "signal_id": signal.signal_id,
                    "channels": channels_sent,
                    "metric": signal.metric,
                    "action_taken": action_taken,
                },
            )
            return True

        return False

    async def _send_via_channel(
        self,
        channel: AlertChannel,
        signal: ThresholdSignal,
        config: AlertConfig,
        is_breach: bool,
        action_taken: Optional[str] = None,
    ) -> bool:
        """
        Send alert via a specific channel.

        Returns:
            True if sent successfully
        """
        if channel == AlertChannel.UI:
            return await self._send_ui_notification(signal, is_breach, action_taken)
        elif channel == AlertChannel.WEBHOOK:
            return await self._send_webhook(signal, config, is_breach, action_taken)
        elif channel == AlertChannel.SLACK:
            return await self._send_slack(signal, config, is_breach, action_taken)
        elif channel == AlertChannel.EMAIL:
            return await self._send_email(signal, config, is_breach, action_taken)
        return False

    async def _send_ui_notification(
        self,
        signal: ThresholdSignal,
        is_breach: bool,
        action_taken: Optional[str],
    ) -> bool:
        """
        Send UI notification.

        In production, this would push to a real-time notification service.
        For now, we just log it and return True.
        """
        notification_type = "breach" if is_breach else "near_threshold"
        logger.info(
            "ui_notification_created",
            extra={
                "notification_type": notification_type,
                "signal_id": signal.signal_id,
                "run_id": signal.run_id,
                "metric": signal.metric,
                "percentage": signal.percentage,
                "action_taken": action_taken,
            },
        )
        # TODO: Integrate with real-time notification service
        return True

    async def _send_webhook(
        self,
        signal: ThresholdSignal,
        config: AlertConfig,
        is_breach: bool,
        action_taken: Optional[str],
    ) -> bool:
        """Send webhook notification."""
        if not config.webhook_url:
            return False

        payload = {
            "event_type": "threshold_breach" if is_breach else "threshold_near",
            "signal_id": signal.signal_id,
            "run_id": signal.run_id,
            "policy_id": signal.policy_id,
            "tenant_id": signal.tenant_id,
            "metric": signal.metric,
            "current_value": signal.current_value,
            "threshold_value": signal.threshold_value,
            "percentage": signal.percentage,
            "step_index": signal.step_index,
            "action_taken": action_taken,
            "timestamp": signal.timestamp.isoformat(),
        }

        try:
            client = self._http_client or httpx.AsyncClient(timeout=10.0)
            headers = {"Content-Type": "application/json"}
            if config.webhook_secret:
                headers["X-Webhook-Secret"] = config.webhook_secret

            response = await client.post(
                config.webhook_url,
                json=payload,
                headers=headers,
            )
            return response.status_code < 400
        except Exception as e:
            logger.error(
                "webhook_send_error",
                extra={"error": str(e), "url": config.webhook_url},
            )
            return False

    async def _send_slack(
        self,
        signal: ThresholdSignal,
        config: AlertConfig,
        is_breach: bool,
        action_taken: Optional[str],
    ) -> bool:
        """Send Slack notification."""
        if not config.slack_webhook_url:
            return False

        emoji = "🚨" if is_breach else "⚠️"
        status = "BREACH" if is_breach else "NEAR THRESHOLD"
        color = "#ff0000" if is_breach else "#ffcc00"

        message = {
            "channel": config.slack_channel,
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} Policy {status}: {signal.metric}",
                    "fields": [
                        {"title": "Run ID", "value": signal.run_id, "short": True},
                        {"title": "Policy ID", "value": signal.policy_id, "short": True},
                        {"title": "Current Value", "value": str(signal.current_value), "short": True},
                        {"title": "Threshold", "value": str(signal.threshold_value), "short": True},
                        {"title": "Percentage", "value": f"{signal.percentage:.1f}%", "short": True},
                    ],
                    "ts": int(signal.timestamp.timestamp()),
                }
            ],
        }

        if action_taken:
            message["attachments"][0]["fields"].append(
                {"title": "Action Taken", "value": action_taken.upper(), "short": True}
            )

        try:
            client = self._http_client or httpx.AsyncClient(timeout=10.0)
            response = await client.post(
                config.slack_webhook_url,
                json=message,
            )
            return response.status_code < 400
        except Exception as e:
            logger.error(
                "slack_send_error",
                extra={"error": str(e)},
            )
            return False

    async def _send_email(
        self,
        signal: ThresholdSignal,
        config: AlertConfig,
        is_breach: bool,
        action_taken: Optional[str],
    ) -> bool:
        """Send email notification."""
        if not config.email_recipients:
            return False

        # TODO: Integrate with email service
        logger.info(
            "email_notification_queued",
            extra={
                "recipients": config.email_recipients,
                "signal_id": signal.signal_id,
            },
        )
        return True

    async def _persist_signal(self, signal: ThresholdSignal) -> None:
        """Persist signal changes to database."""
        if self._session:
            self._session.add(signal)
            self._session.commit()
        else:
            with Session(engine) as session:
                session.add(signal)
                session.commit()

    async def _persist_config(self, config: AlertConfig) -> None:
        """Persist config changes to database."""
        if self._session:
            self._session.add(config)
            self._session.commit()
        else:
            with Session(engine) as session:
                session.add(config)
                session.commit()


# Singleton instance
_alert_emitter: Optional[AlertEmitter] = None


def get_alert_emitter() -> AlertEmitter:
    """Get or create AlertEmitter singleton."""
    global _alert_emitter
    if _alert_emitter is None:
        _alert_emitter = AlertEmitter()
    return _alert_emitter
