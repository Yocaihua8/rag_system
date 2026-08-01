import { defineConfig, devices } from "@playwright/test";

const frontendPort = process.env.KI_E2E_FRONTEND_PORT || "4173";
const baseURL = process.env.KI_E2E_BASE_URL || `http://127.0.0.1:${frontendPort}`;
const browserChannel = process.env.KI_E2E_BROWSER_CHANNEL;

export default defineConfig({
  testDir: "../tests/e2e",
  outputDir: "../test-results",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "list",
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        ...(browserChannel ? { channel: browserChannel } : {}),
      },
    },
  ],
});
