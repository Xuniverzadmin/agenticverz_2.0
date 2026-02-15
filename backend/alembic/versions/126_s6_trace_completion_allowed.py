# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: S6 immutability fix for trace lifecycle completion
# Reference: PIN-193, PIN-194, PIN-405, RunProof gap validation v1

"""S6 trace completion allowed

Revision ID: 126_s6_trace_completion_allowed
Revises: 125_drop_origin_system_id_default
Create Date: 2026-02-10

Purpose:
Allow trace lifecycle updates (status/completed_at/metadata) while preserving
content immutability for aos_traces. This codifies the fix required for
RunProof and trace completion in clean environments.
"""

from alembic import op

# Revision identifiers
revision = "126_s6_trace_completion_allowed"
down_revision = "125_drop_origin_system_id_default"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION reject_trace_update_lifecycle()
        RETURNS TRIGGER AS $$
        BEGIN
            -- S6 LIFECYCLE-AWARE IMMUTABILITY (PIN-193/194 Revised)
            --
            -- Rule: Trace evidence is immutable with respect to CONTENT.
            -- Exceptions:
            --   1) Archival: archived_at NULL → timestamp (one-way)
            --   2) Completion: status/completed_at/metadata updates only

            -- Exception 1: pure archival operation
            IF (
                NEW.archived_at IS DISTINCT FROM OLD.archived_at
                AND OLD.archived_at IS NULL
                AND NEW.archived_at IS NOT NULL
                AND NEW.id = OLD.id
                AND NEW.trace_id = OLD.trace_id
                AND NEW.run_id IS NOT DISTINCT FROM OLD.run_id
                AND NEW.correlation_id IS NOT DISTINCT FROM OLD.correlation_id
                AND NEW.tenant_id IS NOT DISTINCT FROM OLD.tenant_id
                AND NEW.agent_id IS NOT DISTINCT FROM OLD.agent_id
                AND NEW.plan_id IS NOT DISTINCT FROM OLD.plan_id
                AND NEW.seed IS NOT DISTINCT FROM OLD.seed
                AND NEW.frozen_timestamp IS NOT DISTINCT FROM OLD.frozen_timestamp
                AND NEW.root_hash IS NOT DISTINCT FROM OLD.root_hash
                AND NEW.plan_hash IS NOT DISTINCT FROM OLD.plan_hash
                AND NEW.schema_version IS NOT DISTINCT FROM OLD.schema_version
                AND NEW.plan IS NOT DISTINCT FROM OLD.plan
                AND NEW.trace IS NOT DISTINCT FROM OLD.trace
                AND NEW.metadata IS NOT DISTINCT FROM OLD.metadata
                AND NEW.status IS NOT DISTINCT FROM OLD.status
                AND NEW.started_at IS NOT DISTINCT FROM OLD.started_at
                AND NEW.completed_at IS NOT DISTINCT FROM OLD.completed_at
                AND NEW.created_at IS NOT DISTINCT FROM OLD.created_at
                AND NEW.stored_by IS NOT DISTINCT FROM OLD.stored_by
                AND NEW.checksum IS NOT DISTINCT FROM OLD.checksum
                AND NEW.incident_id IS NOT DISTINCT FROM OLD.incident_id
                AND NEW.is_synthetic IS NOT DISTINCT FROM OLD.is_synthetic
                AND NEW.synthetic_scenario_id IS NOT DISTINCT FROM OLD.synthetic_scenario_id
            ) THEN
                RETURN NEW;
            END IF;

            -- Exception 2: lifecycle completion (status/completed_at/metadata only)
            IF (
                NEW.archived_at IS NOT DISTINCT FROM OLD.archived_at
                AND NEW.id = OLD.id
                AND NEW.trace_id = OLD.trace_id
                AND NEW.run_id IS NOT DISTINCT FROM OLD.run_id
                AND NEW.correlation_id IS NOT DISTINCT FROM OLD.correlation_id
                AND NEW.tenant_id IS NOT DISTINCT FROM OLD.tenant_id
                AND NEW.agent_id IS NOT DISTINCT FROM OLD.agent_id
                AND NEW.plan_id IS NOT DISTINCT FROM OLD.plan_id
                AND NEW.seed IS NOT DISTINCT FROM OLD.seed
                AND NEW.frozen_timestamp IS NOT DISTINCT FROM OLD.frozen_timestamp
                AND NEW.root_hash IS NOT DISTINCT FROM OLD.root_hash
                AND NEW.plan_hash IS NOT DISTINCT FROM OLD.plan_hash
                AND NEW.schema_version IS NOT DISTINCT FROM OLD.schema_version
                AND NEW.plan IS NOT DISTINCT FROM OLD.plan
                AND NEW.trace IS NOT DISTINCT FROM OLD.trace
                AND NEW.started_at IS NOT DISTINCT FROM OLD.started_at
                AND NEW.created_at IS NOT DISTINCT FROM OLD.created_at
                AND NEW.stored_by IS NOT DISTINCT FROM OLD.stored_by
                AND NEW.checksum IS NOT DISTINCT FROM OLD.checksum
                AND NEW.incident_id IS NOT DISTINCT FROM OLD.incident_id
                AND NEW.is_synthetic IS NOT DISTINCT FROM OLD.is_synthetic
                AND NEW.synthetic_scenario_id IS NOT DISTINCT FROM OLD.synthetic_scenario_id
            ) THEN
                RETURN NEW;
            END IF;

            RAISE EXCEPTION 'S6_IMMUTABILITY_VIOLATION: aos_traces is immutable. UPDATE rejected for trace_id=%. Only archival (archived_at: NULL -> timestamp) or completion (status/completed_at/metadata only) is permitted.', OLD.trace_id;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        COMMENT ON FUNCTION reject_trace_update_lifecycle() IS
        'S6 Lifecycle-Aware Immutability (PIN-193/194 Revised):
         Trace content is immutable. Allowed UPDATEs:
         1) archived_at NULL → timestamp (archival),
         2) status/completed_at/metadata only (lifecycle completion).
         Blocks all other UPDATEs.';
        """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION reject_trace_update_lifecycle()
        RETURNS TRIGGER AS $$
        BEGIN
            -- S6 LIFECYCLE-AWARE IMMUTABILITY (archival-only)
            IF (
                NEW.archived_at IS DISTINCT FROM OLD.archived_at
                AND OLD.archived_at IS NULL
                AND NEW.archived_at IS NOT NULL
                AND NEW.id = OLD.id
                AND NEW.trace_id = OLD.trace_id
                AND NEW.run_id IS NOT DISTINCT FROM OLD.run_id
                AND NEW.correlation_id IS NOT DISTINCT FROM OLD.correlation_id
                AND NEW.tenant_id IS NOT DISTINCT FROM OLD.tenant_id
                AND NEW.agent_id IS NOT DISTINCT FROM OLD.agent_id
                AND NEW.plan_id IS NOT DISTINCT FROM OLD.plan_id
                AND NEW.seed IS NOT DISTINCT FROM OLD.seed
                AND NEW.frozen_timestamp IS NOT DISTINCT FROM OLD.frozen_timestamp
                AND NEW.root_hash IS NOT DISTINCT FROM OLD.root_hash
                AND NEW.plan_hash IS NOT DISTINCT FROM OLD.plan_hash
                AND NEW.schema_version IS NOT DISTINCT FROM OLD.schema_version
                AND NEW.plan IS NOT DISTINCT FROM OLD.plan
                AND NEW.trace IS NOT DISTINCT FROM OLD.trace
                AND NEW.metadata IS NOT DISTINCT FROM OLD.metadata
                AND NEW.status IS NOT DISTINCT FROM OLD.status
                AND NEW.started_at IS NOT DISTINCT FROM OLD.started_at
                AND NEW.completed_at IS NOT DISTINCT FROM OLD.completed_at
                AND NEW.created_at IS NOT DISTINCT FROM OLD.created_at
                AND NEW.stored_by IS NOT DISTINCT FROM OLD.stored_by
                AND NEW.checksum IS NOT DISTINCT FROM OLD.checksum
                AND NEW.incident_id IS NOT DISTINCT FROM OLD.incident_id
                AND NEW.is_synthetic IS NOT DISTINCT FROM OLD.is_synthetic
                AND NEW.synthetic_scenario_id IS NOT DISTINCT FROM OLD.synthetic_scenario_id
            ) THEN
                RETURN NEW;
            END IF;

            RAISE EXCEPTION 'S6_IMMUTABILITY_VIOLATION: aos_traces is immutable. UPDATE rejected for trace_id=%. Only archival (archived_at: NULL -> timestamp) is permitted.', OLD.trace_id;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        COMMENT ON FUNCTION reject_trace_update_lifecycle() IS
        'S6 Lifecycle-Aware Immutability (PIN-193/194 Revised):
         Trace content is immutable. Archival state transitions permitted.
         Allows: UPDATE archived_at (NULL → timestamp).
         Blocks: All other UPDATEs.';
        """
    )
