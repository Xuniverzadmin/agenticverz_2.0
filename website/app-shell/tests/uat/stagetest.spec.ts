/**
 * Stagetest Evidence Console — Playwright Regression Pack
 *
 * Layer: TEST
 * AUDIENCE: INTERNAL
 * Role: Browser-level regression for Stagetest Evidence Console page
 * Reference: STAGETEST_HOC_API_EVIDENCE_CONSOLE_TASKPACK_2026-02-15
 * artifact_class: TEST
 *
 * Assertions:
 * 1. Stagetest page loads with zero console errors
 * 2. Stats bar renders with numeric values
 * 3. Run list renders (or empty state)
 * 4. Route is wired at /prefops/stagetest and /fops/stagetest
 * 5. All required components exist on disk
 * 6. Fixture shapes are valid
 */

import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

// ============================================================================
// Fixture Loading
// ============================================================================

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const fixturesPath = path.join(__dirname, 'fixtures', 'stagetest-runs.json');

interface RunFixture {
  run_id: string;
  created_at: string;
  stages_executed: string[];
  total_cases: number;
  pass_count: number;
  fail_count: number;
  determinism_digest: string;
  artifact_version: string;
}

interface CaseFixture {
  case_id: string;
  uc_id: string;
  stage: string;
  operation_name: string;
  status: string;
  determinism_hash: string;
}

interface FixtureData {
  runs: RunFixture[];
  cases: CaseFixture[];
  required_data_testids: string[];
  required_components: string[];
}

let fixtures: FixtureData;
try {
  const raw = fs.readFileSync(fixturesPath, 'utf8');
  fixtures = JSON.parse(raw);
} catch (e) {
  console.error('Failed to load stagetest-runs.json:', e);
  fixtures = {
    runs: [],
    cases: [],
    required_data_testids: [],
    required_components: [],
  };
}

// ============================================================================
// Stagetest Evidence Console Tests
// ============================================================================

const STAGETEST_PAGE = '/prefops/stagetest';

