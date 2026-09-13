# CyberGym — gym session launcher (Windows unit, A2D standard)
# A2D: Add-to-Desktop shortcut, Auto-start optional, Deploy-as-service optional.
# Runs the drill engine against the local LLM Armada (Ollama :11434).
# NOTE: unit is GPO-locked for .ps1 — invoke via the established IEX pattern:
#   powershell -ep bypass -c "iex (gc "$env:USERPROFILE\CyberGym\scripts\Start-GymSession.ps1" -raw)"

param(
    [string]$Athlete = "ollama",
    [string]$Model   = "llama3.1:8b",
    [string]$Drill   = "drills/precision/log_triage_01.json",
    [string]$Root    = "$env:USERPROFILE\CyberGym"
)

$ErrorActionPreference = "Stop"
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "python not on PATH — install Python 3.11+ on the unit first."
}

Write-Host "== CyberGym gym ==" -ForegroundColor Cyan
Write-Host "athlete=$Athlete model=$Model drill=$Drill"

python -m gym.engine run --drill $Drill --athlete $Athlete --model $Model --ledger-dir "$Root\ledger"

Write-Host "`n== Front desk: next workout ==" -ForegroundColor Cyan
python -m gym.scheduler --ledger-dir "$Root\ledger" --athlete "$Athlete`:$Model" --drills-dir "$Root\drills"

Write-Host "`n== Scoreboard ==" -ForegroundColor Cyan
python -m gym.scoring --ledger-dir "$Root\ledger" --athlete "$Athlete`:$Model"
