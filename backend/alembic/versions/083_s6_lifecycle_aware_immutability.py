# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: migration
#   Execution: sync
# Role: S6 lifecycle-aware immutability (PIN-193/194 revision)
# Reference: PIN-193, PIN-194, PIN-405

"""S6 lifecycle-aware immutability

Revision ID: 083_s6_lifecycle_aware_immutability
Revises: 082_governance_taxonomy_tables
Create Date: 2026-01-12

S6 Invariant (Revised, Authoritative):
  Trace evidence is immutable with respect to CONTENT and SEMANTICS.
  Lifecycle state transitions that do not alter content are permitted.

This migration replaces the coarse S6 triggers with lifecycle-aware versions:
- Forbidden: Any UPDATE that alters evidentiary content
- Allowed: UPDATE archived_at from NULL to timestamp (one-way archival)

Design Invariants:
- Content immutability is preserved
- Lifecycle transitions (archival) are permitted
- No un-archive (NULL → timestamp only)
- No DELETE (unchanged from original S6)
"""

from alembic import op

# Revision identifiers
revision = "083_s6_lifecycle_aware_immutability"
down_revision = "082_governance_taxonomy_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # REPLACE aos_traces TRIGGER (Lifecycle-aware)
    # ==========================================================================
    # Drop existing trigger and function (handle different trigger names)
    op.execute("DROP TRIGGER IF EXISTS prevent_trace_update ON aos_traces")
    op.execute("DROP TRIGGER IF EXISTS enforce_trace_immutability ON aos_traces")
    op.execute("DROP FUNCTION IF EXISTS reject_trace_update() CASCADE")

    # Create new lifecycle-aware trigger function for aos_traces
    # Schema: id, trace_id, run_id, correlation_id, tenant_id, agent_id, plan_id,
    #         seed, frozen_timestamp, root_hash, plan_hash, schema_version,
    #         plan, trace, metadata, status, started_at, completed_at, created_at,
    #         stored_by, checksum, incident_id, is_synthetic, synthetic_scenario_id, archived_at
    op.execute("""
        CREATE OR REPLACE FUNCTION reject_trace_update_lifecycle()
        RETURNS TRIGGER AS $$
        BEGIN
            -- S6 LIFECYCLE-AWARE IMMUTABILITY (PIN-193/194 Revised)
            --
            -- Rule: Trace evidence is immutable with respect to CONTENT.
            -- Exception: Lifecycle state transitions (archival) are permitted.
            --
            -- Allowed UPDATE: archived_at (NULL → timestamp, one-way only)
            -- Forbidden UPDATE: Any content field

            -- Check if this is a pure archival operation
            IF (
                -- Only archived_at is changing
                NEW.archived_at IS DISTINCT FROM OLD.archived_at
                -- One-way: NULL → timestamp only (no un-archive)
                AND OLD.archived_at IS NULL
                AND NEW.archived_at IS NOT NULL
                -- All content fields are unchanged
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
                -- Allow archival operation
                RETURN NEW;
            END IF;

            -- Block all other updates
            RAISE EXCEPTION 'S6_IMMUTABILITY_VIOLATION: aos_traces is immutable. UPDATE rejected for trace_id=%. Only archival (archived_at: NULL -> timestamp) is permitted.', OLD.trace_id;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create new trigger
    op.execute("""
        CREATE TRIGGER prevent_trace_update
        BEFORE UPDATE ON aos_traces
        FOR EACH ROW
        EXECUTE FUNCTION reject_trace_update_lifecycle();
    """)

    # ==========================================================================
    # REPLACE aos_trace_steps TRIGGER (Lifecycle-aware)
    # ==========================================================================
    # Drop existing trigger and function (handle different trigger names)
    op.execute("DROP TRIGGER IF EXISTS prevent_trace_step_update ON aos_trace_steps")
    op.execute("DROP TRIGGER IF EXISTS enforce_trace_step_immutability ON aos_trace_steps")
    op.execute("DROP FUNCTION IF EXISTS reject_trace_step_update() CASCADE")

    # Create new lifecycle-aware trigger function for aos_trace_steps
    # Schema: id, trace_id, step_index, skill_id, skill_name, params, status,
    #         outcome_category, outcome_code, outcome_data, cost_cents, duration_ms,
    #         retry_count, input_hash, output_hash, rng_state_before, idempotency_key,
    #         replay_behavior, timestamp, source, level, is_synthetic, synthetic_scenario_id, archived_at
    op.execute("""
        CREATE OR REPLACE FUNCTION reject_trace_step_update_lifecycle()
        RETURNS TRIGGER AS $$
        BEGIN
            -- S6 LIFECYCLE-AWARE IMMUTABILITY (PIN-193/194 Revised)
            --
            -- Rule: Trace step evidence is immutable with respect to CONTENT.
            -- Exception: Lifecycle state transitions (archival) are permitted.
            --
            -- Allowed UPDATE: archived_at (NULL → timestamp, one-way only)
            -- Forbidden UPDATE: Any content field

            -- Check if this is a pure archival operation
            IF (
                -- Only archived_at is changing
                NEW.archived_at IS DISTINCT FROM OLD.archived_at
                -- One-way: NULL → timestamp only (no un-archive)
                AND OLD.archived_at IS NULL
                AND NEW.archived_at IS NOT NULL
                -- All content fields are unchanged
                AND NEW.id = OLD.id
                AND NEW.trace_id IS NOT DISTINCT FROM OLD.trace_id
                AND NEW.step_index IS NOT DISTINCT FROM OLD.step_index
                AND NEW.skill_id IS NOT DISTINCT FROM OLD.skill_id
                AND NEW.skill_name IS NOT DISTINCT FROM OLD.skill_name
                AND NEW.params IS NOT DISTINCT FROM OLD.params
                AND NEW.status IS NOT DISTINCT FROM OLD.status
                AND NEW.outcome_category IS NOT DISTINCT FROM OLD.outcome_category
                AND NEW.outcome_code IS NOT DISTINCT FROM OLD.outcome_code
                AND NEW.outcome_data IS NOT DISTINCT FROM OLD.outcome_data
                AND NEW.cost_cents IS NOT DISTINCT FROM OLD.cost_cents
                AND NEW.duration_ms IS NOT DISTINCT FROM OLD.duration_ms
                AND NEW.retry_count IS NOT DISTINCT FROM OLD.retry_count
                AND NEW.input_hash IS NOT DISTINCT FROM OLD.input_hash
                AND NEW.output_hash IS NOT DISTINCT FROM OLD.output_hash
                AND NEW.rng_state_before IS NOT DISTINCT FROM OLD.rng_state_before
                AND NEW.idempotency_key IS NOT DISTINCT FROM OLD.idempotency_key
                AND NEW.replay_behavior IS NOT DISTINCT FROM OLD.replay_behavior
                AND NEW.timestamp IS NOT DISTINCT FROM OLD.timestamp
                AND NEW.source IS NOT DISTINCT FROM OLD.source
                AND NEW.level IS NOT DISTINCT FROM OLD.level
                AND NEW.is_synthetic IS NOT DISTINCT FROM OLD.is_synthetic
                AND NEW.synthetic_scenario_id IS NOT DISTINCT FROM OLD.synthetic_scenario_id
            ) THEN
                -- Allow archival operation
                RETURN NEW;
            END IF;

            -- Block all other updates
            RAISE EXCEPTION 'S6_IMMUTABILITY_VIOLATION: aos_trace_steps is immutable. UPDATE rejected for step_index=% trace_id=%. Only archival (archived_at: NULL -> timestamp) is permitted.', OLD.step_index, OLD.trace_id;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create new trigger
    op.execute("""
        CREATE TRIGGER prevent_trace_step_update
        BEFORE UPDATE ON aos_trace_steps
        FOR EACH ROW
        EXECUTE FUNCTION reject_trace_step_update_lifecycle();
    """)

    # Add comment documenting the S6 revision
    op.execute("""
        COMMENT ON FUNCTION reject_trace_update_lifecycle() IS
        'S6 Lifecycle-Aware Immutability (PIN-193/194 Revised):
         Trace content is immutable. Archival state transitions permitted.
         Allows: UPDATE archived_at (NULL → timestamp).
         Blocks: All other UPDATEs.';
    """)

    op.execute("""
        COMMENT ON FUNCTION reject_trace_step_update_lifecycle() IS
        'S6 Lifecycle-Aware Immutability (PIN-193/194 Revised):
         Trace step content is immutable. Archival state transitions permitted.
         Allows: UPDATE archived_at (NULL → timestamp).
         Blocks: All other UPDATEs.';
    """)


def downgrade() -> None:
    # ==========================================================================
    # RESTORE ORIGINAL aos_traces TRIGGER (Coarse immutability)
    # ==========================================================================
    op.execute("DROP TRIGGER IF EXISTS prevent_trace_update ON aos_traces")
    op.execute("DROP FUNCTION IF EXISTS reject_trace_update_lifecycle()")

    # Restore original coarse trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION reject_trace_update()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'S6_IMMUTABILITY_VIOLATION: aos_traces is immutable. UPDATE rejected for trace_id=%', OLD.trace_id;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER prevent_trace_update
        BEFORE UPDATE ON aos_traces
        FOR EACH ROW
        EXECUTE FUNCTION reject_trace_update();
    """)

    # ==========================================================================
    # RESTORE ORIGINAL aos_trace_steps TRIGGER (Coarse immutability)
    # ==========================================================================
    op.execute("DROP TRIGGER IF EXISTS prevent_trace_step_update ON aos_trace_steps")
    op.execute("DROP FUNCTION IF EXISTS reject_trace_step_update_lifecycle()")

    # Restore original coarse trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION reject_trace_step_update()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'S6_IMMUTABILITY_VIOLATION: aos_trace_steps is immutable. UPDATE rejected for step_index=% trace_id=%', OLD.step_index, OLD.trace_id;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER prevent_trace_step_update
        BEFORE UPDATE ON aos_trace_steps
        FOR EACH ROW
        EXECUTE FUNCTION reject_trace_step_update();
    """)
