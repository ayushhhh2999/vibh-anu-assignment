
$ErrorActionPreference = 'Stop'

$TestKitDir = $PSScriptRoot
$ProjectRoot = Split-Path $TestKitDir -Parent
$BackendDir = Join-Path $ProjectRoot 'backend'
$BackendTestDir = Join-Path $BackendDir 'testing'
$TestEnvFile = Join-Path $TestKitDir '.env.test'
$PythonVenv = Join-Path $BackendDir 'venv\Scripts\python.exe'
$PythonExe = if (Test-Path $PythonVenv) { $PythonVenv } else { (Get-Command python -ErrorAction Stop).Source }
$NodeExe = (Get-Command node -ErrorAction Stop).Source
$NpmCommand = (Get-Command npm -ErrorAction Stop).Source
$OriginalEnvironment = @{}
$StartedProcesses = [System.Collections.Generic.List[System.Diagnostics.Process]]::new()
$SuiteResults = [System.Collections.Generic.List[object]]::new()
$BackendPassedTests = 0
$BrowserPassedTests = 0
$RunRoot = Join-Path $env:TEMP ("vibhanu-e2e-" + [guid]::NewGuid().ToString('N'))
$BackendLog = Join-Path $RunRoot 'backend.log'
$BackendErrorLog = Join-Path $RunRoot 'backend-error.log'
$FrontendLog = Join-Path $RunRoot 'frontend.log'
$FrontendErrorLog = Join-Path $RunRoot 'frontend-error.log'

function Set-TestEnvironmentValue {
    param([string]$Name, [AllowEmptyString()][string]$Value)

    if (-not $OriginalEnvironment.ContainsKey($Name)) {
        $OriginalEnvironment[$Name] = [Environment]::GetEnvironmentVariable($Name, 'Process')
    }
    [Environment]::SetEnvironmentVariable($Name, $Value, 'Process')
}

function Get-FreePort {
    param([int]$FirstPort, [int]$LastPort)

    foreach ($port in $FirstPort..$LastPort) {
        $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
        if ($listeners.Count -eq 0) { return $port }
    }
    throw "No free port found in range $FirstPort-$LastPort. Stop a conflicting test server and retry."
}

function Wait-ForHttp {
    param([string]$Url, [System.Diagnostics.Process]$Process, [int]$Attempts = 80)

    for ($attempt = 0; $attempt -lt $Attempts; $attempt++) {
        if ($Process.HasExited) {
            throw "Server process exited before becoming reachable at $Url."
        }
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
            if ($response.StatusCode -lt 500) { return }
        }
        catch {
            if ($attempt -eq $Attempts - 1) { throw "Server did not become reachable at $Url." }
        }
    }
    throw "Server did not become reachable at $Url."
}

function Invoke-BackendSuite {
    param([string]$Name, [string]$ScriptPath)

    Write-Host "`n=== Backend: $Name ===" -ForegroundColor Cyan
    $output = & $PythonExe $ScriptPath 2>&1
    $code = $LASTEXITCODE
    $text = $output | Out-String
    $output | ForEach-Object { Write-Host $_ }
    $passed = [regex]::Matches($text, 'Passed\s*:\s*(\d+)')
    if ($passed.Count -gt 0) { $script:BackendPassedTests += [int]$passed[$passed.Count - 1].Groups[1].Value }
    $SuiteResults.Add([pscustomobject]@{ Name = $Name; Passed = ($code -eq 0) })
    if ($code -ne 0) { Write-Host "FAILED: $Name (exit $code)" -ForegroundColor Red }
    else { Write-Host "PASSED: $Name" -ForegroundColor Green }
}

