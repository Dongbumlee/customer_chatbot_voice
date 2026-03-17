#!/usr/bin/env pwsh
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

<#
.SYNOPSIS
    Release deployment script for Customer Chatbot GSA with Voice.

.DESCRIPTION
    Performs pre-deployment validation, Docker build verification, test execution,
    and Azure deployment via Azure Developer CLI (azd).

    This script is idempotent and safe to re-run. It will NOT deploy unless all
    pre-flight checks pass.

.PARAMETER Environment
    Target azd environment name (e.g., dev, staging, prod). Defaults to the
    currently selected azd environment.

.PARAMETER SkipTests
    Skip test execution during pre-flight checks. Use only if tests were
    already verified in CI.

.PARAMETER SkipDockerBuild
    Skip local Docker build verification. Use when deploying from CI where
    images are built separately.

.PARAMETER DryRun
    Run all checks but do NOT execute the actual deployment.

.EXAMPLE
    .\scripts\deploy.ps1
    .\scripts\deploy.ps1 -Environment staging
    .\scripts\deploy.ps1 -DryRun
    .\scripts\deploy.ps1 -SkipTests -SkipDockerBuild
#>

[CmdletBinding()]
param(
    [string]$Environment = "",
    [switch]$SkipTests,
    [switch]$SkipDockerBuild,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Constants ────────────────────────────────────────────────────────────────
$RepoRoot       = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path (Join-Path $RepoRoot "azure.yaml"))) {
    # Fallback: script may be invoked from repo root directly
    $RepoRoot = Split-Path -Parent $PSScriptRoot
    if (-not (Test-Path (Join-Path $RepoRoot "azure.yaml"))) {
        $RepoRoot = $PSScriptRoot | Split-Path -Parent
    }
}

$ApiDir          = Join-Path $RepoRoot "src" "CustomerChatbotAPI"
$WebDir          = Join-Path $RepoRoot "src" "CustomerChatbotWeb"
$InfraDir        = Join-Path $RepoRoot "infra"

$RequiredTools   = @("azd", "docker", "uv", "npm")
$StepCount       = 0
$Errors          = @()

# ── Helpers ──────────────────────────────────────────────────────────────────

function Write-Step {
    param([string]$Message)
    $script:StepCount++
    Write-Host ""
    Write-Host "[$script:StepCount] $Message" -ForegroundColor Cyan
    Write-Host ("-" * 60)
}

function Write-Ok {
    param([string]$Message)
    Write-Host "  ✅ $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  ⚠️  $Message" -ForegroundColor Yellow
}

function Write-Fail {
    param([string]$Message)
    Write-Host "  ❌ $Message" -ForegroundColor Red
    $script:Errors += $Message
}

