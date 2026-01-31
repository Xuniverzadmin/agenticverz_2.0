# Layer: L5 — Domain Engine
# NOTE: Renamed email_verification.py → email_verification_engine.py (2026-01-31) per BANNED_NAMING rule
# AUDIENCE: CUSTOMER
# Product: ai-console
# Location: hoc/cus/account/L5_engines/email_verification.py
# Temporal:
#   Trigger: api
#   Execution: async (Redis operations)
# Lifecycle:
#   Emits: OTP_SENT, OTP_VERIFIED
#   Subscribes: none
# Data Access:
#   Reads: Redis (OTP state)
#   Writes: Redis (OTP state)
# Role: Email OTP verification engine for customer onboarding
# Callers: onboarding.py (auth flow)
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, PIN-240, PHASE3_DIRECTORY_RESTRUCTURE_PLAN.md
#
# L4 is reserved for general/L4_runtime/ only per HOC Layer Topology.
#
# NOTE: Redis-only state (not PostgreSQL). M24 onboarding.

"""
Email Verification Service

Provides OTP-based email verification for customer onboarding.

Configuration (environment variables):
    RESEND_API_KEY: Resend.com API key for sending emails
    EMAIL_FROM: Sender email address
    EMAIL_VERIFICATION_TTL: OTP validity in seconds (default: 600 = 10 min)
"""

import hashlib
import logging
import os
import secrets
from dataclasses import dataclass
from typing import Optional

import httpx
from redis import Redis

logger = logging.getLogger("nova.services.email_verification")

# Configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "Agenticverz <noreply@agenticverz.com>")
EMAIL_VERIFICATION_TTL = int(os.getenv("EMAIL_VERIFICATION_TTL", "600"))  # 10 minutes
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# OTP settings
OTP_LENGTH = 6
MAX_OTP_ATTEMPTS = 3
OTP_COOLDOWN_SECONDS = 60  # Minimum time between OTP requests


@dataclass
class VerificationResult:
    """Result of OTP verification."""

    success: bool
    message: str
    email: Optional[str] = None
    attempts_remaining: Optional[int] = None


