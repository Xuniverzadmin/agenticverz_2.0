"""Create recovery_candidates table for M10 Recovery Suggestion Engine

Revision ID: 017_recovery_candidates
Revises: 016_create_failure_pattern_exports
Create Date: 2025-12-08

M10 Recovery Suggestion Engine:
- Stores recovery suggestions with confidence scores
- Tracks human approval workflow
- Supports occurrence counting for pattern learning
- Integrates with failure_matches table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '017_recovery_candidates'
down_revision = '016_failure_pattern_exports'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create recovery_candidates table
    op.execute("""
        CREATE TABLE IF NOT EXISTS recovery_candidates (
            id SERIAL PRIMARY KEY,

            -- Link to failure (unique constraint for idempotent upserts)
            failure_match_id UUID NOT NULL UNIQUE,

            -- Suggestion content
            suggestion TEXT NOT NULL,
            matched_catalog_entry JSONB,
            confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
            explain JSONB DEFAULT '{}',

            -- Creation metadata
            created_by TEXT,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,

            -- Human approval workflow
            approved_by_human TEXT,
            approved_at TIMESTAMPTZ,
            decision TEXT DEFAULT 'pending' CHECK (decision IN ('pending', 'approved', 'rejected')),
            review_note TEXT,

            -- Pattern learning - occurrence tracking
            occurrence_count INT DEFAULT 1 NOT NULL,
            last_occurrence_at TIMESTAMPTZ DEFAULT now() NOT NULL,

            -- Source tracking
            source TEXT,
            error_code TEXT,
            error_signature TEXT,

            -- Timestamps
            updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
        );

        -- Indexes for common query patterns
        CREATE INDEX IF NOT EXISTS idx_rc_decision ON recovery_candidates (decision);
        CREATE INDEX IF NOT EXISTS idx_rc_last_occurrence_at ON recovery_candidates (last_occurrence_at DESC);
        CREATE INDEX IF NOT EXISTS idx_rc_confidence ON recovery_candidates (confidence DESC);
        CREATE INDEX IF NOT EXISTS idx_rc_created_at ON recovery_candidates (created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_rc_error_code ON recovery_candidates (error_code);
        CREATE INDEX IF NOT EXISTS idx_rc_pending ON recovery_candidates (created_at DESC)
            WHERE decision = 'pending';

        -- Add foreign key to failure_matches (soft - doesn't enforce on existing data)
        -- Not adding hard FK to allow flexibility in data lifecycle

        -- Comment
        COMMENT ON TABLE recovery_candidates IS 'M10: Recovery suggestions with confidence scoring and human approval workflow';
        COMMENT ON COLUMN recovery_candidates.failure_match_id IS 'Links to failure_matches.id - unique for idempotent upserts';
        COMMENT ON COLUMN recovery_candidates.confidence IS 'Weighted confidence score (0.0-1.0) based on historical matches';
        COMMENT ON COLUMN recovery_candidates.explain IS 'Scoring provenance: method, matches, occurrences, half_life';
        COMMENT ON COLUMN recovery_candidates.occurrence_count IS 'Number of times this failure pattern was seen';
    """)

    # Create audit table for approval history
    op.execute("""
        CREATE TABLE IF NOT EXISTS recovery_candidates_audit (
            id SERIAL PRIMARY KEY,
            candidate_id INT NOT NULL REFERENCES recovery_candidates(id) ON DELETE CASCADE,
            action TEXT NOT NULL,
            actor TEXT,
            old_decision TEXT,
            new_decision TEXT,
            note TEXT,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_rca_candidate_id ON recovery_candidates_audit (candidate_id);
        CREATE INDEX IF NOT EXISTS idx_rca_created_at ON recovery_candidates_audit (created_at DESC);

        COMMENT ON TABLE recovery_candidates_audit IS 'M10: Immutable audit trail for recovery approval decisions';
    """)

    # Create view for pending candidates with failure context
    op.execute("""
        CREATE OR REPLACE VIEW recovery_candidates_with_context AS
        SELECT
            rc.id,
            rc.failure_match_id,
            rc.suggestion,
            rc.confidence,
            rc.explain,
            rc.decision,
            rc.occurrence_count,
            rc.last_occurrence_at,
            rc.created_at,
            rc.approved_by_human,
            rc.approved_at,
            rc.review_note,
            fm.error_code,
            fm.error_message,
            fm.category,
            fm.severity,
            fm.is_retryable,
            fm.tenant_id,
            fm.skill_id
        FROM recovery_candidates rc
        LEFT JOIN failure_matches fm ON rc.failure_match_id = fm.id::uuid
        ORDER BY rc.created_at DESC;

        COMMENT ON VIEW recovery_candidates_with_context IS 'Recovery candidates joined with failure context for review';
    """)

    # Create function for updating timestamps
    op.execute("""
        CREATE OR REPLACE FUNCTION update_recovery_candidates_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trg_recovery_candidates_updated_at ON recovery_candidates;
        CREATE TRIGGER trg_recovery_candidates_updated_at
            BEFORE UPDATE ON recovery_candidates
            FOR EACH ROW EXECUTE FUNCTION update_recovery_candidates_updated_at();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_recovery_candidates_updated_at ON recovery_candidates;")
    op.execute("DROP FUNCTION IF EXISTS update_recovery_candidates_updated_at();")
    op.execute("DROP VIEW IF EXISTS recovery_candidates_with_context;")
    op.execute("DROP TABLE IF EXISTS recovery_candidates_audit;")
    op.execute("DROP TABLE IF EXISTS recovery_candidates;")
