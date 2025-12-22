"""Add M10 Recovery Enhancement tables (input, action, provenance)

Revision ID: 018_m10_recovery_enhancements
Revises: 017_recovery_candidates
Create Date: 2025-12-09

M10 Recovery Suggestion Engine Enhancements:
- suggestion_input: Structured inputs for rule evaluation
- suggestion_action: Action catalog with templates
- suggestion_provenance: Lineage tracking for audit/debugging

Based on comprehensive spec for rule-based recovery evaluation.
"""

from alembic import op

# revision identifiers
revision = "018_m10_recovery_enhancements"
down_revision = "017_recovery_candidates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # 1. Create m10_recovery schema for organization
    # ==========================================================================
    op.execute("CREATE SCHEMA IF NOT EXISTS m10_recovery;")

    # ==========================================================================
    # 2. suggestion_input - Structured inputs for rule evaluation
    # ==========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS m10_recovery.suggestion_input (
            id SERIAL PRIMARY KEY,

            -- Link to recovery candidate
            suggestion_id INT NOT NULL,

            -- Input classification
            input_type TEXT NOT NULL CHECK (input_type IN (
                'error_code', 'error_message', 'stack_trace',
                'skill_context', 'tenant_context', 'historical_pattern'
            )),

            -- Input content
            raw_value TEXT NOT NULL,
            normalized_value TEXT,
            parsed_data JSONB DEFAULT '{}',

            -- Quality scoring
            confidence REAL DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
            weight REAL DEFAULT 1.0 CHECK (weight >= 0),

            -- Metadata
            source TEXT,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,

            -- Foreign key added separately to allow flexible lifecycle
            CONSTRAINT fk_si_suggestion FOREIGN KEY (suggestion_id)
                REFERENCES recovery_candidates(id) ON DELETE CASCADE
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_si_suggestion_id ON m10_recovery.suggestion_input (suggestion_id);
        CREATE INDEX IF NOT EXISTS idx_si_input_type ON m10_recovery.suggestion_input (input_type);
        CREATE INDEX IF NOT EXISTS idx_si_normalized ON m10_recovery.suggestion_input (normalized_value)
            WHERE normalized_value IS NOT NULL;

        COMMENT ON TABLE m10_recovery.suggestion_input IS
            'M10: Structured inputs that contributed to a recovery suggestion';
        COMMENT ON COLUMN m10_recovery.suggestion_input.input_type IS
            'Classification of input source for rule matching';
        COMMENT ON COLUMN m10_recovery.suggestion_input.normalized_value IS
            'Normalized/cleaned version for pattern matching';
        COMMENT ON COLUMN m10_recovery.suggestion_input.weight IS
            'Relative importance of this input in confidence calculation';
    """
    )

    # ==========================================================================
    # 3. suggestion_action - Action catalog with templates
    # ==========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS m10_recovery.suggestion_action (
            id SERIAL PRIMARY KEY,

            -- Action identification
            action_code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT,

            -- Action template
            action_type TEXT NOT NULL CHECK (action_type IN (
                'retry', 'fallback', 'escalate', 'notify',
                'reconfigure', 'rollback', 'manual', 'skip'
            )),
            template JSONB NOT NULL DEFAULT '{}',

            -- Applicability rules (JSON for flexibility)
            applies_to_error_codes TEXT[] DEFAULT '{}',
            applies_to_skills TEXT[] DEFAULT '{}',
            preconditions JSONB DEFAULT '{}',

            -- Effectiveness tracking
            success_rate REAL DEFAULT 0.0 CHECK (success_rate >= 0 AND success_rate <= 1),
            total_applications INT DEFAULT 0,
            successful_applications INT DEFAULT 0,

            -- Configuration
            is_automated BOOLEAN DEFAULT FALSE,
            requires_approval BOOLEAN DEFAULT TRUE,
            priority INT DEFAULT 50 CHECK (priority >= 0 AND priority <= 100),

            -- Lifecycle
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            created_by TEXT,

            -- Versioning for audit
            version INT DEFAULT 1
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_sa_action_code ON m10_recovery.suggestion_action (action_code);
        CREATE INDEX IF NOT EXISTS idx_sa_action_type ON m10_recovery.suggestion_action (action_type);
        CREATE INDEX IF NOT EXISTS idx_sa_active ON m10_recovery.suggestion_action (is_active) WHERE is_active = TRUE;
        CREATE INDEX IF NOT EXISTS idx_sa_priority ON m10_recovery.suggestion_action (priority DESC) WHERE is_active = TRUE;
        CREATE INDEX IF NOT EXISTS idx_sa_error_codes ON m10_recovery.suggestion_action USING GIN (applies_to_error_codes);
        CREATE INDEX IF NOT EXISTS idx_sa_skills ON m10_recovery.suggestion_action USING GIN (applies_to_skills);

        COMMENT ON TABLE m10_recovery.suggestion_action IS
            'M10: Catalog of available recovery actions with templates and effectiveness tracking';
        COMMENT ON COLUMN m10_recovery.suggestion_action.template IS
            'JSON template for action execution (parameters, steps, etc.)';
        COMMENT ON COLUMN m10_recovery.suggestion_action.success_rate IS
            'Historical success rate = successful_applications / total_applications';
        COMMENT ON COLUMN m10_recovery.suggestion_action.is_automated IS
            'Whether this action can be executed without human intervention';
    """
    )

    # ==========================================================================
    # 4. suggestion_provenance - Lineage tracking for audit/debugging
    # ==========================================================================
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS m10_recovery.suggestion_provenance (
            id SERIAL PRIMARY KEY,

            -- Link to suggestion
            suggestion_id INT NOT NULL,

            -- Provenance event
            event_type TEXT NOT NULL CHECK (event_type IN (
                'created', 'input_added', 'rule_evaluated', 'action_selected',
                'confidence_updated', 'approved', 'rejected', 'executed',
                'success', 'failure', 'rolled_back', 'manual_override'
            )),

            -- Event details
            details JSONB NOT NULL DEFAULT '{}',

            -- Rule/Action reference (nullable)
            rule_id TEXT,
            action_id INT REFERENCES m10_recovery.suggestion_action(id),

            -- Scores at this point in time
            confidence_before REAL,
            confidence_after REAL,

            -- Actor (human or system)
            actor TEXT NOT NULL DEFAULT 'system',
            actor_type TEXT NOT NULL DEFAULT 'system' CHECK (actor_type IN ('system', 'human', 'agent')),

            -- Timing
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            duration_ms INT,

            -- Foreign key
            CONSTRAINT fk_sp_suggestion FOREIGN KEY (suggestion_id)
                REFERENCES recovery_candidates(id) ON DELETE CASCADE
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_sp_suggestion_id ON m10_recovery.suggestion_provenance (suggestion_id);
        CREATE INDEX IF NOT EXISTS idx_sp_event_type ON m10_recovery.suggestion_provenance (event_type);
        CREATE INDEX IF NOT EXISTS idx_sp_created_at ON m10_recovery.suggestion_provenance (created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_sp_actor ON m10_recovery.suggestion_provenance (actor);
        CREATE INDEX IF NOT EXISTS idx_sp_rule_id ON m10_recovery.suggestion_provenance (rule_id) WHERE rule_id IS NOT NULL;

        COMMENT ON TABLE m10_recovery.suggestion_provenance IS
            'M10: Complete lineage of how a recovery suggestion was generated and processed';
        COMMENT ON COLUMN m10_recovery.suggestion_provenance.event_type IS
            'Type of provenance event for filtering and analysis';
        COMMENT ON COLUMN m10_recovery.suggestion_provenance.details IS
            'Event-specific details (inputs, outputs, scores, etc.)';
        COMMENT ON COLUMN m10_recovery.suggestion_provenance.rule_id IS
            'Reference to rule that was evaluated (stored as text for flexibility)';
    """
    )

    # ==========================================================================
    # 5. Add columns to recovery_candidates for enhanced tracking
    # ==========================================================================
    op.execute(
        """
        -- Add action reference column
        ALTER TABLE recovery_candidates
        ADD COLUMN IF NOT EXISTS selected_action_id INT
        REFERENCES m10_recovery.suggestion_action(id);

        -- Add rule evaluation metadata
        ALTER TABLE recovery_candidates
        ADD COLUMN IF NOT EXISTS rules_evaluated JSONB DEFAULT '[]';

        -- Add execution tracking
        ALTER TABLE recovery_candidates
        ADD COLUMN IF NOT EXISTS execution_status TEXT
        CHECK (execution_status IS NULL OR execution_status IN (
            'pending', 'executing', 'succeeded', 'failed', 'rolled_back', 'skipped'
        ));

        ALTER TABLE recovery_candidates
        ADD COLUMN IF NOT EXISTS executed_at TIMESTAMPTZ;

        ALTER TABLE recovery_candidates
        ADD COLUMN IF NOT EXISTS execution_result JSONB;

        -- Index for execution status queries
        CREATE INDEX IF NOT EXISTS idx_rc_execution_status ON recovery_candidates (execution_status)
            WHERE execution_status IS NOT NULL;

        COMMENT ON COLUMN recovery_candidates.selected_action_id IS
            'Reference to the selected action from suggestion_action catalog';
        COMMENT ON COLUMN recovery_candidates.rules_evaluated IS
            'List of rules evaluated with scores [{rule_id, score, matched}]';
        COMMENT ON COLUMN recovery_candidates.execution_status IS
            'Status of action execution (if automated/approved)';
    """
    )

    # ==========================================================================
    # 6. Create function for action success rate update
    # ==========================================================================
    op.execute(
        """
        CREATE OR REPLACE FUNCTION m10_recovery.update_action_success_rate()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Update success rate when execution completes
            IF NEW.execution_status IN ('succeeded', 'failed')
               AND NEW.selected_action_id IS NOT NULL THEN

                UPDATE m10_recovery.suggestion_action
                SET
                    total_applications = total_applications + 1,
                    successful_applications = successful_applications +
                        CASE WHEN NEW.execution_status = 'succeeded' THEN 1 ELSE 0 END,
                    success_rate = (successful_applications +
                        CASE WHEN NEW.execution_status = 'succeeded' THEN 1 ELSE 0 END)::REAL
                        / (total_applications + 1)::REAL,
                    updated_at = now()
                WHERE id = NEW.selected_action_id;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        -- Create trigger
        DROP TRIGGER IF EXISTS trg_update_action_success ON recovery_candidates;
        CREATE TRIGGER trg_update_action_success
            AFTER UPDATE OF execution_status ON recovery_candidates
            FOR EACH ROW
            WHEN (OLD.execution_status IS DISTINCT FROM NEW.execution_status)
            EXECUTE FUNCTION m10_recovery.update_action_success_rate();
    """
    )

    # ==========================================================================
    # 7. Seed default actions
    # ==========================================================================
    op.execute(
        """
        INSERT INTO m10_recovery.suggestion_action
            (action_code, name, description, action_type, template,
             applies_to_error_codes, is_automated, requires_approval, priority)
        VALUES
            ('retry_exponential', 'Retry with Exponential Backoff',
             'Retry the operation with exponential backoff and jitter',
             'retry',
             '{"max_retries": 3, "base_delay_ms": 1000, "max_delay_ms": 30000, "jitter": true}',
             ARRAY['TIMEOUT', 'HTTP_5XX', 'CONNECTION_ERROR', 'RATE_LIMITED'],
             TRUE, FALSE, 80),

            ('fallback_model', 'Fallback to Alternative Model',
             'Switch to a fallback LLM model when primary fails',
             'fallback',
             '{"fallback_model": "gpt-4o-mini", "preserve_context": true}',
             ARRAY['BUDGET_EXCEEDED', 'RATE_LIMITED', 'MODEL_UNAVAILABLE'],
             TRUE, FALSE, 70),

            ('circuit_breaker', 'Enable Circuit Breaker',
             'Activate circuit breaker to prevent cascade failures',
             'reconfigure',
             '{"cooldown_seconds": 60, "failure_threshold": 5}',
             ARRAY['HTTP_5XX', 'CONNECTION_ERROR', 'TIMEOUT'],
             TRUE, TRUE, 60),

            ('notify_ops', 'Notify Operations Team',
             'Send alert to operations team for manual review',
             'notify',
             '{"channel": "slack", "priority": "high", "include_context": true}',
             ARRAY['PERMISSION_DENIED', 'CONFIG_ERROR', 'UNKNOWN'],
             TRUE, FALSE, 50),

            ('rollback_state', 'Rollback to Last Checkpoint',
             'Rollback agent state to last known good checkpoint',
             'rollback',
             '{"checkpoint_strategy": "last_successful"}',
             ARRAY['STATE_CORRUPTION', 'CONSISTENCY_ERROR'],
             FALSE, TRUE, 40),

            ('manual_intervention', 'Request Manual Intervention',
             'Flag for human operator review and decision',
             'manual',
             '{"escalation_path": "recovery_reviewer", "sla_hours": 24}',
             ARRAY['UNKNOWN', 'CRITICAL_ERROR'],
             FALSE, TRUE, 30),

            ('skip_task', 'Skip and Continue',
             'Skip the failed task and continue with workflow',
             'skip',
             '{"record_skip": true, "notify": true}',
             ARRAY['NON_CRITICAL', 'OPTIONAL_TASK'],
             TRUE, TRUE, 20)
        ON CONFLICT (action_code) DO NOTHING;
    """
    )

    # ==========================================================================
    # 8. Create view for suggestions with full context
    # ==========================================================================
    op.execute(
        """
        CREATE OR REPLACE VIEW m10_recovery.suggestions_full_context AS
        SELECT
            rc.id,
            rc.failure_match_id,
            rc.suggestion,
            rc.confidence,
            rc.explain,
            rc.decision,
            rc.occurrence_count,
            rc.created_at,
            rc.approved_by_human,
            rc.approved_at,
            rc.execution_status,
            rc.executed_at,
            rc.selected_action_id,
            sa.action_code,
            sa.name as action_name,
            sa.action_type,
            sa.success_rate as action_success_rate,
            (
                SELECT COUNT(*)
                FROM m10_recovery.suggestion_input si
                WHERE si.suggestion_id = rc.id
            ) as input_count,
            (
                SELECT COUNT(*)
                FROM m10_recovery.suggestion_provenance sp
                WHERE sp.suggestion_id = rc.id
            ) as provenance_count
        FROM recovery_candidates rc
        LEFT JOIN m10_recovery.suggestion_action sa ON rc.selected_action_id = sa.id
        ORDER BY rc.created_at DESC;

        COMMENT ON VIEW m10_recovery.suggestions_full_context IS
            'M10: Complete view of suggestions with action and metadata counts';
    """
    )


def downgrade() -> None:
    # Drop views
    op.execute("DROP VIEW IF EXISTS m10_recovery.suggestions_full_context;")

    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS trg_update_action_success ON recovery_candidates;")
    op.execute("DROP FUNCTION IF EXISTS m10_recovery.update_action_success_rate();")

    # Remove columns from recovery_candidates
    op.execute(
        """
        ALTER TABLE recovery_candidates DROP COLUMN IF EXISTS selected_action_id;
        ALTER TABLE recovery_candidates DROP COLUMN IF EXISTS rules_evaluated;
        ALTER TABLE recovery_candidates DROP COLUMN IF EXISTS execution_status;
        ALTER TABLE recovery_candidates DROP COLUMN IF EXISTS executed_at;
        ALTER TABLE recovery_candidates DROP COLUMN IF EXISTS execution_result;
    """
    )

    # Drop tables (in dependency order)
    op.execute("DROP TABLE IF EXISTS m10_recovery.suggestion_provenance;")
    op.execute("DROP TABLE IF EXISTS m10_recovery.suggestion_input;")
    op.execute("DROP TABLE IF EXISTS m10_recovery.suggestion_action;")

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS m10_recovery;")