try {
    New-Item -ItemType Directory -Path $RunRoot -Force | Out-Null

    if (-not (Test-Path $TestEnvFile)) {
        @(
            'APP_ENV=test',
            'JWT_SECRET_KEY=vibhanu-local-e2e-only-secret-rotate-outside-tests',
            'E2E_MARKETING_EMAIL=marketing@vibhanu.com',
            'E2E_MARKETING_PASSWORD=VibanuTest-Marketing-2026!',
            'E2E_COMMUNICATION_EMAIL=communication@vibhanu.com',
            'E2E_COMMUNICATION_PASSWORD=VibanuTest-Communication-2026!',
            'E2E_VIGILANCE_EMAIL=vigilance@vibhanu.com',
            'E2E_VIGILANCE_PASSWORD=VibanuTest-Vigilance-2026!',
            'E2E_SUPPORT_EMAIL=support@vibhanu.com',
            'E2E_SUPPORT_PASSWORD=VibanuTest-Support-2026!',
            'E2E_SALES_EMAIL=sales@vibhanu.com',
            'E2E_SALES_PASSWORD=VibanuTest-Sales-2026!'
        ) | Set-Content -Path $TestEnvFile -Encoding ASCII
        Write-Host 'Created ignored local test configuration.' -ForegroundColor Yellow
    }

    foreach ($line in Get-Content $TestEnvFile) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$') {
            $name = $Matches[1]
            $value = $Matches[2]
            if ($value.Length -ge 2 -and (($value[0] -eq '"' -and $value[-1] -eq '"') -or ($value[0] -eq "'" -and $value[-1] -eq "'"))) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            Set-TestEnvironmentValue -Name $name -Value $value
        }
    }

    Set-TestEnvironmentValue -Name 'APP_ENV' -Value 'test'
    $BackendPort = Get-FreePort -FirstPort 8001 -LastPort 8010
    $FrontendPort = Get-FreePort -FirstPort 3001 -LastPort 3010
    $BackendUrl = "http://127.0.0.1:$BackendPort"
    $FrontendUrl = "http://127.0.0.1:$FrontendPort"
    $DatabasePath = Join-Path $RunRoot 'vibanu-e2e.db'
    $AudioDir = Join-Path $RunRoot 'uploads\audio'
    $DatabaseUrl = "sqlite:///" + $DatabasePath.Replace('\', '/')

    Set-TestEnvironmentValue -Name 'DATABASE_URL' -Value $DatabaseUrl
    Set-TestEnvironmentValue -Name 'VIBANU_AUDIO_DIR' -Value $AudioDir
    Set-TestEnvironmentValue -Name 'VIBANU_TEST_WORKDIR' -Value $RunRoot
    Set-TestEnvironmentValue -Name 'VIBANU_TEST_API_URL' -Value $BackendUrl
    Set-TestEnvironmentValue -Name 'FRONTEND_URL' -Value $FrontendUrl
    Set-TestEnvironmentValue -Name 'VITE_API_BASE_URL' -Value $BackendUrl
    Set-TestEnvironmentValue -Name 'VIBANU_CORS_ORIGINS' -Value $FrontendUrl

    Write-Host "Python: $PythonExe"
    Write-Host "Node: $NodeExe"
    $pythonCheck = & $PythonExe -c 'import fastapi, sqlalchemy, pwdlib, jwt, dotenv, requests, multipart' 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Installing missing backend test dependencies...' -ForegroundColor Yellow
        & $PythonExe -m pip install -r (Join-Path $BackendDir 'requirements.txt') requests
        if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
    }

    $playwrightPackage = Join-Path $TestKitDir 'node_modules\@playwright\test'
    if (-not (Test-Path $playwrightPackage)) {
        Write-Host 'Installing frontend test dependencies...' -ForegroundColor Yellow
        Push-Location $TestKitDir
        try { & $NpmCommand ci; if ($LASTEXITCODE -ne 0) { throw 'npm ci failed.' } }
        finally { Pop-Location }
    }
    $PlaywrightCli = Join-Path $TestKitDir 'node_modules\playwright\cli.js'
    if (-not (Test-Path $PlaywrightCli)) { throw 'Playwright CLI is missing after dependency verification.' }

    Push-Location $BackendTestDir
    try {
        Write-Host 'Initializing the isolated SQLite database and test accounts...' -ForegroundColor Cyan
        & $PythonExe (Join-Path $TestKitDir 'scripts\seed_test_users.py')
        if ($LASTEXITCODE -ne 0) { throw 'Test-account/database seeding failed.' }
    }
    finally { Pop-Location }

    $backendArgs = @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', [string]$BackendPort)
    $backendProcess = Start-Process -FilePath $PythonExe -ArgumentList $backendArgs -WorkingDirectory $BackendDir -PassThru -WindowStyle Hidden -RedirectStandardOutput $BackendLog -RedirectStandardError $BackendErrorLog
    $StartedProcesses.Add($backendProcess)

    $viteCli = Join-Path $TestKitDir 'node_modules\vite\bin\vite.js'
    $frontendArgs = @($viteCli, '--host', '127.0.0.1', '--port', [string]$FrontendPort, '--strictPort')
    $frontendProcess = Start-Process -FilePath $NodeExe -ArgumentList $frontendArgs -WorkingDirectory $TestKitDir -PassThru -WindowStyle Hidden -RedirectStandardOutput $FrontendLog -RedirectStandardError $FrontendErrorLog
    $StartedProcesses.Add($frontendProcess)

    Wait-ForHttp -Url "$BackendUrl/health" -Process $backendProcess
    Wait-ForHttp -Url $FrontendUrl -Process $frontendProcess
    Write-Host "Backend and frontend are reachable at $BackendUrl and $FrontendUrl." -ForegroundColor Green

    foreach ($suite in @('test_api.py', 'test_vigilance.py', 'test_support.py', 'test_sales.py')) {
        Invoke-BackendSuite -Name $suite -ScriptPath (Join-Path $BackendTestDir $suite)
    }

    Write-Host "`n=== Playwright: visible Chromium ===" -ForegroundColor Cyan
    Push-Location $TestKitDir
    try {
        $browserInstallOutput = & $NodeExe $PlaywrightCli install chromium 2>&1
        if ($LASTEXITCODE -ne 0) {
            $browserInstallOutput | ForEach-Object { Write-Host $_ }
            throw 'Chromium installation/verification failed.'
        }
        $browserOutput = & $NodeExe $PlaywrightCli test --headed 2>&1
        $browserCode = $LASTEXITCODE
        $browserText = $browserOutput | Out-String
        $browserOutput | ForEach-Object { Write-Host $_ }
        $browserPassed = [regex]::Match($browserText, '(\d+) passed')
        if ($browserPassed.Success) { $BrowserPassedTests = [int]$browserPassed.Groups[1].Value }
        $SuiteResults.Add([pscustomobject]@{ Name = 'Playwright browser tests'; Passed = ($browserCode -eq 0) })
    }
    finally { Pop-Location }
}
catch {
    Write-Host "`nTest runner setup/error: $_" -ForegroundColor Red
    if (Test-Path $BackendLog) { Get-Content $BackendLog -Tail 40 | ForEach-Object { Write-Host $_ } }
    if (Test-Path $BackendErrorLog) { Get-Content $BackendErrorLog -Tail 40 | ForEach-Object { Write-Host $_ } }
    if (Test-Path $FrontendLog) { Get-Content $FrontendLog -Tail 40 | ForEach-Object { Write-Host $_ } }
    if (Test-Path $FrontendErrorLog) { Get-Content $FrontendErrorLog -Tail 40 | ForEach-Object { Write-Host $_ } }
    $SuiteResults.Add([pscustomobject]@{ Name = 'Runner setup'; Passed = $false })
}
finally {
    foreach ($process in $StartedProcesses) {
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
    foreach ($name in @($OriginalEnvironment.Keys)) {
        [Environment]::SetEnvironmentVariable($name, $OriginalEnvironment[$name], 'Process')
    }
    if (Test-Path $RunRoot) { Remove-Item -LiteralPath $RunRoot -Recurse -Force -ErrorAction SilentlyContinue }
}

$passedSuites = @($SuiteResults | Where-Object Passed).Count
$failedSuites = @($SuiteResults | Where-Object { -not $_.Passed })
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host 'TEST RUN SUMMARY' -ForegroundColor Cyan
Write-Host "Passed suites: $passedSuites / $($SuiteResults.Count)" -ForegroundColor $(if ($failedSuites.Count -eq 0) { 'Green' } else { 'Yellow' })
Write-Host "Passed checks: $($BackendPassedTests + $BrowserPassedTests) (backend checks: $BackendPassedTests, browser tests: $BrowserPassedTests)"
Write-Host "Failed suites: $($failedSuites.Count)"
if ($failedSuites.Count -gt 0) {
    $failedSuites | ForEach-Object { Write-Host " - $($_.Name)" -ForegroundColor Red }
    Write-Host "HTML report: $TestKitDir\playwright-report\index.html"
    exit 1
}
Write-Host "HTML report: $TestKitDir\playwright-report\index.html"
Write-Host 'All backend and browser suites passed.' -ForegroundColor Green
