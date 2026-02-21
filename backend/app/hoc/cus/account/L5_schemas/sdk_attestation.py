# capability_id: CAP-012
# Layer: L5 — Schema
# AUDIENCE: SHARED
# Role: SDK attestation record — pure data schema for attestation persistence
# Product: system-wide
# Callers: L5 engines, L4 handlers, L6 drivers
# Allowed Imports: stdlib only
# Forbidden Imports: FastAPI, SQLAlchemy, ORM models

"""
SDK Attestation Schema (L5)

Pure dataclass representing an SDK attestation record.
Used by L4 handler and L6 driver for persistence and verification.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SDKAttestationRecord:
    """SDK attestation record for persistence."""

    tenant_id: str
    sdk_version: str
    sdk_language: str
    client_id: Optional[str]
    attested_at: datetime
    attestation_hash: str


__all__ = ["SDKAttestationRecord"]
