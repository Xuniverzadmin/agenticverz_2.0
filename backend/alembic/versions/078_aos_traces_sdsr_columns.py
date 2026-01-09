# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Add SDSR columns to aos_traces and aos_trace_steps per PIN-378
# Reference: PIN-378 (Canonical Logs System - SDSR Extension)

"""Add SDSR columns to aos_traces and aos_trace_steps

Revision ID: 078_aos_traces_sdsr_columns
Revises: 077_prevention_records_sdsr
Create Date: 2026-01-09

CANONICAL LOGS SYSTEM (PIN-378):
- aos_traces + aos_trace_steps are the canonical Logs foundation
- SDSR columns enable synthetic data marking and incident correlation
- Level derived from status at query time (not stored separately for steps)

Columns added to aos_traces:
- incident_id: Optional FK to incidents table for cross-domain correlation
- is_synthetic: SDSR marker (inherited from run.is_synthetic)
- synthetic_scenario_id: Scenario ID for traceability

Columns added to aos_trace_steps:
- source: Origin of the step (engine, external, replay) - default 'engine'
- level: Log level derived from status (INFO, WARN, ERROR) - default 'INFO'

INHERITANCE RULE:
- run.is_synthetic → aos_traces.is_synthetic
- aos_trace_steps inherit via trace_id (no separate SDSR columns on steps)

NOTE: inject_synthetic.py MUST NOT write to aos_traces/aos_trace_steps.
Traces appear naturally when runs execute. Synthetic marking is inherited.
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "078_aos_traces_sdsr_columns"
down_revision = "077_prevention_records_sdsr"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add SDSR and correlation columns to aos_traces and aos_trace_steps.
    """

    # =========================================================================
    # Table: aos_traces - SDSR + Incident correlation
    # =========================================================================

    # incident_id - Cross-domain correlation to incidents table
    op.add_column(
        "aos_traces",
        sa.Column(
            "incident_id",
            sa.String(100),
            nullable=True,
            comment="Cross-domain: Incident ID if trace triggered/relates to an incident",
        ),
    )

    # is_synthetic - SDSR marker (inherited from run.is_synthetic)
    op.add_column(
        "aos_traces",
        sa.Column(
            "is_synthetic",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="SDSR: True if run that created this trace was synthetic",
        ),
    )

    # synthetic_scenario_id - Scenario traceability
    op.add_column(
        "aos_traces",
        sa.Column(
            "synthetic_scenario_id",
            sa.String(64),
            nullable=True,
            comment="SDSR: Scenario ID inherited from run (e.g., ACTIVITY-RETRY-001)",
        ),
    )

    # Index for SDSR cleanup queries
    op.create_index(
        "idx_aos_traces_synthetic_scenario",
        "aos_traces",
        ["is_synthetic", "synthetic_scenario_id"],
        postgresql_where=sa.text("is_synthetic = true"),
    )

    # Index for incident correlation queries
    op.create_index(
        "idx_aos_traces_incident", "aos_traces", ["incident_id"], postgresql_where=sa.text("incident_id IS NOT NULL")
    )

    # =========================================================================
    # Table: aos_trace_steps - Source and Level
    # =========================================================================

    # source - Origin of the step
    op.add_column(
        "aos_trace_steps",
        sa.Column(
            "source",
            sa.String(50),
            nullable=False,
            server_default="engine",
            comment="Origin: engine (normal execution), external (API call), replay (replay execution)",
        ),
    )

    # level - Log level (derived from status, stored for query efficiency)
    # Mapping: success → INFO, retry → WARN, failure → ERROR, skipped → INFO
    op.add_column(
        "aos_trace_steps",
        sa.Column(
            "level",
            sa.String(16),
            nullable=False,
            server_default="INFO",
            comment="Log level: INFO (success/skipped), WARN (retry), ERROR (failure)",
        ),
    )

    # Index for log-style queries (level filtering)
    op.create_index("idx_aos_trace_steps_level", "aos_trace_steps", ["level"])

    # Composite index for log queries: trace + level
    op.create_index("idx_aos_trace_steps_trace_level", "aos_trace_steps", ["trace_id", "level"])


def downgrade() -> None:
    """Remove SDSR and correlation columns."""

    # aos_trace_steps indexes
    op.drop_index("idx_aos_trace_steps_trace_level", "aos_trace_steps")
    op.drop_index("idx_aos_trace_steps_level", "aos_trace_steps")

    # aos_trace_steps columns
    op.drop_column("aos_trace_steps", "level")
    op.drop_column("aos_trace_steps", "source")

    # aos_traces indexes
    op.drop_index("idx_aos_traces_incident", "aos_traces")
    op.drop_index("idx_aos_traces_synthetic_scenario", "aos_traces")

    # aos_traces columns
    op.drop_column("aos_traces", "synthetic_scenario_id")
    op.drop_column("aos_traces", "is_synthetic")
    op.drop_column("aos_traces", "incident_id")
