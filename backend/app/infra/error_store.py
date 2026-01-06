# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: any (api|worker|scheduler)
#   Execution: sync
# Role: Append-only error persistence for forensic diagnostics
# Callers: L4 aggregation services, L7 ops tools
# Allowed Imports: L6 only (db, infra)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-264 (Phase-S Track 1.3)

"""
Error Persistence Store — Phase-S Track 1.3

Append-only, write-once store for ErrorEnvelope persistence.

Design Principles:
- APPEND-ONLY: No updates, no deletes (except retention cleanup)
- WRITE-ONCE: Each error_id is immutable after insert
- INFRA-ONLY: Never exposed to product APIs
- VERSIONED: Envelope version stored for replay compatibility

This is the forensic memory of the system.
Errors written here become incident history.

HARD RULES:
1. No UPDATE operations
2. No DELETE operations (except scheduled retention cleanup)
3. No direct exposure to L2 APIs
4. L4 aggregation services consume this, never expose it
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlmodel import Session

from app.infra.error_envelope import ErrorClass, ErrorEnvelope


def persist_error(session: Session, envelope: ErrorEnvelope) -> bool:
    """
    Persist an error envelope to the store.

    Uses INSERT ON CONFLICT DO NOTHING to ensure idempotency.
    If error_id already exists, silently succeeds (first write wins).

    Args:
        session: Database session
        envelope: ErrorEnvelope to persist

    Returns:
        True if inserted, False if already existed
    """
    stmt = text("""
        INSERT INTO infra_error_events (
            error_id,
            timestamp,
            layer,
            component,
            error_class,
            severity,
            message,
            correlation_id,
            decision_id,
            run_id,
            agent_id,
            tenant_id,
            input_hash,
            exception_type,
            exception_chain,
            context,
            envelope_version,
            created_at
        ) VALUES (
            :error_id,
            :timestamp,
            :layer,
            :component,
            :error_class,
            :severity,
            :message,
            :correlation_id,
            :decision_id,
            :run_id,
            :agent_id,
            :tenant_id,
            :input_hash,
            :exception_type,
            :exception_chain,
            :context,
            :envelope_version,
            :created_at
        )
        ON CONFLICT (error_id) DO NOTHING
        RETURNING error_id
    """)

    result = session.execute(
        stmt,
        {
            "error_id": envelope.error_id,
            "timestamp": envelope.timestamp,
            "layer": envelope.layer,
            "component": envelope.component,
            "error_class": envelope.error_class.value,
            "severity": envelope.severity.value,
            "message": envelope.message,
            "correlation_id": envelope.correlation_id,
            "decision_id": envelope.decision_id,
            "run_id": envelope.run_id,
            "agent_id": envelope.agent_id,
            "tenant_id": envelope.tenant_id,
            "input_hash": envelope.input_hash,
            "exception_type": envelope.exception_type,
            "exception_chain": envelope.exception_chain,
            "context": envelope.context,
            "envelope_version": envelope.version,
            "created_at": datetime.now(timezone.utc),
        },
    )

    # Check if insert happened (RETURNING gives us the error_id if inserted)
    row = result.fetchone()
    return row is not None


def persist_errors_batch(session: Session, envelopes: List[ErrorEnvelope]) -> int:
    """
    Persist multiple error envelopes in a batch.

    Uses bulk insert with ON CONFLICT DO NOTHING.

    Args:
        session: Database session
        envelopes: List of ErrorEnvelopes to persist

    Returns:
        Number of envelopes actually inserted (excludes duplicates)
    """
    if not envelopes:
        return 0

    values = [
        {
            "error_id": e.error_id,
            "timestamp": e.timestamp,
            "layer": e.layer,
            "component": e.component,
            "error_class": e.error_class.value,
            "severity": e.severity.value,
            "message": e.message,
            "correlation_id": e.correlation_id,
            "decision_id": e.decision_id,
            "run_id": e.run_id,
            "agent_id": e.agent_id,
            "tenant_id": e.tenant_id,
            "input_hash": e.input_hash,
            "exception_type": e.exception_type,
            "exception_chain": e.exception_chain,
            "context": e.context,
            "envelope_version": e.version,
            "created_at": datetime.now(timezone.utc),
        }
        for e in envelopes
    ]

    # Count before insert
    count_before = session.execute(text("SELECT COUNT(*) FROM infra_error_events")).scalar() or 0

    # Bulk insert
    stmt = text("""
        INSERT INTO infra_error_events (
            error_id, timestamp, layer, component, error_class, severity,
            message, correlation_id, decision_id, run_id, agent_id, tenant_id,
            input_hash, exception_type, exception_chain, context,
            envelope_version, created_at
        )
        SELECT
            v.error_id, v.timestamp, v.layer, v.component, v.error_class, v.severity,
            v.message, v.correlation_id, v.decision_id, v.run_id, v.agent_id, v.tenant_id,
            v.input_hash, v.exception_type, v.exception_chain, v.context,
            v.envelope_version, v.created_at
        FROM jsonb_to_recordset(:values::jsonb) AS v(
            error_id TEXT, timestamp TIMESTAMPTZ, layer TEXT, component TEXT,
            error_class TEXT, severity TEXT, message TEXT, correlation_id TEXT,
            decision_id TEXT, run_id TEXT, agent_id TEXT, tenant_id TEXT,
            input_hash TEXT, exception_type TEXT, exception_chain JSONB,
            context JSONB, envelope_version TEXT, created_at TIMESTAMPTZ
        )
        ON CONFLICT (error_id) DO NOTHING
    """)

    import json

    session.execute(stmt, {"values": json.dumps(values, default=str)})

    # Count after insert
    count_after = session.execute(text("SELECT COUNT(*) FROM infra_error_events")).scalar() or 0

    return count_after - count_before


# =============================================================================
# Query Functions (Read-Only, for L4 Aggregation Services)
# =============================================================================


def get_errors_by_correlation(
    session: Session,
    correlation_id: str,
) -> List[Dict[str, Any]]:
    """
    Get all errors for a correlation ID (request/workflow trace).

    Used by L4 to correlate errors across components.
    """
    stmt = text("""
        SELECT *
        FROM infra_error_events
        WHERE correlation_id = :correlation_id
        ORDER BY timestamp ASC
    """)

    result = session.execute(stmt, {"correlation_id": correlation_id})
    return [dict(row._mapping) for row in result.fetchall()]


def get_errors_by_component(
    session: Session,
    component: str,
    since: Optional[datetime] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Get recent errors for a component.

    Used by L4 for incident aggregation.
    """
    if since is None:
        since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)

    stmt = text("""
        SELECT *
        FROM infra_error_events
        WHERE component = :component
          AND timestamp >= :since
        ORDER BY timestamp DESC
        LIMIT :limit
    """)

    result = session.execute(
        stmt,
        {
            "component": component,
            "since": since,
            "limit": limit,
        },
    )
    return [dict(row._mapping) for row in result.fetchall()]


