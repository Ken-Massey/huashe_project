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

Write-Host "Restarting Python audit service on port $port..."

foreach ($listener in Get-PortListeners) {
    Write-Host "Stopping old process PID $($listener.OwningProcess)..."
    Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
}

for ($attempt = 0; $attempt -lt 15; $attempt++) {
    if ((Get-PortListeners).Count -eq 0) {
        break
    }
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
    Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host "Audit API failed to start."
if (Test-Path -LiteralPath $stderrLog) {
    Write-Host "Error log:"
    Get-Content -LiteralPath $stderrLog -Tail 30
}
exit 1
