// UC UAT Playwright Configuration
// Reference: UC_CODEBASE_ELICITATION_VALIDATION_UAT_TASKPACK_2026-02-15

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [
    ['list'],
    ['json', { outputFile: 'uat-results.json' }],
  ],

  timeout: 30000,

  use: {
    baseURL: process.env.UAT_BASE_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: process.env.CI ? undefined : {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
    timeout: 120000,
    cwd: '../../',  // Relative to tests/uat/ → website/app-shell/
  },
});
