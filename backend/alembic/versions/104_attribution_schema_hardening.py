"""Attribution Schema Hardening - Phase 1 & 2

Revision ID: 104_attribution_schema_hardening
Revises: ce967f70c95d
Create Date: 2026-01-18

PURPOSE:
    Implements Attribution Migration Checklist Phase 1 (Schema Hardening) and
    Phase 2 (View Integrity Fix) to enable "By Agent" dimension in LIVE-O5 panel.

PHASE 1 - Schema Hardening:
    - Adds actor_type column (HUMAN | SYSTEM | SERVICE)
    - Adds actor_id column (human identity, nullable)
    - Adds origin_system_id column (originating system identifier)
    - Backfills legacy runs with explicit 'legacy-unknown' markers

PHASE 2 - View Integrity Fix:
    - Updates v_runs_o2 to project agent_id (was missing)
    - Projects new attribution columns: actor_type, actor_id, origin_system_id

CONTRACTS IMPLEMENTED:
    - AOS_SDK_ATTRIBUTION_CONTRACT.md (schema backing)
    - RUN_VALIDATION_RULES.md (R1-R8 structural invariants)
    - SDSR_ATTRIBUTION_INVARIANT.md (view projection requirement)
    - LEGACY_DATA_DISCLAIMER_SPEC.md (legacy marker values)

REFERENCE:
    - docs/migrations/ATTRIBUTION_MIGRATION_CHECKLIST.md
    - docs/architecture/ATTRIBUTION_ARCHITECTURE.md
    - docs/governance/ATTRIBUTION_FAILURE_MODE_MATRIX.md
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "104_attribution_schema_hardening"
down_revision = "ce967f70c95d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # PHASE 1: Schema Hardening - Add Attribution Columns
    # =========================================================================

    # actor_type: HUMAN | SYSTEM | SERVICE (NOT NULL after backfill)
    # Per AOS_SDK_ATTRIBUTION_CONTRACT: actor_type is REQUIRED
    op.add_column(
        "runs",
        sa.Column(
            "actor_type",
            sa.String(20),
            nullable=True,  # Temporarily nullable for backfill
            comment="Actor classification: HUMAN, SYSTEM, or SERVICE"
        )
    )

    # actor_id: Human identity (nullable - only required when actor_type=HUMAN)
    # Per RUN_VALIDATION_RULES R4: actor_id REQUIRED if actor_type=HUMAN
    # Per RUN_VALIDATION_RULES R5: actor_id MUST be NULL if actor_type=SYSTEM
    op.add_column(
        "runs",
        sa.Column(
            "actor_id",
            sa.String(255),
            nullable=True,
            comment="Human actor identity (required for HUMAN, null for SYSTEM)"
        )
    )

    # origin_system_id: Where the run came from (NOT NULL after backfill)
    # Per AOS_SDK_ATTRIBUTION_CONTRACT: origin_system_id is REQUIRED
    op.add_column(
        "runs",
        sa.Column(
            "origin_system_id",
            sa.String(100),
            nullable=True,  # Temporarily nullable for backfill
            comment="Originating system identifier for accountability"
        )
    )

    # =========================================================================
    # PHASE 1: Backfill Legacy Runs with Explicit Markers
    # Per LEGACY_DATA_DISCLAIMER_SPEC: Use explicit non-NULL markers
    # =========================================================================

    # Backfill actor_type for existing runs (conservative: assume SYSTEM)
    op.execute("""
        UPDATE runs
        SET actor_type = 'SYSTEM'
        WHERE actor_type IS NULL
    """)

    # Backfill origin_system_id for existing runs
    op.execute("""
        UPDATE runs
        SET origin_system_id = 'legacy-migration'
        WHERE origin_system_id IS NULL
    """)

    # Mark legacy runs with unknown agent_id
    # Per LEGACY_DATA_DISCLAIMER_SPEC: agent_id = 'legacy-unknown' for historical runs
    op.execute("""
        UPDATE runs
        SET agent_id = 'legacy-unknown'
        WHERE agent_id IS NULL OR agent_id = ''
    """)

    # =========================================================================
    # PHASE 1: Record backfill in migration_audit (if table exists)
    # Note: migration_audit table may not exist in all environments
    # =========================================================================

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'migration_audit') THEN
                INSERT INTO migration_audit (
                    migration_id,
                    table_name,
                    rows_affected,
                    executed_at,
                    description
                ) VALUES (
                    'ATTRIBUTION-BACKFILL-001',
                    'runs',
                    (SELECT COUNT(*) FROM runs WHERE origin_system_id = 'legacy-migration'),
                    NOW(),
                    'Attribution enforcement backfill - legacy runs marked per LEGACY_DATA_DISCLAIMER_SPEC'
                );
            END IF;
        END $$;
    """)

    # =========================================================================
    # PHASE 1: Add NOT NULL constraints (after backfill)
    # =========================================================================

    op.alter_column(
        "runs",
        "actor_type",
        existing_type=sa.String(20),
        nullable=False,
        server_default="SYSTEM"
    )

    op.alter_column(
        "runs",
        "origin_system_id",
        existing_type=sa.String(100),
        nullable=False,
        server_default="legacy-migration"
    )

    # =========================================================================
    # PHASE 1: Add indexes for attribution queries
    # Note: idx_runs_tenant_agent may already exist in some environments
    # =========================================================================

    # Create idx_runs_tenant_agent only if it doesn't exist
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_runs_tenant_agent
        ON runs USING btree (tenant_id, agent_id);
    """)

    # Create actor_type index
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_runs_tenant_actor_type
        ON runs USING btree (tenant_id, actor_type);
    """)

    # =========================================================================
    # PHASE 2: Update v_runs_o2 View to Project Attribution Columns
    # Per SDSR_ATTRIBUTION_INVARIANT: Views MUST project declared dimensions
    # =========================================================================

    # Drop existing view
    op.execute("DROP VIEW IF EXISTS v_runs_o2")

    # Recreate view with all attribution columns
    op.execute("""
        CREATE OR REPLACE VIEW v_runs_o2 AS
        SELECT
            id AS run_id,
            tenant_id,
            project_id,
            is_synthetic,

            -- Attribution fields (SDSR_ATTRIBUTION_INVARIANT requirement)
            agent_id,
            actor_type,
            actor_id,
            origin_system_id,

            -- Origin fields
            source,
            provider_type,

            -- Lifecycle
            state,
            status,
            started_at,
            last_seen_at,
            completed_at,
            duration_ms,

            -- Risk and health
            risk_level,
            latency_bucket,
            evidence_health,
            integrity_status,

            -- Impact signals
            incident_count,
            policy_draft_count,
            policy_violation,

            -- Cost tracking
            input_tokens,
            output_tokens,
            estimated_cost_usd,
            expected_latency_ms,

            -- SDSR traceability
            synthetic_scenario_id
        FROM runs
    """)


def downgrade() -> None:
    # Drop the updated view
    op.execute("DROP VIEW IF EXISTS v_runs_o2")

    # Recreate original view (without attribution columns)
    op.execute("""
        CREATE OR REPLACE VIEW v_runs_o2 AS
        SELECT
            id AS run_id,
            tenant_id,
            project_id,
            is_synthetic,
            source,
            provider_type,
            state,
            status,
            started_at,
            last_seen_at,
            completed_at,
            duration_ms,
            risk_level,
            latency_bucket,
            evidence_health,
            integrity_status,
            incident_count,
            policy_draft_count,
            policy_violation,
            input_tokens,
            output_tokens,
            estimated_cost_usd,
            expected_latency_ms,
            synthetic_scenario_id
        FROM runs
    """)

    # Drop indexes (only actor_type, keep tenant_agent if it existed before)
    op.execute("DROP INDEX IF EXISTS idx_runs_tenant_actor_type")

    # Drop columns (in reverse order)
    op.drop_column("runs", "origin_system_id")
    op.drop_column("runs", "actor_id")
    op.drop_column("runs", "actor_type")
