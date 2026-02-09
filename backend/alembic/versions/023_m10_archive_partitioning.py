"""M10 Dead-Letter Archive Partitioning

Revision ID: 023_m10_archive_partitioning
Revises: 022_m10_production_hardening
Create Date: 2025-12-09

**STATUS: DEFERRED (PIN-058)**

This migration is DEFERRED until tables exceed 100K rows.
Current tables have <1K rows - partitioning is premature optimization.

DO NOT apply to production until:
1. dead_letter_archive table exceeds 100K rows
2. replay_log table exceeds 50K rows
3. Query performance degrades measurably

When ready to apply:
    alembic upgrade 023_m10_archive_partitioning

See PIN-058 for rationale on deferring this migration.

---

Original Description:
This migration converts dead_letter_archive to a partitioned table (by month)
for better retention management and query performance.

Features:
- Monthly partitions for dead_letter_archive
- Auto-creation of future partitions (3 months ahead)
- Retention function to drop old partitions
- Maintains all existing data
"""

from alembic import op  # noqa: F401 — required by alembic convention

# revision identifiers
revision = "023_m10_archive_partitioning"
down_revision = "022_m10_production_hardening"
branch_labels = None
depends_on = None


def upgrade():
    # =====================================================================
    # DEFERRED (PIN-058): This migration is a no-op.
    #
    # Partitioning dead_letter_archive and replay_log is deferred until
    # tables exceed 100K rows. The original code also had a schema mismatch
    # with the tables created in migration 022 (different column sets),
    # making the data migration INSERT invalid.
    #
    # When partitioning is needed:
    # 1. Create a NEW migration with the correct schema from 022
    # 2. Reference this revision as down_revision
    # 3. Follow PIN-058 criteria
    # =====================================================================
    pass


def downgrade():
    # No-op: upgrade was deferred (PIN-058), nothing to reverse.
    pass
