"""C2 Prediction Plane: Schema Hardening

This migration hardens the existing prediction_events table to meet
C2 invariants. It adds CHECK constraints that were missing from PB-S5.

C2 Invariants Enforced:
- I-C2-1: advisory MUST be TRUE (hard constraint, not just default)
- I-C2-5: Predictions MUST expire (valid_until NOT NULL)
- Confidence score must be in valid range (0-1)

Reference: PIN-221 (C2 Semantic Contract), PIN-222 (C2 Implementation Spec)

Revision ID: 061_c2_prediction_hardening
Revises: 060_c1_telemetry_plane
Create Date: 2025-12-28

CRITICAL: These constraints are C2 LAW. Do not weaken or remove them.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "061_c2_prediction_hardening"
down_revision = "060_c1_telemetry_plane"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Harden prediction_events table for C2 compliance."""

    # ============================================================
    # STEP 1: Add CHECK constraint for advisory = TRUE (I-C2-1)
    # ============================================================
    # This is the most critical constraint. Predictions MUST be advisory.
    # A default is not enough - we need enforcement.
    op.create_check_constraint(
        "chk_prediction_advisory",
        "prediction_events",
        "is_advisory = TRUE"
    )

    # ============================================================
    # STEP 2: Add CHECK constraint for confidence range
    # ============================================================
    # Confidence is informational only, but must be valid
    op.create_check_constraint(
        "chk_prediction_confidence_range",
        "prediction_events",
        "confidence_score >= 0 AND confidence_score <= 1"
    )

    # ============================================================
    # STEP 3: Rename valid_until to expires_at for clarity
    # ============================================================
    op.alter_column(
        "prediction_events",
        "valid_until",
        new_column_name="expires_at"
    )

    # ============================================================
    # STEP 4: Set default expiry for existing NULL rows
    # ============================================================
    # Before adding NOT NULL, we need to populate NULL values
    # Default: 30 minutes from now (immediate cleanup on next run)
    op.execute(
        """
        UPDATE prediction_events
        SET expires_at = NOW() + INTERVAL '30 minutes'
        WHERE expires_at IS NULL
        """
    )

    # ============================================================
    # STEP 5: Make expires_at NOT NULL (I-C2-5)
    # ============================================================
    # Predictions MUST expire. This is non-negotiable.
    op.alter_column(
        "prediction_events",
        "expires_at",
        nullable=False
    )

    # ============================================================
    # STEP 6: Add index for expiry-based cleanup
    # ============================================================
    # This supports the cleanup job
    op.create_index(
        "ix_prediction_events_expires_at",
        "prediction_events",
        ["expires_at"]
    )

    # ============================================================
    # STEP 7: Update table comment for C2
    # ============================================================
    op.execute(
        """
        COMMENT ON TABLE prediction_events IS
        'C2 Prediction Plane: Advisory predictions with hard constraints. '
        'I-C2-1: is_advisory MUST be TRUE (CHECK constraint enforced). '
        'I-C2-5: expires_at MUST be set (NOT NULL enforced). '
        'Predictions are disposable, expiring, and never replayed. '
        'Reference: PIN-221 (Semantic Contract), PIN-222 (Implementation Spec).';
        """
    )


def downgrade() -> None:
    """Remove C2 hardening (NOT RECOMMENDED in production)."""

    # Remove expiry index
    op.drop_index("ix_prediction_events_expires_at", table_name="prediction_events")

    # Make expires_at nullable again
    op.alter_column(
        "prediction_events",
        "expires_at",
        nullable=True
    )

    # Rename back to valid_until
    op.alter_column(
        "prediction_events",
        "expires_at",
        new_column_name="valid_until"
    )

    # Remove check constraints
    op.drop_constraint("chk_prediction_confidence_range", "prediction_events", type_="check")
    op.drop_constraint("chk_prediction_advisory", "prediction_events", type_="check")
