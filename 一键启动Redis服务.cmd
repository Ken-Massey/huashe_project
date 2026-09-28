@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0\00_start_redis.ps1"
if errorlevel 1 (
    echo Redis startup failed. Check the message above.
) else (
    echo Redis is ready. You can close this window.
)
pause
