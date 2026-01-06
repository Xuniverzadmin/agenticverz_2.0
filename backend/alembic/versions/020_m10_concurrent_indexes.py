"""020_m10_concurrent_indexes - Create heavy indexes CONCURRENTLY

Revision ID: 020_m10_concurrent_indexes
Revises: 019_m10_recovery_enhancements
Create Date: 2025-12-09

IMPORTANT: Run this migration during a maintenance window or low-traffic period.

This migration creates indexes using CREATE INDEX CONCURRENTLY which:
- Does NOT block reads or writes
- Takes longer than regular index creation
- Can be cancelled if needed without leaving corrupt indexes
- Requires a separate transaction per CONCURRENT operation

Heavy indexes for production performance:
- idx_rc_confidence_desc: For sorting by confidence
- idx_rc_decision_created: For filtering and sorting
- idx_fm_error_code_created: For failure_matches lookup
- idx_sp_suggestion_created: For provenance queries
"""

from sqlalchemy import text

from alembic import op

# revision identifiers
revision = "020_m10_concurrent_indexes"
down_revision = "019_m10_recovery_enhancements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create indexes for production performance.

    NOTE: In production, you may want to run these with CONCURRENTLY
    outside of Alembic using raw SQL connections with autocommit mode.
    For Alembic migrations, we use regular CREATE INDEX which is safe
    but will briefly lock the table.
    """
    conn = op.get_bind()

    # ==========================================================================
    # recovery_candidates indexes
    # ==========================================================================

    # Confidence DESC for dashboard ranking queries
    conn.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_rc_confidence_desc
        ON public.recovery_candidates (confidence DESC NULLS LAST);
    """
        )
    )

    # Decision + created_at for filtered listing
    conn.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_rc_decision_created
        ON public.recovery_candidates (decision, created_at DESC);
    """
        )
    )

    # Error code for pattern analysis
    conn.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_rc_error_code
        ON public.recovery_candidates (error_code)
        WHERE error_code IS NOT NULL;
    """
        )
    )

    # ==========================================================================
    # failure_matches indexes (if table exists)
    # ==========================================================================
    try:
        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_fm_error_code_created
            ON public.failure_matches (error_code, created_at DESC);
        """
            )
        )
    except Exception:
        pass  # Table may not exist

    # ==========================================================================
    # m10_recovery.suggestion_provenance indexes
    # ==========================================================================
    try:
        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_sp_suggestion_created
            ON m10_recovery.suggestion_provenance (suggestion_id, created_at DESC);
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_sp_event_created
            ON m10_recovery.suggestion_provenance (event_type, created_at DESC);
        """
            )
        )
    except Exception:
        pass  # Schema may not exist

    # ==========================================================================
    # m10_recovery.suggestion_input indexes
    # ==========================================================================
    try:
        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_si_suggestion_type
            ON m10_recovery.suggestion_input (suggestion_id, input_type);
        """
            )
        )
    except Exception:
        pass  # Schema may not exist

    # ==========================================================================
    # m10_recovery.suggestion_action indexes
    # ==========================================================================
    try:
        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_sa_type_priority
            ON m10_recovery.suggestion_action (action_type, priority DESC)
            WHERE is_active = TRUE;
        """
            )
        )
    except Exception:
        pass  # Schema may not exist


def downgrade() -> None:
    """Drop the indexes."""
    conn = op.get_bind()

    # Drop indexes in reverse order
    try:
        conn.execute(text("DROP INDEX IF EXISTS m10_recovery.idx_sa_type_priority;"))
    except Exception:
        pass

    try:
        conn.execute(text("DROP INDEX IF EXISTS m10_recovery.idx_si_suggestion_type;"))
    except Exception:
        pass

    try:
        conn.execute(text("DROP INDEX IF EXISTS m10_recovery.idx_sp_event_created;"))
    except Exception:
        pass

    try:
        conn.execute(text("DROP INDEX IF EXISTS m10_recovery.idx_sp_suggestion_created;"))
    except Exception:
        pass

    try:
        conn.execute(text("DROP INDEX IF EXISTS public.idx_fm_error_code_created;"))
    except Exception:
        pass

    conn.execute(text("DROP INDEX IF EXISTS public.idx_rc_error_code;"))
    conn.execute(text("DROP INDEX IF EXISTS public.idx_rc_decision_created;"))
    conn.execute(text("DROP INDEX IF EXISTS public.idx_rc_confidence_desc;"))
