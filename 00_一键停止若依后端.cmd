@echo off
chcp 65001 >nul
title 一键停止若依后端

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp000_stop_ruoyi_backend.ps1"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
pause
exit /b %EXIT_CODE%
