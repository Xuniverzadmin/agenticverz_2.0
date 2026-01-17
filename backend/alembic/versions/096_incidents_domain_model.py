# MIGRATION_CONTRACT:
#   parent: 095_activity_signal_indexes
#   description: Incidents domain model enhancements and v_incidents_o2 view
#   authority: neon

"""
Incidents Domain Model Enhancements

Adds:
1. New columns to incidents table (resolution_method, cost_impact)
2. incident_evidence table for append-only evidence records
3. v_incidents_o2 view for analytics endpoints
4. Indexes for query performance

Reference: docs/architecture/incidents/INCIDENTS_DOMAIN_SQL.md

Revision ID: 096_incidents_domain_model
Revises: 095_activity_signal_indexes
Create Date: 2026-01-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "096_incidents_domain_model"
down_revision = "095_activity_signal_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # 1. Add new columns to incidents table (idempotent)
    # =========================================================================

    # Resolution method: how the incident was resolved
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'incidents' AND column_name = 'resolution_method'
            ) THEN
                ALTER TABLE incidents ADD COLUMN resolution_method VARCHAR(20);
                COMMENT ON COLUMN incidents.resolution_method IS 'auto, manual, rollback';
            END IF;
        END $$;
    """)

    # Cost impact: USD cost prevented or incurred
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'incidents' AND column_name = 'cost_impact'
            ) THEN
                ALTER TABLE incidents ADD COLUMN cost_impact NUMERIC(12, 2);
                COMMENT ON COLUMN incidents.cost_impact IS 'USD impact, null if unknown';
            END IF;
        END $$;
    """)

    # =========================================================================
    # 2. Create incident_evidence table (APPEND-ONLY, idempotent)
    # =========================================================================

    op.execute("""
        CREATE TABLE IF NOT EXISTS incident_evidence (
            id VARCHAR(100) PRIMARY KEY,
            incident_id VARCHAR(100) NOT NULL REFERENCES incidents(id),
            evidence_type VARCHAR(30) NOT NULL,
            recovery_executed BOOLEAN NOT NULL DEFAULT FALSE,
            payload JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        COMMENT ON TABLE incident_evidence IS 'Append-only evidence records for incidents';
    """)

    # =========================================================================
    # 3. Create indexes for incidents table (IF NOT EXISTS)
    # =========================================================================

    # Primary query patterns - use raw SQL for IF NOT EXISTS
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_tenant_status
        ON incidents USING btree (tenant_id, status)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_tenant_category
        ON incidents USING btree (tenant_id, category)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_tenant_severity
        ON incidents USING btree (tenant_id, severity)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_tenant_created
        ON incidents USING btree (tenant_id, created_at)
    """)

    # Resolution analysis (partial index)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_resolution
        ON incidents (tenant_id, resolution_method)
        WHERE resolution_method IS NOT NULL
    """)

    # Cost impact analysis (partial index)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_cost_impact
        ON incidents (tenant_id, cost_impact)
        WHERE cost_impact IS NOT NULL
    """)

    # =========================================================================
    # 4. Create indexes for incident_evidence table (IF NOT EXISTS)
    # =========================================================================

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_incident_evidence_incident
        ON incident_evidence USING btree (incident_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_incident_evidence_type
        ON incident_evidence USING btree (incident_id, evidence_type)
    """)

    # =========================================================================
    # 5. Create indexes for incident_events table (if exists)
    # =========================================================================

    # Check if incident_events exists before creating index
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'incident_events') THEN
                CREATE INDEX IF NOT EXISTS idx_incident_events_timeline
                ON incident_events (incident_id, created_at);
            END IF;
        END $$;
    """)

    # =========================================================================
    # 6. Create v_incidents_o2 view (L5 - derived, stable)
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE VIEW v_incidents_o2 AS
        SELECT
            i.id AS incident_id,
            i.tenant_id,
            i.severity,
            i.status,
            i.category,
            i.source_run_id,
            i.resolution_method,
            i.cost_impact,
            i.resolved_at,
            i.resolved_by,
            i.is_synthetic,
            i.lifecycle_state,
            i.cause_type,
            i.title,
            i.trigger_type,
            i.created_at AS first_seen_at,

            -- Last event timestamp (from incident_events if exists, else created_at)
            COALESCE(
                (SELECT MAX(created_at) FROM incident_events WHERE incident_id = i.id),
                i.created_at
            ) AS last_seen_at,

            -- Evidence count
            (SELECT COUNT(*) FROM incident_evidence WHERE incident_id = i.id) AS evidence_count,

            -- Recovery executed flag (any evidence with recovery)
            EXISTS(
                SELECT 1 FROM incident_evidence
                WHERE incident_id = i.id AND recovery_executed = TRUE
            ) AS recovery_attempted,

            -- Recurrence count (same category in last 30 days)
            (
                SELECT COUNT(*) FROM incidents i2
                WHERE i2.tenant_id = i.tenant_id
                  AND i2.category = i.category
                  AND i2.id != i.id
                  AND i2.created_at >= i.created_at - INTERVAL '30 days'
                  AND i2.created_at < i.created_at
            ) AS recurrence_count,

            -- Time to resolution (if resolved)
            CASE
                WHEN i.resolved_at IS NOT NULL THEN
                    EXTRACT(EPOCH FROM (i.resolved_at - i.created_at)) * 1000
                ELSE NULL
            END AS time_to_resolution_ms,

            -- Topic classification (for filtering)
            CASE
                WHEN i.lifecycle_state = 'ACTIVE' THEN 'ACTIVE'
                WHEN i.lifecycle_state = 'ACKED' THEN 'ACTIVE'
                WHEN i.lifecycle_state = 'RESOLVED' THEN 'RESOLVED'
                WHEN i.status = 'open' THEN 'ACTIVE'
                WHEN i.status = 'acknowledged' THEN 'ACTIVE'
                WHEN i.status = 'resolved' THEN 'RESOLVED'
                ELSE 'UNKNOWN'
            END AS topic

        FROM incidents i
    """)


def downgrade() -> None:
    # Drop view first
    op.execute("DROP VIEW IF EXISTS v_incidents_o2")

    # Drop incident_events index if created
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_incident_events_timeline') THEN
                DROP INDEX idx_incident_events_timeline;
            END IF;
        END $$;
    """)

    # Drop incident_evidence indexes
    op.drop_index("idx_incident_evidence_type", table_name="incident_evidence")
    op.drop_index("idx_incident_evidence_incident", table_name="incident_evidence")

    # Drop incident_evidence table
    op.drop_table("incident_evidence")

    # Drop incidents indexes
    op.drop_index("idx_incidents_cost_impact", table_name="incidents")
    op.drop_index("idx_incidents_resolution", table_name="incidents")
    op.drop_index("idx_incidents_tenant_created", table_name="incidents")
    op.drop_index("idx_incidents_tenant_severity", table_name="incidents")
    op.drop_index("idx_incidents_tenant_category", table_name="incidents")
    op.drop_index("idx_incidents_tenant_status", table_name="incidents")

    # Drop new columns
    op.drop_column("incidents", "cost_impact")
    op.drop_column("incidents", "resolution_method")
