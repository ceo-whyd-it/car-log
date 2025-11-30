import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Car Log E2E tests.
 *
 * Tests run against the Gradio app at localhost:7860.
 * Ensure Docker containers are running before testing.
 */
export default defineConfig({
  testDir: '.',
  fullyParallel: false, // Sequential for Gradio state consistency
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Single worker for Gradio
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:7861',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Web server is managed by Docker, but we wait for it
  webServer: {
    command: 'echo "Gradio server should be running in Docker"',
    url: 'http://localhost:7861',
    reuseExistingServer: true,
    timeout: 120 * 1000,
  },
});
