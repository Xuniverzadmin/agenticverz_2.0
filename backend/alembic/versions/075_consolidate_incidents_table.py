# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Consolidate sdsr_incidents into canonical incidents table (PIN-370)
# Reference: PIN-370 (SDSR - One Canonical Incidents Table)

"""Consolidate sdsr_incidents into canonical incidents table

Revision ID: 075_consolidate_incidents
Revises: 074_create_sdsr_incidents
Create Date: 2026-01-09

SDSR Consolidation (PIN-370):
- incidents is the ONE canonical table
- is_synthetic is a property, not a category
- SDSR = traceability layer on same domain
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "075_consolidate_incidents"
down_revision = "074_create_sdsr_incidents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add SDSR columns to canonical incidents table and migrate data.

    After this migration:
    - incidents table has all SDSR columns
    - sdsr_incidents data is migrated to incidents
    - sdsr_incidents table is dropped
    """

    # Step 1: Add SDSR columns to incidents table
    # These columns enable run-failure incidents in the canonical table

    op.add_column("incidents", sa.Column(
        "source_run_id", sa.Text(), nullable=True,
        comment="Run ID that triggered this incident (SDSR)"
    ))
    op.add_column("incidents", sa.Column(
        "source_type", sa.Text(), nullable=True, server_default="killswitch",
        comment="Source type: run, killswitch, policy, manual"
    ))
    op.add_column("incidents", sa.Column(
        "category", sa.Text(), nullable=True,
        comment="EXECUTION_FAILURE, POLICY_VIOLATION, LOOP_DETECTED, etc."
    ))
    op.add_column("incidents", sa.Column(
        "description", sa.Text(), nullable=True,
        comment="Detailed description of the incident"
    ))
    op.add_column("incidents", sa.Column(
        "error_code", sa.Text(), nullable=True,
        comment="Error code e.g. EXECUTION_TIMEOUT"
    ))
    op.add_column("incidents", sa.Column(
        "error_message", sa.Text(), nullable=True,
        comment="Full error message from source"
    ))
    op.add_column("incidents", sa.Column(
        "impact_scope", sa.Text(), nullable=True,
        comment="Impact: single_run, agent, tenant, system"
    ))
    op.add_column("incidents", sa.Column(
        "affected_agent_id", sa.Text(), nullable=True,
        comment="Agent ID affected by incident"
    ))
    op.add_column("incidents", sa.Column(
        "affected_count", sa.Integer(), nullable=True, server_default="1",
        comment="Number of affected runs/entities"
    ))
    op.add_column("incidents", sa.Column(
        "resolution_notes", sa.Text(), nullable=True,
        comment="Notes on how incident was resolved"
    ))
    op.add_column("incidents", sa.Column(
        "escalated", sa.Boolean(), nullable=True, server_default="false",
        comment="Whether incident was escalated"
    ))
    op.add_column("incidents", sa.Column(
        "escalated_at", sa.DateTime(timezone=True), nullable=True
    ))
    op.add_column("incidents", sa.Column(
        "escalated_to", sa.Text(), nullable=True,
        comment="Who was escalated to"
    ))
    op.add_column("incidents", sa.Column(
        "is_synthetic", sa.Boolean(), nullable=True, server_default="false",
        comment="SDSR: True if created during synthetic scenario"
    ))
    op.add_column("incidents", sa.Column(
        "synthetic_scenario_id", sa.Text(), nullable=True,
        comment="SDSR: Scenario ID for traceability"
    ))

    # Step 2: Create indexes for SDSR queries
    op.create_index(
        "idx_incidents_source_run_id",
        "incidents",
        ["source_run_id"],
        postgresql_where=sa.text("source_run_id IS NOT NULL")
    )
    op.create_index(
        "idx_incidents_synthetic",
        "incidents",
        ["is_synthetic", "synthetic_scenario_id"],
        postgresql_where=sa.text("is_synthetic = true")
    )
    op.create_index(
        "idx_incidents_source_type",
        "incidents",
        ["source_type"]
    )

    # Step 3: Migrate data from sdsr_incidents to incidents
    op.execute("""
        INSERT INTO incidents (
            id, tenant_id, title, severity, status,
            source_run_id, source_type, category, description,
            error_code, error_message, impact_scope, affected_agent_id, affected_count,
            resolved_at, resolved_by, resolution_notes,
            escalated, escalated_at, escalated_to,
            is_synthetic, synthetic_scenario_id,
            trigger_type, started_at, created_at, updated_at
        )
        SELECT
            id, tenant_id, title, severity, status,
            source_run_id, source_type, category, description,
            error_code, error_message, impact_scope, affected_agent_id, affected_count,
            resolved_at, resolved_by, resolution_notes,
            escalated, escalated_at, escalated_to,
            is_synthetic, synthetic_scenario_id,
            'run_failure', created_at, created_at, updated_at
        FROM sdsr_incidents
        ON CONFLICT (id) DO NOTHING
    """)

    # Step 4: Drop sdsr_incidents table (data now in incidents)
    # Use IF EXISTS for indexes since they may not exist if table was created manually
    op.execute("DROP INDEX IF EXISTS idx_sdsr_incidents_tenant_severity_status")
    op.execute("DROP INDEX IF EXISTS idx_sdsr_incidents_tenant_status_created")
    op.execute("DROP INDEX IF EXISTS idx_sdsr_incidents_source_run_tenant")
    op.execute("DROP INDEX IF EXISTS idx_sdsr_incidents_synthetic_scenario")
    op.drop_table("sdsr_incidents")


