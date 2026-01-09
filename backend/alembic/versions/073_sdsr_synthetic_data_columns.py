# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Add synthetic data columns for SDSR pipeline per PIN-370
# Reference: PIN-370 (Scenario-Driven System Realization)

"""Add is_synthetic and synthetic_scenario_id columns for SDSR

Revision ID: 073_sdsr_synthetic_data_columns
Revises: 072_create_gcl_daily_anchors
Create Date: 2026-01-09

SDSR Pipeline Support (PIN-370):
- Every SDSR-participating table gets is_synthetic + synthetic_scenario_id
- Queries remain identical (no special synthetic handling needed)
- Cleanup is trivial: DELETE WHERE is_synthetic AND synthetic_scenario_id = 'X'
- Promotion: /precus = is_synthetic=true, /cus = is_synthetic=false
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "073_sdsr_synthetic_data_columns"
down_revision = "072_create_gcl_daily_anchors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add synthetic data columns to SDSR-participating tables.

    Tables:
    - runs: Core run tracking
    - tenants: Organization/tenant
    - api_keys: API key storage
    - worker_runs: Worker-specific runs
    - agents: Agent definitions

    Per PIN-370:
    - is_synthetic: Boolean, NOT NULL, default false
    - synthetic_scenario_id: Text, nullable (scenario identifier when synthetic)
    """

    # =========================================================================
    # Table: runs
    # =========================================================================
    op.add_column(
        "runs",
        sa.Column(
            "is_synthetic",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="SDSR: True if created by synthetic scenario injection"
        )
    )
    op.add_column(
        "runs",
        sa.Column(
            "synthetic_scenario_id",
            sa.Text(),
            nullable=True,
            comment="SDSR: Scenario ID (e.g., ACTIVITY-RETRY-001) for traceability"
        )
    )
    # Index for cleanup queries
    op.create_index(
        "idx_runs_synthetic_scenario",
        "runs",
        ["is_synthetic", "synthetic_scenario_id"],
        postgresql_where=sa.text("is_synthetic = true")
    )

    # =========================================================================
    # Table: tenants
    # =========================================================================
    op.add_column(
        "tenants",
        sa.Column(
            "is_synthetic",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="SDSR: True if created by synthetic scenario injection"
        )
    )
    op.add_column(
        "tenants",
        sa.Column(
            "synthetic_scenario_id",
            sa.Text(),
            nullable=True,
            comment="SDSR: Scenario ID for traceability"
        )
    )
    op.create_index(
        "idx_tenants_synthetic_scenario",
        "tenants",
        ["is_synthetic", "synthetic_scenario_id"],
        postgresql_where=sa.text("is_synthetic = true")
    )

    # =========================================================================
    # Table: api_keys
    # =========================================================================
    op.add_column(
        "api_keys",
        sa.Column(
            "is_synthetic",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="SDSR: True if created by synthetic scenario injection"
        )
    )
    op.add_column(
        "api_keys",
        sa.Column(
            "synthetic_scenario_id",
            sa.Text(),
            nullable=True,
            comment="SDSR: Scenario ID for traceability"
        )
    )
    op.create_index(
        "idx_api_keys_synthetic_scenario",
        "api_keys",
        ["is_synthetic", "synthetic_scenario_id"],
        postgresql_where=sa.text("is_synthetic = true")
    )

    # =========================================================================
    # Table: worker_runs
    # =========================================================================
    op.add_column(
        "worker_runs",
        sa.Column(
            "is_synthetic",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="SDSR: True if created by synthetic scenario injection"
        )
    )
    op.add_column(
        "worker_runs",
        sa.Column(
            "synthetic_scenario_id",
            sa.Text(),
            nullable=True,
            comment="SDSR: Scenario ID for traceability"
        )
    )
    op.create_index(
        "idx_worker_runs_synthetic_scenario",
        "worker_runs",
        ["is_synthetic", "synthetic_scenario_id"],
        postgresql_where=sa.text("is_synthetic = true")
    )

    # =========================================================================
    # Table: agents
    # =========================================================================
    op.add_column(
        "agents",
        sa.Column(
            "is_synthetic",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="SDSR: True if created by synthetic scenario injection"
        )
    )
    op.add_column(
        "agents",
        sa.Column(
            "synthetic_scenario_id",
            sa.Text(),
            nullable=True,
            comment="SDSR: Scenario ID for traceability"
        )
    )
    op.create_index(
        "idx_agents_synthetic_scenario",
        "agents",
        ["is_synthetic", "synthetic_scenario_id"],
        postgresql_where=sa.text("is_synthetic = true")
    )


def downgrade() -> None:
    """Remove synthetic data columns from all tables"""

    # agents
    op.drop_index("idx_agents_synthetic_scenario", "agents")
    op.drop_column("agents", "synthetic_scenario_id")
    op.drop_column("agents", "is_synthetic")

    # worker_runs
    op.drop_index("idx_worker_runs_synthetic_scenario", "worker_runs")
    op.drop_column("worker_runs", "synthetic_scenario_id")
    op.drop_column("worker_runs", "is_synthetic")

    # api_keys
    op.drop_index("idx_api_keys_synthetic_scenario", "api_keys")
    op.drop_column("api_keys", "synthetic_scenario_id")
    op.drop_column("api_keys", "is_synthetic")

    # tenants
    op.drop_index("idx_tenants_synthetic_scenario", "tenants")
    op.drop_column("tenants", "synthetic_scenario_id")
    op.drop_column("tenants", "is_synthetic")

    # runs
    op.drop_index("idx_runs_synthetic_scenario", "runs")
    op.drop_column("runs", "synthetic_scenario_id")
    op.drop_column("runs", "is_synthetic")
