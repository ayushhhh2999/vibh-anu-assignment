import { test, expect, type Page } from '@playwright/test'
import { unlinkSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const roles = [
  { key: 'MARKETING', label: 'Marketing desk', route: '/marketing' },
  { key: 'COMMUNICATION', label: 'Communication', route: '/communication' },
  { key: 'VIGILANCE', label: 'Vigilance', route: '/vigilance' },
  { key: 'SUPPORT', label: 'Support queue', route: '/support' },
  { key: 'SALES', label: 'Sales floor', route: '/sales' },
] as const
const generatedAudioFiles: string[] = []

test.afterAll(() => {
  for (const path of generatedAudioFiles) {
    try { unlinkSync(path) } catch { /* The OS may already have removed the temp file. */ }
  }
})

function credentials(key: string) {
  const email = process.env[`E2E_${key}_EMAIL`]
  const password = process.env[`E2E_${key}_PASSWORD`]
  if (!email || !password) throw new Error(`Set E2E_${key}_EMAIL and E2E_${key}_PASSWORD in your PowerShell session before running tests.`)
  return { email, password }
}

async function login(page: Page, key: string, route: string) {
  const { email, password } = credentials(key)
  await page.goto('/login')
  await page.getByLabel('Work email').fill(email)
  await page.locator('input[name="password"]').fill(password)
  await page.getByRole('button', { name: /sign in to workspace/i }).click()
  await expect(page).toHaveURL(new RegExp(`${route.replace('/', '\\/')}$`))
}

function makeWavFile(): string {
  // Generate a 3-second, valid PCM WAV so Chromium can play it to its ended event.
  const sampleRate = 8000
  const seconds = 3
  const dataSize = sampleRate * seconds * 2
  const buffer = Buffer.alloc(44 + dataSize)
  buffer.write('RIFF', 0); buffer.writeUInt32LE(36 + dataSize, 4); buffer.write('WAVE', 8)
  buffer.write('fmt ', 12); buffer.writeUInt32LE(16, 16); buffer.writeUInt16LE(1, 20)
  buffer.writeUInt16LE(1, 22); buffer.writeUInt32LE(sampleRate, 24); buffer.writeUInt32LE(sampleRate * 2, 28)
  buffer.writeUInt16LE(2, 32); buffer.writeUInt16LE(16, 34); buffer.write('data', 36); buffer.writeUInt32LE(dataSize, 40)
  const path = join(tmpdir(), `vibhanu-e2e-${Date.now()}.wav`)
  writeFileSync(path, buffer)
  generatedAudioFiles.push(path)
  return path
}

test('frontend opens and has no uncaught browser exceptions', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  const response = await page.goto('/')
  expect(response?.status()).toBeLessThan(500)
  await expect(page.locator('body')).not.toBeEmpty()
  await page.screenshot({ path: 'test-results/homepage.png', fullPage: true })
  expect(errors).toEqual([])
})

test('all five accounts can log in and land on their role dashboard', async ({ page }) => {
  for (const role of roles) {
    await login(page, role.key, role.route)
    await expect(page.getByText(role.label, { exact: true }).first()).toBeVisible()
    await page.getByRole('button', { name: /sign out/i }).click()
    await expect(page).toHaveURL(/\/login$/)
  }
})

test('rejects invalid credentials without leaving the login screen', async ({ page }) => {
  const { email } = credentials('MARKETING')
  await page.goto('/login')
  await page.getByLabel('Work email').fill(email)
  await page.locator('input[name="password"]').fill('Definitely-not-the-real-password-123!')
  await page.getByRole('button', { name: /sign in to workspace/i }).click()
  await expect(page.getByRole('alert')).toBeVisible()
  await expect(page).toHaveURL(/\/login$/)
})

test('protected department routes redirect unauthenticated users to login', async ({ page }) => {
  for (const role of roles) {
    await page.goto(role.route)
    await expect(page).toHaveURL(/\/login$/)
  }
})

