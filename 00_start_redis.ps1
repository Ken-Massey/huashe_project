$ErrorActionPreference = 'Stop'

$workspace = $PSScriptRoot
$redisDirectory = 'D:\develop\Redis\Redis-8.8.0-Windows-x64-cygwin-with-Service'
$redisServer = Join-Path $redisDirectory 'redis-server.exe'
$redisClient = Join-Path $redisDirectory 'redis-cli.exe'
$logDirectory = Join-Path $workspace 'audit_api\runtime\logs'
$stdoutLog = Join-Path $logDirectory 'redis_stdout.log'
$stderrLog = Join-Path $logDirectory 'redis_stderr.log'

if (-not (Test-Path -LiteralPath $redisServer) -or -not (Test-Path -LiteralPath $redisClient)) {
    throw "Redis executables were not found in $redisDirectory"
}

function Test-RedisReady {
    try {
        $reply = & $redisClient -h 127.0.0.1 -p 6379 ping 2>$null
        return ($LASTEXITCODE -eq 0 -and ($reply | Select-Object -First 1) -eq 'PONG')
    }
    catch {
        return $false
    }
}

if (Test-RedisReady) {
    Write-Host 'Redis is already ready on 127.0.0.1:6379.'
    exit 0
}

$portInUse = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners() |
    Where-Object { $_.Port -eq 6379 } |
    Select-Object -First 1
if ($portInUse) {
    throw 'Port 6379 is occupied, but Redis did not answer PONG. Check the process using that port.'
}

New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$process = Start-Process -FilePath $redisServer `
    -ArgumentList '--bind', '127.0.0.1', '--port', '6379' `
    -WorkingDirectory $workspace `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -WindowStyle Hidden `
    -PassThru

for ($attempt = 0; $attempt -lt 15; $attempt++) {
    Start-Sleep -Seconds 1
    if (Test-RedisReady) {
        Write-Host 'Redis started successfully on 127.0.0.1:6379.'
        Write-Host "PID: $($process.Id)"
        Write-Host "Logs: $stdoutLog"
        exit 0
    }
    if ($process.HasExited) {
        break
    }
}

Write-Host 'Redis failed to start. Recent output:'
if (Test-Path -LiteralPath $stdoutLog) {
    Get-Content -LiteralPath $stdoutLog -Tail 20
}
if (Test-Path -LiteralPath $stderrLog) {
    Get-Content -LiteralPath $stderrLog -Tail 20
}
exit 1
