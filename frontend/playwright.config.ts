
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  timeout: 30_000,
  reporter: [["list"], ["html", { open: "never" }]],

  use: {
    baseURL: "http://localhost:3000",
    ...devices["Desktop Chrome"],
    headless: false,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },

  outputDir: "test-results",
});
