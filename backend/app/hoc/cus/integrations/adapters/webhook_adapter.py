# capability_id: CAP-018
# Layer: L2 — Adapter
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Webhook notification adapter with retry logic
# Callers: NotificationService, AlertManager
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-153 (Webhook Retry Logic)

"""
Webhook Notification Adapter with Retry Logic (GAP-153)

Provides webhook notifications with robust retry:
- Exponential backoff
- Configurable retry policies
- Circuit breaker pattern
- Dead letter queue support
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import uuid

from .base import (
    NotificationAdapter,
    NotificationMessage,
    NotificationResult,
    NotificationStatus,
    RetryConfig,
)

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 60.0
    half_open_max_calls: int = 3


@dataclass
class CircuitBreaker:
    """Circuit breaker for webhook endpoint."""

    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    half_open_calls: int = 0

    def can_execute(self) -> bool:
        """Check if requests can be executed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.last_failure_time is None:
                return False

            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.config.timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True

            return False

        if self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls

        return False

    def record_success(self) -> None:
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN


@dataclass
class WebhookDeliveryAttempt:
    """Record of a webhook delivery attempt."""

    attempt_number: int
    timestamp: datetime
    status_code: Optional[int] = None
    error: Optional[str] = None
    response_time_ms: Optional[int] = None
    success: bool = False


@dataclass
class WebhookDelivery:
    """Full record of webhook delivery with all attempts."""

    message_id: str
    webhook_url: str
    payload: Dict[str, Any]
    attempts: List[WebhookDeliveryAttempt] = field(default_factory=list)
    final_status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_id": self.message_id,
            "webhook_url": self.webhook_url,
            "payload": self.payload,
            "attempts": [
                {
                    "attempt_number": a.attempt_number,
                    "timestamp": a.timestamp.isoformat(),
                    "status_code": a.status_code,
                    "error": a.error,
                    "response_time_ms": a.response_time_ms,
                    "success": a.success,
                }
                for a in self.attempts
            ],
            "final_status": self.final_status.value,
            "created_at": self.created_at.isoformat(),
        }


