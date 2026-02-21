# capability_id: CAP-012
# Layer: L4 — HOC Spine (Driver)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: discovery_ledger (SQL)
#   Writes: discovery_ledger (SQL)
# Database:
#   Scope: hoc_spine
#   Models: discovery_ledger (via raw SQL)
# Role: Discovery ledger for artifact tracking — pure driver (no transaction ownership)
# Callers: L4 handlers (ActivityDiscoveryHandler)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-470, Discovery System
# Transaction: Driver NEVER commits/rollbacks — L4 handler owns transaction boundaries.

"""
Discovery Ledger - signal recording helpers (pure driver).

Core principle: Discovery Ledger records curiosity, not decisions.

This module provides:
- emit_signal(): Record a discovery signal (aggregating duplicates)
- get_signals(): Query discovery signals from the ledger
- DiscoverySignal: Pydantic model for signal data

Signals are aggregated: same (artifact, field, signal_type) updates seen_count.
Nothing in the system depends on this table - it's pure observation.

Transaction ownership: L4 handler creates and commits the connection.
This driver only executes SQL on a caller-provided connection.
"""

import json
import logging
import os
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DiscoverySignal(BaseModel):
    """Discovery signal data model."""

    artifact: str = Field(..., description="Artifact name (e.g. prediction_events)")
    field: Optional[str] = Field(None, description="Field name (optional)")
    signal_type: str = Field(..., description="Signal type (e.g. high_operator_access)")
    evidence: dict[str, Any] = Field(..., description="Evidence data (counts, queries, etc)")
    confidence: Optional[Decimal] = Field(None, ge=0, le=1, description="Confidence 0.00-1.00")
    detected_by: str = Field(..., description="Subsystem that detected the signal")
    notes: Optional[str] = Field(None, description="Optional notes")


def emit_signal(
    connection: Any,
    artifact: str,
    signal_type: str,
    evidence: dict[str, Any],
    detected_by: str,
    field: Optional[str] = None,
    confidence: Optional[float] = None,
    notes: Optional[str] = None,
    phase: Optional[str] = None,
    environment: Optional[str] = None,
) -> Optional[UUID]:
    """
    Record a discovery signal to the ledger.

    Signals are aggregated: same (artifact, field, signal_type) updates seen_count.
    This is non-blocking and safe to call frequently.

    Args:
        connection: SQLAlchemy Connection (caller owns lifecycle and commit)
        artifact: Artifact name (e.g. "prediction_events")
        signal_type: Signal type (e.g. "high_operator_access")
        evidence: Evidence data as dict
        detected_by: Subsystem name that detected the signal
        field: Optional field name within the artifact
        confidence: Optional confidence score 0.0-1.0
        notes: Optional notes
        phase: Current phase (defaults to env var or "C")
        environment: Environment (defaults to env var or "local")

    Returns:
        UUID of the signal record, or None if recording failed

    Transaction Semantics:
        Driver does NOT commit. Caller (L4 handler) owns the transaction.
    """
    if phase is None:
        phase = os.environ.get("AOS_PHASE", "C")
    if environment is None:
        environment = os.environ.get("AOS_ENVIRONMENT", "local")

    try:
        # Use upsert pattern: ON CONFLICT update seen_count and last_seen_at
        if field is not None:
            upsert_sql = text(
                """
                INSERT INTO discovery_ledger (
                    artifact, field, signal_type, evidence, confidence,
                    detected_by, phase, environment, notes
                )
                VALUES (
                    :artifact, :field, :signal_type, CAST(:evidence AS jsonb), :confidence,
                    :detected_by, :phase, :environment, :notes
                )
                ON CONFLICT (artifact, field, signal_type)
                WHERE field IS NOT NULL
                DO UPDATE SET
                    seen_count = discovery_ledger.seen_count + 1,
                    last_seen_at = now(),
                    evidence = discovery_ledger.evidence || CAST(:evidence AS jsonb),
                    confidence = COALESCE(:confidence, discovery_ledger.confidence)
                RETURNING id
            """
            )
        else:
            upsert_sql = text(
                """
                INSERT INTO discovery_ledger (
                    artifact, signal_type, evidence, confidence,
                    detected_by, phase, environment, notes
                )
                VALUES (
                    :artifact, :signal_type, CAST(:evidence AS jsonb), :confidence,
                    :detected_by, :phase, :environment, :notes
                )
                ON CONFLICT (artifact, signal_type)
                WHERE field IS NULL
                DO UPDATE SET
                    seen_count = discovery_ledger.seen_count + 1,
                    last_seen_at = now(),
                    evidence = discovery_ledger.evidence || CAST(:evidence AS jsonb),
                    confidence = COALESCE(:confidence, discovery_ledger.confidence)
                RETURNING id
            """
            )

        params = {
            "artifact": artifact,
            "field": field,
            "signal_type": signal_type,
            "evidence": json.dumps(evidence),
            "confidence": confidence,
            "detected_by": detected_by,
            "phase": phase,
            "environment": environment,
            "notes": notes,
        }

        result = connection.execute(upsert_sql, params)
        row = result.fetchone()
        if row:
            return row[0]
        return None

    except SQLAlchemyError as e:
        logger.warning(f"Failed to emit discovery signal: {e}")
        return None


def get_signals(
    connection: Any,
    artifact: Optional[str] = None,
    signal_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    """
    Query discovery signals from the ledger.

    Args:
        connection: SQLAlchemy Connection (caller owns lifecycle)
        artifact: Filter by artifact name
        signal_type: Filter by signal type
        status: Filter by status (observed/ignored/promoted)
        limit: Max records to return

    Returns:
        List of signal records as dicts
    """
    try:
        where_clauses = []
        params: dict[str, Any] = {"limit": limit}

        if artifact:
            where_clauses.append("artifact = :artifact")
            params["artifact"] = artifact
        if signal_type:
            where_clauses.append("signal_type = :signal_type")
            params["signal_type"] = signal_type
        if status:
            where_clauses.append("status = :status")
            params["status"] = status

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = text(
            f"""
            SELECT
                id, artifact, field, signal_type, evidence, confidence,
                detected_by, phase, environment, first_seen_at, last_seen_at,
                seen_count, status, notes
            FROM discovery_ledger
            WHERE {where_sql}
            ORDER BY seen_count DESC, last_seen_at DESC
            LIMIT :limit
        """
        )

        result = connection.execute(query, params)
        rows = result.fetchall()

        signals = []
        for row in rows:
            signals.append(
                {
                    "id": str(row.id),
                    "artifact": row.artifact,
                    "field": row.field,
                    "signal_type": row.signal_type,
                    "evidence": row.evidence,
                    "confidence": float(row.confidence) if row.confidence else None,
                    "detected_by": row.detected_by,
                    "phase": row.phase,
                    "environment": row.environment,
                    "first_seen_at": row.first_seen_at.isoformat() if row.first_seen_at else None,
                    "last_seen_at": row.last_seen_at.isoformat() if row.last_seen_at else None,
                    "seen_count": row.seen_count,
                    "status": row.status,
                    "notes": row.notes,
                }
            )
        return signals

    except Exception as e:
        logger.warning(f"Failed to query discovery signals: {e}")
        return []