function Test-Command {
    param([string]$Name)
    $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

# ── Banner ───────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  Customer Chatbot GSA — Release Deployment Script"           -ForegroundColor Magenta
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"                 -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  Repo root : $RepoRoot"
Write-Host "  Dry run   : $DryRun"
Write-Host "  Skip tests: $SkipTests"
Write-Host ""

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Tool prerequisites
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "Checking required tools"

foreach ($tool in $RequiredTools) {
    if (Test-Command $tool) {
        $ver = & $tool --version 2>&1 | Select-Object -First 1
        Write-Ok "$tool — $ver"
    }
    else {
        Write-Fail "Required tool '$tool' is not installed or not on PATH."
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Repository structure validation
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "Validating repository structure"

$RequiredPaths = @(
    (Join-Path $RepoRoot "azure.yaml"),
    (Join-Path $ApiDir   "pyproject.toml"),
    (Join-Path $ApiDir   "Dockerfile"),
    (Join-Path $ApiDir   "app" "main.py"),
    (Join-Path $WebDir   "package.json"),
    (Join-Path $WebDir   "Dockerfile"),
    (Join-Path $InfraDir "main.bicep")
)

foreach ($p in $RequiredPaths) {
    if (Test-Path $p) {
        Write-Ok "Found $(Split-Path -Leaf $p)"
    }
    else {
        Write-Fail "Missing required file: $p"
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Azure Developer CLI environment
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "Verifying Azure Developer CLI environment"

if (Test-Command "azd") {
    try {
        if ($Environment) {
            Write-Host "  Selecting azd environment: $Environment"
            & azd env select $Environment 2>&1 | Out-Null
        }
        $envName = & azd env get-values 2>&1 | Select-String "^AZURE_ENV_NAME=" |
                   ForEach-Object { $_ -replace 'AZURE_ENV_NAME="?([^"]*)"?', '$1' }
        if ($envName) {
            Write-Ok "Active azd environment: $envName"
        }
        else {
            Write-Warn "Could not determine active azd environment. Run 'azd init' or 'azd env new <name>'."
        }
    }
    catch {
        Write-Warn "azd environment not configured. Run 'azd init' or 'azd env new <name>' first."
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Backend tests (pytest)
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "Running backend tests (pytest)"

if ($SkipTests) {
    Write-Warn "Skipped (--SkipTests flag)"
}
else {
    Push-Location $ApiDir
    try {
        Write-Host "  Running: uv run pytest --tb=short -q"
        $testResult = & uv run pytest --tb=short -q 2>&1
        $testExit = $LASTEXITCODE
        $testResult | ForEach-Object { Write-Host "  $_" }

        if ($testExit -eq 0) {
            Write-Ok "Backend tests passed"
        }
        else {
            Write-Fail "Backend tests failed (exit code $testExit)"
        }
    }
    catch {
        Write-Fail "Backend test execution error: $_"
    }
    finally {
        Pop-Location
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Frontend tests (vitest)
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "Running frontend tests (vitest)"

if ($SkipTests) {
    Write-Warn "Skipped (--SkipTests flag)"
}
else {
    Push-Location $WebDir
    try {
        Write-Host "  Running: npx vitest run"
        $testResult = & npx vitest run 2>&1
        $testExit = $LASTEXITCODE
        $testResult | ForEach-Object { Write-Host "  $_" }

        if ($testExit -eq 0) {
            Write-Ok "Frontend tests passed"
        }
        else {
            Write-Fail "Frontend tests failed (exit code $testExit)"
        }
    }
    catch {
        Write-Fail "Frontend test execution error: $_"
    }
    finally {
        Pop-Location
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Docker build verification
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "Verifying Docker builds"

if ($SkipDockerBuild) {
    Write-Warn "Skipped (--SkipDockerBuild flag)"
}
elseif (-not (Test-Command "docker")) {
    Write-Warn "Docker not available — skipping build verification"
}
else {
    # Backend image
    Write-Host "  Building API image..."
    & docker build -t customer-chatbot-api:release-check -f (Join-Path $ApiDir "Dockerfile") $ApiDir 2>&1 |
        Select-Object -Last 5 | ForEach-Object { Write-Host "  $_" }
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "API Docker build succeeded"
    }
    else {
        Write-Fail "API Docker build failed"
    }

    # Frontend image
    Write-Host "  Building Web image..."
    & docker build -t customer-chatbot-web:release-check -f (Join-Path $WebDir "Dockerfile") $WebDir 2>&1 |
        Select-Object -Last 5 | ForEach-Object { Write-Host "  $_" }
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Web Docker build succeeded"
    }
    else {
        Write-Fail "Web Docker build failed"
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# STEP 7 — Infrastructure validation
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "Validating Bicep infrastructure"

$bicepMain = Join-Path $InfraDir "main.bicep"
$expectedModules = @(
    "ai-search.bicep",
    "container-apps-env.bicep",
    "container-registry.bicep",
    "cosmos-db.bicep",
    "key-vault.bicep",
    "log-analytics.bicep",
    "openai.bicep",
    "speech-services.bicep",
    "storage.bicep"
)

foreach ($mod in $expectedModules) {
    $modPath = Join-Path $InfraDir "modules" $mod
    if (Test-Path $modPath) {
        Write-Ok "Bicep module: $mod"
    }
    else {
        Write-Fail "Missing Bicep module: $mod"
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# STEP 8 — Pre-flight summary
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "Pre-flight summary"

if ($Errors.Count -gt 0) {
    Write-Host ""
    Write-Host "  BLOCKED — $($Errors.Count) error(s) found:" -ForegroundColor Red
    foreach ($err in $Errors) {
        Write-Host "    • $err" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "  Fix the errors above before deploying." -ForegroundColor Red
    exit 1
}

Write-Ok "All pre-flight checks passed"

# ══════════════════════════════════════════════════════════════════════════════
# STEP 9 — Deploy via azd
# ══════════════════════════════════════════════════════════════════════════════
Write-Step "Deploying with Azure Developer CLI"

if ($DryRun) {
    Write-Warn "Dry-run mode — skipping actual deployment."
    Write-Host "  Command that would run: azd up --no-prompt"
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  DRY RUN COMPLETE — All checks passed"                       -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    exit 0
}

Write-Host "  Running: azd up --no-prompt"
Write-Host "  This provisions infrastructure and deploys both services."
Write-Host ""

& azd up --no-prompt
$deployExit = $LASTEXITCODE

if ($deployExit -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  DEPLOYMENT SUCCESSFUL"                                       -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Post-deployment checklist:" -ForegroundColor Yellow
    Write-Host "    1. Verify health probes:  GET /healthz  on API container app"
    Write-Host "    2. Verify frontend loads in browser"
    Write-Host "    3. Check Application Insights for errors"
    Write-Host "    4. Monitor Cosmos DB RU consumption"
    Write-Host "    5. Test a chat conversation end-to-end"
    Write-Host "    6. Verify Speech Services resource is provisioned (check AZURE_SPEECH_ENDPOINT)"
    Write-Host ""
    exit 0
}
else {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  DEPLOYMENT FAILED (exit code $deployExit)"                   -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Troubleshooting:" -ForegroundColor Yellow
    Write-Host "    • Run 'azd show' to check environment state"
    Write-Host "    • Run 'azd provision' separately to isolate infra issues"
    Write-Host "    • Run 'azd deploy' separately to isolate app issues"
    Write-Host "    • Check Container App logs in Azure Portal"
    Write-Host ""
    exit $deployExit
}
