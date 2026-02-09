# Layer: L6 — Platform (Database Migration)
# Product: system-wide
"""Add FK incidents.source_run_id → runs.id (enforced for new rows)

Revision ID: 123_incidents_source_run_fk
Revises: 122_knowledge_plane_registry
Create Date: 2026-02-09

Context:
- source_run_id is the de facto linkage used for incident writes/reads.
- PIN-412 introduced llm_run_id as canonical, but write paths were not updated.
- This FK enforces the actually-used linkage for new rows.

Notes:
- NOT VALID avoids blocking on legacy rows; validate after backfill if desired.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "123_incidents_source_run_fk"
down_revision = "122_knowledge_plane_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_incidents_source_run_id'
            ) THEN
                ALTER TABLE incidents
                ADD CONSTRAINT fk_incidents_source_run_id
                FOREIGN KEY (source_run_id)
                REFERENCES runs(id)
                NOT VALID;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_incidents_source_run_id'
            ) THEN
                ALTER TABLE incidents
                DROP CONSTRAINT fk_incidents_source_run_id;
            END IF;
        END $$;
        """
    )
