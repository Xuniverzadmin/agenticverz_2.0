# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: Add interpretation ownership metadata for external responses
# Callers: alembic upgrade
# Allowed Imports: L6 (alembic, sqlalchemy)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-256 Phase E FIX-04

"""
Phase E FIX-04: Interpretation Authority Contract.

Adds external_responses table for tracking raw external data with explicit
interpretation ownership. Adds semantic_owner to state tables.

L3 adapters write raw data to L6. L4 engines interpret and write back.
L5/L2 consumers read L4's interpretation, never interpret raw data.

Reference: PIN-256, PHASE_E_FIX_DESIGN.md
Violations Resolved: VIOLATION-007, VIOLATION-008, VIOLATION-009, VIOLATION-010
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "066_interpretation_ownership"
down_revision = "065_precomputed_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create external_responses table for raw external data with interpretation metadata
    op.create_table(
        "external_responses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Source of external data
        sa.Column(
            "source",
            sa.String(50),
            nullable=False,
            comment="Source: ANTHROPIC, OPENAI, VOYAGEAI, WEBHOOK, OTHER",
        ),
        # Request context
        sa.Column(
            "request_id",
            sa.String(100),
            nullable=True,
            index=True,
            comment="Request ID for correlation",
        ),
        sa.Column(
            "run_id",
            sa.String(100),
            nullable=True,
            index=True,
            comment="Run ID if part of execution",
        ),
        # Raw response (untouched external data)
        sa.Column(
            "raw_response",
            postgresql.JSONB(),
            nullable=False,
            comment="Untouched external response data",
        ),
        # Interpretation ownership
        sa.Column(
            "interpretation_owner",
            sa.String(100),
            nullable=False,
            comment="L4 engine responsible for interpretation",
        ),
        sa.Column(
            "interpretation_contract",
            sa.String(200),
            nullable=True,
            comment="What this data means (contract name)",
        ),
        # Interpreted value (filled by L4 engine)
        sa.Column(
            "interpreted_value",
            postgresql.JSONB(),
            nullable=True,
            comment="Domain-meaningful result from L4 interpretation",
        ),
        sa.Column(
            "interpreted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When L4 engine interpreted this",
        ),
        sa.Column(
            "interpreted_by",
            sa.String(100),
            nullable=True,
            comment="Specific L4 engine instance that interpreted",
        ),
        # Timestamps
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="When raw response was received",
        ),
        # Check constraint for valid sources
        sa.CheckConstraint(
            "source IN ('ANTHROPIC', 'OPENAI', 'VOYAGEAI', 'WEBHOOK', 'OTHER')",
            name="ext_resp_source_valid",
        ),
        comment="Phase E FIX-04: Raw external responses with interpretation ownership",
    )

    # 2. Create indexes for efficient queries
    op.create_index(
        "ix_ext_resp_source",
        "external_responses",
        ["source"],
    )
    op.create_index(
        "ix_ext_resp_interpretation_owner",
        "external_responses",
        ["interpretation_owner"],
    )
    op.create_index(
        "ix_ext_resp_received_at",
        "external_responses",
        ["received_at"],
    )
    # Partial index for uninterpreted responses
    op.create_index(
        "ix_ext_resp_pending",
        "external_responses",
        ["interpretation_owner", "received_at"],
        postgresql_where=sa.text("interpreted_at IS NULL"),
    )

    # 3. Add semantic_owner to state tables (if they exist)
    # These tables track state that needs explicit interpretation authority

    # Check if recovery_candidates table exists before adding column
    # This is a conditional add - if table doesn't exist, skip
    try:
        op.add_column(
            "failure_matches",
            sa.Column(
                "semantic_owner",
                sa.String(100),
                nullable=True,
                server_default="recovery_rule_engine",
                comment="L4 engine with interpretation authority (FIX-04)",
            ),
        )
    except Exception:
        pass  # Table may not exist

    # Add semantic_owner to governance_signals (created in FIX-03)
    op.add_column(
        "governance_signals",
        sa.Column(
            "semantic_owner",
            sa.String(100),
            nullable=True,
            comment="L4 engine with interpretation authority (FIX-04)",
        ),
    )


def downgrade() -> None:
    # 1. Remove semantic_owner from governance_signals
    op.drop_column("governance_signals", "semantic_owner")

    # 2. Remove semantic_owner from failure_matches if it was added
    try:
        op.drop_column("failure_matches", "semantic_owner")
    except Exception:
        pass

    # 3. Drop indexes
    op.drop_index("ix_ext_resp_pending", table_name="external_responses")
    op.drop_index("ix_ext_resp_received_at", table_name="external_responses")
    op.drop_index("ix_ext_resp_interpretation_owner", table_name="external_responses")
    op.drop_index("ix_ext_resp_source", table_name="external_responses")

    # 4. Drop external_responses table
    op.drop_table("external_responses")
