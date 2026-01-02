-- =============================================================================
-- RBAC Promotion Test Data Seed
-- =============================================================================
-- Reference: PIN-274 (RBACv2 Promotion via Neon + Synthetic Load)
--
-- Purpose: Seed Neon DB with test tenants, accounts, and teams
--          for RBAC synthetic load testing.
--
-- Usage:
--   PGPASSWORD=... psql -h <neon-host> -U <user> -d nova_aos -f seed_neon_test_data.sql
--
-- IMPORTANT:
--   - Run this ONLY on Neon test database
--   - Do NOT run on production
--   - Test data uses predictable IDs for synthetic load matching
-- =============================================================================

-- Ensure we're not on production (safety check)
DO $$
BEGIN
    IF current_database() NOT LIKE '%test%' AND current_database() NOT LIKE '%dev%' THEN
        RAISE NOTICE 'Warning: Running on non-test database. Proceeding with caution.';
    END IF;
END $$;

-- =============================================================================
-- Test Tenants
-- =============================================================================
-- These tenant IDs must match the TENANTS list in rbac_synthetic_load.py

INSERT INTO tenants (id, name, plan, created_at, updated_at)
VALUES
    ('tenant-alpha', 'Alpha Corp (Test)', 'enterprise', NOW(), NOW()),
    ('tenant-beta', 'Beta Inc (Test)', 'starter', NOW(), NOW()),
    ('tenant-gamma', 'Gamma LLC (Test)', 'professional', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    plan = EXCLUDED.plan,
    updated_at = NOW();

-- =============================================================================
-- Test Accounts
-- =============================================================================
-- Each tenant has a main account

INSERT INTO accounts (id, tenant_id, name, created_at, updated_at)
VALUES
    ('acct-alpha-1', 'tenant-alpha', 'Alpha Main Account', NOW(), NOW()),
    ('acct-alpha-2', 'tenant-alpha', 'Alpha Secondary Account', NOW(), NOW()),
    ('acct-beta-1', 'tenant-beta', 'Beta Main Account', NOW(), NOW()),
    ('acct-gamma-1', 'tenant-gamma', 'Gamma Main Account', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    updated_at = NOW();

-- =============================================================================
-- Test Teams
-- =============================================================================
-- Teams within accounts for team-level RBAC testing

INSERT INTO teams (id, account_id, name, created_at, updated_at)
VALUES
    ('team-alpha-dev', 'acct-alpha-1', 'Alpha Dev Team', NOW(), NOW()),
    ('team-alpha-ops', 'acct-alpha-1', 'Alpha Ops Team', NOW(), NOW()),
    ('team-alpha-qa', 'acct-alpha-2', 'Alpha QA Team', NOW(), NOW()),
    ('team-beta-main', 'acct-beta-1', 'Beta Main Team', NOW(), NOW()),
    ('team-gamma-engineering', 'acct-gamma-1', 'Gamma Engineering', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    updated_at = NOW();

-- =============================================================================
-- Test Agents (for resource-level tests)
-- =============================================================================

INSERT INTO agents (id, tenant_id, name, description, created_at, updated_at)
VALUES
    ('agent-alpha-1', 'tenant-alpha', 'Alpha Test Agent 1', 'Test agent for RBAC load', NOW(), NOW()),
    ('agent-alpha-2', 'tenant-alpha', 'Alpha Test Agent 2', 'Test agent for RBAC load', NOW(), NOW()),
    ('agent-beta-1', 'tenant-beta', 'Beta Test Agent 1', 'Test agent for RBAC load', NOW(), NOW()),
    ('agent-gamma-1', 'tenant-gamma', 'Gamma Test Agent 1', 'Test agent for RBAC load', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- =============================================================================
-- Test Policies (for policy-level tests)
-- =============================================================================

INSERT INTO policies (id, tenant_id, name, policy_type, config, created_at, updated_at)
VALUES
    ('policy-alpha-rate', 'tenant-alpha', 'Alpha Rate Limit', 'rate_limit', '{"requests_per_minute": 100}'::jsonb, NOW(), NOW()),
    ('policy-beta-budget', 'tenant-beta', 'Beta Budget', 'budget', '{"max_tokens": 10000}'::jsonb, NOW(), NOW()),
    ('policy-gamma-safety', 'tenant-gamma', 'Gamma Safety', 'safety', '{"level": "high"}'::jsonb, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    config = EXCLUDED.config,
    updated_at = NOW();

-- =============================================================================
-- Verification Queries
-- =============================================================================

-- Verify tenant count
SELECT 'Tenants seeded:' AS check, COUNT(*) AS count FROM tenants WHERE id LIKE 'tenant-%';

-- Verify account count
SELECT 'Accounts seeded:' AS check, COUNT(*) AS count FROM accounts WHERE id LIKE 'acct-%';

-- Verify team count
SELECT 'Teams seeded:' AS check, COUNT(*) AS count FROM teams WHERE id LIKE 'team-%';

-- Verify agent count
SELECT 'Agents seeded:' AS check, COUNT(*) AS count FROM agents WHERE id LIKE 'agent-%';

-- Verify policy count
SELECT 'Policies seeded:' AS check, COUNT(*) AS count FROM policies WHERE id LIKE 'policy-%';

-- Summary
SELECT '=== RBAC Test Data Seed Complete ===' AS status;
SELECT 'Ready for synthetic load testing' AS next_step;
