# Layer: L6 — Platform (Database Migration)
# Product: system-wide
# Reference: GAP-024 (Inflection Point Metadata)
"""Add inflection point metadata to incidents tables

Revision ID: 115_add_inflection_point_metadata
Revises: 114_add_threshold_snapshot_hash
Create Date: 2026-01-21

Reference: GAP-024 (Inflection Point Metadata)

This migration adds inflection point metadata to both incidents tables:
- incidents (killswitch incidents and run-failure incidents)
- sdsr_incidents (SDSR-specific incidents)

Purpose:
- Capture the exact moment when an incident was triggered
- Provide step-level granularity for debugging and analysis
- Enable precise incident timeline reconstruction for SOC2 audits

Fields added:
- inflection_step_index: Which step triggered the incident (nullable)
- inflection_timestamp: When the inflection was detected
- inflection_context_json: Additional context about the inflection point
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect as sa_inspect

# revision identifiers
revision = "115_add_inflection_point_metadata"
down_revision = "114_add_threshold_snapshot_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add inflection point columns to main incidents table
    op.add_column(
        "incidents",
        sa.Column(
            "inflection_step_index",
            sa.Integer(),
            nullable=True,
            comment="Step index where incident was triggered (GAP-024)"
        ),
    )
    op.add_column(
        "incidents",
        sa.Column(
            "inflection_timestamp",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Exact timestamp when inflection was detected (GAP-024)"
        ),
    )
    op.add_column(
        "incidents",
        sa.Column(
            "inflection_context_json",
            sa.Text(),
            nullable=True,
            comment="JSON context about what was happening at inflection (GAP-024)"
        ),
    )

    # Create index for inflection timestamp lookups
    op.create_index(
        "ix_incidents_inflection_timestamp",
        "incidents",
        ["inflection_timestamp"],
    )

    # sdsr_incidents was dropped by migration 075 (consolidated into incidents).
    # Only alter if it still exists (e.g. stamped DBs that skipped 075).
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    if inspector.has_table("sdsr_incidents"):
        op.add_column(
            "sdsr_incidents",
            sa.Column(
                "inflection_step_index",
                sa.Integer(),
                nullable=True,
                comment="Step index where incident was triggered (GAP-024)"
            ),
        )
        op.add_column(
            "sdsr_incidents",
            sa.Column(
                "inflection_timestamp",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="Exact timestamp when inflection was detected (GAP-024)"
            ),
        )
        op.add_column(
            "sdsr_incidents",
            sa.Column(
                "inflection_context_json",
                sa.Text(),
                nullable=True,
                comment="JSON context about what was happening at inflection (GAP-024)"
            ),
        )
        op.create_index(
            "ix_sdsr_incidents_inflection_timestamp",
            "sdsr_incidents",
            ["inflection_timestamp"],
        )


def downgrade() -> None:
    # Drop sdsr_incidents artifacts only if table exists
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    if inspector.has_table("sdsr_incidents"):
        op.drop_index("ix_sdsr_incidents_inflection_timestamp", table_name="sdsr_incidents")
        op.drop_column("sdsr_incidents", "inflection_context_json")
        op.drop_column("sdsr_incidents", "inflection_timestamp")
        op.drop_column("sdsr_incidents", "inflection_step_index")

    op.drop_index("ix_incidents_inflection_timestamp", table_name="incidents")

    # Drop columns from incidents
    op.drop_column("incidents", "inflection_context_json")
    op.drop_column("incidents", "inflection_timestamp")
    op.drop_column("incidents", "inflection_step_index")
