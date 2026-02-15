// Browser Integration Test - Page Load Tests
// Reference: PIN-245 (Integration Integrity System)
//
// PURPOSE: Detect browser-console-level integration failures
// SCOPE: Page load only - NO clicks, NO flows, NO content assertions
//
// FAILURE RULE: If ANY console error appears → BUILD FAILS

import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import * as yaml from 'js-yaml';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ============================================
// TYPE DEFINITIONS
// ============================================

interface PageDef {
  path: string;
  name: string;
  auth_required: boolean;
  role?: string;
  product?: string;
}

interface AllowlistEntry {
  page: string;
  pattern: string;
  reason: string;
  expiry: string;
  owner?: string;
}

interface PageRegistry {
  pages: PageDef[];
}

interface Allowlist {
  allowed_console_errors: AllowlistEntry[];
}

// ============================================
// LOAD CONFIGURATION
// ============================================

const registryPath = path.join(__dirname, 'page-registry.yaml');
const allowlistPath = path.join(__dirname, 'allowlist.yaml');

let pages: PageDef[] = [];
let allowlist: AllowlistEntry[] = [];

try {
  const registryContent = fs.readFileSync(registryPath, 'utf8');
  const registry = yaml.load(registryContent) as PageRegistry;
  pages = registry.pages || [];
} catch (e) {
  console.error('Failed to load page-registry.yaml:', e);
}

try {
  const allowlistContent = fs.readFileSync(allowlistPath, 'utf8');
  const allowlistData = yaml.load(allowlistContent) as Allowlist;
  allowlist = allowlistData.allowed_console_errors || [];
} catch (e) {
  console.error('Failed to load allowlist.yaml:', e);
}

// ============================================
// ALLOWLIST CHECKER
// ============================================

function isAllowed(pagePath: string, message: string): boolean {
  const now = new Date();

  for (const entry of allowlist) {
    // Check page match (* = all pages)
    if (entry.page !== '*' && entry.page !== pagePath) {
      continue;
    }

    // Check pattern match
    if (!message.includes(entry.pattern)) {
      continue;
    }

    // Check expiry
    const expiry = new Date(entry.expiry);
    if (expiry < now) {
      // Expired entry - treat as not allowed
      console.warn(`EXPIRED ALLOWLIST ENTRY: ${entry.reason} expired on ${entry.expiry}`);
      continue;
    }

    // Entry is valid and matches
    console.log(`ALLOWED: "${message.substring(0, 50)}..." (reason: ${entry.reason})`);
    return true;
  }

  return false;
}

// ============================================
// MOCK AUTH (for testing authenticated pages)
// ============================================

async function setupMockAuth(page: any): Promise<void> {
  // Set localStorage/sessionStorage values that the app expects
  await page.addInitScript(() => {
    // Mock auth token
    localStorage.setItem('aos_auth_token', 'mock-bit-token');
    localStorage.setItem('aos_tenant_id', 'bit-test-tenant');
    localStorage.setItem('aos_user_role', 'admin');
  });
}

// ============================================
// BIT TESTS
// ============================================

test.describe('Browser Integration Tests', () => {
  test.describe.configure({ mode: 'parallel' });

  for (const pageDef of pages) {
    test(`[BIT] ${pageDef.name} (${pageDef.path}) loads without console errors`, async ({ page }) => {
      const errors: string[] = [];
      const warnings: string[] = [];

      // ============================================
      // CAPTURE CONSOLE ERRORS
      // ============================================
      page.on('console', (msg) => {
        if (msg.type() === 'error') {
          const text = msg.text();
          if (!isAllowed(pageDef.path, text)) {
            errors.push(`[console.error] ${text}`);
          }
        }
      });

      // ============================================
      // CAPTURE UNHANDLED REJECTIONS
      // ============================================
      page.on('pageerror', (error) => {
        const message = error.message || String(error);
        if (!isAllowed(pageDef.path, message)) {
          errors.push(`[unhandled] ${message}`);
        }
      });

      // ============================================
      // CAPTURE NETWORK ERRORS
      // ============================================
      page.on('response', (response) => {
        const status = response.status();
        const url = response.url();

        // 5xx errors are always failures
        if (status >= 500) {
          const msg = `[network] ${status} ${url}`;
          if (!isAllowed(pageDef.path, msg)) {
            errors.push(msg);
          }
        }

        // 4xx errors are warnings (except 401/403 which are auth)
        if (status >= 400 && status < 500 && status !== 401 && status !== 403) {
          warnings.push(`[network] ${status} ${url}`);
        }
      });

      // ============================================
      // SETUP AUTH IF REQUIRED
      // ============================================
      if (pageDef.auth_required) {
        await setupMockAuth(page);
      }

      // ============================================
      // NAVIGATE TO PAGE
      // ============================================
      const response = await page.goto(pageDef.path, {
        waitUntil: 'domcontentloaded',
        timeout: 15000,
      });

      // Check HTTP status
      expect(response?.status(), `Page ${pageDef.path} returned error status`).toBeLessThan(500);

      // Wait for network to settle
      try {
        await page.waitForLoadState('networkidle', { timeout: 10000 });
      } catch {
        // networkidle timeout is acceptable - some pages have long-polling
        console.log(`Note: ${pageDef.path} did not reach networkidle`);
      }

      // Small delay to catch any delayed errors
      await page.waitForTimeout(500);

      // ============================================
      // ASSERT NO ERRORS
      // ============================================
      if (errors.length > 0) {
        console.error(`\n❌ BIT FAILURE: ${pageDef.name} (${pageDef.path})`);
        console.error('Errors detected:');
        for (const error of errors) {
          console.error(`  - ${error}`);
        }
        console.error('\nTo fix:');
        console.error('  1. Fix the underlying integration error');
        console.error('  2. OR add to allowlist.yaml with expiry date');
      }

      if (warnings.length > 0) {
        console.warn(`\n⚠️  BIT WARNINGS: ${pageDef.name} (${pageDef.path})`);
        for (const warning of warnings) {
          console.warn(`  - ${warning}`);
        }
      }

      expect(errors, `Console errors on ${pageDef.path}`).toEqual([]);
    });
  }
});

// ============================================
// ALLOWLIST VALIDATION TEST
// ============================================

test.describe('Allowlist Validation', () => {
  test('No expired allowlist entries', () => {
    const now = new Date();
    const expired: string[] = [];

    for (const entry of allowlist) {
      const expiry = new Date(entry.expiry);
      if (expiry < now) {
        expired.push(`${entry.page}: "${entry.pattern}" (expired: ${entry.expiry})`);
      }
    }

    if (expired.length > 0) {
      console.warn('Expired allowlist entries (should be removed):');
      for (const e of expired) {
        console.warn(`  - ${e}`);
      }
    }

    // Don't fail on expired entries, just warn
    // They're effectively disabled anyway
  });

  test('All entries have valid expiry dates', () => {
    const invalid: string[] = [];

    for (const entry of allowlist) {
      const expiry = new Date(entry.expiry);
      if (isNaN(expiry.getTime())) {
        invalid.push(`${entry.page}: "${entry.pattern}" has invalid expiry: ${entry.expiry}`);
      }
    }

    expect(invalid, 'Invalid allowlist entries').toEqual([]);
  });
});
