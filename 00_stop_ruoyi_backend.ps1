[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$ErrorActionPreference = "Stop"
$port = 8080

try {
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1

    if (-not $listener) {
        Write-Host "[OK] RuoYi backend is not running. Port 8080 is free." -ForegroundColor Green
        exit 0
    }

    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
    $processName = [string]$process.Name
    $commandLine = [string]$process.CommandLine
    $isJava = $processName -in @("java.exe", "javaw.exe")
    $isRuoYi = $commandLine -match "com\.ruoyi\.RuoYiApplication|ruoyi-admin\.jar"

    if (-not ($isJava -and $isRuoYi)) {
        Write-Host "[SKIPPED] Port 8080 belongs to another program. Nothing was stopped." -ForegroundColor Yellow
        Write-Host "Process: $processName"
        Write-Host "PID: $($listener.OwningProcess)"
        Write-Host "Command: $commandLine"
        exit 2
    }

    $pidToStop = [int]$listener.OwningProcess
    Write-Host "Stopping RuoYi backend, PID: $pidToStop ..."
    Stop-Process -Id $pidToStop -Force

    for ($index = 0; $index -lt 30; $index++) {
        Start-Sleep -Milliseconds 200
        $remaining = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if (-not $remaining) {
            Write-Host "[OK] RuoYi backend stopped. Port 8080 is free." -ForegroundColor Green
            exit 0
        }
    }

    Write-Host "[WARNING] Stop command was sent, but port 8080 is still in use. Run this script again later." -ForegroundColor Yellow
    exit 1
}
catch {
    Write-Host "[FAILED] Could not stop RuoYi backend: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
