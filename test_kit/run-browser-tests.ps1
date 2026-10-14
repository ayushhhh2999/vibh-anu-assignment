$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

Write-Host "`n=== Vibh-Anu visible browser tests ===" -ForegroundColor Cyan
$frontDisplay = if ($env:FRONTEND_URL) { $env:FRONTEND_URL } else { 'http://localhost:3000' }
Write-Host "Frontend: $frontDisplay"

# Require credentials without writing passwords into source files.
$required = @(
  'E2E_MARKETING_EMAIL','E2E_MARKETING_PASSWORD',
  'E2E_COMMUNICATION_EMAIL','E2E_COMMUNICATION_PASSWORD',
  'E2E_VIGILANCE_EMAIL','E2E_VIGILANCE_PASSWORD',
  'E2E_SUPPORT_EMAIL','E2E_SUPPORT_PASSWORD',
  'E2E_SALES_EMAIL','E2E_SALES_PASSWORD'
)
$missing = @($required | Where-Object { -not [Environment]::GetEnvironmentVariable($_) })
if ($missing.Count -gt 0) {
  Write-Host 'Missing test credentials. Set these in this PowerShell terminal first:' -ForegroundColor Yellow
  $missing | ForEach-Object { Write-Host "  `$env:$_ = '<your existing test account value>'" }
  exit 2
}

$apiBase = if ($env:VITE_API_BASE_URL) { $env:VITE_API_BASE_URL } else { 'http://127.0.0.1:8000' }
$front = if ($env:FRONTEND_URL) { $env:FRONTEND_URL } else { 'http://localhost:3000' }
try {
  $apiHealth = Invoke-WebRequest -Uri "$apiBase/health" -TimeoutSec 5
  if ($apiHealth.StatusCode -ge 500) { throw 'Backend health check returned a server error.' }
} catch {
  Write-Host "Backend is not reachable at $apiBase. Start FastAPI first." -ForegroundColor Red
  exit 3
}
try {
  $frontResponse = Invoke-WebRequest -Uri $front -TimeoutSec 5
  if ($frontResponse.StatusCode -ge 500) { throw 'Frontend returned a server error.' }
} catch {
  Write-Host "Frontend is not reachable at $front. Start the Vite dev server first." -ForegroundColor Red
  exit 4
}

if (-not (Test-Path 'node_modules/@playwright/test')) {
  Write-Host 'Installing npm dependencies...' -ForegroundColor Cyan
  npm install
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
Write-Host 'Ensuring Chromium is installed...' -ForegroundColor Cyan
npx playwright install chromium
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
# Run the existing Python backend test suites too, if the expected sibling folder exists.
$backendTests = Join-Path (Split-Path $PSScriptRoot -Parent) 'backend\testing'
if (Test-Path $backendTests) {
  $python = 'python'
  $venvPython = Join-Path (Split-Path $PSScriptRoot -Parent) 'backend\venv\Scripts\python.exe'
  if (Test-Path $venvPython) { $python = $venvPython }
  foreach ($suite in @('test_api.py','test_vigilance.py','test_support.py','test_sales.py')) {
    $suitePath = Join-Path $backendTests $suite
    if (Test-Path $suitePath) {
      Write-Host "`n=== Backend: $suite ===" -ForegroundColor Cyan
      Push-Location $backendTests
      try { & $python $suitePath; if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE } }
      finally { if ((Get-Location).Path -eq $backendTests) { Pop-Location } }
    }
  }
} else {
  Write-Host "Backend test folder not found at $backendTests; skipping Python suites." -ForegroundColor Yellow
}

Write-Host 'Opening visible Chromium and running all browser tests...' -ForegroundColor Green
npm run test:e2e:headed
$code = $LASTEXITCODE
Write-Host "`nHTML report: $PSScriptRoot\playwright-report\index.html"
Write-Host "Screenshots / traces: $PSScriptRoot\test-results"
if ($code -ne 0) { Write-Host 'Some tests failed. Open the HTML report for details.' -ForegroundColor Red }
exit $code
