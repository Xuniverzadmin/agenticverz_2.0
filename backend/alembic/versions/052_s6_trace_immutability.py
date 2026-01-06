"""S6: Trace immutability enforcement

Revision ID: 052_s6_trace_immutability
Revises: 051_s4_run_failures
Create Date: 2025-12-26

FROZEN: 2025-12-26
DO NOT EDIT THIS MIGRATION IN PLACE.
Any changes to trace immutability rules require a NEW migration (053+).
See PIN-198 CONSTITUTIONAL NOTICE.

Phase A.5 - S6 Trace Integrity Truth
Enforces AC-3 (Immutability) from PIN-198:
- Trace entries are append-only
- No UPDATE allowed on aos_trace_steps (after initial insert)
- Only status/completed_at UPDATE allowed on aos_traces (for finalization)
- No DELETE allowed (use archival instead)
- Checksum stored per trace for integrity verification

Related Invariants (LESSONS_ENFORCED.md):
- #13 Trace Ledger Semantics
- #14 Replay Is Observational
- #15 First Truth Wins
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision = "052_s6_trace_immutability"
down_revision = "051_s4_run_failures"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add checksum column for integrity verification
    op.add_column(
        "aos_traces",
        sa.Column("checksum", sa.String(64), nullable=True),
    )

    # 2. Create trigger to reject UPDATE on aos_trace_steps
    op.execute(
        """
        CREATE OR REPLACE FUNCTION reject_trace_step_update()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'S6_IMMUTABILITY_VIOLATION: aos_trace_steps is immutable. UPDATE rejected for step_index=% trace_id=%',
                OLD.step_index, OLD.trace_id;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        DROP TRIGGER IF EXISTS enforce_trace_step_immutability ON aos_trace_steps;
        CREATE TRIGGER enforce_trace_step_immutability
        BEFORE UPDATE ON aos_trace_steps
        FOR EACH ROW
        EXECUTE FUNCTION reject_trace_step_update();
    """
    )

    # 3. Create trigger to restrict UPDATE on aos_traces (only allow status/completed_at changes)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION restrict_trace_update()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Only allow updates to status, completed_at, and metadata (for replay metadata)
            -- All other fields must remain unchanged
            IF OLD.trace_id != NEW.trace_id OR
               OLD.run_id != NEW.run_id OR
               OLD.correlation_id != NEW.correlation_id OR
               OLD.tenant_id != NEW.tenant_id OR
               (OLD.agent_id IS DISTINCT FROM NEW.agent_id AND OLD.agent_id IS NOT NULL) OR
               OLD.plan::text != NEW.plan::text OR
               OLD.trace::text != NEW.trace::text OR
               OLD.root_hash != NEW.root_hash OR
               OLD.created_at != NEW.created_at THEN
                RAISE EXCEPTION 'S6_IMMUTABILITY_VIOLATION: aos_traces is immutable except for status/completed_at. Attempted change to protected field for trace_id=%',
                    OLD.trace_id;
                RETURN NULL;
            END IF;

            -- Allow the update (only status/completed_at/metadata changed)
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        DROP TRIGGER IF EXISTS enforce_trace_immutability ON aos_traces;
        CREATE TRIGGER enforce_trace_immutability
        BEFORE UPDATE ON aos_traces
        FOR EACH ROW
        EXECUTE FUNCTION restrict_trace_update();
    """
    )

    # 4. Create trigger to reject DELETE on aos_trace_steps (only cascade from traces allowed)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION reject_trace_step_delete()
        RETURNS TRIGGER AS $$
        DECLARE
            parent_exists boolean;
        BEGIN
            -- Check if parent trace still exists (cascade delete is allowed)
            SELECT EXISTS(SELECT 1 FROM aos_traces WHERE trace_id = OLD.trace_id) INTO parent_exists;

            IF parent_exists THEN
                RAISE EXCEPTION 'S6_IMMUTABILITY_VIOLATION: aos_trace_steps direct DELETE not allowed. Use archival. step_index=% trace_id=%',
                    OLD.step_index, OLD.trace_id;
                RETURN NULL;
            END IF;

            -- Cascade delete from parent is allowed
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        DROP TRIGGER IF EXISTS enforce_trace_step_delete_restriction ON aos_trace_steps;
        CREATE TRIGGER enforce_trace_step_delete_restriction
        BEFORE DELETE ON aos_trace_steps
        FOR EACH ROW
        EXECUTE FUNCTION reject_trace_step_delete();
    """
    )

    # 5. Create trigger to reject DELETE on aos_traces (must use archival instead)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION reject_trace_delete()
        RETURNS TRIGGER AS $$
        DECLARE
            archived boolean;
        BEGIN
            -- Check if this trace exists in archive (archival process is allowed)
            SELECT EXISTS(SELECT 1 FROM aos_traces_archive WHERE trace_id = OLD.trace_id) INTO archived;

            IF NOT archived THEN
                RAISE EXCEPTION 'S6_IMMUTABILITY_VIOLATION: aos_traces direct DELETE not allowed. Archive first using cleanup_old_traces(). trace_id=%',
                    OLD.trace_id;
                RETURN NULL;
            END IF;

            -- Delete after archival is allowed
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        DROP TRIGGER IF EXISTS enforce_trace_delete_restriction ON aos_traces;
        CREATE TRIGGER enforce_trace_delete_restriction
        BEFORE DELETE ON aos_traces
        FOR EACH ROW
        EXECUTE FUNCTION reject_trace_delete();
    """
    )

    # 6. Add index on checksum for integrity verification
    op.create_index("idx_aos_traces_checksum", "aos_traces", ["checksum"])


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS enforce_trace_step_immutability ON aos_trace_steps;")
    op.execute("DROP TRIGGER IF EXISTS enforce_trace_immutability ON aos_traces;")
    op.execute("DROP TRIGGER IF EXISTS enforce_trace_step_delete_restriction ON aos_trace_steps;")
    op.execute("DROP TRIGGER IF EXISTS enforce_trace_delete_restriction ON aos_traces;")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS reject_trace_step_update();")
    op.execute("DROP FUNCTION IF EXISTS restrict_trace_update();")
    op.execute("DROP FUNCTION IF EXISTS reject_trace_step_delete();")
    op.execute("DROP FUNCTION IF EXISTS reject_trace_delete();")

    # Drop checksum column
    op.drop_index("idx_aos_traces_checksum", "aos_traces")
    op.drop_column("aos_traces", "checksum")
