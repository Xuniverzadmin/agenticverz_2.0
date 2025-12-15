"""M15.1.1 Simplify SBA SQL Validator

Revision ID: 029_m15_sba_validator
Revises: 028_m15_1_sba_schema
Create Date: 2025-12-14

Simplifies the SQL validation function to check field presence only.
Detailed semantic validation (governance, dependencies, etc.) handled by Python.

This reduces maintenance burden and prevents SQL/Python logic divergence.
"""

revision = '029_m15_sba_validator'
down_revision = '028_m15_1_sba_schema'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    # Simplified validation function - only checks field presence
    # Semantic validation (governance, dependencies) handled by Python
    op.execute("""
        CREATE OR REPLACE FUNCTION agents.validate_agent_sba(
            p_agent_id TEXT
        ) RETURNS TABLE(
            valid BOOLEAN,
            error_code TEXT,
            error_message TEXT
        ) AS $$
        DECLARE
            v_sba JSONB;
            v_missing_fields TEXT[];
        BEGIN
            -- Get agent SBA from registry
            SELECT sba
            INTO v_sba
            FROM agents.agent_registry
            WHERE agent_id = p_agent_id AND enabled = true;

            -- Agent not found
            IF NOT FOUND THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'AGENT_NOT_FOUND'::TEXT,
                    ('Agent not found in registry: ' || p_agent_id)::TEXT;
                RETURN;
            END IF;

            -- No SBA defined
            IF v_sba IS NULL THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_SBA'::TEXT,
                    ('Agent has no SBA schema: ' || p_agent_id)::TEXT;
                RETURN;
            END IF;

            -- Check required cascade elements (presence only)
            v_missing_fields := ARRAY[]::TEXT[];

            IF NOT (v_sba ? 'winning_aspiration') THEN
                v_missing_fields := array_append(v_missing_fields, 'winning_aspiration');
            END IF;

            IF NOT (v_sba ? 'where_to_play') THEN
                v_missing_fields := array_append(v_missing_fields, 'where_to_play');
            END IF;

            IF NOT (v_sba ? 'how_to_win') THEN
                v_missing_fields := array_append(v_missing_fields, 'how_to_win');
            END IF;

            IF NOT (v_sba ? 'capabilities_capacity') THEN
                v_missing_fields := array_append(v_missing_fields, 'capabilities_capacity');
            END IF;

            IF NOT (v_sba ? 'enabling_management_systems') THEN
                v_missing_fields := array_append(v_missing_fields, 'enabling_management_systems');
            END IF;

            -- Return missing fields if any
            IF array_length(v_missing_fields, 1) > 0 THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_FIELD'::TEXT,
                    ('Missing SBA fields: ' || array_to_string(v_missing_fields, ', '))::TEXT;
                RETURN;
            END IF;

            -- Basic presence check passed
            -- Semantic validation (governance, dependencies, etc.) handled by Python
            RETURN QUERY SELECT
                true::BOOLEAN,
                NULL::TEXT,
                NULL::TEXT;
        END;
        $$ LANGUAGE plpgsql;

        COMMENT ON FUNCTION agents.validate_agent_sba(TEXT) IS
            'M15.1.1: Simplified SBA validation - checks field presence only. '
            'Semantic validation (governance, dependencies) handled by Python SBAValidator.';
    """)


def downgrade():
    # Restore original complex validation function
    op.execute("""
        CREATE OR REPLACE FUNCTION agents.validate_agent_sba(
            p_agent_id TEXT
        ) RETURNS TABLE(
            valid BOOLEAN,
            error_code TEXT,
            error_message TEXT
        ) AS $$
        DECLARE
            v_sba JSONB;
            v_sba_version TEXT;
            v_validated BOOLEAN;
        BEGIN
            -- Get agent SBA from registry
            SELECT sba, sba_version, sba_validated
            INTO v_sba, v_sba_version, v_validated
            FROM agents.agent_registry
            WHERE agent_id = p_agent_id AND enabled = true;

            -- Agent not found
            IF NOT FOUND THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'AGENT_NOT_FOUND'::TEXT,
                    ('Agent not found in registry: ' || p_agent_id)::TEXT;
                RETURN;
            END IF;

            -- No SBA defined
            IF v_sba IS NULL THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_SBA'::TEXT,
                    ('Agent has no SBA schema: ' || p_agent_id)::TEXT;
                RETURN;
            END IF;

            -- Check required SBA fields
            IF NOT (v_sba ? 'winning_aspiration') THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_FIELD'::TEXT,
                    'Missing winning_aspiration in SBA'::TEXT;
                RETURN;
            END IF;

            IF NOT (v_sba ? 'where_to_play') THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_FIELD'::TEXT,
                    'Missing where_to_play in SBA'::TEXT;
                RETURN;
            END IF;

            IF NOT (v_sba ? 'how_to_win') THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_FIELD'::TEXT,
                    'Missing how_to_win in SBA'::TEXT;
                RETURN;
            END IF;

            IF NOT (v_sba ? 'capabilities_capacity') THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_FIELD'::TEXT,
                    'Missing capabilities_capacity in SBA'::TEXT;
                RETURN;
            END IF;

            IF NOT (v_sba ? 'enabling_management_systems') THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'MISSING_FIELD'::TEXT,
                    'Missing enabling_management_systems in SBA'::TEXT;
                RETURN;
            END IF;

            -- Check governance is BudgetLLM
            IF (v_sba->'enabling_management_systems'->>'governance') != 'BudgetLLM' THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'GOVERNANCE_REQUIRED'::TEXT,
                    'BudgetLLM governance is required'::TEXT;
                RETURN;
            END IF;

            -- Check tasks not empty
            IF jsonb_array_length(v_sba->'how_to_win'->'tasks') = 0 THEN
                RETURN QUERY SELECT
                    false::BOOLEAN,
                    'EMPTY_TASKS'::TEXT,
                    'how_to_win.tasks cannot be empty'::TEXT;
                RETURN;
            END IF;

            -- All checks passed
            RETURN QUERY SELECT
                true::BOOLEAN,
                NULL::TEXT,
                NULL::TEXT;
        END;
        $$ LANGUAGE plpgsql;
    """)
