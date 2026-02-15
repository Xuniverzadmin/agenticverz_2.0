# Layer: L6 — Domain Driver
# AUDIENCE: SHARED
# Temporal:
#   Trigger: L5/L4 call
#   Execution: sync
# Data Access:
#   Reads: sdk_attestations (via tenants table JSON column or dedicated table)
#   Writes: sdk_attestations — NO COMMIT (L4 owns transaction)
# Database:
#   Scope: domain (account)
# Role: SDK attestation persistence — write and fetch attestation records
# Product: system-wide
# Callers: L4 account_handler.py
# Allowed Imports: sqlalchemy (text), L5 schemas
# Forbidden Imports: L2, L3, L5 engines

"""
SDK Attestation Driver (L6)

Persists and retrieves SDK attestation records.
Uses raw SQL via sqlalchemy text() — no ORM imports at runtime.

Transaction boundary: L4 handler owns begin()/commit().
This driver NEVER calls commit() or rollback().
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text as sql_text
from app.hoc.cus.account.L5_schemas.sdk_attestation import SDKAttestationRecord

logger = logging.getLogger("nova.drivers.sdk_attestation")


def compute_attestation_hash(
    tenant_id: str, sdk_version: str, sdk_language: str, client_id: Optional[str],
) -> str:
    """Compute a deterministic hash for attestation dedup."""
    raw = f"{tenant_id}:{sdk_version}:{sdk_language}:{client_id or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def write_attestation(session, record: SDKAttestationRecord) -> None:
    """
    Write an SDK attestation record.

    Uses UPSERT (INSERT ON CONFLICT UPDATE) to ensure idempotency.
    NO COMMIT — L4 coordinator owns transaction boundary.
    """
    session.execute(
        sql_text("""
            INSERT INTO sdk_attestations (tenant_id, sdk_version, sdk_language, client_id, attested_at, attestation_hash)
            VALUES (:tenant_id, :sdk_version, :sdk_language, :client_id, :attested_at, :attestation_hash)
            ON CONFLICT (tenant_id, attestation_hash) DO UPDATE SET
                attested_at = EXCLUDED.attested_at,
                sdk_version = EXCLUDED.sdk_version
        """),
        {
            "tenant_id": record.tenant_id,
            "sdk_version": record.sdk_version,
            "sdk_language": record.sdk_language,
            "client_id": record.client_id,
            "attested_at": record.attested_at,
            "attestation_hash": record.attestation_hash,
        },
    )
    # NO COMMIT — L4 coordinator owns transaction boundary


def fetch_attestation(session, tenant_id: str) -> Optional[SDKAttestationRecord]:
    """
    Fetch the latest SDK attestation for a tenant.

    Returns None if no attestation exists.
    """
    row = session.execute(
        sql_text("""
            SELECT tenant_id, sdk_version, sdk_language, client_id, attested_at, attestation_hash
            FROM sdk_attestations
            WHERE tenant_id = :tenant_id
            ORDER BY attested_at DESC
            LIMIT 1
        """),
        {"tenant_id": tenant_id},
    ).mappings().first()

    if row is None:
        return None

    return SDKAttestationRecord(
        tenant_id=row["tenant_id"],
        sdk_version=row["sdk_version"],
        sdk_language=row["sdk_language"],
        client_id=row["client_id"],
        attested_at=row["attested_at"],
        attestation_hash=row["attestation_hash"],
    )


def has_attestation(session, tenant_id: str) -> bool:
    """Check whether a tenant has any SDK attestation."""
    row = session.execute(
        sql_text("SELECT 1 FROM sdk_attestations WHERE tenant_id = :tenant_id LIMIT 1"),
        {"tenant_id": tenant_id},
    ).first()
    return row is not None


__all__ = [
    "compute_attestation_hash",
    "write_attestation",
    "fetch_attestation",
    "has_attestation",
]