test('role-based navigation prevents a Marketing user from opening another department', async ({ page }) => {
  await login(page, 'MARKETING', '/marketing')
  await page.goto('/support')
  await expect(page).toHaveURL(/\/marketing$/)
})

test('complete lead workflow from Marketing through Sales claim', async ({ page }) => {
  const unique = Date.now()
  const leadName = `E2E Lead ${unique}`
  const contact = `98${String(unique).slice(-8)}`
  const audioPath = makeWavFile()

  // Marketing creates a fresh lead.
  await login(page, 'MARKETING', '/marketing')
  await page.getByRole('button', { name: /new lead/i }).click()
  await page.getByLabel('Customer / lead name').fill(leadName)
  await page.getByLabel('Contact number').fill(contact)
  await page.getByRole('button', { name: /^create lead$/i }).click()
  await expect(page.getByText(leadName, { exact: true }).first()).toBeVisible()
  await page.getByRole('button', { name: /sign out/i }).click()

  // Communication enriches and submits it.
  await login(page, 'COMMUNICATION', '/communication')
  await page.getByRole('button', { name: `Open ${leadName}` }).click()
  await page.getByLabel('Postal address').fill('100 Automation Test Street, Gurugram')
  await page.getByLabel('Meeting date').fill('2027-01-15')
  await page.getByLabel('Meeting time').fill('14:30')
  await page.getByLabel('Remark').fill('Created by Playwright end-to-end test')
  await page.getByRole('button', { name: /save changes/i }).click()
  await expect(page.getByText(/lead details saved on the server/i)).toBeVisible()
  await page.getByRole('button', { name: /submit to vigilance/i }).click()
  await expect(page.getByText(/lead submitted to vigilance/i)).toBeVisible()
  await page.getByRole('button', { name: /sign out/i }).click()

  // Vigilance uploads a real playable WAV and verifies it.
  await login(page, 'VIGILANCE', '/vigilance')
  await page.getByRole('button', { name: `Open ${leadName}` }).click()
  await page.locator('input[type="file"]').setInputFiles(audioPath)
  await page.getByRole('button', { name: /upload to backend/i }).click()
  await expect(page.getByText(/recording uploaded and confirmed/i)).toBeVisible()
  await page.getByRole('button', { name: /verify & forward/i }).click()
  await expect(page.getByText(/lead verified and forwarded to support/i)).toBeVisible()
  await page.getByRole('button', { name: /sign out/i }).click()

  // Support checks prerequisites and allocates.
  await login(page, 'SUPPORT', '/support')
  await page.getByRole('button', { name: `Open ${leadName}` }).click()
  await expect(page.getByText('All prerequisites are present.')).toBeVisible()
  await page.getByRole('button', { name: /allocate to sales/i }).click()
  await expect(page.getByText(/lead allocated to sales/i)).toBeVisible()
  await page.getByRole('button', { name: /sign out/i }).click()

  // Sales plays the recording to its natural end and claims the lead.
  await login(page, 'SALES', '/sales')
  await page.getByRole('button', { name: `Open ${leadName}` }).click()
  await expect(page.getByText(contact, { exact: true })).toHaveCount(0)
  const audio = page.getByLabel('Lead audio recording')
  await expect(audio).toBeVisible()
  await expect(page.getByRole('button', { name: /claim lead/i })).toBeDisabled()
  await expect.poll(async () => audio.evaluate((el: HTMLAudioElement) => el.readyState)).toBeGreaterThanOrEqual(2)
  await audio.evaluate((el: HTMLAudioElement) => el.play())
  await expect(page.getByText('Playback acknowledged')).toBeVisible({ timeout: 15_000 })
  await page.getByRole('button', { name: /claim lead/i }).click()
  await expect(page.getByText('Claim confirmed')).toBeVisible()
  await expect(page.getByText(contact, { exact: true })).toBeVisible()
})
