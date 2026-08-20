$ErrorActionPreference = "Stop"

$port = 8000
$workspace = $PSScriptRoot
$serverScript = Join-Path $workspace "audit_api\run_server.py"
$logDirectory = Join-Path $workspace "audit_api\runtime\logs"
$stdoutLog = Join-Path $logDirectory "audit_api_stdout.log"
$stderrLog = Join-Path $logDirectory "audit_api_stderr.log"

function Get-PortListeners {
    return @(
        Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
            Sort-Object -Property OwningProcess -Unique
    )
}

function Stop-PortListener {
    param([int]$ProcessId)

    if (-not $ProcessId) {
        return
    }

    Write-Host "Stopping old process PID $ProcessId..."
    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500

    if (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue) {
        Write-Host "PID $ProcessId is still running, using taskkill..."
        & taskkill.exe /PID $ProcessId /F /T | Out-Null
    }
}

Write-Host "Restarting Python audit service on port $port..."

foreach ($listener in Get-PortListeners) {
    Stop-PortListener -ProcessId $listener.OwningProcess
}

for ($attempt = 0; $attempt -lt 15; $attempt++) {
    if ((Get-PortListeners).Count -eq 0) {
        Write-Host "Port $port released."
        break
    }
    Write-Host "Waiting for port $port to release... ($($attempt + 1)/15)"
    Start-Sleep -Milliseconds 500
}

if ((Get-PortListeners).Count -gt 0) {
    throw "Port $port is still occupied. Please run this script as administrator."
}

$pythonCandidates = @(
    (Join-Path $workspace "stage1_reply_system\.venv\Scripts\python.exe"),
    (Join-Path $workspace ".venv\Scripts\python.exe")
)
$python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not $python) {
    throw "No project Python interpreter was found."
}
if (-not (Test-Path -LiteralPath $serverScript)) {
    throw "Server entry point was not found: $serverScript"
}

New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
Remove-Item -LiteralPath $stdoutLog, $stderrLog -Force -ErrorAction SilentlyContinue

$process = Start-Process `
    -FilePath $python `
    -ArgumentList "audit_api\run_server.py" `
    -WorkingDirectory $workspace `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -WindowStyle Hidden `
    -PassThru

Write-Host "Started new process PID $($process.Id), waiting for API readiness..."

for ($attempt = 0; $attempt -lt 60; $attempt++) {
    if ((Get-PortListeners).Count -gt 0) {
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:$port/health" -TimeoutSec 3
            Write-Host ""
            Write-Host "Audit API restarted successfully."
            Write-Host "PID: $($process.Id)"
            Write-Host "URL: http://127.0.0.1:$port"
            Write-Host "Health: $($response | ConvertTo-Json -Compress)"
            Write-Host "Logs: $logDirectory"
            exit 0
        }
        catch {
            # The port can open briefly before FastAPI is ready.
        }
    }

    if ($process.HasExited) {
        break
    }
    if (($attempt + 1) % 5 -eq 0) {
        Write-Host "Still waiting... ($($attempt + 1)/60)"
    }
    Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host "Audit API failed to start."
if (Test-Path -LiteralPath $stderrLog) {
    Write-Host "Error log:"
    Get-Content -LiteralPath $stderrLog -Tail 30
}
exit 1
