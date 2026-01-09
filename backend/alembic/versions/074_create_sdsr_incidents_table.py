# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Create sdsr_incidents table for SDSR Incidents domain per PIN-370
# Reference: PIN-370 (Scenario-Driven System Realization)

"""Create sdsr_incidents table for SDSR Incidents domain

Revision ID: 074_create_sdsr_incidents_table
Revises: 073_sdsr_synthetic_data_columns
Create Date: 2026-01-09

SDSR Incidents Domain (PIN-370):
- Incidents are REACTIVE - created by Incident Engine when runs fail
- Scenarios inject causes (failed runs), backend creates sdsr_incidents
- UI observes sdsr_incidents via PanelContentRegistry, never writes them
- Cross-domain propagation: Run failure → Incident → Policies → Logs
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "074_create_sdsr_incidents"
down_revision = "073_sdsr_synthetic_data_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create sdsr_incidents table for SDSR Incidents domain.

    Per PIN-370 and INCIDENTS-EXEC-FAILURE-001 scenario:
    - source_run_id: Links incident to triggering run
    - category: EXECUTION_FAILURE, POLICY_VIOLATION, etc.
    - severity: LOW, MEDIUM, HIGH, CRITICAL
    - status: OPEN, ACKNOWLEDGED, INVESTIGATING, RESOLVED, CLOSED
    - is_synthetic + synthetic_scenario_id: SDSR traceability
    """

    op.create_table(
        "sdsr_incidents",
        # Primary key
        sa.Column("id", sa.Text(), primary_key=True),

        # Source linkage
        sa.Column("source_run_id", sa.Text(), nullable=True, index=True,
                  comment="Run ID that triggered this incident"),
        sa.Column("source_type", sa.Text(), nullable=False, server_default="run",
                  comment="Source type: run, policy, budget, manual"),

        # Classification
        sa.Column("category", sa.Text(), nullable=False, index=True,
                  comment="EXECUTION_FAILURE, POLICY_VIOLATION, BUDGET_EXCEEDED, etc."),
        sa.Column("severity", sa.Text(), nullable=False, server_default="MEDIUM", index=True,
                  comment="LOW, MEDIUM, HIGH, CRITICAL"),
        sa.Column("status", sa.Text(), nullable=False, server_default="OPEN", index=True,
                  comment="OPEN, ACKNOWLEDGED, INVESTIGATING, RESOLVED, CLOSED"),

        # Details
        sa.Column("title", sa.Text(), nullable=False,
                  comment="Human-readable incident title"),
        sa.Column("description", sa.Text(), nullable=True,
                  comment="Detailed description of the incident"),
        sa.Column("error_code", sa.Text(), nullable=True, index=True,
                  comment="Error code e.g. EXECUTION_TIMEOUT"),
        sa.Column("error_message", sa.Text(), nullable=True,
                  comment="Full error message from source"),

        # Impact assessment
        sa.Column("impact_scope", sa.Text(), nullable=True,
                  comment="Impact: single_run, agent, tenant, system"),
        sa.Column("affected_agent_id", sa.Text(), nullable=True, index=True),
        sa.Column("affected_count", sa.Integer(), nullable=False, server_default="1",
                  comment="Number of affected runs/entities"),

        # Multi-tenancy
        sa.Column("tenant_id", sa.Text(), nullable=False, index=True,
                  comment="Tenant scope"),

        # Resolution
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.Text(), nullable=True,
                  comment="User/system that resolved"),
        sa.Column("resolution_notes", sa.Text(), nullable=True),

        # Escalation
        sa.Column("escalated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_to", sa.Text(), nullable=True,
                  comment="Who was escalated to"),

        # Metadata
        sa.Column("metadata_json", sa.Text(), nullable=True,
                  comment="Additional context as JSON"),

        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()"), index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),

        # SDSR: Synthetic data marking (PIN-370)
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="false",
                  comment="SDSR: True if created during synthetic scenario"),
        sa.Column("synthetic_scenario_id", sa.Text(), nullable=True,
                  comment="SDSR: Scenario ID for traceability"),
    )

    # Index for SDSR cleanup queries
    op.create_index(
        "idx_sdsr_incidents_synthetic_scenario",
        "sdsr_incidents",
        ["is_synthetic", "synthetic_scenario_id"],
        postgresql_where=sa.text("is_synthetic = true")
    )

    # Index for finding sdsr_incidents by run (Incident Engine lookup)
    op.create_index(
        "idx_sdsr_incidents_source_run_tenant",
        "sdsr_incidents",
        ["source_run_id", "tenant_id"]
    )

    # Index for status queries (dashboard)
    op.create_index(
        "idx_sdsr_incidents_tenant_status_created",
        "sdsr_incidents",
        ["tenant_id", "status", "created_at"]
    )

    # Index for severity-based queries (alerting)
    op.create_index(
        "idx_sdsr_incidents_tenant_severity_status",
        "sdsr_incidents",
        ["tenant_id", "severity", "status"]
    )


def downgrade() -> None:
    """Drop sdsr_incidents table"""
    op.drop_index("idx_sdsr_incidents_tenant_severity_status", "sdsr_incidents")
    op.drop_index("idx_sdsr_incidents_tenant_status_created", "sdsr_incidents")
    op.drop_index("idx_sdsr_incidents_source_run_tenant", "sdsr_incidents")
    op.drop_index("idx_sdsr_incidents_synthetic_scenario", "sdsr_incidents")
    op.drop_table("sdsr_incidents")
