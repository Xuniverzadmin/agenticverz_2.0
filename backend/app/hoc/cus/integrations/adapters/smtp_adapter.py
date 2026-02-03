# Layer: L2 — Adapter
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: SMTP email notification adapter
# Callers: NotificationService, AlertManager
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-151 (SMTP Notification Adapter)

"""
SMTP Notification Adapter (GAP-151)

Provides email notifications via SMTP:
- Async email sending via aiosmtplib
- HTML and plain text support
- Attachment handling
- Connection pooling
"""

import asyncio
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional
import uuid

from .base import (
    NotificationAdapter,
    NotificationMessage,
    NotificationResult,
    NotificationStatus,
)

logger = logging.getLogger(__name__)


class SMTPAdapter(NotificationAdapter):
    """
    SMTP notification adapter for email.

    Uses aiosmtplib for async email operations.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
        from_address: Optional[str] = None,
        from_name: Optional[str] = None,
        timeout: int = 30,
    ):
        self._host = host or os.getenv("SMTP_HOST", "localhost")
        self._port = port or int(os.getenv("SMTP_PORT", "587"))
        self._username = username or os.getenv("SMTP_USERNAME")
        self._password = password or os.getenv("SMTP_PASSWORD")
        self._use_tls = use_tls
        self._from_address = from_address or os.getenv("SMTP_FROM_ADDRESS", "noreply@example.com")
        self._from_name = from_name or os.getenv("SMTP_FROM_NAME", "AOS Notifications")
        self._timeout = timeout
        self._connected = False
        self._sent_messages: Dict[str, NotificationResult] = {}

    async def connect(self) -> bool:
        """Connect to SMTP server (test connection)."""
        try:
            import aiosmtplib

            # Test connection
            smtp = aiosmtplib.SMTP(
                hostname=self._host,
                port=self._port,
                timeout=self._timeout,
                use_tls=self._use_tls,
            )

            await smtp.connect()

            if self._username and self._password:
                await smtp.login(self._username, self._password)

            await smtp.quit()

            self._connected = True
            logger.info(f"Connected to SMTP server {self._host}:{self._port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from SMTP server."""
        self._connected = False
        logger.info("Disconnected from SMTP server")

    async def send(
        self,
        message: NotificationMessage,
    ) -> NotificationResult:
        """Send an email notification."""
        message_id = str(uuid.uuid4())

        try:
            import aiosmtplib

            # Build email
            email = self._build_email(message, message_id)

            # Get recipient addresses
            recipient_addresses = [r.address for r in message.recipients]

            # Create SMTP connection
            smtp = aiosmtplib.SMTP(
                hostname=self._host,
                port=self._port,
                timeout=self._timeout,
                use_tls=self._use_tls,
            )

            await smtp.connect()

            if self._username and self._password:
                await smtp.login(self._username, self._password)

            # Send email
            errors, _ = await smtp.sendmail(
                self._from_address,
                recipient_addresses,
                email.as_string(),
            )

            await smtp.quit()

            # Process results
            recipients_succeeded = [
                addr for addr in recipient_addresses if addr not in errors
            ]
            recipients_failed = list(errors.keys()) if errors else []

            status = NotificationStatus.SENT if not recipients_failed else NotificationStatus.FAILED
            error = str(errors) if errors else None

            result = NotificationResult(
                message_id=message_id,
                status=status,
                recipients_succeeded=recipients_succeeded,
                recipients_failed=recipients_failed,
                error=error,
                metadata={"smtp_host": self._host},
            )

            self._sent_messages[message_id] = result
            logger.info(f"Sent email {message_id} to {len(recipients_succeeded)} recipients")
            return result

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            result = NotificationResult(
                message_id=message_id,
                status=NotificationStatus.FAILED,
                recipients_failed=[r.address for r in message.recipients],
                error=str(e),
            )
            self._sent_messages[message_id] = result
            return result

    def _build_email(
        self,
        message: NotificationMessage,
        message_id: str,
    ) -> MIMEMultipart:
        """Build a MIME email message."""
        email = MIMEMultipart("alternative")

        # Headers
        email["Subject"] = message.subject
        email["From"] = f"{self._from_name} <{self._from_address}>"
        email["To"] = ", ".join(
            f"{r.name} <{r.address}>" if r.name else r.address
            for r in message.recipients
        )
        email["Message-ID"] = f"<{message_id}@{self._host}>"

        if message.correlation_id:
            email["X-Correlation-ID"] = message.correlation_id

        # Priority headers
        if message.priority.value == "urgent":
            email["X-Priority"] = "1"
            email["Importance"] = "high"
        elif message.priority.value == "high":
            email["X-Priority"] = "2"
            email["Importance"] = "high"

        # Body
        email.attach(MIMEText(message.body, "plain", "utf-8"))

        if message.html_body:
            email.attach(MIMEText(message.html_body, "html", "utf-8"))

        # Attachments
        for attachment in message.attachments:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.get("content", b""))
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={attachment.get('filename', 'attachment')}",
            )
            email.attach(part)

        return email

    async def send_batch(
        self,
        messages: List[NotificationMessage],
        max_concurrent: int = 10,
    ) -> List[NotificationResult]:
        """Send multiple emails concurrently."""
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
        """Get the status of a sent email."""
        return self._sent_messages.get(message_id)
