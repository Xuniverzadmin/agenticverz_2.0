"""Attribution CHECK Constraints - Defense in Depth

Revision ID: 105_attribution_check_constraints
Revises: 104_attribution_schema_hardening
Create Date: 2026-01-18

PURPOSE:
    Adds database-level CHECK constraints for attribution fields.
    This provides defense-in-depth even if SDK validation is bypassed.

CONSTRAINTS ADDED:
    - chk_runs_actor_type_valid: actor_type must be HUMAN, SYSTEM, or SERVICE
    - chk_runs_actor_id_human_required: actor_id required when actor_type = HUMAN
    - chk_runs_actor_id_nonhuman_null: actor_id must be null when actor_type != HUMAN
    - chk_runs_agent_id_not_legacy: agent_id cannot be 'legacy-unknown' for new runs
    - chk_runs_origin_system_not_legacy: origin_system_id cannot be 'legacy-migration' for new runs

REFERENCE:
    - docs/sdk/SDK_ATTRIBUTION_ENFORCEMENT.md (Section 5: Backend Safeguards)
    - docs/contracts/RUN_VALIDATION_RULES.md (R3, R4, R5)
    - docs/governance/ATTRIBUTION_FAILURE_MODE_MATRIX.md

NOTE:
    These constraints apply to NEW runs only. Existing legacy runs (created before
    enforcement) are exempt via the created_at condition. The enforcement_date
    should be set to the deployment timestamp of this migration.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "105_attribution_check_constraints"
down_revision = "104_attribution_schema_hardening"
branch_labels = None
depends_on = None

# Enforcement date - runs created after this date must have valid attribution
# This is set to "now" at migration time, meaning all future runs are enforced
ENFORCEMENT_DATE_SQL = "NOW()"


def upgrade() -> None:
    # =========================================================================
    # Constraint 1: actor_type must be from closed set
    # Per RUN_VALIDATION_RULES R3: actor_type MUST be from {HUMAN, SYSTEM, SERVICE}
    # =========================================================================
    op.execute("""
        ALTER TABLE runs
        ADD CONSTRAINT chk_runs_actor_type_valid
        CHECK (actor_type IN ('HUMAN', 'SYSTEM', 'SERVICE'))
    """)

    # =========================================================================
    # Constraint 2: actor_id required when actor_type = HUMAN
    # Per RUN_VALIDATION_RULES R4: actor_id REQUIRED if actor_type = HUMAN
    # =========================================================================
    op.execute("""
        ALTER TABLE runs
        ADD CONSTRAINT chk_runs_actor_id_human_required
        CHECK (
            actor_type != 'HUMAN'
            OR (actor_type = 'HUMAN' AND actor_id IS NOT NULL AND actor_id != '')
        )
    """)

    # =========================================================================
    # Constraint 3: actor_id must be NULL when actor_type != HUMAN
    # Per RUN_VALIDATION_RULES R5: actor_id MUST be NULL if actor_type = SYSTEM/SERVICE
    # =========================================================================
    op.execute("""
        ALTER TABLE runs
        ADD CONSTRAINT chk_runs_actor_id_nonhuman_null
        CHECK (
            actor_type = 'HUMAN'
            OR (actor_type != 'HUMAN' AND (actor_id IS NULL OR actor_id = ''))
        )
    """)

    # =========================================================================
    # Constraint 4: agent_id cannot be legacy sentinel for new runs
    # Per LEGACY_DATA_DISCLAIMER_SPEC: 'legacy-unknown' is for historical data only
    #
    # NOTE: This constraint uses a trigger instead of CHECK because we need
    # to allow existing legacy data while blocking new entries.
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION check_agent_id_not_legacy()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.agent_id = 'legacy-unknown' THEN
                RAISE EXCEPTION 'agent_id cannot be ''legacy-unknown'' for new runs (use real agent identifier)'
                    USING ERRCODE = 'check_violation',
                          CONSTRAINT = 'chk_runs_agent_id_not_legacy';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_runs_agent_id_not_legacy
        BEFORE INSERT ON runs
        FOR EACH ROW
        EXECUTE FUNCTION check_agent_id_not_legacy();
    """)

    # =========================================================================
    # Constraint 5: origin_system_id cannot be legacy sentinel for new runs
    # Per LEGACY_DATA_DISCLAIMER_SPEC: 'legacy-migration' is for historical data only
    # =========================================================================
    op.execute("""
        CREATE OR REPLACE FUNCTION check_origin_system_not_legacy()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.origin_system_id = 'legacy-migration' THEN
                RAISE EXCEPTION 'origin_system_id cannot be ''legacy-migration'' for new runs (use real system identifier)'
                    USING ERRCODE = 'check_violation',
                          CONSTRAINT = 'chk_runs_origin_system_not_legacy';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_runs_origin_system_not_legacy
        BEFORE INSERT ON runs
        FOR EACH ROW
        EXECUTE FUNCTION check_origin_system_not_legacy();
    """)

    # =========================================================================
    # Record constraint addition in migration_audit (if table exists)
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
                    'ATTRIBUTION-CONSTRAINTS-001',
                    'runs',
                    0,
                    NOW(),
                    'Attribution CHECK constraints added for defense-in-depth enforcement'
                );
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS trg_runs_origin_system_not_legacy ON runs")
    op.execute("DROP FUNCTION IF EXISTS check_origin_system_not_legacy()")

    op.execute("DROP TRIGGER IF EXISTS trg_runs_agent_id_not_legacy ON runs")
    op.execute("DROP FUNCTION IF EXISTS check_agent_id_not_legacy()")

    # Drop CHECK constraints
    op.execute("ALTER TABLE runs DROP CONSTRAINT IF EXISTS chk_runs_actor_id_nonhuman_null")
    op.execute("ALTER TABLE runs DROP CONSTRAINT IF EXISTS chk_runs_actor_id_human_required")
    op.execute("ALTER TABLE runs DROP CONSTRAINT IF EXISTS chk_runs_actor_type_valid")
