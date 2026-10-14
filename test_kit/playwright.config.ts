import { defineConfig, devices } from '@playwright/test'

try {
  process.loadEnvFile(new URL('./.env.test', import.meta.url))
} catch (error) {
  if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error
}

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],
  use: {
    baseURL: process.env.FRONTEND_URL || 'http://localhost:3000',
    ...devices['Desktop Chrome'],
    headless: false,
    launchOptions: { args: ['--autoplay-policy=no-user-gesture-required'] },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  outputDir: 'test-results',
})
