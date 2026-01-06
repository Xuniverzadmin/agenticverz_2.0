# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Create infra_error_events table for Phase-S error persistence
# Callers: alembic upgrade
# Allowed Imports: L6 (alembic, sqlalchemy)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-264 Phase-S Track 1.3

"""
Phase-S Track 1.3: Error Persistence.

Creates the infra_error_events table for append-only error storage.

Design Principles:
- APPEND-ONLY: No updates allowed (enforced by trigger)
- WRITE-ONCE: Each error_id is immutable after insert
- INDEXED: By error_class + component for aggregation
- VERSIONED: envelope_version for replay compatibility
- RETENTION-READY: created_at for scheduled cleanup

The only allowed DELETE is retention cleanup (90 days default).

Reference: PIN-264 (Phase-S System Readiness)
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "067_phase_s_error_persistence"
down_revision = "066_interpretation_ownership"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create the infra_error_events table
    op.create_table(
        "infra_error_events",
        # Primary key (error_id is the unique identifier)
        sa.Column(
            "error_id",
            sa.String(50),
            primary_key=True,
            nullable=False,
        ),
        # Timestamp when error occurred
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        # Layer that emitted the error (L2, L3, L4, L5, L6)
        sa.Column(
            "layer",
            sa.String(10),
            nullable=False,
        ),
        # Component that emitted the error (module path)
        sa.Column(
            "component",
            sa.String(200),
            nullable=False,
        ),
        # Error classification (infra.*, domain.*, system.*)
        sa.Column(
            "error_class",
            sa.String(50),
            nullable=False,
        ),
        # Severity level
        sa.Column(
            "severity",
            sa.String(20),
            nullable=False,
        ),
        # Human-readable message
        sa.Column(
            "message",
            sa.Text,
            nullable=False,
        ),
        # Correlation (optional)
        sa.Column(
            "correlation_id",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "decision_id",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "run_id",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "agent_id",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "tenant_id",
            sa.String(100),
            nullable=True,
        ),
        # Input hash (for replay, never raw input)
        sa.Column(
            "input_hash",
            sa.String(64),
            nullable=True,
        ),
        # Exception details (sanitized)
        sa.Column(
            "exception_type",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "exception_chain",
            postgresql.JSONB,
            nullable=True,
        ),
        # Arbitrary context
        sa.Column(
            "context",
            postgresql.JSONB,
            nullable=True,
            server_default="{}",
        ),
        # Envelope version for schema evolution
        sa.Column(
            "envelope_version",
            sa.String(10),
            nullable=False,
            server_default="1.0",
        ),
        # Created timestamp for retention cleanup
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # 2. Create indexes for common query patterns
    # Index for correlation lookups
    op.create_index(
        "ix_infra_error_events_correlation_id",
        "infra_error_events",
        ["correlation_id"],
        postgresql_where=sa.text("correlation_id IS NOT NULL"),
    )

    # Index for component + timestamp (incident aggregation)
    op.create_index(
        "ix_infra_error_events_component_timestamp",
        "infra_error_events",
        ["component", "timestamp"],
    )

    # Index for error_class + timestamp (pattern detection)
    op.create_index(
        "ix_infra_error_events_class_timestamp",
        "infra_error_events",
        ["error_class", "timestamp"],
    )

    # Index for retention cleanup
    op.create_index(
        "ix_infra_error_events_created_at",
        "infra_error_events",
        ["created_at"],
    )

    # Index for run correlation
    op.create_index(
        "ix_infra_error_events_run_id",
        "infra_error_events",
        ["run_id"],
        postgresql_where=sa.text("run_id IS NOT NULL"),
    )

    # 3. Create trigger to prevent updates (append-only enforcement)
    op.execute("""
        CREATE OR REPLACE FUNCTION infra_error_events_prevent_update()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'infra_error_events is append-only. Updates are forbidden. error_id=%', OLD.error_id;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER infra_error_events_no_update
        BEFORE UPDATE ON infra_error_events
        FOR EACH ROW
        EXECUTE FUNCTION infra_error_events_prevent_update();
    """)

    # 4. Add comment for documentation
    op.execute("""
        COMMENT ON TABLE infra_error_events IS
        'Phase-S error persistence. APPEND-ONLY. No updates. Delete only for retention cleanup. PIN-264.';
    """)


def downgrade() -> None:
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS infra_error_events_no_update ON infra_error_events")
    op.execute("DROP FUNCTION IF EXISTS infra_error_events_prevent_update()")

    # Drop indexes
    op.drop_index("ix_infra_error_events_run_id", table_name="infra_error_events")
    op.drop_index("ix_infra_error_events_created_at", table_name="infra_error_events")
    op.drop_index("ix_infra_error_events_class_timestamp", table_name="infra_error_events")
    op.drop_index("ix_infra_error_events_component_timestamp", table_name="infra_error_events")
    op.drop_index("ix_infra_error_events_correlation_id", table_name="infra_error_events")

    # Drop table
    op.drop_table("infra_error_events")