def get_errors_by_class(
    session: Session,
    error_class: ErrorClass,
    since: Optional[datetime] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Get recent errors by classification.

    Used by L4 for pattern detection.
    """
    if since is None:
        since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)

    stmt = text("""
        SELECT *
        FROM infra_error_events
        WHERE error_class = :error_class
          AND timestamp >= :since
        ORDER BY timestamp DESC
        LIMIT :limit
    """)

    result = session.execute(
        stmt,
        {
            "error_class": error_class.value,
            "since": since,
            "limit": limit,
        },
    )
    return [dict(row._mapping) for row in result.fetchall()]


def get_error_counts_by_class(
    session: Session,
    since: datetime,
    until: Optional[datetime] = None,
) -> Dict[str, int]:
    """
    Get error counts grouped by class.

    Used by L4 for trend metrics.
    """
    if until is None:
        until = datetime.now(timezone.utc)

    stmt = text("""
        SELECT error_class, COUNT(*) as count
        FROM infra_error_events
        WHERE timestamp >= :since
          AND timestamp < :until
        GROUP BY error_class
        ORDER BY count DESC
    """)

    result = session.execute(stmt, {"since": since, "until": until})
    return {row.error_class: row.count for row in result.fetchall()}


def get_error_counts_by_component(
    session: Session,
    since: datetime,
    until: Optional[datetime] = None,
) -> Dict[str, int]:
    """
    Get error counts grouped by component.

    Used by L4 for health signals.
    """
    if until is None:
        until = datetime.now(timezone.utc)

    stmt = text("""
        SELECT component, COUNT(*) as count
        FROM infra_error_events
        WHERE timestamp >= :since
          AND timestamp < :until
        GROUP BY component
        ORDER BY count DESC
    """)

    result = session.execute(stmt, {"since": since, "until": until})
    return {row.component: row.count for row in result.fetchall()}


def get_error_timeline(
    session: Session,
    since: datetime,
    bucket_minutes: int = 60,
) -> List[Dict[str, Any]]:
    """
    Get error counts over time in buckets.

    Used by L4 for trend analysis.
    """
    stmt = text("""
        SELECT
            date_trunc('hour', timestamp) +
                (EXTRACT(minute FROM timestamp)::int / :bucket * :bucket) * interval '1 minute'
                AS bucket,
            COUNT(*) as count,
            COUNT(DISTINCT component) as unique_components,
            COUNT(DISTINCT error_class) as unique_classes
        FROM infra_error_events
        WHERE timestamp >= :since
        GROUP BY bucket
        ORDER BY bucket ASC
    """)

    result = session.execute(
        stmt,
        {
            "since": since,
            "bucket": bucket_minutes,
        },
    )
    return [dict(row._mapping) for row in result.fetchall()]


# =============================================================================
# Retention (L7 Ops Tool, Not L4)
# =============================================================================


def cleanup_old_errors(
    session: Session,
    retention_days: int = 90,
) -> int:
    """
    Delete errors older than retention period.

    IMPORTANT: This is the ONLY delete operation allowed.
    Should be called by L7 ops scheduler, NOT by L4 services.

    Args:
        session: Database session
        retention_days: Days to retain errors (default 90)

    Returns:
        Number of rows deleted
    """
    cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff = cutoff.replace(day=cutoff.day - retention_days)

    stmt = text("""
        DELETE FROM infra_error_events
        WHERE created_at < :cutoff
        RETURNING error_id
    """)

    result = session.execute(stmt, {"cutoff": cutoff})
    return len(result.fetchall())
