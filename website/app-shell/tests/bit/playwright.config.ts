// Browser Integration Test - Playwright Configuration
// Reference: PIN-245 (Integration Integrity System)

import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'url';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const appShellRoot = path.resolve(__dirname, '../..');

export default defineConfig({
  testDir: '.',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 0 : 0,  // No retries - integration errors must be fixed
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
    ['json', { outputFile: 'bit-results.json' }],
  ],

  // Global timeout - page loads should be fast
  timeout: 30000,

  use: {
    // Base URL for the console
    baseURL: process.env.BIT_BASE_URL || 'http://127.0.0.1:5173',

    // Capture trace on failure for debugging
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Add Firefox if needed for cross-browser
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
  ],

  // Web server configuration (start dev server if not running)
  webServer: process.env.CI ? undefined : {
    command: 'npm run dev -- --host 127.0.0.1 --port 5173',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
    cwd: appShellRoot,
  },
});
