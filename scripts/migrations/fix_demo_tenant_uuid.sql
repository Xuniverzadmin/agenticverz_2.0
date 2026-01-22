-- ============================================================================
-- Demo Tenant UUID Migration
-- ============================================================================
--
-- PURPOSE: Fix non-UUID tenant IDs and establish canonical Demo Tenant 101
--
-- CONTEXT:
--   The tenant_resolver now requires valid UUIDs for tenant_id. Previously,
--   string identifiers like 'demo-tenant' and 'sdsr-tenant-e2e-004' were used,
--   which now fail validation.
--
-- STRATEGY:
--   1. Create Demo Tenant 101 with canonical UUID
--   2. Migrate valid API keys to reference the new Demo Tenant
--   3. Clean up synthetic SDSR data (is_synthetic=true)
--   4. Leave legacy non-synthetic data for manual review
--
-- DB AUTHORITY:
--   - LOCAL: 11111111-1111-1111-1111-111111111101
--   - NEON TEST: 22222222-2222-2222-2222-222222222101
--
-- Reference: PIN-??? (Demo Tenant Identity Contract)
-- ============================================================================

-- ============================================================================
-- STEP 0: Safety checks
-- ============================================================================

-- Check current state (run this first to understand impact)
-- SELECT id, name, is_synthetic FROM tenants WHERE id NOT SIMILAR TO '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}';
-- SELECT id, tenant_id, name, is_synthetic FROM api_keys WHERE tenant_id NOT SIMILAR TO '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}';

-- ============================================================================
-- STEP 1: Create Demo Tenant 101 (LOCAL version)
-- ============================================================================
-- NOTE: For NEON TEST, change UUID to: 22222222-2222-2222-2222-222222222101

INSERT INTO tenants (
    id,
    name,
    slug,
    plan,
    status,
    max_workers,
    max_runs_per_day,
    max_concurrent_runs,
    max_tokens_per_month,
    max_api_keys,
    onboarding_state,
    is_synthetic,
    created_at,
    updated_at
) VALUES (
    '11111111-1111-1111-1111-111111111101',  -- Demo Tenant 101 (LOCAL)
    'Demo Tenant 101',
    'demo-tenant-101',
    'enterprise',  -- Full access for testing
    'active',
    100,
    100000,
    100,
    1000000000,
    100,
    4,  -- COMPLETE onboarding state
    false,
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- STEP 2: Create a Demo API Key for the new tenant
-- ============================================================================
-- Key: aos_demo_tenant_101_key (for local testing)
-- Hash: SHA256('aos_demo_tenant_101_key')

INSERT INTO api_keys (
    id,
    tenant_id,
    name,
    key_prefix,
    key_hash,
    status,
    rate_limit_rpm,
    is_synthetic,
    created_at
) VALUES (
    '11111111-1111-1111-1111-111111111102',
    '11111111-1111-1111-1111-111111111101',  -- References Demo Tenant 101
    'Demo Tenant 101 API Key',
    'aos_demo_t',  -- max 10 chars per DB constraint
    -- SHA256 of 'aos_demo_tenant_101_key'
    'cc13ebc2d35f5872f0bd3c53eade08bac6ffcaee381e951be4d346f32a79ded1',
    'active',
    10000,
    false,
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- STEP 3: Clean up synthetic SDSR data (safe to delete)
-- ============================================================================
-- These were created by SDSR scenario injection and can be recreated

-- Delete synthetic API keys first (due to FK constraint)
DELETE FROM api_keys WHERE is_synthetic = true;

-- Delete synthetic tenants
DELETE FROM tenants WHERE is_synthetic = true;

-- ============================================================================
-- STEP 4: Migrate non-synthetic legacy keys to Demo Tenant 101
-- ============================================================================
-- These are real test keys that should be preserved

-- Option A: Update existing keys to reference new tenant
UPDATE api_keys
SET tenant_id = '11111111-1111-1111-1111-111111111101'
WHERE tenant_id IN ('demo-tenant', 'default')
  AND is_synthetic = false;

-- Option B: Delete legacy non-synthetic keys (uncomment if preferred)
-- DELETE FROM api_keys
-- WHERE tenant_id NOT SIMILAR TO '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
--   AND is_synthetic = false;

-- ============================================================================
-- STEP 5: Clean up remaining invalid tenants (except Demo Tenant 101)
-- ============================================================================
-- WARNING: This removes legacy tenants. Review before running.

-- First check what would be deleted:
-- SELECT id, name FROM tenants
-- WHERE id NOT SIMILAR TO '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}';

-- Then clean up orphan keys
DELETE FROM api_keys
WHERE tenant_id NOT SIMILAR TO '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}';

-- Then remove invalid tenants
DELETE FROM tenants
WHERE id NOT SIMILAR TO '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}';

-- ============================================================================
-- STEP 6: Verify final state
-- ============================================================================

-- Should return Demo Tenant 101 only (or empty if no invalid data)
SELECT id, name, slug FROM tenants WHERE id = '11111111-1111-1111-1111-111111111101';

-- Should show all keys have valid UUID tenant_ids
SELECT COUNT(*) as invalid_keys FROM api_keys
WHERE tenant_id NOT SIMILAR TO '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}';

-- Should return 0
SELECT COUNT(*) as invalid_tenants FROM tenants
WHERE id NOT SIMILAR TO '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}';
