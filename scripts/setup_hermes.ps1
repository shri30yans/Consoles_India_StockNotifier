# Install Hermes Agent on Windows (official path) and verify CLI.
# Repo docs: https://github.com/NousResearch/hermes-agent
#
# Usage:
#   .\scripts\setup_hermes.ps1              # install Hermes if missing, then doctor
#   .\scripts\setup_hermes.ps1 -SkipInstall # only check PATH and run doctor if present
#
param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

function Test-HermesExe {
    return [bool](Get-Command hermes -ErrorAction SilentlyContinue)
}

if (-not $SkipInstall -and -not (Test-HermesExe)) {
    Write-Host "Hermes CLI not found. Running official installer (downloads deps to LOCALAPPDATA\hermes)..." -ForegroundColor Cyan
    irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
}

if (-not (Test-HermesExe)) {
    Write-Host "Hermes is still not on PATH. Open a new terminal after install, or add the directory containing 'hermes.exe' to PATH." -ForegroundColor Yellow
    exit 1
}

Write-Host "Hermes found: $((Get-Command hermes).Source)" -ForegroundColor Green
Write-Host "Running hermes doctor..." -ForegroundColor Cyan
hermes doctor

Write-Host ""
Write-Host "Next: cd to this repo root and run 'hermes' so AGENTS.md loads." -ForegroundColor Cyan
Write-Host "Configure model with: hermes model" -ForegroundColor Gray
Write-Host "Run the stack with: python -m commerce_platform --host 0.0.0.0 --port 8000" -ForegroundColor Gray
