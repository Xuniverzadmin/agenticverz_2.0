# Layer: L3 — Boundary Adapter (Console → Platform)
# Product: AI Console
# Callers: guard.py (replay endpoint)
# Reference: PIN-240

"""M23 Certificate Service - Cryptographic Evidence of Deterministic Replay

Uses M4 HMAC infrastructure to create signed certificates that prove:
1. Policy decisions were evaluated at a specific time
2. Replay validation passed at a specific determinism level
3. No tampering occurred between original call and validation

Certificate Structure:
- Certificate ID (UUID)
- Original call metadata
- Replay validation result
- HMAC signature (using M4 infrastructure)
- Timestamp and expiry

Usage:
    from app.services.certificate import CertificateService, CertificateRequest

    service = CertificateService()
    cert = service.create_certificate(
        call_id="abc123",
        validation_result=replay_result,
        level=DeterminismLevel.LOGICAL,
    )

    # Verify later
    is_valid = service.verify_certificate(cert)
"""

import hashlib
import hmac
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from app.services.replay_determinism import (
    DeterminismLevel,
    ReplayResult,
)


class CertificateType(str, Enum):
    """Types of certificates that can be issued."""

    REPLAY_PROOF = "replay_proof"  # Proves deterministic replay
    POLICY_AUDIT = "policy_audit"  # Proves policy was evaluated
    INCIDENT_EXPORT = "incident_export"  # Proves incident details at export time


@dataclass
class CertificatePayload:
    """The signed payload of a certificate."""

    # Required fields (no defaults) - must come first
    certificate_id: str
    certificate_type: CertificateType
    call_id: str
    determinism_level: str  # strict, logical, semantic
    match_achieved: str  # exact, logical, semantic, mismatch
    validation_passed: bool

    # Optional fields with defaults
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None  # M23: End-user tracking

    # Policy decisions
    policy_count: int = 0
    policies_passed: int = 0
    policies_failed: int = 0

    # Model info
    model_id: str = "unknown"
    model_drift_detected: bool = False

    # Timing
    issued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    valid_until: str = field(default_factory=lambda: (datetime.now(timezone.utc) + timedelta(days=90)).isoformat())

    # Content hashes
    request_hash: Optional[str] = None
    response_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for signing."""
        return {
            "certificate_id": self.certificate_id,
            "certificate_type": self.certificate_type.value,
            "call_id": self.call_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "determinism_level": self.determinism_level,
            "match_achieved": self.match_achieved,
            "validation_passed": self.validation_passed,
            "policy_count": self.policy_count,
            "policies_passed": self.policies_passed,
            "policies_failed": self.policies_failed,
            "model_id": self.model_id,
            "model_drift_detected": self.model_drift_detected,
            "issued_at": self.issued_at,
            "valid_until": self.valid_until,
            "request_hash": self.request_hash,
            "response_hash": self.response_hash,
        }

    def canonical_json(self) -> str:
        """Canonical JSON for deterministic signing."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


