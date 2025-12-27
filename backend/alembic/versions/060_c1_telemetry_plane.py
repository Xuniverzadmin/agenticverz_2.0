"""C1: Telemetry Plane - Non-authoritative observability signals

Revision ID: 060_c1_telemetry_plane
Revises: 059_pc_discovery_ledger
Create Date: 2025-12-27

C1 Telemetry Plane provides high-volume observability signals that:
- NEVER participate in truth, memory, replay, or enforcement
- Are best-effort, non-blocking, non-transactional
- Have mandatory TTL (expires_at_utc)
- Are always non-authoritative (enforced by CHECK constraint)

INVARIANT (PIN-210):
- If telemetry disappears, nothing factual breaks
- Telemetry -> Truth is FORBIDDEN
- Telemetry -> Memory is FORBIDDEN
- Telemetry -> Replay is FORBIDDEN

Reference: PIN-210-c1-telemetry-plane.md
Truth anchor: "Telemetry observes reality without rewriting it."
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "060_c1_telemetry_plane"
down_revision = "059_pc_discovery_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # TELEMETRY_EVENT TABLE
    # ==========================================================================
    # Non-authoritative observability signals
    # - NO foreign key constraints (intentional - telemetry must not block truth)
    # - CHECK constraint enforces authoritative = FALSE always
    # - TTL via expires_at_utc (mandatory cleanup)

    op.create_table(
        "telemetry_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at_utc", sa.DateTime(timezone=True), nullable=False),
        # Tenant identification (hashed for privacy in observability)
        sa.Column("tenant_hash", sa.Text(), nullable=False),
        # Signal classification
        sa.Column("source_module", sa.Text(), nullable=False),
        sa.Column("signal_type", sa.Text(), nullable=False),
        # Signal data (flexible JSONB)
        sa.Column("signal_payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        # References to truth tables (NO FK constraints - intentional)
        sa.Column("trace_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        # CRITICAL: Always FALSE - enforced by CHECK constraint
        sa.Column("authoritative", sa.Boolean(), nullable=False, server_default="false"),
        # The core invariant: telemetry can NEVER be authoritative
        sa.CheckConstraint("authoritative = FALSE", name="chk_never_authoritative"),
    )

    # ==========================================================================
    # INDEXES FOR QUERY PATTERNS
    # ==========================================================================

    # TTL cleanup - this is the primary operational index
    op.create_index(
        "idx_telemetry_expires",
        "telemetry_event",
        ["expires_at_utc"],
    )

    # Tenant + module queries
    op.create_index(
        "idx_telemetry_tenant_module",
        "telemetry_event",
        ["tenant_hash", "source_module"],
    )

    # Signal type filtering
    op.create_index(
        "idx_telemetry_signal_type",
        "telemetry_event",
        ["signal_type"],
    )

    # Correlation with traces (partial - only where trace_id exists)
    op.create_index(
        "idx_telemetry_trace_id",
        "telemetry_event",
        ["trace_id"],
        postgresql_where=sa.text("trace_id IS NOT NULL"),
    )

    # Correlation with incidents (partial - only where incident_id exists)
    op.create_index(
        "idx_telemetry_incident_id",
        "telemetry_event",
        ["incident_id"],
        postgresql_where=sa.text("incident_id IS NOT NULL"),
    )

    # Time-based queries for dashboards
    op.create_index(
        "idx_telemetry_created_at",
        "telemetry_event",
        ["created_at_utc"],
    )

    # ==========================================================================
    # TELEMETRY_CLEANUP_LOG - Audit trail for TTL enforcement
    # ==========================================================================
    # Tracks cleanup runs so we can verify TTL is being enforced

    op.create_table(
        "telemetry_cleanup_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_at_utc", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("rows_deleted", sa.Integer(), nullable=False),
        sa.Column("oldest_deleted", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
    )

    # ==========================================================================
    # COMMENT BLOCK - Documentation in schema
    # ==========================================================================
    op.execute(
        """
        COMMENT ON TABLE telemetry_event IS
        'C1 Telemetry Plane: Non-authoritative observability signals.
        INVARIANT: If this table is dropped, all truth tables remain valid.
        PIN-210: Telemetry observes reality without rewriting it.';
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN telemetry_event.authoritative IS
        'ALWAYS FALSE. Enforced by CHECK constraint.
        If you need to make something authoritative, it belongs in a truth table.';
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN telemetry_event.trace_id IS
        'Reference only. NO FK constraint. Telemetry must not block trace operations.';
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN telemetry_event.incident_id IS
        'Reference only. NO FK constraint. Telemetry must not block incident operations.';
    """
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("telemetry_cleanup_log")
    op.drop_table("telemetry_event")