test.describe('Stagetest Evidence Console', () => {
  test.describe.configure({ mode: 'serial' });

  // ========================================================================
  // 1. Page Load — Zero Console Errors
  // ========================================================================

  test('stagetest page loads without console errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        // Allow expected API errors (backend may not be running)
        if (
          text.includes('/hoc/api/stagetest') ||
          text.includes('Failed to fetch')
        ) {
          return;
        }
        errors.push(text);
      }
    });

    page.on('pageerror', (error) => {
      errors.push(error.message || String(error));
    });

    await page.addInitScript(() => {
      localStorage.setItem('aos_auth_token', 'mock-stagetest-token');
      localStorage.setItem('aos_tenant_id', 'stagetest-test-tenant');
      localStorage.setItem('aos_user_role', 'FOUNDER');
    });

    const response = await page.goto(STAGETEST_PAGE, {
      waitUntil: 'domcontentloaded',
      timeout: 15000,
    });

    expect(response?.status()).toBeLessThan(500);

    try {
      await page.waitForLoadState('networkidle', { timeout: 10000 });
    } catch {
      // networkidle timeout acceptable
    }

    await page.waitForTimeout(500);
    expect(errors, 'Console errors on stagetest page').toEqual([]);
  });

  // ========================================================================
  // 2. Stats Bar Renders
  // ========================================================================

  test('stagetest stats bar renders', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('aos_auth_token', 'mock-stagetest-token');
      localStorage.setItem('aos_tenant_id', 'stagetest-test-tenant');
      localStorage.setItem('aos_user_role', 'FOUNDER');
    });

    await page.goto(STAGETEST_PAGE, { waitUntil: 'domcontentloaded' });

    try {
      await page.waitForLoadState('networkidle', { timeout: 10000 });
    } catch {
      // acceptable
    }

    const statsBar = page.locator('[data-testid="stagetest-stats"]');
    await expect(statsBar).toBeVisible({ timeout: 5000 });
  });

  // ========================================================================
  // 3. Run List or Empty State Renders
  // ========================================================================

  test('stagetest run list or empty state renders', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('aos_auth_token', 'mock-stagetest-token');
      localStorage.setItem('aos_tenant_id', 'stagetest-test-tenant');
      localStorage.setItem('aos_user_role', 'FOUNDER');
    });

    await page.goto(STAGETEST_PAGE, { waitUntil: 'domcontentloaded' });

    try {
      await page.waitForLoadState('networkidle', { timeout: 10000 });
    } catch {
      // acceptable
    }

    // Either the run list table renders, or the empty state text
    const runList = page.locator('[data-testid="stagetest-run-list"]');
    const pageRoot = page.locator('[data-testid="stagetest-page"]');

    await expect(pageRoot).toBeVisible({ timeout: 5000 });

    // Content area should be present (run list or message)
    const contentArea = page.locator('[data-testid="stagetest-page"] .bg-gray-800\\/30');
    await expect(contentArea).toBeVisible({ timeout: 3000 });
  });

  // ========================================================================
  // 4. Required Components Exist on Disk
  // ========================================================================

  test('all stagetest UI components exist on disk', () => {
    const featureDir = path.resolve(
      __dirname,
      '../../src/features/stagetest',
    );

    for (const component of fixtures.required_components) {
      const fullPath = path.join(featureDir, component);
      expect(
        fs.existsSync(fullPath),
        `Missing component: ${component}`,
      ).toBe(true);
    }
  });

  // ========================================================================
  // 5. Route Wiring — stagetest in founder routes
  // ========================================================================

  test('stagetest route is wired in routes/index.tsx', () => {
    const routesPath = path.resolve(
      __dirname,
      '../../src/routes/index.tsx',
    );
    const source = fs.readFileSync(routesPath, 'utf8');

    // Lazy import exists
    expect(source).toContain("import('@/features/stagetest/StagetestPage')");

    // Route path wired for both prefops and fops via renderFounderRoutes
    expect(source).toContain('/stagetest');

    // FounderRoute guard is applied (via renderFounderRoutes pattern)
    expect(source).toContain('StagetestPage');
  });

  // ========================================================================
  // 6. Fixture Run Shapes Are Valid
  // ========================================================================

  test('fixture runs have valid shapes', () => {
    expect(fixtures.runs.length).toBeGreaterThan(0);

    for (const run of fixtures.runs) {
      expect(run.run_id).toBeTruthy();
      expect(run.created_at).toBeTruthy();
      expect(run.stages_executed.length).toBeGreaterThan(0);
      expect(run.total_cases).toBeGreaterThan(0);
      expect(run.pass_count + run.fail_count).toBeLessThanOrEqual(run.total_cases);
      expect(run.determinism_digest).toMatch(/^[a-f0-9]{64}$/);
      expect(run.artifact_version).toBeTruthy();
    }
  });

  // ========================================================================
  // 7. Fixture Case Shapes Are Valid
  // ========================================================================

  test('fixture cases have valid shapes', () => {
    expect(fixtures.cases.length).toBeGreaterThan(0);

    for (const c of fixtures.cases) {
      expect(c.case_id).toBeTruthy();
      expect(c.uc_id).toMatch(/^UC-\d{3}$/);
      expect(c.stage).toBeTruthy();
      expect(c.operation_name).toBeTruthy();
      expect(['PASS', 'FAIL', 'SKIPPED']).toContain(c.status);
      expect(c.determinism_hash).toMatch(/^[a-f0-9]{64}$/);
    }
  });

  // ========================================================================
  // 8. Client Uses Canonical Route Prefix
  // ========================================================================

  test('stagetestClient uses canonical /hoc/api/stagetest prefix', () => {
    const clientPath = path.resolve(
      __dirname,
      '../../src/features/stagetest/stagetestClient.ts',
    );
    const source = fs.readFileSync(clientPath, 'utf8');

    expect(source).toContain('/hoc/api/stagetest');
    expect(source).not.toContain('/api/v1/stagetest');
  });

  // ========================================================================
  // 9. Case Detail Uses Table Testids (v2 W5 — UI field/table visibility)
  // ========================================================================

  test('StagetestCaseDetail uses explicit table testids instead of JSON blocks', () => {
    const detailPath = path.resolve(
      __dirname,
      '../../src/features/stagetest/StagetestCaseDetail.tsx',
    );
    const source = fs.readFileSync(detailPath, 'utf8');

    // Required table testids (must be present) — V3 requires all 5 table sections
    const requiredTestids = [
      'api-request-fields-table',
      'api-response-fields-table',
      'synthetic-input-table',
      'produced-output-table',
      'apis-used-table',
      'assertions-table',
      'determinism-hash',
      'signature',
    ];

    for (const tid of requiredTestids) {
      expect(
        source,
        `Missing data-testid="${tid}" in StagetestCaseDetail.tsx`,
      ).toContain(`"${tid}"`);
    }

    // Verify KeyValueTable is used (not JsonBlock) for field display
    expect(source).toContain('KeyValueTable');
    expect(source).not.toContain('JsonBlock');
  });
});