@dataclass
class Certificate:
    """A signed certificate proving deterministic replay or policy evaluation."""

    payload: CertificatePayload
    signature: str  # HMAC-SHA256 signature
    version: str = "1.0"  # Certificate format version

    def to_dict(self) -> Dict[str, Any]:
        """Convert to full certificate dict."""
        return {
            "version": self.version,
            "payload": self.payload.to_dict(),
            "signature": self.signature,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Certificate":
        """Create certificate from dict."""
        payload_data = data["payload"]
        payload = CertificatePayload(
            certificate_id=payload_data["certificate_id"],
            certificate_type=CertificateType(payload_data["certificate_type"]),
            call_id=payload_data["call_id"],
            tenant_id=payload_data.get("tenant_id"),
            user_id=payload_data.get("user_id"),
            determinism_level=payload_data["determinism_level"],
            match_achieved=payload_data["match_achieved"],
            validation_passed=payload_data["validation_passed"],
            policy_count=payload_data.get("policy_count", 0),
            policies_passed=payload_data.get("policies_passed", 0),
            policies_failed=payload_data.get("policies_failed", 0),
            model_id=payload_data.get("model_id", "unknown"),
            model_drift_detected=payload_data.get("model_drift_detected", False),
            issued_at=payload_data["issued_at"],
            valid_until=payload_data["valid_until"],
            request_hash=payload_data.get("request_hash"),
            response_hash=payload_data.get("response_hash"),
        )
        return cls(
            payload=payload,
            signature=data["signature"],
            version=data.get("version", "1.0"),
        )


class CertificateService:
    """
    Service for creating and verifying cryptographic certificates.

    Uses M4 HMAC infrastructure (same secret as golden file signing).
    """

    def __init__(self, secret: Optional[str] = None):
        """
        Initialize certificate service.

        Args:
            secret: HMAC secret (default: GOLDEN_SECRET or CERTIFICATE_SECRET env)
        """
        self.secret = secret or os.getenv("CERTIFICATE_SECRET") or os.getenv("GOLDEN_SECRET", "")

        if not self.secret:
            # Generate a random secret for development (not for production)
            import secrets

            self.secret = secrets.token_hex(32)

    def _sign(self, content: str) -> str:
        """Sign content with HMAC-SHA256."""
        assert hmac is not None
        return hmac.new(self.secret.encode(), content.encode(), hashlib.sha256).hexdigest()

    def _verify_signature(self, content: str, signature: str) -> bool:
        """Verify HMAC signature."""
        expected = self._sign(content)
        return hmac.compare_digest(expected, signature)

    def create_replay_certificate(
        self,
        call_id: str,
        validation_result: ReplayResult,
        level: DeterminismLevel,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_hash: Optional[str] = None,
        response_hash: Optional[str] = None,
    ) -> Certificate:
        """
        Create a certificate proving deterministic replay.

        Args:
            call_id: Original call ID
            validation_result: Result from ReplayValidator
            level: Determinism level that was required
            tenant_id: Tenant ID (optional)
            user_id: End-user ID from OpenAI `user` field (optional)
            request_hash: Hash of original request (optional)
            response_hash: Hash of original response (optional)

        Returns:
            Signed certificate
        """
        # Count policy decisions
        policy_count = len(validation_result.original_policies)
        policies_passed = sum(1 for p in validation_result.original_policies if p.passed)
        policies_failed = policy_count - policies_passed

        # Build payload
        payload = CertificatePayload(
            certificate_id=str(uuid.uuid4()),
            certificate_type=CertificateType.REPLAY_PROOF,
            call_id=call_id,
            tenant_id=tenant_id,
            user_id=user_id,
            determinism_level=level.value,
            match_achieved=validation_result.match_level.value,
            validation_passed=validation_result.passed,
            policy_count=policy_count,
            policies_passed=policies_passed,
            policies_failed=policies_failed,
            model_id=validation_result.original_model.model_id if validation_result.original_model else "unknown",
            model_drift_detected=validation_result.model_drift_detected,
            request_hash=request_hash,
            response_hash=response_hash,
        )

        # Sign the payload
        signature = self._sign(payload.canonical_json())

        return Certificate(
            payload=payload,
            signature=signature,
        )

    def create_policy_audit_certificate(
        self,
        incident_id: str,
        policy_decisions: List[Dict[str, Any]],
        tenant_id: Optional[str] = None,
    ) -> Certificate:
        """
        Create a certificate proving policy evaluation at a point in time.

        Args:
            incident_id: Incident ID
            policy_decisions: List of policy decision dicts
            tenant_id: Tenant ID (optional)

        Returns:
            Signed certificate
        """
        policy_count = len(policy_decisions)
        policies_passed = sum(1 for p in policy_decisions if p.get("passed", True))
        policies_failed = policy_count - policies_passed

        payload = CertificatePayload(
            certificate_id=str(uuid.uuid4()),
            certificate_type=CertificateType.POLICY_AUDIT,
            call_id=incident_id,
            tenant_id=tenant_id,
            determinism_level="audit",
            match_achieved="n/a",
            validation_passed=policies_failed == 0,
            policy_count=policy_count,
            policies_passed=policies_passed,
            policies_failed=policies_failed,
        )

        signature = self._sign(payload.canonical_json())

        return Certificate(
            payload=payload,
            signature=signature,
        )

    def verify_certificate(self, certificate: Certificate) -> Dict[str, Any]:
        """
        Verify a certificate's signature and validity.

        Args:
            certificate: Certificate to verify

        Returns:
            Dict with verification result and details
        """
        # Verify signature
        signature_valid = self._verify_signature(certificate.payload.canonical_json(), certificate.signature)

        # Check expiry
        now = datetime.now(timezone.utc)
        valid_until = datetime.fromisoformat(certificate.payload.valid_until.replace("Z", "+00:00"))
        is_expired = now > valid_until

        return {
            "valid": signature_valid and not is_expired,
            "signature_valid": signature_valid,
            "is_expired": is_expired,
            "certificate_id": certificate.payload.certificate_id,
            "certificate_type": certificate.payload.certificate_type.value,
            "issued_at": certificate.payload.issued_at,
            "valid_until": certificate.payload.valid_until,
            "validation_passed": certificate.payload.validation_passed,
        }

    def export_certificate(self, certificate: Certificate, format: str = "json") -> str:
        """
        Export certificate in various formats.

        Args:
            certificate: Certificate to export
            format: Export format (json, pem-like, compact)

        Returns:
            Formatted certificate string
        """
        if format == "json":
            return certificate.to_json()

        elif format == "compact":
            # Compact single-line format for embedding
            return json.dumps(certificate.to_dict(), separators=(",", ":"))

        elif format == "pem":
            # PEM-like format for readability
            lines = [
                "-----BEGIN DETERMINISM CERTIFICATE-----",
                f"Certificate-ID: {certificate.payload.certificate_id}",
                f"Type: {certificate.payload.certificate_type.value}",
                f"Call-ID: {certificate.payload.call_id}",
                f"Issued: {certificate.payload.issued_at}",
                f"Expires: {certificate.payload.valid_until}",
                f"Level: {certificate.payload.determinism_level}",
                f"Match: {certificate.payload.match_achieved}",
                f"Passed: {certificate.payload.validation_passed}",
                f"Policies: {certificate.payload.policies_passed}/{certificate.payload.policy_count}",
                "",
                f"Signature: {certificate.signature[:32]}...{certificate.signature[-8:]}",
                "-----END DETERMINISM CERTIFICATE-----",
            ]
            return "\n".join(lines)

        else:
            raise ValueError(f"Unknown format: {format}")


# Export for convenience
__all__ = [
    "CertificateService",
    "Certificate",
    "CertificatePayload",
    "CertificateType",
]
