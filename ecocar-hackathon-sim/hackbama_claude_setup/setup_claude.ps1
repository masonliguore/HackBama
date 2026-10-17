$ErrorActionPreference = "Stop"
Write-Host "=== HackBama Claude Code Setup ===" -ForegroundColor Cyan
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "git is required." }
$eccDir = Join-Path $env:TEMP "everything-claude-code"
if (Test-Path $eccDir) { Remove-Item -Recurse -Force $eccDir }
git clone --depth 1 https://github.com/affaan-m/everything-claude-code.git $eccDir
if (-not (Test-Path (Join-Path $eccDir "install.ps1"))) { throw "ECC install.ps1 not found." }
Push-Location $eccDir
try { pwsh -ExecutionPolicy Bypass -File .\install.ps1 --target claude python }
finally { Pop-Location }
Write-Host "ECC installed. Restart Claude Code from the EcoCAR repo root." -ForegroundColor Green
