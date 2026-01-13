"""
PIN-412: Incidents lifecycle normalization

Brings incidents table to domain-admissible state by enforcing:
- Explicit lifecycle (ACTIVE/ACKED/RESOLVED)
- Canonical linkage to LLM Runs (llm_run_id FK)
- Normalized cause semantics (cause_type)
- Indexed, queryable structure for O2 performance

After this migration:
- Incidents domain is eligible for O1-O3 UI design
- No policy linkage yet (explicitly deferred to Phase 2)

Revision ID: 087_incidents_lifecycle_repair
Revises: 086_runs_o2_schema
Create Date: 2026-01-13
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "087_incidents_lifecycle_repair"
down_revision = "086_runs_o2_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # STEP 1 — Add Canonical Lifecycle State
    # =========================================================================
    # Existing status values (open, acknowledged, resolved) are inconsistent
    # and UI-hostile. We add lifecycle_state as the canonical semantic.

    op.add_column(
        "incidents",
        sa.Column(
            "lifecycle_state",
            sa.String(length=16),
            nullable=True,
        ),
    )

    # =========================================================================
    # STEP 2 — Backfill lifecycle_state from legacy status
    # =========================================================================
    # Mapping (LOCKED):
    #   OPEN / open           -> ACTIVE
    #   CLOSED / resolved     -> RESOLVED
    #   acknowledged / ACKED  -> ACKED
    #   (default)             -> ACTIVE

    op.execute("""
        UPDATE incidents
        SET lifecycle_state =
            CASE UPPER(status)
                WHEN 'OPEN' THEN 'ACTIVE'
                WHEN 'CLOSED' THEN 'RESOLVED'
                WHEN 'RESOLVED' THEN 'RESOLVED'
                WHEN 'ACKNOWLEDGED' THEN 'ACKED'
                WHEN 'ACKED' THEN 'ACKED'
                ELSE 'ACTIVE'
            END
    """)

    # =========================================================================
    # STEP 3 — Enforce Lifecycle Constraint
    # =========================================================================
    # After backfill, lock correctness with CHECK constraint

    op.create_check_constraint(
        "ck_incidents_lifecycle_state",
        "incidents",
        "lifecycle_state IN ('ACTIVE','ACKED','RESOLVED')",
    )

    # Make column non-nullable after backfill
    op.alter_column(
        "incidents",
        "lifecycle_state",
        nullable=False,
    )

    # =========================================================================
    # STEP 4 — Add Canonical LLM Run Linkage
    # =========================================================================
    # Incidents must be causally attributable to execution.
    # Legacy source_run_id is NOT removed yet (safe migration).

    op.add_column(
        "incidents",
        sa.Column(
            "llm_run_id",
            sa.String(),
            nullable=True,
        ),
    )

    # Add FK constraint separately (runs table uses string ID)
    op.create_foreign_key(
        "fk_incidents_llm_run_id",
        "incidents",
        "runs",
        ["llm_run_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Backfill from legacy source_run_id (safe best-effort)
    op.execute("""
        UPDATE incidents
        SET llm_run_id = source_run_id
        WHERE source_run_id IS NOT NULL
    """)

    # =========================================================================
    # STEP 5 — Normalize Cause Semantics
    # =========================================================================
    # source_type today is ambiguous. We introduce cause_type as canonical.
    # Allowed values: LLM_RUN, SYSTEM, HUMAN

    op.add_column(
        "incidents",
        sa.Column(
            "cause_type",
            sa.String(length=16),
            nullable=True,
        ),
    )

    # Backfill cause_type (conservative mapping)
    op.execute("""
        UPDATE incidents
        SET cause_type =
            CASE
                WHEN source_run_id IS NOT NULL THEN 'LLM_RUN'
                WHEN source_type = 'system' THEN 'SYSTEM'
                ELSE 'HUMAN'
            END
    """)

    # Enforce constraint
    op.create_check_constraint(
        "ck_incidents_cause_type",
        "incidents",
        "cause_type IN ('LLM_RUN','SYSTEM','HUMAN')",
    )

    # Make non-nullable after backfill
    op.alter_column(
        "incidents",
        "cause_type",
        nullable=False,
    )

    # =========================================================================
    # STEP 6 — Indexing (O2 Performance Gate)
    # =========================================================================
    # These indexes are MANDATORY for list view performance.

    op.create_index(
        "idx_incidents_tenant_lifecycle",
        "incidents",
        ["tenant_id", "lifecycle_state"],
    )

    op.create_index(
        "idx_incidents_tenant_severity",
        "incidents",
        ["tenant_id", "severity"],
    )

    op.create_index(
        "idx_incidents_llm_run",
        "incidents",
        ["llm_run_id"],
    )

    op.create_index(
        "idx_incidents_created_at",
        "incidents",
        ["created_at"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_incidents_created_at", table_name="incidents")
    op.drop_index("idx_incidents_llm_run", table_name="incidents")
    op.drop_index("idx_incidents_tenant_severity", table_name="incidents")
    op.drop_index("idx_incidents_tenant_lifecycle", table_name="incidents")

    # Drop constraints
    op.drop_constraint("ck_incidents_cause_type", "incidents", type_="check")
    op.drop_constraint("ck_incidents_lifecycle_state", "incidents", type_="check")
    op.drop_constraint("fk_incidents_llm_run_id", "incidents", type_="foreignkey")

    # Drop columns
    op.drop_column("incidents", "cause_type")
    op.drop_column("incidents", "llm_run_id")
    op.drop_column("incidents", "lifecycle_state")
