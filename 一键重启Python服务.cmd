@echo off
setlocal
cd /d "%~dp0"

echo Restarting Python audit service...
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0\00_restart_audit_api.ps1"

echo.
echo Done. You can close this window after checking the result above.
pause
