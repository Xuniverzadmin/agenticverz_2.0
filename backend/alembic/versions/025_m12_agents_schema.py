"""M12 Multi-Agent System Schema

Revision ID: 025_m12_agents_schema
Revises: 024_m11_skill_audit
Create Date: 2025-12-11

Creates the agents schema for M12 Multi-Agent System (AOS).

Tables:
- agents.instances: Running agent instances with heartbeats
- agents.jobs: Parallel job batches with credit tracking
- agents.job_items: Individual work units with SKIP LOCKED claiming
- agents.messages: P2P inbox for agent communication
- agents.invocations: Correlation ID tracking for agent_invoke

Key Design:
- FOR UPDATE SKIP LOCKED for concurrent-safe job item claiming
- Per-item credit reservation with refund on failure
- Correlation ID routing for agent_invoke responses
- Heartbeat-based agent lifecycle management

Based on: PIN-062-m12-multi-agent-system.md
Reuse: M10 distributed_locks (100%), claim pattern (95%), outbox pattern (80%)
"""

revision = '025_m12_agents_schema'
down_revision = '024_m11_skill_audit'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


def upgrade():
    # Create schema
    op.execute("CREATE SCHEMA IF NOT EXISTS agents")

    # 1. Agent instances table - running agents with heartbeats
    op.create_table(
        'instances',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', sa.String(128), nullable=False, index=True),  # Agent type/name
        sa.Column('instance_id', sa.String(128), nullable=False, unique=True),  # Unique instance identifier
        sa.Column('job_id', UUID(as_uuid=True), nullable=True, index=True),  # Associated job if worker
        sa.Column('status', sa.String(32), nullable=False, server_default='starting'),  # starting, running, idle, stopped
        sa.Column('capabilities', JSONB, nullable=True),  # Skills, rate limits, etc.
        sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        schema='agents'
    )

    # 2. Jobs table - parallel work batches
    op.create_table(
        'jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('orchestrator_instance_id', sa.String(128), nullable=False, index=True),
        sa.Column('task', sa.String(256), nullable=False),  # Task name/description
        sa.Column('config', JSONB, nullable=False),  # Job configuration (worker_agent, parallelism, timeout, etc.)
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),  # pending, running, completed, failed, cancelled
        sa.Column('total_items', sa.Integer(), nullable=True),
        sa.Column('completed_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_items', sa.Integer(), nullable=False, server_default='0'),
        # Credit tracking
        sa.Column('credits_reserved', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('credits_spent', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('credits_refunded', sa.Numeric(12, 2), nullable=False, server_default='0'),
        # Tenant isolation
        sa.Column('tenant_id', sa.String(128), nullable=False, server_default='default', index=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        schema='agents'
    )

    # 3. Job items table - individual work units
    op.create_table(
        'job_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('item_index', sa.Integer(), nullable=False),  # Order within job
        sa.Column('input', JSONB, nullable=False),  # Item-specific input data
        sa.Column('output', JSONB, nullable=True),  # Result after completion
        sa.Column('worker_instance_id', sa.String(128), nullable=True, index=True),  # Who claimed it
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),  # pending, claimed, running, completed, failed
        sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        schema='agents'
    )

    # FK constraint for job_items -> jobs
    op.create_foreign_key(
        'fk_job_items_job',
        'job_items', 'jobs',
        ['job_id'], ['id'],
        source_schema='agents',
        referent_schema='agents',
        ondelete='CASCADE'
    )

    # Partial index for fast SKIP LOCKED claim queries
    op.execute("""
        CREATE INDEX idx_job_items_pending
        ON agents.job_items(job_id, item_index)
        WHERE status = 'pending'
    """)

    # 4. Messages table - P2P inbox
    op.create_table(
        'messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('from_instance_id', sa.String(128), nullable=False, index=True),
        sa.Column('to_instance_id', sa.String(128), nullable=False, index=True),
        sa.Column('job_id', UUID(as_uuid=True), nullable=True, index=True),  # Optional job context
        sa.Column('message_type', sa.String(64), nullable=False),  # request, response, broadcast, heartbeat
        sa.Column('payload', JSONB, nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),  # pending, delivered, read
        sa.Column('reply_to_id', UUID(as_uuid=True), nullable=True),  # For request-response patterns
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        schema='agents'
    )

    # Composite index for inbox queries
    op.execute("""
        CREATE INDEX idx_messages_inbox
        ON agents.messages(to_instance_id, status, created_at DESC)
    """)

    # Index for reply lookups (request-response pattern latency fix)
    op.execute("""
        CREATE INDEX idx_messages_reply_to
        ON agents.messages(reply_to_id)
        WHERE reply_to_id IS NOT NULL
    """)

    # 5. Invocations table - agent_invoke correlation tracking
    op.create_table(
        'invocations',
        sa.Column('invoke_id', sa.String(64), primary_key=True),  # Correlation ID
        sa.Column('caller_instance_id', sa.String(128), nullable=False, index=True),
        sa.Column('target_instance_id', sa.String(128), nullable=False, index=True),
        sa.Column('job_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('request_payload', JSONB, nullable=False),
        sa.Column('response_payload', JSONB, nullable=True),
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),  # pending, completed, timeout, failed
        sa.Column('timeout_at', sa.DateTime(timezone=True), nullable=True),  # When to timeout
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        schema='agents'
    )

    # Index for pending invocations (for timeout sweeper)
    op.execute("""
        CREATE INDEX idx_invocations_pending_timeout
        ON agents.invocations(timeout_at)
        WHERE status = 'pending'
    """)

    # 6. Credit system tables

    # Credit balances table - tenant credit tracking
    op.create_table(
        'credit_balances',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(128), nullable=False, unique=True),
        sa.Column('total_credits', sa.Numeric(12, 2), nullable=False, server_default='1000'),  # Initial grant
        sa.Column('reserved_credits', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('spent_credits', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='agents'
    )

    # Credit ledger table - immutable transaction log
    op.create_table(
        'credit_ledger',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', UUID(as_uuid=True), nullable=True, index=True),  # Nullable for pre-job charges
        sa.Column('tenant_id', sa.String(128), nullable=False, index=True),
        sa.Column('operation', sa.String(32), nullable=False),  # reserve, spend, refund, charge
        sa.Column('skill', sa.String(64), nullable=True),  # Skill that triggered the charge
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('context', JSONB, nullable=True),  # Additional context
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='agents'
    )

    # Index for job credit lookups
    op.execute("""
        CREATE INDEX idx_credit_ledger_job_tenant
        ON agents.credit_ledger(job_id, tenant_id)
        WHERE job_id IS NOT NULL
    """)

    # 7. Create helper functions

    # Function to claim next available job item (FOR UPDATE SKIP LOCKED)
    op.execute("""
        CREATE OR REPLACE FUNCTION agents.claim_job_item(
            p_job_id UUID,
            p_worker_instance_id TEXT
        ) RETURNS TABLE(
            id UUID,
            item_index INTEGER,
            input JSONB
        ) AS $$
        BEGIN
            RETURN QUERY
            WITH claimed AS (
                SELECT ji.id
                FROM agents.job_items ji
                WHERE ji.job_id = p_job_id
                  AND ji.status = 'pending'
                ORDER BY ji.item_index ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE agents.job_items
            SET status = 'claimed',
                worker_instance_id = p_worker_instance_id,
                claimed_at = now()
            FROM claimed
            WHERE agents.job_items.id = claimed.id
            RETURNING agents.job_items.id,
                      agents.job_items.item_index,
                      agents.job_items.input;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Function to complete a job item
    op.execute("""
        CREATE OR REPLACE FUNCTION agents.complete_job_item(
            p_item_id UUID,
            p_output JSONB,
            p_success BOOLEAN
        ) RETURNS BOOLEAN AS $$
        DECLARE
            v_job_id UUID;
            v_status TEXT;
        BEGIN
            -- Get current status and job_id
            SELECT job_id, status INTO v_job_id, v_status
            FROM agents.job_items
            WHERE id = p_item_id;

            IF v_status NOT IN ('claimed', 'running') THEN
                RETURN FALSE;
            END IF;

            -- Update item
            UPDATE agents.job_items
            SET status = CASE WHEN p_success THEN 'completed' ELSE 'failed' END,
                output = p_output,
                completed_at = now()
            WHERE id = p_item_id;

            -- Update job counters
            IF p_success THEN
                UPDATE agents.jobs
                SET completed_items = completed_items + 1
                WHERE id = v_job_id;
            ELSE
                UPDATE agents.jobs
                SET failed_items = failed_items + 1
                WHERE id = v_job_id;
            END IF;

            RETURN TRUE;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Function to mark stale agents (no heartbeat)
    op.execute("""
        CREATE OR REPLACE FUNCTION agents.mark_stale_instances(
            p_stale_threshold INTERVAL DEFAULT '60 seconds'
        ) RETURNS INTEGER AS $$
        DECLARE
            v_count INTEGER;
        BEGIN
            UPDATE agents.instances
            SET status = 'stale'
            WHERE status = 'running'
              AND heartbeat_at < now() - p_stale_threshold;

            GET DIAGNOSTICS v_count = ROW_COUNT;
            RETURN v_count;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Function to reclaim items from stale workers
    op.execute("""
        CREATE OR REPLACE FUNCTION agents.reclaim_stale_items() RETURNS INTEGER AS $$
        DECLARE
            v_count INTEGER;
        BEGIN
            UPDATE agents.job_items ji
            SET status = 'pending',
                worker_instance_id = NULL,
                claimed_at = NULL,
                retry_count = retry_count + 1
            FROM agents.instances i
            WHERE ji.worker_instance_id = i.instance_id
              AND i.status = 'stale'
              AND ji.status IN ('claimed', 'running')
              AND ji.retry_count < ji.max_retries;

            GET DIAGNOSTICS v_count = ROW_COUNT;
            RETURN v_count;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # 7. Create views

    # Job progress view
    op.execute("""
        CREATE OR REPLACE VIEW agents.job_progress AS
        SELECT
            j.id,
            j.task,
            j.status,
            j.total_items,
            j.completed_items,
            j.failed_items,
            j.total_items - j.completed_items - j.failed_items AS pending_items,
            CASE
                WHEN j.total_items > 0
                THEN ROUND((j.completed_items::NUMERIC / j.total_items) * 100, 2)
                ELSE 0
            END AS progress_pct,
            j.credits_reserved,
            j.credits_spent,
            j.credits_refunded,
            j.created_at,
            j.started_at,
            j.completed_at,
            EXTRACT(EPOCH FROM (COALESCE(j.completed_at, now()) - j.started_at)) AS duration_seconds
        FROM agents.jobs j;
    """)

    # Active workers view
    op.execute("""
        CREATE OR REPLACE VIEW agents.active_workers AS
        SELECT
            i.id,
            i.agent_id,
            i.instance_id,
            i.job_id,
            i.status,
            i.heartbeat_at,
            now() - i.heartbeat_at AS heartbeat_age,
            i.created_at,
            (SELECT COUNT(*) FROM agents.job_items ji
             WHERE ji.worker_instance_id = i.instance_id
               AND ji.status = 'completed') AS items_completed,
            (SELECT COUNT(*) FROM agents.job_items ji
             WHERE ji.worker_instance_id = i.instance_id
               AND ji.status IN ('claimed', 'running')) AS items_in_progress
        FROM agents.instances i
        WHERE i.status IN ('running', 'idle');
    """)


def downgrade():
    # Drop views
    op.execute("DROP VIEW IF EXISTS agents.active_workers")
    op.execute("DROP VIEW IF EXISTS agents.job_progress")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS agents.reclaim_stale_items()")
    op.execute("DROP FUNCTION IF EXISTS agents.mark_stale_instances(INTERVAL)")
    op.execute("DROP FUNCTION IF EXISTS agents.complete_job_item(UUID, JSONB, BOOLEAN)")
    op.execute("DROP FUNCTION IF EXISTS agents.claim_job_item(UUID, TEXT)")

    # Drop tables (in reverse order due to FK)
    op.drop_table('credit_ledger', schema='agents')
    op.drop_table('credit_balances', schema='agents')
    op.drop_table('invocations', schema='agents')
    op.drop_table('messages', schema='agents')
    op.drop_table('job_items', schema='agents')
    op.drop_table('jobs', schema='agents')
    op.drop_table('instances', schema='agents')

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS agents CASCADE")