def downgrade() -> None:
    """Recreate sdsr_incidents table and migrate data back."""

    # Recreate sdsr_incidents table
    op.create_table(
        "sdsr_incidents",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("source_run_id", sa.Text(), nullable=True),
        sa.Column("source_type", sa.Text(), nullable=False, server_default="run"),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.Text(), nullable=False, server_default="OPEN"),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("impact_scope", sa.Text(), nullable=True),
        sa.Column("affected_agent_id", sa.Text(), nullable=True),
        sa.Column("affected_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tenant_id", sa.Text(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.Text(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("escalated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_to", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("synthetic_scenario_id", sa.Text(), nullable=True),
    )

    # Migrate data back from incidents where source_type = 'run_failure'
    op.execute("""
        INSERT INTO sdsr_incidents (
            id, source_run_id, source_type, category, severity, status,
            title, description, error_code, error_message,
            impact_scope, affected_agent_id, affected_count,
            tenant_id, resolved_at, resolved_by, resolution_notes,
            escalated, escalated_at, escalated_to,
            is_synthetic, synthetic_scenario_id, created_at, updated_at
        )
        SELECT
            id, source_run_id, source_type, category, severity, status,
            title, description, error_code, error_message,
            impact_scope, affected_agent_id, affected_count,
            tenant_id, resolved_at, resolved_by, resolution_notes,
            escalated, escalated_at, escalated_to,
            is_synthetic, synthetic_scenario_id, created_at, updated_at
        FROM incidents
        WHERE source_type = 'run_failure'
    """)

    # Recreate indexes
    op.create_index("idx_sdsr_incidents_synthetic_scenario", "sdsr_incidents",
                    ["is_synthetic", "synthetic_scenario_id"])
    op.create_index("idx_sdsr_incidents_source_run_tenant", "sdsr_incidents",
                    ["source_run_id", "tenant_id"])
    op.create_index("idx_sdsr_incidents_tenant_status_created", "sdsr_incidents",
                    ["tenant_id", "status", "created_at"])
    op.create_index("idx_sdsr_incidents_tenant_severity_status", "sdsr_incidents",
                    ["tenant_id", "severity", "status"])

    # Delete migrated rows from incidents
    op.execute("DELETE FROM incidents WHERE source_type = 'run_failure'")

    # Drop SDSR columns from incidents
    op.drop_index("idx_incidents_source_type", "incidents")
    op.drop_index("idx_incidents_synthetic", "incidents")
    op.drop_index("idx_incidents_source_run_id", "incidents")
    op.drop_column("incidents", "synthetic_scenario_id")
    op.drop_column("incidents", "is_synthetic")
    op.drop_column("incidents", "escalated_to")
    op.drop_column("incidents", "escalated_at")
    op.drop_column("incidents", "escalated")
    op.drop_column("incidents", "resolution_notes")
    op.drop_column("incidents", "affected_count")
    op.drop_column("incidents", "affected_agent_id")
    op.drop_column("incidents", "impact_scope")
    op.drop_column("incidents", "error_message")
    op.drop_column("incidents", "error_code")
    op.drop_column("incidents", "description")
    op.drop_column("incidents", "category")
    op.drop_column("incidents", "source_type")
    op.drop_column("incidents", "source_run_id")