class EmailVerificationError(Exception):
    """Email verification error."""

    def __init__(self, message: str, error_code: str = "verification_error"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class EmailVerificationService:
    """
    Handles OTP generation, sending, and verification for email signup.

    Uses Redis for OTP storage with TTL.
    """

    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis = redis_client
        if not self.redis:
            import redis

            self.redis = redis.from_url(REDIS_URL, decode_responses=True)

    def _otp_key(self, email: str) -> str:
        """Generate Redis key for OTP storage."""
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:16]
        return f"email_otp:{email_hash}"

    def _attempts_key(self, email: str) -> str:
        """Generate Redis key for attempt tracking."""
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:16]
        return f"email_otp_attempts:{email_hash}"

    def _cooldown_key(self, email: str) -> str:
        """Generate Redis key for cooldown tracking."""
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:16]
        return f"email_otp_cooldown:{email_hash}"

    def _generate_otp(self) -> str:
        """Generate a cryptographically secure OTP."""
        return "".join(secrets.choice("0123456789") for _ in range(OTP_LENGTH))

    async def send_otp(self, email: str, name: Optional[str] = None) -> dict:
        """
        Generate and send OTP to email address.

        Args:
            email: Email address to verify
            name: Optional user name for personalization

        Returns:
            Dict with status and message

        Raises:
            EmailVerificationError: If sending fails
        """
        email = email.lower().strip()

        # Check cooldown
        cooldown_key = self._cooldown_key(email)
        if self.redis.exists(cooldown_key):
            ttl = self.redis.ttl(cooldown_key)
            raise EmailVerificationError(f"Please wait {ttl} seconds before requesting another code", "cooldown_active")

        # Generate OTP
        otp = self._generate_otp()

        # Store in Redis with TTL
        otp_key = self._otp_key(email)
        self.redis.setex(otp_key, EMAIL_VERIFICATION_TTL, f"{email}:{otp}")

        # Reset attempts
        attempts_key = self._attempts_key(email)
        self.redis.delete(attempts_key)

        # Set cooldown
        self.redis.setex(cooldown_key, OTP_COOLDOWN_SECONDS, "1")

        # Send email
        await self._send_otp_email(email, otp, name)

        logger.info(f"OTP sent to {email[:3]}***@***")

        return {
            "success": True,
            "message": "Verification code sent",
            "expires_in": EMAIL_VERIFICATION_TTL,
        }

    async def _send_otp_email(self, email: str, otp: str, name: Optional[str] = None):
        """Send OTP email via Resend."""
        if not RESEND_API_KEY:
            logger.warning(f"RESEND_API_KEY not configured, OTP: {otp}")
            return

        greeting = f"Hi {name}," if name else "Hi,"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 500px; margin: 0 auto; padding: 40px 20px; }}
                .code {{
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    text-align: center;
                    padding: 20px;
                    background: #f1f5f9;
                    border-radius: 8px;
                    margin: 30px 0;
                }}
                .footer {{ color: #64748b; font-size: 14px; margin-top: 40px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <p>{greeting}</p>
                <p>Your verification code for Agenticverz is:</p>
                <div class="code">{otp}</div>
                <p>This code expires in {EMAIL_VERIFICATION_TTL // 60} minutes.</p>
                <p>If you didn't request this code, you can safely ignore this email.</p>
                <div class="footer">
                    <p>— The Agenticverz Team</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
{greeting}

Your verification code for Agenticverz is: {otp}

This code expires in {EMAIL_VERIFICATION_TTL // 60} minutes.

If you didn't request this code, you can safely ignore this email.

— The Agenticverz Team
        """

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": EMAIL_FROM,
                    "to": [email],
                    "subject": f"Your Agenticverz verification code: {otp}",
                    "html": html_content,
                    "text": text_content,
                },
            )

            if response.status_code not in (200, 201):
                logger.error(f"Failed to send email: {response.text}")
                raise EmailVerificationError("Failed to send verification email", "send_failed")

    def verify_otp(self, email: str, otp: str) -> VerificationResult:
        """
        Verify OTP code.

        Args:
            email: Email address
            otp: OTP code to verify

        Returns:
            VerificationResult with success status
        """
        email = email.lower().strip()
        otp_key = self._otp_key(email)
        attempts_key = self._attempts_key(email)

        # Check attempts
        attempts = int(self.redis.get(attempts_key) or 0)
        if attempts >= MAX_OTP_ATTEMPTS:
            # Delete OTP to force new request
            self.redis.delete(otp_key)
            return VerificationResult(
                success=False,
                message="Too many attempts. Please request a new code.",
                attempts_remaining=0,
            )

        # Get stored OTP
        stored = self.redis.get(otp_key)
        if not stored:
            return VerificationResult(
                success=False,
                message="Code expired or not found. Please request a new code.",
            )

        assert stored is not None
        stored_email, stored_otp = stored.split(":", 1)

        # Verify
        if stored_otp == otp and stored_email == email:
            # Success - delete OTP
            self.redis.delete(otp_key)
            self.redis.delete(attempts_key)
            return VerificationResult(
                success=True,
                message="Email verified successfully",
                email=email,
            )
        else:
            # Increment attempts
            self.redis.incr(attempts_key)
            self.redis.expire(attempts_key, EMAIL_VERIFICATION_TTL)
            remaining = MAX_OTP_ATTEMPTS - attempts - 1

            return VerificationResult(
                success=False,
                message="Invalid code",
                attempts_remaining=max(0, remaining),
            )


# Singleton instance
_service: Optional[EmailVerificationService] = None


def get_email_verification_service() -> EmailVerificationService:
    """Get email verification service singleton."""
    global _service
    if _service is None:
        _service = EmailVerificationService()
    return _service