class WebhookAdapter(NotificationAdapter):
    """
    Webhook notification adapter with retry logic.

    Features:
    - Exponential backoff with jitter
    - Circuit breaker per endpoint
    - HMAC signature verification
    - Dead letter queue callback
    """

    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        signing_secret: Optional[str] = None,
        default_timeout: int = 30,
        dead_letter_callback: Optional[Callable[[WebhookDelivery], None]] = None,
    ):
        self._retry_config = retry_config or RetryConfig()
        self._circuit_config = circuit_breaker_config or CircuitBreakerConfig()
        self._signing_secret = signing_secret or os.getenv("WEBHOOK_SIGNING_SECRET")
        self._default_timeout = default_timeout
        self._dead_letter_callback = dead_letter_callback

        self._http_client = None
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._deliveries: Dict[str, WebhookDelivery] = {}

    async def connect(self) -> bool:
        """Initialize HTTP client."""
        try:
            import httpx

            self._http_client = httpx.AsyncClient(
                timeout=self._default_timeout,
                follow_redirects=True,
            )

            logger.info("Webhook adapter initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize webhook adapter: {e}")
            return False

    async def disconnect(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
        self._http_client = None
        logger.info("Webhook adapter disconnected")

    def _get_circuit_breaker(self, url: str) -> CircuitBreaker:
        """Get or create circuit breaker for URL."""
        # Use host as circuit breaker key
        from urllib.parse import urlparse
        host = urlparse(url).netloc

        if host not in self._circuit_breakers:
            self._circuit_breakers[host] = CircuitBreaker(config=self._circuit_config)

        return self._circuit_breakers[host]

    def _sign_payload(self, payload: bytes, timestamp: str) -> str:
        """Generate HMAC signature for payload."""
        if not self._signing_secret:
            return ""

        message = f"{timestamp}.{payload.decode()}"
        signature = hmac.new(
            self._signing_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        return f"v1={signature}"

    async def send(
        self,
        message: NotificationMessage,
    ) -> NotificationResult:
        """Send a webhook notification with retry logic."""
        if not self._http_client:
            raise RuntimeError("Webhook adapter not initialized")

        message_id = str(uuid.uuid4())
        recipients_succeeded = []
        recipients_failed = []

        for recipient in message.recipients:
            webhook_url = recipient.address

            # Create delivery record
            payload = {
                "subject": message.subject,
                "body": message.body,
                "priority": message.priority.value,
                "metadata": message.metadata,
                "correlation_id": message.correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            delivery = WebhookDelivery(
                message_id=message_id,
                webhook_url=webhook_url,
                payload=payload,
            )

            # Attempt delivery with retries
            success = await self._deliver_with_retry(delivery)

            if success:
                recipients_succeeded.append(webhook_url)
            else:
                recipients_failed.append(webhook_url)

                # Call dead letter callback if configured
                if self._dead_letter_callback:
                    try:
                        self._dead_letter_callback(delivery)
                    except Exception as e:
                        logger.error(f"Dead letter callback failed: {e}")

            self._deliveries[message_id] = delivery

        status = NotificationStatus.SENT if recipients_succeeded else NotificationStatus.FAILED

        result = NotificationResult(
            message_id=message_id,
            status=status,
            recipients_succeeded=recipients_succeeded,
            recipients_failed=recipients_failed,
            error=None if recipients_succeeded else "All deliveries failed",
        )

        return result

    async def _deliver_with_retry(
        self,
        delivery: WebhookDelivery,
    ) -> bool:
        """Attempt delivery with exponential backoff retry."""
        circuit = self._get_circuit_breaker(delivery.webhook_url)

        for attempt in range(self._retry_config.max_retries + 1):
            # Check circuit breaker
            if not circuit.can_execute():
                logger.warning(f"Circuit open for {delivery.webhook_url}, skipping")
                delivery.final_status = NotificationStatus.FAILED
                return False

            # Calculate delay (skip for first attempt)
            if attempt > 0:
                delay = self._retry_config.get_delay(attempt - 1)
                logger.debug(f"Retry {attempt} for {delivery.webhook_url} after {delay:.2f}s")
                await asyncio.sleep(delay)

            # Attempt delivery
            attempt_record = await self._attempt_delivery(delivery, attempt + 1)
            delivery.attempts.append(attempt_record)

            if attempt_record.success:
                circuit.record_success()
                delivery.final_status = NotificationStatus.DELIVERED
                return True
            else:
                circuit.record_failure()

        delivery.final_status = NotificationStatus.FAILED
        return False

    async def _attempt_delivery(
        self,
        delivery: WebhookDelivery,
        attempt_number: int,
    ) -> WebhookDeliveryAttempt:
        """Make a single delivery attempt."""
        start_time = time.time()
        timestamp = str(int(start_time))

        try:
            payload_bytes = json.dumps(delivery.payload).encode()
            signature = self._sign_payload(payload_bytes, timestamp)

            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Timestamp": timestamp,
                "X-Webhook-Delivery-ID": delivery.message_id,
            }

            if signature:
                headers["X-Webhook-Signature"] = signature

            response = await self._http_client.post(
                delivery.webhook_url,
                content=payload_bytes,
                headers=headers,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)

            if 200 <= response.status_code < 300:
                return WebhookDeliveryAttempt(
                    attempt_number=attempt_number,
                    timestamp=datetime.now(timezone.utc),
                    status_code=response.status_code,
                    response_time_ms=elapsed_ms,
                    success=True,
                )
            else:
                return WebhookDeliveryAttempt(
                    attempt_number=attempt_number,
                    timestamp=datetime.now(timezone.utc),
                    status_code=response.status_code,
                    error=f"HTTP {response.status_code}",
                    response_time_ms=elapsed_ms,
                    success=False,
                )

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return WebhookDeliveryAttempt(
                attempt_number=attempt_number,
                timestamp=datetime.now(timezone.utc),
                error=str(e),
                response_time_ms=elapsed_ms,
                success=False,
            )

    async def send_batch(
        self,
        messages: List[NotificationMessage],
        max_concurrent: int = 10,
    ) -> List[NotificationResult]:
        """Send multiple webhook notifications concurrently."""
        if not self._http_client:
            raise RuntimeError("Webhook adapter not initialized")

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
        """Get the status of a webhook delivery."""
        delivery = self._deliveries.get(message_id)
        if not delivery:
            return None

        return NotificationResult(
            message_id=delivery.message_id,
            status=delivery.final_status,
            recipients_succeeded=[delivery.webhook_url] if delivery.final_status == NotificationStatus.DELIVERED else [],
            recipients_failed=[delivery.webhook_url] if delivery.final_status == NotificationStatus.FAILED else [],
            metadata={"attempts": len(delivery.attempts)},
        )

    def get_delivery_details(
        self,
        message_id: str,
    ) -> Optional[WebhookDelivery]:
        """Get full delivery details including all attempts."""
        return self._deliveries.get(message_id)

    def get_circuit_breaker_status(
        self,
        url: str,
    ) -> Optional[Dict[str, Any]]:
        """Get circuit breaker status for a URL."""
        from urllib.parse import urlparse
        host = urlparse(url).netloc

        circuit = self._circuit_breakers.get(host)
        if not circuit:
            return None

        return {
            "host": host,
            "state": circuit.state.value,
            "failure_count": circuit.failure_count,
            "success_count": circuit.success_count,
            "last_failure_time": circuit.last_failure_time,
        }
