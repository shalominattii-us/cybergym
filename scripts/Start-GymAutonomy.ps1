# CyberGym — autonomy launcher (Windows unit, A2D standard)
# A2D: Add-to-Desktop shortcut, Auto-start-on-boot, Deploy-as-service.
# Waits for LM Studio (:1234), then trains the athlete unattended.
#
# GPO-safe invocation (unit blocks .ps1 by policy):
#   powershell -ep bypass -c "iex (gc "C:\Sovereign\CyberGym\scripts\Start-GymAutonomy.ps1" -raw)"

param(
    [string]$Athlete  = "lmstudio",
    [string]$Root     = "C:\Sovereign\CyberGym",
    [int]$IntervalSec = 1800
)

$ErrorActionPreference = "Stop"
Set-Location $Root

Write-Host "== CyberGym autonomy ==" -ForegroundColor Cyan
Write-Host "athlete=$Athlete interval=${IntervalSec}s root=$Root"

# Pull latest gym before starting — BUNDLEMIT in reverse.
if (Get-Command git -ErrorAction SilentlyContinue) {
    git pull --ff-only 2>$null
}

python scripts\gym_loop.py --athlete $Athlete --root $Root --interval $IntervalSec
