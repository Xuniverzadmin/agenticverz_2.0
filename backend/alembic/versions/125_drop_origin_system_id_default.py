# Layer: L6 — Platform (Database Migration)
# Product: system-wide
# Reference: Run Proof Test Plan v2 (origin_system_id design fix)
"""Drop self-contradictory default on runs.origin_system_id

Revision ID: 125_drop_origin_system_id_default
Revises: 124_prevention_records_run_id
Create Date: 2026-02-09

The runs.origin_system_id column has DEFAULT 'legacy-migration' (migration 104),
but trigger trg_runs_origin_system_not_legacy (migration 105) rejects that value.
This makes the schema self-contradictory: any INSERT omitting origin_system_id
gets the default, which is then rejected by the trigger.

Fix: Drop the default. Column stays NOT NULL + trigger-enforced.
Callers must provide an explicit origin_system_id.
"""

from alembic import op

# revision identifiers
revision = "125_drop_origin_system_id_default"
down_revision = "124_prevention_records_run_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "runs",
        "origin_system_id",
        server_default=None,
    )


def downgrade() -> None:
    op.alter_column(
        "runs",
        "origin_system_id",
        server_default="legacy-migration",
    )
